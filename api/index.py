from flask import Flask, request, jsonify
import time
import os
import json
import hashlib
import random

app = Flask(__name__)

ADMIN_PASS = os.environ.get('ADMIN_PASS', 'XcRNB-RNG-XcNBAA-713alo4937alp43791pqnc316')
DATA_FILE = '/tmp/player_data.json'

# ========== 数据读写 ==========
def load_player_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_player_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

player_data = load_player_data()

# ========== 设备ID生成 ==========
def get_device_id(device_info):
    info_string = f"{device_info.get('imei', '')}_{device_info.get('android_id', '')}_{device_info.get('mac', '')}_{device_info.get('serial', '')}_{device_info.get('model', '')}"
    return hashlib.sha256(info_string.encode()).hexdigest()

# ========== 根路径 ==========
@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'ok', 'time': int(time.time())})

# ========== 玩家接口 ==========

# 1. 注册/绑定设备
@app.route('/player/register', methods=['POST'])
def player_register():
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请传入设备信息'})
    
    device_info = data.get('device_info', {})
    if not device_info:
        return jsonify({'code': 400, 'msg': '设备信息不能为空'})
    
    device_id = get_device_id(device_info)
    now = int(time.time())
    
    # 检查是否已注册
    for pid, info in player_data.items():
        if info.get('device_id') == device_id:
            return jsonify({
                'code': 200,
                'msg': '设备已绑定',
                'player_id': pid,
                'gold': info.get('gold', 0)
            })
    
    # 新玩家
    player_id = f"P{now}{random.randint(1000, 9999)}"
    player_data[player_id] = {
        "device_id": device_id,
        "gold": 100,
        "register_time": now,
        "last_login": now,
        "device_info": device_info
    }
    save_player_data(player_data)
    
    return jsonify({
        'code': 200,
        'msg': '注册成功',
        'player_id': player_id,
        'gold': 100
    })

# 2. 查询金币
@app.route('/player/gold', methods=['GET'])
def get_gold():
    player_id = request.args.get('player_id', '')
    device_info_json = request.args.get('device_info', '')
    
    if player_id:
        if player_id not in player_data:
            return jsonify({'code': 404, 'msg': '玩家不存在'})
        return jsonify({
            'code': 200,
            'player_id': player_id,
            'gold': player_data[player_id].get('gold', 0)
        })
    
    if device_info_json:
        try:
            device_info = json.loads(device_info_json)
            device_id = get_device_id(device_info)
        except:
            return jsonify({'code': 400, 'msg': '设备信息格式错误'})
        
        for pid, info in player_data.items():
            if info.get('device_id') == device_id:
                return jsonify({
                    'code': 200,
                    'player_id': pid,
                    'gold': info.get('gold', 0)
                })
        return jsonify({'code': 404, 'msg': '未找到该设备绑定的玩家'})
    
    return jsonify({'code': 400, 'msg': '请传入player_id或device_info'})

# 3. 增加金币
@app.route('/player/gold/add', methods=['POST'])
def add_gold():
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请传入参数'})
    
    player_id = data.get('player_id', '')
    device_info = data.get('device_info', {})
    amount = data.get('amount', 0)
    
    try:
        amount = int(amount)
    except:
        return jsonify({'code': 400, 'msg': '金额必须为数字'})
    
    if amount <= 0:
        return jsonify({'code': 400, 'msg': '金额必须大于0'})
    
    if player_id and player_id in player_data:
        player_data[player_id]['gold'] = player_data[player_id].get('gold', 0) + amount
        save_player_data(player_data)
        return jsonify({
            'code': 200,
            'msg': f'增加 {amount} 金币成功',
            'player_id': player_id,
            'gold': player_data[player_id]['gold']
        })
    
    if device_info:
        device_id = get_device_id(device_info)
        for pid, info in player_data.items():
            if info.get('device_id') == device_id:
                player_data[pid]['gold'] = player_data[pid].get('gold', 0) + amount
                save_player_data(player_data)
                return jsonify({
                    'code': 200,
                    'msg': f'增加 {amount} 金币成功',
                    'player_id': pid,
                    'gold': player_data[pid]['gold']
                })
    
    return jsonify({'code': 404, 'msg': '玩家不存在'})

# 4. 扣除金币
@app.route('/player/gold/sub', methods=['POST'])
def sub_gold():
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请传入参数'})
    
    player_id = data.get('player_id', '')
    device_info = data.get('device_info', {})
    amount = data.get('amount', 0)
    
    try:
        amount = int(amount)
    except:
        return jsonify({'code': 400, 'msg': '金额必须为数字'})
    
    if amount <= 0:
        return jsonify({'code': 400, 'msg': '金额必须大于0'})
    
    if player_id and player_id in player_data:
        current = player_data[player_id].get('gold', 0)
        if current < amount:
            return jsonify({'code': 400, 'msg': f'金币不足，当前只有 {current} 金币'})
        player_data[player_id]['gold'] = current - amount
        save_player_data(player_data)
        return jsonify({
            'code': 200,
            'msg': f'扣除 {amount} 金币成功',
            'player_id': player_id,
            'gold': player_data[player_id]['gold']
        })
    
    if device_info:
        device_id = get_device_id(device_info)
        for pid, info in player_data.items():
            if info.get('device_id') == device_id:
                current = info.get('gold', 0)
                if current < amount:
                    return jsonify({'code': 400, 'msg': f'金币不足，当前只有 {current} 金币'})
                player_data[pid]['gold'] = current - amount
                save_player_data(player_data)
                return jsonify({
                    'code': 200,
                    'msg': f'扣除 {amount} 金币成功',
                    'player_id': pid,
                    'gold': player_data[pid]['gold']
                })
    
    return jsonify({'code': 404, 'msg': '玩家不存在'})

# ========== 管理员接口 ==========

# 5. 查看所有玩家
@app.route('/admin/players', methods=['GET'])
def admin_players():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    result = {}
    for pid, info in player_data.items():
        result[pid] = {
            "gold": info.get('gold', 0),
            "device_id": info.get('device_id', ''),
            "register_time": info.get('register_time', 0)
        }
    return jsonify({'code': 200, 'data': result})

# 6. 管理员设置金币
@app.route('/admin/gold/set', methods=['POST'])
def admin_set_gold():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请传入参数'})
    
    player_id = data.get('player_id', '')
    gold = data.get('gold', 0)
    
    try:
        gold = int(gold)
    except:
        return jsonify({'code': 400, 'msg': '金额必须为数字'})
    
    if gold < 0:
        return jsonify({'code': 400, 'msg': '金额不能为负数'})
    
    if player_id not in player_data:
        return jsonify({'code': 404, 'msg': '玩家不存在'})
    
    player_data[player_id]['gold'] = gold
    save_player_data(player_data)
    
    return jsonify({
        'code': 200,
        'msg': '设置成功',
        'player_id': player_id,
        'gold': gold
    })

# 7. 管理员删除玩家
@app.route('/admin/player/del', methods=['GET'])
def admin_del_player():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    player_id = request.args.get('player_id', '')
    
    if not player_id:
        return jsonify({'code': 400, 'msg': 'player_id不能为空'})
    
    if player_id not in player_data:
        return jsonify({'code': 404, 'msg': '玩家不存在'})
    
    del player_data[player_id]
    save_player_data(player_data)
    
    return jsonify({'code': 200, 'msg': f'删除成功: {player_id}'})

# ========== Vercel 需要 ==========
app = app

# ========== 本地运行 ==========
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
