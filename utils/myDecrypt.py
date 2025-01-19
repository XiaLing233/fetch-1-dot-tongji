# 解密部分

import configparser # 读取配置文件
import base64 # base64 编码
from urllib.parse import unquote_plus # URL 解码
from Crypto.PublicKey import RSA # RSA 加密
from Crypto.Cipher import PKCS1_v1_5 # RSA 加密

# 读取配置文件

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

# 私钥

PRIVATE_KEY_PATH = CONFIG['RSA']['private_key_path']

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

# 测试
# decrypted_password = decryptPassword("fuu%2BO%2BiGv5LmsKfDSDBvQ8HCx7ZLVushbVdMs1kTTdWU%2FP09p6bmQMnVo573gE%2FotHMGQcRf9cLXsnyTUu9bSeqnuAM3Y6HWuTzGSWxPeGEii%2FS27Eokir5IF%2BoB1K%2F79Y4MAw4Mr%2FEyT1V7mYVTB9aA1FXX8wIGMzv8A%2FpUWCCBiu89RlZNZsKuMsfxqxyFh3ji1B8BoiG50N2QVVYzgTJbqryGMhgPnUsL8uvGenOpip9d5yS4T%2FA6ONdG4Kjf2YGhrhGAEaBr5C6y0ezX3%2FV2qJR17GZkQbtw1ReCqdDyIBlnB0oCNoVYOLxZiCMd%2BLFYZA2YraI1eNkvq5yHxw%3D%3D")
# print(decrypted_password)