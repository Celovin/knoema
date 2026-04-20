from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import pytest
from playwright.sync_api import Page, expect, sync_playwright

LIVE_SPACE_URL: Final[str] = "https://huggingface.co/spaces/celovin/knoema-playground"
SPACE_IFRAME_SELECTOR: Final[str] = "iframe[aria-label='Space app']"
SCREENSHOT_DIR = Path("artifacts")
EXPECT_FORCE_GRAPH = os.environ.get("KNOEMA_EXPECT_FORCE_GRAPH") == "1"


def _set_slider_value(page: Page, *, elem_id: str, value: int) -> None:
    app_frame = page.frame_locator(SPACE_IFRAME_SELECTOR)
    slider_inputs = app_frame.locator(
        f"#{elem_id} input[type='range'], #{elem_id} input[type='number'], #{elem_id} input"
    )
    expect(slider_inputs.first).to_be_visible(timeout=15_000)
    slider_inputs.evaluate_all(
        """(elements, nextValue) => {
            for (const element of elements) {
                element.value = String(nextValue);
                element.dispatchEvent(new Event("input", { bubbles: true }));
                element.dispatchEvent(new Event("change", { bubbles: true }));
            }
        }""",
        value,
    )


def _screenshot_path(prefix: str = "live-graph") -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return SCREENSHOT_DIR / f"{prefix}-{timestamp}.png"


@pytest.fixture(scope="module")
def page() -> Page:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        page.set_default_timeout(15_000)
        try:
            yield page
        finally:
            browser.close()


def test_live_space_smoke_flow(page: Page) -> None:
    page.goto(LIVE_SPACE_URL, wait_until="domcontentloaded", timeout=15_000)
    expect(page.locator(SPACE_IFRAME_SELECTOR)).to_be_visible(timeout=15_000)
    app_frame = page.frame_locator(SPACE_IFRAME_SELECTOR)
    expect(app_frame.locator("#run-button")).to_be_visible(timeout=30_000)
    scenario_input = app_frame.locator("#scenario-dropdown input[role='listbox']")
    expect(scenario_input).to_be_visible(timeout=15_000)
    scenario_input.click()
    expect(app_frame.get_by_role("option", name="\uae30\uc219\uc0ac", exact=False)).to_be_visible(
        timeout=15_000
    )
    scenario_input.press("Escape")

    _set_slider_value(page, elem_id="agent-count-slider", value=5)
    page.wait_for_timeout(750)
    app_frame.locator("#run-button").click()

    page.wait_for_timeout(15_000)

    visible_error_badges = app_frame.locator("span.error:visible")
    visible_error_texts = [
        (visible_error_badges.nth(index).text_content() or "").strip()
        for index in range(visible_error_badges.count())
    ]
    assert visible_error_texts.count("\uc624\ub958") == 0

    graph = app_frame.locator("#relationship-graph")
    expect(graph).to_be_visible(timeout=15_000)
    graph_iframe = app_frame.locator("#relationship-graph iframe")
    if EXPECT_FORCE_GRAPH:
        expect(graph_iframe).to_have_count(1, timeout=45_000)
    if graph_iframe.count():
        force_graph_frame = app_frame.frame_locator("#relationship-graph iframe")
        canvas = force_graph_frame.locator("canvas")
        expect(canvas).to_be_visible(timeout=15_000)

        before_path = _screenshot_path("live-graph-before")
        after_path = _screenshot_path("live-graph")
        canvas.screenshot(path=str(before_path))

        box = canvas.bounding_box()
        assert box is not None
        start_x = box["x"] + (box["width"] * 0.5)
        start_y = box["y"] + (box["height"] * 0.5)
        page.mouse.move(start_x, start_y)
        page.mouse.down()
        page.mouse.move(start_x + 140, start_y + 36, steps=16)
        page.mouse.up()
        page.wait_for_timeout(1_200)

        canvas.screenshot(path=str(after_path))
        assert before_path.read_bytes() != after_path.read_bytes()
        screenshot_path = after_path
    else:
        if EXPECT_FORCE_GRAPH:
            raise AssertionError("force-directed graph iframe missing from live Space")
        screenshot_path = _screenshot_path()
        graph.screenshot(path=str(screenshot_path))

    assert screenshot_path.exists()
    assert screenshot_path.stat().st_size > 0
