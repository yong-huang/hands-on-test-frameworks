"""lab 07 被测对象：订单"API 载荷构造 + HTML 行渲染"——两类典型快照对象。"""
import os

# SNAP_BREAK=1 时故意改坏输出——供演示"输出变化 → 快照变红"（正常跑测试别设它）
_BREAK = os.environ.get("SNAP_BREAK") == "1"


def order_payload(order: dict) -> dict:
    """把订单行聚合成 API 返回载荷：字段多、嵌套深、改一处牵全身——快照的主场"""
    qty, price = order["qty"], order["price"]
    total = round(qty * price + 1, 2) if _BREAK else round(qty * price, 2)
    return {
        "id": order["id"],
        "customer": {"name": order["customer"], "tier": order.get("tier", "regular")},
        "item": {"sku": order["sku"], "qty": qty, "unit_price": price},
        "amount": {"currency": "CNY", "total": total},
        "meta": {"channel": order.get("channel", "web"), "version": 3},
    }


def render_row(payload: dict) -> str:
    """把载荷渲染成表格行 HTML：前端回归时 HTML 片段就是要守住的"画面" """
    td, th = ("<td>", "<th>") if _BREAK else ("<td>", "<td>")
    return (
        f'<tr data-id="{payload["id"]}">'
        f'{td} class="name">{payload["customer"]["name"]}</{td[:-1]}>'
        f'{td} class="qty">{payload["item"]["qty"]}</{td[:-1]}>'
        f'{th} class="total">¥{payload["amount"]["total"]}</{th[:-1]}>'
        "</tr>"
    )
