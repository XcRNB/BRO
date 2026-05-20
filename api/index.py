from flask import Flask, request, jsonify
import time

app = Flask(__name__)

card_data = {
    "XcRNG": {
        "max": 5,
        "used": 0,
        "users": [],
        "expiry": 1900000000
    },
}

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'ok', 'time': int(time.time())})

@app.route('/verify', methods=['GET'])
def verify():
    card_key = request.args.get('key', '')
    user_id = request.args.get('userId', '')
    current_time = int(time.time())
    
    if card_key not in card_data:
        return jsonify({'success': False, 'message': '卡密不存在'})
    
    data = card_data[card_key]
    
    if data['expiry'] < current_time:
        return jsonify({'success': False, 'message': '卡密已过期'})
    
    if user_id in data['users']:
        return jsonify({
            'success': True, 
            'message': f'验证成功（剩余 {data["max"] - data["used"]} 次）'
        })
    
    if data['used'] >= data['max']:
        return jsonify({
            'success': False, 
            'message': f'卡密已达上限（最多 {data["max"]} 人）'
        })
    
    data['used'] += 1
    data['users'].append(user_id)
    
    return jsonify({
        'success': True, 
        'message': f'验证成功（剩余 {data["max"] - data["used"]} 次）'
    })

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
