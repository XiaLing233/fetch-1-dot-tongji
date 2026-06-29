"""
腾讯验证码校验模块
用于验证前端返回的验证码 ticket 和 randstr 是否有效
"""

import json
import configparser
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.captcha.v20190722 import captcha_client, models


class CaptchaChecker:
    """验证码验证类"""
    
    def __init__(self, config_path='config.ini'):
        """
        初始化验证码验证器
        :param config_path: 配置文件路径
        """
        # 读取配置文件
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        
        self.secret_id = config['Captcha']['secret_id']
        self.secret_key = config['Captcha']['secret_key']
        self.app_secret_key = config['Captcha']['app_secret_key']
        self.captcha_app_id = 190271421
        
        # 初始化客户端
        self._init_client()
    
    def _init_client(self):
        """初始化腾讯云客户端"""
        try:
            # 实例化认证对象
            cred = credential.Credential(self.secret_id, self.secret_key)
            
            # 实例化http选项
            http_profile = HttpProfile()
            http_profile.endpoint = "captcha.tencentcloudapi.com"
            
            # 实例化client选项
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            
            # 实例化client对象
            self.client = captcha_client.CaptchaClient(cred, "", client_profile)
        except Exception as e:
            print(f"[ERROR] 初始化验证码客户端失败: {e}")
            raise
    
    def verify_captcha(self, ticket, randstr, user_ip):
        """
        验证验证码
        :param ticket: 前端回调函数返回的用户验证票据
        :param randstr: 前端回调函数返回的随机字符串
        :param user_ip: 用户的外网IP地址
        :return: (是否验证成功, 错误信息)
        """
        try:
            # 实例化请求对象
            req = models.DescribeCaptchaResultRequest()
            params = {
                "CaptchaType": 9,  # 验证码类型，固定为9
                "Ticket": ticket,
                "UserIp": user_ip,
                "Randstr": randstr,
                "CaptchaAppId": self.captcha_app_id,
                "AppSecretKey": self.app_secret_key
            }
            req.from_json_string(json.dumps(params))
            
            # 调用接口验证（所有票据都必须通过腾讯API验证）
            resp = self.client.DescribeCaptchaResult(req)
            
            # 解析响应
            resp_dict = json.loads(resp.to_json_string())
            
            # CaptchaCode: 1-验证成功, 其他值-验证失败
            captcha_code = resp_dict.get('CaptchaCode', 0)
            captcha_msg = resp_dict.get('CaptchaMsg', '未知错误')
            
            if captcha_code == 1:
                # 验证成功
                return True, "验证成功"
            else:
                # 验证失败
                return False, f"验证失败: {captcha_msg} (Code: {captcha_code})"
                
        except TencentCloudSDKException as err:
            error_msg = f"验证码SDK异常: {err}"
            print(f"[ERROR] {error_msg}")
            # SDK异常时一律拒绝，不放行任何票据（包括容灾票据）
            return False, error_msg
        except Exception as e:
            error_msg = f"验证码验证异常: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return False, error_msg


# 全局实例（懒加载）
_captcha_checker_instance = None


def get_captcha_checker():
    """获取验证码验证器单例"""
    global _captcha_checker_instance
    if _captcha_checker_instance is None:
        _captcha_checker_instance = CaptchaChecker()
    return _captcha_checker_instance


def verify_captcha(ticket, randstr, user_ip):
    """
    验证验证码的快捷函数
    :param ticket: 前端回调函数返回的用户验证票据
    :param randstr: 前端回调函数返回的随机字符串
    :param user_ip: 用户的外网IP地址
    :return: (是否验证成功, 错误信息)
    """
    checker = get_captcha_checker()
    return checker.verify_captcha(ticket, randstr, user_ip)