import React from "react";
import { Shield, Lock, Globe, CheckCircle2, AlertTriangle } from "lucide-react";

const BAD_STATUSES = new Set(["blocked", "dropped", "failed", "locked", "nxdomain", "servfail", "refused"]);
const OK_STATUSES = new Set(["allowed", "success", "noerror"]);

function statusColor(status) {
  const s = String(status || "").toLowerCase();
  if (BAD_STATUSES.has(s)) return "var(--red)";
  if (OK_STATUSES.has(s)) return "var(--green)";
  return "var(--amber)";
}

function typeIcon(type) {
  if (type === "firewall") return Shield;
  if (type === "auth") return Lock;
  return Globe;
}

function detailFor(record) {
  return record.user || record.domain || record.target_ip || "—";
}

export default function EventTable({ records, loading, emptyLabel = "No events yet.", onRowClick }) {
  return (
    <div className="mono" style={{ fontSize: 11.5 }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "110px 76px 130px 170px 100px 1fr",
          padding: "7px 12px",
          color: "var(--text-faint)",
          fontSize: 10,
          letterSpacing: "0.04em",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div>EVENT ID</div>
        <div>TYPE</div>
        <div>SOURCE IP</div>
        <div>DETAIL</div>
        <div>STATUS</div>
        <div>TIME</div>
      </div>

      <div style={{ maxHeight: 420, overflowY: "auto" }}>
        {loading && (
          <div style={{ padding: "24px 12px", color: "var(--text-muted)", fontFamily: "var(--font-sans)" }}>
            Loading events…
          </div>
        )}

        {!loading && records.length === 0 && (
          <div style={{ padding: "24px 12px", color: "var(--text-muted)", fontFamily: "var(--font-sans)" }}>
            {emptyLabel}
          </div>
        )}

        {!loading &&
          records.map((r) => {
            const Icon = typeIcon(r.log_type);
            const flagged = BAD_STATUSES.has(String(r.status || "").toLowerCase());
            return (
              <div
                key={r.event_id}
                onClick={onRowClick ? () => onRowClick(r) : undefined}
                style={{
                  display: "grid",
                  gridTemplateColumns: "110px 76px 130px 170px 100px 1fr",
                  padding: "9px 12px",
                  borderBottom: "1px solid var(--border)",
                  alignItems: "center",
                  background: flagged ? "rgba(225,67,67,0.05)" : "transparent",
                  cursor: onRowClick ? "pointer" : "default",
                }}
              >
                <div style={{ color: "var(--text-muted)" }}>{r.event_id}</div>
                <div style={{ display: "flex", alignItems: "center", gap: 5, color: "var(--text)" }}>
                  <Icon size={11} color="var(--red)" strokeWidth={2} />
                  {r.log_type}
                </div>
                <div style={{ color: "var(--text)" }}>{r.source_ip}</div>
                <div style={{ color: "var(--text-secondary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {detailFor(r)}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 5, color: statusColor(r.status) }}>
                  {flagged ? <AlertTriangle size={11} /> : <CheckCircle2 size={11} />}
                  {r.status}
                </div>
                <div style={{ color: "var(--text-faint)" }}>
                  {r.timestamp ? new Date(r.timestamp).toLocaleString() : "—"}
                </div>
              </div>
            );
          })}
      </div>
    </div>
  );
}
