from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from .persona import AIPersonaSetup, LlmOverride
from .player import Player
from .round import ChatMessage, ChoiceOption, IdeaProposal, RoundReveal


class GlobalLlmConfig(BaseModel):
    provider: str
    model: str
    apiKey: Optional[str] = None


class SetupPayload(BaseModel):
    user_name: str
    idea_topic: str
    ai_personas: List[AIPersonaSetup]
    global_llm_config: GlobalLlmConfig
    protocol_id: Optional[str] = "default"
    composition_id: Optional[str] = None


class GameState(BaseModel):
    session_id: str
    topic: str
    players: List[Player]
    global_llm_config: GlobalLlmConfig
    # Modelo próprio do juiz (usado pelo model_pairing da simulação); None = global.
    judge_llm_override: Optional[LlmOverride] = None
    conversation: List[ChatMessage] = []

    # Rodada global (1-based)
    round: int = 1
    total_rounds: int = 4

    # Fase do jogo (v2):
    #  - proposing: jogador escreve a ideia (cego às ideias de IA da rodada)
    #  - choosing : todas as ideias reveladas ANÔNIMAS; jogador escolhe a melhor
    #  - revealing: autoria + escolha do juiz reveladas; aguarda avançar
    #  - finished : jogo encerrado
    game_phase: Literal["proposing", "choosing", "revealing", "finished"] = "proposing"

    # phase_name mantido por compat de UI (sempre discussion/closing na v2)
    phase_name: Literal["discussion", "closing"] = "discussion"

    # Opções anônimas pra escolha do jogador (cegueira de fonte)
    choice_options: List[ChoiceOption] = []
    # Bloco de revelação (preenchido quando game_phase == "revealing")
    round_reveal: Optional[RoundReveal] = None

    # NÃO expomos current_proposals ao frontend durante a escolha (evita leak
    # de autoria); mantido vazio aqui — o working set vive no game_service.
    current_proposals: List[IdeaProposal] = []

    final_summary: Optional[str] = None
    seed: Optional[int] = None

    # Memória refletida das personas — id → "como me sinto sobre a mesa"
    persona_memos: Dict[int, str] = Field(default_factory=dict)

    # Instrumentos a aplicar (ids dos arquivos YAML, ou None)
    pre_session_instrument: Optional[str] = None
    post_session_instrument: Optional[str] = None
