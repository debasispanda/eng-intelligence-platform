import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "node stub-backend.mjs live 8100",
      url: "http://127.0.0.1:8100/health",
      reuseExistingServer: false,
    },
    {
      command: "node stub-backend.mjs error 8101",
      url: "http://127.0.0.1:8101/health",
      reuseExistingServer: false,
    },
    {
      command:
        "cd .. && BACKEND_API_BASE_URL=http://127.0.0.1:8100 npm run start -- --hostname 127.0.0.1 --port 3100",
      url: "http://127.0.0.1:3100",
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command:
        "cd .. && BACKEND_API_BASE_URL=http://127.0.0.1:8101 npm run start -- --hostname 127.0.0.1 --port 3101",
      url: "http://127.0.0.1:3101",
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
