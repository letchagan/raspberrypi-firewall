import requests
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from config import Config
from utils import is_valid_ip, run_command, log_audit

Config.ensure_log_dir()
load_dotenv()

logging.basicConfig(
    filename=Config.THREAT_INTEL_LOG,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_api_key():
    api_key = os.getenv('ABUSEIPDB_API_KEY')
    if not api_key:
        try:
            with open(Config.ENV_FILE) as f:
                for line in f:
                    if line.startswith('ABUSEIPDB_API_KEY'):
                        return line.strip().split('=')[1].strip('\'"')
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Failed to read API key from {Config.ENV_FILE}: {e}")
    return api_key

def fetch_blocklist(api_key, confidence=None, limit=None):
    if confidence is None:
        confidence = Config.ABUSEIPDB_CONFIDENCE
    if limit is None:
        limit = Config.ABUSEIPDB_LIMIT

    print("Fetching blocklist from AbuseIPDB...")
    logger.info(f"Fetching blocklist from AbuseIPDB (confidence: {confidence}, limit: {limit})")

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
            ips = [entry['ipAddress'] for entry in data.get('data', [])]
            ips = [ip for ip in ips if is_valid_ip(ip)]
            print(f"Fetched {len(ips)} malicious IPs")
            logger.info(f"Fetched {len(ips)} IPs from AbuseIPDB")
            return ips
        else:
            print(f"API Error: {response.status_code}")
            logger.error(f"AbuseIPDB API Error: {response.status_code} - {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        logger.error(f"Connection error: {e}")
        return []

def apply_blocklist(ips):
    if not ips:
        print("No IPs to block")
        logger.warning("No IPs to block")
        return

    print(f"Applying {len(ips)} IPs to nftables blocklist...")
    logger.info(f"Applying {len(ips)} IPs to nftables blocklist")

    setup_commands = [
        ['nft', 'add', 'table', 'ip', 'blocklist'],
        ['nft', 'add', 'set', 'ip', 'blocklist', 'blocked_ips', '{ type ipv4_addr; flags interval; }'],
    ]

    for cmd in setup_commands:
        run_command(cmd)

    run_command(['nft', 'flush', 'set', 'ip', 'blocklist', 'blocked_ips'])

    batch_size = 50
    blocked_count = 0

    for i in range(0, len(ips), batch_size):
        batch = ips[i:i+batch_size]
        elements = ', '.join(batch)
        cmd = ['nft', 'add', 'element', 'ip', 'blocklist', 'blocked_ips', f'{{ {elements} }}']
        success, _, stderr = run_command(cmd)

        if success:
            blocked_count += len(batch)
        else:
            logger.error(f"Failed to add batch {i//batch_size}: {stderr}")

    print(f"Successfully blocked {blocked_count} IPs")
    logger.info(f"Blocked {blocked_count} IPs in nftables")

    try:
        with open(Config.BLOCKED_IPS_FILE, 'w') as f:
            f.write(f"# Updated: {datetime.now()}\n")
            f.write(f"# Source: AbuseIPDB\n")
            f.write(f"# Total: {len(ips)} IPs\n")
            for ip in ips:
                f.write(f"{ip}\n")
    except IOError as e:
        logger.error(f"Failed to write blocked IPs file: {e}")

def block_ip(ip, reason="Manual block"):
    if not is_valid_ip(ip):
        logger.warning(f"Invalid IP address: {ip}")
        return

    print(f"Blocking IP: {ip} — Reason: {reason}")

    setup_commands = [
        ['nft', 'add', 'table', 'ip', 'blocklist'],
        ['nft', 'add', 'set', 'ip', 'blocklist', 'blocked_ips', '{ type ipv4_addr; flags interval; }'],
    ]

    for cmd in setup_commands:
        run_command(cmd)

    success, _, stderr = run_command(['nft', 'add', 'element', 'ip', 'blocklist', 'blocked_ips', f'{{ {ip} }}'])

    if success:
        logger.info(f"BLOCKED: {ip} — {reason}")
        try:
            with open(Config.BLOCKED_IPS_FILE, 'a') as f:
                f.write(f"{ip}  # {reason} — {datetime.now()}\n")
        except IOError as e:
            logger.error(f"Failed to write to blocked IPs file: {e}")
        log_audit(logger, 'BLOCK', ip, True, reason)
        print(f"IP {ip} blocked successfully!")
    else:
        logger.error(f"Failed to block IP {ip}: {stderr}")
        log_audit(logger, 'BLOCK', ip, False, stderr)

def unblock_ip(ip):
    if not is_valid_ip(ip):
        logger.warning(f"Invalid IP address: {ip}")
        return

    success, _, stderr = run_command(['nft', 'delete', 'element', 'ip', 'blocklist', 'blocked_ips', f'{{ {ip} }}'])

    if success:
        print(f"IP {ip} unblocked!")
        logger.info(f"UNBLOCKED: {ip}")
        log_audit(logger, 'UNBLOCK', ip, True)
    else:
        print(f"Could not unblock {ip} — may not be in blocklist")
        logger.warning(f"Failed to unblock IP {ip}: {stderr}")
        log_audit(logger, 'UNBLOCK', ip, False, stderr)

if __name__ == "__main__":
    api_key = load_api_key()
    if not api_key:
        print("ERROR: API key not found in environment or .env file")
        logger.error("API key not found in environment or .env file")
        exit(1)

    try:
        ips = fetch_blocklist(api_key)
        apply_blocklist(ips)
        print("\nThreat intelligence update complete!")
        logger.info("Threat intelligence update complete")
    except Exception as e:
        logger.error(f"Unexpected error during threat intelligence update: {e}")
        print(f"Error: {e}")
