from pydantic import BaseModel, Field
from .persona import AIPersonaSetup


class Player(BaseModel):
    id: int = Field(..., description="Identificador único do jogador na mesa (1 a 5)")
    name: str = Field(..., description="Nome do jogador ou da IA")
    persona: AIPersonaSetup
    is_ai: bool = Field(default=True)
    balance: float = Field(default=1000.0)
    drinks: int = Field(default=0)
