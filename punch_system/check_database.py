import pymysql

DB_CONFIG = {
    'host': '123.56.88.190',
    'port': 3306,
    'user': 'student',
    'password': '123456',
    'database': 'student',
    'cursorclass': pymysql.cursors.DictCursor
}

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("=== 检查users表结构 ===")
    cursor.execute("DESCRIBE users")
    columns = cursor.fetchall()
    for column in columns:
        print(f"  {column['Field']}: {column['Type']}")
    
    print("\n=== 检查users表数据 ===")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    for user in users:
        print(f"  ID: {user['id']}, Username: {user['username']}, Role: {user.get('role', 'N/A')}, Online: {user.get('is_online', 0)}")
    
    print("\n=== 检查admin_applications表数据 ===")
    cursor.execute("SELECT * FROM admin_applications")
    applications = cursor.fetchall()
    for app in applications:
        print(f"  ID: {app['id']}, User ID: {app['user_id']}, Username: {app['username']}, Status: {app['status']}")
    
    conn.close()
    print("\n✅ 检查完成！")
    
except Exception as e:
    print(f"❌ 错误: {e}")
