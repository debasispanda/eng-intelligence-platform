import type { DashboardOverview } from "@/lib/dashboard-types";

export type { DashboardOverview } from "@/lib/dashboard-types";

const dashboardApiBaseUrl =
  process.env.BACKEND_API_BASE_URL ?? "http://localhost:8000";

export async function getDashboardOverview(
  fetcher: typeof fetch = fetch,
): Promise<DashboardOverview> {
  const response = await fetcher(
    new URL("/dashboard/overview", dashboardApiBaseUrl),
    { cache: "no-store", headers: { Accept: "application/json" } },
  );

  if (!response.ok) {
    throw new Error(`Dashboard overview request failed with status ${response.status}.`);
  }

  return response.json();
}
