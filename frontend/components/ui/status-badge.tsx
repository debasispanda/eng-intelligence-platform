type StatusBadgeProps = {
  value: "On Track" | "At Risk" | "Delayed" | "Low" | "Medium" | "High";
};

export function StatusBadge({ value }: StatusBadgeProps) {
  const tone =
    value === "On Track" || value === "Low"
      ? "badge-positive"
      : value === "At Risk" || value === "Medium"
        ? "badge-warning"
        : "badge-critical";

  return (
    <span className={`status-badge ${tone}`} aria-label={`status ${value}`}>
      {value}
    </span>
  );
}
