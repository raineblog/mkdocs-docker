# syntax=docker/dockerfile:1
FROM python:3.12-alpine AS builder

WORKDIR /build

RUN apk add --no-cache \
    build-base \
    cairo-dev \
    freetype-dev \
    git \
    jpeg-dev \
    libffi-dev \
    zlib-dev

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir -r requirements.txt

RUN git clone --depth 1 https://github.com/raineblog/mkdocs-material.git && \
    pip install --no-cache-dir ./mkdocs-material

FROM python:3.12-alpine

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apk add --no-cache \
    bash \
    ca-certificates \
    cairo \
    freetype \
    git \
    git-fast-import \
    libjpeg-turbo \
    nodejs \
    npm \
    openssh \
    pngquant \
    tini \
    zlib

RUN npm install -g markdownlint-cli2 && \
    npm cache clean --force

COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV

WORKDIR /app

COPY .markdownlint.json .
COPY scripts/ /app/scripts/
COPY --chmod=755 bin/ /usr/local/bin/

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/mkdocs-build"]