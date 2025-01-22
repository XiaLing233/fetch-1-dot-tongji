# 获取 1 系统新发布的活动
# 并将其存储到本地

import requests # 用于发送 HTTP 请求
from packages import myEncrypt # 用于加密密码
import time # 生成时间戳
import configparser # 读取配置文件
from urllib.parse import urlencode # 用于编码请求体
from packages.tjSql import sqlInsertNotification, sqlHaveRecorded, SqlInsertAttachment, SQlInsertRelation  # 用于写入数据库
import json

# 读取配置文件
CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

# 代理
HTTP_PROXY = CONFIG['Proxy']['http']
HTTPS_PROXY = CONFIG['Proxy']['https']

# 配置 SOCKS5 代理
PROXIES = {
    'http': HTTP_PROXY,
    'https': HTTPS_PROXY
}

# 存储文件的路径
STORE_PATH = CONFIG['Storage']['path'] # 末尾没有斜杠

# 学号
STU_NO = CONFIG['Account']['sno']
# 调试

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

    response = session.get(entry_url, proxies=PROXIES)

    # 获取 authnLcKey
    authnLcKey = response.url.split('=')[-1] # 从 URL 中提取 authnLcKey，从后往前找到第一个等号，取等号后的部分
    # print(authnLcKey)

    # ----- 第二步：ActionAuthChain ----- #

    global RSA_URL
    # 获取 RSA 公钥所在 js 文件的链接
    for line in response.text.split('\n'):
        if 'crypt.js' in line:
            RSA_URL = "https://iam.tongji.edu.cn/idp/" + line.split('src=\"')[1].split('\"')[0]
            print(RSA_URL)

    chain_url = response.url

    login_data = urlencode({
        "j_username": myEncrypt.STU_NO,
        "j_password": myEncrypt.encryptPassword(RSA_URL),
        "j_checkcode": "请输入验证码",
        "op": "login",
        "spAuthChainCode": myEncrypt.getspAuthChainCode(response.text), # 似乎是个固定值，写死在页面的 
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

    response = session.post(chain_url, data=login_data, allow_redirects=False, proxies=PROXIES)

    # ----- 第三步：AuthnEngine ----- #

    auth_url = "https://iam.tongji.edu.cn/idp/AuthnEngine?currentAuth=urn_oasis_names_tc_SAML_2.0_ac_classes_BAMUsernamePassword&authnLcKey=" + authnLcKey + "&entityId=SYS20230001"

    response = session.post(auth_url, data=login_data, allow_redirects=False, proxies=PROXIES)

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

    response = session.get(sso_url, allow_redirects=False, proxies=PROXIES)

    # ----- 第五步：LoginIn code & state----- #

    loginIn_url = response.headers['Location']

    response = session.get(loginIn_url, allow_redirects=False, proxies=PROXIES)

    # ----- 第六步：ssologin token----- #

    ssologin_url = response.headers['Location']

    response = session.get(ssologin_url, allow_redirects=False, proxies=PROXIES)

    # ----- 第七步：转 HTTPS ----- #

    https_url = response.headers['Location']

    response = session.get(https_url, allow_redirects=False, proxies=PROXIES)

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

    response = session.post(login_url, data=login_req_body, proxies=PROXIES)

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

    response = session.post(msg_url, data=req_body, proxies=PROXIES)

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

    response = session.get(req_url, proxies=PROXIES)

    if (response.status_code == 200):
        print("请求成功！")
        return response.json()['data']
    else:
        print("请求失败！")
        return None
    

# 处理附件
def handleDownloadfile(session, attachment):
    # 生成下载链接
    download_url = f"https://1.tongji.edu.cn/api/commonservice/obsfile/downloadfile?objectkey="

    # 对文件名进行加密
    remotefilePath = myEncrypt.encryptFilePath(AES_URL, attachment['fileLacation']) # 要和返回的 key 对应，不要乱起名。我也很惊讶，但就是 Lacation...

    download_url += remotefilePath

    # 下载附件
    response = session.get(download_url, proxies=PROXIES)

    # 保存到本地
    localFilePath = STORE_PATH + "/" + attachment['fileName'] # 要和返回的 key 对应，不要乱起名

    with open(localFilePath, "wb") as f:
        f.write(response.content)

    return localFilePath.replace(STORE_PATH + "/", "") # 返回相对路径
    

# 处理活动，写入数据库
# events 是一个列表，每个元素是一个活动
def processEvents(session, events):
    # 测试
    print("开始处理活动！")
    for event in events:
        print("处理活动：", event['id'])
        print("活动标题：", event['title'])
        if (sqlHaveRecorded(event['id'])): # 如果已经记录过了
            continue
        else:
            # 获取活动的具体内容
            event = findCommonMsgPublishById(session, event['id'])
            sqlInsertNotification(event)
            print("插入通知成功！")
            time.sleep(2) # 不要频繁请求

            # 处理附件
            # 注意，1 系统的 findMyCommonMsgPublish 返回的附件列表永远是 null
            # 必须 ById 才能获取附件
            if (event['commonAttachmentList'] != None):
                for attachment in event['commonAttachmentList']:
                    localFilePath = handleDownloadfile(session, attachment)
                    SqlInsertAttachment(attachment, localFilePath)
                    print("插入附件成功！")
                    SQlInsertRelation(event['id'], attachment['id'])
                    print("插入关系成功！")
                    time.sleep(5) # 不要频繁请求

    # 退出登录
    logout_data = {
        "sessionid": session.cookies.get_dict()['sessionid'],
        "uid": STU_NO,
    }

    logout_data = json.dumps(logout_data, separators=(",", ":"))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://1.tongji.edu.cn/',        
        'Referer': 'https://1.tongji.edu.cn/workbench',        
        "Content-Type": "application/json",
        "Content-Length": str(len(logout_data),),
    }

    session.headers.update(headers)

    print(headers)

    response = session.post("https://1.tongji.edu.cn/api/sessionservice/session/logout", proxies=PROXIES, data=logout_data)

    if (response.status_code == 200):
        print("退出登录成功！")
    else:
        print("退出登录失败！")
        print("状态码：", response.status_code)
            



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

session = login()

events = findMyCommonMsgPublish(session)

processEvents(session, events)
