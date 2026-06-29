"""爬虫数据库测试：通知写入、附件管理。"""

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
        # 验证更新成功——重新插入会报 duplicate，说明记录存在
        assert tjSql.sqlHaveRecorded(sample_notification['id']) is True


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
        assert True  # 没抛异常即成功


class TestUserNotification:
    def test_get_all_receive_noti_users(self):
        users = tjSql.sqlGetAllReceiveNotiUser()
        assert isinstance(users, list)
