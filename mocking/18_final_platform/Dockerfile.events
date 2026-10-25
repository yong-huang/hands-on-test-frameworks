FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir kafka-python-ng
COPY events_worker.py ./
CMD ["python", "events_worker.py"]
