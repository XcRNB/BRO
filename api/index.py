from flask import Flask, request, jsonify
import time
import os
import json

app = Flask(__name__)

ADMIN_PASS = os.environ.get('ADMIN_PASS', 'XcRNB-RNG-XcNBAA-713alo4937alp43791pqnc316')

DATA_FILE = '/app/data/card_data.json'

def load_card_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_card_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

card_data = load_card_data()

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'ok', 'time': int(time.time())})

@app.route('/verify', methods=['GET'])
def verify():
    key = request.args.get('key', '')
    uid = request.args.get('userId', '')
    fingerprint = request.args.get('fingerprint', '')
    now = int(time.time())
    
    if key not in card_data:
        return jsonify({'success': False, 'message': '卡密不存在'})
    
    d = card_data[key]
    
    if d['used'] == 0 and d.get('start_time') is None:
        d['start_time'] = now
        save_card_data(card_data)
    
    if 'duration' in d and d['start_time'] is not None:
        expire_time = d['start_time'] + d['duration'] * 86400
        if expire_time < now:
            return jsonify({'success': False, 'message': '卡密已过期'})
    
    if d['used'] >= d['max']:
        return jsonify({'success': False, 'message': '卡密已达上限'})
    
    user_key = uid + "_" + fingerprint
    
    if user_key in d['users']:
        remaining = d['max'] - d['used']
        if 'duration' in d and d['start_time'] is not None:
            expire_time = d['start_time'] + d['duration'] * 86400
            remaining_days = (expire_time - now) // 86400
            return jsonify({'success': True, 'message': f'验证成功，剩余{remaining}次，还剩{remaining_days}天'})
        return jsonify({'success': True, 'message': f'验证成功，剩余{remaining}次'})
    
    for existing_user in d['users']:
        existing_uid = existing_user.split("_")[0]
        if existing_uid == uid:
            return jsonify({'success': False, 'message': '此卡密已在其他设备使用'})
    
    d['used'] += 1
    d['users'].append(user_key)
    save_card_data(card_data)
    
    remaining = d['max'] - d['used']
    if 'duration' in d and d['start_time'] is not None:
        expire_time = d['start_time'] + d['duration'] * 86400
        remaining_days = (expire_time - now) // 86400
        return jsonify({'success': True, 'message': f'验证成功，剩余{remaining}次，还剩{remaining_days}天'})
    
    return jsonify({'success': True, 'message': f'验证成功，剩余{remaining}次'})

@app.route('/admin/add', methods=['GET'])
def admin_add():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    key = request.args.get('key', '')
    max_uses = request.args.get('max', 1)
    duration = request.args.get('duration', 30)
    
    try:
        max_uses = int(max_uses)
        duration = int(duration)
    except:
        return jsonify({'code': 400, 'msg': '参数格式错误'})
    
    if not key:
        return jsonify({'code': 400, 'msg': '卡密不能为空'})
    
    if key in card_data:
        return jsonify({'code': 400, 'msg': '卡密已存在'})
    
    card_data[key] = {
        "max": max_uses,
        "used": 0,
        "users": [],
        "duration": duration,
        "start_time": None
    }
    save_card_data(card_data)
    
    return jsonify({'code': 200, 'msg': f'添加成功: {key}，最多{max_uses}人，有效{duration}天'})

@app.route('/admin/list', methods=['GET'])
def admin_list():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    result = {}
    for k, v in card_data.items():
        remaining_days = 0
        if v.get('start_time') and v.get('duration'):
            expire_time = v['start_time'] + v['duration'] * 86400
            remaining_days = max(0, (expire_time - int(time.time())) // 86400)
        
        result[k] = {
            "剩余次数": v["max"] - v["used"],
            "总次数": v["max"],
            "已用人数": len(v["users"]),
            "有效期天数": v.get("duration", 0),
            "剩余天数": remaining_days,
            "状态": "已过期" if v.get('start_time') and v.get('duration') and v['start_time'] + v['duration'] * 86400 < int(time.time()) else "有效"
        }
    return jsonify({'code': 200, 'data': result})

@app.route('/admin/del', methods=['GET'])
def admin_del():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    key = request.args.get('key', '')
    
    if not key:
        return jsonify({'code': 400, 'msg': '卡密不能为空'})
    
    if key not in card_data:
        return jsonify({'code': 400, 'msg': '卡密不存在'})
    
    del card_data[key]
    save_card_data(card_data)
    
    return jsonify({'code': 200, 'msg': f'删除成功: {key}'})

@app.route('/stats', methods=['GET'])
def stats():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    result = {}
    for key, data in card_data.items():
        remaining_days = 0
        if data.get('start_time') and data.get('duration'):
            expire_time = data['start_time'] + data['duration'] * 86400
            remaining_days = max(0, (expire_time - int(time.time())) // 86400)
        
        result[key] = {
            "剩余次数": data["max"] - data["used"],
            "总次数": data["max"],
            "已用人数": len(data["users"]),
            "有效期天数": data.get("duration", 0),
            "剩余天数": remaining_days,
            "开始时间": data.get("start_time", "未使用")
        }
    return jsonify(result)

app = app
