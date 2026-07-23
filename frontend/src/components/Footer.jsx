import React from "react";
import { ShieldCheck } from "lucide-react";

export default function Footer() {
  return (
    <footer
      style={{
        marginTop: 28,
        paddingTop: 16,
        borderTop: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 10,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 11.5, color: "var(--text-faint)" }}>
        <ShieldCheck size={13} color="var(--red-dim)" />
        CipherFlow — Security Log Processing &amp; Validation Pipeline
      </div>
      <div className="mono" style={{ fontSize: 11, color: "var(--text-faint)" }}>
        Powered by <span style={{ color: "var(--red)" }}>Mafa</span>
      </div>
    </footer>
  );
}
