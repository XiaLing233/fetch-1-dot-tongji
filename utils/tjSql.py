# 存放了数据库部分
import mysql.connector # 数据库连接
import configparser # 读取配置文件

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
def SqlInsertAttachment(attachment, localFilePath):
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
def SQlInsertRelation(notification_id, attachment_id):
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
    
# 查询所有发布的通知，不返回内容
def sqlFindMyCommonMsgPublish():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 查询通知，除了内容之外的所有列
    sql = (
        f"SELECT {N_ID}, {N_TITLE}, {N_START_TIME}, {N_END_TIME}, "
        f"{N_INVALID_TOP_TIME}, {N_CREATE_ID}, {N_CREATE_USER}, "
        f"{N_CREATE_TIME}, {N_PUBLISH_TIME} FROM {N_TABLE_NAME}"
    )
    
    print("执行的 SQL 语句是：", sql)

    cursor.execute(sql)
    
    result = cursor.fetchall()

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

# 查询所有发布的通知，返回内容和附件
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
            f"{ A_ID }": attachment_info[0][0],
            f'{ A_FILENAME }': attachment_info[0][1]
        }
        print("查询到的附件信息是：", attachment_info)
        attachment_list.append(attachment_info)

    # 把通知和附件信息合并
    notification_data = {
        f"{ N_ID }": result[0][0],
        f"{ N_TITLE }": result[0][1],
        f"{ N_CONTENT }": result[0][2],
        f"{ N_START_TIME }": result[0][3],
        f"{ N_END_TIME }": result[0][4],
        f"{ N_INVALID_TOP_TIME }": result[0][5],
        f"{ N_CREATE_ID }": result[0][6],
        f"{ N_CREATE_USER }": result[0][7],
        f"{ N_CREATE_TIME }": result[0][8],
        f"{ N_PUBLISH_TIME }": result[0][9],
        'attachments': attachment_list
    }
    
    print("查询到的通知是：", notification_data)

    return notification_data
    