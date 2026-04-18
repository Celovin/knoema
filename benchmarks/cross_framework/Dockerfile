FROM python:3.11-slim

WORKDIR /app
COPY framework_specs.json run_comparison.py ./
RUN mkdir -p results
CMD ["python", "run_comparison.py"]
