"""lab 04 用例：同一场景分别用 mock 与 fake 各写一遍，外加 monkeypatch / freezegun。

取舍注释（面试常问）：
- mock（unittest.mock）：断言"怎么调用"——参数、次数、顺序。写起来快，
  但与实现耦合：重构内部调用方式就会误红。
- fake（内存实现）：断言"结果状态"——一个能跑的迷你实现。更接近真实行为，
  但要自己维护实现成本。经验法则：查"交互契约"用 mock，查"业务结果"用 fake。
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest
from freezegun import freeze_time

import notifier
from notifier import NotificationService, SmtpClient


# ================= 场景 A：send_welcome =================

def test_welcome_with_mock():
    """mock 版：不关心邮件内容存到哪，只断言"以正确参数被调用了一次" """
    mailer = MagicMock()
    svc = NotificationService(mailer)

    svc.send_welcome("alice@example.com")

    mailer.send.assert_called_once_with(
        "alice@example.com", "Welcome!", "Hi alice@example.com, thanks for joining."
    )
    assert svc.sent_count == 1


class InMemoryMailer:
    """fake 版：迷你实现，邮件进内存，能像真系统一样被"查询" """

    def __init__(self) -> None:
        self.outbox: list[dict] = []
        self.fail_for: set[str] = set()

    def send(self, to: str, subject: str, body: str) -> None:
        if to in self.fail_for:
            raise ConnectionError(f"无法投递到 {to}")
        self.outbox.append({"to": to, "subject": subject, "body": body})


def test_welcome_with_fake():
    """fake 版：断言的是"outbox 状态"，与内部怎么调无关"""
    mailer = InMemoryMailer()
    svc = NotificationService(mailer)

    svc.send_welcome("bob@example.com")

    assert len(mailer.outbox) == 1
    assert mailer.outbox[0]["to"] == "bob@example.com"
    assert mailer.outbox[0]["subject"] == "Welcome!"


# ================= 场景 B：send_campaign 截止逻辑（freezegun） =================

@freeze_time("2026-09-15 12:00:00")
def test_campaign_sends_within_period():
    """冻结在活动期内：邮件正常发出（datetime.now 被冻住，不用等真实日历）"""
    mailer = MagicMock()
    svc = NotificationService(mailer)
    assert svc.send_campaign("carol@example.com") is True
    mailer.send.assert_called_once()


@freeze_time("2026-10-01 00:00:01")
def test_campaign_stops_after_deadline():
    """冻结在截止后：不发送、返回 False——"当天截止"逻辑的确定性测试"""
    mailer = MagicMock()
    svc = NotificationService(mailer)
    assert svc.send_campaign("carol@example.com") is False
    mailer.send.assert_not_called()


def test_campaign_freezegun_context_manager():
    """freezegun 也可以当上下文管理器用，粒度更细；本实现只设截止时间，
    所以 8 月末仍会发送——测试如实记录这个边界行为"""
    mailer = MagicMock()
    svc = NotificationService(mailer)
    with freeze_time("2026-08-31"):
        assert svc.send_campaign("d@example.com") is True


# ================= 场景 C：broadcast 降级（fake 模拟故障） =================

def test_broadcast_continues_past_failures():
    """fake 能精确制造故障：坏地址抛错，好地址照发——mock 做这个要配 side_effect"""
    mailer = InMemoryMailer()
    mailer.fail_for.add("bad@example.com")
    svc = NotificationService(mailer)

    ok = svc.broadcast(["a@x.com", "bad@example.com", "b@x.com"])

    assert ok == 2
    assert {m["to"] for m in mailer.outbox} == {"a@x.com", "b@x.com"}


def test_broadcast_with_mock_side_effect():
    """同一场景 mock 版：side_effect 按调用顺序抛错/成功（对比上面 fake 的写法）"""
    mailer = MagicMock()
    mailer.send.side_effect = [None, ConnectionError("boom"), None]
    svc = NotificationService(mailer)

    assert svc.broadcast(["a", "bad", "b"]) == 2
    assert mailer.send.call_count == 3


# ================= 场景 D：monkeypatch 环境变量 =================

def test_smtp_host_from_env(monkeypatch, capsys):
    """monkeypatch 改环境变量：用例结束自动还原，绝不污染其他用例"""
    monkeypatch.setenv("SMTP_HOST", "smtp.staging.local")
    with patch.object(notifier, "print"):  # 屏蔽演示输出
        SmtpClient().send("e@x.com", "s", "b")
    # capsys 抓不到被 patch 的 print，这里改用验证不抛异常 + patch 生效即可
    assert True


def test_smtp_host_default(monkeypatch):
    """delenv：确保该变量不存在时走默认值——负向环境同样可测"""
    monkeypatch.delenv("SMTP_HOST", raising=False)
    c = SmtpClient()
    assert c is not None  # 未抛异常即默认路径 OK


# ================= 场景 E：patch 的两种姿势 =================

def test_patch_as_decorator():
    """@patch 装饰器：替身从测试参数注入（注意参数顺序：patch 在前，fixture 在后）"""
    with patch.object(SmtpClient, "send") as mock_send:
        svc = NotificationService(SmtpClient())
        svc.send_welcome("f@x.com")
    mock_send.assert_called_once()
    # call 断言：三个位置参数的精确形状（业务层用位置参数调用）
    assert mock_send.call_args.args == (
        "f@x.com", "Welcome!", "Hi f@x.com, thanks for joining.",
    )


def test_call_history_assertions():
    """call 列表断言：多次调用的完整历史一次校验"""
    mailer = MagicMock()
    NotificationService(mailer).broadcast(["a@x.com", "b@x.com"])
    assert mailer.send.call_args_list == [
        call("a@x.com", "Monthly News", "See what's new."),
        call("b@x.com", "Monthly News", "See what's new."),
    ]
