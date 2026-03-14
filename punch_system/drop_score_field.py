import pymysql


DB_CONFIG = {
    'host': '123.56.88.190',
    'port': 3306,
    'user': 'student',
    'password': '123456',
    'database': 'student',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}


def drop_score_column():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = 'users'
              AND COLUMN_NAME = 'score'
            ''',
            (DB_CONFIG['database'],)
        )
        if not cursor.fetchone():
            print("✓ users.score 不存在，无需删除")
            return

        cursor.execute('ALTER TABLE users DROP COLUMN score')
        conn.commit()
        print("✅ 已删除 users.score 字段")
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    drop_score_column()

