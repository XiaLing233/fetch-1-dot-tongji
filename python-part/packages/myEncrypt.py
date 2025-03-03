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

# 使用代理
ENABLE_PROXY = CONFIG['Flag']['use_proxy'] == '1'

# 账号密码认证部分
STU_NO = CONFIG['Account']['sno']
STU_PWD = CONFIG['Account']['passwd']

# js 链接
# RSA_URL = CONFIG['Js']['rsa_url'] # 动态获取
# AES_URL = CONFIG['Js']['aes_url'] # 动态获取

# 代理
HTTP_PROXY = CONFIG['Proxy']['http']
HTTPS_PROXY = CONFIG['Proxy']['https']

# 配置 SOCKS5 代理
PROXIES = {
    'http': HTTP_PROXY,
    'https': HTTPS_PROXY
}

# ----- 登录部分 ----- #

# 读取 RSA 公钥
def getRSAPublicKey(js_url):
    # js_url = RSA_URL

    if ENABLE_PROXY:
        response = requests.get(js_url, proxies=PROXIES, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'})
    else:
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
# 原始密码(str) -> 字节串(bytes) -> RSA加密(bytes) -> base64编码(bytes) -> 最终字符串(str)
def encryptPassword(js_url):
    auth_key = getRSAPublicKey(js_url)

    public_key = RSA.import_key(auth_key)

    cipher = PKCS1_v1_5.new(public_key)

    crypto = cipher.encrypt(STU_PWD.encode())

    crypto = base64.b64encode(crypto)
    
    return crypto.decode()

# ----- 通知内容请求部分 ----- #

# 读取 AES 密钥 和 IV
# js 文件会变，从 ssologin 中获取
def getAESKeyAndIV(js_url):
    # js_url = AES_URL
    
    if ENABLE_PROXY:
        response = requests.get(js_url, proxies=PROXIES, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}) 
    else:
        response = requests.get(js_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'})

    # 从 js 文件中提取密钥和 IV
    # 因为这个文件是混淆过的，所以用 , 来分行
    content = response.text
    for line in content.split(','):
        if "iv:n.enc.Utf8.parse" in line:
            iv = line.split("\"")[1] # 可能会有多个行都含有 iv，没关系，值是一样的
        if "i=n.enc.Utf8.parse" in line:
            key = line.split("\"")[1]

    return iv, key # 返回的是 ASCII 编码的 str

# 对数据进行 AES 加密
def encryptFilePath(js_url, filePath):
    iv, key = getAESKeyAndIV(js_url) # 现在得到的是 ASCII 编码的 str

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

    