import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/playwright",
  timeout: 60_000,
  retries: 0,
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    video: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: devices["Desktop Chrome"] }],
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
});
