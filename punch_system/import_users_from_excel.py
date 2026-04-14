from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re

import openpyxl
import pymysql
from werkzeug.security import generate_password_hash

from db_env import get_db_connection


ROLE_MAP = {
    '部员': 'user',
    '部长': 'admin',
    '主席': 'super_admin',
}

STUDENT_NO_OVERRIDES = {
    ('任锦程', '软件工程242003', '202420050421'): '202420040319',
}

TABLES_TO_TRUNCATE = [
    'admin_applications',
    'delegation_applications',
    'phone_change_requests',
    'punch_records',
    'temporary_super_admin_grants',
    'user_sessions',
    'activities',
    'users',
]


@dataclass
class UserRow:
    row_number: int
    name: str
    class_name: str
    student_no: str
    department: str
    phone: str
    level: str
    role: str
    username: str


def _text(value) -> str:
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def _load_excel(excel_path: Path) -> tuple[list[UserRow], list[str]]:
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb.active

    users: list[UserRow] = []
    seen_usernames: set[str] = set()
    seen_student_nos: set[str] = set()
    fixes: list[str] = []

    for row_number, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        name = _text(row[0] if len(row) > 0 else None)
        class_name = _text(row[1] if len(row) > 1 else None)
        student_no = _text(row[2] if len(row) > 2 else None)
        department = _text(row[3] if len(row) > 3 else None)
        phone = _text(row[4] if len(row) > 4 else None)
        level = _text(row[5] if len(row) > 5 else None)

        if not any([name, class_name, student_no, department, phone, level]):
            continue

        if not all([name, class_name, student_no, department, phone, level]):
            raise ValueError(f'第 {row_number} 行存在空字段，无法导入')

        role = ROLE_MAP.get(level)
        if role is None:
            raise ValueError(f'第 {row_number} 行职级 `{level}` 无法映射到系统角色')

        username = name
        if username in seen_usernames:
            raise ValueError(f'第 {row_number} 行姓名 `{name}` 重复，无法作为唯一用户名导入')

        if student_no in seen_student_nos:
            inferred_student_no = STUDENT_NO_OVERRIDES.get(
                (name, class_name, student_no)
            ) or _infer_student_no(class_name=class_name, student_no=student_no)
            if inferred_student_no == student_no or inferred_student_no in seen_student_nos:
                raise ValueError(
                    f'第 {row_number} 行学号 `{student_no}` 重复，且无法自动推断修正值'
                )
            fixes.append(
                f'第 {row_number} 行学号 `{student_no}` 与前文重复，按班级 `{class_name}` 推断修正为 `{inferred_student_no}`'
            )
            student_no = inferred_student_no

        seen_usernames.add(username)
        seen_student_nos.add(student_no)
        users.append(
            UserRow(
                row_number=row_number,
                name=name,
                class_name=class_name,
                student_no=student_no,
                department=department,
                phone=phone,
                level=level,
                role=role,
                username=username,
            )
        )

    if not users:
        raise ValueError('Excel 中没有可导入的数据')

    return users, fixes


def _infer_student_no(*, class_name: str, student_no: str) -> str:
    normalized_student_no = _text(student_no)
    if len(normalized_student_no) < 8:
        return normalized_student_no

    major_name = re.sub(r'\d+$', '', class_name).strip()
    major_code = {
        '计算机': '01',
        '软件工程': '04',
        '物联网': '05',
        '智能科学': '06',
    }.get(major_name)
    if not major_code:
        return normalized_student_no

    return normalized_student_no[:6] + major_code + normalized_student_no[8:]


def _truncate_tables(cursor: pymysql.cursors.Cursor) -> None:
    cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
    try:
        for table in TABLES_TO_TRUNCATE:
            cursor.execute(f'TRUNCATE TABLE `{table}`')
    finally:
        cursor.execute('SET FOREIGN_KEY_CHECKS = 1')


def _import_users(users: list[UserRow], default_password: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        _truncate_tables(cursor)

        password_hash = generate_password_hash(default_password)
        sql = '''
            INSERT INTO users (
                nickname,
                username,
                password,
                student_no,
                class_name,
                department,
                phone,
                role,
                is_admin
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        params = [
            (
                user.name,
                user.username,
                password_hash,
                user.student_no,
                user.class_name,
                user.department,
                user.phone,
                user.role,
                1 if user.role in {'admin', 'super_admin'} else 0,
            )
            for user in users
        ]
        cursor.executemany(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def _print_summary(users: list[UserRow], fixes: list[str], default_password: str) -> None:
    role_counts = {'user': 0, 'admin': 0, 'super_admin': 0}
    for user in users:
        role_counts[user.role] += 1

    print(f'导入完成: {len(users)} 条用户')
    print(f'默认密码: {default_password}')
    print(f'角色分布: user={role_counts["user"]}, admin={role_counts["admin"]}, super_admin={role_counts["super_admin"]}')
    if fixes:
        print('自动修正:')
        for fix in fixes:
            print(f'  - {fix}')


def main() -> None:
    parser = argparse.ArgumentParser(description='清空数据库并从 Excel 导入用户数据')
    parser.add_argument('excel_path', type=Path, help='Excel 文件路径')
    parser.add_argument('--default-password', default='Aa123456', help='导入用户的统一初始密码')
    args = parser.parse_args()

    users, fixes = _load_excel(args.excel_path)
    _import_users(users, args.default_password)
    _print_summary(users, fixes, args.default_password)


if __name__ == '__main__':
    main()
