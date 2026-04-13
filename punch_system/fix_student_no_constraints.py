from db_env import get_db_connection


def assign_reserved_student_nos(cursor):
    def _assign_by_query(label, reserved_no, sql, params=()):
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if not rows:
            print(f'未找到需要设置学号 {reserved_no} 的{label}账号')
            return False
        if len(rows) > 1:
            print(f'{label}账号匹配到多条记录，跳过自动设置学号 {reserved_no}')
            return False

        user = rows[0]
        current = str(user.get('student_no') or '').strip()
        if current == reserved_no:
            print(f'{label}账号学号已是 {reserved_no}')
            return True
        if current:
            print(f'{label}账号已存在学号 {current}，跳过自动改为 {reserved_no}')
            return True

        cursor.execute('SELECT id, username FROM users WHERE student_no = %s LIMIT 1', (reserved_no,))
        owner = cursor.fetchone()
        if owner and int(owner.get('id') or 0) != int(user.get('id') or 0):
            print(f"学号 {reserved_no} 已被账号 {owner.get('username') or owner.get('id')} 占用，跳过为{label}账号自动设置")
            return False

        cursor.execute('UPDATE users SET student_no = %s WHERE id = %s', (reserved_no, user['id']))
        print(f"已为{label}账号 {user.get('username') or user['id']} 设置学号 {reserved_no}")
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


def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print('正在规范 users.student_no 数据...')
        cursor.execute("UPDATE users SET student_no = NULL WHERE student_no IS NOT NULL AND TRIM(student_no) = ''")
        assign_reserved_student_nos(cursor)
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
