import { expect, test } from "@playwright/test";

import { registerNewUser } from "./helpers";

/**
 * A student's full path through one lesson: read the passage, answer both
 * checks (right or wrong is never gating - see `LessonView`'s own docs),
 * and mark it complete. `staff-clefs-and-ledger-lines` is the curriculum's
 * first lesson (`stage0.py`) and has no composition step, so this covers
 * reading + quiz steps; `composition-submission.spec.ts` covers the third
 * kind separately.
 */
test("a student reads a lesson, answers its checks, and completes it", async ({ page }) => {
  await registerNewUser(page);

  await page.goto("/learn");
  // The very first lesson is also where a fresh account's "Continue" banner
  // points, so its link appears on the roadmap twice - the banner and its
  // own card in the course list. Either is the same destination.
  await page.getByRole("link", { name: /staff, clefs and ledger lines/i }).first().click();
  await expect(page).toHaveURL("/learn/staff-clefs-and-ledger-lines");

  // Step 1: reading. The passage's own opening line, not the page's h1 -
  // the reading content renders its own markdown heading with the same
  // title text, and asserting on that would be ambiguous between the two.
  await expect(page.getByText(/music is written on a/i)).toBeVisible();
  await page.getByRole("button", { name: "Next" }).click();

  // Step 2: the first quiz check - answering doesn't have to be correct to
  // move on, but the verdict and explanation should still appear.
  await page.getByRole("radio").first().check();
  await page.getByRole("button", { name: "Check answer" }).click();
  await expect(page.getByRole("status")).toContainText(/correct|not quite/i);
  await page.getByRole("button", { name: "Next" }).click();

  // Step 3: the second quiz check.
  await page.getByRole("radio").first().check();
  await page.getByRole("button", { name: "Check answer" }).click();
  await expect(page.getByRole("status")).toContainText(/correct|not quite/i);

  // No more steps - this is where `LessonCompletion` takes over.
  await expect(page.getByRole("button", { name: "Next" })).toHaveCount(0);
  await page.getByRole("button", { name: "Mark lesson complete" }).click();
  await expect(page.getByRole("heading", { name: "Lesson complete" })).toBeVisible();
});
