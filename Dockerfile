FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

COPY pyproject.toml uv.lock ./

RUN uv export --frozen --format requirements-txt --no-dev > requirements.txt

FROM python:3.14-alpine

RUN apk update --no-cache && apk upgrade --no-cache
RUN apk add --no-cache git ripgrep

COPY --from=ghcr.io/astral-sh/uv:python3.14-alpine /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder requirements.txt ./

RUN uv pip install --system -r requirements.txt

COPY main.py ./
COPY model/ ./model/
COPY utils/ ./utils/
