"""Local-only exact build server and evidence sink. Does not publish model bytes."""
import hashlib
import http.server
import json
import os
import pathlib
import sys
root,ready,state=sys.argv[1:]
MODEL='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=root,**kwargs)
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
        self.send_header('Pragma','no-cache')
        super().end_headers()
    def do_POST(self):
        if not self.path.endswith('/evidence'):
            self.send_error(404);return
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<250 or n>2000000:raise ValueError('invalid evidence length')
            payload=self.rfile.read(n);data=json.loads(payload)
            if data.get('schema')!='hareworks-woman-world-pinned-ik-v0.1.11':raise ValueError('wrong schema')
            if data.get('sourceSha256')!=MODEL:raise ValueError('wrong original model')
            if data.get('sourceClip')!='Walking_Woman' or data.get('rigBones')!=74:raise ValueError('wrong source or rig')
            if data.get('generatedAnimationMixerCount')!=0 or data.get('oneVisibleCharacter') is not True:raise ValueError('requested execution lane absent')
            if data.get('cameraFixedFollow') is not True or data.get('stanceAnchorCoordinateSystem')!='WORLD':raise ValueError('camera or world lock absent')
            if data.get('physicsRateHz')!=120 or int(data.get('sampledFrames',0))<300:raise ValueError('incomplete physical audit')
            for field in ['worldTravelZ','maximumContactAnchorTranslation','maxFootPenetration','maxIKResidual','cameraWorldFollowError']:
                v=data.get(field)
                if not isinstance(v,(float,int)) or not (-1e8<v<1e8):raise ValueError('invalid '+field)
            if not (isinstance(data.get('strideCycle'),(int,float)) and .48<=data['strideCycle']<=.76 and isinstance(data.get('footClearance'),(int,float)) and .025<=data['footClearance']<=.12 and isinstance(data.get('actualCyclesTested'),(int,float)) and 2.99<=data['actualCyclesTested']<=3.03):raise ValueError('missing or invalid stride/clearance/cycles')
            if data.get('status') not in ['WORLD_IK_GATE_PASS_OWNER_REVIEW_PENDING','WORLD_IK_GATE_WARN_OWNER_REVIEW_REQUIRED']:raise ValueError('invalid audit status')
            out=pathlib.Path(state);out.mkdir(parents=True,exist_ok=True)
            path=out/'woman-world-ik-evidence.json';path.write_bytes(payload)
            receipt={'state':'REAL_BROWSER_SKINNED_WORLD_PIN_AUDIT_SAVED_NOT_OWNER_APPROVED','sha256':hashlib.sha256(payload).hexdigest(),'path':str(path),'sourceSHA256':MODEL,'ownerAccepted':False,'auditedPass':data['status']=='WORLD_IK_GATE_PASS_OWNER_REVIEW_PENDING'}
            (out/'woman-world-ik-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
            result=json.dumps(receipt).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(result)));self.end_headers();self.wfile.write(result)
        except Exception as e:self.send_error(422,'evidence rejected: '+str(e)[:80])
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
pathlib.Path(ready).write_text(json.dumps({'pid':os.getpid(),'port':server.server_address[1],'root':root,'state':state}))
server.serve_forever()
