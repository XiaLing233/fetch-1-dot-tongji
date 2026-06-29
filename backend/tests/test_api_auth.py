"""认证 API 测试：注册、登录、找回密码、登出、Token 检查。"""

import os
import time
import uuid

from db import tjSql


def _uid():
    return uuid.uuid4().hex[:8]


def _encrypt_password(plaintext):
    """用 RSA 公钥加密密码，返回 URL 编码的密文。"""
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_v1_5
    import base64
    from urllib.parse import quote

    pub_path = os.getenv('RSA_PRIVATE_KEY_PATH', 'keys/web_login_pri.pem').replace('pri', 'pub')
    if not os.path.exists(pub_path):
        # Runner 环境没有密钥文件，生成临时密钥对
        key = RSA.generate(2048)
        with open(pub_path, 'wb') as f:
            f.write(key.publickey().export_key())
        priv_path = pub_path.replace('pub', 'pri')
        if not os.path.exists(priv_path):
            with open(priv_path, 'wb') as f:
                f.write(key.export_key())
    with open(pub_path, 'r') as f:
        pub_key = RSA.import_key(f.read())
    cipher = PKCS1_v1_5.new(pub_key)
    encrypted = base64.b64encode(cipher.encrypt(plaintext.encode()))
    return quote(encrypted.decode())


def _setup_session(client, email):
    """模拟发送验证码后的 session。"""
    with client.session_transaction() as sess:
        sess['captcha_code'] = 'ABCD'
        sess['captcha_time'] = time.time()
        sess['verification_code'] = '123456'
        sess['email'] = email
        sess['send_time'] = time.time()
        sess['tried_times'] = 0


class TestRegister:
    def test_register_success(self, client):
        email = f'test{_uid()}@tongji.edu.cn'
        _setup_session(client, email)
        encrypted = _encrypt_password('testpassword123')
        resp = client.post('/api/auth/register', json={
            'xl_email': email,
            'xl_password': encrypted,
            'xl_veri_code': '123456',
        })
        assert resp.status_code == 200
        assert resp.json['code'] == 200
        assert resp.json['msg'] == '注册成功'
        assert tjSql.sqlUserExist(email) is True

    def test_register_missing_email(self, client):
        resp = client.post('/api/auth/register', json={})
        assert resp.status_code == 400

    def test_register_wrong_verification_code(self, client):
        email = f'test{_uid()}@tongji.edu.cn'
        _setup_session(client, email)
        resp = client.post('/api/auth/register', json={
            'xl_email': email,
            'xl_password': 'ignored',
            'xl_veri_code': '000000',
        })
        assert resp.status_code == 400
        assert '验证码错误' in resp.json['msg']

    def test_register_email_mismatch(self, client):
        _setup_session(client, f's{_uid()}@tongji.edu.cn')
        resp = client.post('/api/auth/register', json={
            'xl_email': f'd{_uid()}@tongji.edu.cn',
            'xl_password': 'ignored',
            'xl_veri_code': '123456',
        })
        assert resp.status_code == 400
        assert '不一致' in resp.json['msg']

    def test_register_duplicate(self, client):
        email = f'dup{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'dup{_uid()}', email, 'hash', '2025-01-01 00:00:00')
        _setup_session(client, email)
        resp = client.post('/api/auth/register', json={
            'xl_email': email,
            'xl_password': 'ignored',
            'xl_veri_code': '123456',
        })
        assert resp.status_code == 400
        assert '已注册' in resp.json['msg']


class TestLogin:
    def test_login_wrong_credentials(self, client):
        resp = client.post('/api/auth/login', json={
            'xl_email': 'nouser@tongji.edu.cn',
            'xl_password': 'anything',
        })
        assert resp.status_code == 400
        assert '用户名或密码错误' in resp.json['msg']

    def test_login_missing_fields(self, client):
        resp = client.post('/api/auth/login', json={})
        assert resp.status_code in (400, 403)
        if resp.status_code == 400:
            assert '用户名或密码错误' in resp.json['msg']


class TestRecovery:
    def test_recovery_wrong_code(self, client):
        email = f'rec{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'rec{_uid()}', email, 'old_hash', '2025-01-01 00:00:00')
        _setup_session(client, email)
        resp = client.put('/api/auth/password/reset', json={
            'xl_email': email,
            'xl_password': 'ignored',
            'xl_veri_code': '000000',
        })
        assert resp.status_code == 400
        assert '验证码错误' in resp.json['msg']

    def test_recovery_user_not_exist(self, client):
        email = f'norec{_uid()}@tongji.edu.cn'
        _setup_session(client, email)
        resp = client.put('/api/auth/password/reset', json={
            'xl_email': email,
            'xl_password': 'ignored',
            'xl_veri_code': '123456',
        })
        assert resp.status_code == 400
        assert '用户不存在' in resp.json['msg']

    def test_recovery_email_mismatch(self, client):
        email = f'rec2{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'rec2{_uid()}', email, 'old_hash', '2025-01-01 00:00:00')
        _setup_session(client, f'other{_uid()}@tongji.edu.cn')
        resp = client.put('/api/auth/password/reset', json={
            'xl_email': email,
            'xl_password': 'ignored',
            'xl_veri_code': '123456',
        })
        assert resp.status_code == 400
        assert '不一致' in resp.json['msg']


class TestLogout:
    def test_logout_no_token_returns_401(self, client):
        resp = client.delete('/api/auth/session')
        assert resp.status_code == 401

    def test_logout_with_token_returns_200(self, auth_client):
        resp = auth_client.delete('/api/auth/session')
        assert resp.status_code == 200


class TestCheckToken:
    def test_check_no_token_returns_401(self, client):
        resp = client.get('/api/auth/check')
        assert resp.status_code == 401

    def test_check_valid_token_returns_200(self, auth_client):
        resp = auth_client.get('/api/auth/check')
        assert resp.status_code == 200
