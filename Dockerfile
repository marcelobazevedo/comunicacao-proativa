FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update \
    && apt-get install --no-install-recommends -y libatomic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /aplicacao

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

EXPOSE 5001
