# Tutorial 01 - Getting Started With Knoema In 10 Minutes

## Goal

새 사용자가 저장소를 clone하고, 개발 의존성을 설치하고, deterministic local simulation을 실행한 뒤 dashboard에서 JSONL 로그를 확인한다.

## Audience

- Python 개발자
- 게임 프로토타입 제작자
- 연구용 agent simulation을 빠르게 검토하려는 연구자

## Recording Setup

- Resolution: 1920x1080
- Frame rate: 60 fps
- Browser zoom: 100 percent
- Terminal font: 16 px 이상
- Capture surfaces: terminal, repository tree, browser dashboard
- Audio: narration first, keyboard noise low

## Script

### 00:00 - 00:35 Opening

Screen: GitHub repository top page.

Narration:
Knoema Engine은 LLM 기반 multi-agent social simulation engine입니다. 오늘은 API 키 없이 deterministic local mode로 설치, 실행, 로그 확인까지 10분 안에 끝내겠습니다.

Action:
Show README headline, applications table, CI badge.

### 00:35 - 01:40 Install

Screen: Terminal in repository root.

Commands:

```bash
git clone https://github.com/Celovin/knoema.git
cd knoema
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,dashboard]"
```

Narration:
개발 모드는 notebooks, tests, dashboard를 함께 설치합니다. 실제 모델 provider 없이도 local client가 같은 입력에서 같은 결과를 돌려주므로 첫 실행 비용은 없습니다.

### 01:40 - 03:10 Run Tests

Screen: Terminal.

Commands:

```bash
pytest
ruff check .
mypy src
```

Narration:
Knoema는 public demo보다 재현성을 먼저 확인합니다. 테스트에는 memory, relationship, environment, simulator, DSL, benchmark, SDK가 포함됩니다.

### 03:10 - 05:30 Run A YAML Simulation

Screen: `examples/cli_dorm.yaml`, then terminal.

Commands:

```bash
knoema run examples/cli_dorm.yaml --output runs/demo_dorm.jsonl --json
```

Narration:
YAML config에는 agents, environment, tick duration, output path가 들어갑니다. 결과는 JSONL로 남고, 같은 config와 seed를 쓰면 다시 확인할 수 있습니다.

### 05:30 - 07:40 Open Dashboard

Screen: Browser at dashboard.

Commands:

```bash
streamlit run dashboard/app.py
```

Narration:
dashboard에서는 agent summary, relationship edges, log rows, realtime playback을 확인합니다. 연구자와 개발자가 같은 로그를 보고 논의할 수 있게 하는 것이 핵심입니다.

### 07:40 - 09:10 Try The Playground

Screen: Hugging Face Playground.

Narration:
브라우저에서 먼저 보고 싶다면 Playground를 사용합니다. replay-only mode는 API 키 없이 동작하고, live run은 사용자가 세션 키를 넣을 때만 실행됩니다.

### 09:10 - 10:00 Wrap

Screen: README links and docs list.

Narration:
다음 영상에서는 Python Game SDK로 첫 NPC를 만들고, response text와 branch flags를 게임 규칙에 연결해 보겠습니다.

## YouTube Description

Knoema Engine을 설치하고 deterministic local simulation을 실행하는 10분 튜토리얼입니다. API 키 없이 YAML config, JSONL export, Streamlit dashboard까지 확인합니다.

Links:
- GitHub: https://github.com/Celovin/knoema
- Playground: https://huggingface.co/spaces/Celovin/knoema-playground
- CLI docs: https://github.com/Celovin/knoema/blob/main/docs/cli.md
- Dashboard app: https://github.com/Celovin/knoema/tree/main/dashboard

