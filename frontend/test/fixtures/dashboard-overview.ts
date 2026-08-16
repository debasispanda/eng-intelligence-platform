import type {
  EpicTimelineRow,
  HotRepository,
  KpiCard,
  ReleaseRow,
  UserProfile,
} from "@/lib/dashboard-types";

export const dashboardData = {
  appTitle: "Engineering Intelligence",
  profile: {
    name: "Riley Chen",
    role: "VP Engineering",
    email: "riley.chen@example.com",
    avatarInitials: "RC",
  } satisfies UserProfile,
  kpis: [
    { title: "Open PRs", value: "38", delta: "+6 this week", trend: "up" },
    { title: "Merged PRs", value: "124", delta: "+14 this week", trend: "up" },
    {
      title: "Failed Builds",
      value: "11",
      delta: "-3 since last week",
      trend: "down",
    },
    {
      title: "Blocked Tickets",
      value: "19",
      delta: "+2 since yesterday",
      trend: "up",
    },
  ] satisfies KpiCard[],
  releases: [
    {
      name: "Platform 2.8",
      owner: "Core Services",
      status: "On Track",
      completion: 74,
      date: "2026-08-04",
    },
    {
      name: "Web App 5.2",
      owner: "Frontend",
      status: "At Risk",
      completion: 58,
      date: "2026-07-29",
    },
  ] satisfies ReleaseRow[],
  offTimelineEpics: [
    {
      epic: "Tenant Isolation Upgrade",
      owner: "Platform Security",
      delayedByDays: 9,
      risk: "High",
    },
  ] satisfies EpicTimelineRow[],
  hotRepositories: {
    mostActive: [
      { repository: "frontend-app", metric: 36, label: "PRs this week" },
      { repository: "platform-api", metric: 31, label: "PRs this week" },
    ] satisfies HotRepository[],
    mostFailed: [
      { repository: "platform-api", metric: 7, label: "failed builds" },
      { repository: "mobile-sdk", metric: 5, label: "failed builds" },
    ] satisfies HotRepository[],
  },
};
