# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11
# Fast Python builds using uv on Debian bookworm-slim
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS base

ARG UID=10001

# Ensures that logs are captured in realtime
ENV PYTHONUNBUFFERED=1

# Create unprivileged user
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# System build deps for common Python wheels
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependency install first for better caching
COPY pyproject.toml uv.lock ./
RUN mkdir -p src
RUN uv sync --locked

# Copy application code
COPY . .
RUN chown -R appuser:appuser /app
USER appuser

# Pre-download models/assets at build time
RUN uv run src/voice_agent.py download-files

# Start the agent
CMD ["uv", "run", "src/voice_agent.py", "dev"]
