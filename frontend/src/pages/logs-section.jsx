import { useEffect, useState } from "react";

import { getApiErrorMessage } from "../api/client";
import { getEmailLogs } from "../api/email-dashboard-api";
import { FeedbackMessage } from "../components/feedback-message";
import { Panel } from "../components/panel";
import { StatusPill } from "../components/status-pill";

function formatTimestamp(timestamp) {
  const parsedDate = new Date(timestamp);

  if (Number.isNaN(parsedDate.getTime())) {
    return timestamp;
  }

  return parsedDate.toLocaleString();
}

export function LogsSection({ refreshKey }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadLogs() {
      try {
        setLoading(true);
        setError("");
        const response = await getEmailLogs();

        if (isMounted) {
          setLogs(response);
        }
      } catch (requestError) {
        if (isMounted) {
          setError(getApiErrorMessage(requestError, "Unable to load email logs."));
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    void loadLogs();

    return () => {
      isMounted = false;
    };
  }, [refreshKey]);

  return (
    <Panel
      id="logs"
      title="Logs"
      description="Review recent email activity recorded by the backend."
    >
      <FeedbackMessage type="error" message={error} />

      <div className="table-shell">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Email</th>
              <th>Subject</th>
              <th>Status</th>
              <th>Error</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {!loading && logs.length === 0 ? (
              <tr>
                <td colSpan="6" className="empty-cell">
                  No email logs available yet.
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.id}</td>
                  <td>{log.email}</td>
                  <td>{log.subject}</td>
                  <td>
                    <StatusPill value={log.status} />
                  </td>
                  <td>{log.error_message || "-"}</td>
                  <td>{formatTimestamp(log.timestamp)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
