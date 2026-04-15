# 获取 1 系统新发布的活动
# 并将其存储到本地

from packages import myEncrypt # 用于加密密码
from packages import loginout
import time # 生成时间戳
import datetime # 生成时间
import configparser # 读取配置文件
from packages.tjSql import sqlInsertNotification, sqlHaveRecorded, sqlInsertAttachment, sqlInsertRelation, sqlGetAllReceiveNotiUser, sqlUpdateNotification, sqlFindAttachmentById # 用于写入数据库

# 邮件
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import smtplib

# COS
from packages.upload_to_cos import CosUpload

MYCOS = CosUpload()

# 数据库

# 读取配置文件
CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

ENABLE_PROXY = CONFIG['Flag']['use_proxy'] == '1'
SEND_EMAIL = CONFIG['Flag']['send_email'] == '1'

# 代理
if ENABLE_PROXY:
    HTTP_PROXY = CONFIG['Proxy']['http']
    HTTPS_PROXY = CONFIG['Proxy']['https']

    # 配置 SOCKS5 代理
    PROXIES = {
        'http': HTTP_PROXY,
        'https': HTTPS_PROXY
    }

# 存储文件的路径
STORE_PATH = CONFIG['Storage']['attachment_path'] # 末尾没有斜杠

# 学号
STU_NO = CONFIG['Account']['sno']

# 邮件
SMTP_SERVER = CONFIG['Email']['smtp_server']
SMTP_PORT = CONFIG['Email']['smtp_port']
SMTP_USERNAME = CONFIG['Email']['smtp_username_batch'] # 是营销邮件，需要批量发送
SMTP_PASSWORD = CONFIG['Email']['smtp_password_batch']

# 加强认证
IMAP_SERVER = CONFIG["IMAP"]["server_domain"]
IMAP_PORT = CONFIG["IMAP"]["server_port"]
IMAP_USERNAME =  CONFIG["IMAP"]["qq_emailaddr"]
IMAP_PASSWORD =  CONFIG["IMAP"]["qq_grantcode"]

def debug_response(step, response):
    print("第", step, "步：\n")
    print("状态码：", response.status_code, "\n")
    print("当前链接：", response.url, "\n")
    print("返回的头部：", response.headers, "\n")
    print("--------------------\n")

# 获取活动
# 这里用了和学校系统一样的方法名
def findMyCommonMsgPublish(session):
    # Request Body 准备
    req_body = {
        "pageNum_": 1,
        "pageSize_": 100, # 直接 100 个，1 页就请求全了
        "status": "",
        "title": "",
        "total": 0, # 第一次请求是 0，后端不会认为是错误
    }

    # 发送请求
    msg_url = "https://1.tongji.edu.cn/api/commonservice/commonMsgPublish/findMyCommonMsgPublish"

    if ENABLE_PROXY:
        response = session.post(msg_url, data=req_body, proxies=PROXIES)
    else:
        response = session.post(msg_url, data=req_body)

    if (response.status_code == 200):
        print("请求成功！")
        # 调试，输出到文件中
        # with open("response.json", "w") as f:
        #     f.write(response.text)

        return response.json()['data']['list'] # 返回活动列表
    else:
        print("请求失败！")
        return None

# 获得活动的具体内容
def findCommonMsgPublishById(session, id):
    # * 1000 是为了转换为毫秒级时间戳
    req_url = f"https://1.tongji.edu.cn/api/commonservice/commonMsgPublish/findCommonMsgPublishById?id={ id }&t={ int(time.time() * 1000) }"

    if ENABLE_PROXY:
        response = session.get(req_url, proxies=PROXIES)
    else:
        response = session.get(req_url)

    if (response.status_code == 200):
        print("请求成功！")
        return response.json()['data']
    else:
        print("请求失败！")
        return None
    

# 处理附件
def handleDownloadfile(session, attachment):
    # 生成下载链接
    download_url = "https://1.tongji.edu.cn/api/commonservice/obsfile/downloadfile?objectkey="

    # 对文件名进行加密
    remotefilePath = myEncrypt.encryptFilePath(AES_URL, attachment['fileLacation']) # 要和返回的 key 对应，不要乱起名。我也很惊讶，但就是 Lacation...

    download_url += remotefilePath

    # 下载附件
    if ENABLE_PROXY:
        response = session.get(download_url, proxies=PROXIES)
    else:
        response = session.get(download_url)

    # 保存到本地
    # localFilePath = STORE_PATH + "/" + attachment['fileLacation'].split('/')[-1] # 要和返回的 key 对应，不要乱起名

    # with open(localFilePath, "wb") as f:
    #     f.write(response.content)

    # return localFilePath.replace(STORE_PATH + "/", "") # 返回相对路径

    cosFilePath = f"{STORE_PATH}/{attachment['fileLacation'].split('/')[-1]}"
    print(cosFilePath)

    MYCOS.upload_from_bytes(content=response.content, object_key=cosFilePath)

    return cosFilePath.replace(STORE_PATH + "/", "") # 返回相对路径

    
