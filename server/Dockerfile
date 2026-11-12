FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1
WORKDIR /app
