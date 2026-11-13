import signal
import logging
import os
import ssl
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from config import Config
from ssl_helper import SSLHelper

Config.ensure_log_dir()

logging.basicConfig(
    filename=Config.THREAT_INTEL_LOG,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

shutdown_event = False

def signal_handler(sig, frame):
    global shutdown_event
    logger.info("Received shutdown signal, stopping block page server...")
    shutdown_event = True

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

class BlockPageHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        block_page_path = os.path.join(Config.BLOCKPAGE_DIR, 'block.html')

        if not os.path.exists(block_page_path):
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>404: Block page not found</h1>")
            logger.warning(f"Block page not found at {block_page_path}")
            return

        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()

            with open(block_page_path, 'rb') as f:
                self.wfile.write(f.read())
        except IOError as e:
            logger.error(f"Failed to read block page: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>500: Internal server error</h1>")

    def log_message(self, format, *args):
        logger.info(f"Block page: {format % args}")

if __name__ == '__main__':
    try:
        server_address = (Config.BLOCKPAGE_HOST, Config.BLOCKPAGE_PORT)
        httpd = HTTPServer(server_address, BlockPageHandler)

        ssl_context = None

        if Config.SSL_ENABLED:
            # Ensure certificates directory exists
            Path(Config.SSL_CERT_PATH).parent.mkdir(parents=True, exist_ok=True)

            # Generate self-signed certificate if needed
            if Config.SSL_AUTO_GENERATE and not SSLHelper.verify_certificate_exists(
                Config.SSL_CERT_PATH, Config.SSL_KEY_PATH
            ):
                logger.info("Auto-generating self-signed SSL certificate for block page...")
                SSLHelper.generate_self_signed_cert(
                    Config.SSL_CERT_PATH,
                    Config.SSL_KEY_PATH,
                    hostname=Config.SSL_HOSTNAME,
                )

            # Create SSL context
            ssl_context = SSLHelper.create_ssl_context(
                Config.SSL_CERT_PATH,
                Config.SSL_KEY_PATH,
            )

            if ssl_context:
                httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
                logger.info(f"Block page server running on HTTPS {Config.BLOCKPAGE_HOST}:{Config.BLOCKPAGE_PORT}...")
                print(f"Block page server running on HTTPS {Config.BLOCKPAGE_HOST}:{Config.BLOCKPAGE_PORT}...")
            else:
                logger.warning("Failed to create SSL context for block page, running without HTTPS")
                print(f"Block page server running on HTTP {Config.BLOCKPAGE_HOST}:{Config.BLOCKPAGE_PORT}...")
        else:
            print(f"Block page server running on HTTP {Config.BLOCKPAGE_HOST}:{Config.BLOCKPAGE_PORT}...")
            logger.info(f"Block page server started on HTTP {Config.BLOCKPAGE_HOST}:{Config.BLOCKPAGE_PORT}")

        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Block page server error: {e}")
        print(f"Error: {e}")
    finally:
        logger.info("Block page server stopped")
