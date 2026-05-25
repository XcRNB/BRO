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
    
    if key not in card_data:
        return jsonify({'success': False, 'message': '卡密不存在'})
    
    d = card_data[key]
    
    if d['used'] >= d['max']:
        return jsonify({'success': False, 'message': f'卡密已达上限（最多 {d["max"]} 人）'})
    
    user_key = uid + "_" + fingerprint
    
    if user_key in d['users']:
        return jsonify({'success': True, 'message': f'验证成功（剩余 {d["max"] - d["used"]} 次）'})
    
    for existing_user in d['users']:
        existing_uid = existing_user.split("_")[0]
        if existing_uid == uid:
            return jsonify({'success': False, 'message': '此卡密已在其他设备使用'})
    
    d['used'] += 1
    d['users'].append(user_key)
    save_card_data(card_data)
    
    return jsonify({'success': True, 'message': f'验证成功（剩余 {d["max"] - d["used"]} 次）'})

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
            "已用": len(v["users"])
        }
    return jsonify({'code': 200, 'data': result})

@app.route('/admin/add', methods=['GET'])
def admin_add():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    key = request.args.get('key', '')
    max_uses = request.args.get('max', 1)
    
    try:
        max_uses = int(max_uses)
    except:
        return jsonify({'code': 400, 'msg': '参数格式错误'})
    
    if not key:
        return jsonify({'code': 400, 'msg': '卡密不能为空'})
    
    if key in card_data:
        return jsonify({'code': 400, 'msg': '卡密已存在'})
    
    card_data[key] = {
        "max": max_uses,
        "used": 0,
        "users": []
    }
    save_card_data(card_data)
    
    return jsonify({'code': 200, 'msg': f'添加成功: {key}，最多{max_uses}人使用'})

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
        result[key] = {
            "剩余次数": data["max"] - data["used"],
            "总次数": data["max"],
            "已用人数": len(data["users"])
        }
    return jsonify(result)

app = app
