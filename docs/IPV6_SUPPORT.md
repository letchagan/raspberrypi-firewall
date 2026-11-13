# IPv6 Support Guide

This guide covers IPv6 configuration and support for the Raspberry Pi Firewall & IDPS.

## Overview

As of v2.1.0, the Raspberry Pi Firewall & IDPS has full support for blocking and monitoring both IPv4 and IPv6 traffic.

## Features

- ✅ IPv6 address validation and detection
- ✅ IPv6 blocking via nftables (ip6 tables)
- ✅ IPv6 alert processing
- ✅ IPv6 whitelist support
- ✅ Mixed IPv4/IPv6 environment support
- ✅ Link-local address detection

## Configuration

### Enable IPv6

Edit `.env`:

```bash
IPV6_ENABLED=True
IPV6_WHITELIST_IPS=::1,fe80::/10
```

### Whitelist IPv6 Addresses

```bash
# .env file
IPV6_WHITELIST_IPS=::1,2001:db8::1,fe80::/10
```

**Common IPv6 ranges to whitelist:**
- `::1` - Loopback
- `fe80::/10` - Link-local addresses
- `fc00::/7` - Unique local addresses (ULA)
- `ff00::/8` - Multicast

## IPv6 Address Validation

The system automatically detects and handles both IPv4 and IPv6 addresses:

```python
from utils import is_ipv4, is_ipv6, get_ip_version

# Validate IPv4
is_ipv4("192.168.1.1")  # True
is_ipv4("2001:db8::1")  # False

# Validate IPv6
is_ipv6("2001:db8::1")  # True
is_ipv6("192.168.1.1")  # False

# Get IP version
get_ip_version("192.168.1.1")  # 4
get_ip_version("2001:db8::1")  # 6
get_ip_version("invalid")      # None
```

## API Blocking IPv6 Addresses

### Block IPv6

```bash
curl -X POST http://192.168.50.1:3000/api/block \
  -H "Content-Type: application/json" \
  -H "X-API-Token: your-token" \
  -d '{"ip": "2001:db8::bad"}'

# Response
{
  "status": "blocked",
  "ip": "2001:db8::bad",
  "version": "IPv6"
}
```

### Unblock IPv6

```bash
curl -X POST http://192.168.50.1:3000/api/unblock \
  -H "Content-Type: application/json" \
  -H "X-API-Token: your-token" \
  -d '{"ip": "2001:db8::bad"}'

# Response
{
  "status": "unblocked",
  "ip": "2001:db8::bad",
  "version": "IPv6"
}
```

## nftables IPv6 Configuration

### Check IPv6 blocklist

```bash
# List IPv6 blocked IPs
sudo nft list set ip6 blocklist blocked_ips

# Add IPv6 manually
sudo nft add element ip6 blocklist blocked_ips { 2001:db8::bad }

# Remove IPv6
sudo nft delete element ip6 blocklist blocked_ips { 2001:db8::bad }
```

### Setup IPv6 Firewall Rules

The system automatically creates both IPv4 and IPv6 tables during setup:

```bash
# Verify dual-stack setup
sudo nft list ruleset | grep -A 5 "table ip6"

# Should show both:
# table ip blocklist   (IPv4)
# table ip6 blocklist  (IPv6)
```

## Private IPv6 Address Detection

The system recognizes private IPv6 addresses:

```python
from utils import is_private_ip, is_ipv6_link_local

# Unique Local Addresses (ULA)
is_private_ip("fc00::1")  # True

# Link-local
is_private_ip("fe80::1")  # True
is_ipv6_link_local("fe80::1")  # True

# Loopback
is_private_ip("::1")  # True
```

Private IPs are NOT automatically blocked even if detected in alerts.

## Suricata IPv6 Configuration

Ensure Suricata is monitoring IPv6 traffic:

```yaml
# /etc/suricata/suricata.yaml

vars:
  address-groups:
    HOME_NET: "[192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,[2001:db8::/32]]"
    EXTERNAL_NET: "![HOME_NET]"
    HTTP_PORTS: "80"
    SHELLCODE: "!:0"
```

## IPv6 Threat Intelligence

AbuseIPDB and other threat intelligence sources support IPv6.

