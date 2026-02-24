# syntax=docker/dockerfile:1
FROM python:alpine

COPY --chmod=755 seo-push /usr/local/bin/

RUN apk add \
    bash tini tar zstd \
    git git-fast-import \
    ca-certificates curl wget

RUN git config --system --add safe.directory /__w/*

WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install requests

COPY main.py .

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/seo-push"]