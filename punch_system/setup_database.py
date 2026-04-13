import ast
import json
import re
from pathlib import Path

from db_env import get_db_connection, get_db_name, get_server_connection


DB_NAME = get_db_name()

def load_default_activities_seed():
    seed_path = Path(__file__).resolve().parents[1] / 'punch_system_vue' / 'src' / 'lib' / 'activities.js'
    if not seed_path.exists():
        return []

    text = seed_path.read_text(encoding='utf-8')
    start = text.find('[')
    end = text.rfind(']')
    if start < 0 or end < 0 or end <= start:
        return []

    body = text[start:end + 1]
    body = re.sub(r'(\b[A-Za-z_][A-Za-z0-9_]*\b)\s*:', r'"\1":', body)
    try:
        parsed = ast.literal_eval(body)
    except Exception:
        return []
    return parsed if isinstance(parsed, list) else []


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
            student_no VARCHAR(32) NULL DEFAULT NULL,
            class_name VARCHAR(64) DEFAULT '',
            department VARCHAR(64) DEFAULT '',
            phone VARCHAR(32) DEFAULT '',
            role ENUM('user', 'admin', 'super_admin') DEFAULT 'user',
            is_online TINYINT(1) NOT NULL DEFAULT 0,
            is_admin TINYINT(1) NOT NULL DEFAULT 0,
            last_login_at DATETIME NULL DEFAULT NULL,
            last_logout_at DATETIME NULL DEFAULT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uniq_users_username (username),
            UNIQUE KEY uniq_users_student_no (student_no)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''
    )
    print("✓ users 表已存在/已创建")


