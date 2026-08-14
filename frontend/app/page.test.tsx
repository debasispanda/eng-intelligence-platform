import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Home from "@/app/page";
import { dashboardData } from "@/lib/dashboard-data";

describe("Dashboard page", () => {
  it("renders the core KPI cards", () => {
    render(<Home />);

    expect(screen.getByText("Open PRs")).toBeInTheDocument();
    expect(screen.getByText("Merged PRs")).toBeInTheDocument();
    expect(screen.getByText("Failed Builds")).toBeInTheDocument();
    expect(screen.getByText("Blocked Tickets")).toBeInTheDocument();
  });

  it("renders release rows and epics table", () => {
    render(<Home />);

    expect(screen.getByText("Release Status")).toBeInTheDocument();
    expect(screen.getByText("Platform 2.8")).toBeInTheDocument();
    expect(screen.getByText("Epics Off Timeline")).toBeInTheDocument();
    expect(screen.getByText("Tenant Isolation Upgrade")).toBeInTheDocument();
  });

  it("keeps release rows structured for narrow layouts", () => {
    render(<Home />);

    const releaseTable = screen.getByRole("table", { name: "Release status rows" });

    expect(within(releaseTable).getAllByRole("columnheader")).toHaveLength(5);
    expect(within(releaseTable).getAllByRole("row")).toHaveLength(
      dashboardData.releases.length + 1,
    );
  });

  it("renders both hot repository lists", () => {
    render(<Home />);

    expect(screen.getByText("Hot Repositories: Most Active")).toBeInTheDocument();
    expect(screen.getByText("Hot Repositories: Most Failed")).toBeInTheDocument();
    expect(screen.getAllByText("frontend-app").length).toBeGreaterThan(1);
    expect(screen.getByText("mobile-sdk")).toBeInTheDocument();
  });
});
