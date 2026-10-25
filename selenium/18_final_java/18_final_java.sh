#!/usr/bin/env bash
# 18_final_java.sh — 项目 18：🏁 终极对照（TestNG × Grid 并行 + 重试演示 + 终版差异报告）
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "拉起共享靶场 + Grid（复用项目 13 的 compose）"
    bash "$SERIES/shop/shop.sh" apply
    if ! curl -sf -m 2 "http://127.0.0.1:4444/status" >/dev/null 2>&1; then
        docker compose -f "$SERIES/13_grid/docker-compose.yml" up -d
        for i in $(seq 1 60); do
            curl -sf "http://127.0.0.1:4444/status" >/dev/null && break
            sleep 1
        done
        echo "Grid 就绪"
    else
        echo "Grid 已在运行"
    fi
}

do_observe() {
    step "observe" "mvn test：TestNG 并行(methods×2) 打 Grid，含重试演示"
    local out
    out=$(mvn test 2>&1) || { echo "$out" | tail -30; exit 1; }
    echo "$out" | grep -E 'Tests run:' | tail -2 | sed 's/^/    /'
    echo "$out" | grep -q '第二次执行通过（重试生效）' || { echo "❌ 未见到重试成功案例"; exit 1; }
    echo "$out" | grep -q '故意失败（RetryAnalyzer 将接管）' || { echo "❌ 未见到首试失败记录"; exit 1; }
    echo "$out" | grep -Eq 'Tests run: [0-9]+, Failures: 0' || { echo "❌ 存在失败"; exit 1; }
    echo "    ✅ 并行 + 重试演示 + 全绿 三项验收通过"
}

do_clean() {
    step "clean" "停 Grid、清运行产物"
    docker compose -f "$SERIES/13_grid/docker-compose.yml" down -v --remove-orphans >/dev/null 2>&1 || true
    rm -rf target
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
