# syntax=docker/dockerfile:1
FROM python:3.12-alpine

RUN apk add --no-cache bash git ca-certificates

COPY --from=davidanson/markdownlint-cli2:latest /usr/local/bin/markdownlint-cli2 /usr/local/bin/markdownlint-cli2

WORKDIR /app

COPY requirements.txt .
COPY .markdownlint.json .

RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ /app/scripts/
COPY bin/ /usr/local/bin/
RUN for f in /usr/local/bin/*.sh; do mv "$f" "${f%.sh}"; done && chmod +x /usr/local/bin/*

CMD ["/usr/local/bin/mkdocs-build"]