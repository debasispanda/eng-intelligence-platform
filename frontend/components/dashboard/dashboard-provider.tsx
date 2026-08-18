"use client";

import { createContext, useContext } from "react";
import type { ReactNode } from "react";
import type { DashboardOverview, RiskAssessment } from "@/lib/dashboard-types";

type DashboardContextValue = {
  error: string | null;
  overview: DashboardOverview | null;
  riskError: string | null;
  risks: RiskAssessment[];
};

const DashboardContext = createContext<DashboardContextValue | null>(null);

type DashboardProviderProps = DashboardContextValue & {
  children: ReactNode;
};

export function DashboardProvider({
  children,
  error,
  overview,
  riskError,
  risks,
}: DashboardProviderProps) {
  return (
    <DashboardContext.Provider value={{ error, overview, riskError, risks }}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboardData(): DashboardContextValue {
  const value = useContext(DashboardContext);
  if (value === null) {
    throw new Error("DashboardProvider is required to render dashboard data.");
  }

  return value;
}
