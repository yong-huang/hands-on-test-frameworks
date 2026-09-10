#!/usr/bin/env python3
"""解析 matrix_results.txt，输出矩阵表 + 最优工作点分析 → docs/tuning.md。"""
from pathlib import Path


def load():
    rows = []
    for line in Path("reports/matrix_results.txt").read_text().splitlines():
        if not line.strip():
            continue
        rows.append(dict(kv.split("=", 1) for kv in line.split() if "=" in kv))
    return rows


def matrix(rows, exp, first_key, first_label):
    out = [f"### {exp} 矩阵", "", f"| {first_label} | 并发 | RPS | P95(ms) |", "|:---|---:|---:|---:|"]
    for r in rows:
        if r.get("exp") == exp:
            out.append(f"| {r[first_key]} | {r['vu']} | {r['RPS']} | {r['P95']} |")
    return out


def best(rows, exp, first_key):
    cand = [r for r in rows if r.get("exp") == exp and r["vu"] == "200"]
    if not cand:
        return None, None
    return max(cand, key=lambda r: float(r["RPS"])), cand


def main():
    rows = load()
    lines = ["# 08 · 并发模型与容量调参报告", ""]

    bs, shop_c = best(rows, "shop", "workers")
    bg, go_c = best(rows, "go", "procs")
    if shop_c:
        lines += matrix(rows, "shop", "workers", "uvicorn workers")
        base = [r for r in shop_c if r["workers"] == "1"]
        if base and bs:
            gain = (float(bs["RPS"]) / float(base[0]["RPS"]) - 1) * 100
            lines += ["", f"最优：{bs['workers']} workers @200VU（{bs['RPS']} RPS，"
                          f"比默认 1 worker 提升 **{gain:.0f}%**）",
                      f"注：连接池是**每进程**的——{bs['workers']} workers × pool{10} = "
                      f"{int(bs['workers']) * 10} 条 PG 连接，别忘了 max_connections 预算。"]
    if go_c:
        lines += [""] + matrix(rows, "go", "procs", "GOMAXPROCS")
        base = [r for r in go_c if r["procs"] == "1"]
        if base and bg:
            gain = (float(bg["RPS"]) / float(base[0]["RPS"]) - 1) * 100
            lines += ["", f"最优：GOMAXPROCS={bg['procs']} @200VU（{bg['RPS']} RPS，"
                          f"比默认 1 P 提升 **{gain:.0f}%**）"]

    lines += [
        "",
        "## 判读要点",
        "",
        "- RPS 不再随并发增长的档位 = 饱和区；饱和区里 P95 最低的配置 = 最优工作点",
        "- worker 数超过容器 CPU 配额后收益归零甚至回退（上下文切换税）",
        "- GOMAXPROCS 硬压到 1 会人为制造 CPU 瓶颈——真实部署里它是留给容器",
        "  CPU limit 对齐用的（超卖环境不设对齐会抖）",
        "",
    ]
    out = Path("docs/tuning.md")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
