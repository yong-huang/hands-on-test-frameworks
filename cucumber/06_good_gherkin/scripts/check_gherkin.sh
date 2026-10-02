#!/usr/bin/env bash
# check_gherkin.sh — BDD 门禁：feature 文件禁 UI 操作词（命令式泄漏检测）
# 词表可按团队增删；命中的文件与行号输出后返回非零
set -euo pipefail
cd "$(dirname "$0")/.."

BAD_WORDS="点击|输入框|按钮|等待1秒|再次点击|检查页面上出现"
HITS=0
for f in features/checkout_good.feature; do
    if grep -nE "$BAD_WORDS" "$f"; then
        HITS=1
    fi
done
if [ "$HITS" -eq 0 ]; then
    echo ">>> checkout_good.feature 零 UI 操作词 ✓"
else
    echo ">>> 命令式泄漏：声明式 feature 里不应出现 UI 操作词" >&2
    exit 1
fi
