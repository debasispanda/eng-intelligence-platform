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

export type RiskAssessment = {
  entityType: "epic" | "release";
  entityId: string;
  title: string;
  risk: "Low" | "Medium" | "High";
  score: number;
  confidence: number;
  ruleVersion: string;
  factors: string[];
};
