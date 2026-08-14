import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AppHeader } from "@/components/header/app-header";
import { dashboardData } from "@/lib/dashboard-data";

describe("AppHeader", () => {
  it("renders brand title and profile avatar", () => {
    render(<AppHeader appTitle={dashboardData.appTitle} profile={dashboardData.profile} />);

    expect(screen.getByText("Engineering Intelligence")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open profile menu" })).toBeInTheDocument();
  });

  it("opens dropdown with user details and signout", () => {
    render(<AppHeader appTitle={dashboardData.appTitle} profile={dashboardData.profile} />);

    fireEvent.click(screen.getByRole("button", { name: "Open profile menu" }));

    expect(screen.getByText("Riley Chen")).toBeInTheDocument();
    expect(screen.getByText("VP Engineering")).toBeInTheDocument();
    expect(screen.getByText("riley.chen@example.com")).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Sign out" })).toBeInTheDocument();
  });

  it("closes the dropdown on escape", () => {
    render(<AppHeader appTitle={dashboardData.appTitle} profile={dashboardData.profile} />);

    fireEvent.click(screen.getByRole("button", { name: "Open profile menu" }));
    fireEvent.keyDown(document, { key: "Escape" });

    expect(screen.queryByRole("menu", { name: "User menu" })).not.toBeInTheDocument();
  });
});
