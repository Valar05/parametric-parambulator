#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
CAMPAIGN=hareworks-gait-extraction-v1.0.8
REPO=Valar05/parametric-parambulator
BASE=9b77c19d2f542706d5e04319068345f32583be2a
MODEL_SHA=a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6
MODEL_SIZE=6784896
MODEL=assets/hareworks/Hareworks-nine-clips.glb
DIR=tools/hareworks-gait-extraction/v1.0.8
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
exec > >(tee -a "$STATE/run.log") 2>&1
phase=preflight
fail(){
  echo "BLOCKED step=$phase reason=$*"
  python3 - "$STATE/blocked.json" "$CAMPAIGN" "$phase" "$*" "$BASE" "$MODEL_SHA" <<'PY' || true
import json,sys,datetime
from pathlib import Path
p,c,step,reason,head,sha=sys.argv[1:]
Path(p).write_text(json.dumps(dict(campaign=c,phase='blocked',step=step,reason=reason,base=head,modelSha256=sha,atUtc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2))
PY
  exit 1
}
trap 'echo "ERROR line=$LINENO command=$BASH_COMMAND"' ERR
for c in git git-lfs python3 sha256sum curl; do command -v "$c" >/dev/null || fail "dependency $c missing"; done
command -v termux-open-url >/dev/null || fail 'termux-open-url missing'
ROOT="$STATE/work"
phase=checkout
if [[ -e "$ROOT" ]]; then
  [[ -d "$ROOT/.git" ]] || fail 'isolated checkout path collision'
  [[ "$(git -C "$ROOT" remote get-url origin)" == "https://github.com/$REPO.git" ]] || fail 'unexpected checkout origin'
  [[ -z "$(git -C "$ROOT" status --porcelain --untracked-files=all)" ]] || fail 'checkout has modifications; preserved without reset'
else
  git -c lfs.install.skip=true clone --filter=blob:none --depth=1 --no-checkout "https://github.com/$REPO.git" "$ROOT" || fail 'clone failed'
fi
git -C "$ROOT" sparse-checkout init --cone || fail 'sparse init failed'
git -C "$ROOT" sparse-checkout set assets/hareworks tools/hareworks-gait-extraction campaigns || fail 'sparse set failed'
env GIT_LFS_SKIP_SMUDGE=1 git -C "$ROOT" fetch --depth=1 --no-tags origin main || fail 'fetch failed'
HEAD=$(git -C "$ROOT" rev-parse FETCH_HEAD)
[[ "$HEAD" == "$BASE" ]] || fail "main advanced: expected $BASE actual $HEAD; no changes"
env GIT_LFS_SKIP_SMUDGE=1 git -C "$ROOT" checkout -B "$CAMPAIGN" "$HEAD" || fail 'checkout failed'
cd "$ROOT"
[[ -f AGENTS.md ]] && grep -Fq 'Termux Git only' AGENTS.md || fail 'pinned AGENTS.md failed'
AGENTS_BLOB=$(git rev-parse HEAD:AGENTS.md)
REPL_BLOB=$(git rev-parse HEAD:assets/repl/Repl.glb)
OLD_HARE_BLOB=$(git rev-parse HEAD:assets/hareworks/Hareworks.glb)
phase=collision
# Check every publication destination BEFORE any write, including the input LFS path.
for path in "$MODEL" "$DIR/index.html" "$DIR/gait-extract.mjs" "$DIR/README.md" "$DIR/contract.json" "campaigns/$CAMPAIGN.sh"; do
  if [[ -e "$path" || -L "$path" ]] || git cat-file -e "HEAD:$path" 2>/dev/null; then
    fail "destination occupied: $path; never overwrite"
  fi
done
# The v1.0.7 worktree may contain an unfinished asset. Do not mutate it or
# reinterpret its presence as a remote publication; use the owner Downloads GLB.
phase=source
SOURCE=''
SEARCH=()
for d in "$HOME/storage/downloads" /storage/emulated/0/Download /sdcard/Download; do
  [[ -d "$d" ]] || continue
  abs=$(cd -P -- "$d" 2>/dev/null && pwd) || continue
  [[ -r "$abs" ]] || continue
  case " ${SEARCH[*]-} " in *" $abs "*) ;; *) SEARCH+=("$abs");; esac
