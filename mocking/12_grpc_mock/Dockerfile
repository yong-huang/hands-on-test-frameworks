FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir grpcio grpcio-tools grpcio-reflection
COPY proto/ proto/
COPY grpc_mock_server.py ./
RUN python -m grpc_tools.protoc -I proto --python_out=proto --grpc_python_out=proto proto/order.proto
EXPOSE 9850
CMD ["python", "grpc_mock_server.py", "--port", "9850"]
