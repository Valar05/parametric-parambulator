"""SHA-checking localhost-only viewer. No cache, no external binding."""
import argparse,hashlib,json,pathlib,urllib.parse,os
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--ready',required=True);p.add_argument('--port',type=int,default=9440);a=p.parse_args()
cfg=json.loads(pathlib.Path(a.config).read_text());root=pathlib.Path(cfg['root']);files={'/index.html':root/'viewer.html','/model.glb':root/'model.glb','/manifest.json':root/'manifest.json'}
for file in files.values():
 if not file.is_file():raise RuntimeError('VIEWER_MISSING_'+str(file))
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):self.send_data(True)
 def do_HEAD(self):self.send_data(False)
 def send_data(self,body):
  key=urllib.parse.urlsplit(self.path).path
  if key=='/':key='/index.html'
  if key=='/health':raw=json.dumps({'run':cfg['run'],'sha256':cfg['modelSHA256'],'status':'SERVING'}).encode();mime='application/json'
  elif key in files:
   raw=files[key].read_bytes()
   if key=='/model.glb' and hashlib.sha256(raw).hexdigest()!=cfg['modelSHA256']:
    self.send_error(409,'MODEL_SHA_MISMATCH');return
   mime={'/index.html':'text/html; charset=utf-8','/model.glb':'model/gltf-binary','/manifest.json':'application/json'}[key]
  else:self.send_error(404);return
  self.send_response(200)
  for k,v in {'Content-Type':mime,'Content-Length':str(len(raw)),'Cache-Control':'no-store, max-age=0','X-Model-SHA256':cfg['modelSHA256']}.items():self.send_header(k,v)
  self.end_headers()
  if body:
   try:self.wfile.write(raw)
   except (BrokenPipeError,ConnectionResetError):pass
 def log_message(self,*args):pass
srv=None
for port in range(a.port,a.port+50):
 try:srv=ThreadingHTTPServer(('127.0.0.1',port),Handler);break
 except OSError:pass
if srv is None:raise RuntimeError('NO_OPEN_LOCAL_VIEWER_PORT')
url=f'http://127.0.0.1:{srv.server_address[1]}/index.html?run='+urllib.parse.quote(cfg['run'])
pathlib.Path(a.ready).write_text(json.dumps({'url':url,'port':srv.server_address[1],'sha256':cfg['modelSHA256']})+'\n')
print('VIEWER_URL='+url,flush=True)
srv.serve_forever()
