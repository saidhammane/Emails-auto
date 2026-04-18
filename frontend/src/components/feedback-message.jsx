export function FeedbackMessage({ type = "info", message }) {
  if (!message) {
    return null;
  }

  return <div className={`feedback-message feedback-message-${type}`}>{message}</div>;
}
