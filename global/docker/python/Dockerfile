FROM python:3.13-slim AS build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

FROM python:3.13-slim

WORKDIR /app
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home app && chown -R app /app
USER app

CMD ["python", "-m", "app"]
