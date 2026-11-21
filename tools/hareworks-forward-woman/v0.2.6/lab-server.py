"""Termux-local, no-cache lab UI and validated durable evidence receiver."""
import csv
import datetime
import hashlib
import http.server
import io
import json
import math
import os
import pathlib
import sys
import tempfile
import urllib.parse

MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
REPORT_URL='/tools/hareworks-forward-woman/v0.2.6/style-report'
LAYERS=['pelvis','legs','torso','arms']

def validate_report(a):
    assert isinstance(a,dict)
    assert a.get('schema')=='hareworks-gated-backward-style-lab-v0.2.6'
    assert a.get('sourceSha256')==MODEL_SHA
    assert a.get('sourceClips')==['Walk_Backward','Walking','Walking_Woman']
    assert a.get('sourceBones')==74
    assert a.get('sourceModelUnchanged') is True and a.get('originalGaitsUnchanged') is True
    assert a.get('styleAcceptedByOwner') is False
    assert a.get('approvedBackwardMotionPlaybackTracks')==0
    assert a.get('generatedSourceAnimationTracks')==0
    assert a.get('zeroFrame',{}).get('pass') is True
    assert a.get('zeroFrame',{}).get('joints')==74
    for key in ['requested','applied']:
        o=a[key]
        assert set(o)==set(LAYERS)
        assert all(isinstance(o[k],(int,float)) and math.isfinite(o[k]) and 0<=o[k]<=1 for k in LAYERS)
    audited=a.get('fullRateAudit',{})
    assert audited.get('pass') is True
    assert [o['rateHz'] for o in audited['perRate']]==[30,60,120]
    assert audited.get('sampleCount',0)>150
    assert not audited.get('rejections')
    assert 0<=len(a.get('trials',[]))<=8
    return a

def atomic(path,data):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.tmp-hareworks-024-',delete=False) as f:
        tmp=pathlib.Path(f.name);f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def store_report(raw,state):
    if len(raw)>1_500_000: raise ValueError('OVERSIZE_STYLE_REPORT')
    a=validate_report(json.loads(raw))
    payload=(json.dumps(a,indent=2,allow_nan=False)+'\n').encode()
    rows=io.StringIO();csvw=csv.writer(rows);csvw.writerow(['layer','requested','applied','status'])
    for x in a['trials']:
        if x.get('layer'):csvw.writerow([x['layer'],x.get('requested'),x.get('applied'),x.get('status')])
    state=pathlib.Path(state)
    atomic(state/'style-lab-report.json',payload)
    atomic(state/'style-lab-trials.csv',rows.getvalue().encode())
    digest=hashlib.sha256(payload).hexdigest()
    receipt={'campaign':'hareworks-backward-style-lab-v0.2.6','status':'REAL_BROWSER_GATED_TRIAL_SAVED',
      'modelSha256':MODEL_SHA,'sourceClips':a['sourceClips'],'reportSha256':digest,
      'jsonPath':str(state/'style-lab-report.json'),'csvPath':str(state/'style-lab-trials.csv'),
      'acceptedBackwardUnchanged':True,'acceptedForwardUnchanged':True,'ownerAcceptedStyle':False,
      'receivedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    atomic(state/'style-lab-receipt.json',(json.dumps(receipt,indent=2)+'\n').encode())
    return {'saved':True,'sha256':digest,'path':receipt['jsonPath']}

def make_handler(root,state,ready):
    class Handler(http.server.SimpleHTTPRequestHandler):
        extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
        def __init__(self,*args,**kw):super().__init__(*args,directory=root,**kw)
        def end_headers(self):
            self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
            self.send_header('Pragma','no-cache')
            self.send_header('X-Content-Type-Options','nosniff')
            super().end_headers()
        def do_POST(self):
            if urllib.parse.urlsplit(self.path).path!=REPORT_URL:
                self.send_error(404,'Unknown lab report endpoint');return
            origin=self.headers.get('Origin','')
            expected='http://127.0.0.1:'+str(self.server.server_address[1])
            if origin and origin!=expected:
                self.send_error(403,'Invalid report origin');return
            try:
                n=int(self.headers.get('Content-Length','0'))
                if n<=0 or n>1_500_000:
                    self.send_error(413,'Bad report size');return
                result=store_report(self.rfile.read(n),state)
                payload=json.dumps(result).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
            except (ValueError,TypeError,KeyError,AssertionError) as err:
                self.send_error(422,'Rejected lab evidence: '+str(err)[:120])
    return Handler

def main():
    root,state,ready=sys.argv[1:]
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),make_handler(root,state,ready))
    atomic(ready,json.dumps({'pid':os.getpid(),'port':server.server_address[1],'root':root}).encode())
    server.serve_forever()

if __name__=='__main__':main()
