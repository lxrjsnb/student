import logging
import os
import re
import secrets
import sys
import threading
import time
from datetime import datetime, timedelta
from functools import wraps

from db_env import get_db_config, load_env_file

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
    return pymysql.connect(**DB_CONFIG)

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
            _punch_schema_checked = True
        except Exception as e:
            logger.error(f"初始化 punch_records.approved 失败（可忽略但会影响审批）: {e}")
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
    if not user_id:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        try:
            cursor.execute('SELECT role FROM users WHERE id = %s', (user_id,))
            row = cursor.fetchone() or {}
            return row.get('role') or 'user'
        except Exception:
            cursor.execute('SELECT is_admin FROM users WHERE id = %s', (user_id,))
            row = cursor.fetchone() or {}
            return 'admin' if int(row.get('is_admin') or 0) == 1 else 'user'
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

        role = _get_user_role(session.get('user_id'))
        if role not in ['admin', 'super_admin']:
            return jsonify({'code': 403, 'msg': '需要管理员权限'}), 403

        g.user_session = session
        g.user_role = role
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

        g.user_session = session
        g.user_role = _get_user_role(session.get('user_id'))
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

        role = _get_user_role(session.get('user_id'))
        if role != 'super_admin':
            return jsonify({'code': 403, 'msg': '需要超级管理员权限'}), 403

        g.user_session = session
        g.user_role = role
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
        role = user.get('role', 'user')
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
            'is_admin': is_admin,
            'is_super_admin': is_super_admin,
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
        role = user.get('role', 'user')
        return jsonify({
            'code': 200,
            'user_id': user['id'],
            'nickname': user.get('nickname') or user['username'],
            'username': user['username'],
            'student_no': user.get('student_no') or '',
            'phone': user.get('phone') or '',
            'department': user.get('department') or '',
            'role': role,
            'is_admin': role in ['admin', 'super_admin'],
            'is_super_admin': role == 'super_admin',
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

    role = user.get('role', 'user')
    if role not in ['admin', 'super_admin']:
        return jsonify({'code': 403, 'msg': '需要管理员账号'}), 403

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
        'is_admin': True,
        'is_super_admin': role == 'super_admin',
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
        SELECT pr.id, pr.user_id, u.username, pr.punch_time, pr.approved, pr.is_urge
        FROM punch_records pr
        JOIN users u ON pr.user_id = u.id
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
                SET approved = 1, is_urge = 0
                WHERE id IN ({placeholders}) AND approved = 0
                ''',
                tuple(punch_ids)
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
                SET approved = -1, is_urge = 0
                WHERE id IN ({placeholders}) AND approved = 0
                ''',
                tuple(punch_ids)
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

    role = user.get('role', 'user')
    is_admin = role in ['admin', 'super_admin']
    is_super_admin = role == 'super_admin'

    return jsonify({
        'code': 200, 
        'role': role,
        'is_admin': is_admin,
        'is_super_admin': is_super_admin
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
