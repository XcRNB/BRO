from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# 管理密码（必须和 AndLua 中的 ADMIN_PASS 一致）
ADMIN_PASS = "admin123"

# 卡密数据存储
card_data = {
    "XcRNG": {
        "max": 5,
        "used": 0,
        "users": [],
        "expiry": 1900000000
    },
}

# ========== 验证接口（Roblox 客户端调用）==========
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
        return jsonify({
            'success': True, 
            'message': f'验证成功（剩余 {d["max"] - d["used"]} 次）'
        })
    
    if d['used'] >= d['max']:
        return jsonify({
            'success': False, 
            'message': f'卡密已达上限（最多 {d["max"]} 人）'
        })
    
    d['used'] += 1
    d['users'].append(uid)
    
    return jsonify({
        'success': True, 
        'message': f'验证成功（剩余 {d["max"] - d["used"]} 次）'
    })

# ========== 添加卡密接口（AndLua 调用）==========
@app.route('/admin/add', methods=['POST'])
def add_key():
    data = request.get_json()
    
    if not data or data.get('pass') != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    key = data.get('key')
    max_uses = data.get('max', 1)
    expiry = data.get('expiry', 1900000000)
    
    if not key:
        return jsonify({'code': 400, 'msg': '卡密不能为空'})
    
    if key in card_data:
        return jsonify({'code': 400, 'msg': '卡密已存在'})
    
    card_data[key] = {
        "max": max_uses,
        "used": 0,
        "users": [],
        "expiry": expiry
    }
    
    return jsonify({'code': 200, 'msg': f'添加成功: {key}'})

# ========== 删除卡密接口（AndLua 调用）==========
@app.route('/admin/del', methods=['POST'])
def del_key():
    data = request.get_json()
    
    if not data or data.get('pass') != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    key = data.get('key')
    
    if key not in card_data:
        return jsonify({'code': 400, 'msg': '卡密不存在'})
    
    del card_data[key]
    return jsonify({'code': 200, 'msg': f'删除成功: {key}'})

# ========== 列出卡密接口（AndLua 调用）==========
@app.route('/admin/list', methods=['GET'])
def list_keys():
    pwd = request.args.get('pass', '')
    
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    result = {}
    for k, v in card_data.items():
        result[k] = {
            "剩余": v["max"] - v["used"],
            "总数": v["max"],
            "已用": v["used"],
            "过期时间": v["expiry"]
        }
    
    return jsonify({'code': 200, 'data': result})

# ========== 根路径测试 ==========
@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'ok', 'time': int(time.time())})

app = app
