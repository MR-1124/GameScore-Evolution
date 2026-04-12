from dataclasses import dataclass
from math import sin


@dataclass
class TeamDynamics:
    """Per-team coefficients controlling scoring behavior."""

    attack: float = 1.2
    defense: float = 1.0
    momentum: float = 1.0
    clutch: float = 0.25


@dataclass
class MatchParams:
    """Global ODE parameters for a match simulation."""

    team_a: TeamDynamics
    team_b: TeamDynamics
    score_cap: float = 120.0
    tempo: float = 1.0
    pressure_strength: float = 0.03
    coupling: float = 0.02


def _drive_term(attack: float, momentum: float, score: float, cap: float, tempo: float) -> float:
    """Base scoring drive with mild saturation as score approaches cap."""

    saturation = max(0.05, 1.0 - (score / max(cap, 1.0)))
    return attack * momentum * tempo * saturation


def score_derivatives(t: float, state: tuple[float, float], params: MatchParams) -> tuple[float, float]:
    """Coupled ODE system for Team A and Team B score dynamics."""

    score_a, score_b = state

    lead = score_a - score_b
    pressure_a = 1.0 - params.pressure_strength * lead
    pressure_b = 1.0 + params.pressure_strength * lead

    drive_a = _drive_term(
        params.team_a.attack,
        params.team_a.momentum,
        score_a,
        params.score_cap,
        params.tempo,
    )
    drive_b = _drive_term(
        params.team_b.attack,
        params.team_b.momentum,
        score_b,
        params.score_cap,
        params.tempo,
    )

    # Periodic clutch term models end-to-end runs and match swings.
    clutch_a = params.team_a.clutch * sin(t * 0.9)
    clutch_b = params.team_b.clutch * sin(t * 0.9 + 1.1)

    defense_drag_a = params.team_b.defense * params.coupling * max(score_a, 0.0)
    defense_drag_b = params.team_a.defense * params.coupling * max(score_b, 0.0)

    d_score_a = max(0.0, drive_a * pressure_a + clutch_a - defense_drag_a)
    d_score_b = max(0.0, drive_b * pressure_b + clutch_b - defense_drag_b)

    return d_score_a, d_score_b
