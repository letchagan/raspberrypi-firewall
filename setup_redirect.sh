#!/bin/bash
# Remove old drop rules
nft delete table ip blocklist 2>/dev/null || true

# Create new table with redirect instead of drop
nft add table ip nat_redirect
nft add chain ip nat_redirect prerouting { type nat hook prerouting priority -100 \; }
nft add chain ip nat_redirect output { type nat hook output priority -100 \; }

# Redirect HTTP (port 80) from blocked IPs to block page
nft add set ip nat_redirect blocked_ips { type ipv4_addr \; flags interval \; }

# Redirect any connection TO blocked IPs on port 80
nft add rule ip nat_redirect prerouting \
  ip daddr @blocked_ips tcp dport 80 \
  redirect to :5001

# Also create DROP table for non-HTTP blocked traffic
nft add table ip blocklist
nft add set ip blocklist blocked_ips { type ipv4_addr \; flags interval \; }
nft add chain ip blocklist input { type filter hook input priority 0 \; }
nft add chain ip blocklist forward { type filter hook forward priority 0 \; }
nft add rule ip blocklist forward ip daddr @blocked_ips drop

echo "Redirect rules applied!"
