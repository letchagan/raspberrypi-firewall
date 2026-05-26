#!/bin/bash
echo "======================================"
echo "  CONFIGURING RASPBERRY PI GATEWAY"
echo "======================================"

# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1 >/dev/null

# Remove any stale conflicting route
sudo ip route del 192.168.50.0/24 dev wlan0 2>/dev/null

# Flush existing nftables rules
sudo nft flush ruleset

# NAT table
sudo nft add table ip nat
sudo nft add chain ip nat postrouting '{ type nat hook postrouting priority 100; }'
sudo nft add rule ip nat postrouting oifname "wlan0" masquerade

# Blocklist table
sudo nft add table ip blocklist
sudo nft add set ip blocklist blocked_ips '{ type ipv4_addr; flags interval; }'

# Forward chain
sudo nft add chain ip blocklist forward '{ type filter hook forward priority 0; policy accept; }'

# Drop traffic from blocked IPs
sudo nft add rule ip blocklist forward ip saddr @blocked_ips drop

echo "======================================"
echo "  GATEWAY READY"
echo "  WAN : wlan0"
echo "  LAN : eth0 (192.168.50.1)"
echo "======================================"
