import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end tests: a real browser driving the real app against a real
 * backend, unlike `tests/unit` (component-level, mocked APIs). Both
 * `webServer` entries are started fresh for the run and torn down after -
 * `run_e2e_server.sh` migrates and seeds its own dedicated database every
 * time, so a run here never depends on (or pollutes) local dev data or
 * `pytest`'s own database.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: "list",
  timeout: 30_000,
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "bash ../backend/scripts/run_e2e_server.sh",
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: "npm run dev",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
});
