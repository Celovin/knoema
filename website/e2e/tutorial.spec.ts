import { expect, test } from "@playwright/test";

test("runs and completes the first tutorial chapter", async ({ page }) => {
  await page.goto("/tutorial");
  await page.getByTestId("run-chapter").click();

  await expect(page.getByTestId("run-output")).toContainText("Maya is ready");
  await page.getByLabel("values").check();
  await page.getByTestId("complete-chapter").click();
  await expect(page.getByLabel("Progress 20%")).toBeVisible();
});

test("edits code and preserves a Monaco-compatible editor surface", async ({ page }) => {
  await page.goto("/tutorial");
  await page.getByLabel("Monaco code editor").fill("print('hello from tutorial')");
  await page.getByTestId("run-chapter").click();

  await expect(page.locator("[data-monaco-editor='true']")).toBeVisible();
  await expect(page.getByTestId("run-output")).toContainText("1 edited lines checked");
});
