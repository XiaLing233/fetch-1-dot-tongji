"""数据库层测试。"""

import datetime

from db import tjSql


class TestNotifications:
    def test_insert_and_check_exists(self, sample_notification):
        tjSql.sqlInsertNotification(sample_notification)
        assert tjSql.sqlHaveRecorded(sample_notification['id']) is True

    def test_not_exists(self):
        assert tjSql.sqlHaveRecorded(99999999) is False

    def test_update_notification(self, sample_notification):
        tjSql.sqlInsertNotification(sample_notification)
        sample_notification['title'] = '更新后的标题'
        tjSql.sqlUpdateNotification(sample_notification)
        detail = tjSql.sqlFindMyCommonMsgPublishById(sample_notification['id'])
        assert detail['title'] == '更新后的标题'

    def test_find_notices_pagination(self, sample_notification):
        tjSql.sqlInsertNotification(sample_notification)
        items, total = tjSql.sqlFindNotices(page=1, page_size=20)
        assert total >= 1
        assert any(item['id'] == sample_notification['id'] for item in items)

    def test_find_notices_search(self, sample_notification):
        tjSql.sqlInsertNotification(sample_notification)
        items, _ = tjSql.sqlFindNotices(page=1, page_size=20, search='测试通知')
        assert any(item['id'] == sample_notification['id'] for item in items)

    def test_find_notices_search_no_match(self):
        items, _ = tjSql.sqlFindNotices(page=1, page_size=20, search='不存在的内容')
        assert len(items) == 0

    def test_find_notices_status_filter_active(self, sample_notification):
        tjSql.sqlInsertNotification(sample_notification)
        items, _ = tjSql.sqlFindNotices(page=1, page_size=20, status='发布中')
        assert all(item['status'] == '发布中' for item in items)

    def test_find_by_id_with_attachments(self, sample_notification):
        tjSql.sqlInsertNotification(sample_notification)
        detail = tjSql.sqlFindMyCommonMsgPublishById(sample_notification['id'])
        assert detail['title'] == sample_notification['title']
        assert 'attachments' in detail


class TestAttachments:
    def test_insert_and_find(self):
        attachment = {'id': 88888, 'fileName': 'test.pdf', 'fileLacation': '/path/to/test.pdf'}
        local_path = '1dot/test.pdf'
        tjSql.sqlInsertAttachment(attachment, local_path)
        result = tjSql.sqlFindAttachmentById(attachment['id'])
        assert len(result) > 0
        assert result[0][1] == 'test.pdf'

    def test_insert_relation(self, sample_notification):
        tjSql.sqlInsertNotification(sample_notification)
        attachment = {'id': 77777, 'fileName': 'rel.pdf', 'fileLacation': '/path/rel.pdf'}
        tjSql.sqlInsertAttachment(attachment, '1dot/rel.pdf')
        tjSql.sqlInsertRelation(sample_notification['id'], attachment['id'])
        relations = tjSql.sqlFindAttachmentByNotificationId(sample_notification['id'])
        assert len(relations) > 0


class TestUsers:
    def test_user_crud(self):
        email = 'test_crud@tongji.edu.cn'
        assert tjSql.sqlUserExist(email) is False

        tjSql.sqlInsertUser('tester', email, 'hashed_pw', '2025-01-01 00:00:00')
        assert tjSql.sqlUserExist(email) is True

        info = tjSql.sqlGetUserInfo(email)
        assert info[0] == 'tester'
        assert info[1] == email
        assert info[3] == 0  # receive_noti default

    def test_get_password(self):
        email = 'test_pwd@tongji.edu.cn'
        tjSql.sqlInsertUser('pwd_user', email, 'secure_hash_123', '2025-01-01 00:00:00')
        assert tjSql.sqlGetPassword(email) == 'secure_hash_123'

    def test_update_password(self):
        email = 'test_updpwd@tongji.edu.cn'
        tjSql.sqlInsertUser('pwd2', email, 'old_hash', '2025-01-01 00:00:00')
        tjSql.sqlUpdatePassword(email, 'new_hash')
        assert tjSql.sqlGetPassword(email) == 'new_hash'

    def test_toggle_receive_noti(self):
        email = 'test_toggle@tongji.edu.cn'
        tjSql.sqlInsertUser('toggle', email, 'hash', '2025-01-01 00:00:00')
        tjSql.sqltoggleReceiveNoti(email, 1)
        info = tjSql.sqlGetUserInfo(email)
        assert info[3] == 1

    def test_get_all_receive_noti_users(self):
        email = 'test_rcv@tongji.edu.cn'
        tjSql.sqlInsertUser('rcv', email, 'hash', '2025-01-01 00:00:00')
        tjSql.sqltoggleReceiveNoti(email, 1)
        users = tjSql.sqlGetAllReceiveNotiUser()
        assert any(u['email'] == email for u in users)

    def test_login_log(self):
        email = 'test_log@tongji.edu.cn'
        tjSql.sqlInsertUser('log_user', email, 'hash', '2025-01-01 00:00:00')
        tjSql.sqlUpdateLoginLog(email, '192.168.1.1', '2025-01-02 00:00:00')
        logs = tjSql.sqlGetLoginLog(email)
        assert logs is not None
        assert any(log['ip_address'] == '192.168.1.1' for log in logs)
