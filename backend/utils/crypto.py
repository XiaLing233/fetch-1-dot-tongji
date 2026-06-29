# 解密部分

import os
import base64 # base64 编码
from urllib.parse import unquote_plus # URL 解码
from Crypto.PublicKey import RSA # RSA 加密
from Crypto.Cipher import PKCS1_v1_5 # RSA 加密
from Crypto.Cipher import AES # AES 加密
from Crypto.Util.Padding import unpad

# 密钥路径和 AES 参数（从环境变量读取）
PRIVATE_KEY_PATH = os.getenv('RSA_PRIVATE_KEY_PATH', 'keys/web_login_pri.pem')
AES_KEY = os.getenv('AES_KEY', '')
AES_IV = os.getenv('AES_IV', '')

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
    # URL 解码 → base64 解码 → AES 解密 → 去填充 → 去 URI 编码
    encrypted_file_path = unquote_plus(encrypted_file_path)
    encrypted_file_path = base64.b64decode(encrypted_file_path)
    cipher = AES.new(AES_KEY.encode(), AES.MODE_CBC, AES_IV.encode())
    decrypted_file_path = cipher.decrypt(encrypted_file_path)
    decrypted_file_path = unpad(decrypted_file_path, 16)
    decrypted_file_path = unquote_plus(decrypted_file_path.decode())
    return decrypted_file_path
