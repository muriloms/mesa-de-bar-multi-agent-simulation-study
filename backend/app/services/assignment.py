"""Runner de atribuição experimental — balanceia braço × tópico × composição.

Balanceamento ANINHADO e determinístico:
  1. escolhe o BRAÇO menos preenchido (empate → ordem em study.arms)
  2. dentro do braço, o TÓPICO menos preenchido (empate → ordem em study.topics)
  3. dentro de (braço, tópico), a COMPOSIÇÃO menos preenchida

O ledger append-only em data/studies/<id>/assignments.jsonl é a fonte de
verdade da contagem — garante reprodutibilidade e auditoria.
"""
import json
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from core import ids
from domain.study import Assignment, Study
from persistence import paths


def _read_ledger(study_id: str) -> List[dict]:
    path = paths.study_ledger_path(study_id)
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


def _append_ledger(study_id: str, assignment: Assignment) -> None:
    path = paths.study_ledger_path(study_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(assignment.model_dump(), ensure_ascii=False) + "\n")


def _least_filled(options: List[str], counts: Dict[str, int]) -> str:
    """Devolve a opção com menor contagem; empate resolvido pela ordem da lista."""
    best = None
    best_count = None
    for opt in options:
        c = counts.get(opt, 0)
        if best_count is None or c < best_count:
            best, best_count = opt, c
    return best


def assign(study: Study, session_id: Optional[str] = None) -> Assignment:
    """Atribui (braço, tópico, composição) ao próximo participante e registra."""
    ledger = _read_ledger(study.id)

    if study.assignment == "random":
        arm = random.choice(study.arms)
        topic = random.choice(study.topics) if study.topics else None
        comp = random.choice(study.compositions) if study.compositions else None
    else:
        # 1) braço menos preenchido
        arm_counts: Dict[str, int] = {}
        for r in ledger:
            arm_counts[r.get("arm")] = arm_counts.get(r.get("arm"), 0) + 1
        arm = _least_filled(study.arms, arm_counts)

        # 2) tópico menos preenchido DENTRO do braço
        topic = None
        if study.topics:
            t_counts: Dict[str, int] = {}
            for r in ledger:
                if r.get("arm") == arm and r.get("topic") is not None:
                    t_counts[r["topic"]] = t_counts.get(r["topic"], 0) + 1
            topic = _least_filled(study.topics, t_counts)

        # 3) composição menos preenchida DENTRO de (braço, tópico)
        comp = None
        if study.compositions:
            c_counts: Dict[str, int] = {}
            for r in ledger:
                if r.get("arm") == arm and r.get("topic") == topic and r.get("composition") is not None:
                    c_counts[r["composition"]] = c_counts.get(r["composition"], 0) + 1
            comp = _least_filled(study.compositions, c_counts)

    cell = "|".join([arm or "", topic or "", comp or ""])
    assignment = Assignment(
        assignment_id="asg_" + ids.event_id().split("_", 1)[1][:16],
        study_id=study.id, session_id=session_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        arm=arm, topic=topic, composition=comp,
        strategy=study.assignment, cell=cell,
    )
    _append_ledger(study.id, assignment)
    return assignment


def balance_report(study: Study) -> dict:
    """Resumo das contagens por braço/tópico/composição (pra auditoria)."""
    ledger = _read_ledger(study.id)
    by_arm: Dict[str, int] = {}
    by_cell: Dict[str, int] = {}
    for r in ledger:
        by_arm[r.get("arm")] = by_arm.get(r.get("arm"), 0) + 1
        by_cell[r.get("cell", "")] = by_cell.get(r.get("cell", ""), 0) + 1
    return {"total": len(ledger), "by_arm": by_arm, "by_cell": by_cell}
