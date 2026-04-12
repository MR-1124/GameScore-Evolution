from dataclasses import dataclass
from math import sqrt
from statistics import fmean, pstdev

from .methods import SimulationResult


@dataclass
class MatchAnalytics:
    method: str
    final_score_a: float
    final_score_b: float
    winner: str
    lead_changes: int
    avg_total_scoring_rate: float
    volatility_index: float
    comeback_index: float


@dataclass
class BenchmarkMetrics:
    method: str
    runtime_ms: float
    final_error_team_a: float
    final_error_team_b: float
    trajectory_rmse: float
    efficiency_score: float


def _count_lead_changes(score_a: list[float], score_b: list[float]) -> int:
    lead_changes = 0
    prev_sign = 0

    for a, b in zip(score_a, score_b):
        diff = a - b
        sign = 1 if diff > 0 else (-1 if diff < 0 else 0)
        if sign != 0 and prev_sign != 0 and sign != prev_sign:
            lead_changes += 1
        if sign != 0:
            prev_sign = sign

    return lead_changes


def _comeback_index(score_a: list[float], score_b: list[float]) -> float:
    deficits_a = [max(0.0, b - a) for a, b in zip(score_a, score_b)]
    deficits_b = [max(0.0, a - b) for a, b in zip(score_a, score_b)]

    max_deficit_a = max(deficits_a) if deficits_a else 0.0
    max_deficit_b = max(deficits_b) if deficits_b else 0.0

    final_diff = score_a[-1] - score_b[-1]

    if final_diff > 0:
        return min(1.0, max_deficit_a / max(score_a[-1], 1.0))
    if final_diff < 0:
        return min(1.0, max_deficit_b / max(score_b[-1], 1.0))
    return min(1.0, (max_deficit_a + max_deficit_b) / max(score_a[-1] + score_b[-1], 1.0))


def summarize(result: SimulationResult) -> MatchAnalytics:
    final_a = result.score_a[-1]
    final_b = result.score_b[-1]

    if final_a > final_b:
        winner = "Team A"
    elif final_b > final_a:
        winner = "Team B"
    else:
        winner = "Draw"

    total_scores = [a + b for a, b in zip(result.score_a, result.score_b)]
    total_rate = (total_scores[-1] - total_scores[0]) / max(result.times[-1] - result.times[0], 1e-9)
    volatility = pstdev(total_scores) / max(fmean(total_scores), 1.0)

    return MatchAnalytics(
        method=result.method,
        final_score_a=round(final_a, 2),
        final_score_b=round(final_b, 2),
        winner=winner,
        lead_changes=_count_lead_changes(result.score_a, result.score_b),
        avg_total_scoring_rate=round(total_rate, 3),
        volatility_index=round(volatility, 3),
        comeback_index=round(_comeback_index(result.score_a, result.score_b), 3),
    )


def trajectory_rmse(result: SimulationResult, ref_a: list[float], ref_b: list[float]) -> float:
    count = min(len(result.score_a), len(ref_a), len(result.score_b), len(ref_b))
    if count == 0:
        return 0.0

    sq_err = 0.0
    for i in range(count):
        da = result.score_a[i] - ref_a[i]
        db = result.score_b[i] - ref_b[i]
        sq_err += da * da + db * db

    return sqrt(sq_err / (2.0 * count))
