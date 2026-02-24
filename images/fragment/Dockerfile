# syntax=docker/dockerfile:1
FROM python:alpine

COPY --chmod=755 bin/ /usr/local/bin/

RUN apk add --no-cache \
    bash tini tar zstd \
    git git-fast-import \
    ca-certificates curl wget pandoc-cli

RUN git config --system --add safe.directory /__w/*

WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ /app/scripts/
COPY templates/ /app/templates/
COPY theme/ /app/theme/

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/mkdocs-fragment"]