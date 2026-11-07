import signal
import logging
from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
from flask import send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
import time
import os
import subprocess
from datetime import datetime
import threading
from pathlib import Path

from config import Config
from utils import is_valid_ip, require_api_token, log_audit, sanitize_ip, run_command

Config.ensure_log_dir()

app = Flask(__name__)
CORS(app)
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

logging.basicConfig(
    filename=Config.DECISION_ENGINE_LOG,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ALERTS = []
alerts_lock = threading.Lock()
shutdown_event = threading.Event()

def read_alerts():
    while not shutdown_event.is_set():
        try:
            with open(Config.EVE_LOG, 'r') as f:
                f.seek(0, 2)
                while not shutdown_event.is_set():
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    try:
                        event = json.loads(line)
                        if event.get('event_type') == 'alert':
                            alert = {
                                'timestamp': event.get('timestamp', ''),
                                'src_ip': event.get('src_ip', ''),
                                'dest_ip': event.get('dest_ip', ''),
                                'signature': event.get('alert', {}).get('signature', 'Unknown'),
                                'severity': event.get('alert', {}).get('severity', 3),
                                'category': event.get('alert', {}).get('category', 'Unknown'),
                            }
                            with alerts_lock:
                                ALERTS.insert(0, alert)
                                if len(ALERTS) > Config.MAX_ALERTS:
                                    ALERTS.pop()
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        except FileNotFoundError:
            logger.warning(f"EVE log not found: {Config.EVE_LOG}")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error reading alerts: {e}")
            time.sleep(5)

def event_stream():
    last_count = 0
    while not shutdown_event.is_set():
        with alerts_lock:
            if len(ALERTS) > last_count:
                new_alerts = ALERTS[:len(ALERTS) - last_count]
                last_count = len(ALERTS)

        for alert in new_alerts:
            yield f"data: {json.dumps(alert)}\n\n"
        time.sleep(Config.ALERT_STREAM_INTERVAL)

def signal_handler(sig, frame):
    logger.info("Received shutdown signal, gracefully shutting down...")
    shutdown_event.set()

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

alert_thread = threading.Thread(target=read_alerts, daemon=True)
alert_thread.start()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/stream')
def stream():
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/api/alerts')
@limiter.limit("30 per minute")
def get_alerts():
    with alerts_lock:
        alerts_copy = ALERTS[:50].copy()
    return jsonify(alerts_copy)

@app.route('/api/stats')
@limiter.limit("30 per minute")
def get_stats():
    blocked_count = 0
    try:
        with open(Config.BLOCKED_IPS_FILE) as f:
            blocked_count = sum(1 for line in f if line.strip() and not line.startswith('#'))
    except (FileNotFoundError, IOError):
        pass

    try:
        uptime = subprocess.getoutput('uptime -p')
    except:
        uptime = "Unknown"

    return jsonify({
        'total_alerts': len(ALERTS),
        'blocked_ips': blocked_count,
        'suricata_status': 'Running' if os.path.exists('/var/run/suricata.pid') else 'Stopped',
        'uptime': uptime,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/health')
@limiter.limit("60 per minute")
def health():
    health_status = {
        'status': 'ok',
        'components': {
            'suricata': 'running' if os.path.exists('/var/run/suricata.pid') else 'stopped',
            'eve_log': 'accessible' if os.path.exists(Config.EVE_LOG) else 'missing',
            'logs_dir': 'accessible' if os.path.isdir(Config.LOG_DIR) else 'missing',
        },
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(health_status)

@app.route('/api/block', methods=['POST'])
@limiter.limit("10 per minute")
@require_api_token
def block_ip():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    ip = sanitize_ip(data.get('ip', ''))

    if not ip:
        return jsonify({'error': 'Invalid IP address'}), 400

    if not is_valid_ip(ip):
        return jsonify({'error': 'Invalid IP address format'}), 400

    success, stdout, stderr = run_command(['nft', 'add', 'element', 'ip', 'blocklist', 'blocked_ips', f'{{ {ip} }}'])

    if success:
        try:
            with open(Config.BLOCKED_IPS_FILE, 'a') as f:
                f.write(f"{ip}  # Manual block — {datetime.now()}\n")
        except IOError as e:
            logger.error(f"Failed to write to blocked IPs file: {e}")

        log_audit(logger, 'BLOCK', ip, True)
        return jsonify({'status': 'blocked', 'ip': ip}), 200
    else:
        log_audit(logger, 'BLOCK', ip, False, stderr)
        return jsonify({'error': 'Failed to block IP', 'details': stderr}), 500

@app.route('/blocked')
def blocked():
    try:
        return send_from_directory(Config.BLOCKPAGE_DIR, 'block.html')
    except FileNotFoundError:
        return jsonify({'error': 'Block page not found'}), 404

@app.route('/api/unblock', methods=['POST'])
@limiter.limit("10 per minute")
@require_api_token
def unblock_ip():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    ip = sanitize_ip(data.get('ip', ''))

    if not ip:
        return jsonify({'error': 'Invalid IP address'}), 400

    if not is_valid_ip(ip):
        return jsonify({'error': 'Invalid IP address format'}), 400

    success, stdout, stderr = run_command(['nft', 'delete', 'element', 'ip', 'blocklist', 'blocked_ips', f'{{ {ip} }}'])

    if success:
        log_audit(logger, 'UNBLOCK', ip, True)
        return jsonify({'status': 'unblocked', 'ip': ip}), 200
    else:
        log_audit(logger, 'UNBLOCK', ip, False, stderr)
        return jsonify({'error': 'Failed to unblock IP', 'details': stderr}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded'}), 429

@app.errorhandler(404)
def not_found_handler(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error_handler(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.DEBUG, threaded=True)
