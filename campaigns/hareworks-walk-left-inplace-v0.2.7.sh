#!/data/data/com.termux/files/usr/bin/bash
# Hareworks v0.2.7: actual WALK LEFT, not slide. Independent 74-joint in-place reconstruction.
# Original GLB, forward v0.1.9, backward v0.2.2, pelvis-only v0.2.6 remain immutable.
set -Eeuo pipefail
CAMPAIGN='hareworks-walk-left-inplace-v0.2.7'
REPO='Valar05/parametric-parambulator'
BASE='ae6b2bf58a5700ac35c39094d05ab680a2ccf9db'
DIR='tools/hareworks-forward-woman/v0.2.7'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
PROTECTED_FORWARD='a17f8109766dcfa39fbb75b6b2ff335c358733cb'
PROTECTED_BACKWARD='61c9bea2aa3c5da5f331c45e2df41077670c3603'
PROTECTED_PELVIS_LAB='bde7aff0b75252192a64157a8b0f8ce6486e93fb'
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
exec > >(tee -a "$STATE/run.log") 2>&1
phase=preflight; ROOT=''; WORK=''; COMMIT=''; PID=''; PORT=''; SOURCE=''
fail(){
 echo "BLOCKED step=$phase reason=$*"
 python3 - "$STATE/blocked.json" "$CAMPAIGN" "$phase" "$*" "$COMMIT" "$ROOT" <<'PY_BLOCK' || true
import datetime,json,pathlib,sys
p,campaign,phase,error,commit,root=sys.argv[1:]
pathlib.Path(p).write_text(json.dumps({'campaign':campaign,'state':'BLOCKED','phase':phase,'reason':error,'sourceRevision':commit,'snapshot':root,'modelUnchanged':True,'approvedGaitsUnchanged':True,'ownerApprovedLeftWalk':False,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
PY_BLOCK
 exit 1
}
hash(){ sha256sum -- "$1" | cut -d' ' -f1; }
if [[ "${1:-run}" == status ]];then
 [[ -f "$STATE/receipt.json" ]] && cat "$STATE/receipt.json" || echo "NO_RECEIPT=$STATE/receipt.json"
 [[ ! -f "$STATE/left-walk-browser-receipt.json" ]] || cat "$STATE/left-walk-browser-receipt.json"
 exit 0
fi
[[ "${1:-run}" == run || "${1:-run}" == resume ]] || fail 'usage: bash campaign.sh [run|resume|status]'
for c in git python3 node curl sha256sum;do command -v "$c" >/dev/null || fail "missing Termux command $c";done
phase=embedded-python-preflight
python3 - "$0" <<'PY_PREFLIGHT' || fail 'embedded Python syntax rejected before checkout'
import ast,pathlib,re,sys
source=pathlib.Path(sys.argv[1]).read_text()
lines=source.splitlines(keepends=True)
found=[]
for i,line in enumerate(lines):
 m=re.search(r"<<'(?P<tag>PY_[A-Z0-9_]+)'",line)
 if not m:continue
 tag=m.group('tag');rest=''.join(lines[i+1:]);end=rest.find('\n'+tag+'\n')
 if end<0:raise SyntaxError('missing terminator '+tag)
 ast.parse(rest[:end],filename=tag);found.append(tag)
assert len(found)>=4,('insufficient Python blocks',found)
print('EMBEDDED_PYTHON_AST_PREFLIGHT_PASS',len(found))
PY_PREFLIGHT
SELF_SHA=$(hash "$0")
echo "CAMPAIGN=$CAMPAIGN"
echo "ENTRYPOINT_SHA256=$SELF_SHA"
echo "PINNED_PARENT=$BASE"
echo "SOURCE_CLIPS=Cautious_Crouch_Walk_Left,Cautious_Crouch_Walk_Left_inplace"
echo 'EXCLUDED_CLIP=slide_right'
echo "CANONICAL_MODEL_SHA256=$MODEL_SHA"
echo "RULES_AGENTS_BLOB=$AGENTS_BLOB"
echo 'CAMPAIGN_ETIQUETTE_HOME_CENTER=1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
echo 'TOP_DOWN_ETIQUETTE_HOME_CENTER=1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ORIGIN="https://github.com/$REPO.git"
phase=remote-preflight
REMOTE=''
for attempt in 1 2 3;do
 REMOTE=$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1) || REMOTE=''
 [[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] && break
 sleep "$attempt"
done
[[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] || fail 'remote HEAD cannot be determined'
echo "OBSERVED_REMOTE_MAIN=$REMOTE"
[[ "$REMOTE" == "$BASE" ]] || fail "main changed from pinned parent, no overwrite: $REMOTE"
phase=isolated-checkout
ROOT=$(mktemp -d "$STATE/snapshot.XXXXXXXX") || fail 'snapshot cannot be created'
WORK="$ROOT/repo"
for attempt in 1 2;do
 if GIT_LFS_SKIP_SMUDGE=1 git -c lfs.install.skip=true clone --depth=2 --filter=blob:none --no-checkout --single-branch --branch main "$ORIGIN" "$WORK";then break;fi
 [[ ! -e "$WORK" ]] || fail 'partial clone preserved; never modify a dirty clone'
 sleep "$attempt"
done
[[ -d "$WORK/.git" ]] || fail 'isolated checkout unavailable'
git -C "$WORK" sparse-checkout init --cone || fail 'sparse setup failed'
git -C "$WORK" sparse-checkout set assets/hareworks tools/hareworks-forward-woman campaigns || fail 'sparse paths failed'
GIT_LFS_SKIP_SMUDGE=1 git -C "$WORK" checkout -B "$CAMPAIGN" "$BASE" || fail 'checkout failed'
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$BASE" ]] || fail 'wrong checkout'
cd "$WORK"
[[ -z "$(git status --porcelain)" ]] || fail 'isolated checkout unexpectedly dirty'
phase=authority-and-source
[[ -f AGENTS.md ]] && grep -Fq 'Termux Git only' AGENTS.md || fail 'AGENTS authority unavailable'
[[ "$(git rev-parse HEAD:AGENTS.md)" == "$AGENTS_BLOB" ]] || fail 'root AGENTS changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.9/viewer.mjs)" == "$PROTECTED_FORWARD" ]] || fail 'accepted forward changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.2/viewer.mjs)" == "$PROTECTED_BACKWARD" ]] || fail 'accepted backward changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.6/viewer.mjs)" == "$PROTECTED_PELVIS_LAB" ]] || fail 'existing pelvis lab changed'
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" <<'PY_POINTER' || fail 'original model LFS pointer mismatch'
import subprocess,sys
p,sha,size=sys.argv[1:]
want=f'version https://git-lfs.github.com/spec/v1\noid sha256:{sha}\nsize {size}\n'.encode()
assert subprocess.check_output(['git','show','HEAD:'+p])==want
print('CANONICAL_GLB_POINTER_PASS')
PY_POINTER
phase=collision-gate
FILES=(
  "$DIR/index.html"
  "$DIR/viewer.mjs"
  "$DIR/sidestep-core.mjs"
  "$DIR/sidestep-core-test.mjs"
  "$DIR/source-witness.json"
  "$DIR/source-witness-test.mjs"
  "$DIR/README.md"
  "$DIR/contract.json"
  "$DIR/review-server.py"
  "campaigns/$CAMPAIGN.sh"
)
for file in "${FILES[@]}";do
 [[ ! -e "$file" && ! -L "$file" ]] || fail "new file collision $file"
 if git cat-file -e "HEAD:$file" 2>/dev/null;then fail "tracked path collision $file";fi
done
phase=model-acquisition
for searchRoot in "$HOME/.local/state/hareworks" "$HOME/storage/downloads" /storage/emulated/0/Download;do
 [[ -d "$searchRoot" ]] || continue
 depth=2; [[ "$searchRoot" != "$HOME/.local/state/hareworks" ]] || depth=10
 while IFS= read -r -d '' f;do
  [[ "$(wc -c < "$f" | tr -d ' ')" == "$MODEL_SIZE" ]] || continue
  if [[ "$(hash "$f")" == "$MODEL_SHA" ]];then SOURCE="$f";break;fi
 done < <(find -L "$searchRoot" -maxdepth "$depth" -type f -name 'Hareworks-nine-clips.glb' -print0 2>/dev/null)
 [[ -z "$SOURCE" ]] || break
done
if [[ -z "$SOURCE" ]];then
 command -v git-lfs >/dev/null || fail 'real model not cached and git-lfs unavailable'
 git lfs install --local || fail 'git-lfs local install failed'
 for attempt in 1 2 3;do
  if GIT_LFS_SKIP_SMUDGE=1 git lfs fetch -I "$MODEL" -X '' origin "$REMOTE";then break;fi
  sleep "$attempt"
 done
 OBJECT=$(git rev-parse --git-path "lfs/objects/${MODEL_SHA:0:2}/${MODEL_SHA:2:2}/$MODEL_SHA")
 [[ -f "$OBJECT" ]] || fail 'canonical binary model Git LFS missing'
 SOURCE="$OBJECT"
fi
[[ "$(wc -c < "$SOURCE" | tr -d ' ')" == "$MODEL_SIZE" && "$(hash "$SOURCE")" == "$MODEL_SHA" ]] || fail 'source binary hash or size mismatch'
python3 - "$SOURCE" <<'PY_GLB' || fail 'real GLB source clip/bone identity mismatch'
import json,struct,sys
with open(sys.argv[1],'rb') as f:
 h=f.read(20)
 assert h[:4]==b'glTF' and struct.unpack_from('<I',h,8)[0]==6784896
 n,kind=struct.unpack_from('<I4s',h,12)
 assert kind==b'JSON';raw=json.loads(f.read(n))
assert len(raw['skins'][0]['joints'])==74
names={a['name'] for a in raw['animations']}
assert len(names)==9
assert {'Cautious_Crouch_Walk_Left','Cautious_Crouch_Walk_Left_inplace'}<=names
print('REAL_74_JOINT_GLB_LEFT_WALK_PAIR_VERIFIED')
PY_GLB
phase=install-additive-only
mkdir -p "$DIR" || fail 'new output directory unavailable'
cat > "$DIR/index.html" <<'__HAREWORKS_LEFT_V027_FILE_0__'
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#111b27"><title>Hareworks v0.2.7 · Walk Left, not Slide</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>:root{font:15px system-ui,sans-serif;background:#101a26;color:#e9f4ff;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:1100px;margin:auto;padding:12px}h1{font-size:21px;margin:8px 0}.sub{font-size:13px;color:#c4d1dc;line-height:1.5}.labels{display:grid;grid-template-columns:1fr 1fr;gap:12px;text-align:center;padding:12px 0}#stage{border:1px solid #50768f;border-radius:10px;overflow:hidden}canvas{display:block;width:100%;touch-action:none}button,select{font:inherit;color:#f4f8ff;background:#2b4b64;border:1px solid #749ab4;border-radius:7px;min-height:44px;padding:8px}button:focus-visible,select:focus-visible,input:focus-visible{outline:3px solid #9eecf5}.toolbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:12px 0;padding:9px;background:#213548;border-radius:8px}input[type=range]{flex:1;min-width:140px;accent-color:#8ce3d9}label{font-size:13px}#status{color:#b3efbb;min-height:48px;padding:8px 0}#audit{background:#152c3c;border:1px solid #547487;border-radius:9px;padding:12px;white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.6 ui-monospace,monospace;max-height:400px;overflow:auto}#identity{color:#a5bed4;font:11px/1.4 ui-monospace,monospace;overflow-wrap:anywhere}a{color:#a8ddef}</style></head><body><main>
<h1>🐇 Hareworks · Walk Left</h1><p class="sub"><strong>Not slide_right.</strong> Compare the original authored <code>Cautious_Crouch_Walk_Left_inplace</code> (left) with its independent 74-joint procedural reconstruction (right). A separate toggle lets you examine the traveling <code>Cautious_Crouch_Walk_Left</code> source, with its locomotion removed only for side-by-side presentation. No feminine style transfer.</p>
<div id="identity">Checking exact GLB…</div><div id="status" role="status" aria-live="polite">Loading exact source rig…</div>
<div class="labels"><strong>LEFT · original in-place source</strong><strong>RIGHT · procedural in-place</strong></div><div id="stage" aria-label="Animated 3D leftward stepping comparison; original and procedural" role="img"></div>
<div class="toolbar"><button id="side">Side</button><button id="front">Front</button><button id="oblique">Three-quarter</button><button id="top">Top</button><span class="sub">Drag to orbit; pinch to zoom</span></div>
<div class="toolbar"><button id="play">Pause</button><label for="phase">Cycle phase</label><input id="phase" type="range" min="0" max="1000" step="1" value="0"><output id="phaseOut">0%</output></div>
<div class="toolbar"><label for="reference">Left comparison</label><select id="reference"><option value="inplace">Original Walk Left (in-place)</option><option value="travelling">Original Walk Left (traveling source, detrended for display)</option></select></div>
<div class="toolbar"><button id="auditButton">Run 74-joint + foot parity</button><button id="exportButton">Export evidence JSON</button><a href="../v0.2.2/index.html">Approved backward</a><a href="../v0.1.9/index.html">Approved forward</a></div>
<div id="audit" role="status">Awaiting actual skinned calibration…</div><p class="sub">The reference source clips have a discontinuous terminal reset; procedural cycle stitching is explicitly measured. Horizontal root travel is separated from cyclic pelvis sway, preserving natural stepping. Source contact witnesses are estimates, not force measurements. A passing numerical audit is not visual acceptance. Approved existing walks and source GLB remain unchanged.</p>
</main><script type="module" src="./viewer.mjs"></script></body></html>
__HAREWORKS_LEFT_V027_FILE_0__
[[ "$(hash "$DIR/index.html")" == "4f7d97ab6ed402d25c2ec1493b03b044eb8d063a9ab0aecd99e94b9aa373544d" ]] || fail "payload hash mismatch index.html"
cat > "$DIR/viewer.mjs" <<'__HAREWORKS_LEFT_V027_FILE_1__'
/* Hareworks v0.2.7: Walk LEFT, not slide. Source original vs independent full-rig math. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {ROOT,CLIPS,calibrate,pose,angleDeg} from './sidestep-core.mjs';
const $=id=>document.getElementById(id), V=()=>new THREE.Vector3();
const GLB='../../../assets/hareworks/Hareworks-nine-clips.glb', SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6',SIZE=6784896;
const N=720,SEP=2.8,scene=new THREE.Scene();scene.background=new THREE.Color('#101b27');
scene.add(new THREE.HemisphereLight(0xeef8ff,0x324456,2.5));const lamp=new THREE.DirectionalLight(0xffffff,3.2);lamp.position.set(-4,7,5);scene.add(lamp);
const grid=new THREE.GridHelper(15,30,0x6b869e,0x344759);scene.add(grid);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-4,4,2.5,-2.5,.01,100),orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.enablePan=false;orbit.target.set(0,.9,0);orbit.minZoom=.55;orbit.maxZoom=3.8;
const views={side:[-7,3.2,0],front:[0,2.6,8],oblique:[-6,3.6,6],top:[-.01,9,.01]};
function cameraAt(v){camera.position.set(...views[v]);camera.up.set(0,1,0);camera.zoom=1;camera.lookAt(orbit.target);camera.updateProjectionMatrix();orbit.update()}
function resize(){const w=Math.max(320,$('stage').clientWidth),h=Math.max(300,Math.min(590,Math.round(w*.72)));renderer.setSize(w,h,false);camera.left=-2.4*w/h;camera.right=-camera.left;camera.top=2.4;camera.bottom=-2.4;camera.updateProjectionMatrix()}
window.addEventListener('resize',resize);for(const k of Object.keys(views))$(k).onclick=()=>cameraAt(k);cameraAt('side');resize();
let reference=null,generated=null,refRig=null,genRig=null,mixer=null,clips={},samples={},plans={},ready=false,playing=true,phase=0,last=performance.now(),lastAudit=null;
const status=s=>$('status').textContent=s;
function rig(root){const m={};root.traverse(n=>{if(n.isBone){if(m[n.name])throw Error('DUPLICATE_BONE_'+n.name);m[n.name]=n}});if(Object.keys(m).length!==74||!m[ROOT])throw Error('NOT_74_BONES');return m}
function capture(gltf,key){const model=cloneSkeleton(gltf.scene),bones=rig(model),action=new THREE.AnimationMixer(model),clip=clips[key];action.clipAction(clip).reset().play();const result={name:key,sampleCount:N,duration:clip.duration,bones:{}};
 for(const name of Object.keys(bones))result.bones[name]={pos:[],quat:[],scale:[]};
 for(let i=0;i<N;i++){action.setTime(clip.duration*i/N);model.updateMatrixWorld(true);for(const [name,b] of Object.entries(bones)){const d=result.bones[name];d.pos.push(b.position.toArray());d.quat.push(b.quaternion.toArray());d.scale.push(b.scale.toArray())}}
 const raw=clip.tracks.find(t=>t.name===ROOT+'.position');if(raw){const z=raw.getValueSize(),n=raw.times.length;result.terminalRootTrack={lastTime:raw.times[n-1],lastPosition:Array.from(raw.values.slice((n-1)*z,n*z)),previousPosition:Array.from(raw.values.slice((n-2)*z,(n-1)*z))}}
 return result;}
function copyGenerated(p){const g=pose(samples[CLIPS[1]],plans[CLIPS[1]],p);for(const [name,c] of Object.entries(g.bones)){let b=genRig[name];b.position.fromArray(c.position);b.quaternion.fromArray(c.quaternion).normalize();b.scale.fromArray(c.scale)}generated.updateMatrixWorld(true);return g;}
function referenceAt(p,mode='inplace'){const name=mode==='travelling'?CLIPS[0]:CLIPS[1],clip=clips[name],q=((p%1)+1)%1;
 mixer.stopAllAction();mixer.clipAction(clip).play();mixer.setTime(q*clip.duration);
 const src=plans[name];refRig[ROOT].position.x-=src.trend[0]*q;refRig[ROOT].position.z-=src.trend[2]*q;reference.updateMatrixWorld(true);
}
function sampleAt(p){if(!ready)return;phase=((p%1)+1)%1;referenceAt(phase,$('reference').value);copyGenerated(phase);$('phaseOut').textContent=Math.round(phase*100)+'%';}
function atModel(b,model){return model.worldToLocal(b.getWorldPosition(V()));}
async function audit(){if(!ready)return;const prev=phase,was=playing;playing=false;$('play').textContent='Play';const counts=[],measures={},errors=[],baseline=samples[CLIPS[1]],plan=plans[CLIPS[1]];let maxFoot=0,changedWindow=1-plan.seamStart;
 const record=(name,kind,v,rate,q)=>{let k=name+':'+kind,o=measures[k]??={bone:name,metric:kind,n:0,sumSq:0,max:0,worst:null};o.n++;o.sumSq+=v*v;if(v>o.max){o.max=v;o.worst={rateHz:rate,phase:q}}};
 try{for(const hz of [30,60,120]){let count=0;for(let i=0;i<Math.ceil(baseline.duration*hz*2);i++){const p=i/(2*hz*baseline.duration);if(p>=plan.seamStart)break;
   referenceAt(p,'inplace');copyGenerated(p);
   for(const name of Object.keys(baseline.bones)){const a=refRig[name],b=genRig[name];record(name,'localQuaternionDeg',angleDeg(a.quaternion.toArray(),b.quaternion.toArray()),hz,p);record(name,'localPosition',a.position.distanceTo(b.position),hz,p);record(name,'localScale',a.scale.distanceTo(b.scale),hz,p);const d=atModel(a,reference).distanceTo(atModel(b,generated));record(name,'worldJoint',d,hz,p);if(/Foot$|ToeBase$/.test(name))maxFoot=Math.max(maxFoot,d);}
   count++;if(i%36===0)await new Promise(r=>requestAnimationFrame(r));}
  counts.push({hz,sampledHalfFrames:count});}
 const table=Object.values(measures).map(o=>({bone:o.bone,metric:o.metric,rms:Math.sqrt(o.sumSq/o.n),max:o.max,worst:o.worst}));table.sort((a,b)=>b.max-a.max);
 const limits={localQuaternionDeg:{rms:.4,max:1},localPosition:{rms:.003,max:.006},localScale:{rms:.0005,max:.001},worldJoint:{rms:.004,max:.008}};
 const failed=table.filter(r=>r.rms>limits[r.metric].rms||r.max>limits[r.metric].max);
 const z=pose(baseline,plan,0).bones,u=pose(baseline,plan,1-1e-7).bones;let seamRotation=0,seamPosition=0;
 for(const name of Object.keys(z)){seamRotation=Math.max(seamRotation,angleDeg(z[name].quaternion,u[name].quaternion));seamPosition=Math.max(seamPosition,Math.hypot(...z[name].position.map((v,i)=>v-u[name].position[i])))}
 lastAudit={schema:'hareworks-walk-left-inplace-parity-v0.2.7',status:failed.length?'SOURCE_PARITY_WARNINGS':'SOURCE_PARITY_WITHIN_LIMITS_OWNER_REVIEW_PENDING',sourceClips:CLIPS,sourceSha256:SHA,joints:74,calibratedSamples:N,reference:'authored Cautious_Crouch_Walk_Left_inplace source played by mixer, compared before repaired seam',generated:'independent pose equations, no AnimationMixer',testedPhase:[0,plan.seamStart],repairedPhaseFraction:changedWindow,sourceTerminalResetExcluded:true,rootTravel:{traveling:plans[CLIPS[0]].trend,inplace:plans[CLIPS[1]].trend},counts,thresholds:limits,perJoint:table,parityFailureCount:failed.length,failures:failed.slice(0,60),sourceModelUnchanged:true,acceptedForwardUnchanged:true,acceptedBackwardUnchanged:true,ownerAcceptedLeft:false,firstFrame:'explicitly compared in full parity; source and generated at p0',maxFootJointError:maxFoot,seam:{maxRotationDeg:seamRotation,maxPosition:seamPosition},createdAtUtc:new Date().toISOString()};
 $('audit').textContent=`${lastAudit.status}\nOriginal left walk vs in-place: source-travel x ${plans[CLIPS[0]].trend[0].toFixed(4)} model units; in-place residual trend x ${plans[CLIPS[1]].trend[0].toFixed(4)}.\nAll 74 joints, ${counts.map(s=>s.hz+'Hz '+s.sampledHalfFrames).join(' / ')}.\nViolations ${failed.length}, max foot positional error ${maxFoot.toFixed(5)}.\nSeam rotation ${seamRotation.toFixed(4)}°, position ${seamPosition.toFixed(6)}. Excluded modified terminal ${(changedWindow*100).toFixed(1)}%.\nWorst: ${table.slice(0,8).map(x=>x.bone+':'+x.metric+' '+x.max.toFixed(4)).join(' | ')}\nDownload evidence JSON for per-joint records.`;
 status(lastAudit.status==='SOURCE_PARITY_WARNINGS'?'PER-JOINT SOURCE WARNINGS · generated animation still visible':'74-JOINT SOURCE PARITY MEASURED · owner visual review pending');
 try{const r=await fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(lastAudit)});if(r.ok){const receipt=await r.json();status('ACTUAL BROWSER AUDIT SAVED IN TERMUX STATE · sha '+receipt.sha256.slice(0,12)+' · visual review pending')}else status('BROWSER AUDIT COMPUTED · automatic save HTTP '+r.status+' · use Export evidence')}
 catch(e){status('BROWSER AUDIT COMPUTED · autosave unavailable · use Export evidence')}
 }catch(e){status('AUDIT_ERROR '+e.message);console.error(e)}finally{sampleAt(prev);playing=was;$('play').textContent=playing?'Pause':'Play';}}
$('auditButton').onclick=()=>audit();$('exportButton').onclick=()=>{if(!lastAudit){status('Run audit first');return}const b=new Blob([JSON.stringify(lastAudit,null,2)],{type:'application/json'}),url=URL.createObjectURL(b),a=document.createElement('a');a.href=url;a.download='hareworks-walk-left-parity-v0.2.7.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),8000)};
$('play').onclick=()=>{if(!ready)return;playing=!playing;$('play').textContent=playing?'Pause':'Play'};
$('phase').oninput=()=>{playing=false;$('play').textContent='Play';sampleAt(Number($('phase').value)/1000)};
$('reference').onchange=()=>sampleAt(phase);
function frame(now){requestAnimationFrame(frame);const d=Math.min(.06,Math.max(0,(now-last)/1000));last=now;if(ready&&playing){sampleAt((phase+d/samples[CLIPS[1]].duration)%1);$('phase').value=Math.round(phase*1000)}orbit.update();renderer.render(scene,camera)}requestAnimationFrame(frame);
window.addEventListener('error',e=>status('VIEWER_ERROR '+(e.error?.message||e.message)));
try{const r=await fetch(GLB,{cache:'no-store'});if(!r.ok)throw Error('SOURCE_HTTP_'+r.status);const bytes=await r.arrayBuffer();if(bytes.byteLength!==SIZE)throw Error('SOURCE_SIZE_'+bytes.byteLength);
 const sha=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');if(sha!==SHA)throw Error('SOURCE_SHA_MISMATCH_'+sha);
 const gltf=await new GLTFLoader().parseAsync(bytes,new URL('../../../assets/hareworks/',import.meta.url).href);if(gltf.animations.length!==9)throw Error('NINE_CLIPS_REQUIRED');
 for(const k of CLIPS){clips[k]=gltf.animations.find(c=>c.name===k);if(!clips[k])throw Error('MISSING_LEFT_SOURCE_'+k)}
 reference=cloneSkeleton(gltf.scene);generated=cloneSkeleton(gltf.scene);refRig=rig(reference);genRig=rig(generated);reference.position.z=-SEP/2;generated.position.z=SEP/2;scene.add(reference,generated);
 mixer=new THREE.AnimationMixer(reference);for(const k of CLIPS)mixer.clipAction(clips[k]).reset().play();
 for(const k of CLIPS){samples[k]=capture(gltf,k);plans[k]=calibrate(samples[k]);}
 const changed=plans[CLIPS[0]].trend[0]-plans[CLIPS[1]].trend[0];if(!(changed>1&&changed<2))throw Error('SOURCE_LEFT_TRAVEL_SEPARATION_MISMATCH '+changed);
 ready=true;sampleAt(0);grid.position.y=new THREE.Box3().setFromObject(reference).min.y;resize();cameraAt('oblique');
 $('identity').textContent=`v0.2.7 · exact GLB SHA ${SHA} · original clips ${CLIPS.join(' and ')} · 74/74 joints · ${N} samples per clip · generated mixer=0 · commit ${new URLSearchParams(location.search).get('commit')||'unknown'} · entry SHA ${new URLSearchParams(location.search).get('scriptSha')||'unknown'}`;
 $('audit').textContent=`LEFT STEP SOURCE CONFIRMED · original traveling pelvis trend x ${plans[CLIPS[0]].trend[0].toFixed(4)}; in-place source residual trend x ${plans[CLIPS[1]].trend[0].toFixed(4)}.\nSource is not a slide. Generated solver uses the authored in-place clip and repairs the end-of-cycle seam.\nRun full 74-joint parity to confirm.`;
 status('LEFT STEPPING SOURCE VERIFIED · original in-place vs procedural; visual review pending');}
catch(e){status('SOURCE_OR_STARTUP_BLOCKED '+e.message);console.error(e)}
__HAREWORKS_LEFT_V027_FILE_1__
[[ "$(hash "$DIR/viewer.mjs")" == "3355d4c909417184393b5309fa25598982367a2cae09b33c56d06d6226b02352" ]] || fail "payload hash mismatch viewer.mjs"
cat > "$DIR/sidestep-core.mjs" <<'__HAREWORKS_LEFT_V027_FILE_2__'
/* Hareworks left STEP v0.2.7. Reconstruct original Cautious_Crouch_Walk_Left_inplace
   as an independent 74-joint continuous mathematical curve. The traveling
   Cautious_Crouch_Walk_Left is diagnostic only. No slide_right anywhere. */
export const ROOT='mixamorigHips';
export const CLIPS=['Cautious_Crouch_Walk_Left','Cautious_Crouch_Walk_Left_inplace'];
export const mod1=v=>((v%1)+1)%1;
const finite=(a,n)=>Array.isArray(a)&&a.length===n&&a.every(Number.isFinite);
function norm(a){if(!finite(a,4))throw Error('INVALID_QUAT');const l=Math.hypot(...a);if(l<1e-12)throw Error('ZERO_QUAT');return a.map(x=>x/l)}
export function qm(a,b){const [x,y,z,w]=a,[X,Y,Z,W]=b;return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]}
export const qc=a=>[-a[0],-a[1],-a[2],a[3]];
export function angleDeg(a,b){const x=norm(a),y=norm(b);const d=Math.min(1,Math.abs(x.reduce((s,v,i)=>s+v*y[i],0)));return 2*Math.acos(d)*180/Math.PI}
function slerp(A,B,t){const a=norm(A);let b=norm(B);let dot=a.reduce((s,v,i)=>s+v*b[i],0);if(dot<0){b=b.map(x=>-x);dot=-dot}if(dot>.9995)return norm(a.map((v,i)=>v*(1-t)+t*b[i]));const theta=Math.acos(Math.min(1,dot)),sin=Math.sin(theta);return norm(a.map((v,i)=>(Math.sin((1-t)*theta)*v+Math.sin(t*theta)*b[i])/sin))}
const lerp=(a,b,u)=>a.map((v,i)=>v+(b[i]-v)*u);
const hermite=(a,b,da,db,u,h)=>a.map((v,i)=>(2*u**3-3*u*u+1)*v+(u**3-2*u*u+u)*h*da[i]+(-2*u**3+3*u*u)*b[i]+(u**3-u*u)*h*db[i]);
function qlog(A){let q=norm(A);if(q[3]<0)q=q.map(x=>-x);const sin=Math.hypot(q[0],q[1],q[2]);if(sin<1e-10)return q.slice(0,3).map(x=>2*x);const a=2*Math.atan2(sin,q[3]);return q.slice(0,3).map(x=>x*a/sin)}
function qexp(v){if(!finite(v,3))throw Error('BAD_QEXP');const a=Math.hypot(...v),s=a<1e-9?.5:Math.sin(a/2)/a;return norm([...v.map(x=>x*s),Math.cos(a/2)])}
export function sample(clip,name,p){const n=clip?.sampleCount,s=clip?.bones?.[name];if(!s||!Number.isInteger(n)||n<120)throw Error('MISSING_SOURCE_BONE '+name);const u=Math.max(0,Math.min(n-1,p*n)),i=Math.floor(u),j=Math.min(n-1,i+1),t=u-i;return {position:lerp(s.pos[i],s.pos[j],t),quaternion:slerp(s.quat[i],s.quat[j],t),scale:lerp(s.scale[i],s.scale[j],t)}}
export function validate(clip){const n=clip?.sampleCount;if(!Number.isInteger(n)||n<240||Object.keys(clip.bones||{}).length!==74||!clip.bones[ROOT])throw Error('SOURCE_NOT_74_JOINT_240_SAMPLE');for(const [name,s] of Object.entries(clip.bones))if(s.pos?.length!==n||s.quat?.length!==n||s.scale?.length!==n||!s.pos.every(x=>finite(x,3))||!s.quat.every(x=>finite(x,4))||!s.scale.every(x=>finite(x,3)))throw Error('CORRUPT_SOURCE_'+name);return true}
export function calibrate(clip,seamStart=.93){validate(clip);if(!Number.isFinite(seamStart)||seamStart<.80||seamStart>.97)throw Error('SEAM_START_OUT_OF_RANGE');const n=clip.sampleCount,e=1/n,anchor=sample(clip,ROOT,0).position;
 // Measure noncyclic trend from the surviving endpoint just BEFORE the last
 // source key, never from the potentially teleported terminal key.
 const sampledEnd=sample(clip,ROOT,(n-1)/n).position;
 const endPhase=(n-1)/n;
 const trend=[(sampledEnd[0]-anchor[0])/endPhase,0,(sampledEnd[2]-anchor[2])/endPhase];
 const terminal=clip.terminalRootTrack||null;
 function detrend(name,p){const result=sample(clip,name,p);if(name===ROOT){result.position[0]-=trend[0]*p;result.position[2]-=trend[2]*p;}return result}
 const paths=Object.fromEntries(Object.keys(clip.bones).map(name=>{
  const start=detrend(name,0),s0=detrend(name,seamStart),sm=detrend(name,seamStart-e),sp=detrend(name,seamStart+e),startPlus=detrend(name,e);
  const deriv=(a,b)=>a.map((v,i)=>(v-b[i])/(2*e));
  const d0=deriv(sp.position,sm.position),d1=startPlus.position.map((v,i)=>(v-start.position[i])/e);
  const sc0=deriv(sp.scale,sm.scale),sc1=startPlus.scale.map((v,i)=>(v-start.scale[i])/e);
  const q0=norm(s0.quaternion),q1=norm(start.quaternion),qm0=norm(sm.quaternion),qp=norm(sp.quaternion),qep=norm(startPlus.quaternion);
  return [name,{p0:s0.position,p1:start.position,d0,d1,sc0:s0.scale,sc1:start.scale,ds0:sc0,ds1:sc1,q0,q1,delta:qlog(qm(qc(q0),q1)),w0:qlog(qm(qc(qm0),qp)).map(x=>x/(2*e)),w1:qlog(qm(qc(q1),qep)).map(x=>x/e)}]
 }));
 return {clip:clip.name,seamStart,anchor,trend,paths,rootMotionDetrended:true,sampledLast:sampledEnd,terminal};}
