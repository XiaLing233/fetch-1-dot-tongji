"""数据库访问层。所有函数通过 DB 上下文管理器自动处理连接/提交/关闭。"""

import os
import datetime

import mysql.connector

# 数据库配置（从环境变量读取）
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'tongjinoti'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
}


class DB:
    """MySQL 连接上下文管理器。自动提交/回滚、关闭游标和连接。"""

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


def sqlHaveRecorded(notification_id):
    with DB() as db:
        db.cursor.execute("SELECT * FROM notifications WHERE id = %s", (notification_id,))
        return len(db.cursor.fetchall()) > 0


# ----- 工具函数 ----- #

_NOTICE_COLS = ['id', 'title', 'start_time', 'end_time', 'invalid_top_time',
                'create_id', 'create_user', 'create_time', 'publish_time']


def _format_notice_row(row):
    """把一条通知记录的字段格式化（兼容 tuple 和 dict）。"""
    if isinstance(row, dict):
        item = dict(row)
    else:
        item = dict(zip(_NOTICE_COLS, row))
    for col in ('start_time', 'end_time', 'create_time', 'publish_time'):
        if item.get(col):
            item[col] = item[col].strftime("%Y-%m-%d %H:%M:%S")
    if item.get('invalid_top_time'):
        item['invalid_top_time'] = item['invalid_top_time'].strftime("%Y-%m-%d %H:%M:%S")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if item.get('invalid_top_time') and item['invalid_top_time'] > now:
        item['status'] = "置顶"
    elif item.get('end_time', '') > now:
        item['status'] = "发布中"
    else:
        item['status'] = "已过期"
    return item


