"""公开 API 测试：背景图、验证码、邮件发送。"""

import time
import pytest


class TestBackground:
    def test_get_background_success(self, client):
        resp = client.get('/api/background')
        assert resp.status_code == 200
        assert resp.json['code'] == 200
        assert resp.json['data']


class TestCaptcha:
    def test_get_captcha_success(self, client):
        resp = client.get('/api/captcha', headers={'X-Forwarded-For': '10.1.1.1'})
        assert resp.status_code == 200
        assert resp.json['code'] == 200
        assert resp.json['data']

    def test_rate_limit_after_10_requests(self, client):
        for _ in range(10):
            resp = client.get('/api/captcha', headers={'X-Forwarded-For': '10.1.1.2'})
            assert resp.status_code == 200
        resp = client.get('/api/captcha', headers={'X-Forwarded-For': '10.1.1.2'})
        assert resp.status_code == 429


class TestVerificationEmail:
    def test_missing_captcha_code(self, client):
        resp = client.post('/api/verification/email', json={
            'xl_email': 'test@tongji.edu.cn',
        })
        assert resp.status_code == 400
        assert '请输入验证码' in resp.json['msg']

    def test_invalid_email_domain(self, client):
        with client.session_transaction() as sess:
            sess['captcha_code'] = 'ABCD'
            sess['captcha_time'] = time.time()

        resp = client.post('/api/verification/email', json={
            'xl_email': 'student@gmail.com',
            'captcha_code': 'ABCD',
        })
        assert resp.status_code == 400
        assert '邮箱格式错误' in resp.json['msg']


class TestRecoveryEmail:
    def test_missing_captcha_code(self, client):
        resp = client.post('/api/recovery/email', json={
            'xl_email': 'test@tongji.edu.cn',
        })
        assert resp.status_code == 400

    def test_invalid_email_domain(self, client):
        with client.session_transaction() as sess:
            sess['captcha_code'] = 'ABCD'
            sess['captcha_time'] = time.time()

        resp = client.post('/api/recovery/email', json={
            'xl_email': 'bad@gmail.com',
            'captcha_code': 'ABCD',
        })
        assert resp.status_code == 400
        assert '邮箱格式错误' in resp.json['msg']
