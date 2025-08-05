# Flask 后端

from flask import Flask, request, jsonify, session
# from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, set_access_cookies, unset_access_cookies
from flask_mail import Mail, Message
from flask_session import Session
from packages import tjSql, myDecrypt

import configparser
from argon2 import PasswordHasher
import random # 生成随机数
import re # 正则表达式
import time # 时间
import pytz # 时区
import datetime # 时间
import redis # redis
import os # 文件操作

import base64 # base64 编码

import logging

# COS
from packages.upload_to_cos import CosUpload

MYCOS = CosUpload()

# 不需要链接数据库，因为由 tjSql 完成

# ----- 配置 ----- #

PRODUCTION = True # 是否为生产环境

# 读取配置文件

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini', encoding='utf-8')

SECRET_KEY = CONFIG['JWT']['secret_key']

SMTP_SERVER = CONFIG['Email']['smtp_server']
SMTP_PORT = CONFIG['Email']['smtp_port']
SMTP_USERNAME = CONFIG['Email']['smtp_username']
SMTP_PASSWORD = CONFIG['Email']['smtp_password']

ATTACHMENT_PATH = CONFIG['Storage']['attachment_path']
IMG_PATH = CONFIG['Storage']['img_path'] # 背景图片路径

# app 初始化

app = Flask(__name__)

# CORS(app, supports_credentials=True) # 支持跨域

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
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(seconds=10) # token 过期时间

jwt = JWTManager(app)

# 设置邮件
app.config['MAIL_SERVER'] = SMTP_SERVER
app.config['MAIL_PORT'] = SMTP_PORT
app.config['MAIL_USERNAME'] = SMTP_USERNAME
app.config['MAIL_PASSWORD'] = SMTP_PASSWORD
app.config['MAIL_USE_SSL'] = True

SMTP_NICKNAME = "琪露诺bot"

mail = Mail(app)

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

def triedTooManyTimes():
    return session.get('tried_times', 0) >= 5

# 发送注册邮件
def sendEmailVerification(recEmail, token):
    # 创建邮件内容
    msg = Message(
        '邮箱验证', 
        sender=f'{SMTP_NICKNAME} <{SMTP_USERNAME}>',
        recipients=[recEmail]
        )
    msg.body = f'''亲爱的用户：

    您好！感谢您注册我们的服务。
    
    您的验证码是：{token}
    
    请在10分钟内完成验证。出于安全考虑，请不要将验证码泄露给他人。
    
    如果这不是您的操作，请忽略此邮件。
        
    此致
    xialing.icu
    '''
    
    # 发送邮件
    try:
        mail.send(msg)
        print("邮件发送成功")
    except Exception as e:
        print("邮件发送失败：", e)

# 发送找回密码邮件
def sendEmailFindPassword(recEmail, token):
    # 创建邮件内容
    msg = Message(
        '找回密码', 
        sender=f'{SMTP_NICKNAME} <{SMTP_USERNAME}>',
        recipients=[recEmail]
        )
    msg.body = f'''亲爱的用户：

    您好！您正在尝试找回密码。
    
    您的验证码是：{token}
    
    请在10分钟内完成验证。出于安全考虑，请不要将验证码泄露给他人。
    
    如果这不是您的操作，请忽略此邮件。
    
    此致
    xialing.icu
    '''
    
    # 发送邮件
    try:
        mail.send(msg)
        print("邮件发送成功")
    except Exception as e:
        print("邮件发送失败：", e)

# 检查邮箱格式
def checkEmailFormat(email):
    if re.match(r'^[a-zA-Z0-9._-]+@tongji\.edu\.cn$', email):
        return True
    else:
        return False

# 生成验证码，6位数字
def generateVerificationCode():
    return str(random.randint(100000, 999999))

# 获取 IP 地址
def get_client_ip():
    # 首先检查是否有 X-Forwarded-For 头部
    if 'X-Forwarded-For' in request.headers:
        # 获取第一个 IP 地址（有可能是代理链中的第一个）
        return request.headers.getlist('X-Forwarded-For')[0].split(',')[0] # 返回第一个 IP 地址，因为有 cloudflare 的代理，所以可能有多个 IP 地址
    # 如果没有，使用 request.remote_addr 获取客户端的 IP 地址
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