def sqlFindMyCommonMsgTop():
    with DB() as db:
        sql = (
            "SELECT id, title, start_time, end_time,"
            " invalid_top_time, create_id, create_user,"
            " create_time, publish_time FROM notifications"
            " WHERE invalid_top_time > %s ORDER BY publish_time DESC"
        )
        db.cursor.execute(sql, (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
        return [dict(zip(db.cursor.column_names, row)) for row in db.cursor.fetchall()]


def sqlFindNotices(page=1, page_size=20, search='', statuses=None):
    """分页查询通知，支持标题搜索和状态多选筛选。返回 (items, total_count)。

    statuses: 状态列表，如 ['置顶', '发布中']，OR 拼接；空列表或无筛选时返回全部。
    通过 ORDER BY 统一排序+分页，置顶项始终排在最前。
    """
    if statuses is None:
        statuses = []

    with DB() as db:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        where_parts = []
        params = []

        # 状态筛选：多个状态用 OR 连接
        status_ors = []
        if '置顶' in statuses:
            status_ors.append("invalid_top_time > %s")
            params.append(now)
        if '发布中' in statuses:
            status_ors.append("end_time > %s")
            params.append(now)
        if '已过期' in statuses:
            status_ors.append("end_time <= %s")
            params.append(now)
        if status_ors:
            where_parts.append("(" + " OR ".join(status_ors) + ")")

        if search:
            where_parts.append("title LIKE %s")
            params.append(f"%{search}%")

        where = " AND ".join(where_parts) if where_parts else "1=1"

        # COUNT
        db.cursor.execute(
            f"SELECT COUNT(*) AS cnt FROM notifications WHERE {where}", params
        )
        total = db.cursor.fetchone()[0]

        # 分页：置顶优先（invalid_top_time > now 为真时排前面），再按发布时间倒序
        # 使用 IS NOT NULL AND 确保 NULL 值返回 FALSE(0) 而非 NULL，
        # 避免 MySQL ORDER BY DESC 中 NULL 排序不一致
        sql = (
            "SELECT id, title, start_time, end_time, invalid_top_time,"
            " create_id, create_user, create_time, publish_time"
            f" FROM notifications WHERE {where}"
            " ORDER BY (invalid_top_time IS NOT NULL AND invalid_top_time > %s) DESC,"
            " publish_time DESC"
            " LIMIT %s OFFSET %s"
        )
        db.cursor.execute(sql, params + [now, page_size, (page - 1) * page_size])
        items = [_format_notice_row(r) for r in db.cursor.fetchall()]

    print(f"[DB] 查询通知: page={page}, size={page_size}, search='{search}', statuses={statuses} → total={total}")
    return items, total


def sqlFindAttachmentByNotificationId(notification_id):
    with DB() as db:
        sql = (
            "SELECT MAX(r.attachment_id) as attachment_id"
            " FROM relations r"
            " JOIN attachments a ON r.attachment_id = a.id"
            " WHERE r.notification_id = %s"
            " GROUP BY a.file_location_remote"
        )
        db.cursor.execute(sql, (notification_id,))
        return db.cursor.fetchall()


def sqlFindAttachmentById(attachment_id):
    with DB() as db:
        db.cursor.execute("SELECT * FROM attachments WHERE id = %s", (attachment_id,))
        return db.cursor.fetchall()


def sqlFindMyCommonMsgPublishById(notification_id):
    with DB() as db:
        db.cursor.execute("SELECT * FROM notifications WHERE id = %s", (notification_id,))
        result = db.cursor.fetchall()
        if not result:
            return None

        attachments = sqlFindAttachmentByNotificationId(notification_id)
        attachment_list = []
        for attachment in attachments:
            info = sqlFindAttachmentById(attachment[0])
            item = {'filename': info[0][1], 'file_location_local': info[0][3]}
            filename = item['filename']
            if ".doc" in filename:
                item['fileType'] = "doc"
            elif ".xls" in filename:
                item['fileType'] = "xls"
            elif ".ppt" in filename:
                item['fileType'] = "ppt"
            elif ".zip" in filename or ".rar" in filename:
                item['fileType'] = "rar"
            elif ".pdf" in filename:
                item['fileType'] = "pdf"
            else:
                item['fileType'] = "other"
            attachment_list.append(item)

        invalid_top_time = result[0][5].strftime("%Y-%m-%d %H:%M:%S") if result[0][5] else None
        return {
        'id': result[0][0],
        'title': result[0][1],
        'content': result[0][2],
        'start_time': result[0][3].strftime("%Y-%m-%d %H:%M:%S"),
        'end_time': result[0][4].strftime("%Y-%m-%d %H:%M:%S"),
        'invalid_top_time': invalid_top_time,
        'create_id': result[0][6],
        'create_user': result[0][7],
        'create_time': result[0][8].strftime("%Y-%m-%d %H:%M:%S"),
        'publish_time': result[0][9].strftime("%Y-%m-%d %H:%M:%S"),
        'attachments': attachment_list,
    }


# ----- 用户 ----- #

def sqlUserExist(email):
    with DB() as db:
        db.cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return len(db.cursor.fetchall()) > 0


def sqlInsertUser(userName, email, password, created_at):
    with DB() as db:
        sql = "INSERT INTO users (nickname, email, password, created_at) VALUES (%s, %s, %s, %s)"
        db.cursor.execute(sql, (userName, email, password, created_at))
        return db.cursor.rowcount == 1


def sqlGetPassword(email):
    with DB() as db:
        db.cursor.execute("SELECT password FROM users WHERE email = %s", (email,))
        result = db.cursor.fetchall()
        return result[0][0] if result else None


def sqlUpdatePassword(email, newPassword):
    with DB() as db:
        db.cursor.execute("UPDATE users SET password = %s WHERE email = %s", (newPassword, email))
        return db.cursor.rowcount == 1


def sqlGetUserInfo(email):
    with DB() as db:
        sql = "SELECT nickname, email, created_at, receive_noti FROM users WHERE email = %s"
        db.cursor.execute(sql, (email,))
        result = db.cursor.fetchall()
        return result[0] if result else None


def sqltoggleReceiveNoti(email, option):
    with DB() as db:
        db.cursor.execute("UPDATE users SET receive_noti = %s WHERE email = %s", (option, email))
        return db.cursor.rowcount == 1


def sqlGetAllReceiveNotiUser():
    with DB() as db:
        db.cursor.execute("SELECT nickname, email FROM users WHERE receive_noti = 1")
        return [dict(zip(db.cursor.column_names, row)) for row in db.cursor.fetchall()]


def sqlGetUserIdByEmail(email):
    with DB() as db:
        db.cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        result = db.cursor.fetchall()
        return result[0][0] if result else None


# ----- 登录日志 ----- #

def sqlUpdateLoginLog(email, ip_address, login_at):
    user_id = sqlGetUserIdByEmail(email)
    with DB() as db:
        sql = "INSERT INTO login_logs (user_id, ip_address, login_at) VALUES (%s, %s, %s)"
        db.cursor.execute(sql, (user_id, ip_address, login_at))
        return db.cursor.rowcount == 1


def sqlGetLoginLog(email):
    user_id = sqlGetUserIdByEmail(email)
    with DB() as db:
        sql = "SELECT ip_address, login_at FROM login_logs WHERE user_id = %s ORDER BY login_at DESC LIMIT 10"
        db.cursor.execute(sql, (user_id,))
        result = db.cursor.fetchall()
        if not result:
            return None
        result = [(item[0], item[1].strftime("%Y-%m-%d %H:%M:%S")) for item in result]
        return [dict(zip(db.cursor.column_names, row)) for row in result]
