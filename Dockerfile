FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_NAME=myapp \
    APP_ENV=production \
    APP_VERSION=1.0.0

WORKDIR /app

COPY app/requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt \
    && useradd -m appuser

COPY app/ .

USER appuser

EXPOSE 8080

CMD ["python", "main.py"]
