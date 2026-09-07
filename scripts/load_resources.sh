#!/usr/bin/env bash
# =============================================================================
# load_resources.sh — 全系列共享环境准备（幂等，可重复执行）
#
# 解决本系列最普遍的环境阻塞：
#   1. 共享 Python 虚拟环境 .venv（pytest 全家桶 + SUT + 各框架依赖）
#   2. Playwright 三核浏览器（Chromium/Firefox/WebKit）
#   3. k6 / act（性能与本地 CI，brew）
#   4. Docker 可用性体检（lab 14/24/29 需要）
#
# 用法: bash scripts/load_resources.sh          # 全量检查+安装
#       bash scripts/load_resources.sh check    # 只体检不安装
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-install}"
VENV=".venv"
PY="$VENV/bin/python"

# 每个实验脚本都会 source 本文件，因此把"激活 venv"做成幂等入口
if [ -x "$PY" ]; then
    export PATH="$PWD/$VENV/bin:$PATH"
fi

ok()   { echo "  ✅ $*"; }
warn() { echo "  ⚠️  $*"; }
miss() { echo "  ❌ $*"; }

do_install_python() {
    echo "=====> [python] 共享虚拟环境 .venv"
    if [ ! -x "$PY" ]; then
        python3 -m venv "$VENV"
        "$VENV/bin/pip" install --quiet --upgrade pip
    fi
    # 只在缺包时装（幂等）：requirements 由根 README 统一维护
    if ! "$PY" -c "import pytest, httpx, fastapi, playwright, hypothesis, syrupy, locust, selenium" 2>/dev/null; then
        "$VENV/bin/pip" install --quiet \
            pytest pytest-cov pytest-xdist pytest-asyncio pytest-playwright pytest-html \
            hypothesis syrupy time-machine freezegun httpx requests \
            fastapi "uvicorn[standard]" locust selenium \
            "testcontainers[postgres]" pact-python psycopg2-binary axe-playwright-python
    fi
    ok "python $($PY --version | cut -d' ' -f2) + 依赖就绪"
}

do_install_browsers() {
    echo "=====> [playwright] 三核浏览器（缺哪个补哪个）"
    if ! ls ~/Library/Caches/ms-playwright/chromium-* >/dev/null 2>&1; then
        "$VENV/bin/playwright" install chromium
    fi
    if ! ls ~/Library/Caches/ms-playwright/firefox-* >/dev/null 2>&1; then
        "$VENV/bin/playwright" install firefox || warn "firefox 安装失败：lab 20 三核回归需要它"
    fi
    if ! ls ~/Library/Caches/ms-playwright/webkit-* >/dev/null 2>&1; then
        "$VENV/bin/playwright" install webkit || warn "webkit 安装失败：lab 20 三核回归需要它"
    fi
    ok "浏览器缓存 ~/Library/Caches/ms-playwright"
}

do_install_cli() {
    echo "=====> [cli] k6 / act（brew）"
    command -v k6  >/dev/null 2>&1 || brew install k6  || warn "k6 安装失败：lab 27 受阻"
    command -v act >/dev/null 2>&1 || brew install act || warn "act 安装失败：lab 30 本地验证退化为仅 GitHub Actions"
    ok "k6=$(command -v k6 >/dev/null && k6 version | head -1 || echo 缺) act=$(command -v act >/dev/null && echo 有 || echo 缺)"
}

check_all() {
    echo "=====> [check] 环境体检"
    command -v python3 >/dev/null && ok "python3 $(python3 --version)" || miss "python3"
    command -v node    >/dev/null && ok "node $(node --version)"       || warn "node 缺（lab 21/22 Cypress 需要）"
    command -v docker  >/dev/null && docker info >/dev/null 2>&1 \
        && ok "docker $(docker --version | cut -d' ' -f3 | tr -d ',')" \
        || warn "docker 不可用（lab 14/24/29/30 的 act 受阻，README 已标注）"
    [ -x "$PY" ] && ok ".venv 就绪（$($PY --version)）" || warn ".venv 不存在，跑 bash scripts/load_resources.sh"
    command -v k6  >/dev/null && ok "k6 $(k6 version | head -1)"  || warn "k6 缺（lab 27）"
    command -v act >/dev/null && ok "act $(act --version | head -1)" || warn "act 缺（lab 30 本地复跑）"
}

case "$MODE" in
    check)  check_all ;;
    install)
        do_install_python
        do_install_browsers
        do_install_cli
        check_all
        ;;
    *) echo "用法: $0 [check|install]" >&2; exit 1 ;;
esac
