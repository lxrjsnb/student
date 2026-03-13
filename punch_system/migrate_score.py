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
    
    print("正在添加score字段...")
    cursor.execute("ALTER TABLE users ADD COLUMN score DECIMAL(10,2) DEFAULT 0.0")
    print("score字段添加成功！")
    
    cursor.execute("UPDATE users SET score = 0.0 WHERE score IS NULL")
    print("现有用户的分数已初始化为0")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("数据库迁移完成！")
    
except pymysql.err.OperationalError as e:
    if e.args[0] == 1060:
        print("score字段已存在，无需重复添加")
    else:
        print(f"数据库错误: {e}")
except Exception as e:
    print(f"错误: {e}")
