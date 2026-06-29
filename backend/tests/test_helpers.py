"""工具函数测试：IP 限流、邮件验证、加密解密。"""

import time
import pytest

from utils.helpers import (
    checkEmailFormat,
    generateVerificationCode,
    triedTooManyTimes,
)
from utils import crypto as myDecrypt


class TestEmailFormat:
    def test_valid_email(self):
        assert checkEmailFormat('student@tongji.edu.cn') is True

    def test_invalid_domain(self):
        assert checkEmailFormat('student@gmail.com') is False

    def test_invalid_format(self):
        assert checkEmailFormat('not-an-email') is False

    def test_subdomain(self):
        assert checkEmailFormat('user.name_test@tongji.edu.cn') is True


class TestVerificationCode:
    def test_generates_6_digits(self):
        code = generateVerificationCode()
        assert len(code) == 6
        assert code.isdigit()


class TestTriedTooManyTimes:
    def test_default_zero(self, app):
        with app.test_request_context():
            assert triedTooManyTimes() is False


class TestPasswordDecryption:
    def test_decrypt_known_ciphertext(self):
        """验证 RSA 解密能正常运行（需要 keys/ 目录存在）。"""
        import os
        key_path = os.getenv('RSA_PRIVATE_KEY_PATH', 'keys/web_login_pri.pem')
        if not os.path.exists(key_path):
            pytest.skip("RSA key not found")

        # 用公钥加密一段明文
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_v1_5
        import base64
        from urllib.parse import quote

        with open(key_path.replace('pri', 'pub'), 'r') as f:
            pub_key = RSA.import_key(f.read())
        cipher = PKCS1_v1_5.new(pub_key)
        encrypted = base64.b64encode(cipher.encrypt(b'test123'))
        encoded = quote(encrypted.decode())

        result = myDecrypt.decryptPassword(encoded)
        assert result == 'test123'


class TestFilepathDecryption:
    def test_decrypt_filepath(self):
        """验证 AES 文件路径解密。"""
        import os
        if not os.getenv('AES_KEY'):
            pytest.skip("AES key not configured")

        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        import base64
        from urllib.parse import quote

        key = os.getenv('AES_KEY', '').encode()
        iv = os.getenv('AES_IV', '').encode()
        plaintext = '/path/to/file.pdf'

        padded = pad(plaintext.encode(), 16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
        encoded = quote(encrypted)

        result = myDecrypt.decryptFilePath(encoded)
        assert result == plaintext
