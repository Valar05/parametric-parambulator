#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
CAMPAIGN=hareworks-gait-extraction-v1.0.0
REPO=Valar05/parametric-parambulator
EXPECTED_HEAD=dd7251f3406b795af22dc9bdf38d14e40e8c3578
EXPECTED_GLB=4ee555a0e416e3b2d03290fea85fa5306f894b9b4a5e8feb3f41078d5eb7d828
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
LOG="$STATE/run.log"
exec > >(tee -a "$LOG") 2>&1
fail(){ echo "BLOCKED step=$1 reason=$2"; exit 1; }
trap 'echo "FAILED line=$LINENO command=$BASH_COMMAND"' ERR
for c in git git-lfs python3 sha256sum curl; do command -v "$c" >/dev/null || fail dependency "$c missing"; done
command -v termux-open-url >/dev/null || fail dependency 'termux-open-url missing'
# The repo and live etiquette were read by the author; verify pinned AGENTS in checkout.
ROOT="$STATE/work"
if [[ -d "$ROOT/.git" ]]; then
  [[ -z "$(git -C "$ROOT" status --porcelain)" ]] || fail checkout 'existing isolated checkout is dirty'
  env GIT_LFS_SKIP_SMUDGE=1 git -C "$ROOT" fetch --no-tags origin main || fail fetch 'cannot refresh existing checkout'
  env GIT_LFS_SKIP_SMUDGE=1 git -C "$ROOT" checkout -B "$CAMPAIGN" origin/main
else
  [[ ! -e "$ROOT" ]] || fail checkout 'work path collision'
  GIT_LFS_SKIP_SMUDGE=1 git clone --filter=blob:none --no-checkout "https://github.com/$REPO.git" "$ROOT" || fail clone 'clone failed'
  env GIT_LFS_SKIP_SMUDGE=1 git -C "$ROOT" checkout -b "$CAMPAIGN" origin/main || fail checkout 'checkout failed'
fi
cd "$ROOT"
HEAD=$(git rev-parse HEAD)
[[ "$HEAD" == "$EXPECTED_HEAD" ]] || fail source "main changed; expected $EXPECTED_HEAD actual $HEAD; no writes"
[[ -f AGENTS.md ]] && grep -q 'Termux Git only' AGENTS.md || fail rules 'AGENTS read gate failed'
REPL_BLOB=$(git rev-parse HEAD:assets/repl/Repl.glb)
[[ -n "$REPL_BLOB" ]] || fail source 'canonical Repl missing'
REPL_SHA=$(git show HEAD:assets/repl/Repl.glb | sha256sum | cut -d' ' -f1)
# LFS path filter must exclude the historical missing Repl LFS object.
git -c lfs.fetchrecentalways=false lfs fetch --include='assets/hareworks/Hareworks.glb' --exclude='assets/repl/*' origin "$HEAD" || fail lfs 'Hareworks LFS fetch failed'
git lfs checkout assets/hareworks/Hareworks.glb || fail lfs 'Hareworks checkout failed'
[[ "$(sha256sum assets/hareworks/Hareworks.glb | cut -d' ' -f1)" == "$EXPECTED_GLB" ]] || fail source 'Hareworks source hash mismatch'
DIR="tools/hareworks-gait-extraction/v1.0.0"
for f in "$DIR/index.html" "$DIR/README.md" "$DIR/gait-extract.mjs" "campaigns/$CAMPAIGN.sh"; do
  [[ ! -e "$f" ]] && ! git ls-tree -r --name-only HEAD | grep -Fxq "$f" || fail collision "$f exists"
