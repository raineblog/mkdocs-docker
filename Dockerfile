# syntax=docker/dockerfile:1
FROM python:3.12-alpine

RUN apk add --no-cache \
    bash \
    git \
    ca-certificates \
    nodejs \
    npm \
    cairo \
    freetype-dev \
    git \
    git-fast-import \
    jpeg-dev \
    openssh \
    pngquant \
    tini \
    zlib-dev

RUN npm install -g markdownlint-cli2 && \
    npm cache clean --force

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY .markdownlint.json .

RUN git clone --depth 1 https://github.com/raineblog/mkdocs-material.git && \
    pip install --no-cache-dir ./mkdocs-material

COPY scripts/ /app/scripts/
COPY --chmod=755 bin/ /usr/local/bin/

CMD ["/usr/local/bin/mkdocs-build"]
