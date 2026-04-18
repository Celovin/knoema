# Installation

Knoema targets Python 3.11 or newer.

## Editable Development Install

```bash
git clone https://github.com/Celovin/knoema.git
cd knoema
pip install -e '.[dev]'
```

Run the core checks:

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
