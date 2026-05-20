from flask import Flask, request, jsonify
import time
import os

app = Flask(__name__)

SECRET_KEY = os.environ.get('SECRET_KEY', '8x7k3m9p2q5w1v4r6t8y2u4i7o0p9a3s')

# 有效卡密列表
valid_keys = {
    "XcRNG": {"expiry": 1746230400},  # 2026-05-21 过期
}

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
    
    return jsonify({'success': True, 'message': '验证成功'})

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
    
    return jsonify({'success': True, 'message': '验证成功'})

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    return jsonify({'success': True})

@app.route('/heartbeat', methods=['GET'])
def heartbeat_get():
    return jsonify({'success': True})

app = app
