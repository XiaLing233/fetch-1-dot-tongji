"""邮件队列：生产者。路由层只需调用 enqueue_email() 入队即可返回。"""

import json
import time

from utils.redis_client import get_redis


def enqueue_email(to, subject, body, use_batch=False, is_html=False):
    """
    将邮件任务推入 Redis 队列。

    use_batch=True  → 使用批量发送账号（通知推送）
    is_html=True    → HTML 格式正文
    """
    redis_client = get_redis()
    task = json.dumps({
        'to': to,
        'subject': subject,
        'body': body,
        'use_batch': use_batch,
        'is_html': is_html,
        'queued_at': time.time(),
    }, ensure_ascii=False)
    redis_client.lpush('email:queue', task)
    print(f"[EMAIL] 入队: {to} - {subject}")
