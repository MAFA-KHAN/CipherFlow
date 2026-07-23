import React from "react";
import { Lock } from "lucide-react";
import LogTypeView from "../components/LogTypeView.jsx";

export default function AuthLogs() {
  return (
    <LogTypeView
      logType="auth"
      icon={Lock}
      title="Authentication"
      subtitle="Login, logout, and lockout events parsed from identity provider logs"
    />
  );
}