done
((${#SEARCH[@]})) || fail 'Android Downloads inaccessible'
seen=0
for d in "${SEARCH[@]}"; do
  while IFS= read -r -d '' f; do
    seen=$((seen+1))
    sha=$(sha256sum -- "$f" | cut -d' ' -f1) || fail "cannot hash $f"
    echo "SOURCE_CANDIDATE_SHA=$sha FILE=$f"
    if [[ "$sha" == "$MODEL_SHA" ]]; then SOURCE="$f"; break; fi
  done < <(find "$d" -maxdepth 1 -type f -iname '*.glb' -print0 2>/dev/null)
  [[ -n "$SOURCE" ]] && break
done
[[ -n "$SOURCE" ]] || fail "nine-clip source not found among $seen candidates"
[[ "$(wc -c < "$SOURCE" | tr -d ' ')" == "$MODEL_SIZE" ]] || fail 'source size changed'
# Parse the actual GLB, not merely a filename or Three.js's sanitized names.
python3 - "$SOURCE" "$MODEL_SHA" <<'PY' || fail 'GLB skeleton or animation validation failed'
import sys,hashlib,json,struct
b=open(sys.argv[1],'rb').read()
assert hashlib.sha256(b).hexdigest()==sys.argv[2]
assert b[:4]==b'glTF' and struct.unpack_from('<I',b,8)[0]==len(b)
length,typ=struct.unpack_from('<I4s',b,12)
assert typ==b'JSON'
g=json.loads(b[20:20+length]); n=g['nodes']; lookup={x.get('name'):i for i,x in enumerate(n)}; parent={child:i for i,x in enumerate(n) for child in x.get('children',[])}
assert len(g['skins'][0]['joints'])==74 and len(g['animations'])==9
assert {'Idle_Turn_Left','Idle_Turn_Right'} <= {x['name'] for x in g['animations']}
for side,mid in [('Left','Bone_017'),('Right','Bone_013')]:
    names=['mixamorig:Hips','mixamorig:'+side+'UpLeg','mixamorig:'+side+'Leg',mid,'mixamorig:'+side+'Foot','mixamorig:'+side+'ToeBase']
    ids=[lookup[x] for x in names]
    assert all(i in g['skins'][0]['joints'] for i in ids)
    assert all(parent[b]==a for a,b in zip(ids,ids[1:])),names
print('SOURCE_VALIDATED=YES JOINTS=74 CLIPS=9 IDLE_TURNS=2')
PY
phase=author
mkdir -p "$DIR" campaigns
cp -- "$SOURCE" "$MODEL"
[[ "$(sha256sum "$MODEL" | cut -d' ' -f1)" == "$MODEL_SHA" ]] || fail 'copied source mismatch'
cp -- "$0" "campaigns/$CAMPAIGN.sh"
cat > "$DIR/gait-extract.mjs" <<'JS'
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const SOURCE_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const expected=['Idle_Turn_Left','Idle_Turn_Right'];
const $=id=>document.getElementById(id);
const scene=new THREE.Scene();scene.background=new THREE.Color(0x151b25);
const camera=new THREE.PerspectiveCamera(38,1,.01,1000);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));$('stage').append(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x38445a,2.0));const key=new THREE.DirectionalLight(0xffffff,2.5);key.position.set(4,8,6);scene.add(key);
const grid=new THREE.GridHelper(20,20,0x778899,0x334455);scene.add(grid);
const V=()=>new THREE.Vector3();
const vec=a=>new THREE.Vector3(...a);
const rnd=x=>Number.isFinite(x)?+x.toFixed(6):null;
const xyz=v=>v.toArray().map(rnd);
const qyaw=q=>{const f=new THREE.Vector3(0,0,1).applyQuaternion(q);return Math.atan2(f.x,f.z)};
const degrees=r=>rnd(THREE.MathUtils.radToDeg(r));
const delta=(a,b)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
const quantile=(a,p)=>{if(!a.length)return null;const s=[...a].sort((x,y)=>x-y);return s[Math.floor((s.length-1)*p)]};
const distXZ=(a,b)=>Math.hypot(a[0]-b[0],a[2]-b[2]);
let root,clips,mixer,report=null,current=0,play=true,last=performance.now(),floorY=0,actions=[];
function findBone(name){const arr=[];root.traverse(o=>{if(o.isBone&&o.name===name)arr.push(o)});if(arr.length!==1)throw Error('UNIQUE_BONE_REQUIRED '+name+' count '+arr.length);return arr[0]}
function buildRig(){
 const hips=findBone('mixamorigHips');
 const legs={};for(const [side,mid] of [['left','Bone_017'],['right','Bone_013']]){
  const S=side==='left'?'Left':'Right';const names=[`mixamorig${S}UpLeg`,`mixamorig${S}Leg`,mid,`mixamorig${S}Foot`,`mixamorig${S}ToeBase`];
  const chain=names.map(findBone);if(chain[0].parent!==hips||chain.some((b,i)=>i&&b.parent!==chain[i-1]))throw Error('RIG_HIERARCHY_'+side);legs[side]={chain,ankle:chain[3],toe:chain[4]};
 }
 const upper=['mixamorigSpine','mixamorigSpine1','mixamorigSpine2','mixamorigNeck','mixamorigHead'].map(n=>{const arr=[];root.traverse(o=>{if(o.isBone&&o.name===n)arr.push(o)});return arr.length===1?arr[0]:null});
 return {hips,legs,upper,upperNames:upper.map((b,i)=>b?.name||null)};
}
function world(o){return xyz(o.getWorldPosition(V()))}
function quaternion(o){return o.getWorldQuaternion(new THREE.Quaternion())}
function skinnedWitnesses(rig){
 // Collect bounded skinned toe/sole witnesses by dominant skin influence.
 // If mesh influences cannot resolve unambiguously, mark sole evidence unavailable.
 const info={left:[],right:[]};const meshes=[];root.traverse(o=>{if(o.isSkinnedMesh&&o.geometry?.attributes?.skinIndex&&o.geometry?.attributes?.position)meshes.push(o)});
 for(const mesh of meshes){const skin=mesh.geometry.attributes.skinIndex, weight=mesh.geometry.attributes.skinWeight, pos=mesh.geometry.attributes.position;
  const inverse=new Map(mesh.skeleton.bones.map((b,i)=>[b,i]));
  for(const side of ['left','right']){
   const {ankle,toe}=rig.legs[side];const target=new Set([inverse.get(ankle),inverse.get(toe)]);
   if(target.has(undefined))continue;
   const candidates=[];
   for(let i=0;i<pos.count;i++){
    let bestW=0,bestI=-1;
    for(let k=0;k<4;k++){const w=weight.getComponent(i,k);if(w>bestW){bestW=w;bestI=skin.getComponent(i,k)}}
    if(target.has(bestI)&&bestW>=.5)candidates.push(i);
   }
   // Deterministic subsampling, preserves spatial coverage without large per-frame work.
   const limit=64,step=Math.max(1,Math.ceil(candidates.length/limit));for(let i=0;i<candidates.length;i+=step)info[side].push({mesh,index:candidates[i]});
  }
 }
 return {info,counts:Object.fromEntries(Object.entries(info).map(([s,a])=>[s,a.length])),meshCount:meshes.length};
}
function solePoints(witnesses){const out={};for(const side of ['left','right']){
 const pts=[];for(const {mesh,index} of witnesses.info[side]){
  const p=mesh.applyBoneTransform(index,V());mesh.localToWorld(p);pts.push(p);
 }
 if(!pts.length){out[side]=null;continue}
 pts.sort((a,b)=>a.y-b.y);const band=pts.slice(0,Math.max(3,Math.ceil(pts.length*.20)));
 const center=band.reduce((v,p)=>v.add(p),V()).multiplyScalar(1/band.length);
 out[side]={center:xyz(center),bottomY:rnd(pts[0].y),spreadY:rnd(pts.at(-1).y-pts[0].y)};
 }return out;
}
function sampleClip(clip,rig,witnesses){
 // Isolate each animation action so the previous clip cannot contaminate samples.
 mixer.stopAllAction();mixer.setTime(0);const action=mixer.clipAction(clip);action.reset().setLoop(THREE.LoopOnce,1).play();
 const count=Math.max(60,Math.ceil(clip.duration*60));const samples=[];
 for(let i=0;i<=count;i++){
  const t=clip.duration*i/count;mixer.setTime(t);root.updateMatrixWorld(true);
  const hips=world(rig.hips),hipQ=quaternion(rig.hips),hipYaw=qyaw(hipQ), sole=solePoints(witnesses);
  const upper=rig.upper.map(b=>b?{position:world(b),yaw:qyaw(quaternion(b))}:null);
  const feet={};for(const side of ['left','right']){
   const chain=rig.legs[side].chain.map(world);
   feet[side]={hip:chain[0],knee:chain[1],intermediate:chain[2],ankle:chain[3],toe:chain[4],ankleYaw:qyaw(quaternion(rig.legs[side].ankle)),sole:sole[side]};
  }
  samples.push({t:rnd(t),pelvis:hips,pelvisYaw:hipYaw,upper,feet});
 }
 action.stop();
 // Stable unwrap across -pi/+pi, maintaining signed accumulated rotation.
 const unwrapped=[];for(let i=0;i<samples.length;i++)unwrapped.push(i?unwrapped[i-1]+delta(samples[i].pelvisYaw,samples[i-1].pelvisYaw):0);
 const rotation=degrees(unwrapped.at(-1));const translation=xyz(vec(samples.at(-1).pelvis).sub(vec(samples[0].pelvis)));
 const upperTurns={};rig.upper.forEach((b,j)=>{if(!b)return;let v=0;const s=samples.map(x=>x.upper[j].yaw);for(let i=1;i<s.length;i++)v+=delta(s[i],s[i-1]);upperTurns[b.name]={worldYawDeltaDeg:degrees(v),relativeToPelvisDeg:degrees(v-unwrapped.at(-1))}});
 const feet={};for(const side of ['left','right']){
  const rows=samples.map(s=>s.feet[side]);const bottoms=rows.map(r=>r.sole?.bottomY).filter(x=>x!==undefined&&x!==null);const haveSole=bottoms.length===rows.length;
  const baseline=haveSole?quantile(bottoms,.08):null;
  const verticalRange=haveSole?quantile(bottoms,.95)-quantile(bottoms,.05):null;
  const tol=haveSole?Math.max(.005,verticalRange*.13):null;
  // Distinguish planted translating feet from turning pivots; label both heuristically.
  const velocities=[],rotRates=[];for(let i=1;i<rows.length;i++){
   const dt=samples[i].t-samples[i-1].t;
   const a=rows[i].sole?.center||rows[i].toe,b=rows[i-1].sole?.center||rows[i-1].toe;
   velocities.push(distXZ(a,b)/dt);rotRates.push(Math.abs(delta(rows[i].ankleYaw,rows[i-1].ankleYaw))/dt);
  }
  const speedThreshold=haveSole?Math.max(.015,(quantile(velocities,.25)||0)*1.35):null;
  const contact=[];let slides=0,angular=0,contactCount=0;const intervals=[];let start=null;
  for(let i=0;i<rows.length;i++){
   const near=haveSole&&rows[i].sole.bottomY-baseline<=tol;
   // Ground-near is evidence for potential support; speed is scored separately.
   const supported=Boolean(near);contact.push(supported);
   if(supported){contactCount++;if(start===null)start=i;if(i>0){slides+=distXZ(rows[i].sole.center,rows[i-1].sole.center);angular+=Math.abs(delta(rows[i].ankleYaw,rows[i-1].ankleYaw));}}
   else if(start!==null){intervals.push([samples[start].t,samples[i-1].t]);start=null}
  }
  if(start!==null)intervals.push([samples[start].t,samples.at(-1).t]);
  feet[side]={soleWitnessCount:witnesses.counts[side],evidence:haveSole?'SKINNED_VERTEX_WITNESSES_HEURISTIC':'UNAVAILABLE_NO_SKINNED_SOLE_WITNESSES',baselineSoleY:baseline,heightThreshold:tol,contactCandidateFraction:haveSole?rnd(contactCount/rows.length):null,groundNearIntervals:intervals,groundNearAccumulatedTravel:rnd(slides),groundNearAccumulatedFootYawDeg:degrees(angular),contactSpeedReference:speedThreshold,peakCenterHorizontalSpeed:rnd(Math.max(...velocities)),ankleYawDeltaDeg:degrees(rows.reduce((a,r,i)=>i?a+delta(r.ankleYaw,rows[i-1].ankleYaw):0,0)),note:'Support intervals are preliminary. Sole witnesses are sampled from skinned vertices, not verified contact patches; no measured world floor or force data.'};
  rows.forEach((r,i)=>{r.contactCandidate=contact[i];r.horizontalSpeed=i?rnd(velocities[i-1]):null});
 }
 return {name:clip.name,duration:rnd(clip.duration),samples:samples.length,pelvisTranslation:translation,pelvisYawDeltaDeg:rotation,pelvisYawPathDeg:degrees(unwrapped.reduce((sum,v,i)=>i?sum+Math.abs(v-unwrapped[i-1]):0,0)),upperTurns,feet,classification:/Idle_Turn/i.test(clip.name)?'IDLE_TURN_REFERENCE':'LOCOMOTION_REFERENCE',sourceFrame:'world +Y up, +Z reference forward; yaw around world Y, positive toward +X',cautions:['Pelvis is a joint, not proven independent root-motion transform','Ground/support identification is heuristic; check actual mesh contact and floor','Turn clip is reference motion, not an implemented aim controller'],tracks:samples};
}
function summary(r){return {clip:r.name,duration:r.duration,pelvisYawDeg:r.pelvisYawDeltaDeg,pelvisTravelXZ:rnd(Math.hypot(r.pelvisTranslation[0],r.pelvisTranslation[2])),chestYawRelDeg:r.upperTurns.mixamorigSpine2?.relativeToPelvisDeg??null,leftGroundNear:r.feet.left.contactCandidateFraction,rightGroundNear:r.feet.right.contactCandidateFraction,leftFootTravel:r.feet.left.groundNearAccumulatedTravel,rightFootTravel:r.feet.right.groundNearAccumulatedTravel}}
function renderTable(){const body=$('table');body.textContent='';for(const x of report.summary){const tr=document.createElement('tr');for(const k of ['clip','duration','pelvisYawDeg','pelvisTravelXZ','chestYawRelDeg','leftGroundNear','rightGroundNear']){const td=document.createElement('td');td.textContent=x[k]??'unknown';tr.append(td)}body.append(tr)}}
function save(name,obj){const url=URL.createObjectURL(new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),3000)}
function draw(){const now=performance.now();if(mixer&&play)mixer.update(Math.min((now-last)/1000,.05));last=now;renderer.render(scene,camera);requestAnimationFrame(draw)}requestAnimationFrame(draw);
function size(){const width=Math.max(300,$('stage').clientWidth),height=Math.round(width*.65);renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix()}addEventListener('resize',size);
function select(i){current=i;mixer.stopAllAction();mixer.setTime(0);mixer.clipAction(clips[i]).reset().play();$('clip').value=String(i);$('detail').textContent=JSON.stringify(summary(report.clips[i]),null,2)}
$('play').onclick=()=>{play=!play;$('play').textContent=play?'Pause':'Play'};
$('clip').onchange=e=>select(+e.target.value);
$('export').onclick=()=>report&&save('hareworks-nine-clip-gait-and-idle-turn-v1.0.8.json',report);
$('turnleft').onclick=()=>select(clips.findIndex(c=>c.name==='Idle_Turn_Left'));
$('turnright').onclick=()=>select(clips.findIndex(c=>c.name==='Idle_Turn_Right'));
try{
 $('status').textContent='Loading nine-clip rig and skinned surfaces…';const gltf=await new GLTFLoader().loadAsync('../../../assets/hareworks/Hareworks-nine-clips.glb');root=gltf.scene;scene.add(root);clips=gltf.animations;
 if(clips.length!==9||expected.some(n=>!clips.find(c=>c.name===n)))throw Error('NINE_CLIP_SET_MISMATCH');
 mixer=new THREE.AnimationMixer(root);const rig=buildRig();const witnesses=skinnedWitnesses(rig);
 if(!witnesses.counts.left||!witnesses.counts.right)throw Error('MISSING_SKINNED_FOOT_WITNESSES');
 const bbox=new THREE.Box3().setFromObject(root);const center=bbox.getCenter(V()),sz=bbox.getSize(V());floorY=bbox.min.y;grid.position.y=floorY;
 camera.position.set(center.x+sz.x*2+1,center.y+sz.y*1.4+1,center.z+sz.z*2+2);camera.lookAt(center);
 report={schema:'hareworks-gait-and-idle-turn-v1.0.8',sourceSha256:SOURCE_SHA,computedInBrowserAt:new Date().toISOString(),rig:{jointCount:74,upperBones:rig.upperNames,legChains:Object.fromEntries(Object.entries(rig.legs).map(([s,v])=>[s,v.chain.map(b=>b.name)])),skinnedWitnesses:witnesses.counts},coordinates:'GLTF world space, +Y up, +Z heading convention; root translation cannot be inferred from pelvis alone',idleAimDesign:{status:'PROPOSED_NOT_IMPLEMENTED',inputs:['movement vector','world aim angle','last planted stance','turn rate','torso twist limit'],plan:['When moving, let gait heading and aim heading be measured independently','When stopped, maintain planted support until upper-body twist budget is reached','Use measured left/right idle turn clips to estimate step direction, pivot foot, pelvis yaw and stance transfer','Trigger a deliberate foot reposition when the torso/hip twist budget is exceeded','Blend upper-body aiming independently from footstep progression; never rotate planted feet through the ground'],calibration:'Derive thresholds from user-approved visual review after measurements. No arbitrary accepted degrees.'},notes:['Measured source clips, NOT procedural IK or implemented aim input','Uniform ~60 Hz clip sampling; endpoint may reflect loop discontinuity','Sole witnesses approximate weighted foot vertices, not full outsole/contact mechanics','World yaw path unwrapped to avoid modulo 360 aliasing'],clips:[]};
 for(const clip of clips){$('status').textContent='Extracting '+clip.name;report.clips.push(sampleClip(clip,rig,witnesses));const opt=document.createElement('option');opt.value=String($('clip').length);opt.textContent=clip.name;$('clip').append(opt)}
 report.summary=report.clips.map(summary);renderTable();select(0);size();$('status').textContent='All nine clips analyzed. Idle left/right turn deltas, upper twist, sole witnesses and tentative support exported. Visual approval pending.';
}catch(e){$('status').textContent='BLOCKED '+e.message;console.error(e)}
JS
cat > "$DIR/index.html" <<'HTML'
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hareworks: gait + idle turning v1.0.8</title><script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script><style>body{margin:0;background:#111824;color:#f0f2f5;font:16px system-ui}main{max-width:1100px;margin:auto;padding:14px}button,select{font:inherit;color:#fff;background:#303e50;padding:9px;margin:4px;border:1px solid #657b8d;border-radius:5px}button:focus-visible,select:focus-visible{outline:3px solid #fbbf24}#stage{width:100%;border:1px solid #657b8d}table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:8px;border-bottom:1px solid #39495b;text-align:left}section{overflow-x:auto}pre{white-space:pre-wrap}small{color:#afbecd}</style></head><body><main><h2>Hareworks · gait and idle turning v1.0.8</h2><p id="status" role="status" aria-live="polite">Starting extraction…</p><div id="stage" aria-label="Animated original 3D Hareworks model"></div><label for="clip">Reference motion</label><select id="clip"></select><button id="play">Pause</button><button id="turnleft">Inspect left idle turn</button><button id="turnright">Inspect right idle turn</button><button id="export">Export nine-clip measurements JSON</button><p><small>Idle aim controller is a design proposal, not installed IK. Ground contact remains a skinned-vertex heuristic, not proven physical support. Both turn clips retain their original animation and are measured separately.</small></p><section><table><thead><tr><th>Clip</th><th>Seconds</th><th>Pelvis yaw °</th><th>Travel XZ</th><th>Chest rel °</th><th>L near ground</th><th>R near ground</th></tr></thead><tbody id="table"></tbody></table></section><h3>Selected clip summary</h3><pre id="detail"></pre></main><script type="module" src="./gait-extract.mjs"></script></body></html>
HTML
cat > "$DIR/README.md" <<'MD'
# Hareworks nine-clip gait and idle-turn archaeology v1.0.8

Reads the *unchanged* 6,784,896-byte Hareworks nine-clip source. Browser samples nine clips, including `Idle_Turn_Left` and `Idle_Turn_Right`, at ~60 Hz, with precise skeletal chains and bounded skinned-foot vertex witnesses. Reports pelvis world yaw unwrapped across 360°, pelvis displacement (not falsely named root motion), upper/chest turn relative to pelvis, ankle yaw, approximate ground-near intervals, foot-ground travel and exportable tracks. Uses separate clip-action reset for each pass. All contact labels remain **heuristic**. No IK or aim controller is claimed to be implemented; report includes proposed idle aiming turn-and-step behavior requiring visual calibration.

The animated viewer is served by local Termux HTTP from the isolated checkout and requires internet to load Three.js from its pinned CDN version. Browser export must be tapped to persist analysis JSON on Android. Viewer HTTP success does not prove browser WebGL or extraction success; owner visual and JSON review are separate gates. Do not confuse v1.0.7's interrupted local LFS copy with a GitHub asset.
MD
python3 - "$DIR/contract.json" "$BASE" "$MODEL_SHA" <<'PY'
import json,sys
p,base,sha=sys.argv[1:]
with open(p,'w') as f:json.dump(dict(campaign='hareworks-gait-extraction-v1.0.8',sourceCommit=base,modelSha256=sha,repo='Valar05/parametric-parambulator',ownerLane='Android Termux Git only',immutable=['assets/repl/Repl.glb','assets/hareworks/Hareworks.glb','AGENTS.md'],newOutputs=['assets/hareworks/Hareworks-nine-clips.glb','tools/hareworks-gait-extraction/v1.0.8/*','campaigns/hareworks-gait-extraction-v1.0.8.sh'],turnClips=['Idle_Turn_Left','Idle_Turn_Right'],acceptance=['remote readback','browser JSON export','owner visual verdict']),f,indent=2)
PY
phase=validate
# Verify syntax of BOTH produced source languages; real browser and skinned asset still require device validation.
if command -v node >/dev/null; then node --check "$DIR/gait-extract.mjs" || fail 'JS syntax'; else echo 'JS_SYNTAX_CHECK_UNAVAILABLE=node absent'; fi
python3 - "$DIR" "$MODEL" <<'PY' || fail 'static extract assertions'
from pathlib import Path
import sys
p=Path(sys.argv[1]);js=(p/'gait-extract.mjs').read_text();html=(p/'index.html').read_text()
for s in ['Idle_Turn_Left','Idle_Turn_Right','applyBoneTransform','pelvisYawDeltaDeg','relativeToPelvisDeg','groundNearAccumulatedTravel','idleAimDesign','UNAVAILABLE_NO_SKINNED_SOLE_WITNESSES']:
 assert s in js,s
for i in ['clip','export','table','detail','turnleft','turnright','status','stage','play']:
 assert f'id="{i}"' in html,i
assert len(Path(sys.argv[2]).read_bytes())==6784896
print('STATIC_CONTRACT=PASS')
PY
[[ "$(git rev-parse HEAD:AGENTS.md)" == "$AGENTS_BLOB" && "$(git rev-parse HEAD:assets/repl/Repl.glb)" == "$REPL_BLOB" && "$(git rev-parse HEAD:assets/hareworks/Hareworks.glb)" == "$OLD_HARE_BLOB" ]] || fail 'protected canonical blobs changed'
phase=publish
paths=("$MODEL" "$DIR/index.html" "$DIR/gait-extract.mjs" "$DIR/README.md" "$DIR/contract.json" "campaigns/$CAMPAIGN.sh")
git add -- "${paths[@]}"
python3 - "${paths[@]}" <<'PY' || fail 'path check'
import subprocess,sys
wanted=set(sys.argv[1:]);actual=set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines())
assert wanted==actual,(wanted,actual)
print('STAGED_EXACT_PATHS=YES',len(actual))
PY
git -c user.name='Hareworks Termux Campaign' -c user.email='hareworks-campaign@users.noreply.github.com' commit -m 'Hareworks nine-clip gait and idle-turn extraction v1.0.8' || fail 'commit failed'
COMMIT=$(git rev-parse HEAD)
# git-lfs pre-push hook must upload the exact binary before Git ref publication.
git lfs install --local || fail 'cannot install LFS pre-push hook'
git lfs ls-files | grep -Fq "$MODEL" || fail 'new model not registered in Git LFS'
git push origin HEAD:refs/heads/main || fail "push failed; commit preserved $COMMIT"
phase=readback
remote=$(git ls-remote origin refs/heads/main | cut -f1)
[[ "$remote" == "$COMMIT" ]] || fail "remote main differs $remote vs $COMMIT"
GIT_LFS_SKIP_SMUDGE=1 git fetch --depth=1 origin main || fail 'remote fetch failed'
[[ "$(git rev-parse FETCH_HEAD)" == "$COMMIT" ]] || fail 'remote commit readback differs'
for entry in "${paths[@]}"; do
 if [[ "$entry" == "$MODEL" ]]; then
   ptr=$(git show "FETCH_HEAD:$MODEL")
   grep -Fq "oid sha256:$MODEL_SHA" <<<"$ptr" || fail 'remote LFS sha mismatch'
   grep -Fq "size $MODEL_SIZE" <<<"$ptr" || fail 'remote LFS byte count mismatch'
 else
   [[ "$(git show "FETCH_HEAD:$entry" | sha256sum | cut -d' ' -f1)" == "$(sha256sum "$entry" | cut -d' ' -f1)" ]] || fail "remote file differs $entry"
 fi
