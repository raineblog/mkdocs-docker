# syntax=docker/dockerfile:1
FROM python:alpine

COPY --chmod=755 bin/ /usr/local/bin/

RUN apk add --no-cache \
    bash tini tar zstd \
    git git-fast-import \
    ca-certificates curl wget \
    weasyprint \
    so:libgobject-2.0.so.0 so:libpango-1.0.so.0 so:libharfbuzz.so.0 so:libharfbuzz-subset.so.0 so:libfontconfig.so.1 so:libpangoft2-1.0.so.0 \
    font-liberation font-liberation-sans-narrow ttf-linux-libertine \
    fontconfig texlive-full && fc-cache -fv

RUN git config --system --add safe.directory /__w/*

WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ /app/scripts/

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/mkdocs-export"]