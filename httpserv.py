from http.server import HTTPServer, BaseHTTPRequestHandler

f = open('./client.html','r')
content = f.read()
f.close()

class myHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())

httpd = HTTPServer(('', 8888), myHandler)
httpd.serve_forever()