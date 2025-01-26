# 说明

## config.ini 格式

```ini
[Account]
sno = 1234567   # 学号
passwd = 1234567 # 明文密码

; [Js]
; rsa_url = https://iam.tongji.edu.cn/xxx # rsa 公钥所在位置
; aes_url = https://1.tongji.edu.cn/xxx # aes iv 和公钥所在位置

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

# User table
u_table_name = 
u_nickname = 
u_email = 
u_password = 
u_created_at = 
u_receive_noti = 

# Login log table
l_table_name = 
l_user_id = 
l_ip_address = 
l_login_at = 

[Storage]
attachment_path = ./data # 附件文件存储的位置
img_path = ./data/background

# 使用代理来转发请求，如果不需要，不用填写这个字段
# 并把所有网络请求的 proxies=xxx 删除
# 文件开头的代理配置部分也要删除
[Proxy]
http = socks5h://...
https = socks5h://...

[RSA]
private_key_path = 
public_key_path = 

[AES]
key = 
iv = 

[JWT]
secret_key = 

[Email]
smtp_server = 
smtp_port = 
smtp_username = 
smtp_password = 
smtp_username_batch = 
smtp_password_batch = 

[Session]
secret_key = 
```

在本文件夹下新建一个 `config.ini`，把学号和密码替换为自己的，即可实现登录功能。

## 依赖版本

pip 版本是 23.1.2，升级之后可能有问题，导入包会失效..玄学

Package     |           Version | 手动 pip 安装? |
-------------|------------------- | -------- |
argon2-cffi | 23.1.0 | ✅ |
argon2-cffi-bindings | 21.2.0 | |
blinker | 1.9.0 | |
cachelib | 0.13.0 | |
certifi | 2024.12.14 | |
cffi | 1.17.1 | |
charset-normalizer | 3.4.1 | |
click | 8.1.8 | |
colorama | 0.4.6 | |
configparser | 7.1.0 | ✅ |
Flask | 3.1.0 | ✅ |
Flask-Cors | 5.0.0 | ✅ |
Flask-JWT-Extended | 4.7.1 | ✅ |
Flask-Mail | 0.10.0 | ✅ |
Flask-Session | 0.8.0 | ✅ |
idna | 3.10 | |
itsdangerous | 2.2.0 | |
Jinja2 | 3.1.5 | |
MarkupSafe | 3.0.2 | |
msgspec | 0.19.0 | |
mysql-connector-python | 9.1.0 | ✅ |
pip | 23.1.2 | |
pycparser | 2.22 | |
pycryptodome | 3.21.0 | ✅ |
PyJWT | 2.10.1 | |
PySocks | 1.7.1 | ✅ |
pytz | 2024.2 | ✅ |
redis | 5.2.1 | ✅ |
requests | 2.32.3 | ✅ |
setuptools | 65.5.0 | |
urllib3 | 2.3.0 | |
Werkzeug | 3.1.3 | |

## api

### `/api/getBackgroundImg`

`GET`

> 返回

```json
{
    "code": 200,
    "msg": "成功",
    "data": "base64编码的图片"
}
```

### `/api/register`

`POST`

> 传入：

```json
{
    "xl_email": "cirno@tongji.edu.cn",
    "xl_password": "RSA加密后的密码",
    "xl_veri_code": "233333"
}
```

> 返回

```json
{
    "code": 200,
    "msg": "成功",
}
```

### `/api/login`

`POST`

> 传入：

```json
{
    "xl_email": "cirno@tongji.edu.cn",
    "xl_password": "RSA加密后的密码"
}
```

> 返回

```json
{
    "code": 200,
    "msg": "成功",
}
```

### `/api/recovery`

`POST`

> 传入：

```json
{
    "xl_email": "cirno@tongji.edu.cn",
    "xl_password": "RSA加密后的密码"
}
```

> 返回

```json
{
    "code": 200,
    "msg": "成功",
}
```

### `/api/sendVerificationEmail`

`POST`

> 传入：

```json
{
    "xl_email": "cirno@tongji.edu.cn",
}
```

> 返回

```json
{
    "code": 200,
    "msg": "成功",
}
```

### `/api/sendRecoveryEmail`

`POST`

> 传入：

```json
{
    "xl_email": "cirno@tongji.edu.cn",
}
```

> 返回

```json
{
    "code": 200,
    "msg": "成功",
}
```

### 以下需要验证 token

### `/api/changePassword`

`POST`

> 传入：

```json
{
    "xl_email": "cirno@tongji.edu.cn",
    "xl_newpassword": "加密后的新密码"
}
```

> 返回

```json
{
    "code": 200,
    "msg": "成功",
}
```

### `/api/findMyCommonMsgPublish`（本方法不需要验证 token）

`GET`

> 返回

```json
{
    "code": 200,
    "msg": "成功",
    "data": [
        {
        "id": 2204,
        "title": "关于2024-2025学年第二学期本科生、研究生及继续教育（本科）教材选用情况的公示",
        "startTime": "2025-01-15 00:00:00.0",
        "endTime": "2025-01-22 00:00:00.0",
        "invalidTopTime": null,
        "createId": "12345",
        "createUser": "夏凌",
        "createTime": "2025-01-15 17:26:41.0",
        "publishTime": "2025-01-16 15:11:50.0",
        },
        {
            // ...
        },
        {
            // ...
        }
    ]
}
```

### `/api/findMyCommonMsgPublishById`

`POST`

> 传入：

```json
{
    "id": 2204
}
```

> 返回

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "title": "关于2024-2025学年第二学期本科生、研究生及继续教育（本科）教材选用情况的公示",
        "content": "<p>test</p>",
        "attachments": [
            {
                "fileName": "xxx",
                "fileType": "文档 | 表格 | 演示文稿 | 压缩包 | 其他"
            },
            {
                // ...
            },
        ]
        }
}
```

### `/api/downloadAttachmentByFileName`

`POST`

> 传入：

```json
{
    "fileLocation": "URI编码(base64编码(AES加密(文件名)))"
}
```

> 返回：

`二进制文件`

### `/api/getUserInfo`

`POST`

> 传入：

```json
{
    "xl_email": "cirno@tongji.edu.cn"
}
```

> 返回：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "xl_nickname": "琪露诺",
        "xl_email": "cirno@tongji.edu.cn",
        "xl_created_at": "2019年9月9日 09:09:09",
        "xl_receive_noti": "true | false"
    }
}
```

### `/api/toggleReceiveNoti`

`POST`

> 传入：

```json
{
    "xl_email": "cirno@tongji.edu.cn",
    "expect_option": "true | false"
}
```

> 返回：

```json
{
    "code": 200,
    "msg": "成功"
}
```
