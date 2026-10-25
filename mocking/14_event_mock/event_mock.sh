#!/usr/bin/env bash
# =============================================================================
# event_mock.sh — mocking 14 主演示脚本：
# testcontainers 起 Kafka → 替身生产者注入（正常/乱序/毒丸）→ 消费 worker
# → 断言毒丸进 DLQ 且不阻塞 → 容器自动销毁
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖体检 + Docker daemon 探测（testcontainers 需要）"
    "$PY" -c "import testcontainers, kafka" 2>/dev/null || {
        echo "缺依赖：pip install testcontainers[kafka] kafka-python-ng" >&2; exit 1; }
    if ! "$PY" -c "
import docker, os
docker.DockerClient(base_url=os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock')).ping()
" 2>/dev/null; then
        if [ -S "$HOME/.orbstack/run/docker.sock" ]; then
            export DOCKER_HOST="unix://$HOME/.orbstack/run/docker.sock"
            echo "使用 OrbStack socket：$DOCKER_HOST"
        else
            echo "Docker daemon 不可达" >&2; exit 1
        fi
    fi
    # 导出给子进程（event_pipeline 内的 testcontainers 读取）
    [ -n "${DOCKER_HOST:-}" ] && export DOCKER_HOST
    echo "依赖与 daemon 就绪（首次运行会拉取 cp-kafka 镜像，约数百 MB）"
    mkdir -p reports
}

do_observe() {
    step "observe" "② 全流程：拉 Kafka → 注入 → 消费 → 断言（脚本自带全部断言）"
    "$PY" event_pipeline.py 2>&1 | tee reports/run.txt
    grep -q "❌" reports/run.txt && { echo "存在失败断言"; exit 1; } || true
}

do_clean() {
    step "clean" "确认容器已随 context manager 销毁"
    rm -rf reports __pycache__
    if docker ps -a --format '{{.names}}' 2>/dev/null | grep -qi "kafka\|redpanda"; then
        echo "❌ 有 Kafka 容器残留"; exit 1
    fi
    echo "已清理（无 Kafka 容器残留）"
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
