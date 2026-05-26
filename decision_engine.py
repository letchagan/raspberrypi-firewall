import json
import time
import os
import logging
from datetime import datetime
import subprocess

# Setup logging
logging.basicConfig(
    filename='/home/pi/idps/logs/decision_engine.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

BLOCKED_IPS = set()
EVE_LOG = '/var/log/suricata/eve.json'

# Never auto-block these trusted IPs
WHITELIST_IPS = {
    "192.168.50.1",  # Raspberry Pi
    "192.168.50.2",  # Your Windows laptop
    "127.0.0.1",
}

def block_ip(ip, reason):
    if ip in BLOCKED_IPS:
        return

    # Skip trusted IPs
    if ip in WHITELIST_IPS:
        print(f"[WHITELIST] Skipping trusted IP: {ip}")
        logging.info(f"WHITELISTED: {ip} — not blocked")
        return

    # Skip common private ranges
    if ip.startswith('192.168.') or ip.startswith('10.') or ip == '127.0.0.1':
        return

    print(f"[{datetime.now()}] BLOCKING: {ip} — {reason}")
    os.system(f'nft add element ip blocklist blocked_ips "{{ {ip} }}"')
    BLOCKED_IPS.add(ip)

    logging.info(f"BLOCKED: {ip} — {reason}")

    with open('/home/pi/idps/logs/blocked_ips.txt', 'a') as f:
        f.write(f"{ip}  # {reason} — {datetime.now()}\n")

def monitor_suricata():
    print(f"[{datetime.now()}] Decision engine started — monitoring Suricata alerts...")
    print("Watching: /var/log/suricata/eve.json")
    print("Press Ctrl+C to stop\n")

    # Start from end of file
    with open(EVE_LOG, 'r') as f:
        f.seek(0, 2)  # Seek to end
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            try:
                event = json.loads(line)
                if event.get('event_type') == 'alert':
                    src_ip = event.get('src_ip', '')
                    dest_ip = event.get('dest_ip', '')
                    signature = event['alert']['signature']
                    severity = event['alert'].get('severity', 3)
                    timestamp = event.get('timestamp', '')

                    print(f"\n🚨 ALERT DETECTED!")
                    print(f"   Time     : {timestamp}")
                    print(f"   From     : {src_ip}")
                    print(f"   To       : {dest_ip}")
                    print(f"   Rule     : {signature}")
                    print(f"   Severity : {severity}")

                    # Auto-block if severity is high (1=highest, 3=lowest)
                    if severity <= 2:
                        block_ip(dest_ip, signature)
                        print(f"   Action   : ✅ BLOCKED {src_ip}")
                    else:
                        print(f"   Action   : ⚠️  LOGGED ONLY")

                    logging.info(f"ALERT: {src_ip} -> {dest_ip} | {signature}")

            except json.JSONDecodeError:
                continue
            except KeyboardInterrupt:
                print("\nDecision engine stopped.")
                break

if __name__ == "__main__":
    monitor_suricata()
