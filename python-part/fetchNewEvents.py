# 获取 1 系统新发布的活动
# 并将其存储到本地

import requests # 用于发送 HTTP 请求
from packages import myEncrypt # 用于加密密码
from packages import imap_email
import time # 生成时间戳
import datetime # 生成时间
import configparser # 读取配置文件
from urllib.parse import urlencode # 用于编码请求体
from packages.tjSql import sqlInsertNotification, sqlHaveRecorded, sqlInsertAttachment, sqlInsertRelation, sqlGetAllReceiveNotiUser, sqlUpdateNotification, sqlFindAttachmentById # 用于写入数据库
import json
import xml.etree.ElementTree as ET

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

U_NICKNAME = CONFIG['Table']['u_nickname']
U_EMAIL = CONFIG['Table']['u_email']

def debug_response(step, response):
    print("第", step, "步：\n")
    print("状态码：", response.status_code, "\n")
    print("当前链接：", response.url, "\n")
    print("返回的头部：", response.headers, "\n")
    print("--------------------\n")


# 登录
def login():
    # ----- 第一步：登录前页面 ----- #

    entry_url = "https://1.tongji.edu.cn/api/ssoservice/system/loginIn"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Referer': 'https://1.tongji.edu.cn/',
    }

    session = requests.Session()
    session.headers.update(headers)
    if ENABLE_PROXY:
        response = session.get(entry_url, proxies=PROXIES)
    else:
        response = session.get(entry_url)

    # 获取 authnLcKey
    authnLcKey = response.url.split('=')[-1] # 从 URL 中提取 authnLcKey，从后往前找到第一个等号，取等号后的部分
    # print(authnLcKey)

    # ----- 第二步：ActionAuthChain ----- #

    # 获取 RSA 公钥所在 js 文件的链接
    for line in response.text.split('\n'):
        if 'crypt.js' in line:
            RSA_URL = "https://iam.tongji.edu.cn/idp/" + line.split('src=\"')[1].split('\"')[0]
            print(RSA_URL)

    CHAIN_URL = response.url

    SP_AUTH_CHAIN_CODE = myEncrypt.getspAuthChainCode(response.text)

    login_data = urlencode({
        "j_username": myEncrypt.STU_NO,
        "j_password": myEncrypt.encryptPassword(RSA_URL),
        "j_checkcode": "请输入验证码",
        "op": "login",
        "spAuthChainCode": SP_AUTH_CHAIN_CODE, # 似乎是个固定值，写死在页面的 
        "authnLcKey": authnLcKey,
    })

    # 发送登录请求
    session.headers.update(
        {
            # 'Referer': response.url, # 设置 Referer
            # 'Host': 'iam.tongji.edu.cn', # 设置 Host
            'Origin': 'https://iam.tongji.edu.cn', # 设置 Origin
            'Content-Length': str(len(login_data)), # 设置 Content-Length
            'Content-Type': 'application/x-www-form-urlencoded', # 设置 Content-Type
        }
    )
    if ENABLE_PROXY:
        response = session.post(CHAIN_URL, data=login_data, allow_redirects=False, proxies=PROXIES)
    else:
        response = session.post(CHAIN_URL, data=login_data, allow_redirects=False)

    # ----- 第 2.5 步 加强认证 ----- #

    is_enhance = False  # Flag

    # 检查是否需要加强认证
    response_xml = ET.fromstring(response.text)  # 虽然是 json，但是本质是 XML 格式

    print(response.text)
    # input()

    if response_xml.find('loginFailed').text != 'false':
        is_enhance = True  # 是加强认证

        # 发送验证码
        veri_data = urlencode({
            "j_username": myEncrypt.STU_NO,
            "type": "email" #  邮箱是 email，短信是 sms
        })  # 格式是 form_data

        if ENABLE_PROXY:
            session.post("https://iam.tongji.edu.cn/idp/sendCheckCode.do",
                        data=veri_data, allow_redirects=False, proxies=PROXIES)
        else:
            session.post("https://iam.tongji.edu.cn/idp/sendCheckCode.do",
                        data=veri_data, allow_redirects=False)

        sleep_time = 30
        failed_time = 0

    while True:
        try:
            if is_enhance:
                time.sleep(sleep_time)  # 等待 30 秒

                with imap_email.EmailVerifier(IMAP_USERNAME, IMAP_PASSWORD, IMAP_SERVER, IMAP_PORT) as v:
                    code = v.get_latest_verification_code()
                    if code:
                        print(code)
                    else:
                        raise Exception("登录失败！未找到验证码")

                login_data = urlencode({
                "j_username": myEncrypt.STU_NO,
                "type": "email",
                "sms_checkcode": code,
                "popViewException": "Pop2",
                "j_checkcode": "请输入验证码",
                "op": "login",
                "spAuthChainCode": SP_AUTH_CHAIN_CODE, # 似乎是个固定值，写死在页面的
                })

                if ENABLE_PROXY:
                    response = session.post(CHAIN_URL, data=login_data, allow_redirects=False, proxies=PROXIES)
                else:
                    response = session.post(CHAIN_URL, data=login_data, allow_redirects=False)

            # ----- 第三步：AuthnEngine ----- #

            if is_enhance:
                auth_url = "https://iam.tongji.edu.cn/idp/AuthnEngine?currentAuth=urn_oasis_names_tc_SAML_2.0_ac_classes_SMSUsernamePassword&authnLcKey=" + authnLcKey + "&entityId=SYS20230001"
            else:  # Not enhance
                auth_url = "https://iam.tongji.edu.cn/idp/AuthnEngine?currentAuth=urn_oasis_names_tc_SAML_2.0_ac_classes_BAMUsernamePassword&authnLcKey=" + authnLcKey + "&entityId=SYS20230001"

            if ENABLE_PROXY:
                response = session.post(auth_url, data=login_data, allow_redirects=False, proxies=PROXIES)
            else:
                response = session.post(auth_url, data=login_data, allow_redirects=False)

            # ----- 第四步：SSO 登录 ----- #

            sso_url = response.headers['Location']
            
            # 有必要更新 headers
            sso_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            }
            
            session.headers.clear() # 记得清空 headers，因为有 Content-Type 等不需要的字段
            session.headers.update(sso_headers)

            if ENABLE_PROXY:
                response = session.get(sso_url, allow_redirects=False, proxies=PROXIES)
            else:
                response = session.get(sso_url, allow_redirects=False)

            # ----- 第五步：LoginIn code & state----- #

            loginIn_url = response.headers['Location']  # 如果给的验证码不正确, 这里不会有 Location 属性

            if ENABLE_PROXY:
                response = session.get(loginIn_url, allow_redirects=False, proxies=PROXIES)
            else:
                response = session.get(loginIn_url, allow_redirects=False)

            break
        except Exception as e:
            print(f"发生异常{e}，继续")
            sleep_time = 10 + 5 * failed_time
            failed_time += 1

            if failed_time > 5:
                print("登录失败，尝试次数过多")
                return None
    

    # ----- 第六步：ssologin token----- #

    ssologin_url = response.headers['Location']

    if ENABLE_PROXY:
        response = session.get(ssologin_url, allow_redirects=False, proxies=PROXIES)
    else:
        response = session.get(ssologin_url, allow_redirects=False)

    # ----- 第七步：转 HTTPS ----- #

    https_url = response.headers['Location']

    if ENABLE_PROXY:
        response = session.get(https_url, allow_redirects=False, proxies=PROXIES)
    else:
        response = session.get(https_url, allow_redirects=False)

    global AES_URL

    # 提取 AES 公钥的链接
    for line in response.text.split('>'): # 混淆过的，没有换行符
        if '/static/js/app.' in line:
            # print(line)
            AES_URL = "https://1.tongji.edu.cn" + line.split('src=')[1].split('>')[0] # 提取链接 
            print(AES_URL)


    # ----- 第八步：https://1.tongji.edu.cn/api/sessionservice/session/login ----- #

    login_url = "https://1.tongji.edu.cn/api/sessionservice/session/login"

    # 准备数据，提取 ssologin 链接中的参数
    url_params = ssologin_url.split('?')[1].split('&') # 先用 ? 分割，再用 & 分割
    login_req_body = {
        "token": url_params[0].split('=')[1], # 用 = 分割
        "ts": url_params[2].split('=')[1],
        "uid": url_params[1].split('=')[1]
    }

    # 发送请求

    if ENABLE_PROXY:
        response = session.post(login_url, data=login_req_body, proxies=PROXIES)
    else:
        response = session.post(login_url, data=login_req_body)

    # 打印结果
    if response.status_code == 200:
        print("登录成功！")
        # print("当前链接", response.url) # 输出 URL
        print(session.cookies) # 输出 cookies
        # print(session.headers) # 输出 headers
        return session
    else:
        print("登录失败！")
        return None

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
        msg['To'] = to[U_EMAIL]
        # 标题带同济大学可能会被拦截，把同济改成TJ
        msg['Subject'] = "1系统发布了新内容：" + event['title']

        # 邮件正文，HTML 格式
        msg.attach(MIMEText(f"尊敬的 {to[U_NICKNAME]}：", 'html'))
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
            server.sendmail(SMTP_USERNAME, to[U_EMAIL], msg.as_string())
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

    # 退出登录
    time.sleep(60) # 至少等待 1 分钟再退出登录
    logout_data = {
        "sessionid": session.cookies.get_dict()['sessionid'],
        "uid": STU_NO,
    }

    # logout_data = json.dumps(logout_data, separators=(",", ":"))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://1.tongji.edu.cn/',        
        'Referer': 'https://1.tongji.edu.cn/workbench',        
    }

    session.headers.update(headers)

    print(headers)

    if ENABLE_PROXY:
        response = session.post("https://1.tongji.edu.cn/api/sessionservice/session/logout", proxies=PROXIES, json=logout_data)
    else:
        response = session.post("https://1.tongji.edu.cn/api/sessionservice/session/logout", json=logout_data)

    if (response.status_code == 200):
        print("退出登录成功！")
    else:
        print("退出登录失败！")
        print("状态码：", response.status_code)

    print("现在是：", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("处理活动结束！")
    print("\n\n\n")
            



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
        session = login()
        
        events = findMyCommonMsgPublish(session)

        processEvents(session, events)
    #except Exception as e:
        # print(e)


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
