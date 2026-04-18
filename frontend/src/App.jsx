import { useState } from "react";

import { AnalyticsSection } from "./pages/analytics-section";
import { BulkEmailSection } from "./pages/bulk-email-section";
import { DashboardOverviewSection } from "./pages/dashboard-overview-section";
import { LogsSection } from "./pages/logs-section";
import { ScheduleEmailSection } from "./pages/schedule-email-section";
import { SendTestEmailSection } from "./pages/send-test-email-section";

const sectionLinks = [
  { href: "#overview", label: "Overview" },
  { href: "#send-test", label: "Send Test Email" },
  { href: "#bulk-email", label: "Bulk Email" },
  { href: "#schedule", label: "Schedule Email" },
  { href: "#logs", label: "Logs" },
  { href: "#analytics", label: "Analytics" },
];

function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  function handleDataChanged() {
    setRefreshKey((currentKey) => currentKey + 1);
  }

  return (
    <div className="app-shell">
      <header className="hero-card">
        <div className="hero-copy">
          <span className="eyebrow">Email Dashboard &amp; Automation Tool</span>
          <h1>Frontend dashboard for sending, scheduling, logs, and analytics</h1>
          <p>
            This React dashboard connects directly to the existing FastAPI backend
            and keeps the flow simple for local demo and iteration.
          </p>
        </div>

        <nav className="section-nav" aria-label="Dashboard sections">
          {sectionLinks.map((item) => (
            <a key={item.href} href={item.href} className="section-link">
              {item.label}
            </a>
          ))}
        </nav>
      </header>

      <main className="dashboard-layout">
        <DashboardOverviewSection refreshKey={refreshKey} />
        <SendTestEmailSection onActionComplete={handleDataChanged} />
        <BulkEmailSection onActionComplete={handleDataChanged} />
        <ScheduleEmailSection onActionComplete={handleDataChanged} />
        <LogsSection refreshKey={refreshKey} />
        <AnalyticsSection refreshKey={refreshKey} />
      </main>
    </div>
  );
}

export default App;
