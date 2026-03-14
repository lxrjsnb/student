-- 在远程数据库中创建管理员申请表和添加角色字段

-- 创建管理员申请表
CREATE TABLE IF NOT EXISTS admin_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 检查并添加role字段
SET @dbname = DATABASE();
SET @tablename = 'users';
SET @columnname = 'role';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_schema = @dbname)
      AND (table_name = @tablename)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' ENUM("user", "admin", "super_admin") DEFAULT "user"')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 将现有的admin用户设置为超级管理员
UPDATE users SET role = 'super_admin' WHERE username = 'admin';

-- 创建打卡记录表：每次打卡一条记录（可一天多次，可多次加分）
CREATE TABLE IF NOT EXISTS punch_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    score_add DECIMAL(10,2) NOT NULL DEFAULT 0.30,
    punch_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_time (user_id, punch_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
