from flask import Flask, request, jsonify
from flask_cors import CORS  # 新增这一行
import pymysql
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 新增这一行，启用跨域

# 下面的代码保持不变...
DB_CONFIG = {
    'host': '123.56.88.190',
    'port': 3306,
    'user': 'student',
    'password': '123456',
    'database': 'student',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

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
        return jsonify({'code': 200, 'msg': '登录成功', 'user_id': user['id']})
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
    cursor.execute('INSERT INTO punch_records (user_id) VALUES (%s)', (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'code': 200, 'msg': '打卡成功', 'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

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

# 启动后端服务
if __name__ == '__main__':
    app.run(debug=True, port=5000)