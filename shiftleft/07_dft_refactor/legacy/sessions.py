"""会话管理·原版（重构前）——从 labs/11 main.py 的 login/TOKENS 语义复刻。

三处硬编码依赖，就是可测性欠账的本体：
  1. secrets.token_hex    —— 随机源焊死，无法断言「同用户重复登录 token 不同」以外的确定行为
  2. time.monotonic()     —— 时钟焊死，「token 过期拒绝」的测试必须真实等待 TTL
  3. 模块级字典 _TOKENS   —— 状态藏在模块里，测试之间互相污染，只能手动 clear
"""
import secrets
import time

TTL = 3600.0  # token 有效期（秒）——模块级常量，测试只能 monkeypatch 它

_TOKENS: dict[str, tuple[str, float]] = {}  # token -> (role, 签发时刻 monotonic)


def issue_token(username: str, role: str) -> str:
    """签发 token：角色跟人走（labs/11 的 login 规则）。"""
    token = secrets.token_hex(16)             # 硬编码随机源
    _TOKENS[token] = (role, time.monotonic())  # 硬编码时钟
    return token


def validate_token(token: str, required_role: str | None = None) -> str | None:
    """校验 token：不存在/过期/角色不符 → None；通过 → 角色。

    过期即清理（labs/11 没有 TTL 逻辑，这里补上是本域的语义需求）。
    """
    entry = _TOKENS.get(token)
    if entry is None:
        return None
    role, issued_at = entry
    if time.monotonic() - issued_at > TTL:  # 硬编码时钟 → 过期测试只能真睡
        _TOKENS.pop(token, None)
        return None
    if required_role is not None and role != required_role:
        return None
    return role
