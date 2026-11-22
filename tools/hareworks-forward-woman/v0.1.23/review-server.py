"""Read-only local Hareworks viewer, explicit owner-unapproved browser audits."""
import hashlib
import http.server
import json
import math
import os
import pathlib
import sys

root,ready,state=sys.argv[1:]
SOURCE='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
SCHEMA='hareworks-woman-accepted-v019-world-pin-v0.1.23'
class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,
        '.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
    def __init__(self,*a,**kw):super().__init__(*a,directory=root,**kw)
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
        self.send_header('Pragma','no-cache')
        super().end_headers()
    def do_POST(self):
        if self.path.split('?')[0].split('/')[-1]!='evidence':
            self.send_error(404);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 100<=size<=4000000:raise ValueError('invalid evidence size')
            raw=self.rfile.read(size);d=json.loads(raw)
            if d.get('schema')=='hareworks-v0.1.23-startup-diagnostic':
                if d.get('sourceSha256')!=SOURCE or d.get('ownerVisualAcceptance') is not False or d.get('physicalContactVerified') is not False:
                    raise ValueError('diagnostic cannot claim physical contact')
                if d.get('mode')!='PROCEDURAL_PREVIEW_UNPINNED':raise ValueError('wrong diagnostic mode')
                if not isinstance(d.get('error'),str) or len(d['error'])>1000:raise ValueError('invalid diagnostic error')
                out=pathlib.Path(state);out.mkdir(parents=True,exist_ok=True)
                path=out/'startup-diagnostic-v0.1.23.json';path.write_bytes(raw)
                receipt={'state':'UNPINNED_PROCEDURAL_PREVIEW_DIAGNOSTIC_SAVED','sha256':hashlib.sha256(raw).hexdigest(),
                         'path':str(path),'modelSha256':SOURCE,'ownerVisualAcceptance':False,'physicalContactVerified':False}
                b=json.dumps(receipt).encode();self.send_response(200);self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
            if size<450:raise ValueError('physical audit payload too small')
            if d.get('schema')!=SCHEMA or d.get('sourceSha256')!=SOURCE:raise ValueError('wrong artifact or source')
            if d.get('sourceClip')!='Walking_Woman' or d.get('rigBones')!=74:raise ValueError('wrong rig')
            if d.get('generatedAnimationMixerCount')!=0 or d.get('oneVisibleCharacter') is not True:
                raise ValueError('source clip playback forbidden on generated actor')
            if d.get('cameraOrbitEnabled') is not True or d.get('cameraFixedFollow') is not True:
                raise ValueError('camera orbit/follow regression')
            if d.get('rootMovementIsWorldTravel') is not True or d.get('stanceAnchorCoordinateSystem')!='WORLD':
                raise ValueError('not physical world locomotion')
            if d.get('physicsRateHz')!=120 or d.get('sampledFrames',0)<300:raise ValueError('incomplete real browser audit')
            if d.get('contactGate') not in ('PASS','WARN') or d.get('resemblanceGate')!='OWNER_VISUAL_REVIEW_PENDING':
                raise ValueError('contact and appearance verdicts conflated')
            if d.get('ownerVisualAcceptance') is not False:raise ValueError('owner verdict cannot be self-reported')
            if set(d.get('sourceContactMethod',{}))!={'left','right'}:raise ValueError('source leg windows absent')
            for side in ('left','right'):
                duty=d['sourceContactMethod'][side].get('duty')
                if not isinstance(duty,(int,float)) or not .45<=duty<=.73:raise ValueError('support window incorrect')
            for key in ('rootStridePerFullCycle','worldTravelZ','maximumContactAnchorTranslation',
                'maxFootPenetration','maxIKResidual','cameraWorldFollowError','sourceAnkleRms',
                'maxTrailingExtensionDeficit','maxAnchorHeight'):
                val=d.get(key)
                if not isinstance(val,(int,float)) or not math.isfinite(val):raise ValueError('nonfinite or missing '+key)
            if not .90<d['rootStridePerFullCycle']<1.55:raise ValueError('full-cycle distance regressed')
            out=pathlib.Path(state);out.mkdir(parents=True,exist_ok=True)
            path=out/'woman-accepted-v019-world-pinning-browser-v0.1.23.json';path.write_bytes(raw)
            receipt={'state':'BROWSER_MEASURED_CONTACT_AUDIT_SAVED_OWNER_GAIT_REVIEW_PENDING',
                'sha256':hashlib.sha256(raw).hexdigest(),'path':str(path),
                'modelSha256':SOURCE,'contactGate':d['contactGate'],
                'cameraOrbitEnabled':True,'ownerVisualAcceptance':False}
            (out/'browser-receipt-v0.1.23.json').write_text(json.dumps(receipt,indent=2)+'\n')
            b=json.dumps(receipt).encode();self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
        except Exception as e:self.send_error(422,'evidence rejected '+str(e)[:90])
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
pathlib.Path(ready).write_text(json.dumps({'pid':os.getpid(),'port':server.server_address[1],
    'root':root,'state':state,'sourceSha256':SOURCE,'ownerVisualAcceptance':False}))
server.serve_forever()
