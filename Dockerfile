FROM python:3.14-alpine

RUN apk update --no--cache && akp upgrade --no-cache
RUN apk add ripgre --no-cache

# TODO: Install using uv and system python - will need docs
