-- 创建管理员申请表
CREATE TABLE IF NOT EXISTS admin_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 修改用户表，添加角色字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS role ENUM('user', 'admin', 'super_admin') DEFAULT 'user';

-- 将现有的admin用户设置为超级管理员
UPDATE users SET role = 'super_admin' WHERE username = 'admin';