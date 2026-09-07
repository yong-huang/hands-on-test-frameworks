"""lab 08 被测对象：带指数退避重试的异步客户端。

可测性设计（本实验的核心思想）：
- transport 可注入——网络不进测试；
- sleeper 可注入——退避等待不进测试（这是"时间加速"的正确姿势，原因见 README）；
- clock 可注入——时间戳逻辑交给 time-machine 冻结。
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone


class TransientError(Exception):
    """瞬态错误：值得重试（超时、5xx、限流）"""


class FatalError(Exception):
    """致命错误：重试没有意义（4xx、参数错）"""


@dataclass
class Response:
    status: int
    body: str
    fetched_at: datetime


@dataclass
class AsyncRetryClient:
    transport: object = None                      # async (url) -> Response
    retries: int = 3                              # 总尝试次数（含首次）
    backoff_base: float = 0.5                     # 首次退避秒数，之后 ×2
    sleeper: object = field(default=asyncio.sleep)  # 可替换的"睡觉"实现
    clock: object = field(default=lambda: datetime.now(timezone.utc))

    async def get(self, url: str) -> Response:
        last_exc: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                resp = await self.transport(url)
                resp.fetched_at = self.clock()
                return resp
            except TransientError as exc:
                last_exc = exc
                if attempt == self.retries:       # 最后一次：不再退避，直接抛出
                    raise
                await self.sleeper(self.backoff_base * 2 ** (attempt - 1))
            except FatalError:                    # 致命错误立即上抛，不浪费重试
                raise
        raise last_exc  # pragma: no cover——防御分支
