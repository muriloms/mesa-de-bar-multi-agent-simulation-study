"""Resolução de paths por session_id.

Toda escrita em disco passa por aqui — nenhum outro módulo deve
construir paths manualmente.
"""
from pathlib import Path
from core import config


def session_dir(session_id: str) -> Path:
    return config.SESSIONS_DIR / session_id


def manifest_path(session_id: str) -> Path:
    return session_dir(session_id) / "manifest.json"


def events_log_path(session_id: str) -> Path:
    return session_dir(session_id) / "events.jsonl"


def llm_log_path(session_id: str) -> Path:
    return session_dir(session_id) / "llm_calls.jsonl"


def transcript_json_path(session_id: str) -> Path:
    return session_dir(session_id) / "transcript.json"


def transcript_md_path(session_id: str) -> Path:
    return session_dir(session_id) / "transcript.md"


def protocol_path(session_id: str) -> Path:
    return session_dir(session_id) / "protocol.json"


def final_idea_path(session_id: str) -> Path:
    return session_dir(session_id) / "final_idea.json"


def study_dir(study_id: str) -> Path:
    return config.DATA_DIR / "studies" / study_id


def study_ledger_path(study_id: str) -> Path:
    return study_dir(study_id) / "assignments.jsonl"


def cat_dir(study_id: str) -> Path:
    return config.DATA_DIR / "cat" / study_id


def cat_items_path(study_id: str) -> Path:
    return cat_dir(study_id) / "items.json"


def cat_key_path(study_id: str) -> Path:
    return cat_dir(study_id) / "key.json"


def cat_ratings_path(study_id: str) -> Path:
    return cat_dir(study_id) / "ratings.jsonl"
