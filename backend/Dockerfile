FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "--worker-class", "gevent", "--access-logfile", "-", "--error-logfile", "-", "app:application"]
