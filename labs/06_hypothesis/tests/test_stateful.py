"""lab 06 有状态测试：RuleBasedStateMachine 对一个简单队列做"规则轰炸"。

传统用例是"编剧"（你安排剧情），RuleBasedStateMachine 是"导演"——
它随机挑规则执行几百步，用不变量随时抓违规。
"""
from hypothesis import HealthCheck, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule


class Queue:
    """被测对象：FIFO 队列（内置 list 简化实现）"""

    def __init__(self) -> None:
        self._items: list = []

    def push(self, x) -> None:
        self._items.append(x)

    def pop(self):
        """空队列 pop 返回 None 而不是抛错——一条容易被忽略的边界契约"""
        return self._items.pop(0) if self._items else None

    def __len__(self) -> int:
        return len(self._items)


class QueueMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.q = Queue()
        self.model: list = []  # 心智模型：用最朴素的 list 记录"应该"的状态

    @rule(x=st.integers())
    def push(self, x):
        self.q.push(x)
        self.model.append(x)

    @rule()
    def pop(self):
        expect = self.model.pop(0) if self.model else None
        assert self.q.pop() == expect  # FIFO 次序永远与模型一致

    @precondition(lambda self: len(self.model) > 0)
    @rule()
    def pop_nonempty_returns_head(self):
        """前置条件版规则：仅当队列非空才抽中执行"""
        assert self.q.pop() == self.model.pop(0)

    @invariant()
    def size_matches_model(self):
        """不变量：任意一步之后长度必须与模型一致"""
        assert len(self.q) == len(self.model)


QueueMachine.TestCase.settings = settings(
    max_examples=25, stateful_step_count=30, deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
TestQueueMachine = QueueMachine.TestCase
