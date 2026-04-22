from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

FORBIDDEN_STRINGS = tuple(
    "".join(parts)
    for parts in (
        ("Lith", "eon"),
        ("Sei", "zn"),
        ("Ovr", "iel"),
        ("Fang", "den"),
        ("Not", "rivo"),
        ("Milky", "pix"),
        ("Ya", "mi"),
        ("Qwen", "3.5-35B-A3B"),
    )
)


def _markdown_table(path: Path) -> dict[str, dict[str, str]]:
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0] == "---" or cells[0] == "Tier":
            continue
        if cells[0] in {"Free", "Pro", "Team", "Enterprise"}:
            rows.append(cells)

    return {
        row[0]: {
            "price": row[1],
            "token_cap": row[2],
        }
        for row in rows
    }


class PricingTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: dict[str, dict[str, str]] = {}
        self._in_table = False
        self._active_row: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {name: value or "" for name, value in attrs}
        if tag == "table" and attr.get("data-pricing-table") == "tiers":
            self._in_table = True
            return
        if tag == "tr" and self._in_table and "data-tier" in attr:
            self._active_row = {
                "tier": attr["data-tier"],
                "price": attr["data-price"],
                "token_cap": attr["data-token-cap"],
            }

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self._active_row is not None:
            tier = self._active_row.pop("tier")
            self.rows[tier] = self._active_row
            self._active_row = None
            return
        if tag == "table" and self._in_table:
            self._in_table = False


def _html_table(path: Path) -> dict[str, dict[str, str]]:
    parser = PricingTableParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.rows


def test_pricing_markdown_and_static_html_have_identical_prices_and_caps() -> None:
    markdown = _markdown_table(Path("docs/pricing.md"))
    html = _html_table(Path("site-snapshot/pricing.html"))

    assert markdown == {
        "Free": {"price": "$0/mo", "token_cap": "100,000 output tokens"},
        "Pro": {"price": "$49/mo", "token_cap": "2,000,000 output tokens"},
        "Team": {"price": "$199/mo", "token_cap": "10,000,000 output tokens"},
        "Enterprise": {"price": "Contact sales", "token_cap": "Contract-specific"},
    }
    assert html == markdown


def test_pricing_pages_do_not_include_forbidden_strings() -> None:
    for path in (Path("docs/pricing.md"), Path("site-snapshot/pricing.html")):
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_STRINGS:
            assert forbidden not in text


def test_pricing_static_html_is_self_contained() -> None:
    html = Path("site-snapshot/pricing.html").read_text(encoding="utf-8")

    assert "<link" not in html
    assert "<script" not in html
    assert "@import" not in html
    assert len(html.encode("utf-8")) < 30_000
