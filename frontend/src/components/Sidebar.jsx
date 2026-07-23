import React from "react";
import { NavLink } from "react-router-dom";
import {
  Terminal, Activity, Shield, Lock, Globe, Database, ShieldAlert, Radio,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/", icon: Activity, label: "Overview", end: true },
  { to: "/firewall", icon: Shield, label: "Firewall logs" },
  { to: "/auth", icon: Lock, label: "Authentication" },
  { to: "/dns", icon: Globe, label: "DNS activity" },
  { to: "/store", icon: Database, label: "Normalized store" },
  { to: "/validator", icon: ShieldAlert, label: "Quality validator" },
];

export default function Sidebar() {
  return (
    <aside
      style={{
        width: 224,
        flexShrink: 0,
        borderRight: "1px solid var(--border)",
        background: "var(--ink)",
        padding: "22px 14px",
        display: "flex",
        flexDirection: "column",
        gap: 3,
        minHeight: "100vh",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 9, padding: "0 8px 26px" }}>
        <div
          style={{
            width: 32, height: 32, borderRadius: 8, background: "var(--red)",
            display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
          }}
        >
          <Terminal size={17} color="var(--ink)" strokeWidth={2.2} />
        </div>
        <div>
          <div className="mono" style={{ fontSize: 15, fontWeight: 600, color: "var(--text)" }}>
            CipherFlow
          </div>
          <div style={{ fontSize: 9.5, color: "var(--text-faint)", letterSpacing: "0.06em" }}>
            SECOPS PIPELINE
          </div>
        </div>
      </div>

      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          style={({ isActive }) => ({
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "10px 11px",
            borderRadius: 7,
            fontSize: 13.5,
            color: isActive ? "var(--red)" : "var(--text-secondary)",
            background: isActive ? "var(--red-bg)" : "transparent",
            fontWeight: isActive ? 500 : 400,
          })}
        >
          <item.icon size={15} strokeWidth={1.8} />
          {item.label}
        </NavLink>
      ))}

      <div style={{ marginTop: "auto", paddingTop: 18, borderTop: "1px solid var(--border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11.5, color: "var(--text-muted)", padding: "0 8px" }}>
          <Radio size={12} color="var(--green)" />
          Pipeline online
        </div>
        <div className="mono" style={{ fontSize: 10.5, color: "var(--text-faint)", marginTop: 5, padding: "0 8px" }}>
          v0.4.0 — build 0247
        </div>
      </div>
    </aside>
  );
}
