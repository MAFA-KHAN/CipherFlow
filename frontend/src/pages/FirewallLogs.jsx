import React from "react";
import { Shield } from "lucide-react";
import LogTypeView from "../components/LogTypeView.jsx";

export default function FirewallLogs() {
  return (
    <LogTypeView
      logType="firewall"
      icon={Shield}
      title="Firewall logs"
      subtitle="Connection-level events parsed from perimeter firewall output"
    />
  );
}
