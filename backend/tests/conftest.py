"""测试 fixtures：Flask 客户端、JWT token 生成。"""

import os
import datetime
import pytest

from app import create_app


@pytest.fixture(scope='session')
def rsa_keys(tmp_path_factory):
    """生成临时 RSA 密钥对供测试使用。"""
    from Crypto.PublicKey import RSA
    key = RSA.generate(2048)
    keys_dir = tmp_path_factory.mktemp('keys')
    pub_path = keys_dir / 'pub.pem'
    pri_path = keys_dir / 'pri.pem'
    pub_path.write_bytes(key.publickey().export_key())
    pri_path.write_bytes(key.export_key())
    os.environ['RSA_PRIVATE_KEY_PATH'] = str(pri_path)
    return str(pub_path), str(pri_path)


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

