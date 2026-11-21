"""Hareworks v0.1.12: no-store viewer with strict browser evidence readback."""
import hashlib
import http.server
import json
import os
import pathlib
import sys

root,ready,state=sys.argv[1:]
SOURCE_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
SCHEMA='hareworks-woman-source-measured-world-ik-v0.1.12'
class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,
        '.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=root,**kwargs)
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
        self.send_header('Pragma','no-cache')
        super().end_headers()
    def do_POST(self):
        if self.path.split('?')[0].split('/')[-1]!='evidence':
            self.send_error(404);return
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<350 or n>4000000:raise ValueError('invalid evidence size')
            raw=self.rfile.read(n);d=json.loads(raw)
            if d.get('schema')!=SCHEMA or d.get('sourceSha256')!=SOURCE_SHA:raise ValueError('wrong campaign source')
            if d.get('sourceClip')!='Walking_Woman' or d.get('rigBones')!=74:raise ValueError('wrong rig or clip')
            if d.get('generatedAnimationMixerCount')!=0 or d.get('oneVisibleCharacter') is not True:raise ValueError('runtime source animation forbidden')
            if d.get('cameraFixedFollow') is not True or d.get('stanceAnchorCoordinateSystem')!='WORLD':raise ValueError('contact/camera requirement')
            if d.get('physicsRateHz')!=120 or d.get('sampledFrames',0)<300:raise ValueError('incomplete measured audit')
            if d.get('contactGate') not in ('PASS','WARN') or d.get('resemblanceGate')!='OWNER_VISUAL_REVIEW_PENDING':raise ValueError('must keep style gate pending')
            if d.get('ownerVisualAcceptance') is not False:raise ValueError('owner acceptance cannot be self-reported')
            if not isinstance(d.get('sourceContactMethod'),dict) or set(d['sourceContactMethod'])!={'left','right'}:raise ValueError('missing source gait events')
            for s in ('left','right'):
                g=d['sourceContactMethod'][s]
                if not (isinstance(g.get('duty'),(int,float)) and .30<=g['duty']<=.79):raise ValueError('invalid gait events')
            for f in ('worldTravelZ','maximumContactAnchorTranslation','maxFootPenetration','maxIKResidual','cameraWorldFollowError','sourceAnkleRms'):
                val=d.get(f)
                if not isinstance(val,(int,float)) or not (-1e7<val<1e7):raise ValueError('invalid metric '+f)
            out=pathlib.Path(state);out.mkdir(parents=True,exist_ok=True)
            p=out/'woman-measured-source-browser-evidence-v0.1.12.json';p.write_bytes(raw)
            receipt={'status':'BROWSER_MEASURED_AUDIT_SAVED_NOT_OWNER_ACCEPTED',
                'sha256':hashlib.sha256(raw).hexdigest(),'path':str(p),
                'modelSha256':SOURCE_SHA,'contactGate':d['contactGate'],
                'resemblanceGate':'OWNER_VISUAL_REVIEW_PENDING'}
            (out/'browser-receipt-v0.1.12.json').write_text(json.dumps(receipt,indent=2)+'\n')
            raw_out=json.dumps(receipt).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(raw_out)));self.end_headers();self.wfile.write(raw_out)
        except Exception as exc:
            self.send_error(422,'evidence rejected: '+str(exc)[:100])
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
pathlib.Path(ready).write_text(json.dumps({'pid':os.getpid(),'port':server.server_address[1],
 'root':root,'state':state,'sourceSha256':SOURCE_SHA}))
server.serve_forever()
