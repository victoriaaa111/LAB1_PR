FROM python:3.12-slim
WORKDIR /app
COPY server_mt.py ./
ENV PORT=8001 MAX_WORKERS=16 SIMULATE_WORK_MS=0
EXPOSE 8001
CMD ["python", "server_mt.py", "/serve"]
