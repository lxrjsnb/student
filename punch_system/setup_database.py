from db_env import get_db_connection, get_db_name, get_server_connection


DB_NAME = get_db_name()


def ensure_database_exists():
    conn = get_server_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        print(f"✓ 数据库 `{DB_NAME}` 已存在/已创建")
    finally:
        cursor.close()
        conn.close()


def ensure_users_table(cursor):
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nickname VARCHAR(50) DEFAULT '',
            username VARCHAR(50) NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('user', 'admin', 'super_admin') DEFAULT 'user',
            is_online TINYINT(1) NOT NULL DEFAULT 0,
            is_admin TINYINT(1) NOT NULL DEFAULT 0,
            last_login_at DATETIME NULL DEFAULT NULL,
            last_logout_at DATETIME NULL DEFAULT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uniq_users_username (username)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''
    )
    print("✓ users 表已存在/已创建")

def setup_database():
    try:
        ensure_database_exists()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("正在连接数据库...")

        ensure_users_table(cursor)

        def column_exists(column_name):
            cursor.execute(
                '''
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = 'users'
                  AND COLUMN_NAME = %s
                ''',
                (DB_NAME, column_name)
            )
            return cursor.fetchone() is not None

        def table_exists(table_name):
            cursor.execute(
                '''
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = %s
                ''',
                (DB_NAME, table_name)
            )
            return cursor.fetchone() is not None

        def table_column_exists(table_name, column_name):
            cursor.execute(
                '''
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = %s
                  AND COLUMN_NAME = %s
                ''',
                (DB_NAME, table_name, column_name)
            )
            return cursor.fetchone() is not None
        
        # 1. 创建 user_sessions 表（用于30天免登录）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                token VARCHAR(255) NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP NULL DEFAULT NULL,
                UNIQUE KEY uniq_token (token),
                KEY idx_user_id (user_id),
                KEY idx_expires_at (expires_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        print("✓ user_sessions 表创建成功")

        # 2. 检查并创建 admin_applications 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_applications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                username VARCHAR(50) NOT NULL,
                reason TEXT NOT NULL,
                status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_status (status),
                INDEX idx_user_id (user_id),
                CONSTRAINT fk_admin_applications_user
                    FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        print("✓ admin_applications 表创建成功")
        
        # 3. 检查并添加 role 字段到 users 表
        cursor.execute('''
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'role'
        ''', (DB_NAME,))
        role_column = cursor.fetchone()
        
        if not role_column:
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN role ENUM('user', 'admin', 'super_admin') DEFAULT 'user'
            ''')
            print("✓ users 表添加 role 字段成功")
        else:
            print("✓ users 表已有 role 字段")

        # 3.1 users 表字段补全：nickname、is_online、is_admin、last_login_at、last_logout_at、created_at
        if not column_exists('nickname'):
            cursor.execute("ALTER TABLE users ADD COLUMN nickname VARCHAR(50) DEFAULT '' AFTER id")
            print("✓ users 表添加 nickname 字段成功")
        else:
            print("✓ users 表已有 nickname 字段")

        if not column_exists('is_online'):
            cursor.execute("ALTER TABLE users ADD COLUMN is_online TINYINT(1) NOT NULL DEFAULT 0 AFTER password")
            print("✓ users 表添加 is_online 字段成功")
        else:
            print("✓ users 表已有 is_online 字段")

        if not column_exists('is_admin'):
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0 AFTER is_online")
            print("✓ users 表添加 is_admin 字段成功")
        else:
            print("✓ users 表已有 is_admin 字段")

        if not column_exists('last_login_at'):
            cursor.execute("ALTER TABLE users ADD COLUMN last_login_at DATETIME NULL DEFAULT NULL AFTER is_admin")
            print("✓ users 表添加 last_login_at 字段成功")
        else:
            print("✓ users 表已有 last_login_at 字段")

        if not column_exists('last_logout_at'):
            cursor.execute("ALTER TABLE users ADD COLUMN last_logout_at DATETIME NULL DEFAULT NULL AFTER last_login_at")
            print("✓ users 表添加 last_logout_at 字段成功")
        else:
            print("✓ users 表已有 last_logout_at 字段")

        if not column_exists('created_at'):
            cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER last_logout_at")
            print("✓ users 表添加 created_at 字段成功")
        else:
            print("✓ users 表已有 created_at 字段")

        # 3.2 尝试调整字段顺序（忽略失败：不同版本/已有约束可能不支持）
        try:
            cursor.execute("""
                ALTER TABLE users
                  MODIFY COLUMN id INT NOT NULL AUTO_INCREMENT FIRST,
                  MODIFY COLUMN nickname VARCHAR(50) DEFAULT '' AFTER id,
                  MODIFY COLUMN username VARCHAR(50) NOT NULL AFTER nickname,
                  MODIFY COLUMN password VARCHAR(255) NOT NULL AFTER username,
                  MODIFY COLUMN is_online TINYINT(1) NOT NULL DEFAULT 0 AFTER password,
                  MODIFY COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0 AFTER is_online,
                  MODIFY COLUMN last_login_at DATETIME NULL DEFAULT NULL AFTER is_admin,
                  MODIFY COLUMN last_logout_at DATETIME NULL DEFAULT NULL AFTER last_login_at,
                  MODIFY COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER last_logout_at
            """)
            print("✓ users 表字段顺序调整完成")
        except Exception as e:
            print(f"⚠ users 表字段顺序调整跳过: {e}")

        # 3.3 username 唯一索引
        try:
            cursor.execute('CREATE UNIQUE INDEX uniq_users_username ON users (username)')
            print("✓ users 表添加 username 唯一索引成功")
        except Exception:
            print("✓ users 表已有 username 唯一索引（或已存在同名索引）")
        
        # 4. 将 admin 用户设置为超级管理员
        cursor.execute('UPDATE users SET role = "super_admin" WHERE username = "admin"')
        print("✓ admin 用户已设置为超级管理员")

        # 4.1 同步 is_admin 字段
        try:
            cursor.execute('UPDATE users SET is_admin = 1 WHERE role IN ("admin", "super_admin")')
            cursor.execute('UPDATE users SET is_admin = 0 WHERE role NOT IN ("admin", "super_admin") OR role IS NULL')
            print("✓ users 表 is_admin 字段已同步")
        except Exception as e:
            print(f"⚠ 同步 is_admin 失败: {e}")

        # 4.2 同步 is_online：存在未过期 session 的用户视为在线
        try:
            cursor.execute('UPDATE users SET is_online = 0')
            cursor.execute(
                '''
                UPDATE users u
                JOIN (
                    SELECT DISTINCT user_id
                    FROM user_sessions
                    WHERE expires_at >= NOW()
                ) s ON s.user_id = u.id
                SET u.is_online = 1
                '''
            )
            print("✓ users 表 is_online 已根据 user_sessions 同步")
        except Exception as e:
            print(f"⚠ 同步 is_online 失败: {e}")

        # 4.3 打卡记录表：每次打卡一条记录（可一天多次，可多次加分）
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS punch_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                score_add DECIMAL(10,2) NOT NULL DEFAULT 0.30,
                punch_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                approved TINYINT(1) NOT NULL DEFAULT 0,
                is_urge TINYINT(1) NOT NULL DEFAULT 0,
                KEY idx_user_time (user_id, punch_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            '''
        )
        print("✓ punch_records 表创建成功（如不存在）")

        # 兼容旧表：补齐字段
        if table_exists('punch_records') and not table_column_exists('punch_records', 'score_add'):
            cursor.execute('ALTER TABLE punch_records ADD COLUMN score_add DECIMAL(10,2) NOT NULL DEFAULT 0.30 AFTER user_id')
            print("✓ punch_records 表添加 score_add 字段成功")
        elif table_exists('punch_records'):
            try:
                cursor.execute('ALTER TABLE punch_records MODIFY COLUMN score_add DECIMAL(10,2) NOT NULL DEFAULT 0.30')
            except Exception:
                pass
        if table_exists('punch_records') and not table_column_exists('punch_records', 'punch_time'):
            cursor.execute('ALTER TABLE punch_records ADD COLUMN punch_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP')
            print("✓ punch_records 表添加 punch_time 字段成功")
        elif table_exists('punch_records'):
            try:
                cursor.execute('ALTER TABLE punch_records MODIFY COLUMN punch_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP')
            except Exception:
                pass

        if table_exists('punch_records') and not table_column_exists('punch_records', 'approved'):
            cursor.execute('ALTER TABLE punch_records ADD COLUMN approved TINYINT(1) NOT NULL DEFAULT 0')
            print("✓ punch_records 表添加 approved 字段成功")

        if table_exists('punch_records') and not table_column_exists('punch_records', 'is_urge'):
            cursor.execute('ALTER TABLE punch_records ADD COLUMN is_urge TINYINT(1) NOT NULL DEFAULT 0')
            print("✓ punch_records 表添加 is_urge 字段成功")

        # 兼容旧数据：将 NULL 的 score_add 补齐为 0.30
        try:
            cursor.execute('UPDATE punch_records SET score_add = 0.30 WHERE score_add IS NULL')
        except Exception:
            pass
        
        # 4. 查看当前用户状态
        cursor.execute('SELECT id, username, role FROM users ORDER BY id LIMIT 10')
        users = cursor.fetchall()
        print("\n当前用户列表（前10个）：")
        for user in users:
            print(f"  ID: {user['id']}, 用户名: {user['username']}, 角色: {user.get('role', 'user')}")
        
        # 5. 查看当前申请列表
        cursor.execute('SELECT * FROM admin_applications ORDER BY created_at DESC LIMIT 5')
        applications = cursor.fetchall()
        print("\n当前管理员申请列表（前5个）：")
        if applications:
            for app in applications:
                print(f"  ID: {app['id']}, 用户: {app['username']}, 状态: {app['status']}, 时间: {app['created_at']}")
        else:
            print("  暂无申请")
        
        conn.commit()
        print("\n✅ 数据库设置完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    setup_database()
