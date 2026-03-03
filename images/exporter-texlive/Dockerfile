# syntax=docker/dockerfile:1
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN set -eux; \
  cat > /etc/dpkg/dpkg.cfg.d/01-ci-nodoc <<'EOF' \
path-exclude /usr/share/doc/* \
path-include /usr/share/doc/*/copyright \
path-exclude /usr/share/man/* \
path-exclude /usr/share/info/* \
path-exclude /usr/share/lintian/* \
path-exclude /usr/share/linda/* \
EOF

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    make bash tini tar zstd git ca-certificates curl wget \
    ghostscript biber fontconfig texlive-full \
    fonts-noto-cjk fonts-noto-cjk-extra fonts-noto-core fonts-noto-extra \
    fonts-liberation fonts-linuxlibertine \
    && fc-cache -fv \
    && /usr/local/bin/cleanup.sh

COPY --chmod=755 bin/ /usr/local/bin/
COPY templates/ /app/templates/

COPY docker-cleanup.sh /tmp/
RUN chmod +x /tmp/docker-cleanup.sh && \
    /tmp/docker-cleanup.sh && \
    rm /tmp/docker-cleanup.sh

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/local/bin/build-pdf"]
