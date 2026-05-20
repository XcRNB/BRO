from flask import Flask, request, jsonify
import hashlib
import time
import jwt
import os
import redis
import json

app = Flask(__name__)

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-to-random-32-chars')
redis_client = redis.from_url(os.environ.get('REDIS_URL'))

def create_verification_token(user_id, card_key):
    payload = {
        'user_id': user_id,
        'card_key': card_key,
        'exp': int(time.time()) + 3600,
        'iat': int(time.time())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

@app.route('/verify', methods=['POST'])
def verify():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效请求'})
        
        card_key = data.get('key', '').strip()
        user_id = str(data.get('userId', ''))
        fingerprint = data.get('fingerprint', '')
        client_timestamp = int(request.headers.get('X-Timestamp', 0))
        
        current_time = int(time.time())
        if abs(current_time - client_timestamp) > 60:
            return jsonify({'success': False, 'message': '请求超时'})
        
        if len(card_key) < 6:
            return jsonify({'success': False, 'message': '卡密格式错误'})
        
        used_key = f"used:{card_key}"
        existing_user = redis_client.get(used_key)
        
        if existing_user:
            if existing_user.decode() != user_id:
                return jsonify({'success': False, 'message': '卡密已被其他用户使用'})
            else:
                token = create_verification_token(user_id, card_key)
                return jsonify({
                    'success': True, 
                    'message': '验证成功',
                    'token': token
                })
        
        # 有效卡密列表
        valid_keys = {
            "TEST-2024-ABCD": {"expiry": 1798761600},
        }
        
        if card_key not in valid_keys:
            return jsonify({'success': False, 'message': '卡密不存在'})
        
        if valid_keys[card_key]['expiry'] < current_time:
            return jsonify({'success': False, 'message': '卡密已过期'})
        
        redis_client.setex(used_key, 86400 * 30, user_id)
        token = create_verification_token(user_id, card_key)
        
        return jsonify({
            'success': True,
            'message': '验证成功',
            'token': token
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'})

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    try:
        data = request.get_json()
        token = data.get('token', '')
        
        if not token:
            return jsonify({'success': False}), 401
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if user_id:
                redis_client.setex(f"heartbeat:{user_id}", 45, int(time.time()))
            
            return jsonify({'success': True})
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Token无效'}), 401
            
    except Exception as e:
        return jsonify({'success': False}), 500

@app.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': int(time.time())})

app = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
