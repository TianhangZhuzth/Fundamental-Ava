FROM python:3.12-slim AS base

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir .

COPY benchmarks ./benchmarks
COPY experiments ./experiments

ENTRYPOINT ["python", "-c", "import ava; print(f'Ava {ava.__version__} ready')"]
