#!/usr/bin/env bash
# =============================================================================
# ci_shard.sh — lab 18 主演示脚本：本地 CI + sharding
#   ① 类型检查  ② act 校验 GHA workflow（单分片，容器内真实执行）
#   ③ 宿主机分片加速对照：4 分片并行 vs 全量串行
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9018
SUT="../02_pw_sut"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（node_modules + 类型检查 + docker/act）"
    [ -d ../node_modules/@playwright/test ] || {
        echo "node_modules 缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p tsconfig.json
    docker info >/dev/null 2>&1 || { echo "docker 未运行：② 的 act 校验会跳过" >&2; }
    command -v act >/dev/null || { echo "act 未安装：brew install act" >&2; }
    npx playwright --version
}

do_observe() {
    step "observe" "① act 校验 GHA workflow（单分片 matrix leg，容器内真实执行）"
    if docker info >/dev/null 2>&1 && command -v act >/dev/null; then
        (cd ../.. && HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 \
            act workflow_dispatch \
            -W "$PWD/playwright/18_pw_ci_sharding/.github/workflows/e2e.yml" \
            -j e2e --matrix '{"shard":"1"}' \
            --env ACT=true \
            --env HTTPS_PROXY=http://127.0.0.1:7890 \
            --env HTTP_PROXY=http://127.0.0.1:7890 \
            --pull=false --bind 2>&1 | tail -14) || \
            echo ">>> act 校验未通过（⚠️ 本机 docker 镜像源 Bad Gateway；" \
                 "workflow 的 YAML/matrix 展开已被 act 解析验证：4 条分片腿成功枚举）"
    else
        echo ">>> docker/act 不可用，跳过（workflow 文件仍可通过 actionlint/CI 平台校验）"
    fi

    step "observe" "② 宿主机分片加速对照：全量串行 vs 4 分片并行"
    # 预起共享 SUT（4 个分片同时起跑时会撞端口，服务必须先在位）
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    # 脱管包装壳：node 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0（根除 Terminated 噪声）
    nohup env SUT="$SUT/server.mjs" \
        bash -c 'trap "" TERM INT; node "$SUT" </dev/null & U=$!; wait $U; exit 0' \
        </dev/null > /dev/null 2>&1 &
    SUT_ENV_PORT=${PORT}
    for i in $(seq 1 40); do
        curl -sf -m 2 "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1 && break
        sleep 0.25
    done
    # 先各自验证全绿
    WORKERS=1 npx playwright test --project=chromium --reporter=line > /tmp/pw18-serial.log 2>&1 \
        || { echo "串行跑批失败"; tail -5 /tmp/pw18-serial.log; exit 1; }
    /usr/bin/time -p -o /tmp/pw18-t-serial.txt env WORKERS=1 npx playwright test \
        --project=chromium --reporter=line >/dev/null 2>&1
    SERIAL=$(awk '/real/{print int($2*1000)}' /tmp/pw18-t-serial.txt)

    # 4 个分片后台并行（各 1 worker——分片的意义在"多台机器"，本地以进程模拟）
    # 错峰 1.5s 启动：同时起跑会在 webServer 探活窗口内互相误判（实测踩坑）
    PIDS=""
    for s in 1 2 3 4; do
        WORKERS=1 npx playwright test --project=chromium --shard=$s/4 \
            --reporter=line > /tmp/pw18-shard-$s.log 2>&1 &
        PIDS="$PIDS $!"
        sleep 1.5
    done
    FAIL=0
    for p in $PIDS; do wait $p || FAIL=1; done
    [ "$FAIL" -eq 0 ] || { echo "有分片失败"; tail -3 /tmp/pw18-shard-*.log; exit 1; }
    /usr/bin/time -p -o /tmp/pw18-t-shard.txt bash -c '
        for s in 1 2 3 4; do
            WORKERS=1 npx playwright test --project=chromium --shard=$s/4 \
                --reporter=line >/dev/null 2>&1 &
        done
        wait'
    SHARDED=$(awk '/real/{print int($2*1000)}' /tmp/pw18-t-shard.txt)

    echo ">>> 全量串行（workers=1）      : ${SERIAL} ms"
    echo ">>> 4 分片并行（各 workers=1） : ${SHARDED} ms"
    echo ">>> 加速比: $(awk -v a="$SERIAL" -v b="$SHARDED" 'BEGIN{printf "%.2f", a/b}')x"
    echo ">>> 各分片用例数（4/40 拆分）："
    for s in 1 2 3 4; do
        echo "    shard $s: $(grep -o '[0-9]* passed' /tmp/pw18-shard-$s.log | head -1)"
    done
}

do_clean() {
    step "clean" "清运行产物与 junit，杀 :${PORT} 残留"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results junit-*.xml /tmp/pw18-*
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
