CREATE TABLE IF NOT EXISTS temporary_super_admin_grants (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  granted_by INT NOT NULL,
  duration_hours INT NOT NULL DEFAULT 24,
  starts_at DATETIME NOT NULL,
  expires_at DATETIME NOT NULL,
  revoked_at DATETIME NULL DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_user_expires (user_id, expires_at),
  KEY idx_granted_by (granted_by),
  KEY idx_active_window (starts_at, expires_at, revoked_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
