"""Carregador da configuração de simulação e das personas-jogador."""
from pathlib import Path
from typing import List, Optional, Union, Dict
import yaml
from pydantic import BaseModel, Field, field_validator

from core import config
from core.exceptions import MesaDeBarError


class JogadorLLM(BaseModel):
    temperature: float = 0.7
    top_p: float = 1.0
    model: Optional[str] = None


class JogadorPersona(BaseModel):
    id: str
    name: str = "Jogador"
    description: Optional[str] = None
    llm: JogadorLLM = Field(default_factory=JogadorLLM)
    profile: Optional[str] = None
    traits: Dict[str, str] = Field(default_factory=dict)


class RoleModel(BaseModel):
    provider: str = "openai"
    model: str


class RoleModels(BaseModel):
    personas: RoleModel
    judge: RoleModel
    player: RoleModel


class Condicoes(BaseModel):
    best_idea: List[str] = ["player_decides"]
    composicao: List[str] = ["random"]
    tema: List[str] = ["random"]
    rounds: List[int] = [4]
    source_blind_on_choice: List[bool] = [True]
    judge_criterion: List[str] = ["originalidade"]
    model_pairing: List[str] = ["same_model"]   # Fator D (ver model_map)


class Simulacao(BaseModel):
    run_id: Optional[str] = None
    seed: int = 12345
    n_games: int = Field(default=10, ge=1)
    jogadores: Union[str, List[str]] = "todos"
    temperaturas: List[float] = []          # cruza persona × temperatura (vazio = usa a da persona)
    condicoes: Condicoes = Field(default_factory=Condicoes)
    model_map: Dict[str, RoleModels] = {}   # pairing -> modelo por papel (ver model_pairing)
    juiz: Optional[str] = None              # id da persona do juiz (juiz/<id>.yaml)
    judge_blind_follows_choice: bool = True # acopla cegueira do juiz à da escolha
    yoked_seeds: List[str] = []             # fatores a parear (mesmo tema/personas entre níveis)
    formularios: str = "off"
    output_dir: str = "data/sim_runs"
    mark_synthetic: bool = True
    dry_run: bool = False
    max_parallel: int = Field(default=1, ge=1)

    @field_validator("formularios", mode="before")
    @classmethod
    def _coerce_formularios(cls, v):
        # YAML lê 'off' como False e 'on' como True — normaliza para string.
        if v is False:
            return "off"
        if v is True:
            return "answer"
        return str(v)


def simulacao_file() -> Path:
    return config.RESEARCH_DIR / "simulacao.yaml"


def jogadores_dir() -> Path:
    return config.RESEARCH_DIR / "jogadores_simulados"


def load_simulacao() -> Simulacao:
    path = simulacao_file()
    if not path.exists():
        return Simulacao()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise MesaDeBarError(f"Erro ao parsear {path}: {e}")
    return Simulacao(**data)


def load_jogador(jid: str) -> JogadorPersona:
    path = jogadores_dir() / f"{jid}.yaml"
    if not path.exists():
        raise MesaDeBarError(f"Persona-jogador '{jid}' não encontrada em {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return JogadorPersona(**data)


def list_jogadores() -> List[JogadorPersona]:
    d = jogadores_dir()
    if not d.exists():
        return []
    out = []
    for f in sorted(d.glob("*.yaml")):
        if f.name.startswith("_"):
            continue
        try:
            out.append(load_jogador(f.stem))
        except Exception:
            continue
    return out


def selected_jogadores(sim: Simulacao) -> List[JogadorPersona]:
    todos = list_jogadores()
    if isinstance(sim.jogadores, str) and sim.jogadores == "todos":
        return todos
    ids = sim.jogadores if isinstance(sim.jogadores, list) else [sim.jogadores]
    return [j for j in todos if j.id in ids]


def _temp_tag(t: float) -> str:
    """0.4 -> 't04', 0.7 -> 't07', 1.0 -> 't10' (combina com a convenção do usuário)."""
    return "t" + str(t).replace(".", "")


def expand_players(sim: Simulacao) -> List[JogadorPersona]:
    """População efetiva: personas-base × temperaturas (se houver).

    Sem `temperaturas`, devolve as personas-base (cada uma com a sua temperatura).
    Com `temperaturas`, cruza cada persona-base com cada temperatura, gerando um
    'indivíduo' sintético por combinação (id = '<base>_t<NN>').
    """
    base = selected_jogadores(sim)
    if not sim.temperaturas:
        return base
    out: List[JogadorPersona] = []
    for p in base:
        for t in sim.temperaturas:
            clone = p.model_copy(deep=True)
            clone.id = f"{p.id}_{_temp_tag(t)}"
            clone.name = f"{p.name} (T={t})"
            clone.llm = clone.llm.model_copy(update={"temperature": float(t)})
            out.append(clone)
    return out
