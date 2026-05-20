from flask import Flask, request, jsonify
import time
import os
import jwt
import urllib.request
import json

app = Flask(__name__)

SECRET_KEY = os.environ.get('SECRET_KEY', '8x7k3m9p2q5w1v4r6t8y2u4i7o0p9a3s')

# Upstash REST API
REDIS_REST_URL = os.environ.get('UPSTASH_REDIS_REST_URL', '')
REDIS_REST_TOKEN = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')

def redis_get(key):
    url = f"{REDIS_REST_URL}/get/{key}"
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {REDIS_REST_TOKEN}'}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get('result')
    except:
        return None

def redis_setex(key, seconds, value):
    url = f"{REDIS_REST_URL}/setex/{key}/{seconds}"
    req = urllib.request.Request(
        url,
        data=json.dumps(value).encode(),
        headers={
            'Authorization': f'Bearer {REDIS_REST_TOKEN}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    try:
        urllib.request.urlopen(req, timeout=5)
        return True
    except:
        return False

# 有效卡密列表
valid_keys = {
    "XcRNG": {"expiry": 1900000000},  # 2030年过期
}

def create_verification_token(user_id, card_key):
    payload = {
        'user_id': user_id,
        'card_key': card_key,
        'exp': int(time.time()) + 3600,
        'iat': int(time.time())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

@app.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': int(time.time())})

@app.route('/verify', methods=['GET'])
def verify_get():
    card_key = request.args.get('key', '')
    user_id = request.args.get('userId', '')
    
    current_time = int(time.time())
    
    if card_key not in valid_keys:
        return jsonify({'success': False, 'message': '卡密无效'})
    
    if valid_keys[card_key]['expiry'] < current_time:
        return jsonify({'success': False, 'message': '卡密已过期'})
    
    used_key = f"used:{card_key}"
    existing_user = redis_get(used_key)
    
    if existing_user:
        if existing_user != user_id:
            return jsonify({'success': False, 'message': '卡密已被其他用户使用'})
        else:
            token = create_verification_token(user_id, card_key)
            return jsonify({'success': True, 'message': '验证成功', 'token': token})
    
    redis_setex(used_key, 86400 * 30, user_id)
    token = create_verification_token(user_id, card_key)
    
    return jsonify({'success': True, 'message': '验证成功', 'token': token})

@app.route('/verify', methods=['POST'])
def verify_post():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效请求'})
    
    card_key = data.get('key', '').strip()
    user_id = str(data.get('userId', ''))
    current_time = int(time.time())
    
    if card_key not in valid_keys:
        return jsonify({'success': False, 'message': '卡密无效'})
    
    if valid_keys[card_key]['expiry'] < current_time:
        return jsonify({'success': False, 'message': '卡密已过期'})
    
    used_key = f"used:{card_key}"
    existing_user = redis_get(used_key)
    
    if existing_user:
        if existing_user != user_id:
            return jsonify({'success': False, 'message': '卡密已被其他用户使用'})
        else:
            token = create_verification_token(user_id, card_key)
            return jsonify({'success': True, 'message': '验证成功', 'token': token})
    
    redis_setex(used_key, 86400 * 30, user_id)
    token = create_verification_token(user_id, card_key)
    
    return jsonify({'success': True, 'message': '验证成功', 'token': token})

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json()
    token = data.get('token', '') if data else ''
    
    if not token:
        return jsonify({'success': False}), 401
    
    try:
        jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 401

app = app
