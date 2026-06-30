from typing import List
from pydantic import BaseModel, Field


class LabIdea(BaseModel):
    title: str = Field(description="Título curto, profissional e cativante.")
    problem_statement: str = Field(description="Problema que a ideia resolve.")
    core_solution: str = Field(description="Como a ideia soluciona o problema.")
    key_features: List[str] = Field(description="3 a 5 funcionalidades chave.")
    target_audience: str = Field(description="Usuários ou clientes ideais.")
    potential_impact: str = Field(description="Benefício/impacto esperado.")
    next_steps: str = Field(description="Próximos passos práticos.")
