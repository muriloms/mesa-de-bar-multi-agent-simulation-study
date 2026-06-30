"""Study — desenho experimental que orquestra braços, tópicos e composições.

Um estudo lista as condições (braços = protocolos), um banco de tópicos e um
conjunto de composições de mesa. O runner atribui cada participante a uma
célula (braço × tópico × composição) de forma BALANCEADA (round-robin pelo
menos-preenchido), registrando num ledger append-only pra reprodutibilidade.

Tópico/composição podem ser fixos (1 item) ou variáveis (N itens, balanceados).
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Study(BaseModel):
    id: str
    title: str = ""
    description: str = ""

    # Braços = ids de protocolos em protocols/<id>.yaml
    arms: List[str] = Field(..., min_length=1)

    # Banco de tópicos padronizados (comparabilidade entre braços)
    topics: List[str] = Field(default_factory=list)

    # Composições de mesa a balancear (ids em compositions/<id>.yaml).
    # Vazio = não controla composição (usa a do protocolo/manual).
    compositions: List[str] = Field(default_factory=list)

    # Estratégia de atribuição
    assignment: Literal["balanced", "random"] = "balanced"

    # Single-blind: participante não vê/escolhe a condição
    blind_condition: bool = True


class Assignment(BaseModel):
    """Registro append-only de uma atribuição feita pelo runner."""
    assignment_id: str
    study_id: str
    session_id: Optional[str] = None
    timestamp: str
    arm: str                       # protocol_id atribuído
    topic: Optional[str] = None
    composition: Optional[str] = None
    strategy: str = "balanced"
    cell: str = ""                 # chave da célula (arm|topic|composition) p/ balanceamento
