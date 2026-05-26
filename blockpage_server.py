from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class BlockPageHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open('/home/pi/idps/blockpage/block.html', 'rb') as f:
            self.wfile.write(f.read())

    def log_message(self, format, *args):
        pass  # Suppress logs

print("Block page server running on port 5001...")
HTTPServer(('0.0.0.0', 5001), BlockPageHandler).serve_forever()
