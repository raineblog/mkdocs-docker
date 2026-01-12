# syntax=docker/dockerfile:1
FROM node:lts-alpine AS builder

WORKDIR /build

RUN npm install -g markdownlint-cli2 pkg
RUN npx pkg /usr/local/lib/node_modules/markdownlint-cli2 \
    --targets node18-alpine-x64 \
    --output /build/markdownlint

FROM python:3.12-alpine

RUN apk add --no-cache \
    bash \
    git \
    ca-certificates \
    libstdc++

COPY --from=builder --chmod=755 /build/markdownlint /usr/local/bin/markdownlint-cli2

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY .markdownlint.json .

COPY scripts/ /app/scripts/
COPY bin/ /usr/local/bin/

CMD ["/usr/local/bin/mkdocs-build"]
