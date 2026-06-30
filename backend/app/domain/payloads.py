"""Payloads de request da API (v2)."""
from typing import Optional
from pydantic import BaseModel


class UserIdeaPayload(BaseModel):
    """Humano submete a ideia da rodada (sem aposta)."""
    session_id: str
    idea_text: str


class PlayerPickPayload(BaseModel):
    """Humano escolhe a melhor ideia (referência anônima)."""
    session_id: str
    pick_ref: str


class AdvancePayload(BaseModel):
    """Avança a rodada após a revelação.

    `agree_judge` só é relevante quando houve divergência entre a escolha do
    jogador e a do juiz: True = jogador concorda com o juiz; False = mantém a
    própria escolha. Em caso de match, pode vir None.
    """
    session_id: str
    agree_judge: Optional[bool] = None


class PassPayload(BaseModel):
    """Humano passa a vez nesta rodada (não propõe)."""
    session_id: str
    justification: Optional[str] = ""


class TelemetryPayload(BaseModel):
    """Telemetria comportamental do humano em uma submissão.

    `kind`: "idea" | "pass"
    `events`: lista de {t, k} ou {t, k:"<paste>", n}
    `metrics`: agregados calculados no front
    """
    session_id: str
    kind: str
    events: list = []
    metrics: dict = {}


class SessionOnlyPayload(BaseModel):
    """Payload genérico que carrega só o session_id (end, etc)."""
    session_id: str


class StudyStartPayload(BaseModel):
    """Inicia uma sessão sob um estudo (runner atribui a condição)."""
    study_id: str
    user_name: str
    global_llm_config: "GlobalLlmConfig"
    chosen_topic: Optional[str] = None         # quando theme.mode = choose/write
    chosen_composition: Optional[str] = None   # quando table.mode = choose


# Resolve forward ref de GlobalLlmConfig (definido em session.py)
from .session import GlobalLlmConfig  # noqa: E402
StudyStartPayload.model_rebuild()
