# syntax=docker/dockerfile:1
FROM python:3.12-alpine

RUN apk add --no-cache \
    bash \
    git \
    ca-certificates \
    nodejs-lts npm

RUN npm install -g markdownlint-cli2 && \
    npm cache clean --force

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY .markdownlint.json .

COPY scripts/ /app/scripts/
COPY --chmod=755 bin/ /usr/local/bin/

CMD ["/usr/local/bin/mkdocs-build"]
