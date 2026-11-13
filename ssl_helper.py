"""SSL/TLS certificate management helper module."""

import os
import ssl
import logging
from pathlib import Path
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)


class SSLHelper:
    """Helper class for SSL/TLS certificate management."""

    @staticmethod
    def generate_self_signed_cert(
        cert_path: str,
        key_path: str,
        hostname: str = "localhost",
        days_valid: int = 365,
    ) -> bool:
        """
        Generate a self-signed SSL certificate.

        Args:
            cert_path: Path to save the certificate
            key_path: Path to save the private key
            hostname: Hostname for the certificate (CN field)
            days_valid: Number of days the certificate is valid

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directories if they don't exist
            Path(cert_path).parent.mkdir(parents=True, exist_ok=True)
            Path(key_path).parent.mkdir(parents=True, exist_ok=True)

            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            # Generate certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Org"),
                x509.NameAttribute(NameOID.COMMON_NAME, hostname),
            ])

            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(private_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.utcnow())
                .not_valid_after(datetime.utcnow() + timedelta(days=days_valid))
                .add_extension(
                    x509.SubjectAlternativeName([
                        x509.DNSName(hostname),
                        x509.DNSName("*.local"),
                    ]),
                    critical=False,
                )
                .sign(private_key, hashes.SHA256(), default_backend())
            )

            # Write certificate to file
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            os.chmod(cert_path, 0o644)

            # Write private key to file
            with open(key_path, "wb") as f:
                f.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                )
            os.chmod(key_path, 0o600)

            logger.info(
                f"Generated self-signed certificate: {cert_path}, key: {key_path}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to generate SSL certificate: {e}")
            return False

    @staticmethod
    def verify_certificate_exists(cert_path: str, key_path: str) -> bool:
        """
        Verify that certificate and key files exist and are readable.

        Args:
            cert_path: Path to certificate file
            key_path: Path to private key file

        Returns:
            True if both files exist and are readable, False otherwise
        """
        try:
            return os.path.isfile(cert_path) and os.path.isfile(key_path)
        except Exception as e:
            logger.error(f"Error verifying certificate files: {e}")
            return False

    @staticmethod
    def get_certificate_info(cert_path: str) -> dict:
        """
        Extract information from a certificate file.

        Args:
            cert_path: Path to certificate file

        Returns:
            Dictionary with certificate information
        """
        try:
            with open(cert_path, "rb") as f:
                cert_data = f.read()

            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

            return {
                "subject": cert.subject.rfc4514_string(),
                "issuer": cert.issuer.rfc4514_string(),
                "not_valid_before": cert.not_valid_before,
                "not_valid_after": cert.not_valid_after,
                "serial_number": cert.serial_number,
                "is_valid": cert.not_valid_before <= datetime.utcnow() <= cert.not_valid_after,
            }

        except Exception as e:
            logger.error(f"Error reading certificate: {e}")
            return {}

    @staticmethod
    def create_ssl_context(
        cert_path: str,
        key_path: str,
        protocol: int = ssl.PROTOCOL_TLS_SERVER,
    ) -> ssl.SSLContext:
        """
        Create an SSL context for HTTPS server.

        Args:
            cert_path: Path to certificate file
            key_path: Path to private key file
            protocol: SSL protocol version

        Returns:
            Configured SSLContext or None on error
        """
        try:
            context = ssl.SSLContext(protocol)
            context.load_cert_chain(cert_path, key_path)

            # Security options
            context.set_ciphers(
                "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL"
            )
            context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE

            logger.info("SSL context created successfully")
            return context

        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            return None

    @staticmethod
    def is_certificate_expiring_soon(cert_path: str, days: int = 30) -> bool:
        """
        Check if certificate will expire within specified days.

        Args:
            cert_path: Path to certificate file
            days: Number of days to check ahead

        Returns:
            True if certificate expires within specified days
        """
        try:
            cert_info = SSLHelper.get_certificate_info(cert_path)
            if not cert_info:
                return True

            expiry = cert_info.get("not_valid_after")
            if not expiry:
                return True

            return expiry <= datetime.utcnow() + timedelta(days=days)

        except Exception as e:
            logger.error(f"Error checking certificate expiry: {e}")
            return True
