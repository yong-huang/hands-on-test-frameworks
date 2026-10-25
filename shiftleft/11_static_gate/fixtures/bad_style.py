"""坏 fixture · 风格层：默认只有 warning 级（E501 超长行 / F401 未用导入），升到 error 后才会阻断——升降级演示的主角。"""

import os  # F401：导入未使用


def banner(text: str) -> str:
    return f"== {text} ==" + "这是故意写得很长的一行，用来触发 E501 行长度规则，超过 ruff 默认的 88 个字符限制很多很多，方便演示。"
