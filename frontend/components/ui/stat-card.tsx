type StatCardProps = {
  title: string;
  value: string;
  delta: string;
  trend: "up" | "down" | "flat";
};

export function StatCard({ title, value, delta, trend }: StatCardProps) {
  const trendLabel = trend === "up" ? "Rising" : trend === "down" ? "Improving" : "Stable";
  const trendClass = trend === "up" ? "trend-up" : trend === "down" ? "trend-down" : "trend-flat";

  return (
    <article className="stat-card">
      <p className="stat-title">{title}</p>
      <p className="stat-value">{value}</p>
      <p className={`stat-delta ${trendClass}`}>
        <span>{trendLabel}</span>
        <span>{delta}</span>
      </p>
    </article>
  );
}
