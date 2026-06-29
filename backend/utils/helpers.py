"""共享辅助函数：限流、邮件发送、IP 获取等。"""

import re
import time
import random
import datetime

from flask import request, session, current_app


# ----- 工具函数 ----- #

def triedTooManyTimes():
    return session.get('tried_times', 0) >= 5


def checkEmailFormat(email):
    if re.match(r'^[a-zA-Z0-9._-]+@tongji\.edu\.cn$', email):
        return True
    return False


def generateVerificationCode():
    return str(random.randint(100000, 999999))


def get_client_ip():
    """
    安全地获取客户端真实IP地址
    优先级：CF-Connecting-IP > X-Real-IP > X-Forwarded-For(最后一个) > remote_addr
    """
    if 'CF-Connecting-IP' in request.headers:
        return request.headers.get('CF-Connecting-IP')
    if 'X-Real-IP' in request.headers:
        return request.headers.get('X-Real-IP')
    if 'X-Forwarded-For' in request.headers:
        forwarded_ips = request.headers.get('X-Forwarded-For').split(',')
        for ip in reversed(forwarded_ips):
            ip = ip.strip()
            if not ip.startswith(('10.', '172.16.', '172.17.', '172.18.', '172.19.',
                                  '172.20.', '172.21.', '172.22.', '172.23.', '172.24.',
                                  '172.25.', '172.26.', '172.27.', '172.28.', '172.29.',
                                  '172.30.', '172.31.', '192.168.', '127.')):
                return ip
        return forwarded_ips[0].strip()
    return request.remote_addr


# ----- IP 限流 ----- #

def check_ip_rate_limit(ip, action, max_attempts=5, block_time=3600):
    redis_client = current_app.config['SESSION_REDIS']
    block_key = f'ip_block:{action}:{ip}'
    attempt_key = f'ip_attempt:{action}:{ip}'

    block_until = redis_client.get(block_key)
    if block_until:
        remaining_time = int(float(block_until) - time.time())
        if remaining_time > 0:
            return True, remaining_time
        else:
            redis_client.delete(block_key)
            redis_client.delete(attempt_key)
    return False, 0


def record_ip_attempt(ip, action, max_attempts=5, block_time=3600):
    redis_client = current_app.config['SESSION_REDIS']
    attempt_key = f'ip_attempt:{action}:{ip}'
    block_key = f'ip_block:{action}:{ip}'

    attempts = redis_client.incr(attempt_key)
    if attempts == 1:
        redis_client.expire(attempt_key, block_time)
    if attempts >= max_attempts:
        block_until = time.time() + block_time
        redis_client.setex(block_key, block_time, str(block_until))
        redis_client.delete(attempt_key)
        return True, attempts
    return False, attempts


def clear_ip_attempts(ip, action):
    redis_client = current_app.config['SESSION_REDIS']
    attempt_key = f'ip_attempt:{action}:{ip}'
    redis_client.delete(attempt_key)


# ----- 邮件限流与滥用检测 ----- #

def check_daily_email_limit(ip):
    redis_client = current_app.config['SESSION_REDIS']
    MAX_DAILY_EMAILS = 10
    today = datetime.datetime.now().strftime('%Y%m%d')
    daily_key = f'daily_email:{ip}:{today}'

    count = redis_client.get(daily_key)
    if count:
        count = int(count)
        if count >= MAX_DAILY_EMAILS:
            return True, count, MAX_DAILY_EMAILS
    return False, int(count) if count else 0, MAX_DAILY_EMAILS


def record_email_sent(ip, email):
    redis_client = current_app.config['SESSION_REDIS']
    today = datetime.datetime.now().strftime('%Y%m%d')
    daily_key = f'daily_email:{ip}:{today}'
    count = redis_client.incr(daily_key)
    if count == 1:
        now = datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        midnight = datetime.datetime.combine(tomorrow.date(), datetime.time.min)
        seconds_until_midnight = int((midnight - now).total_seconds())
        redis_client.expire(daily_key, seconds_until_midnight + 3600)
    unverified_key = f'unverified_emails:{ip}:{today}'
    redis_client.sadd(unverified_key, email)
    redis_client.expire(unverified_key, 86400)
    print(f"[INFO] IP {ip} 今日已发送 {count} 封邮件")


def clear_unverified_email(ip, email):
    redis_client = current_app.config['SESSION_REDIS']
    today = datetime.datetime.now().strftime('%Y%m%d')
    unverified_key = f'unverified_emails:{ip}:{today}'
    redis_client.srem(unverified_key, email)


def check_abuse_pattern(ip):
    redis_client = current_app.config['SESSION_REDIS']
    today = datetime.datetime.now().strftime('%Y%m%d')
    unverified_key = f'unverified_emails:{ip}:{today}'
    unverified_count = redis_client.scard(unverified_key)
    if unverified_count >= 5:
        print(f"[SECURITY] 检测到可疑行为: IP {ip} 有 {unverified_count} 封未验证邮件")
        return True, unverified_count
    return False, unverified_count
