#!/usr/bin/env python3
"""Strict localhost-only, no-cache, SHA-tagged real-GLB viewer server."""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,socket,sys,time,urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class StrictServer(ThreadingHTTPServer):
    allow_reuse_address=False
    daemon_threads=True

class ViewerHandler(BaseHTTPRequestHandler):
    server_version='ObsidiantiMwniViewer/1.4.8'
    def log_message(self,fmt,*args):
        sys.stdout.write(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+' '+fmt%args+'\n');sys.stdout.flush()
    def do_HEAD(self):self.serve(False)
    def do_GET(self):self.serve(True)
    def serve(self,with_body):
        spec=self.server.spec
        route=urllib.parse.urlsplit(self.path).path
        headers={'X-Obsidianti-Run':spec['runId'],'X-Obsidianti-Build':spec['buildToken'],'X-Obsidianti-Source-Commit':spec['sourceCommit']}
        if route in ('/','/index.html'):
            body=pathlib.Path(spec['htmlPath']).read_bytes()
            mimetype='text/html; charset=utf-8'
        elif route=='/manifest.json':
            safe={k:v for k,v in spec.items() if k not in ('htmlPath',) and k!='modelPaths'}
            body=(json.dumps(safe,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8')
            mimetype='application/json; charset=utf-8'
        elif route=='/health':
            body=(json.dumps({'status':'SERVING','runId':spec['runId'],'buildToken':spec['buildToken'],'pid':os.getpid(),'sourceCommit':spec['sourceCommit'],'models':{k:v['sha256'] for k,v in spec['models'].items()}},sort_keys=True)+'\n').encode()
            mimetype='application/json; charset=utf-8'
        elif route.startswith('/models/') and route.endswith('.glb'):
            key=route[len('/models/'):-len('.glb')]
            if key not in spec['models']:
                self.send_error(404,'Unknown model');return
            meta=spec['models'][key]
            file=pathlib.Path(spec['modelPaths'][key])
            if not file.is_file() or file.stat().st_size!=meta['bytes']:
                self.send_error(409,'Model file missing or changed size');return
            headers['X-Model-SHA256']=meta['sha256']
            length=meta['bytes'];mimetype='model/gltf-binary'
            self.send_response(200)
            self.send_header('Content-Type',mimetype)
            self.send_header('Content-Length',str(length))
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
            self.send_header('Pragma','no-cache')
            for k,v in headers.items():self.send_header(k,v)
            self.end_headers()
            if with_body:
                try:
                    with open(file,'rb') as stream:
                        while True:
                            buf=stream.read(1024*1024)
                            if not buf:break
                            self.wfile.write(buf)
                except (BrokenPipeError,ConnectionResetError):pass
            return
        else:
            self.send_error(404,'Unknown route');return
        self.send_response(200)
        self.send_header('Content-Type',mimetype)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
        self.send_header('Pragma','no-cache')
        for k,v in headers.items():self.send_header(k,v)
        self.end_headers()
        if with_body:
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--ready',required=True);ap.add_argument('--host',default='127.0.0.1');ap.add_argument('--port-base',type=int,default=9180);a=ap.parse_args()
    if a.host!='127.0.0.1':raise SystemExit('ONLY_LOOPBACK_BIND_PERMITTED')
    spec=json.loads(pathlib.Path(a.config).read_text())
    for field in ('buildToken','runId','sourceCommit','htmlPath','modelPaths','models','launcherSHA256'):
        if not spec.get(field):raise SystemExit('INVALID_VIEWER_CONFIG_MISSING_'+field)
    for key,meta in spec['models'].items():
        if key not in spec['modelPaths']:raise SystemExit('MODEL_PATH_MISSING_'+key)
        f=pathlib.Path(spec['modelPaths'][key]);
        if not f.is_file() or f.stat().st_size!=meta['bytes']:raise SystemExit('MODEL_SIZE_OR_FILE_MISSING_'+key)
    server=None
    for port in range(a.port_base,a.port_base+35):
        try:
            server=StrictServer((a.host,port),ViewerHandler)
            break
        except OSError:continue
    if server is None:raise SystemExit('NO_AVAILABLE_UNIQUE_LOOPBACK_PORT')
    server.spec=spec
    url=f'http://127.0.0.1:{server.server_address[1]}/index.html?run='+urllib.parse.quote(spec['runId'])+'&build='+urllib.parse.quote(spec['buildToken'])
    ready={'pid':os.getpid(),'port':server.server_address[1],'url':url,'buildToken':spec['buildToken'],'runId':spec['runId'],'sourceCommit':spec['sourceCommit']}
    rp=pathlib.Path(a.ready);tmp=rp.with_name('.'+rp.name+'.tmp-'+str(os.getpid()))
    tmp.write_text(json.dumps(ready,indent=2)+'\n');os.replace(tmp,rp)
    print('VIEWER_URL='+url,flush=True)
    try:server.serve_forever(poll_interval=.3)
    finally:server.server_close()

if __name__=='__main__':main()
