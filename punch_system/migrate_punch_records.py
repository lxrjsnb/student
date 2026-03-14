import pymysql

DB_CONFIG = {
    'host': '123.56.88.190',
    'port': 3306,
    'user': 'student',
    'password': '123456',
    'database': 'student',
    'cursorclass': pymysql.cursors.DictCursor,
}


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        '''
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME = %s
        ''',
        (DB_CONFIG['database'], table_name),
    )
    return cursor.fetchone() is not None


def _column_exists(cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(
        '''
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        ''',
        (DB_CONFIG['database'], table_name, column_name),
    )
    return cursor.fetchone() is not None


def migrate():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        print("正在迁移 punch_records 表...")

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS punch_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                score_add DECIMAL(10,2) NOT NULL DEFAULT 0.30,
                punch_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                KEY idx_user_time (user_id, punch_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            '''
        )
        print("✓ punch_records 表已存在/已创建")

        if _table_exists(cursor, 'punch_records') and not _column_exists(cursor, 'punch_records', 'score_add'):
            cursor.execute(
                'ALTER TABLE punch_records ADD COLUMN score_add DECIMAL(10,2) NOT NULL DEFAULT 0.30 AFTER user_id'
            )
            print("✓ punch_records.score_add 字段已添加")
        elif _table_exists(cursor, 'punch_records'):
            try:
                cursor.execute(
                    'ALTER TABLE punch_records MODIFY COLUMN score_add DECIMAL(10,2) NOT NULL DEFAULT 0.30'
                )
            except Exception:
                pass

        if _table_exists(cursor, 'punch_records') and not _column_exists(cursor, 'punch_records', 'punch_time'):
            cursor.execute(
                'ALTER TABLE punch_records ADD COLUMN punch_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP'
            )
            print("✓ punch_records.punch_time 字段已添加")
        elif _table_exists(cursor, 'punch_records'):
            try:
                cursor.execute(
                    'ALTER TABLE punch_records MODIFY COLUMN punch_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP'
                )
            except Exception:
                pass

        try:
            cursor.execute('UPDATE punch_records SET score_add = 0.30 WHERE score_add IS NULL')
        except Exception:
            pass

        conn.commit()
        print("✅ punch_records 迁移完成！")
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    migrate()
