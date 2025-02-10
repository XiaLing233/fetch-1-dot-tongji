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

# 表格结构读取

# 读取通知表格结构

N_TABLE_NAME = CONFIG['Table']['n_table_name']
N_ID = CONFIG['Table']['n_id']
N_TITLE = CONFIG['Table']['n_title']
N_CONTENT = CONFIG['Table']['n_content']
N_START_TIME = CONFIG['Table']['n_start_time']
N_END_TIME = CONFIG['Table']['n_end_time']
N_INVALID_TOP_TIME = CONFIG['Table']['n_invalid_top_time']
N_CREATE_ID = CONFIG['Table']['n_create_id']
N_CREATE_USER = CONFIG['Table']['n_create_user']
N_CREATE_TIME = CONFIG['Table']['n_create_time']
N_PUBLISH_TIME = CONFIG['Table']['n_publish_time']

# 读取附件表格结构

A_TABLE_NAME = CONFIG['Table']['a_table_name']
A_ID = CONFIG['Table']['a_id']
A_FILENAME = CONFIG['Table']['a_filename']
A_FILE_LOCATION_REMOTE = CONFIG['Table']['a_file_location_remote']
A_FILE_LOCATION_LOCAL = CONFIG['Table']['a_file_location_local']

# 读取关系表格结构

R_TABLE_NAME = CONFIG['Table']['r_table_name']
# R_ID = CONFIG['Table']['r_id'] # 关系表格的主键是自增的，不需要传入
R_NOTIFICATION_ID = CONFIG['Table']['r_notification_id']
R_ATTACHMENT_ID = CONFIG['Table']['r_attachment_id']

# 读取用户表格结构

U_TABLE_NAME = CONFIG['Table']['u_table_name']
U_ID = CONFIG['Table']['u_id']
U_NICKNAME = CONFIG['Table']['u_nickname']
U_EMAIL = CONFIG['Table']['u_email']
U_PASSWORD = CONFIG['Table']['u_password']
U_CREATED_AT = CONFIG['Table']['u_created_at']
U_RECEIVE_NOTI = CONFIG['Table']['u_receive_noti']

# 读取登录日志表格结构

L_TABLE_NAME = CONFIG['Table']['l_table_name']
# L_ID = CONFIG['Table']['l_id']
L_USER_ID = CONFIG['Table']['l_user_id']
L_IP_ADDRESS = CONFIG['Table']['l_ip_address']
L_LOGIN_AT = CONFIG['Table']['l_login_at']


# ----- 数据插入部分 ----- #

