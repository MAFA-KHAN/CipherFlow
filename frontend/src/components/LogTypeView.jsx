import React, { useContext, useState } from "react";
import { CheckCircle2, AlertTriangle } from "lucide-react";
import Topbar from "./Topbar.jsx";
import StatCard from "./StatCard.jsx";
import EventTable from "./EventTable.jsx";
import { SimulationContext } from "./Layout.jsx";

const BAD = new Set(["blocked", "dropped", "failed", "locked", "nxdomain", "servfail", "refused"]);
const OK = new Set(["allowed", "success", "noerror"]);

export default function LogTypeView({ logType, icon: Icon, title, subtitle }) {
  const sim = useContext(SimulationContext);
  const [statusFilter, setStatusFilter] = useState("all");

  if (!sim || !sim.records) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "40vh" }}>
        <div className="mono" style={{ fontSize: 13, color: "var(--text-muted)", display: "flex", gap: 10, alignItems: "center" }}>
          <span className="pulse-dot" style={{ width: 6, height: 6 }} />
          INITIALIZING {title} Feed...
        </div>
      </div>
    );
  }

  const { records: allRecords, loading, runManualPipeline } = sim;

  // Filter records by logType
  const records = allRecords.filter((r) => r.log_type === logType);

  const total = records.length;
  const ok = records.filter((r) => OK.has(String(r.status || "").toLowerCase())).length;
  const bad = records.filter((r) => BAD.has(String(r.status || "").toLowerCase())).length;

  const statuses = ["all", ...Array.from(new Set(records.map((r) => r.status).filter(Boolean)))];
  const filtered = statusFilter === "all" ? records : records.filter((r) => r.status === statusFilter);

  return (
    <>
      <Topbar title={title} subtitle={subtitle} onRefresh={runManualPipeline} refreshing={loading} flagged={bad} />

      <div style={{ display: "flex", gap: 14, marginBottom: 16, flexWrap: "wrap" }}>
        <StatCard icon={Icon} label="Analyzed logs" value={total.toLocaleString()} delta={0} />
        <StatCard icon={CheckCircle2} label="Healthy Event Log" value={ok.toLocaleString()} delta={0} />
        <StatCard icon={AlertTriangle} label="Anomalies Flagged" value={bad.toLocaleString()} delta={0} deltaGood={false} />
      </div>

      <div className="card" style={{ padding: "16px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12, flexWrap: "wrap", gap: 8 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>Event Matrix</div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {statuses.map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`btn-cyber ${statusFilter === s ? "active" : ""}`}
                style={{
                  fontSize: 10.5,
                  padding: "5px 11px",
                  textTransform: "capitalize",
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <EventTable records={filtered} loading={loading} emptyLabel={`No ${logType} events parsed yet. Wait for simulator logs or run pipeline manually.`} />
      </div>
    </>
  );
}
