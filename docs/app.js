// Crypto Market News Analyzer — dashboard renderer
const DATA_URL = "data/analysis.json";

const COLORS = {
  bullish: "#16c784",
  bearish: "#ea3943",
  neutral: "#6b7280",
  accent: "#f0b90b",
  text: "#e6edf3",
  muted: "#8b95a5",
  grid: "#1f2733",
};

let charts = {};

async function loadData() {
  try {
    const res = await fetch(DATA_URL + "?t=" + Date.now());
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("Failed to load data:", err);
    document.getElementById("headlines").innerHTML =
      `<p class="muted">Could not load analysis.json yet. First run may still be in progress.</p>`;
    document.getElementById("updated").textContent =
      "Awaiting first run — see repo Actions tab";
    return null;
  }
}

function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function sentimentColor(label) {
  if (label === "bullish") return COLORS.bullish;
  if (label === "bearish") return COLORS.bearish;
  return COLORS.neutral;
}

function renderGauge(label, score) {
  const ctx = document.getElementById("sentimentGauge");
  const color = sentimentColor(label);
  // Score range: -1 (bear) → 0 (neutral) → +1 (bull)
  // Map to angle: -90° → 0° → 90°
  const angle = (Math.max(-1, Math.min(1, score || 0)) * 90);
  const data = {
    datasets: [{
      data: [1, 1, 1],
      backgroundColor: [COLORS.bearish, COLORS.neutral, COLORS.bullish],
      borderWidth: 0,
      cutout: "75%",
      circumference: 180,
      rotation: 270,
    }],
  };
  charts.gauge = new Chart(ctx, {
    type: "doughnut",
    data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false },
      },
    },
    plugins: [{
      id: "needle",
      afterDraw(chart) {
        const { ctx, chartArea } = chart;
        const cx = (chartArea.left + chartArea.right) / 2;
        const cy = chartArea.bottom;
        const len = (chartArea.right - chartArea.left) * 0.4;
        const rad = ((angle - 90) * Math.PI) / 180;
        const nx = cx + Math.cos(rad) * len;
        const ny = cy + Math.sin(rad) * len;
        ctx.save();
        ctx.strokeStyle = color;
        ctx.lineWidth = 4;
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(nx, ny);
        ctx.stroke();
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(cx, cy, 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      },
    }],
  });
  document.getElementById("sentimentLabel").textContent = label;
  document.getElementById("sentimentLabel").style.color = color;
  document.getElementById("sentimentScore").textContent =
    `score: ${score >= 0 ? "+" : ""}${score?.toFixed(3) ?? "—"}`;
}

function renderMixChart(distribution) {
  const ctx = document.getElementById("mixChart");
  const labels = ["bullish", "neutral", "bearish"];
  const vals = labels.map((l) => distribution[l] || 0);
  charts.mix = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: vals,
        backgroundColor: [COLORS.bullish, COLORS.neutral, COLORS.bearish],
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom", labels: { color: COLORS.text } },
      },
    },
  });
}

function renderBarChart(canvasId, items, valueKey) {
  const ctx = document.getElementById(canvasId);
  charts[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: items.map((i) => i.coin || i.topic),
      datasets: [{
        data: items.map((i) => i[valueKey]),
        backgroundColor: COLORS.accent,
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: COLORS.muted }, grid: { color: COLORS.grid } },
        y: { ticks: { color: COLORS.text }, grid: { display: false } },
      },
    },
  });
}

function renderHeadlines(articles) {
  const container = document.getElementById("headlines");
  if (!articles || articles.length === 0) {
    container.innerHTML = `<p class="muted">No articles yet.</p>`;
    return;
  }
  container.innerHTML = articles.slice(0, 30).map((a) => {
    const label = a.sentiment?.label || "neutral";
    const coins = (a.coins || []).slice(0, 3).map((c) =>
      `<span class="tag">${c}</span>`).join("");
    const date = fmtDate(a.published_at);
    return `
      <div class="headline ${label}">
        <a href="${a.url}" target="_blank" rel="noopener">${escapeHtml(a.title)}</a>
        <div class="headline-meta">
          <span>${escapeHtml(a.source)}</span>
          <span>${date}</span>
          <span>sentiment: ${label} (${a.sentiment?.score ?? 0})</span>
          ${coins}
        </div>
      </div>
    `;
  }).join("");
}

function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

(async function main() {
  const data = await loadData();
  if (!data) return;

  document.getElementById("updated").textContent =
    `Last updated: ${fmtDate(data.generated_at)}`;
  document.getElementById("articleCount").textContent = data.article_count;

  const summary = data.summary || {};
  renderGauge(summary.market_sentiment_label || "neutral",
              summary.market_sentiment_score || 0);
  renderMixChart(summary.label_distribution || {});
  renderBarChart("coinsChart", summary.top_coins || [], "mentions");
  renderBarChart("topicsChart", summary.top_topics || [], "mentions");
  renderHeadlines(data.articles || []);
})();