# 向数据库中插入通知
def sqlInsertNotification(notification):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 插入通知
    sql = (
        f"INSERT INTO {N_TABLE_NAME} "
        f"({N_ID}, {N_TITLE}, {N_CONTENT}, {N_START_TIME}, "
        f"{N_END_TIME}, {N_INVALID_TOP_TIME}, {N_CREATE_ID}, "
        f"{N_CREATE_USER}, {N_CREATE_TIME}, {N_PUBLISH_TIME}) "
        f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
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
        f"INSERT INTO {A_TABLE_NAME} "
        f"({A_ID}, {A_FILENAME}, {A_FILE_LOCATION_REMOTE}, {A_FILE_LOCATION_LOCAL}) "
        f"VALUES (%s, %s, %s, %s)"
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
        f"INSERT INTO {R_TABLE_NAME} "
        f"({R_NOTIFICATION_ID}, {R_ATTACHMENT_ID}) "
        f"VALUES (%s, %s)"
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
    sql = f"SELECT * FROM {N_TABLE_NAME} WHERE {N_ID} = %s"
    
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
        f"SELECT {N_ID}, {N_TITLE}, {N_START_TIME}, {N_END_TIME}, "
        f"{N_INVALID_TOP_TIME}, {N_CREATE_ID}, {N_CREATE_USER}, "
        f"{N_CREATE_TIME}, {N_PUBLISH_TIME} FROM {N_TABLE_NAME} "
        f"WHERE {N_INVALID_TOP_TIME} > %s"
        f"ORDER BY {N_PUBLISH_TIME} DESC"
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



# 查询所有发布的通知，不返回内容
# 先查询置顶的，再查询未置顶的
def sqlFindMyCommonMsgPublish():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 先查询置顶的
    result = sqlFindMyCommonMsgTop()

    # 再查询未置顶的
    sql = (
        f"SELECT {N_ID}, {N_TITLE}, {N_START_TIME}, {N_END_TIME}, "
        f"{N_INVALID_TOP_TIME}, {N_CREATE_ID}, {N_CREATE_USER}, "
        f"{N_CREATE_TIME}, {N_PUBLISH_TIME} FROM {N_TABLE_NAME} "
        f"WHERE {N_INVALID_TOP_TIME} <= %s "
        f"OR {N_INVALID_TOP_TIME} IS NULL "
        f"ORDER BY {N_PUBLISH_TIME} DESC" # 按照发布时间倒序排列，最新的在前
    )
    
    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    
    # 合并查询结果，字典
    result += [dict(zip(cursor.column_names, row)) for row in cursor.fetchall()]

    # 把时间列转换为中文格式
    for item in result:
        item[N_START_TIME] = item[N_START_TIME].strftime("%Y-%m-%d %H:%M:%S")
        item[N_END_TIME] = item[N_END_TIME].strftime("%Y-%m-%d %H:%M:%S")
        item[N_CREATE_TIME] = item[N_CREATE_TIME].strftime("%Y-%m-%d %H:%M:%S")
        item[N_PUBLISH_TIME] = item[N_PUBLISH_TIME].strftime("%Y-%m-%d %H:%M:%S")
        if item[N_INVALID_TOP_TIME] != None:
            item[N_INVALID_TOP_TIME] = item[N_INVALID_TOP_TIME].strftime("%Y-%m-%d %H:%M:%S")

    # 增加一列表示状态
    for item in result:
        if item[N_END_TIME] > datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
            item['status'] = "发布中"
        else:
            item['status'] = "已过期"
        
        if item[N_INVALID_TOP_TIME] != None and item[N_INVALID_TOP_TIME] > datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
            item['status'] = "置顶"
    
    print("查询到的通知数量是：", len(result))
    # print("查询到的通知是：", result)
    
    cursor.close()
    conn.close()

    return result

# 查询一个通知关联的所有附件 ID
def sqlFindAttachmentByNotificationId(notification_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询关系表，找到关联的附件
    sql = (
        f"SELECT { R_ATTACHMENT_ID } FROM {R_TABLE_NAME} "
        f"WHERE {R_NOTIFICATION_ID} = %s"
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
        f"SELECT * FROM {A_TABLE_NAME} WHERE {A_ID} = %s"
    )

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
        f"SELECT * FROM {N_TABLE_NAME} WHERE {N_ID} = %s"
    )

    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql, (notification_id,))

    result = cursor.fetchall()

    # 查询关联附件的 ID
    attachments = sqlFindAttachmentByNotificationId(notification_id)

    attachment_list = []

    # 查询附件的信息
    for attachment in attachments:
        attachment_info = sqlFindAttachmentById(attachment[0])
        # 只保留 id 和 fileName
        attachment_info = {
            f'{ A_FILENAME }': attachment_info[0][1]
        }

        # 判断附件的类型，新建 fileType 字段
        filename = attachment_info[A_FILENAME]
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
        f"{ N_ID }": result[0][0],
        f"{ N_TITLE }": result[0][1],
        f"{ N_CONTENT }": result[0][2],
        f"{ N_START_TIME }": result[0][3].strftime("%Y-%m-%d %H:%M:%S"),
        f"{ N_END_TIME }": result[0][4].strftime("%Y-%m-%d %H:%M:%S"),
        f"{ N_INVALID_TOP_TIME }": invalid_top_time,
        f"{ N_CREATE_ID }": result[0][6],
        f"{ N_CREATE_USER }": result[0][7],
        f"{ N_CREATE_TIME }": result[0][8].strftime("%Y-%m-%d %H:%M:%S"),
        f"{ N_PUBLISH_TIME }": result[0][9].strftime("%Y-%m-%d %H:%M:%S"),
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
    sql = f"SELECT * FROM {U_TABLE_NAME} WHERE {U_EMAIL} = %s"

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
        f"INSERT INTO {U_TABLE_NAME} "
        f"({U_NICKNAME}, {U_EMAIL}, {U_PASSWORD}, {U_CREATED_AT}) "
        f"VALUES (%s, %s, %s, %s)"
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
    sql = f"SELECT {U_PASSWORD} FROM {U_TABLE_NAME} WHERE {U_EMAIL} = %s"

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
    sql = f"UPDATE {U_TABLE_NAME} SET {U_PASSWORD} = %s WHERE {U_EMAIL} = %s"

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
    sql = f"SELECT {U_NICKNAME}, {U_EMAIL}, { U_CREATED_AT }, { U_RECEIVE_NOTI } FROM {U_TABLE_NAME} WHERE {U_EMAIL} = %s"

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

    # 更新用户的密码
    sql = f"UPDATE {U_TABLE_NAME} SET {U_RECEIVE_NOTI} = %s WHERE {U_EMAIL} = %s"

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
    sql = f"SELECT { U_NICKNAME }, {U_EMAIL} FROM {U_TABLE_NAME} WHERE {U_RECEIVE_NOTI} = 1"

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
    sql = f"SELECT { U_ID } FROM {U_TABLE_NAME} WHERE {U_EMAIL} = %s"

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
        f"INSERT INTO {L_TABLE_NAME} "
        f"({L_USER_ID}, {L_IP_ADDRESS}, {L_LOGIN_AT}) "
        f"VALUES (%s, %s, %s)"
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
    sql = f"SELECT { L_IP_ADDRESS }, { L_LOGIN_AT } FROM {L_TABLE_NAME} WHERE {L_USER_ID} = %s ORDER BY {L_LOGIN_AT} DESC LIMIT 10"

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