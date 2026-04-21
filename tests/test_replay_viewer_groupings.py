from __future__ import annotations

from pathlib import Path

from playwright.sync_api import expect, sync_playwright

VIEWER_PATH = Path(__file__).resolve().parents[1] / "demo" / "replay" / "viewer.html"


def test_replay_viewer_groups_cat28_profiles_for_file_mode() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(VIEWER_PATH.as_uri(), wait_until="domcontentloaded")
            page.wait_for_function(
                "() => document.querySelectorAll('#profile optgroup option').length === 15"
            )

            groups = page.eval_on_selector_all(
                "#profile optgroup",
                """(nodes) => nodes.map((group) => ({
                    label: group.label,
                    count: group.querySelectorAll("option").length,
                    values: [...group.querySelectorAll("option")].map((option) => option.value),
                    labels: [...group.querySelectorAll("option")].map((option) => option.textContent)
                }))""",
            )
            assert groups == [
                {
                    "label": "Criminology - Tier 1",
                    "count": 4,
                    "values": [
                        "fbi-organized",
                        "fbi-disorganized",
                        "canter-geographic-a",
                        "kicrim-fraud-archetype",
                    ],
                    "labels": [
                        "FBI organized archetype",
                        "FBI disorganized archetype",
                        "Canter geographic archetype A",
                        "KICRIM fraud archetype",
                    ],
                },
                {
                    "label": "Criminology - Tier 2 Historical",
                    "count": 3,
                    "values": ["whitechapel-1888", "holmes-1890s", "gunness-1900s"],
                    "labels": [
                        "Whitechapel 1888",
                        "H.H. Holmes 1890s",
                        "Belle Gunness 1900s",
                    ],
                },
                {
                    "label": "Personality - CAT-28 (Tier 5)",
                    "count": 8,
                    "values": [
                        "cat28-tsundere",
                        "cat28-kuudere",
                        "cat28-dandere",
                        "cat28-genki",
                        "cat28-chuunibyou",
                        "cat28-oneesan",
                        "cat28-yankee",
                        "cat28-intellectual",
                    ],
                    "labels": [
                        "CAT-28 Tsundere (pedagogical)",
                        "CAT-28 Kuudere (pedagogical)",
                        "CAT-28 Dandere (pedagogical)",
                        "CAT-28 Genki (pedagogical)",
                        "CAT-28 Chuunibyou (pedagogical)",
                        "CAT-28 Oneesan (pedagogical)",
                        "CAT-28 Yankee (pedagogical)",
                        "CAT-28 Intellectual (pedagogical)",
                    ],
                },
            ]
            assert page.locator("#profile > option[disabled]").count() == 1
        finally:
            browser.close()


def test_replay_viewer_tier5_selection_requires_personality_notice() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(VIEWER_PATH.as_uri(), wait_until="domcontentloaded")
            page.wait_for_function(
                "() => document.querySelectorAll('#profile optgroup option').length === 15"
            )
            page.evaluate("sessionStorage.clear()")

            page.select_option("#profile", "cat28-tsundere")

            expect(page.locator("#ethics")).to_be_visible()
            expect(page.locator("#ethics-personality-note")).to_be_visible()
            expect(page.locator("#ethics-accept")).to_be_disabled()

            page.locator("#ethics-check").check()
            expect(page.locator("#ethics-accept")).to_be_enabled()
            page.locator("#ethics-accept").click()

            expect(page.locator("#ethics")).not_to_be_visible()
            expect(page.locator("#status")).to_contain_text("Archetype overlay injected")
        finally:
            browser.close()
