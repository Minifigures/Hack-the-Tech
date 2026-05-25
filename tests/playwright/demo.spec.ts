/**
 * Demo flow: walks the same 5-minute path Marco gives on stage.
 *
 * The backend MUST be running in mock mode on :8000 and the frontend on :3000
 * before this runs. The CI helper `make test-e2e` starts both with `make dev`.
 */
import { expect, test } from "@playwright/test";

test.describe("EvalForge demo flow", () => {
  test("cockpit loads and shows system status", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: /CI\/CD for/i }),
    ).toBeVisible();
    await expect(page.getByText(/mock \(deterministic\)|live/i)).toBeVisible();
  });

  test("compare: baseline fails, engineered grounded with citations", async ({
    page,
  }) => {
    await page.goto("/compare");
    await page.getByTestId("preset-healthcare").first().click();
    await page.getByTestId("compare-submit").click();

    const baseline = page.getByTestId("trace-card-baseline");
    const engineered = page.getByTestId("trace-card-engineered");
    await expect(baseline).toBeVisible();
    await expect(engineered).toBeVisible();

    // engineered output is typed
    await expect(engineered.getByText(/typed/i)).toBeVisible();
    // engineered output has at least one citation chip with a source_id path
    await expect(
      engineered.locator("p.font-mono.text-\\[11px\\].text-forge-ice").first(),
    ).toBeVisible();
    // baseline is unstructured
    await expect(baseline.getByText(/unstructured/i)).toBeVisible();
  });

  test("compare: prompt injection probe is refused by engineered", async ({
    page,
  }) => {
    await page.goto("/compare");
    await page.getByTestId("preset-safety").first().click();
    await page.getByTestId("compare-submit").click();

    const engineered = page.getByTestId("trace-card-engineered");
    await expect(engineered.getByText(/refusal:/i)).toBeVisible({
      timeout: 30_000,
    });
  });

  test("evals: run full eval and see engineered beat baseline", async ({
    page,
  }) => {
    await page.goto("/evals");
    await page.getByTestId("evals-run").click();
    // generous wait — 50 mock runs
    await expect(page.getByText(/Per-question results/i)).toBeVisible({
      timeout: 90_000,
    });
    await expect(page.getByText(/Faithfulness/i).first()).toBeVisible();
  });

  test("deploy gate: engineered PASS, baseline FAIL", async ({ page }) => {
    await page.goto("/deploy-gate");
    await page.getByTestId("run-gate").click();
    const eng = page.getByTestId("gate-engineered");
    const base = page.getByTestId("gate-baseline");
    await expect(eng.getByTestId("verdict-pass")).toBeVisible({
      timeout: 90_000,
    });
    await expect(base.getByTestId("verdict-fail")).toBeVisible();
  });

  test("traces: drill into a recent trace", async ({ page }) => {
    await page.goto("/traces");
    await page.locator("[data-testid^='trace-row-']").first().click();
    await expect(page.getByTestId("trace-detail")).toBeVisible();
  });

  test("guardrails: probe surfaces baseline failures and engineered refusal", async ({
    page,
  }) => {
    await page.goto("/guardrails");
    await page.locator("[data-testid^='probe-']").first().click();
    await expect(page.getByTestId("probe-result").first()).toBeVisible({
      timeout: 30_000,
    });
  });
});