export function pose(clip,plan,phase){if(!plan||plan.clip!==clip.name||!finite(plan.anchor,3)||!finite(plan.trend,3))throw Error('WRONG_CALIBRATION');if(!Number.isFinite(phase))throw Error('BAD_PHASE');const p=mod1(phase),out={};for(const name of Object.keys(clip.bones)){
  let x;if(p<plan.seamStart){x=sample(clip,name,p);if(name===ROOT){x.position[0]-=plan.trend[0]*p;x.position[2]-=plan.trend[2]*p}}
  else{const a=plan.paths[name],u=(p-plan.seamStart)/(1-plan.seamStart),h=1-plan.seamStart;
   x={position:hermite(a.p0,a.p1,a.d0,a.d1,u,h),quaternion:norm(qm(a.q0,qexp(hermite([0,0,0],a.delta,a.w0,a.w1,u,h)))),scale:hermite(a.sc0,a.sc1,a.ds0,a.ds1,u,h)};
  }
  if(!finite(x.position,3)||!finite(x.quaternion,4)||!finite(x.scale,3))throw Error('NONFINITE_POSE_'+name);out[name]=x;
 }
 return {bones:out,phase:p,seamModified:p>=plan.seamStart};}
__HAREWORKS_LEFT_V027_FILE_2__
[[ "$(hash "$DIR/sidestep-core.mjs")" == "ba7978877852428a5a01d81008417f4eb6527f3faca3e9675150911b1ae543b4" ]] || fail "payload hash mismatch sidestep-core.mjs"
cat > "$DIR/sidestep-core-test.mjs" <<'__HAREWORKS_LEFT_V027_FILE_3__'
import assert from 'node:assert/strict';
import {ROOT,CLIPS,angleDeg,calibrate,pose,qm,validate} from './sidestep-core.mjs';
assert.deepEqual(CLIPS,['Cautious_Crouch_Walk_Left','Cautious_Crouch_Walk_Left_inplace']);
assert.ok(angleDeg(qm([0,0,0,1],[0,0,0,1]),[0,0,0,1])<1e-7);
const N=720;
function make(name){const bones={};for(let j=0;j<74;j++){
 const k=j?`Bone_${j}`:ROOT;const p=[],quat=[],scale=[];
 for(let i=0;i<N;i++){const x=i/N,w=2*Math.PI*x,angle=.18*Math.sin(w+j*.03),travel=name===CLIPS[0]?1.43*x:.12*Math.sin(Math.PI*x)**2;
  p.push(k===ROOT?[.006+travel,.83-.024*Math.sin(Math.PI*x)**2,.1+.04*Math.sin(w)]:[j*.001,.03*Math.sin(w+j),-.03*Math.cos(w)]);
  quat.push([0,Math.sin(angle/2),0,Math.cos(angle/2)]);scale.push([1,1,1]);
 }
 bones[k]={pos:p,quat,scale};}
 return {name,sampleCount:N,duration:1.166667,bones,terminalRootTrack:{lastTime:1.166667,lastPosition:[.003,.966,.0896]}}}
