# 说明

## config.ini 格式

```ini
[Account]
sno = 2365472
passwd = 

; [Js]
; deprecated
; rsa_url = https://iam.tongji.edu.cn/idp/themes/default/js/main/crypt.js?date=202211232020
; aes_url = https://1.tongji.edu.cn/static/js/app.e03cb41897b900e3dd87.js

[Sql]
; 登录 SQL 的账户信息
host = localhost
user = cirno
password = 
database = tongjinoti
port = 3306
charset = utf8mb4

[Table]
; SQL 通知表格
n_table_name = notifications
n_id = id
n_title = title
n_content = content
n_start_time = start_time
n_end_time = end_time
n_invalid_top_time = invalid_top_time
n_create_id = create_id
n_create_user = create_user
n_create_time = create_time
n_publish_time = publish_time

; 附件表格
a_table_name = attachments
a_id = id
a_filename = filename
a_file_location_remote = file_location_remote
a_file_location_local = file_location_local

; 通知和附件的关系表
r_table_name = relations
r_notification_id = notification_id
r_attachment_id = attachment_id

# 用户表
u_id = id
u_table_name = users
u_nickname = nickname
u_email = email
u_password = password
u_created_at = created_at
u_receive_noti = receive_noti

# 登录日志表
l_table_name = login_logs
l_user_id = user_id
l_ip_address = ip_address
l_login_at = login_at

[Storage]
attachment_path = ./1dot  ; 腾讯 COS 中的云目录名
img_path = ./data/background  ; 本地背景图片文件夹

[Proxy]
; deprecated
; 一般不需要代理
http = socks5h://localhost:9527
https = socks5h://localhost:9527

[RSA]
; RSA 加密的密钥路径
private_key_path = keys/web_login_pri.pem
public_key_path = keys/web_login_pub.pem

[AES]
key = 
iv = 

[JWT]
; jwt 用来进行访问控制
secret_key = 

[Email]
; 通知邮件相关
smtp_server = smtpdm.aliyun.com
smtp_port = 465
smtp_username = cirno@xialing.icu
smtp_password = 
smtp_username_batch = notify@xialing.icu
smtp_password_batch = 

[Session]
; session 在后端保存验证码等信息
secret_key =

[Flag]
; 是否发送邮件、是否使用代理
send_email = 1
use_proxy = 0

[IMAP]
; 接收邮件相关，涉及到 fetchNewEvents 脚本
qq_emailaddr = 
qq_grantcode = 
server_domain = imap.qq.com
server_port = 993

[QCloud]
; Tencent COS
region = ap-tokyo 
secret_id = 
secret_key = 
bucket_name =  
domain = static.xialing.icu
```

在本文件夹下新建一个 `config.ini`，把学号和密码替换为自己的，即可实现登录功能。

## 依赖

参见 `requirements.txt`。

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
