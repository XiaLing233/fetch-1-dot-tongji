# 和腾讯云 COS 有关的文件

import configparser
from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.streambody import StreamBody
from qcloud_cos import CosServiceError
from urllib3.response import HTTPResponse

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

class CosUpload():
    def __init__(self):
        region = CONFIG["QCloud"]["region"]
        secret_id = CONFIG["QCloud"]["secret_id"]
        secret_key = CONFIG["QCloud"]["secret_key"]
        self.bucket_name = CONFIG["QCloud"]["bucket_name"]

        config = CosConfig(Region=region, 
                           SecretId=secret_id, 
                           SecretKey=secret_key
                           )
        
        self.client = CosS3Client(config)
    

    def upload_from_bytes(self, content: bytes, object_key):
        """
        :param content: 要上传的内容, 二进制形式
        :param object_key: 目标路径, 以`{文件夹}/{文件名}`的形式
        """
        flag = self.client.put_object(Bucket=self.bucket_name,
                               Body=content,
                               Key=object_key)
        print(flag)


    def download_as_bytes(self, target_link) -> bytes:
        """
        :param target_link: 要访问的文件在 COS 中的路径
        :return: 原始字节形式的内容
        """
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=target_link)
            stream_body: StreamBody = response['Body']
            raw_stream: HTTPResponse = stream_body.get_raw_stream()
            content = raw_stream.read()
            print("Downloaded content size:", len(content))
            return content
        
        except CosServiceError as e:
            processed = e.get_digest_msg()

            # print(processed)
            raise Exception("下载时发生异常: <br>"
                            f"请求的资源为: {processed['resource']}<br>"
                            f"错误码: {processed['code']}<br>"
                            f"详细信息: {processed['message']}")
    
    def generate_temporary_url(self, key):
        """
        生成临时具有权限的下载链接
        """
        url = self.client.get_presigned_download_url(Bucket=self.bucket_name,
                                                     Key=key)
        print(url)

        return url


if __name__ == "__main__":
    # 上传测试
    # with open("./packages/upload_to_cos.py", 'rb') as f:
    #     foo = qCloud()
    #     foo.upload_from_bytes(f, "backup/upload_to_cos.py")
    
    # 下载测试
    # try:
    #     foo = CosUpload()
    #     foo.download_as_bytes(target_link="backup/upload_to_cos1.py")
    # except Exception as e:
    #     print(e)

    # 生成链接测试
    foo = CosUpload()
    foo.generate_temporary_url(key="backup/upload_to_cos.py")