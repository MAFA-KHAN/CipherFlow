import React from "react";

export default function StatCard({ icon: Icon, label, value, sub, accent, trend }) {
  const accentColor = {
    red:   "var(--red)",
    green: "var(--green)",
    amber: "var(--amber)",
    blue:  "var(--blue)",
  }[accent] || "var(--red)";

  return (
    <div className="stat-card" style={{ "--accent": accentColor }}>
      {/* Top accent line */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: "2px",
        background: `linear-gradient(90deg, ${accentColor}, transparent)`,
      }} />

      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase",
                      color: "var(--text-muted)", marginBottom: 8 }}>
            {label}
          </p>
          <p style={{ fontSize: 28, fontWeight: 700, color: "var(--text)", lineHeight: 1, marginBottom: 4 }}>
            {value ?? "—"}
          </p>
          {sub && (
            <p style={{ fontSize: 11.5, color: "var(--text-muted)", marginTop: 4 }}>
              {sub}
            </p>
          )}
        </div>

        {Icon && (
          <div style={{
            width: 40, height: 40, borderRadius: "var(--radius)",
            background: `color-mix(in srgb, ${accentColor} 10%, transparent)`,
            border: `1px solid color-mix(in srgb, ${accentColor} 20%, transparent)`,
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0,
          }}>
            <Icon size={18} style={{ color: accentColor }} />
          </div>
        )}
      </div>

      {trend !== undefined && (
        <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 6 }}>
          <div className="quality-bar-track" style={{ flex: 1 }}>
            <div
              className={`quality-bar-fill ${trend >= 90 ? "high" : ""}`}
              style={{ width: `${Math.min(100, Math.max(0, trend))}%` }}
            />
          </div>
          <span style={{ fontSize: 10, color: "var(--text-muted)", minWidth: 32, textAlign: "right" }}>
            {trend}%
          </span>
        </div>
      )}
    </div>
  );
}
