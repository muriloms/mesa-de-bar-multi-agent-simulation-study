"""Utilitários de tempo: timestamps ISO-8601 e elapsed_ms."""
from datetime import datetime, timezone


def iso_now() -> str:
    """ISO-8601 UTC com milissegundos, sufixo Z."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def elapsed_ms(since: datetime) -> int:
    return int((datetime.now(timezone.utc) - since).total_seconds() * 1000)
