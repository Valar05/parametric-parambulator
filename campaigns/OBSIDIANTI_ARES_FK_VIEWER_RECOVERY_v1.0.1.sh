#!/data/data/com.termux/files/usr/bin/bash
# Repo-owned after first authorized Termux Git run; recovery-only, no model mutation.
set -Eeuo pipefail
[[ -n "${PREFIX:-}" && -x "$PREFIX/bin/bash" ]] || { echo BLOCKED_TERMUX_REQUIRED; exit 2; }
for p in python3 git sha256sum; do command -v "$p" >/dev/null || { echo "BLOCKED_MISSING=$p"; exit 2; }; done
SELF="$(readlink -f "${BASH_SOURCE[0]}")"
SELF_SHA="$(sha256sum "$SELF" | cut -d' ' -f1)"
echo "CAMPAIGN=OBSIDIANTI_ARES_FK_VIEWER_RECOVERY_v1.0.1"
echo "AUTHORITY=TERMUX_GIT_ONLY"
echo "LAUNCHER_SHA256=$SELF_SHA"
echo "SOURCE=$SELF"
python3 -B - "$SELF" "$SELF_SHA" <<'PY'
from __future__ import annotations
import datetime, hashlib, http.server, json, os, pathlib, shutil, socket, subprocess, sys, tempfile, time, traceback, urllib.request, zipfile

VERSION='OBSIDIANTI_ARES_FK_VIEWER_RECOVERY_v1.0.1'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
REPO_FILE='campaigns/OBSIDIANTI_ARES_FK_VIEWER_RECOVERY_v1.0.1.sh'
ARCHIVE='diagnostics/obsidianti/ares-fk-rebase-v1.0.1/UNAPPROVED_CANDIDATE.zip'
ARCHIVE_SHA='4a039eb3d73ae1d3430c7eb9c90c55aba5d4c00fda7a86e6704c8eaab2c45b10'
MODEL_SHA='955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32'
AGENTS_SHA='547c2af52303f4efb718bbf8f82a698110c7bfca'
EXPECTED_RESULT='diagnostics/obsidianti/ares-fk-rebase-v1.0.1/RESULT.json'
MODEL_MEMBER='AresScaled_PreContactFK_UNAPPROVED.glb'
MODEL_NAME='Obsidianti_Ares_FK_v1.0.1_UNAPPROVED.glb'
HTML_NAME='index.html'
PORTS=range(8179,8190)

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def cmd(args,timeout=600,check=True,env=None):
    r=subprocess.run([str(a) for a in args],capture_output=True,text=True,timeout=timeout,env=env)
    if check and r.returncode: raise RuntimeError('CMD_FAIL '+repr(args[:5])+'\n'+r.stderr[-900:]+'\n'+r.stdout[-500:])
    return r

def atomic_copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.is_file() and sha(dst)==sha(src):return 'ALREADY_VERIFIED'
    temp=dst.with_name('.'+dst.name+'.'+str(os.getpid())+'.tmp')
    try:
        with open(src,'rb') as r,open(temp,'xb') as w:
            shutil.copyfileobj(r,w,1024*1024)
            w.flush();os.fsync(w.fileno())
        if sha(temp)!=sha(src):raise RuntimeError('ATOMIC_COPY_SHA_MISMATCH '+str(dst))
        os.replace(temp,dst)
    finally:
        if temp.exists():temp.unlink()
    return 'COPIED_VERIFIED'

