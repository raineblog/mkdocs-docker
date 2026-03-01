# syntax=docker/dockerfile:1
FROM alpine:latest

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add --update-cache \
    make bash tini tar zstd git ca-certificates curl wget \
    ghostscript biber fontconfig texlive-full \
    font-noto-cjk font-noto font-noto-extra font-noto-emoji \
    font-wqy-zenhei font-noto-cjk-extra \
    font-ipa font-ipaex font-dejavu font-unifont \
    font-liberation font-linux-libertine \
    font-liberation font-liberation-sans-narrow ttf-linux-libertine \
    && fc-cache -fv

RUN curl -sSLf https://gist.githubusercontent.com/christiansteier/dd8c5544c69504d29bd938726691255b/raw/5317638ec64c0e8c3d22cd9965237a452bf82895/docker-alpine-cleanup.sh | sh

COPY --chmod=755 bin/ /usr/local/bin/

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/build-pdf"]
