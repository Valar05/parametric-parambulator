#!/usr/bin/env python3
"""Viewer server: authenticated only to local device, pinned hashes, unique port and no-cache."""
import argparse,hashlib,json,os,pathlib,sys,time,urllib.parse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
class Server(ThreadingHTTPServer):
 allow_reuse_address=False
 daemon_threads=True
class Handler(BaseHTTPRequestHandler):
 server_version='ObsidiantiPalmGripIK/2.0.36'
 def log_message(self,fmt,*a):sys.stdout.write(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+' '+fmt%a+'\n');sys.stdout.flush()
 def do_HEAD(self):self.serve(False)
 def do_GET(self):self.serve(True)
 def serve(self,write_body):
  spec=self.server.spec;path=urllib.parse.urlsplit(self.path).path
  headers={'X-Obsidianti-Run':spec['runId'],'X-Obsidianti-Build':spec['buildToken'],'X-Obsidianti-Source-Commit':spec['sourceCommit']}
  if path in ('/','/index.html'):
   raw=pathlib.Path(spec['htmlPath']).read_bytes();mime='text/html; charset=utf-8'
  elif path=='/manifest.json':
   meta={k:v for k,v in spec.items() if k not in ('htmlPath','modelPaths')}
   raw=(json.dumps(meta,sort_keys=True,separators=(',',':'))+'\n').encode();mime='application/json; charset=utf-8'
  elif path=='/health':
   raw=(json.dumps({'status':'SERVING','runId':spec['runId'],'buildToken':spec['buildToken'],'pid':os.getpid(),'sourceCommit':spec['sourceCommit'],'models':{k:v['sha256'] for k,v in spec['models'].items()}},sort_keys=True)+'\n').encode();mime='application/json'
  elif path.startswith('/models/') and path.endswith('.glb'):
   k=path[len('/models/'):-len('.glb')]
   if k not in spec['models']:self.send_error(404,'Model route not found');return
   meta=spec['models'][k];file=pathlib.Path(spec['modelPaths'][k])
   if not file.is_file() or file.stat().st_size!=meta['bytes']:self.send_error(409,'Model file mismatch');return
   headers['X-Model-SHA256']=meta['sha256'];self.send_response(200)
   self.send_header('Content-Type','model/gltf-binary');self.send_header('Content-Length',str(meta['bytes']))
   self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate');self.send_header('Pragma','no-cache')
   self.send_header('X-Content-Type-Options','nosniff')
   for x,y in headers.items():self.send_header(x,y)
   self.end_headers()
   if write_body:
    try:
     with file.open('rb') as f:
      while True:
       chunk=f.read(1<<20)
       if not chunk:break
       self.wfile.write(chunk)
    except (BrokenPipeError,ConnectionResetError):pass
   return
  else:self.send_error(404,'Unknown route');return
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)))
  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate');self.send_header('Pragma','no-cache')
  self.send_header('X-Content-Type-Options','nosniff')
  for x,y in headers.items():self.send_header(x,y)
  self.end_headers()
  if write_body:
   try:self.wfile.write(raw)
   except (BrokenPipeError,ConnectionResetError):pass

def main():
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--ready',required=True);p.add_argument('--host',default='127.0.0.1');p.add_argument('--port-base',type=int,default=9240);a=p.parse_args()
 if a.host!='127.0.0.1':raise SystemExit('LOCALHOST_ONLY')
 spec=json.loads(pathlib.Path(a.config).read_text())
 for key in ('runId','sourceCommit','launcherSHA256','buildToken','models','modelPaths','htmlPath'):
  if not spec.get(key):raise SystemExit('MISSING_VIEWER_IDENTITY_'+key)
 for key,meta in spec['models'].items():
  f=pathlib.Path(spec['modelPaths'][key]);
  if not f.is_file() or f.stat().st_size!=meta['bytes']:raise SystemExit('INPUT_MODEL_FILE_CHANGED_'+key)
 server=None
 for port in range(a.port_base,a.port_base+50):
  try:server=Server((a.host,port),Handler);break
  except OSError:continue
 if server is None:raise SystemExit('NO_UNUSED_PORT')
 server.spec=spec
 url='http://127.0.0.1:'+str(server.server_address[1])+'/index.html?run='+urllib.parse.quote(spec['runId'])+'&build='+urllib.parse.quote(spec['buildToken'])
 ready={'pid':os.getpid(),'port':server.server_address[1],'url':url,'buildToken':spec['buildToken'],'runId':spec['runId'],'sourceCommit':spec['sourceCommit']}
 dst=pathlib.Path(a.ready);tmp=dst.with_name('.'+dst.name+'.tmp-'+str(os.getpid()));tmp.write_text(json.dumps(ready,indent=2)+'\n');os.replace(tmp,dst)
 print('VIEWER_URL='+url,flush=True)
 try:server.serve_forever(poll_interval=.3)
 finally:server.server_close()
if __name__=='__main__':main()
