# syntax=docker/dockerfile:1
FROM python:3.12-alpine
ENV TZ=UTC

RUN apk add --no-cache \
    bash \
    tree \
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
    tini \
    pngquant \
    zlib-dev \
    curl \
    wget \
    tar \
    zstd \
    unzip \
    zip \
    gcompat \
    fontconfig \
    ttf-dejavu \
    font-noto-cjk \
    font-noto-cjk-extra \
    && fc-cache -fv

RUN npm install -g markdownlint-cli2 katex && \
    npm cache clean --force

WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY assets/.markdownlint.json .

COPY scripts/ /app/scripts/
COPY --chmod=755 bin/ /usr/local/bin/

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/mkdocs-build"]