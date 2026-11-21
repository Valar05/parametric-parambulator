import hashlib,http.server,json,os,pathlib,sys
root,ready,state=sys.argv[1:]
class Handler(http.server.SimpleHTTPRequestHandler):
 extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
 def __init__(self,*args,**kwargs): super().__init__(*args,directory=root,**kwargs)
 def end_headers(self):
  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
  self.send_header('Pragma','no-cache')
  super().end_headers()
 def do_POST(self):
  if not self.path.endswith('/evidence'):
   self.send_error(404);return
  try:
   n=int(self.headers.get('Content-Length','0'))
   if n<32 or n>3_000_000: raise ValueError('invalid evidence length')
   payload=self.rfile.read(n);data=json.loads(payload)
   if data.get('schema')!='hareworks-walk-left-inplace-parity-v0.2.7': raise ValueError('schema mismatch')
   if data.get('sourceSha256')!='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6':raise ValueError('model mismatch')
   if data.get('sourceClips')!=['Cautious_Crouch_Walk_Left','Cautious_Crouch_Walk_Left_inplace']:raise ValueError('wrong clip')
   if data.get('joints')!=74 or len(data.get('perJoint',[]))!=296: raise ValueError('joint evidence incomplete')
   sha=hashlib.sha256(payload).hexdigest();pathlib.Path(state).mkdir(parents=True,exist_ok=True)
   out=pathlib.Path(state)/'left-walk-browser-evidence.json';out.write_bytes(payload)
   receipt={'status':'REAL_BROWSER_EVIDENCE_SAVED_NOT_OWNER_APPROVED','sha256':sha,'path':str(out),'sourceModelSHA256':data['sourceSha256'],'ownerAccepted':False}
   (pathlib.Path(state)/'left-walk-browser-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
   answer=json.dumps(receipt).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(answer)));self.end_headers();self.wfile.write(answer)
  except Exception as e:self.send_error(422,'evidence rejected: '+str(e)[:80])
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
pathlib.Path(ready).write_text(json.dumps({'pid':os.getpid(),'port':server.server_address[1],'root':root,'state':state}))
server.serve_forever()
