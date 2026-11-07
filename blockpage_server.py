import signal
import logging
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from config import Config

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
        print(f"Block page server running on {Config.BLOCKPAGE_HOST}:{Config.BLOCKPAGE_PORT}...")
        logger.info(f"Block page server started on {Config.BLOCKPAGE_HOST}:{Config.BLOCKPAGE_PORT}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Block page server error: {e}")
        print(f"Error: {e}")
    finally:
        logger.info("Block page server stopped")
