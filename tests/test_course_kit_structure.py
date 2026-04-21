from pathlib import Path

EDUCATION_DIR = Path("docs/education")


def test_batch_gg_course_kit_core_files_exist() -> None:
    expected = [
        EDUCATION_DIR / "syllabus.md",
        EDUCATION_DIR / "rubric.md",
        EDUCATION_DIR / "lab_exercises.md",
        EDUCATION_DIR / "slides" / "reveal_template.html",
    ]

    for path in expected:
        assert path.exists(), path


def test_batch_gg_syllabus_has_twelve_weeks_and_assignments() -> None:
    syllabus = (EDUCATION_DIR / "syllabus.md").read_text(encoding="utf-8")

    assert syllabus.count("## Week ") == 12
    assert "LLM-Based Multi-Agent Social Simulation" in syllabus
    assert "assignments/week_12_final_project_presentation.md" in syllabus


def test_batch_gg_assignments_have_required_sections() -> None:
    assignments = sorted((EDUCATION_DIR / "assignments").glob("week_*.md"))

    assert len(assignments) == 12
    for assignment in assignments:
        text = assignment.read_text(encoding="utf-8")
        assert "## Learning Goal" in text
        assert "## Task" in text
        assert "## Deliverables" in text
        assert "## Grading" in text


def test_batch_gg_rubric_labs_slides_and_nav_are_complete() -> None:
    rubric = (EDUCATION_DIR / "rubric.md").read_text(encoding="utf-8")
    labs = (EDUCATION_DIR / "lab_exercises.md").read_text(encoding="utf-8")
    slides = (EDUCATION_DIR / "slides" / "reveal_template.html").read_text(encoding="utf-8")
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")

    assert "30%" in rubric
    assert "40%" in rubric
    assert "20%" in rubric
    assert "10%" in rubric
    assert labs.count("## Lab ") == 10
    assert "reveal.js@5" in slides
    assert "education/syllabus.md" in mkdocs
    assert "education/assignments/week_01_scenario_authoring.md" in mkdocs
