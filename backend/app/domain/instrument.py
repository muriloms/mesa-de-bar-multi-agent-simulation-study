"""Modelos de instrumentos de pesquisa (questionários).

Um Instrument é definido em YAML em `instruments/<id>.yaml` e carregado
sob demanda. Tem seções, itens (perguntas), e regras de validação simples.

Tipos de item suportados:
  - text_short, text_long: texto livre
  - number: campo numérico (idade, quantidade) com min/max/step e unidade opcional
  - likert: escala 1-N com rótulos
  - single_select: uma opção de várias
  - multi_select: múltiplas opções
  - slider: valor numérico contínuo entre min e max
  - ranking: arrastar-e-soltar pra ordenar opções

Resposta é guardada em `data/sessions/<id>/instruments/<instrument_id>.json`.
"""
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


ItemType = Literal[
    "text_short", "text_long",
    "number",
    "likert",
    "single_select", "multi_select",
    "slider",
    "ranking",
]


class InstrumentItem(BaseModel):
    """Uma pergunta/item individual."""
    id: str = Field(..., description="Identificador único dentro do instrumento")
    type: ItemType
    question: str
    description: Optional[str] = None
    required: bool = True

    # text_short/text_long
    placeholder: Optional[str] = None
    max_length: Optional[int] = None

    # likert
    scale: Optional[int] = Field(default=None, description="Tamanho da escala (ex: 5 ou 7)")
    labels: Optional[List[str]] = Field(default=None, description="Rótulos para cada ponto")

    # single_select / multi_select / ranking
    options: Optional[List[str]] = None

    # slider / number (faixa numérica)
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    min_label: Optional[str] = None
    max_label: Optional[str] = None
    default: Optional[float] = None
    unit: Optional[str] = Field(default=None, description="Unidade exibida ao lado do número (ex: anos)")


class InstrumentSection(BaseModel):
    """Agrupamento lógico de itens."""
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    items: List[InstrumentItem]


class Instrument(BaseModel):
    """Definição completa de um instrumento de pesquisa."""
    id: str
    version: str = "1.0.0"
    title: str
    description: Optional[str] = None
    moment: Literal["pre_session", "post_session", "post_round"] = "pre_session"
    sections: List[InstrumentSection]


class InstrumentItemResponse(BaseModel):
    """Resposta a um item individual."""
    item_id: str
    value: Any  # tipo varia por tipo de item; validação no client
    time_spent_ms: Optional[int] = None
    answered_at: Optional[str] = None  # ISO-8601


class InstrumentResponse(BaseModel):
    """Resposta completa a um instrumento."""
    instrument_id: str
    instrument_version: str
    session_id: str
    moment: str
    started_at: str
    submitted_at: str
    duration_ms: int
    responses: List[InstrumentItemResponse]
    response_order: List[str] = Field(
        default_factory=list,
        description="Ordem em que itens foram respondidos (telemetria)"
    )
