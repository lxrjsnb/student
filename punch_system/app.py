import logging
import os
import re
import secrets
import sys
import threading
import time
import json
import ast
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from db_env import get_db_config, get_db_connection as get_pooled_db_connection, load_env_file

load_env_file()
os.environ.setdefault('FLASK_SKIP_DOTENV', '1')

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import pymysql
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization", "X-User-Role"]}})

def _get_log_level():
    level = (os.getenv('APP_LOG_LEVEL') or 'INFO').strip().upper()
    return getattr(logging, level, logging.INFO)

def _get_werkzeug_log_level():
    level = (os.getenv('WERKZEUG_LOG_LEVEL') or 'WARNING').strip().upper()
    return getattr(logging, level, logging.WARNING)

def _request_log_enabled():
    return (os.getenv('REQUEST_LOG_ENABLED') or '1').strip() == '1'

def _get_request_log_level():
    level = (os.getenv('REQUEST_LOG_LEVEL') or 'INFO').strip().upper()
    return getattr(logging, level, logging.INFO)

def _get_bool_env(name, default='0'):
    return (os.getenv(name) or default).strip() == '1'

logging.basicConfig(
    level=_get_log_level(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger(__name__)

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(_get_werkzeug_log_level())
werkzeug_logger.propagate = True

@app.before_request
def before_request():
    g.request_started_at = time.perf_counter()

@app.after_request
def after_request(response):
    if _request_log_enabled():
        started_at = getattr(g, 'request_started_at', None)
        duration_ms = ((time.perf_counter() - started_at) * 1000) if started_at else 0.0
        logger.log(
            _get_request_log_level(),
            "request method=%s path=%s status=%s duration_ms=%.1f ip=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            request.headers.get('X-Forwarded-For', request.remote_addr),
        )
    elif os.getenv('DEBUG_REQUEST_LOG') == '1':
        logger.debug(
            "response status=%s method=%s path=%s",
            response.status_code,
            request.method,
            request.path,
        )
    return response

DB_CONFIG = get_db_config()

SESSION_TTL_DAYS = 30
RELOGIN_AFTER_DAYS = int(os.getenv('RELOGIN_AFTER_DAYS') or '7')

class ReLoginRequired(Exception):
    pass

def get_db_connection():
    return get_pooled_db_connection()

_schema_checked = False
_schema_lock = threading.Lock()

def _ensure_schema_once():
    global _schema_checked
    if _schema_checked:
        return

    with _schema_lock:
        if _schema_checked:
            return

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                '''
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
                '''
            )
            cursor.execute(
                '''
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
                  KEY idx_user_id (user_id),
                  KEY idx_approved (approved),
                  KEY idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                '''
            )
            cursor.execute(
                '''
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
                '''
            )
            cursor.execute(
                '''
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
                '''
            )

            def _ensure_users_column(column_name, ddl_sql):
                cursor.execute("SHOW COLUMNS FROM users LIKE %s", (column_name,))
                if cursor.fetchone():
                    return
                cursor.execute(ddl_sql)

            _ensure_users_column(
                'is_online',
                "ALTER TABLE users ADD COLUMN is_online TINYINT(1) NOT NULL DEFAULT 0"
            )
            _ensure_users_column(
                'last_login_at',
                "ALTER TABLE users ADD COLUMN last_login_at DATETIME NULL DEFAULT NULL"
            )
            _ensure_users_column(
                'last_logout_at',
                "ALTER TABLE users ADD COLUMN last_logout_at DATETIME NULL DEFAULT NULL"
            )
            _ensure_users_column(
                'student_no',
                "ALTER TABLE users ADD COLUMN student_no VARCHAR(32) DEFAULT ''"
            )
            _ensure_users_column(
                'class_name',
                "ALTER TABLE users ADD COLUMN class_name VARCHAR(64) DEFAULT ''"
            )
            _ensure_users_column(
                'department',
                "ALTER TABLE users ADD COLUMN department VARCHAR(64) DEFAULT ''"
            )
            _ensure_users_column(
                'phone',
                "ALTER TABLE users ADD COLUMN phone VARCHAR(32) DEFAULT ''"
            )

            conn.commit()
            _schema_checked = True
        except Exception as e:
            logger.error(f"初始化数据库表结构失败（可忽略但会影响在线/登录时间更新）: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

_punch_schema_checked = False
_punch_schema_lock = threading.Lock()

def _ensure_punch_records_schema_once():
    global _punch_schema_checked
    if _punch_schema_checked:
        return

    with _punch_schema_lock:
        if _punch_schema_checked:
            return

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SHOW COLUMNS FROM punch_records LIKE 'approved'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE punch_records ADD COLUMN approved TINYINT(1) NOT NULL DEFAULT 0")
                # 兼容旧数据：新增 approved 字段时，历史记录默认视为已通过
                cursor.execute("UPDATE punch_records SET approved = 1 WHERE approved = 0")
                conn.commit()

            cursor.execute("SHOW COLUMNS FROM punch_records LIKE 'is_urge'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE punch_records ADD COLUMN is_urge TINYINT(1) NOT NULL DEFAULT 0")
                conn.commit()

            cursor.execute("SHOW COLUMNS FROM punch_records LIKE 'approved_by'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE punch_records ADD COLUMN approved_by INT NULL DEFAULT NULL")
                conn.commit()

            cursor.execute("SHOW COLUMNS FROM punch_records LIKE 'approved_at'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE punch_records ADD COLUMN approved_at DATETIME NULL DEFAULT NULL")
                conn.commit()
            _punch_schema_checked = True
        except Exception as e:
            logger.error(f"初始化 punch_records.approved 失败（可忽略但会影响审批）: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

_activities_schema_checked = False
_activities_schema_lock = threading.Lock()

def _load_default_activities_seed():
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
    except Exception as exc:
        logger.error(f"解析默认活动种子失败: {exc}")
        return []
    return parsed if isinstance(parsed, list) else []

def _serialize_activity_row(row):
    def _loads_list(value):
        if not value:
            return []
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    return {
        'id': row.get('slug') or str(row.get('id')),
        'db_id': row.get('id'),
        'title': row.get('title') or '',
        'category': row.get('category') or '',
        'frequency': row.get('frequency') or '',
        'duration': row.get('duration') or '',
        'difficulty': row.get('difficulty') or '',
        'scene': row.get('scene') or '',
        'summary': row.get('summary') or '',
        'tagline': row.get('tagline') or '',
        'description': row.get('description') or '',
        'highlights': _loads_list(row.get('highlights_json')),
        'steps': _loads_list(row.get('steps_json')),
        'tips': _loads_list(row.get('tips_json')),
        'cover_image': row.get('cover_image') or '',
        'status': row.get('status') or 'approved',
        'submitted_by': row.get('created_by'),
        'reviewed_by': row.get('reviewed_by'),
        'reviewed_at': row.get('reviewed_at').strftime('%Y-%m-%d %H:%M:%S') if row.get('reviewed_at') else None,
        'created_at': row.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if row.get('created_at') else None,
        'updated_at': row.get('updated_at').strftime('%Y-%m-%d %H:%M:%S') if row.get('updated_at') else None,
    }

def _seed_default_activities(cursor):
    defaults = _load_default_activities_seed()
    if not defaults:
        return 0

    inserted = 0
    for index, item in enumerate(defaults):
        cursor.execute(
            '''
            INSERT IGNORE INTO activities (
              slug, title, category, frequency, duration, difficulty, scene,
              summary, tagline, description, highlights_json, steps_json, tips_json,
              cover_image, sort_order, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
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
    return inserted

def _ensure_activities_schema_once():
    global _activities_schema_checked
    if _activities_schema_checked:
        return

    with _activities_schema_lock:
        if _activities_schema_checked:
            return

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''
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
                '''
            )
            def _ensure_activity_column(column_name, ddl_sql):
                cursor.execute("SHOW COLUMNS FROM activities LIKE %s", (column_name,))
                if cursor.fetchone():
                    return
                cursor.execute(ddl_sql)

            _ensure_activity_column(
                'status',
                "ALTER TABLE activities ADD COLUMN status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'approved' AFTER sort_order"
            )
            _ensure_activity_column(
                'reviewed_by',
                "ALTER TABLE activities ADD COLUMN reviewed_by INT NULL DEFAULT NULL AFTER created_by"
            )
            _ensure_activity_column(
                'reviewed_at',
                "ALTER TABLE activities ADD COLUMN reviewed_at DATETIME NULL DEFAULT NULL AFTER reviewed_by"
            )
            cursor.execute("UPDATE activities SET status = 'approved' WHERE status IS NULL OR status = ''")
            cursor.execute('SELECT COUNT(*) AS total FROM activities')
            total = int((cursor.fetchone() or {}).get('total') or 0)
            if total == 0:
                _seed_default_activities(cursor)
            conn.commit()
            _activities_schema_checked = True
        except Exception as exc:
            logger.error(f"初始化 activities 表失败: {exc}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

def _read_bearer_token():
    auth = request.headers.get('Authorization') or ''
    if not auth.startswith('Bearer '):
        return None
    token = auth.replace('Bearer ', '').strip()
    return token or None

def _encode_item_id(item_type, item_id):
    return f'{item_type}:{int(item_id)}'

def _parse_item_ids(raw_ids):
    punch_ids = []
    phone_ids = []

    for raw in raw_ids or []:
        if isinstance(raw, int):
            punch_ids.append(int(raw))
            continue

        text = str(raw or '').strip()
        if not text:
            continue

        if text.isdigit():
            punch_ids.append(int(text))
            continue

        item_type, sep, item_id = text.partition(':')
        if not sep or not item_id.isdigit():
            raise ValueError('invalid item id')

        item_id_int = int(item_id)
        if item_type == 'punch':
            punch_ids.append(item_id_int)
        elif item_type == 'phone':
            phone_ids.append(item_id_int)
        else:
            raise ValueError('invalid item type')

    return punch_ids, phone_ids

def _get_user_session(token):
    if not token:
        return None

    _ensure_schema_once()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT user_id, token, expires_at
            FROM user_sessions
            WHERE token = %s
            ''',
            (token,)
        )
        session = cursor.fetchone()
        if not session:
            return None

        expires_at = session.get('expires_at')
        if expires_at and expires_at < datetime.now():
            cursor.execute('DELETE FROM user_sessions WHERE token = %s', (token,))
            conn.commit()
            try:
                _mark_user_offline_if_no_active_sessions(session.get('user_id'))
            except Exception as e:
                logger.error(f"清理过期 session 后更新 is_online 失败: {e}")
            return None

        # 重新登录规则：若最后登录时间超过 7 天（可通过环境变量 RELOGIN_AFTER_DAYS 调整），则强制重新登录
        try:
            cursor.execute('SELECT last_login_at FROM users WHERE id = %s LIMIT 1', (session.get('user_id'),))
            user_row = cursor.fetchone() or {}
            last_login_at = user_row.get('last_login_at')
            if last_login_at and last_login_at < (datetime.now() - timedelta(days=RELOGIN_AFTER_DAYS)):
                cursor.execute('DELETE FROM user_sessions WHERE user_id = %s', (session.get('user_id'),))
                cursor.execute(
                    'UPDATE users SET is_online = 0, last_logout_at = %s WHERE id = %s',
                    (datetime.now(), session.get('user_id'))
                )
                conn.commit()
                raise ReLoginRequired()
        except ReLoginRequired:
            raise
        except Exception as e:
            logger.error(f"检查是否需要重新登录失败: {e}")

        cursor.execute('UPDATE user_sessions SET last_used_at = CURRENT_TIMESTAMP WHERE token = %s', (token,))
        # 只要存在有效 session，就认为在线（避免迁移后一直为0）
        cursor.execute('UPDATE users SET is_online = 1 WHERE id = %s AND is_online = 0', (session.get('user_id'),))
        conn.commit()
        return session
    finally:
        cursor.close()
        conn.close()

def _create_user_session(user_id):
    _ensure_schema_once()

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=SESSION_TTL_DAYS)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO user_sessions (user_id, token, expires_at)
            VALUES (%s, %s, %s)
            ''',
            (user_id, token, expires_at)
        )
        conn.commit()
        return token, expires_at
    finally:
        cursor.close()
        conn.close()

def _mark_user_online(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE users SET is_online = 1, last_login_at = %s WHERE id = %s',
            (datetime.now(), user_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def _mark_user_offline_if_no_active_sessions(user_id):
    if not user_id:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT COUNT(*) AS cnt
            FROM user_sessions
            WHERE user_id = %s AND expires_at >= %s
            ''',
            (user_id, datetime.now())
        )
        row = cursor.fetchone() or {}
        if int(row.get('cnt') or 0) > 0:
            return
        cursor.execute(
            'UPDATE users SET is_online = 0, last_logout_at = %s WHERE id = %s',
            (datetime.now(), user_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def _verify_password_and_maybe_upgrade(user_row, password_plain):
    stored = (user_row or {}).get('password')
    if not stored:
        return False

    # 兼容旧数据：历史上可能存的是明文密码
    if stored == password_plain:
        try:
            new_hash = generate_password_hash(password_plain)
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('UPDATE users SET password = %s WHERE id = %s', (new_hash, user_row['id']))
                conn.commit()
            finally:
                cursor.close()
                conn.close()
        except Exception as e:
            logger.error(f"升级 password 为哈希失败: {e}")
        return True

    try:
        return check_password_hash(stored, password_plain)
    except Exception:
        return False

def _validate_password_policy(user_row, password_plain):
    password_text = str(password_plain or '')
    if len(password_text) < 8 or len(password_text) > 64:
        return '密码长度需为 8-64 位。'
    if not re.search(r'[A-Z]', password_text) or not re.search(r'[a-z]', password_text) or not re.search(r'\d', password_text):
        return '密码至少包含大写字母、小写字母和数字。'

    normalized_password = password_text.casefold()
    personal_values = [
        user_row.get('username'),
        user_row.get('nickname'),
        user_row.get('student_no'),
        user_row.get('phone'),
        user_row.get('class_name'),
        user_row.get('department'),
    ]
    for value in personal_values:
        value_text = str(value or '').strip()
        if len(value_text) < 3:
            continue
        if value_text.casefold() in normalized_password:
            return '密码不得包含账号、学号、手机号等个人信息。'

    return None

def user_session_optional(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = _read_bearer_token()
        session = None
        try:
            session = _get_user_session(token) if token else None
        except ReLoginRequired:
            g.relogin_required = True
            session = None
        except Exception as e:
            logger.error(f"读取 user_sessions 失败（可能未建表）: {e}")
            session = None

        g.user_session = session
        return f(*args, **kwargs)
    return decorated_function

def _get_user_role(user_id):
    role_info = _get_role_info(user_id)
    return role_info.get('effective_role')

def _get_base_user_role(user_id, cursor=None):
    if not user_id:
        return None
    own_conn = None
    try:
        if cursor is None:
            own_conn = get_db_connection()
            cursor = own_conn.cursor()
        try:
            cursor.execute('SELECT role FROM users WHERE id = %s', (user_id,))
            row = cursor.fetchone() or {}
            return row.get('role') or 'user'
        except Exception:
            cursor.execute('SELECT is_admin FROM users WHERE id = %s', (user_id,))
            row = cursor.fetchone() or {}
            return 'admin' if int(row.get('is_admin') or 0) == 1 else 'user'
    finally:
        if own_conn:
            cursor.close()
            own_conn.close()

def _get_role_info(user_id):
    if not user_id:
        return {
            'base_role': None,
            'effective_role': None,
            'is_temporary_super_admin': False,
            'grant_expires_at': None,
            'grant_id': None
        }

    _ensure_schema_once()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        base_role = _get_base_user_role(user_id, cursor=cursor) or 'user'
        role_info = {
            'base_role': base_role,
            'effective_role': base_role,
            'is_temporary_super_admin': False,
            'grant_expires_at': None,
            'grant_id': None
        }

        if base_role != 'admin':
            return role_info

        try:
            cursor.execute(
                '''
                SELECT id, expires_at
                FROM temporary_super_admin_grants
                WHERE user_id = %s
                  AND revoked_at IS NULL
                  AND starts_at <= NOW()
                  AND expires_at > NOW()
                ORDER BY expires_at DESC, id DESC
                LIMIT 1
                ''',
                (user_id,)
            )
            grant = cursor.fetchone()
        except Exception:
            grant = None

        if grant:
            role_info['effective_role'] = 'super_admin'
            role_info['is_temporary_super_admin'] = True
            role_info['grant_expires_at'] = grant.get('expires_at')
            role_info['grant_id'] = grant.get('id')

        return role_info
    finally:
        cursor.close()
        conn.close()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = _read_bearer_token()
        session = None
        try:
            session = _get_user_session(token) if token else None
        except ReLoginRequired:
            g.relogin_required = True
            session = None
        except Exception as e:
            logger.error(f"读取 user_sessions 失败（可能未建表）: {e}")
            session = None

        if not session:
            if getattr(g, 'relogin_required', False):
                return jsonify({'code': 401, 'msg': f'登录已超过{RELOGIN_AFTER_DAYS}天，请重新登录'}), 401
            return jsonify({'code': 401, 'msg': '需要登录'}), 401

        role_info = _get_role_info(session.get('user_id'))
        role = role_info.get('effective_role')
        if role not in ['admin', 'super_admin']:
            return jsonify({'code': 403, 'msg': '需要管理员权限'}), 403

        g.user_session = session
        g.user_role = role
        g.base_user_role = role_info.get('base_role')
        g.role_info = role_info
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = _read_bearer_token()
        session = None
        try:
            session = _get_user_session(token) if token else None
        except ReLoginRequired:
            g.relogin_required = True
            session = None
        except Exception as e:
            logger.error(f"读取 user_sessions 失败（可能未建表）: {e}")
            session = None

        if not session:
            if getattr(g, 'relogin_required', False):
                return jsonify({'code': 401, 'msg': f'登录已超过{RELOGIN_AFTER_DAYS}天，请重新登录'}), 401
            return jsonify({'code': 401, 'msg': '需要登录'}), 401

        role_info = _get_role_info(session.get('user_id'))
        g.user_session = session
        g.user_role = role_info.get('effective_role')
        g.base_user_role = role_info.get('base_role')
        g.role_info = role_info
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = _read_bearer_token()
        session = None
        try:
            session = _get_user_session(token) if token else None
        except ReLoginRequired:
            g.relogin_required = True
            session = None
        except Exception as e:
            logger.error(f"读取 user_sessions 失败（可能未建表）: {e}")
            session = None

        if not session:
            if getattr(g, 'relogin_required', False):
                return jsonify({'code': 401, 'msg': f'登录已超过{RELOGIN_AFTER_DAYS}天，请重新登录'}), 401
            return jsonify({'code': 401, 'msg': '需要登录'}), 401

        role_info = _get_role_info(session.get('user_id'))
        role = role_info.get('effective_role')
        if role != 'super_admin':
            return jsonify({'code': 403, 'msg': '需要超级管理员权限'}), 403

        g.user_session = session
        g.user_role = role
        g.base_user_role = role_info.get('base_role')
        g.role_info = role_info
        return f(*args, **kwargs)
    return decorated_function

def _is_self_or_admin(target_user_id):
    session = getattr(g, 'user_session', None) or {}
    role = getattr(g, 'user_role', None) or _get_user_role(session.get('user_id'))
    session_user_id = session.get('user_id')
    if role in ['admin', 'super_admin']:
        return True
    return int(session_user_id or 0) == int(target_user_id or 0)

# 1. 注册接口
@app.route('/register', methods=['POST'])
def register():
    return jsonify({'code': 403, 'msg': '系统已禁用用户注册，请联系管理员创建账号'}), 403

# 2. 登录接口
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'code': 400, 'msg': '用户名和密码不能为空'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = %s LIMIT 1', (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and _verify_password_and_maybe_upgrade(user, password):
        role_info = _get_role_info(user['id'])
        role = role_info.get('effective_role') or user.get('role', 'user')
        base_role = role_info.get('base_role') or user.get('role', 'user')
        is_admin = role in ['admin', 'super_admin']
        is_super_admin = role == 'super_admin'
        session_token = None
        session_expires_at = None

        # 在线/登录时间不应依赖 user_sessions 是否存在
        try:
            _ensure_schema_once()
            _mark_user_online(user['id'])
        except Exception as e:
            logger.error(f"更新 last_login_at/is_online 失败: {e}")

        try:
            session_token, session_expires_at = _create_user_session(user['id'])
        except Exception as e:
            logger.error(f"创建 user_sessions 失败（可能未建表）: {e}")
        return jsonify({
            'code': 200, 
            'msg': '登录成功', 
            'user_id': user['id'], 
            'username': user['username'],
            'nickname': user.get('nickname') or user['username'],
            'student_no': user.get('student_no') or '',
            'phone': user.get('phone') or '',
            'department': user.get('department') or '',
            'base_role': base_role,
            'is_admin': is_admin,
            'is_super_admin': is_super_admin,
            'is_temporary_super_admin': bool(role_info.get('is_temporary_super_admin')),
            'grant_expires_at': role_info.get('grant_expires_at').strftime('%Y-%m-%d %H:%M:%S') if role_info.get('grant_expires_at') else None,
            'role': role,
            'session_token': session_token,
            'session_expires_at': session_expires_at.strftime('%Y-%m-%d %H:%M:%S') if session_expires_at else None,
            'session_ttl_days': SESSION_TTL_DAYS if session_token else None
        })
    else:
        return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

# 3. 打卡接口
@app.route('/punch', methods=['POST'])
@user_required
def punch():
    user_id = g.user_session.get('user_id')

    _ensure_punch_records_schema_once()

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查用户最后一次打卡时间
    cursor.execute('SELECT punch_time FROM punch_records WHERE user_id = %s ORDER BY punch_time DESC LIMIT 1', (user_id,))
    last_punch = cursor.fetchone()
    
    current_time = datetime.now()
    
    if last_punch:
        last_time = last_punch['punch_time']
        time_diff = (current_time - last_time).total_seconds()
        
        if time_diff < 10:
            remaining = int(10 - time_diff)
            return jsonify({'code': 429, 'msg': f'打卡太频繁，请等待 {remaining} 秒后再试'}), 429
    
    # 插入打卡记录
    cursor.execute('INSERT INTO punch_records (user_id) VALUES (%s)', (user_id,))
    record_id = cursor.lastrowid
    conn.commit()

    # 返回待审批数量，便于前端展示“待审批”提示
    pending_count = 0
    try:
        cursor.execute('SELECT COUNT(*) AS cnt FROM punch_records WHERE user_id = %s AND approved = 0', (user_id,))
        row = cursor.fetchone() or {}
        pending_count = int(row.get('cnt') or 0)
    except Exception:
        pending_count = 0

    cursor.close()
    conn.close()

    return jsonify({
        'code': 200, 
        'msg': '已提交管理员，待审批中',
        'time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
        'record_id': record_id,
        'pending': {
            'count': pending_count
        }
    })

# 4. 查询打卡记录接口
@app.route('/records/<int:user_id>', methods=['GET'])
@user_required
def get_records(user_id):
    if not _is_self_or_admin(user_id):
        return jsonify({'code': 403, 'msg': '无权限查看该用户记录'}), 403

    _ensure_punch_records_schema_once()
    _ensure_schema_once()
    conn = get_db_connection()
    cursor = conn.cursor()

    # 仅返回已审批通过的有效打卡记录
    cursor.execute(
        'SELECT * FROM punch_records WHERE user_id = %s AND approved = 1 ORDER BY punch_time DESC',
        (user_id,)
    )
    records = cursor.fetchall() or []

    pending_count = 0
    pending_latest_candidates = []
    try:
        cursor.execute(
            'SELECT COUNT(*) AS cnt, MAX(punch_time) AS latest FROM punch_records WHERE user_id = %s AND approved = 0',
            (user_id,)
        )
        row = cursor.fetchone() or {}
        pending_count += int(row.get('cnt') or 0)
        if row.get('latest'):
            pending_latest_candidates.append(row.get('latest'))
    except Exception:
        pass

    try:
        cursor.execute(
            'SELECT COUNT(*) AS cnt, MAX(created_at) AS latest FROM phone_change_requests WHERE user_id = %s AND approved = 0',
            (user_id,)
        )
        row = cursor.fetchone() or {}
        pending_count += int(row.get('cnt') or 0)
        if row.get('latest'):
            pending_latest_candidates.append(row.get('latest'))
    except Exception:
        pass

    cursor.close()
    conn.close()

    pending_latest = max(pending_latest_candidates) if pending_latest_candidates else None
    pending_latest_text = None
    try:
        if pending_latest:
            pending_latest_text = pending_latest.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        pending_latest_text = str(pending_latest) if pending_latest else None

    return jsonify({
        'code': 200,
        'data': records,
        'pending': {
            'count': pending_count,
            'latest_time': pending_latest_text
        }
    })

# 4.1 查询用户提交的打卡审批消息（含待审批/通过/驳回）
@app.route('/records/messages/<int:user_id>', methods=['GET'])
@user_required
def get_punch_messages(user_id):
    if not _is_self_or_admin(user_id):
        return jsonify({'code': 403, 'msg': '无权限查看该用户记录'}), 403

    _ensure_punch_records_schema_once()
    _ensure_schema_once()

    limit = request.args.get('limit')
    include_phone = (request.args.get('include_phone') or '').strip() == '1'
    try:
        limit_int = int(limit or 50)
    except Exception:
        return jsonify({'code': 400, 'msg': 'limit 必须为数字'}), 400

    if limit_int <= 0:
        limit_int = 50
    limit_int = min(limit_int, 200)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT id, punch_time, approved, is_urge
            FROM punch_records
            WHERE user_id = %s
            ORDER BY punch_time DESC, id DESC
            LIMIT %s
            ''',
            (user_id, limit_int)
        )
        rows = []
        for row in (cursor.fetchall() or []):
            rows.append({
                'id': _encode_item_id('punch', row['id']),
                'item_type': 'punch',
                'punch_time': row.get('punch_time'),
                'approved': row.get('approved', 0),
                'is_urge': row.get('is_urge', 0),
                'title': '打卡记录',
                'detail': '打卡提交记录'
            })

        if include_phone:
            cursor.execute(
                '''
                SELECT id, created_at, approved, is_urge, current_phone, requested_phone
                FROM phone_change_requests
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                ''',
                (user_id, limit_int)
            )
            for row in (cursor.fetchall() or []):
                rows.append({
                    'id': _encode_item_id('phone', row['id']),
                    'item_type': 'phone_change',
                    'punch_time': row.get('created_at'),
                    'approved': row.get('approved', 0),
                    'is_urge': row.get('is_urge', 0),
                    'title': '手机号变更',
                    'detail': f"申请改为 {row.get('requested_phone') or '-'}"
                })

        rows.sort(key=lambda item: (str(item.get('punch_time') or ''), str(item.get('id') or '')), reverse=True)
        rows = rows[:limit_int]
        return jsonify({'code': 200, 'data': rows})
    finally:
        cursor.close()
        conn.close()

# 4.2 用户对待审批记录发起催办
@app.route('/records/<int:record_id>/urge', methods=['POST'])
@user_required
def urge_punch_record(record_id):
    _ensure_punch_records_schema_once()
    user_id = int(g.user_session.get('user_id'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'SELECT id, user_id, approved, is_urge FROM punch_records WHERE id = %s LIMIT 1',
            (record_id,)
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({'code': 404, 'msg': '记录不存在'}), 404

        if int(row.get('user_id') or 0) != user_id:
            return jsonify({'code': 403, 'msg': '无权限操作该记录'}), 403

        if int(row.get('approved') or 0) != 0:
            return jsonify({'code': 400, 'msg': '该记录已处理，无法催办'}), 400

        if int(row.get('is_urge') or 0) == 1:
            return jsonify({'code': 200, 'msg': '已催办', 'updated': 0})

        cursor.execute(
            'UPDATE punch_records SET is_urge = 1 WHERE id = %s AND approved = 0',
            (record_id,)
        )
        conn.commit()
        return jsonify({'code': 200, 'msg': '催办成功', 'updated': cursor.rowcount})
    finally:
        cursor.close()
        conn.close()

@app.route('/phone-change-requests/<int:request_id>/urge', methods=['POST'])
@user_required
def urge_phone_change_request(request_id):
    user_id = int(g.user_session.get('user_id'))
    _ensure_schema_once()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT id, user_id, approved, is_urge
            FROM phone_change_requests
            WHERE id = %s
            LIMIT 1
            ''',
            (request_id,)
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({'code': 404, 'msg': '申请不存在'}), 404
        if int(row.get('user_id') or 0) != user_id:
            return jsonify({'code': 403, 'msg': '无权限操作该申请'}), 403
        if int(row.get('approved') or 0) != 0:
            return jsonify({'code': 400, 'msg': '该申请已处理，无法催办'}), 400
        if int(row.get('is_urge') or 0) == 1:
            return jsonify({'code': 200, 'msg': '已催办', 'updated': 0}), 200

        cursor.execute(
            'UPDATE phone_change_requests SET is_urge = 1 WHERE id = %s AND approved = 0',
            (request_id,)
        )
        conn.commit()
        return jsonify({'code': 200, 'msg': '催办成功', 'updated': cursor.rowcount})
    finally:
        cursor.close()
        conn.close()

# 可选：前端刷新时校验 session_token
@app.route('/me', methods=['GET'])
@user_required
def me():
    user_id = g.user_session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'SELECT id, nickname, username, student_no, phone, department, role, is_online, is_admin, last_login_at, last_logout_at, created_at FROM users WHERE id = %s',
            (user_id,)
        )
        user = cursor.fetchone()
        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'}), 404
        role_info = _get_role_info(user['id'])
        role = role_info.get('effective_role') or user.get('role', 'user')
        return jsonify({
            'code': 200,
            'user_id': user['id'],
            'nickname': user.get('nickname') or user['username'],
            'username': user['username'],
            'student_no': user.get('student_no') or '',
            'phone': user.get('phone') or '',
            'department': user.get('department') or '',
            'base_role': role_info.get('base_role') or user.get('role', 'user'),
            'role': role,
            'is_admin': role in ['admin', 'super_admin'],
            'is_super_admin': role == 'super_admin',
            'is_temporary_super_admin': bool(role_info.get('is_temporary_super_admin')),
            'grant_expires_at': role_info.get('grant_expires_at').strftime('%Y-%m-%d %H:%M:%S') if role_info.get('grant_expires_at') else None,
            'is_online': user.get('is_online', 0),
            'last_login_at': user.get('last_login_at').strftime('%Y-%m-%d %H:%M:%S') if user.get('last_login_at') else None,
            'last_logout_at': user.get('last_logout_at').strftime('%Y-%m-%d %H:%M:%S') if user.get('last_logout_at') else None,
            'created_at': user.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if user.get('created_at') else None
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/logout', methods=['POST'])
@user_required
def logout():
    token = _read_bearer_token()
    user_id = g.user_session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM user_sessions WHERE token = %s', (token,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    try:
        _mark_user_offline_if_no_active_sessions(user_id)
    except Exception as e:
        logger.error(f"退出登录后更新 is_online 失败: {e}")

    return jsonify({'code': 200, 'msg': '已退出'})

def _normalize_text(value, default=''):
    return str(value or default).strip()

def _normalize_list(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item or '').strip()]
    text = str(value or '').strip()
    if not text:
        return []
    return [part.strip() for part in re.split(r'[\n,，]+', text) if part.strip()]

@app.route('/activities', methods=['GET'])
@user_required
def get_activities():
    _ensure_activities_schema_once()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT id, slug, title, category, frequency, duration, difficulty, scene,
                   summary, tagline, description, highlights_json, steps_json, tips_json,
                   cover_image, status, created_by, reviewed_by, reviewed_at, created_at, updated_at
            FROM activities
            WHERE is_active = 1 AND status = 'approved'
            ORDER BY created_at DESC, id DESC
            '''
        )
        rows = cursor.fetchall() or []
        return jsonify({'code': 200, 'data': [_serialize_activity_row(row) for row in rows]})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/activities', methods=['GET'])
@admin_required
def get_admin_activities():
    _ensure_activities_schema_once()
    role = getattr(g, 'user_role', 'user')
    current_user_id = int((g.user_session or {}).get('user_id') or 0)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT id, slug, title, category, frequency, duration, difficulty, scene,
                   summary, tagline, description, highlights_json, steps_json, tips_json,
                   cover_image, status, created_by, reviewed_by, reviewed_at, created_at, updated_at
            FROM activities
            WHERE status = 'approved' AND is_active = 1
            ORDER BY created_at DESC, id DESC
            '''
        )
        approved_rows = cursor.fetchall() or []

        cursor.execute(
            '''
            SELECT id, slug, title, category, frequency, duration, difficulty, scene,
                   summary, tagline, description, highlights_json, steps_json, tips_json,
                   cover_image, status, created_by, reviewed_by, reviewed_at, created_at, updated_at
            FROM activities
            WHERE created_by = %s AND status IN ('pending', 'rejected')
            ORDER BY created_at DESC, id DESC
            ''',
            (current_user_id,)
        )
        own_rows = cursor.fetchall() or []

        pending_rows = []
        if role == 'super_admin':
            cursor.execute(
                '''
                SELECT id, slug, title, category, frequency, duration, difficulty, scene,
                       summary, tagline, description, highlights_json, steps_json, tips_json,
                       cover_image, status, created_by, reviewed_by, reviewed_at, created_at, updated_at
                FROM activities
                WHERE status = 'pending'
                ORDER BY created_at DESC, id DESC
                '''
            )
            pending_rows = cursor.fetchall() or []

        return jsonify({
            'code': 200,
            'approved': [_serialize_activity_row(row) for row in approved_rows],
            'submissions': [_serialize_activity_row(row) for row in own_rows],
            'pending_reviews': [_serialize_activity_row(row) for row in pending_rows],
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/activities', methods=['POST'])
@admin_required
def create_activity():
    _ensure_activities_schema_once()
    data = request.json or {}
    role = getattr(g, 'user_role', 'user')

    title = _normalize_text(data.get('title'))
    if not title:
        return jsonify({'code': 400, 'msg': '活动名称不能为空'}), 400

    category = _normalize_text(data.get('category'), '日常活动')
    frequency = _normalize_text(data.get('frequency'), '每日')
    duration = _normalize_text(data.get('duration'), '10-20 分钟')
    difficulty = _normalize_text(data.get('difficulty'), '轻松')
    scene = _normalize_text(data.get('scene'), '校园 / 宿舍 / 日常场景')
    summary = _normalize_text(data.get('summary'), '管理员新增的日常活动内容。')
    tagline = _normalize_text(data.get('tagline'), '新增活动内容')
    description = _normalize_text(data.get('description'), summary)
    highlights = _normalize_list(data.get('highlights'))
    steps = _normalize_list(data.get('steps'))
    tips = _normalize_list(data.get('tips'))
    cover_image = _normalize_text(data.get('cover_image'))
    slug = f'activity-{int(time.time() * 1000)}-{secrets.token_hex(3)}'
    created_by = int((g.user_session or {}).get('user_id') or 0) or None
    status = 'approved' if role == 'super_admin' else 'pending'
    is_active = 1 if status == 'approved' else 0
    reviewed_by = created_by if role == 'super_admin' else None
    reviewed_at = datetime.now() if role == 'super_admin' else None

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_sort FROM activities')
        next_sort = int((cursor.fetchone() or {}).get('next_sort') or 0)
        cursor.execute(
            '''
            INSERT INTO activities (
              slug, title, category, frequency, duration, difficulty, scene,
              summary, tagline, description, highlights_json, steps_json, tips_json,
              cover_image, sort_order, status, is_active, created_by, reviewed_by, reviewed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''',
            (
                slug, title, category, frequency, duration, difficulty, scene,
                summary, tagline, description,
                json.dumps(highlights, ensure_ascii=False),
                json.dumps(steps, ensure_ascii=False),
                json.dumps(tips, ensure_ascii=False),
                cover_image, next_sort, status, is_active, created_by, reviewed_by, reviewed_at
            )
        )
        activity_id = cursor.lastrowid
        conn.commit()

        cursor.execute(
            '''
            SELECT id, slug, title, category, frequency, duration, difficulty, scene,
                   summary, tagline, description, highlights_json, steps_json, tips_json,
                   cover_image, status, created_by, reviewed_by, reviewed_at, created_at, updated_at
            FROM activities
            WHERE id = %s
            LIMIT 1
            ''',
            (activity_id,)
        )
        row = cursor.fetchone() or {}
        msg = '活动已发布' if status == 'approved' else '活动已提交，等待主席审批'
        return jsonify({'code': 200, 'msg': msg, 'data': _serialize_activity_row(row)})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/activities/<int:activity_id>/approve', methods=['POST'])
@super_admin_required
def approve_activity(activity_id):
    _ensure_activities_schema_once()
    reviewer_id = int((g.user_session or {}).get('user_id') or 0) or None
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            UPDATE activities
            SET status = 'approved', is_active = 1, reviewed_by = %s, reviewed_at = NOW()
            WHERE id = %s AND status = 'pending'
            ''',
            (reviewer_id, activity_id)
        )
        conn.commit()
        if cursor.rowcount <= 0:
            return jsonify({'code': 404, 'msg': '待审批活动不存在'}), 404
        return jsonify({'code': 200, 'msg': '活动已通过审批', 'updated': cursor.rowcount})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/activities/<int:activity_id>/reject', methods=['POST'])
@super_admin_required
def reject_activity(activity_id):
    _ensure_activities_schema_once()
    reviewer_id = int((g.user_session or {}).get('user_id') or 0) or None
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            UPDATE activities
            SET status = 'rejected', is_active = 0, reviewed_by = %s, reviewed_at = NOW()
            WHERE id = %s AND status = 'pending'
            ''',
            (reviewer_id, activity_id)
        )
        conn.commit()
        if cursor.rowcount <= 0:
            return jsonify({'code': 404, 'msg': '待审批活动不存在'}), 404
        return jsonify({'code': 200, 'msg': '活动已驳回', 'updated': cursor.rowcount})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/activities/<int:activity_id>', methods=['DELETE'])
@admin_required
def delete_activity(activity_id):
    _ensure_activities_schema_once()
    role = getattr(g, 'user_role', 'user')
    if role != 'super_admin':
        return jsonify({'code': 403, 'msg': '只有主席可以删除活动'}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM activities WHERE id = %s', (activity_id,))
        conn.commit()
        if cursor.rowcount <= 0:
            return jsonify({'code': 404, 'msg': '活动不存在'}), 404
        return jsonify({'code': 200, 'msg': '活动已删除', 'deleted': cursor.rowcount})
    finally:
        cursor.close()
        conn.close()

# 5. 管理员登录接口
@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'code': 400, 'msg': '用户名和密码不能为空'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM users WHERE username = %s LIMIT 1', (username,))
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not user or not _verify_password_and_maybe_upgrade(user, password):
        return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

    base_role = user.get('role', 'user')
    if base_role not in ['admin', 'super_admin']:
        return jsonify({'code': 403, 'msg': '需要管理员账号'}), 403

    role_info = _get_role_info(user['id'])
    role = role_info.get('effective_role') or base_role

    session_token = None
    session_expires_at = None

    # 在线/登录时间不应依赖 user_sessions 是否存在
    try:
        _ensure_schema_once()
        _mark_user_online(user['id'])
    except Exception as e:
        logger.error(f"更新 last_login_at/is_online 失败: {e}")

    try:
        session_token, session_expires_at = _create_user_session(user['id'])
    except Exception as e:
        logger.error(f"创建 user_sessions 失败（可能未建表）: {e}")

    return jsonify({
        'code': 200,
        'msg': '登录成功',
        'user_id': user['id'],
        'username': user['username'],
        'nickname': user.get('nickname') or user['username'],
        'student_no': user.get('student_no') or '',
        'phone': user.get('phone') or '',
        'department': user.get('department') or '',
        'base_role': role_info.get('base_role') or base_role,
        'is_admin': True,
        'is_super_admin': role == 'super_admin',
        'is_temporary_super_admin': bool(role_info.get('is_temporary_super_admin')),
        'grant_expires_at': role_info.get('grant_expires_at').strftime('%Y-%m-%d %H:%M:%S') if role_info.get('grant_expires_at') else None,
        'role': role,
        'session_token': session_token,
        'session_expires_at': session_expires_at.strftime('%Y-%m-%d %H:%M:%S') if session_expires_at else None,
        'session_ttl_days': SESSION_TTL_DAYS if session_token else None
    })

# 6. 获取所有用户列表（管理员）
@app.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    # 管理端读取时顺便同步一次在线状态：存在未过期 session 视为在线
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
        conn.commit()
    except Exception as e:
        logger.error(f"同步 users.is_online 失败（可能无 user_sessions 表）: {e}")

    cursor.execute(
        'SELECT id, nickname, username, role, is_online, last_login_at, last_logout_at, created_at FROM users ORDER BY id'
    )
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({'code': 200, 'data': users})

# 7. 获取所有打卡记录（管理员）
@app.route('/admin/records', methods=['GET'])
@admin_required
def get_all_records():
    _ensure_punch_records_schema_once()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            pr.id,
            pr.user_id,
            u.username,
            u.student_no,
            u.department,
            pr.punch_time,
            pr.approved,
            pr.is_urge,
            pr.approved_by,
            pr.approved_at,
            approver.username AS approved_by_username
        FROM punch_records pr
        JOIN users u ON pr.user_id = u.id
        LEFT JOIN users approver ON approver.id = pr.approved_by
        ORDER BY pr.punch_time DESC
    ''')
    records = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({'code': 200, 'data': records})

# 9. 查询待审批打卡记录（管理员）
@app.route('/admin/punch-approvals', methods=['GET'])
@admin_required
def admin_get_punch_approvals():
    _ensure_punch_records_schema_once()
    _ensure_schema_once()

    user_id = (request.args.get('user_id') or '').strip()
    username = (request.args.get('username') or '').strip()
    start_date = (request.args.get('start_date') or '').strip()
    end_date = (request.args.get('end_date') or '').strip()
    status = (request.args.get('status') or 'pending').strip().lower()  # pending/approved/rejected/all
    limit = request.args.get('limit')
    page = request.args.get('page')
    page_size = request.args.get('page_size')

    clauses = []
    params = []

    # 审批界面只处理普通用户（不展示管理员/超级管理员）
    # 兼容旧库：优先依赖 users.is_admin 字段（比 users.role 更稳定）
    clauses.append('IFNULL(u.is_admin, 0) = 0')

    if status == 'pending':
        clauses.append('pr.approved = 0')
    elif status == 'approved':
        clauses.append('pr.approved = 1')
    elif status == 'rejected':
        clauses.append('pr.approved = -1')
    elif status == 'all':
        pass
    else:
        return jsonify({'code': 400, 'msg': 'status 参数错误'}), 400

    if username:
        clauses.append('(u.username LIKE %s OR u.nickname LIKE %s)')
        like = f'%{username}%'
        params.extend([like, like])

    if user_id:
        try:
            user_id_int = int(user_id)
        except Exception:
            return jsonify({'code': 400, 'msg': 'user_id 必须为数字'}), 400
        clauses.append('pr.user_id = %s')
        params.append(user_id_int)

    def _parse_date(s):
        try:
            return datetime.strptime(s, '%Y-%m-%d')
        except Exception:
            return None

    start_dt = _parse_date(start_date) if start_date else None
    end_dt = _parse_date(end_date) if end_date else None

    if start_date and not start_dt:
        return jsonify({'code': 400, 'msg': 'start_date 格式应为 YYYY-MM-DD'}), 400
    if end_date and not end_dt:
        return jsonify({'code': 400, 'msg': 'end_date 格式应为 YYYY-MM-DD'}), 400

    if start_dt:
        clauses.append('pr.punch_time >= %s')
        params.append(start_dt.strftime('%Y-%m-%d 00:00:00'))
    if end_dt:
        clauses.append('pr.punch_time <= %s')
        params.append((end_dt + timedelta(days=1) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'))

    where_sql = ('WHERE ' + ' AND '.join(clauses)) if clauses else ''

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f'''
            SELECT
              'punch' AS item_type,
              pr.id AS raw_id,
              pr.user_id,
              u.username,
              u.nickname,
              pr.punch_time,
              pr.approved,
              pr.is_urge,
              '打卡记录' AS content
            FROM punch_records pr
            JOIN users u ON pr.user_id = u.id
            {where_sql}
            ORDER BY pr.punch_time DESC, pr.id DESC
            ''',
            tuple(params)
        )
        punch_rows = cursor.fetchall() or []

        phone_clauses = ['IFNULL(u.is_admin, 0) = 0']
        phone_params = []
        if status == 'pending':
            phone_clauses.append('pcr.approved = 0')
        elif status == 'approved':
            phone_clauses.append('pcr.approved = 1')
        elif status == 'rejected':
            phone_clauses.append('pcr.approved = -1')
        if username:
            phone_clauses.append('(u.username LIKE %s OR u.nickname LIKE %s)')
            like = f'%{username}%'
            phone_params.extend([like, like])
        if user_id:
            phone_clauses.append('pcr.user_id = %s')
            phone_params.append(user_id_int)
        if start_dt:
            phone_clauses.append('pcr.created_at >= %s')
            phone_params.append(start_dt.strftime('%Y-%m-%d 00:00:00'))
        if end_dt:
            phone_clauses.append('pcr.created_at <= %s')
            phone_params.append((end_dt + timedelta(days=1) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'))

        phone_where_sql = 'WHERE ' + ' AND '.join(phone_clauses)
        cursor.execute(
            f'''
            SELECT
              'phone' AS item_type,
              pcr.id AS raw_id,
              pcr.user_id,
              u.username,
              u.nickname,
              pcr.created_at AS punch_time,
              pcr.approved,
              pcr.is_urge,
              CONCAT('手机号改为 ', pcr.requested_phone) AS content
            FROM phone_change_requests pcr
            JOIN users u ON pcr.user_id = u.id
            {phone_where_sql}
            ORDER BY pcr.created_at DESC, pcr.id DESC
            ''',
            tuple(phone_params)
        )
        phone_rows = cursor.fetchall() or []
    finally:
        cursor.close()
        conn.close()

    merged = []
    for row in punch_rows + phone_rows:
        row['id'] = _encode_item_id(row.get('item_type'), row.get('raw_id'))
        merged.append(row)

    def _approval_sort_key(row):
        approved = int(row.get('approved') or 0)
        is_pending = 0 if approved == 0 else 1
        is_urged = 0 if approved == 0 and int(row.get('is_urge') or 0) == 1 else 1
        return (
            is_pending,
            is_urged,
            str(row.get('punch_time') or ''),
            str(row.get('id') or '')
        )

    merged.sort(key=_approval_sort_key)

    if page is None and page_size is None and limit is not None:
        try:
            limit_int = int(limit)
        except Exception:
            return jsonify({'code': 400, 'msg': 'limit 必须为数字'}), 400
        if limit_int <= 0:
            limit_int = 2000
        limit_int = min(limit_int, 5000)
        return jsonify({'code': 200, 'data': merged[:limit_int], 'meta': {'mode': 'limit', 'limit': limit_int}})

    try:
        page_int = int(page or 1)
        page_size_int = int(page_size or 200)
    except Exception:
        return jsonify({'code': 400, 'msg': 'page/page_size 必须为数字'}), 400

    if page_int <= 0:
        page_int = 1
    if page_size_int <= 0:
        page_size_int = 200
    page_size_int = min(page_size_int, 500)
    offset = (page_int - 1) * page_size_int
    page_rows = merged[offset:offset + page_size_int + 1]
    has_more = len(page_rows) > page_size_int
    records = page_rows[:page_size_int]
    return jsonify({
        'code': 200,
        'data': records,
        'meta': {
            'mode': 'page',
            'page': page_int,
            'page_size': page_size_int,
            'has_more': has_more
        }
    })

# 10. 批量审批通过打卡记录（管理员）
@app.route('/admin/punch-approvals/approve', methods=['POST'])
@admin_required
def admin_approve_punch_records():
    _ensure_punch_records_schema_once()
    _ensure_schema_once()
    approver_id = int((g.user_session or {}).get('user_id') or 0) or None

    data = request.json or {}
    record_ids = data.get('record_ids') or []
    if not isinstance(record_ids, list) or not record_ids:
        return jsonify({'code': 400, 'msg': 'record_ids 不能为空'}), 400

    try:
        punch_ids, phone_ids = _parse_item_ids(record_ids)
    except Exception:
        return jsonify({'code': 400, 'msg': 'record_ids 格式错误'}), 400

    updated = 0
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if punch_ids:
            placeholders = ','.join(['%s'] * len(punch_ids))
            cursor.execute(
                f'''
                UPDATE punch_records
                SET approved = 1, is_urge = 0, approved_by = %s, approved_at = NOW()
                WHERE id IN ({placeholders}) AND approved = 0
                ''',
                (approver_id, *tuple(punch_ids))
            )
            updated += cursor.rowcount

        if phone_ids:
            placeholders = ','.join(['%s'] * len(phone_ids))
            cursor.execute(
                f'''
                SELECT id, user_id, requested_phone
                FROM phone_change_requests
                WHERE id IN ({placeholders}) AND approved = 0
                ''',
                tuple(phone_ids)
            )
            phone_rows = cursor.fetchall() or []
            if phone_rows:
                cursor.execute(
                    f'''
                    UPDATE phone_change_requests
                    SET approved = 1, is_urge = 0
                    WHERE id IN ({placeholders}) AND approved = 0
                    ''',
                    tuple(phone_ids)
                )
                updated += cursor.rowcount
                for row in phone_rows:
                    cursor.execute(
                        'UPDATE users SET phone = %s WHERE id = %s',
                        (row.get('requested_phone') or '', row.get('user_id'))
                    )
        conn.commit()
        return jsonify({'code': 200, 'msg': '审批成功', 'updated': updated})
    finally:
        cursor.close()
        conn.close()

# 11. 批量驳回打卡记录（管理员）
@app.route('/admin/punch-approvals/reject', methods=['POST'])
@admin_required
def admin_reject_punch_records():
    _ensure_punch_records_schema_once()
    _ensure_schema_once()
    approver_id = int((g.user_session or {}).get('user_id') or 0) or None

    data = request.json or {}
    record_ids = data.get('record_ids') or []
    if not isinstance(record_ids, list) or not record_ids:
        return jsonify({'code': 400, 'msg': 'record_ids 不能为空'}), 400

    try:
        punch_ids, phone_ids = _parse_item_ids(record_ids)
    except Exception:
        return jsonify({'code': 400, 'msg': 'record_ids 格式错误'}), 400

    updated = 0
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if punch_ids:
            placeholders = ','.join(['%s'] * len(punch_ids))
            cursor.execute(
                f'''
                UPDATE punch_records
                SET approved = -1, is_urge = 0, approved_by = %s, approved_at = NOW()
                WHERE id IN ({placeholders}) AND approved = 0
                ''',
                (approver_id, *tuple(punch_ids))
            )
            updated += cursor.rowcount

        if phone_ids:
            placeholders = ','.join(['%s'] * len(phone_ids))
            cursor.execute(
                f'''
                UPDATE phone_change_requests
                SET approved = -1, is_urge = 0
                WHERE id IN ({placeholders}) AND approved = 0
                ''',
                tuple(phone_ids)
            )
            updated += cursor.rowcount
        conn.commit()
        return jsonify({'code': 200, 'msg': '驳回成功', 'updated': updated})
    finally:
        cursor.close()
        conn.close()

# 8. 删除打卡记录（管理员）
@app.route('/admin/records/<int:record_id>', methods=['DELETE'])
@admin_required
def delete_record(record_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM punch_records WHERE id = %s', (record_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'code': 200, 'msg': '删除成功'})

# 6. 申请管理员接口
@app.route('/admin/apply', methods=['POST'])
@user_required
def apply_admin():
    print(f"\n=== 收到管理员申请请求 ===", flush=True)
    print(f"请求方法: {request.method}", flush=True)
    print(f"请求头: {dict(request.headers)}", flush=True)
    print(f"原始数据: {request.get_data()}", flush=True)
    
    try:
        data = request.json
    except Exception as e:
        print(f"解析JSON失败: {e}", flush=True)
        return jsonify({'code': 400, 'msg': '请求数据格式错误'}), 400
    
    user_id = data.get('user_id')
    username = data.get('username')
    reason = data.get('reason')

    print(f"解析后的数据: user_id={user_id}, username={username}, reason={reason}", flush=True)

    if not user_id or not username or not reason:
        print(f"参数检查失败: user_id={user_id}, username={username}, reason={reason}", flush=True)
        return jsonify({'code': 400, 'msg': '缺少必要参数'}), 400

    session_user_id = int(g.user_session.get('user_id'))
    if int(user_id) != session_user_id:
        return jsonify({'code': 403, 'msg': '无权限代替其他用户申请管理员'}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户是否已经有待处理的申请
        try:
            cursor.execute('SELECT * FROM admin_applications WHERE user_id = %s AND status = %s', (user_id, 'pending'))
            existing = cursor.fetchone()
            if existing:
                return jsonify({'code': 400, 'msg': '您已有待处理的申请，请等待审批'}), 400
        except Exception as e:
            app.logger.error(f"查询admin_applications表失败: {e}")
            return jsonify({'code': 500, 'msg': f'数据库表不存在或查询失败：{str(e)}'}), 500
        
        # 检查用户是否已经是管理员
        cursor.execute('SELECT role FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        if user and user.get('role') in ['admin', 'super_admin']:
            return jsonify({'code': 400, 'msg': '您已经是管理员'}), 400
        
        # 创建申请
        cursor.execute('INSERT INTO admin_applications (user_id, username, reason) VALUES (%s, %s, %s)', 
                    (user_id, username, reason))
        conn.commit()
        
        app.logger.info(f"管理员申请创建成功: user_id={user_id}")
        return jsonify({'code': 200, 'msg': '申请已提交，请等待超级管理员审批'})
    except Exception as e:
        app.logger.error(f"申请管理员失败: {e}")
        return jsonify({'code': 500, 'msg': f'申请失败：{str(e)}'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 7. 获取管理员申请列表接口
@app.route('/admin/applications', methods=['GET'])
@super_admin_required
def get_admin_applications():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admin_applications ORDER BY created_at DESC')
    applications = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({'code': 200, 'data': applications})

# 8. 审批管理员申请接口
@app.route('/admin/approve', methods=['POST'])
@super_admin_required
def approve_admin():
    data = request.json
    application_id = data.get('application_id')
    action = data.get('action')  # 'approve' or 'reject'

    if not application_id or not action:
        return jsonify({'code': 400, 'msg': '缺少必要参数'}), 400

    if action not in ['approve', 'reject']:
        return jsonify({'code': 400, 'msg': '无效的操作'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取申请信息
        cursor.execute('SELECT * FROM admin_applications WHERE id = %s', (application_id,))
        application = cursor.fetchone()
        if not application:
            return jsonify({'code': 404, 'msg': '申请不存在'}), 400
        
        if application['status'] != 'pending':
            return jsonify({'code': 400, 'msg': '该申请已被处理'}), 400
        
        # 更新申请状态
        new_status = 'approved' if action == 'approve' else 'rejected'
        cursor.execute('UPDATE admin_applications SET status = %s WHERE id = %s', (new_status, application_id))
        
        # 如果批准，更新用户角色
        if action == 'approve':
            cursor.execute('UPDATE users SET role = %s WHERE id = %s', ('admin', application['user_id']))
        
        conn.commit()
        msg = '申请已批准' if action == 'approve' else '申请已拒绝'
        return jsonify({'code': 200, 'msg': msg})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'审批失败：{str(e)}'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/delegation-applications', methods=['POST'])
@admin_required
def create_delegation_application():
    _ensure_schema_once()
    if getattr(g, 'base_user_role', None) != 'admin':
        return jsonify({'code': 403, 'msg': '只有部长可以申请放权'}), 403

    data = request.json or {}
    reason = _normalize_text(data.get('reason'))
    user_id = int((g.user_session or {}).get('user_id') or 0)
    username = _normalize_text(data.get('username'))

    if not reason:
        return jsonify({'code': 400, 'msg': '请填写申请理由'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT username FROM users WHERE id = %s LIMIT 1', (user_id,))
        user_row = cursor.fetchone() or {}
        username = username or user_row.get('username') or ''

        cursor.execute(
            '''
            SELECT id
            FROM delegation_applications
            WHERE user_id = %s AND status = 'pending'
            ORDER BY id DESC
            LIMIT 1
            ''',
            (user_id,)
        )
        if cursor.fetchone():
            return jsonify({'code': 400, 'msg': '您已有待处理的放权申请，请等待审批'}), 400

        cursor.execute(
            '''
            SELECT id
            FROM temporary_super_admin_grants
            WHERE user_id = %s
              AND revoked_at IS NULL
              AND starts_at <= NOW()
              AND expires_at > NOW()
            ORDER BY id DESC
            LIMIT 1
            ''',
            (user_id,)
        )
        if cursor.fetchone():
            return jsonify({'code': 400, 'msg': '您当前已处于放权状态，无需重复申请'}), 400

        cursor.execute(
            '''
            INSERT INTO delegation_applications (user_id, username, reason)
            VALUES (%s, %s, %s)
            ''',
            (user_id, username, reason)
        )
        conn.commit()
        return jsonify({'code': 200, 'msg': '放权申请已提交，请等待主席处理'})
    finally:
        cursor.close()
        conn.close()

@app.route('/delegation-applications/mine', methods=['GET'])
@admin_required
def get_my_delegation_applications():
    _ensure_schema_once()
    if getattr(g, 'base_user_role', None) != 'admin':
        return jsonify({'code': 403, 'msg': '只有部长可以查看放权申请'}), 403

    user_id = int((g.user_session or {}).get('user_id') or 0)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT
                da.id,
                da.user_id,
                da.username,
                da.reason,
                da.status,
                da.is_urge,
                da.reviewed_by,
                reviewer.username AS reviewed_by_username,
                da.reviewed_at,
                da.grant_id,
                da.created_at,
                da.updated_at,
                g.starts_at,
                g.expires_at,
                g.revoked_at
            FROM delegation_applications da
            LEFT JOIN users reviewer ON reviewer.id = da.reviewed_by
            LEFT JOIN temporary_super_admin_grants g ON g.id = da.grant_id
            WHERE da.user_id = %s
            ORDER BY da.created_at DESC, da.id DESC
            ''',
            (user_id,)
        )
        return jsonify({'code': 200, 'data': cursor.fetchall() or []})
    finally:
        cursor.close()
        conn.close()

@app.route('/delegation-applications/<int:application_id>/urge', methods=['POST'])
@admin_required
def urge_delegation_application(application_id):
    _ensure_schema_once()
    if getattr(g, 'base_user_role', None) != 'admin':
        return jsonify({'code': 403, 'msg': '只有部长可以催办放权申请'}), 403

    user_id = int((g.user_session or {}).get('user_id') or 0)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT id, user_id, status, is_urge
            FROM delegation_applications
            WHERE id = %s
            LIMIT 1
            ''',
            (application_id,)
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({'code': 404, 'msg': '放权申请不存在'}), 404
        if int(row.get('user_id') or 0) != user_id:
            return jsonify({'code': 403, 'msg': '无权限操作该申请'}), 403
        if row.get('status') != 'pending':
            return jsonify({'code': 400, 'msg': '该申请已处理，无法催办'}), 400
        if int(row.get('is_urge') or 0) == 1:
            return jsonify({'code': 200, 'msg': '已催办', 'updated': 0})

        cursor.execute(
            'UPDATE delegation_applications SET is_urge = 1 WHERE id = %s AND status = %s',
            (application_id, 'pending')
        )
        conn.commit()
        return jsonify({'code': 200, 'msg': '催办成功', 'updated': cursor.rowcount})
    finally:
        cursor.close()
        conn.close()

@app.route('/super-admin/delegation-applications', methods=['GET'])
@super_admin_required
def get_super_admin_delegation_applications():
    _ensure_schema_once()
    if getattr(g, 'base_user_role', None) != 'super_admin':
        return jsonify({'code': 403, 'msg': '仅主席可查看放权申请'}), 403

    status = _normalize_text(request.args.get('status'), 'all')
    allowed = {'all', 'pending', 'approved', 'rejected'}
    if status not in allowed:
        status = 'all'

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = '''
            SELECT
                da.id,
                da.user_id,
                da.username,
                u.nickname,
                u.department,
                u.student_no,
                da.reason,
                da.status,
                da.is_urge,
                da.reviewed_by,
                reviewer.username AS reviewed_by_username,
                da.reviewed_at,
                da.grant_id,
                da.created_at,
                da.updated_at,
                g.starts_at,
                g.expires_at,
                g.revoked_at
            FROM delegation_applications da
            JOIN users u ON u.id = da.user_id
            LEFT JOIN users reviewer ON reviewer.id = da.reviewed_by
            LEFT JOIN temporary_super_admin_grants g ON g.id = da.grant_id
        '''
        params = []
        if status != 'all':
            sql += ' WHERE da.status = %s'
            params.append(status)
        sql += ' ORDER BY CASE WHEN da.status = "pending" THEN 0 ELSE 1 END, da.created_at DESC, da.id DESC'
        cursor.execute(sql, params)
        return jsonify({'code': 200, 'data': cursor.fetchall() or []})
    finally:
        cursor.close()
        conn.close()

@app.route('/super-admin/delegation-applications/<int:application_id>/approve', methods=['POST'])
@super_admin_required
def approve_delegation_application(application_id):
    _ensure_schema_once()
    if getattr(g, 'base_user_role', None) != 'super_admin':
        return jsonify({'code': 403, 'msg': '仅主席可处理放权申请'}), 403

    data = request.json or {}
    duration_hours = int(data.get('duration_hours') or 24)
    reviewer_id = int((g.user_session or {}).get('user_id') or 0)
    if duration_hours < 1 or duration_hours > 720:
        return jsonify({'code': 400, 'msg': '时长需在 1 到 720 小时之间'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT id, user_id, username, status
            FROM delegation_applications
            WHERE id = %s
            LIMIT 1
            ''',
            (application_id,)
        )
        application = cursor.fetchone()
        if not application:
            return jsonify({'code': 404, 'msg': '放权申请不存在'}), 404
        if application.get('status') != 'pending':
            return jsonify({'code': 400, 'msg': '该放权申请已处理'}), 400

        cursor.execute(
            '''
            SELECT id
            FROM temporary_super_admin_grants
            WHERE user_id = %s
              AND revoked_at IS NULL
              AND starts_at <= NOW()
              AND expires_at > NOW()
            ORDER BY id DESC
            LIMIT 1
            ''',
            (application.get('user_id'),)
        )
        if cursor.fetchone():
            return jsonify({'code': 400, 'msg': '该部长当前已处于放权状态'}), 400

        cursor.execute(
            '''
            INSERT INTO temporary_super_admin_grants (
                user_id, granted_by, duration_hours, starts_at, expires_at
            ) VALUES (%s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL %s HOUR))
            ''',
            (application.get('user_id'), reviewer_id, duration_hours, duration_hours)
        )
        grant_id = cursor.lastrowid

        cursor.execute(
            '''
            UPDATE delegation_applications
            SET status = 'approved',
                is_urge = 0,
                reviewed_by = %s,
                reviewed_at = NOW(),
                grant_id = %s
            WHERE id = %s
            ''',
            (reviewer_id, grant_id, application_id)
        )
        conn.commit()
        return jsonify({'code': 200, 'msg': f'已批准 {application.get("username") or "该部长"} 的放权申请'})
    finally:
        cursor.close()
        conn.close()

@app.route('/super-admin/delegation-applications/<int:application_id>/reject', methods=['POST'])
@super_admin_required
def reject_delegation_application(application_id):
    _ensure_schema_once()
    if getattr(g, 'base_user_role', None) != 'super_admin':
        return jsonify({'code': 403, 'msg': '仅主席可处理放权申请'}), 403

    reviewer_id = int((g.user_session or {}).get('user_id') or 0)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT id, username, status
            FROM delegation_applications
            WHERE id = %s
            LIMIT 1
            ''',
            (application_id,)
        )
        application = cursor.fetchone()
        if not application:
            return jsonify({'code': 404, 'msg': '放权申请不存在'}), 404
        if application.get('status') != 'pending':
            return jsonify({'code': 400, 'msg': '该放权申请已处理'}), 400

        cursor.execute(
            '''
            UPDATE delegation_applications
            SET status = 'rejected',
                is_urge = 0,
                reviewed_by = %s,
                reviewed_at = NOW()
            WHERE id = %s
            ''',
            (reviewer_id, application_id)
        )
        conn.commit()
        return jsonify({'code': 200, 'msg': f'已驳回 {application.get("username") or "该部长"} 的放权申请'})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/messages', methods=['GET'])
@admin_required
def get_admin_messages():
    _ensure_schema_once()
    _ensure_activities_schema_once()
    current_user_id = int((g.user_session or {}).get('user_id') or 0)
    base_role = getattr(g, 'base_user_role', None) or getattr(g, 'user_role', 'user')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        items = []
        if base_role == 'super_admin':
            cursor.execute(
                '''
                SELECT a.id, a.title, a.summary, a.status, a.created_at, a.updated_at, u.username
                FROM activities a
                LEFT JOIN users u ON u.id = a.created_by
                WHERE a.status = 'pending'
                ORDER BY a.created_at DESC, a.id DESC
                LIMIT 30
                '''
            )
            for row in cursor.fetchall() or []:
                items.append({
                    'id': f"activity:{row.get('id')}",
                    'raw_id': row.get('id'),
                    'item_type': 'activity_review',
                    'title': row.get('title') or '活动申请',
                    'subtitle': row.get('username') or '-',
                    'detail': row.get('summary') or '管理员提交了新的活动草稿',
                    'status': row.get('status') or 'pending',
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at'),
                    'can_open': True,
                    'can_urge': False,
                    'target_view': 'activity'
                })

            cursor.execute(
                '''
                SELECT id, user_id, username, reason, status, is_urge, created_at, updated_at
                FROM delegation_applications
                WHERE status = 'pending'
                ORDER BY created_at DESC, id DESC
                LIMIT 30
                '''
            )
            for row in cursor.fetchall() or []:
                items.append({
                    'id': f"delegation:{row.get('id')}",
                    'raw_id': row.get('id'),
                    'item_type': 'delegation_review',
                    'title': f"{row.get('username') or '部长'} 的放权申请",
                    'subtitle': f"用户 ID {row.get('user_id')}",
                    'detail': row.get('reason') or '申请临时主席权限',
                    'status': row.get('status') or 'pending',
                    'is_urge': int(row.get('is_urge') or 0),
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at'),
                    'can_open': True,
                    'can_urge': False,
                    'target_view': 'delegation'
                })
        else:
            cursor.execute(
                '''
                SELECT id, title, summary, status, created_at, updated_at
                FROM activities
                WHERE created_by = %s
                ORDER BY updated_at DESC, id DESC
                LIMIT 30
                ''',
                (current_user_id,)
            )
            for row in cursor.fetchall() or []:
                items.append({
                    'id': f"activity:{row.get('id')}",
                    'raw_id': row.get('id'),
                    'item_type': 'activity_submission',
                    'title': row.get('title') or '活动申请',
                    'subtitle': '活动投稿',
                    'detail': row.get('summary') or '已提交到主席审批',
                    'status': row.get('status') or 'pending',
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at'),
                    'can_open': True,
                    'can_urge': False,
                    'target_view': 'activity'
                })

            cursor.execute(
                '''
                SELECT
                    da.id,
                    da.reason,
                    da.status,
                    da.is_urge,
                    da.created_at,
                    da.updated_at,
                    da.reviewed_at,
                    g.starts_at,
                    g.expires_at,
                    g.revoked_at
                FROM delegation_applications da
                LEFT JOIN temporary_super_admin_grants g ON g.id = da.grant_id
                WHERE da.user_id = %s
                ORDER BY da.updated_at DESC, da.id DESC
                LIMIT 30
                ''',
                (current_user_id,)
            )
            for row in cursor.fetchall() or []:
                detail = row.get('reason') or '申请临时主席权限'
                if row.get('status') == 'approved' and row.get('expires_at'):
                    detail = f"已放权至 {row.get('expires_at')}"
                items.append({
                    'id': f"delegation:{row.get('id')}",
                    'raw_id': row.get('id'),
                    'item_type': 'delegation_application',
                    'title': '放权申请',
                    'subtitle': '临时主席权限',
                    'detail': detail,
                    'status': row.get('status') or 'pending',
                    'is_urge': int(row.get('is_urge') or 0),
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at'),
                    'can_open': True,
                    'can_urge': (row.get('status') == 'pending'),
                    'target_view': 'delegation'
                })

            cursor.execute(
                '''
                SELECT id, duration_hours, starts_at, expires_at, revoked_at, created_at
                FROM temporary_super_admin_grants
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT 10
                ''',
                (current_user_id,)
            )
            for row in cursor.fetchall() or []:
                status = 'scheduled'
                if row.get('revoked_at') is not None:
                    status = 'revoked'
                elif row.get('expires_at') and row.get('expires_at') <= datetime.now():
                    status = 'expired'
                elif row.get('starts_at') and row.get('starts_at') <= datetime.now():
                    status = 'approved'
                items.append({
                    'id': f"grant:{row.get('id')}",
                    'raw_id': row.get('id'),
                    'item_type': 'delegation_grant',
                    'title': '放权结果',
                    'subtitle': f"{row.get('duration_hours') or 0} 小时",
                    'detail': f"{row.get('starts_at')} 至 {row.get('expires_at')}",
                    'status': status,
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('expires_at') or row.get('created_at'),
                    'can_open': True,
                    'can_urge': False,
                    'target_view': 'delegation'
                })

        def _item_time_value(item):
            return item.get('updated_at') or item.get('created_at') or datetime.min

        items.sort(key=_item_time_value, reverse=True)
        return jsonify({'code': 200, 'data': items[:60]})
    finally:
        cursor.close()
        conn.close()

@app.route('/super-admin/delegations', methods=['GET'])
@super_admin_required
def list_super_admin_delegations():
    if getattr(g, 'base_user_role', None) != 'super_admin':
        return jsonify({'code': 403, 'msg': '仅主席可管理放权'}), 403
    _ensure_schema_once()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT
                g.id,
                g.user_id,
                u.username,
                u.nickname,
                u.department,
                g.granted_by,
                granter.username AS granted_by_username,
                g.duration_hours,
                g.starts_at,
                g.expires_at,
                g.revoked_at,
                CASE
                    WHEN g.revoked_at IS NOT NULL THEN 'revoked'
                    WHEN g.expires_at <= NOW() THEN 'expired'
                    WHEN g.starts_at <= NOW() AND g.expires_at > NOW() THEN 'active'
                    ELSE 'scheduled'
                END AS status
            FROM temporary_super_admin_grants g
            JOIN users u ON u.id = g.user_id
            JOIN users granter ON granter.id = g.granted_by
            ORDER BY
                CASE
                    WHEN g.revoked_at IS NULL AND g.starts_at <= NOW() AND g.expires_at > NOW() THEN 0
                    WHEN g.revoked_at IS NULL AND g.expires_at <= NOW() THEN 1
                    ELSE 2
                END,
                g.expires_at DESC,
                g.id DESC
            LIMIT 50
            '''
        )
        rows = cursor.fetchall() or []
        return jsonify({'code': 200, 'data': rows})
    finally:
        cursor.close()
        conn.close()

@app.route('/super-admin/delegations', methods=['POST'])
@super_admin_required
def create_super_admin_delegation():
    if getattr(g, 'base_user_role', None) != 'super_admin':
        return jsonify({'code': 403, 'msg': '仅主席可管理放权'}), 403
    _ensure_schema_once()
    data = request.json or {}
    target_user_id = int(data.get('target_user_id') or 0)
    duration_hours = int(data.get('duration_hours') or 0)
    granted_by = int((g.user_session or {}).get('user_id') or 0)

    if target_user_id <= 0:
        return jsonify({'code': 400, 'msg': '请选择要放权的管理员'}), 400
    if duration_hours < 1 or duration_hours > 720:
        return jsonify({'code': 400, 'msg': '时长需在 1 到 720 小时之间'}), 400
    if target_user_id == granted_by:
        return jsonify({'code': 400, 'msg': '不能给自己放权'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, username, role FROM users WHERE id = %s', (target_user_id,))
        target_user = cursor.fetchone()
        if not target_user:
            return jsonify({'code': 404, 'msg': '目标管理员不存在'}), 404
        if (target_user.get('role') or 'user') != 'admin':
            return jsonify({'code': 400, 'msg': '只能给部长临时授予主席权限'}), 400

        cursor.execute(
            '''
            SELECT id
            FROM temporary_super_admin_grants
            WHERE user_id = %s
              AND revoked_at IS NULL
              AND starts_at <= NOW()
              AND expires_at > NOW()
            ORDER BY id DESC
            LIMIT 1
            ''',
            (target_user_id,)
        )
        active_grant = cursor.fetchone()
        if active_grant:
            return jsonify({'code': 400, 'msg': '该管理员当前已拥有临时主席权限'}), 400

        cursor.execute(
            '''
            INSERT INTO temporary_super_admin_grants (
                user_id, granted_by, duration_hours, starts_at, expires_at
            ) VALUES (%s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL %s HOUR))
            ''',
            (target_user_id, granted_by, duration_hours, duration_hours)
        )
        delegation_id = cursor.lastrowid
        conn.commit()

        cursor.execute(
            '''
            SELECT id, user_id, duration_hours, starts_at, expires_at
            FROM temporary_super_admin_grants
            WHERE id = %s
            ''',
            (delegation_id,)
        )
        delegation = cursor.fetchone() or {}
        return jsonify({
            'code': 200,
            'msg': f'已向 {target_user.get("username") or "该管理员"} 放权 {duration_hours} 小时',
            'data': delegation
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/super-admin/delegations/<int:delegation_id>/revoke', methods=['POST'])
@super_admin_required
def revoke_super_admin_delegation(delegation_id):
    if getattr(g, 'base_user_role', None) != 'super_admin':
        return jsonify({'code': 403, 'msg': '仅主席可管理放权'}), 403
    _ensure_schema_once()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT id, user_id, revoked_at, expires_at
            FROM temporary_super_admin_grants
            WHERE id = %s
            LIMIT 1
            ''',
            (delegation_id,)
        )
        delegation = cursor.fetchone()
        if not delegation:
            return jsonify({'code': 404, 'msg': '放权记录不存在'}), 404
        if delegation.get('revoked_at') is not None:
            return jsonify({'code': 400, 'msg': '该放权已撤销'}), 400
        if delegation.get('expires_at') and delegation.get('expires_at') <= datetime.now():
            return jsonify({'code': 400, 'msg': '该放权已到期'}), 400

        cursor.execute(
            'UPDATE temporary_super_admin_grants SET revoked_at = NOW(), expires_at = NOW() WHERE id = %s',
            (delegation_id,)
        )
        conn.commit()
        return jsonify({'code': 200, 'msg': '已收回临时主席权限'})
    finally:
        cursor.close()
        conn.close()

# 9. 获取用户角色接口
@app.route('/user/role/<int:user_id>', methods=['GET'])
@user_required
def get_user_role(user_id):
    if not _is_self_or_admin(user_id):
        return jsonify({'code': 403, 'msg': '无权限查看该用户角色'}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    role_info = _get_role_info(user_id)
    role = role_info.get('effective_role') or user.get('role', 'user')
    is_admin = role in ['admin', 'super_admin']
    is_super_admin = role == 'super_admin'

    return jsonify({
        'code': 200, 
        'base_role': role_info.get('base_role') or user.get('role', 'user'),
        'role': role,
        'is_admin': is_admin,
        'is_super_admin': is_super_admin,
        'is_temporary_super_admin': bool(role_info.get('is_temporary_super_admin')),
        'grant_expires_at': role_info.get('grant_expires_at').strftime('%Y-%m-%d %H:%M:%S') if role_info.get('grant_expires_at') else None
    })

@app.route('/user/profile/<int:user_id>', methods=['PUT'])
@user_required
def update_user_profile(user_id):
    if int(g.user_session.get('user_id') or 0) != int(user_id):
        return jsonify({'code': 403, 'msg': '无权限修改该用户资料'}), 403

    data = request.json or {}
    password = data.get('password')
    username = (data.get('username') or '').strip()
    nickname = (data.get('nickname') or '').strip()

    if not password:
        return jsonify({'code': 400, 'msg': '缺少密码'}), 400
    if not username:
        return jsonify({'code': 400, 'msg': '用户名不能为空'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, password FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        if not user or not _verify_password_and_maybe_upgrade(user, password):
            return jsonify({'code': 401, 'msg': '密码错误'}), 401

        try:
            if nickname:
                cursor.execute('UPDATE users SET username = %s, nickname = %s WHERE id = %s', (username, nickname, user_id))
            else:
                cursor.execute('UPDATE users SET username = %s WHERE id = %s', (username, user_id))
            conn.commit()
            return jsonify({'code': 200, 'msg': '用户信息更新成功', 'username': username, 'nickname': nickname or None})
        except pymysql.err.IntegrityError:
            return jsonify({'code': 400, 'msg': '用户名已存在'}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/user/phone/<int:user_id>', methods=['PUT'])
@user_required
def update_user_phone(user_id):
    if int(g.user_session.get('user_id') or 0) != int(user_id):
        return jsonify({'code': 403, 'msg': '无权限修改该用户手机号'}), 403

    data = request.json or {}
    password = data.get('password')
    phone = str(data.get('phone') or '').strip()

    if not password:
        return jsonify({'code': 400, 'msg': '缺少密码'}), 400
    if not phone:
        return jsonify({'code': 400, 'msg': '手机号不能为空'}), 400
    if not re.fullmatch(r'\d{11}', phone):
        return jsonify({'code': 400, 'msg': '手机号格式不正确，必须为 11 位数字'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, username, phone, password FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        if not user or not _verify_password_and_maybe_upgrade(user, password):
            return jsonify({'code': 400, 'msg': '密码错误'}), 400
        if phone == str(user.get('phone') or '').strip():
            return jsonify({'code': 400, 'msg': '新手机号不能与当前手机号相同'}), 400

        cursor.execute(
            '''
            SELECT id
            FROM phone_change_requests
            WHERE user_id = %s AND approved = 0
            ORDER BY id DESC
            LIMIT 1
            ''',
            (user_id,)
        )
        pending = cursor.fetchone()
        if pending:
            return jsonify({'code': 400, 'msg': '您已有待审批的手机号修改申请，请先等待处理'}), 400

        cursor.execute(
            '''
            INSERT INTO phone_change_requests (user_id, username, current_phone, requested_phone)
            VALUES (%s, %s, %s, %s)
            ''',
            (user_id, user.get('username') or '', user.get('phone') or '', phone)
        )
        conn.commit()
        return jsonify({'code': 200, 'msg': '手机号修改申请已提交，请等待管理员审批', 'requested_phone': phone})
    finally:
        cursor.close()
        conn.close()

@app.route('/user/password/<int:user_id>', methods=['PUT'])
@user_required
def update_user_password(user_id):
    if int(g.user_session.get('user_id') or 0) != int(user_id):
        return jsonify({'code': 403, 'msg': '无权限修改该用户密码'}), 403

    data = request.json or {}
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({'code': 400, 'msg': '旧密码和新密码不能为空'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'SELECT id, username, nickname, student_no, phone, class_name, department, password FROM users WHERE id = %s',
            (user_id,)
        )
        user = cursor.fetchone()
        if not user or not _verify_password_and_maybe_upgrade(user, old_password):
            return jsonify({'code': 400, 'msg': '旧密码错误'}), 400

        password_error = _validate_password_policy(user, new_password)
        if password_error:
            return jsonify({'code': 400, 'msg': password_error}), 400

        cursor.execute('UPDATE users SET password = %s WHERE id = %s', (generate_password_hash(new_password), user_id))
        conn.commit()
        return jsonify({'code': 200, 'msg': '密码修改成功'})
    finally:
        cursor.close()
        conn.close()

# 测试路由
@app.route('/test', methods=['GET'])
def test():
    return jsonify({'code': 200, 'msg': '后端服务正常运行', 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

# 启动后端服务
if __name__ == '__main__':
    if os.getenv('PRINT_ROUTES') == '1':
        print("\n=== Flask应用启动 ===", flush=True)
        print("注册的路由:", flush=True)
        for rule in app.url_map.iter_rules():
            print(f"  {rule.methods} {rule.endpoint} {rule.rule}", flush=True)
        print("==================\n", flush=True)
    port = int(os.getenv('PORT') or 5000)
    host = (os.getenv('FLASK_HOST') or '0.0.0.0').strip()
    debug = _get_bool_env('FLASK_DEBUG', '1')
    logger.info(
        "starting server host=%s port=%s debug=%s db_host=%s db_name=%s request_log=%s",
        host,
        port,
        debug,
        DB_CONFIG.get('host'),
        DB_CONFIG.get('database'),
        _request_log_enabled(),
    )
    app.run(host=host, debug=debug, port=port)
