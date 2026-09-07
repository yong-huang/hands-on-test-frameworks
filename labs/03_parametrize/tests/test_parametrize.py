"""lab 03 用例：参数化矩阵（ids 可读命名 / 笛卡尔积 / indirect）+ 异常消息断言。

收集到的用例数远超函数数——一条 parametrize 展开 20+ 输入组合。
"""
import pytest

from config_parser import ConfigError, parse_config, parse_value


# ---------- parse_value：类型推断矩阵，ids 让报告可读 ----------
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("42", 42),                # 纯数字 → int
        ("-7", -7),                # 负数也是 int
        ("007", 7),                # 前导零会被 int() 吃掉（记录在案的行为）
        ("true", True),            # bool 三种大小写
        ("True", True),
        ("FALSE", False),
        ("hello", "hello"),        # 其余一律 str
        ("1.5", "1.5"),            # 浮点不做数值转换（设计如此）
        ("", ""),                  # 空串
    ],
    ids=["int", "negative-int", "leading-zero", "bool-lower", "bool-upper",
         "bool-false", "str", "float-as-str", "empty"],
)
def test_parse_value(raw, expected):
    assert parse_value(raw) == expected


# ---------- 笛卡尔积：两个 @parametrize 叠加 = 全组合 ----------
@pytest.mark.parametrize("prefix", ["", "# ", "; "], ids=["plain", "hash-comment", "semi-comment"])
@pytest.mark.parametrize("body", ["k=1", "  k = 2  "], ids=["tight", "spaced"])
def test_lines_that_are_skipped_or_kept(prefix, body):
    """注释行(任意前后缀组合)不产生键；非注释行总是产生键——2×3=6 组合自动展开"""
    text = prefix + body
    result = parse_config(text)
    if prefix.strip():
        assert result["default"] == {}
    else:
        assert "k" in result["default"]


# ---------- 正常解析：多节 + 类型混合 ----------
def test_full_document():
    doc = """
# 注释行
[server]
host = 0.0.0.0
port = 8080
debug = true

[client]
retries = 3
name = lab-03
"""
    cfg = parse_config(doc)
    assert cfg["server"] == {"host": "0.0.0.0", "port": 8080, "debug": True}
    assert cfg["client"]["retries"] == 3
    assert cfg["client"]["name"] == "lab-03"


def test_no_section_goes_to_default():
    assert parse_config("a = 1") == {"default": {"a": 1}}


# ---------- 异常断言：pytest.raises + match 校验消息内容 ----------
@pytest.mark.parametrize(
    "bad_text,match",
    [
        ("just_a_line", "缺少 '='"),          # 无等号
        ("[oops", "未闭合"),                   # 节名未闭合
        ("[]\n", "节名为空"),                  # 空节名
        (" = 5\n", "键名为空"),                # 空键
        ("a = 1\na = 2\n", "重复键"),          # 重复键
    ],
    ids=["no-equals", "unclosed-section", "empty-section", "empty-key", "dup-key"],
)
def test_config_errors(bad_text, match):
    """异常类型 + 消息内容双重断言：match 是正则，不是子串相等"""
    with pytest.raises(ConfigError, match=match):
        parse_config(bad_text)


# ---------- indirect：参数先过 fixture 再进用例（预处理管道） ----------
@pytest.fixture()
def loaded(request):
    """indirect fixture：收到的不是裸参数，而是先解析成配置再交给用例"""
    return parse_config(request.param)


@pytest.mark.parametrize(
    "loaded,expected_port",
    [("[srv]\nport = 9000", 9000), ("[srv]\nport = 80", 80)],
    ids=["port-9000", "port-80"],
    indirect=["loaded"],  # 只有 loaded 走 fixture，expected_port 仍直传
)
def test_indirect_parametrize(loaded, expected_port):
    assert loaded["srv"]["port"] == expected_port
