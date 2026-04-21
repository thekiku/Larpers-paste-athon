from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringConfig:
    alpha: float = 1.0
    beta: float = 1e-9
    gamma: float = 1.0


SCORING_CONFIG = ScoringConfig()
