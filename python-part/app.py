# Flask 后端

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
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

# 不需要链接数据库，因为由 tjSql 完成

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

CORS(app) # 允许跨域

# 设置 JWT
app.config['JWT_SECRET_KEY'] = SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1) # token 过期时间
jwt = JWTManager(app)

# 设置邮件
app.config['MAIL_SERVER'] = SMTP_SERVER
app.config['MAIL_PORT'] = SMTP_PORT
app.config['MAIL_USERNAME'] = SMTP_USERNAME
app.config['MAIL_PASSWORD'] = SMTP_PASSWORD
app.config['MAIL_USE_SSL'] = True

SMTP_NICKNAME = "琪露诺bot"

mail = Mail(app)

# 设置 session
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.Redis(host='localhost', port=6379, db=0)

Session(app)



# ----- 功能函数 ----- #



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
    mail.send(msg)

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
    mail.send(msg)

# 检查邮箱格式
def checkEmailFormat(email):
    if re.match(r'^[a-zA-Z0-9._-]+@tongji\.edu\.cn$', email):
        return True
    else:
        return False

# 生成验证码，6位数字
def generateVerificationCode():
    return random.randint(100000, 999999)


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
    })


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
    if checkEmailFormat(xl_email) == False:
        return jsonify({
            'code': 400,
            'msg': '邮箱格式错误，只接受@tongji.edu.cn的邮箱'
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
    if checkEmailFormat(xl_email) == False:
        return jsonify({
            'code': 400,
            'msg': '邮箱格式错误，只接受@tongji.edu.cn的邮箱'
        }), 400

    # 检查用户是否存在
    if tjSql.sqlUserExist(xl_email) == False:
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
    "xl_token": "12345"
}
'''
@app.route('/api/register', methods=['POST'])
def register():
    # 获取参数
    xl_email = request.json.get('xl_email')
    xl_password = request.json.get('xl_password')
    xl_veri_code = request.json.get('xl_veri_code')

    # 检查邮箱格式
    if checkEmailFormat(xl_email) == False:
        return jsonify({
            'code': 400,
            'msg': '邮箱格式错误，只接受@tongji.edu.cn的邮箱'
        })

    # 检查用户名是否存在
    if tjSql.sqlUserExist(xl_email) == True:
        return jsonify({
            'code': 400,
            'msg': '用户已存在'
        })

    # 检查验证码
    if session.get('verification_code') != xl_veri_code:
        return jsonify({
            'code': 400,
            'msg': '验证码错误'
        })

    # 检查验证码是否过期
    if time.time() - session.get('send_time') > 600:
        return jsonify({
            'code': 400,
            'msg': '验证码过期，请重新发送'
        })

    # 解密密码
    xl_password = myDecrypt.decryptPassword(xl_password)

    hashed_password = PasswordHasher().hash(xl_password)

    # 把用户信息写入数据库
    # 顺序：@前的部分作为用户名; 邮箱; 密码; 当前时间
    nickname = xl_email.split('@')[0]
    tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    tjSql.sqlInsertUser(nickname, xl_email, hashed_password, current_time)

    # 返回 token
    access_token = create_access_token(identity=xl_email)

    return jsonify({
        'code': 200,
        'msg': '注册成功',
        'xl_token': access_token
    })



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
    xl_email = request.json.get('xl_email')
    xl_password = request.json.get('xl_password')

    # 先判断用户名是否存在
    if tjSql.sqlUserExist(xl_email) == False:
        return jsonify({
            'code': 400,
            'msg': '用户不存在'
        })
    
    # 解密密码
    xl_password = myDecrypt.decryptPassword(xl_password)

    # 获取数据库中的密码
    hashed_password = tjSql.sqlGetPassword(xl_email)

    # 验证密码
    if PasswordHasher().verify(hashed_password, xl_password) == False:
        return jsonify({
            'code': 400,
            'msg': '密码错误'
        })

    # 返回 token
    access_token = create_access_token(identity=xl_email)

    response = jsonify({
        'code': 200,
        'msg': '登录成功',
    })

    # 设置 cookie，不在返回体中设置
    response.set_cookie('xl_token', access_token, httponly=True, samesite='Strict', secure=True)

    return response

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
    "xl_token": "12345"
}
'''
@app.route('/api/recovery', methods=['POST'])
def recovery():
    # 获取参数
    xl_email = request.json.get('xl_email')
    xl_password = request.json.get('xl_password')
    xl_veri_code = request.json.get('xl_veri_code')

    # 检查邮箱格式
    if checkEmailFormat(xl_email) == False:
        return jsonify({
            'code': 400,
            'msg': '邮箱格式错误，只接受@tongji.edu.cn的邮箱'
        })

    # 检查用户名是否存在
    if tjSql.sqlUserExist(xl_email) == False:
        return jsonify({
            'code': 400,
            'msg': '用户不存在'
        })

    # 检查验证码
    if session.get('verification_code') != xl_veri_code:
        return jsonify({
            'code': 400,
            'msg': '验证码错误'
        })

    # 检查验证码是否过期
    if time.time() - session.get('send_time') > 600:
        return jsonify({
            'code': 400,
            'msg': '验证码过期，请重新发送'
        })

    # 解密密码
    xl_password = myDecrypt.decryptPassword(xl_password)

    hashed_password = PasswordHasher().hash(xl_password)

    # 更新密码
    tjSql.sqlUpdatePassword(xl_email, hashed_password)

    # 返回 token
    access_token = create_access_token(identity=xl_email)

    return jsonify({
        'code': 200,
        'msg': '密码修改成功',
        'xl_token': access_token
    })

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
    })

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
@app.route('/api/findMyCommonMsgPublish', methods=['POST'])
@jwt_required()
def findMyCommonMsgPublish():
    # 查询通知
    data = tjSql.sqlFindMyCommonMsgPublish()

    return jsonify({
        'code': 200,
        'msg': '成功',
        'data': data
    })


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
    })


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

    # 解密文件名
    filePath = myDecrypt.decryptFilePath(fileLocation)

    # 读取文件
    with open(f'{ATTACHMENT_PATH}/{filePath}', 'rb') as f:
        content = f.read()

    return content