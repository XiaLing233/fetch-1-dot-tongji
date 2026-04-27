# Flask 后端

from flask import Flask, request, jsonify, session, redirect
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, set_access_cookies, unset_access_cookies, get_jwt_identity
from flask_session import Session
from packages import tjSql, myDecrypt

import configparser
import datetime
import redis
import os
import urllib.parse
import string
import base64
import logging
import requests
import secrets
import random

# COS
from packages.upload_to_cos import CosUpload

MYCOS = CosUpload()

# ----- 配置 ----- #

PRODUCTION = False # 是否为生产环境

# 读取配置文件

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini', encoding='utf-8')

SECRET_KEY = CONFIG['JWT']['secret_key']

ATTACHMENT_PATH = CONFIG['Storage']['attachment_path']
IMG_PATH = CONFIG['Storage']['img_path'] # 背景图片路径

# OIDC 配置
OIDC_IDP_AUTHORIZE_URL = CONFIG['OIDC']['idp_authorize_url']
OIDC_IDP_TOKEN_URL = CONFIG['OIDC']['idp_token_url']
OIDC_IDP_USERINFO_URL = CONFIG['OIDC']['idp_userinfo_url']
OIDC_CLIENT_ID = CONFIG['OIDC']['client_id']
OIDC_CLIENT_SECRET = CONFIG['OIDC']['client_secret']
if PRODUCTION:
    OIDC_REDIRECT_URI = 'https://1.xialing.icu/api/sso/callback'
    FRONTEND_URL = 'https://1.xialing.icu'
else:
    OIDC_REDIRECT_URI = 'http://localhost:5173/api/sso/callback'
    FRONTEND_URL = 'http://localhost:5173'

# app 初始化

app = Flask(__name__)

# 设置 JWT
app.config['JWT_SECRET_KEY'] = SECRET_KEY
app.config['JWT_TOKEN_LOCATION'] = ['cookies'] # token 位置
app.config['JWT_ACCESS_COOKIE_NAME'] = 'xl_token' # token 名称
if PRODUCTION:
    app.config['JWT_COOKIE_SECURE'] = True
    app.config['JWT_COOKIE_SAMESITE'] = 'Strict'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1) # token 过期时间

else:
    app.config['JWT_COOKIE_SECURE'] = False
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1) # token 过期时间

jwt = JWTManager(app)

SESSION_SECRET_KEY = CONFIG['Session']['secret_key']

# 设置 session
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SECRET_KEY'] = SESSION_SECRET_KEY
app.config['SESSION_REDIS'] = redis.Redis(host='localhost', port=6379, db=0)
if PRODUCTION:
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    app.config['SESSION_COOKIE_NAME'] = '__Secure-xl_session'

Session(app)


# ----- 功能函数 ----- #

# 获取 IP 地址
def get_client_ip():
    """
    安全地获取客户端真实IP地址
    优先级：CF-Connecting-IP > X-Real-IP > X-Forwarded-For(最后一个) > remote_addr
    """
    # 1. Cloudflare 特定头部（最可信，无法伪造）
    if 'CF-Connecting-IP' in request.headers:
        return request.headers.get('CF-Connecting-IP')

    # 2. X-Real-IP（某些代理使用）
    if 'X-Real-IP' in request.headers:
        return request.headers.get('X-Real-IP')

    # 3. X-Forwarded-For（取最右边的IP，即最后一个代理添加的）
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

    # 4. 直接连接的IP（无代理）
    return request.remote_addr


# ----- API ----- #

# 获取背景图片
'''
> 返回

{
    "code": 200,
    "msg": "成功",
    "data": "base64编码的图片"
}
'''
@app.route('/api/getBackgroundImg', methods=['GET'])
def getBackgroundImg():
    # 获取文件夹中图片的数量
    img_num = len([name for name in os.listdir(IMG_PATH) if os.path.isfile(os.path.join(IMG_PATH, name))])

    # 根据当前的日期，选择图片
    current_day = datetime.datetime.now().day

    img_index = current_day % img_num + 1 # 文件命名风格 tongji_%d.jpg

    # 读取图片
    with open(f'{IMG_PATH}/tongji_{img_index}.jpg', 'rb') as f:
        img = f.read()

    # base64 编码
    img = base64.b64encode(img).decode('utf-8')

    print("路径是：", f'{IMG_PATH}/tongji_{img_index}.jpg')
    return jsonify({
        'code': 200,
        'msg': '成功',
        'data': img
    }), 200


