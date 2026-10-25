#!/usr/bin/env python3
"""compose 形态的编排 worker（testcontainers 版见 event_pipeline.py）：
注入 6 类事件 → 消费 → 结果写 RESULT_PATH（正常/乱序全处理、毒丸进 DLQ、不阻塞）。"""
import json, os, time
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP = os.environ.get("BOOTSTRAP", "redpanda:9092")
TOPIC, DLQ = "orders.events", "orders.dlq"
RESULT = os.environ.get("RESULT_PATH", "/results/events.json")

def wait_kafka():
    for _ in range(60):
        try:
            KafkaProducer(bootstrap_servers=BOOTSTRAP).close(); return
        except Exception: time.sleep(1)
    raise RuntimeError("Kafka 不可达")

def main():
    wait_kafka()
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP)
    events = [
        {"seq": 1, "type": "normal", "stage": "created"},
        {"seq": 2, "type": "normal", "stage": "paid"},
        {"seq": 3, "type": "normal", "stage": "reviewed"},
        {"seq": 3, "type": "out-of-order", "stage": "reviewed-dup"},
        "NOT-JSON-{{{",
        {"seq": 4, "type": "normal", "stage": "shipped"},
    ]
    for ev in events:
        producer.send(TOPIC, value=ev.encode() if isinstance(ev, str) else json.dumps(ev).encode())
    producer.flush()

    consumer = KafkaConsumer(TOPIC, bootstrap_servers=BOOTSTRAP,
                             auto_offset_reset="earliest", consumer_timeout_ms=15000,
                             value_deserializer=lambda v: v.decode("utf-8", "replace"))
    processed, dead = [], []
    for msg in consumer:
        try: processed.append(json.loads(msg.value))
        except json.JSONDecodeError: dead.append(msg.value)

    ok = (len(processed) == 5 and len(dead) == 1 and any(e.get("seq") == 4 for e in processed))
    result = {"processed": len(processed), "dead_letter": len(dead),
              "seqs": [e.get("seq") for e in processed], "verdict": "GREEN" if ok else "RED"}
    with open(RESULT, "w", encoding="utf-8") as f: json.dump(result, f, ensure_ascii=False)
    print(json.dumps(result, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
