# Stage 1: Install markdownlint-cli2
FROM node:alpine AS linter-builder
RUN npm install -g markdownlint-cli2

# Stage 2: Final Image
FROM python:3.12-alpine

# Set working directory early to avoid repeating /app
WORKDIR /app

# 1. Install runtime essentials and Node.js (for linter)
# git is needed for mkdocs-git plugins and git-auto-commit actions.
# bash is needed for the entrypoint scripts.
# ca-certificates is needed for HTTPS requests (pip, mkdocs etc).
RUN apk add --no-cache \
    bash \
    git \
    nodejs \
    ca-certificates

# 2. Copy markdownlint-cli2 from builder and create a slim shim
COPY --from=linter-builder /usr/local/lib/node_modules/markdownlint-cli2 /usr/local/lib/node_modules/markdownlint-cli2
RUN printf '#!/bin/sh\nnode /usr/local/lib/node_modules/markdownlint-cli2/markdownlint-cli2.js "$@"' > /usr/local/bin/markdownlint-cli2 && \
    chmod +x /usr/local/bin/markdownlint-cli2

# 3. Install Python dependencies and clean up cache in one layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy scripts and build script
COPY scripts/ /app/scripts/
COPY --chmod=755 mkdocs-build.sh /usr/local/bin/mkdocs-build
COPY --chmod=755 mkdocs-serve.sh /usr/local/bin/mkdocs-serve
COPY --chmod=755 zensical-serve.sh /usr/local/bin/zensical-serve

# Set default command
CMD ["/usr/local/bin/mkdocs-build"]