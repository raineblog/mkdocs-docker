# syntax=docker/dockerfile:1
FROM python:alpine

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHON_GIL=1
    
RUN apk add --no-cache \
    bash tini tar zstd \
    git git-fast-import \
    ca-certificates curl wget \
    nodejs npm zlib-dev \
    cairo freetype-dev jpeg-dev openssh pngquant && \
    npm install -g npm bun && \
    git config --system --add safe.directory /__w/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY package.json .
RUN bun install

RUN --mount=type=bind,source=.python-version,target=.python-version \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked
ENV PATH="/app/.venv/bin:$PATH"

COPY gulpfile.js .

COPY scripts/ /app/scripts/
COPY templates/ /app/templates/
COPY --chmod=755 bin/ /usr/local/bin/
# COPY mkdocs-fragment-theme/ /app/mkdocs-fragment-theme/

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/mkdocs-build"]