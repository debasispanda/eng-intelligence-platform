import { describe, expect, it, vi } from "vitest";
import { getDashboardOverview } from "@/lib/dashboard-api";
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

  it("surfaces an unsuccessful overview response", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(null, { status: 503 }),
    );

    await expect(getDashboardOverview(fetcher)).rejects.toThrow(
      "Dashboard overview request failed with status 503.",
    );
  });
});
