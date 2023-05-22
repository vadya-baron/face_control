CREATE DATABASE IF NOT EXISTS `face_control` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `face_control`;

CREATE TABLE IF NOT EXISTS `face_control`.`employees` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `external_id` int(11) NULL,
  `date_create` datetime NOT NULL,
  `date_update` datetime NULL,
  `display_name` varchar(255) NOT NULL,
  `employee_position` varchar(255) NULL,
  `status` tinyint(2) NOT NULL DEFAULT '1',
  KEY `index_employees_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `face_control`.`employees_vectors` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `employee_id` int(11) unsigned NOT NULL,
  `face_vector` blob NOT NULL,
  `face_recognize_vector` blob NOT NULL,
  FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE
) ENGINE='InnoDB' DEFAULT CHARSET=utf8mb4 COLLATE 'utf8mb4_general_ci';

CREATE TABLE IF NOT EXISTS `face_control`.`employee_visits` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `employee_id` int(11) unsigned NOT NULL,
  `visit_date` datetime NOT NULL,
  `direction` tinyint NOT NULL DEFAULT '0' COMMENT '0 = entered, 1 = came out',
  KEY `index_date_desc` (`visit_date` DESC),
  KEY `index_employee` (`employee_id`),
  KEY `index_direction` (`direction`),
  FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;