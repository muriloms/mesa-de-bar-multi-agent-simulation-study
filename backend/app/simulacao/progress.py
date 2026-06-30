"""Store em memória do progresso das execuções de simulação (para a API)."""
from typing import Dict, Optional
import threading

_runs: Dict[str, dict] = {}
_lock = threading.Lock()


def init_run(run_id: str, plan: dict) -> None:
    with _lock:
        _runs[run_id] = {
            "run_id": run_id,
            "status": "running",          # running | done | error
            "total_sessions": plan.get("total_sessions", 0),
            "cells": plan.get("cells", 0),
            "completed": 0,
            "current": None,              # descrição da etapa atual
            "errors": [],
            "started_at": None,
            "finished_at": None,
            "output_dir": None,
        }


def update(run_id: str, **kw) -> None:
    with _lock:
        if run_id in _runs:
            _runs[run_id].update(kw)


def tick(run_id: str, current: Optional[str] = None) -> None:
    with _lock:
        if run_id in _runs:
            _runs[run_id]["completed"] += 1
            if current is not None:
                _runs[run_id]["current"] = current


def get(run_id: str) -> Optional[dict]:
    with _lock:
        return dict(_runs[run_id]) if run_id in _runs else None
