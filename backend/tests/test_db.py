"""数据库层测试。"""

import uuid

from db import tjSql


def _uid():
    return uuid.uuid4().hex[:8]


class TestNotifications:
    def test_not_exists(self):
        assert tjSql.sqlHaveRecorded(99999999) is False

    def test_find_notices_search_no_match(self):
        items, _ = tjSql.sqlFindNotices(page=1, page_size=20, search='不存在的内容')
        assert len(items) == 0

    def test_find_notices_returns_paginated(self):
        items, total = tjSql.sqlFindNotices(page=1, page_size=20)
        assert isinstance(items, list)
        assert isinstance(total, int)


class TestUsers:
    def test_user_crud(self):
        email = f'crud{_uid()}@tongji.edu.cn'
        assert tjSql.sqlUserExist(email) is False
        tjSql.sqlInsertUser(f'crud{_uid()}', email, 'hashed_pw', '2025-01-01 00:00:00')
        assert tjSql.sqlUserExist(email) is True
        info = tjSql.sqlGetUserInfo(email)
        assert info[0].startswith('crud')
        assert info[1] == email
        assert info[3] == 0

    def test_get_password(self):
        email = f'pwd{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'pwd{_uid()}', email, 'secure_hash_123', '2025-01-01 00:00:00')
        assert tjSql.sqlGetPassword(email) == 'secure_hash_123'

    def test_update_password(self):
        email = f'upd{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'upd{_uid()}', email, 'old_hash', '2025-01-01 00:00:00')
        tjSql.sqlUpdatePassword(email, 'new_hash')
        assert tjSql.sqlGetPassword(email) == 'new_hash'

    def test_toggle_receive_noti(self):
        email = f'tog{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'tog{_uid()}', email, 'hash', '2025-01-01 00:00:00')
        tjSql.sqltoggleReceiveNoti(email, 1)
        info = tjSql.sqlGetUserInfo(email)
        assert info[3] == 1

    def test_get_all_receive_noti_users(self):
        email = f'rcv{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'rcv{_uid()}', email, 'hash', '2025-01-01 00:00:00')
        tjSql.sqltoggleReceiveNoti(email, 1)
        users = tjSql.sqlGetAllReceiveNotiUser()
        assert any(u['email'] == email for u in users)

    def test_login_log(self):
        email = f'log{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'log{_uid()}', email, 'hash', '2025-01-01 00:00:00')
        tjSql.sqlUpdateLoginLog(email, '192.168.1.1', '2025-01-02 00:00:00')
        logs = tjSql.sqlGetLoginLog(email)
        assert logs is not None
        assert any(log['ip_address'] == '192.168.1.1' for log in logs)
