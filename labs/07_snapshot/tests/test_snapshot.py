"""lab 07 用例：对 API JSON 与渲染 HTML 各拍一张快照。

snapshot fixture 来自 syrupy；快照文件在 tests/__snapshots__/*.ambr，
由 --snapshot-update 生成或更新（先审查 diff，再有意更新——绝不无脑 -u）。
"""
ORDER = {
    "id": "A1024",
    "customer": "王小明",
    "sku": "SKU-88",
    "qty": 3,
    "price": 19.9,
    "tier": "vip",
    "channel": "app",
}


def test_order_payload_snapshot(snapshot):
    from renderer import order_payload
    assert order_payload(ORDER) == snapshot


def test_render_row_snapshot(snapshot):
    from renderer import order_payload, render_row
    assert render_row(order_payload(ORDER)) == snapshot