# ----- SSO OIDC 登录 ----- #

@app.route('/api/sso/login', methods=['GET'])
def sso_login():
    '''
    发起 OIDC 授权请求，重定向到 IdP 登录页
    '''
    # 生成随机 state 防止 CSRF
    state = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    session['oidc_state'] = state

    # 构建授权 URL
    params = {
        'client_id': OIDC_CLIENT_ID,
        'redirect_uri': OIDC_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid profile email',
        'state': state,
    }
    authorize_url = OIDC_IDP_AUTHORIZE_URL + '?' + urllib.parse.urlencode(params)

    return redirect(authorize_url)


@app.route('/api/sso/callback', methods=['GET'])
def sso_callback():
    '''
    IdP 回调处理：用 code 换 token，再换取用户信息，最后登录本地系统
    '''
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    def redirect_home(error_msg=None):
        if error_msg:
            return redirect(f'{FRONTEND_URL}/?error={urllib.parse.quote(error_msg)}')
        return redirect(f'{FRONTEND_URL}/')

    if error:
        return redirect_home(f'IdP 返回错误: {error}')

    if not code or not state:
        return redirect_home('缺少必要参数')

    # 验证 state 防止 CSRF
    expected_state = session.get('oidc_state')
    if not expected_state or expected_state != state:
        return redirect_home('State 校验失败，请重新登录')

    # 清除 session 中的 state
    session.pop('oidc_state', None)

    # 用 code 换取 token
    token_payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': OIDC_CLIENT_ID,
        'client_secret': OIDC_CLIENT_SECRET,
        'redirect_uri': OIDC_REDIRECT_URI,
    }

    try:
        token_resp = requests.post(OIDC_IDP_TOKEN_URL, data=token_payload, timeout=10)
        token_data = token_resp.json()
    except Exception as e:
        print(f"[ERROR] Token 请求失败: {e}")
        return redirect_home('无法从 IdP 获取 Token')

    if 'access_token' not in token_data:
        print(f"[ERROR] IdP 返回错误: {token_data}")
        return redirect_home('Token 换取失败')

    access_token = token_data['access_token']

    # 获取用户信息
    try:
        userinfo_resp = requests.get(
            OIDC_IDP_USERINFO_URL,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        userinfo = userinfo_resp.json()
    except Exception as e:
        print(f"[ERROR] UserInfo 请求失败: {e}")
        return redirect_home('无法从 IdP 获取用户信息')

    email = userinfo.get('email')
    if not email:
        return redirect_home('IdP 未返回邮箱信息')

    # 检查本地用户是否存在，不存在则自动创建（JIT provisioning）
    if not tjSql.sqlUserExist(email):
        nickname = email.split('@')[0]
        name = userinfo.get('name', nickname)
        # 本地密码已无用，使用随机占位值
        dummy_password = secrets.token_hex(32)
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        tjSql.sqlInsertUser(name, email, dummy_password, current_time)
        print(f"[INFO] 自动创建本地用户: {email}")

    # 登录成功，记录日志
    tjSql.sqlUpdateLoginLog(email, get_client_ip(), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 签发本地 JWT 并设置 cookie，然后重定向回前端
    access_token_local = create_access_token(identity=email)
    response = redirect_home()
    set_access_cookies(response, access_token_local)
    return response


# @@@@@@@@@@@@@WARNING@@@@@@@@@@@@ #
# @@@@@@@@以下需要验证 token@@@@@@@ #
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ #

# 获取通知列表
'''
> 返回

{
    "code": 200,
    "msg": "成功",
    "data": [
        {
        "id": 2204,
        "title": "关于2024-2025学年第二学期本科生、研究生及继续教育（本科）教材选用情况的公示",
        "startTime": "2025-01-15 00:00:00.0",
        "endTime": "2025-01-22 00:00:00.0",
        "invalidTopTime": null,
        "createId": "12345",
        "createUser": "夏凌",
        "createTime": "2025-01-15 17:26:41.0",
        "publishTime": "2025-01-16 15:11:50.0",
        },
        {
            // ...
        },
        {
            // ...
        }
    ]
}
'''
@app.route('/api/findMyCommonMsgPublish', methods=['GET'])
# @jwt_required()
def findMyCommonMsgPublish():
    # 查询通知
    data = tjSql.sqlFindMyCommonMsgPublish()

    return jsonify({
        'code': 200,
        'msg': '成功',
        'data': data
    }), 200


# 获取通知详情
'''
> 传入：

{
    "id": 2204
}

> 返回

{
    "code": 200,
    "msg": "成功",
    "data": {
        "title": "关于2024-2025学年第二学期本科生、研究生及继续教育（本科）教材选用情况的公示",
        "content": "<p>test</p>",
        "attachments": [
            {
                "fileName": "xxx",
                "fileType": "文档 | 表格 | 演示文稿 | 压缩包 | 其他"
            },
            {
                // ,,,
            },
        ]
        }
}
'''
@app.route('/api/findMyCommonMsgPublishById', methods=['POST'])
@jwt_required()
def findMyCommonMsgPublishById():
    # 获取参数
    id = request.json.get('id')

    # 查询通知
    data = tjSql.sqlFindMyCommonMsgPublishById(id)

    return jsonify({
        'code': 200,
        'msg': '成功',
        'data': data
    }), 200


# 文件下载
'''
> 传入：

{
    "fileLocation": "URI编码(base64编码(AES加密(文件名)))"
}

> 返回：

`二进制文件`
'''
@app.route('/api/downloadAttachmentByFileName', methods=['POST'])
@jwt_required()
def downloadAttachmentByFileName():
    # 获取参数
    fileLocation = request.json.get('fileLocation')

    print("文件位置：", fileLocation)

    # 解密文件名
    filePath = myDecrypt.decryptFilePath(fileLocation)

    print("文件路径：", filePath)

    return jsonify({
        "code": 200,
        "location": MYCOS.generate_temporary_url(f"{ATTACHMENT_PATH}/{filePath}")
    })

# 获取用户信息
@app.route('/api/getUserInfo', methods=['POST'])
@jwt_required()
def getUserInfo():
    xl_email = get_jwt_identity()
    print("xl_email: ", xl_email)

    # 查询用户信息
    data = tjSql.sqlGetUserInfo(xl_email)
    # 查询登录信息
    data_login = tjSql.sqlGetLoginLog(xl_email)

    print(data)

    # 转换为键值对
    data = {
        'xl_nickname': data[0],
        'xl_email': data[1],
        'xl_created_at': data[2].strftime('%Y年%m月%d日 %H:%M:%S'),
        'xl_receive_noti': bool(data[3]),
        'xl_login_log': data_login
    }

    return jsonify({
        'code': 200,
        'msg': '成功',
        'data': data
    }), 200


# 更新获取提醒的设置
@app.route('/api/toggleReceiveNoti', methods=['POST'])
@jwt_required()
def toggleReceiveNoti():
    payload = request.get_json(silent=True) or {}
    xl_email = get_jwt_identity()
    expect_option = payload.get('expect_option')
    if expect_option is None:
        return jsonify({
            'code': 400,
            'msg': '缺少参数'
        }), 400

    tjSql.sqltoggleReceiveNoti(xl_email, expect_option)

    return jsonify({
        'code': 200,
        'msg': '成功'
    }), 200

# 退出登录
@app.route('/api/logout', methods=['GET'])
@jwt_required()
def logout():
    # 清除本地 cookie，返回 URL 在 JSON 中，由前端处理重定向
    idp_base = 'https://iam.xialing.icu' if PRODUCTION else 'http://localhost:5174'
    return_url = FRONTEND_URL + '/'
    idp_logout_url = idp_base + '/api/logout?return_url=' + urllib.parse.quote(return_url, safe='')

    # 清除本地 JWT cookie
    response = jsonify({
        'code': 200,
        'msg': '成功',
        'idp_logout_url': idp_logout_url
    })

    unset_access_cookies(response)

    return response, 200

# 测试凭证是否过期，一个简单的 GET 请求
@app.route('/api/checkToken', methods=['GET'])
@jwt_required()
def checkToken():
    return jsonify({
        'code': 200,
        'msg': '成功'
    }), 200
