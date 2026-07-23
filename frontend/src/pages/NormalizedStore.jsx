import React, { useContext, useState } from "react";
import { Database } from "lucide-react";
import Topbar from "../components/Topbar.jsx";
import EventTable from "../components/EventTable.jsx";
import { SimulationContext } from "../components/Layout.jsx";

const SCHEMA = [
  ["event_id", "string", "Unique identifier generated per normalized event"],
  ["timestamp", "ISO-8601", "Event time, normalized to UTC"],
  ["source_ip", "string", "Originating IP address, validated"],
  ["target_ip", "string | null", "Destination IP address, firewall events only"],
  ["user", "string | null", "Authenticated identity, auth events only"],
  ["action", "string", "Normalized action label, e.g. LOGIN, QUERY, TCP_CONNECT"],
  ["status", "string", "Outcome of the event as reported by the source"],
  ["log_type", "firewall | auth | dns", "Origin of the raw log line"],
  ["original_line", "string", "The unparsed source line, kept for audit"],
  ["parsed_at", "ISO-8601", "When log_parser.py normalized this record"],
];

export default function NormalizedStore() {
  const sim = useContext(SimulationContext);
  const [selected, setSelected] = useState(null);

  if (!sim || !sim.stats) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "40vh" }}>
        <div className="mono" style={{ fontSize: 13, color: "var(--text-muted)", display: "flex", gap: 10, alignItems: "center" }}>
          <span className="pulse-dot" style={{ width: 6, height: 6 }} />
          INITIALIZING Unified Database Feed...
        </div>
      </div>
    );
  }

  const { records, loading, runManualPipeline } = sim;

  return (
    <>
      <Topbar
        title="Normalized Data Store"
        subtitle="output_normalized.jsonl — Unified index of parsed logs from firewall, authentication, and DNS"
        onRefresh={runManualPipeline}
        refreshing={loading}
      />

      <div style={{ display: "flex", gap: 14, marginBottom: 16, flexWrap: "wrap" }}>
        {/* Schema Viewer */}
        <div className="card" style={{ flex: 2, minWidth: 320, padding: "16px 20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <Database size={15} color="var(--red)" />
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>Unified Security Schema</div>
          </div>
          <div className="mono" style={{ fontSize: 11 }}>
            {SCHEMA.map(([field, type, desc]) => (
              <div
                key={field}
                style={{
                  display: "grid", gridTemplateColumns: "130px 140px 1fr", gap: 10,
                  padding: "6px 0", borderBottom: "1px solid var(--border)",
                }}
              >
                <div style={{ color: "var(--red)" }}>{field}</div>
                <div style={{ color: "var(--amber)" }}>{type}</div>
                <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-sans)" }}>{desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Record Detail */}
        <div className="card active-card" style={{ flex: 1, minWidth: 240, padding: "16px 20px" }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 12 }}>Inspect Record Payload</div>
          {selected ? (
            <pre
              className="mono"
              style={{
                fontSize: 10.5, color: "var(--text-secondary)", whiteSpace: "pre-wrap",
                wordBreak: "break-all", margin: 0, maxHeight: 260, overflowY: "auto",
                background: "var(--card-2)", padding: 10, borderRadius: 6, border: "1px solid var(--border)"
              }}
            >
              {JSON.stringify(selected, null, 2)}
            </pre>
          ) : (
            <div style={{ fontSize: 12, color: "var(--text-faint)" }}>
              Click an ingestion record row below to audit its JSON payload.
            </div>
          )}
        </div>
      </div>

      <div className="card" style={{ padding: "16px 20px" }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 12 }}>
          Live Stream Records Store ({records.length})
        </div>
        <EventTable records={records} loading={loading} onRowClick={setSelected} />
      </div>
    </>
  );
}
