FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 用法: docker compose run --rm crawler
ENTRYPOINT ["python3", "-u", "fetchNewEvents.py"]
CMD []
