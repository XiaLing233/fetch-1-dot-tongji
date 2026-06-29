"""测试 fixtures：Flask 客户端、JWT token 生成。"""

import os
import datetime
import tempfile

import pytest

# 在 import app 之前生成测试密钥（crypto.py 在 import 时读取 PRIVATE_KEY_PATH）
_KEYS_DIR = tempfile.mkdtemp(prefix='ftj_test_keys_')
_PRI_PATH = os.path.join(_KEYS_DIR, 'pri.pem')
_PUB_PATH = os.path.join(_KEYS_DIR, 'pub.pem')
if not os.path.exists(_PRI_PATH):
    from Crypto.PublicKey import RSA
    _key = RSA.generate(2048)
    with open(_PUB_PATH, 'wb') as f:
        f.write(_key.publickey().export_key())
    with open(_PRI_PATH, 'wb') as f:
        f.write(_key.export_key())
os.environ['RSA_PRIVATE_KEY_PATH'] = _PRI_PATH

from app import create_app


@pytest.fixture(scope='session')
def rsa_keys():
    return _PUB_PATH, _PRI_PATH


@pytest.fixture(scope='session')
def app():
    """创建测试 Flask 应用（session 级别，复用）。"""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture()
def client(app):
    """Flask 测试客户端。"""
    return app.test_client()


@pytest.fixture()
def auth_client(client):
    """返回已登录的 Flask 测试客户端（JWT cookie 已设置）。"""
    from db import tjSql

    email = 'testuser@tongji.edu.cn'
    with client.application.app_context():
        if not tjSql.sqlUserExist(email):
            tjSql.sqlInsertUser(
                'testuser', email,
                '$argon2id$v=19$m=65536,t=3,p=4$dummy_hash_for_test',
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            )
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=email)

    client.set_cookie(key='xl_token', value=token, domain='localhost')
    return client

