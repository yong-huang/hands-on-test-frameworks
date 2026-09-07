#!/usr/bin/env bash
# =============================================================================
# testcontainers_lab.sh — lab 14 主演示脚本：容器起停全自动 + 差异实测记录
# 前置：Docker Desktop 已启动（scripts/load_resources.sh check 可体检）
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "Docker 可用性检查（testcontainers 的唯一硬前置）"
    docker info --format 'Docker Server: {{.ServerVersion}}'
}

do_observe() {
    step "observe" "① 起 Postgres 容器跑全套（容器由 testcontainers 自动起停）"
    # 首跑会拉起容器（约 5-15s），结束后自动销毁
    $PY -m pytest $INI -q

    step "observe" "② 证明容器已自动销毁：测试结束后查不到 postgres 容器"
    sleep 2
    if docker ps --format '{{.Image}}' | grep -q postgres; then
        echo "⚠️ 仍有 postgres 容器在运行（残留！）："; docker ps | grep postgres
    else
        echo "✅ 无 postgres 容器残留——随测试会话自动销毁"
    fi

    step "observe" "③ 生成与 SQLite 的差异记录 docs/differences.md"
    cat > docs/differences.md <<'DIFF'
# SUT 数据层：SQLite vs Postgres 行为差异实测（lab 14）

| # | 行为 | SQLite（SUT 现状） | Postgres（lab 14 实测） | 影响 |
|:--|:---|:---|:---|:---|
| 1 | 类型约束 | 类型亲和：字符串可塞进 INTEGER 列不报错 | 强约束：错误类型直接拒绝 | SQLite 掩盖了脏数据 bug |
| 2 | 并发写 | 单写者：并发写未串行化时报 database is locked（lab 13 实测） | MVCC：20 线程裸写全部成功 | lab 26 压测拐点的根源 |
| 3 | 金额存储 | REAL 浮点：0.1+0.2 = 0.30000000000000004 | NUMERIC(10,2) 定点：0.30 | 金额计算口径必须统一 |
| 4 | 取回自增 id | cursor.lastrowid | INSERT ... RETURNING * | 数据层不可直接互换，需方言适配 |
DIFF
    echo "已写入 docs/differences.md（4 条实测差异）"
}

do_clean() {
    step "clean" "清理缓存（容器已随会话销毁，无其他残留）"
    rm -rf .pytest_cache tests/__pycache__ __pycache__
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
