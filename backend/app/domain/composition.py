"""Modelos de composições de mesa (times de personas pré-definidos).

Uma composição é um arquivo YAML em `compositions/<id>.yaml` com 4
personas curadas pra um tema. O usuário escolhe no setup e o time é
carregado direto no SetupScreen.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class CompositionPersona(BaseModel):
    """Persona dentro de uma composição. Compatível com AIPersonaSetup."""
    name: str
    description: str
    role: str
    goal: str
    instructions: str
    icon: Optional[str] = None  # path/url do avatar, opcional


class Composition(BaseModel):
    """Time de personas curado pra um tema/domínio."""
    id: str
    title: str  # Nome amigável (ex: "Filósofos Clássicos")
    description: str = ""  # 1-2 linhas no card
    tags: List[str] = Field(default_factory=list)
    personas: List[CompositionPersona]
