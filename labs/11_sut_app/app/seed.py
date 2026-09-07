"""种子数据：一条命令造出演示订单（make seed / python seed.py）"""
import store

DEMO_ORDERS = [
    ("王小明", "机械键盘", 1, 399.0),
    ("李华",   "显示器支架", 2, 159.0),
    ("Cindy",  "USB-C 扩展坞", 1, 299.0),
    ("张伟",   "人体工学椅", 1, 1299.0),
    ("刘洋",   "笔记本支架", 3, 89.0),
    ("Alice",  "降噪耳机", 1, 1699.0),
    ("陈静",   "桌面台灯", 2, 129.0),
    ("Bob",    "4K 摄像头", 1, 549.0),
    ("赵磊",   "机械键盘", 2, 399.0),
    ("孙芳",   "升降桌", 1, 2499.0),
]


def seed(db_path) -> int:
    store.init_db(db_path)
    n = 0
    for customer, item, qty, price in DEMO_ORDERS:
        store.create_order(db_path, customer, item, qty, price)
        n += 1
    return n


if __name__ == "__main__":
    import argparse
    import pathlib
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=str(pathlib.Path(__file__).parent / "orders.db"))
    args = p.parse_args()
    n = seed(args.db)
    print(f"已写入 {n} 条演示订单 -> {args.db}")
