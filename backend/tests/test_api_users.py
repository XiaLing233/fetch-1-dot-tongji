"""用户 API 测试。"""

import pytest


class TestGetUserInfo:
    def test_no_auth(self, client):
        resp = client.get('/api/users/me')
        assert resp.status_code == 401

    def test_with_auth(self, auth_client):
        resp = auth_client.get('/api/users/me')
        assert resp.status_code == 200
        assert resp.json['code'] == 200
        assert 'data' in resp.json


class TestChangePassword:
    def test_no_auth(self, client):
        resp = client.put('/api/users/me/password', json={
            'xl_newpassword': 'encrypted',
        })
        assert resp.status_code == 401

    def test_missing_param(self, auth_client):
        resp = auth_client.put('/api/users/me/password', json={})
        assert resp.status_code == 400


class TestToggleNotification:
    def test_no_auth(self, client):
        resp = client.post('/api/users/me/notification', json={
            'expect_option': True,
        })
        assert resp.status_code == 401

    def test_missing_param(self, auth_client):
        resp = auth_client.post('/api/users/me/notification', json={})
        assert resp.status_code == 400

    def test_success(self, auth_client):
        resp = auth_client.post('/api/users/me/notification', json={
            'expect_option': 1,
        })
        assert resp.status_code == 200
