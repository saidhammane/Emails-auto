import { useState } from "react";

import { getApiErrorMessage } from "../api/client";
import { sendBulkEmail } from "../api/email-dashboard-api";
import { FeedbackMessage } from "../components/feedback-message";
import { MetricCard } from "../components/metric-card";
import { Panel } from "../components/panel";

const initialFormState = {
  file: null,
  subjectTemplate: "",
  bodyTemplate: "",
};

function IssueList({ title, items }) {
  if (!items?.length) {
    return null;
  }

  return (
    <div className="issue-list-card">
      <h4>{title}</h4>
      <ul className="issue-list">
        {items.map((item, index) => (
          <li key={`${title}-${item.row}-${item.email}-${index}`}>
            <strong>Row {item.row}</strong>
            <span>{item.email || "No email provided"}</span>
            <span>{item.reason}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function BulkEmailSection({ onActionComplete }) {
  const [formState, setFormState] = useState(initialFormState);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState({ type: "", message: "" });
  const [result, setResult] = useState(null);

  function handleInputChange(event) {
    const { name, value } = event.target;
    setFormState((currentState) => ({ ...currentState, [name]: value }));
  }

  function handleFileChange(event) {
    setFormState((currentState) => ({
      ...currentState,
      file: event.target.files?.[0] || null,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    try {
      setSubmitting(true);
      setFeedback({ type: "", message: "" });

      const response = await sendBulkEmail({
        file: formState.file,
        subject_template: formState.subjectTemplate,
        body_template: formState.bodyTemplate,
      });

      setResult(response);
      setFeedback({ type: "success", message: response.message });
      onActionComplete();
    } catch (requestError) {
      setResult(null);
      setFeedback({
        type: "error",
        message: getApiErrorMessage(requestError, "Bulk email request failed."),
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Panel
      id="bulk-email"
      title="Bulk Email Upload"
      description="Upload a CSV or XLSX file and send personalized emails in one pass."
    >
      <form className="stacked-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>Recipient file</span>
          <input
            type="file"
            accept=".csv,.xlsx"
            onChange={handleFileChange}
            required
          />
        </label>

        <label className="field">
          <span>Subject template</span>
          <input
            type="text"
            name="subjectTemplate"
            value={formState.subjectTemplate}
            onChange={handleInputChange}
            placeholder="Welcome {{name}}"
            required
          />
        </label>

        <label className="field">
          <span>Body template</span>
          <textarea
            name="bodyTemplate"
            value={formState.bodyTemplate}
            onChange={handleInputChange}
            rows="5"
            placeholder="Hello {{name}}, welcome to {{company}}."
            required
          />
        </label>

        <button className="primary-button" type="submit" disabled={submitting}>
          {submitting ? "Sending..." : "Send bulk email"}
        </button>
      </form>

      <FeedbackMessage type={feedback.type} message={feedback.message} />

      {result ? (
        <div className="stacked-results">
          <div className="metrics-grid">
            <MetricCard label="Total rows" value={result.total_rows} hint="Rows uploaded" />
            <MetricCard label="Valid rows" value={result.valid_rows} hint="Rows ready to send" />
            <MetricCard label="Sent" value={result.sent_count} hint="Emails sent successfully" />
            <MetricCard label="Failed" value={result.failed_count} hint="Rows that failed to send" />
            <MetricCard label="Skipped" value={result.skipped_count} hint="Rows ignored safely" />
          </div>

          <div className="two-column-grid">
            <IssueList title="Failures" items={result.failures} />
            <IssueList title="Skipped rows" items={result.skipped} />
          </div>
        </div>
      ) : null}
    </Panel>
  );
}
