# lab 30：make quality —— 一键本地等价流水线（失败即阻断，顺序同 CI）
# 快速通道：make unit / api / e2e / perf / a11y 逐层单独跑
PY := .venv/bin/python

.PHONY: quality unit api e2e perf a11y clean

quality: unit api e2e perf a11y
	@echo ""
	@echo "================ 全层流水线通过 ✅ ================"

unit:
	@echo "=====> [unit] pytest 基本功 + 高级单测（绿色子集；教学脚本含故意失败，故直接调 pytest）"
	cd labs/01_pytest_basics && ../../.venv/bin/python -m pytest -c configs/pytest.ini --rootdir=. -q -k "not regression_demo"
	cd labs/03_parametrize && ../../.venv/bin/python -m pytest -c configs/pytest.ini --rootdir=. -q
	cd labs/08_async && ../../.venv/bin/python -m pytest -c configs/pytest.ini --rootdir=. -q

api:
	@echo "=====> [api] API 测试套件"
	cd labs/12_api_tests && ./api_tests.sh

e2e:
	@echo "=====> [e2e] Playwright E2E"
	cd labs/16_pw_basics && ./pw_basics.sh

perf:
	@echo "=====> [perf] k6 smoke"
	cd labs/27_k6 && ./k6_run.sh

a11y:
	@echo "=====> [a11y+security] 双基线"
	cd labs/29_a11y_security && ./a11y_security.sh

clean:
	cd labs/16_pw_basics && ./pw_basics.sh clean || true
	cd labs/12_api_tests && ./api_tests.sh clean || true
	cd labs/27_k6 && ./k6_run.sh clean || true
	cd labs/29_a11y_security && ./a11y_security.sh clean || true
	cd labs/11_sut_app && ./sut_app.sh clean || true
	@echo "全部清理完成"
