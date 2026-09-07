"""lab 08 用例：async fixture、重试矩阵、退避加速、超时与取消、时间冻结。

关键设计：测试注入 fake sleep（记录"名义退避时长"、瞬间完成），
因此 3 次重试名义上要等 3.5s 的用例，真实耗时 <1ms——确定性且飞快。
time-machine 负责另一类时间断言：时间戳本身。
"""
import asyncio
import time
from dataclasses import dataclass, field

import pytest
import time_machine

from client import AsyncRetryClient, FatalError, Response, TransientError

OK = Response(status=200, body="ok", fetched_at=None)
FAIL = TransientError("503 busy")
BAD = FatalError("400 bad request")


@dataclass
class Recorder:
    calls: int = 0
    urls: list = field(default_factory=list)
    sleeps: list = field(default_factory=list)  # 每次名义退避的秒数


# ---------- async 工厂 fixture：按"剧本"组装客户端 ----------
@pytest.fixture()
def make_client():
    """outcomes 是一段剧本：每次调用依次取一个结果（Response 或异常）"""

    def _make(outcomes, **kw):
        rec = Recorder()

        async def transport(url):
            rec.calls += 1
            rec.urls.append(url)
            out = outcomes[min(rec.calls, len(outcomes)) - 1]
            if isinstance(out, Exception):
                raise out
            return out

        async def fake_sleep(seconds):
            rec.sleeps.append(seconds)  # 记账不真睡：时间加速的正确姿势

        return AsyncRetryClient(transport=transport, sleeper=fake_sleep, **kw), rec

    return _make


# ---------- 重试矩阵 ----------
async def test_success_first_try(make_client):
    """一次成功：零退避、只调一次"""
    c, rec = make_client([OK])
    assert (await c.get("u://a")).status == 200
    assert (rec.calls, rec.sleeps) == (1, [])


async def test_retry_then_success(make_client):
    """挂两次活一次：共调 3 次，退避序列 [0.5, 1.0]——指数增长"""
    c, rec = make_client([FAIL, FAIL, OK])
    assert (await c.get("u://a")).body == "ok"
    assert rec.calls == 3
    assert rec.sleeps == [0.5, 1.0]


async def test_retries_exhausted(make_client):
    """三次全挂：TransientError 上抛；最后一次失败前没有多余退避"""
    c, rec = make_client([FAIL, FAIL, FAIL])
    with pytest.raises(TransientError):
        await c.get("u://a")
    assert rec.calls == 3
    assert rec.sleeps == [0.5, 1.0]


async def test_fatal_not_retried(make_client):
    """致命错误零重试：重试预算不浪费在 4xx 上"""
    c, rec = make_client([BAD])
    with pytest.raises(FatalError):
        await c.get("u://a")
    assert (rec.calls, rec.sleeps) == (1, [])


async def test_backoff_accelerated_under_1s(make_client):
    """核心演示：名义退避 3.5s（0.5+1.0+2.0），真实耗时 <1s"""
    c, rec = make_client([FAIL, FAIL, FAIL, FAIL], retries=4)  # 4 次尝试 → 退避 [0.5,1.0,2.0]=3.5s 名义
    t0 = time.perf_counter()
    with pytest.raises(TransientError):
        await c.get("u://a")
    elapsed = time.perf_counter() - t0
    assert rec.sleeps == [0.5, 1.0, 2.0]          # 名义退避序列正确
    assert elapsed < 1.0, f"退避没有被加速？实际 {elapsed:.3f}s"


# ---------- 超时与取消：asyncio 原生行为的确定性测试 ----------
async def test_hanging_transport_times_out(make_client):
    """挂死的 transport 被 asyncio.wait_for 处决：0.05s 真实等待，确定性"""
    rec_holder = {}

    async def hanging(url):
        await asyncio.sleep(30)  # 假装网络黑洞
        return OK

    c = AsyncRetryClient(transport=hanging)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(c.get("u://a"), timeout=0.05)


async def test_cancellation_propagates(make_client):
    """任务被 cancel 后 CancelledError 必须浮出——异步清理不吞异常"""
    started = asyncio.Event()

    async def slow(url):
        started.set()
        await asyncio.sleep(5)
        return OK

    c = AsyncRetryClient(transport=slow)
    task = asyncio.create_task(c.get("u://a"))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


# ---------- time-machine：时间戳断言（另一类"时间测试"） ----------
@time_machine.travel("2026-09-01 08:00:00 +00:00")
async def test_fetched_at_frozen(make_client):
    """冻结时钟后 fetched_at 是确定值——把'当前时间'变成可断言的输入"""
    c, rec = make_client([OK])
    resp = await c.get("u://a")
    assert resp.fetched_at.year == 2026
    assert (resp.fetched_at.month, resp.fetched_at.day) == (9, 1)
