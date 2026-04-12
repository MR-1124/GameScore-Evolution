(() => {
  const simulations = window.simulations || [];
  const benchmarks = window.benchmarks || [];
  const scenarioPresets = window.scenarioPresets || {};

  const scenarioButtons = Array.from(document.querySelectorAll(".scenario-card"));
  const scenarioInput = document.getElementById("scenarioInput");
  const methodChecks = Array.from(document.querySelectorAll(".method-check"));

  const setMethodCardState = () => {
    methodChecks.forEach((checkbox) => {
      const card = checkbox.closest(".method-card");
      if (!card) {
        return;
      }
      card.classList.toggle("selected", checkbox.checked);
    });
  };

  const applyScenarioValues = (scenarioKey) => {
    const scenario = scenarioPresets[scenarioKey];
    if (!scenario || !scenario.values) {
      return;
    }

    Object.entries(scenario.values).forEach(([name, value]) => {
      const input = document.querySelector(`[name="${name}"]`);
      if (input) {
        input.value = value;
      }
    });

    if (scenarioInput) {
      scenarioInput.value = scenarioKey;
    }

    scenarioButtons.forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.scenarioKey === scenarioKey);
    });
  };

  methodChecks.forEach((checkbox) => {
    checkbox.addEventListener("change", setMethodCardState);
  });
  setMethodCardState();

  scenarioButtons.forEach((btn) => {
    btn.addEventListener("click", () => applyScenarioValues(btn.dataset.scenarioKey));
  });

  const ctx = document.getElementById("scoreChart");
  if (!ctx || simulations.length === 0) {
    return;
  }

  const colorCache = new Map();

  const hashToHue = (text) => {
    let hash = 0;
    for (let i = 0; i < text.length; i += 1) {
      hash = (hash * 31 + text.charCodeAt(i)) % 360;
    }
    return hash;
  };

  const methodColor = (method) => {
    if (!colorCache.has(method)) {
      const hue = hashToHue(method);
      colorCache.set(method, {
        base: `hsl(${hue} 68% 42%)`,
        soft: `hsla(${hue} 68% 42% / 0.72)`,
        strong: `hsla(${hue} 68% 42% / 0.95)`,
      });
    }
    return colorCache.get(method);
  };

  const datasets = [];
  simulations.forEach((sim, i) => {
    const tone = methodColor(sim.method);
    datasets.push({
      label: `${sim.method} - Team A`,
      data: sim.score_a,
      borderColor: tone.strong,
      backgroundColor: tone.strong,
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.2,
    });
    datasets.push({
      label: `${sim.method} - Team B`,
      data: sim.score_b,
      borderColor: tone.soft,
      borderDash: [7, 4],
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.2,
    });
  });

  const labels = simulations[0].times;

  // Stagger chart fade to make the dashboard feel dynamic.
  ctx.style.opacity = 0;
  ctx.style.transform = "translateY(8px)";
  setTimeout(() => {
    ctx.style.transition = "opacity 600ms ease, transform 600ms ease";
    ctx.style.opacity = 1;
    ctx.style.transform = "translateY(0)";
  }, 50);

  new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          labels: {
            boxWidth: 16,
            usePointStyle: true,
            pointStyle: "line",
          },
        },
        tooltip: {
          callbacks: {
            title(items) {
              return `t = ${items[0].label}`;
            },
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: "Time" },
          grid: { color: "rgba(15, 31, 47, 0.08)" },
        },
        y: {
          title: { display: true, text: "Score" },
          grid: { color: "rgba(15, 31, 47, 0.08)" },
        },
      },
    },
  });

  const btx = document.getElementById("benchmarkChart");
  if (!btx || benchmarks.length === 0) {
    return;
  }

  const methodLabels = benchmarks.map((x) => x.method);
  const runtime = benchmarks.map((x) => x.runtime_ms);
  const rmse = benchmarks.map((x) => x.trajectory_rmse);

  new Chart(btx, {
    data: {
      labels: methodLabels,
      datasets: [
        {
          type: "bar",
          label: "Runtime (ms)",
          data: runtime,
          backgroundColor: "rgba(12, 125, 115, 0.65)",
          borderRadius: 8,
          yAxisID: "y",
        },
        {
          type: "line",
          label: "Trajectory RMSE",
          data: rmse,
          borderColor: "#d2641a",
          backgroundColor: "#d2641a",
          borderWidth: 2,
          pointRadius: 3,
          yAxisID: "y1",
          tension: 0.28,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top" },
      },
      scales: {
        y: {
          position: "left",
          title: { display: true, text: "Runtime (ms)" },
          grid: { color: "rgba(15, 31, 47, 0.08)" },
        },
        y1: {
          position: "right",
          title: { display: true, text: "RMSE" },
          grid: { drawOnChartArea: false },
        },
      },
    },
  });
})();