# 发送新活动邮件
# event 是一个元组，包含 title 和 content 等
def sendNotiEmail(event):
    # 获取收件人列表，包含昵称和邮箱
    to_list = sqlGetAllReceiveNotiUser()

    # 创建邮件
    for to in to_list:
        msg = MIMEMultipart()
        msg['From'] = formataddr(["琪露诺bot", SMTP_USERNAME])
        msg['To'] = to["email"]
        # 标题带同济大学可能会被拦截，把同济改成TJ
        msg['Subject'] = "1系统发布了新内容：" + event['title']

        # 邮件正文，HTML 格式
        msg.attach(MIMEText(f"尊敬的 {to['nickname']}：", 'html'))
        msg.attach(MIMEText(f"<br>通知标题：<b>{event['title']}</b><br>", 'html'))
        msg.attach(MIMEText(event['content'], 'html'))

        # 把附件名称加入邮件，不要附件内容
        if (event['commonAttachmentList'] != []): # 有附件
            msg.attach(MIMEText("<br>该通知包含以下" + str(len(event['commonAttachmentList'])) + "个附件: <br>", 'html'))
            for attachment in event['commonAttachmentList']:
                msg.attach(MIMEText(attachment['fileName'] + "<br>", 'html'))
        else:
            msg.attach(MIMEText("<br>该通知没有附件。", 'html'))
        
        # 结尾
        msg.attach(MIMEText("<br>请您及时查看，谢谢！<br>琪露诺bot", 'html'))

        # print(msg)
        
        # 发送邮件
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, to["email"], msg.as_string())
            print("邮件发送成功！")
            time.sleep(5) # 不要频繁请求


# 处理活动，写入数据库
# events 是一个列表，每个元素是一个活动
def processEvents(session, events):
    # 测试
    print("\n\n\n")
    print("现在是：", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("开始处理活动！")
    print("\n\n\n")
    for event in events:
        print("处理活动：", event['id'])
        print("活动标题：", event['title'])
        if (sqlHaveRecorded(event['id'])): # 如果已经记录过了，更新
            event = findCommonMsgPublishById(session, event['id'])
            sqlUpdateNotification(event)
            print("更新通知成功！")
        else:
            # 获取活动的具体内容
            event = findCommonMsgPublishById(session, event['id'])
            sqlInsertNotification(event)
            print("插入通知成功！")

            # 发送邮件
            if SEND_EMAIL:
                try:
                    sendNotiEmail(event)
                except Exception as e:
                    print(f"发送邮件失败：{e}")  # 有可能是配置错误，也可能是邮件内容被学校服务器屏蔽了
            else:
                time.sleep(10) # 模拟发送邮件
                print("邮件发送成功！(模拟)")

            time.sleep(2) # 不要频繁请求

        # 处理附件，不管 if-else
        # 注意，1 系统的 findMyCommonMsgPublish 返回的附件列表永远是 null
        # 必须 ById 才能获取附件
        if (event['commonAttachmentList'] != None):
            for attachment in event['commonAttachmentList']:
                try:
                    # 如果附件已经存在，就不再插入
                    # 这里可能有一个问题是，附件的 id 不一样，但是下载文件的地址却是一样的
                    # 我推测的原因可能是，发布者更新了附件，原地址不变，但是 id 却递增了
                    #TODO：到时候再说吧
                    if sqlFindAttachmentById(attachment["id"]):
                        print("附件已存在！")
                        continue
                    localFilePath = handleDownloadfile(session, attachment)
                    sqlInsertAttachment(attachment, localFilePath)
                    print("插入附件成功！")
                    sqlInsertRelation(event['id'], attachment['id'])
                    print("插入关系成功！")
                except Exception as e:
                    print(f"{e}\n处理附件失败！") # 发现有的通知居然有假的附件！点了链接没反应！不要因为某个附件失败就中断整个程序
                time.sleep(5) # 不要频繁请求
            



# ----- 测试环境 ----- #

# 记录 dump Cookie
# import json
# with open("cookies.json", "w") as f:
    # json.dump(session.cookies.get_dict(), f)

# session = requests.Session()

# 读取 dump Cookie
# with open("cookies.json", "r") as f:
    # cookies = json.load(f)
    # session.cookies.update(cookies)

# events = findMyCommonMsgPublish(session)

# processEvents(session, events)

# ----- 生产环境 ----- #

if __name__ == "__main__":
    #try:
        session = loginout.login()
        
        events = findMyCommonMsgPublish(session)

        processEvents(session, events)

        # 退出登录
        time.sleep(10) # 至少等待 10s 再退出登录
        loginout.logout(session)

        print("现在是：", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("处理活动结束！")
        print("\n\n\n")


# 调试
# if __name__ == "__main__":
#     session = login()

#     while True:
#         fileName = input()

#         attachment = {
#             "fileLacation": fileName,
#             "test": True,
#         }

#         print(handleDownloadfile(session, attachment))"""
