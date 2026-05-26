/**
 * app.js — wires the dashboard together: poll API, update DOM, handle states.
 */

const POLL_INTERVAL_MS = 3000;

const THRESHOLDS = {
  cpu: 80,
  memory: 85,
  disk: 90,
};

const UI = {
  dashboard: document.getElementById("dashboard"),
  loadingBanner: document.getElementById("loading-banner"),
  alertBanner: document.getElementById("alert-banner"),
  errorBanner: document.getElementById("error-banner"),
  statusDot: document.getElementById("status-dot"),
  statusLabel: document.getElementById("status-label"),
  lastUpdated: document.getElementById("last-updated"),
  cpuReadout: document.getElementById("cpu-readout"),
  cpuBadge: document.getElementById("cpu-badge"),
  memoryReadout: document.getElementById("memory-readout"),
  memoryBadge: document.getElementById("memory-badge"),
  diskReadout: document.getElementById("disk-readout"),
  diskBadge: document.getElementById("disk-badge"),
  networkSent: document.getElementById("network-sent"),
  networkRecv: document.getElementById("network-recv"),
};

let pollTimerId = null;
let isFetching = false;
let hasLoadedOnce = false;

function setStatus(state, label) {
  UI.statusDot.className = "status-dot";
  if (state === "live") {
    UI.statusDot.classList.add("status-dot--live");
  } else if (state === "loading") {
    UI.statusDot.classList.add("status-dot--loading");
  } else if (state === "error" || state === "stale") {
    UI.statusDot.classList.add("status-dot--error");
  }
  UI.statusLabel.textContent = label;
}

function showLoading(show) {
  UI.loadingBanner.classList.toggle("hidden", !show);
  UI.dashboard.classList.toggle("dashboard--loading", show && !hasLoadedOnce);
  UI.dashboard.setAttribute("aria-busy", show ? "true" : "false");
}

function showAlert(message) {
  if (!message) {
    UI.alertBanner.classList.add("hidden");
    UI.alertBanner.textContent = "";
    return;
  }
  UI.alertBanner.textContent = message;
  UI.alertBanner.classList.remove("hidden");
}

function showError(message) {
  if (!message) {
    UI.errorBanner.classList.add("hidden");
    UI.errorBanner.innerHTML = "";
    return;
  }
  UI.errorBanner.innerHTML = `${message} <button type="button" class="banner__retry">Retry now</button>`;
  UI.errorBanner.classList.remove("hidden");
  UI.errorBanner.querySelector(".banner__retry")?.addEventListener("click", () => {
    refreshMetrics();
  }, { once: true });
}

function setStaleView(isStale) {
  UI.dashboard.classList.toggle("dashboard--stale", isStale);
}

function badgeClass(percent, threshold) {
  if (percent >= threshold) {
    return "badge badge--danger";
  }
  if (percent >= threshold - 10) {
    return "badge badge--warn";
  }
  return "badge";
}

function updateReadouts(data) {
  const cpu = data.cpu?.cpu_percent ?? 0;
  const memory = data.memory ?? {};
  const disks = data.disk?.disks ?? [];
  const network = data.network ?? {};

  UI.cpuReadout.textContent = `${cpu.toFixed(1)}%`;
  UI.cpuBadge.textContent = `${cpu.toFixed(0)}%`;
  UI.cpuBadge.className = badgeClass(cpu, THRESHOLDS.cpu);

  const memPercent = memory.percent ?? 0;
  UI.memoryReadout.textContent = `${formatBytes(memory.used_bytes)} / ${formatBytes(memory.total_bytes)}`;
  UI.memoryBadge.textContent = `${memPercent.toFixed(0)}%`;
  UI.memoryBadge.className = badgeClass(memPercent, THRESHOLDS.memory);

  if (disks.length === 0) {
    UI.diskReadout.textContent = "No disks reported";
    UI.diskBadge.textContent = "—";
    UI.diskBadge.className = "badge badge--muted";
  } else {
    const maxDisk = disks.reduce((max, d) => (d.percent > max.percent ? d : max), disks[0]);
    UI.diskReadout.textContent = `${disks.length} mount point(s) · highest ${maxDisk.mountpoint} ${maxDisk.percent}%`;
    UI.diskBadge.textContent = `${maxDisk.percent}%`;
    UI.diskBadge.className = badgeClass(maxDisk.percent, THRESHOLDS.disk);
  }

  UI.networkSent.textContent = formatRate(network.bytes_sent_per_sec);
  UI.networkRecv.textContent = formatRate(network.bytes_recv_per_sec);

  updateThresholdAlerts(cpu, memPercent, disks);
}

function updateThresholdAlerts(cpu, memPercent, disks) {
  const warnings = [];

  if (cpu >= THRESHOLDS.cpu) {
    warnings.push(`CPU ${cpu.toFixed(1)}%`);
  }
  if (memPercent >= THRESHOLDS.memory) {
    warnings.push(`Memory ${memPercent.toFixed(1)}%`);
  }

  const maxDisk = disks.length
    ? disks.reduce((max, d) => (d.percent > max.percent ? d : max), disks[0])
    : null;
  if (maxDisk && maxDisk.percent >= THRESHOLDS.disk) {
    warnings.push(`Disk ${maxDisk.mountpoint} ${maxDisk.percent}%`);
  }

  if (warnings.length > 0) {
    showAlert(`High usage: ${warnings.join(" · ")}`);
  } else {
    showAlert(null);
  }
}

async function refreshMetrics() {
  if (isFetching) {
    return;
  }

  isFetching = true;
  setStatus("loading", "Updating…");
  showLoading(!hasLoadedOnce);

  try {
    const data = await fetchMetrics();
    updateChartsFromMetrics(data);

    hasLoadedOnce = true;
    showLoading(false);
    showError(null);
    setStaleView(false);
    updateReadouts(data);
    setStatus("live", "Live");

    const now = new Date();
    UI.lastUpdated.textContent = `Updated ${now.toLocaleTimeString()}`;
    UI.lastUpdated.dateTime = now.toISOString();
  } catch (error) {
    console.error("Metrics fetch failed:", error);

    if (hasLoadedOnce) {
      setStatus("stale", "Stale data");
      setStaleView(true);
      showError(`${error.message} — showing last known metrics.`);
    } else {
      setStatus("error", "Error");
      setStaleView(false);
      showError(error.message || "Failed to load metrics");
    }
    showLoading(false);
  } finally {
    isFetching = false;
    scheduleNextPoll();
  }
}

/**
 * Wait POLL_INTERVAL_MS after each request finishes (not a fixed interval timer).
 * Avoids skipped polls when /api/metrics takes ~2s to respond.
 */
function scheduleNextPoll() {
  clearTimeout(pollTimerId);
  if (document.hidden) {
    return;
  }
  pollTimerId = setTimeout(refreshMetrics, POLL_INTERVAL_MS);
}

function startPolling() {
  refreshMetrics();
}

function stopPolling() {
  clearTimeout(pollTimerId);
  pollTimerId = null;
}

function initDashboard() {
  try {
    initCharts();
  } catch (error) {
    showError(error.message);
    setStatus("error", "Chart error");
    return;
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stopPolling();
    } else {
      refreshMetrics();
    }
  });

  startPolling();
}

document.addEventListener("DOMContentLoaded", initDashboard);
