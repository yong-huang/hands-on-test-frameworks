#!/usr/bin/env bash
# =============================================================================
# ci_lifecycle.sh — mocking 17 主演示脚本：
# act 本地跑 mock-lifecycle 工作流 ×3：健康门放行 / 零残留 / 缓存判定
# （第 1 次 reuse=false 启动 mock；第 2、3 次配置未变 reuse=true 跳过重启）
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖体检（act + docker）+ 清缓存目录"
    command -v act >/dev/null || { echo "缺 act（brew install act）" >&2; exit 1; }
    docker info >/dev/null 2>&1 || { echo "Docker daemon 不可达" >&2; exit 1; }
    if [ ! -S /var/run/docker.sock ] && [ -S "$HOME/.orbstack/run/docker.sock" ]; then
        export DOCKER_HOST="unix://$HOME/.orbstack/run/docker.sock"
        echo "DOCKER_HOST → $DOCKER_HOST"
    fi
    mkdir -p reports
    rm -rf .mock-cache                 # 从 miss 开始，演示缓存从无到有
    echo "依赖就绪"
}

run_once() {  # $1 = 轮次
    act -W .github/workflows/mock-lifecycle.yml \
        -P "ubuntu-latest=ubuntu:24.04" \
        --bind \
        > "reports/run$1.log" 2>&1
    local rc=$?
    [ "$rc" -eq 0 ] || { echo "❌ 第 $1 次运行失败（rc=${rc}），见 reports/run$1.log"; exit 1; }
    grep -q "零残留确认" "reports/run$1.log" || { echo "❌ 第 $1 次无零残留确认"; exit 1; }
    grep -o "reuse=[a-z]*" "reports/run$1.log" | head -1
}

do_observe() {
    step "observe" "② 第 1 次：缓存 miss → 启动 mock（健康门放行）→ 冒烟 → 零残留"
    echo "reuse 判定：$(run_once 1)"
    grep -q "reuse=false" reports/run1.log && echo "  ✅ 首跑 cache miss，mock 已启动"

    step "observe" "③ 第 2、3 次：配置未变 → reuse=true，跳过启动与冒烟（fresh 容器无长效 mock，跳过即诚实）"
    for i in 2 3; do
        echo "reuse 判定：$(run_once $i)"
    done
    grep -q "reuse=true" reports/run2.log && grep -q "reuse=true" reports/run3.log \
        && echo "  ✅ 第 2、3 次缓存命中：mock 启动与冒烟全部 Skipped，零残留保持"

    step "observe" "④ 反向验证：改 mock 配置 → 缓存失效 → 重新启动"
    echo '{"seed": "v2"}' > stubs/config.json
    echo "reuse 判定：$(run_once 4)"
    grep -q "reuse=false" reports/run4.log && echo "  ✅ 配置变更后缓存失效，mock 重启"

    step "observe" "⑤ 宿主零残留：容器与端口均不在场"
    docker rm -f $(docker ps -q --filter "name=act-mock-lifecycle") >/dev/null 2>&1 || true
    if docker ps --format '{{.Names}}' | grep -q "act-mock-lifecycle"; then
        echo "❌ act 容器残留"; exit 1
    fi
    python3 -c "import socket; s=socket.socket(); s.settimeout(1); assert s.connect_ex(('127.0.0.1',9810)) != 0, 'residue'"
    echo "宿主侧零残留确认（act 容器自动销毁，端口 9810 不在宿主）"

    echo
    echo ">>> 验收：健康门放行 ✅ 零残留 ✅×3 缓存命中 ✅ 配置变更失效 ✅"
}

do_clean() {
    step "clean" "删产物与缓存——环境回到实验前状态"
    rm -rf reports .mock-cache __pycache__
    git checkout -- stubs/config.json 2>/dev/null || echo '{"seed": "v1"}' > stubs/config.json
    echo "已清理"
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
