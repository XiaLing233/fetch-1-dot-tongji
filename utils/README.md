# config.ini 格式

```ini
[Account]
sno = 1234567   # 学号
passwd = 1234567 # 明文密码

[Js]
rsa_url = https://iam.tongji.edu.cn/xxx # rsa 公钥所在位置
aes_url = https://1.tongji.edu.cn/xxx # aes iv 和公钥所在位置

[Storage]
path = ./data # 附件文件存储的位置
```

在本文件夹下新建一个 `config.ini`，把学号和密码替换为自己的，即可实现登录功能。
