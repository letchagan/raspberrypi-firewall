# Development Guide

This guide covers development setup, testing, and contribution guidelines for the Raspberry Pi Firewall & IDPS project.

## Development Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/letchagan/raspberrypi-firewall.git
cd raspberrypi-firewall
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies (including dev tools)

```bash
pip install -r requirements.txt
pip install pytest pytest-cov black flake8
```

### 4. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit configuration
```

## Project Structure

```
raspberrypi-firewall/
├── app.py                          # Flask dashboard backend
├── decision_engine.py              # Suricata alert processor
├── threat_intel.py                 # Threat intelligence integration
├── blockpage_server.py             # Block page HTTP server
├── config.py                       # Centralized configuration
├── utils.py                        # Utility functions (validation, etc)
├── requirements.txt                # Python dependencies
├── .env.example                    # Example environment configuration
├── .gitignore                      # Git ignore rules
│
├── templates/
│   └── dashboard.html              # Web dashboard UI
├── blockpage/
│   └── block.html                  # Blocked traffic page
│
├── tests/                          # Unit and integration tests
│   ├── test_app.py                 # Flask app tests
│   └── test_utils.py               # Utility function tests
│
├── systemd/                        # Systemd service files
│   ├── idps.target                 # IDPS service target
│   ├── idps-decision-engine.service
│   ├── idps-blockpage.service
│   └── idps-dashboard.service
│
├── setup_gateway.sh                # Network gateway setup
├── setup_redirect.sh               # HTTP redirect setup
├── start_idps.sh                   # Startup script
│
├── README.md                       # Project overview
├── INSTALL.md                      # Installation guide
├── DEVELOPMENT.md                  # This file
├── SECURITY.md                     # Security guide
│
└── logs/                           # Runtime logs (gitignored)
```

## Code Style and Linting

### Format Code with Black

```bash
black app.py decision_engine.py threat_intel.py utils.py
```

### Lint with Flake8

```bash
flake8 app.py decision_engine.py threat_intel.py utils.py
```

### Fix Common Issues

```bash
# Format all Python files
black *.py

# Check for linting issues
flake8 *.py --max-line-length=120
```

## Running Tests

### Run All Tests

```bash
pytest
pytest -v  # Verbose
pytest --cov=.  # With coverage
```

### Run Specific Test File

```bash
pytest tests/test_utils.py -v
pytest tests/test_app.py -v
```

### Run with Coverage Report

```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## Key Modules

### config.py

Centralized configuration management using environment variables.

```python
from config import Config

# Access configuration
print(Config.FLASK_PORT)  # 3000
print(Config.GATEWAY_IP)  # 192.168.50.1
print(Config.EVE_LOG)     # /var/log/suricata/eve.json
```

### utils.py

Utility functions for validation and security.

```python
from utils import is_valid_ip, sanitize_ip, run_command, require_api_token

# Validate IP address
if is_valid_ip("192.168.1.1"):
    print("Valid IP")

# Safely run shell command
success, stdout, stderr = run_command(['nft', 'list', 'ruleset'])

# Protect Flask route with API token
@require_api_token
def protected_route():
    return "Only authenticated users see this"
```

## Adding New Features

### Adding a New API Endpoint

1. **Define the endpoint in app.py:**

```python
from utils import require_api_token, sanitize_ip, is_valid_ip

@app.route('/api/new-feature', methods=['POST'])
@limiter.limit("10 per minute")
@require_api_token
def new_feature():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    # Validate input
    value = sanitize_ip(data.get('value', ''))
    if not value:
        return jsonify({'error': 'Invalid value'}), 400
    
    # Process
    try:
        result = do_something(value)
        return jsonify({'status': 'success', 'result': result}), 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': 'Operation failed'}), 500
```

2. **Add tests in tests/test_app.py:**

```python
def test_new_feature(self, client):
    response = client.post('/api/new-feature', json={'value': '192.168.1.1'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status' in data

def test_new_feature_invalid_input(self, client):
    response = client.post('/api/new-feature', json={'value': 'invalid'})
    assert response.status_code == 400
```

