import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Home from "@/app/page";
import Loading from "@/app/loading";
import { DashboardProvider } from "@/components/dashboard/dashboard-provider";
import type { DashboardOverview } from "@/lib/dashboard-types";
import type { RiskAssessment } from "@/lib/dashboard-types";
import { dashboardData } from "@/test/fixtures/dashboard-overview";

function renderDashboard(
  overview: DashboardOverview | null = dashboardData,
  error: string | null = null,
  risks: RiskAssessment[] = [],
  riskError: string | null = null,
) {
  return render(
    <DashboardProvider
      error={error}
      overview={overview}
      riskError={riskError}
      risks={risks}
    >
      <Home />
    </DashboardProvider>,
  );
}

describe("Dashboard page", () => {
  it("renders the core KPI cards", () => {
    renderDashboard();

    expect(screen.getByText("Open PRs")).toBeInTheDocument();
    expect(screen.getByText("Merged PRs")).toBeInTheDocument();
    expect(screen.getByText("Failed Builds")).toBeInTheDocument();
    expect(screen.getByText("Blocked Tickets")).toBeInTheDocument();
  });

  it("renders release rows and epics table", () => {
    renderDashboard();

    expect(screen.getByText("Release Status")).toBeInTheDocument();
    expect(screen.getByText("Platform 2.8")).toBeInTheDocument();
    expect(screen.getByText("Epics Off Timeline")).toBeInTheDocument();
    expect(screen.getByText("Tenant Isolation Upgrade")).toBeInTheDocument();
  });

  it("keeps release rows structured for narrow layouts", () => {
    renderDashboard();

    const releaseTable = screen.getByRole("table", { name: "Release status rows" });

    expect(within(releaseTable).getAllByRole("columnheader")).toHaveLength(5);
    expect(within(releaseTable).getAllByRole("row")).toHaveLength(
      dashboardData.releases.length + 1,
    );
  });

  it("renders both hot repository lists", () => {
    renderDashboard();

    expect(screen.getByText("Hot Repositories: Most Active")).toBeInTheDocument();
    expect(screen.getByText("Hot Repositories: Most Failed")).toBeInTheDocument();
    expect(screen.getByText("frontend-app")).toBeInTheDocument();
    expect(screen.getByText("mobile-sdk")).toBeInTheDocument();
  });

  it("renders risk intelligence assessments", () => {
    renderDashboard(dashboardData, null, [
      {
        entityType: "epic",
        entityId: "epic-1",
        title: "Tenant Isolation Upgrade",
        risk: "High",
        score: 85,
        confidence: 0.95,
        ruleVersion: "risk-v1",
        factors: ["Source risk is High."],
      },
    ]);

    expect(screen.getByText("Risk Intelligence")).toBeInTheDocument();
    expect(screen.getAllByText("Tenant Isolation Upgrade")).toHaveLength(2);
    expect(screen.getByText("85")).toBeInTheDocument();
  });

  it("renders an explicit empty state", () => {
    renderDashboard({
      ...dashboardData,
      kpis: [],
      releases: [],
      offTimelineEpics: [],
      hotRepositories: { mostActive: [], mostFailed: [] },
    });

    expect(screen.getByRole("status")).toHaveTextContent("No dashboard data yet");
  });

  it("renders an explicit backend error state", () => {
    renderDashboard(null, "Dashboard data is unavailable.");

    expect(screen.getByRole("status")).toHaveTextContent("Dashboard unavailable");
    expect(screen.getByText("Dashboard data is unavailable.")).toBeInTheDocument();
  });

  it("renders a loading state", () => {
    render(<Loading />);

    expect(screen.getByRole("status", { name: "Loading dashboard" })).toHaveTextContent(
      "Loading dashboard data...",
    );
  });
});
