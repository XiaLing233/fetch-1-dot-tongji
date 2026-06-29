FROM python:3.11-alpine

WORKDIR /app

RUN pip install --no-cache-dir redis==5.2.1

COPY utils/redis_client.py /app/utils/redis_client.py

COPY services/email_consumer.py /app/email_consumer.py

CMD ["python3", "-u", "email_consumer.py"]
