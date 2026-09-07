"""lab 02 被测对象：一个"昂贵"的数据库连接（fake，不碰真数据库）。

用 sleep 模拟真实连接成本（迁移、握手），用类属性统计实例化次数——
fixture 作用域对错，看这个计数器一目了然。
"""
import time


class FakeDB:
    """模拟昂贵资源：实例化要 0.2s（真环境里是 2s 的数据库握手）"""

    instances = 0  # 全局实例计数：验证 session fixture 只建一次的关键证据

    def __init__(self, dsn: str = "sqlite://:memory:") -> None:
        time.sleep(0.2)
        FakeDB.instances += 1
        self.dsn = dsn
        self.users: dict[int, dict] = {}
        self.closed = False

    def add_user(self, name: str) -> dict:
        uid = len(self.users) + 1
        self.users[uid] = {"id": uid, "name": name}
        return self.users[uid]

    def get_user(self, uid: int) -> dict | None:
        return self.users.get(uid)

    def close(self) -> None:
        self.closed = True
