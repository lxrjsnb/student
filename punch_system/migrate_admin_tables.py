import pymysql
import sys

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        database='punch_system',
        charset='utf8mb4'
    )

def execute_sql_file(sql_file_path):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for statement in statements:
            try:
                if 'ALTER TABLE users ADD COLUMN IF NOT EXISTS role' in statement:
                    cursor.execute('SHOW COLUMNS FROM users LIKE "role"')
                    if cursor.fetchone():
                        print("跳过（role列已存在）: ALTER TABLE users ADD COLUMN role...")
                        continue
                    else:
                        cursor.execute('ALTER TABLE users ADD COLUMN role ENUM("user", "admin", "super_admin") DEFAULT "user"')
                        print("执行成功: ALTER TABLE users ADD COLUMN role...")
                elif 'UPDATE users SET role = "super_admin" WHERE username = "admin"' in statement:
                    cursor.execute('UPDATE users SET role = "super_admin" WHERE username = "admin"')
                    print("执行成功: UPDATE users SET role...")
                else:
                    cursor.execute(statement)
                    print(f"执行成功: {statement[:50]}...")
            except pymysql.Error as e:
                if "Duplicate column name" in str(e):
                    print(f"跳过（列已存在）: {statement[:50]}...")
                elif "Duplicate entry" in str(e):
                    print(f"跳过（记录已存在）: {statement[:50]}...")
                else:
                    print(f"执行失败: {e}")
        
        conn.commit()
        print("\n数据库迁移完成！")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    execute_sql_file('create_admin_tables.sql')
