"""邮件消费者：从 Redis 队列取任务，通过 smtplib 发送。"""

import json
import os
import smtplib
import time
from email.mime.text import MIMEText

import redis


def create_mail_client():
    """创建 SMTP 连接。"""
    host = os.getenv('SMTP_HOST', 'localhost')
    port = int(os.getenv('SMTP_PORT', '465'))
    user = os.getenv('SMTP_USER', '')
    password = os.getenv('SMTP_PASS', '')
    nickname = os.getenv('SMTP_NICKNAME', '琪露诺bot')

    server = smtplib.SMTP_SSL(host, port)
    server.login(user, password)
    return server, user, nickname


def send_one(server, smtp_user, nickname, task):
    """发送单封邮件。"""
    msg = MIMEText(task['body'], 'plain', 'utf-8')
    msg['From'] = f'{nickname} <{smtp_user}>'
    msg['To'] = task['to']
    msg['Subject'] = task['subject']
    server.sendmail(smtp_user, task['to'], msg.as_string())
    print(f"[EMAIL] 已发送: {task['to']} - {task['subject']}")


def run_consumer():
    """主循环：阻塞式从 Redis 队列取任务并发送。"""
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', '6379'))
    r = redis.Redis(host=redis_host, port=redis_port, db=0)

    print("[EMAIL] 消费者启动，等待邮件任务...")

    while True:
        try:
            # BRPOP 阻塞等待，超时 30s 后重试
            result = r.brpop('email:queue', timeout=30)
            if result is None:
                continue

            _, raw = result
            task = json.loads(raw)
            server, user, nickname = create_mail_client()
            send_one(server, user, nickname, task)
            server.quit()

        except Exception as e:
            # 发送失败：放回队列头部，稍后重试
            print(f"[EMAIL] 发送失败 ({e})，稍后重试")
            try:
                r.lpush('email:queue', raw)
            except Exception:
                pass
            time.sleep(5)


if __name__ == '__main__':
    run_consumer()
