# Flask 后端

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
from flask_mail import Mail, Message
from packages import tjSql, myDecrypt
import configparser
from argon2 import PasswordHasher

# 不需要链接数据库，因为由 tjSql 完成

# 读取配置文件

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini', encoding='utf-8')

SECRET_KEY = CONFIG['JWT']['secret_key']

SMTP_SERVER = CONFIG['Email']['smtp_server']
SMTP_PORT = int(CONFIG['Email']['smtp_port'])
SMTP_USERNAME = CONFIG['Email']['smtp_username']
SMTP_PASSWORD = CONFIG['Email']['smtp_password']


# app 初始化

app = Flask(__name__)

CORS(app) # 允许跨域

# 设置 JWT
app.config['JWT_SECRET_KEY'] = SECRET_KEY
jwt = JWTManager(app)

# 设置邮件
app.config['MAIL_SERVER'] = SMTP_SERVER
app.config['MAIL_PORT'] = SMTP_PORT
app.config['MAIL_USERNAME'] = SMTP_USERNAME
app.config['MAIL_PASSWORD'] = SMTP_PASSWORD
app.config['MAIL_USE_SSL'] = True

SMTP_NICKNAME = "琪露诺bot"

mail = Mail(app)


# 发送邮件
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

# 测试邮箱发送
sendEmailVerification('summerice233@qq.com', '123456')

# 注册


# 登录
'''
> 请求
{
    "xl_username": "admin@tongji.edu.cn",
    "xl_password": "RSA加密&URI编码后的密码"
}
```

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
    xl_username = request.json.get('xl_username')
    xl_password = request.json.get('xl_password')

    # 先判断用户名是否存在
    if sqlUserExist(xl_username) == False:
        return jsonify({
            'code': 400,
            'msg': '用户不存在'
        })
    
    # 解密密码
    xl_password = myDecrypt.decryptPassword(xl_password)

    # 获取数据库中的密码