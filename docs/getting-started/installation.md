# Installation

Luvoire targets Python 3.11 or newer.

## Linux and macOS

```bash
git clone https://github.com/Celovin/luvoire.git
cd luvoire
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest tests/test_version.py tests/test_phase1_types.py --no-cov -q
```

Use the CLI from the same shell:

```bash
luvoire list-scenarios --json
luvoire run examples/cli_dorm.yaml --json
```

## Windows PowerShell

```powershell
git clone https://github.com/Celovin/luvoire.git
cd luvoire
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest tests\test_version.py tests\test_phase1_types.py --no-cov -q
```

Use the CLI from the same PowerShell session:

```powershell
luvoire list-scenarios --json
luvoire run examples\cli_dorm.yaml --json
```

## Core Checks

```bash
pytest
ruff check .
mypy src
```

## Optional Dashboard Install

```bash
pip install -e '.[dashboard]'
streamlit run dashboard/app.py
```

## Optional Docs Install

```bash
pip install -e '.[docs]'
mkdocs build
mkdocs serve
```

## Browser Playground

The public Playground supports replay-only demos without API keys.

```bash
pip install -r playground/requirements.txt
python playground/app.py
```

## Node-Based Website

```bash
cd website
npm install
npm run build
npm run dev
```
