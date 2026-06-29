CREATE DATABASE IF NOT EXISTS `tongjinoti_test`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `tongjinoti_test`;

CREATE TABLE IF NOT EXISTS `attachments` (
  `id` int NOT NULL,
  `filename` varchar(500) DEFAULT NULL,
  `file_location_remote` varchar(500) DEFAULT NULL,
  `file_location_local` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nickname` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(100) NOT NULL,
  `created_at` datetime NOT NULL,
  `receive_noti` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username_UNIQUE` (`nickname`),
  UNIQUE KEY `email_UNIQUE` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `notifications` (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `relations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `notification_id` int NOT NULL,
  `attachment_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_n_idx` (`notification_id`),
  KEY `fk_a_idx` (`attachment_id`),
  CONSTRAINT `fk_a` FOREIGN KEY (`attachment_id`) REFERENCES `attachments` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_n` FOREIGN KEY (`notification_id`) REFERENCES `notifications` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `login_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `login_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `uid_idx` (`user_id`),
  CONSTRAINT `uid` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
