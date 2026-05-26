/**
 * charts.js — Chart.js setup and update helpers.
 *
 * No fetch() here: this file only knows how to draw charts when given numbers.
 */

const MAX_CPU_POINTS = 20;
const MAX_NETWORK_POINTS = 20;

const chartColors = {
  cpu: "#3b82f6",
  memoryUsed: "#3b82f6",
  memoryFree: "#334155",
  disk: "#22c55e",
  networkSent: "#a78bfa",
  networkRecv: "#38bdf8",
};

/** Shared dark-theme defaults for every chart */
const baseChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 400 },
  plugins: {
    legend: {
      labels: { color: "#94a3b8", boxWidth: 12 },
    },
  },
};

let charts = {
  cpu: null,
  memory: null,
  disk: null,
  network: null,
};

/** Rolling history for line charts */
const history = {
  cpuLabels: [],
  cpuValues: [],
  networkLabels: [],
  networkSent: [],
  networkRecv: [],
};

// After the first draw, skip animation to avoid jank during 3s polling.
let skipChartAnimation = false;

function applyChartUpdate(chart) {
  chart.update(skipChartAnimation ? "none" : undefined);
  skipChartAnimation = true;
}

function truncateLabel(text, maxLen = 14) {
  if (!text || text.length <= maxLen) {
    return text;
  }
  return `${text.slice(0, maxLen - 1)}…`;
}

function initCharts() {
  if (typeof Chart === "undefined") {
    throw new Error("Chart.js did not load. Check the CDN script in index.html.");
  }

  Chart.defaults.color = "#94a3b8";
  Chart.defaults.borderColor = "rgba(148, 163, 184, 0.15)";

  charts.cpu = new Chart(document.getElementById("cpu-chart"), {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "CPU %",
          data: [],
          borderColor: chartColors.cpu,
          backgroundColor: "rgba(59, 130, 246, 0.12)",
          fill: true,
          tension: 0.35,
          pointRadius: 2,
        },
      ],
    },
    options: {
      ...baseChartOptions,
      scales: {
        y: {
          min: 0,
          max: 100,
          ticks: { callback: (v) => `${v}%` },
        },
      },
    },
  });

  charts.memory = new Chart(document.getElementById("memory-chart"), {
    type: "doughnut",
    data: {
      labels: ["Used", "Available"],
      datasets: [
        {
          data: [0, 1],
          backgroundColor: [chartColors.memoryUsed, chartColors.memoryFree],
          borderWidth: 0,
        },
      ],
    },
    options: {
      ...baseChartOptions,
      cutout: "68%",
      plugins: { legend: { position: "bottom" } },
    },
  });

  charts.disk = new Chart(document.getElementById("disk-chart"), {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          label: "Used %",
          data: [],
          backgroundColor: chartColors.disk,
          borderRadius: 6,
        },
      ],
    },
    options: {
      ...baseChartOptions,
      scales: {
        x: {
          ticks: {
            maxRotation: 45,
            minRotation: 0,
            callback: function (value) {
              const label = this.getLabelForValue(value);
              return truncateLabel(label);
            },
          },
        },
        y: {
          min: 0,
          max: 100,
          ticks: { callback: (v) => `${v}%` },
        },
      },
      plugins: {
        tooltip: {
          callbacks: {
            title: (items) => {
              const index = items[0]?.dataIndex;
              const disks = items[0]?.chart?.data?.labels;
              return disks?.[index] ?? "";
            },
          },
        },
      },
    },
  });

  charts.network = new Chart(document.getElementById("network-chart"), {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Upload",
          data: [],
          borderColor: chartColors.networkSent,
          tension: 0.35,
          pointRadius: 2,
        },
        {
          label: "Download",
          data: [],
          borderColor: chartColors.networkRecv,
          tension: 0.35,
          pointRadius: 2,
        },
      ],
    },
    options: {
      ...baseChartOptions,
      scales: {
        y: {
          ticks: {
            callback: (value) => formatBytes(value) + "/s",
          },
        },
      },
    },
  });
}

function pushRolling(labels, values, label, value, maxPoints) {
  labels.push(label);
  values.push(value);
  if (labels.length > maxPoints) {
    labels.shift();
    values.shift();
  }
}

function updateCpuChart(cpuPercent) {
  const label = new Date().toLocaleTimeString();
  pushRolling(history.cpuLabels, history.cpuValues, label, cpuPercent, MAX_CPU_POINTS);

  charts.cpu.data.labels = history.cpuLabels;
  charts.cpu.data.datasets[0].data = history.cpuValues;
  applyChartUpdate(charts.cpu);
}

function updateMemoryChart(memory) {
  const used = memory.used_bytes ?? 0;
  const available = memory.available_bytes ?? 0;

  charts.memory.data.datasets[0].data = [used, available];
  applyChartUpdate(charts.memory);
}

function updateDiskChart(disks) {
  if (!disks.length) {
    charts.disk.data.labels = [];
    charts.disk.data.datasets[0].data = [];
  } else {
    charts.disk.data.labels = disks.map((d) => d.mountpoint || d.device);
    charts.disk.data.datasets[0].data = disks.map((d) => d.percent ?? 0);
  }
  applyChartUpdate(charts.disk);
}

function updateNetworkChart(network) {
  const sent = network.bytes_sent_per_sec ?? 0;
  const recv = network.bytes_recv_per_sec ?? 0;
  const label = new Date().toLocaleTimeString();

  history.networkLabels.push(label);
  history.networkSent.push(sent);
  history.networkRecv.push(recv);

  if (history.networkLabels.length > MAX_NETWORK_POINTS) {
    history.networkLabels.shift();
    history.networkSent.shift();
    history.networkRecv.shift();
  }

  charts.network.data.labels = history.networkLabels;
  charts.network.data.datasets[0].data = history.networkSent;
  charts.network.data.datasets[1].data = history.networkRecv;
  applyChartUpdate(charts.network);
}

/**
 * Update every chart from the /api/metrics payload.
 */
function updateChartsFromMetrics(data) {
  const cpuPercent = data.cpu?.cpu_percent ?? 0;
  updateCpuChart(cpuPercent);

  if (data.memory) {
    updateMemoryChart(data.memory);
  }

  const disks = data.disk?.disks ?? [];
  updateDiskChart(disks);

  if (data.network) {
    updateNetworkChart(data.network);
  }

  return cpuPercent;
}
