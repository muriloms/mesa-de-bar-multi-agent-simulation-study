"""Geradores de identificadores únicos."""
import uuid
from datetime import datetime, timezone


def session_id() -> str:
    """Format: YYYYMMDD-HHMMSS_<short>. Ordenável lexicograficamente."""
    now = datetime.now(timezone.utc)
    short = uuid.uuid4().hex[:8]
    return now.strftime("%Y%m%d-%H%M%S") + "_" + short


def event_id() -> str:
    return "evt_" + uuid.uuid4().hex[:24]


def call_id() -> str:
    return "call_" + uuid.uuid4().hex[:24]
