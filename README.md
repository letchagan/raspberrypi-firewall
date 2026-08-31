# Raspberry Pi Firewall & IDPS

A lightweight Raspberry Pi–based **Intrusion Detection and Prevention System (IDPS)** that combines **Suricata**, **nftables**, threat intelligence, and a **Flask web dashboard** to monitor network traffic, detect suspicious activity, and block malicious IP addresses.

## 🚀 Overview

This project turns a Raspberry Pi into a network security gateway.

The system uses:

- **Suricata** to inspect network traffic and generate security alerts.
- **Python decision engine** to process Suricata alerts and automatically react to high-severity threats.
- **nftables** to maintain and enforce IP blocklists.
- **AbuseIPDB** to obtain external threat-intelligence IP blocklists.
- **Flask dashboard** to visualize alerts and firewall statistics in real time.
- **HTTP block page** to provide feedback when traffic is redirected.
- **Benchmarking tools** to evaluate detection rate, response time, latency, and false positives.

## 🏗️ Architecture

```text
                         Internet / WAN
                              │
                              ▼
                       ┌───────────────┐
                       │  Raspberry Pi │
                       │   Gateway     │
                       └───────┬───────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐     ┌──────────┐    ┌──────────────┐
        │ Suricata │     │ nftables │    │ Threat Intel │
        │ IDS / IPS│     │ Firewall │    │  AbuseIPDB   │
        └────┬─────┘     └────┬─────┘    └──────┬───────┘
             │                │                 │
             ▼                │                 │
      /var/log/suricata/      │                 │
          eve.json            │                 │
             │                │                 │
             ▼                ▼                 ▼
       ┌─────────────────────────────────────────┐
       │            Decision Engine              │
       │     Detect → Evaluate → Block/Log       │
       └───────────────────┬─────────────────────┘
                           │
                           ▼
                    Blocked IPs / Logs
                           │
                           ▼
                  ┌──────────────────┐
                  │ Flask Dashboard  │
                  │  Live Monitoring │
                  └──────────────────┘
```

## ✨ Features

- 🔍 Real-time Suricata alert monitoring
- 🛡️ Automatic blocking of high-severity threats
- 🔥 nftables-based IP filtering
- 🌐 AbuseIPDB threat-intelligence integration
- 📊 Web-based security dashboard
- ⚡ Live alerts using Server-Sent Events (SSE)
- 🚫 Manual IP block/unblock API
- 📄 Custom HTTP block page
- 📈 Detection and performance benchmarking
- 📉 False-positive and latency measurements
- 📝 Security event logging

## 📁 Project Structure

```text
raspberrypi-firewall/
│
├── app.py                    # Flask dashboard backend
├── decision_engine.py        # Suricata alert decision engine
├── threat_intel.py           # AbuseIPDB threat intelligence
├── blockpage_server.py       # Local block-page HTTP server
│
├── setup_gateway.sh          # Raspberry Pi gateway configuration
├── setup_redirect.sh         # nftables HTTP redirect configuration
├── start_idps.sh             # Start complete IDPS stack
│
├── benchmark.py              # Detection/performance benchmarking
├── generate_graphs.py        # Benchmark graph generation
│
├── templates/
│   └── dashboard.html        # Web dashboard UI
│
├── blockpage/
│   └── block.html             # Blocked traffic page
│
├── logs/                     # Runtime and benchmark logs
│
├── idps_model.pkl            # Serialized IDPS model
├── scaler.pkl                # Model feature scaler
├── label_encoder.pkl         # Model label encoder
│
└── README.md
```

## 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| Raspberry Pi | Security gateway hardware |
| Linux | Operating system |
| Suricata | IDS/IPS traffic inspection |
| nftables | Firewall and IP blocking |
| Python | Security automation and backend |
| Flask | Web dashboard/API |
| Server-Sent Events | Real-time alert streaming |
| AbuseIPDB | Threat intelligence |
| Matplotlib | Benchmark visualization |
| Bash | System/network setup |

## 🔧 Requirements

Recommended environment:

