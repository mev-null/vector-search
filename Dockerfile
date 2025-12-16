FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY api/pyproject.toml api/uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]