# 验证码验证接口
'''
> 传入：

{
    "xl_email": "admin@tongji.edu.cn",
}


> 返回

{
    "code": 200,
    "msg": "成功",
}
'''
@app.route('/api/sendVerificationEmail', methods=['POST'])
def sendVerificationEmail():
    # 获取参数
    xl_email = request.json.get('xl_email')

    # 检查邮箱格式
    if not checkEmailFormat(xl_email):
        return jsonify({
            'code': 400,
            'msg': '邮箱格式错误，只接受@tongji.edu.cn的邮箱'
        }), 400

    # 检查用户名是否存在
    if tjSql.sqlUserExist(xl_email):
        return jsonify({
            'code': 400,
            'msg': '用户已注册，请登录'
        }), 400
    
    # 检查发送频率限制
    current_time = time.time()
    last_send_time = session.get('send_time', 0)
    last_email = session.get('email', '')

     # 如果是同一个邮箱且未超过5分钟，则拒绝请求
    if last_email == xl_email and (current_time - last_send_time) < 300:  # 300秒 = 5分钟
        return jsonify({
            'code': 429,
            'msg': '已经发送过验证码，请及时查收，请格外留意垃圾邮件(邮箱地址正确了吗？)'
        }), 429

    # 生成验证码
    token = generateVerificationCode()

    # redis 中保存验证码
    session['verification_code'] = token
    session['email'] = xl_email
    session['send_time'] = time.time()
    session['tried_times'] = 0

    # 发送邮件
    sendEmailVerification(xl_email, token)

    return jsonify({
        'code': 200,
        'msg': '发送成功'
    }), 200


# 找回密码邮件发送
'''
> 传入：

{
    "xl_email": "admin@tongji.edu.cn",
}


> 返回

{
    "code": 200,
    "msg": "成功",
}
'''
@app.route('/api/sendRecoveryEmail', methods=['POST'])
def sendRecoveryEmail():
    # 获取参数
    xl_email = request.json.get('xl_email')

    # 检查邮箱格式
    if not checkEmailFormat(xl_email):
        return jsonify({
            'code': 400,
            'msg': '邮箱格式错误，只接受@tongji.edu.cn的邮箱'
        }), 400

    # 检查用户是否存在
    if not tjSql.sqlUserExist(xl_email):
        return jsonify({
            'code': 400,
            'msg': '用户不存在，请移步注册页面'
        }), 400

    # 检查发送频率限制
    current_time = time.time()
    last_send_time = session.get('send_time', 0)
    last_email = session.get('email', '')

     # 如果是同一个邮箱且未超过5分钟，则拒绝请求
    if last_email == xl_email and (current_time - last_send_time) < 300:  # 300秒 = 5分钟
        return jsonify({
            'code': 429,
            'msg': '已经发送过验证码，请及时查收，请格外留意垃圾邮件(邮箱地址正确了吗？)'
        }), 429
    
    # 生成验证码
    token = generateVerificationCode()

    # session 中保存验证码
    session['verification_code'] = token
    session['email'] = xl_email
    session['send_time'] = time.time() # 发送时间
    session['tried_times'] = 0

    # 发送邮件
    sendEmailFindPassword(xl_email, token)

    return jsonify({
        'code': 200,
        'msg': '发送成功'
    }), 200



