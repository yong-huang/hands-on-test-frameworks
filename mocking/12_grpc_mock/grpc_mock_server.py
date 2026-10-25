#!/usr/bin/env python3
"""gRPC 替身服务端：proto 驱动的 unary + server-streaming。

- 字段校验：order_id 为空 → INVALID_ARGUMENT，消息里点名字段（proto3 没有
  required，必填语义由服务端显式校验——这正是 gRPC 校验的常规做法）
- 流式应答：固定 5 条生命周期事件，seq 1..5 有序，客户端可断言顺序
"""
import sys
from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

sys.path.insert(0, "proto")
import order_pb2
import order_pb2_grpc

STAGES = ["created", "paid", "reviewed", "shipped", "settled"]


class OrderQueryServicer(order_pb2_grpc.OrderQueryServicer):

    def GetOrder(self, request, context):
        if not request.order_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT,
                          "order_id is required（缺必填字段：order_id）")
        return order_pb2.OrderResponse(
            order_id=request.order_id,
            customer="alice",
            amount=123.5,
            status="created",
        )

    def StreamOrderEvents(self, request, context):
        if not request.order_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT,
                          "order_id is required（缺必填字段：order_id）")
        for seq, stage in enumerate(STAGES, start=1):
            yield order_pb2.OrderEvent(seq=seq, stage=stage,
                                       order_id=request.order_id)


def serve(port: int) -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    order_pb2_grpc.add_OrderQueryServicer_to_server(OrderQueryServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{port}")
    # 开启反射：grpcurl 的 list 与不带 -proto 的调用都依赖它
    reflection.enable_server_reflection((
        order_pb2.DESCRIPTOR.services_by_name['OrderQuery'].full_name,
        reflection.SERVICE_NAME,
    ), server)
    server.start()
    print(f"gRPC 替身已就绪，监听 :{port}", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    serve(int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 9850)
