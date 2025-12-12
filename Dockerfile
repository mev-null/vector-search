FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# COPY pyproject.toml uv.lock ./

# RUN uv sync --frozen --no-cache

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]