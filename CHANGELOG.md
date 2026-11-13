# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2024-11-06 - Security & Architecture Overhaul

### 🔒 Security Improvements

- **Command Injection Prevention**: Replaced all `os.system()` calls with `subprocess.run()` using argument lists
- **Input Validation**: Added comprehensive IP address validation using `ipaddress` module
- **API Authentication**: Optional token-based authentication via `X-API-Token` header
- **Rate Limiting**: Added Flask-Limiter to prevent brute-force attacks and DoS
- **Exception Handling**: Improved error handling with specific exception types
- **Thread Safety**: Added `threading.Lock()` for shared data structures
- **Graceful Shutdown**: Implemented signal handlers for SIGTERM/SIGINT
- **Private IP Detection**: Added whitelist for private IP ranges

### 📋 Configuration & Deployment

- **Centralized Config**: Created `config.py` for centralized configuration management
- **Environment Variables**: Support for `.env` configuration file via `python-dotenv`
- **Systemd Services**: Added production-ready systemd service files
- **Log Management**: Standardized logging across all components
- **Health Endpoint**: Added `/api/health` endpoint for monitoring

### 🏗️ Architecture Improvements

- **Modular Utilities**: Created `utils.py` with reusable security functions
- **Error Responses**: Proper HTTP status codes and error messages
- **Logging**: Comprehensive logging with structured format
- **Rate Limiting**: Configurable rate limits on sensitive endpoints
- **API Audit Trail**: Action logging for block/unblock operations

### 📚 Documentation

- **INSTALL.md**: Complete installation and deployment guide
- **SECURITY.md**: Security hardening guide and best practices
- **DEVELOPMENT.md**: Development setup and contribution guidelines
- **CHANGELOG.md**: This file - version history

### 🧪 Testing

- **Unit Tests**: Added pytest-based test suite
- **Validation Tests**: Tests for IP validation functions
- **API Tests**: Tests for Flask endpoints
- **Rate Limiting Tests**: Tests for rate limit enforcement
- **pytest.ini**: Test configuration

### 📦 Project Structure

- **requirements.txt**: Pinned Python dependencies
- **.env.example**: Example configuration template
- **.gitignore**: Updated to exclude sensitive files
- **systemd/**: Production service files
- **tests/**: Comprehensive test suite

### 🔧 Dependencies

Added:
- `Flask-Limiter==3.5.0` - Rate limiting
- `python-dotenv==1.0.0` - Environment variable management

Updated:
- All dependencies now have pinned versions for reproducibility

### ⚠️ Breaking Changes

- Configuration moved to `config.py` and `.env` file
- All `os.system()` calls replaced with `subprocess.run()`
- Flask endpoint responses now include proper error messages and status codes
- IP validation is now mandatory for block/unblock operations

### 🔄 Migration Guide from v1.x

For users upgrading from v1.x:

1. Copy `.env.example` to `.env`
2. Update configuration values from previous hardcoded settings
3. Test all endpoints before deploying to production
4. Review security recommendations in `SECURITY.md`
5. Set up systemd services for production deployment

### 🐛 Bug Fixes

- Fixed race condition in ALERTS list access
- Fixed exception handling in file operations
- Fixed command injection vulnerability in IP blocking
- Fixed missing error handling in API endpoints

### 📝 Code Quality

- Added comprehensive docstrings
- Improved exception handling
- Standardized logging format
- Added type hints where appropriate
- Improved code organization

### 🚀 Performance

- Optimized alert processing with thread locks
- Improved batch processing for threat intelligence IPs
- Reduced memory footprint with proper cleanup

---

## [1.0.0] - Initial Release

- Initial Raspberry Pi Firewall & IDPS implementation
- Suricata IDS/IPS integration
- nftables firewall configuration
- Flask web dashboard
- AbuseIPDB threat intelligence integration
- Benchmarking tools
- HTTP block page redirection
