# config.ini 格式

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
```

在本文件夹下新建一个 `config.ini`，把学号和密码替换为自己的，即可实现登录功能。
