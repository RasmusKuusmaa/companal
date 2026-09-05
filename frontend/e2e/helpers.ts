import type { Page } from "@playwright/test";

/**
 * Registers a fresh account through the real UI and lands on the
 * dashboard, logged in - the starting point every e2e spec needs. A new,
 * randomized email every call so specs never collide with a previous run's
 * leftover user in the e2e database.
 */
export async function registerNewUser(page: Page): Promise<{ email: string }> {
  const email = `e2e-${Date.now()}-${Math.random().toString(36).slice(2)}@example.com`;

  await page.goto("/register");
  await page.getByLabel("Full name").fill("E2E Test Student");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill("a-secure-password-1");
  await page.getByLabel("Confirm password").fill("a-secure-password-1");
  await page.getByRole("button", { name: "Create account" }).click();

  await page.waitForURL("/");
  return { email };
}
