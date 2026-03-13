import pymysql

def get_db_connection():
    return pymysql.connect(
        host='123.56.88.190',
        port=3306,
        user='student',
        password='123456',
        database='student',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def setup_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("正在连接数据库...")
        
        # 1. 检查并创建 admin_applications 表
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
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        print("✓ admin_applications 表创建成功")
        
        # 2. 检查并添加 role 字段到 users 表
        cursor.execute('''
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'student' 
            AND TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'role'
        ''')
        role_column = cursor.fetchone()
        
        if not role_column:
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN role ENUM('user', 'admin', 'super_admin') DEFAULT 'user'
            ''')
            print("✓ users 表添加 role 字段成功")
        else:
            print("✓ users 表已有 role 字段")
        
        # 3. 将 admin 用户设置为超级管理员
        cursor.execute('UPDATE users SET role = "super_admin" WHERE username = "admin"')
        print("✓ admin 用户已设置为超级管理员")
        
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
