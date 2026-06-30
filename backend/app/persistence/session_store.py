"""Manifest, protocol freeze e transcript da sessão."""
import json

from domain.session import GameState
from domain.protocol import Protocol
from . import paths


def create(session_id: str) -> None:
    """Cria a pasta da sessão (idempotente)."""
    paths.session_dir(session_id).mkdir(parents=True, exist_ok=True)


def write_manifest(session_id: str, manifest: dict) -> None:
    paths.manifest_path(session_id).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def read_manifest(session_id: str) -> dict:
    return json.loads(paths.manifest_path(session_id).read_text(encoding="utf-8"))


def write_protocol(session_id: str, protocol: Protocol) -> None:
    """Congela uma cópia do protocolo na pasta da sessão."""
    paths.protocol_path(session_id).write_text(
        protocol.model_dump_json(indent=2), encoding="utf-8"
    )


def write_transcript(session_id: str, game_state: GameState) -> None:
    """Grava transcript.json (estruturado) e transcript.md (legível)."""
    # JSON estruturado
    paths.transcript_json_path(session_id).write_text(
        json.dumps({
            "session_id": session_id,
            "topic": game_state.topic,
            "round": game_state.round,
            "phase": game_state.game_phase,
            "messages": [m.model_dump() for m in game_state.conversation],
            "final_summary": game_state.final_summary,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Markdown legível
    md = [f"# Mesa de Bar — Sessão `{session_id}`", ""]
    md.append(f"**Tópico:** {game_state.topic}")
    md.append(f"**Rodada atual:** {game_state.round}")
    md.append(f"**Fase:** {game_state.game_phase}")
    md.append("")
    md.append("## Conversa")
    md.append("")
    for m in game_state.conversation:
        md.append(f"**{m.player_name}:** {m.message}")
        md.append("")
    if game_state.final_summary:
        md.append("## Síntese final do Dono do Bar")
        md.append("")
        md.append(game_state.final_summary)
    paths.transcript_md_path(session_id).write_text("\n".join(md), encoding="utf-8")
