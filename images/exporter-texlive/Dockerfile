# syntax=docker/dockerfile:1
FROM alpine:latest

RUN --mount=type=cache,target=/var/cache/apk \
    apk add --update-cache \
    make bash tini tar zstd git ca-certificates curl wget \
    ghostscript biber fontconfig texlive-full \
    font-noto-cjk font-noto font-noto-extra font-noto-cjk-extra \
    font-liberation font-linux-libertine font-liberation-sans-narrow ttf-linux-libertine \
    && fc-cache -fv

COPY --chmod=755 bin/ /usr/local/bin/
COPY templates/ /app/templates/

RUN curl -sSLf https://gist.githubusercontent.com/christiansteier/dd8c5544c69504d29bd938726691255b/raw/5317638ec64c0e8c3d22cd9965237a452bf82895/docker-alpine-cleanup.sh | sh
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/build-pdf"]

