from flask import Flask, request, jsonify
import time
import os
import json
import urllib.request

app = Flask(__name__)

ADMIN_PASS = "admin123"

# Upstash Redis REST API 配置
REDIS_URL = os.environ.get('UPSTASH_REDIS_REST_URL', '')
REDIS_TOKEN = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')

def redis_get(key):
    """从 Redis 获取数据"""
    try:
        url = f"{REDIS_URL}/get/{key}"
        req = urllib.request.Request(
            url,
            headers={'Authorization': f'Bearer {REDIS_TOKEN}'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            result = data.get('result')
            if result:
                return json.loads(result)
            return None
    except Exception as e:
        print(f"Redis GET 错误: {e}")
        return None

def redis_set(key, value):
    """存入 Redis"""
    try:
        url = f"{REDIS_URL}/set/{key}"
        data = json.dumps(json.dumps(value)).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Authorization': f'Bearer {REDIS_TOKEN}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception as e:
        print(f"Redis SET 错误: {e}")
        return False

def load_card_data():
    """从 Redis 加载卡密数据"""
    data = redis_get('card_data')
    if data:
        return data
    # 默认数据
    default = {
        "XcRNG": {"max": 5, "used": 0, "users": [], "expiry": 1900000000}
    }
    redis_set('card_data', default)
    return default

def save_card_data(data):
    """保存卡密数据到 Redis"""
    redis_set('card_data', data)

# 初始化加载数据
card_data = load_card_data()

# ========== 根路径 ==========
@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'ok', 'time': int(time.time())})

# ========== 验证卡密 ==========
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
    save_card_data(card_data)
    
    return jsonify({'success': True, 'message': f'验证成功（剩余 {d["max"] - d["used"]} 次）'})

# ========== 添加卡密（GET）==========
@app.route('/admin/add', methods=['GET'])
def admin_add():
    pwd = request.args.get('pass', '')
    if pwd != ADMIN_PASS:
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    key = request.args.get('key', '')
    max_uses = request.args.get('max', 1)
    expiry = request.args.get('expiry', 1900000000)
    
    try:
        max_uses = int(max_uses)
        expiry = int(expiry)
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
        "expiry": expiry
    }
    save_card_data(card_data)
    
    return jsonify({'code': 200, 'msg': f'添加成功: {key}'})

# ========== 删除卡密（GET）==========
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

# ========== 查看卡密列表 ==========
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

# ========== 统计查看 ==========
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