- Raspberry Pi
- Raspberry Pi OS / Debian-based Linux
- Python 3
- Suricata
- nftables
- Root/sudo access
- Network interfaces such as `wlan0` and `eth0`
- AbuseIPDB API key

Python packages:

```bash
pip install flask flask-cors requests numpy matplotlib
```

## 📥 Installation

### 1. Clone the repository

```bash
git clone https://github.com/letchagan/raspberrypi-firewall.git
cd raspberrypi-firewall
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install flask flask-cors requests numpy matplotlib
```

## 🔐 Configure AbuseIPDB

Create a `.env` file:

```env
ABUSEIPDB_API_KEY=your_api_key_here
```

**Never expose a real API key in a public repository.**

The threat-intelligence module uses the AbuseIPDB blacklist endpoint and currently requests malicious IPs with a confidence threshold of 85%.

## 🌐 Network Configuration

The current gateway configuration assumes:

```text
WAN Interface : wlan0
LAN Interface : eth0
LAN Gateway   : 192.168.50.1
```

The gateway enables IPv4 forwarding and configures NAT masquerading on `wlan0`.

Before deployment, change the interfaces/subnet in the scripts if your network uses a different topology.

## ⚙️ Gateway Setup

Run:

```bash
sudo bash setup_gateway.sh
```

This configures:

- IPv4 forwarding
- nftables NAT
- IP masquerading
- Blocklist table
- Blocklist IPv4 set
- Forwarding filter
- Blocked-source packet dropping

Check the firewall afterward:

```bash
sudo nft list ruleset
```

## 🚫 Configure Block Redirection

Run:

```bash
sudo bash setup_redirect.sh
```

The redirect configuration:

- Creates an nftables redirect table.
- Redirects HTTP traffic destined for blocked IPs to port `5001`.
- Drops other forwarded traffic destined for blocked IPs.

## ▶️ Start the IDPS

Run:

```bash
sudo bash start_idps.sh
```

The startup sequence launches:

1. Suricata
2. Threat-intelligence update
3. Decision engine
4. Block-page server
5. Flask dashboard

### Dashboard

The Flask application currently listens on:

```text
0.0.0.0:3000
```

Open:

```text
http://192.168.50.1:3000
```

> **Note:** `start_idps.sh` currently displays port `5000` in its final message, while `app.py` actually starts Flask on port `3000`. The application configuration should be treated as the source of truth.

### Block Page

The block page server listens on:

```text
0.0.0.0:5001
```

## 🧠 Decision Engine

`decision_engine.py` continuously monitors:

```text
/var/log/suricata/eve.json
```

When a Suricata alert is detected, the engine extracts:

- Timestamp
- Source IP
- Destination IP
- Signature
- Severity

Current response logic:

```text
Severity 1 → Automatically block
Severity 2 → Automatically block
Severity 3 → Log only
```

The project also includes a trusted-IP list to prevent configured local systems from being automatically blocked.

Example:

```python
WHITELIST_IPS = {
    "192.168.50.1",
    "192.168.50.2",
    "127.0.0.1",
}
```

## 🌍 Threat Intelligence

Run:

```bash
sudo python3 threat_intel.py
```

The module:

1. Reads the AbuseIPDB API key.
2. Downloads the AbuseIPDB blacklist.
3. Filters using a confidence threshold.
4. Loads malicious IPs into nftables.
5. Saves the blocklist to the logs directory.

The default configuration requests:

```text
Confidence minimum: 85
Maximum IPs:        500
```

## 📊 Flask Dashboard API

### Get Alerts

```http
GET /api/alerts
```

Returns recent Suricata alerts.

### Get Statistics

```http
GET /api/stats
```

Provides information such as:

- Total alerts
- Blocked IP count
- Suricata status
- System uptime
- Current timestamp

### Live Alert Stream

```http
GET /stream
```

Uses Server-Sent Events to stream newly detected alerts.

### Block an IP

```http
POST /api/block
Content-Type: application/json
```

Request:

```json
{
  "ip": "203.0.113.10"
}
```

### Unblock an IP

```http
POST /api/unblock
Content-Type: application/json
```

Request:

```json
{
  "ip": "203.0.113.10"
}
```

