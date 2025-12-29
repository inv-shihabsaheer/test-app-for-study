FROM python:3.11-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

ENV APP_NAME=myapp
ENV APP_ENV=production
ENV APP_VERSION=1.0.0

EXPOSE 8080

CMD ["python", "main.py"]
