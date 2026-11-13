# SSL/TLS Setup Guide

This guide covers HTTPS/TLS configuration for the Raspberry Pi Firewall & IDPS Flask dashboard and block page server.

## Quick Start

### Enable HTTPS with Auto-Generated Self-Signed Certificate

1. Update `.env` file:
```bash
cp .env.example .env
nano .env

# Set these values:
SSL_ENABLED=True
SSL_AUTO_GENERATE=True
SSL_HOSTNAME=raspberrypi.local
SSL_CERT_PATH=/home/pi/idps/logs/certs/cert.pem
SSL_KEY_PATH=/home/pi/idps/logs/certs/key.pem
```

2. Start the application:
```bash
python3 app.py
```

The application will automatically generate a self-signed certificate on first run.

## Configuration Options

### Environment Variables

```bash
# Enable HTTPS (default: False)
SSL_ENABLED=True

# Certificate file path
SSL_CERT_PATH=/home/pi/idps/logs/certs/cert.pem

# Private key file path
SSL_KEY_PATH=/home/pi/idps/logs/certs/key.pem

# Hostname for certificate CN field (default: localhost)
SSL_HOSTNAME=raspberrypi.local

# Auto-generate self-signed certificate if missing (default: True)
SSL_AUTO_GENERATE=True

# SSL protocol version (default: TLS)
SSL_PROTOCOL=TLS
```

## Certificate Types

### 1. Self-Signed Certificate (Default)

Suitable for development and internal use.

**Pros:**
- No cost
- Quick to generate
- Works for internal networks

**Cons:**
- Browser warnings (certificate not trusted)
- Not suitable for public-facing services
- Manual browser acceptance required

**Generate automatically:**
```bash
SSL_ENABLED=True
SSL_AUTO_GENERATE=True
```

### 2. Let's Encrypt Certificate

Suitable for production deployments with domain names.

**Pros:**
- Trusted by all browsers
- Free
- Automatic renewal

**Cons:**
- Requires public domain name
- Requires internet access
- Certificate renewal automation needed

**Manual setup:**

```bash
# 1. Install certbot
sudo apt-get install certbot

# 2. Generate certificate
sudo certbot certonly --standalone -d yourdomain.com

# 3. Update .env
SSL_ENABLED=True
SSL_AUTO_GENERATE=False
SSL_CERT_PATH=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### 3. Custom Certificate

Use your own certificate from a Certificate Authority.

**Setup:**

```bash
# 1. Copy your certificate files
cp your-cert.pem /home/pi/idps/logs/certs/cert.pem
cp your-key.pem /home/pi/idps/logs/certs/key.pem

# 2. Update .env
SSL_ENABLED=True
SSL_AUTO_GENERATE=False
SSL_CERT_PATH=/home/pi/idps/logs/certs/cert.pem
SSL_KEY_PATH=/home/pi/idps/logs/certs/key.pem

# 3. Ensure correct permissions
sudo chmod 600 /home/pi/idps/logs/certs/key.pem
sudo chmod 644 /home/pi/idps/logs/certs/cert.pem
```

## Accessing the Dashboard

### With Self-Signed Certificate

```bash
# Accept self-signed certificate (for testing)
curl -k https://192.168.50.1:3000/api/health

# In browser, navigate to:
https://192.168.50.1:3000
# (Click "Advanced" and accept the warning)
```

### With Valid Certificate

```bash
curl https://yourdomain.com:3000/api/health
```

## Certificate Validation

### Check certificate information:

```bash
# View certificate details
openssl x509 -in /home/pi/idps/logs/certs/cert.pem -text -noout

# Check expiration date
openssl x509 -in /home/pi/idps/logs/certs/cert.pem -noout -dates

# Verify certificate and key match
openssl x509 -noout -modulus -in /home/pi/idps/logs/certs/cert.pem | \
  openssl md5 | cut -d' ' -f2
openssl rsa -noout -modulus -in /home/pi/idps/logs/certs/key.pem | \
  openssl md5 | cut -d' ' -f2
```

### Programmatic validation:

```python
from ssl_helper import SSLHelper

# Get certificate information
info = SSLHelper.get_certificate_info('/home/pi/idps/logs/certs/cert.pem')
print(info)

# Check if expiring soon
if SSLHelper.is_certificate_expiring_soon('/home/pi/idps/logs/certs/cert.pem', days=30):
    print("Certificate expires within 30 days!")
