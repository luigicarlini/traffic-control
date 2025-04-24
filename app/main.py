# main.py

from flask import Flask, render_template, request, jsonify
import threading
from sender import traffic_loop
from config import config

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', config=config.get())

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(config.get())

@app.route('/api/start-burst', methods=['POST'])
def start_burst():
    try:
        rate = int(request.form.get('rate', 1))
        duration = int(request.form.get('duration', 1))
        print(f"[🔥 API Trigger] Burst request: {rate}ms for {duration}s")
    except ValueError:
        return jsonify({'error': 'Invalid burst input'}), 400

    config.start_burst(rate, duration)
    return '', 200


@app.route('/api/set-rate', methods=['POST'])
def apply_rate():
    data = request.get_json()
    if not data or 'rate_ms' not in data:
        return jsonify({'error': "Missing 'rate_ms' in request"}), 400

    try:
        new_rate = int(data['rate_ms'])
    except ValueError:
        return jsonify({'error': 'Invalid rate value'}), 400

    config.set_rate(new_rate)
    print(f"[💾] Apply Rate clicked — setting rate to {new_rate} ms and resuming traffic.")
    return jsonify(config.get())

@app.route('/api/stop', methods=['POST'])
def stop_traffic():
    config.stop()
    return '', 200

if __name__ == '__main__':
    thread = threading.Thread(target=traffic_loop, daemon=True)
    thread.start()
    app.run(host='0.0.0.0', port=5050)
