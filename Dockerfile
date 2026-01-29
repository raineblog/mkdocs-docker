# syntax=docker/dockerfile:1
FROM python:alpine
ENV TZ=Etc/UTC

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
    tzdata \
    gcompat \
    fontconfig \
    font-noto-cjk \
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