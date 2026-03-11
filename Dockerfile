FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

ENV UV_SYSTEM_PYTHON=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app

WORKDIR /app

RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.14-alpine AS runner

RUN apk update --no-cache && apk upgrade --no-cache
RUN apk add --no-cache git ripgrep

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV=/app/.venv

COPY main.py /app
COPY model/ /app/model/
COPY utils/ /app/utils/
COPY agent_ask_system_prompt.txt /app
COPY agent_implement_system_prompt.txt /app
COPY agent_implement_user_prompt_template.txt /app

WORKDIR /app

ENTRYPOINT ["python", "main.py"]