for(const k of CLIPS){const c=make(k);assert.equal(validate(c),true);const m=calibrate(c,.93);assert.equal(m.clip,k);
 assert.ok(Math.abs(m.trend[0]-(k===CLIPS[0]?1.43:0))<.007,'measured source root trend');
 for(const p of [0,.1,.25,.5,.85,.929, .97, .999999]){
  const x=pose(c,m,p).bones;assert.equal(Object.keys(x).length,74);
  if(p<.93){const original=c.bones.Bone_20.quat[Math.floor(p*N)];assert.ok(angleDeg(x.Bone_20.quaternion,original)<1,'source joint reconstruction');}
 }
 const p0=pose(c,m,0).bones,pend=pose(c,m,1-1e-8).bones;
 for(const b of Object.keys(p0)){assert.ok(angleDeg(p0[b].quaternion,pend[b].quaternion)<.02,'seam rotations '+b);assert.ok(Math.hypot(...p0[b].position.map((v,i)=>v-pend[b].position[i]))<.0001,'seam positions '+b)}
 assert.ok(Math.abs(pose(c,m,.5).bones[ROOT].position[0]-(k===CLIPS[0]?.006:.126))<.005,'linear travel removed, cyclic sway preserved');
 assert.throws(()=>calibrate(c,.76),/SEAM_START_OUT_OF_RANGE/);assert.throws(()=>pose(c,m,NaN),/BAD_PHASE/);
 const damaged=structuredClone(c);delete damaged.bones.Bone_73;assert.throws(()=>validate(damaged),/SOURCE_NOT_74/);
 const broken=structuredClone(c);broken.bones.Bone_1.pos[3][2]=NaN;assert.throws(()=>validate(broken),/CORRUPT_SOURCE/);
}
console.log('SIDESTEP_V027_INPLACE_SOURCE_PARITY_TESTS_PASS');
__HAREWORKS_LEFT_V027_FILE_3__
[[ "$(hash "$DIR/sidestep-core-test.mjs")" == "3afe3c93f023ab459eb199e908c7c283694edb07d02599a0eb2f511526fee214" ]] || fail "payload hash mismatch sidestep-core-test.mjs"
cat > "$DIR/source-witness.json" <<'__HAREWORKS_LEFT_V027_FILE_4__'
{
  "schema": "hareworks-left-step-source-witness-v0.2.7",
  "sourceSHA256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "sourceReportSchema": "hareworks-gait-and-idle-turn-v1.0.8",
  "clips": [
    {
      "name": "Cautious_Crouch_Walk_Left",
      "duration": 1.166667,
      "samples": 71,
      "pelvisStart": [
        0.00625,
        0.830801,
        0.102619
      ],
      "pelvisLastClean": [
        1.434964,
        0.83128,
        0.10348
      ],
      "pelvisTerminal": [
        0.00332,
        0.966211,
        0.089648
      ],
      "pelvisXMaxClean": 1.434964,
      "pelvisXMinClean": 0.00625,
      "sourceClassification": "LOCOMOTION_REFERENCE"
    },
    {
      "name": "Cautious_Crouch_Walk_Left_inplace",
      "duration": 1.166667,
      "samples": 71,
      "pelvisStart": [
        0.00625,
        0.834755,
        0.102619
      ],
      "pelvisLastClean": [
        0.011267,
        0.835211,
        0.103619
      ],
      "pelvisTerminal": [
        0.00332,
        0.966211,
        0.089648
      ],
      "pelvisXMaxClean": 0.125896,
      "pelvisXMinClean": -0.006524,
      "sourceClassification": "LOCOMOTION_REFERENCE"
    }
  ],
  "sourceFrame": "GLTF world space, +Y up, +Z heading convention; root translation cannot be inferred from pelvis alone"
}
__HAREWORKS_LEFT_V027_FILE_4__
[[ "$(hash "$DIR/source-witness.json")" == "9beb0ce7b7497630a094c473f0880c1c3027c4f458610b0928adf1e2733a8547" ]] || fail "payload hash mismatch source-witness.json"
cat > "$DIR/source-witness-test.mjs" <<'__HAREWORKS_LEFT_V027_FILE_5__'
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {CLIPS} from './sidestep-core.mjs';
const w=JSON.parse(fs.readFileSync(new URL('./source-witness.json',import.meta.url),'utf8'));
assert.equal(w.sourceSHA256,'a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6');
assert.deepEqual(w.clips.map(c=>c.name),CLIPS);
assert.equal(w.clips[0].duration,w.clips[1].duration);
assert.ok(w.clips[0].pelvisXMaxClean>1.4&&w.clips[0].pelvisXMaxClean<1.5);
assert.ok(w.clips[1].pelvisXMaxClean>.1&&w.clips[1].pelvisXMaxClean<.14);
assert.ok(w.clips[0].pelvisTerminal[0]<.01&&w.clips[0].pelvisLastClean[0]>1.4);
assert.ok(w.clips[0].pelvisLastClean[1]>.8&&w.clips[0].pelvisLastClean[1]<.86);
console.log('LEFT_WALK_REAL_SOURCE_WITNESS_PASS: 1.43-unit traveling left vs cyclic authored in-place; no slide_right');
__HAREWORKS_LEFT_V027_FILE_5__
[[ "$(hash "$DIR/source-witness-test.mjs")" == "f607923a6c3cd8025b93546bd9c1f72616046192752b6d705159ba0518d01dc1" ]] || fail "payload hash mismatch source-witness-test.mjs"
cat > "$DIR/README.md" <<'__HAREWORKS_LEFT_V027_FILE_6__'
# Hareworks Left Walk, In Place, v0.2.7

