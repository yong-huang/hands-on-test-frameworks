"""lab 06 被测对象：编解码器 + 排序 + 一个"埋了雷"的均值函数。

Hypothesis 的舞台需要"性质"：
1. 编解码往返（roundtrip）：decode(encode(x)) == x 对一切 x 成立
2. 排序不变量：输出有序、是输入的置换、幂等
3. 埋雷的 mean()：手写用例想不到，Hypothesis 100% 挖出来（教学核心）
"""


def encode(items: list[str]) -> str:
    """序列化：JSON 风格，逗号连接，反斜杠与逗号转义"""
    escaped = [i.replace("\\", "\\\\").replace(",", "\\,") for i in items]
    return ",".join(escaped)


def decode(raw: str) -> list[str]:
    """反序列化 encode 的输出；转义处理必须与 encode 严格互逆。

    注：decode(encode([]))==[''] 这个 bug 恰恰是本实验撰写时被
    Hypothesis 当场挖出来的（空串会误产生一个空元素）——已修复并保留此注释。
    """
    if raw == "":
        return []
    out, buf, esc = [], "", False
    for ch in raw:
        if esc:
            buf += ch
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == ",":
            out.append(buf)
            buf = ""
        else:
            buf += ch
    out.append(buf)
    return out


def buggy_mean(nums: list[float]) -> float:
    """【埋雷】把"和超精度"的坑埋在 float 求和里：

    Hypothesis 会找到类似 [1e308, 1e308, -1e308] 的输入——手写用例几乎想不到，
    这就是 property-based 的价值。演示文件 test_props.py 的最后一个用例预期失败。
    """
    total = 0.0
    for n in nums:
        total += n  # 大数先加会吞掉小数：经典精度陷阱
    return total / len(nums) if nums else 0.0


def stable_mean(nums: list[float]) -> float:
    """修复版：math.fsum 保精度求和——修复后的回归验证用 @example 固定"""
    import math

    return math.fsum(nums) / len(nums) if nums else 0.0
