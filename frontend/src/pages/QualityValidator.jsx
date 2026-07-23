import React, { useContext } from "react";
import { ShieldAlert, ShieldCheck, AlertTriangle } from "lucide-react";
import Topbar from "../components/Topbar.jsx";
import StatCard from "../components/StatCard.jsx";
import RiskGauge from "../components/RiskGauge.jsx";
import { SimulationContext } from "../components/Layout.jsx";

export default function QualityValidator() {
  const sim = useContext(SimulationContext);

  if (!sim || !sim.report) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "40vh" }}>
        <div className="mono" style={{ fontSize: 13, color: "var(--text-muted)", display: "flex", gap: 10, alignItems: "center" }}>
          <span className="pulse-dot" style={{ width: 6, height: 6 }} />
          INITIALIZING Quality Validation Engine...
        </div>
      </div>
    );
  }

  const { report, loading, runManualPipeline } = sim;
  const score = report.quality_score_pct;

  return (
    <>
      <Topbar
        title="Data Quality Validator"
        subtitle="Verifies schema field constraints, IP formatting, timestamp parsing, and duplicate keys in real-time"
        onRefresh={runManualPipeline}
        refreshing={loading}
      />

      <div style={{ display: "flex", gap: 14, marginBottom: 16, flexWrap: "wrap" }}>
        <StatCard icon={ShieldCheck} label="Total Records Audited" value={(report.total_records || 0).toLocaleString()} delta={0} />
        <StatCard icon={ShieldCheck} label="Clean Event Records" value={(report.clean_records || 0).toLocaleString()} delta={0} />
        <StatCard icon={ShieldAlert} label="Flagged Anomalous Records" value={(report.flagged_records || 0).toLocaleString()} delta={0} deltaGood={false} />
        <div className="card active-card" style={{ padding: "12px 20px", display: "flex", alignItems: "center", justifyContent: "center", minWidth: 176 }}>
          <RiskGauge score={score} label="INTEGRITY" />
        </div>
      </div>

      <div style={{ display: "flex", gap: 14, marginBottom: 16, flexWrap: "wrap" }}>
        {/* Source breakdown */}
        <div className="card" style={{ flex: 1, minWidth: 260, padding: "16px 20px" }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 12 }}>Ingested Events by Source</div>
          {Object.entries(report.records_by_type || {}).map(([type, count]) => (
            <Bar key={type} label={type} value={count} max={report.total_records || 1} color="var(--red)" />
          ))}
        </div>

        {/* Issues breakdown */}
        <div className="card" style={{ flex: 1, minWidth: 260, padding: "16px 20px" }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 12 }}>Validation Failure Breakdown</div>
          {Object.keys(report.issue_breakdown || {}).length === 0 ? (
            <div style={{ fontSize: 12, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 8, height: "100px", justifyContent: "center" }}>
              <ShieldCheck size={16} color="var(--green)" />
              All current log streams strictly adhere to schema requirements.
            </div>
          ) : (
            Object.entries(report.issue_breakdown).map(([issue, count]) => (
              <Bar key={issue} label={issue.replace(/_/g, " ")} value={count} max={report.total_records || 1} color="var(--amber)" />
            ))
          )}
        </div>
      </div>

      {/* Flagged events table */}
      <div className="card" style={{ padding: "16px 20px" }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 12 }}>Flagged Schema Violations</div>
        {(report.flagged_events || []).length === 0 ? (
          <div style={{ fontSize: 12, color: "var(--text-muted)", padding: "10px 0" }}>
            No errors detected. Every record in the database complies with security constraints.
          </div>
        ) : (
          <div className="mono" style={{ fontSize: 11.5 }}>
            <div style={{ display: "grid", gridTemplateColumns: "140px 100px 1fr", padding: "6px 10px", color: "var(--text-faint)", fontSize: 10, borderBottom: "1px solid var(--border)" }}>
              <div>EVENT ID</div><div>LOG SOURCE</div><div>RULE FAILURES</div>
            </div>
            <div style={{ maxHeight: 350, overflowY: "auto" }}>
              {report.flagged_events.map((f, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "140px 100px 1fr", padding: "8px 10px", borderBottom: "1px solid var(--border)", alignItems: "center" }}>
                  <div style={{ color: "var(--text-muted)" }}>{f.event_id || "—"}</div>
                  <div style={{ color: "var(--text)", textTransform: "uppercase", fontSize: 11 }}>{f.log_type || "—"}</div>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {f.issues.map((issue) => (
                      <span key={issue} className="badge badge-danger">
                        <AlertTriangle size={10} />
                        {issue.replace(/_/g, " ")}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}

function Bar({ label, value, max, color }) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 5 }}>
        <span style={{ color: "var(--text-secondary)", textTransform: "capitalize" }}>{label}</span>
        <span className="mono" style={{ color: "var(--text)" }}>{value}</span>
      </div>
      <div style={{ height: 6, borderRadius: 3, background: "var(--card-3)", overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 3 }} />
      </div>
    </div>
  );
}
