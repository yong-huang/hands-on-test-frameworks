FROM python:3.13-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ app/
# workers 数是项目 8 的调参旋钮（默认 1）；shell 形式为了展开环境变量
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8931 --workers ${UVICORN_WORKERS:-1}"]
