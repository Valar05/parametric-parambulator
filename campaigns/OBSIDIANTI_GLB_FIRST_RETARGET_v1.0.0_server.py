import http.server,pathlib,json,hashlib,sys
root=pathlib.Path(sys.argv[1]);port=int(sys.argv[2]);token=sys.argv[3]
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(root),**kwargs)
 def end_headers(self):
  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate');self.send_header('Pragma','no-cache');super().end_headers()
 def do_GET(self):
  if self.path.split('?')[0]=='/__identity':
   d=json.loads((root/'manifest.json').read_text());actual=hashlib.sha256((root/'candidate.glb').read_bytes()).hexdigest();ok=actual==d['modelSHA256'] and d['sessionToken']==token
   blob=json.dumps({'ready':ok,'campaign':d['campaign'],'sourceHead':d['sourceHead'],'modelSHA256':actual,'launcherSHA256':d['launcherSHA256'],'sessionToken':token}).encode()
   self.send_response(200 if ok else 500);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(blob)));self.end_headers();self.wfile.write(blob);return
  return super().do_GET()
 def log_message(self,*args):pass
http.server.ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
