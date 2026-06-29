"""公开接口：背景图、验证码、验证邮件、找回密码邮件。"""

import os
import time
import base64
import datetime

from flask import Blueprint, request, jsonify, session, current_app

from services.captcha import generate_captcha, verify_captcha_code
from utils.helpers import (
    get_client_ip,
    check_ip_rate_limit, record_ip_attempt,
    check_daily_email_limit, record_email_sent,
    check_abuse_pattern, clear_unverified_email,
    checkEmailFormat, generateVerificationCode,
)

public_bp = Blueprint('public', __name__)


# ----- 邮件发送 ----- #

def _send_email(to, subject, body):
    from flask_mail import Message
    mail = current_app.extensions['mail']
    smtp_username = current_app.config.get('MAIL_USERNAME', '')
    SMTP_NICKNAME = "琪露诺bot"
    msg = Message(
        subject,
        sender=f'{SMTP_NICKNAME} <{smtp_username}>',
        recipients=[to],
    )
    msg.body = body
    try:
        mail.send(msg)
        print("邮件发送成功")
    except Exception as e:
        print("邮件发送失败：", e)


def send_email_verification(recEmail, token):
    _send_email(recEmail, '邮箱验证', f'''亲爱的用户：

您好！感谢您注册我们的服务。

您的验证码是：{token}

请在10分钟内完成验证。出于安全考虑，请不要将验证码泄露给他人。

如果这不是您的操作，请忽略此邮件。

此致
1.xialing.icu
''')


def send_email_recovery(recEmail, token):
    _send_email(recEmail, '找回密码', f'''亲爱的用户：

您好！您正在尝试找回密码。

您的验证码是：{token}

请在10分钟内完成验证。出于安全考虑，请不要将验证码泄露给他人。

如果这不是您的操作，请忽略此邮件。

此致
1.xialing.icu
''')


# ----- 路由 ----- #

@public_bp.route('/api/getBackgroundImg', methods=['GET'])
def getBackgroundImg():
    img_path = current_app.config['IMG_PATH']
    img_num = len([name for name in os.listdir(img_path)
                   if os.path.isfile(os.path.join(img_path, name))])
    current_day = datetime.datetime.now().day
    img_index = current_day % img_num + 1

    with open(f'{img_path}/tongji_{img_index}.jpg', 'rb') as f:
        img = f.read()

    img = base64.b64encode(img).decode('utf-8')
    print("路径是：", f'{img_path}/tongji_{img_index}.jpg')
    return jsonify({'code': 200, 'msg': '成功', 'data': img}), 200


@public_bp.route('/api/getCaptcha', methods=['GET'])
def getCaptcha():
    user_ip = get_client_ip()
    redis_client = current_app.config['SESSION_REDIS']
    captcha_rate_key = f'captcha_rate:{user_ip}'
    captcha_count = redis_client.get(captcha_rate_key)

    if captcha_count:
        captcha_count = int(captcha_count)
        if captcha_count >= 10:
            return jsonify({'code': 429, 'msg': '获取验证码过于频繁，请稍后再试'}), 429
        redis_client.incr(captcha_rate_key)
    else:
        redis_client.setex(captcha_rate_key, 60, 1)

    code, img_base64 = generate_captcha()
    session['captcha_code'] = code.upper()
    session['captcha_time'] = time.time()
    print(f"[INFO] 生成验证码: {code}, IP: {user_ip}")

    return jsonify({'code': 200, 'msg': '成功', 'data': img_base64}), 200


