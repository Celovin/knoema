from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")
deposit_module = importlib.import_module("luvoire.research.deposit")


def test_subtask65_korean_labels_do_not_reuse_english_user_facing_copy() -> None:
    allowed_identical_keys = {"environment_default", "routine_text_placeholder"}
    identical_labels = {
        key: ko_value
        for key, ko_value in playground_app.LABELS["ko"].items()
        if key not in allowed_identical_keys
        and isinstance(ko_value, str)
        and ko_value == playground_app.LABELS["en"].get(key)
    }

    assert identical_labels == {}, f"unlocalized Korean labels: {sorted(identical_labels)}"


def test_subtask65_korean_scenario_labels_are_curated_for_demo_choices() -> None:
    localized = {
        scenario_name: label
        for label, scenario_name in playground_simulation.scenario_choices_localized("ko")
    }

    assert len(localized) == 30
    assert localized["Startup pivot meeting"] == "스타트업 방향 전환 회의"
    assert localized["Classroom pop quiz"] == "교실 깜짝 퀴즈"
    assert localized["Tech demo day"] == "기술 데모 데이"
    assert localized["Wedding after-party"] == "결혼식 뒤풀이"
    assert localized["Zoom team standup"] == "줌 팀 스탠드업 회의"
    assert localized["Senior center chess"] == "노인복지관 체스 모임"
    assert localized["Concert lobby intermission"] == "콘서트 로비 휴식 시간"


def test_subtask65_preregistration_preview_uses_korean_section_headings() -> None:
    markdown = playground_app._preregistration_markdown(
        "실행 요약",
        "",
        playground_app.KOREAN_CHOICE,
        "기숙사 협력 연구",
        "친화성이 협력 행동을 높인다.",
        "결정론적 재생으로 비교한다.",
        "협력 행동 비율",
        "배치 비교 후 해석한다.",
        True,
        "",
    )

    assert "## OSF 형식 사전등록" in markdown
    assert "### 연구 제목" in markdown
    assert "### 첨부 실행 근거" in markdown
    assert "- 아직 첨부된 실행 결과가 없습니다." in markdown
    assert "### Study title" not in markdown
    assert "### Attached run evidence" not in markdown


def test_subtask65_deposit_status_markdown_uses_korean_field_labels() -> None:
    result = deposit_module.ZenodoDepositResult(
        mode="local_draft",
        bundle_path=Path("deposit-bundle.zip"),
        deposition_id=42,
        doi="10.5072/zenodo.42",
        html_url="https://sandbox.zenodo.org/deposit/42",
        api_base="https://sandbox.zenodo.org",
        message="로컬 초안으로 저장했습니다.",
    )

    status = playground_app._deposit_status_markdown(result, playground_app.KOREAN_CHOICE)

    assert "- 모드:" in status
    assert "- 번들:" in status
    assert "- API 기본 주소:" in status
    assert "- 등록 ID:" in status
    assert "- 링크:" in status
    assert "- 메모: 로컬 초안으로 저장했습니다." in status


def test_subtask65_apply_routine_preset_uses_current_language_placeholder() -> None:
    korean_update = playground_app._apply_routine_preset("shopkeeper", playground_app.KOREAN_CHOICE)
    english_update = playground_app._apply_routine_preset("shopkeeper", "English")

    assert korean_update["value"]
    assert korean_update["placeholder"] == playground_app.LABELS["ko"]["routine_text_placeholder"]
    assert english_update["placeholder"] == playground_app.LABELS["en"]["routine_text_placeholder"]
