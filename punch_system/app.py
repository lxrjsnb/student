from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from datetime import datetime
from functools import wraps
import logging
import sys

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization", "X-User-Role"]}})

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger(__name__)

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.DEBUG)
werkzeug_logger.addHandler(logging.StreamHandler(sys.stdout))

@app.after_request
def after_request(response):
    print(f"\n=== 响应信息 ===", flush=True)
    print(f"状态码: {response.status_code}", flush=True)
    print(f"路径: {request.path}", flush=True)
    print(f"方法: {request.method}", flush=True)
    print(f"==================\n", flush=True)
    return response

DB_CONFIG = {
    'host': '123.56.88.190',
    'port': 3306,
    'user': 'student',
    'password': '123456',
    'database': 'student',
    'cursorclass': pymysql.cursors.DictCursor
}

ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin123'
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth:
            return jsonify({'code': 401, 'msg': '需要登录'}), 401
        
        token = auth.replace('Bearer ', '')
        if token != 'admin_token':
            return jsonify({'code': 403, 'msg': '需要管理员权限'}), 403
        
        user_role = request.headers.get('X-User-Role')
        if user_role not in ['admin', 'super_admin']:
            return jsonify({'code': 403, 'msg': '需要管理员权限'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth:
            return jsonify({'code': 401, 'msg': '需要登录'}), 401
        
        token = auth.replace('Bearer ', '')
        if token != 'admin_token':
            return jsonify({'code': 403, 'msg': '需要超级管理员权限'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# 1. 注册接口
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'code': 400, 'msg': '用户名和密码不能为空'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
        conn.commit()
        return jsonify({'code': 200, 'msg': '注册成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 400, 'msg': '用户名已存在'}), 400
    finally:
        cursor.close()
        conn.close()

# 2. 登录接口
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'code': 400, 'msg': '用户名和密码不能为空'}), 400

    if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
        return jsonify({'code': 200, 'msg': '登录成功', 'user_id': 0, 'username': username, 'score': 0, 'is_admin': True})

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        role = user.get('role', 'user')
        is_admin = role in ['admin', 'super_admin']
        is_super_admin = role == 'super_admin'
        return jsonify({
            'code': 200, 
            'msg': '登录成功', 
            'user_id': user['id'], 
            'username': user['username'], 
            'score': user.get('score', 0), 
            'is_admin': is_admin,
            'is_super_admin': is_super_admin,
            'role': role
        })
    else:
        return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

# 3. 打卡接口
@app.route('/punch', methods=['POST'])
def punch():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少用户ID'}), 400

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
    
    # 自动加0.5分
    cursor.execute('UPDATE users SET score = score + 0.5 WHERE id = %s', (user_id,))
    
    conn.commit()
    
    # 获取更新后的分数
    cursor.execute('SELECT score FROM users WHERE id = %s', (user_id,))
    score_result = cursor.fetchone()
    new_score = score_result['score'] if score_result else 0
    
    cursor.close()
    conn.close()

    return jsonify({
        'code': 200, 
        'msg': '打卡成功，获得0.5分', 
        'time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
        'score': new_score,
        'points_gained': 0.5
    })

# 4. 查询打卡记录接口
@app.route('/records/<int:user_id>', methods=['GET'])
def get_records(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM punch_records WHERE user_id = %s ORDER BY punch_time DESC', (user_id,))
    records = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({'code': 200, 'data': records})

# 5. 管理员登录接口
@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
        return jsonify({
            'code': 200, 
            'msg': '登录成功', 
            'token': 'admin_token',
            'role': 'super_admin',
            'is_admin': True,
            'is_super_admin': True
        })
    else:
        return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

# 6. 获取所有用户列表（管理员）
@app.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, score FROM users ORDER BY id')
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({'code': 200, 'data': users})

# 7. 获取所有打卡记录（管理员）
@app.route('/admin/records', methods=['GET'])
@admin_required
def get_all_records():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pr.id, pr.user_id, u.username, pr.punch_time
        FROM punch_records pr
        JOIN users u ON pr.user_id = u.id
        ORDER BY pr.punch_time DESC
    ''')
    records = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({'code': 200, 'data': records})

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

# 9. 修改用户分数（管理员）
@app.route('/admin/users/<int:user_id>/score', methods=['PUT'])
@admin_required
def update_user_score(user_id):
    data = request.json
    score = data.get('score')
    
    if score is None:
        return jsonify({'code': 400, 'msg': '缺少分数参数'}), 400
    
    try:
        score = float(score)
    except (ValueError, TypeError):
        return jsonify({'code': 400, 'msg': '分数必须是数字'}), 400
    
    if score < 0:
        return jsonify({'code': 400, 'msg': '分数不能为负数'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET score = %s WHERE id = %s', (score, user_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'code': 200, 'msg': '分数修改成功', 'score': score})

# 6. 申请管理员接口
@app.route('/admin/apply', methods=['POST'])
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
def get_user_role(user_id):
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

# 测试路由
@app.route('/test', methods=['GET'])
def test():
    return jsonify({'code': 200, 'msg': '后端服务正常运行', 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

# 启动后端服务
if __name__ == '__main__':
    print("\n=== Flask应用启动 ===", flush=True)
    print("注册的路由:", flush=True)
    for rule in app.url_map.iter_rules():
        print(f"  {rule.methods} {rule.endpoint} {rule.rule}", flush=True)
    print("==================\n", flush=True)
    app.run(debug=True, port=5000)