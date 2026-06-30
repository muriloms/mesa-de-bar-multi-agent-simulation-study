"""Exporta a ideia organizada em diferentes formatos."""
import json
from typing import Dict, Any

from core.exceptions import SessionNotFoundError
from persistence import paths


def load_idea(session_id: str) -> Dict[str, Any]:
    """Lê final_idea.json e devolve {summary, lab_idea}."""
    session_dir = paths.session_dir(session_id)
    if not session_dir.exists():
        raise SessionNotFoundError(session_id)
    path = paths.final_idea_path(session_id)
    if not path.exists():
        return {"summary": None, "lab_idea": None}
    return json.loads(path.read_text(encoding="utf-8"))


def idea_to_markdown(idea: Dict[str, Any], topic: str = "") -> str:
    """Renderiza a ideia organizada como Markdown legível."""
    lines = []
    structured = idea.get("lab_idea") or {}
    summary = idea.get("summary") or ""

    title = structured.get("title") or topic or "Ideia da Mesa de Bar"
    lines.append(f"# {title}\n")

    if topic:
        lines.append(f"**Tópico discutido:** {topic}\n")

    if structured.get("problem_statement"):
        lines.append("## Problema\n")
        lines.append(structured["problem_statement"].strip() + "\n")

    if structured.get("core_solution"):
        lines.append("## Solução central\n")
        lines.append(structured["core_solution"].strip() + "\n")

    features = structured.get("key_features") or []
    if features:
        lines.append("## Funcionalidades-chave\n")
        for f in features:
            lines.append(f"- {f}")
        lines.append("")

    if structured.get("target_audience"):
        lines.append("## Público-alvo\n")
        lines.append(structured["target_audience"].strip() + "\n")

    if structured.get("potential_impact"):
        lines.append("## Impacto potencial\n")
        lines.append(structured["potential_impact"].strip() + "\n")

    if structured.get("next_steps"):
        lines.append("## Próximos passos\n")
        lines.append(structured["next_steps"].strip() + "\n")

    if summary:
        lines.append("---\n")
        lines.append("## Síntese do Dono do Bar\n")
        lines.append(summary.strip() + "\n")

    return "\n".join(lines)
