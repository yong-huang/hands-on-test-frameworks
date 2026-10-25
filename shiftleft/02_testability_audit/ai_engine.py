"""ai_engine.py —— AI 可测性评估引擎：调本地 Ollama 模型做语义层可测性判断。

与规则引擎（audit.py）的关系：两层并行，不替换——
  规则层（确定性）：关键词匹配 + 结构规则，快、可复现、零成本
  AI 层（语义）：LLM 理解「为什么不可测」，能抓规则漏掉的语义模糊

用法：
    from ai_engine import assess_story
    result = assess_story(story_dict)   # → {"score": int, "findings": [...], "raw": str}
"""
import json
import re

import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3.8:latest"

SYSTEM_PROMPT = """你是测试可测性评估专家。对给定的验收条件列表，逐条评估可测性。
返回 JSON（不要 markdown 代码块）：
{"score": 0-100整数, "findings": [{"ac_index": 0, "issue": "问题描述", "suggestion": "改进建议"}]}

评分标准（从 100 开始扣）：
- 模糊/主观词（快速/友好/稳定/合理等）：每处 -15
- 无可断言预期值（没有数字/状态码/明确终态）：每条 -10
- 无法自动化（纯 UI 感受/人工判断）：每条 -10
- 依赖其他故事/条件：每处 -10
- 一条塞多个行为：每处 -5

如果所有验收条件都完美可测，score=100，findings 为空数组。"""


def assess_story(story: dict, timeout: int = 120) -> dict:
    """调 Ollama 评估单条用户故事的可测性。

    返回 {"score": int, "findings": [...], "model": str, "raw": str}。
    连接失败或解析失败时返回 {"score": None, "error": "..."}。
    """
    acs = story.get("acceptance_criteria", [])
    if not acs:
        return {"score": None, "error": "无验收条件"}

    ac_text = "\n".join(f"{i}. {ac}" for i, ac in enumerate(acs))
    user_msg = f"用户故事：{story.get('title', '')}\n验收条件：\n{ac_text}"

    try:
        r = httpx.post(OLLAMA_URL, json={
            "model": MODEL,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        }, timeout=timeout)
        raw = r.json()["message"]["content"]
    except httpx.ConnectError:
        return {"score": None, "error": "Ollama 未运行（http://127.0.0.1:11434 连接失败）"}
    except httpx.TimeoutException:
        return {"score": None, "error": f"Ollama 响应超时（>{timeout}s）"}
    except Exception as e:
        return {"score": None, "error": f"Ollama 调用异常：{e}"}

    parsed = _extract_json(raw)
    if parsed is None:
        return {"score": None, "error": f"JSON 解析失败：{raw[:120]}"}

    score = parsed.get("score")
    if not isinstance(score, (int, float)) or not (0 <= score <= 100):
        return {"score": None, "error": f"score 字段异常：{score}"}

    return {
        "score": int(score),
        "findings": parsed.get("findings", []),
        "model": MODEL,
        "raw": raw,
    }


def _extract_json(text: str) -> dict | None:
    """从 LLM 输出中提取 JSON（容忍 markdown 代码块和前后噪音）。"""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        return None
