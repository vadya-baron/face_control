CREATE DATABASE IF NOT EXISTS `face_control` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `face_control`;

CREATE TABLE IF NOT EXISTS `employee_visits` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `employee_id` int(11) NOT NULL,
  `visit_date` datetime NOT NULL,
  `direction` tinyint NOT NULL DEFAULT '0' COMMENT '0 = entered, 1 = came out',
  PRIMARY KEY (`id`),
  KEY `index_date_desc` (`visit_date` DESC),
  KEY `index_employee` (`employee_id`),
  KEY `index_direction` (`direction`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;