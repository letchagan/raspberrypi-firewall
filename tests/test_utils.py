import pytest
from utils import is_valid_ip, is_private_ip, sanitize_ip

class TestIPValidation:
    def test_valid_ipv4(self):
        assert is_valid_ip("192.168.1.1") == True
        assert is_valid_ip("8.8.8.8") == True
        assert is_valid_ip("203.0.113.10") == True

    def test_invalid_ipv4(self):
        assert is_valid_ip("256.256.256.256") == False
        assert is_valid_ip("192.168.1") == False
        assert is_valid_ip("not-an-ip") == False
        assert is_valid_ip("") == False

    def test_private_ip(self):
        assert is_private_ip("192.168.1.1") == True
        assert is_private_ip("10.0.0.1") == True
        assert is_private_ip("127.0.0.1") == True
        assert is_private_ip("8.8.8.8") == False
        assert is_private_ip("203.0.113.10") == False

    def test_sanitize_ip(self):
        assert sanitize_ip("192.168.1.1") == "192.168.1.1"
        assert sanitize_ip("  8.8.8.8  ") == "8.8.8.8"
        assert sanitize_ip("invalid") is None
        assert sanitize_ip("") is None
        assert sanitize_ip(None) is None