The owner explicitly corrected the selected animation: **the walk to the left, NOT the slide**. Source clips are `Cautious_Crouch_Walk_Left` and `Cautious_Crouch_Walk_Left_inplace`. No `slide_right` clip is loaded, compared, or transferred.

The real GLB original extracted evidence shows a ~1.43-unit lateral pelvis trajectory in the traveling left walk and only ~0.13 unit cyclic sideways excursion in its authored in-place version. The latter is our exact parity target. Recreate it using source-calibrated mathematical per-joint rotation, translation and scale trajectories across all 74 bones (720 calibrated phases). The generated character does not run source animation tracks. The original authored source clip plays only on the visible reference rig, and the traveling variant is offered exclusively for source comparison.

Remove only the small noncyclic source-root X/Z trend from the in-place curve. Preserve legitimate cyclical lateral sway and vertical bounce; this is not freezing the pelvis. Reconstruct the final ~7% seam with continuous quaternion/position/scale splines to avoid the GLB terminal reset. Explicitly disclose source-parity exclusion in the modified seam window. The generated at time zero should match the original source at time zero across all 74 local joints, independent of the two scene placements.

The browser audits 30, 60 and 120 Hz with half frames, measures all joints in the same model space and reports contact-ankle, toe and joint parity. It exports JSON and posts a copy to Termux persistent campaign state. It never claims that low-foot proximity proves physical foot contact. Numerical parity does not mean owner visual acceptance.

