"""测试 fixtures：Flask 客户端、JWT token 生成。"""

import datetime
import pytest

from app import create_app


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


_noti_counter = 0


@pytest.fixture()
def sample_notification():
    """示例通知数据（每次调用生成唯一 ID）。"""
    global _noti_counter
    _noti_counter += 1
    return {
        'id': 90000 + _noti_counter,
        'title': f'测试通知标题-{_noti_counter}',
        'content': '<p>测试内容</p>',
        'startTime': '2025-01-01 00:00:00',
        'endTime': '2099-01-01 00:00:00',
        'invalidTopTime': None,
        'createId': 'test001',
        'createUser': '测试用户',
        'createTime': '2025-01-01 00:00:00',
        'publishTime': '2025-01-01 00:00:00',
    }
