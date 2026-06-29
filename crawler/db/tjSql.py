"""爬虫专用数据库操作：通知写入、附件管理、邮件收件人查询。"""

import os
import datetime

import mysql.connector

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'tongjinoti'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
}


class DB:
    """MySQL 连接上下文管理器。"""

    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            try:
                self.conn.commit()
            except Exception:
                pass
        self.cursor.close()
        self.conn.close()


# ----- 通知写入 ----- #

def sqlInsertNotification(notification):
    with DB() as db:
        sql = (
            "INSERT INTO notifications"
            " (id, title, content, start_time, end_time, invalid_top_time,"
            "  create_id, create_user, create_time, publish_time)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        db.cursor.execute(sql, (
            notification["id"], notification["title"], notification["content"],
            notification["startTime"], notification["endTime"], notification["invalidTopTime"],
            notification["createId"], notification["createUser"], notification["createTime"],
            notification["publishTime"],
        ))


def sqlUpdateNotification(notification):
    with DB() as db:
        sql = (
            "UPDATE notifications SET"
            " title = %s, content = %s, start_time = %s,"
            " end_time = %s, invalid_top_time = %s, create_id = %s,"
            " create_user = %s, create_time = %s, publish_time = %s"
            " WHERE id = %s"
        )
        db.cursor.execute(sql, (
            notification["title"], notification["content"],
            notification["startTime"], notification["endTime"],
            notification["invalidTopTime"], notification["createId"],
            notification["createUser"], notification["createTime"],
            notification["publishTime"], notification["id"],
        ))


def sqlHaveRecorded(notification_id):
    with DB() as db:
        db.cursor.execute("SELECT * FROM notifications WHERE id = %s", (notification_id,))
        return len(db.cursor.fetchall()) > 0


# ----- 附件 ----- #

def sqlInsertAttachment(attachment, localFilePath):
    with DB() as db:
        sql = (
            "INSERT INTO attachments"
            " (id, filename, file_location_remote, file_location_local)"
            " VALUES (%s, %s, %s, %s)"
        )
        db.cursor.execute(sql, (
            attachment["id"], attachment["fileName"],
            attachment["fileLacation"], localFilePath,
        ))


def sqlInsertRelation(notification_id, attachment_id):
    with DB() as db:
        sql = "INSERT INTO relations (notification_id, attachment_id) VALUES (%s, %s)"
        db.cursor.execute(sql, (notification_id, attachment_id))


def sqlFindAttachmentById(attachment_id):
    with DB() as db:
        db.cursor.execute("SELECT * FROM attachments WHERE id = %s", (attachment_id,))
        return db.cursor.fetchall()


# ----- 用户通知 ----- #

def sqlGetAllReceiveNotiUser():
    with DB() as db:
        db.cursor.execute("SELECT nickname, email FROM users WHERE receive_noti = 1")
        return [dict(zip(db.cursor.column_names, row)) for row in db.cursor.fetchall()]
