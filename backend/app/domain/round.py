from typing import List, Literal, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    player_id: int
    player_name: str
    message: str


# Stance: postura tomada pela IA em relação à conversa atual.
#  - complement: complementa/aprofunda uma ideia anterior
#  - counter: contesta ou apresenta contraponto
#  - redirect: muda o ângulo / propõe direção nova
StanceType = Literal["complement", "counter", "redirect"]


class IdeaProposal(BaseModel):
    """Uma ideia proposta numa rodada (humano ou IA). Sem aposta na v2."""
    player_id: int
    player_name: str
    idea_text: str
    stance: Optional[StanceType] = None
    refers_to_player_id: Optional[int] = None  # quem ela está respondendo


class ChoiceOption(BaseModel):
    """Ideia apresentada ANONIMAMENTE ao jogador na hora de escolher a melhor.

    `ref` é um handle anônimo estável (ex: 'opt_1'); a autoria real é mantida
    apenas no servidor até a revelação. Isso implementa a cegueira de fonte.
    """
    ref: str
    idea_text: str


class AuthoredOption(BaseModel):
    """Opção já com autoria revelada (pós-escolha)."""
    ref: str
    player_id: int
    player_name: str
    idea_text: str
    is_ai: bool


class RoundReveal(BaseModel):
    """Estado de revelação de uma rodada: autoria + escolhas + comparação."""
    options: List[AuthoredOption] = []
    player_pick_ref: Optional[str] = None
    player_pick_player_id: Optional[int] = None
    player_pick_name: Optional[str] = None
    judge_pick_player_id: Optional[int] = None
    judge_pick_name: Optional[str] = None
    judge_rationale: Optional[str] = None
    match: bool = False
    advanced_player_id: Optional[int] = None
    advanced_name: Optional[str] = None
    advanced_rule: Optional[str] = None  # "juiz_ia" | "jogador"
