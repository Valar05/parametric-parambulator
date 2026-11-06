import http.server,sys,pathlib
root=pathlib.Path(sys.argv[1]).resolve();port=int(sys.argv[2]);run=sys.argv[3]
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*args,**kw):super().__init__(*args,directory=str(root),**kw)
 def end_headers(self):
  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
  self.send_header('Pragma','no-cache')
  self.send_header('X-Obsidianti-Run',run)
  super().end_headers()
 def log_message(self,fmt,*args):print('%s '+fmt%args,flush=True)
with http.server.ThreadingHTTPServer(('127.0.0.1',port),Handler) as server:server.serve_forever()
