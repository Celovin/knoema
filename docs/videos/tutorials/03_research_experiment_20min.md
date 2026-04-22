# Tutorial 03 - Build A Reproducible Research Experiment In 20 Minutes

## Goal

Scenario DSL과 CLI를 사용해 synthetic scenario를 실행하고, JSONL log, reproducibility report, benchmark artifact를 연구용 evidence bundle로 정리한다.

## Audience

- 사회 시뮬레이션 연구자
- 공공안전 예방 연구를 synthetic replay로 검토하는 팀
- 실험 재현성을 요구하는 평가자

## Recording Setup

- Resolution: 1920x1080
- Frame rate: 60 fps
- Capture surfaces: editor, terminal, dashboard, PDF viewer
- Browser tabs: GitHub, local dashboard, report PDF
- Safety note: 실제 개인이나 실제 사건을 입력하지 않는다는 문장을 초반에 명확히 말한다

## Script

### 00:00 - 01:10 Opening And Safety Boundary

Screen: `docs/dsl/tutorial.md`.

Narration:
이번 영상은 public-safety style scenario를 다루지만, 실제 개인이나 실제 사건을 입력하지 않습니다. Luvoire의 DSL은 fictional, synthetic, non-identifying replay를 위한 도구입니다. 사람을 점수화하거나 미래 사건을 단정하는 용도가 아닙니다.

### 01:10 - 04:30 Scenario DSL Structure

Screen: `examples/scenarios/01_shopkeeper_winter_crime.yaml`.

Narration:
Scenario DSL은 agents, environment, events, metrics, guardrail notes를 YAML로 기록합니다. 실험 조건이 코드 안에 묻히지 않기 때문에 재실행과 검토가 쉬워집니다.

Action:
Show persona block, environment block, events block, ethics notes.

### 04:30 - 07:20 Validate And Run

Screen: Terminal.

Commands:

```bash
luvoire run examples/scenarios/01_shopkeeper_winter_crime.yaml --dry-run
luvoire run examples/scenarios/01_shopkeeper_winter_crime.yaml --output runs/research_demo.jsonl --json
```

Narration:
dry run은 파일 구조와 guardrail을 먼저 확인합니다. 실제 실행은 JSONL log를 남깁니다. 같은 config와 seed를 보관하면 결과를 다시 비교할 수 있습니다.

### 07:20 - 10:40 Inspect Logs

Screen: Streamlit dashboard.

Narration:
dashboard에서 agent별 행동, relationship edges, playback window를 확인합니다. 중요한 것은 화면에 보이는 그래프와 원본 JSONL이 같은 artifact에서 나온다는 점입니다.

### 10:40 - 13:50 Reproducibility Tests

Screen: `tests/reproducibility/`.

Narration:
Luvoire는 same-seed deterministic runs, seed propagation, config serialization, JSONL replay를 테스트합니다. 연구용 demo는 실행 결과보다 재실행 조건이 더 중요합니다.

Commands:

```bash
pytest tests/reproducibility/
```

### 13:50 - 16:50 Benchmark Reports

Screen: `benchmarks/formal_report/report.pdf` and figures.

Narration:
Formal benchmark report는 scenario A부터 D까지의 결과와 baseline discipline을 기록합니다. 측정하지 않은 외부 수치는 만들지 않고 `not-measured`로 둡니다.

### 16:50 - 18:50 Package Evidence

Screen: README links and report paths.

Narration:
연구 공유용 evidence bundle에는 config, seed, JSONL, summary, figures, report, commit hash가 들어가야 합니다. 그래프 이미지만 공유하면 재현성이 약해집니다.

### 18:50 - 20:00 Wrap

Screen: Reproducibility report.

Narration:
Luvoire의 연구 흐름은 간단합니다. synthetic scenario를 쓰고, guardrail을 확인하고, seed와 config를 고정하고, JSONL과 report를 함께 남깁니다.

## YouTube Description

Luvoire Scenario DSL과 CLI로 재현 가능한 연구 실험을 만드는 20분 튜토리얼입니다. synthetic replay, guardrail, JSONL log, dashboard inspection, reproducibility tests, benchmark report를 한 흐름으로 다룹니다.

Links:
- GitHub: https://github.com/Celovin/luvoire
- Scenario DSL tutorial: https://github.com/Celovin/luvoire/blob/main/docs/dsl/tutorial.md
- Reproducibility report: https://github.com/Celovin/luvoire/blob/main/docs/reports/reproducibility.md
- Formal benchmark report: https://github.com/Celovin/luvoire/blob/main/benchmarks/formal_report/report.pdf

