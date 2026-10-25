"""契约测试唯一入口：schemathesis 把 contract.yaml 的每个操作变成 property-based 测试。

先有契约后有实现——本文件只认识 contract.yaml，不 import 任何实现代码：
被测对象由 conftest 按 APP_IMPL 起 uvicorn 子进程，schemathesis 生成的随机
请求打过去，响应逐条对契约校验（状态码一致 + 响应体符合 schema + 不允许 5xx）。
"""
import os
from pathlib import Path

import pytest
import yaml
import schemathesis
from schemathesis import checks
from schemathesis.pytest import parametrize

from conftest import RUN_STATS

ROOT = Path(__file__).resolve().parent
CONTRACT = Path(os.environ.get("CONTRACT", ROOT / "contract.yaml"))
raw = yaml.safe_load(CONTRACT.read_text())
schema = schemathesis.openapi.from_dict(raw)

# 核心契约检查四件套：不允许 5xx、状态码在契约内、内容类型一致、响应体符合 schema。
# 默认集还含 Allow 头/否定拒绝等框架向检查——与 FastAPI 的 405/422 行为打架，
# 属框架怪癖而非契约违反，本实验聚焦契约语义，显式只留四件套。
CORE_CHECKS = [checks.not_a_server_error, checks.status_code_conformance,
               checks.content_type_conformance, checks.response_schema_conformance]


@parametrize(schema=schema)  # 4.x 的 parametrize 只收关键字参数（**schemas）
def test_contract_first(case, base_url):
    RUN_STATS["cases"] += 1  # 实际执行的生成案例数：验收「≥50」看这个实测值
    case.call_and_validate(base_url=base_url, checks=CORE_CHECKS)
