#!/usr/bin/env bash
# =============================================================================
# ci_github.sh — lab 13 主演示脚本：BDD 套件进 CI
#   apply 体检 → observe ① act 容器内校验 workflow ② 宿主机直跑冒烟集
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（类型检查 + SUT 构建产物）"
    npx tsc -p tsconfig.json
    [ -f ../../playwright/02_pw_sut/app/dist/index.html ] || \
        npx vite build ../../playwright/02_pw_sut/app --logLevel warn
    npx cucumber-js --version | head -1
}

do_observe() {
    step "observe" "① act 容器内校验 workflow（单 job，ACT 守卫跳过 checkout/npm ci）"
    if docker info >/dev/null 2>&1 && command -v act >/dev/null; then
        (cd ../.. && HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 \
            act workflow_dispatch \
            -W "$PWD/.github/workflows/bdd.yml" \
            -j bdd --env ACT=true --pull=false --bind 2>&1 | tail -10) || \
            echo ">>> act 校验未通过（代理/镜像源原因见日志；workflow 的 YAML 已被 act 解析）"
    else
        echo ">>> docker/act 不可用，跳过"
    fi

    step "observe" "② 宿主机直跑 BDD 冒烟集（API 层 3 条）"
    lsof -ti :9115 2>/dev/null | xargs kill 2>/dev/null || true
    PORT=9115 nohup node ../../playwright/02_pw_sut/server.mjs </dev/null > /dev/null 2>&1 &
    for i in $(seq 1 40); do
        curl -sf http://127.0.0.1:9115/api/health >/dev/null 2>&1 && break
        sleep 0.25
    done
    BASE_URL=http://127.0.0.1:9115 npx cucumber-js
    lsof -ti :9115 | xargs kill 2>/dev/null || true
}

do_clean() {
    step "clean" "清运行产物，杀残留"
    lsof -ti :9114 :9115 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf reports .sut.log
    echo ">>> 已清理"
}

main() {
    local target="${1:-all}"
    case "${target}" in
        apply)   do_apply ;;
        observe) do_observe ;;
        clean)   do_clean ;;
        all)     do_apply; do_observe; do_clean ;;
        *) echo "可用: apply | observe | clean | all" >&2; exit 1 ;;
    esac
}
main "$@"
