import React, { useContext } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";
import { Activity, ShieldAlert, CheckCircle2 } from "lucide-react";
import Topbar from "../components/Topbar.jsx";
import StatCard from "../components/StatCard.jsx";
import RiskGauge from "../components/RiskGauge.jsx";
import EventTable from "../components/EventTable.jsx";
import { SimulationContext } from "../components/Layout.jsx";

const TYPE_COLORS = { firewall: "#FF3333", auth: "#FF9900", dns: "#8F726D" };

export default function Overview() {
  const sim = useContext(SimulationContext);

  if (!sim || !sim.stats) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "40vh" }}>
        <div className="mono" style={{ fontSize: 13, color: "var(--text-muted)", display: "flex", gap: 10, alignItems: "center" }}>
          <span className="pulse-dot" style={{ width: 6, height: 6 }} />
          INITIALIZING Command Cockpit Data Feed...
        </div>
      </div>
    );
  }

  const { stats, report, records, settings, runManualPipeline, loading } = sim;

  const totalEvents = stats?.total_events ?? 0;
  const flagged = stats?.flagged_events ?? 0;
  const qualityScore = report?.quality_score_pct ?? 0;
  const riskScore = totalEvents ? Math.min(100, Math.round((flagged / totalEvents) * 220)) : 0;

  const typeMix = Object.entries(stats.by_type || {}).map(([name, value]) => ({
    name, value, color: TYPE_COLORS[name] || "#8F726D",
  }));

  const recentRecords = records.slice(0, 12);

  return (
    <>
      <Topbar
        title="Attack Surface Command View"
        subtitle="Real-time log ingestion normalized across perimeter firewall, system auth, and DNS activity"
        onRefresh={runManualPipeline}
        refreshing={loading}
        flagged={flagged}
      />

      <div style={{ display: "flex", gap: 14, marginBottom: 16, flexWrap: "wrap" }}>
        <StatCard icon={Activity} label="Total Events Processed" value={totalEvents.toLocaleString()} delta={12} deltaGood />
        <StatCard icon={ShieldAlert} label="Anomalous / Blocked Events" value={flagged.toLocaleString()} delta={7} deltaGood={false} />
        <StatCard icon={CheckCircle2} label="Log Quality Integrity" value={`${qualityScore}%`} delta={2} deltaGood />
        <div className="card active-card" style={{ padding: "12px 20px", display: "flex", alignItems: "center", justifyContent: "center", minWidth: 176 }}>
          <RiskGauge score={riskScore} />
        </div>
      </div>

      <div style={{ display: "flex", gap: 14, marginBottom: 16, flexWrap: "wrap" }}>
        {/* Hourly Volume Line Chart */}
        <div className="card" style={{ flex: 2, minWidth: 320, padding: "18px 20px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>Normalized Incident Frequency by Hour</div>
            <Legend />
          </div>
          <ResponsiveContainer width="100%" height={190}>
            <LineChart data={stats.timeline || []} margin={{ top: 4, right: 6, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="1 5" vertical={false} />
              <XAxis dataKey="hour" tick={{ fontSize: 9.5, fill: "var(--text-muted)", fontFamily: "var(--font-mono)" }} axisLine={{ stroke: "var(--border)" }} tickLine={false} />
              <YAxis tick={{ fontSize: 9.5, fill: "var(--text-muted)", fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "var(--card-2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 11 }} labelStyle={{ color: "var(--text)" }} />
              <Line type="monotone" dataKey="firewall" stroke="#FF3333" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="auth" stroke="#FF9900" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="dns" stroke="#8F726D" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Source Mix Pie Chart */}
        <div className="card" style={{ flex: 1, minWidth: 220, padding: "18px 20px" }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 10 }}>Inbound Log Source Distribution</div>
          <ResponsiveContainer width="100%" height={140}>
            <PieChart>
              <Pie data={typeMix} dataKey="value" innerRadius={42} outerRadius={58} paddingAngle={4} stroke="none">
                {typeMix.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display: "flex", flexDirection: "column", gap: 5, marginTop: 4 }}>
            {typeMix.map((t) => (
              <div key={t.name} style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                <span style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-muted)", textTransform: "capitalize" }}>
                  <span style={{ width: 6, height: 6, borderRadius: 1.5, background: t.color, display: "inline-block" }} />
                  {t.name}
                </span>
                <span className="mono" style={{ color: "var(--text)" }}>{t.value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ padding: "16px 20px" }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 12 }}>
          Live Normalized Ingest Stream (Last 12 Events)
        </div>
        <EventTable records={recentRecords} loading={loading} />
      </div>
    </>
  );
}

function Legend() {
  return (
    <div style={{ display: "flex", gap: 12, fontSize: 11, color: "var(--text-muted)" }}>
      <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
        <span style={{ width: 6, height: 6, borderRadius: 1.5, background: "#FF3333", display: "inline-block" }} />Firewall
      </span>
      <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
        <span style={{ width: 6, height: 6, borderRadius: 1.5, background: "#FF9900", display: "inline-block" }} />Auth
      </span>
      <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
        <span style={{ width: 6, height: 6, borderRadius: 1.5, background: "#8F726D", display: "inline-block" }} />DNS
      </span>
    </div>
  );
}
