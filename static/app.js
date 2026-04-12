(() => {
  const simulations = window.simulations || [];
  const benchmarks = window.benchmarks || [];
  const ctx = document.getElementById("scoreChart");
  if (!ctx || simulations.length === 0) {
    return;
  }

  const palette = [
    { a: "#0c7d73", b: "#1eaa9d" },
    { a: "#d2641a", b: "#f0932b" },
    { a: "#2d5b9f", b: "#5f84bf" },
  ];

  const datasets = [];
  simulations.forEach((sim, i) => {
    const tone = palette[i % palette.length];
    datasets.push({
      label: `${sim.method} - Team A`,
      data: sim.score_a,
      borderColor: tone.a,
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.2,
    });
    datasets.push({
      label: `${sim.method} - Team B`,
      data: sim.score_b,
      borderColor: tone.b,
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
