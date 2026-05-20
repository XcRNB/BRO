from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# 管理密码（和 AndLua 保持一致）
ADMIN_PASS = "admin123"

# 卡密数据
card_data = {
    "XcRNG": {
        "max": 5,
        "used": 0,
        "users": [],
        "expiry": 1900000000
    },
}

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'ok', 'time': int(time.time())})

@app.route('/verify', methods=['GET'])
def verify():
    key = request.args.get('key', '')
    uid = request.args.get('userId', '')
    now = int(time.time())
    
    if key not in card_data:
        return jsonify({'success': False, 'message': '卡密不存在'})
    
    d = card_data[key]
    
    if d['expiry'] < now:
        return jsonify({'success': False, 'message': '卡密已过期'})
    
    if uid in d['users']:
        return jsonify({'success': True, 'message': f'验证成功（剩余 {d["max"] - d["used"]} 次）'})
    
    if d['used'] >= d['max']:
        return jsonify({'success': False, 'message': f'卡密已达上限（最多 {d["max"]} 人）'})
    
    d['used'] += 1
    d['users'].append(uid)
    
    return jsonify({'success': True, 'message': f'验证成功（剩余 {d["max"] - d["used"]} 次）'})

# ========== 管理接口 ==========
@app.route('/admin/list', methods=['GET'])
def admin_list():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    result = {}
    for k, v in card_data.items():
        result[k] = {
            "剩余": v["max"] - v["used"],
            "总数": v["max"],
            "已用": v["used"]
        }
    return jsonify({'code': 200, 'data': result})

@app.route('/admin/add', methods=['POST'])
def admin_add():
    data = request.get_json()
    if not data or data.get('pass') != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    key = data.get('key')
    if not key:
        return jsonify({'code': 400, 'msg': '卡密不能为空'})
    
    if key in card_data:
        return jsonify({'code': 400, 'msg': '卡密已存在'})
    
    card_data[key] = {
        "max": data.get('max', 1),
        "used": 0,
        "users": [],
        "expiry": data.get('expiry', 1900000000)
    }
    return jsonify({'code': 200, 'msg': f'添加成功: {key}'})

@app.route('/admin/del', methods=['POST'])
def admin_del():
    data = request.get_json()
    if not data or data.get('pass') != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    key = data.get('key')
    if key not in card_data:
        return jsonify({'code': 400, 'msg': '卡密不存在'})
    
    del card_data[key]
    return jsonify({'code': 200, 'msg': f'删除成功: {key}'})

@app.route('/stats', methods=['GET'])
def stats():
    result = {}
    for key, data in card_data.items():
        result[key] = {
            "剩余次数": data["max"] - data["used"],
            "总次数": data["max"],
            "已用人数": data["used"],
            "过期时间戳": data["expiry"],
            "是否过期": data["expiry"] < int(time.time())
        }
    return jsonify(result)

app = app
