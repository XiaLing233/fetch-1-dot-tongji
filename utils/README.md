# 说明

## config.ini 格式

```ini
[Account]
sno = 1234567   # 学号
passwd = 1234567 # 明文密码

[Js]
rsa_url = https://iam.tongji.edu.cn/xxx # rsa 公钥所在位置
aes_url = https://1.tongji.edu.cn/xxx # aes iv 和公钥所在位置

[Sql]
host = 
user = 
password = 
database = 
port = 
charset = 

[Table]
# Notification table
n_table_name = 
n_id = 
n_title = 
n_content = 
n_start_time = 
n_end_time = 
n_invalid_top_time =
n_create_id = 
n_create_user = 
n_create_time = 
n_publish_time = 

# Attachment table
a_table_name = 
a_id = 
a_filename = 
a_file_location_remote = 
a_file_location_local = 

# Relation table
r_table_name = 
r_notification_id = 
r_attachment_id = 

[Storage]
path = ./data # 附件文件存储的位置

# 使用代理来转发请求，如果不需要，不用填写这个字段
# 并把所有网络请求的 proxies=xxx 删除
# 文件开头的代理配置部分也要删除
[Proxy]
http = socks5h://...
https = socks5h://...

```

在本文件夹下新建一个 `config.ini`，把学号和密码替换为自己的，即可实现登录功能。

## 依赖版本

pip 版本是 23.1.2，升级之后可能有问题，导入包会失效..玄学

Package     |           Version | 手动 pip 安装? |
-------------|------------------- | -------- |
certifi           |     2024.12.14 | |
charset-normalizer |     3.4.1      |  |
configparser      |     7.1.0      | √ |
idna              |     3.10       | |
mysql-connector-python | 9.1.0     | √ |
pip               |     23.1.2     | |
pycryptodome      |     3.21.0     | √ |
PySocks           |     1.7.1      | √ |
requests          |     2.32.3     | √ |
setuptools        |     65.5.0     | |
urllib3           |     2.3.0      | |
