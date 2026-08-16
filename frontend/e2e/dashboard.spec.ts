import { expect, test } from "@playwright/test";

test.describe("connected dashboard", () => {
  test("renders live overview data and the profile menu", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByText("Open PRs")).toBeVisible();
    await expect(page.getByText("Platform 2.8")).toBeVisible();
    await expect(page.getByText("frontend-app")).toBeVisible();

    await page.getByRole("button", { name: "Open profile menu" }).click();
    await expect(page.getByRole("menu")).toContainText("Riley Chen");
    await expect(page.getByRole("menuitem", { name: "Sign out" })).toBeVisible();
  });
});

test.describe("dashboard failure state", () => {
  test("shows an explicit backend error", async ({ page }) => {
    await page.goto("http://127.0.0.1:3101/");

    await expect(page.getByRole("status")).toContainText("Dashboard unavailable");
    await expect(page.getByRole("status")).toContainText("backend connection");
  });
});

test.describe("dashboard themes", () => {
  test("preserves the light theme", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.goto("/");

    await expect(page.locator("body")).toHaveCSS("background-color", "rgb(255, 255, 255)");
  });

  test("preserves the dark theme", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto("/");

    await expect(page.locator("body")).toHaveCSS("background-color", "rgb(0, 0, 0)");
  });
});
