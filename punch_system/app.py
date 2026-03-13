from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from datetime import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

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
        if not auth or auth != 'Bearer admin_token':
            return jsonify({'code': 403, 'msg': '需要管理员权限'}), 403
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

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return jsonify({'code': 200, 'msg': '登录成功', 'user_id': user['id'], 'username': user['username'], 'score': user.get('score', 0)})
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
        return jsonify({'code': 200, 'msg': '登录成功', 'token': 'admin_token'})
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

# 启动后端服务
if __name__ == '__main__':
    app.run(debug=True, port=5000)