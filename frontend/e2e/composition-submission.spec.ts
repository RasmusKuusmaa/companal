import { expect, test } from "@playwright/test";

import { registerNewUser } from "./helpers";

/**
 * A student writes something in the staff editor and submits it for
 * grading. This deliberately doesn't try to satisfy the lesson's actual
 * requirements (key, meter, cadence, ...) - that's the deterministic
 * grader's own territory, covered exhaustively by the backend's test
 * suite. What this checks is the pipeline a unit test can't: the editor's
 * keyboard entry produces a real document, submitting it reaches the API,
 * and a verdict - pass or fail - comes back and renders.
 */
test("a student enters notes in the editor and submits them for grading", async ({ page }) => {
  await registerNewUser(page);

  await page.goto("/learn/simple-and-compound-meter");

  // Past the reading step and both quiz checks to reach the composition task.
  await page.getByRole("button", { name: "Next" }).click();
  await page.getByRole("radio").first().check();
  await page.getByRole("button", { name: "Check answer" }).click();
  await page.getByRole("button", { name: "Next" }).click();
  await page.getByRole("radio").first().check();
  await page.getByRole("button", { name: "Check answer" }).click();
  await page.getByRole("button", { name: "Next" }).click();

  await expect(page.getByText("Write a four-measure melody in 6/8 time.")).toBeVisible();

  // Focus the staff editor and enter a few notes via its keyboard shortcuts
  // (see NotationEditor.vue's own handleKeydown) - the same input path a
  // student typing at the keyboard uses, not a direct document mutation.
  const editor = page.locator("[tabindex='0']").first();
  await editor.click();
  for (const key of ["c", "d", "e", "c", "d", "e"]) {
    await editor.press(key);
  }

  await page.getByRole("button", { name: "Submit", exact: true }).click();
  await expect(page.getByRole("status").getByText(/every requirement met|not quite there yet/i)).toBeVisible();
});
