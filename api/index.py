from flask import Flask, request, jsonify
import time
import os
import json
import hashlib

app = Flask(__name__)

ADMIN_PASS = os.environ.get('ADMIN_PASS', 'XcRNB-RNG-XcNBAA-713alo4937alp43791pqnc316')

DATA_FILE = '/app/data/player_data.json'

# 获取设备唯一标识（手机信息加密）
def get_device_id(device_info):
    """
    传入设备信息字典，返回唯一设备ID
    设备信息包括：IMEI、AndroidID、MAC地址等
    用SHA256加密确保不可伪造
    """
    info_string = f"{device_info.get('imei', '')}_{device_info.get('android_id', '')}_{device_info.get('mac', '')}_{device_info.get('serial', '')}"
    return hashlib.sha256(info_string.encode()).hexdigest()

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
        json.dump(data, f)

player_data = load_player_data()

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'ok', 'time': int(time.time())})

# ========== 玩家接口 ==========

# 1. 注册/登录 - 绑定手机设备
@app.route('/player/register', methods=['POST'])
def player_register():
    """
    玩家首次绑定设备
    传入: device_info (手机信息JSON)
    返回: player_id, 金币初始值
    """
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
    
    # 新玩家注册
    player_id = f"P{now}{str(len(player_data) + 1).zfill(4)}"
    player_data[player_id] = {
        "device_id": device_id,
        "gold": 100,  # 初始金币
        "register_time": now,
        "last_login": now,
        "device_info": device_info  # 保存原始信息便于查证
    }
    save_player_data(player_data)
    
    return jsonify({
        'code': 200,
        'msg': '注册成功',
        'player_id': player_id,
        'gold': 100
    })

# 2. 获取玩家金币
@app.route('/player/gold', methods=['GET'])
def get_gold():
    """
    获取玩家金币
    传入: player_id 或 device_info
    """
    player_id = request.args.get('player_id', '')
    device_info_json = request.args.get('device_info', '')
    
    if player_id:
        # 通过player_id查询
        if player_id not in player_data:
            return jsonify({'code': 404, 'msg': '玩家不存在'})
        return jsonify({
            'code': 200,
            'player_id': player_id,
            'gold': player_data[player_id].get('gold', 0)
        })
    
    elif device_info_json:
        # 通过设备信息查询
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
    """
    增加金币
    传入: player_id 或 device_info, amount
    """
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
    
    # 通过player_id查找
    if player_id and player_id in player_data:
        player_data[player_id]['gold'] = player_data[player_id].get('gold', 0) + amount
        save_player_data(player_data)
        return jsonify({
            'code': 200,
            'msg': f'增加 {amount} 金币成功',
            'player_id': player_id,
            'gold': player_data[player_id]['gold']
        })
    
    # 通过设备信息查找
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
    """
    扣除金币
    传入: player_id 或 device_info, amount
    """
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
    
    # 通过player_id查找
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
    
    # 通过设备信息查找
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

# 5. 管理员 - 查看所有玩家
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
            "register_time": info.get('register_time', 0),
            "last_login": info.get('last_login', 0)
        }
    return jsonify({'code': 200, 'data': result})

# 6. 管理员 - 修改金币
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
        'msg': f'设置成功',
        'player_id': player_id,
        'gold': gold
    })

# 7. 管理员 - 删除玩家
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
