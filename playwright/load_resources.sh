#!/usr/bin/env bash
# =============================================================================
# playwright/load_resources.sh — Playwright 进阶系列（31-49）共享环境准备
# 与仓库根 scripts/load_resources.sh（Python 系列用）互不依赖：
#   1. playwright/node_modules（@playwright/test + vite + react 全家桶）
#   2. 三核浏览器构建（Chromium/Firefox/WebKit，与 Python 版共存于同一缓存目录）
# 用法: bash playwright/load_resources.sh          # 全量检查+安装
#       bash playwright/load_resources.sh check    # 只体检不安装
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-install}"

ok()   { echo "  ✅ $*"; }
warn() { echo "  ⚠️  $*"; }

do_install() {
    echo "=====> [node] 共享 node_modules（系列全部实验复用）"
    command -v node >/dev/null 2>&1 || { warn "node 缺失：系列全部受阻（brew install node）"; exit 1; }
    if [ ! -d node_modules/@playwright/test ]; then
        npm install --no-fund --no-audit || warn "npm install 失败"
    fi
    ok "node $(node --version) + @playwright/test $(node -p "require('./node_modules/@playwright/test/package.json').version")"

    echo "=====> [browsers] 三核浏览器构建（缺哪个补哪个，直连可下）"
    npx playwright install chromium firefox webkit >/dev/null 2>&1 \
        && ok "chromium / firefox / webkit 构建就绪（~/Library/Caches/ms-playwright）" \
        || warn "浏览器补装失败：手动执行 npx playwright install chromium firefox webkit"
}

do_check() {
    echo "=====> [check] Playwright 系列环境体检"
    command -v node >/dev/null 2>&1 && ok "node $(node --version)" || warn "node 缺"
    [ -d node_modules/@playwright/test ] \
        && ok "node_modules 就绪（@playwright/test $(node -p "require('./node_modules/@playwright/test/package.json').version")）" \
        || warn "node_modules 缺：bash playwright/load_resources.sh"
    npx playwright --version 2>/dev/null | head -1
    for b in chromium firefox webkit; do
        ls ~/Library/Caches/ms-playwright/${b}-* >/dev/null 2>&1 \
            && ok "${b} 构建已缓存" || warn "${b} 构建缺：npx playwright install ${b}"
    done
}

case "$MODE" in
    check)   do_check ;;
    install) do_install; do_check ;;
    *) echo "用法: $0 [check|install]" >&2; exit 1 ;;
esac
