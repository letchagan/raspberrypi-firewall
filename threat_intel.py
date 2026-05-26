import requests
import subprocess
import json
import os
import logging
from datetime import datetime

# ── Setup logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    filename='/home/pi/idps/logs/threat_intel.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ── Load API key ──────────────────────────────────────────────────────────────
def load_api_key():
    with open('/home/pi/idps/.env') as f:
        for line in f:
            if line.startswith('ABUSEIPDB_API_KEY'):
                return line.strip().split('=')[1]
    return None

# ── Fetch blocklist from AbuseIPDB ────────────────────────────────────────────
def fetch_blocklist(api_key, confidence=85, limit=500):
    print("Fetching blocklist from AbuseIPDB...")
    url = "https://api.abuseipdb.com/api/v2/blacklist"
    headers = {
        "Key": api_key,
        "Accept": "application/json"
    }
    params = {
        "confidenceMinimum": confidence,
        "limit": limit
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            ips = [entry['ipAddress'] for entry in data['data']]
            print(f"Fetched {len(ips)} malicious IPs")
            logging.info(f"Fetched {len(ips)} IPs from AbuseIPDB")
            return ips
        else:
            print(f"API Error: {response.status_code}")
            logging.error(f"API Error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Connection error: {e}")
        logging.error(f"Connection error: {e}")
        return []

# ── Apply blocklist to nftables ───────────────────────────────────────────────
def apply_blocklist(ips):
    if not ips:
        print("No IPs to block")
        return

    print(f"Applying {len(ips)} IPs to nftables blocklist...")

    # Create nftables set if not exists
    commands = [
        "nft add table ip blocklist 2>/dev/null || true",
        "nft add set ip blocklist blocked_ips { type ipv4_addr\\; flags interval\\; } 2>/dev/null || true",
        "nft add chain ip blocklist input { type filter hook input priority 0\\; } 2>/dev/null || true",
        "nft add rule ip blocklist input ip saddr @blocked_ips drop 2>/dev/null || true",
    ]

    for cmd in commands:
        os.system(cmd)

    # Flush old IPs and add new ones
    os.system("nft flush set ip blocklist blocked_ips 2>/dev/null || true")

    # Add IPs in batches
    batch_size = 50
    blocked_count = 0
    for i in range(0, len(ips), batch_size):
        batch = ips[i:i+batch_size]
        ip_list = ", ".join(batch)
        cmd = f'nft add element ip blocklist blocked_ips {{ {ip_list} }}'
        result = os.system(cmd)
        if result == 0:
            blocked_count += len(batch)

    print(f"Successfully blocked {blocked_count} IPs")
    logging.info(f"Blocked {blocked_count} IPs in nftables")

    # Save to file for reference
    with open('/home/pi/idps/logs/blocked_ips.txt', 'w') as f:
        f.write(f"# Updated: {datetime.now()}\n")
        f.write(f"# Total: {len(ips)} IPs\n")
        for ip in ips:
            f.write(ip + "\n")

# ── Block a single IP immediately ─────────────────────────────────────────────
def block_ip(ip, reason="Manual block"):
    print(f"Blocking IP: {ip} — Reason: {reason}")
    commands = [
        "nft add table ip blocklist 2>/dev/null || true",
        "nft add set ip blocklist blocked_ips { type ipv4_addr\\; flags interval\\; } 2>/dev/null || true",
        "nft add chain ip blocklist input { type filter hook input priority 0\\; } 2>/dev/null || true",
        "nft add rule ip blocklist input ip saddr @blocked_ips drop 2>/dev/null || true",
        f"nft add element ip blocklist blocked_ips {{ {ip} }}",
    ]
    for cmd in commands:
        os.system(cmd)

    # Log the block
    logging.info(f"BLOCKED: {ip} — {reason}")
    with open('/home/pi/idps/logs/blocked_ips.txt', 'a') as f:
        f.write(f"{ip}  # {reason} — {datetime.now()}\n")
    print(f"IP {ip} blocked successfully!")

# ── Unblock an IP ─────────────────────────────────────────────────────────────
def unblock_ip(ip):
    cmd = f"nft delete element ip blocklist blocked_ips {{ {ip} }}"
    result = os.system(cmd)
    if result == 0:
        print(f"IP {ip} unblocked!")
        logging.info(f"UNBLOCKED: {ip}")
    else:
        print(f"Could not unblock {ip} — may not be in blocklist")

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    api_key = load_api_key()
    if not api_key:
        print("ERROR: API key not found in .env file")
        exit(1)
    ips = fetch_blocklist(api_key)
    apply_blocklist(ips)
    print("\nThreat intelligence update complete!")
