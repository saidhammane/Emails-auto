import { useEffect, useState } from "react";

import { getApiErrorMessage } from "../api/client";
import { getAnalyticsSummary } from "../api/email-dashboard-api";
import { FeedbackMessage } from "../components/feedback-message";
import { MetricCard } from "../components/metric-card";
import { Panel } from "../components/panel";

const emptySummary = {
  total_sent: 0,
  total_failed: 0,
  total_scheduled: 0,
  success_rate: 0,
  failure_rate: 0,
};

function formatRate(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

export function DashboardOverviewSection({ refreshKey }) {
  const [summary, setSummary] = useState(emptySummary);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadSummary() {
      try {
        setLoading(true);
        setError("");
        const response = await getAnalyticsSummary();

        if (isMounted) {
          setSummary(response);
        }
      } catch (requestError) {
        if (isMounted) {
          setError(
            getApiErrorMessage(requestError, "Unable to load dashboard summary."),
          );
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    void loadSummary();

    return () => {
      isMounted = false;
    };
  }, [refreshKey]);

  return (
    <Panel
      id="overview"
      title="Dashboard Overview"
      description="A quick snapshot of sending performance from the existing analytics API."
      action={loading ? <span className="panel-note">Refreshing...</span> : null}
    >
      <FeedbackMessage type="error" message={error} />

      <div className="metrics-grid">
        <MetricCard
          label="Total sent"
          value={summary.total_sent}
          hint="Emails delivered successfully"
        />
        <MetricCard
          label="Total failed"
          value={summary.total_failed}
          hint="Send attempts that failed"
        />
        <MetricCard
          label="Total scheduled"
          value={summary.total_scheduled}
          hint="Jobs waiting to run"
        />
        <MetricCard
          label="Success rate"
          value={formatRate(summary.success_rate)}
          hint="Sent versus attempted"
        />
        <MetricCard
          label="Failure rate"
          value={formatRate(summary.failure_rate)}
          hint="Failed versus attempted"
        />
      </div>
    </Panel>
  );
}
