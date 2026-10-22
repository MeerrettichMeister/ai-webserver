# Image of the recipe API. Runs uvicorn on port 8000; `alembic upgrade head` applies migrations.
# Build: docker build -t py-server .

# Both stages use the same Python image, so the venv's interpreter links stay valid.
ARG PYTHON_IMAGE=python:3.15-slim-trixie

# --- Build: install the locked dependencies and the app into /app/.venv ---
FROM ${PYTHON_IMAGE} AS build

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv

# Compile bytecode for faster startup; copy from the cache mount instead of hardlinking;
# use the image's Python instead of downloading one.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencies first, in their own layer, so code changes don't reinstall them.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

COPY . .
# --no-editable copies the app into the venv, so the runtime stage needs no sources.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# --- Runtime: Python, the venv and what Alembic needs ---
FROM ${PYTHON_IMAGE}

RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app
COPY --from=build /app/.venv .venv
# Alembic reads [tool.alembic] from pyproject.toml and the revisions from migrations/.
COPY pyproject.toml ./
COPY migrations migrations

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 8000
CMD ["uvicorn", "py_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
