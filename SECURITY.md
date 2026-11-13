# Security Hardening Guide

This document outlines the security improvements made to the Raspberry Pi Firewall & IDPS project and best practices for deployment.

## Recent Security Improvements

### 1. Command Injection Prevention
- ✅ Replaced all `os.system()` calls with `subprocess.run()` using argument lists
- ✅ IP addresses are no longer interpolated directly into shell commands
- **Impact:** Prevents malicious IPs from breaking out of shell context

### 2. Input Validation
- ✅ All IP addresses are validated using `ipaddress.ip_address()`
- ✅ Whitelist checks for private/trusted IPs
- ✅ JSON input validation and error responses
- **Impact:** Prevents invalid or malicious IPs from being processed

### 3. API Authentication
- ✅ Optional token-based authentication via `X-API-Token` header
- ✅ Enable with `ENABLE_AUTH=True` in `.env`
- **Impact:** Restricts dashboard access to authenticated users

### 4. Rate Limiting
- ✅ Flask-Limiter configured on sensitive endpoints
- ✅ `/api/block` and `/api/unblock`: 10 requests per minute
- ✅ `/api/alerts` and `/api/stats`: 30 requests per minute
- **Impact:** Prevents brute-force attacks and DoS

### 5. Exception Handling
- ✅ Specific exception handling (no bare `except:` clauses)
- ✅ Proper error responses with HTTP status codes
- ✅ Comprehensive logging of failures
- **Impact:** Better debugging and security monitoring

### 6. Configuration Management
- ✅ Centralized configuration via `config.py`
- ✅ Environment variable support via `.env`
- ✅ No hardcoded paths or credentials
- **Impact:** Easier secure deployment and configuration

### 7. Thread Safety
- ✅ `threading.Lock()` for shared data structures
- ✅ Safe concurrent alert streaming
- **Impact:** Prevents race conditions

### 8. Graceful Shutdown
- ✅ Signal handlers for SIGTERM and SIGINT
- ✅ Clean shutdown of all components
- **Impact:** Prevents data corruption and clean restarts

## Deployment Security Checklist

### Before Production Deployment

- [ ] Change `API_TOKEN` in `.env` to a strong secret
- [ ] Set `ENABLE_AUTH=True` if exposing dashboard to network
- [ ] Review and update `WHITELIST_IPS` in `config.py`
- [ ] Configure network firewall to restrict dashboard access (port 3000)
- [ ] Use HTTPS/TLS for dashboard access (reverse proxy recommended)
- [ ] Set proper file permissions on `.env` file: `chmod 600 .env`
- [ ] Set proper permissions on log files: `chmod 600 logs/*`
- [ ] Disable Flask debug mode (default: False)
- [ ] Restrict Suricata log file access: `chmod 600 /var/log/suricata/eve.json`
- [ ] Run components as systemd services (not as root directly)
- [ ] Enable SELinux/AppArmor profiles if available
- [ ] Regularly update Suricata rules: `suricata-update`
- [ ] Monitor logs for suspicious activity: `journalctl -u idps-decision-engine`
- [ ] Test backup and restore procedures
- [ ] Document any custom firewall rules

### Network Access Control

The dashboard should NOT be exposed directly to untrusted networks. Recommended setup:

```
┌─────────────┐
│  Internet   │
└──────┬──────┘
       │
   ┌───┴────────────────────┐
   │  Nginx/HAProxy (HTTPS) │
   │  (Authentication)      │
   └──────┬─────────────────┘
          │
  ┌───────┴──────────┐
  │  Raspberry Pi    │
  │  IDPS Dashboard  │
  │  (Port 3000)     │
  └──────────────────┘
```

### API Token Security

Never commit `.env` files with real API tokens to version control:

```bash
# Good
git add .env.example
git add .gitignore

# Bad - Don't do this!
git add .env
```

### Logging and Monitoring

Enable comprehensive logging:

```bash
journalctl -u idps-dashboard -f
journalctl -u idps-decision-engine -f
journalctl -u idps-blockpage -f
tail -f /home/pi/idps/logs/*.log
```

### Firewall Configuration

Protect the dashboard with network-level firewall rules:

```bash
# Allow only from management network
sudo ufw allow from 192.168.50.0/24 to any port 3000
sudo ufw deny to any port 3000
```

## Security Incident Response

### If dashboard is compromised:

1. Stop all IDPS services: `sudo systemctl stop idps.target`
2. Review logs: `journalctl -u idps* --since "2 hours ago"`
3. Check blocked IPs: `sudo nft list set ip blocklist blocked_ips`
4. Review `.env` file for exposed credentials
5. Rotate API token: update `API_TOKEN` in `.env`
6. Check for unauthorized blocks: `grep "Manual block" /home/pi/idps/logs/blocked_ips.txt`
7. Restart services: `sudo systemctl start idps.target`

### If Suricata rules are compromised:

1. Redownload official Suricata rules
2. Review custom rules for injected signatures
3. Restart Suricata: `sudo systemctl restart suricata`

## Future Security Enhancements

- [ ] Add HTTPS/TLS support to Flask dashboard
- [ ] Implement OAuth2 authentication
- [ ] Add Web Application Firewall (WAF)
- [ ] Implement audit logging for all administrative actions
- [ ] Add role-based access control (RBAC)
- [ ] Implement request signing for API endpoints
- [ ] Add IP reputation scoring
- [ ] Implement automated security scans
- [ ] Add threat intelligence integration (VirusTotal, etc.)

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE-78: Command Injection](https://cwe.mitre.org/data/definitions/78.html)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [Raspberry Pi Security](https://www.raspberrypi.org/documentation/computers/configuration.html#securing-your-raspberry-pi)
