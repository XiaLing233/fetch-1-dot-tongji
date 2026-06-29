# 加密部分
import os
import requests # 网络请求
from Crypto.PublicKey import RSA # RSA 加密
from Crypto.Cipher import PKCS1_v1_5 # RSA 加密
from Crypto.Cipher import AES # AES 加密
import base64 # base64 编码
from urllib.parse import quote

# ----- 登录部分 ----- #

# 读取 RSA 公钥
def getRSAPublicKey(js_url):
    # js_url = RSA_URL

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

    crypto = cipher.encrypt(os.getenv('TJ_PASSWD', '').encode())

    crypto = base64.b64encode(crypto)
    
    return crypto.decode()

# ----- 通知内容请求部分 ----- #

# 读取 AES 密钥 和 IV
# js 文件会变，从 ssologin 中获取
def getAESKeyAndIV(js_url):
    # js_url = AES_URL
    
    response = requests.get(js_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'})

    # 从 js 文件中提取密钥和 IV
    # 格式形如: r.enc.Utf8.parse("fCm^7p1AwqKPTNjn"), iv:r.enc.Utf8.parse("MaW5a2v%%I9em$UI")
    import re
    content = response.text
    iv = None
    key = None

    m = re.search(r'iv:\w\.enc\.Utf8\.parse\("([^"]+)"\)', content)
    if m:
        iv = m.group(1)

    m = re.search(r'[=,]\w\.enc\.Utf8\.parse\("([^"]+)"\)', content)
    if m:
        key = m.group(1)

    if not iv or not key:
        raise RuntimeError("无法提取 AES key/iv，学校前端可能已更新")

    return iv, key

# 对数据进行 AES 加密
def encryptFilePath(js_url, filePath):
    iv, key = getAESKeyAndIV(js_url) # 现在得到的是 ASCII 编码的 str

    # print(filePath)
    # 把 filePath 进行 URI 编码，使用 quote_plus 以确保 / 被编码为 %2F

    # print(filePath)
    # input('Press Enter to continue...')

    filePath = quote(filePath, safe='') # 移除 safe 参数，确保所有字符都被编码
    # filePath = quote_plus(filePath) # 也可以使用 quote_plus，默认 safe='/'，但是会把空格编码为 + 而不是 %20

    # print(filePath)
    # input('Press Enter to continue...')

    # PKCS7 填充
    block_size = 16
    padding_length = block_size - (len(filePath) % block_size)
    padded_text = filePath + chr(padding_length) * padding_length

    # 用 AES 加密
    cipher = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
    cipher_text = cipher.encrypt(padded_text.encode())

    # print(cipher_text)
    # input('Press Enter to continue...')

    # base64 编码
    cipher_text = quote(base64.b64encode(cipher_text).decode(), safe='') # 这里也要进行 URI 编码，确保 + 和 / 被编码为 %2B 和 %2F

    return cipher_text # 返回 URI 编码后的密文

    