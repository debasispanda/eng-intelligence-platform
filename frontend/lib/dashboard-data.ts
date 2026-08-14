export type UserProfile = {
  name: string;
  role: string;
  email: string;
  avatarInitials: string;
};

export type KpiCard = {
  title: string;
  value: string;
  delta: string;
  trend: "up" | "down" | "flat";
};

export type ReleaseRow = {
  name: string;
  owner: string;
  status: "On Track" | "At Risk" | "Delayed";
  completion: number;
  date: string;
};

export type EpicTimelineRow = {
  epic: string;
  owner: string;
  delayedByDays: number;
  risk: "Low" | "Medium" | "High";
};

export type HotRepository = {
  repository: string;
  metric: number;
  label: string;
};

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
    {
      title: "Merged PRs",
      value: "124",
      delta: "+14 this week",
      trend: "up",
    },
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
    {
      name: "Data Sync 1.9",
      owner: "Data Platform",
      status: "Delayed",
      completion: 41,
      date: "2026-08-11",
    },
    {
      name: "Mobile SDK 3.3",
      owner: "Developer Experience",
      status: "On Track",
      completion: 67,
      date: "2026-08-08",
    },
  ] satisfies ReleaseRow[],
  offTimelineEpics: [
    {
      epic: "Tenant Isolation Upgrade",
      owner: "Platform Security",
      delayedByDays: 9,
      risk: "High",
    },
    {
      epic: "Unified Metrics Pipeline",
      owner: "Data Platform",
      delayedByDays: 6,
      risk: "Medium",
    },
    {
      epic: "Checkout Latency Program",
      owner: "Growth Engineering",
      delayedByDays: 4,
      risk: "Medium",
    },
    {
      epic: "Observability Coverage",
      owner: "SRE",
      delayedByDays: 2,
      risk: "Low",
    },
  ] satisfies EpicTimelineRow[],
  hotRepositories: {
    mostActive: [
      { repository: "frontend-app", metric: 36, label: "PRs this week" },
      { repository: "platform-api", metric: 31, label: "PRs this week" },
      { repository: "event-router", metric: 27, label: "PRs this week" },
      { repository: "data-sync", metric: 22, label: "PRs this week" },
    ] satisfies HotRepository[],
    mostFailed: [
      { repository: "platform-api", metric: 7, label: "failed builds" },
      { repository: "mobile-sdk", metric: 5, label: "failed builds" },
      { repository: "data-sync", metric: 4, label: "failed builds" },
      { repository: "frontend-app", metric: 3, label: "failed builds" },
    ] satisfies HotRepository[],
  },
};
