import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    LOG_DIR = os.getenv('IDPS_LOG_DIR', '/home/pi/idps/logs')
    EVE_LOG = os.getenv('EVE_LOG', '/var/log/suricata/eve.json')
    BLOCKPAGE_DIR = os.getenv('BLOCKPAGE_DIR', '/home/pi/idps/blockpage')
    ENV_FILE = os.getenv('ENV_FILE', '/home/pi/idps/.env')

    GATEWAY_IP = os.getenv('GATEWAY_IP', '192.168.50.1')
    LAN_INTERFACE = os.getenv('LAN_IFACE', 'eth0')
    WAN_INTERFACE = os.getenv('WAN_IFACE', 'wlan0')
    LAN_SUBNET = os.getenv('LAN_SUBNET', '192.168.50.0/24')

    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 3000))

    BLOCKPAGE_HOST = os.getenv('BLOCKPAGE_HOST', '0.0.0.0')
    BLOCKPAGE_PORT = int(os.getenv('BLOCKPAGE_PORT', 5001))

    BLOCKED_IPS_FILE = os.path.join(LOG_DIR, 'blocked_ips.txt')
    DECISION_ENGINE_LOG = os.path.join(LOG_DIR, 'decision_engine.log')
    THREAT_INTEL_LOG = os.path.join(LOG_DIR, 'threat_intel.log')

    WHITELIST_IPS = {
        GATEWAY_IP,
        '127.0.0.1',
    }

    ABUSEIPDB_CONFIDENCE = int(os.getenv('ABUSEIPDB_CONFIDENCE', 85))
    ABUSEIPDB_LIMIT = int(os.getenv('ABUSEIPDB_LIMIT', 500))

    API_TOKEN = os.getenv('API_TOKEN', 'change-me-in-production')
    ENABLE_AUTH = os.getenv('ENABLE_AUTH', 'False').lower() == 'true'

    MAX_ALERTS = int(os.getenv('MAX_ALERTS', 100))
    ALERT_STREAM_INTERVAL = float(os.getenv('ALERT_STREAM_INTERVAL', 0.5))

    AUTO_BLOCK_SEVERITY = int(os.getenv('AUTO_BLOCK_SEVERITY', 2))

    @classmethod
    def ensure_log_dir(cls):
        Path(cls.LOG_DIR).mkdir(parents=True, exist_ok=True)
        Path(cls.BLOCKPAGE_DIR).mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls):
        required_paths = [cls.EVE_LOG]
        for path in required_paths:
            if not os.path.exists(path):
                print(f"Warning: {path} does not exist yet")
