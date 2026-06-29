"""认证接口：注册、登录、找回密码、登出、Token 检查。"""

import datetime
import time

import pytz
from argon2 import PasswordHasher
from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import (
    create_access_token, jwt_required,
    set_access_cookies, unset_access_cookies, get_jwt_identity,
)

from db import tjSql
from utils import crypto as myDecrypt
from utils.helpers import (
    triedTooManyTimes,
    get_client_ip,
    check_ip_rate_limit, record_ip_attempt, clear_ip_attempts,
    clear_unverified_email,
    checkEmailFormat,
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/register', methods=['POST'])
def register():
    if triedTooManyTimes():
        return jsonify({'code': 429, 'msg': '错误次数过多，请稍后再试'}), 429

    xl_email = request.json.get('xl_email')
    xl_password = request.json.get('xl_password')
    xl_veri_code = request.json.get('xl_veri_code')

    if not checkEmailFormat(xl_email):
        return jsonify({'code': 400, 'msg': '邮箱格式错误，只接受@tongji.edu.cn的邮箱'}), 400

    if session.get('email') != xl_email:
        return jsonify({'code': 400, 'msg': '邮箱与发送验证码时不一致'}), 400

    if tjSql.sqlUserExist(xl_email):
        return jsonify({'code': 400, 'msg': '用户已注册，请登录'}), 400

    if time.time() - session.get('send_time', 0) > 600:
        return jsonify({'code': 400, 'msg': '验证码过期，请重新发送'}), 400

    if session.get('verification_code') != xl_veri_code:
        session['tried_times'] = session.get('tried_times', 0) + 1
        return jsonify({'code': 400, 'msg': f'验证码错误，您还有{5 - session.get("tried_times")}次机会'}), 400

    xl_password = myDecrypt.decryptPassword(xl_password)
    hashed_password = PasswordHasher().hash(xl_password)

    nickname = xl_email.split('@')[0]
    tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    tjSql.sqlInsertUser(nickname, xl_email, hashed_password, current_time)
    tjSql.sqlUpdateLoginLog(xl_email, get_client_ip(), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    user_ip = get_client_ip()
    clear_unverified_email(user_ip, xl_email)

    access_token = create_access_token(identity=xl_email)
    response = jsonify({'code': 200, 'msg': '注册成功'})
    set_access_cookies(response, access_token)

    for key in ('verification_code', 'email', 'send_time', 'tried_times'):
        session.pop(key, None)

    return response, 200


@auth_bp.route('/api/login', methods=['POST'])
def login():
    print(request.json)
    xl_email = request.json.get('xl_email')
    xl_password = request.json.get('xl_password')
    user_ip = get_client_ip()

    is_blocked, remaining_time = check_ip_rate_limit(user_ip, 'login', max_attempts=5, block_time=900)
    if is_blocked:
        minutes = remaining_time // 60
        return jsonify({'code': 403, 'msg': f'登录失败次数过多，请 {minutes} 分钟后再试'}), 403

    if not tjSql.sqlUserExist(xl_email):
        record_ip_attempt(user_ip, 'login', max_attempts=5, block_time=900)
        return jsonify({'code': 400, 'msg': '用户名或密码错误'}), 400

    xl_password = myDecrypt.decryptPassword(xl_password)
    hashed_password = tjSql.sqlGetPassword(xl_email)
    print("数据库中的密码：", hashed_password)

    try:
        PasswordHasher().verify(hashed_password, xl_password)
    except Exception:
        is_now_blocked, attempts = record_ip_attempt(user_ip, 'login', max_attempts=5, block_time=900)
        if is_now_blocked:
            return jsonify({'code': 403, 'msg': '失败次数过多，请稍后再试(err: -70001)'}), 403
        return jsonify({'code': 400, 'msg': '用户名或密码错误'}), 400

    clear_ip_attempts(user_ip, 'login')
    tjSql.sqlUpdateLoginLog(xl_email, get_client_ip(), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    access_token = create_access_token(identity=xl_email)
    response = jsonify({'code': 200, 'msg': '登录成功'})
    set_access_cookies(response, access_token)
    return response, 200


@auth_bp.route('/api/recovery', methods=['POST'])
def recovery():
    if triedTooManyTimes():
        return jsonify({'code': 429, 'msg': '错误次数过多，请稍后再试'}), 429

    xl_email = request.json.get('xl_email')
    xl_password = request.json.get('xl_password')
    xl_veri_code = request.json.get('xl_veri_code')

    print("session中的验证码：", session.get('verification_code'))
    print("传入的验证码：", xl_veri_code)

    if not checkEmailFormat(xl_email):
        return jsonify({'code': 400, 'msg': '邮箱格式错误，只接受@tongji.edu.cn的邮箱'}), 400

    if session.get('email') != xl_email:
        return jsonify({'code': 400, 'msg': '邮箱与发送验证码时不一致'}), 400

    if not tjSql.sqlUserExist(xl_email):
        return jsonify({'code': 400, 'msg': '用户不存在'}), 400

    if time.time() - session.get('send_time', 0) > 600:
        return jsonify({'code': 400, 'msg': '验证码过期，请重新发送'}), 400

    if session.get('verification_code') != xl_veri_code:
        session['tried_times'] = session.get('tried_times', 0) + 1
        return jsonify({'code': 400, 'msg': f'验证码错误，您还有{5 - session.get("tried_times")}次机会'}), 400

    xl_password = myDecrypt.decryptPassword(xl_password)
    hashed_password = PasswordHasher().hash(xl_password)
    tjSql.sqlUpdatePassword(xl_email, hashed_password)
    tjSql.sqlUpdateLoginLog(xl_email, get_client_ip(), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    user_ip = get_client_ip()
    clear_unverified_email(user_ip, xl_email)

    access_token = create_access_token(identity=xl_email)
    response = jsonify({'code': 200, 'msg': '密码修改成功'})
    set_access_cookies(response, access_token)

    for key in ('verification_code', 'email', 'send_time', 'tried_times'):
        session.pop(key, None)

    return response, 200


@auth_bp.route('/api/logout', methods=['GET'])
@jwt_required()
def logout():
    response = jsonify({'code': 200, 'msg': '成功'})
    unset_access_cookies(response)
    return response, 200


@auth_bp.route('/api/checkToken', methods=['GET'])
@jwt_required()
def checkToken():
    return jsonify({'code': 200, 'msg': '成功'}), 200
