#!/bin/bash
set -e  # 遇到错误立即退出

# 可以在这里打印一些日志，方便调试
echo ">>> Starting mkdocs Serve Process..."
echo ">>> Container Workdir: $(pwd)"

# 调用 Python 脚本
# "$@" 表示将传递给 shell 脚本的所有参数透传给 python 脚本
# 使用 exec 可以让 python 进程替换当前 shell 进程，接收信号更准确

python /app/scripts/generate.serve.py "$@"
mkdocs serve --dirty --livereload --dev-addr 0.0.0.0:8000
