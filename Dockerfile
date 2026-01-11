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
COPY mkdocs-build.sh /usr/local/bin/mkdocs-build
RUN chmod +x /usr/local/bin/mkdocs-build

CMD ["/usr/local/bin/mkdocs-build"]