FROM python:3.12.8-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        libsodium-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /bin/

ENV PATH="/root/.cargo/bin:${PATH}" \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/signifypy

WORKDIR /app

COPY pyproject.toml uv.lock README.md LICENSE pytest.ini ./
COPY src/ src/
COPY scripts/ scripts/

RUN uv sync --locked --no-dev --no-editable

FROM python:3.12.8-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libsodium23 \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/signifypy/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8

WORKDIR /app

COPY --from=builder /opt/signifypy /opt/signifypy
COPY scripts/ scripts/

CMD ["sigpy", "--help"]
