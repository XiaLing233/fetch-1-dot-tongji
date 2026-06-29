# Flask 后端 — 应用工厂

import configparser
import datetime
import os

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_session import Session
from utils.redis_client import get_redis

# ----- 配置 ----- #

PRODUCTION = os.getenv('PRODUCTION', 'true').lower() == 'true'

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini', encoding='utf-8')

SECRET_KEY = CONFIG['JWT']['secret_key']
SESSION_SECRET_KEY = CONFIG['Session']['secret_key']

ATTACHMENT_PATH = CONFIG['Storage']['attachment_path']
IMG_PATH = CONFIG['Storage']['img_path']


def create_app():
    app = Flask(__name__)

    # ----- JWT ----- #
    app.config['JWT_SECRET_KEY'] = SECRET_KEY
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_ACCESS_COOKIE_NAME'] = 'xl_token'
    if PRODUCTION:
        app.config['JWT_COOKIE_SECURE'] = True
        app.config['JWT_COOKIE_SAMESITE'] = 'Strict'
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)
    else:
        app.config['JWT_COOKIE_SECURE'] = False
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(seconds=10)

    JWTManager(app)

    # ----- Session (Redis) ----- #
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SECRET_KEY'] = SESSION_SECRET_KEY
    app.config['SESSION_REDIS'] = get_redis()
    if PRODUCTION:
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
        app.config['SESSION_COOKIE_NAME'] = '__Secure-xl_session'

    Session(app)

    # 把路径存入 app.config 供蓝图使用
    app.config['ATTACHMENT_PATH'] = ATTACHMENT_PATH
    app.config['IMG_PATH'] = IMG_PATH

    # ----- 注册蓝图 ----- #
    from routes.public import public_bp
    from routes.auth import auth_bp
    from routes.notices import notices_bp
    from routes.users import users_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(notices_bp)
    app.register_blueprint(users_bp)

    return app


# ----- 入口 ----- #

if __name__ == '__main__':
    application = create_app()
    application.run(debug=not PRODUCTION, port=8000)
else:
    # gunicorn 入口: gunicorn app:application
    application = create_app()
