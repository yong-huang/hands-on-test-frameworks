FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir ariadne uvicorn
COPY server.py schema.graphql ./
EXPOSE 9750
CMD ["uvicorn", "server:serve", "--host", "0.0.0.0", "--port", "9750"]
