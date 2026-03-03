#!/bin/sh
set -eu

# 目标：只清理“构建期垃圾”，不做不可控的“系统大扫除”
# 建议：在 Dockerfile 里与 apt-get install 放在同一个 RUN 里调用

cleanup_apt() {
  # 1) 清 APT lists（Docker 官方 best practice 常规项）
  rm -rf /var/lib/apt/lists/*

  # 2) 清 APT 下载的 .deb 包缓存（两种方式二选一即可）
  apt-get clean
  # 如果你不想依赖 apt-get clean，也可以用：
  # rm -rf /var/cache/apt/archives/* /var/cache/apt/archives/partial/*
}

cleanup_docs() {
  # dpkg path-exclude 只能阻止“未来安装”落盘；
  # 基础镜像或你在开启过滤前装过的包，仍可能已有 docs/man/info，需要收尾。
  #
  # 保留 copyright（Ubuntu Wiki 推荐这么做）
  if [ -d /usr/share/doc ]; then
    find /usr/share/doc -mindepth 2 -type f ! -name copyright -delete 2>/dev/null || true
    find /usr/share/doc -type d -empty -delete 2>/dev/null || true
  fi

  rm -rf \
    /usr/share/man \
    /usr/share/groff \
    /usr/share/info \
    /usr/share/lintian \
    /usr/share/linda \
    /var/cache/man 2>/dev/null || true
}

cleanup_tmp_and_logs() {
  rm -rf /tmp/* /var/tmp/* 2>/dev/null || true
  rm -rf /root/.cache/* 2>/dev/null || true
  rm -rf /var/log/* 2>/dev/null || true
}

cleanup_apt
cleanup_docs
cleanup_tmp_and_logs