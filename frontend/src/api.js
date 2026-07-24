const BASE = "/api";
const WS_URL = `ws://${window.location.hostname}:8000/ws`;

async function request(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`Request failed: ${path} (${res.status})`);
  return res.json();
}

export const api = {
  stats: () => request("/stats"),
  records: (logType, limit = 50) =>
    request(`/records?${logType ? `log_type=${logType}&` : ""}limit=${limit}`),
  qualityReport: () => request("/quality-report"),
  event: (id) => request(`/event/${id}`),
  notifications: () => request("/notifications"),

  run: () =>
    fetch(`${BASE}/run`, { method: "POST" }).then((r) => {
      if (!r.ok) throw new Error("Pipeline run failed");
      return r.json();
    }),

  updateSettings: (simulationSpeed, triggerAttack) =>
    fetch(`${BASE}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        simulation_speed: simulationSpeed,
        trigger_attack: triggerAttack,
      }),
    }).then((r) => {
      if (!r.ok) throw new Error("Update settings failed");
      return r.json();
    }),

  reset: () =>
    fetch(`${BASE}/reset`, { method: "POST" }).then((r) => {
      if (!r.ok) throw new Error("Reset failed");
      return r.json();
    }),
};

/**
 * Opens a WebSocket connection to /ws and calls onMessage(data) every time
 * the server pushes a live stats snapshot. Returns a cleanup function.
 *
 * Usage:
 *   const cleanup = api.connectLiveStats((data) => setStats(data));
 *   // call cleanup() on component unmount
 */
api.connectLiveStats = (onMessage) => {
  let ws;
  let reconnectTimer;

  const connect = () => {
    ws = new WebSocket(WS_URL);

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.type === "stats") onMessage(data);
      } catch (_) {}
    };

    ws.onclose = () => {
      // Auto-reconnect after 3s if the connection drops
      reconnectTimer = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  };

  connect();

  return () => {
    clearTimeout(reconnectTimer);
    if (ws) ws.close();
  };
};

