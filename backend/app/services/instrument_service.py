"""Serviço de aplicação de instrumentos.

Fluxo:
  1. Front pede `GET /api/instruments/{id}` → backend devolve definição
  2. Front renderiza, coleta respostas
  3. Front envia `POST /api/sessions/{sid}/instruments/{iid}/responses`
  4. Backend valida (existe sessão? respostas batem com itens?), grava em
     `data/sessions/<sid>/instruments/<iid>.json`, emite evento.
"""
import json
from typing import Any, Dict, List

from core import ids, time as core_time
from core.exceptions import MesaDeBarError, SessionNotFoundError
from domain.instrument import (
    Instrument, InstrumentItemResponse, InstrumentResponse,
)
from instruments.loader import load_instrument
from persistence import event_log, paths
from domain.event import Event


def _emit_event(session_id: str, type_: str, payload: dict, started_ms: int = 0) -> None:
    event = Event(
        event_id=ids.event_id(),
        session_id=session_id,
        timestamp=core_time.iso_now(),
        elapsed_ms=started_ms,
        type=type_,
        actor="user",
        payload=payload,
    )
    event_log.append(session_id, event)


def get_instrument(instrument_id: str) -> Instrument:
    return load_instrument(instrument_id)


def submit_instrument_response(
    session_id: str,
    instrument_id: str,
    started_at: str,
    submitted_at: str,
    duration_ms: int,
    responses: List[Dict[str, Any]],
    response_order: List[str],
) -> Dict[str, Any]:
    """Valida e grava as respostas de um instrumento."""
    instrument = load_instrument(instrument_id)

    # Valida que session_id tem pasta
    session_dir = paths.session_dir(session_id)
    if not session_dir.exists():
        raise SessionNotFoundError(session_id)

    # Mapa item_id → item pra checagens
    valid_item_ids = {
        item.id: item
        for section in instrument.sections
        for item in section.items
    }

    # Filtra/valida cada resposta — descarta com item_id desconhecido
    clean_responses: List[InstrumentItemResponse] = []
    for r in responses:
        iid = r.get("item_id")
        if iid not in valid_item_ids:
            continue
        clean_responses.append(InstrumentItemResponse(
            item_id=iid,
            value=r.get("value"),
            time_spent_ms=r.get("time_spent_ms"),
            answered_at=r.get("answered_at"),
        ))

    # Verifica items required
    answered_ids = {r.item_id for r in clean_responses}
    missing_required = [
        item.id for item in valid_item_ids.values()
        if item.required and item.id not in answered_ids
    ]
    # Não bloqueamos por hora — apenas reportamos no payload do evento.
    # Permite estudo flexível (alguns items required podem ser opcionais
    # em alguns protocolos via override). Se quiser fail-fast, descomente:
    # if missing_required:
    #     raise MesaDeBarError(f"Itens obrigatórios não respondidos: {missing_required}")

    response = InstrumentResponse(
        instrument_id=instrument_id,
        instrument_version=instrument.version,
        session_id=session_id,
        moment=instrument.moment,
        started_at=started_at,
        submitted_at=submitted_at,
        duration_ms=duration_ms,
        responses=clean_responses,
        response_order=response_order,
    )

    # Grava em data/sessions/<sid>/instruments/<iid>.json
    instruments_dir = session_dir / "instruments"
    instruments_dir.mkdir(parents=True, exist_ok=True)
    output_path = instruments_dir / f"{instrument_id}.json"
    output_path.write_text(
        response.model_dump_json(indent=2),
        encoding="utf-8",
    )

    # Emite evento
    _emit_event(
        session_id,
        f"instrument.submitted",
        {
            "instrument_id": instrument_id,
            "instrument_version": instrument.version,
            "moment": instrument.moment,
            "duration_ms": duration_ms,
            "responses_count": len(clean_responses),
            "missing_required": missing_required,
        },
    )

    return {
        "ok": True,
        "instrument_id": instrument_id,
        "responses_count": len(clean_responses),
        "missing_required": missing_required,
    }
