FROM python:3.12-slim
WORKDIR /app
COPY server.py client.py ./
RUN useradd -m app && chown -R app:app /app
USER app
EXPOSE 8000