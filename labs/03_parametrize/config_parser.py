"""lab 03 被测对象：INI 风格配置解析器。

支持 `key = value` 行、`[section]` 节、int/bool/str 三种类型自动推断；
坏行、重复键、空节名要抛出带清晰消息的 ConfigError。
函数小而规则密集——正是参数化矩阵的绝佳猎物。
"""


class ConfigError(ValueError):
    """配置语法错误"""


def parse_value(raw: str) -> object:
    """类型推断：纯数字→int；true/false→bool；其余→str（保留首尾空格已由调用方剥离）"""
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        return raw


def parse_config(text: str) -> dict:
    """解析整段配置文本，返回 {section: {key: value}}；无节时归入 default 节"""
    result: dict[str, dict] = {}
    section = "default"
    result[section] = {}

    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith(("#", ";")):  # 空行与注释
            continue
        if line.startswith("["):
            if not line.endswith("]"):
                raise ConfigError(f"第 {lineno} 行节名未闭合: {line}")
            name = line[1:-1].strip()
            if not name:
                raise ConfigError(f"第 {lineno} 行节名为空")
            section = name
            result.setdefault(section, {})
            continue
        if "=" not in line:
            raise ConfigError(f"第 {lineno} 行缺少 '=': {line}")
        key, _, raw = line.partition("=")
        key, raw = key.strip(), raw.strip()
        if not key:
            raise ConfigError(f"第 {lineno} 行键名为空")
        if key in result[section]:
            raise ConfigError(f"第 {lineno} 行重复键: {key}")
        result[section][key] = parse_value(raw)

    return result
