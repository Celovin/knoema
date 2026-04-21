FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY playground ./playground

RUN python -m pip install --upgrade pip \
    && python -m pip install . \
    && python -m pip install \
        "gradio==5.31.0" \
        "huggingface_hub>=0.24,<1.0" \
        "plotly>=5.24" \
        "pyyaml>=6.0" \
        "scipy>=1.14"

EXPOSE 7860

CMD ["knoema", "playground", "--host", "0.0.0.0", "--port", "7860"]
