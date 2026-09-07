# axe-core 扫描修复前后对比（SUT · 2026-09 实测）

## 修复前（首次扫描）

| 页面 | 违例 id | 等级 | 说明 |
|:---|:---|:---|:---|
| / (index.html) | label | **critical** | 表单元素必须有关联 label（客户名/商品/数量/单价 4 个输入框只有 placeholder） |
| /login.html | label | **critical** | 用户名/密码输入框同样缺 label |

（运行 `SUT_URL=... pytest tests/test_a11y.py` 可复现上述红。）

## 修复动作（SUT 侧，labs/11_sut_app/app/static/）

- `index.html`：4 个输入框补 `aria-label`（客户名/商品/数量/单价）
- `login.html`：2 个输入框补 `aria-label`（用户名/密码）

## 修复后

| 页面 | critical/serious 违例 |
|:---|:---|
| / | 0 ✅ |
| /login.html | 0 ✅ |
| /slow.html | 0 ✅ |

门禁用例：`tests/test_a11y.py`（impact ∈ {critical, serious} 必须为空）。
一键重跑：`./a11y_security.sh`。
