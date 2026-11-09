"""No-cache version-specific localhost viewer server."""
import argparse,hashlib,json,os,pathlib,urllib.parse,time
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--ready',required=True);p.add_argument('--port',type=int,default=9380);a=p.parse_args()
spec=json.loads(pathlib.Path(a.config).read_text());root=pathlib.Path(spec['root']);src={'/index.html':root/'viewer.html','/model.glb':root/'model.glb','/manifest.json':root/'manifest.json'}
for path in src.values():
 if not path.is_file():raise SystemExit('MISSING_VIEWER_RESOURCE_'+str(path))
class Handler(BaseHTTPRequestHandler):
 def do_HEAD(self):self.send_content(False)
 def do_GET(self):self.send_content(True)
 def send_content(self,body):
  url=urllib.parse.urlsplit(self.path).path
  if url=='/':url='/index.html'
  if url=='/health':
   raw=json.dumps({'status':'SERVING','run':spec['run'],'sha256':spec['modelSHA256'],'pid':os.getpid()}).encode();mime='application/json'
  elif url in src:
   if url=='/model.glb':
    if hashlib.sha256(src[url].read_bytes()).hexdigest()!=spec['modelSHA256']:
     self.send_error(409,'MODEL_HASH_CHANGED');return
   raw=src[url].read_bytes();mime={'/index.html':'text/html; charset=utf-8','/model.glb':'model/gltf-binary','/manifest.json':'application/json'}[url]
  else:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)))
  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
  self.send_header('Pragma','no-cache');self.send_header('X-Content-Type-Options','nosniff')
  self.send_header('X-Obsidianti-Run',spec['run']);self.send_header('X-Model-SHA256',spec['modelSHA256']);self.end_headers()
  if body:
   try:self.wfile.write(raw)
   except (BrokenPipeError,ConnectionResetError):pass
 def log_message(self,fmt,*args):pass
server=None
for port in range(a.port,a.port+60):
 try:server=ThreadingHTTPServer(('127.0.0.1',port),Handler);break
 except OSError:continue
if server is None:raise SystemExit('NO_AVAILABLE_LOCAL_PORT')
url='http://127.0.0.1:'+str(server.server_address[1])+'/index.html?run='+urllib.parse.quote(spec['run'])
ready={'url':url,'pid':os.getpid(),'port':server.server_address[1],'modelSHA256':spec['modelSHA256'],'run':spec['run']}
target=pathlib.Path(a.ready);target.write_text(json.dumps(ready,indent=2)+'\n');print('VIEWER_URL='+url,flush=True)
server.serve_forever()