```

## Certificate Renewal

### For Self-Signed Certificates

```bash
# Delete old certificate
rm /home/pi/idps/logs/certs/cert.pem /home/pi/idps/logs/certs/key.pem

# Restart app (will auto-generate new certificate)
systemctl restart idps-dashboard
```

### For Let's Encrypt Certificates

```bash
# Renew certificate
sudo certbot renew

# Restart application
systemctl restart idps-dashboard
```

## SSL/TLS Security

### Cipher Configuration

By default, the application uses strong ciphers:

```python
"ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL"
```

This prioritizes:
- ECDHE (Elliptic Curve Diffie-Hellman)
- AESGCM and CHACHA20 (modern ciphers)
- Excludes NULL and anon ciphers

### Protocol Version

By default:
- TLS 1.2+ (TLS 1.0 and 1.1 disabled)
- TLS 1.3 preferred when available

## Systemd Service Configuration

Update `/etc/systemd/system/idps-dashboard.service`:

```ini
[Unit]
Description=IDPS Flask Dashboard
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/idps
Environment="SSL_ENABLED=True"
Environment="SSL_CERT_PATH=/home/pi/idps/logs/certs/cert.pem"
Environment="SSL_KEY_PATH=/home/pi/idps/logs/certs/key.pem"
ExecStart=/usr/bin/python3 /home/pi/idps/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable idps-dashboard.service
sudo systemctl restart idps-dashboard.service
```

## Troubleshooting

### Certificate Not Found

```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution:**
- Set `SSL_AUTO_GENERATE=True`
- Or place certificate files at configured paths
- Restart application

### Permission Denied on Certificate

```
Permission denied: '/home/pi/idps/logs/certs/key.pem'
```

**Solution:**
```bash
sudo chmod 600 /home/pi/idps/logs/certs/key.pem
sudo chmod 644 /home/pi/idps/logs/certs/cert.pem
sudo chown pi:pi /home/pi/idps/logs/certs/*
```

### Certificate and Key Don't Match

```
SSL: PEM_LIB (_ssl.c:4039)
```

**Solution:**
- Verify certificate and key match (see "Certificate Validation" section)
- Use files generated together or from same source
- Regenerate if needed

### Port Already in Use

```
Address already in use
```

**Solution:**
```bash
# Kill existing process
sudo lsof -ti:3000 | xargs kill -9

# Or change port in .env
FLASK_PORT=3443
```

## Best Practices

1. **Always use HTTPS in production**
   ```bash
   SSL_ENABLED=True
   ```

2. **Keep certificates backed up**
   ```bash
   sudo cp -r /home/pi/idps/logs/certs /backup/idps-certs/
   ```

3. **Monitor certificate expiration**
   - Set calendar reminder
   - Use monitoring script with systemd timer

4. **Rotate certificates regularly**
   - Even for self-signed certs (e.g., yearly)
   - For Let's Encrypt, enable auto-renewal

5. **Restrict certificate file permissions**
   ```bash
   chmod 600 /home/pi/idps/logs/certs/key.pem
   chmod 644 /home/pi/idps/logs/certs/cert.pem
   ```

## API Examples

### With Self-Signed Certificate

```bash
# Accept self-signed cert
curl -k -X GET https://192.168.50.1:3000/api/health

# Block an IP
curl -k -X POST https://192.168.50.1:3000/api/block \
  -H "Content-Type: application/json" \
  -H "X-API-Token: your-secret-token" \
  -d '{"ip": "203.0.113.10"}'
```

### With Valid Certificate

```bash
curl -X GET https://yourdomain.com:3000/api/health

curl -X POST https://yourdomain.com:3000/api/block \
  -H "Content-Type: application/json" \
  -H "X-API-Token: your-secret-token" \
  -d '{"ip": "203.0.113.10"}'
```

## Certificate Chain

For production with CA-signed certificates, ensure you have the full chain:

```bash
# Combine certificate and intermediate CA certs
cat your-cert.pem intermediate-ca.pem ca-root.pem > fullchain.pem

# Use in configuration
SSL_CERT_PATH=/path/to/fullchain.pem
SSL_KEY_PATH=/path/to/key.pem
```

## Further Reading

- [OWASP Transport Layer Protection](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Python ssl Module](https://docs.python.org/3/library/ssl.html)
