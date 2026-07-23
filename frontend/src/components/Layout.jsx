import React, { createContext, useState, useEffect, useCallback } from "react";
import { NavLink } from "react-router-dom";
import {
  Terminal, Activity, Shield, Lock, Globe, Database, ShieldAlert,
  Settings, Bell, RefreshCw, Trash2, ShieldCheck, Play, Pause, FastForward,
  ChevronRight, ChevronLeft, AlertTriangle, AlertCircle, Info
} from "lucide-react";
import { api } from "../api.js";
import Footer from "./Footer.jsx";

export const SimulationContext = createContext(null);

const NAV_ITEMS = [
  { to: "/", icon: Activity, label: "Overview", end: true },
  { to: "/firewall", icon: Shield, label: "Firewall" },
  { to: "/auth", icon: Lock, label: "Auth" },
  { to: "/dns", icon: Globe, label: "DNS" },
  { to: "/store", icon: Database, label: "Store" },
  { to: "/validator", icon: ShieldAlert, label: "Validator" },
];

export default function Layout({ children }) {
  const [stats, setStats] = useState(null);
  const [report, setReport] = useState(null);
  const [records, setRecords] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [settings, setSettings] = useState({
    simulation_speed: "normal",
    active_attack: null,
    attack_remaining: 0,
  });
  
  const [isDrawerOpen, setIsDrawerOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [updatingSettings, setUpdatingSettings] = useState(false);
  const [runningManual, setRunningManual] = useState(false);

  // Poll backend data
  const fetchData = useCallback(async () => {
    try {
      const [s, r, rec, n] = await Promise.all([
        api.stats(),
        api.qualityReport(),
        api.records(null, 100),
        api.notifications(),
      ]);
      setStats(s || {});
      setReport(r || {});
      setRecords((rec && Array.isArray(rec.records)) ? rec.records : []);
      setNotifications(Array.isArray(n) ? n : []);
    } catch (err) {
      console.error("Error polling real-time simulation data", err);
      // Ensure we always have array structures to prevent page crashes
      setRecords([]);
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Poll health / settings
  const fetchSettings = useCallback(async () => {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        setSettings({
          simulation_speed: data.simulation_speed,
          active_attack: data.active_attack,
          attack_remaining: 0, // Injected from response if needed, but api.py doesn't return count in health
        });
      }
    } catch (e) {
      console.error("Failed to fetch settings status", e);
    }
  }, []);

  // Initial load + interval setup
  useEffect(() => {
    fetchData();
    fetchSettings();
    const interval = setInterval(() => {
      fetchData();
    }, 2000);
    return () => clearInterval(interval);
  }, [fetchData, fetchSettings]);

  const updateSimulationSpeed = async (speed) => {
    setUpdatingSettings(true);
    try {
      const res = await api.updateSettings(speed, null);
      setSettings((prev) => ({ ...prev, simulation_speed: res.simulation_speed }));
      await fetchData();
    } catch (e) {
      console.error(e);
    } finally {
      setUpdatingSettings(false);
    }
  };

  const triggerAttack = async (type) => {
    setUpdatingSettings(true);
    try {
      const res = await api.updateSettings(null, type);
      setSettings((prev) => ({
        ...prev,
        active_attack: res.active_attack,
        attack_remaining: res.attack_remaining,
      }));
      await fetchData();
    } catch (e) {
      console.error(e);
    } finally {
      setUpdatingSettings(false);
    }
  };

  const resetSimulation = async () => {
    setUpdatingSettings(true);
    try {
      const res = await api.reset();
      setSettings(res.settings);
      await fetchData();
    } catch (e) {
      console.error(e);
    } finally {
      setUpdatingSettings(false);
    }
  };

  const runManualPipeline = async () => {
    setRunningManual(true);
    try {
      await api.run();
      await fetchData();
    } catch (e) {
      console.error(e);
    } finally {
      setRunningManual(false);
    }
  };

  const getSeverityIcon = (sev) => {
    if (sev === "critical") return <AlertCircle size={13} color="var(--red)" />;
    if (sev === "warning") return <AlertTriangle size={13} color="var(--amber)" />;
    return <Info size={13} color="var(--text-muted)" />;
  };

  return (
    <SimulationContext.Provider
      value={{
        stats,
        report,
        records,
        notifications,
        settings,
        loading,
        updateSimulationSpeed,
        triggerAttack,
        resetSimulation,
        runManualPipeline,
        refreshData: fetchData,
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", background: "var(--page)" }}>
        {/* Top Command Dock */}
        <header
          style={{
            height: 64,
            borderBottom: "1px solid var(--border)",
            background: "var(--ink)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 24px",
            position: "sticky",
            top: 0,
            zIndex: 100,
          }}
        >
          {/* Logo / Brand */}
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 6,
                background: "var(--red-bg-strong)",
                border: "1px solid var(--red)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "var(--red-glow)",
              }}
            >
              <Terminal size={16} color="var(--red)" strokeWidth={2} />
            </div>
            <div>
              <div className="mono" style={{ fontSize: 14.5, fontWeight: 700, letterSpacing: "0.02em", display: "flex", alignItems: "center", gap: 6 }}>
                CIPHERFLOW
                <span className="pulse-dot" style={{ width: 5, height: 5 }} />
              </div>
              <div style={{ fontSize: 9, color: "var(--text-faint)", letterSpacing: "0.1em" }}>
                SECOPS SIMULATOR &amp; COCKPIT
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav style={{ display: "flex", gap: 6 }}>
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                style={({ isActive }) => ({
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "8px 14px",
                  borderRadius: 6,
                  fontSize: 12.5,
                  fontWeight: 500,
                  color: "var(--text-secondary)",
                  background: "transparent",
                  border: "1px solid transparent",                  transition: "all 0.2s ease",
                })}
              >
                <item.icon size={13.5} strokeWidth={1.8} />
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* Live Command Cockpit Metrics */}
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div className="mono" style={{ fontSize: 11.5, borderRight: "1px solid var(--border)", paddingRight: 16, display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
              <span style={{ color: "var(--text-faint)", fontSize: 9 }}>INGEST RATE</span>
              <span style={{ color: settings.active_attack ? "var(--red)" : "var(--text)", fontWeight: 600 }}>
                {stats?.eps || 0} EPS
              </span>
            </div>
            <div className="mono" style={{ fontSize: 11.5, borderRight: "1px solid var(--border)", paddingRight: 16, display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
              <span style={{ color: "var(--text-faint)", fontSize: 9 }}>THREATS</span>
              <span style={{ color: (stats?.flagged_events ?? 0) > 0 ? "var(--red)" : "var(--green)", fontWeight: 600 }}>
                {stats?.flagged_events ?? 0}
              </span>
            </div>
            
            <button
              onClick={() => setIsDrawerOpen(!isDrawerOpen)}
              className="btn-cyber"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "6px 10px",
                borderColor: isDrawerOpen ? "var(--red-dim)" : "var(--border)",
                color: isDrawerOpen ? "var(--red)" : "var(--text-muted)",
              }}
            >
              <Settings size={12.5} style={{ animation: settings.simulation_speed !== "off" ? "spin 6s linear infinite" : "none" }} />
              {isDrawerOpen ? "Close Controls" : "Open Controls"}
            </button>
          </div>
        </header>

        {/* Outer Workspace Grid */}
        <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
          {/* Main Workspace */}
          <main
            style={{
              flex: 1,
              padding: "20px 24px",
              minWidth: 0,
              display: "flex",
              flexDirection: "column",
              overflowY: "auto",
              height: "calc(100vh - 64px)",
            }}
          >
            {/* Warning header for active attack simulations */}
            {settings.active_attack && (
              <div
                style={{
                  background: "var(--red-bg)",
                  border: "1px solid var(--red-dim)",
                  borderRadius: 6,
                  padding: "10px 14px",
                  marginBottom: 16,
                  fontSize: 12,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  boxShadow: "var(--red-glow)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span className="pulse-dot" style={{ width: 8, height: 8 }} />
                  <span style={{ fontWeight: 600, color: "var(--red)", textTransform: "uppercase" }}>
                    Active Attack Simulation: {settings.active_attack.replace("_", " ")}
                  </span>
                </div>
                <span className="mono" style={{ color: "var(--text-muted)" }}>
                  Injecting mock threat packets...
                </span>
              </div>
            )}

            <div style={{ flex: 1 }}>{children}</div>
            <Footer />
          </main>

          {/* Right Simulation Control & Intelligence Panel */}
          {isDrawerOpen && (
            <aside
              style={{
                width: 320,
                flexShrink: 0,
                borderLeft: "1px solid var(--border)",
                background: "var(--ink)",
                display: "flex",
                flexDirection: "column",
                height: "calc(100vh - 64px)",
                overflowY: "auto",
              }}
            >
              {/* Section 1: Ingest Simulation Controller */}
              <div style={{ padding: "18px 20px", borderBottom: "1px solid var(--border)" }}>
                <div style={{ fontSize: 12.5, fontWeight: 600, color: "var(--text)", marginBottom: 14, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span>SIMULATOR CONTROL</span>
                  {updatingSettings && <span className="mono" style={{ fontSize: 9.5, color: "var(--text-faint)", marginLeft: "auto" }}>SYNCING...</span>}
                </div>

                {/* Speed Controls */}
                <div style={{ marginBottom: 18 }}>
                  <div style={{ fontSize: 10, color: "var(--text-faint)", marginBottom: 8, textTransform: "uppercase" }}>Ingestion speed</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 4 }}>
                    {[
                      { val: "off", label: "PAUSE", icon: Pause },
                      { val: "slow", label: "SLOW", icon: Play },
                      { val: "normal", label: "NORM", icon: Play },
                      { val: "fast", label: "FAST", icon: FastForward },
                    ].map((btn) => (
                      <button
                        key={btn.val}
                        onClick={() => updateSimulationSpeed(btn.val)}
                        disabled={updatingSettings}
                        className={`btn-cyber ${settings.simulation_speed === btn.val ? "active" : ""}`}
                        style={{ padding: "8px 0", fontSize: 9.5, display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}
                      >
                        <btn.icon size={11} />
                        {btn.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Attack Scenario Trigger Buttons */}
                <div style={{ marginBottom: 18 }}>
                  <div style={{ fontSize: 10, color: "var(--text-faint)", marginBottom: 8, textTransform: "uppercase" }}>Attack Scenarios</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <button
                      onClick={() => triggerAttack("ddos")}
                      disabled={updatingSettings || !!settings.active_attack}
                      className="btn-cyber"
                      style={{ textAlign: "left", padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}
                    >
                      <span>Simulate DDoS</span>
                      <ChevronRight size={12} />
                    </button>
                    <button
                      onClick={() => triggerAttack("brute_force")}
                      disabled={updatingSettings || !!settings.active_attack}
                      className="btn-cyber"
                      style={{ textAlign: "left", padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}
                    >
                      <span>Simulate Brute Force</span>
                      <ChevronRight size={12} />
                    </button>
                    <button
                      onClick={() => triggerAttack("dns_tunneling")}
                      disabled={updatingSettings || !!settings.active_attack}
                      className="btn-cyber"
                      style={{ textAlign: "left", padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}
                    >
                      <span>Simulate DNS Tunneling</span>
                      <ChevronRight size={12} />
                    </button>
                  </div>
                </div>

                {/* Reset & Manual Overrides */}
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    onClick={runManualPipeline}
                    disabled={runningManual}
                    className="btn-cyber"
                    style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 5 }}
                  >
                    <RefreshCw size={11} style={{ animation: runningManual ? "spin 1s linear infinite" : "none" }} />
                    Parse Files
                  </button>
                  <button
                    onClick={resetSimulation}
                    disabled={updatingSettings}
                    className="btn-cyber"
                    style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "8px 10px" }}
                    title="Reset Simulation State"
                  >
                    <Trash2 size={11.5} />
                  </button>
                </div>
              </div>

              {/* Section 2: Intel Alert Feed */}
              <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
                <div
                  style={{
                    padding: "16px 20px 10px",
                    borderBottom: "1px solid var(--border)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <div style={{ fontSize: 12.5, fontWeight: 600, color: "var(--text)", display: "flex", alignItems: "center", gap: 8 }}>
                    <Bell size={13} color="var(--red)" />
                    LIVE ALERTS FEED
                  </div>
                  <span className="badge badge-danger" style={{ fontSize: 9, padding: "2px 6px" }}>
                    {(notifications || []).length} EVENTS
                  </span>
                </div>

                {/* Notifications List container */}
                <div style={{ flex: 1, overflowY: "auto" }}>
                  {!(notifications || []).length ? (
                    <div style={{ padding: 24, textAlign: "center", fontSize: 12, color: "var(--text-faint)" }}>
                      No alerts triggered. System operating within baseline thresholds.
                    </div>
                  ) : (
                    (notifications || []).map((n) => {
                      if (!n) return null;
                      let timeStr = "—";
                      try {
                        const d = new Date(n.timestamp);
                        if (!isNaN(d.getTime())) {
                          timeStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                        }
                      } catch (e) {}
                      return (
                        <div key={n.id || Math.random()} className={`notif-item notif-severity-${n.severity || 'info'}`}>
                          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10 }}>
                            {getSeverityIcon(n.severity)}
                            <span
                              className="mono"
                              style={{
                                color: n.severity === "critical" ? "var(--red)" : n.severity === "warning" ? "var(--amber)" : "var(--text-muted)",
                                textTransform: "uppercase",
                                fontWeight: 600,
                              }}
                            >
                              {n.severity || 'info'}
                            </span>
                            <span className="mono" style={{ color: "var(--text-faint)", marginLeft: "auto" }}>
                              {timeStr}
                            </span>
                          </div>
                          <div style={{ color: "var(--text-secondary)", lineHeight: "1.4" }}>
                            {n.message}
                          </div>
                          <div style={{ display: "flex", gap: 8, fontSize: 9.5, color: "var(--text-faint)", marginTop: 2 }}>
                            <span className="mono" style={{ textTransform: "capitalize" }}>Source: {n.source || 'system'}</span>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </aside>
          )}
        </div>
      </div>
    </SimulationContext.Provider>
  );
}
