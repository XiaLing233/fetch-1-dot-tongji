FROM python:3.11-slim

WORKDIR /app

# 安装 crawler 自身依赖
COPY crawler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制 crawler 代码
COPY crawler/ .

# 从 backend 复制共享模块
COPY backend/db ./db
COPY backend/services/__init__.py ./services/__init__.py
COPY backend/services/cos.py ./services/cos.py
COPY backend/utils/__init__.py ./utils/__init__.py
COPY backend/utils/email.py ./utils/email.py
COPY backend/utils/redis_client.py ./utils/redis_client.py

# 用法: docker compose run --rm crawler
ENTRYPOINT ["python3", "-u", "fetchNewEvents.py"]
CMD []
