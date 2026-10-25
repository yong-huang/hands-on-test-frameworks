FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir httpx
COPY bff.py ./
EXPOSE 9804
CMD ["python", "bff.py"]
