"""Leitura das sessões em disco → registros organizados pra análise.

Não depende do estado in-memory do jogo: lê manifest.json, events.jsonl e
final_idea.json de cada sessão. Anexa a condição experimental (braço, tópico,
composição) a cada ideia.
"""
import json
from typing import Dict, List, Optional

from core import config
from persistence import paths


def _read_jsonl(path) -> List[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _read_json(path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def list_session_ids() -> List[str]:
    d = config.SESSIONS_DIR
    if not d.exists():
        return []
    return sorted([p.name for p in d.iterdir() if p.is_dir()])


def _condition_from_manifest(manifest: dict) -> dict:
    """Extrai a condição. Prioriza o bloco study; cai pro protocolo."""
    study = manifest.get("study") or {}
    return {
        "study_id": study.get("study_id"),
        "arm": study.get("arm") or manifest.get("protocol_id"),
        "topic": study.get("topic") or manifest.get("topic"),
        "composition": study.get("composition")
            or (manifest.get("composition") or {}).get("id"),
        "protocol_id": manifest.get("protocol_id"),
        "quem_avanca": manifest.get("quem_avanca"),
        "source_blind": manifest.get("source_blind_on_choice"),
        "judge_criterion": manifest.get("judge_criterion"),
    }


def load_session(session_id: str) -> dict:
    """Carrega uma sessão: condição + ideias (propostas) + ideia final."""
    manifest = _read_json(paths.manifest_path(session_id)) or {}
    events = _read_jsonl(paths.events_log_path(session_id))
    final = _read_json(paths.final_idea_path(session_id)) or {}
    cond = _condition_from_manifest(manifest)

    # quem é humano vs IA (do manifest/personas)
    persona_names = set(manifest.get("personas") or [])
    user_name = manifest.get("user_name")

    # Mapas auxiliares por rodada
    advanced_by_round: Dict[int, int] = {}
    player_pick_by_round: Dict[int, int] = {}
    judge_pick_by_round: Dict[int, int] = {}
    match_by_round: Dict[int, bool] = {}
    for e in events:
        r = e.get("round")
        t = e.get("type")
        p = e.get("payload", {})
        if t == "round.idea_advanced":
            advanced_by_round[r] = p.get("advanced_player_id")
        elif t == "player.picked":
            player_pick_by_round[r] = p.get("player_id")
        elif t == "judge.picked":
            judge_pick_by_round[r] = p.get("player_id")
        elif t == "round.choices_compared":
            match_by_round[r] = p.get("match")

    ideas: List[dict] = []
    for e in events:
        if e.get("type") != "round.proposal_submitted":
            continue
        p = e.get("payload", {})
        r = e.get("round")
        pid = p.get("player_id")
        actor = e.get("actor", "")
        author_type = "human" if actor == "user" else "persona"
        ideas.append({
            "session_id": session_id,
            **cond,
            "round": r,
            "player_id": pid,
            "author_type": author_type,
            "idea_text": p.get("idea_text") or "",
            "stance": p.get("stance"),
            "reasoning_mode": p.get("reasoning_mode"),
            "is_advanced": advanced_by_round.get(r) == pid,
            "picked_by_player": player_pick_by_round.get(r) == pid,
            "picked_by_judge": judge_pick_by_round.get(r) == pid,
            "judge_match": match_by_round.get(r),
        })

    final_text = (final.get("summary") or "").strip()
    final_record = None
    if final_text:
        final_record = {"session_id": session_id, **cond, "final_text": final_text}

    return {"session_id": session_id, "condition": cond,
            "ideas": ideas, "final": final_record,
            "user_name": user_name, "personas": list(persona_names)}


def load_all(session_ids: Optional[List[str]] = None) -> List[dict]:
    ids = session_ids if session_ids is not None else list_session_ids()
    return [load_session(sid) for sid in ids]


def flatten_ideas(sessions: List[dict]) -> List[dict]:
    out = []
    for s in sessions:
        out.extend(s["ideas"])
    return out


def final_ideas(sessions: List[dict]) -> List[dict]:
    return [s["final"] for s in sessions if s.get("final")]
