import { describe, expect, it, vi } from "vitest";
import { getDashboardOverview, getRiskAssessments } from "@/lib/dashboard-api";
import { dashboardData } from "@/test/fixtures/dashboard-overview";

describe("getDashboardOverview", () => {
  it("returns the typed dashboard overview response", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(dashboardData), { status: 200 }),
    );

    await expect(getDashboardOverview(fetcher)).resolves.toEqual(dashboardData);
    expect(fetcher).toHaveBeenCalledWith(
      new URL("http://localhost:8000/dashboard/overview"),
      { cache: "no-store", headers: { Accept: "application/json" } },
    );
  });

  describe("getRiskAssessments", () => {
    it("returns risk assessments from the risk endpoint", async () => {
      const risks = [
        {
          entityType: "epic",
          entityId: "epic-1",
          title: "Tenant Isolation Upgrade",
          risk: "High",
          score: 85,
          confidence: 0.95,
          ruleVersion: "risk-v2",
          factors: ["Source risk is High."],
        },
      ];
      const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
        new Response(JSON.stringify(risks), { status: 200 }),
      );

      await expect(getRiskAssessments(fetcher)).resolves.toEqual(risks);
      expect(fetcher).toHaveBeenCalledWith(
        new URL("http://localhost:8000/dashboard/risks"),
        { cache: "no-store", headers: { Accept: "application/json" } },
      );
    });
  });

  it("surfaces an unsuccessful overview response", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(null, { status: 503 }),
    );

    await expect(getDashboardOverview(fetcher)).rejects.toThrow(
      "Dashboard overview request failed with status 503.",
    );
  });
});
