# 加密部分

import configparser # 读取配置文件
import requests # 网络请求
from Crypto.PublicKey import RSA # RSA 加密
from Crypto.Cipher import PKCS1_v1_5 # RSA 加密
from Crypto.Cipher import AES # AES 加密
import base64 # base64 编码
from urllib.parse import quote_plus

# 读取配置文件

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

# 账号密码认证部分
STU_NO = CONFIG['Account']['sno']
STU_PWD = CONFIG['Account']['passwd']

# js 链接
RSA_URL = CONFIG['Js']['rsa_url']
AES_URL = CONFIG['Js']['aes_url']

# ----- 登录部分 ----- #

# 读取 RSA 公钥
def getRSAPublicKey():
    js_url = RSA_URL

    response = requests.get(js_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'})

    # 从 js 文件中提取公钥
    content = response.text
    for line in content.split('\n'):
        if 'encrypt.setPublicKey' in line and not line.strip().startswith('//'):
            public_key = line.split("'")[1] # Extract key between single quotes
            public_key = "-----BEGIN PUBLIC KEY-----\n" + public_key + "\n-----END PUBLIC KEY-----"
            return public_key
    return None

# 从 HTML 中读取 spAuthChainCode，一行形如 $("#spAuthChainCode1").val('4c1eb8ec14fa4e8ba0f31188dbf88cdd');
def getspAuthChainCode(response_text):
    for line in response_text.split('\n'):
        if '\"#spAuthChainCode1"' in line:
            return line.split("'")[1]
        
    return None
    
# 把密码用 RSA 加密，公钥是 auth_key
def encryptPassword():
    auth_key = getRSAPublicKey()

    public_key = RSA.import_key(auth_key)

    cipher = PKCS1_v1_5.new(public_key)

    crypto = cipher.encrypt(STU_PWD.encode())

    crypto = base64.b64encode(crypto)
    
    return crypto.decode()

# ----- 通知内容请求部分 ----- #

# 读取 AES 密钥 和 IV
def getAESKeyAndIV():
    js_url = AES_URL
    
    response = requests.get(js_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'})

    # 从 js 文件中提取密钥和 IV
    # 因为这个文件是混淆过的，所以用 , 来分行
    content = response.text
    for line in content.split(','):
        if "iv:n.enc.Utf8.parse" in line:
            iv = line.split("\"")[1] # 可能会有多个行都含有 iv，没关系，值是一样的
        if "i=n.enc.Utf8.parse" in line:
            key = line.split("\"")[1]

    return iv, key # 返回的是 utf-8 编码的 str

# 对数据进行 AES 加密
def encryptFilePath(filePath):
    iv, key = getAESKeyAndIV() # 现在得到的是 utf-8 编码的 str

    # print(filePath)
    # 把 filePath 进行 URI 编码，使用 quote_plus 以确保 / 被编码为 %2F
    filePath = quote_plus(filePath)

    # print(filePath)

    # PKCS7 填充
    block_size = 16
    padding_length = block_size - (len(filePath) % block_size)
    padded_text = filePath + chr(padding_length) * padding_length

    # 用 AES 加密
    cipher = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
    cipher_text = cipher.encrypt(padded_text.encode())

    # base64 编码
    cipher_text = quote_plus(base64.b64encode(cipher_text).decode())

    return cipher_text # 返回 URI 编码后的密文

# 调试

# getAESKeyAndIV()


# val = "/api/commonservice/obsfile/downloadfile?objectkey=" + encryptFilePath("face/file/20250117115629105628_同济大学第二届中华美育大赛通知new.pdf")

# if ("/api/commonservice/obsfile/downloadfile?objectkey=zxegBMG%2Br5h2jLTwimMTDofu9Rs7Kk%2BmvGQyEi462aYpfVJsMlVUA63qfQd3LlZcqnCtIM%2FsjB0MNzEE0avajJC77UrvGpkjiLLTdDXVhGxVYu%2B34saJLWMDemuXYI0mAJnbOGKPIOsPg8RUWT9InjKPpMy8n1wnsoTmSQ8rDgDGVDUDZMabRlEE0P3BjSCtZeR500Ns%2FOcayGhUmbZcl5lSNacBRYHkOslMS%2FD4cHsEC5iXC5CIpawnvbwoiekE" == val):
#     print("Test Passed")
# else:
#     print("Test Failed")

# print(val)
    