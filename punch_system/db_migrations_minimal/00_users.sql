CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nickname VARCHAR(50) DEFAULT '',
  username VARCHAR(50) NOT NULL,
  password VARCHAR(255) NOT NULL,
  is_online TINYINT(1) NOT NULL DEFAULT 0,
  is_admin TINYINT(1) NOT NULL DEFAULT 0,
  last_login_at DATETIME NULL DEFAULT NULL,
  last_logout_at DATETIME NULL DEFAULT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  role ENUM('user', 'admin', 'super_admin') DEFAULT 'user',
  UNIQUE KEY uniq_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
