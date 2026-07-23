import React from "react";
import { Globe } from "lucide-react";
import LogTypeView from "../components/LogTypeView.jsx";

export default function DnsActivity() {
  return (
    <LogTypeView
      logType="dns"
      icon={Globe}
      title="DNS activity"
      subtitle="Resolver queries parsed from DNS server logs, including failed and suspicious lookups"
    />
  );
}
