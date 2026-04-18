const STATUS_CLASS_NAMES = {
  sent: "status-pill status-pill-success",
  failed: "status-pill status-pill-danger",
  scheduled: "status-pill status-pill-warning",
};

export function StatusPill({ value }) {
  const normalizedValue = (value || "unknown").toLowerCase();
  const className = STATUS_CLASS_NAMES[normalizedValue] || "status-pill";

  return <span className={className}>{normalizedValue}</span>;
}