done
[[ "$(git rev-parse FETCH_HEAD:assets/repl/Repl.glb)" == "$REPL_BLOB" && "$(git rev-parse FETCH_HEAD:assets/hareworks/Hareworks.glb)" == "$OLD_HARE_BLOB" ]] || fail 'remote canonical regression'
phase=viewer
PORT=0
for p in 8765 8766 8767 8768 8769; do if ! (echo >/dev/tcp/127.0.0.1/$p) >/dev/null 2>&1; then PORT=$p;break;fi;done
((PORT>0)) || fail 'no available local viewer port'
cat > "$STATE/server.py" <<'PY'
import http.server,sys
class Server(http.server.SimpleHTTPRequestHandler):
 def end_headers(self):
  self.send_header('Cache-Control','no-store')
  super().end_headers()
http.server.ThreadingHTTPServer(('127.0.0.1',int(sys.argv[1])),Server).serve_forever()
PY
nohup python3 "$STATE/server.py" "$PORT" >"$STATE/server.log" 2>&1 </dev/null &
PID=$!
ready=0
for i in 1 2 3 4 5 6 7 8; do
 if curl -fsS "http://127.0.0.1:$PORT/$DIR/index.html" >/dev/null && curl -fsS "http://127.0.0.1:$PORT/$DIR/gait-extract.mjs" >/dev/null;then ready=1;break;fi
 sleep 1