**Immutable approved baselines:** accepted forward v0.1.9, backward in-place v0.2.2, approved pelvis-only style experiment v0.2.6, source GLB (SHA a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6) and all prior files. This is an append-only prototype under `tools/hareworks-forward-woman/v0.2.7/`, deployed using the owner's Termux Git lane ONLY. No direct GitHub writes, no replacement architecture or visual approval claimed.

Fail clearly if Git HEAD changed, artifact paths collide, exact model identity fails, or a required test fails. A browser warning should remain viewable rather than hiding the animated model. Source comparison and generated gait remain explicitly separate.
__HAREWORKS_LEFT_V027_FILE_6__
[[ "$(hash "$DIR/README.md")" == "50a80f770ec7aed9985f291e5db15ec13b63f01f21e4213f1e6d60841a676108" ]] || fail "payload hash mismatch README.md"
cat > "$DIR/contract.json" <<'__HAREWORKS_LEFT_V027_FILE_7__'
{
  "campaign":"hareworks-walk-left-inplace-v0.2.7",
  "authoritativeRepo":"Valar05/parametric-parambulator",
  "expectedMain":"ae6b2bf58a5700ac35c39094d05ab680a2ccf9db",
  "ownerCorrection":"walk to the LEFT, not slide_right",
  "sourceClips":["Cautious_Crouch_Walk_Left","Cautious_Crouch_Walk_Left_inplace"],
  "sourceCalibrationTarget":"Cautious_Crouch_Walk_Left_inplace",
  "leftOriginalTravelComparisonOnly":true,
  "sourceModelSHA256":"a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "sourceModelBytes":6784896,
  "rigJointCount":74,
  "calibrationSamplesPerSourceClip":720,
  "generatedUsesAnimationMixer":false,
  "rootMotion":"remove noncyclic X and Z trend, preserve authored cyclical lateral sway and Y bounce",
  "seam":"source-derived periodic repair; exclude repaired source phase from strict direct parity",
  "strictReview":"all 74 joints, local quaternion/position/scale and model-space world positions; 30/60/120 fps plus half frames",
  "preserveForwardVersion":"v0.1.9",
  "preserveBackwardVersion":"v0.2.2",
  "preservePelvisOnlyStyleExperimentVersion":"v0.2.6",
  "executionLane":"Android Termux Git only",
  "ownerAcceptedLeft":false,
  "requiredAGENTSBlob":"547c2af52303f4efb718bbf8f82a698110c7bfca",
  "campaignEtiquetteHomeCenterId":"1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI"
}
__HAREWORKS_LEFT_V027_FILE_7__
[[ "$(hash "$DIR/contract.json")" == "b1b36b51fbae0f40ebaa72e421f6a1f88e396efb9c549ea5e1a1e3c2981b89af" ]] || fail "payload hash mismatch contract.json"
cat > "$DIR/review-server.py" <<'__HAREWORKS_LEFT_V027_FILE_8__'
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
__HAREWORKS_LEFT_V027_FILE_8__
[[ "$(hash "$DIR/review-server.py")" == "7631612f0734aa3afa13f2a2b4345ed2ccb851320fc0dd4ec95e1100880b14ba" ]] || fail "payload hash mismatch review-server.py"

