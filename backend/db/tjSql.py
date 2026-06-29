# 存放了数据库部分
import mysql.connector # 数据库连接
import configparser # 读取配置文件
import datetime # 时间处理

# 读取配置文件
CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini', encoding='utf-8')

# 设置数据库连接
DB_HOST = CONFIG['Sql']['host']
DB_USER = CONFIG['Sql']['user']
DB_PASSWORD = CONFIG['Sql']['password']
DB_DATABASE = CONFIG['Sql']['database']
DB_PORT = int(CONFIG['Sql']['port'])
DB_CHARSET = CONFIG['Sql']['charset']

# 连接数据库
DB_CONFIG = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_DATABASE,
    'port': DB_PORT,
    'charset': DB_CHARSET
}


# ----- 数据更新部分 ----- #
def sqlUpdateNotification(notification):
    '''
    更新所有信息，因为置顶状态等会改变。
    '''
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 插入通知
    sql = (
        " UPDATE notifications SET"
        " title = %s, content = %s, start_time = %s, "
        " end_time = %s, invalid_top_time = %s, create_id = %s, "
        " create_user = %s, create_time = %s, publish_time = %s"
        " WHERE id = %s"
    )

    print("执行的 SQL 语句是：", sql)

    # print(notification)
    # input()

    cursor.execute(sql, (notification["title"], notification["content"],
                        notification["startTime"], notification["endTime"],
                        notification["invalidTopTime"], notification["createId"],
                        notification["createUser"], notification["createTime"],
                        notification["publishTime"], notification["id"]))
    
    conn.commit()
    cursor.close()
    conn.close()

# ----- 数据插入部分 ----- #

# 向数据库中插入通知
def sqlInsertNotification(notification):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 插入通知
    sql = (
        "INSERT INTO notifications "
        "(id, title, content, start_time, "
        "end_time, invalid_top_time, create_id, "
        "create_user, create_time, publish_time) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )

    print("执行的 SQL 语句是：", sql)

    print(notification["content"])
    
    cursor.execute(sql, (notification["id"], notification["title"], notification["content"], 
                        notification["startTime"], notification["endTime"], notification["invalidTopTime"], 
                        notification["createId"], notification["createUser"], notification["createTime"], 
                        notification["publishTime"]))
    
    conn.commit()
    cursor.close()
    conn.close()

# 向数据库中插入附件
def sqlInsertAttachment(attachment, localFilePath):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 插入附件
    sql = (
        "INSERT INTO attachments "
        "(id, filename, file_location_remote, file_location_local) "
        "VALUES (%s, %s, %s, %s)"
    )
    
    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (attachment["id"], attachment["fileName"], 
                         attachment["fileLacation"], localFilePath))
    
    conn.commit()
    cursor.close()
    conn.close()

# 向数据库中插入关系
# 关系的主键是自增的，所以不需要传入
def sqlInsertRelation(notification_id, attachment_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 插入关系
    sql = (
        "INSERT INTO relations "
        "(notification_id, attachment_id) "
        "VALUES (%s, %s)"
    )

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (notification_id, attachment_id))
    
    conn.commit()
    cursor.close()
    conn.close()


# ----- 数据查询部分 ----- #

# 查询数据库中是否已经记录过这个通知
def sqlHaveRecorded(notification_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询通知
    sql = "SELECT * FROM notifications WHERE id = %s"
    
    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (notification_id,))
    
    result = cursor.fetchall()
    
    cursor.close()
    conn.close()

    if len(result) == 0:
        print(f"通知 {notification_id} 未记录")
        return False
    else:
        print(f"通知 {notification_id} 已记录")
        return True
    
# 查询所有置顶的通知，不返回内容
# 置顶与否的判据是当前时间是否超过了 invalidTopTime
def sqlFindMyCommonMsgTop():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询通知，除了内容之外的所有列
    sql = (
        "SELECT id, title, start_time, end_time, "
        "invalid_top_time, create_id, create_user, "
        "create_time, publish_time FROM notifications "
        "WHERE invalid_top_time > %s"
        "ORDER BY publish_time DESC"
    )

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    
    result = cursor.fetchall()

    print("查询到的通知数量是：", len(result))
    # print("查询到的通知是：", result)

    # 转换为字典
    result = [dict(zip(cursor.column_names, row)) for row in result]

    cursor.close()
    conn.close()

    return result



