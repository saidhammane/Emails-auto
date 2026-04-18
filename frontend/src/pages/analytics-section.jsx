import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getApiErrorMessage } from "../api/client";
import { getAnalyticsDaily, getAnalyticsErrors } from "../api/email-dashboard-api";
import { FeedbackMessage } from "../components/feedback-message";
import { Panel } from "../components/panel";

export function AnalyticsSection({ refreshKey }) {
  const [dailyData, setDailyData] = useState([]);
  const [errorData, setErrorData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadAnalytics() {
      try {
        setLoading(true);
        setError("");

        const [dailyResponse, errorResponse] = await Promise.all([
          getAnalyticsDaily(),
          getAnalyticsErrors(),
        ]);

        if (!isMounted) {
          return;
        }

        setDailyData(dailyResponse);
        setErrorData(errorResponse);
      } catch (requestError) {
        if (!isMounted) {
          return;
        }

        setError(
          getApiErrorMessage(requestError, "Unable to load analytics right now."),
        );
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    void loadAnalytics();

    return () => {
      isMounted = false;
    };
  }, [refreshKey]);

  return (
    <Panel
      id="analytics"
      title="Analytics"
      description="Track daily sending activity and the most common failure reasons."
    >
      <FeedbackMessage type="error" message={error} />

      <div className="two-column-grid">
        <div className="panel-block">
          <h3>Daily activity</h3>
          <p className="panel-block-copy">Sent and failed email counts grouped by date.</p>
          <div className="chart-shell">
            {loading ? (
              <p className="muted-text">Loading analytics...</p>
            ) : dailyData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" tickLine={false} axisLine={false} />
                  <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="sent_count" fill="#0f766e" name="Sent" radius={[6, 6, 0, 0]} />
                  <Bar
                    dataKey="failed_count"
                    fill="#dc2626"
                    name="Failed"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="muted-text">No daily activity has been logged yet.</p>
            )}
          </div>
        </div>

        <div className="panel-block">
          <h3>Common errors</h3>
          <p className="panel-block-copy">Most frequent failed-email error messages.</p>
          <div className="table-shell">
            <table>
              <thead>
                <tr>
                  <th>Error message</th>
                  <th>Count</th>
                </tr>
              </thead>
              <tbody>
                {!loading && errorData.length === 0 ? (
                  <tr>
                    <td colSpan="2" className="empty-cell">
                      No failed email errors logged yet.
                    </td>
                  </tr>
                ) : (
                  errorData.map((item) => (
                    <tr key={`${item.error_message}-${item.count}`}>
                      <td>{item.error_message}</td>
                      <td>{item.count}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Panel>
  );
}
