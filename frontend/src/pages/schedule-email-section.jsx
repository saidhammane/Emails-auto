import { useState } from "react";

import { getApiErrorMessage } from "../api/client";
import {
  scheduleBulkEmail,
  scheduleEmail,
} from "../api/email-dashboard-api";
import { FeedbackMessage } from "../components/feedback-message";
import { Panel } from "../components/panel";

const initialSingleScheduleState = {
  to: "",
  subject: "",
  body: "",
  sendAt: "",
};

const initialBulkScheduleState = {
  file: null,
  subjectTemplate: "",
  bodyTemplate: "",
  sendAt: "",
};

function ScheduleResult({ label, value }) {
  if (!value) {
    return null;
  }

  return (
    <div className="schedule-result">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function ScheduleEmailSection({ onActionComplete }) {
  const [singleForm, setSingleForm] = useState(initialSingleScheduleState);
  const [bulkForm, setBulkForm] = useState(initialBulkScheduleState);
  const [singleSubmitting, setSingleSubmitting] = useState(false);
  const [bulkSubmitting, setBulkSubmitting] = useState(false);
  const [singleFeedback, setSingleFeedback] = useState({ type: "", message: "" });
  const [bulkFeedback, setBulkFeedback] = useState({ type: "", message: "" });
  const [singleScheduledFor, setSingleScheduledFor] = useState("");
  const [bulkScheduledFor, setBulkScheduledFor] = useState("");

  function handleSingleInputChange(event) {
    const { name, value } = event.target;
    setSingleForm((currentState) => ({ ...currentState, [name]: value }));
  }

  function handleBulkInputChange(event) {
    const { name, value } = event.target;
    setBulkForm((currentState) => ({ ...currentState, [name]: value }));
  }

  function handleBulkFileChange(event) {
    setBulkForm((currentState) => ({
      ...currentState,
      file: event.target.files?.[0] || null,
    }));
  }

  async function handleSingleSubmit(event) {
    event.preventDefault();

    try {
      setSingleSubmitting(true);
      setSingleFeedback({ type: "", message: "" });

      const response = await scheduleEmail({
        to: singleForm.to,
        subject: singleForm.subject,
        body: singleForm.body,
        send_at: singleForm.sendAt,
      });

      setSingleScheduledFor(response.scheduled_for || "");
      setSingleFeedback({ type: "success", message: response.message });
      onActionComplete();
    } catch (requestError) {
      setSingleScheduledFor("");
      setSingleFeedback({
        type: "error",
        message: getApiErrorMessage(requestError, "Failed to schedule the email."),
      });
    } finally {
      setSingleSubmitting(false);
    }
  }

  async function handleBulkSubmit(event) {
    event.preventDefault();

    try {
      setBulkSubmitting(true);
      setBulkFeedback({ type: "", message: "" });

      const response = await scheduleBulkEmail({
        file: bulkForm.file,
        subject_template: bulkForm.subjectTemplate,
        body_template: bulkForm.bodyTemplate,
        send_at: bulkForm.sendAt,
      });

      setBulkScheduledFor(response.scheduled_for || "");
      setBulkFeedback({ type: "success", message: response.message });
      onActionComplete();
    } catch (requestError) {
      setBulkScheduledFor("");
      setBulkFeedback({
        type: "error",
        message: getApiErrorMessage(
          requestError,
          "Failed to schedule the bulk email job.",
        ),
      });
    } finally {
      setBulkSubmitting(false);
    }
  }

  return (
    <Panel
      id="schedule"
      title="Schedule Email"
      description="Schedule single or bulk sends using the backend scheduler."
    >
      <div className="two-column-grid">
        <div className="panel-block">
          <h3>Schedule single email</h3>
          <form className="stacked-form" onSubmit={handleSingleSubmit}>
            <label className="field">
              <span>To</span>
              <input
                type="email"
                name="to"
                value={singleForm.to}
                onChange={handleSingleInputChange}
                placeholder="recipient@example.com"
                required
              />
            </label>

            <label className="field">
              <span>Subject</span>
              <input
                type="text"
                name="subject"
                value={singleForm.subject}
                onChange={handleSingleInputChange}
                placeholder="Scheduled email subject"
                required
              />
            </label>

            <label className="field">
              <span>Body</span>
              <textarea
                name="body"
                value={singleForm.body}
                onChange={handleSingleInputChange}
                rows="5"
                placeholder="Message to send later"
                required
              />
            </label>

            <label className="field">
              <span>Send at</span>
              <input
                type="datetime-local"
                name="sendAt"
                value={singleForm.sendAt}
                onChange={handleSingleInputChange}
                required
              />
            </label>

            <button className="primary-button" type="submit" disabled={singleSubmitting}>
              {singleSubmitting ? "Scheduling..." : "Schedule single email"}
            </button>
          </form>

          <FeedbackMessage type={singleFeedback.type} message={singleFeedback.message} />
          <ScheduleResult label="Scheduled for" value={singleScheduledFor} />
        </div>

        <div className="panel-block">
          <h3>Schedule bulk email</h3>
          <form className="stacked-form" onSubmit={handleBulkSubmit}>
            <label className="field">
              <span>Recipient file</span>
              <input
                type="file"
                accept=".csv,.xlsx"
                onChange={handleBulkFileChange}
                required
              />
            </label>

            <label className="field">
              <span>Subject template</span>
              <input
                type="text"
                name="subjectTemplate"
                value={bulkForm.subjectTemplate}
                onChange={handleBulkInputChange}
                placeholder="Welcome {{name}}"
                required
              />
            </label>

            <label className="field">
              <span>Body template</span>
              <textarea
                name="bodyTemplate"
                value={bulkForm.bodyTemplate}
                onChange={handleBulkInputChange}
                rows="5"
                placeholder="Hello {{name}}, welcome to {{company}}."
                required
              />
            </label>

            <label className="field">
              <span>Send at</span>
              <input
                type="datetime-local"
                name="sendAt"
                value={bulkForm.sendAt}
                onChange={handleBulkInputChange}
                required
              />
            </label>

            <button className="primary-button" type="submit" disabled={bulkSubmitting}>
              {bulkSubmitting ? "Scheduling..." : "Schedule bulk email"}
            </button>
          </form>

          <FeedbackMessage type={bulkFeedback.type} message={bulkFeedback.message} />
          <ScheduleResult label="Scheduled for" value={bulkScheduledFor} />
        </div>
      </div>
    </Panel>
  );
}
