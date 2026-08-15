/* ==========================================================
   AuthenChain — Analytics Dashboard
   ========================================================== */

async function loadAnalytics() {
  if (!document.getElementById("verificationTrendChart")) return;

  try {
    const [history, riskSummary] = await Promise.all([
      apiRequest("/verification/history"),
      apiRequest("/ai/risk-summary"),
    ]);

    renderVerificationTrend(history.history);
    renderDecisionChart(riskSummary.decision_distribution);
    renderRiskChart(riskSummary.risk_distribution);
    renderScanMethodChart(history.history);

    const summaryGrid = document.getElementById("analyticsSummaryGrid");
    if (summaryGrid) {
      const total = riskSummary.total;
      const counterfeitPct = total ? ((riskSummary.decision_distribution.counterfeit / total) * 100).toFixed(1) : "0.0";
      summaryGrid.innerHTML = `
        ${statCard("blue", "fa-chart-line", total, "Total Verifications")}
        ${statCard("red", "fa-triangle-exclamation", riskSummary.decision_distribution.counterfeit || 0, "Counterfeit Detections")}
        ${staticStatCard("orange", "fa-percent", counterfeitPct + "%", "Counterfeit Rate")}
        ${statCard("green", "fa-shield-halved", riskSummary.decision_distribution.genuine || 0, "Genuine Confirmations")}
      `;
      summaryGrid.querySelectorAll("[data-count]").forEach((el) => animateCount(el, parseInt(el.dataset.count)));
    }
  } catch (err) { showToast(err.message, "danger"); }
}

/* Shows a clear message in place of a chart if Chart.js didn't load, instead
   of leaving a confusing blank white box with no explanation. */
function chartFallback(canvas, hasData) {
  const wrap = canvas.closest(".panel") || canvas.parentElement;
  if (!wrap) return;
  const msg = document.createElement("div");
  msg.className = "chart-fallback-msg";
  msg.innerHTML = !window.Chart
    ? '<i class="fa-solid fa-triangle-exclamation"></i><span>Chart library failed to load (no internet connection). The underlying data is still real — reconnect and refresh to see the chart.</span>'
    : '<i class="fa-solid fa-chart-simple"></i><span>No data yet for this chart.</span>';
  canvas.style.display = "none";
  wrap.appendChild(msg);
}

function renderVerificationTrend(history) {
  const ctx = document.getElementById("verificationTrendChart");
  if (!ctx) return;
  if (!window.Chart || !history.length) return chartFallback(ctx, history.length > 0);

  // history comes back newest-first from the API — sort chronologically
  // ascending so the trend line/bars read left-to-right, oldest to newest.
  const sorted = [...history].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  const byDay = {};
  sorted.forEach((h) => {
    const day = new Date(h.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" });
    byDay[day] = (byDay[day] || 0) + 1;
  });
  const labels = Object.keys(byDay).slice(-14);

  new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Verifications",
        data: labels.map((l) => byDay[l]),
        backgroundColor: "#2952e3",
        borderRadius: 6,
      }],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });
}

function renderDecisionChart(dist) {
  const ctx = document.getElementById("decisionChart");
  if (!ctx) return;
  const total = (dist.genuine || 0) + (dist.suspicious || 0) + (dist.counterfeit || 0);
  if (!window.Chart || !total) return chartFallback(ctx, total > 0);
  new Chart(ctx, {
    type: "pie",
    data: {
      labels: ["Genuine", "Suspicious", "Counterfeit"],
      datasets: [{ data: [dist.genuine || 0, dist.suspicious || 0, dist.counterfeit || 0], backgroundColor: ["#2fd18a", "#f5a623", "#ef4460"], borderWidth: 0 }],
    },
    options: { plugins: { legend: { position: "bottom" } } },
  });
}

function renderRiskChart(dist) {
  const ctx = document.getElementById("riskChart");
  if (!ctx) return;
  const total = (dist.low || 0) + (dist.medium || 0) + (dist.high || 0);
  if (!window.Chart || !total) return chartFallback(ctx, total > 0);
  new Chart(ctx, {
    type: "polarArea",
    data: {
      labels: ["Low Risk", "Medium Risk", "High Risk"],
      datasets: [{ data: [dist.low || 0, dist.medium || 0, dist.high || 0], backgroundColor: ["rgba(47,209,138,0.75)", "rgba(245,166,35,0.75)", "rgba(239,68,96,0.75)"] }],
    },
    options: { plugins: { legend: { position: "bottom" } } },
  });
}

function renderScanMethodChart(history) {
  const ctx = document.getElementById("scanMethodChart");
  if (!ctx) return;
  const counts = { qr: 0, image: 0, camera: 0 };
  history.forEach((h) => { counts[h.scan_method] = (counts[h.scan_method] || 0) + 1; });
  const total = counts.qr + counts.image + counts.camera;
  if (!window.Chart || !total) return chartFallback(ctx, total > 0);
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["QR Scan", "Image Upload", "Camera Capture"],
      datasets: [{ data: [counts.qr, counts.image, counts.camera], backgroundColor: ["#2952e3", "#2fd18a", "#f5a623"], borderWidth: 0 }],
    },
    options: { plugins: { legend: { position: "bottom" } }, cutout: "60%" },
  });
}

document.addEventListener("DOMContentLoaded", loadAnalytics);