done
((ready==1)) && kill -0 "$PID" || fail 'viewer HTTP server failed'
URL="http://127.0.0.1:$PORT/$DIR/index.html?commit=$COMMIT"
python3 - "$STATE/receipt.json" "$CAMPAIGN" "$BASE" "$COMMIT" "$AGENTS_BLOB" "$REPL_BLOB" "$MODEL_SHA" "$URL" "$PID" <<'PY'
import json,sys,datetime
p,c,base,commit,agents,repl,model,url,pid=sys.argv[1:]
with open(p,'w') as f:json.dump(dict(campaign=c,phase='viewer_http_ready',timestampUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sourceCommit=base,publishedCommit=commit,agentsBlob=agents,canonicalReplGitBlob=repl,nineClipModelSha256=model,rulesRead={'repositoryAgents':'pinned Git source','campaignEtiquette':'Home Center live document 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI; author fetched 2026-11-20','topDownEtiquette':'Home Center live document 1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU; author fetched 2026-11-20'},viewerUrl=url,viewerPid=int(pid),browserAnalysisComplete=False,ownerVisualAcceptance=False),f,indent=2)
PY
echo "REMOTE_COMMIT=$COMMIT"
echo "VIEWER_URL=$URL"
echo "RECEIPT=$STATE/receipt.json"
echo 'BROWSER_MEASUREMENTS_PENDING=YES; OPEN VIEWER THEN EXPORT JSON'
termux-open-url "$URL" || echo 'VIEWER_OPEN_FAILED=YES; use VIEWER_URL above'
