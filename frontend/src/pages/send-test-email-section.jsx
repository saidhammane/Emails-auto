import { useState } from "react";

import { getApiErrorMessage } from "../api/client";
import { sendTestEmail } from "../api/email-dashboard-api";
import { FeedbackMessage } from "../components/feedback-message";
import { Panel } from "../components/panel";

const initialFormState = {
  to: "",
  subject: "",
  body: "",
};

export function SendTestEmailSection({ onActionComplete }) {
  const [formState, setFormState] = useState(initialFormState);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState({ type: "", message: "" });

  function handleChange(event) {
    const { name, value } = event.target;
    setFormState((currentState) => ({ ...currentState, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    try {
      setSubmitting(true);
      setFeedback({ type: "", message: "" });

      const response = await sendTestEmail(formState);
      setFeedback({ type: "success", message: response.message });
      onActionComplete();
    } catch (requestError) {
      setFeedback({
        type: "error",
        message: getApiErrorMessage(requestError, "Failed to send test email."),
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Panel
      id="send-test"
      title="Send Test Email"
      description="Send a single test message directly through the backend SMTP endpoint."
    >
      <form className="stacked-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>To</span>
          <input
            type="email"
            name="to"
            value={formState.to}
            onChange={handleChange}
            placeholder="recipient@example.com"
            required
          />
        </label>

        <label className="field">
          <span>Subject</span>
          <input
            type="text"
            name="subject"
            value={formState.subject}
            onChange={handleChange}
            placeholder="Test email subject"
            required
          />
        </label>

        <label className="field">
          <span>Body</span>
          <textarea
            name="body"
            value={formState.body}
            onChange={handleChange}
            rows="5"
            placeholder="Write a short test message"
            required
          />
        </label>

        <button className="primary-button" type="submit" disabled={submitting}>
          {submitting ? "Sending..." : "Send test email"}
        </button>
      </form>

      <FeedbackMessage type={feedback.type} message={feedback.message} />
    </Panel>
  );
}
