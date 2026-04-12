from dataclasses import dataclass
from typing import Callable


State = tuple[float, float]
DerivativeFn = Callable[[float, State], State]


@dataclass
class SimulationResult:
    method: str
    times: list[float]
    score_a: list[float]
    score_b: list[float]


def _clip_state(y: State) -> State:
    return max(0.0, y[0]), max(0.0, y[1])


def _integrate(
    method_name: str,
    step_fn: Callable[[DerivativeFn, float, State, float], State],
    f: DerivativeFn,
    t0: float,
    y0: State,
    h: float,
    steps: int,
) -> SimulationResult:
    times = [t0]
    y = _clip_state(y0)
    a_scores = [y[0]]
    b_scores = [y[1]]
    t = t0

    for _ in range(steps):
        y = _clip_state(step_fn(f, t, y, h))
        t += h
        times.append(t)
        a_scores.append(y[0])
        b_scores.append(y[1])

    return SimulationResult(method_name, times, a_scores, b_scores)


class NumericalMethods:
    """Collection of explicit ODE solvers for score evolution."""

    @staticmethod
    def _euler_step(f: DerivativeFn, t: float, y: State, h: float) -> State:
        dy = f(t, y)
        return y[0] + h * dy[0], y[1] + h * dy[1]

    @staticmethod
    def _heun_step(f: DerivativeFn, t: float, y: State, h: float) -> State:
        k1 = f(t, y)
        predictor = (y[0] + h * k1[0], y[1] + h * k1[1])
        k2 = f(t + h, predictor)
        return (
            y[0] + (h / 2.0) * (k1[0] + k2[0]),
            y[1] + (h / 2.0) * (k1[1] + k2[1]),
        )

    @staticmethod
    def _midpoint_step(f: DerivativeFn, t: float, y: State, h: float) -> State:
        k1 = f(t, y)
        mid = (y[0] + 0.5 * h * k1[0], y[1] + 0.5 * h * k1[1])
        k2 = f(t + h / 2.0, mid)
        return y[0] + h * k2[0], y[1] + h * k2[1]

    @staticmethod
    def _ralston_step(f: DerivativeFn, t: float, y: State, h: float) -> State:
        k1 = f(t, y)
        y2 = (y[0] + 0.75 * h * k1[0], y[1] + 0.75 * h * k1[1])
        k2 = f(t + 0.75 * h, y2)
        return (
            y[0] + h * ((1.0 / 3.0) * k1[0] + (2.0 / 3.0) * k2[0]),
            y[1] + h * ((1.0 / 3.0) * k1[1] + (2.0 / 3.0) * k2[1]),
        )

    @staticmethod
    def _rk4_step(f: DerivativeFn, t: float, y: State, h: float) -> State:
        k1 = f(t, y)
        k2 = f(t + h / 2.0, (y[0] + h * k1[0] / 2.0, y[1] + h * k1[1] / 2.0))
        k3 = f(t + h / 2.0, (y[0] + h * k2[0] / 2.0, y[1] + h * k2[1] / 2.0))
        k4 = f(t + h, (y[0] + h * k3[0], y[1] + h * k3[1]))
        return (
            y[0] + (h / 6.0) * (k1[0] + 2.0 * k2[0] + 2.0 * k3[0] + k4[0]),
            y[1] + (h / 6.0) * (k1[1] + 2.0 * k2[1] + 2.0 * k3[1] + k4[1]),
        )

    @staticmethod
    def euler(f: DerivativeFn, t0: float, y0: State, h: float, steps: int) -> SimulationResult:
        return _integrate("Euler", NumericalMethods._euler_step, f, t0, y0, h, steps)

    @staticmethod
    def heun(f: DerivativeFn, t0: float, y0: State, h: float, steps: int) -> SimulationResult:
        return _integrate("Heun", NumericalMethods._heun_step, f, t0, y0, h, steps)

    @staticmethod
    def midpoint(f: DerivativeFn, t0: float, y0: State, h: float, steps: int) -> SimulationResult:
        return _integrate("Midpoint", NumericalMethods._midpoint_step, f, t0, y0, h, steps)

    @staticmethod
    def ralston(f: DerivativeFn, t0: float, y0: State, h: float, steps: int) -> SimulationResult:
        return _integrate("Ralston", NumericalMethods._ralston_step, f, t0, y0, h, steps)

    @staticmethod
    def rk4(f: DerivativeFn, t0: float, y0: State, h: float, steps: int) -> SimulationResult:
        return _integrate("RK4", NumericalMethods._rk4_step, f, t0, y0, h, steps)

    @staticmethod
    def adams_bashforth2(f: DerivativeFn, t0: float, y0: State, h: float, steps: int) -> SimulationResult:
        times = [t0]
        y = _clip_state(y0)
        a_scores = [y[0]]
        b_scores = [y[1]]

        if steps <= 0:
            return SimulationResult("Adams-Bashforth 2", times, a_scores, b_scores)

        t = t0
        y1 = _clip_state(NumericalMethods._heun_step(f, t, y, h))
        t += h
        times.append(t)
        a_scores.append(y1[0])
        b_scores.append(y1[1])

        prev = y
        curr = y1

        for _ in range(1, steps):
            fn = f(t, curr)
            fnm1 = f(t - h, prev)
            next_state = (
                curr[0] + h * (1.5 * fn[0] - 0.5 * fnm1[0]),
                curr[1] + h * (1.5 * fn[1] - 0.5 * fnm1[1]),
            )
            prev, curr = curr, _clip_state(next_state)
            t += h
            times.append(t)
            a_scores.append(curr[0])
            b_scores.append(curr[1])

        return SimulationResult("Adams-Bashforth 2", times, a_scores, b_scores)