def assign_reserved_student_nos(cursor):
    def _assign_by_query(label, reserved_no, sql, params=()):
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if not rows:
            print(f"✓ 未找到需要设置学号 {reserved_no} 的{label}账号")
            return False
        if len(rows) > 1:
            print(f"⚠ {label}账号匹配到多条记录，跳过自动设置学号 {reserved_no}")
            return False

        user = rows[0]
        current = str(user.get('student_no') or '').strip()
        if current == reserved_no:
            print(f"✓ {label}账号学号已是 {reserved_no}")
            return True
        if current:
            print(f"⚠ {label}账号已存在学号 {current}，跳过自动改为 {reserved_no}")
            return True

        cursor.execute('SELECT id, username FROM users WHERE student_no = %s LIMIT 1', (reserved_no,))
        owner = cursor.fetchone()
        if owner and int(owner.get('id') or 0) != int(user.get('id') or 0):
            print(
                f"⚠ 学号 {reserved_no} 已被账号 {owner.get('username') or owner.get('id')} 占用，"
                f"跳过为{label}账号自动设置"
            )
            return False

        cursor.execute('UPDATE users SET student_no = %s WHERE id = %s', (reserved_no, user['id']))
        print(f"✓ 已为{label}账号 {user.get('username') or user['id']} 设置学号 {reserved_no}")
        return True

    _assign_by_query(
        'admin',
        '1',
        '''
        SELECT id, username, student_no
        FROM users
        WHERE username = %s
        LIMIT 2
        ''',
        ('admin',)
    )

    assigned_super = _assign_by_query(
        'super_admin',
        '2',
        '''
        SELECT id, username, student_no
        FROM users
        WHERE username IN (%s, %s)
        ORDER BY CASE WHEN username = %s THEN 0 ELSE 1 END, id ASC
        LIMIT 2
        ''',
        ('superadmin', 'super_admin', 'superadmin')
    )
    if assigned_super:
        return

    _assign_by_query(
        'super_admin',
        '2',
        '''
        SELECT id, username, student_no
        FROM users
        WHERE role = %s
        ORDER BY id ASC
        LIMIT 2
        ''',
        ('super_admin',)
    )

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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS phone_change_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                username VARCHAR(50) NOT NULL,
                current_phone VARCHAR(32) DEFAULT '',
                requested_phone VARCHAR(32) NOT NULL,
                approved TINYINT(1) NOT NULL DEFAULT 0,
                is_urge TINYINT(1) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_approved (approved),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        print("✓ phone_change_requests 表创建成功")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                slug VARCHAR(128) NOT NULL,
                title VARCHAR(120) NOT NULL,
                category VARCHAR(64) NOT NULL DEFAULT '',
                frequency VARCHAR(64) NOT NULL DEFAULT '',
                duration VARCHAR(64) NOT NULL DEFAULT '',
                difficulty VARCHAR(32) NOT NULL DEFAULT '',
                scene VARCHAR(128) NOT NULL DEFAULT '',
                summary TEXT,
                tagline VARCHAR(255) NOT NULL DEFAULT '',
                description TEXT,
                highlights_json LONGTEXT,
                steps_json LONGTEXT,
                tips_json LONGTEXT,
                cover_image LONGTEXT,
                sort_order INT NOT NULL DEFAULT 0,
                status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'approved',
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_by INT NULL DEFAULT NULL,
                reviewed_by INT NULL DEFAULT NULL,
                reviewed_at DATETIME NULL DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_slug (slug),
                KEY idx_active_sort (is_active, sort_order, id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        print("✓ activities 表创建成功")

        cursor.execute('''
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        print("✓ temporary_super_admin_grants 表创建成功")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS delegation_applications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                username VARCHAR(50) NOT NULL,
                reason TEXT NOT NULL,
                status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
                is_urge TINYINT(1) NOT NULL DEFAULT 0,
                reviewed_by INT NULL DEFAULT NULL,
                reviewed_at DATETIME NULL DEFAULT NULL,
                grant_id INT NULL DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                KEY idx_user_status (user_id, status),
                KEY idx_status_created (status, created_at),
                KEY idx_reviewed_by (reviewed_by)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        print("✓ delegation_applications 表创建成功")

        if not table_column_exists('activities', 'status'):
            cursor.execute("ALTER TABLE activities ADD COLUMN status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'approved' AFTER sort_order")
            print("✓ activities 表添加 status 字段成功")
        else:
            print("✓ activities 表已有 status 字段")

        if not table_column_exists('activities', 'reviewed_by'):
            cursor.execute("ALTER TABLE activities ADD COLUMN reviewed_by INT NULL DEFAULT NULL AFTER created_by")
            print("✓ activities 表添加 reviewed_by 字段成功")
        else:
            print("✓ activities 表已有 reviewed_by 字段")

        if not table_column_exists('activities', 'reviewed_at'):
            cursor.execute("ALTER TABLE activities ADD COLUMN reviewed_at DATETIME NULL DEFAULT NULL AFTER reviewed_by")
            print("✓ activities 表添加 reviewed_at 字段成功")
        else:
            print("✓ activities 表已有 reviewed_at 字段")
        
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

        # 3.1 users 表字段补全：nickname、student_no、class_name、department、phone、is_online、is_admin、last_login_at、last_logout_at、created_at
        if not column_exists('nickname'):
            cursor.execute("ALTER TABLE users ADD COLUMN nickname VARCHAR(50) DEFAULT '' AFTER id")
            print("✓ users 表添加 nickname 字段成功")
        else:
            print("✓ users 表已有 nickname 字段")

        if not column_exists('student_no'):
            cursor.execute("ALTER TABLE users ADD COLUMN student_no VARCHAR(32) NULL DEFAULT NULL AFTER password")
            print("✓ users 表添加 student_no 字段成功")
        else:
            print("✓ users 表已有 student_no 字段")

        if not column_exists('class_name'):
            cursor.execute("ALTER TABLE users ADD COLUMN class_name VARCHAR(64) DEFAULT '' AFTER student_no")
            print("✓ users 表添加 class_name 字段成功")
        else:
            print("✓ users 表已有 class_name 字段")

        if not column_exists('department'):
            cursor.execute("ALTER TABLE users ADD COLUMN department VARCHAR(64) DEFAULT '' AFTER class_name")
            print("✓ users 表添加 department 字段成功")
        else:
            print("✓ users 表已有 department 字段")

        if not column_exists('phone'):
            cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(32) DEFAULT '' AFTER department")
            print("✓ users 表添加 phone 字段成功")
        else:
            print("✓ users 表已有 phone 字段")

        if not column_exists('is_online'):
            cursor.execute("ALTER TABLE users ADD COLUMN is_online TINYINT(1) NOT NULL DEFAULT 0 AFTER phone")
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
                  MODIFY COLUMN student_no VARCHAR(32) NULL DEFAULT NULL AFTER password,
                  MODIFY COLUMN class_name VARCHAR(64) DEFAULT '' AFTER student_no,
                  MODIFY COLUMN department VARCHAR(64) DEFAULT '' AFTER class_name,
                  MODIFY COLUMN phone VARCHAR(32) DEFAULT '' AFTER department,
                  MODIFY COLUMN is_online TINYINT(1) NOT NULL DEFAULT 0 AFTER phone,
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

        try:
            cursor.execute("UPDATE users SET student_no = NULL WHERE student_no IS NOT NULL AND TRIM(student_no) = ''")
            assign_reserved_student_nos(cursor)
            cursor.execute('CREATE UNIQUE INDEX uniq_users_student_no ON users (student_no)')
            print("✓ users 表添加 student_no 唯一索引成功")
        except Exception as e:
            print(f"⚠ users 表 student_no 唯一索引跳过: {e}")
        
        # 4. 保持角色字段与当前权限定义一致，不再强制覆盖 admin 用户角色
        print("✓ 跳过 admin 用户角色强制覆盖")

        # 4.1 同步 is_admin 字段
        try:
            cursor.execute('UPDATE users SET is_admin = 1 WHERE role IN ("admin", "super_admin")')
            cursor.execute('UPDATE users SET is_admin = 0 WHERE role NOT IN ("admin", "super_admin") OR role IS NULL')
            print("✓ users 表 is_admin 字段已同步")
        except Exception as e:
            print(f"⚠ 同步 is_admin 失败: {e}")

        try:
            cursor.execute('SELECT COUNT(*) AS total FROM activities')
            total = int((cursor.fetchone() or {}).get('total') or 0)
            if total == 0:
                defaults = load_default_activities_seed()
                inserted = 0
                for index, item in enumerate(defaults):
                    cursor.execute(
                        '''
                        INSERT IGNORE INTO activities (
                            slug, title, category, frequency, duration, difficulty, scene,
                            summary, tagline, description, highlights_json, steps_json, tips_json,
                            cover_image, sort_order, status, is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'approved', 1)
                        ''',
                        (
                            item.get('id') or f'activity-{index + 1}',
                            item.get('title') or '',
                            item.get('category') or '',
                            item.get('frequency') or '',
                            item.get('duration') or '',
                            item.get('difficulty') or '',
                            item.get('scene') or '',
                            item.get('summary') or '',
                            item.get('tagline') or '',
                            item.get('description') or '',
                            json.dumps(item.get('highlights') or [], ensure_ascii=False),
                            json.dumps(item.get('steps') or [], ensure_ascii=False),
                            json.dumps(item.get('tips') or [], ensure_ascii=False),
                            item.get('cover_image') or '',
                            index,
                        )
                    )
                    inserted += int(cursor.rowcount or 0)
                print(f"✓ activities 表已写入默认活动 {inserted} 条")
            else:
                print("✓ activities 表已有内容")
        except Exception as e:
            print(f"⚠ 初始化 activities 数据失败: {e}")

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

        if table_exists('punch_records') and not table_column_exists('punch_records', 'approved_by'):
            cursor.execute('ALTER TABLE punch_records ADD COLUMN approved_by INT NULL DEFAULT NULL')
            print("✓ punch_records 表添加 approved_by 字段成功")

        if table_exists('punch_records') and not table_column_exists('punch_records', 'approved_at'):
            cursor.execute('ALTER TABLE punch_records ADD COLUMN approved_at DATETIME NULL DEFAULT NULL')
            print("✓ punch_records 表添加 approved_at 字段成功")

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
