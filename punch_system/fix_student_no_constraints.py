from db_env import get_db_connection


def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print('正在规范 users.student_no 数据...')
        cursor.execute("UPDATE users SET student_no = NULL WHERE student_no IS NOT NULL AND TRIM(student_no) = ''")
        conn.commit()

        cursor.execute(
            '''
            SELECT student_no, COUNT(*) AS total
            FROM users
            WHERE student_no IS NOT NULL
            GROUP BY student_no
            HAVING COUNT(*) > 1
            ORDER BY total DESC, student_no ASC
            '''
        )
        duplicates = cursor.fetchall()
        if duplicates:
            print('发现重复学号，已阻止创建唯一索引：')
            for row in duplicates:
                student_no = row.get('student_no') or '<NULL>'
                total = row.get('total') or 0
                print(f'  学号: {student_no}，重复 {total} 次')

                cursor.execute(
                    '''
                    SELECT id, username, nickname, department
                    FROM users
                    WHERE student_no = %s
                    ORDER BY id ASC
                    ''',
                    (row.get('student_no'),)
                )
                for user in cursor.fetchall():
                    print(
                        f"    - id={user.get('id')}, username={user.get('username')}, "
                        f"nickname={user.get('nickname') or '-'}, department={user.get('department') or '-'}"
                    )
            raise SystemExit(1)

        cursor.execute(
            '''
            ALTER TABLE users
            MODIFY COLUMN student_no VARCHAR(32) NULL DEFAULT NULL
            '''
        )
        try:
            cursor.execute('CREATE UNIQUE INDEX uniq_users_student_no ON users (student_no)')
            print('已创建 uniq_users_student_no 唯一索引')
        except Exception as exc:
            message = str(exc)
            if 'Duplicate key name' in message or 'already exists' in message:
                print('uniq_users_student_no 唯一索引已存在')
            else:
                raise

        conn.commit()
        print('student_no 约束处理完成')
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
