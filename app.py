from __future__ import annotations

from functools import partial
from time import perf_counter
from typing import Mapping

from flask import Flask, render_template, request

from game_score_evolution.analytics import BenchmarkMetrics, summarize, trajectory_rmse
from game_score_evolution.methods import NumericalMethods
from game_score_evolution.model import MatchParams, TeamDynamics, score_derivatives

app = Flask(__name__)


def _float(form: dict[str, str], key: str, default: float) -> float:
    try:
        return float(form.get(key, default))
    except (TypeError, ValueError):
        return default


def _int(form: dict[str, str], key: str, default: int) -> int:
    try:
        return int(float(form.get(key, default)))
    except (TypeError, ValueError):
        return default


def _sample_reference(series: list[float], refinement: int, count: int) -> list[float]:
    sampled: list[float] = []
    for i in range(count):
        idx = min(i * refinement, len(series) - 1)
        sampled.append(series[idx])
    return sampled


def _get_method_ids(form_data: Mapping[str, str] | object) -> list[str]:
    if hasattr(form_data, "getlist"):
        selected = form_data.getlist("methods")
        if selected:
            return selected
    return ["euler", "heun", "midpoint", "ralston", "ab2", "rk4"]


def simulate(form_data: Mapping[str, str] | object) -> dict:
    t0 = 0.0
    h = _float(form_data, "step_size", 0.1)
    steps = max(20, _int(form_data, "steps", 240))
    benchmark_refinement = max(2, _int(form_data, "benchmark_refinement", 5))

    team_a = TeamDynamics(
        attack=_float(form_data, "attack_a", 1.4),
        defense=_float(form_data, "defense_a", 1.0),
        momentum=_float(form_data, "momentum_a", 1.0),
        clutch=_float(form_data, "clutch_a", 0.20),
    )
    team_b = TeamDynamics(
        attack=_float(form_data, "attack_b", 1.3),
        defense=_float(form_data, "defense_b", 1.0),
        momentum=_float(form_data, "momentum_b", 1.0),
        clutch=_float(form_data, "clutch_b", 0.20),
    )

    params = MatchParams(
        team_a=team_a,
        team_b=team_b,
        score_cap=_float(form_data, "score_cap", 120.0),
        tempo=_float(form_data, "tempo", 1.0),
        pressure_strength=_float(form_data, "pressure_strength", 0.03),
        coupling=_float(form_data, "coupling", 0.02),
    )

    initial_state = (
        max(0.0, _float(form_data, "initial_a", 0.0)),
        max(0.0, _float(form_data, "initial_b", 0.0)),
    )

    method_ids = _get_method_ids(form_data)

    derivative = partial(score_derivatives, params=params)

    method_map = {
        "euler": NumericalMethods.euler,
        "heun": NumericalMethods.heun,
        "midpoint": NumericalMethods.midpoint,
        "ralston": NumericalMethods.ralston,
        "ab2": NumericalMethods.adams_bashforth2,
        "rk4": NumericalMethods.rk4,
    }

    reference = NumericalMethods.rk4(
        derivative,
        t0,
        initial_state,
        h / benchmark_refinement,
        steps * benchmark_refinement,
    )
    coarse_count = steps + 1
    ref_a = _sample_reference(reference.score_a, benchmark_refinement, coarse_count)
    ref_b = _sample_reference(reference.score_b, benchmark_refinement, coarse_count)

    simulations = []
    analytics = []
    benchmarks: list[BenchmarkMetrics] = []

    for method_id in method_ids:
        solver = method_map.get(method_id)
        if solver is None:
            continue
        start = perf_counter()
        result = solver(derivative, t0, initial_state, h, steps)
        runtime_ms = (perf_counter() - start) * 1000.0
        path_rmse = trajectory_rmse(result, ref_a, ref_b)

        final_error_a = abs(result.score_a[-1] - ref_a[-1])
        final_error_b = abs(result.score_b[-1] - ref_b[-1])
        efficiency = 1.0 / ((path_rmse + 1e-6) * (runtime_ms + 1e-6))

        simulations.append(
            {
                "method": result.method,
                "times": [round(x, 3) for x in result.times],
                "score_a": [round(x, 3) for x in result.score_a],
                "score_b": [round(x, 3) for x in result.score_b],
            }
        )
        analytics.append(summarize(result))
        benchmarks.append(
            BenchmarkMetrics(
                method=result.method,
                runtime_ms=round(runtime_ms, 4),
                final_error_team_a=round(final_error_a, 4),
                final_error_team_b=round(final_error_b, 4),
                trajectory_rmse=round(path_rmse, 4),
                efficiency_score=round(efficiency, 4),
            )
        )

    if benchmarks:
        best_accuracy = min(benchmarks, key=lambda b: b.trajectory_rmse)
        fastest = min(benchmarks, key=lambda b: b.runtime_ms)
        best_efficiency = max(benchmarks, key=lambda b: b.efficiency_score)
    else:
        best_accuracy = fastest = best_efficiency = None

    return {
        "simulations": simulations,
        "analytics": analytics,
        "benchmarks": benchmarks,
        "benchmark_summary": {
            "best_accuracy": best_accuracy,
            "fastest": fastest,
            "best_efficiency": best_efficiency,
            "reference_method": f"RK4 (h/{benchmark_refinement})",
        },
        "inputs": {
            "step_size": h,
            "steps": steps,
            "benchmark_refinement": benchmark_refinement,
            "attack_a": team_a.attack,
            "defense_a": team_a.defense,
            "momentum_a": team_a.momentum,
            "clutch_a": team_a.clutch,
            "attack_b": team_b.attack,
            "defense_b": team_b.defense,
            "momentum_b": team_b.momentum,
            "clutch_b": team_b.clutch,
            "score_cap": params.score_cap,
            "tempo": params.tempo,
            "pressure_strength": params.pressure_strength,
            "coupling": params.coupling,
            "initial_a": initial_state[0],
            "initial_b": initial_state[1],
            "methods": method_ids,
        },
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        payload = simulate(request.form)
    else:
        payload = simulate(request.args)

    return render_template("index.html", **payload)


if __name__ == "__main__":
    app.run(debug=True)
