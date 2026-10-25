"""行为等价测试：一套用例 × 两个实现，全部通过 = 重构不改行为的证明。

用例只写业务语义（签发/校验/角色/唯一性），不关心时间与随机从哪来——
这正是依赖注入带给测试的视角：行为与机制分离。
"""


def test_issue_then_validate(make_service):
    svc = make_service()
    token = svc.issue("alice", "admin")
    assert isinstance(token, str) and token
    assert svc.validate(token) == "admin"


def test_unknown_token_is_none(make_service):
    svc = make_service()
    assert svc.validate("no-such-token") is None


def test_role_mismatch_rejected(make_service):
    svc = make_service()
    token = svc.issue("bob", "user")
    assert svc.validate(token, required_role="admin") is None
    assert svc.validate(token, required_role="user") == "user"


def test_tokens_are_unique(make_service):
    svc = make_service()
    a = svc.issue("carol", "user")
    b = svc.issue("carol", "user")  # 同一人重复登录
    assert a != b                    # 随机源是否可注入，这里都能过——机制差异不在行为层
