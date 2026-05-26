/**
 * api.js — all HTTP calls to the Flask backend.
 *
 * The browser talks to Nginx on the same origin; Nginx proxies /api/* to Flask.
 */

const API_BASE = "/api";
const METRICS_URL = `${API_BASE}/metrics`;

// /api/metrics blocks ~2s (CPU + network sampling). Allow headroom before aborting.
const FETCH_TIMEOUT_MS = 15000;

/**
 * Fetch CPU, memory, disk, and network in one request.
 * @returns {Promise<object>} The `data` object from the API envelope
 */
async function fetchMetrics() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    const response = await fetch(METRICS_URL, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
      signal: controller.signal,
    });

    let body = null;
    try {
      body = await response.json();
    } catch {
      throw new Error("Server returned a non-JSON response");
    }

    if (!response.ok || body.status === "error") {
      const message = body.message || `Request failed (${response.status})`;
      throw new Error(message);
    }

    if (!body.data) {
      throw new Error("Invalid response: missing data field");
    }

    return body.data;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Request timed out — the API may still be collecting metrics");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Turn raw bytes into a human-readable string (KB, MB, GB).
 * Declared as a function (not const) so charts.js can use it in axis labels.
 */
function formatBytes(bytes) {
  if (bytes == null || Number.isNaN(bytes)) {
    return "—";
  }
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = Number(bytes);
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  const decimals = value >= 10 || unitIndex === 0 ? 0 : 1;
  return `${value.toFixed(decimals)} ${units[unitIndex]}`;
}

/**
 * Format bytes per second for network throughput labels.
 */
function formatRate(bytesPerSec) {
  if (bytesPerSec == null || Number.isNaN(bytesPerSec)) {
    return "—";
  }
  return `${formatBytes(bytesPerSec)}/s`;
}
