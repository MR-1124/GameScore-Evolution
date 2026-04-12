from __future__ import annotations

from functools import partial
from time import perf_counter
from typing import Mapping

from flask import Flask, render_template, request

from game_score_evolution.analytics import BenchmarkMetrics, summarize, trajectory_rmse
from game_score_evolution.methods import NumericalMethods
from game_score_evolution.model import MatchParams, TeamDynamics, score_derivatives

app = Flask(__name__)


SCENARIO_PRESETS = {
    "balanced_classic": {
        "name": "Balanced Classic",
        "description": "Even match pace with moderate pressure and stable defenses.",
        "values": {
            "step_size": 0.1,
            "steps": 240,
            "benchmark_refinement": 5,
            "score_cap": 120,
            "tempo": 1.0,
            "pressure_strength": 0.03,
            "coupling": 0.02,
            "initial_a": 0,
            "initial_b": 0,
            "attack_a": 1.4,
            "defense_a": 1.0,
            "momentum_a": 1.0,
            "clutch_a": 0.2,
            "attack_b": 1.3,
            "defense_b": 1.0,
            "momentum_b": 1.0,
            "clutch_b": 0.2,
        },
    },
    "high_scoring_arena": {
        "name": "High Scoring Arena",
        "description": "Fast offense-heavy game with loose defensive containment.",
        "values": {
            "step_size": 0.08,
            "steps": 260,
            "benchmark_refinement": 6,
            "score_cap": 160,
            "tempo": 1.35,
            "pressure_strength": 0.018,
            "coupling": 0.013,
            "initial_a": 2,
            "initial_b": 2,
            "attack_a": 1.75,
            "defense_a": 0.85,
            "momentum_a": 1.2,
            "clutch_a": 0.3,
            "attack_b": 1.72,
            "defense_b": 0.82,
            "momentum_b": 1.18,
            "clutch_b": 0.32,
        },
    },
    "defensive_grind": {
        "name": "Defensive Grind",
        "description": "Low tempo tactical match with strong defensive suppression.",
        "values": {
            "step_size": 0.1,
            "steps": 250,
            "benchmark_refinement": 5,
            "score_cap": 95,
            "tempo": 0.78,
            "pressure_strength": 0.04,
            "coupling": 0.03,
            "initial_a": 0,
            "initial_b": 0,
            "attack_a": 1.1,
            "defense_a": 1.25,
            "momentum_a": 0.95,
            "clutch_a": 0.15,
            "attack_b": 1.06,
            "defense_b": 1.28,
            "momentum_b": 0.92,
            "clutch_b": 0.14,
        },
    },
    "late_comeback_drama": {
        "name": "Late Comeback Drama",
        "description": "Team A starts behind while clutch and momentum trigger a late surge.",
        "values": {
            "step_size": 0.09,
            "steps": 260,
            "benchmark_refinement": 6,
            "score_cap": 130,
            "tempo": 1.05,
            "pressure_strength": 0.045,
            "coupling": 0.02,
            "initial_a": 0,
            "initial_b": 8,
            "attack_a": 1.5,
            "defense_a": 1.02,
            "momentum_a": 1.2,
            "clutch_a": 0.42,
            "attack_b": 1.35,
            "defense_b": 1.08,
            "momentum_b": 0.95,
            "clutch_b": 0.18,
        },
    },
}


METHOD_CATALOG = [
    {
        "id": "euler",
        "label": "Euler",
        "order": "1st",
        "description": "Baseline first-order explicit method with lowest compute cost.",
    },
    {
        "id": "heun",
        "label": "Heun",
        "order": "2nd",
        "description": "Improved Euler predictor-corrector for stronger stability.",
    },
    {
        "id": "midpoint",
        "label": "Midpoint RK2",
        "order": "2nd",
        "description": "Uses midpoint slope estimate to reduce local truncation error.",
    },
    {
        "id": "ralston",
        "label": "Ralston RK2",
        "order": "2nd",
        "description": "Weighted RK2 variant optimized for lower error constants.",
    },
    {
        "id": "ab2",
        "label": "Adams-Bashforth 2",
        "order": "2-step",
        "description": "Multistep explicit method reusing previous derivative information.",
    },
    {
        "id": "rk4",
        "label": "Runge-Kutta 4",
        "order": "4th",
        "description": "High-fidelity reference-grade solver with four slope evaluations.",
    },
]


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


def _scenario_key(form_data: Mapping[str, str] | object) -> str:
    default_key = "balanced_classic"
    if hasattr(form_data, "get"):
        selected = form_data.get("scenario", default_key)
        if isinstance(selected, str) and selected in SCENARIO_PRESETS:
            return selected
    return default_key


def _get_method_ids(form_data: Mapping[str, str] | object) -> list[str]:
    if hasattr(form_data, "getlist"):
        selected = form_data.getlist("methods")
        if selected:
            return selected
    return ["euler", "heun", "midpoint", "ralston", "ab2", "rk4"]


def simulate(form_data: Mapping[str, str] | object) -> dict:
    selected_scenario = _scenario_key(form_data)
    defaults = SCENARIO_PRESETS[selected_scenario]["values"]

    t0 = 0.0
    h = _float(form_data, "step_size", defaults["step_size"])
    steps = max(20, _int(form_data, "steps", defaults["steps"]))
    benchmark_refinement = max(2, _int(form_data, "benchmark_refinement", defaults["benchmark_refinement"]))

    team_a = TeamDynamics(
        attack=_float(form_data, "attack_a", defaults["attack_a"]),
        defense=_float(form_data, "defense_a", defaults["defense_a"]),
        momentum=_float(form_data, "momentum_a", defaults["momentum_a"]),
        clutch=_float(form_data, "clutch_a", defaults["clutch_a"]),
    )
    team_b = TeamDynamics(
        attack=_float(form_data, "attack_b", defaults["attack_b"]),
        defense=_float(form_data, "defense_b", defaults["defense_b"]),
        momentum=_float(form_data, "momentum_b", defaults["momentum_b"]),
        clutch=_float(form_data, "clutch_b", defaults["clutch_b"]),
    )

    params = MatchParams(
        team_a=team_a,
        team_b=team_b,
        score_cap=_float(form_data, "score_cap", defaults["score_cap"]),
        tempo=_float(form_data, "tempo", defaults["tempo"]),
        pressure_strength=_float(form_data, "pressure_strength", defaults["pressure_strength"]),
        coupling=_float(form_data, "coupling", defaults["coupling"]),
    )

    initial_state = (
        max(0.0, _float(form_data, "initial_a", defaults["initial_a"])),
        max(0.0, _float(form_data, "initial_b", defaults["initial_b"])),
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
            "scenario": selected_scenario,
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
        "scenario_presets": SCENARIO_PRESETS,
        "method_catalog": METHOD_CATALOG,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        payload = simulate(request.form)
    else:
        payload = simulate(request.args)

    return render_template("index.html", **payload)


@app.route("/presentation", methods=["GET"])
def presentation():
    payload = simulate(request.args)
    return render_template("presentation.html", **payload)


@app.route("/study-guide", methods=["GET"])
def study_guide():
    payload = simulate(request.args)
    return render_template("study_guide.html", **payload)


@app.route("/technical-reference", methods=["GET"])
def technical_reference():
    payload = simulate(request.args)
    return render_template("technical_reference.html", **payload)


if __name__ == "__main__":
    app.run(debug=True)
