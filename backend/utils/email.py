"""邮件队列：生产者。路由层只需调用 enqueue_email() 入队即可返回。"""

import json
import time

from utils.redis_client import get_redis


def enqueue_email(to, subject, body):
    """
    将邮件任务推入 Redis 队列。
    路由层调用此函数后立即返回，不阻塞 HTTP 响应。
    """
    redis_client = get_redis()
    task = json.dumps({
        'to': to,
        'subject': subject,
        'body': body,
        'queued_at': time.time(),
    }, ensure_ascii=False)
    redis_client.lpush('email:queue', task)
    print(f"[EMAIL] 入队: {to} - {subject}")
