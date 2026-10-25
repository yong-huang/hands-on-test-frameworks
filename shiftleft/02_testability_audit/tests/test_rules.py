"""规则引擎单测：每条规则「坏的查得出、好的零误报」+ 评分封顶与分档边界。

运行：pytest tests/ -q   （在实验根目录）
夹具直接加载 configs/ 下的规则与样例——测试的就是生产口径，不另养一套。
"""
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit import RuleEngine  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RULES = yaml.safe_load((ROOT / "configs/rules.yaml").read_text())
STORIES = yaml.safe_load((ROOT / "configs/stories.yaml").read_text())["stories"]
ENGINE = RuleEngine(RULES)


def audit_one(acs, title="测试故事", sid="US-X"):
    return ENGINE.audit_story({"id": sid, "title": title, "acceptance_criteria": acs})


def rules_of(result):
    return [f["rule"] for f in result["findings"]]


# ---------- 规则 1：歧义词 ----------

def test_vague_word_hit():
    r = audit_one(["系统响应要快速"])
    assert "vague_word" in rules_of(r)
    assert r["score"] == 75  # 歧义词 −15，无数字 −10；「响应」是线索词，不扣自动化分


def test_vague_word_clean_text_no_hit():
    assert "vague_word" not in rules_of(audit_one(["调用接口返回 422"]))


@pytest.mark.parametrize("word", ["快速", "稳定", "优化", "满意", "正确"])
def test_vague_word_table(word):
    assert "vague_word" in rules_of(audit_one([f"服务{word}"]))


# ---------- 规则 2：可观察预期值 ----------

def test_observable_digit_no_hit():
    assert "no_observable" not in rules_of(audit_one(["返回 422"]))


def test_no_observable_deducted():
    assert "no_observable" in rules_of(audit_one(["接口返回处理结果"]))  # 无任何数字


# ---------- 规则 3：可自动化线索 ----------

def test_automation_hint_no_hit_when_present():
    assert "no_automation" not in rules_of(audit_one(["调用 POST /api/orders 返回 200"]))


def test_no_automation_deducted():
    assert "no_automation" in rules_of(audit_one(["页面配色得体"]))  # 无接口/字段线索


# ---------- 规则 4/5：依赖与连接词 ----------

def test_dependency_word_hit():
    assert "dependency" in rules_of(audit_one(["在上游完成后校验数据 42 条"]))


def test_dependency_clean_no_hit():
    assert "dependency" not in rules_of(
        audit_one(["下单成功调用 PUT /api/stock 后库存字段减 1，返回 200"]))


def test_connector_word_hit():
    assert "connector" in rules_of(audit_one(["同时校验订单金额与库存余量 2 个字段"]))


# ---------- 结构性封顶与评分下限 ----------

def test_empty_acs_capped_at_40():
    r = audit_one([])
    assert r["score"] == 40 and "empty_acs" in rules_of(r)


def test_oversized_capped_at_55():
    acs = [f"调用接口创建优惠券类型 {i}，返回 201" for i in range(9)]
    r = audit_one(acs)
    assert r["score"] <= 55 and "too_many" in rules_of(r)


def test_exactly_max_acs_not_oversized():
    acs = [f"调用接口执行操作 {i}，返回 200" for i in range(1, 8)]  # 恰好 7 条
    assert "too_many" not in rules_of(audit_one(acs))


def test_score_floor_zero():
    r = audit_one([f"快速{w}优化" for w in ("合理", "稳定", "友好")])  # 每条 2 个歧义词
    assert r["score"] == 0  # 100 − 6×15 = 10 → 再加无数字/无线索扣分触底


# ---------- 分档边界 ----------

@pytest.mark.parametrize("score,tier", [(100, "良好"), (80, "良好"), (79, "需修订"),
                                        (60, "需修订"), (59, "不可测"), (0, "不可测")])
def test_tier_boundaries(score, tier):
    assert ENGINE.tier_of(score) == tier


# ---------- 样例故事整体验收：5 好 ≥80，5 坏 ≤60 且建议可执行 ----------

@pytest.mark.parametrize("sid", ["US-G1", "US-G2", "US-G3", "US-G4", "US-G5"])
def test_good_stories_score_at_least_80(sid):
    story = next(s for s in STORIES if s["id"] == sid)
    assert ENGINE.audit_story(story)["score"] >= 80


@pytest.mark.parametrize("sid", ["US-B1", "US-B2", "US-B3", "US-B4", "US-B5"])
def test_bad_stories_score_at_most_60(sid):
    story = next(s for s in STORIES if s["id"] == sid)
    assert ENGINE.audit_story(story)["score"] <= 60


@pytest.mark.parametrize("sid", ["US-B1", "US-B2", "US-B3", "US-B4", "US-B5"])
def test_bad_stories_have_actionable_suggestion(sid):
    story = next(s for s in STORIES if s["id"] == sid)
    r = ENGINE.audit_story(story)
    assert r["findings"], f"{sid} 必须至少给出 1 条违规"
    assert all(f["suggestion"].strip() for f in r["findings"])
