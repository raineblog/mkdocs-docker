# syntax=docker/dockerfile:1
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    make bash tini tar zstd git ca-certificates curl wget \
    ghostscript biber fontconfig texlive-full \
    fonts-noto-cjk fonts-noto-cjk-extra fonts-noto-core fonts-noto-extra \
    fonts-liberation fonts-linuxlibertine \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --chmod=755 bin/ /usr/local/bin/
COPY templates/ /app/templates/

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/local/bin/build-pdf"]