def _send_email_endpoint(xl_email, captcha_code, action):
    """公共逻辑：sendVerificationEmail / sendRecoveryEmail 共享。"""
    if not captcha_code:
        return jsonify({'code': 400, 'msg': '请输入验证码'}), 400

    user_ip = get_client_ip()

    is_daily_limited, daily_count, max_daily = check_daily_email_limit(user_ip)
    if is_daily_limited:
        print(f"[SECURITY] IP {user_ip} 达到每日邮件发送上限: {daily_count}/{max_daily}")
        return jsonify({'code': 403, 'msg': '操作过于频繁，请稍后再试(err: -80001)'}), 403

    is_suspicious, unverified_count = check_abuse_pattern(user_ip)
    if is_suspicious and unverified_count >= 5:
        print(f"[SECURITY] 检测到可疑行为: IP {user_ip} 有 {unverified_count} 封未验证邮件")
        return jsonify({'code': 403, 'msg': '操作过于频繁，请稍后再试(err: -80002)'}), 403

    is_blocked, remaining_time = check_ip_rate_limit(user_ip, action)
    if is_blocked:
        return jsonify({'code': 403, 'msg': f'操作过于频繁，请稍后再试(err: -80003)'}), 403

    # 验证图形验证码
    session_captcha = session.get('captcha_code')
    captcha_time = session.get('captcha_time', 0)
    if time.time() - captcha_time > 300:
        return jsonify({'code': 400, 'msg': '验证码已过期，请刷新'}), 400

    MAX_ATTEMPTS = 5
    if not verify_captcha_code(captcha_code, session_captcha):
        print(f"[SECURITY] 图形验证码验证失败, IP: {user_ip}, Email: {xl_email}")
        is_now_blocked, attempts = record_ip_attempt(user_ip, action, max_attempts=MAX_ATTEMPTS, block_time=3600)
        if is_now_blocked:
            return jsonify({'code': 403, 'msg': '操作过于频繁，请稍后再试(err: -80004)'}), 403
        return jsonify({'code': 400, 'msg': f'验证码错误，您还有 {MAX_ATTEMPTS - attempts} 次机会'}), 400

    print(f"[INFO] 图形验证码验证成功, IP: {user_ip}, Email: {xl_email}")

    if not checkEmailFormat(xl_email):
        return jsonify({'code': 400, 'msg': '邮箱格式错误，只接受@tongji.edu.cn的邮箱'}), 400

    # 使用 Redis 锁
    redis_client = current_app.config['SESSION_REDIS']
    lock_key = f'email_lock:{xl_email}'
    lock_acquired = redis_client.set(lock_key, str(time.time()), nx=True, ex=10)
    if not lock_acquired:
        return jsonify({'code': 429, 'msg': '操作过于频繁，请稍后再试(err: -80005)'}), 429

    try:
        rate_limit_key = f'email_rate_limit:{xl_email}'
        last_send_time = redis_client.get(rate_limit_key)
        if last_send_time and (time.time() - float(last_send_time)) < 300:
            return jsonify({'code': 429, 'msg': '已经发送过验证码，请及时查收，请格外留意垃圾邮件(邮箱地址正确了吗？)'}), 429

        token = generateVerificationCode()
        session['verification_code'] = token
        session['email'] = xl_email
        session['send_time'] = time.time()
        session['tried_times'] = 0
        redis_client.setex(rate_limit_key, 300, str(time.time()))
        record_email_sent(user_ip, xl_email)

        print("[DEBUG] 发送邮件！")
        if action == 'register':
            send_email_verification(xl_email, token)
        else:
            send_email_recovery(xl_email, token)

        return jsonify({'code': 200, 'msg': '发送成功'}), 200
    finally:
        redis_client.delete(lock_key)


@public_bp.route('/api/sendVerificationEmail', methods=['POST'])
def sendVerificationEmail():
    xl_email = request.json.get('xl_email')
    captcha_code = request.json.get('captcha_code')
    return _send_email_endpoint(xl_email, captcha_code, 'register')


@public_bp.route('/api/sendRecoveryEmail', methods=['POST'])
def sendRecoveryEmail():
    xl_email = request.json.get('xl_email')
    captcha_code = request.json.get('captcha_code')
    return _send_email_endpoint(xl_email, captcha_code, 'recovery')
