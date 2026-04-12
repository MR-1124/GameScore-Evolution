# Game Score Evolution Simulator

A Numerical Methods project that models game score dynamics as a coupled ODE system and compares multiple solvers for sports/game balancing analysis.

## Topic Alignment

- **Subject**: Numerical Methods
- **Project Theme**: Game Score Evolution Simulator + Game Analytics
- **Core Math**: Coupled Ordinary Differential Equations (ODE)
- **Implemented Methods**:
  - Euler Method
  - Heun Method (Improved Euler)
  - Midpoint Method (RK2)
  - Ralston Method (RK2 optimized weights)
  - Adams-Bashforth 2-step Method (AB2)
  - RK4 (Runge-Kutta 4th order)
- **Platform**: Python + Flask Web App

## Why this is meaningful

This project demonstrates how different numerical methods affect prediction quality for nonlinear systems. In game balancing, score progression is not linear: pressure, momentum, defense, and clutch effects create dynamic swings. The simulator helps compare model behavior and method sensitivity for balancing decisions.

## ODE Model

Let $S_A(t)$ and $S_B(t)$ be Team A and Team B scores:

$$
\frac{dS_A}{dt} = \max\left(0, D_A(S_A)\cdot P_A(\Delta S) + C_A(t) - R_A(S_A)\right)
$$

$$
\frac{dS_B}{dt} = \max\left(0, D_B(S_B)\cdot P_B(\Delta S) + C_B(t) - R_B(S_B)\right)
$$

Where:
- $D_i$ is scoring drive from attack, momentum, tempo, and saturation
- $P_i$ is pressure term driven by lead difference $\Delta S = S_A - S_B$
- $C_i(t)$ is periodic clutch/run factor
- $R_i$ is defensive drag from opponent coupling

## Features

- Adjustable team coefficients (attack, defense, momentum, clutch)
- Global parameters (tempo, pressure strength, defensive coupling, score cap)
- Method selection via checkboxes
- Built-in benchmark reference with fine-step RK4
- Line chart comparing score evolution per method for Team A and Team B
- Benchmark chart (runtime vs trajectory RMSE)
- Analytics table with:
  - Final score
  - Winner
  - Lead changes
  - Average scoring rate
  - Volatility index
  - Comeback index
- Benchmark metrics table with:
  - Runtime in milliseconds
  - Final score error vs reference (Team A and Team B)
  - Trajectory RMSE
  - Efficiency score
- Responsive, presentation-friendly UI

## Project Structure

```
Game-Score/
├─ app.py
├─ requirements.txt
├─ game_score_evolution/
│  ├─ __init__.py
│  ├─ model.py
│  ├─ methods.py
│  └─ analytics.py
├─ templates/
│  └─ index.html
└─ static/
   ├─ style.css
   └─ app.js
```

## Run Locally

1. Create virtual environment:

```bash
python -m venv .venv
```

2. Activate environment:

```bash
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start app:

```bash
python app.py
```

5. Open browser:

- http://127.0.0.1:5000

## Presentation Flow (for viva/demo)

1. Explain the ODE assumptions and parameters.
2. Run with the same step size across all selected methods.
3. Use benchmark refinement to generate the RK4 fine-step reference.
4. Show divergence/consistency between methods with RMSE.
5. Discuss runtime vs accuracy using the benchmark chart.
4. Discuss trade-off:
   - Euler: simplest, lower accuracy for nonlinear dynamics
   - Heun: moderate cost, improved stability
  - Midpoint/Ralston: strong RK2 alternatives for better accuracy than Euler
  - AB2: multistep approach with low per-step cost after startup
   - RK4: best accuracy, higher compute per step
6. Use gameplay analytics metrics to justify balancing interpretation.

## Suggested Extensions

- Add Monte Carlo noise for stochastic events (injuries, power-ups, random crits)
- Add error analysis against a reference method with very small step size
- Export simulation runs to CSV
- Add parameter presets for different game genres (MOBA, FPS, Basketball)
