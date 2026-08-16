export default function Loading() {
  return (
    <div className="dashboard-loading" aria-label="Loading dashboard" role="status">
      <span className="dashboard-loading-indicator" aria-hidden="true" />
      Loading dashboard data...
    </div>
  );
}
