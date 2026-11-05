#!/usr/bin/env python3
"""Persistent, provenance-checked localhost server for the owner's Termux campaign."""
import http.server,json,sys,os,zipfile
from pathlib import Path
out=Path(sys.argv[1]).resolve();port=int(sys.argv[2]);token=sys.argv[3];run_id=sys.argv[4]
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(out),**kw)
 def end_headers(self):
  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
  self.send_header('Pragma','no-cache');self.send_header('Expires','0')
  self.send_header('X-Repl-Build',token);self.send_header('X-Repl-Run',run_id)
  super().end_headers()
 def do_POST(self):
  if not self.path.startswith('/telemetry?'):
   self.send_error(404);return
  from urllib.parse import parse_qs,urlsplit
  q=parse_qs(urlsplit(self.path).query)
  if q.get('build')!=[token] or q.get('run')!=[run_id]:self.send_error(403);return
  n=int(self.headers.get('Content-Length','0'))
  if n<=0 or n>4096:self.send_error(400);return
  data=self.rfile.read(n)
  try:
   item=json.loads(data)
   with (out/'runtime_log.jsonl').open('a') as f:f.write(json.dumps({'run':run_id,'client':item})+'\n')
   with zipfile.ZipFile(out/'diagnostics.zip','w',compression=zipfile.ZIP_DEFLATED) as bundle:
    for name in ('receipt.json','runtime_log.jsonl','http_log.txt','server_process.log'):
     p=out/name
     if p.is_file():bundle.write(p,arcname=name)
   self.send_response(204);self.end_headers()
  except Exception:self.send_error(400)
 def log_message(self,fmt,*args):
  try:
   with (out/'http_log.txt').open('a') as f:f.write((fmt%args)+'\n')
  except Exception:pass
http.server.ThreadingHTTPServer.allow_reuse_address=False
http.server.ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
