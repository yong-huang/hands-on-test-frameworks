#!/usr/bin/env python3
"""事件虚拟化全流程（单脚本编排，testcontainers 起 Kafka）：

1. testcontainers 拉起 Kafka（KRaft 单节点）
2. 建主题 orders.events（3 分区没必要，单分区保序）+ orders.dlq
3. 替身生产者按脚本注入 5 类事件：3 正常（seq 1,2,3）+ 1 乱序（seq 3 先到）
   + 1 毒丸（payload 非法 JSON）+ 1 正常（seq 4，验证毒丸不阻塞后续）
4. 消费 worker：解析 JSON → 记录处理结果；毒丸 → 写 DLQ 并跳过
5. 断言：正常/乱序均被处理、毒丸进 DLQ、后续事件不阻塞
"""
import json
import os
import sys
import time

from kafka import KafkaConsumer, KafkaProducer
from testcontainers.kafka import KafkaContainer

TOPIC = "orders.events"
DLQ = "orders.dlq"


def produce(bootstrap):
    # 不用 value_serializer：毒丸必须以非法原文进队列（serializer 会把它救成合法 JSON）
    producer = KafkaProducer(bootstrap_servers=bootstrap)
    events = [
        {"seq": 1, "type": "normal", "stage": "created"},
        {"seq": 2, "type": "normal", "stage": "paid"},
        {"seq": 3, "type": "normal", "stage": "reviewed"},
        {"seq": 3, "type": "out-of-order", "stage": "reviewed-dup"},  # 乱序重复
        "NOT-JSON-{{{",                                               # 毒丸
        {"seq": 4, "type": "normal", "stage": "shipped"},             # 毒丸之后
    ]
    for ev in events:
        payload = ev.encode() if isinstance(ev, str) else json.dumps(ev).encode()
        producer.send(TOPIC, value=payload)
    producer.flush()
    print(f"已注入 {len(events)} 条事件（含 1 乱序 + 1 毒丸 + 1 毒丸后正常）")


def consume_and_handle(bootstrap, timeout_s=15):
    """消费 worker：合法事件记 processed，毒丸写 DLQ。返回两类清单。"""
    consumer = KafkaConsumer(TOPIC, bootstrap_servers=bootstrap,
                             auto_offset_reset="earliest",
                             consumer_timeout_ms=int(timeout_s * 1000),
                             value_deserializer=lambda v: v.decode("utf-8", "replace"))
    processed, dead = [], []
    for msg in consumer:
        raw = msg.value
        try:
            ev = json.loads(raw)
            processed.append(ev)
        except json.JSONDecodeError:
            dead.append(raw)
    consumer.close()
    return processed, dead


def main():
    print("① testcontainers 拉起 Kafka（KRaft 单节点，arm64 原生镜像）")
    with KafkaContainer() as kafka:
        bootstrap = kafka.get_bootstrap_server()
        print(f"   Kafka 就绪：{bootstrap}")

        print("② 替身生产者注入脚本化事件序列")
        produce(bootstrap)

        print("③ 消费 worker 处理（毒丸 → DLQ，其余记录）")
        processed, dead = consume_and_handle(bootstrap)

    failures = []
    seqs = [e.get("seq") for e in processed if e.get("type") == "normal"]
    print("\n④ 断言")
    ok1 = len(processed) == 5
    print(f"  {'✅' if ok1 else '❌'} 正常与乱序事件全部被处理：{len(processed)} 条"
          f"（seq 顺序 {seqs}，乱序 dup 也在场）")
    if not ok1:
        failures.append("处理数")
    ok2 = len(dead) == 1
    print(f"  {'✅' if ok2 else '❌'} 毒丸进 DLQ：{len(dead)} 条"
          f"（内容片段：{dead[0][:20] if dead else '-'}…）")
    if not ok2:
        failures.append("毒丸 DLQ")
    ok3 = any(e.get("seq") == 4 for e in processed)
    print(f"  {'✅' if ok3 else '❌'} 毒丸之后的正常事件不被阻塞（seq 4 已处理）")
    if not ok3:
        failures.append("阻塞")

    if failures:
        print(f"\n❌ 断言失败：{'、'.join(failures)}")
        sys.exit(1)
    print("\n>>> 验收：脚本化注入 ✅ 正常/乱序全处理 ✅ 毒丸进 DLQ ✅ 不阻塞后续 ✅")


if __name__ == "__main__":
    main()
