import type {
  EpicTimelineRow,
  HotRepository,
  KpiCard,
  ReleaseRow,
  UserProfile,
} from "@/lib/dashboard-data";

export type DashboardOverview = {
  appTitle: string;
  profile: UserProfile;
  kpis: KpiCard[];
  releases: ReleaseRow[];
  offTimelineEpics: EpicTimelineRow[];
  hotRepositories: {
    mostActive: HotRepository[];
    mostFailed: HotRepository[];
  };
};

const dashboardApiBaseUrl =
  process.env.BACKEND_API_BASE_URL ?? "http://localhost:8000";

export async function getDashboardOverview(
  fetcher: typeof fetch = fetch,
): Promise<DashboardOverview> {
  const response = await fetcher(
    new URL("/dashboard/overview", dashboardApiBaseUrl),
    { headers: { Accept: "application/json" } },
  );

  if (!response.ok) {
    throw new Error(`Dashboard overview request failed with status ${response.status}.`);
  }

  return response.json();
}
