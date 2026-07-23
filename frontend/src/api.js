const BASE = "/api";

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
