import os
import logging
import threading
from flask import Flask, render_template, request, jsonify

from sender import traffic_loop
from config import config

# —— Setup logging level from environment ——
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("cfg")

# Suppress Flask/Werkzeug request logs unless elevated
logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)

# Cache last config to prevent logging floods
_last_config_snapshot = None
_last_config_log_ts = 0

@app.route('/')
def index():
    return render_template('index.html', config=config.get())

@app.route('/api/config', methods=['GET'])
def get_config():
    global _last_config_snapshot, _last_config_log_ts
    cfg = config.get()

    # Log changes or once every 10s
    from time import time
    if cfg != _last_config_snapshot or time() - _last_config_log_ts > 10:
        log.info("/api/config fetched: %s", cfg)
        _last_config_snapshot = cfg
        _last_config_log_ts = time()

    return jsonify(cfg)

@app.route('/api/start-burst', methods=['POST'])
def start_burst():
    try:
        rate = int(request.form.get('rate', 1))
        duration = int(request.form.get('duration', 1))
    except ValueError:
        return jsonify({'error': 'Invalid burst input'}), 400

    config.start_burst(rate, duration)
    log.info("Burst %dms for %ds requested", rate, duration)
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
    log.info("Manual rate set to %d ms", new_rate)
    return jsonify(config.get())

@app.route('/api/stop', methods=['POST'])
def stop_traffic():
    config.stop()
    log.info("Traffic stopped via API")
    return '', 200

if __name__ == '__main__':
    thread = threading.Thread(target=traffic_loop, daemon=True)
    thread.start()
    app.run(host='0.0.0.0', port=5050)
