from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
from flask import send_from_directory
import json
import time
import os
import subprocess
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)

EVE_LOG = '/var/log/suricata/eve.json'
BLOCKED_IPS_FILE = '/home/pi/idps/logs/blocked_ips.txt'
ALERTS = []
MAX_ALERTS = 100

# ── Background thread to read Suricata alerts ─────────────────────────────────
def read_alerts():
    while True:
        try:
            with open(EVE_LOG, 'r') as f:
                f.seek(0, 2)
                while True:
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
                                'signature': event['alert']['signature'],
                                'severity': event['alert'].get('severity', 3),
                                'category': event['alert'].get('category', 'Unknown'),
                            }
                            ALERTS.insert(0, alert)
                            if len(ALERTS) > MAX_ALERTS:
                                ALERTS.pop()
                    except:
                        continue
        except Exception as e:
            time.sleep(5)

# Start background thread
t = threading.Thread(target=read_alerts, daemon=True)
t.start()

# ── SSE stream ────────────────────────────────────────────────────────────────
def event_stream():
    last_count = 0
    while True:
        if len(ALERTS) > last_count:
            new_alerts = ALERTS[:len(ALERTS) - last_count]
            last_count = len(ALERTS)
            for alert in new_alerts:
                yield f"data: {json.dumps(alert)}\n\n"
        time.sleep(0.5)

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/stream')
def stream():
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/api/alerts')
def get_alerts():
    return jsonify(ALERTS[:50])

@app.route('/api/stats')
def get_stats():
    blocked_count = 0
    try:
        with open(BLOCKED_IPS_FILE) as f:
            blocked_count = sum(1 for line in f if line.strip() and not line.startswith('#'))
    except:
        pass
    return jsonify({
        'total_alerts': len(ALERTS),
        'blocked_ips': blocked_count,
        'suricata_status': 'Running' if os.path.exists('/var/run/suricata.pid') else 'Stopped',
        'uptime': subprocess.getoutput('uptime -p'),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/block', methods=['POST'])
def block_ip():
    data = request.json
    ip = data.get('ip')
    if ip:
        os.system(f'nft add element ip blocklist blocked_ips "{{ {ip} }}"')
        return jsonify({'status': 'blocked', 'ip': ip})
    return jsonify({'status': 'error'})

@app.route('/blocked')
def blocked():
    return send_from_directory('/home/pi/idps/blockpage', 'block.html')

@app.route('/api/unblock', methods=['POST'])
def unblock_ip():
    data = request.json
    ip = data.get('ip')
    if ip:
        os.system(f'nft delete element ip blocklist blocked_ips "{{ {ip} }}"')
        return jsonify({'status': 'unblocked', 'ip': ip})
    return jsonify({'status': 'error'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False, threaded=True)
