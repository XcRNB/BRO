from flask import Flask, request, jsonify
import time
import os
import json
import urllib.request

app = Flask(__name__)

ADMIN_PASS = "admin123"

# Upstash Redis REST API
REDIS_URL = os.environ.get('UPSTASH_REDIS_REST_URL', '')
REDIS_TOKEN = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')

def redis_get(key):
    """从 Redis 获取数据"""
    url = f"{REDIS_URL}/get/{key}"
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {REDIS_TOKEN}'}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get('result')
    except:
        return None

def redis_set(key, value):
    """存入 Redis"""
    url = f"{REDIS_URL}/set/{key}"
    data = json.dumps(value).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Bearer {REDIS_TOKEN}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    try:
        urllib.request.urlopen(req, timeout=5)
        return True
    except:
        return False

def load_card_data():
    """从 Redis 加载卡密数据"""
    data = redis_get('card_data')
    if data:
        return json.loads(data)
    # 默认数据
    default = {
        "XcRNG": {"max": 5, "used": 0, "users": [], "expiry": 1900000000}
    }
    redis_set('card_data', json.dumps(default))
    return default

def save_card_data(data):
    """保存卡密数据到 Redis"""
    redis_set('card_data', json.dumps(data))

# 初始化
card_data = load_card_data()

# ========== API 接口（需要时自动保存）==========
@app.route('/admin/add', methods=['GET'])
def admin_add():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    key = request.args.get('key', '')
    max_uses = int(request.args.get('max', 1))
    expiry = int(request.args.get('expiry', 1900000000))
    
    if key in card_data:
        return jsonify({'code': 400, 'msg': '卡密已存在'})
    
    card_data[key] = {"max": max_uses, "used": 0, "users": [], "expiry": expiry}
    save_card_data(card_data)  # 保存到 Redis
    
    return jsonify({'code': 200, 'msg': f'添加成功: {key}'})

@app.route('/admin/del', methods=['GET'])
def admin_del():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    key = request.args.get('key', '')
    if key not in card_data:
        return jsonify({'code': 400, 'msg': '卡密不存在'})
    
    del card_data[key]
    save_card_data(card_data)
    
    return jsonify({'code': 200, 'msg': f'删除成功: {key}'})

@app.route('/admin/list', methods=['GET'])
def admin_list():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    result = {}
    for k, v in card_data.items():
        result[k] = {"剩余": v["max"] - v["used"], "总数": v["max"], "已用": v["used"]}
    return jsonify({'code': 200, 'data': result})

# ... 其他接口类似，每次修改后调用 save_card_data
