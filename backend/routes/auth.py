"""认证接口：注册、登录、找回密码、登出、Token 检查。"""

import datetime

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, unset_access_cookies, get_jwt_identity

from db import tjSql
from utils.response import ok, err
from utils.helpers import (
    get_client_ip,
    check_ip_rate_limit, record_ip_attempt, clear_ip_attempts,
    clear_unverified_email,
    validate_verification_flow,
    decrypt_password, hash_password, verify_password,
    issue_jwt_cookie, record_login, clear_auth_session,
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    xl_email = request.json.get('xl_email')
    xl_password = request.json.get('xl_password')
    xl_veri_code = request.json.get('xl_veri_code')

    validation_error = validate_verification_flow(xl_email, xl_veri_code)
    if validation_error is not None:
        return validation_error

    if tjSql.sqlUserExist(xl_email):
        return err(400, '用户已注册，请登录')

    hashed = hash_password(decrypt_password(xl_password))
    nickname = xl_email.split('@')[0]
    tjSql.sqlInsertUser(nickname, xl_email, hashed, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    user_ip = get_client_ip()
    record_login(xl_email, user_ip)
    clear_unverified_email(user_ip, xl_email)
    clear_auth_session()

    return issue_jwt_cookie(xl_email, '注册成功')


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    xl_email = request.json.get('xl_email')
    xl_password = request.json.get('xl_password')
    user_ip = get_client_ip()

    is_blocked, remaining_time = check_ip_rate_limit(user_ip, 'login', max_attempts=5, block_time=900)
    if is_blocked:
        minutes = remaining_time // 60
        return err(403, f'登录失败次数过多，请 {minutes} 分钟后再试')

    if not tjSql.sqlUserExist(xl_email):
        record_ip_attempt(user_ip, 'login', max_attempts=5, block_time=900)
        return err(400, '用户名或密码错误')

    plain = decrypt_password(xl_password)
    hashed = tjSql.sqlGetPassword(xl_email)

    try:
        verify_password(hashed, plain)
    except Exception:
        is_now_blocked, attempts = record_ip_attempt(user_ip, 'login', max_attempts=5, block_time=900)
        if is_now_blocked:
            return err(403, '失败次数过多，请稍后再试(err: -70001)')
        return err(400, '用户名或密码错误')

    clear_ip_attempts(user_ip, 'login')
    record_login(xl_email, user_ip)
    return issue_jwt_cookie(xl_email, '登录成功')


@auth_bp.route('/api/auth/password/reset', methods=['PUT'])
def recovery():
    xl_email = request.json.get('xl_email')
    xl_password = request.json.get('xl_password')
    xl_veri_code = request.json.get('xl_veri_code')

    validation_error = validate_verification_flow(xl_email, xl_veri_code)
    if validation_error is not None:
        return validation_error

    if not tjSql.sqlUserExist(xl_email):
        return err(400, '用户不存在')

    hashed = hash_password(decrypt_password(xl_password))
    tjSql.sqlUpdatePassword(xl_email, hashed)

    user_ip = get_client_ip()
    record_login(xl_email, user_ip)
    clear_unverified_email(user_ip, xl_email)
    clear_auth_session()

    return issue_jwt_cookie(xl_email, '密码修改成功')


@auth_bp.route('/api/auth/session', methods=['DELETE'])
@jwt_required()
def logout():
    from flask import jsonify
    response = jsonify({'code': 200, 'msg': '成功'})
    unset_access_cookies(response)
    return response, 200


@auth_bp.route('/api/auth/check', methods=['GET'])
@jwt_required()
def checkToken():
    return ok(msg='成功')
