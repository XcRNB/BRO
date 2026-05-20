from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# 卡密数据存储
# 格式: {卡密: {"max": 总次数, "used": 已用次数, "users": [用户ID列表], "expiry": 过期时间戳}}
card_data = {
    "XcRNG": {
        "max": 5,                    # 最多5个人用
        "used": 0,                   # 已用人数
        "users": [],                 # 已使用的用户ID
        "expiry": 1900000000         # 2030年过期（改这个调整时间）
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
    
    # 检查卡密是否存在
    if card_key not in card_data:
        return jsonify({'success': False, 'message': '卡密不存在'})
    
    data = card_data[card_key]
    
    # 检查是否过期
    if data['expiry'] < current_time:
        return jsonify({'success': False, 'message': '卡密已过期'})
    
    # 检查该用户是否已经用过
    if user_id in data['users']:
        return jsonify({
            'success': True, 
            'message': f'验证成功（该卡密剩余 {data["max"] - data["used"]} 次）'
        })
    
    # 检查是否还有剩余次数
    if data['used'] >= data['max']:
        return jsonify({
            'success': False, 
            'message': f'卡密已达上限（最多 {data["max"]} 人使用）'
        })
    
    # 使用一次
    data['used'] += 1
    data['users'].append(user_id)
    
    return jsonify({
        'success': True, 
        'message': f'验证成功（剩余 {data["max"] - data["used"]} 次）'
    })

@app.route('/verify', methods=['POST'])
def verify_post():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效请求'})
    
    card_key = data.get('key', '')
    user_id = str(data.get('userId', ''))
    current_time = int(time.time())
    
    if card_key not in card_data:
        return jsonify({'success': False, 'message': '卡密不存在'})
    
    card = card_data[card_key]
    
    if card['expiry'] < current_time:
        return jsonify({'success': False, 'message': '卡密已过期'})
    
    if user_id in card['users']:
        return jsonify({'success': True, 'message': f'验证成功（剩余 {card["max"] - card["used"]} 次）'})
    
    if card['used'] >= card['max']:
        return jsonify({'success': False, 'message': f'卡密已达上限（最多 {card["max"]} 人）'})
    
    card['used'] += 1
    card['users'].append(user_id)
    
    return jsonify({'success': True, 'message': f'验证成功（剩余 {card["max"] - card["used"]} 次）'})

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
