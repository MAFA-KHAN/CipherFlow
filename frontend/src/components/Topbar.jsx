import React from "react";
import { Search, Bell, Settings, RefreshCw } from "lucide-react";

export default function Topbar({ title, subtitle, onRefresh, refreshing, flagged }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 22, flexWrap: "wrap", gap: 12 }}>
      <div>
        <div className="page-title" style={{ fontSize: 17, fontWeight: 700, letterSpacing: "-0.01em" }}>{title}</div>
        {subtitle && <div className="page-subtitle" style={{ fontSize: 11.5, color: "var(--text-muted)" }}>{subtitle}</div>}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div
          style={{
            display: "flex", alignItems: "center", gap: 7, background: "var(--card)",
            border: "1px solid var(--border)", borderRadius: 6, padding: "6px 12px",
            color: "var(--text-faint)", fontSize: 12, minWidth: 170,
          }}
        >
          <Search size={12} />
          <span style={{ fontSize: 11.5 }}>Search events...</span>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="btn-cyber"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "7px 12px",
            }}
          >
            <RefreshCw size={12} style={{ animation: refreshing ? "spin 0.8s linear infinite" : "none" }} />
            {refreshing ? "Running…" : "Run pipeline"}
          </button>
        )}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
