import React from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Overview from "./pages/Overview.jsx";
import FirewallLogs from "./pages/FirewallLogs.jsx";
import AuthLogs from "./pages/AuthLogs.jsx";
import DnsActivity from "./pages/DnsActivity.jsx";
import NormalizedStore from "./pages/NormalizedStore.jsx";
import QualityValidator from "./pages/QualityValidator.jsx";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/firewall" element={<FirewallLogs />} />
        <Route path="/auth" element={<AuthLogs />} />
        <Route path="/dns" element={<DnsActivity />} />
        <Route path="/store" element={<NormalizedStore />} />
        <Route path="/validator" element={<QualityValidator />} />
      </Routes>
    </Layout>
  );
}
