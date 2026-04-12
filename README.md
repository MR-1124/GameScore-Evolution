# 🎮 Game Score Evolution Simulator

A Numerical Methods academic project that models competitive game scoring as a **coupled ODE system** and compares **six numerical solvers** on accuracy, speed, and efficiency — with interactive visualization, detailed benchmarking, and comprehensive educational documentation.

---

## 📋 Project Summary

| Area | Detail |
|------|--------|
| **Subject** | Numerical Methods |
| **Theme** | Game Score Evolution + Game Analytics |
| **Core Math** | Coupled Nonlinear Ordinary Differential Equations (ODEs) |
| **Solvers** | Euler, Heun, Midpoint, Ralston, Adams-Bashforth 2, RK4 |
| **Tech Stack** | Python, Flask, Jinja2, Chart.js |
| **Pages** | Simulator Dashboard, Presentation Deck, Study Guide, Technical Reference |

---

## 🧠 Why This Project Matters

In competitive games, scoring is never linear — teams experience momentum swings, defensive tightening, comeback pressure, and clutch moments. This project models those dynamics mathematically using coupled ODEs and lets you **see** how different numerical solvers handle the same nonlinear system differently.

**Key academic value:**
- Applies abstract numerical methods to a tangible, relatable domain
- All 6 solvers are **hand-implemented from scratch** — no SciPy, no black boxes
- Produces **quantitative benchmark data** (RMSE, runtime, efficiency) for critical analysis
- Demonstrates model flexibility through 4 scenario presets with no code changes
- Full-stack application: math → backend → visualization pipeline

---

## 📐 ODE Model

The system tracks two scores $S_A(t)$ and $S_B(t)$ as a coupled IVP:

$$
\frac{dS_A}{dt} = \max\left(0,\; D_A \cdot P_A + C_A(t) - R_A\right)
$$

$$
\frac{dS_B}{dt} = \max\left(0,\; D_B \cdot P_B + C_B(t) - R_B\right)
$$

| Term | Name | Role |
|------|------|------|
| $D_i$ | **Saturation Drive** | `attack × momentum × tempo × max(0.05, 1 − S/cap)` — base scoring with diminishing returns |
| $P_i$ | **Competitive Pressure** | `1 ∓ pressure × (S_A − S_B)` — trailing team boosted, leading team suppressed |
| $C_i(t)$ | **Clutch Oscillation** | `clutch × sin(ωt + φ)` — periodic hot/cold streaks with phase offset |
| $R_i$ | **Defensive Drag** | `defense_opponent × coupling × S_i` — score-proportional resistance |

The `max(0, ...)` clamp ensures scores are **monotonically non-decreasing** (scores never go down).

---

## 🔬 Numerical Methods Implemented

| Method | Order | Evaluations/Step | Key Property |
|--------|-------|-----------------|--------------|
| **Euler** | 1st | 1 | Simplest baseline — one forward slope |
| **Heun** (Improved Euler) | 2nd | 2 | Predictor-corrector averaging start + end slopes |
| **Midpoint** (RK2) | 2nd | 2 | Uses midpoint slope for full step |
| **Ralston** (Optimized RK2) | 2nd | 2 | Minimized error constant via optimized weights |
| **Adams-Bashforth 2** | 2nd | 1* | Multistep: reuses previous derivative, bootstraps with Heun |
| **RK4** | 4th | 4 | Gold standard — 1:2:2:1 weighted slopes |

\* AB2 uses 1 new evaluation per step after the Heun bootstrap step.

---

## ✨ Features

### Simulator Dashboard (`/`)
- Interactive simulation form with adjustable team & global parameters
- 4 clickable scenario presets that auto-fill parameters
- Method selection via interactive solver cards
- **Score Evolution Chart** — multi-method trajectory comparison via Chart.js
- **Benchmark Chart** — dual-axis (runtime bars + RMSE line)
- **Analytics Table** — winner, lead changes, volatility index, comeback index, avg scoring rate
- **Benchmark Table** — runtime (ms), final-score error, trajectory RMSE, efficiency score
- Fine-step RK4 reference solution for ground-truth benchmarking

### Presentation Deck (`/presentation`)
- 16-slide academic presentation with speaker notes
- Architecture diagram, ODE deep-dive, worked numerical example
- Error analysis theory, live benchmark data, real-world applications
- Comprehensive Q&A slide for viva defense

### Study Guide (`/guide`)
- 16-section deep study resource
- ODE fundamentals, model walkthrough with worked examples
- Each solver explained with intuition + formula + strengths/weaknesses
- 10 viva Q&As with confident answers, common mistakes, glossary
- Presentation speaking flow with timing guide

