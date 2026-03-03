# syntax=docker/dockerfile:1
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN set -eux; \
    mkdir -p /etc/dpkg/dpkg.cfg.d; \
    cat > /etc/dpkg/dpkg.cfg.d/01-ci-nodoc <<'EOF'
path-exclude /usr/share/doc/*
path-include /usr/share/doc/*/copyright
path-exclude /usr/share/man/*
path-exclude /usr/share/groff/*
path-exclude /usr/share/info/*
path-exclude /usr/share/lintian/*
path-exclude /usr/share/linda/*
EOF

RUN set -eux; \
  cat > /etc/apt/apt.conf.d/99ci-no-translations <<'EOF'
Acquire::Languages "none";
EOF

RUN set -eux; \
  cat > /etc/apt/apt.conf.d/99ci-gzip-indexes <<'EOF'
Acquire::GzipIndexes "true";
EOF

COPY --chmod=755 ci-cleanup.sh /usr/local/bin/ci-cleanup

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends eatmydata; \
    eatmydata apt-get update && eatmydata apt-get install -y --no-install-recommends \
    make bash tini tar zstd git ca-certificates curl wget \
    ghostscript biber fontconfig texlive-full \
    fonts-noto-cjk fonts-noto-cjk-extra fonts-noto-core fonts-noto-extra \
    fonts-liberation fonts-linuxlibertine \
    ca-certificates curl git; \
    fc-cache -fv; \
    rm -rf /var/lib/apt/lists/*; \
    /usr/local/bin/ci-cleanup

COPY --chmod=755 bin/ /usr/local/bin/
COPY templates/ /app/templates/

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/local/bin/build-pdf"]
