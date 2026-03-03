#!/bin/sh
set -eu

rm -rf \
  /usr/share/doc \
  /usr/share/man \
  /usr/share/groff \
  /usr/share/info \
  /usr/share/lintian \
  /usr/share/linda \
  /var/cache/man 2 || true

rm -rf /tmp/* /var/tmp/* || true
rm -rf /root/.cache/* || true
rm -rf /var/log/* || true
