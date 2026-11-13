# Installation and Deployment Guide

This guide covers installation and deployment of the Raspberry Pi Firewall & IDPS on a Raspberry Pi running Raspberry Pi OS.

## Prerequisites

- Raspberry Pi 4 or later (2GB+ RAM)
- Raspberry Pi OS (Bullseye or newer)
- Two network interfaces (WAN: wlan0, LAN: eth0)
- Root/sudo access
- Internet connection for initial setup

## Step 1: System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
sudo apt-get install -y suricata nftables
sudo apt-get install -y git
```

## Step 2: Clone and Setup Project

```bash
git clone https://github.com/letchagan/raspberrypi-firewall.git
cd raspberrypi-firewall

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

## Step 3: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration with your settings
nano .env
```

### Key Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GATEWAY_IP` | 192.168.50.1 | Gateway IP address |
| `LAN_IFACE` | eth0 | LAN network interface |
| `WAN_IFACE` | wlan0 | WAN network interface |
| `LAN_SUBNET` | 192.168.50.0/24 | LAN subnet |
| `FLASK_PORT` | 3000 | Dashboard port |
| `ENABLE_AUTH` | False | Enable API authentication |
| `API_TOKEN` | change-me-in-production | API authentication token |
| `ABUSEIPDB_API_KEY` | (required) | AbuseIPDB API key |

### Getting AbuseIPDB API Key

1. Visit https://www.abuseipdb.com
2. Create a free account
3. Navigate to Account → API
4. Copy your API key
5. Add to `.env`: `ABUSEIPDB_API_KEY=your-key-here`

## Step 4: Set File Permissions

```bash
# Secure .env file
chmod 600 .env

# Create log directory with proper permissions
mkdir -p logs
chmod 700 logs

# Create blockpage directory
mkdir -p blockpage
chmod 755 blockpage
```

## Step 5: Network Configuration

### Configure Gateway (Raspberry Pi)

```bash
sudo bash setup_gateway.sh
```

This configures:
- IPv4 forwarding
- NAT masquerading
- nftables firewall rules
- Blocklist tables

Verify:
```bash
sudo nft list ruleset
```

### Configure HTTP Redirect (Optional)

```bash
sudo bash setup_redirect.sh
```

This redirects blocked HTTP traffic to the block page server.

## Step 6: Test Components

### Test Suricata
```bash
sudo pgrep -a suricata
sudo tail -f /var/log/suricata/eve.json
```

### Test nftables
```bash
sudo nft list ruleset
sudo nft list set ip blocklist blocked_ips
```

### Test Python Environment
```bash
source .venv/bin/activate
python3 -c "import flask; print(f'Flask {flask.__version__} OK')"
```

## Step 7: Choose Deployment Method

### Option A: Manual Startup (Development)

```bash
# Terminal 1: Decision Engine
sudo .venv/bin/python3 decision_engine.py

# Terminal 2: Block Page Server
sudo .venv/bin/python3 blockpage_server.py

# Terminal 3: Flask Dashboard
sudo .venv/bin/python3 app.py
```

Access dashboard: http://192.168.50.1:3000

### Option B: Shell Script (Development)

```bash
sudo bash start_idps.sh
```

### Option C: Systemd Services (Production - Recommended)

```bash
# Copy service files
sudo cp systemd/idps*.service /etc/systemd/system/
sudo cp systemd/idps.target /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable idps.target
sudo systemctl start idps.target

# Check status
sudo systemctl status idps.target
sudo systemctl status idps-decision-engine
sudo systemctl status idps-blockpage
sudo systemctl status idps-dashboard

# View logs
journalctl -u idps.target -f
```

## Step 8: Initial Threat Intelligence Update

```bash
# Activate virtual environment
source .venv/bin/activate

# Download and apply threat intelligence
sudo python3 threat_intel.py

# Verify blocked IPs
sudo nft list set ip blocklist blocked_ips
```

## Verification Checklist

- [ ] Suricata is running and generating alerts
- [ ] nftables tables and sets are created
- [ ] Flask dashboard is accessible on port 3000
- [ ] Block page server is accessible on port 5001
- [ ] Decision engine is processing alerts
- [ ] Threat intelligence has loaded IPs
- [ ] Logs are being written without errors
- [ ] API endpoints return valid JSON responses

## Testing the System

### Simulate an Alert (Optional)

Test if alerts trigger blocking:

```bash
# Check available test rules
sudo suricata -T

# Generate test traffic
curl http://testphp.vulnweb.com
```

### Test API Endpoints

```bash
# Get alerts
curl http://192.168.50.1:3000/api/alerts

# Get statistics
curl http://192.168.50.1:3000/api/stats

# Get health status
curl http://192.168.50.1:3000/api/health

# Block an IP (requires authentication if enabled)
curl -X POST http://192.168.50.1:3000/api/block \
  -H "Content-Type: application/json" \
  -H "X-API-Token: your-api-token" \
  -d '{"ip": "203.0.113.10"}'
```

## Troubleshooting

### Dashboard not accessible

```bash
# Check Flask process
sudo ps aux | grep app.py

# Check Flask logs
sudo journalctl -u idps-dashboard -n 50

# Verify port
sudo netstat -tlnp | grep 3000
```

### Suricata not generating alerts

```bash
# Check Suricata status
sudo systemctl status suricata
sudo tail -f /var/log/suricata/fast.log

# Restart Suricata
sudo systemctl restart suricata
```

### Threat intelligence update fails

```bash
# Check API key in .env
cat .env | grep ABUSEIPDB_API_KEY

# Check network connectivity
curl -I https://api.abuseipdb.com

# Run threat intelligence manually
source .venv/bin/activate
sudo python3 threat_intel.py
```

### nftables errors

```bash
# Flush and reset tables
sudo nft flush ruleset

# Rerun setup script
sudo bash setup_gateway.sh
```

## Production Hardening

See [SECURITY.md](SECURITY.md) for production security recommendations.

## Updating the System

```bash
cd raspberrypi-firewall

# Pull latest changes
git pull origin main

# Update Python dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl restart idps.target
```

## Backup and Recovery

```bash
# Backup configuration
tar -czf idps-backup-$(date +%Y%m%d).tar.gz \
  .env logs/ blockpage/

# Restore from backup
tar -xzf idps-backup-20240101.tar.gz
```

## Support and Issues

For bug reports and feature requests, visit:
- GitHub Issues: https://github.com/letchagan/raspberrypi-firewall/issues
- Documentation: https://github.com/letchagan/raspberrypi-firewall

## References

- [Suricata Documentation](https://suricata.io/documentation/)
- [nftables Wiki](https://wiki.nftables.org/)
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [Flask Documentation](https://flask.palletsprojects.com/)
