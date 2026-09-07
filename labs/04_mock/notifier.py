"""lab 04 被测对象：邮件通知服务。

三层结构刻意分开，方便演示替身注入：
- SmtpClient：真正发包的"外部世界"（测试里绝不能真发）
- Mailer 接口约定：send(to, subject, body)
- NotificationService：业务逻辑——欢迎邮件、活动截止、发信失败降级
"""
import os
from datetime import datetime, timezone


class SmtpClient:
    """外部依赖：真实实现会连 SMTP 服务器（演示中只记录调用）"""

    def send(self, to: str, subject: str, body: str) -> None:
        host = os.environ.get("SMTP_HOST", "smtp.example.com")
        # 真实实现：smtplib.SMTP(host).sendmail(...)
        print(f"[SmtpClient] via {host}: {to} <- {subject}")


class NotificationService:
    """业务层：只依赖"会 send 的东西"，为注入替身留了缝"""

    def __init__(self, mailer) -> None:  # mailer: 任何有 .send(to, subject, body) 的对象
        self.mailer = mailer
        self.sent_count = 0

    def send_welcome(self, user_email: str) -> None:
        """新用户欢迎邮件：固定标题 + 个性化称呼"""
        self.mailer.send(user_email, "Welcome!", f"Hi {user_email}, thanks for joining.")
        self.sent_count += 1

    def send_campaign(self, user_email: str, now: datetime | None = None) -> bool:
        """营销邮件：只在活动期（2026-09 整月、UTC）内发送；过期不发送。

        时间来自参数注入，默认当前时间——freezegun 冻结的就是这个"当前"。
        """
        now = now or datetime.now(timezone.utc)
        deadline = datetime(2026, 10, 1, tzinfo=timezone.utc)
        if now >= deadline:  # 活动已截止
            return False
        self.mailer.send(user_email, "September Deals", "50% off everything!")
        self.sent_count += 1
        return True

    def broadcast(self, emails: list[str]) -> int:
        """群发；单个失败不中断，返回成功数（降级逻辑）"""
        ok = 0
        for e in emails:
            try:
                self.mailer.send(e, "Monthly News", "See what's new.")
                ok += 1
            except Exception:  # noqa: BLE001——演示：单个坏地址不拖垮整批
                continue
        self.sent_count += ok
        return ok
