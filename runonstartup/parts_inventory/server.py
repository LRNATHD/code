import http.server
import socketserver
import json
import os

PORT = 8000
DB_FILE = 'db.json'

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/inventory':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            if os.path.exists(DB_FILE):
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    try:
                        data = f.read()
                        if not data: data = "[]"
                    except:
                        data = "[]"
                self.wfile.write(data.encode('utf-8'))
            else:
                self.wfile.write(b'[]')
        else:
            return super().do_GET()

    def do_POST(self):
        if self.path == '/api/inventory':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Validate JSON (ensure it's not garbage)
                json_data = json.loads(post_data.decode('utf-8'))
                
                with open(DB_FILE, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
        else:
            self.send_error(404)

print(f"Starting PartScout Server on port {PORT}...")
print(f"Data will be saved to: {os.path.abspath(DB_FILE)}")

with socketserver.TCPServer(("0.0.0.0", PORT), RequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
