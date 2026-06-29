"""用户接口：个人信息、通知偏好、修改密码。"""

from argon2 import PasswordHasher
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from db import tjSql
from utils import crypto as myDecrypt
from utils.response import ok, err

users_bp = Blueprint('users', __name__)


@users_bp.route('/api/changePassword', methods=['POST'])
@jwt_required()
def changePassword():
    payload = request.get_json(silent=True) or {}
    xl_email = get_jwt_identity()
    xl_newpassword = payload.get('xl_newpassword')
    if not xl_newpassword:
        return err(400, '缺少参数')

    xl_newpassword = myDecrypt.decryptPassword(xl_newpassword)
    hashed_password = PasswordHasher().hash(xl_newpassword)
    tjSql.sqlUpdatePassword(xl_email, hashed_password)

    return ok(msg='密码修改成功')


@users_bp.route('/api/getUserInfo', methods=['POST'])
@jwt_required()
def getUserInfo():
    xl_email = get_jwt_identity()
    print("xl_email: ", xl_email)

    data = tjSql.sqlGetUserInfo(xl_email)
    data_login = tjSql.sqlGetLoginLog(xl_email)
    print(data)

    data = {
        'xl_nickname': data[0],
        'xl_email': data[1],
        'xl_created_at': data[2].strftime('%Y年%m月%d日 %H:%M:%S'),
        'xl_receive_noti': bool(data[3]),
        'xl_login_log': data_login,
    }

    return ok(data, '成功')


@users_bp.route('/api/toggleReceiveNoti', methods=['POST'])
@jwt_required()
def toggleReceiveNoti():
    payload = request.get_json(silent=True) or {}
    xl_email = get_jwt_identity()
    expect_option = payload.get('expect_option')
    if expect_option is None:
        return err(400, '缺少参数')

    tjSql.sqltoggleReceiveNoti(xl_email, expect_option)
    return ok(msg='成功')