cp -- "$0" "campaigns/$CAMPAIGN.sh" || fail 'source script copy failed'
[[ "$(hash "campaigns/$CAMPAIGN.sh")" == "$SELF_SHA" ]] || fail 'copied entrypoint bytes differ'
phase=testing
node "$DIR/sidestep-core-test.mjs" || fail 'kinematic source mathematical tests failed'
node "$DIR/source-witness-test.mjs" || fail 'authentic source extraction tests failed'
for f in "$DIR/viewer.mjs" "$DIR/sidestep-core.mjs" "$DIR/sidestep-core-test.mjs" "$DIR/source-witness-test.mjs";do node --check "$f" || fail "JavaScript parse failure $f";done
python3 - "$DIR/review-server.py" <<'PY_SERVER_AST' || fail 'server parse failure'
import ast,pathlib,sys
ast.parse(pathlib.Path(sys.argv[1]).read_text())
print('PYTHON_REVIEW_SERVER_AST_PASS')
PY_SERVER_AST
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || fail 'old tracked files unexpectedly changed'
phase=git-publication
git add -- "${FILES[@]}" || fail 'scoped new file staging failed'
[[ "$(git diff --cached --name-only | wc -l | tr -d ' ')" == "${#FILES[@]}" ]] || fail 'wrong staged file count'
git diff --cached --name-only | while IFS= read -r path;do [[ " $path " == " ${DIR}/"* || "$path" == "campaigns/$CAMPAIGN.sh" ]] || exit 1;done || fail 'staged an unauthorized path'
git -c commit.gpgsign=false commit -m "hareworks: 74-joint procedural left walk in-place v0.2.7" || fail 'git commit blocked'
COMMIT=$(git rev-parse HEAD)
[[ "$COMMIT" =~ ^[0-9a-f]{40}$ ]] || fail 'invalid new commit'
[[ "$(git show -s --format=%P "$COMMIT" | awk '{print $1}')" == "$BASE" ]] || fail 'unexpected parent'
phase=git-push
[[ "$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'main changed before push; no forced update'
git push origin "HEAD:refs/heads/main" || fail 'Git push failed; local commit preserved'
phase=git-exact-remote-readback
HEAD_REMOTE=$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1)
[[ "$HEAD_REMOTE" == "$COMMIT" ]] || fail 'remote HEAD does not match committed version'
git fetch --depth=1 origin main || fail 'remote readback fetch failed'
[[ "$(git rev-parse FETCH_HEAD)" == "$COMMIT" ]] || fail 'fetched remote commit differs'
for f in "${FILES[@]}";do
 [[ "$(git show "FETCH_HEAD:$f" | sha256sum | cut -d' ' -f1)" == "$(hash "$f")" ]] || fail "remote file readback hash mismatch $f"
done
echo "GIT_PUBLISHED_REMOTE_READBACK_VERIFIED=$COMMIT"
phase=local-browser-snapshot
cp -- "$SOURCE" "$MODEL" || fail 'browser read-only binary model copy failed'
[[ "$(hash "$MODEL")" == "$MODEL_SHA" ]] || fail 'browser model bytes differ'
READY="$ROOT/server-ready.json"
nohup python3 "$DIR/review-server.py" "$WORK" "$READY" "$STATE" > "$ROOT/server.log" 2>&1 </dev/null &
PID=$!
for attempt in 1 2 3 4 5 6 7 8 9 10;do
 if [[ -f "$READY" ]];then
  PORT=$(python3 - "$READY" <<'PY_PORT'
import json,sys
print(json.load(open(sys.argv[1]))['port'])
PY_PORT
)
 fi
 if [[ "$PORT" =~ ^[0-9]+$ ]] && curl --max-time 3 -fsS "http://127.0.0.1:$PORT/$DIR/index.html" >/dev/null;then break;fi
 sleep 1
done
[[ "$PORT" =~ ^[0-9]+$ ]] && kill -0 "$PID" 2>/dev/null || fail 'fresh browser server unavailable'
python3 - "http://127.0.0.1:$PORT" "$DIR" "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" "$STATE/http-manifest.json" <<'PY_HTTP' || fail 'exact browser dependencies or source GLB not served'
import hashlib,json,pathlib,sys,urllib.request
origin,directory,model,sha,size,out=sys.argv[1:]
def get(path):
 with urllib.request.urlopen(origin+'/'+path,timeout=35) as r:
  assert 'no-store' in r.headers.get('Cache-Control','')
  return r.read()
files=['index.html','viewer.mjs','sidestep-core.mjs','source-witness.json','review-server.py']
for name in files:
 assert len(get(directory+'/'+name))>20
raw=get(model)
assert len(raw)==int(size) and hashlib.sha256(raw).hexdigest()==sha
body=get(directory+'/viewer.mjs').decode()
assert 'Cautious_Crouch_Walk_Left' in body or 'CLIPS' in body
assert 'slide_right' not in body
record={'httpVerified':True,'modelSha256':sha,'modelBytes':len(raw),'browserRunPending':True,'paths':[directory+'/'+n for n in files]}
pathlib.Path(out).write_text(json.dumps(record,indent=2)+'\n')
print('HTTP_LEFT_STEP_SOURCE_AND_DEPS_PASS')
PY_HTTP
curl -fsSI --max-time 5 "http://127.0.0.1:$PORT/$DIR/index.html" > "$STATE/http-headers.txt" || fail 'headers readback failed'
URL="http://127.0.0.1:$PORT/$DIR/index.html?commit=$COMMIT&scriptSha=$SELF_SHA&modelSha=$MODEL_SHA"
python3 - "$STATE/receipt.json" "$CAMPAIGN" "$BASE" "$COMMIT" "$SELF_SHA" "$MODEL_SHA" "$AGENTS_BLOB" "$URL" "$PID" "$PORT" "$ROOT" <<'PY_RECEIPT' || fail 'receipt write failure'
import datetime,json,pathlib,sys
path,campaign,parent,commit,entry,model,agents,url,pid,port,snapshot=sys.argv[1:]
x={'campaign':campaign,'status':'PUBLISHED_TERMUX_GIT_READBACK_HTTP_VERIFIED_BROWSER_PARITY_PENDING','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'parent':parent,'actualRemoteCommit':commit,'entrySHA256':entry,'modelSHA256':model,'AGENTS_blob':agents,
 'etiquetteHomeCenterId':'1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI','topDownHomeCenterId':'1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU',
 'sourceClips':['Cautious_Crouch_Walk_Left','Cautious_Crouch_Walk_Left_inplace'],'excludedClip':'slide_right','generatedRigJointCount':74,
 'sourceModelUnchanged':True,'approvedForwardBackwardUnchanged':True,'approvedPelvisExperimentUnchanged':True,'generatedAnimationMixerCount':0,
 'actualBrowserParity':'PENDING','ownerLeftGaitAcceptance':'PENDING','viewerURL':url,'viewerPID':int(pid),'viewerPort':int(port),'snapshot':snapshot,'executionLane':'Android Termux Git only'}
pathlib.Path(path).write_text(json.dumps(x,indent=2)+'\n')
PY_RECEIPT
echo "REMOTE_COMMIT=$COMMIT"
echo "MODEL_SHA256=$MODEL_SHA"
echo 'REFERENCE_SOURCE=Cautious_Crouch_Walk_Left_inplace'
echo 'TRAVELING_SOURCE=Cautious_Crouch_Walk_Left'
echo 'EXCLUDED_SLIDING_CLIP=slide_right'
echo "VIEWER_URL=$URL"
echo "VIEWER_PORT=$PORT VIEWER_PID=$PID"
echo "RECEIPT=$STATE/receipt.json"
echo "BROWSER_EVIDENCE_AFTER_AUDIT=$STATE/left-walk-browser-evidence.json"
echo 'REAL_SKINNED_BROWSER_PARITY=PENDING; OWNER_VISUAL_ACCEPTANCE=PENDING'
if command -v termux-open-url >/dev/null;then
 termux-open-url "$URL" || echo "OPEN_REQUEST_FAILED; open VIEWER_URL=$URL"
else echo "TERMUX_OPEN_URL_UNAVAILABLE; open VIEWER_URL=$URL";fi
