"""通知 API 测试。"""

import pytest

from db import tjSql


class TestListNotices:
    def test_list_returns_paginated_response(self, client):
        resp = client.get('/api/notices')
        assert resp.status_code == 200
        assert resp.json['code'] == 200
        payload = resp.json['data']
        assert 'items' in payload
        assert 'totalCount' in payload
        assert 'page' in payload
        assert 'pageSize' in payload
        assert isinstance(payload['items'], list)

    def test_list_with_all_params(self, client):
        resp = client.get('/api/notices?page=1&pageSize=10&search=测试&status=发布中')
        assert resp.status_code == 200
        assert resp.json['code'] == 200

    def test_list_extreme_params_still_ok(self, client):
        resp = client.get('/api/notices?page=1&pageSize=9999')
        assert resp.status_code == 200
        assert resp.json['code'] == 200


class TestGetNotice:
    def test_get_non_existent_returns_404(self, auth_client):
        resp = auth_client.get('/api/notices/99999999')
        assert resp.status_code == 404
        assert resp.json['code'] == 404

    def test_get_without_auth_returns_401(self, client):
        resp = client.get('/api/notices/1')
        assert resp.status_code == 401


class TestDownloadAttachment:
    def test_download_without_auth_returns_401(self, client):
        resp = client.get('/api/attachments/test.pdf/download')
        assert resp.status_code == 401
