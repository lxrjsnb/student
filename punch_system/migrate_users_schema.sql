-- users 表字段设计（按顺序）：
-- id、nickname、username、password（暗码/哈希）、is_online、is_admin、last_login_at、last_logout_at、created_at

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS nickname VARCHAR(50) DEFAULT '' AFTER id,
  ADD COLUMN IF NOT EXISTS is_online TINYINT(1) NOT NULL DEFAULT 0 AFTER password,
  ADD COLUMN IF NOT EXISTS is_admin TINYINT(1) NOT NULL DEFAULT 0 AFTER is_online,
  ADD COLUMN IF NOT EXISTS last_login_at DATETIME NULL DEFAULT NULL AFTER is_admin,
  ADD COLUMN IF NOT EXISTS last_logout_at DATETIME NULL DEFAULT NULL AFTER last_login_at,
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER last_logout_at;

-- 尝试调整字段顺序（对已存在字段也生效）
ALTER TABLE users
  MODIFY COLUMN id INT NOT NULL AUTO_INCREMENT FIRST,
  MODIFY COLUMN nickname VARCHAR(50) DEFAULT '' AFTER id,
  MODIFY COLUMN username VARCHAR(50) NOT NULL AFTER nickname,
  MODIFY COLUMN password VARCHAR(255) NOT NULL AFTER username,
  MODIFY COLUMN is_online TINYINT(1) NOT NULL DEFAULT 0 AFTER password,
  MODIFY COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0 AFTER is_online,
  MODIFY COLUMN last_login_at DATETIME NULL DEFAULT NULL AFTER is_admin,
  MODIFY COLUMN last_logout_at DATETIME NULL DEFAULT NULL AFTER last_login_at,
  MODIFY COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER last_logout_at;

-- username 唯一约束（如果你已存在唯一索引，可忽略执行错误）
ALTER TABLE users ADD UNIQUE KEY uniq_users_username (username);

