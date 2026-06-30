"""Engine de rodadas (v2).

A v2 colapsou os 4 atos num contador linear de N rodadas. Mantemos o nome
`PhaseEngine` e a superfície de propriedades que o `game_service` consome
(`current_phase_name`, `global_round`, `phase_round`, `total_rounds_in_phase`,
`is_closing`, `finished`, `advance_round`) pra minimizar churn — mas agora
só existe uma "fase" lógica de discussão, seguida de closing.
"""
from typing import Optional, Tuple


class PhaseEngine:
    def __init__(self, total_rounds: int):
        self.total_rounds = max(1, int(total_rounds))
        self.global_round = 1
        self.finished = False

    # ------ leitura (compat com o serviço) ------
    @property
    def current_phase_name(self) -> str:
        return "closing" if self.finished else "discussion"

    @property
    def phase_round(self) -> int:
        return self.global_round

    @property
    def total_rounds_in_phase(self) -> int:
        return self.total_rounds

    @property
    def is_closing(self) -> bool:
        return self.finished

    # ------ transições ------
    def advance_round(self) -> Tuple[Optional[str], Optional[str]]:
        """Avança 1 rodada. Devolve (from_phase, to_phase).

        Enquanto houver rodadas, segue em 'discussion'. Na última, marca
        finished e sinaliza transição pra 'closing'.
        """
        if self.finished:
            return None, None
        if self.global_round < self.total_rounds:
            self.global_round += 1
            return None, None
        # Última rodada concluída → closing
        self.finished = True
        return "discussion", "closing"

    # ------ serialização ------
    def to_dict(self) -> dict:
        return {
            "global_round": self.global_round,
            "total_rounds": self.total_rounds,
            "phase_name": self.current_phase_name,
            "is_closing": self.is_closing,
            "finished": self.finished,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PhaseEngine":
        engine = cls(d.get("total_rounds", 4))
        engine.global_round = d.get("global_round", 1)
        engine.finished = d.get("finished", False)
        return engine
