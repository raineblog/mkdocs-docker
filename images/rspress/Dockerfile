# syntax=docker/dockerfile:1
FROM node:lts-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash tini tar zstd \
    git \
    ca-certificates curl wget \
    && rm -rf /var/lib/apt/lists/*
COPY --chmod=755 bin/ /usr/local/bin/
RUN git config --system --add safe.directory /__w/*
WORKDIR /app
COPY templates/ /app/
RUN npm install
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/local/bin/rspress-build"]