done
mkdir -p "$DIR" campaigns
cp "$0" "campaigns/$CAMPAIGN.sh"
cat > "$DIR/gait-extract.mjs" <<'JS'
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const loader=new GLTFLoader();
const output=document.querySelector('#status'), selector=document.querySelector('#clip'), table=document.querySelector('#table');
const stage=document.querySelector('#stage');
const scene=new THREE.Scene();scene.background=new THREE.Color('#20242d');
const camera=new THREE.PerspectiveCamera(38,1,.01,1000);camera.position.set(4,3.8,5.2);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));stage.append(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x404050,2));const sun=new THREE.DirectionalLight(0xffffff,2.5);sun.position.set(4,7,5);scene.add(sun);
const floor=new THREE.GridHelper(20,20,0x667788,0x444455);scene.add(floor);
let model,mixer,clips=[],last=performance.now(),playing=true,active=0,report=null;
const bones={left:['LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase'],right:['RightUpLeg','RightLeg','RightFoot','RightToeBase']};
function findBone(root,name){let matches=[];root.traverse(o=>{if(o.isBone && (o.name===name||o.name.endsWith(':'+name)||o.name.endsWith('_'+name)))matches.push(o)});return matches[0]||null}
function pos(b){return b.getWorldPosition(new THREE.Vector3()).toArray().map(x=>+x.toFixed(6))}
function angle(a,b,c){const u=new THREE.Vector3().fromArray(a).sub(new THREE.Vector3().fromArray(b)).normalize();const v=new THREE.Vector3().fromArray(c).sub(new THREE.Vector3().fromArray(b)).normalize();return +THREE.MathUtils.radToDeg(Math.acos(THREE.MathUtils.clamp(u.dot(v),-1,1))).toFixed(3)}
function quantile(a,p){if(!a.length)return null;const s=[...a].sort((x,y)=>x-y);return s[Math.floor((s.length-1)*p)]}
function analyze(clip){const nodes={};for(const [side,names] of Object.entries(bones)){nodes[side]=names.map(n=>findBone(model,n));if(nodes[side].some(n=>!n))throw new Error('Missing bone chain '+side+': '+names.map((n,i)=>nodes[side][i]?null:n).filter(Boolean).join(','))}
const pelvis=findBone(model,'Hips');if(!pelvis)throw new Error('Hips bone missing');
const duration=clip.duration, count=Math.max(60,Math.ceil(duration*60));const tracks=[];
const prior=mixer.timeScale;mixer.timeScale=1;mixer.stopAllAction();const action=mixer.clipAction(clip);action.reset().play();
for(let i=0;i<=count;i++){const t=duration*i/count;mixer.setTime(t);model.updateMatrixWorld(true);let row={t:+t.toFixed(6),pelvis:pos(pelvis),feet:{}};for(const side of ['left','right']){const [hip,knee,ankle,toe]=nodes[side].map(pos);row.feet[side]={hip,knee,ankle,toe,kneeAngle:angle(hip,knee,ankle)}}tracks.push(row)}
action.stop();mixer.timeScale=prior;
const profiles={};for(const side of ['left','right']){const ys=tracks.map(r=>r.feet[side].toe[1]);const baseline=quantile(ys,.08);const speeds=[];for(let i=1;i<tracks.length;i++){const a=tracks[i-1].feet[side].toe,b=tracks[i].feet[side].toe;const dt=tracks[i].t-tracks[i-1].t;speeds.push(Math.hypot(b[0]-a[0],b[2]-a[2])/dt)}const threshold=Math.max(.015,(quantile(speeds,.25)||0)*1.35);const tolerance=Math.max(.012,(quantile(ys,.75)-baseline)*.17);let contacts=0,segments=[],open=null;for(let i=0;i<tracks.length;i++){const grounded=(ys[i]-baseline)<tolerance && (i===0||speeds[i-1]<threshold);tracks[i].feet[side].contactCandidate=grounded;if(grounded){contacts++;if(open===null)open=i}else if(open!==null){segments.push([tracks[open].t,tracks[i-1].t]);open=null}}if(open!==null)segments.push([tracks[open].t,tracks.at(-1).t]);profiles[side]={baselineToeY:baseline,contactHeightTolerance:tolerance,contactSpeedThreshold:threshold,contactFraction:contacts/tracks.length,contactIntervals:segments,verticalToeRange:[Math.min(...ys),Math.max(...ys)],kneeAngleRange:[Math.min(...tracks.map(r=>r.feet[side].kneeAngle)),Math.max(...tracks.map(r=>r.feet[side].kneeAngle))]}}
const p0=tracks[0].pelvis,p1=tracks.at(-1).pelvis;return {clip:clip.name,duration,samples:tracks.length,rootPelvisDisplacement:p1.map((x,i)=>+(x-p0[i]).toFixed(6)),contactInference:'HEURISTIC: toe height + horizontal velocity, not verified skinned-sole contact',profiles,tracks}}
function renderReport(){table.textContent='';for(const r of report.clips){const tr=document.createElement('tr');for(const x of [r.clip,r.duration.toFixed(2),r.samples,r.profiles.left.contactFraction.toFixed(2),r.profiles.right.contactFraction.toFixed(2)]){const td=document.createElement('td');td.textContent=x;tr.append(td)}table.append(tr)}}
function download(name,content){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type:'application/json'}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),3000)}
document.querySelector('#export').onclick=()=>{if(report)download('hareworks-gait-seven-clips-v1.0.0.json',JSON.stringify(report,null,2))};
document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'Pause':'Play'};
selector.onchange=()=>{active=+selector.value;mixer.stopAllAction();mixer.clipAction(clips[active]).reset().play()};
function size(){const w=stage.clientWidth,h=Math.max(320,Math.round(w*.63));renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}window.addEventListener('resize',size);
function tick(now){requestAnimationFrame(tick);if(mixer&&playing)mixer.update(Math.min((now-last)/1000,.05));last=now;renderer.render(scene,camera)}requestAnimationFrame(tick);
try{output.textContent='Loading source GLB…';const gltf=await loader.loadAsync('../../../assets/hareworks/Hareworks.glb');model=gltf.scene;scene.add(model);model.updateMatrixWorld(true);const bbox=new THREE.Box3().setFromObject(model);const center=bbox.getCenter(new THREE.Vector3()),size3=bbox.getSize(new THREE.Vector3());floor.position.y=bbox.min.y;camera.position.set(size3.x*2+1,size3.y*1.2+1,size3.z*2+3);camera.lookAt(center);clips=gltf.animations;mixer=new THREE.AnimationMixer(model);report={schema:'hareworks-gait-extraction-v1.0.0',sourceSha256:'4ee555a0e416e3b2d03290fea85fa5306f894b9b4a5e8feb3f41078d5eb7d828',units:'source model units',frame:'model scene/world coordinates; root motion NOT subtracted',notes:['Heuristic contact candidates, not validated skinned sole','Root motion vs in-place classification requires further analysis','No procedural IK implemented in this campaign'],clips:[]};for(const clip of clips){output.textContent='Analyzing '+clip.name;report.clips.push(analyze(clip));const o=document.createElement('option');o.value=String(selector.length);o.textContent=clip.name;selector.append(o)}renderReport();mixer.stopAllAction();mixer.clipAction(clips[0]).reset().play();size();output.textContent='Seven-clip analysis complete. Export JSON for the full trajectories.'}catch(e){output.textContent='BLOCKED: '+e.message;console.error(e)}
JS
cat > "$DIR/index.html" <<'HTML'
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hareworks gait extraction v1.0.0</title><script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script><style>body{margin:0;background:#161a20;color:#eee;font:16px system-ui}main{max-width:1050px;margin:auto;padding:14px}#stage{width:100%;border:1px solid #667;border-radius:8px;overflow:hidden}button,select{font:inherit;padding:9px;margin:6px;background:#303b49;color:white;border:1px solid #718}table{border-collapse:collapse;width:100%;font-size:13px}td,th{padding:8px;border-bottom:1px solid #445;text-align:left}small{color:#bbc}</style></head><body><main><h2>Hareworks • seven-clip gait archaeology</h2><p id="status" role="status">Starting…</p><div id="stage"></div><label>Reference clip <select id="clip"></select></label><button id="play">Pause</button><button id="export">Export all trajectory JSON</button><p><small>Contact phases are heuristic candidates, not proof of planted soles. This is an animation analysis viewer, not procedural IK.</small></p><table><thead><tr><th>Clip</th><th>Seconds</th><th>Samples</th><th>Left contact fraction</th><th>Right contact fraction</th></tr></thead><tbody id="table"></tbody></table></main><script type="module" src="./gait-extract.mjs"></script></body></html>
HTML
cat > "$DIR/README.md" <<'MD'
# Hareworks gait extraction v1.0.0

Read-only browser-side extraction from `assets/hareworks/Hareworks.glb`. It samples all seven animation clips at >=60 Hz through Three.js AnimationMixer, records world-space hip/knee/ankle/toe and pelvis trajectories, knee angle, and preliminary toe contact candidates. Use the **Export all trajectory JSON** button to save measurements. Contact estimates are explicitly heuristic, not skinned-sole validated. Does not implement IK or modify any GLB. The CDN requires internet on first viewer load. The viewer is served from the repository root so its relative GLB path resolves correctly.
MD
python3 - <<'PY'
from pathlib import Path
p=Path('tools/hareworks-gait-extraction/v1.0.0/gait-extract.mjs')
s=p.read_text()
assert s.count('await loader.loadAsync')==1
assert 'contactInference' in s and 'rootPelvisDisplacement' in s
assert 'mixer.setTime(t)' in s
assert 'assets/hareworks/Hareworks.glb' in s
assert 'new THREE.AnimationMixer(model)' in s
print('STATIC_ANALYSIS_CHECK=PASS')
PY
[[ "$(git rev-parse HEAD:assets/repl/Repl.glb)" == "$REPL_BLOB" ]] || fail regression 'Repl changed'
[[ "$(sha256sum assets/hareworks/Hareworks.glb | cut -d' ' -f1)" == "$EXPECTED_GLB" ]] || fail regression 'Hareworks changed'
git add -- "$DIR/index.html" "$DIR/gait-extract.mjs" "$DIR/README.md" "campaigns/$CAMPAIGN.sh"
[[ "$(git diff --cached --name-only | wc -l)" -eq 4 ]] || fail scope 'unexpected staged files'
git -c user.name='Hareworks Termux Campaign' -c user.email='hareworks-campaign@users.noreply.github.com' commit -m 'Add Hareworks seven-clip gait extraction viewer v1.0.0'
COMMIT=$(git rev-parse HEAD)
# No force push; if main advances, fail safely.
git push origin HEAD:refs/heads/main || fail publish 'push failed; local commit preserved'
REMOTE=$(git ls-remote origin refs/heads/main | cut -f1)
[[ "$REMOTE" == "$COMMIT" ]] || fail readback "remote mismatch $REMOTE vs $COMMIT"
git fetch origin main || fail readback "remote fetch failed"
[[ "$(git rev-parse FETCH_HEAD)" == "$COMMIT" ]] || fail readback "fetched remote commit differs"
[[ "$(git rev-parse FETCH_HEAD:assets/repl/Repl.glb)" == "$REPL_BLOB" ]] || fail readback "remote Repl changed"
for f in "$DIR/index.html" "$DIR/gait-extract.mjs" "$DIR/README.md" "campaigns/$CAMPAIGN.sh"; do
  [[ "$(git show FETCH_HEAD:"$f" | sha256sum | cut -d' ' -f1)" == "$(sha256sum "$f" | cut -d' ' -f1)" ]] || fail readback "content mismatch $f"
done
PORT=0
for p in 8765 8766 8767 8768 8769; do
  if ! (echo >/dev/tcp/127.0.0.1/$p) >/dev/null 2>&1; then PORT=$p; break; fi
done
[[ "$PORT" -gt 0 ]] || fail viewer 'no free port'
cat > "$STATE/server.py" <<'PYSERVER'
import http.server,sys
class Handler(http.server.SimpleHTTPRequestHandler):
 def end_headers(self):
  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
  self.send_header('Pragma','no-cache')
  super().end_headers()
http.server.ThreadingHTTPServer(('127.0.0.1',int(sys.argv[1])),Handler).serve_forever()
PYSERVER
nohup python3 "$STATE/server.py" "$PORT" >"$STATE/server.log" 2>&1 </dev/null &
PID=$!
for i in 1 2 3 4 5 6 7 8; do curl -fsS "http://127.0.0.1:$PORT/$DIR/index.html" >/dev/null && break; sleep 1; done
kill -0 "$PID" || fail viewer 'server exited'
URL="http://127.0.0.1:$PORT/$DIR/index.html?commit=$COMMIT"
python3 - "$STATE/receipt.json" "$HEAD" "$COMMIT" "$REPL_SHA" "$EXPECTED_GLB" "$URL" "$PID" <<'PY'
import json,sys
from pathlib import Path
out,source,commit,repl,hare,url,pid=sys.argv[1:]
Path(out).write_text(json.dumps({'campaign':'hareworks-gait-extraction-v1.0.0','sourceCommit':source,'publishedCommit':commit,'rulesRead':'AGENTS.md plus Home Center Campaign Etiquette read by author','canonicalReplSha256':repl,'hareworksSha256':hare,'viewerUrl':url,'viewerPid':int(pid),'state':'viewer_started_browser_extraction_pending','ownerVisualAcceptance':False},indent=2))
PY
echo "REMOTE_COMMIT=$COMMIT"
echo "MODEL_UNCHANGED=YES"
echo "GAME_VIEWER_URL=$URL"
echo "RECEIPT=$STATE/receipt.json"
termux-open-url "$URL" || echo 'VIEWER_OPEN_FAILED=YES URL_PRINTED=YES'
