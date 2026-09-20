# SUT 镜像：一份应用，N 个隔离实例（ephemeral 环境的原料）
FROM python:3.12-slim
WORKDIR /app
COPY app/ /app/
RUN pip install --no-cache-dir fastapi uvicorn
ENV SUT_DB=/app/data/orders.db
RUN mkdir -p /app/data
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