# 注册
'''
> 传入：

{
    "xl_email": "admin@tongji.edu.cn",
    "xl_password": "RSA加密后的密码",
    "xl_veri_code": "233333"
}

> 返回

{
    "code": 200,
    "msg": "成功",
}
'''
@app.route('/api/register', methods=['POST'])
def register():
    if triedTooManyTimes():
        return jsonify({
            'code': 429,
            'msg': '错误次数过多，请稍后再试'
        }), 429

    # 获取参数
    xl_email = request.json.get('xl_email')
    xl_password = request.json.get('xl_password')
    xl_veri_code = request.json.get('xl_veri_code')

    # 检查邮箱格式
    if not checkEmailFormat(xl_email):
        return jsonify({
            'code': 400,
            'msg': '邮箱格式错误，只接受@tongji.edu.cn的邮箱'
        }), 400

    # 检查用户名是否存在
    if tjSql.sqlUserExist(xl_email):
        return jsonify({
            'code': 400,
            'msg': '用户已注册，请登录'
        }), 400

    # 检查验证码是否过期
    if time.time() - session.get('send_time') > 600:
        return jsonify({
            'code': 400,
            'msg': '验证码过期，请重新发送'
        }), 400

    # 检查验证码
    if session.get('verification_code') != xl_veri_code:
        session['tried_times'] += 1

        return jsonify({
            'code': 400,
            'msg': f'验证码错误，您还有{5 - session.get("tried_times")}次机会'
        }), 400

    # 解密密码
    xl_password = myDecrypt.decryptPassword(xl_password)

    hashed_password = PasswordHasher().hash(xl_password)

    # 把用户信息写入数据库
    # 顺序：@前的部分作为用户名; 邮箱; 密码; 当前时间
    nickname = xl_email.split('@')[0]
    tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    tjSql.sqlInsertUser(nickname, xl_email, hashed_password, current_time)

    # 登录日志
    tjSql.sqlUpdateLoginLog(xl_email, get_client_ip(), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 返回 token
    access_token = create_access_token(identity=xl_email)

    response = jsonify({
        'code': 200,
        'msg': '注册成功',
    })

    set_access_cookies(response, access_token)

    # 清空和验证码相关的 session
    session.pop('verification_code', None)
    session.pop('email', None)
    session.pop('send_time', None)
    session.pop('tried_times', None)

    # 设置 cookie，不在返回体中设置
    return response, 200




# 登录
'''
> 请求
{
    "xl_email": "admin@tongji.edu.cn",
    "xl_password": "RSA加密&URI编码后的密码"
}

> 返回
{
    "code": 200,
    "msg": "成功",
    "xl_token": "12345"
}
'''
@app.route('/api/login', methods=['POST'])
def login():
    # 获取参数
    print(request.json)
    xl_email = request.json.get('xl_email')
    xl_password = request.json.get('xl_password')

    # 先判断用户名是否存在
    if not tjSql.sqlUserExist(xl_email):
        return jsonify({
            'code': 400,
            # 'msg': '用户不存在'
            'msg': '用户名或密码错误'
        }), 400
    
    # 解密密码
    xl_password = myDecrypt.decryptPassword(xl_password)

    # 获取数据库中的密码
    hashed_password = tjSql.sqlGetPassword(xl_email)

    print("数据库中的密码：", hashed_password)

    # 验证密码
    try: 
        PasswordHasher().verify(hashed_password, xl_password)
    except Exception:
        return jsonify({
            'code': 400,
            # 'msg': '密码错误'
            'msg': '用户名或密码错误'
        }), 400

    # 登录日志
    tjSql.sqlUpdateLoginLog(xl_email, get_client_ip(), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 返回 token
    access_token = create_access_token(identity=xl_email)

    response = jsonify({
        'code': 200,
        'msg': '登录成功',
    })

    set_access_cookies(response, access_token)
    # 设置 cookie，不在返回体中设置
    # response.set_cookie('xl_token', access_token, httponly=True) #, samesite='Strict') # , secure=True)

    return response, 200

# 找回密码
'''
> 传入：

{
    "xl_email": "admin@tongji.edu.cn",
    "xl_password": "RSA加密后的密码"
}


> 返回

{
    "code": 200,
    "msg": "成功",
}
'''
@app.route('/api/recovery', methods=['POST'])
def recovery():
    if triedTooManyTimes():
        return jsonify({
            'code': 429,
            'msg': '错误次数过多，请稍后再试'
        }), 429

    # 获取参数
    xl_email = request.json.get('xl_email')
    xl_password = request.json.get('xl_password')
    xl_veri_code = request.json.get('xl_veri_code')

    print("session中的验证码：", session.get('verification_code'))
    print("传入的验证码：", xl_veri_code)

    # 检查邮箱格式
    if not checkEmailFormat(xl_email):
        return jsonify({
            'code': 400,
            'msg': '邮箱格式错误，只接受@tongji.edu.cn的邮箱'
        }), 400

    # 检查用户名是否存在
    if not tjSql.sqlUserExist(xl_email):
        return jsonify({
            'code': 400,
            'msg': '用户不存在'
        }), 400

    # 检查验证码是否过期
    if time.time() - session.get('send_time') > 600:
        return jsonify({
            'code': 400,
            'msg': '验证码过期，请重新发送'
        }), 400

    # 检查验证码
    if session.get('verification_code') != xl_veri_code:
        session['tried_times'] += 1

        return jsonify({
            'code': 400,
            'msg': f'验证码错误，您还有{5 - session.get("tried_times")}次机会'
        }), 400

    # 解密密码
    xl_password = myDecrypt.decryptPassword(xl_password)

    hashed_password = PasswordHasher().hash(xl_password)

    # 更新密码
    tjSql.sqlUpdatePassword(xl_email, hashed_password)

    # 登录日志
    tjSql.sqlUpdateLoginLog(xl_email, get_client_ip(), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 返回 token
    access_token = create_access_token(identity=xl_email)

    response = jsonify({
        'code': 200,
        'msg': '密码修改成功',
    })

    set_access_cookies(response, access_token)
    
    # 设置 cookie，不在返回体中设置
    # response.set_cookie('xl_token', access_token, httponly=True) #, samesite='Strict') #, secure=True)

    # 清空和验证码相关的 session
    session.pop('verification_code', None)
    session.pop('email', None)
    session.pop('send_time', None)
    session.pop('tried_times', None)

    return response, 200

# @@@@@@@@@@@@@WARNING@@@@@@@@@@@@ #
# @@@@@@@@以下需要验证 token@@@@@@@ #
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ #

# 修改密码
'''
> 传入：

{
    "xl_email": "admin@tongji.edu.cn",
    "xl_newpassword": "加密后的新密码"
}

> 返回

json
{
    "code": 200,
    "msg": "成功",
}
'''
@app.route('/api/changePassword', methods=['POST'])
@jwt_required()
def changePassword():
    # 获取参数
    xl_email = request.json.get('xl_email')
    xl_newpassword = request.json.get('xl_newpassword')

    # 解密密码
    xl_newpassword = myDecrypt.decryptPassword(xl_newpassword)

    hashed_password = PasswordHasher().hash(xl_newpassword)

    # 更新密码
    tjSql.sqlUpdatePassword(xl_email, hashed_password)

    return jsonify({
        'code': 200,
        'msg': '密码修改成功'
    }), 200

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

    # time.sleep(5) # 模拟网络延迟

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

    # 读取文件
    # with open(f'{ATTACHMENT_PATH}/{filePath}', 'rb') as f:
    #     content = f.read()

    return jsonify({
        "code": 200,
        "location": MYCOS.generate_temporary_url(f"{ATTACHMENT_PATH}/{filePath}")
    })

    # try:
    #     content = MYCOS.download_as_bytes(target_link=f"{ATTACHMENT_PATH}/{filePath}")
    #     return content
    
    # except Exception as e:
    #     print(e)
    #     return jsonify({
    #         "content": e.__str__()
    #     }), 400

# 获取用户信息
@app.route('/api/getUserInfo', methods=['POST'])
@jwt_required()
def getUserInfo():
    xl_email = request.json.get('xl_email')

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
    xl_email = request.json.get('xl_email')
    expect_option = request.json.get('expect_option')

    tjSql.sqltoggleReceiveNoti(xl_email, expect_option)

    return jsonify({
        'code': 200,
        'msg': '成功'
    }), 200

# 退出登录
@app.route('/api/logout', methods=['GET'])
@jwt_required()
def logout():
    # 清除 cookie
    response = jsonify({
        'code': 200,
        'msg': '成功'
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