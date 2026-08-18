import type {
  DashboardOverview,
  DeliverySummary,
  RiskAssessment,
} from "@/lib/dashboard-types";

export type {
  DashboardOverview,
  DeliverySummary,
  RiskAssessment,
} from "@/lib/dashboard-types";

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

export async function getRiskAssessments(
  fetcher: typeof fetch = fetch,
): Promise<RiskAssessment[]> {
  const response = await fetcher(
    new URL("/dashboard/risks", dashboardApiBaseUrl),
    { cache: "no-store", headers: { Accept: "application/json" } },
  );

  if (!response.ok) {
    throw new Error(`Risk assessments request failed with status ${response.status}.`);
  }

  return response.json();
}

export async function getDeliverySummary(
  fetcher: typeof fetch = fetch,
): Promise<DeliverySummary> {
  const response = await fetcher(
    new URL("/dashboard/summary", dashboardApiBaseUrl),
    { cache: "no-store", headers: { Accept: "application/json" } },
  );

  if (!response.ok) {
    throw new Error(`Delivery summary request failed with status ${response.status}.`);
  }

  return response.json();
}
