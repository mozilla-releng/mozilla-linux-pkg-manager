FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim AS builder

WORKDIR /app
COPY README.md pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.11-slim-trixie

RUN groupadd -r -g 15731 worker && useradd -r -u 15731 -g worker -d /home/worker -m worker
USER worker
WORKDIR /app

COPY --from=builder --chown=worker:worker /app/.venv ./.venv

ENTRYPOINT [".venv/bin/mozilla-linux-pkg-manager"]