3. **Update documentation in README.md or INSTALL.md**

### Adding Configuration Options

1. **Add to config.py:**

```python
class Config:
    NEW_OPTION = os.getenv('NEW_OPTION', 'default-value')
```

2. **Add to .env.example:**

```env
# New Feature Configuration
NEW_OPTION=default-value
```

3. **Use in code:**

```python
from config import Config
print(Config.NEW_OPTION)
```

## Testing Against Suricata

### Enable Suricata on Development Machine

```bash
# Install Suricata
sudo apt-get install suricata

# Copy test EVE log
echo '{"event_type":"alert","timestamp":"2024-01-01T12:00:00Z","src_ip":"192.168.1.100","dest_ip":"192.168.1.1","alert":{"signature":"Test Alert","severity":1,"category":"Test"}}' >> /var/log/suricata/eve.json

# Run decision engine
python3 decision_engine.py
```

### Mock Suricata Data

For testing without a real Suricata instance:

```python
# tests/conftest.py
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_eve_log(tmp_path):
    eve_file = tmp_path / "eve.json"
    eve_file.write_text(
        '{"event_type":"alert","timestamp":"2024-01-01T12:00:00Z",'
        '"src_ip":"203.0.113.1","dest_ip":"192.168.1.1",'
        '"alert":{"signature":"Test","severity":1}}\n'
    )
    return str(eve_file)
```

## Debug Mode

### Enable Debug Logging

```bash
DEBUG=True python3 app.py
```

### Flask Debug Server

```bash
FLASK_ENV=development FLASK_DEBUG=1 python3 -m flask run
```

### Verbose nftables Logging

```bash
sudo nft -nn list ruleset
```

## Common Development Tasks

### Adding a new utility function

1. Write function in utils.py
2. Add docstring
3. Write tests in tests/test_utils.py
4. Run pytest to verify

### Modifying decision engine logic

1. Edit decision_engine.py
2. Update AUTO_BLOCK_SEVERITY in .env if needed
3. Test with mock Suricata data
4. Review logs: tail -f /home/pi/idps/logs/decision_engine.log

### Updating API responses

1. Modify response in app.py
2. Add tests in tests/test_app.py
3. Document in INSTALL.md API section
4. Test with curl or Postman

## Debugging Tips

### Flask App Debugging

```python
# app.py
app.config['PROPAGATE_EXCEPTIONS'] = True

@app.before_request
def log_request():
    app.logger.info(f"Request: {request.method} {request.path}")

@app.after_request
def log_response(response):
    app.logger.info(f"Response: {response.status_code}")
    return response
```

### Decision Engine Debugging

```python
# decision_engine.py
import pdb

# Add breakpoint
pdb.set_trace()

# Or use print debugging
print(f"DEBUG: src_ip={src_ip}, severity={severity}")
```

### Check Running Processes

```bash
ps aux | grep python3
ps aux | grep suricata
ps aux | grep nft
```

### Monitor System Resources

```bash
top -p $(pgrep -f "python3|suricata" | tr '\n' ',')
watch -n 1 'ps aux | grep python3'
```

## Performance Optimization

### Profile with cProfile

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
process_alerts()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Memory Profiling

```bash
pip install memory-profiler
python3 -m memory_profiler decision_engine.py
```

## Git Workflow

### Create a Feature Branch

```bash
git checkout -b feature/my-feature
# Make changes
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature
# Open Pull Request
```

### Commit Message Format

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Add/update tests
- `refactor:` Code refactoring
- `perf:` Performance improvement
- `chore:` Maintenance tasks

Examples:
```
feat: add IP reputation scoring
fix: prevent command injection in nftables calls
docs: update security guide
test: add unit tests for utils
```

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Best Practices](https://pep8.org/)
- [Suricata Development](https://suricata.io/development/)
- [nftables Internals](https://wiki.nftables.org/wiki-nftables/index.php/Main_Page)