VIEWER=r'''<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><title>Obsidianti Ares FK v1.0.1 | UNAPPROVED</title>
<style>:root{color-scheme:dark}*{box-sizing:border-box}html,body{height:100%;margin:0;font:15px system-ui;color:#edf1f7;background:#121722}body{display:flex;flex-direction:column}header,footer{padding:10px 12px;background:#202b3c}header strong{display:block}small,#status{color:#b8c9e0}main{position:relative;min-height:180px;flex:1}canvas{width:100%;height:100%;display:block}footer{display:flex;align-items:center;flex-wrap:wrap;gap:8px}select,button{font:inherit;padding:7px;border-radius:7px;background:#33445d;color:white;border:1px solid #8b9fb9}button:focus-visible,select:focus-visible{outline:2px solid #fdd76c}.identity{font-size:11px;overflow-wrap:anywhere}</style>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.181.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.181.0/examples/jsm/"}}</script></head><body>
<header><strong>Obsidianti • Ares-scaled historical FK <span style="color:#f7ca7e">UNAPPROVED REVIEW</span></strong><div class="identity">Model SHA-256: 955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32</div><div id="status" role="status" aria-live="polite">Verifying exact candidate bytes…</div></header><main id="stage"></main><footer><label for="clips">Clip</label><select id="clips" aria-label="Animation clip"></select><button id="play">Pause</button><button id="again">Replay</button><label for="speed">Speed</label><select id="speed"><option value=".5">½×</option><option value="1" selected>1×</option><option value="1.5">1½×</option><option value="2">2×</option></select><small>Drag to orbit • Pinch to zoom • Review candidate, not canonical model</small></footer>
<script type="module">
import * as THREE from 'three';import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const expected='955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32',status=document.getElementById('status'),stage=document.getElementById('stage');
const scene=new THREE.Scene();scene.background=new THREE.Color(0x151922);scene.add(new THREE.HemisphereLight(0xffffff,0x68768c,2.2));const light=new THREE.DirectionalLight(0xffffff,2.2);light.position.set(3,6,4);scene.add(light);scene.add(new THREE.GridHelper(7,24,0x57637b,0x374358));
const camera=new THREE.PerspectiveCamera(38,1,.02,200);camera.position.set(2,2,4);const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;stage.appendChild(renderer.domElement);const orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.target.set(0,1,0);const choice=document.getElementById('clips');let mixer=null,clipActions=new Map(),current=null,paused=false,last=performance.now();
new ResizeObserver(()=>{const w=Math.max(stage.clientWidth,1),h=Math.max(stage.clientHeight,1);camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h)}).observe(stage);
function select(name){if(!mixer)return;for(const a of clipActions.values())a.stop();current=clipActions.get(name);if(!current)return;current.reset().setEffectiveWeight(1).play();paused=false;current.paused=false;document.getElementById('play').textContent='Pause';choice.value=name}
choice.addEventListener('change',()=>select(choice.value));document.getElementById('play').onclick=()=>{paused=!paused;if(current)current.paused=paused;document.getElementById('play').textContent=paused?'Play':'Pause'};document.getElementById('again').onclick=()=>select(choice.value);document.getElementById('speed').onchange=e=>{if(mixer)mixer.timeScale=Number(e.target.value)};
async function load(){
 const response=await fetch('./candidate.glb',{cache:'no-store'});if(!response.ok)throw Error('Candidate GET HTTP '+response.status);
 const bytes=await response.arrayBuffer();const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');
 if(digest!==expected)throw Error('CANDIDATE_SHA_MISMATCH: '+digest);
 status.textContent='Verified exact candidate SHA-256; loading real skinned model…';
 const gltf=await new Promise((resolve,reject)=>new GLTFLoader().parse(bytes,'',resolve,reject));scene.add(gltf.scene);mixer=new THREE.AnimationMixer(gltf.scene);
 for(const c of gltf.animations){clipActions.set(c.name,mixer.clipAction(c));const o=document.createElement('option');o.value=c.name;o.textContent=c.name;choice.appendChild(o)}
 const bounds=new THREE.Box3().setFromObject(gltf.scene),size=bounds.getSize(new THREE.Vector3()),center=bounds.getCenter(new THREE.Vector3());orbit.target.copy(center);camera.position.set(center.x+size.y*1.5,center.y+size.y*.7,center.z+size.y*2.0);camera.lookAt(center);orbit.update();
 const preferred=['Lionheart_Heavy1','Lionheart_Heavy2','Lionheart_Light3'];select(preferred.find(x=>clipActions.has(x))||gltf.animations[0]?.name);
 status.textContent='VERIFIED ARES FK CANDIDATE | '+gltf.animations.length+' clips | owner visual review pending';
}
load().catch(e=>{status.textContent='VIEWER ERROR: '+String(e);console.error(e)});
function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-last)/1000,.08);last=now;if(mixer)mixer.update(dt);orbit.update();renderer.render(scene,camera)}requestAnimationFrame(animate);
</script></body></html>'''

