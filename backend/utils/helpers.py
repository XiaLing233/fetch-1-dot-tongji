"""共享辅助函数：限流、邮件发送、认证、IP 获取等。"""

import datetime as dt

import pytz
from argon2 import PasswordHasher
from flask import session, jsonify
from flask_jwt_extended import create_access_token, set_access_cookies

from utils.redis_client import get_redis
from utils.response import ok, err

from utils import crypto
from utils.email import enqueue_email

import re
import time
import random
import datetime

from flask import request, session


# ----- 工具函数 ----- #

def triedTooManyTimes():
    return session.get('tried_times', 0) >= 5


def checkEmailFormat(email):
    if not email or not isinstance(email, str):
        return False
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
    redis_client = get_redis()
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
    redis_client = get_redis()
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
    redis_client = get_redis()
    attempt_key = f'ip_attempt:{action}:{ip}'
    redis_client.delete(attempt_key)


# ----- 邮件限流与滥用检测 ----- #

def check_daily_email_limit(ip):
    redis_client = get_redis()
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
    redis_client = get_redis()
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
    redis_client = get_redis()
    today = datetime.datetime.now().strftime('%Y%m%d')
    unverified_key = f'unverified_emails:{ip}:{today}'
    redis_client.srem(unverified_key, email)


def check_abuse_pattern(ip):
    redis_client = get_redis()
    today = datetime.datetime.now().strftime('%Y%m%d')
    unverified_key = f'unverified_emails:{ip}:{today}'
    unverified_count = redis_client.scard(unverified_key)
    if unverified_count >= 5:
        print(f"[SECURITY] 检测到可疑行为: IP {ip} 有 {unverified_count} 封未验证邮件")
        return True, unverified_count
    return False, unverified_count


# ----- 邮件发送 ----- #

def send_email(to, subject, body):
    """入队邮件任务到 Redis 队列，由消费者异步发送。"""
    enqueue_email(to, subject, body)


def send_email_verification(recEmail, token):
    send_email(recEmail, '邮箱验证', f'''亲爱的用户：

您好！感谢您注册我们的服务。

您的验证码是：{token}

请在10分钟内完成验证。出于安全考虑，请不要将验证码泄露给他人。

如果这不是您的操作，请忽略此邮件。

此致
1.xialing.icu
''')


def send_email_recovery(recEmail, token):
    send_email(recEmail, '找回密码', f'''亲爱的用户：

您好！您正在尝试找回密码。

您的验证码是：{token}

请在10分钟内完成验证。出于安全考虑，请不要将验证码泄露给他人。

如果这不是您的操作，请忽略此邮件。

此致
1.xialing.icu
''')


# ----- 认证公共逻辑 ----- #

def decrypt_password(encrypted_password):
    """RSA 解密密码。"""
    return crypto.decryptPassword(encrypted_password)


def hash_password(password):
    """Argon2 哈希。"""
    return PasswordHasher().hash(password)


def verify_password(hashed, plain):
    """验证 Argon2 密码，失败抛出异常。"""
    return PasswordHasher().verify(hashed, plain)


def validate_verification_flow(xl_email, xl_veri_code):
    """
    register / recovery 公共验证流程。
    返回 None 表示通过，否则返回 (error_response, status_code)。
    """
    if triedTooManyTimes():
        return err(429, '错误次数过多，请稍后再试')

    if not checkEmailFormat(xl_email):
        return err(400, '邮箱格式错误，只接受@tongji.edu.cn的邮箱')

    if session.get('email') != xl_email:
        return err(400, '邮箱与发送验证码时不一致')

    if time.time() - session.get('send_time', 0) > 600:
        return err(400, '验证码过期，请重新发送')

    if session.get('verification_code') != xl_veri_code:
        session['tried_times'] = session.get('tried_times', 0) + 1
        return err(400, f'验证码错误，您还有{5 - session.get("tried_times")}次机会')

    return None


def issue_jwt_cookie(xl_email, success_msg, status_code=200):
    """签发 JWT 并打包为带 cookie 的 response。"""
    access_token = create_access_token(identity=xl_email)
    response = jsonify({'code': status_code, 'msg': success_msg})
    set_access_cookies(response, access_token)
    return response, status_code


def record_login(xl_email, ip):
    """记录登录日志（北京时区）。"""
    from db import tjSql
    tz = pytz.timezone('Asia/Shanghai')
    now = dt.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    tjSql.sqlUpdateLoginLog(xl_email, ip, now)


def clear_auth_session():
    """清除验证码相关 session。"""
    for key in ('verification_code', 'email', 'send_time', 'tried_times'):
        session.pop(key, None)
