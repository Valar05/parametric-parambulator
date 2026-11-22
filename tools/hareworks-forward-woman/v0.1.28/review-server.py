"""Version-pinned local left-walk viewer. Evidence is not owner approval."""
import hashlib, http.server, json, math, os, pathlib, sys
root, ready, state = sys.argv[1:]
SOURCE = 'a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
CLIPS = ['Cautious_Crouch_Walk_Left', 'Cautious_Crouch_Walk_Left_inplace']
SCHEMA = 'hareworks-v0.1.26-real-left-source-procedural-audit'
class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,
      '.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
    def __init__(self,*a,**kw): super().__init__(*a,directory=root,**kw)
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
        self.send_header('Pragma','no-cache')
        super().end_headers()
    def do_POST(self):
        if self.path.split('?')[0].split('/')[-1]!='evidence': self.send_error(404);return
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<300 or n>1000000:raise ValueError('evidence size')
            raw=self.rfile.read(n);d=json.loads(raw)
            if d.get('schema')!=SCHEMA or d.get('sourceSha256')!=SOURCE:raise ValueError('source/schema mismatch')
            if d.get('sourceClips')!=CLIPS or d.get('rigBones')!=74 or d.get('sourceFramesPerClip')!=720:raise ValueError('source clips/rig mismatch')
            if d.get('ownerAccepted') is not False:raise ValueError('false owner-approval state')
            if d.get('actualFrames',0)<250 or d.get('physicsHz')!=120:raise ValueError('incomplete actual browser sample')
            if d.get('contactGate') not in ('ANKLE_PIN_WARN','ANKLE_PIN_PASS__NOT_SKINNED_SOLE_CERTIFICATION'):raise ValueError('unsupported contact gate')
            for x in ('worldTravelX','travelPerCycle','worldAnkleAnchorMaxDrift','sourceJointMaxQuaternionDeg'):
                if not isinstance(d.get(x),(int,float)) or not math.isfinite(d[x]):raise ValueError('bad numeric '+x)
            if d['worldTravelX']<=2 or d['travelPerCycle']<=1:raise ValueError('wrong left root travel')
            path=pathlib.Path(state);path.mkdir(parents=True,exist_ok=True)
            artifact=path/'left-procedural-browser-evidence-v0.1.26.json';artifact.write_bytes(raw)
            result={'status':'REAL_BROWSER_EVIDENCE_SAVED_OWNER_REVIEW_PENDING','sha256':hashlib.sha256(raw).hexdigest(),
                 'sourceSha256':SOURCE,'path':str(artifact),'contactGate':d['contactGate'],'ownerAccepted':False}
            (path/'left-procedural-browser-receipt-v0.1.26.json').write_text(json.dumps(result,indent=2)+'\n')
            b=json.dumps(result).encode();self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
        except Exception as e:self.send_error(422,'evidence rejected '+str(e)[:100])
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
pathlib.Path(ready).write_text(json.dumps({'pid':os.getpid(),'port':server.server_address[1], 'root':root,'state':state,'sourceSha256':SOURCE,'ownerAccepted':False}))
server.serve_forever()
