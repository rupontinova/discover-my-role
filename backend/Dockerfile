FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS runtime

# Added HF_HOME to force Hugging Face to use a specific directory
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    HF_HOME=/app/huggingface_cache

WORKDIR /app
ARG ENABLE_DOCLING=false

COPY prod/pyproject.toml ./pyproject.toml
COPY prod/uv.lock ./uv.lock
RUN EXTRAS=""; \
    if [ "$ENABLE_DOCLING" = "true" ]; then EXTRAS="$EXTRAS --extra docling"; fi; \
    uv sync --frozen --no-dev --no-install-project $EXTRAS
RUN .venv/bin/playwright install --with-deps chromium

COPY README.md alembic.ini main.py ./
COPY alembic ./alembic
COPY src ./src
RUN EXTRAS=""; \
    if [ "$ENABLE_DOCLING" = "true" ]; then EXTRAS="$EXTRAS --extra docling"; fi; \
    uv sync --frozen --no-dev $EXTRAS

EXPOSE 8000
CMD ["sh", "-c", ".venv/bin/alembic upgrade head && exec .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000"]