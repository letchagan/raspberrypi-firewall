import ipaddress
import subprocess
import logging
from functools import wraps
from flask import request, jsonify

def is_valid_ip(ip_str):
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def is_private_ip(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback
    except ValueError:
        return False

def run_command(cmd_list):
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def require_api_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from config import Config

        if not Config.ENABLE_AUTH:
            return f(*args, **kwargs)

        token = request.headers.get('X-API-Token') or request.args.get('token')

        if not token or token != Config.API_TOKEN:
            return jsonify({'error': 'Unauthorized'}), 401

        return f(*args, **kwargs)

    return decorated_function

def log_audit(logger, action, ip, success, reason=""):
    message = f"ACTION: {action} | IP: {ip} | SUCCESS: {success}"
    if reason:
        message += f" | REASON: {reason}"

    if success:
        logger.info(message)
    else:
        logger.warning(message)

def sanitize_ip(ip_str):
    if not ip_str:
        return None
    ip_str = ip_str.strip()
    if is_valid_ip(ip_str):
        return ip_str
    return None
