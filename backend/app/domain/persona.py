from typing import Optional
from pydantic import BaseModel


class LlmOverride(BaseModel):
    provider: str = ""
    model: str = ""
    apiKey: str = ""


class AIPersonaSetup(BaseModel):
    name: str
    description: str
    role: str
    goal: str
    instructions: str
    icon: Optional[str] = None
    llmOverride: Optional[LlmOverride] = None
