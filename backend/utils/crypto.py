# 解密部分

import configparser # 读取配置文件
import base64 # base64 编码
from urllib.parse import unquote_plus # URL 解码
from Crypto.PublicKey import RSA # RSA 加密
from Crypto.Cipher import PKCS1_v1_5 # RSA 加密
from Crypto.Cipher import AES # AES 加密
from Crypto.Util.Padding import unpad

# 读取配置文件

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

# 私钥

PRIVATE_KEY_PATH = CONFIG['RSA']['private_key_path']
AES_KEY = CONFIG['AES']['key']
AES_IV = CONFIG['AES']['iv']

# 解密密码，输入是 URI 编码的密码
def decryptPassword(encrypted_password):
    # 读取私钥
    with open(PRIVATE_KEY_PATH, 'r') as f:
        private_key = RSA.importKey(f.read())
    
    # 创建 RSA 解密对象
    cipher = PKCS1_v1_5.new(private_key)
    
    # URL 解码
    encrypted_password = unquote_plus(encrypted_password)

    # base64 解码
    encrypted_password = base64.b64decode(encrypted_password)
    
    # 解密
    decrypted_password = cipher.decrypt(encrypted_password, None)
    
    return decrypted_password.decode('utf-8')


# 解密文件名，输入是 URI 编码的文件名
def decryptFilePath(encrypted_file_path):
    # URL 解码
    encrypted_file_path = unquote_plus(encrypted_file_path)

    print(encrypted_file_path)

    # base64 解码
    encrypted_file_path = base64.b64decode(encrypted_file_path)
    
    print(encrypted_file_path)

    # AES 解密
    cipher = AES.new(AES_KEY.encode(), AES.MODE_CBC, AES_IV.encode())
    decrypted_file_path = cipher.decrypt(encrypted_file_path)
    
    print(decrypted_file_path)

    # PKCS7 去填充
    decrypted_file_path = unpad(decrypted_file_path, 16)

    print(decrypted_file_path)
    
    # 去 URI 编码
    decrypted_file_path = unquote_plus(decrypted_file_path.decode())
    
    print(decrypted_file_path)

    return decrypted_file_path

# from urllib.parse import quote_plus # URL 编码

# # 调试
# # 对数据进行 AES 加密
# def myEncryptFilePath(filePath):
#     iv = AES_IV
#     key = AES_KEY

#     # print(filePath)
#     # 把 filePath 进行 URI 编码，使用 quote_plus 以确保 / 被编码为 %2F
#     filePath = quote_plus(filePath)

#     # print(filePath)

#     # PKCS7 填充
#     block_size = 16
#     padding_length = block_size - (len(filePath) % block_size)
#     padded_text = filePath + chr(padding_length) * padding_length

#     # 用 AES 加密
#     cipher = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
#     cipher_text = cipher.encrypt(padded_text.encode())

#     # base64 编码
#     cipher_text = quote_plus(base64.b64encode(cipher_text).decode())

#     return cipher_text # 返回 URI 编码后的密文

# # 测试
# myEncryptedFilePath = myEncryptFilePath("关于举办2025年国家公派研究生项目线上宣讲会的通知（1月2日下午3点线上）.pdf")

# print(myEncryptedFilePath)

# decrypted_file_path = decryptFilePath(myEncryptedFilePath)

# print(decrypted_file_path)
    