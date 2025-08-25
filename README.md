# 同济大学 1 系统通知存档与提醒

## Archived

不再打算研发。项目未来还可以提升的空间是：

1. 支持通过非同济邮箱接收通知；
2. 通过国内的服务器加速爬取 1 系统时文件的传输速度。

备份站可能会在某一天关停。

## 网站部署在

[同济大学通知公告备份站](https://1.xialing.icu)

## 需求

同济大学 [1 系统](https://1.tongji.edu.cn)是同济大学的教学信息管理平台，发布教务教学的通知公告。发布的通知较为重要，但是过了一段时间便会下架，不给人回看的可能。目标：查询并存档 1 系统的消息通知。

> 本文档仅供学习交流使用，不应用于破坏计算机系统的用途。本文档作者不对任何因使用本文档而产生的后果承担责任。

## 如何运行本项目

1. 将项目 clone 下来;
2. 在 `python-part` 文件夹下补充 `config.ini`, 模板参见 `python-part/README.md`;
3. 补充 `config.ini` 中的敏感信息, 如 AES, COS, 邮箱, 密码等;
4. 在 MySQL 中创建数据库, 具体命令如下所示;
5. 安装必要的依赖. 在前端文件夹中运行 `npm install`, 在后端文件夹中**创建虚拟环境(建议)**, **激活虚拟环境后**运行 `pip install -r requirements.txt`;
6. 运行 `fetchNewEvents.py` 爬取通知, 写入数据库;
7. 在后端文件夹运行 `flask run --port=8001` 启动后端, 在前端文件夹运行 `npm run dev` 启动前端;
8. 用浏览器打开前端地址, 便可运行本项目(tips: 在非 https 环境下, 可能要将 `app.py` 中的 `PRODUCTION` 置 `False`, 同时按需修改凭证过期时间, 默认是 10 秒);
9. 进阶设置: 定时爬虫, 日志记录, 服务器部署...

```sql
-- 创建数据库的命令
CREATE DATABASE `tongjinoti`;
USE tongjinoti;

CREATE TABLE `attachments` (
  `id` int NOT NULL,
  `filename` varchar(500) DEFAULT NULL,
  `file_location_remote` varchar(500) DEFAULT NULL,
  `file_location_local` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `login_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `login_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `uid_idx` (`user_id`),
  CONSTRAINT `uid` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=149 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `notifications` (
  `id` int NOT NULL,
  `title` varchar(500) NOT NULL,
  `content` longtext NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `invalid_top_time` datetime DEFAULT '1970-01-01 00:00:00',
  `create_id` varchar(45) NOT NULL,
  `create_user` varchar(45) NOT NULL,
  `create_time` datetime NOT NULL,
  `publish_time` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `relations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `notification_id` int NOT NULL,
  `attachment_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_n_idx` (`notification_id`),
  KEY `fk_a_idx` (`attachment_id`),
  CONSTRAINT `fk_a` FOREIGN KEY (`attachment_id`) REFERENCES `attachments` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_n` FOREIGN KEY (`notification_id`) REFERENCES `notifications` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=59 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nickname` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(100) NOT NULL,
  `created_at` datetime NOT NULL,
  `receive_noti` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username_UNIQUE` (`nickname`),
  UNIQUE KEY `email_UNIQUE` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```
