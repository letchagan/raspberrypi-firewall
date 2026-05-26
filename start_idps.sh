#!/bin/bash
echo "======================================"
echo "  IDPS STARTUP SEQUENCE"
echo "======================================"

# Kill any existing processes
echo "[1/6] Stopping existing processes..."
sudo pkill suricata 2>/dev/null
sudo pkill -f app.py 2>/dev/null
sudo pkill -f decision_engine.py 2>/dev/null
sleep 3

# Clear old logs
echo "[2/6] Clearing old logs..."
sudo rm -f /var/log/suricata/fast.log
sudo rm -f /var/log/suricata/eve.json

# Start Suricata
echo "[3/6] Starting Suricata IPS..."
sudo suricata -c /etc/suricata/suricata.yaml --pcap=usb0 -l /var/log/suricata/ -D
sleep 10
sudo pgrep suricata > /dev/null && echo "  ✅ Suricata running" || echo "  ❌ Suricata failed"

# Update threat intel
echo "[4/6] Updating threat intelligence..."
cd /home/pi/idps
sudo python3 threat_intel.py
echo "  ✅ Threat intel updated"

# Start decision engine
echo "[5/6] Starting decision engine..."
sudo python3 /home/pi/idps/decision_engine.py &
sleep 2
echo "  ✅ Decision engine running"

echo "[+] Starting block page server..."
sudo python3 /home/pi/idps/blockpage_server.py &
sleep 1
echo "  Block page running on port 5001"

# Start dashboard
echo "[6/6] Starting dashboard..."
cd /home/pi/idps && sudo python3 app.py &
sleep 2
echo "  ✅ Dashboard running"

echo ""
echo "======================================"
echo "  IDPS FULLY OPERATIONAL!"
echo "  Dashboard: http://192.168.50.1:5000"
echo "  Monitoring: eth0 (laptop traffic)"
echo "  Logs: sudo tail -f /var/log/suricata/fast.log"
echo "======================================"
