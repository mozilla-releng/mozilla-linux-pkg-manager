ARG PYTHON_VERSION
ARG UV_VERSION

FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_VERSION}-trixie-slim AS builder

WORKDIR /app

# %include README.md
# %include pyproject.toml
# %include uv.lock
# %include src
COPY topsrcdir/README.md topsrcdir/pyproject.toml topsrcdir/uv.lock ./
COPY topsrcdir/src ./src

RUN uv sync --frozen --no-dev --no-editable

FROM python:${PYTHON_VERSION}-slim-trixie

RUN groupadd -r -g 15731 worker && useradd -r -u 15731 -g worker -d /home/worker -m worker
USER worker
WORKDIR /app

COPY --from=builder --chown=worker:worker /app/.venv ./.venv

ENTRYPOINT [".venv/bin/mozilla-linux-pkg-manager"]
