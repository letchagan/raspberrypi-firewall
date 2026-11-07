import json
import time
import os
import signal
import logging
from datetime import datetime
from pathlib import Path

from config import Config
from utils import is_valid_ip, is_private_ip, run_command, log_audit

Config.ensure_log_dir()

logging.basicConfig(
    filename=Config.DECISION_ENGINE_LOG,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BLOCKED_IPS = set()
shutdown_event = False

def signal_handler(sig, frame):
    global shutdown_event
    logger.info("Received shutdown signal, stopping decision engine...")
    shutdown_event = True

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def block_ip(ip, reason):
    global BLOCKED_IPS

    if not is_valid_ip(ip):
        logger.warning(f"Invalid IP address: {ip}")
        return

    if ip in BLOCKED_IPS:
        return

    if ip in Config.WHITELIST_IPS:
        print(f"[WHITELIST] Skipping trusted IP: {ip}")
        logger.info(f"WHITELISTED: {ip} — not blocked")
        return

    if is_private_ip(ip):
        logger.info(f"SKIPPED PRIVATE IP: {ip}")
        return

    print(f"[{datetime.now()}] BLOCKING: {ip} — {reason}")
    success, stdout, stderr = run_command(['nft', 'add', 'element', 'ip', 'blocklist', 'blocked_ips', f'{{ {ip} }}'])

    if success:
        BLOCKED_IPS.add(ip)
        logger.info(f"BLOCKED: {ip} — {reason}")

        try:
            with open(Config.BLOCKED_IPS_FILE, 'a') as f:
                f.write(f"{ip}  # {reason} — {datetime.now()}\n")
        except IOError as e:
            logger.error(f"Failed to write to blocked IPs file: {e}")

        log_audit(logger, 'AUTO_BLOCK', ip, True, reason)
    else:
        logger.error(f"Failed to block IP {ip}: {stderr}")
        log_audit(logger, 'AUTO_BLOCK', ip, False, stderr)

def monitor_suricata():
    print(f"[{datetime.now()}] Decision engine started — monitoring Suricata alerts...")
    print(f"Watching: {Config.EVE_LOG}")
    print("Press Ctrl+C to stop\n")

    if not os.path.exists(Config.EVE_LOG):
        print(f"Error: EVE log not found at {Config.EVE_LOG}")
        logger.error(f"EVE log not found at {Config.EVE_LOG}")
        return

    with open(Config.EVE_LOG, 'r') as f:
        f.seek(0, 2)
        while not shutdown_event:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            try:
                event = json.loads(line)
                if event.get('event_type') == 'alert':
                    src_ip = event.get('src_ip', '')
                    dest_ip = event.get('dest_ip', '')
                    signature = event.get('alert', {}).get('signature', 'Unknown')
                    severity = event.get('alert', {}).get('severity', 3)
                    timestamp = event.get('timestamp', '')

                    print(f"\n🚨 ALERT DETECTED!")
                    print(f"   Time     : {timestamp}")
                    print(f"   From     : {src_ip}")
                    print(f"   To       : {dest_ip}")
                    print(f"   Rule     : {signature}")
                    print(f"   Severity : {severity}")

                    if severity <= Config.AUTO_BLOCK_SEVERITY:
                        block_ip(src_ip, signature)
                        print(f"   Action   : ✅ BLOCKED {src_ip}")
                    else:
                        print(f"   Action   : ⚠️  LOGGED ONLY")

                    logger.info(f"ALERT: {src_ip} -> {dest_ip} | {signature} | Severity: {severity}")

            except (json.JSONDecodeError, KeyError, ValueError):
                continue
            except Exception as e:
                logger.error(f"Error processing alert: {e}")

if __name__ == "__main__":
    try:
        monitor_suricata()
    except KeyboardInterrupt:
        print("\nDecision engine stopped.")
        logger.info("Decision engine stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Error: {e}")
