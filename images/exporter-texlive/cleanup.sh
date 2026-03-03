#!/bin/sh
set -e

# set -euxo pipefail

# APT 清理
apt-get clean
apt-get autoclean
apt-get autoremove --purge -y

rm -rf /var/lib/apt/lists/*
rm -rf /var/cache/apt/archives/*
rm -rf /var/cache/apt/*

# 文档、man、info（这些占空间很大）
rm -rf /usr/share/doc/*
rm -rf /usr/share/man/*
rm -rf /usr/share/info/*
rm -rf /usr/share/lintian/*


find /usr/share/doc -depth -type f ! -name copyright|xargs rm || true
find /usr/share/doc -empty|xargs rmdir || true
rm -rf /usr/share/man /usr/share/groff /usr/share/info /usr/share/lintian /usr/share/linda /var/cache/man

# 临时文件和缓存
rm -rf /tmp/* /var/tmp/* /root/.cache/* 

# 可选激进清理（根据你的语言栈决定是否开启）
# find /usr/lib -name '*.a' -delete || true
# find / -name __pycache__ -type d -exec rm -rf {} + || true
# rm -rf /root/.npm /root/.yarn /root/.cargo/registry etc.

# APT 元数据缓存（最常见的无用体积来源）
rm -rf /var/lib/apt/lists/*

# 临时目录
rm -rf /tmp/* /var/tmp/*

# 文档/手册/信息（如果你没有用 dpkg path-exclude，这里也能删；但要同层才真正瘦身）
rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/info/*

# 一些无关紧要的静态数据（可选）
rm -rf /usr/share/lintian/ /usr/share/linda/ || true

# 日志（通常不大，但 CI 镜像可以清）
rm -rf /var/log/* || true
