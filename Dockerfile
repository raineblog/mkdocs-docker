FROM python:3.12-alpine

# Install dependencies for GitHub Actions and build tools
RUN apk add --no-cache \
    bash \
    git \
    make \
    tar \
    gzip \
    ca-certificates

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY scripts/ /app/scripts/

COPY --chmod=755 mkdocs-build.sh /usr/local/bin/mkdocs-build
COPY --chmod=755 mkdocs-serve.sh /usr/local/bin/mkdocs-serve
COPY --chmod=755 zensical-serve.sh /usr/local/bin/zensical-serve

CMD ["/usr/local/bin/mkdocs-build"]