def _format_notice_row(row):
    """把一条通知记录的字段格式化。"""
    item = dict(row)
    for col in ('start_time', 'end_time', 'create_time', 'publish_time'):
        if item.get(col):
            item[col] = item[col].strftime("%Y-%m-%d %H:%M:%S")
    if item.get('invalid_top_time'):
        item['invalid_top_time'] = item['invalid_top_time'].strftime("%Y-%m-%d %H:%M:%S")

    # status
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if item.get('invalid_top_time') and item['invalid_top_time'] > now:
        item['status'] = "置顶"
    elif item.get('end_time', '') > now:
        item['status'] = "发布中"
    else:
        item['status'] = "已过期"
    return item


def sqlFindNotices(page=1, page_size=20, search='', status=''):
    """
    分页查询通知，支持标题搜索和状态筛选。
    返回 (items, total_count)。
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 构建 WHERE 条件
    where_parts = ["(invalid_top_time <= %s OR invalid_top_time IS NULL)"]
    params = [now]

    if search:
        where_parts.append("title LIKE %s")
        params.append(f"%{search}%")

    if status == '置顶':
        where_parts = ["invalid_top_time > %s"]
        params = [now]
    elif status == '发布中':
        where_parts.append("end_time > %s")
        params.append(now)
    elif status == '已过期':
        where_parts.append("end_time <= %s")
        params.append(now)

    where = " AND ".join(where_parts)

    # 先查置顶（如果无状态筛选）
    pinned = []
    if status != '置顶' and not search:
        cursor.execute(
            "SELECT * FROM notifications WHERE invalid_top_time > %s ORDER BY publish_time DESC",
            (now,)
        )
        pinned = [_format_notice_row(r) for r in cursor.fetchall()]

    # COUNT
    count_sql = f"SELECT COUNT(*) AS cnt FROM notifications WHERE {where}"
    cursor.execute(count_sql, params)
    total = cursor.fetchone()['cnt'] + len(pinned)

    # 分页查询（非置顶部分）
    base_sql = (
        "SELECT id, title, start_time, end_time, invalid_top_time, "
        "create_id, create_user, create_time, publish_time "
        "FROM notifications WHERE {where} ORDER BY publish_time DESC "
        "LIMIT %s OFFSET %s"
    ).format(where=where)

    params += [page_size, (page - 1) * page_size]
    cursor.execute(base_sql, params)
    items = [_format_notice_row(r) for r in cursor.fetchall()]

    cursor.close()
    conn.close()

    # 首页时置顶排最前面
    result = pinned + items if page == 1 else items

    print(f"[DB] 查询通知: page={page}, size={page_size}, search='{search}', status='{status}' → total={total}")
    return result, total

# 查询一个通知关联的所有附件 ID
def sqlFindAttachmentByNotificationId(notification_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询关系表，找到关联的附件
    # 如果多个附件具有相同的 file_location_remote，只返回 id 更大的
    sql = (
        "SELECT MAX(r.attachment_id) as attachment_id "
        "FROM relations r "
        "JOIN attachments a ON r.attachment_id = a.id "
        "WHERE r.notification_id = %s "
        "GROUP BY a.file_location_remote"
    )

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (notification_id,))

    result = cursor.fetchall()

    print("查询到的附件数量是：", len(result))

    print("查询到的附件是：", result)

    cursor.close()
    conn.close()

    return result

# 根据附件的 Id 查询附件的信息，返回全部信息，根据需要再取舍
def sqlFindAttachmentById(attachment_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询附件表，找到附件的信息
    sql = (
        "SELECT * FROM attachments WHERE id = %s"
    )

    print(attachment_id)

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (attachment_id,))

    result = cursor.fetchall()

    # print("查询到的附件是：", result)

    cursor.close()
    conn.close()

    return result

# 根据 id 查询发布的通知，返回内容和附件
def sqlFindMyCommonMsgPublishById(notification_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询通知，返回所有列
    sql = (
        "SELECT * FROM notifications WHERE id = %s"
    )

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (notification_id,))

    result = cursor.fetchall()

    # 查询关联附件的 ID
    attachments = sqlFindAttachmentByNotificationId(notification_id)

    attachment_list = []

    # 查询附件的信息
    for attachment in attachments:
        print(attachment)
        attachment_info = sqlFindAttachmentById(attachment[0])
        # 只保留 id 和 fileName
        attachment_info = {
            'filename': attachment_info[0][1],
            'file_location_local': attachment_info[0][3]
        }

        # 判断附件的类型，新建 fileType 字段
        filename = attachment_info['filename']
        if ".doc" in filename:
            attachment_info['fileType'] = "doc"
        elif ".xls" in filename:
            attachment_info['fileType'] = "xls"
        elif ".ppt" in filename:
            attachment_info['fileType'] = "ppt"
        elif ".zip" in filename or ".rar" in filename:
            attachment_info['fileType'] = "rar"
        elif ".pdf" in filename:
            attachment_info['fileType'] = "pdf"
        else:
            attachment_info['fileType'] = "other"
        print("查询到的附件信息是：", attachment_info)
        attachment_list.append(attachment_info)

    if result[0][5] != None:
        invalid_top_time = result[0][5].strftime("%Y-%m-%d %H:%M:%S")
    else:
        invalid_top_time = None

    # 把通知和附件信息合并
    notification_data = {
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
        'attachments': attachment_list
    }
    
    print("查询到的通知是：", notification_data)

    return notification_data
    


# ----- 用户注册登录部分 ----- #

# 查询用户是否存在
def sqlUserExist(email):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询用户
    sql = "SELECT * FROM users WHERE email = %s"

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (email,))

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    if len(result) == 0:
        print(f"用户 {email} 不存在")
        return False
    else:
        print(f"用户 {email} 已存在")
        return True
    

# 用户注册
# 顺序是：用户名，邮箱，密码，注册时间
def sqlInsertUser(userName, email, password, created_at):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 插入用户
    sql = (
        "INSERT INTO users "
        "(nickname, email, password, created_at) "
        "VALUES (%s, %s, %s, %s)"
    )

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (userName, email, password, created_at))

    conn.commit()
    cursor.close()
    conn.close()

    if cursor.rowcount == 1:
        print("插入成功")
        return True
    else:
        print("插入失败")
        return False


# 返回数据库中的密码，加密的，原样返回
def sqlGetPassword(email):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询用户的密码
    sql = "SELECT password FROM users WHERE email = %s"

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (email,))

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    if len(result) == 0:
        print("用户不存在")
        return None
    


    return result[0][0]

# 更新密码
def sqlUpdatePassword(email, newPassword):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 更新用户的密码
    sql = "UPDATE users SET password = %s WHERE email = %s"

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (newPassword, email))

    conn.commit()
    cursor.close()
    conn.close()

    if cursor.rowcount == 1:
        print("更新成功")
        return True
    else:
        print("更新失败")
        return False

# 获取用户信息
def sqlGetUserInfo(email):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("查询的用户邮箱是：", email)

    # 查询用户的信息
    sql = "SELECT nickname, email, created_at, receive_noti FROM users WHERE email = %s"

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (email,))

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    if len(result) == 0:
        print("用户不存在")
        return None

    print(result[0])

    return result[0]

# 切换用户是否接收通知
def sqltoggleReceiveNoti(email, option):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 更新用户的接收通知选项
    sql = "UPDATE users SET receive_noti = %s WHERE email = %s"

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (option, email))

    conn.commit()
    cursor.close()
    conn.close()

    if cursor.rowcount == 1:
        print("更新成功")
        return True
    else:
        print("更新失败")


# 获取所有要接受通知的用户邮箱
def sqlGetAllReceiveNotiUser():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询用户的邮箱
    sql = "SELECT nickname, email FROM users WHERE receive_noti = 1"

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql)

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    # 转换为字典
    result = [dict(zip(cursor.column_names, row)) for row in result]

    print("查询到的用户邮箱是：", result)

    return result

# 通过邮箱获取用户 ID
def sqlGetUserIdByEmail(email):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询用户的 ID
    sql = "SELECT id FROM users WHERE email = %s"

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (email,))

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    if len(result) == 0:
        print("用户不存在")
        return None

    return result[0][0]

# 更新登录记录
def sqlUpdateLoginLog(email, ip_address, login_at):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询用户的 ID
    user_id = sqlGetUserIdByEmail(email)

    # 插入登录记录
    sql = (
        "INSERT INTO login_logs "
        "(user_id, ip_address, login_at) "
        "VALUES (%s, %s, %s)"
    )

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (user_id, ip_address, login_at))

    conn.commit()
    cursor.close()
    conn.close()

    if cursor.rowcount == 1:
        print("插入成功")
        return True
    else:
        print("插入失败")
        return False
    
# 查询登录记录
def sqlGetLoginLog(email):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询用户的 ID
    user_id = sqlGetUserIdByEmail(email)

    # 查询登录记录
    sql = "SELECT ip_address, login_at FROM login_logs WHERE user_id = %s ORDER BY login_at DESC LIMIT 10"

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (user_id,))

    result = cursor.fetchall()

    print(result)

    # 时间转换为中文格式，原始数据是元组
    result = [(item[0], item[1].strftime("%Y-%m-%d %H:%M:%S")) for item in result]

    # 转换为字典
    result = [dict(zip(cursor.column_names, row)) for row in result]

    cursor.close()
    conn.close()

    if len(result) == 0:
        print("登录记录不存在")
        return None

    return result