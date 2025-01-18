# 同济大学 1 系统通知存档与提醒

## 需求

同济大学 [1 系统](https://1.tongji.edu.cn)是同济大学的教学信息管理平台，发布教务教学的通知公告。发布的通知较为重要，但是过了一段时间便会下架，不给人回看的可能。目标：查询并存档 1 系统的消息通知。

由于 `AES` 加密是对称加密，因此对获取秘钥的步骤进行了脱敏处理。

> 本文档仅供学习交流使用，不应用于破坏计算机系统的用途。本文档作者不对任何因使用本文档而产生的后果承担责任。

## 步骤

### 登录进 1 系统

1 系统的用户登录请求需要发送如下数据：

```json
{
    "j_username": 学号,
    "j_password": 使用 RSA 加密后的密码,
    "j_checkcode": "请输入验证码", // 如果没要求输入验证码，就是这个串
    "spAuthChainCode":一串写死的值,  
    "authnLcKey": 每个 SESSION 不一样, 
}
```

模拟登录时，用户名字段的处理是平凡的。

对密码的处理，首先要查找公钥的位置。注意到有如下函数会被调用：

```js
//RSA加密
function encryptByRSA(message) {
    var encrypt = new JSEncrypt();
    encrypt.setPublicKey('foo');
    var encrypted = encrypt.encrypt(message);
    return encrypted;
}
```

因此提取到了公钥，只需要本地同样进行 `RSA` 加密即可。

> 注意，`RSA` 加密每次获得的串不一定相同。且需要进行 `base64` 编码，便于传输。

`j_checkcode` 在不需要输入验证码时就是这样一个字符串。如果登录太频繁，需要输入验证码，到时候再进行优化。尽量不要登录太频繁。

`spAuthChainCode` 这个值我找了好久。一开始在页面的 `HTML` 骨架中，`value = ""`，但是在 `ajax` 发送请求前，对表格进行 `Serialize()` 后，却是非空值。切换了几个登录用户后判断，这是一个写死的值。后来在 Network 中找到了页面的原始内容，其中的一个脚本会对这一变量进行赋值。

```js
 $("#spAuthChainCode1").val('bar');
```

`authnLcKey` 会根据每次访问的请求来生成，就是 `URL` 中显示出来的部分。

### 数据库表格的设置

### 内容的爬取与存储

#### 爬取

获取消息列表 `findMyCommonMsgPublish`，后端返回的数据格式为：

```json
    // 后端返回的数据格式为 JSON
    '''
    {
        "code": 200,
        "msg": "",
        "data": {
            "pageNum_": 1,
            "pageSize_": 100,
            "total_": 24,
            "list": [
                {
                    "pageNum_": 1,                              // 【注意】这个字段没用，正确的 pageNum_ 是外层的
                    "pageSize_": 10,                            // 【注意】这个字段没用，正确的 pageSize_ 是外层的
                    "dic": true,
                    "id": 1271,                                 // id 应该是唯一的
                    "startTime": "2024-10-23 00:00:00.0",       // 发布时间
                    "endTime": "2025-10-01 00:00:00.0",         // 下架时间
                    "popStatus": "0",                           // 是否弹出
                    "topStatus": "1",                           // 是否置顶
                    "invalidTopTime": "2025-09-01 00:00:00.0",  // 到了什么时候停止置顶
                    "receiverPattern": "1",
                    "customGroupId": null,
                    "faceUser": "224,254,20,219,253",
                    "faceUserName": "全校",                     // 面向的对象，我能接收到的应该只有全校
                    "title": "教学部门首问视频会议室",          // 标题
                    "content": null,                            // 【注意】这里不会返回内容，需要用其他方法请求
                    "status": "3",
                    "workflowNo": null,
                    "tagStatus": "1",
                    "rejectReason": null,
                    "createId": "12345",                        // 发布信息的教师工号
                    "createUser": "夏凌",                       // 发布信息的教师姓名
                    "createTime": "2022-03-10 09:25:39.0",      // 创建消息的时间
                    "publishTime": "2022-03-10 09:26:11.0",     // 发布消息的时间
                    "groupIds": null,
                    "noTipsMsg": null,
                    "ids": null,
                    "type": null,
                    "editExplain": null,
                    "evidenceList": null,
                    "commonAttachmentList": null,
                    "porjIds": null,
                    "projIdStr": null,
                    "marReadStatus": true,
                    "publishStartTime": null,
                    "publishEndTime": null,
                    "receiverList": null,
                    "userCode": null
                }
            ]
        }
    }
    '''
```

获取一条消息的内容 `findMyCommonMsgPublishById`，后端返回的数据格式为：

```json
{
  "code": 200,
  "msg": "",
  "data": {
    "pageNum_": 1,
    "pageSize_": 10,
    "dic": true,
    "id": 2204,
    "startTime": "2025-01-15 00:00:00.0",
    "endTime": "2025-01-22 00:00:00.0",
    "popStatus": "0",
    "topStatus": "0",
    "invalidTopTime": null,
    "receiverPattern": "1",
    "customGroupId": "",
    "faceUser": null,
    "faceUserName": "全校",
    "title": "关于2024-2025学年第二学期本科生、研究生及继续教育（本科）教材选用情况的公示",
    "content": "<p>test</p>", // 这里存放了内容
    "status": "3",
    "workflowNo": null,
    "tagStatus": "1",
    "rejectReason": null,
    "createId": "12345",
    "createUser": "夏凌",
    "createTime": "2025-01-15 17:26:41.0",
    "publishTime": "2025-01-16 15:11:50.0",
    "groupIds": null,
    "noTipsMsg": null,
    "ids": null,
    "type": null,
    "editExplain": null,
    "evidenceList": null,
    "commonAttachmentList": [ // 这里存放了附件
      {
        "pageNum_": 1, // 忽略
        "pageSize_": 10, // 忽略
        "dic": true,
        "id": 10100, // 这个 id 应该是唯一的
        "relationId": 2204, // 和通知 id 的关系
        "relationType": "01",
        "fileName": "xxx",  // 文件名
        "fileLacation": "xxx", // 文件存放地址，需要进行加密后发送下载请求
        "uploadUserId": null,
        "uploadName": null,
        "uploadTime": null,
        "moduleName": null,
        "rateStatus": null,
        "processRate": null,
        "projId": null,
        "projIdI18n": ""
      },
    ],
    "porjIds": null,
    "projIdStr": null,
    "marReadStatus": false,
    "publishStartTime": null,
    "publishEndTime": null,
    "receiverList": null,
    "userCode": null
  }
}
```

进行附件的下载，关键在于下载链接的获取。注意到如下函数：

```js
// 处理下载文件，t 是文件位置，e 是文件名
handleDownloadfile: function(t, e) {
            t && Object(d.b)(t) // Object(d.b)(t) 是下方的 function s(e)
        },
```

```js
// e 是文件位置，获得 t 之后打开新窗口，可就开始文件下载，因此 t 是关键
function s(e) {
            var t = "/api/commonservice/obsfile/downloadfile?objectkey=" + n.a.encrypt(e);
            window.open(encodeURI(t))
        }
```

```js
e.encrypt = function(e) {
    var i = {
        iv: a,                      // 初始化向量 (IV)，这里的 `a` 应该是一个事先定义的值
        mode: n.mode.CBC,           // 加密模式为 CBC（Cipher Block Chaining）
        padding: n.pad.Pkcs7        // 填充模式为 PKCS7，常用于 CBC 模式中处理块大小不一致的问题
    }
    , r = encodeURIComponent(e)      // 将输入的文本 `e` 进行 URL 编码
    , o = n.AES.encrypt(String(r), t, i);  // 使用 AES 加密库对编码后的字符串 `r` 进行加密，`t` 是密钥，`i` 是配置项
    return encodeURIComponent(n.enc.Base64.stringify(o.ciphertext)); // 对加密后的密文进行 Base64 编码，并进行 URL 编码
}
```

> 注意：`AES` 加密是对称加密，因此不要公开秘钥和初始向量！！！

#### 存储

数据库表格的设置（采用下划线命名法）：

1. 通知表(notifications)
    * id：通知的唯一标识符。
    * title：通知的标题。
    * content：通知的内容，可能需要存储 HTML 格式的内容。
    * start_time：通知的发布时间。
    * end_time：通知的下架时间。
    * invalid_top_time: 什么时候停止置顶
    * status：通知的状态（例如发布、撤回等）。
    * created_id：发布人的工号。
    * created_user：发布人的姓名。
    * create_time：通知的创建时间。
    * publish_time：通知的发布时间。

2. 附件表(attachments)
    * id：附件的唯一标识符。
    * file_name：附件文件名。
    * file_location：附件的存储路径（文件地址），存储附件的实际位置。
    * upload_time：附件的上传时间。

3. 通知和附件的关系表(relations)
    * id：主键
    * notification_id：存放通知
    * attachment_id：存放附件

### 用户注册与登录的功能

#### 邮箱验证码注册

#### 账号密码登录

#### 邮箱登录

### 历史文件下载
