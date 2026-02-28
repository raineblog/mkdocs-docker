# syntax=docker/dockerfile:1
FROM ghcr.io/rainppr/gh-action-docker:latest

WORKDIR /app

COPY package.json .
RUN bun install

RUN --mount=type=bind,source=.python-version,target=.python-version \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-cache
ENV PATH="/app/.venv/bin:$PATH"

COPY gulpfile.js .

COPY scripts/ /app/scripts/
COPY templates/ /app/templates/
COPY --chmod=755 bin/ /usr/local/bin/
# COPY mkdocs-fragment-theme/ /app/mkdocs-fragment-theme/

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/mkdocs-build"]