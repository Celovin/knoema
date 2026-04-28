from __future__ import annotations

import ast
import inspect
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import gradio as gr

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_FILE = REPO_ROOT / "playground" / "app.py"

# Kwargs that Gradio moves between ``Blocks`` constructor and ``launch``
# across major versions but keeps accepting on the OLD location with a
# deprecation warning. The guard treats these as compatible (the runtime
# does not raise) so a deprecation does not become a CI hard fail. List
# is keyed by the call shape they are passed to.
_DEPRECATED_BLOCKS_KWARGS: frozenset[str] = frozenset({"css", "head"})


def _accepts_var_keyword(signature: inspect.Signature) -> bool:
    """Return ``True`` when the callable accepts ``**kwargs``.

    Gradio 6 routes ``css`` / ``head`` through ``**kwargs`` on the
    ``Blocks`` constructor (with a deprecation warning at runtime).
    Treating any VAR_KEYWORD-accepting signature as 'permissive on the
    deprecated kwarg list' lets the guard keep catching genuine typos
    without false-flagging the deprecation path.
    """

    return any(
        param.kind is inspect.Parameter.VAR_KEYWORD
        for param in signature.parameters.values()
    )


@dataclass(frozen=True, slots=True)
class CompatibilityIssue:
    line: int
    call_name: str
    keyword: str
    message: str


def _keyword_issues(
    tree: ast.AST,
    *,
    attribute_name: str,
    call_name: str,
    allowed_keywords: set[str],
) -> list[CompatibilityIssue]:
    issues: list[CompatibilityIssue] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != attribute_name:
            continue
        for keyword in node.keywords:
            if keyword.arg is None or keyword.arg in allowed_keywords:
                continue
            issues.append(
                CompatibilityIssue(
                    line=keyword.value.lineno,
                    call_name=call_name,
                    keyword=keyword.arg,
                    message=(
                        f"{call_name} keyword '{keyword.arg}' is not supported by the installed "
                        f"Gradio signature."
                    ),
                )
            )
    return issues


def _blocks_issues(tree: ast.AST) -> list[CompatibilityIssue]:
    blocks_sig = inspect.signature(gr.Blocks)
    allowed_keywords = set(blocks_sig.parameters)
    # Gradio 6 routed the historical ``css`` / ``head`` constructor
    # kwargs through ``**kwargs`` with a deprecation warning. The guard
    # accepts these so the existing main playground app does not regress
    # against the live Gradio signature; a future major Gradio release
    # that drops the deprecation entirely will surface here as a real
    # incompat.
    if _accepts_var_keyword(blocks_sig):
        allowed_keywords |= _DEPRECATED_BLOCKS_KWARGS
    issues: list[CompatibilityIssue] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if not isinstance(func.value, ast.Name) or func.value.id != "gr" or func.attr != "Blocks":
            continue
        for keyword in node.keywords:
            if keyword.arg is None or keyword.arg in allowed_keywords:
                continue
            issues.append(
                CompatibilityIssue(
                    line=keyword.value.lineno,
                    call_name="gr.Blocks(...)",
                    keyword=keyword.arg,
                    message=(
                        f"gr.Blocks(...) keyword '{keyword.arg}' is not supported by the installed "
                        f"Gradio signature."
                    ),
                )
            )
    return issues


def find_compatibility_issues(source: str) -> list[CompatibilityIssue]:
    tree = ast.parse(source)
    launch_keywords = set(inspect.signature(gr.Blocks.launch).parameters)
    issues = _blocks_issues(tree)
    issues.extend(
        _keyword_issues(
            tree,
            attribute_name="launch",
            call_name=".launch(...)",
            allowed_keywords=launch_keywords,
        )
    )
    return sorted(issues, key=lambda issue: (issue.line, issue.call_name, issue.keyword))


def _format_issues(path: Path, issues: Iterable[CompatibilityIssue]) -> str:
    lines = [f"Gradio compatibility check failed for {path}:"]
    for issue in issues:
        lines.append(f"  line {issue.line}: {issue.message}")
    return "\n".join(lines)


def main() -> int:
    source = TARGET_FILE.read_text(encoding="utf-8")
    issues = find_compatibility_issues(source)
    if issues:
        print(_format_issues(TARGET_FILE, issues), file=sys.stderr)
        return 1
    print(f"Gradio compatibility OK: {TARGET_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