```bash
# In .env
ABUSEIPDB_API_KEY=your-key
ABUSEIPDB_CONFIDENCE=85
```

The system will block IPv6 addresses from threat intelligence feeds automatically.

## Logging IPv6 Blocks

IPv6 blocks are logged with IPv6 table reference:

```
BLOCKED: 2001:db8::bad (ip6) — Malicious Activity
ALERT: 2001:db8::bad -> 192.168.50.1 | Port Scan | Severity: 2
```

## Testing IPv6 Blocking

### Generate test IPv6 alert

```python
# In Python, simulate IPv6 alert
import json
from datetime import datetime

alert = {
    "event_type": "alert",
    "timestamp": datetime.now().isoformat(),
    "src_ip": "2001:db8::bad",
    "dest_ip": "2001:db8::1",
    "alert": {
        "signature": "Test IPv6 Alert",
        "severity": 2,
        "category": "Test"
    }
}

print(json.dumps(alert))
```

### Verify IPv6 blocked list

```bash
# Check if IPv6 address is blocked
sudo nft list set ip6 blocklist blocked_ips | grep "2001:db8::bad"

# Or use timeout with IPv6 test
timeout 5 curl -6 http://[2001:db8::bad]:80/ 2>/dev/null || echo "Blocked"
```

## Dual-Stack Network Setup

### IPv6 Address Configuration

```bash
# Configure interface with IPv6
sudo ip addr add 2001:db8::1/64 dev eth0

# Enable IPv6 forwarding
sudo sysctl -w net.ipv6.conf.all.forwarding=1

# Make persistent
echo "net.ipv6.conf.all.forwarding = 1" | sudo tee -a /etc/sysctl.conf
```

### nftables IPv6 Rules

The setup scripts should create IPv6 rules:

```bash
# View IPv6 NAT configuration
sudo nft list table ip6 nat

# Manually add IPv6 NAT if needed
sudo nft add rule ip6 nat postrouting masquerade
```

## Troubleshooting

### IPv6 alerts not being blocked

**Problem:** IPv6 IPs appear in alerts but aren't blocked

**Solution:**
```bash
# Check if IPv6 table exists
sudo nft list table ip6 blocklist

# If missing, create manually
sudo nft add table ip6 blocklist
sudo nft add set ip6 blocklist blocked_ips { type ipv6_addr \; flags interval \; }
```

### Can't block IPv6 address via API

**Problem:** API call fails with error

**Solution:**
```bash
# Verify address is valid IPv6
python3 -c "import ipaddress; ipaddress.ip_address('2001:db8::1')"

# Check nftables permissions
sudo nft list ruleset | grep ip6

# Ensure running as root/sudo
sudo python3 app.py
```

### Notification not sent for IPv6 alerts

**Problem:** Email/Telegram not triggered for IPv6 alerts

**Solution:**
- Verify notification settings in `.env`
- Check notification logs
- Confirm alert severity meets notification threshold (AUTO_BLOCK_SEVERITY)

## Performance Considerations

IPv6 handling has minimal performance impact:

- IP validation: < 1ms per address
- nftables IPv6 operations: Same as IPv4
- Logging: Identical performance

## IPv6 CIDR Notation

The system supports IPv6 CIDR notation for subnets:

```bash
# Whitelist entire IPv6 subnet
IPV6_WHITELIST_IPS=::1,2001:db8::/32,fc00::/7

# API blocking CIDR ranges
curl -X POST http://192.168.50.1:3000/api/block \
  -H "X-API-Token: token" \
  -d '{"ip": "2001:db8::/32"}'
```

## Migration from IPv4-Only

If upgrading from IPv4-only installation:

1. Update `.env.example` to `.env`
2. Set `IPV6_ENABLED=True`
3. Update nftables rules for IPv6
4. Restart decision engine and dashboard
5. Verify IPv6 table creation: `sudo nft list ruleset | grep ip6`

## Further Reading

- [RFC 4291 - IPv6 Addressing Architecture](https://tools.ietf.org/html/rfc4291)
- [nftables IPv6 Support](https://wiki.nftables.org/wiki-nftables/index.php/IPv6)
- [Python ipaddress Module](https://docs.python.org/3/library/ipaddress.html)
- [Suricata IPv6](https://suricata.readthedocs.io/en/latest/)