## 🧪 Benchmarking

Run:

```bash
sudo python3 benchmark.py
```

The benchmark tests include:

- Malicious user-agent detection
- Attack-response detection
- Nmap port-scan detection
- Network latency
- False-positive rate
- Detection response time

Each detection test performs multiple trials and calculates:

```text
Detection Rate
Average Response Time
Minimum Response Time
Maximum Response Time
```

Results are saved as:

```text
/home/pi/idps/logs/benchmark_results.json
```

## 📈 Generate Graphs

Run:

```bash
python3 generate_graphs.py
```

Generated graphs include:

```text
fig3_detection_accuracy.png
fig4_response_time.png
fig5_cost_vs_performance.png
fig6_false_positive.png
```

These charts can be used for project reports, presentations, and performance analysis.

## 📝 Logs

Important logs include:

```text
/var/log/suricata/eve.json
/var/log/suricata/fast.log

/home/pi/idps/logs/decision_engine.log
/home/pi/idps/logs/threat_intel.log
/home/pi/idps/logs/blocked_ips.txt
/home/pi/idps/logs/benchmark_results.json
```

Monitor Suricata:

```bash
sudo tail -f /var/log/suricata/eve.json
```

Monitor the decision engine:

```bash
sudo tail -f /home/pi/idps/logs/decision_engine.log
```

## 🔎 Useful Commands

### Check Suricata

```bash
sudo pgrep -a suricata
```

### Check nftables

```bash
sudo nft list ruleset
```

### Check blocked IPs

```bash
sudo nft list set ip blocklist blocked_ips
```

### Check network interfaces

```bash
ip addr
```

### Check routing

```bash
ip route
```

### Test dashboard

```bash
curl http://127.0.0.1:3000/api/stats
```

### Test block page

```bash
curl http://127.0.0.1:5001/
```

## 🔒 Security Considerations

This project performs privileged network operations and should be deployed carefully.

Before using it in a production environment, consider:

- Validate all IP addresses received through the API.
- Avoid passing untrusted input directly to shell commands.
- Replace `os.system()` with safer `subprocess` argument lists.
- Protect the dashboard with authentication.
- Restrict dashboard access to a trusted management network.
- Store API keys securely.
- Make network interfaces configurable.
- Make filesystem paths configurable.
- Persist nftables rules across reboots.
- Run components as managed `systemd` services.
- Add automated unit/integration tests.
- Review the automatic blocking direction for each Suricata rule.

## ⚠️ Current Limitations

The current implementation contains environment-specific configuration, including:

```text
/home/pi/idps
192.168.50.0/24
wlan0
eth0
usb0
```

These values may need to be changed for another Raspberry Pi/network.

The dashboard also contains privileged firewall operations, so it should not be exposed directly to an untrusted network.

## 🛠️ Future Improvements

Potential improvements include:

- [ ] Add authentication to the dashboard
- [ ] Add HTTPS support
- [ ] Add configurable firewall rules
- [ ] Add persistent nftables configuration
- [ ] Add systemd services
- [ ] Add Docker deployment option
- [ ] Add database-backed alert history
- [ ] Add IP reputation scoring
- [ ] Add configurable severity thresholds
- [ ] Add email/Telegram security alerts
- [ ] Add automated unit tests
- [ ] Add Docker/CI testing
- [ ] Improve IPv6 support
- [ ] Add role-based dashboard access
- [ ] Make all paths and interfaces configurable

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch:

```bash
git checkout -b feature/my-feature
```

3. Make your changes.
4. Test the changes on an isolated network.
5. Commit:

```bash
git commit -m "feat: add my feature"
```

6. Push:

```bash
git push origin feature/my-feature
```

7. Open a Pull Request.

## ⚖️ License

No license file is currently included in this repository.

If you want others to legally use, modify, and distribute the project, add an appropriate `LICENSE` file.

## 👨‍💻 Author

**Letchagan**

GitHub: https://github.com/letchagan

Repository: https://github.com/letchagan/raspberrypi-firewall

---

⭐ If you find this project useful, consider giving the repository a star!
