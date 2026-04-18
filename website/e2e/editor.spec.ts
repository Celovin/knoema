import { expect, test } from "@playwright/test";

test("exports YAML after editing scenario title", async ({ page }) => {
  await page.goto("/editor");
  await page.getByTestId("scenario-title").fill("Library Orientation Drill");
  await page.getByTestId("prepare-export").click();

  await expect(page.getByTestId("yaml-preview")).toContainText(
    'title: "Library Orientation Drill"',
  );
  await expect(page.getByTestId("export-status")).toHaveText("Export ready");
});

test("drags a palette agent into the scene", async ({ page }) => {
  await page.goto("/editor");
  const before = await page.locator("[data-testid^='agent-']").count();

  await page.getByTestId("palette-observer").dragTo(page.getByTestId("scene-canvas"));

  await expect(page.locator("[data-testid^='agent-']")).toHaveCount(before + 1);
  await expect(page.getByTestId("yaml-preview")).toContainText("observer_1");
});

test("updates agent and timeline fields in the YAML preview", async ({ page }) => {
  await page.goto("/editor");
  await page.getByTestId("agent-mentor_1").click();
  await page.getByTestId("agent-name").fill("Guide");
  await page.getByTestId("event-description-event_1").fill(
    "Guide checks the setup and gives the newcomer a first station.",
  );

  await expect(page.getByTestId("yaml-preview")).toContainText('name: "Guide"');
  await expect(page.getByTestId("yaml-preview")).toContainText(
    "first station",
  );
});
