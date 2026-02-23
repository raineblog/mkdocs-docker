# syntax=docker/dockerfile:1
FROM python:alpine

COPY --chmod=755 bin/ /usr/local/bin/

RUN apk add --no-cache \
    bash tini tar zstd \
    git git-fast-import \
    ca-certificates curl wget \
    nodejs npm zlib-dev \
    cairo freetype-dev jpeg-dev openssh pngquant

RUN git config --system --add safe.directory /__w/*

WORKDIR /app

COPY posthtml/package.json .
RUN npm install

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY posthtml/gulpfile.js .

COPY scripts/ /app/scripts/
copy templates/ /app/templates/

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/mkdocs-build"]