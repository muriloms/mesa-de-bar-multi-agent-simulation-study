"""Protocol — configuração de um estudo (v2).

Mudanças da v2 vs Fase 2B:
- Fases colapsadas em `rounds: int` (default 4). Sem 4 atos, sem aposta.
- Economia removida (sem apostas, sem drinks, temperatura fixa).
- `quem_avanca`: qual ideia segue pra mesa a cada rodada (juiz_ia | jogador).
- `judge`: o antigo Garçom, renomeado — escolhe a melhor ideia toda rodada.
- `source_blind_on_choice`: ideias mostradas anônimas na hora de escolher,
  autoria revelada depois (mede viés de fonte).
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Juiz (antigo Garçom) — escolhe a melhor ideia a cada rodada
# ---------------------------------------------------------------------------
class JudgeConfig(BaseModel):
    """Configuração do Juiz IA."""
    criterion: Literal["originalidade", "viabilidade", "interesse", "composto"] = Field(
        default="originalidade",
        description="Critério explícito que o juiz usa pra escolher a melhor ideia.",
    )
    blind_to_source: bool = Field(
        default=True,
        description="Se True, o juiz não vê a autoria das ideias (só os textos).",
    )


# ---------------------------------------------------------------------------
# Owner (Dono do Bar) — síntese final
# ---------------------------------------------------------------------------
class OwnerConfig(BaseModel):
    bias: Literal["neutral", "pro_human"] = "neutral"


# ---------------------------------------------------------------------------
# Memory — como personas mantêm contexto entre rodadas
# ---------------------------------------------------------------------------
class MemoryConfig(BaseModel):
    mode: Literal["none", "private_memo", "reflected_summary"] = "reflected_summary"


# ---------------------------------------------------------------------------
# Telemetry — telemetria comportamental do humano
# ---------------------------------------------------------------------------
class TelemetryConfig(BaseModel):
    capture_keystrokes: bool = True
    aggregate_metrics: bool = True


# ---------------------------------------------------------------------------
# Display — manipulações de apresentação
# ---------------------------------------------------------------------------
class DisplayConfig(BaseModel):
    """Manipulações experimentais de apresentação.

    `blind_personas`: nomes/roles das personas viram "Persona A", "B"... pro
                     humano durante toda a sessão (dados internos preservados).
    `solo_baseline`: humano joga sozinho (0 IAs). Controle científico.
    """
    blind_personas: bool = False
    solo_baseline: bool = False


# ---------------------------------------------------------------------------
# Instruments
# ---------------------------------------------------------------------------
class InstrumentsConfig(BaseModel):
    pre_session: Optional[str] = None
    post_session: Optional[str] = None
    post_round: Optional[str] = None


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------
QuemAvanca = Literal["juiz_ia", "jogador"]


class Protocol(BaseModel):
    id: str
    version: str = "3.0.0"
    description: str = ""

    language: Literal["pt", "en"] = "pt"

    # LLM defaults — temperatura FIXA (sem economia de drinks)
    llm_default_provider: str = "google"
    llm_default_model: str = "gemini-1.5-flash"
    llm_temperature: float = 0.7

    # Reprodutibilidade
    llm_seed_strategy: str = "random_logged"
    randomization_seed: Optional[int] = None

    # Estrutura do jogo — N rodadas (colapsou os 4 atos)
    rounds: int = Field(default=4, ge=1, description="Número de rodadas da sessão.")

    # Manipulação de raciocínio das personas (CoT vs direto).
    # cot: a persona raciocina brevemente antes de propor (raciocínio é logado,
    # não exibido na mesa). Gancho com a hipótese de homogeneização/fixação.
    reasoning_mode: Literal["direct", "cot"] = Field(
        default="direct",
        description="Modo de raciocínio das personas ao propor (direct | cot).",
    )

    # Manipulações experimentais centrais da v2
    quem_avanca: QuemAvanca = Field(
        default="juiz_ia",
        description="Qual ideia segue pra mesa: a escolha do juiz IA ou a do jogador.",
    )
    source_blind_on_choice: bool = Field(
        default=True,
        description="Ideias anônimas na hora de escolher; autoria revelada depois.",
    )

    # Subsistemas
    judge: JudgeConfig = Field(default_factory=JudgeConfig)
    owner: OwnerConfig = Field(default_factory=OwnerConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    instruments: InstrumentsConfig = Field(default_factory=InstrumentsConfig)
    display: DisplayConfig = Field(default_factory=DisplayConfig)
