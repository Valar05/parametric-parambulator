#!/data/data/com.termux/files/usr/bin/bash
# Focused, owner-reviewable forward Woman leg proof. Termux Git only.
# Preserves all source GLBs. No backward/strafe/turn/aim implementation.
set -Eeuo pipefail
CAMPAIGN='hareworks-forward-woman-proof-v0.1.1'
REPO='Valar05/parametric-parambulator'
BASE='323a847157fbdedb75e603ad8db2f0d0a8b0eca8'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_BYTES='6784896'
DIR='tools/hareworks-forward-woman/v0.1.1'
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
LOG="$STATE/run.log"
exec > >(tee -a "$LOG") 2>&1
phase='preflight'
fail(){
  echo "BLOCKED step=$phase reason=$*"
  python3 - "$STATE/blocked.json" "$CAMPAIGN" "$phase" "$*" <<'PY' || true
import json,sys,datetime
from pathlib import Path
out,campaign,step,reason=sys.argv[1:]
Path(out).write_text(json.dumps({'campaign':campaign,'phase':'blocked','step':step,'reason':reason,'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY
  exit 1
}
if [[ "${1:-run}" == status ]]; then
  [[ -f "$STATE/receipt.json" ]] || fail 'receipt does not exist; script has not started a verified viewer'
  cat "$STATE/receipt.json"
  exit 0
fi
[[ "${1:-run}" == run ]] || fail 'usage: bash script.sh [run|status]'
for c in git python3 sha256sum curl;do command -v "$c" >/dev/null || fail "missing dependency $c; new Termux workspace needs it";done
hash(){ sha256sum -- "$1" | cut -d' ' -f1; }
ORIGIN="https://github.com/$REPO.git"
REMOTE=$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1) || fail 'cannot read remote main'
[[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] || fail 'Git remote returned invalid commit identifier'
echo "REMOTE_MAIN=$REMOTE"
ROOT=$(mktemp -d "$STATE/snapshot.XXXXXXXX") || fail 'cannot reserve new isolated snapshot'
WORK="$ROOT/repo"
# Clone into a NEW subdirectory, never into an occupied or dirty checkout.
GIT_LFS_SKIP_SMUDGE=1 git -c lfs.install.skip=true clone --depth=1 --filter=blob:none --no-checkout --single-branch --branch main "$ORIGIN" "$WORK" || fail 'safe shallow clone failed'
git -C "$WORK" sparse-checkout init --cone || fail 'sparse checkout initialization failed'
git -C "$WORK" sparse-checkout set assets/hareworks tools/hareworks-forward-woman campaigns || fail 'sparse paths failed'
GIT_LFS_SKIP_SMUDGE=1 git -C "$WORK" checkout -B "$CAMPAIGN" "$REMOTE" || fail 'bounded sparse checkout failed'
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$REMOTE" ]] || fail 'pinned checkout mismatch'
cd "$WORK"
[[ -f AGENTS.md ]] && grep -Fq 'Termux Git only' AGENTS.md || fail 'pinned AGENTS.md rules unreadable'
AGENTS_BLOB=$(git rev-parse 'HEAD:AGENTS.md')
REPL_BLOB=$(git rev-parse 'HEAD:assets/repl/Repl.glb')
OLD_HARE_BLOB=$(git rev-parse 'HEAD:assets/hareworks/Hareworks.glb')
[[ "$AGENTS_BLOB" == '547c2af52303f4efb718bbf8f82a698110c7bfca' ]] || fail 'AGENTS.md changed from audited repository revision'
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_BYTES" <<'PY' || fail 'published nine-clip pointer changed'
import subprocess,sys
path,oid,size=sys.argv[1:]
p=subprocess.check_output(['git','show','HEAD:'+path])
assert p==f'version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize {size}\n'.encode()
print('EXACT_PUBLISHED_SOURCE_POINTER=PASS')
PY
phase='collision-check'
# All new paths must be absent on the pinned baseline, but after a successful
# publication this same campaign may safely relaunch the viewer from the
# exact recorded remote content instead of attempting another Git commit.
FILES=("$DIR/index.html" "$DIR/viewer.mjs" "$DIR/gait-kernel.mjs" "$DIR/profile.json" "$DIR/reference-legs.json" "$DIR/kinematics-test.mjs" "$DIR/README.md" "campaigns/$CAMPAIGN.sh")
PUBLISHED=0
if [[ "$REMOTE" == "$BASE" ]]; then
  for f in "${FILES[@]}"; do
    [[ ! -e "$f" && ! -L "$f" ]] && ! git cat-file -e "HEAD:$f" 2>/dev/null || fail "destination collision $f"
  done
else
  if git cat-file -e "HEAD:${FILES[0]}" 2>/dev/null && git cat-file -e "HEAD:campaigns/$CAMPAIGN.sh" 2>/dev/null;then
    PUBLISHED=1
    echo "REMOTE_ALREADY_CONTAINS_CANDIDATE=$REMOTE; verifying every published byte before reopening"
  else
    fail "remote main advanced beyond audited $BASE without this campaign; do not change current owner work"
  fi
fi
phase='materialize-source'
SOURCE=''
for base in "$HOME/.local/state/hareworks" "$HOME/storage/downloads" /storage/emulated/0/Download;do
  [[ -d "$base" ]] || continue
  if [[ "$base" == "$HOME/.local/state/hareworks" ]];then
    while IFS= read -r -d '' candidate;do
      [[ "$(wc -c < "$candidate" | tr -d ' ')" == "$MODEL_BYTES" ]] || continue
      if [[ "$(hash "$candidate")" == "$MODEL_SHA" ]];then SOURCE="$candidate";break;fi
    done < <(find "$base" -maxdepth 9 -type f -name 'Hareworks-nine-clips.glb' -print0 2>/dev/null)
  else
    while IFS= read -r -d '' candidate;do
      [[ "$(wc -c < "$candidate" | tr -d ' ')" == "$MODEL_BYTES" ]] || continue
      if [[ "$(hash "$candidate")" == "$MODEL_SHA" ]];then SOURCE="$candidate";break;fi
    done < <(find -L "$base" -maxdepth 1 -type f -name '*.glb' -print0 2>/dev/null)
  fi
  [[ -z "$SOURCE" ]] || break
done
if [[ -z "$SOURCE" ]];then
  command -v git-lfs >/dev/null || fail 'exact source missing and git-lfs unavailable to fetch its published object'
  echo 'EXACT_MODEL_NOT_LOCAL=YES fetching only published nine-clip GLB object, not historical LFS assets'
  git lfs install --local || fail 'git-lfs setup failed'
  GIT_LFS_SKIP_SMUDGE=1 git lfs fetch -I "$MODEL" -X '' origin "$REMOTE" || fail 'exact object fetch failed'
  OBJ=$(git rev-parse --git-path "lfs/objects/${MODEL_SHA:0:2}/${MODEL_SHA:2:2}/$MODEL_SHA")
  [[ -f "$OBJ" ]] || fail 'exact LFS object missing after fetch'
  SOURCE="$OBJ"
fi
[[ "$(wc -c < "$SOURCE" | tr -d ' ')" == "$MODEL_BYTES" && "$(hash "$SOURCE")" == "$MODEL_SHA" ]] || fail 'verified asset bytes do not match owner source'
echo "EXACT_MODEL_AVAILABLE=YES $MODEL_SHA"
python3 - "$SOURCE" <<'PY' || fail 'actual nine-clip GLB header/skin/clip check failed'
import json,struct,sys
b=open(sys.argv[1],'rb').read();assert b[:4]==b'glTF';assert struct.unpack_from('<I',b,8)[0]==len(b)
n,typ=struct.unpack_from('<I4s',b,12);assert typ==b'JSON';g=json.loads(b[20:20+n]);names=[a.get('name') for a in g['animations']]
assert len(g['skins'][0]['joints'])==74 and len(names)==9 and 'Walking_Woman' in names
print('ACTUAL_SOURCE_RIG=PASS 74 joint skin / 9 clips / Walking_Woman')
PY
phase='write-packet'
if ((PUBLISHED==0));then
  mkdir -p "$DIR" campaigns
  cat > "$DIR/index.html" <<'__HAREWORKS_FW_V011_0__'
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#101821"><title>Hareworks Woman Forward Leg Proof v0.1.1</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>
:root{font:15px system-ui,sans-serif;color:#eff4ff;background:#101821;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:1100px;margin:auto;padding:12px}h1{font-size:20px;margin:4px 0}p{line-height:1.42}#status{padding:10px 0;min-height:43px;color:#aee5d5}#stage{width:100%;background:#0b121a;border:1px solid #52697d;border-radius:10px;overflow:hidden}#stage canvas{width:100%;display:block;touch-action:none}header{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px}.label{display:inline-block;background:#243748;padding:5px 8px;border-radius:20px;font-size:11px}.panes{display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:12px;color:#b5d7ec;text-align:center;margin:5px 0}.controls{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}button{border:1px solid #667f95;color:white;background:#294054;border-radius:8px;padding:10px 12px;min-height:42px;font:inherit}button:focus-visible{outline:3px solid #80d7ee}#measure{white-space:pre-wrap;padding:9px;background:#192a37;border:1px solid #3b536a;border-radius:6px;font:12px ui-monospace,monospace}small{color:#adbacb}code{overflow-wrap:anywhere}@media(max-width:550px){main{padding:8px}h1{font-size:17px}.label{font-size:10px}}
</style></head><body><main>
<header><h1>🐇 Hareworks · Woman Walk Leg Proof</h1><span class="label">v0.1.1 · forward only · 30 fps</span></header>
<p>One animation supplies the <strong>reference</strong>. A separate copy of the same skinned GLB uses <strong>generated ankle targets + analytic two-link knee IK</strong>. The procedural side borrows source pelvis/hip motion and source ankle orientation to isolate leg-geometry correctness. The audition plays one reference cycle at a time so a potentially discontinuous clip endpoint is not disguised as a valid seamless gait.</p>
<div class="panes"><strong>Left: original Walking_Woman</strong><strong>Right: generated legs, same rig</strong></div>
<div id="status" role="status" aria-live="polite">Preparing exact source model…</div>
<div id="stage" aria-label="Two synchronized Hareworks 3D characters, reference left and procedural forward leg geometry right"></div>
<div id="measure" aria-live="off">Awaiting joint measurements…</div>
<div class="controls"><button id="play">Play</button><button id="prev">Previous frame</button><button id="next">Next frame</button><button id="review">Run 30 fps rig check</button><button id="markers">Show/hide ankle markers</button><button id="export">Export joint evidence JSON</button></div>
<p><strong>Reject this candidate if:</strong> the right character's legs visibly pop, twist unnaturally, lose silhouette, or fail to land ahead of the hips, or if its ankles disagree significantly with the reference. Tests report actual joint positions, not decorative foot markers. This is still not a planted-world-foot walking controller.</p>
<small>Source clip: <code>Walking_Woman</code>, 0.967 s; model SHA <code>a0e0c757…2aec6</code>. Original nine-clip GLB and all existing models remain unchanged. Three.js requires internet on first load. Visual acceptance is exclusively the owner's verdict.</small>
</main><script type="module" src="./viewer.mjs"></script></body></html>
__HAREWORKS_FW_V011_0__
  cat > "$DIR/viewer.mjs" <<'__HAREWORKS_FW_V011_1__'
/* Hareworks v0.1.1: forward-only skinned-leg comparison, NOT generalized locomotion. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {trajectory,worldOffset} from './gait-kernel.mjs';
const $=id=>document.getElementById(id);
const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const Q=()=>new THREE.Quaternion();
const SOURCE='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const EPS=1e-8, PARENT_OFFSET=2.75;
const boneNames={
 left:['mixamorigLeftUpLeg','mixamorigLeftLeg','Bone_017','mixamorigLeftFoot','mixamorigLeftToeBase'],
 right:['mixamorigRightUpLeg','mixamorigRightLeg','Bone_013','mixamorigRightFoot','mixamorigRightToeBase']
};
const toDegrees=x=>x*180/Math.PI;
function world(b){return b.getWorldPosition(V())}
function wq(b){return b.getWorldQuaternion(Q())}
function pelvisYaw(b){const f=V(0,0,1).applyQuaternion(wq(b));return Math.atan2(f.x,f.z)}
function getRig(model){
 const bones=new Map();model.traverse(o=>{if(o.isBone){if(bones.has(o.name))throw Error('DUPLICATE_BONE '+o.name);bones.set(o.name,o)}});
 if(bones.size!==74)throw Error('EXPECTED_74_BONES got '+bones.size);
 const hips=bones.get('mixamorigHips');if(!hips)throw Error('HIPS_MISSING');
 const legs={};
 for(const [side,names] of Object.entries(boneNames)){
  const c=names.map(n=>{const b=bones.get(n);if(!b)throw Error('BONE_MISSING '+n);return b});
  if(c[0].parent!==hips||c.some((b,i)=>i&&b.parent!==c[i-1]))throw Error('BONE_CHAIN_MISMATCH '+side);
  legs[side]={up:c[0],knee:c[1],mid:c[2],ankle:c[3],toe:c[4],chain:c};
 }
 return {hips,legs};
}
function fromToBone(bone,point,desired){
 const pivot=world(bone),actual=point.clone().sub(pivot),want=desired.clone().sub(pivot);
 if(actual.lengthSq()<EPS||want.lengthSq()<EPS)throw Error('ZERO_LENGTH_SOLVER');
 const delta=Q().setFromUnitVectors(actual.normalize(),want.normalize());
 const parentInv=wq(bone.parent).invert();
 bone.quaternion.copy(parentInv.multiply(delta).multiply(wq(bone))).normalize();
}
function analyticKnee(H,A,L1,L2,poleLocal,yaw){
 const axis=A.clone().sub(H),d=axis.length();
 if(d>L1+L2-.003||d<Math.abs(L1-L2)+.003)throw Error('UNREACHABLE_TARGET '+d.toFixed(5)+' lengths '+(L1+L2).toFixed(5));
 axis.divideScalar(d);
 const a=(L1*L1-L2*L2+d*d)/(2*d),rad=Math.sqrt(Math.max(0,L1*L1-a*a));
 const pw=V(...poleLocal).applyAxisAngle(V(0,1,0),yaw);
 const perp=pw.addScaledVector(axis,-pw.dot(axis));
 if(perp.lengthSq()<EPS)throw Error('POLE_SINGULARITY');perp.normalize();
 return H.clone().addScaledVector(axis,a).addScaledVector(perp,rad);
}

const scene=new THREE.Scene();scene.background=new THREE.Color('#101821');
scene.add(new THREE.HemisphereLight(0xd9e4ff,0x30303c,2.5));const sunlight=new THREE.DirectionalLight(0xffffff,3.2);sunlight.position.set(-4,7,3);scene.add(sunlight);
const grid=new THREE.GridHelper(9,18,0x59727e,0x344553);scene.add(grid);
const camera=new THREE.OrthographicCamera(-3.6,3.6,1.9,-1.9,.05,120);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
$('stage').append(renderer.domElement);
function resize(){const w=$('stage').clientWidth,h=Math.max(260,Math.min(570,w*.68));renderer.setSize(w,h,false);camera.left=-3.4*w/h/2;camera.right=-camera.left;camera.top=1.9;camera.bottom=-1.9;camera.updateProjectionMatrix()}
window.addEventListener('resize',resize);
camera.position.set(-7,3.3,0);camera.lookAt(0,1,0);
let reference,generated,refRig,genRig,refMixer,genMixer,sourceClip,profile;
let active=false,playing=true,frame=0,last=performance.now(),accumulator=0,metrics=[],debug=true;
let markers=[];
function buildMarkers(rig,color){for(const side of ['left','right']){const m=new THREE.Mesh(new THREE.SphereGeometry(.025,10,8),new THREE.MeshBasicMaterial({color:color[side],depthTest:false}));m.renderOrder=50;scene.add(m);markers.push({rig,side,m})}}
function validateProfile(){if(profile.modelSha256!==SOURCE||profile.clip!=='Walking_Woman')throw Error('PROFILE_SOURCE_MISMATCH');}
function sample(t){
 refMixer.setTime(t);genMixer.setTime(t);
 reference.updateMatrixWorld(true);generated.updateMatrixWorld(true);
 const output=[];
 for(const side of ['left','right']){
  const ref=refRig.legs[side],leg=genRig.legs[side],p=profile[side],yaw=pelvisYaw(genRig.hips);
  const H=world(leg.up),f=trajectory(t,profile,side);
  // Standard Three.js R_y: local forward +Z maps to (+sin(yaw), 0, +cos(yaw)).
  const offset=V(...worldOffset(f,yaw,H.y));
  const A=H.clone().add(offset),L1=world(leg.up).distanceTo(world(leg.knee)),L2=world(leg.knee).distanceTo(world(leg.ankle));
  if(Math.abs(L1-p.upperLength)>.009||Math.abs(L2-p.lowerLength)>.009)throw Error('SOURCE_RIG_LINK_LENGTH_MISMATCH '+side+' '+L1+' '+L2);
  const K=analyticKnee(H,A,L1,L2,p.pole,yaw);
  // Direct two-link solve, not iterative CCD, and no previous-frame solver state.
  // Intermediate and toe bone local bind transforms are preserved.
  const actualK=world(leg.knee);fromToBone(leg.up,actualK,K);generated.updateMatrixWorld(true);
  fromToBone(leg.knee,world(leg.ankle),A);generated.updateMatrixWorld(true);
  // Foot orientation intentionally BORROWED from source during this isolated leg geometry proof.
  leg.ankle.quaternion.copy(wq(leg.ankle.parent).invert().multiply(wq(ref.ankle)));
  generated.updateMatrixWorld(true);
  const reached=world(leg.ankle),knee=world(leg.knee),sourceK=world(ref.knee).add(V(0,0,PARENT_OFFSET)),sourceA=world(ref.ankle).add(V(0,0,PARENT_OFFSET));
  const residual=reached.distanceTo(A),kneeError=knee.distanceTo(sourceK),ankleError=reached.distanceTo(sourceA);
  const kneeh=world(leg.up).distanceTo(knee),kneel=knee.distanceTo(reached);
  if(![residual,kneeError,ankleError,kneeh,kneel].every(Number.isFinite))throw Error('NONFINITE_SOLUTION');
  if(residual>.012)throw Error('IK_TARGET_RESIDUAL_'+side+'='+residual.toFixed(5));
  if(Math.abs(kneeh-L1)>.001||Math.abs(kneel-L2)>.001)throw Error('BONE_LENGTH_CHANGED');
  output.push({side,t,relativeForward:f.z,ankleResidual:residual,ankleDifferenceToReference:ankleError,kneeDifferenceToReference:kneeError,
   hipWorld:H.toArray(),kneeWorld:knee.toArray(),ankleWorld:reached.toArray(),footOrientationSource:'reference clip quaternion (isolated leg proof)'});
 }
 for(const {rig,side,m} of markers){m.position.copy(world(rig.legs[side].ankle));m.visible=debug}
 return output;
}
function resetLegs(){
 for(const side of ['left','right'])for(const b of genRig.legs[side].chain)b.quaternion.copy(b.userData.seedQuat);
 generated.updateMatrixWorld(true);
}
function tick(){
 if(!active)return;
 const t=(frame/30)%sourceClip.duration;
 resetLegs();
 try{
  const o=sample(t);
  $('measure').textContent=`frame ${frame} · ${t.toFixed(3)}s  |  Left +Z ${o[0].relativeForward.toFixed(3)} / IK ${o[0].ankleResidual.toFixed(4)}  |  Right +Z ${o[1].relativeForward.toFixed(3)} / IK ${o[1].ankleResidual.toFixed(4)}`;
  if(metrics.length<600)metrics.push(o);
 }catch(e){playing=false;$('play').textContent='Play';$('status').textContent='BLOCKED_REAL_RIG '+e.message;console.error(e)}
 renderer.render(scene,camera);
}
function animate(now){requestAnimationFrame(animate);const dt=Math.min(.08,(now-last)/1000);last=now;if(playing&&active){accumulator+=dt;if(accumulator>=1/30){const steps=Math.min(2,Math.floor(accumulator*30));accumulator-=steps/30;frame+=steps;if(frame>=Math.round(sourceClip.duration*30)-1){frame=Math.round(sourceClip.duration*30)-1;playing=false;$('play').textContent='Replay cycle'}tick()}}}
requestAnimationFrame(animate);
$('play').onclick=()=>{if(!playing&&frame>=Math.round(sourceClip.duration*30)-1){frame=0;accumulator=0}playing=!playing;$('play').textContent=playing?'Pause':'Play'};
$('next').onclick=()=>{playing=false;$('play').textContent='Play';frame=(frame+1)%Math.round(sourceClip.duration*30);tick()};
$('prev').onclick=()=>{playing=false;$('play').textContent='Play';frame=(frame-1+Math.round(sourceClip.duration*30))%Math.round(sourceClip.duration*30);tick()};
$('markers').onclick=()=>{debug=!debug;tick()};
$('export').onclick=()=>{
 const report={schema:'hareworks-forward-woman-v0.1.1-browser-geometry-check',sourceSha256:SOURCE,model:'actual GLB',input:'Walking_Woman upper/root tracks, original foot orientations borrowed',phase:sourceClip.duration,frames:metrics,ownerAcceptance:false};
 const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='hareworks-woman-forward-v0.1.1-real-rig.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);
};
$('review').onclick=()=>{
 if(!active)return;playing=false;$('play').textContent='Play';metrics=[];
 const report={frames:0,maxResidual:0,maxKneeDiff:0,maxAnkleDiff:0,frontLeft:-Infinity,frontRight:-Infinity,errors:[]};
 for(let i=0;i<Math.round(sourceClip.duration*30);i++){
  frame=i;resetLegs();try{const o=sample(i/30);metrics.push(o);report.frames++;for(const p of o){report.maxResidual=Math.max(report.maxResidual,p.ankleResidual);report.maxKneeDiff=Math.max(report.maxKneeDiff,p.kneeDifferenceToReference);report.maxAnkleDiff=Math.max(report.maxAnkleDiff,p.ankleDifferenceToReference);if(p.side==='left')report.frontLeft=Math.max(report.frontLeft,p.relativeForward);else report.frontRight=Math.max(report.frontRight,p.relativeForward)}}catch(e){report.errors.push({frame:i,message:e.message});break}
 }
 $('status').textContent='30 FPS REAL RIG: '+(report.errors.length?'BLOCKED '+JSON.stringify(report.errors[0]):`MEASURED ${report.frames} frames; max IK residual ${report.maxResidual.toFixed(4)}, knee difference ${report.maxKneeDiff.toFixed(4)}. Visual review REQUIRED.`);
 console.info('HAREWORKS_FORWARD_PROOF',report);frame=0;resetLegs();tick();
};
try{
 $('status').textContent='Loading exact nine-clip Hareworks model and forward gait parameters...';
 [profile]=await Promise.all([fetch('./profile.json').then(r=>{if(!r.ok)throw Error('PROFILE_FETCH_'+r.status);return r.json()})]);
 validateProfile();
 const loaded=await new GLTFLoader().loadAsync('../../../assets/hareworks/Hareworks-nine-clips.glb');
 reference=loaded.scene;generated=cloneSkeleton(loaded.scene);
 reference.position.z=-PARENT_OFFSET/2;generated.position.z=PARENT_OFFSET/2;
 scene.add(reference,generated);reference.updateMatrixWorld(true);generated.updateMatrixWorld(true);
 const names=loaded.animations.map(x=>x.name);sourceClip=loaded.animations.find(x=>x.name===profile.clip);
 if(names.length!==9||!sourceClip)throw Error('NINE_CLIP_SOURCE_NOT_FOUND');
 if(Math.abs(sourceClip.duration-profile.clipDuration)>.001)throw Error('CLIP_DURATION_MISMATCH');
 refRig=getRig(reference);genRig=getRig(generated);
 refMixer=new THREE.AnimationMixer(reference);refMixer.clipAction(sourceClip).reset().play();refMixer.setTime(0);
 const allExcluded=Object.values(boneNames).flat();
 const removedTracks=sourceClip.tracks.filter(tr=>allExcluded.some(b=>tr.name.startsWith(b+'.')||tr.name.startsWith(b+'[')));
 if(removedTracks.length<4)throw Error('LEG_TRACK_FILTER_FAILED count='+removedTracks.length);
 const torsoClip=new THREE.AnimationClip('Walking_Woman_torso_only',sourceClip.duration,sourceClip.tracks.filter(tr=>!removedTracks.includes(tr)));
 // Exactly one seed frame, to anchor explicit leg rotational baselines.
 const seedMixer=new THREE.AnimationMixer(generated);seedMixer.clipAction(sourceClip).reset().play();seedMixer.setTime(0);
 for(const side of ['left','right'])for(const b of genRig.legs[side].chain)b.userData.seedQuat=b.quaternion.clone();
 seedMixer.stopAllAction();seedMixer.uncacheRoot(generated);
 genMixer=new THREE.AnimationMixer(generated);genMixer.clipAction(torsoClip).reset().play();genMixer.setTime(0);
 resetLegs();
 buildMarkers(refRig,{left:0x46c5fa,right:0xffc67b});buildMarkers(genRig,{left:0x46c5fa,right:0xffc67b});
 const bounds=new THREE.Box3().setFromObject(reference),bounds2=new THREE.Box3().setFromObject(generated);bounds.union(bounds2);grid.position.y=bounds.min.y;
 resize();active=true;playing=false;$('play').textContent='Play';tick();
 $('status').textContent='REAL SKINNED GLB LOADED · one reference woman clip vs generated leg IK. Run 30 fps check; visual review pending. No walking controller claim.';
}catch(e){$('status').textContent='BLOCKED_SOURCE_OR_RIG '+e.message;console.error(e)}
__HAREWORKS_FW_V011_1__
  cat > "$DIR/gait-kernel.mjs" <<'__HAREWORKS_FW_V011_2__'
/* Pure forward-only gait math. World convention: Three.js +Y up, +Z forward,
 * positive body yaw carries +Z toward +X. No browser or rig dependency. */
export function harmonic(coeff,q){let out=coeff[0];for(let i=1;i<coeff.length;i+=2){let n=(i+1)/2;out+=coeff[i]*Math.sin(2*Math.PI*n*q)+coeff[i+1]*Math.cos(2*Math.PI*n*q)}return out}
export function trajectory(t,profile,side){
 const p=profile[side],beta=profile.beta,L=p.front-p.rear;
 const q=((t/profile.clipDuration-p.phaseOffset)%1+1)%1;
 let z;
 if(q<beta)z=p.front-L*q/beta;
 else{let s=(q-beta)/(1-beta),m=-L*(1-beta)/beta;
  z=(2*s**3-3*s*s+1)*p.rear+(s**3-2*s*s+s)*m+(-2*s**3+3*s*s)*p.front+(s**3-s*s)*m;
 }
 return {x:harmonic(p.xFourier,q),y:harmonic(p.yFourier,q),z,q};
}
export function worldOffset(f,yaw,hipY){const c=Math.cos(yaw),s=Math.sin(yaw);return [f.x*c+f.z*s,f.y-hipY,-f.x*s+f.z*c]}
export function inverseWorldOffset(d,yaw){const c=Math.cos(yaw),s=Math.sin(yaw);return {x:d[0]*c-d[2]*s,z:d[0]*s+d[2]*c}}
__HAREWORKS_FW_V011_2__
  cat > "$DIR/profile.json" <<'__HAREWORKS_FW_V011_3__'
{
  "schema": "hareworks-woman-forward-proof-v0.1.1",
  "modelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "clip": "Walking_Woman",
  "clipDuration": 0.966667,
  "beta": 0.5450263949523612,
  "methods": "C1 periodic stance/swing foot-forward model with cubic-Hermite swing matched to stance velocity, low-order sinusoidal ankle height/lateral movement, anatomically fixed-pole 3D two-link knee IK",
  "scope": "forward-only in-place leg reconstruction, original woman reference hips; not real-skin, no full rooted locomotion",
  "calibration": "offline reference fit, NOT skinned acceptance",
  "left": {
    "phaseOffset": 0.26349253919859394,
    "front": 0.37182881416846864,
    "rear": -0.2580721893467686,
    "yFourier": [
      0.22509998798918085,
      -0.03522277091703029,
      0.019448162298900284,
      0.010006862810507531,
      -0.0005350439781932797,
      -0.009751997049610274,
      0.015756535841922905
    ],
    "xFourier": [
      0.028394521525500573,
      -0.04103614012582482,
      -0.01745184754566487,
      0.012529099177870652,
      0.015775597948693307
    ],
    "upperLength": 0.35676898841949994,
    "lowerLength": 0.38032414500319417,
    "pole": [
      -0.2593787162639453,
      -0.059392742416757106,
      0.9639477079683756
    ]
  },
  "right": {
    "phaseOffset": 0.754171779630934,
    "front": 0.37759839953016017,
    "rear": -0.28752168229932656,
    "yFourier": [
      0.224462720113572,
      -0.03497510372706922,
      0.02082298395983054,
      0.0020614899616770575,
      0.0017283505131568627,
      -0.010236171796325173,
      0.011910246395294376
    ],
    "xFourier": [
      -0.012316014403698287,
      0.042256605481880274,
      -0.0056043785493931,
      -0.009632050782018384,
      -0.01318883563090366
    ],
    "upperLength": 0.3479932042491327,
    "lowerLength": 0.39037758997519456,
    "pole": [
      0.14220938316980694,
      0.0016930416084295448,
      0.9898351503904956
    ]
  }
}
__HAREWORKS_FW_V011_3__
  cat > "$DIR/reference-legs.json" <<'__HAREWORKS_FW_V011_4__'
{"schema":"hareworks-woman-reference-leg-geometry-v0.1.1","clip":"Walking_Woman","sourceSha256":"a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6","duration":0.966667,"note":"Exported from user-provided v1.0.8 browser report, omit t=duration alias sample","frames":[{"t":0,"pelvisYaw":0.18521718701095075,"feet":{"left":{"hip":[0.071316,0.905387,0.096975],"knee":[0.090923,0.580018,0.242009],"ankle":[0.122703,0.260144,0.038744]},"right":{"hip":[-0.062096,0.920859,0.120764],"knee":[-0.021762,0.58172,0.187528],"ankle":[-0.008507,0.191808,0.20121]}}},{"t":0.016111,"pelvisYaw":0.1703646634613494,"feet":{"left":{"hip":[0.073206,0.90727,0.096379],"knee":[0.087465,0.587844,0.254645],"ankle":[0.124612,0.250332,0.08332]},"right":{"hip":[-0.060644,0.921441,0.118455],"knee":[-0.021818,0.580393,0.17571],"ankle":[-0.010498,0.190192,0.178871]}}},{"t":0.032222,"pelvisYaw":0.15558625778186014,"feet":{"left":{"hip":[0.07509,0.909161,0.095804],"knee":[0.083449,0.596173,0.266837],"ankle":[0.124846,0.244124,0.129016]},"right":{"hip":[-0.059164,0.922042,0.11615],"knee":[-0.021573,0.579376,0.163754],"ankle":[-0.011914,0.18919,0.156269]}}},{"t":0.048333,"pelvisYaw":0.1343668258485819,"feet":{"left":{"hip":[0.07736,0.909073,0.095646],"knee":[0.08105,0.600071,0.273937],"ankle":[0.126206,0.235862,0.174139]},"right":{"hip":[-0.057392,0.920514,0.113393],"knee":[-0.022354,0.576468,0.152173],"ankle":[-0.014172,0.186645,0.133051]}}},{"t":0.064444,"pelvisYaw":0.11275899426403757,"feet":{"left":{"hip":[0.079644,0.908847,0.095549],"knee":[0.078386,0.603726,0.280439],"ankle":[0.125873,0.231255,0.219972]},"right":{"hip":[-0.055549,0.918855,0.110612],"knee":[-0.022843,0.573687,0.140429],"ankle":[-0.015718,0.184605,0.109468]}}},{"t":0.080556,"pelvisYaw":0.08824782894604943,"feet":{"left":{"hip":[0.082191,0.907651,0.096115],"knee":[0.077384,0.604729,0.284529],"ankle":[0.125657,0.227932,0.266089]},"right":{"hip":[-0.053421,0.916047,0.108075],"knee":[-0.023743,0.569945,0.128853],"ankle":[-0.017023,0.181945,0.08636]}}},{"t":0.096667,"pelvisYaw":0.06334889889703664,"feet":{"left":{"hip":[0.084753,0.906309,0.096823],"knee":[0.076468,0.6053,0.288158],"ankle":[0.124091,0.228738,0.312237]},"right":{"hip":[-0.051192,0.913081,0.105594],"knee":[-0.024288,0.56632,0.117073],"ankle":[-0.017436,0.179771,0.062962]}}},{"t":0.112778,"pelvisYaw":0.039547131887606085,"feet":{"left":{"hip":[0.086996,0.904264,0.098471],"knee":[0.076644,0.604958,0.292358],"ankle":[0.122539,0.232768,0.355721]},"right":{"hip":[-0.04917,0.909811,0.104126],"knee":[-0.025258,0.562641,0.104472],"ankle":[-0.018297,0.177645,0.040249]}}},{"t":0.128889,"pelvisYaw":0.01604597375552917,"feet":{"left":{"hip":[0.089131,0.90204,0.100381],"knee":[0.077003,0.604391,0.296703],"ankle":[0.120234,0.240336,0.397903]},"right":{"hip":[-0.04717,0.90647,0.102935],"knee":[-0.025834,0.55932,0.091487],"ankle":[-0.018354,0.176098,0.017463]}}},{"t":0.145,"pelvisYaw":-0.004067708635633959,"feet":{"left":{"hip":[0.090683,0.898989,0.103211],"knee":[0.077563,0.603532,0.302753],"ankle":[0.117976,0.248541,0.433117]},"right":{"hip":[-0.045653,0.903051,0.103052],"knee":[-0.026752,0.556417,0.078827],"ankle":[-0.019905,0.175186,-0.004901]}}},{"t":0.161111,"pelvisYaw":-0.022900186095453707,"feet":{"left":{"hip":[0.091999,0.895624,0.106388],"knee":[0.078128,0.602606,0.309446],"ankle":[0.115462,0.257702,0.46531]},"right":{"hip":[-0.044312,0.899599,0.103666],"knee":[-0.027387,0.554035,0.066264],"ankle":[-0.021368,0.175046,-0.027147]}}},{"t":0.177222,"pelvisYaw":-0.03935702071182589,"feet":{"left":{"hip":[0.093542,0.891059,0.11024],"knee":[0.079107,0.601713,0.318458],"ankle":[0.113495,0.262915,0.487809]},"right":{"hip":[-0.042703,0.895145,0.105264],"knee":[-0.027384,0.551055,0.055597],"ankle":[-0.023368,0.174941,-0.048888]}}},{"t":0.193333,"pelvisYaw":-0.05456276410968913,"feet":{"left":{"hip":[0.095198,0.885863,0.114445],"knee":[0.080227,0.600934,0.32863],"ankle":[0.111786,0.265641,0.505349]},"right":{"hip":[-0.040948,0.890164,0.107379],"knee":[-0.026896,0.547924,0.04595],"ankle":[-0.025281,0.175274,-0.070344]}}},{"t":0.209444,"pelvisYaw":-0.06616825376061237,"feet":{"left":{"hip":[0.096938,0.881257,0.117856],"knee":[0.081367,0.599274,0.335864],"ankle":[0.110639,0.264321,0.513617]},"right":{"hip":[-0.039121,0.885431,0.109219],"knee":[-0.02507,0.545086,0.038036],"ankle":[-0.026235,0.176392,-0.090252]}}},{"t":0.225556,"pelvisYaw":-0.07523209074600297,"feet":{"left":{"hip":[0.098741,0.877067,0.12071],"knee":[0.082553,0.59694,0.341052],"ankle":[0.110018,0.260045,0.51539]},"right":{"hip":[-0.037247,0.880875,0.110867],"knee":[-0.022425,0.542408,0.031371],"ankle":[-0.026724,0.178152,-0.108963]}}},{"t":0.241667,"pelvisYaw":-0.08018560374337601,"feet":{"left":{"hip":[0.100933,0.87578,0.123312],"knee":[0.083876,0.592677,0.339751],"ankle":[0.109389,0.254174,0.511249]},"right":{"hip":[-0.035031,0.878703,0.112857],"knee":[-0.019802,0.541693,0.027465],"ankle":[-0.027919,0.182208,-0.12452]}}},{"t":0.257778,"pelvisYaw":-0.08132579694623228,"feet":{"left":{"hip":[0.103487,0.877209,0.125678],"knee":[0.085436,0.586856,0.332204],"ankle":[0.108906,0.247048,0.501397]},"right":{"hip":[-0.032495,0.878763,0.115165],"knee":[-0.017325,0.542695,0.026126],"ankle":[-0.030213,0.188262,-0.136986]}}},{"t":0.273889,"pelvisYaw":-0.08179323469318528,"feet":{"left":{"hip":[0.106013,0.878818,0.128858],"knee":[0.0863,0.582526,0.326612],"ankle":[0.107206,0.239584,0.489706]},"right":{"hip":[-0.02998,0.879156,0.118376],"knee":[-0.016063,0.543177,0.028801],"ankle":[-0.032512,0.195277,-0.147521]}}},{"t":0.29,"pelvisYaw":-0.08144076459075932,"feet":{"left":{"hip":[0.108509,0.880646,0.13304],"knee":[0.086233,0.579841,0.323575],"ankle":[0.103858,0.231757,0.475805]},"right":{"hip":[-0.027493,0.879959,0.122697],"knee":[-0.016232,0.543012,0.036446],"ankle":[-0.034798,0.20367,-0.15564]}}},{"t":0.306111,"pelvisYaw":-0.08104877534836259,"feet":{"left":{"hip":[0.111333,0.882781,0.136845],"knee":[0.08689,0.577748,0.32026],"ankle":[0.101809,0.224849,0.461281]},"right":{"hip":[-0.024671,0.880919,0.126674],"knee":[-0.01729,0.542127,0.047523],"ankle":[-0.037333,0.213389,-0.162058]}}},{"t":0.322222,"pelvisYaw":-0.08055745974902692,"feet":{"left":{"hip":[0.114691,0.885414,0.140035],"knee":[0.088759,0.57647,0.316573],"ankle":[0.101958,0.219063,0.445926]},"right":{"hip":[-0.021303,0.882131,0.130085],"knee":[-0.019582,0.540403,0.064371],"ankle":[-0.040205,0.225601,-0.165563]}}},{"t":0.338333,"pelvisYaw":-0.07862202063464137,"feet":{"left":{"hip":[0.118107,0.888431,0.142578],"knee":[0.09068,0.575618,0.31193],"ankle":[0.101929,0.213774,0.428501]},"right":{"hip":[-0.017876,0.883744,0.133056],"knee":[-0.021788,0.539413,0.082855],"ankle":[-0.043385,0.238276,-0.164622]}}},{"t":0.354444,"pelvisYaw":-0.07341394120544903,"feet":{"left":{"hip":[0.121661,0.892287,0.143687],"knee":[0.092562,0.575565,0.305316],"ankle":[0.10111,0.209142,0.406844]},"right":{"hip":[-0.014327,0.886232,0.135045],"knee":[-0.02408,0.539714,0.104552],"ankle":[-0.046339,0.249577,-0.155678]}}},{"t":0.370556,"pelvisYaw":-0.06890731308659537,"feet":{"left":{"hip":[0.124988,0.896097,0.144181],"knee":[0.094431,0.575546,0.297797],"ankle":[0.100416,0.205384,0.384922]},"right":{"hip":[-0.010979,0.888654,0.136334],"knee":[-0.025914,0.541116,0.12666],"ankle":[-0.048686,0.26016,-0.143414]}}},{"t":0.386667,"pelvisYaw":-0.06651876229025133,"feet":{"left":{"hip":[0.127617,0.899741,0.142762],"knee":[0.09642,0.57518,0.287577],"ankle":[0.100546,0.202369,0.362686]},"right":{"hip":[-0.008292,0.890844,0.135433],"knee":[-0.027881,0.543672,0.149096],"ankle":[-0.049234,0.264569,-0.123007]}}},{"t":0.402778,"pelvisYaw":-0.06486321870242424,"feet":{"left":{"hip":[0.129986,0.903393,0.141214],"knee":[0.098248,0.574967,0.276908],"ankle":[0.10056,0.199978,0.340346]},"right":{"hip":[-0.005851,0.893182,0.134289],"knee":[-0.029314,0.547964,0.17135],"ankle":[-0.048959,0.269114,-0.101141]}}},{"t":0.418889,"pelvisYaw":-0.06661198571705809,"feet":{"left":{"hip":[0.131145,0.907046,0.139067],"knee":[0.099486,0.574522,0.264405],"ankle":[0.100463,0.198004,0.318069]},"right":{"hip":[-0.004633,0.896178,0.131989],"knee":[-0.029631,0.554404,0.192528],"ankle":[-0.046876,0.268287,-0.072489]}}},{"t":0.435,"pelvisYaw":-0.06843325363276435,"feet":{"left":{"hip":[0.132148,0.910649,0.136924],"knee":[0.100709,0.574341,0.251784],"ankle":[0.10038,0.196562,0.295708]},"right":{"hip":[-0.003574,0.899212,0.129673],"knee":[-0.029744,0.562367,0.21304],"ankle":[-0.044907,0.268301,-0.04326]}}},{"t":0.451111,"pelvisYaw":-0.07086689273178969,"feet":{"left":{"hip":[0.131821,0.913809,0.134818],"knee":[0.101631,0.573941,0.239042],"ankle":[0.100238,0.195212,0.273809]},"right":{"hip":[-0.003899,0.902564,0.127213],"knee":[-0.02848,0.570987,0.229937],"ankle":[-0.043023,0.261648,-0.007745]}}},{"t":0.467222,"pelvisYaw":-0.07300061799414023,"feet":{"left":{"hip":[0.131469,0.916901,0.132688],"knee":[0.102516,0.573822,0.226192],"ankle":[0.100011,0.194367,0.251759]},"right":{"hip":[-0.004249,0.90586,0.124767],"knee":[-0.027107,0.580601,0.246354],"ankle":[-0.041002,0.256996,0.028453]}}},{"t":0.483333,"pelvisYaw":-0.06674595316262086,"feet":{"left":{"hip":[0.130473,0.918081,0.129883],"knee":[0.103703,0.572314,0.213626],"ankle":[0.100168,0.192338,0.229485]},"right":{"hip":[-0.005331,0.907597,0.122705],"knee":[-0.025035,0.587881,0.258692],"ankle":[-0.041279,0.246504,0.070031]}}},{"t":0.499444,"pelvisYaw":-0.060508556666022624,"feet":{"left":{"hip":[0.129471,0.919266,0.127079],"knee":[0.104669,0.571104,0.200919],"ankle":[0.099888,0.190859,0.207044]},"right":{"hip":[-0.006412,0.909336,0.120647],"knee":[-0.022627,0.595775,0.2707],"ankle":[-0.040193,0.239228,0.112713]}}},{"t":0.515556,"pelvisYaw":-0.046455523443138615,"feet":{"left":{"hip":[0.12776,0.919403,0.124398],"knee":[0.105946,0.569056,0.188154],"ankle":[0.1003,0.188789,0.184732]},"right":{"hip":[-0.008274,0.910647,0.119705],"knee":[-0.020716,0.602389,0.280706],"ankle":[-0.04131,0.231082,0.161953]}}},{"t":0.531667,"pelvisYaw":-0.032165385741569796,"feet":{"left":{"hip":[0.126,0.919517,0.121729],"knee":[0.106845,0.567293,0.175167],"ankle":[0.100003,0.187254,0.162134]},"right":{"hip":[-0.010155,0.91195,0.118819],"knee":[-0.018472,0.609289,0.29036],"ankle":[-0.040886,0.22742,0.212462]}}},{"t":0.547778,"pelvisYaw":-0.014379200353257515,"feet":{"left":{"hip":[0.123288,0.918635,0.119271],"knee":[0.108044,0.564866,0.162851],"ankle":[0.10143,0.18531,0.139605]},"right":{"hip":[-0.012982,0.912801,0.11859],"knee":[-0.017401,0.616102,0.300385],"ankle":[-0.041346,0.227769,0.268468]}}},{"t":0.563889,"pelvisYaw":0.003779672967327321,"feet":{"left":{"hip":[0.120431,0.917657,0.116856],"knee":[0.108846,0.56265,0.150326],"ankle":[0.10222,0.183879,0.11664]},"right":{"hip":[-0.015896,0.913615,0.11846],"knee":[-0.016157,0.623202,0.310187],"ankle":[-0.040844,0.233891,0.325104]}}},{"t":0.58,"pelvisYaw":0.020767026397290802,"feet":{"left":{"hip":[0.117842,0.915485,0.115322],"knee":[0.110259,0.559587,0.139061],"ankle":[0.105083,0.182031,0.093553]},"right":{"hip":[-0.018478,0.912884,0.119101],"knee":[-0.015948,0.627342,0.317993],"ankle":[-0.039932,0.242583,0.379475]}}},{"t":0.596111,"pelvisYaw":0.0375179887599168,"feet":{"left":{"hip":[0.11529,0.913071,0.113985],"knee":[0.11146,0.556593,0.127866],"ankle":[0.107608,0.180693,0.07015]},"right":{"hip":[-0.020972,0.91184,0.119914],"knee":[-0.01591,0.630975,0.325312],"ankle":[-0.039445,0.256303,0.432373]}}},{"t":0.612222,"pelvisYaw":0.05405104495975427,"feet":{"left":{"hip":[0.113068,0.909285,0.114112],"knee":[0.112602,0.552547,0.118784],"ankle":[0.110176,0.179022,0.047231]},"right":{"hip":[-0.023086,0.908698,0.122232],"knee":[-0.015607,0.630235,0.330802],"ankle":[-0.03802,0.267087,0.472279]}}},{"t":0.628333,"pelvisYaw":0.07052816708318371,"feet":{"left":{"hip":[0.110943,0.905059,0.114708],"knee":[0.113461,0.548326,0.110296],"ankle":[0.112018,0.177829,0.024413]},"right":{"hip":[-0.025063,0.904893,0.125029],"knee":[-0.0152,0.628085,0.335694],"ankle":[-0.036869,0.278122,0.507307]}}},{"t":0.644444,"pelvisYaw":0.08744214544109562,"feet":{"left":{"hip":[0.109029,0.898707,0.114909],"knee":[0.113773,0.542143,0.103776],"ankle":[0.113465,0.175844,0.001447]},"right":{"hip":[-0.026785,0.898757,0.127506],"knee":[-0.0156,0.625701,0.342947],"ankle":[-0.03532,0.280984,0.525089]}}},{"t":0.660556,"pelvisYaw":0.10455115079509175,"feet":{"left":{"hip":[0.107199,0.891398,0.114933],"knee":[0.113774,0.535086,0.098126],"ankle":[0.11436,0.174056,-0.021473]},"right":{"hip":[-0.02838,0.891573,0.129839],"knee":[-0.016262,0.623321,0.351183],"ankle":[-0.033063,0.279562,0.535418]}}},{"t":0.676667,"pelvisYaw":0.11909438630089914,"feet":{"left":{"hip":[0.105291,0.885656,0.115279],"knee":[0.112225,0.529674,0.092637],"ankle":[0.114993,0.174099,-0.04229]},"right":{"hip":[-0.030061,0.886141,0.132121],"knee":[-0.016588,0.62048,0.356491],"ankle":[-0.030603,0.27346,0.534748]}}},{"t":0.692778,"pelvisYaw":0.1320793318439705,"feet":{"left":{"hip":[0.103336,0.880873,0.115824],"knee":[0.109708,0.525304,0.087282],"ankle":[0.115501,0.175434,-0.061728]},"right":{"hip":[-0.03179,0.881784,0.134373],"knee":[-0.01673,0.617311,0.360043],"ankle":[-0.02811,0.26473,0.527231]}}},{"t":0.708889,"pelvisYaw":0.1405026901661199,"feet":{"left":{"hip":[0.101245,0.87794,0.116798],"knee":[0.107404,0.52293,0.081951],"ankle":[0.116974,0.178433,-0.078911]},"right":{"hip":[-0.033726,0.879546,0.136402],"knee":[-0.01646,0.612898,0.359337],"ankle":[-0.025507,0.255164,0.515348]}}},{"t":0.725,"pelvisYaw":0.145229265068788,"feet":{"left":{"hip":[0.099046,0.876514,0.11812],"knee":[0.105233,0.522222,0.076613],"ankle":[0.119146,0.182793,-0.094387]},"right":{"hip":[-0.035834,0.879032,0.138248],"knee":[-0.015993,0.607559,0.355061],"ankle":[-0.02314,0.245057,0.499754]}}},{"t":0.741111,"pelvisYaw":0.14871059287345206,"feet":{"left":{"hip":[0.096664,0.876112,0.119755],"knee":[0.103646,0.522418,0.073533],"ankle":[0.121261,0.188543,-0.107749]},"right":{"hip":[-0.038144,0.879511,0.140237],"knee":[-0.015658,0.603306,0.350723],"ankle":[-0.020992,0.236709,0.484785]}}},{"t":0.757222,"pelvisYaw":0.1508513455649889,"feet":{"left":{"hip":[0.094085,0.876804,0.121724],"knee":[0.102794,0.523503,0.072875],"ankle":[0.123542,0.19564,-0.118756]},"right":{"hip":[-0.040672,0.881053,0.142378],"knee":[-0.015416,0.600228,0.346335],"ankle":[-0.018948,0.230159,0.470559]}}},{"t":0.773333,"pelvisYaw":0.1527415502191336,"feet":{"left":{"hip":[0.091284,0.877475,0.123779],"knee":[0.101879,0.524127,0.075647],"ankle":[0.124124,0.203678,-0.12798]},"right":{"hip":[-0.04342,0.882726,0.144547],"knee":[-0.015401,0.596967,0.341158],"ankle":[-0.01658,0.224081,0.456697]}}},{"t":0.789444,"pelvisYaw":0.15427078139492897,"feet":{"left":{"hip":[0.088165,0.878117,0.125953],"knee":[0.100821,0.524122,0.08339],"ankle":[0.123012,0.213196,-0.134506]},"right":{"hip":[-0.046481,0.884588,0.146755],"knee":[-0.015658,0.593462,0.334891],"ankle":[-0.013617,0.218492,0.443461]}}},{"t":0.805556,"pelvisYaw":0.15472449904139382,"feet":{"left":{"hip":[0.085043,0.878883,0.127704],"knee":[0.099731,0.523934,0.094849],"ankle":[0.122539,0.224344,-0.13833]},"right":{"hip":[-0.049556,0.886562,0.148397],"knee":[-0.016708,0.590925,0.329005],"ankle":[-0.011611,0.213052,0.426887]}}},{"t":0.821667,"pelvisYaw":0.15310274800675094,"feet":{"left":{"hip":[0.08192,0.879878,0.128645],"knee":[0.098249,0.523812,0.113336],"ankle":[0.122494,0.238633,-0.137127]},"right":{"hip":[-0.052662,0.888741,0.148964],"knee":[-0.019166,0.58989,0.32408],"ankle":[-0.011387,0.207891,0.404146]}}},{"t":0.837778,"pelvisYaw":0.15188592921514776,"feet":{"left":{"hip":[0.078936,0.881052,0.128678],"knee":[0.096312,0.52472,0.131713],"ankle":[0.12348,0.253118,-0.133128]},"right":{"hip":[-0.055607,0.89117,0.148674],"knee":[-0.021389,0.588768,0.317438],"ankle":[-0.011305,0.20378,0.381287]}}},{"t":0.853889,"pelvisYaw":0.15173057034725415,"feet":{"left":{"hip":[0.076323,0.882689,0.12633],"knee":[0.094586,0.527134,0.149377],"ankle":[0.125177,0.264554,-0.12405]},"right":{"hip":[-0.058132,0.894247,0.146136],"knee":[-0.022914,0.58736,0.306384],"ankle":[-0.010944,0.200694,0.358736]}}},{"t":0.87,"pelvisYaw":0.15261736282614055,"feet":{"left":{"hip":[0.073885,0.884776,0.123578],"knee":[0.092699,0.531066,0.166233],"ankle":[0.125675,0.275141,-0.113161]},"right":{"hip":[-0.060447,0.897756,0.14334],"knee":[-0.02422,0.5861,0.293863],"ankle":[-0.0106,0.198255,0.336118]}}},{"t":0.886111,"pelvisYaw":0.15757728096683843,"feet":{"left":{"hip":[0.072136,0.888559,0.119285],"knee":[0.091917,0.537524,0.179842],"ankle":[0.125312,0.278728,-0.096845]},"right":{"hip":[-0.061981,0.902896,0.13956],"knee":[-0.024454,0.584988,0.276035],"ankle":[-0.009846,0.196724,0.313887]}}},{"t":0.902222,"pelvisYaw":0.16320420272950079,"feet":{"left":{"hip":[0.070552,0.892344,0.1149],"knee":[0.091238,0.544934,0.193403],"ankle":[0.124248,0.281823,-0.079231]},"right":{"hip":[-0.063333,0.907912,0.135793],"knee":[-0.024619,0.584378,0.257965],"ankle":[-0.009259,0.195743,0.291457]}}},{"t":0.918333,"pelvisYaw":0.17314247375835626,"feet":{"left":{"hip":[0.070038,0.896079,0.10993],"knee":[0.091048,0.553542,0.207451],"ankle":[0.12173,0.277518,-0.052387]},"right":{"hip":[-0.063588,0.912111,0.132087],"knee":[-0.023643,0.583617,0.239768],"ankle":[-0.008371,0.194655,0.269265]}}},{"t":0.934444,"pelvisYaw":0.18249014861723536,"feet":{"left":{"hip":[0.069614,0.899753,0.105029],"knee":[0.091139,0.563045,0.220998],"ankle":[0.119947,0.274413,-0.024985]},"right":{"hip":[-0.063761,0.916183,0.128377],"knee":[-0.022866,0.583378,0.221474],"ankle":[-0.007939,0.194111,0.246834]}}},{"t":0.950556,"pelvisYaw":0.18385672187871982,"feet":{"left":{"hip":[0.070465,0.902569,0.101002],"knee":[0.091059,0.571214,0.231631],"ankle":[0.121423,0.266219,0.006459]},"right":{"hip":[-0.062929,0.91852,0.12457],"knee":[-0.022333,0.582289,0.20457],"ankle":[-0.008226,0.192656,0.2241]}}}]}
__HAREWORKS_FW_V011_4__
  cat > "$DIR/kinematics-test.mjs" <<'__HAREWORKS_FW_V011_5__'
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {trajectory,worldOffset,inverseWorldOffset} from './gait-kernel.mjs';
const json=f=>JSON.parse(readFileSync(new URL(f,import.meta.url),'utf8'));
const profile=json('./profile.json'),ref=json('./reference-legs.json');
assert.equal(ref.frames.length,60);
assert.equal(ref.sourceSha256,profile.modelSha256);
assert.ok(Math.abs(ref.duration-profile.clipDuration)<1e-4);
function dot(a,b){return a.reduce((r,v,i)=>r+v*b[i],0)}
function minus(a,b){return a.map((v,i)=>v-b[i])}
function plus(a,b){return a.map((v,i)=>v+b[i])}
function mult(a,k){return a.map(v=>v*k)}
function norm(a){return Math.hypot(...a)}
function getKnee(h,a,l1,l2,pole,yaw){
 const diff=minus(a,h),d=norm(diff),u=mult(diff,1/d),alpha=(l1*l1-l2*l2+d*d)/(2*d);
 const c=plus(h,mult(u,alpha)),rad=Math.sqrt(Math.max(0,l1*l1-alpha*alpha));
 const cs=Math.cos(yaw),sn=Math.sin(yaw),pw=[pole[0]*cs+pole[2]*sn,pole[1],-pole[0]*sn+pole[2]*cs];
 const pp=minus(pw,mult(u,dot(pw,u)));
 return plus(c,mult(pp,rad/norm(pp)));
}
const evidence={schema:'hareworks-forward-woman-v0.1.1-node-geometry-proof',referenceSha256:ref.sourceSha256,samples:ref.frames.length,validation:'source 30 Hz complementary holdout',results:{}};
for(const side of ['left','right']){
 const p=profile[side];let errA=0,errK=0,N=0,front=-Infinity,rear=Infinity,maxTargetReach=0;
 for(let i=0;i<ref.frames.length;i++){
  const frame=ref.frames[i],r=frame.feet[side],f=trajectory(frame.t,profile,side),ofs=worldOffset(f,frame.pelvisYaw,r.hip[1]),a=plus(r.hip,ofs);
  const inv=inverseWorldOffset(ofs,frame.pelvisYaw);
  assert.ok(Math.abs(inv.z-f.z)<1e-9&&Math.abs(inv.x-f.x)<1e-9,'angle/sign convention regression');
  const d=norm(minus(a,r.hip)),k=getKnee(r.hip,a,p.upperLength,p.lowerLength,p.pole,frame.pelvisYaw);
  assert.ok(Number.isFinite(k[0]+k[1]+k[2]));
  assert.ok(d<=p.upperLength+p.lowerLength-0.004,'unsupported heel target beyond anatomical reach '+side+' '+i);
  assert.ok(Math.abs(norm(minus(k,r.hip))-p.upperLength)<1e-8,'upper bone not rigid');
  assert.ok(Math.abs(norm(minus(k,a))-p.lowerLength)<1e-8,'lower bone not rigid');
  maxTargetReach=Math.max(maxTargetReach,d);front=Math.max(front,f.z);rear=Math.min(rear,f.z);
  // 60Hz odd frames train, 60Hz even frames represent the held-out 30fps grid.
  if(i%2===0){errA+=norm(minus(a,r.ankle))**2;errK+=norm(minus(k,r.knee))**2;N++;}
 }
 const ankleRMS=Math.sqrt(errA/N),kneeRMS=Math.sqrt(errK/N);
 assert.ok(front>.35,'never plants a leading foot in front of hip');
 assert.ok(rear<-.20,'never swings the foot behind hip');
 assert.ok(ankleRMS<.035,'generated ankle path failed woman reference fit');
 assert.ok(kneeRMS<.055,'IK knee path failed woman reference fit');
 evidence.results[side]={samples:N,front,rear,maxTargetReach,ankleRMS,kneeRMS};
 // The generator must make continuous swing and stance movement at their connection.
 const edge=(p.phaseOffset+profile.beta)*profile.clipDuration;const dt=1e-5;
 const z0=trajectory(edge-dt,profile,side).z,z1=trajectory(edge,profile,side).z,z2=trajectory(edge+dt,profile,side).z;
 assert.ok(Math.abs((z1-z0)-(z2-z1))<.001,'swing/stance velocity discontinuity');
}
// Failure injection: invalid +X/+Z handedness must be detected by the projection round trip.
const sample=worldOffset({x:.3,z:.6,y:.2},.5,.7);assert.ok(Math.abs(inverseWorldOffset(sample,.5).z-.6)<1e-9);
assert.ok(Math.abs(inverseWorldOffset(sample,-.5).z-.6)>.1,'handedness negative-control not detected');
console.log('FORWARD_WOMAN_30FPS_REFERENCE_HOLDOUT=PASS');console.log(JSON.stringify(evidence,null,2));
__HAREWORKS_FW_V011_5__
  cat > "$DIR/README.md" <<'__HAREWORKS_FW_V011_6__'
# Hareworks v0.1.1: Straight-Ahead Woman Walk Leg Proof

**Purpose**: Replicate the leg motion of the existing `Walking_Woman` reference before revisiting world-root movement, strafing or aiming. The owner rejected v0.1.0 because its leading foot never got ahead of the body, its support leg overextended, its CCD knees snapped, and dual-stick controls were reversed. Those systems are out of scope, not reported fixed.

## Measured source

Published nine-clip Hareworks GLB SHA `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`. Browser-exported `hareworks-gait-and-idle-turn-v1.0.8.json` provides 60 approximately uniform samples per gait excluding its potentially discontinuous `t=duration` endpoint. `Walking_Woman` period approximately 0.966667s. 74 skin joints. Actual hip/knee/intermediate/ankle/toe leg chains are asserted in the viewer.

A 30Hz holdout reference check fitted a continuous-velocity stance/swing trajectory, low-order swing-height and lateral components, and an anatomical knee bend pole derived from the source measurements. Summary before actual 3D skin tests: left ankle RMS 0.0149, right 0.0180 source units; left knee RMS 0.0255, right 0.0242. The target is ~0.39–0.40 units ahead of each hip; no sampled hard reach violations. These offline measurements are *not* runtime or visual proof.

## Model comparison

Left character: original `Walking_Woman` clip. Right: *same actual skinned GLB*, torso/root track subset of `Walking_Woman`, with all named leg tracks removed from its AnimationClip. A stable fixed-pole two-link IK generates the actual hip and knee bone orientations from analytically constructed ankle targets. This is not a CCD search and does not borrow reference leg angles; the knee is derived from two link lengths and a fixed pole. The intermediate and toe local joints are maintained from the seed pose. Source ankle/world orientation is borrowed deliberately for this narrow anatomical-leg validation. Both source and generated animated bodies are displayed side-by-side at 30 fps, one cycle per playback. The exported endpoint sample may be discontinuous, so this candidate does not claim a seamless loop. A real-bone residual failure blocks the comparison rather than becoming a warning.

This is **not a complete procedural walking controller**, because the root/pelvis path and ankle roll are not independent, actual sole contact patches are not grounded, and forward world traversal is not established. The viewer is intended only to establish whether we can put the skinned legs into convincing source-like shapes without popping. Once the owner visually accepts the side-by-side comparison, we can move on to independent forward root travel and foot-plant constraints.

## Campaign discipline

Android Termux Git only, isolated SHA-pinned checkout, preflight path collision check, text-only commit, exact remote readback, protected asset-hash checks, no LFS change, local exact-source GLB verification, viewer HTTP verified, owner visual acceptance pending. No direct connector code mutation.
__HAREWORKS_FW_V011_6__
  cp -- "$0" "campaigns/$CAMPAIGN.sh" || fail 'cannot preserve exact versioned launcher in repo'
fi
phase='precommit-validation'
# No new source asset is added or modified in Git, no LFS upload is required.
if command -v node >/dev/null;then
  node --check "$DIR/gait-kernel.mjs" || fail 'gait kernel syntax failed'
  node --check "$DIR/viewer.mjs" || fail 'real-rig browser script syntax failed'
  node "$DIR/kinematics-test.mjs" > "$STATE/math-test.json.log" || fail 'actual forward-kinematics reference holdout failed'
  echo 'NODE_30FPS_REFERENCE_TEST=PASS'
else
  echo 'NODE_MISSING_ON_FRESH_TERMUX=YES; browser runtime check still required; numeric packet validated by author'
fi
python3 - "$DIR/profile.json" "$DIR/reference-legs.json" "$MODEL_SHA" <<'PY' || fail 'numeric reference/contract mismatch'
import sys,json,math
p=json.load(open(sys.argv[1]));r=json.load(open(sys.argv[2]));sha=sys.argv[3]
assert p['modelSha256']==r['sourceSha256']==sha
assert p['clip']==r['clip']=='Walking_Woman' and len(r['frames'])==60
assert abs(p['clipDuration']-r['duration'])<.0001
for s in ('left','right'):
 assert len(p[s]['pole'])==3 and len(p[s]['xFourier'])==5 and len(p[s]['yFourier'])==7
 assert .2<p[s]['front']<.65 and -.45<p[s]['rear']<-.1
print('PROFILE_CONTRACT=PASS')
PY
if ((PUBLISHED==0));then
  phase='stage'
  [[ "$REMOTE" == "$BASE" ]] || fail 'pin advanced before staging'
  git add -- "${FILES[@]}" || fail 'text-only file staging failed'
  python3 - "${FILES[@]}" <<'PY' || fail 'unexpected staged file mutation'
import subprocess,sys
want=set(sys.argv[1:]);got=set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines())
assert want==got,(want-got,got-want)
print('STAGED_SCOPE=PASS',len(got))
PY
  for f in AGENTS.md assets/repl/Repl.glb assets/hareworks/Hareworks.glb "$MODEL";do
    git diff --quiet -- "$f" || fail "protected source worktree unexpectedly modified: $f"
    [[ "$(git rev-parse "HEAD:$f")" == "$(git rev-parse "$BASE:$f")" ]] || fail "protected source commit changed $f"
  done
  phase='commit'
  git -c user.name='Hareworks Termux Campaign' -c user.email='hareworks-campaign@users.noreply.github.com' commit -m 'Add Hareworks forward woman walking leg-only comparison v0.1.1' || fail 'text-only Git commit failed'
  COMMIT=$(git rev-parse HEAD)
  [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'unexpected publication parent'
  phase='publish'
  [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote advanced during candidate work, no force push'
  GIT_LFS_SKIP_PUSH=1 git push origin HEAD:refs/heads/main || fail "text-only push failed, local evidence preserved at $COMMIT"
else
  phase='recovery-readback'
  # Compare EXACT authored files with repository, so this rerun cannot silently
  # reuse another, different campaign revision.
  for f in "${FILES[@]}";do
    [[ -f "$f" ]] && [[ "$(hash "$f")" == "$(git show "HEAD:$f" | sha256sum | cut -d' ' -f1)" ]] || fail "existing remote candidate differs from this packet: $f"
  done
  COMMIT="$REMOTE"
fi
phase='readback'
[[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$COMMIT" ]] || fail 'main did not read back exact published SHA'
GIT_LFS_SKIP_SMUDGE=1 git fetch --depth=1 origin main || fail 'remote fetch readback failed'
[[ "$(git rev-parse FETCH_HEAD)" == "$COMMIT" ]] || fail 'remote fetch differs from observed commit'
for f in "${FILES[@]}";do
  [[ "$(git rev-parse "FETCH_HEAD:$f")" == "$(git rev-parse "HEAD:$f")" ]] || fail "remote content readback mismatch $f"
done
for f in AGENTS.md assets/repl/Repl.glb assets/hareworks/Hareworks.glb "$MODEL";do
  [[ "$(git rev-parse "FETCH_HEAD:$f")" == "$(git rev-parse "$BASE:$f")" ]] || fail "source changed $f"
done
echo "GIT_REMOTE_READBACK=PASS $COMMIT"
phase='viewer'
# Populate the exact published LFS bytes for HTTP viewing only after Git has
# committed the text-only candidate. Never stage the model.
cp -- "$SOURCE" "$MODEL" || fail 'could not populate read-only viewer source'
[[ "$(hash "$MODEL")" == "$MODEL_SHA" ]] || fail 'viewer GLB differs from owner-published source'
cat > "$ROOT/server.py" <<'PY'
import http.server,json,os,pathlib,sys
root,ready=sys.argv[1:]
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs): super().__init__(*args,directory=root,**kwargs)
 def end_headers(self):
  self.send_header('Cache-Control','no-store')
  super().end_headers()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
pathlib.Path(ready).write_text(json.dumps({'pid':os.getpid(),'port':server.server_address[1],'root':root}))
server.serve_forever()
PY
READY="$ROOT/server-ready.json"
nohup python3 "$ROOT/server.py" "$WORK" "$READY" > "$ROOT/server.log" 2>&1 </dev/null &
PID=$!
PORT='';OK=0
for n in 1 2 3 4 5 6 7 8 9 10;do
  if [[ -f "$READY" ]];then
    PORT=$(python3 - "$READY" <<'PY'
import json,sys
print(json.load(open(sys.argv[1]))['port'])
PY
)
    if curl -fsS --max-time 3 "http://127.0.0.1:$PORT/$DIR/index.html" >/dev/null 2>&1 && curl -fsS --max-time 3 "http://127.0.0.1:$PORT/$DIR/viewer.mjs" >/dev/null 2>&1;then OK=1;break;fi
  fi
  sleep 1
done
[[ "$OK" == 1 ]] && kill -0 "$PID" 2>/dev/null || fail 'viewer server not responding'
HTTP_MODEL_SHA=$(curl -fsS --max-time 40 "http://127.0.0.1:$PORT/$MODEL" | sha256sum | cut -d' ' -f1) || fail 'HTTP model GET failed'
[[ "$HTTP_MODEL_SHA" == "$MODEL_SHA" ]] || fail 'viewer served wrong model bytes'
URL="http://127.0.0.1:$PORT/$DIR/index.html?commit=$COMMIT"
python3 - "$STATE/receipt.json" "$CAMPAIGN" "$BASE" "$COMMIT" "$MODEL_SHA" "$AGENTS_BLOB" "$URL" "$PID" "$PORT" "$ROOT" <<'PY'
import json,datetime,sys,pathlib
out,campaign,base,commit,model,agents,url,pid,port,root=sys.argv[1:]
receipt=dict(campaign=campaign,phase='viewer_http_model_verified_browser_pending',timestampUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),auditedBase=base,remoteCommit=commit,sourceSha256=model,agentsGitBlob=agents,rulesRead={'agents':'read from exact checked out repository','campaignEtiquette':'Home Center 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI read 2026-11-20','topDownEtiquette':'Home Center 1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU read 2026-11-20'},viewerUrl=url,viewerPid=int(pid),viewerPort=int(port),snapshot=root,localHttpModelShaVerified=True,realSkinnedBrowserRigCheck='PENDING',ownerVisualAcceptance=False,sourceModelsModified=False,mutatingExecutionLane='Termux Git only')
pathlib.Path(out).write_text(json.dumps(receipt,indent=2))
PY
echo "REMOTE_COMMIT=$COMMIT"
echo "MODEL_SHA_VERIFIED=$MODEL_SHA"
echo "VIEWER_PORT=$PORT PID=$PID"
echo "VIEWER_URL=$URL"
echo "RECEIPT=$STATE/receipt.json"
echo 'REAL_SKINNED_30FPS_REVIEW=PENDING; CLICK Run 30 fps rig check AND RECORD VISUAL VERDICT'
if command -v termux-open-url >/dev/null;then termux-open-url "$URL" || echo "BROWSER_OPEN_FAILED; manually open $URL";else echo "TERMUX_OPEN_URL_MISSING; manually open $URL";fi
