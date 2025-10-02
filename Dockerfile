FROM python:3.12-slim
WORKDIR /app
COPY . /app
ENV ROOT_DIR=/app/public
ENV PORT=8000
EXPOSE 8000
CMD ["python", "server.py"]
