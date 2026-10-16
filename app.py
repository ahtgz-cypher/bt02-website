import sys
import os
import json
import requests

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

BANNER_FILE = os.path.join(os.path.dirname(__file__), 'banner.json')
ADMIN_PIN = "2006" # Mã PIN admin xác thực cập nhật banner từ điện thoại
NTFY_TOPIC = "nguyenhoang_bt02_vku" # Kênh push notification đến điện thoại

def get_banner():
    if os.path.exists(BANNER_FILE):
        try:
            with open(BANNER_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('message', '')
        except Exception:
            pass
    return "Chào mừng bạn đến với Website cá nhân của Nguyễn Hoàng - Sinh viên An toàn thông tin (VKU)! Hệ thống giám sát SOC đang trực tuyến."

def save_banner(msg):
    with open(BANNER_FILE, 'w', encoding='utf-8') as f:
        json.dump({'message': msg}, f, ensure_ascii=False)

def send_push_notification(name, email, message):
    """Gửi thông báo đẩy về điện thoại của sinh viên qua ntfy.sh / Webhook"""
    try:
        # Gửi qua ntfy.sh (Miễn phí, có app iOS & Android, nhận tức thời)
        res = requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=f"Từ: {name} ({email})\nLời nhắn: {message}".encode('utf-8'),
            headers={
                "Title": "Website BT-02 có tin nhắn mới!".encode('utf-8'),
                "Priority": "high",
                "Tags": "bell,shield"
            },
            timeout=5
        )
        print(f"[PUSH NOTIFICATION] Đã gửi thông báo đến điện thoại qua ntfy: HTTP {res.status_code}")
    except Exception as e:
        print(f"[PUSH NOTIFICATION] Lỗi khi gửi push notification: {e}")

@app.route('/')
def home():
    banner = get_banner()
    return render_template('index.html', banner_message=banner)

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/api/banner', methods=['GET', 'POST'])
def handle_banner():
    if request.method == 'GET':
        return jsonify({'message': get_banner()}), 200

    # POST: Cập nhật banner từ điện thoại
    data = request.get_json(silent=True) or request.form
    pin = data.get('pin', '').strip()
    new_msg = data.get('message', '').strip()

    if pin != ADMIN_PIN:
        return jsonify({'status': 'error', 'message': 'Mã PIN xác thực Admin không chính xác!'}), 403

    if not new_msg:
        return jsonify({'status': 'error', 'message': 'Nội dung lời nhắn banner không được để trống!'}), 400

    save_banner(new_msg)
    print(f"\n[TOP BANNER UPDATED] Admin đã đổi lời nhắn banner thành: {new_msg}\n")

    return jsonify({
        'status': 'success',
        'message': 'Đã cập nhật Top Banner chữ chạy thành công!',
        'new_banner': new_msg
    }), 200

@app.route('/api/message', methods=['POST'])
def receive_message():
    try:
        data = request.get_json(silent=True) or request.form
    except Exception:
        data = {}

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    message = data.get('message', '').strip()

    if not name or not email or not message:
        return jsonify({'status': 'error', 'message': 'Vui lòng điền đầy đủ các thông tin bắt buộc!'}), 400

    # 1. Ghi log terminal
    try:
        print(f"\n>>> [TIN NHẮN MỚI TỪ WEBSITE] Người gửi: {name} | Email: {email}")
        print(f">>> Lời nhắn: {message}\n")
    except Exception:
        pass

    # 2. Gửi thông báo đẩy tức thì đến điện thoại
    send_push_notification(name, email, message)

    return jsonify({
        'status': 'success',
        'message': f'Cảm ơn {name}! Tin nhắn đã được gửi đến điện thoại của Nguyễn Hoàng thành công.'
    }), 200

if __name__ == '__main__':
    # Chạy trên tất cả giao diện mạng tại cổng 8080
    app.run(host='0.0.0.0', port=8080, debug=False)
