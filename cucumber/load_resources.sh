#!/usr/bin/env bash
# =============================================================================
# cucumber/load_resources.sh — Cucumber BDD 系列（01-14）共享环境准备
# 与 playwright/load_resources.sh 同构：node_modules 装在本目录全系列复用；
# 浏览器构建与 playwright/ 系列共用（playwright 1.62.1 同版本）。
# 另一项职责：确保共享靶场 pw-store 已构建（labs 全部打它）。
# 用法: bash cucumber/load_resources.sh          # 全量检查+安装
#       bash cucumber/load_resources.sh check    # 只体检不安装
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-install}"

ok()   { echo "  ✅ $*"; }
warn() { echo "  ⚠️  $*"; }

ensure_pwstore_built() {
    # pw-store 前端构建产物（playwright/02 产出）是本系列全部实验的依赖
    if [ ! -f ../playwright/02_pw_sut/app/dist/index.html ]; then
        echo "=====> [pw-store] 靶场未构建，执行 vite build"
        npx vite build ../playwright/02_pw_sut/app --logLevel warn
    fi
    ok "pw-store 构建产物就绪（../playwright/02_pw_sut/app/dist）"
}

do_install() {
    echo "=====> [node] 共享 node_modules（cucumber 13 + playwright 1.62 + tsx 转译钩子）"
    command -v node >/dev/null 2>&1 || { warn "node 缺失：系列全部受阻（brew install node）"; exit 1; }
    if [ ! -d node_modules/@cucumber/cucumber ]; then
        npm install --no-fund --no-audit || warn "npm install 失败"
    fi
    ok "node $(node --version) + cucumber $(node -p "require('./node_modules/@cucumber/cucumber/package.json').version")"
    ok "playwright $(node -p "require('./node_modules/playwright/package.json').version") + tsx 转译钩子"

    echo "=====> [browsers] 三核浏览器构建（与 playwright/ 系列共用缓存）"
    npx playwright install chromium firefox webkit >/dev/null 2>&1 \
        && ok "chromium / firefox / webkit 构建就绪" \
        || warn "浏览器补装失败：手动执行 npx playwright install chromium"

    ensure_pwstore_built
}

do_check() {
    echo "=====> [check] Cucumber 系列环境体检"
    command -v node >/dev/null 2>&1 && ok "node $(node --version)" || warn "node 缺"
    [ -d node_modules/@cucumber/cucumber ] \
        && ok "node_modules 就绪（cucumber $(node -p "require('./node_modules/@cucumber/cucumber/package.json').version")）" \
        || warn "node_modules 缺：bash cucumber/load_resources.sh"
    npx cucumber-js --version 2>/dev/null | head -1
    ls ~/Library/Caches/ms-playwright/chromium-* >/dev/null 2>&1 \
        && ok "chromium 构建已缓存" || warn "chromium 缺：npx playwright install chromium"
    [ -f ../playwright/02_pw_sut/app/dist/index.html ] \
        && ok "pw-store 构建产物就绪" || warn "pw-store 未构建（install 会自动补）"
}

case "$MODE" in
    check)   do_check ;;
    install) do_install; do_check ;;
    *) echo "用法: $0 [check|install]" >&2; exit 1 ;;
esac
