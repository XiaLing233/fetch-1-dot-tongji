FROM python:3.11-alpine

WORKDIR /app

RUN pip install --no-cache-dir redis==5.2.1

COPY email_consumer.py .

CMD ["python3", "-u", "email_consumer.py"]
