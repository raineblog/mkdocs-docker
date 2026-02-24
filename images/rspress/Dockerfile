# syntax=docker/dockerfile:1
FROM node:alpine
RUN apk add --no-cache \
    bash tini tar zstd \
    git git-fast-import \
    ca-certificates curl wget
COPY --chmod=755 bin/ /usr/local/bin/
RUN git config --system --add safe.directory /__w/*
WORKDIR /app
COPY templates/ /app/
RUN npm install
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/rspress-build"]