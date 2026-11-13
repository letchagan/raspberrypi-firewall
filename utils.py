import ipaddress
import subprocess
import logging
from functools import wraps
from flask import request, jsonify

def is_valid_ip(ip_str):
    """Check if string is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


def is_ipv4(ip_str):
    """Check if string is a valid IPv4 address."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return isinstance(ip, ipaddress.IPv4Address)
    except ValueError:
        return False


def is_ipv6(ip_str):
    """Check if string is a valid IPv6 address."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return isinstance(ip, ipaddress.IPv6Address)
    except ValueError:
        return False


def is_private_ip(ip_str):
    """Check if IP is private, loopback, or link-local."""
    try:
        ip = ipaddress.ip_address(ip_str)
        if isinstance(ip, ipaddress.IPv4Address):
            return ip.is_private or ip.is_loopback
        else:  # IPv6
            return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def is_ipv6_link_local(ip_str):
    """Check if IPv6 address is link-local."""
    try:
        ip = ipaddress.ip_address(ip_str)
        if isinstance(ip, ipaddress.IPv6Address):
            return ip.is_link_local
        return False
    except ValueError:
        return False


def get_ip_version(ip_str):
    """Get IP version (4 or 6), or None if invalid."""
    try:
        ip = ipaddress.ip_address(ip_str)
        if isinstance(ip, ipaddress.IPv4Address):
            return 4
        return 6
    except ValueError:
        return None

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