SERVER=r'''#!/usr/bin/env python3
import hashlib,http.server,json,pathlib,sys
root=pathlib.Path(sys.argv[1]).resolve();port=int(sys.argv[2]);expected=sys.argv[3]
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*args,**kw):super().__init__(*args,directory=str(root),**kw)
 def do_GET(self):
  if self.path.split('?')[0]=='/__identity':
   actual=hashlib.sha256((root/'candidate.glb').read_bytes()).hexdigest()
   payload=json.dumps({'campaign':'OBSIDIANTI_ARES_FK_VIEWER_RECOVERY_v1.0.1','candidateSHA256':actual,'expectedSHA256':expected,'ready':actual==expected}).encode()
   self.send_response(200 if actual==expected else 500);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload);return
  return super().do_GET()
 def log_message(self,*args):pass
http.server.ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
'''

def check_url(port):
    try:
        with urllib.request.urlopen('http://127.0.0.1:'+str(port)+'/__identity',timeout=2) as r:
            x=json.loads(r.read());return r.status==200 and x.get('candidateSHA256')==MODEL_SHA and x.get('ready') is True
    except Exception:return False

def main():
    script=pathlib.Path(sys.argv[1]).resolve();scriptsha=sys.argv[2]
    home=pathlib.Path.home();downloads=pathlib.Path('/storage/emulated/0/Download')
    state=home/'.local/state/obsidianti-ares-fk-viewer-v101';state.mkdir(parents=True,exist_ok=True)
    content=state/'web';content.mkdir(exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    receipt=state/('RECEIPT_'+stamp+'.json')
    record={'campaign':VERSION,'authority':'TERMUX_GIT_ONLY','launcherSHA256':scriptsha,'status':'STARTED','canonicalGLBMutated':False,'ownerVisualAcceptance':'PENDING','candidateSHA256Expected':MODEL_SHA,'archiveSHA256Expected':ARCHIVE_SHA,'agentsBlobSHAExpected':AGENTS_SHA,'receipt':str(receipt)}
    def save():
        p=receipt.with_suffix('.tmp');p.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');os.replace(p,receipt)
    save()
    try:
        # Canonical shared-storage path, not media-indexed discovery or an assumed Termux symlink.
        if not downloads.is_dir() or not os.access(downloads,os.W_OK):raise RuntimeError('ANDROID_SHARED_DOWNLOADS_UNAVAILABLE '+str(downloads))
        # Independent checkout, no impact on operator's dirty worktree.
        work=pathlib.Path(tempfile.mkdtemp(prefix='obs-ares-viewer-v101-',dir=str(state)))
        repo=work/'repo';env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1'
        cmd(['git','clone','--quiet',REMOTE,repo],timeout=480,env=env)
        record['remoteHeadAtClone']=cmd(['git','-C',repo,'rev-parse','HEAD']).stdout.strip()
        record['resolvedRepo']=str(repo);record['executionDir']=str(repo)
        record['branch']=cmd(['git','-C',repo,'branch','--show-current']).stdout.strip()
        origin=cmd(['git','-C',repo,'remote','get-url','origin']).stdout.strip()
        if origin.rstrip('/').removesuffix('.git')!=REMOTE.removesuffix('.git'):raise RuntimeError('WRONG_REMOTE '+origin)
        agents=repo/'AGENTS.md'
        if not agents.is_file():raise RuntimeError('AGENTS_MISSING')
        record['agentsBlobSHA']=cmd(['git','-C',repo,'rev-parse','HEAD:AGENTS.md']).stdout.strip()
        if record['agentsBlobSHA']!=AGENTS_SHA:raise RuntimeError('AGENTS_CHANGED_REVIEW_REQUIRED')
        existing=repo/REPO_FILE
        # Re-running an already-published launcher must be idempotent.
        if existing.exists():
            if sha(existing)!=scriptsha:raise RuntimeError('VERSIONED_SOURCE_COLLISION '+REPO_FILE)
            record['repoSource']='EXACT_ALREADY_PUBLISHED'
        else:
            existing.parent.mkdir(parents=True,exist_ok=True);atomic_copy(script,existing)
            cmd(['git','-C',repo,'add','--',REPO_FILE])
            cmd(['git','-C',repo,'commit','-m','Obsidianti: Ares FK candidate viewing recovery v1.0.1'])
            cmd(['git','-C',repo,'push','origin','HEAD:main'],timeout=180)
            record['repoSource']='COMMITTED_IN_TERMUX'
        record['sourceCommit']=cmd(['git','-C',repo,'rev-parse','HEAD']).stdout.strip()
        cmd(['git','-C',repo,'fetch','--quiet','origin','main'])
        record['remoteReadbackCommit']=cmd(['git','-C',repo,'rev-parse','refs/remotes/origin/main']).stdout.strip()
        if record['sourceCommit']!=record['remoteReadbackCommit']:raise RuntimeError('REMOTE_COMMIT_READBACK_MISMATCH')
        # Historical candidate is immutable evidence in Git LFS, not canonical GLB.
        result=json.loads((repo/EXPECTED_RESULT).read_text())
        if result.get('candidateSha256')!=MODEL_SHA or result.get('sourceSha256')!='5fa8773736cf4fd28eae13e13368246642642a1802d76e47ed7e14faf70d04c0':raise RuntimeError('RESULT_PROVENANCE_MISMATCH')
        archive=repo/ARCHIVE
        if not archive.is_file():raise RuntimeError('CANDIDATE_ARCHIVE_PATH_MISSING')
        cmd(['git','-C',repo,'lfs','fetch','--include='+ARCHIVE,'--exclude=','origin','HEAD'],timeout=600)
        cmd(['git','-C',repo,'lfs','checkout','--',ARCHIVE],timeout=180)
        if sha(archive)!=ARCHIVE_SHA:raise RuntimeError('GIT_LFS_ARCHIVE_SHA_MISMATCH')
        with zipfile.ZipFile(archive) as z:
            members=z.namelist()
            expected_members={MODEL_MEMBER,'RESULT.json'}
            if len(members)!=2 or set(members)!=expected_members or len(set(members))!=2:
                raise RuntimeError('ARCHIVE_MEMBER_SET_MISMATCH '+repr(members))
            for member in z.infolist():
                if member.is_dir() or member.filename not in expected_members or '/' in member.filename or chr(92) in member.filename:
                    raise RuntimeError('UNSAFE_ARCHIVE_MEMBER '+member.filename)
            # This is the archive's original production contract: model + result JSON.
            # Validate embedded provenance against the independently read Git result.
            embedded=json.loads(z.read('RESULT.json'))
            if embedded!=result or embedded.get('candidateSha256')!=MODEL_SHA:
                raise RuntimeError('ARCHIVE_RESULT_PROVENANCE_MISMATCH')
            out=content/'candidate.glb';tmp=content/'.candidate.glb.tmp'
            with z.open(MODEL_MEMBER) as src,open(tmp,'wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
            if sha(tmp)!=MODEL_SHA:raise RuntimeError('EXTRACTED_CANDIDATE_SHA_MISMATCH')
            os.replace(tmp,out)
        record['archiveSHA256Verified']=sha(archive);record['candidateSHA256Verified']=sha(out)
        page=content/HTML_NAME;page.write_text(VIEWER,encoding='utf-8')
        server=state/'server.py';server.write_text(SERVER,encoding='utf-8')
        # Shared-Downloads file: verify exact phone-visible path, without depending on MediaStore indexing.
        public=downloads/MODEL_NAME;record['sharedDownloadWrite']=atomic_copy(out,public)
        if sha(public)!=MODEL_SHA:raise RuntimeError('ANDROID_DOWNLOADS_SHA_READBACK_FAILED')
        record['sharedDownloadPath']=str(public);record['sharedDownloadSHA256']=sha(public)
        # Check Termux storage alias only for equality; don't confuse media scans with verified visibility.
        alias=home/'storage/downloads'
        if alias.is_dir():
            alias_candidate=alias/MODEL_NAME
            record['termuxAliasPath']=str(alias_candidate)
            record['termuxAliasSHA256']=sha(alias_candidate) if alias_candidate.is_file() else None
            if record['termuxAliasSHA256']!=MODEL_SHA:raise RuntimeError('DOWNLOADS_ALIAS_DISAGREES_WITH_SHARED_PATH')
        record['mediaScan']='NOT_REQUIRED_FOR_GLB'
        # Review URL is ALWAYS emitted to stdout; browser opening is best effort only.
        port=None
        for x in PORTS:
            if check_url(x):port=x;record['serverMode']='REUSED_VERIFIED';break
        if port is None:
            for x in PORTS:
                s=socket.socket()
                try:s.bind(('127.0.0.1',x))
                except OSError:continue
                finally:s.close()
                log=open(state/('server-'+str(x)+'.log'),'ab',buffering=0)
                try:
                    p=subprocess.Popen([sys.executable,'-B',str(server),str(content),str(x),MODEL_SHA],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=str(state))
                    for _ in range(35):
                        if check_url(x):port=x;record['viewerPID']=p.pid;record['serverMode']='STARTED_DETACHED';break
                        if p.poll() is not None:break
                        time.sleep(.2)
                    if port is not None:break
                    if p.poll() is None:p.terminate()
                finally:log.close()
        if port is None:raise RuntimeError('VERIFIED_PHONE_VIEWER_UNAVAILABLE')
        url=f'http://127.0.0.1:{port}/index.html'
        with urllib.request.urlopen(url,timeout=4) as r:
            data=r.read()
            if r.status!=200 or MODEL_SHA.encode() not in data or b'candidate.glb' not in data:raise RuntimeError('VIEWER_HTML_IDENTITY_FAILED')
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/candidate.glb',timeout=15) as r:
            if r.status!=200 or r.headers.get('Content-Length')!=str(out.stat().st_size):raise RuntimeError('VIEWER_MODEL_HTTP_BYTES_FAILED')
            # Verify actual served bytes as opposed to server's preflight identity alone.
            hh=hashlib.sha256()
            for chunk in iter(lambda:r.read(1024*1024),b''):hh.update(chunk)
            if hh.hexdigest()!=MODEL_SHA:raise RuntimeError('VIEWER_HTTP_MODEL_SHA_MISMATCH')
        record['reviewUrl']=url;record['viewerHTTPVerified']=True
        record['status']='VIEWER_READY_UNAPPROVED'
        save()
        public_receipt=downloads/(VERSION+'_LATEST_RECEIPT.json')
        atomic_copy(receipt,public_receipt)
        record['sharedReceiptPath']=str(public_receipt)
        save()
        atomic_copy(receipt,public_receipt)
        print('RESOLVED_REPO='+str(repo),flush=True)
        print('EXECUTION_DIR='+str(repo),flush=True)
        print('BRANCH='+record['branch']+' HEAD='+record['sourceCommit'],flush=True)
        print('ANDROID_DOWNLOADS_GLB='+str(public),flush=True)
        print('CANDIDATE_SHA256='+MODEL_SHA,flush=True)
        print('REMOTE_READBACK_VERIFIED=YES',flush=True)
        print('REVIEW_URL='+url,flush=True)
        print('REVIEW_URL='+url,flush=True)
        print('REVIEW_URL='+url,flush=True)
        print('STATUS=VIEWER_READY_UNAPPROVED',flush=True)
        print('RECEIPT='+str(receipt),flush=True)
        print('ANDROID_DOWNLOADS_RECEIPT='+str(public_receipt),flush=True)
        # Optional open only. It cannot be the only disclosure mechanism.
        if shutil.which('termux-open-url'):
            p=cmd(['termux-open-url',url],timeout=15,check=False)
            print('BROWSER_OPEN_ATTEMPT='+('COMMAND_ACCEPTED' if p.returncode==0 else 'FAILED'),flush=True)
        return 0
    except Exception as exc:
        record['status']='BLOCKED';record['error']=str(exc);record['errorType']=type(exc).__name__;save()
        print('BLOCKED='+str(exc),flush=True)
        if record.get('reviewUrl'):print('REVIEW_URL='+record['reviewUrl'],flush=True)
        print('RECEIPT='+str(receipt),flush=True)
        traceback.print_exc();return 2

sys.exit(main())
PY
