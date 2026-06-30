"""Estatísticas da sessão para a tela final.

Lê events.jsonl + manifest + state in-memory e devolve um payload
estruturado pra UI da Tela 3 mostrar.
"""
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import json
from typing import Any, Dict, List, Optional

from core.exceptions import SessionNotFoundError
from persistence import paths
from services.costs import compute_session_costs


def compute_session_stats(session_id: str) -> Dict[str, Any]:
    """Calcula estatísticas de uma sessão pra mostrar ao jogador.

    Returns:
        {
          "session_id": ...,
          "duration_ms": int,
          "rounds_played": int,
          "phases_done": [...],
          "players": [{player_id, name, drinks, balance, ...}],
          "totals": {total_bid, total_pot, ...},
          "stances": {complement: N, counter: N, redirect: N, none: N},
          "winners_by_round": [{round, phase, winner_id, winner_name, bid}],
          "costs": { ... from compute_session_costs },
          "winner_counts": {player_id: count},
        }
    """
    session_dir = paths.session_dir(session_id)
    if not session_dir.exists():
        raise SessionNotFoundError(session_id)

    manifest_path = session_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) \
        if manifest_path.exists() else {}

    events_path = session_dir / "events.jsonl"
    events: List[dict] = []
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    transcript_path = session_dir / "transcript.json"
    transcript = json.loads(transcript_path.read_text(encoding="utf-8")) \
        if transcript_path.exists() else {}

    # === Duração ===
    started_at = manifest.get("started_at")
    finished_at = manifest.get("finished_at")
    duration_ms = 0
    if started_at and finished_at:
        try:
            start_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
            duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
        except ValueError:
            pass
    if duration_ms == 0 and events:
        # fallback: último elapsed_ms dos eventos
        duration_ms = max(e.get("elapsed_ms", 0) for e in events)

    # === Players ===
    players = transcript.get("players", [])

    # === Eventos por tipo ===
    by_type: Dict[str, List[dict]] = defaultdict(list)
    for e in events:
        by_type[e.get("type", "")].append(e)

    # === Rodadas e vencedores ===
    round_starteds = by_type.get("round.started", [])
    rounds_played = len(round_starteds)

    winners_by_round: List[dict] = []
    winner_counts: Counter = Counter()
    for ev in by_type.get("vote.resolved", []):
        pl = ev.get("payload", {})
        winner_id = pl.get("winner_id")
        winners_by_round.append({
            "round": ev.get("round"),
            "phase": ev.get("phase"),
            "winner_id": winner_id,
            "winner_name": pl.get("winner_name"),
            "winning_bid": pl.get("winning_bid"),
            "pot": pl.get("pot"),
            "drink_awarded": pl.get("drink_awarded"),
        })
        if winner_id is not None:
            winner_counts[winner_id] += 1

    # === Fases percorridas ===
    phases_done: List[str] = []
    for ev in by_type.get("phase.entered", []):
        ph = ev.get("payload", {}).get("phase") or ev.get("phase")
        if ph and ph not in phases_done:
            phases_done.append(ph)

    # === Apostas e propostas ===
    proposals = by_type.get("round.proposal_submitted", [])
    total_bid = sum(p.get("payload", {}).get("bid_amount_effective", 0) or 0 for p in proposals)
    total_pot = sum(w.get("pot", 0) or 0 for w in winners_by_round)
    total_proposals = len(proposals)

    # === Distribuição de stances ===
    stance_counter: Counter = Counter()
    for p in proposals:
        s = p.get("payload", {}).get("stance")
        stance_counter[s or "none"] += 1
    stances = {
        "complement": stance_counter.get("complement", 0),
        "counter": stance_counter.get("counter", 0),
        "redirect": stance_counter.get("redirect", 0),
        "none": stance_counter.get("none", 0),
    }

    # === Comprimento médio das propostas ===
    char_counts = [
        p.get("payload", {}).get("idea_chars") or len(str(p.get("payload", {}).get("idea_text") or ""))
        for p in proposals
    ]
    avg_idea_chars = int(sum(char_counts) / len(char_counts)) if char_counts else 0

    # === Drinks finais por player ===
    drinks_by_player: Dict[int, int] = {}
    for w in winners_by_round:
        if w.get("drink_awarded") and w.get("winner_id") is not None:
            drinks_by_player[w["winner_id"]] = drinks_by_player.get(w["winner_id"], 0) + 1

    # === Pesquisas respondidas ===
    instruments_path = session_dir / "instruments"
    instruments_filled: List[str] = []
    if instruments_path.exists():
        for f in instruments_path.glob("*.json"):
            instruments_filled.append(f.stem)

    # === Custos LLM ===
    try:
        costs = compute_session_costs(session_id)
    except Exception:
        costs = {"total": {"calls": 0, "cost_usd": 0.0, "tokens_in": 0, "tokens_out": 0}}

    return {
        "session_id": session_id,
        "topic": manifest.get("topic"),
        "user_name": manifest.get("user_name"),
        "protocol_id": manifest.get("protocol_id"),
        "language": manifest.get("language"),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
        "rounds_played": rounds_played,
        "phases_done": phases_done,
        "players": [
            {
                "player_id": p.get("id"),
                "name": p.get("name"),
                "is_ai": p.get("is_ai"),
                "balance": p.get("balance"),
                "drinks": p.get("drinks", drinks_by_player.get(p.get("id"), 0)),
                "wins": winner_counts.get(p.get("id"), 0),
            }
            for p in players
        ],
        "winners_by_round": winners_by_round,
        "totals": {
            "total_bid": round(total_bid, 2),
            "total_pot": round(total_pot, 2),
            "total_proposals": total_proposals,
            "avg_idea_chars": avg_idea_chars,
        },
        "stances": stances,
        "instruments_filled": instruments_filled,
        "costs": {
            "calls": costs.get("total", {}).get("calls", 0),
            "tokens_in": costs.get("total", {}).get("tokens_in", 0),
            "tokens_out": costs.get("total", {}).get("tokens_out", 0),
            "cost_usd": round(costs.get("total", {}).get("cost_usd", 0.0), 4),
            "avg_latency_ms": costs.get("total", {}).get("avg_latency_ms", 0),
        },
    }
