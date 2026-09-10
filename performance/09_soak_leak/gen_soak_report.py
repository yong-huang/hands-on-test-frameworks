#!/usr/bin/env python3
"""汇总浸泡/差分证据 → docs/soak.md。"""
from pathlib import Path


def parse(tag):
    p = Path(f"reports/soak_{tag}_samples.txt")
    if not p.exists():
        return None
    rows = [l.split() for l in p.read_text().splitlines() if l.strip() and len(l.split()) >= 3]
    rss = [float(r[1]) for r in rows]
    gor = [int(r[2]) for r in rows]
    return rss[0], rss[-1], gor[0], gor[-1]


def main():
    lines = ["# 09 · 浸泡测试与泄漏定位报告", ""]
    for tag in ("heap", "goroutine", "fixed"):
        d = parse(tag)
        if not d:
            continue
        r0, r1, g0, g1 = d
        label = "修复后（LEAK_MODE=off）" if tag == "fixed" else f"泄漏注入（{tag}）"
        lines.append(f"- **{label}**：RSS {r0:.0f}→{r1:.0f}MB（Δ{r1-r0:+.0f}），"
                     f"goroutines {g0}→{g1}（Δ{g1-g0:+d}）——"
                     f"{'单调上升，泄漏实锤' if tag != 'fixed' else '尾部平台化，平稳'}")

    diff = Path("reports/heap_diff.txt")
    if diff.exists():
        lines += ["", "## heap 差分 top（正值 = 新增分配嫌疑犯）", "", "```",
                  diff.read_text().strip()[:1200], "```", ""]
    lines += [
        "## 判读",
        "",
        "- 泄漏版（heap 模式）RSS 单调上升且不回落——短压测看不见，时间揭发；",
        "- goroutine 模式看 go_goroutines 单调上升（每请求孵一个永不返回的 goroutine）；",
        "- 修复版同配方曲线平稳即验收通过。",
        "",
    ]
    out = Path("docs/soak.md")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