### Technical Reference (`/technical-reference`)
- 14-section authoritative documentation
- Full ODE derivation (6 labeled steps), all solver formulas with Python code
- Convergence order analysis, stability concepts, Adams-Bashforth deep-dive
- Complete input field specification, API reference, module-by-module code walkthrough

---

## 🎯 Scenario Presets

| Preset | What It Demonstrates |
|--------|---------------------|
| **Balanced Classic** | Fair match, steady scoring — baseline for method comparison |
| **High Scoring Arena** | Fast offense, weak defense — reveals Euler drift at high growth |
| **Defensive Grind** | Low tempo, strong defense — shows methods converge on gentle ODEs |
| **Late Comeback Drama** | Team B starts ahead, high clutch — showcases pressure + coupling effects |

---

## 📁 Project Structure

```
Game-Score/
├── app.py                          # Flask backend — routes, simulation orchestration
├── requirements.txt                # Python dependencies (Flask, gunicorn)
├── README.md
│
├── game_score_evolution/           # Core computation package
│   ├── __init__.py
│   ├── model.py                    # ODE model: TeamDynamics, MatchParams, score_derivatives()
│   ├── methods.py                  # 6 numerical solvers: Euler, Heun, Midpoint, Ralston, AB2, RK4
│   └── analytics.py                # Game analytics: lead changes, volatility, RMSE computation
│
├── templates/                      # Jinja2 HTML templates
│   ├── index.html                  # Main simulator dashboard
│   ├── presentation.html           # 16-slide presentation deck
│   ├── guide.html                  # 16-section study guide
│   └── technical_reference.html    # 14-section technical reference
│
└── static/                         # Frontend assets
    ├── style.css                   # Glassmorphic design system + educational components
    └── app.js                      # Chart.js visualization + form interactivity
```

---

## 🚀 Run Locally

**1. Clone and setup:**
```bash
git clone https://github.com/YOUR_USERNAME/Game-Score.git
cd Game-Score
python -m venv .venv
```

**2. Activate environment:**
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Start the app:**
```bash
python app.py
```

**5. Open in browser:**
```
http://127.0.0.1:5000
```

---

## 🌐 Deploy Online

The app is production-ready with `gunicorn`. Deploy to any of these free platforms:

| Platform | Start Command | Free Tier |
|----------|--------------|-----------|
| [Render](https://render.com) | `gunicorn app:app` | ✅ |
| [Railway](https://railway.app) | `gunicorn app:app --bind 0.0.0.0:$PORT` | ✅ |
| [PythonAnywhere](https://pythonanywhere.com) | WSGI config | ✅ |

---

## 📊 Benchmark Metrics

| Metric | Formula | Purpose |
|--------|---------|---------|
| **Trajectory RMSE** | `√(1/(2N) × Σ[(A−A_ref)² + (B−B_ref)²])` | Path accuracy over entire simulation |
| **Final-Score Error** | `\|S_final − S_ref_final\|` | Endpoint accuracy |
| **Runtime** | `perf_counter()` timing in ms | Computational speed |
| **Efficiency Score** | `1 / ((RMSE + ε) × (runtime + ε))` | Speed-accuracy trade-off |

Reference solution: RK4 at `h/refinement` step size (default 5× finer).

---

## 🎓 Presentation Flow (Viva/Demo)

1. **Introduce** the project: ODE-based game score modeling + numerical method comparison
2. **Show the model**: Walk through drive → pressure → clutch → drag → assembly
3. **Demonstrate scenarios**: Switch presets to prove model flexibility
4. **Run live simulation**: Select methods, run, show evolution + benchmark charts
5. **Analyze results**: Point to RMSE, runtime, efficiency — discuss trade-offs
6. **Highlight key finding**: Different methods can predict different winners
7. **Address limitations**: Deterministic, fixed params, no adaptive stepping
8. **Conclude**: Solver choice is a consequential engineering decision

---

## 🔮 Future Enhancements

- **Stochastic Differential Equations (SDEs)** — noise terms for game unpredictability
- **Adaptive step-size control (RK45)** — automatic step adjustment based on estimated error
- **Time-varying parameters** — fatigue curves, tactical changes mid-match
- **Implicit methods** — backward Euler, BDF for stiff system comparison
- **ML calibration** — train parameters from real game data
- **Multi-team tournaments** — bracket simulation with round-robin/elimination

---

## 📄 License

This project is developed for academic purposes.
