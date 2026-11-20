#!/data/data/com.termux/files/usr/bin/bash
# Hareworks forward Woman v0.1.3: preserve pelvis, repair feet and knees.
# Real skinned source, 30/60/120fps continuity plus deliberate atomic rollback gate.
# Only approved mutation/execution: Termux Git. Previous source remains immutable.
set -Eeuo pipefail
CAMPAIGN='hareworks-forward-woman-proof-v0.1.3'
REPO='Valar05/parametric-parambulator'
BASE='429cef2c1d26f81d58bcb6196eb80dd065b51168'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_BYTES=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
LOCKED_V012_VIEWER='c1bd2151df80d76d1431b5767f7f6632805f30a5'
LOCKED_V012_PELVIS='4d43c5864de31ec93563c42a910863579138e4c5'
DIR='tools/hareworks-forward-woman/v0.1.3'
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
exec > >(tee -a "$STATE/run.log") 2>&1
phase='preflight'
fail(){
  echo "BLOCKED step=$phase reason=$*"
  python3 - "$STATE/blocked.json" "$CAMPAIGN" "$phase" "$*" <<'PY_BLOCK' || true
import json,sys,datetime,pathlib
out,campaign,step,reason=sys.argv[1:]
pathlib.Path(out).write_text(json.dumps({'campaign':campaign,'phase':'blocked','step':step,'reason':reason,'atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY_BLOCK
  exit 1
}
if [[ "${1:-run}" == status ]];then
  [[ -f "$STATE/receipt.json" ]] || fail 'no published viewer receipt yet'
  cat "$STATE/receipt.json"
  exit 0
fi
[[ "${1:-run}" == run || "${1:-run}" == resume ]] || fail 'usage: bash campaign.sh [run|resume|status]'
for c in git python3 sha256sum curl;do command -v "$c" >/dev/null || fail "required dependency missing: $c";done
hash(){ sha256sum -- "$1" | cut -d' ' -f1; }
ORIGIN="https://github.com/$REPO.git"
REMOTE=$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1) || fail 'cannot read GitHub main'
[[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] || fail 'invalid remote commit id'
echo "AUDITED_BASE=$BASE"
echo "OBSERVED_REMOTE_MAIN=$REMOTE"
ROOT=$(mktemp -d "$STATE/snapshot.XXXXXXXX") || fail 'cannot create isolated snapshot'
WORK="$ROOT/repo"
# Use a NEW subdirectory under a unique snapshot: never reuse or reset dirty work.
GIT_LFS_SKIP_SMUDGE=1 git -c lfs.install.skip=true clone --depth=1 --filter=blob:none --no-checkout --single-branch --branch main "$ORIGIN" "$WORK" || fail 'shallow isolated clone failed'
git -C "$WORK" sparse-checkout init --cone || fail 'sparse init failed'
git -C "$WORK" sparse-checkout set assets/hareworks tools/hareworks-forward-woman campaigns || fail 'sparse set failed'
GIT_LFS_SKIP_SMUDGE=1 git -C "$WORK" checkout -B "$CAMPAIGN" "$REMOTE" || fail 'checkout failed'
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$REMOTE" ]] || fail 'checkout ref drift'
cd "$WORK"
[[ -f AGENTS.md ]] && grep -Fq 'Termux Git only' AGENTS.md || fail 'repository rules gate unreadable'
[[ "$(git rev-parse HEAD:AGENTS.md)" == "$AGENTS_BLOB" ]] || fail 'repository rules changed from audited source'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.2/viewer.mjs)" == "$LOCKED_V012_VIEWER" ]] || fail 'previous real-rig viewer changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.2/motion-profile.json)" == "$LOCKED_V012_PELVIS" ]] || fail 'pelvis profile changed, preserve owner-accepted hips'
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_BYTES" <<'PY_PTR' || fail 'source LFS pointer changed'
import subprocess,sys
path,oid,size=sys.argv[1:]
pointer=subprocess.check_output(['git','show','HEAD:'+path]);expected=(f'version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize {size}\n').encode()
assert pointer==expected,(pointer[:100],expected)
print('PUBLISHED_SOURCE_POINTER=PASS')
PY_PTR
FILES=("$DIR/index.html" "$DIR/viewer.mjs" "$DIR/foot-kernel.mjs" "$DIR/foot-kernel-test.mjs" "$DIR/foot-profile.json" "$DIR/reference-leg-witnesses.json" "$DIR/README.md" "$DIR/contract.json" "campaigns/$CAMPAIGN.sh")
phase='collision-check'
PUBLISHED=0
if [[ "$REMOTE" == "$BASE" ]];then
 for p in "${FILES[@]}";do
  [[ ! -e "$p" && ! -L "$p" ]] && ! git cat-file -e "HEAD:$p" 2>/dev/null || fail "collision with prior or dirty path: $p"
 done
else
 if git cat-file -e "HEAD:campaigns/$CAMPAIGN.sh" 2>/dev/null && git cat-file -e "HEAD:${FILES[0]}" 2>/dev/null;then
  [[ "$(git show "HEAD:campaigns/$CAMPAIGN.sh" | sha256sum | cut -d' ' -f1)" == "$(hash "$0")" ]] || fail 'a different packet already occupies this campaign filename; no overwrite'
  [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'published recovery commit does not extend audited base'
  PUBLISHED=1;echo "CAMPAIGN_ALREADY_PUBLISHED=$REMOTE exact launcher matches; skip Git mutation"
 else
  fail 'remote main advanced by another change; no force push or reset'
 fi
fi
phase='source'
SOURCE=''
for base in "$HOME/.local/state/hareworks" "$HOME/storage/downloads" /storage/emulated/0/Download;do
 [[ -d "$base" ]] || continue
 if [[ "$base" == "$HOME/.local/state/hareworks" ]];then
  while IFS= read -r -d '' f;do
   [[ "$(wc -c < "$f" | tr -d ' ')" == "$MODEL_BYTES" ]] || continue
   if [[ "$(hash "$f")" == "$MODEL_SHA" ]];then SOURCE="$f";break;fi
  done < <(find "$base" -maxdepth 10 -type f -name 'Hareworks-nine-clips.glb' -print0 2>/dev/null)
 else
  while IFS= read -r -d '' f;do
   [[ "$(wc -c < "$f" | tr -d ' ')" == "$MODEL_BYTES" ]] || continue
   if [[ "$(hash "$f")" == "$MODEL_SHA" ]];then SOURCE="$f";break;fi
  done < <(find -L "$base" -maxdepth 1 -type f -iname '*.glb' -print0 2>/dev/null)
 fi
 [[ -n "$SOURCE" ]] && break
done
if [[ -z "$SOURCE" ]];then
 command -v git-lfs >/dev/null || fail 'exact model unavailable and git-lfs not installed'
 git lfs install --local || fail 'local LFS setup failed'
 GIT_LFS_SKIP_SMUDGE=1 git lfs fetch -I "$MODEL" -X '' origin "$REMOTE" || fail 'exact nine-clip LFS fetch failed'
 OBJ=$(git rev-parse --git-path "lfs/objects/${MODEL_SHA:0:2}/${MODEL_SHA:2:2}/$MODEL_SHA")
 [[ -f "$OBJ" ]] || fail 'exact model object not in LFS store'
 SOURCE="$OBJ"
fi
[[ "$(wc -c < "$SOURCE" | tr -d ' ')" == "$MODEL_BYTES" && "$(hash "$SOURCE")" == "$MODEL_SHA" ]] || fail 'model source hash and length mismatch'
python3 - "$SOURCE" <<'PY_RIG' || fail 'real 74-joint nine-clip model structure invalid'
import json,struct,sys
b=open(sys.argv[1],'rb').read();assert b[:4]==b'glTF' and struct.unpack_from('<I',b,8)[0]==len(b)
n,magic=struct.unpack_from('<I4s',b,12);assert magic==b'JSON'
g=json.loads(b[20:20+n]);names=[a['name'] for a in g['animations']]
assert len(names)==9 and 'Walking_Woman' in names and len(g['skins'][0]['joints'])==74
print('ORIGINAL_SKIN_AND_WOMAN_CLIP=PASS')
PY_RIG
echo "EXACT_SOURCE_SHA256=$MODEL_SHA"
phase='packet'
if ((PUBLISHED==0));then
 mkdir -p "$DIR" campaigns
fi
if ((PUBLISHED==0));then
 cat > "$DIR/index.html" <<'__HAREWORKS_FW_V013_0__'
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#101821"><title>Hareworks | Woman Foot Continuity Proof v0.1.3</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>
:root{font:14px system-ui,sans-serif;color:#edf5ff;background:#101821;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:1150px;margin:auto;padding:12px}h1{font-size:19px;margin:3px 0}header{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center}p{line-height:1.45;color:#bcd0df;margin:8px 0}.pill{border:1px solid #51667c;padding:5px 9px;border-radius:20px;color:#cde1ef;font-size:11px}#status{padding:10px 0;color:#a4e9d7;min-height:43px}#stage{border:1px solid #506579;border-radius:10px;overflow:hidden;background:#09121b}#stage canvas{width:100%;display:block;touch-action:none}.labels{display:grid;grid-template-columns:1fr 1fr;text-align:center;gap:10px;margin:8px 0;color:#d8eaf6;font-size:12px}.toolbar,.cameraBar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}.cameraBar{background:#182a39;padding:8px;border-radius:8px}button{font:inherit;background:#2a455d;color:white;border:1px solid #617f98;border-radius:7px;min-height:42px;padding:9px 12px}button:focus-visible{outline:3px solid #7ae1fa}button:active{background:#456780}#metrics{white-space:pre-wrap;background:#1a2c3b;padding:10px;border-radius:7px;border:1px solid #435b6a;font:12px/1.5 ui-monospace,monospace;overflow-wrap:anywhere}small{color:#a8bacb}select{background:#213e54;color:#eaf6ff;border:1px solid #66879e;border-radius:5px;padding:6px}#frame{accent-color:#80dff3;flex:1;min-width:150px}label{display:flex;align-items:center;gap:7px}#frameNumber{min-width:6ch;text-align:right}#instructions{font-size:12px}@media(max-width:540px){main{padding:8px}.labels{font-size:11px}button{padding:8px 10px}h1{font-size:17px}}
</style></head><body><main>
<header><h1>🐇 Hareworks · Independent Forward Woman Proof</h1><span class="pill">v0.1.3 · forward only · 30/60/120 fps checks</span></header>
<p>Left: the original <strong>Walking_Woman</strong>. Right: <strong>unchanged v0.1.2 generated pelvis, new reach-safe ankle trajectory, continuous knee-plane IK and analytically oriented feet</strong>. The generated side borrows only non-leg upper-body animation; no animated pelvis or leg tracks. v0.1.2 feet were visually rejected for snapping. Both use the same unchanged skinned GLB.</p>
<div class="labels"><strong>REFERENCE · source clip</strong><strong>GENERATED · fitted phase equations</strong></div>
<div id="status" role="status" aria-live="polite">Loading exact Hareworks source…</div>
<div id="stage" role="img" aria-label="Orbitable synchronized reference and procedural Hareworks 3D woman walking in place"></div>
<div class="cameraBar" role="group" aria-label="Camera controls"><strong>Camera:</strong><button id="side">Side</button><button id="front">Front</button><button id="top">Overhead</button><button id="oblique">Three-quarter</button><button id="resetCamera">Reset orbit</button><span id="instructions">Drag to orbit · pinch/scroll to zoom</span></div>
<div class="toolbar"><button id="play">Play one cycle</button><label>Playback <select id="playRate" aria-label="Playback sampling rate"><option value="60" selected>60 fps</option><option value="30">30 fps</option><option value="120">120 fps</option></select></label><label><input id="loop" type="checkbox" checked> Loop</label><button id="previous">◀ Frame</button><button id="next">Frame ▶</button><label>Frame <input type="range" min="0" max="28" step="1" value="0" id="frame" aria-label="Walk cycle frame"><output id="frameNumber">0/28</output></label><button id="test">Full 30/60/120 fps real-rig gate</button><button id="markers">Toggle joint markers</button><button id="export">Export evidence</button></div>
<div id="metrics" role="status" aria-live="off">Waiting for rig…</div>
<p><strong>Acceptance question:</strong> do the generated feet, knees, pitch and toe action match without popping, including near full extension and the cycle seam from side, front and overhead? This is a one-cycle <em>in-place leg-and-pelvis reproduction</em>, not world-space planted locomotion, strafing, turning or a complete game controller.</p>
<small>30 fps frame stepping remains available; high-rate playback defaults to 60 fps. The source extraction has an anomalous endpoint at exactly t=duration; the viewer excludes it. The gate samples 30, 60 and 120 Hz, checks joint rotations and tests atomic rollback. The model is hash-verified by the Termux launcher; real skinned acceptance is pending. Browser import uses Three.js 0.170.0 via CDN; camera requires pointer/touch events. Source GLB, v0.1.1, and other project assets are never modified.</small>
</main><script type="module" src="./viewer.mjs"></script></body></html>
__HAREWORKS_FW_V013_0__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/viewer.mjs" <<'__HAREWORKS_FW_V013_1__'
/* v0.1.3: ONE forward cycle, original reference against generated pelvis, IK
 * and foot motion. Reference tracks are never used as inputs to generated
 * pelvis, leg or ankle orientation. Upper body tracks remain reference-derived.
 * This does NOT claim root travel, planted sole contact or full procedural walk. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {independentPose,validateProfile,angleDiff} from '../v0.1.2/pose-kernel.mjs';
import {legAt,rotateY,kneeFromTarget,validateFootProfile} from './foot-kernel.mjs';

const $=id=>document.getElementById(id);
const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const Q=()=>new THREE.Quaternion();
const YA=V(0,1,0);
const SEP=2.75, FPS=30, SOURCE='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const names={
 left:['mixamorigLeftUpLeg','mixamorigLeftLeg','Bone_017','mixamorigLeftFoot','mixamorigLeftToeBase'],
 right:['mixamorigRightUpLeg','mixamorigRightLeg','Bone_013','mixamorigRightFoot','mixamorigRightToeBase']
};
const world=o=>o.getWorldPosition(V());
const wq=o=>o.getWorldQuaternion(Q());
const forwardYaw=q=>{const f=V(0,0,1).applyQuaternion(q);return Math.atan2(f.x,f.z)};
const rad=x=>THREE.MathUtils.radToDeg(x);
function rigOf(scene){
 const bones=new Map();scene.traverse(o=>{if(o.isBone){if(bones.has(o.name))throw Error('DUPLICATE_BONE_'+o.name);bones.set(o.name,o)}});
 if(bones.size!==74)throw Error('RIG_JOINT_COUNT_'+bones.size);
 const hips=bones.get('mixamorigHips'),spine=bones.get('mixamorigSpine');if(!hips||!spine)throw Error('HIPS_OR_SPINE_MISSING');
 const legs={};for(const [side,cn] of Object.entries(names)){
  const chain=cn.map(name=>{const b=bones.get(name);if(!b)throw Error('MISSING_BONE_'+name);return b});
  if(chain[0].parent!==hips||chain.some((b,i)=>i&&b.parent!==chain[i-1]))throw Error('LEG_HIERARCHY_'+side);
  legs[side]={chain,up:chain[0],knee:chain[1],ankle:chain[3],toe:chain[4]};
 }
 return {hips,spine,legs,bones};
}
function pose(b){return {position:b.position.clone(),quaternion:b.quaternion.clone(),scale:b.scale.clone()}}
function restore(b,p){b.position.copy(p.position);b.quaternion.copy(p.quaternion);b.scale.copy(p.scale)}
function setWorldBoneRotation(b,desired){const parent=wq(b.parent).invert();b.quaternion.copy(parent.multiply(desired)).normalize()}
function turnBoneToward(b,from,to){
 const a=from.clone().sub(world(b)),z=to.clone().sub(world(b));
 if(a.lengthSq()<1e-10||z.lengthSq()<1e-10)throw Error('ZERO_LENGTH_BONE_SOLVE');
 const delta=Q().setFromUnitVectors(a.normalize(),z.normalize());
 setWorldBoneRotation(b,delta.multiply(wq(b)));
}
// Atomic deterministic posing: a failed frame must never leave half a leg updated.
function takePose() {
 const state=[];
 generated.traverse(o=>{if(o.isBone)state.push([o,pose(o)])});
 return state;
}
function restorePose(state){for(const [bone,p] of state)restore(bone,p);generated.updateMatrixWorld(true)}
function poseMatches(state,tol=1e-10){
 return state.every(([bone,p])=>bone.position.distanceTo(p.position)<=tol && bone.quaternion.angleTo(p.quaternion)<=tol && bone.scale.distanceTo(p.scale)<=tol);
}
// Stable analytical foot orientation, no frame-history-dependent Newton solver.
// Align the toe vector then resolve the projected heading as a single twist.
function setFootProcedural(leg, desiredToeVector, desiredYaw) {
 const from=world(leg.toe).sub(world(leg.ankle));
 const to=V(...desiredToeVector);
 if(from.lengthSq()<1e-9||to.lengthSq()<1e-9)throw Error('ZERO_FOOT_VECTOR');
 const axis=to.normalize();
 const base=Q().setFromUnitVectors(from.normalize(),axis).multiply(wq(leg.ankle));
 const forward=V(0,0,1).applyQuaternion(base);
 const desired=V(Math.sin(desiredYaw),0,Math.cos(desiredYaw));
 const fp=forward.addScaledVector(axis,-forward.dot(axis));
 const dp=desired.addScaledVector(axis,-desired.dot(axis));
 if(fp.lengthSq()<1e-7||dp.lengthSq()<1e-7)throw Error('FOOT_HEADING_SINGULAR');
 fp.normalize();dp.normalize();
 const twist=Math.atan2(axis.dot(fp.clone().cross(dp)),fp.dot(dp));
 const solved=Q().setFromAxisAngle(axis,twist).multiply(base).normalize();
 setWorldBoneRotation(leg.ankle,solved);
}

const scene=new THREE.Scene();scene.background=new THREE.Color('#101821');
scene.add(new THREE.HemisphereLight(0xe2eeff,0x323d45,2.6));
const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(-4,7,3);scene.add(light);
const floor=new THREE.GridHelper(10,20,0x728390,0x3e4f5e);scene.add(floor);
const camera=new THREE.OrthographicCamera(-4,4,2,-2,.05,100);
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
$('stage').append(renderer.domElement);
const orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.dampingFactor=.1;orbit.enablePan=false;orbit.minZoom=.55;orbit.maxZoom=3.5;orbit.target.set(0,.9,0);
const presets={side:[-7,3.4,0],front:[0,2.3,9],top:[-.01,9,.01],oblique:[-6,4.5,5]};
function cameraPreset(k){camera.position.set(...presets[k]);orbit.target.set(0,.9,0);camera.up.set(0,1,0);camera.zoom=1;camera.lookAt(orbit.target);camera.updateProjectionMatrix();orbit.update()}
function resize(){const w=$('stage').clientWidth,h=Math.max(300,Math.min(590,Math.round(w*.69)));renderer.setSize(w,h,false);camera.left=-2.25*w/h;camera.right=-camera.left;camera.top=2.25;camera.bottom=-2.25;camera.updateProjectionMatrix();orbit.update()}
window.addEventListener('resize',resize);
for(const k of ['side','front','top','oblique'])$(k).onclick=()=>cameraPreset(k);
$('resetCamera').onclick=()=>cameraPreset('side');
cameraPreset('side');resize();
let reference,generated,refRig,genRig,refMixer,genMixer,clip,profile,footProfile,seed;
let running=false,playing=false,frame=0,last=performance.now(),elapsed=0,cycleT=0,markersVisible=false,markers=[],lastReport=null;
let nFrames=29;
function addMarkers(rig,cols){for(const side of ['left','right']){
 for(const part of ['ankle','knee']){
 const mat=new THREE.MeshBasicMaterial({color:cols[side],depthTest:false});
 const ball=new THREE.Mesh(new THREE.SphereGeometry(part==='ankle'?.03:.023,10,8),mat);ball.renderOrder=40;scene.add(ball);markers.push({ball,node:rig.legs[side][part]});
 }}}
function showMarkers(){for(const m of markers){m.ball.position.copy(world(m.node));m.ball.visible=markersVisible}}
function excludedTrackNames(root){
 const forbidden=new Set();for(const leg of Object.values(genRig.legs))for(const b of leg.chain)forbidden.add(b.name);
 let parent=genRig.hips;while(parent){if(parent.name)forbidden.add(parent.name);parent=parent.parent}
 const allowed=new Set();genRig.spine.traverse(o=>{if(o.isBone)allowed.add(o.name)});
 return {forbidden,allowed};
}
function applyGeneratedPose(t,fault=null){
 const sourceTime=Math.min(t,clip.duration-1e-6);
 const prediction=independentPose(profile,sourceTime);
 genMixer.setTime(sourceTime);
 for(const [b,p] of seed.legPose)restore(b,p);
 restore(genRig.hips,seed.hip);
 // The pelvis offset is in measured world units, transformed into the local
 // space of the hips parent. No source clip hip tracks are in genMixer.
 const delta=V(...prediction.pelvis).sub(V(...profile.zeroPelvis));
 const parent=genRig.hips.parent;generated.updateMatrixWorld(true);
 const localDelta=delta.applyQuaternion(wq(parent).invert());
 const parentScale=parent.getWorldScale(V());localDelta.set(localDelta.x/parentScale.x,localDelta.y/parentScale.y,localDelta.z/parentScale.z);
 genRig.hips.position.copy(seed.hip.position).add(localDelta);
 const dyaw=angleDiff(prediction.pelvisYaw,profile.zeroPelvisYaw);
 const parentQ=wq(parent),localYaw=parentQ.clone().invert().multiply(Q().setFromAxisAngle(YA,dyaw)).multiply(parentQ);
 genRig.hips.quaternion.copy(localYaw.multiply(seed.hip.quaternion)).normalize();
 generated.updateMatrixWorld(true);
 const pelvisYaw=forwardYaw(wq(genRig.hips));
 const rows=[];
 for(const side of ['left','right']){
  const leg=genRig.legs[side],f=legAt(footProfile,side,sourceTime),cfg=footProfile[side];
  const H=world(leg.up),vec=V(...rotateY(f.ankleLocal,pelvisYaw));
  const A=H.clone().add(vec);
  if(fault==='unreachable'&&side==='right')A.y+=2.0;
  const l1=world(leg.up).distanceTo(world(leg.knee));
  const l2=world(leg.knee).distanceTo(world(leg.ankle));
  if(Math.abs(l1-cfg.upperLength)>.009||Math.abs(l2-cfg.lowerLength)>.009)throw Error('LINK_LENGTH_MISMATCH_'+side);
  const K=V(...kneeFromTarget(H.toArray(),A.toArray(),l1,l2,rotateY(f.poleLocal,pelvisYaw)));
  turnBoneToward(leg.up,world(leg.knee),K);generated.updateMatrixWorld(true);
  turnBoneToward(leg.knee,world(leg.ankle),A);generated.updateMatrixWorld(true);
  const target=prediction.feet[side];
  setFootProcedural(leg,target.toeVector,target.ankleYaw);generated.updateMatrixWorld(true);
  const actualAnkle=world(leg.ankle),actualKnee=world(leg.knee),actualToe=world(leg.toe);
  const toeVector=actualToe.clone().sub(actualAnkle);
  const r={side,relativeForward:f.ankleLocal[2],reachMargin:(l1+l2)-H.distanceTo(A),hip:world(leg.up).toArray(),knee:actualKnee.toArray(),ankle:actualAnkle.toArray(),toe:actualToe.toArray(),
   ikResidual:actualAnkle.distanceTo(A),toeVectorDifferenceToCurve:toeVector.distanceTo(V(...target.toeVector)),
   ankleYawDifferenceToCurveDeg:rad(angleDiff(forwardYaw(wq(leg.ankle)),target.ankleYaw))};
  if(![r.ikResidual,r.toeVectorDifferenceToCurve,r.ankleYawDifferenceToCurveDeg,...r.hip,...r.knee,...r.ankle,...r.toe].every(Number.isFinite))throw Error('NONFINITE_GENERATED_POSE');
  if(r.ikResidual>.008)throw Error('IK_TARGET_RESIDUAL '+side+' '+r.ikResidual.toFixed(6));
  rows.push(r);
 }
 return {t:sourceTime,profilePhase:prediction.q,pelvis:world(genRig.hips).toArray(),pelvisYaw:pelvisYaw,legs:rows};
}
function evaluateTime(t, fault=null){
 if(!running)return null;
 t=Math.max(0,Math.min(t,clip.duration-1e-6));
 const before=takePose();
 try {
 refMixer.setTime(t);reference.updateMatrixWorld(true);
 const generatedPose=applyGeneratedPose(t,fault);
 const refPelvis=world(refRig.hips).add(V(0,0,SEP));
 const metrics={frame:Math.min(nFrames-1,Math.round(t*FPS)),t,hipDiff:world(genRig.hips).distanceTo(refPelvis),pelvisYawDiffDeg:rad(angleDiff(generatedPose.pelvisYaw,forwardYaw(wq(refRig.hips)))),legs:{}};
 for(const s of ['left','right']){
  const gen=genRig.legs[s],ref=refRig.legs[s],r=generatedPose.legs.find(x=>x.side===s);
  const refKnee=world(ref.knee).add(V(0,0,SEP)),refAnkle=world(ref.ankle).add(V(0,0,SEP)),refToe=world(ref.toe).add(V(0,0,SEP));
  metrics.legs[s]={forward:r.relativeForward,reachMargin:r.reachMargin,kneeDiff:world(gen.knee).distanceTo(refKnee),ankleDiff:world(gen.ankle).distanceTo(refAnkle),toeDiff:world(gen.toe).distanceTo(refToe),ikResidual:r.ikResidual,
   ankleYawDifferenceToReferenceDeg:rad(angleDiff(forwardYaw(wq(gen.ankle)),forwardYaw(wq(ref.ankle)))),
   toeVectorCurveResidual:r.toeVectorDifferenceToCurve,ankleYawCurveResidualDeg:r.ankleYawDifferenceToCurveDeg,
   upperQuat:gen.up.quaternion.toArray(),lowerQuat:gen.knee.quaternion.toArray(),footQuat:gen.ankle.quaternion.toArray()};
 }
 showMarkers();return metrics;
 }catch(e){restorePose(before);if(!poseMatches(before))throw Error('ATOMIC_ROLLBACK_FAILED '+e.message);throw e;}
}
function evaluate(f){return evaluateTime(f/FPS)}
function display(m){if(!m)return;
 $('frame').value=m.frame;$('frameNumber').textContent=`${m.frame}/${nFrames-1} (${m.t.toFixed(3)}s)`;
 $('metrics').textContent=`Frame ${m.frame}/${nFrames-1}, time ${m.t.toFixed(3)}s\nGenerated hips Δ ${m.hipDiff.toFixed(4)} units / yaw Δ ${m.pelvisYawDiffDeg.toFixed(2)}°\nLEFT   forward ${m.legs.left.forward.toFixed(3)}   ankle Δ ${m.legs.left.ankleDiff.toFixed(3)}  knee Δ ${m.legs.left.kneeDiff.toFixed(3)}  toe Δ ${m.legs.left.toeDiff.toFixed(3)}\nRIGHT  forward ${m.legs.right.forward.toFixed(3)}   ankle Δ ${m.legs.right.ankleDiff.toFixed(3)}  knee Δ ${m.legs.right.kneeDiff.toFixed(3)}  toe Δ ${m.legs.right.toeDiff.toFixed(3)}\nFoot yaw reference Δ ${m.legs.left.ankleYawDifferenceToReferenceDeg.toFixed(1)}° / ${m.legs.right.ankleYawDifferenceToReferenceDeg.toFixed(1)}°\nAnkle IK residual ${m.legs.left.ikResidual.toFixed(5)} / ${m.legs.right.ikResidual.toFixed(5)}`;
}
function sampleTime(t){try{const m=evaluateTime(t);frame=Math.floor(t*FPS)%nFrames;display(m)}catch(e){playing=false;$('status').textContent='BLOCKED_REAL_RIG '+e.message;console.error(e)}}
function sampleFrame(f){frame=(f+nFrames)%nFrames;cycleT=frame/FPS;sampleTime(cycleT)}
function render(now){requestAnimationFrame(render);const dt=Math.min(.065,(now-last)/1000);last=now;
 if(playing&&running){
  elapsed+=dt;
  const rate=Number($('playRate').value);
  let advances=0;
  while(elapsed>=1/rate&&advances<5){elapsed-=1/rate;cycleT+=1/rate;advances++;
   if(cycleT>=clip.duration){if(!$('loop').checked){cycleT=clip.duration-1/120;playing=false;$('play').textContent='Replay cycle';break}else cycleT=0}
  }
  if(advances>0)sampleTime(cycleT);
 }
 orbit.update();renderer.render(scene,camera);
}
requestAnimationFrame(render);
$('play').onclick=()=>{if(!running)return;if(!playing&&cycleT>clip.duration-.04)sampleFrame(0);playing=!playing;$('play').textContent=playing?'Pause':'Play cycle'};
$('previous').onclick=()=>{playing=false;$('play').textContent='Play cycle';sampleFrame(frame-1)};
$('next').onclick=()=>{playing=false;$('play').textContent='Play cycle';sampleFrame(frame+1)};
$('frame').oninput=()=>{playing=false;$('play').textContent='Play cycle';sampleFrame(Number($('frame').value))};
$('markers').onclick=()=>{markersVisible=!markersVisible;showMarkers()};
const jsonDownload=(filename,obj)=>{const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),4000)};
$('export').onclick=()=>{if(!lastReport){$('status').textContent='Run the 30 fps real-rig comparison first to create exportable evidence.';return}jsonDownload('hareworks-forward-foot-continuity-v0.1.3.json',lastReport)};
function runRealRigGate(auto=false){
 if(!running)return;
 playing=false;
 const max={pelvis:0,ankle:0,knee:0,toe:0,footYaw:0,IK:0,quatStep30:0,quatStep60:0,quatStep120:0},maxFront={left:-Infinity,right:-Infinity},minReach={left:Infinity,right:Infinity};
 const errors=[],rows=[],rateReports=[];const bones=['upperQuat','lowerQuat','footQuat'];
 for(const rate of [30,60,120]){
   const per=[];let lastRow=null,stepMax=0;
   const expected=Math.floor((clip.duration-1e-4)*rate)+1;
   for(let i=0;i<expected;i++){
    try{
     const r=evaluateTime(i/rate);per.push(r);
     if(rate===30)rows.push(r);
     max.pelvis=Math.max(max.pelvis,r.hipDiff);
     for(const side of ['left','right']){
       const v=r.legs[side];
       max.ankle=Math.max(max.ankle,v.ankleDiff);max.knee=Math.max(max.knee,v.kneeDiff);max.toe=Math.max(max.toe,v.toeDiff);
       max.footYaw=Math.max(max.footYaw,Math.abs(v.ankleYawDifferenceToReferenceDeg));max.IK=Math.max(max.IK,v.ikResidual);
       maxFront[side]=Math.max(maxFront[side],v.forward);minReach[side]=Math.min(minReach[side],v.reachMargin);
       if(lastRow){for(const bone of bones){const p=new THREE.Quaternion().fromArray(lastRow.legs[side][bone]);const q=new THREE.Quaternion().fromArray(v[bone]);stepMax=Math.max(stepMax,rad(p.angleTo(q)))}}
     }
     lastRow=r;
    }catch(e){errors.push({rate,frame:i,t:i/rate,message:e.message});break}
   }
   if(per.length>1){for(const side of ['left','right'])for(const bone of bones){const p=new THREE.Quaternion().fromArray(per.at(-1).legs[side][bone]),q=new THREE.Quaternion().fromArray(per[0].legs[side][bone]);stepMax=Math.max(stepMax,rad(p.angleTo(q)))}}
   max['quatStep'+rate]=stepMax;
   rateReports.push({fps:rate,expected,completed:per.length,maximumJointStepDeg:stepMax});
 }
 for(const side of ['left','right'])if(maxFront[side]<.30)errors.push({message:'NO_AHEAD_OF_HIP_SWING',side,value:maxFront[side]});
 if(max.IK>.008)errors.push({message:'IK_TARGET_RESIDUAL',value:max.IK});
 if(max.ankle>.040||max.knee>.050)errors.push({message:'REFERENCE_LEG_MISMATCH',ankle:max.ankle,knee:max.knee});
 if(max.pelvis>.030)errors.push({message:'PELVIS_REGRESSION',value:max.pelvis});
 if(minReach.left<0||minReach.right<0)errors.push({message:'UNREACHABLE_GEOMETRY',minReach});
 for(const [r,cap] of [[30,30],[60,18],[120,11]])if(max['quatStep'+r]>cap)errors.push({message:'JOINT_SNAP',fps:r,max:max['quatStep'+r],limit:cap});
 // Deliberately force an unreachable request to verify atomic rollback on the real rig.
 let injection='NOT_CHECKED';
 try{
   const before=takePose();
   try{evaluateTime(.12,'unreachable');injection='FAULT_WAS_NOT_REJECTED'}
   catch(e){injection=/UNREACHABLE_KNEE/.test(e.message)&&poseMatches(before)?'ROLLBACK_PASS':'ROLLBACK_FAIL '+e.message}
 }catch(e){injection='ROLLBACK_EXCEPTION '+e.message}
 if(injection!=='ROLLBACK_PASS')errors.push({message:'ATOMIC_INJECTED_FAILURE',detail:injection});
 const report={schema:'hareworks-forward-woman-v0.1.3-real-rig',sourceSha256:SOURCE,sourceClip:'Walking_Woman',pelvisImplementation:'v0.1.2 unchanged',legAnimationTracks:0,ankleTargets:'six-harmonic phase equation',anatomicalKneePoles:'six-harmonic phase equation',footOrientation:'analytical toe align and yaw twist',worldRootMotion:false,
  fpsRates:[30,60,120],rateReports,maxFront,minReach,maximumErrors:max,atomicInjection:injection,errors,rows,ownerAccepted:false,
  result:errors.length?'BLOCKED_REAL_RIG_PHYSICAL_GATE':'MEASURED_REQUIRES_OWNER_VISUAL_REVIEW'};
 lastReport=report;sampleFrame(0);
 $('status').textContent=report.result+' · '+rateReports.map(r=>r.completed+'/'+r.expected+' @'+r.fps).join(', ')+' · '+(errors[0]?.message||'review side/front/top at high playback rate');
 console.info('HAREWORKS_v013_REAL_RIG_GATE',report);
 if(!auto)jsonDownload('hareworks-forward-foot-continuity-v0.1.3.json',report);
}
$('test').onclick=()=>runRealRigGate(false);

try{
 const paths=['../v0.1.2/motion-profile.json','./foot-profile.json'];
 const loaded=await Promise.all([...paths.map(p=>fetch(p).then(r=>{if(!r.ok)throw Error('FETCH_'+p+'_'+r.status);return r.json()})),new GLTFLoader().loadAsync('../../../assets/hareworks/Hareworks-nine-clips.glb')]);
 [profile,footProfile]=loaded;const gltf=loaded[2];validateProfile(profile);validateFootProfile(footProfile);
 if(footProfile.sourceSha256!==SOURCE||profile.sourceSha256!==SOURCE)throw Error('MODEL_PARAMETER_SHA_MISMATCH');
 reference=gltf.scene;generated=cloneSkeleton(gltf.scene);reference.position.z=-SEP/2;generated.position.z=SEP/2;
 scene.add(reference,generated);reference.updateMatrixWorld(true);generated.updateMatrixWorld(true);
 const clips=gltf.animations;clip=clips.find(c=>c.name==='Walking_Woman');
 if(clips.length!==9||!clip||Math.abs(clip.duration-profile.duration)>.001)throw Error('SOURCE_CLIP_CONTRACT');
 refRig=rigOf(reference);genRig=rigOf(generated);
 refMixer=new THREE.AnimationMixer(reference);refMixer.clipAction(clip).reset().play();refMixer.setTime(0);
 const seedMixer=new THREE.AnimationMixer(generated);seedMixer.clipAction(clip).reset().play();seedMixer.setTime(0);
 const legPose=new Map();for(const leg of Object.values(genRig.legs))for(const b of leg.chain)legPose.set(b,pose(b));
 seed={hip:pose(genRig.hips),legPose};
 seedMixer.stopAllAction();seedMixer.uncacheRoot(generated);
 // Only bones in the Spine subtree are eligible for a source upper-body track.
 // Hip/root and both leg chains are explicitly excluded from the generated mixer.
 const {forbidden,allowed}=excludedTrackNames(generated);
 const allowedTracks=clip.tracks.filter(tr=>{const boneName=tr.name.replace(/\..*$/,'').replace(/\[.*$/,'');return allowed.has(boneName)&&!forbidden.has(boneName)});
 const excludedLeg=clip.tracks.filter(tr=>Object.values(names).flat().some(n=>tr.name.startsWith(n+'.')||tr.name.startsWith(n+'[')));
 const excludedHip=clip.tracks.filter(tr=>tr.name.startsWith(genRig.hips.name+'.')||tr.name.startsWith(genRig.hips.name+'['));
 if(excludedLeg.length<4||excludedHip.length<1||allowedTracks.length<1)throw Error('SOURCE_TRACK_FILTER_MISSING '+excludedLeg.length+' '+excludedHip.length+' '+allowedTracks.length);
 if(allowedTracks.some(tr=>!allowed.has(tr.name.split('.')[0])))throw Error('UNAUTHORIZED_GENERATED_TRACK');
 genMixer=new THREE.AnimationMixer(generated);genMixer.clipAction(new THREE.AnimationClip('upper_body_only',clip.duration,allowedTracks)).reset().play();
 profile.zeroPelvis=[profile.pelvis.x.start,profile.pelvis.y.start,profile.pelvis.z.start];profile.zeroPelvisYaw=profile.pelvis.yaw.start;
 addMarkers(refRig,{left:0x1ecbff,right:0xffb767});addMarkers(genRig,{left:0x1ecbff,right:0xffb767});
 floor.position.y=new THREE.Box3().setFromObject(reference).min.y;
 nFrames=Math.floor(clip.duration*FPS)+1;while((nFrames-1)/FPS>=clip.duration-1e-6)nFrames--;
 $('frame').max=nFrames-1;
 running=true;display(evaluate(0));resize();cameraPreset('side');
 $('status').textContent=`REAL SKINNED GLB READY v0.1.3 · ${excludedLeg.length} leg tracks and ${excludedHip.length} hip tracks excluded from generated animation; ${allowedTracks.length} upper-body tracks retained. Orbit viewer to judge results. Visual acceptance pending.`;
 runRealRigGate(true);
 console.info('HAREWORKS_v013_TRACK_AUDIT',{excludedLeg:excludedLeg.length,excludedHip:excludedHip.length,upperBody:allowedTracks.length,sourceSha:SOURCE});
}catch(e){running=false;$('status').textContent='BLOCKED_SOURCE_OR_RIG '+e.message;console.error(e)}
__HAREWORKS_FW_V013_1__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/foot-kernel.mjs" <<'__HAREWORKS_FW_V013_2__'
/* v0.1.3 forward-only Woman foot path and anatomical knee plane.
 * Six-harmonic, continuously looping PHASE FUNCTIONS fitted to the source.
 * Never accesses source animation tracks at runtime. The pelvis remains v0.1.2.
 * Source space: Y up; X lateral; Z forward; local offsets rotate by pelvis yaw.
 */
export function fourier(coeff, q) {
  if (!Array.isArray(coeff) || coeff.length !== 13) throw Error('FOOT_COEFFICIENT_SHAPE');
  let result = coeff[0];
  for (let n = 1; n <= 6; n++) {
    const angle = 2 * Math.PI * n * q;
    result += coeff[2*n-1]*Math.sin(angle) + coeff[2*n]*Math.cos(angle);
  }
  return result;
}
export const cyc = (t, duration) => ((t / duration) % 1 + 1) % 1;
export const rotateY = (v, yaw) => {
  const c=Math.cos(yaw),s=Math.sin(yaw);
  return [v[0]*c + v[2]*s,v[1],-v[0]*s + v[2]*c];
};
export const magnitude = v => Math.hypot(...v);
export const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
export const scale=(a,f)=>a.map(v=>v*f);
export const sub=(a,b)=>a.map((v,i)=>v-b[i]);
export const add=(a,b)=>a.map((v,i)=>v+b[i]);
export function legAt(profile, side, t) {
  const p=profile[side];if (!p) throw Error('UNKNOWN_LEG_'+side);
  const q=cyc(t,profile.duration);
  return {
    q,
    ankleLocal:p.ankle.map(coeff=>fourier(coeff,q)),
    poleLocal:p.pole.map(coeff=>fourier(coeff,q)),
  };
}
// Explicitly no hidden reach clamp: an out-of-range request must fail the gate.
// Pole is the fitted knee plane projected orthogonally to hip-to-ankle axis.
export function kneeFromTarget(hip,ankle,l1,l2,pole,eps=1e-5) {
  const dvec=sub(ankle,hip),d=magnitude(dvec),total=l1+l2;
  if (!(d < total + eps && d > Math.abs(l1-l2) + eps)) throw Error('UNREACHABLE_KNEE_'+d.toFixed(6)+'_REACH_'+total.toFixed(6));
  const u=scale(dvec,1/d), a=(l1*l1-l2*l2+d*d)/(2*d),height=Math.sqrt(Math.max(0,l1*l1-a*a));
  const projected=sub(pole,scale(u,dot(pole,u))),norm=magnitude(projected);
  if (norm < 1e-5) throw Error('KNEE_POLE_SINGULAR');
  return add(add(hip,scale(u,a)),scale(projected,height/norm));
}
export function validateFootProfile(p) {
 if (p.schema!=='hareworks-forward-woman-foot-pole-v0.1.3'||p.sourceSha256!=='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'||p.clip!=='Walking_Woman'||Math.abs(p.duration-.966667)>1e-4) throw Error('FOOT_PROFILE_IDENTITY');
 for(const side of ['left','right']){
   const s=p[side];if (!(s.upperLength>.2&&s.lowerLength>.2))throw Error('FOOT_LENGTH_INVALID');
   for(const ch of [...s.ankle,...s.pole]) if(ch.length!==13||!ch.every(Number.isFinite))throw Error('FOOT_FOURIER_INVALID');
 }
 return true;
}
__HAREWORKS_FW_V013_2__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/foot-kernel-test.mjs" <<'__HAREWORKS_FW_V013_3__'
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {legAt,rotateY,kneeFromTarget,validateFootProfile,magnitude,add,sub} from './foot-kernel.mjs';
const here=new URL('.',import.meta.url);
const profile=JSON.parse(readFileSync(new URL('./foot-profile.json',here)));
const witness=JSON.parse(readFileSync(new URL('./reference-leg-witnesses.json',here)));
assert.ok(validateFootProfile(profile));
assert.equal(witness.schema,'hareworks-forward-woman-leg-witnesses-v0.1.3');
assert.equal(witness.sourceSha256,profile.sourceSha256);
assert.equal(witness.samples.length,60);
const result={schema:'hareworks-forward-woman-v0.1.3-offline-geometry',sourceSha256:profile.sourceSha256,holdout:'odd source 60Hz frames; even for fitting',fps:[30,60,120,240],sides:{}};
for(const side of ['left','right']) {
 let maxAnkle=0,maxKnee=0,ankleSq=0,kneeSq=0,n=0;
 for(let i=1;i<witness.samples.length;i+=2){
  const sample=witness.samples[i],rig=sample.legs[side];
  const g=legAt(profile,side,sample.t);
  const ankle=add(rig.hip,rotateY(g.ankleLocal,sample.pelvisYaw));
  const knee=kneeFromTarget(rig.hip,ankle,profile[side].upperLength,profile[side].lowerLength,rotateY(g.poleLocal,sample.pelvisYaw));
  const ea=magnitude(sub(ankle,rig.ankle)),ek=magnitude(sub(knee,rig.knee));
  maxAnkle=Math.max(maxAnkle,ea);maxKnee=Math.max(maxKnee,ek);ankleSq+=ea*ea;kneeSq+=ek*ek;n++;
 }
 assert.ok(Math.sqrt(ankleSq/n)<.004,`${side} ankle holdout mismatch`);
 assert.ok(Math.sqrt(kneeSq/n)<.007,`${side} knee holdout mismatch`);
 let minReach=Infinity,maxFront=-Infinity,maxStep={};
 for(const fps of result.fps){
  let prev=null,maxIncrement=0;
  for(let i=0;i<=Math.floor(profile.duration*fps);i++){
   const t=i/fps;if(t>=profile.duration-.0001)continue;
   const g=legAt(profile,side,t),d=magnitude(g.ankleLocal),reach=profile[side].upperLength+profile[side].lowerLength;
   minReach=Math.min(minReach,reach-d);maxFront=Math.max(maxFront,g.ankleLocal[2]);
   assert.ok(d<reach,`${side} unreachable at ${fps}Hz t=${t} d=${d} limit=${reach}`);
   // No implied pose from a constant: exercise each actual profile and knee solver.
   const ankle=add([0,0,0],g.ankleLocal),knee=kneeFromTarget([0,0,0],ankle,profile[side].upperLength,profile[side].lowerLength,g.poleLocal);
   assert.ok(knee.every(Number.isFinite));
   if(prev)maxIncrement=Math.max(maxIncrement,magnitude(sub(ankle,prev)));
   prev=ankle;
  }
  maxStep[fps]=maxIncrement;
 }
 assert.ok(maxFront>.30,`${side} never advances ahead of hip`);
 assert.ok(minReach>.0007,`${side} too near reach singularity ${minReach}`);
 const a=legAt(profile,side,0),b=legAt(profile,side,profile.duration);
 assert.ok(magnitude(sub(a.ankleLocal,b.ankleLocal))<1e-9,`${side} loop geometry discontinuous`);
 result.sides[side]={holdoutSamples:n,ankleRms:Math.sqrt(ankleSq/n),kneeRms:Math.sqrt(kneeSq/n),maxAnkle,maxKnee,minReach,maxFront,maxAnkleStep:maxStep};
}
console.log('FOOT_KERNEL_TESTS=PASS');console.log(JSON.stringify(result,null,2));
__HAREWORKS_FW_V013_3__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/foot-profile.json" <<'__HAREWORKS_FW_V013_4__'
{
  "schema": "hareworks-forward-woman-foot-pole-v0.1.3",
  "sourceSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "clip": "Walking_Woman",
  "duration": 0.966667,
  "method": "6-harmonic, 30 even-index fit, 30 odd-index held-out 60Hz walking-woman foot offsets and anatomical knee-plane pole",
  "left": {
    "ankle": [
      [
        0.02854385688204203,
        -0.013888590775110076,
        0.042294019753224235,
        -0.014952959511449803,
        -0.013499964021537803,
        -0.007384213898269611,
        -0.0001467604813308883,
        -0.0023329741084401065,
        0.002844892029392568,
        0.00046120713539806406,
        0.00028269473139828574,
        -0.00043941442429309426,
        0.00013627868235402594
      ],
      [
        -0.6744177081405048,
        0.018736595310296353,
        0.04315432487820422,
        -0.020529304948040752,
        -0.012873813746135608,
        -0.018718995702214095,
        -0.0030726847261065954,
        -0.008726523124394594,
        0.0025496095736690077,
        -0.000984451632576692,
        0.000308501688694451,
        0.0018165308402986477,
        -0.001046891045715517
      ],
      [
        0.05797608665949965,
        0.29624523676569836,
        -0.06573486565220502,
        0.05427167465638952,
        -0.030866628925778666,
        -0.0017750713858325103,
        -0.009324249393638637,
        -0.002469142259805482,
        0.0005480857432989624,
        -0.0014402803160686994,
        0.0019233544787885127,
        -0.00021676120563033608,
        0.0003117596502001467
      ]
    ],
    "pole": [
      [
        -0.27710668551822903,
        -0.20340554353180335,
        -0.022204289053622577,
        0.025876197679405136,
        0.06453334886929311,
        -0.008527232525312872,
        0.045613237607246,
        0.0028915981627794115,
        -0.018647786739792446,
        0.022306727789073673,
        -0.002830889093537341,
        0.004916748539183904,
        -0.010451811099645898
      ],
      [
        0.046067790829032236,
        0.37369766124966486,
        -0.11008376647967041,
        0.07930519410537815,
        -0.018268245411523595,
        0.018120444489706927,
        -0.005792101734193144,
        0.006515544134323375,
        -0.00035967196209780176,
        0.002764459800650883,
        0.0009815262158050831,
        0.00010134874233479181,
        -0.0031412140017072613
      ],
      [
        0.8994068964173648,
        -0.09111322207839229,
        -0.017220701033640786,
        0.015160841339450722,
        0.06733508891532795,
        0.017664435186227134,
        0.027217939599335945,
        0.010211762235080574,
        0.0009502225563170089,
        0.0066603709476433385,
        -0.002132289439816591,
        0.0011364248335238322,
        -0.007113981148637661
      ]
    ],
    "upperLength": 0.35676909129295376,
    "lowerLength": 0.38032400937227195
  },
  "right": {
    "ankle": [
      [
        -0.01220725068723768,
        0.006905461787533918,
        0.04231852245073466,
        0.010226270770663825,
        0.012806971565717098,
        -0.007647456367931789,
        -0.0037646490755362874,
        0.003243983145575807,
        -0.0014041697814376212,
        -9.999141501731091e-05,
        -4.473658789637564e-06,
        -0.0007019646175164999,
        -1.9537527694351323e-05
      ],
      [
        -0.6781861735711474,
        -0.021286946310646267,
        -0.041079413123210576,
        -0.013713422580446591,
        -0.016074147654936803,
        0.015160629236096913,
        0.00924141739766458,
        -0.010012513889308836,
        -0.0020380442676407665,
        0.0037363453555316816,
        -0.0016142739486872419,
        0.0005608656030439065,
        0.001117078665082672
      ],
      [
        0.045713899334612645,
        -0.31091949660459806,
        0.053630510851797465,
        0.07464383395653863,
        -0.023673328159617445,
        -0.006416217374226314,
        0.016065462336947573,
        -0.005480298470102732,
        -0.005022143643801818,
        0.005879917449764852,
        -0.0001491280110532899,
        -0.0028644993134213717,
        0.002483031421092533
      ]
    ],
    "pole": [
      [
        0.19314059982708748,
        0.07803002132931339,
        0.05846224700931056,
        0.07406728878246134,
        -0.07352136667067626,
        -0.029917155374917848,
        0.06144963132098001,
        0.015836447170706553,
        0.036462633544470185,
        0.04977389193385242,
        -0.001957095948712472,
        -0.006522977698584801,
        0.013587933042246142
      ],
      [
        0.06028679150059591,
        -0.41374930379462355,
        0.08867905226290704,
        0.10711672502524351,
        -0.034119211728449075,
        -0.01877561515758951,
        0.01583165211993897,
        0.0015051884358490335,
        4.0772648852464496e-05,
        0.006126427684743693,
        -0.0006052639299986503,
        -0.003423357725806976,
        -0.0017067794979714476
      ],
      [
        0.9192331203988192,
        0.008578402767001683,
        0.011670901351420767,
        -0.004505684563913476,
        0.05985323243560457,
        -0.0008216760882766581,
        -0.036383251194239415,
        0.0038129569496690055,
        -0.005278045860632771,
        -0.018439834224670146,
        0.0016424708818886604,
        0.0005179303845259715,
        -0.0005443716831372606
      ]
    ],
    "upperLength": 0.3479932766261441,
    "lowerLength": 0.390377129245554
  }
}
__HAREWORKS_FW_V013_4__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/reference-leg-witnesses.json" <<'__HAREWORKS_FW_V013_5__'
{"schema":"hareworks-forward-woman-leg-witnesses-v0.1.3","sourceSha256":"a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6","sourceReportSchema":"hareworks-gait-and-idle-turn-v1.0.8","sourceClip":"Walking_Woman","sampling":"60 source frames strictly before duration; holdout odd indices; calibrated on even","duration":0.966667,"samples":[{"t":0,"pelvisYaw":0.18521718701095075,"legs":{"left":{"hip":[0.071316,0.905387,0.096975],"knee":[0.090923,0.580018,0.242009],"ankle":[0.122703,0.260144,0.038744],"toe":[0.152138,0.167294,-0.001792]},"right":{"hip":[-0.062096,0.920859,0.120764],"knee":[-0.021762,0.58172,0.187528],"ankle":[-0.008507,0.191808,0.20121],"toe":[-0.047971,0.094231,0.241999]}}},{"t":0.016111,"pelvisYaw":0.1703646634613494,"legs":{"left":{"hip":[0.073206,0.90727,0.096379],"knee":[0.087465,0.587844,0.254645],"ankle":[0.124612,0.250332,0.08332],"toe":[0.154427,0.153393,0.054263]},"right":{"hip":[-0.060644,0.921441,0.118455],"knee":[-0.021818,0.580393,0.17571],"ankle":[-0.010498,0.190192,0.178871],"toe":[-0.050021,0.092184,0.218553]}}},{"t":0.032222,"pelvisYaw":0.15558625778186014,"legs":{"left":{"hip":[0.07509,0.909161,0.095804],"knee":[0.083449,0.596173,0.266837],"ankle":[0.124846,0.244124,0.129016],"toe":[0.154715,0.144402,0.111872]},"right":{"hip":[-0.059164,0.922042,0.11615],"knee":[-0.021573,0.579376,0.163754],"ankle":[-0.011914,0.18919,0.156269],"toe":[-0.051442,0.090737,0.194829]}}},{"t":0.048333,"pelvisYaw":0.1343668258485819,"legs":{"left":{"hip":[0.07736,0.909073,0.095646],"knee":[0.08105,0.600071,0.273937],"ankle":[0.126206,0.235862,0.174139],"toe":[0.156882,0.13507,0.168623]},"right":{"hip":[-0.057392,0.920514,0.113393],"knee":[-0.022354,0.576468,0.152173],"ankle":[-0.014172,0.186645,0.133051],"toe":[-0.053482,0.08806,0.171494]}}},{"t":0.064444,"pelvisYaw":0.11275899426403757,"legs":{"left":{"hip":[0.079644,0.908847,0.095549],"knee":[0.078386,0.603726,0.280439],"ankle":[0.125873,0.231255,0.219972],"toe":[0.157,0.130636,0.22609]},"right":{"hip":[-0.055549,0.918855,0.110612],"knee":[-0.022843,0.573687,0.140429],"ankle":[-0.015718,0.184605,0.109468],"toe":[-0.054696,0.08586,0.147842]}}},{"t":0.080556,"pelvisYaw":0.08824782894604943,"legs":{"left":{"hip":[0.082191,0.907651,0.096115],"knee":[0.077384,0.604729,0.284529],"ankle":[0.125657,0.227932,0.266089],"toe":[0.157458,0.128873,0.283594]},"right":{"hip":[-0.053421,0.916047,0.108075],"knee":[-0.023743,0.569945,0.128853],"ankle":[-0.017023,0.181945,0.08636],"toe":[-0.055598,0.08303,0.124702]}}},{"t":0.096667,"pelvisYaw":0.06334889889703664,"legs":{"left":{"hip":[0.084753,0.906309,0.096823],"knee":[0.076468,0.6053,0.288158],"ankle":[0.124091,0.228738,0.312237],"toe":[0.156287,0.132429,0.340846]},"right":{"hip":[-0.051192,0.913081,0.105594],"knee":[-0.024288,0.56632,0.117073],"ankle":[-0.017436,0.179771,0.062962],"toe":[-0.055481,0.080624,0.101235]}}},{"t":0.112778,"pelvisYaw":0.039547131887606085,"legs":{"left":{"hip":[0.086996,0.904264,0.098471],"knee":[0.076644,0.604958,0.292358],"ankle":[0.122539,0.232768,0.355721],"toe":[0.154719,0.140165,0.394703]},"right":{"hip":[-0.04917,0.909811,0.104126],"knee":[-0.025258,0.562641,0.104472],"ankle":[-0.018297,0.177645,0.040249],"toe":[-0.056319,0.07826,0.07792]}}},{"t":0.128889,"pelvisYaw":0.01604597375552917,"legs":{"left":{"hip":[0.089131,0.90204,0.100381],"knee":[0.077003,0.604391,0.296703],"ankle":[0.120234,0.240336,0.397903],"toe":[0.152119,0.152407,0.446713]},"right":{"hip":[-0.04717,0.90647,0.102935],"knee":[-0.025834,0.55932,0.091487],"ankle":[-0.018354,0.176098,0.017463],"toe":[-0.056388,0.076429,0.054364]}}},{"t":0.145,"pelvisYaw":-0.004067708635633959,"legs":{"left":{"hip":[0.090683,0.898989,0.103211],"knee":[0.077563,0.603532,0.302753],"ankle":[0.117976,0.248541,0.433117],"toe":[0.149295,0.165676,0.490415]},"right":{"hip":[-0.045653,0.903051,0.103052],"knee":[-0.026752,0.556417,0.078827],"ankle":[-0.019905,0.175186,-0.004901],"toe":[-0.058283,0.074959,0.030086]}}},{"t":0.161111,"pelvisYaw":-0.022900186095453707,"legs":{"left":{"hip":[0.091999,0.895624,0.106388],"knee":[0.078128,0.602606,0.309446],"ankle":[0.115462,0.257702,0.46531],"toe":[0.146036,0.180414,0.53029]},"right":{"hip":[-0.044312,0.899599,0.103666],"knee":[-0.027387,0.554035,0.066264],"ankle":[-0.021368,0.175046,-0.027147],"toe":[-0.060158,0.074179,0.005464]}}},{"t":0.177222,"pelvisYaw":-0.03935702071182589,"legs":{"left":{"hip":[0.093542,0.891059,0.11024],"knee":[0.079107,0.601713,0.318458],"ankle":[0.113495,0.262915,0.487809],"toe":[0.142868,0.190288,0.558471]},"right":{"hip":[-0.042703,0.895145,0.105264],"knee":[-0.027384,0.551055,0.055597],"ankle":[-0.023368,0.174941,-0.048888],"toe":[-0.062222,0.073224,-0.01912]}}},{"t":0.193333,"pelvisYaw":-0.05456276410968913,"legs":{"left":{"hip":[0.095198,0.885863,0.114445],"knee":[0.080227,0.600934,0.32863],"ankle":[0.111786,0.265641,0.505349],"toe":[0.139711,0.197185,0.580611]},"right":{"hip":[-0.040948,0.890164,0.107379],"knee":[-0.026896,0.547924,0.04595],"ankle":[-0.025281,0.175274,-0.070344],"toe":[-0.063964,0.072629,-0.043702]}}},{"t":0.209444,"pelvisYaw":-0.06616825376061237,"legs":{"left":{"hip":[0.096938,0.881257,0.117856],"knee":[0.081367,0.599274,0.335864],"ankle":[0.110639,0.264321,0.513617],"toe":[0.136651,0.197355,0.590879]},"right":{"hip":[-0.039121,0.885431,0.109219],"knee":[-0.02507,0.545086,0.038036],"ankle":[-0.026235,0.176392,-0.090252],"toe":[-0.064632,0.07251,-0.068424]}}},{"t":0.225556,"pelvisYaw":-0.07523209074600297,"legs":{"left":{"hip":[0.098741,0.877067,0.12071],"knee":[0.082553,0.59694,0.341052],"ankle":[0.110018,0.260045,0.51539],"toe":[0.133819,0.192567,0.592919]},"right":{"hip":[-0.037247,0.880875,0.110867],"knee":[-0.022425,0.542408,0.031371],"ankle":[-0.026724,0.178152,-0.108963],"toe":[-0.064748,0.073045,-0.093179]}}},{"t":0.241667,"pelvisYaw":-0.08018560374337601,"legs":{"left":{"hip":[0.100933,0.87578,0.123312],"knee":[0.083876,0.592677,0.339751],"ankle":[0.109389,0.254174,0.511249],"toe":[0.131702,0.183716,0.586537]},"right":{"hip":[-0.035031,0.878703,0.112857],"knee":[-0.019802,0.541693,0.027465],"ankle":[-0.027919,0.182208,-0.12452],"toe":[-0.063448,0.075276,-0.117772]}}},{"t":0.257778,"pelvisYaw":-0.08132579694623228,"legs":{"left":{"hip":[0.103487,0.877209,0.125678],"knee":[0.085436,0.586856,0.332204],"ankle":[0.108906,0.247048,0.501397],"toe":[0.130411,0.171529,0.571859]},"right":{"hip":[-0.032495,0.878763,0.115165],"knee":[-0.017325,0.542695,0.026126],"ankle":[-0.030213,0.188262,-0.136986],"toe":[-0.061284,0.079865,-0.14218]}}},{"t":0.273889,"pelvisYaw":-0.08179323469318528,"legs":{"left":{"hip":[0.106013,0.878818,0.128858],"knee":[0.0863,0.582526,0.326612],"ankle":[0.107206,0.239584,0.489706],"toe":[0.129471,0.159101,0.554182]},"right":{"hip":[-0.02998,0.879156,0.118376],"knee":[-0.016063,0.543177,0.028801],"ankle":[-0.032512,0.195277,-0.147521],"toe":[-0.059779,0.087178,-0.165224]}}},{"t":0.29,"pelvisYaw":-0.08144076459075932,"legs":{"left":{"hip":[0.108509,0.880646,0.13304],"knee":[0.086233,0.579841,0.323575],"ankle":[0.103858,0.231757,0.475805],"toe":[0.128827,0.146626,0.532899]},"right":{"hip":[-0.027493,0.879959,0.122697],"knee":[-0.016232,0.543012,0.036446],"ankle":[-0.034798,0.20367,-0.15564],"toe":[-0.059094,0.097783,-0.186297]}}},{"t":0.306111,"pelvisYaw":-0.08104877534836259,"legs":{"left":{"hip":[0.111333,0.882781,0.136845],"knee":[0.08689,0.577748,0.32026],"ankle":[0.101809,0.224849,0.461281],"toe":[0.128203,0.135687,0.511119]},"right":{"hip":[-0.024671,0.880919,0.126674],"knee":[-0.01729,0.542127,0.047523],"ankle":[-0.037333,0.213389,-0.162058],"toe":[-0.058483,0.111506,-0.205817]}}},{"t":0.322222,"pelvisYaw":-0.08055745974902692,"legs":{"left":{"hip":[0.114691,0.885414,0.140035],"knee":[0.088759,0.57647,0.316573],"ankle":[0.101958,0.219063,0.445926],"toe":[0.127673,0.126243,0.488981]},"right":{"hip":[-0.021303,0.882131,0.130085],"knee":[-0.019582,0.540403,0.064371],"ankle":[-0.040205,0.225601,-0.165563],"toe":[-0.058212,0.12991,-0.222671]}}},{"t":0.338333,"pelvisYaw":-0.07862202063464137,"legs":{"left":{"hip":[0.118107,0.888431,0.142578],"knee":[0.09068,0.575618,0.31193],"ankle":[0.101929,0.213774,0.428501],"toe":[0.127714,0.118871,0.466698]},"right":{"hip":[-0.017876,0.883744,0.133056],"knee":[-0.021788,0.539413,0.082855],"ankle":[-0.043385,0.238276,-0.164622],"toe":[-0.058521,0.150722,-0.234246]}}},{"t":0.354444,"pelvisYaw":-0.07341394120544903,"legs":{"left":{"hip":[0.121661,0.892287,0.143687],"knee":[0.092562,0.575565,0.305316],"ankle":[0.10111,0.209142,0.406844],"toe":[0.128511,0.114672,0.444989]},"right":{"hip":[-0.014327,0.886232,0.135045],"knee":[-0.02408,0.539714,0.104552],"ankle":[-0.046339,0.249577,-0.155678],"toe":[-0.058846,0.172091,-0.236805]}}},{"t":0.370556,"pelvisYaw":-0.06890731308659537,"legs":{"left":{"hip":[0.124988,0.896097,0.144181],"knee":[0.094431,0.575546,0.297797],"ankle":[0.100416,0.205384,0.384922],"toe":[0.129031,0.111266,0.423045]},"right":{"hip":[-0.010979,0.888654,0.136334],"knee":[-0.025914,0.541116,0.12666],"ankle":[-0.048686,0.26016,-0.143414],"toe":[-0.060388,0.191073,-0.231915]}}},{"t":0.386667,"pelvisYaw":-0.06651876229025133,"legs":{"left":{"hip":[0.127617,0.899741,0.142762],"knee":[0.09642,0.57518,0.287577],"ankle":[0.100546,0.202369,0.362686],"toe":[0.129251,0.10828,0.400816]},"right":{"hip":[-0.008292,0.890844,0.135433],"knee":[-0.027881,0.543672,0.149096],"ankle":[-0.049234,0.264569,-0.123007],"toe":[-0.064529,0.194119,-0.20987]}}},{"t":0.402778,"pelvisYaw":-0.06486321870242424,"legs":{"left":{"hip":[0.129986,0.903393,0.141214],"knee":[0.098248,0.574967,0.276908],"ankle":[0.10056,0.199978,0.340346],"toe":[0.129318,0.105917,0.378503]},"right":{"hip":[-0.005851,0.893182,0.134289],"knee":[-0.029314,0.547964,0.17135],"ankle":[-0.048959,0.269114,-0.101141],"toe":[-0.067904,0.196889,-0.185798]}}},{"t":0.418889,"pelvisYaw":-0.06661198571705809,"legs":{"left":{"hip":[0.131145,0.907046,0.139067],"knee":[0.099486,0.574522,0.264405],"ankle":[0.100463,0.198004,0.318069],"toe":[0.129135,0.103972,0.356364]},"right":{"hip":[-0.004633,0.896178,0.131989],"knee":[-0.029631,0.554404,0.192528],"ankle":[-0.046876,0.268287,-0.072489],"toe":[-0.070011,0.192127,-0.152531]}}},{"t":0.435,"pelvisYaw":-0.06843325363276435,"legs":{"left":{"hip":[0.132148,0.910649,0.136924],"knee":[0.100709,0.574341,0.251784],"ankle":[0.10038,0.196562,0.295708],"toe":[0.128939,0.102527,0.334077]},"right":{"hip":[-0.003574,0.899212,0.129673],"knee":[-0.029744,0.562367,0.21304],"ankle":[-0.044907,0.268301,-0.04326],"toe":[-0.072129,0.188336,-0.11814]}}},{"t":0.451111,"pelvisYaw":-0.07086689273178969,"legs":{"left":{"hip":[0.131821,0.913809,0.134818],"knee":[0.101631,0.573941,0.239042],"ankle":[0.100238,0.195212,0.273809],"toe":[0.128593,0.100941,0.311748]},"right":{"hip":[-0.003899,0.902564,0.127213],"knee":[-0.02848,0.570987,0.229937],"ankle":[-0.043023,0.261648,-0.007745],"toe":[-0.072967,0.175632,-0.07443]}}},{"t":0.467222,"pelvisYaw":-0.07300061799414023,"legs":{"left":{"hip":[0.131469,0.916901,0.132688],"knee":[0.102516,0.573822,0.226192],"ankle":[0.100011,0.194367,0.251759],"toe":[0.128137,0.099853,0.289263]},"right":{"hip":[-0.004249,0.90586,0.124767],"knee":[-0.027107,0.580601,0.246354],"ankle":[-0.041002,0.256996,0.028453],"toe":[-0.073513,0.165685,-0.029407]}}},{"t":0.483333,"pelvisYaw":-0.06674595316262086,"legs":{"left":{"hip":[0.130473,0.918081,0.129883],"knee":[0.103703,0.572314,0.213626],"ankle":[0.100168,0.192338,0.229485],"toe":[0.128252,0.097617,0.266496]},"right":{"hip":[-0.005331,0.907597,0.122705],"knee":[-0.025035,0.587881,0.258692],"ankle":[-0.041279,0.246504,0.070031],"toe":[-0.075243,0.149156,0.024074]}}},{"t":0.499444,"pelvisYaw":-0.060508556666022624,"legs":{"left":{"hip":[0.129471,0.919266,0.127079],"knee":[0.104669,0.571104,0.200919],"ankle":[0.099888,0.190859,0.207044],"toe":[0.127866,0.095914,0.243558]},"right":{"hip":[-0.006412,0.909336,0.120647],"knee":[-0.022627,0.595775,0.2707],"ankle":[-0.040193,0.239228,0.112713],"toe":[-0.0752,0.137249,0.079289]}}},{"t":0.515556,"pelvisYaw":-0.046455523443138615,"legs":{"left":{"hip":[0.12776,0.919403,0.124398],"knee":[0.105946,0.569056,0.188154],"ankle":[0.1003,0.188789,0.184732],"toe":[0.128335,0.09363,0.220638]},"right":{"hip":[-0.008274,0.910647,0.119705],"knee":[-0.020716,0.602389,0.280706],"ankle":[-0.04131,0.231082,0.161953],"toe":[-0.077135,0.126135,0.14086]}}},{"t":0.531667,"pelvisYaw":-0.032165385741569796,"legs":{"left":{"hip":[0.126,0.919517,0.121729],"knee":[0.106845,0.567293,0.175167],"ankle":[0.100003,0.187254,0.162134],"toe":[0.12801,0.091852,0.197411]},"right":{"hip":[-0.010155,0.91195,0.118819],"knee":[-0.018472,0.609289,0.29036],"ankle":[-0.040886,0.22742,0.212462],"toe":[-0.077149,0.120863,0.203922]}}},{"t":0.547778,"pelvisYaw":-0.014379200353257515,"legs":{"left":{"hip":[0.123288,0.918635,0.119271],"knee":[0.108044,0.564866,0.162851],"ankle":[0.10143,0.18531,0.139605],"toe":[0.129241,0.089603,0.174205]},"right":{"hip":[-0.012982,0.912801,0.11859],"knee":[-0.017401,0.616102,0.300385],"ankle":[-0.041346,0.227769,0.268468],"toe":[-0.07775,0.12099,0.272384]}}},{"t":0.563889,"pelvisYaw":0.003779672967327321,"legs":{"left":{"hip":[0.120431,0.917657,0.116856],"knee":[0.108846,0.56265,0.150326],"ankle":[0.10222,0.183879,0.11664],"toe":[0.1297,0.087817,0.150514]},"right":{"hip":[-0.015896,0.913615,0.11846],"knee":[-0.016157,0.623202,0.310187],"ankle":[-0.040844,0.233891,0.325104],"toe":[-0.077149,0.128253,0.341376]}}},{"t":0.58,"pelvisYaw":0.020767026397290802,"legs":{"left":{"hip":[0.117842,0.915485,0.115322],"knee":[0.110259,0.559587,0.139061],"ankle":[0.105083,0.182031,0.093553],"toe":[0.132368,0.085556,0.126396]},"right":{"hip":[-0.018478,0.912884,0.119101],"knee":[-0.015948,0.627342,0.317993],"ankle":[-0.039932,0.242583,0.379475],"toe":[-0.075365,0.139809,0.409879]}}},{"t":0.596111,"pelvisYaw":0.0375179887599168,"legs":{"left":{"hip":[0.11529,0.913071,0.113985],"knee":[0.11146,0.556593,0.127866],"ankle":[0.107608,0.180693,0.07015],"toe":[0.134644,0.08377,0.101861]},"right":{"hip":[-0.020972,0.91184,0.119914],"knee":[-0.01591,0.630975,0.325312],"ankle":[-0.039445,0.256303,0.432373],"toe":[-0.073991,0.158429,0.476752]}}},{"t":0.612222,"pelvisYaw":0.05405104495975427,"legs":{"left":{"hip":[0.113068,0.909285,0.114112],"knee":[0.112602,0.552547,0.118784],"ankle":[0.110176,0.179022,0.047231],"toe":[0.137223,0.081546,0.077187]},"right":{"hip":[-0.023086,0.908698,0.122232],"knee":[-0.015607,0.630235,0.330802],"ankle":[-0.03802,0.267087,0.472279],"toe":[-0.070846,0.174863,0.528487]}}},{"t":0.628333,"pelvisYaw":0.07052816708318371,"legs":{"left":{"hip":[0.110943,0.905059,0.114708],"knee":[0.113461,0.548326,0.110296],"ankle":[0.112018,0.177829,0.024413],"toe":[0.139073,0.079769,0.05239]},"right":{"hip":[-0.025063,0.904893,0.125029],"knee":[-0.0152,0.628085,0.335694],"ankle":[-0.036869,0.278122,0.507307],"toe":[-0.067953,0.192639,0.574156]}}},{"t":0.644444,"pelvisYaw":0.08744214544109562,"legs":{"left":{"hip":[0.109029,0.898707,0.114909],"knee":[0.113773,0.542143,0.103776],"ankle":[0.113465,0.175844,0.001447],"toe":[0.14065,0.077202,0.02716]},"right":{"hip":[-0.026785,0.898757,0.127506],"knee":[-0.0156,0.625701,0.342947],"ankle":[-0.03532,0.280984,0.525089],"toe":[-0.064645,0.201294,0.599466]}}},{"t":0.660556,"pelvisYaw":0.10455115079509175,"legs":{"left":{"hip":[0.107199,0.891398,0.114933],"knee":[0.113774,0.535086,0.098126],"ankle":[0.11436,0.174056,-0.021473],"toe":[0.141678,0.074853,0.001827]},"right":{"hip":[-0.02838,0.891573,0.129839],"knee":[-0.016262,0.623321,0.351183],"ankle":[-0.033063,0.279562,0.535418],"toe":[-0.060476,0.205241,0.615837]}}},{"t":0.676667,"pelvisYaw":0.11909438630089914,"legs":{"left":{"hip":[0.105291,0.885656,0.115279],"knee":[0.112225,0.529674,0.092637],"ankle":[0.114993,0.174099,-0.04229],"toe":[0.142423,0.073988,-0.023425]},"right":{"hip":[-0.030061,0.886141,0.132121],"knee":[-0.016588,0.62048,0.356491],"ankle":[-0.030603,0.27346,0.534748],"toe":[-0.05625,0.202434,0.618651]}}},{"t":0.692778,"pelvisYaw":0.1320793318439705,"legs":{"left":{"hip":[0.103336,0.880873,0.115824],"knee":[0.109708,0.525304,0.087282],"ankle":[0.115501,0.175434,-0.061728],"toe":[0.143023,0.074438,-0.048579]},"right":{"hip":[-0.03179,0.881784,0.134373],"knee":[-0.01673,0.617311,0.360043],"ankle":[-0.02811,0.26473,0.527231],"toe":[-0.052105,0.195594,0.613176]}}},{"t":0.708889,"pelvisYaw":0.1405026901661199,"legs":{"left":{"hip":[0.101245,0.87794,0.116798],"knee":[0.107404,0.52293,0.081951],"ankle":[0.116974,0.178433,-0.078911],"toe":[0.143643,0.076499,-0.073552]},"right":{"hip":[-0.033726,0.879546,0.136402],"knee":[-0.01646,0.612898,0.359337],"ankle":[-0.025507,0.255164,0.515348],"toe":[-0.047849,0.183483,0.599639]}}},{"t":0.725,"pelvisYaw":0.145229265068788,"legs":{"left":{"hip":[0.099046,0.876514,0.11812],"knee":[0.105233,0.522222,0.076613],"ankle":[0.119146,0.182793,-0.094387],"toe":[0.144148,0.080382,-0.098565]},"right":{"hip":[-0.035834,0.879032,0.138248],"knee":[-0.015993,0.607559,0.355061],"ankle":[-0.02314,0.245057,0.499754],"toe":[-0.04388,0.16746,0.579069]}}},{"t":0.741111,"pelvisYaw":0.14871059287345206,"legs":{"left":{"hip":[0.096664,0.876112,0.119755],"knee":[0.103646,0.522418,0.073533],"ankle":[0.121261,0.188543,-0.107749],"toe":[0.144175,0.086614,-0.122446]},"right":{"hip":[-0.038144,0.879511,0.140237],"knee":[-0.015658,0.603306,0.350723],"ankle":[-0.020992,0.236709,0.484785],"toe":[-0.042644,0.153368,0.557776]}}},{"t":0.757222,"pelvisYaw":0.1508513455649889,"legs":{"left":{"hip":[0.094085,0.876804,0.121724],"knee":[0.102794,0.523503,0.072875],"ankle":[0.123542,0.19564,-0.118756],"toe":[0.143898,0.095465,-0.14485]},"right":{"hip":[-0.040672,0.881053,0.142378],"knee":[-0.015416,0.600228,0.346335],"ankle":[-0.018948,0.230159,0.470559],"toe":[-0.04423,0.141567,0.535786]}}},{"t":0.773333,"pelvisYaw":0.1527415502191336,"legs":{"left":{"hip":[0.091284,0.877475,0.123779],"knee":[0.101879,0.524127,0.075647],"ankle":[0.124124,0.203678,-0.12798],"toe":[0.142023,0.106733,-0.165554]},"right":{"hip":[-0.04342,0.882726,0.144547],"knee":[-0.015401,0.596967,0.341158],"ankle":[-0.01658,0.224081,0.456697],"toe":[-0.045813,0.130611,0.512831]}}},{"t":0.789444,"pelvisYaw":0.15427078139492897,"legs":{"left":{"hip":[0.088165,0.878117,0.125953],"knee":[0.100821,0.524122,0.08339],"ankle":[0.123012,0.213196,-0.134506],"toe":[0.139022,0.121201,-0.183611]},"right":{"hip":[-0.046481,0.884588,0.146755],"knee":[-0.015658,0.593462,0.334891],"ankle":[-0.013617,0.218492,0.443461],"toe":[-0.047204,0.120696,0.48874]}}},{"t":0.805556,"pelvisYaw":0.15472449904139382,"legs":{"left":{"hip":[0.085043,0.878883,0.127704],"knee":[0.099731,0.523934,0.094849],"ankle":[0.122539,0.224344,-0.13833],"toe":[0.135516,0.138702,-0.198559]},"right":{"hip":[-0.049556,0.886562,0.148397],"knee":[-0.016708,0.590925,0.329005],"ankle":[-0.011611,0.213052,0.426887],"toe":[-0.047999,0.113362,0.465357]}}},{"t":0.821667,"pelvisYaw":0.15310274800675094,"legs":{"left":{"hip":[0.08192,0.879878,0.128645],"knee":[0.098249,0.523812,0.113336],"ankle":[0.122494,0.238633,-0.137127],"toe":[0.129912,0.160827,-0.207991]},"right":{"hip":[-0.052662,0.888741,0.148964],"knee":[-0.019166,0.58989,0.32408],"ankle":[-0.011387,0.207891,0.404146],"toe":[-0.047462,0.108678,0.444117]}}},{"t":0.837778,"pelvisYaw":0.15188592921514776,"legs":{"left":{"hip":[0.078936,0.881052,0.128678],"knee":[0.096312,0.52472,0.131713],"ankle":[0.12348,0.253118,-0.133128],"toe":[0.126687,0.182849,-0.211757]},"right":{"hip":[-0.055607,0.89117,0.148674],"knee":[-0.021389,0.588768,0.317438],"ankle":[-0.011305,0.20378,0.381287],"toe":[-0.047168,0.104973,0.422437]}}},{"t":0.853889,"pelvisYaw":0.15173057034725415,"legs":{"left":{"hip":[0.076323,0.882689,0.12633],"knee":[0.094586,0.527134,0.149377],"ankle":[0.125177,0.264554,-0.12405],"toe":[0.12685,0.197611,-0.205576]},"right":{"hip":[-0.058132,0.894247,0.146136],"knee":[-0.022914,0.58736,0.306384],"ankle":[-0.010944,0.200694,0.358736],"toe":[-0.046958,0.102105,0.400276]}}},{"t":0.87,"pelvisYaw":0.15261736282614055,"legs":{"left":{"hip":[0.073885,0.884776,0.123578],"knee":[0.092699,0.531066,0.166233],"ankle":[0.125675,0.275141,-0.113161],"toe":[0.127211,0.210082,-0.1962]},"right":{"hip":[-0.060447,0.897756,0.14334],"knee":[-0.02422,0.5861,0.293863],"ankle":[-0.0106,0.198255,0.336118],"toe":[-0.046856,0.099859,0.377904]}}},{"t":0.886111,"pelvisYaw":0.15757728096683843,"legs":{"left":{"hip":[0.072136,0.888559,0.119285],"knee":[0.091917,0.537524,0.179842],"ankle":[0.125312,0.278728,-0.096845],"toe":[0.13297,0.210498,-0.176948]},"right":{"hip":[-0.061981,0.902896,0.13956],"knee":[-0.024454,0.584988,0.276035],"ankle":[-0.009846,0.196724,0.313887],"toe":[-0.046744,0.098456,0.355411]}}},{"t":0.902222,"pelvisYaw":0.16320420272950079,"legs":{"left":{"hip":[0.070552,0.892344,0.1149],"knee":[0.091238,0.544934,0.193403],"ankle":[0.124248,0.281823,-0.079231],"toe":[0.137996,0.21045,-0.155699]},"right":{"hip":[-0.063333,0.907912,0.135793],"knee":[-0.024619,0.584378,0.257965],"ankle":[-0.009259,0.195743,0.291457],"toe":[-0.046859,0.097612,0.332674]}}},{"t":0.918333,"pelvisYaw":0.17314247375835626,"legs":{"left":{"hip":[0.070038,0.896079,0.10993],"knee":[0.091048,0.553542,0.207451],"ankle":[0.12173,0.277518,-0.052387],"toe":[0.141492,0.200344,-0.121555]},"right":{"hip":[-0.063588,0.912111,0.132087],"knee":[-0.023643,0.583617,0.239768],"ankle":[-0.008371,0.194655,0.269265],"toe":[-0.046737,0.096652,0.310078]}}},{"t":0.934444,"pelvisYaw":0.18249014861723536,"legs":{"left":{"hip":[0.069614,0.899753,0.105029],"knee":[0.091139,0.563045,0.220998],"ankle":[0.119947,0.274413,-0.024985],"toe":[0.145423,0.192257,-0.086074]},"right":{"hip":[-0.063761,0.916183,0.128377],"knee":[-0.022866,0.583378,0.221474],"ankle":[-0.007939,0.194111,0.246834],"toe":[-0.047091,0.096262,0.287269]}}},{"t":0.950556,"pelvisYaw":0.18385672187871982,"legs":{"left":{"hip":[0.070465,0.902569,0.101002],"knee":[0.091059,0.571214,0.231631],"ankle":[0.121423,0.266219,0.006459],"toe":[0.148989,0.17815,-0.044673]},"right":{"hip":[-0.062929,0.91852,0.12457],"knee":[-0.022333,0.582289,0.20457],"ankle":[-0.008226,0.192656,0.2241],"toe":[-0.047536,0.094942,0.264708]}}}]}
__HAREWORKS_FW_V013_5__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/README.md" <<'__HAREWORKS_FW_V013_6__'
# Hareworks Forward Woman: reach / knee / foot continuity proof v0.1.3

**Mission boundary:** Repair the user's rejected v0.1.2 foot and knee motion on the actual 74-joint, nine-clip Hareworks skinned GLB. Forward `Walking_Woman` in-place reference versus generated motion **only**. Preserve v0.1.2 independent pelvis/hip equations and upper-body reference treatment exactly. No turning, walking backward, strafing, world-root locomotion, foot-plant controller, asset replacement, or alteration of the old campaigns.

**Owner's evidence:** high-frame-rate recording `5361.mp4` revealed foot popping; the v0.1.2 viewer reported `BLOCKED_REAL_RIG_UNREACHABLE_KNEE` at hip-to-ankle distances about 0.736–0.740. The precise skinned behavior of this release still needs the user's review.

## Changes and why

1. The old v0.1.1 ankle path used a simplified stance/swing forward interpolation and independent vertical/lateral harmonics. It occasionally requested geometry outside the actual physical reach in v0.1.2. New **six-harmonic ankle trajectory** is fitted in pelvis-yaw-relative, hip-relative coordinates from the exact `Walking_Woman` 60 Hz joint extraction, using 30 even-index training samples and 30 odd-index held-out samples. It has C-infinity periodic position continuity. Forward reach is ~0.394 left and ~0.402 right, close to source measurements.
2. The moving **knee-bend pole** is fitted from measured reference knee-plane normals instead of using a fixed pole, preserving the bend side throughout the cycle. Each frame still solves knee position using actual upper and lower anatomical lengths. There is **no silent target clamp**; an unreachable leg remains a hard diagnostic error.
3. The old foot twist used five Newton iterations against a world-yaw target and could produce discontinuities or singularities. New foot orientation uses one deterministic swing-to-toe alignment followed by one analytical twist around the toe axis. The generated foot does not read original clip ankle rotations at runtime. Rotation continuity and mismatch from the original are measured against the live GLB.
4. A failing frame now **rolls back all generated bone positions/quaternions/scales** atomically, rather than leaving half a pose on screen. A deliberate injected unreachable-right-leg test must fail and verify the previous real-skinned pose is restored.
5. Playback defaults to **60 fps**, selectable 30, 60 or 120 fps, with loop and the original orbit/zoom camera. The actual-rig gate samples full **30/60/120 Hz** cycles plus wraparound, measures hip/knee/ankle/toe errors and every successive leg joint quaternion step, and checks the injected failure. It runs automatically on load and can export a full JSON receipt from the viewer.

## Offline source fit (not runtime acceptance)

The source is the user's browser-exported `hareworks-nine-clip-gait-and-idle-turn-v1.0.8.json`, hash-labelled canonical GLB `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`. The new profile retains 6 sine/cosine pairs per component rather than samples/keyframes. Node/Python tests evaluate held-out source poses and check the actual fitted ankle and knee targets at 30, 60, 120 and 240 Hz.

| Offline held-out sample RMS | Left | Right |
|---|---:|---:|
| Ankle position | 0.001629 | 0.001751 |
| Anatomical knee position | 0.003043 | 0.003575 |
| Minimum geometry reach margin | 0.002317 | 0.001025 |

These are **mathematical fit results**, not proof that the skinned mesh is good or that its feet plant. The actual skinned pose uses the existing nonuniform 5-node Hareworks leg chains; failure to meet numerical gates is reported, not dismissed.

## Acceptance gates and limitations

- Real 74-joint GLB is pinned by exact LFS SHA/size; original `Walking_Woman` clip is compared with generated motion from multiple viewing angles. Source model is read-only and copied only to an isolated HTTP viewer snapshot.
- The generated side must have no original hip, root, or leg animation tracks. The original `Walking_Woman` serves only the reference and unchanged upper-body subtree on generated side.
- Automated real-model diagnostics: 29 frames at 30 fps, 58 at 60 fps, 116 at 120 fps; all expected frames must evaluate; both feet move ahead of the hips; no unreachable knee; ankle residual <= 0.008 model units; 3D knee and ankle reference discrepancies <= 0.05 and <= 0.04 respectively; maximum per-sample joint quaternion changes at 30/60/120 fps <= 30/18/11 degrees; no injected-fault pose corruption. These limits are explicit provisional tests, **not visually accepted thresholds**.
- No claim of fully independent world locomotion, planted outsole or friction, accepted physics, validated heel-ground force, or polished gait. The fitted pelvis, toe vectors and ankle yaw remain phase-based and source-calibrated. A real video or owner's review is required for quality approval.
- If a physical test fails, preserve the viewer and export the exact failure, then refine within this original forward-leg-only scope. Do not retroactively call the experiment successful.

## Authority, provenance and transport

- Repo: `Valar05/parametric-parambulator`, `main`. Parent commit is pinned at campaign generation.
- Rules: root `AGENTS.md`, Home Center Campaign Etiquette ID `1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI`, Top-Down Etiquette ID `1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU` reread on 2026-11-20.
- Publication: **Termux Git only**, fresh isolated snapshot, unique paths, hash-pinned embedded files, scope-only staging, exact remote commit/tree readback. Original GLB, source clips, v0.1.1/v0.1.2, Repl, and Boneforge are immutable.
- Results: Termux launch verifies Git + local HTTP byte serving; Android WebGL and true skinned gait gate execute separately inside the viewer; owner visual approval is last. No local host test can stand in for Termux execution or browser evidence.
__HAREWORKS_FW_V013_6__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/contract.json" <<'__HAREWORKS_FW_V013_7__'
{
  "campaign": "hareworks-forward-woman-proof-v0.1.3",
  "repository": "Valar05/parametric-parambulator",
  "auditedParentCommit": "429cef2c1d26f81d58bcb6196eb80dd065b51168",
  "modelPath": "assets/hareworks/Hareworks-nine-clips.glb",
  "modelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "modelBytes": 6784896,
  "executionLane": "Android Termux Git only",
  "sourceClip": "Walking_Woman",
  "ownerRejected": "v0.1.2 generated feet and knees snap; preserve hips",
  "goal": "Forward-only Woman walking, 74-joint real-skinned reference versus continuous reach-safe procedural feet and knee pole; 30/60/120fps gate and atomic rollback",
  "immutablePaths": ["AGENTS.md", "assets/repl/Repl.glb", "assets/hareworks/Hareworks.glb", "assets/hareworks/Hareworks-nine-clips.glb", "tools/hareworks-forward-woman/v0.1.1", "tools/hareworks-forward-woman/v0.1.2"],
  "newOutputs": ["tools/hareworks-forward-woman/v0.1.3/index.html", "tools/hareworks-forward-woman/v0.1.3/viewer.mjs", "tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs", "tools/hareworks-forward-woman/v0.1.3/foot-kernel-test.mjs", "tools/hareworks-forward-woman/v0.1.3/foot-profile.json", "tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json", "tools/hareworks-forward-woman/v0.1.3/README.md", "tools/hareworks-forward-woman/v0.1.3/contract.json", "campaigns/hareworks-forward-woman-proof-v0.1.3.sh"],
  "immutableV012Pelvis": "tools/hareworks-forward-woman/v0.1.2/motion-profile.json",
  "successGates": ["script SHA guarded", "exact LFS source SHA and GLB rig verified", "30 held-out raw source ankle and knee witnesses", "30/60/120/240fps path and reach offline tests", "isolated Termux Git commit and exact remote readback", "real GLB browser loaded and real-rig 30/60/120fps continuity gate", "real-body foot and knee visual evaluation by owner"],
  "nonclaims": ["not approved animation", "not world-root walking", "not 3D physics", "not force/ground validated", "not demonstrated on phone until owner's actual run"]
}
__HAREWORKS_FW_V013_7__
fi
if ((PUBLISHED==0));then
 cp -- "$0" "campaigns/$CAMPAIGN.sh" || fail 'cannot install exact launcher source'
fi
phase='packet-hash'
[[ "$(hash "$DIR/index.html")" == '1fca336fdca0e0ed1ecb6fa2dffcbbdb8cb5f417bb52c7bbafe95231a04bfbdb' ]] || fail 'packet SHA mismatch: index.html'
[[ "$(hash "$DIR/viewer.mjs")" == '6cb46f446469f07df7f3e1b122b1a40a12d59b765e487177d212125652c78a53' ]] || fail 'packet SHA mismatch: viewer.mjs'
[[ "$(hash "$DIR/foot-kernel.mjs")" == '35ff314aba97b7e5fbf5035046cdb2607cbe369730fbc1f5d53d93ca0d986728' ]] || fail 'packet SHA mismatch: foot-kernel.mjs'
[[ "$(hash "$DIR/foot-kernel-test.mjs")" == 'ef8ab32301a17dc69b72beb528e46923b92db7b0ac0183cb6022e666e07764ab' ]] || fail 'packet SHA mismatch: foot-kernel-test.mjs'
[[ "$(hash "$DIR/foot-profile.json")" == '80deb7b695ec057ec993ae316a2ab01ce5ad59e950988bb4635d5bef513ea1c8' ]] || fail 'packet SHA mismatch: foot-profile.json'
[[ "$(hash "$DIR/reference-leg-witnesses.json")" == '5049e1e1c0ffb214f06d19bc4d7c9d000fa1adc925a083cb15ccfa8ec7b5bb78' ]] || fail 'packet SHA mismatch: reference-leg-witnesses.json'
[[ "$(hash "$DIR/README.md")" == '4621d08eb4ae8fb2ef57d930ba15b718d54a6dcebbc1a6e8980305cb90bb90fb' ]] || fail 'packet SHA mismatch: README.md'
[[ "$(hash "$DIR/contract.json")" == '8d852b1eee4d62eafda7787f2214c5fc3a8cab7afd4a676584c9419c5301c43e' ]] || fail 'packet SHA mismatch: contract.json'
[[ "$(hash "campaigns/$CAMPAIGN.sh")" == "$(hash "$0")" ]] || fail 'launcher/repository packet differs'
phase='validation'
python3 - "$DIR/foot-profile.json" "$DIR/reference-leg-witnesses.json" "$DIR/contract.json" "$MODEL_SHA" <<'PY_VERIFY' || fail 'real-source 60fps ankle/knee fit failed'
import json,sys,math
p,r,c=(json.load(open(f)) for f in sys.argv[1:4]);sha=sys.argv[4]
assert p['sourceSha256']==r['sourceSha256']==c['modelSha256']==sha
assert p['clip']==r['sourceClip']==c['sourceClip']=='Walking_Woman'
assert len(r['samples'])==60 and abs(p['duration']-0.966667)<.0001
assert all(r['samples'][i]['t']<r['samples'][i+1]['t'] for i in range(59))
def evalch(coeff,q):return coeff[0]+sum(coeff[2*k-1]*math.sin(2*math.pi*k*q)+coeff[2*k]*math.cos(2*math.pi*k*q) for k in range(1,7))
def norm(a):return math.sqrt(sum(x*x for x in a))
def minus(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
for side in ('left','right'):
 cfg=p[side];l1=cfg['upperLength'];l2=cfg['lowerLength'];amin=1e9;maxfront=-1e9;erra=[];errk=[]
 for k in range(241):
  q=k/240;a=[evalch(x,q) for x in cfg['ankle']];d=norm(a);amin=min(amin,l1+l2-d);maxfront=max(maxfront,a[2]);assert abs(l1-l2)+.00001<d<l1+l2
 assert maxfront>.30 and amin>.0007,(side,maxfront,amin)
 for i in range(1,60,2):
  row=r['samples'][i];q=row['t']/p['duration'];ref=row['legs'][side]
  yaw=row['pelvisYaw'];cs=math.cos(yaw);sn=math.sin(yaw)
  rot=lambda v:[v[0]*cs+v[2]*sn,v[1],v[2]*cs-v[0]*sn]
  delta=rot([evalch(ch,q) for ch in cfg['ankle']]);H=ref['hip'];A=[h+d for h,d in zip(H,delta)]
  pole=rot([evalch(ch,q) for ch in cfg['pole']]);d=norm(delta);axis=[x/d for x in delta]
  along=(l1*l1-l2*l2+d*d)/(2*d);height=math.sqrt(max(0,l1*l1-along*along))
  dotp=dot(pole,axis);pole=[v-dotp*u for v,u in zip(pole,axis)];n=norm(pole);assert n>.01
  K=[h+u*along+p0/n*height for h,u,p0 in zip(H,axis,pole)]
  erra.append(norm(minus(A,ref['ankle'])));errk.append(norm(minus(K,ref['knee'])))
 assert (sum(v*v for v in erra)/30)**.5<.004
 assert (sum(v*v for v in errk)/30)**.5<.007
 print('HELDOOUT_30_SAMPLES',side,'ankleRms=',(sum(x*x for x in erra)/30)**.5,'kneeRms=',(sum(x*x for x in errk)/30)**.5,'minimumReach=',amin)
print('REAL_SOURCE_FORWARD_FOOT_FIT=PASS, BROWSER_REAL_RIG=PENDING')
PY_VERIFY
if command -v node >/dev/null;then
 node --check "$DIR/foot-kernel.mjs" || fail 'foot-kernel JS syntax failure'
 node --check "$DIR/viewer.mjs" || fail 'viewer JS syntax failure'
 node --check "$DIR/foot-kernel-test.mjs" || fail 'test JS syntax failure'
 node "$DIR/foot-kernel-test.mjs" > "$STATE/offline-foot-test.jsonlog" || fail 'held-out original foot trajectory test failed'
 node tools/hareworks-forward-woman/v0.1.2/pose-kernel-test.mjs > "$STATE/preserved-pelvis-test.log" || fail 'preserved v0.1.2 pelvis test regressed'
 node tools/hareworks-forward-woman/v0.1.1/kinematics-test.mjs > "$STATE/prior-leg-test.log" || fail 'prior independent leg kernel test regressed'
 echo 'OFFLINE_FOOT_AND_PELVIS_TESTS=PASS'
else
 echo 'NODE_NOT_INSTALLED=YES; Python holdout passed, browser 30/60/120fps real-rig gate is mandatory'
fi
if ((PUBLISHED==0));then
 phase='staging'
 [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote advanced before commit'
 git add -- "${FILES[@]}" || fail 'scoped text staging failed'
 python3 - "${FILES[@]}" <<'PY_SCOPE' || fail 'Git staging differs from explicit new-file allowlist'
import subprocess,sys
allowed=set(sys.argv[1:]);staged=set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines())
assert staged==allowed,(sorted(allowed-staged),sorted(staged-allowed))
for name in staged:
 assert not name.endswith('.glb')
print('STAGED_ONLY_NEW_TEXT_FILES=PASS',len(staged))
PY_SCOPE
 for f in AGENTS.md assets/repl/Repl.glb assets/hareworks/Hareworks.glb "$MODEL" tools/hareworks-forward-woman/v0.1.2/motion-profile.json tools/hareworks-forward-woman/v0.1.2/viewer.mjs;do
  git diff --quiet -- "$f" || fail "protected worktree content changed: $f"
  [[ "$(git rev-parse "HEAD:$f")" == "$(git rev-parse "$BASE:$f")" ]] || fail "protected Git blob changed: $f"
 done
 phase='commit'
 git -c user.name='Hareworks Termux Campaign' -c user.email='hareworks-campaign@users.noreply.github.com' commit -m 'Test Hareworks forward woman leg reach and continuous foot solving v0.1.3' || fail 'commit failed'
 COMMIT=$(git rev-parse HEAD)
 [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'commit parent mismatch'
 phase='publish'
 [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote advanced, refusing non-fast-forward publication'
 GIT_LFS_SKIP_PUSH=1 git push origin HEAD:refs/heads/main || fail "push failed; local commit preserved at $COMMIT"
else
 COMMIT="$REMOTE"
fi
phase='remote-readback'
[[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$COMMIT" ]] || fail 'published main SHA did not read back'
GIT_LFS_SKIP_SMUDGE=1 git fetch --depth=1 origin main || fail 'remote readback fetch failed'
[[ "$(git rev-parse FETCH_HEAD)" == "$COMMIT" ]] || fail 'fetched commit differs from published SHA'
for p in "${FILES[@]}";do
 [[ "$(git rev-parse "FETCH_HEAD:$p")" == "$(git rev-parse "HEAD:$p")" ]] || fail "remote packet file differs: $p"
done
for f in AGENTS.md assets/repl/Repl.glb assets/hareworks/Hareworks.glb "$MODEL" tools/hareworks-forward-woman/v0.1.2/viewer.mjs tools/hareworks-forward-woman/v0.1.2/motion-profile.json;do
 [[ "$(git rev-parse "FETCH_HEAD:$f")" == "$(git rev-parse "$BASE:$f")" ]] || fail "immutable remote file differs: $f"
done
echo "EXACT_REMOTE_READBACK=PASS $COMMIT"
phase='viewer'
# The only working-tree GLB copy is in a disposable viewer snapshot, never Git staged.
cp -- "$SOURCE" "$MODEL" || fail 'viewer source model could not be mounted'
[[ "$(hash "$MODEL")" == "$MODEL_SHA" ]] || fail 'viewer snapshot model digest mismatch'
cat > "$ROOT/server.py" <<'PY_SERVER'
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
PY_SERVER
READY="$ROOT/server-ready.json"
nohup python3 "$ROOT/server.py" "$WORK" "$READY" > "$ROOT/server.log" 2>&1 </dev/null &
PID=$!
PORT='';READY_OK=0
for i in 1 2 3 4 5 6 7 8 9 10;do
 if [[ -f "$READY" ]];then
  PORT=$(python3 - "$READY" <<'PY_PORT'
import json,sys
print(json.load(open(sys.argv[1]))['port'])
PY_PORT
)
  if curl -fsS --max-time 3 "http://127.0.0.1:$PORT/$DIR/index.html" >/dev/null 2>&1 && \
     curl -fsS --max-time 3 "http://127.0.0.1:$PORT/$DIR/viewer.mjs" >/dev/null 2>&1 && \
     curl -fsS --max-time 3 "http://127.0.0.1:$PORT/$DIR/motion-profile.json" >/dev/null 2>&1;then READY_OK=1;break;fi
 fi
 sleep 1
done
[[ "$READY_OK" == 1 ]] && kill -0 "$PID" 2>/dev/null || fail 'HTTP viewer server failed; inspect snapshot/server.log'
curl -sSI --max-time 5 "http://127.0.0.1:$PORT/$DIR/index.html" > "$STATE/http-headers.txt" || fail 'HTTP response headers unavailable'
MODEL_HTTP_SHA=$(curl -fsS --max-time 45 "http://127.0.0.1:$PORT/$MODEL" | sha256sum | cut -d' ' -f1) || fail 'HTTP GLB GET failed'
[[ "$MODEL_HTTP_SHA" == "$MODEL_SHA" ]] || fail 'HTTP-served GLB digest mismatch'
URL="http://127.0.0.1:$PORT/$DIR/index.html?commit=$COMMIT"
python3 - "$STATE/receipt.json" "$CAMPAIGN" "$BASE" "$COMMIT" "$MODEL_SHA" "$AGENTS_BLOB" "$URL" "$PID" "$PORT" "$ROOT" <<'PY_RECEIPT'
import json,datetime,sys,pathlib
out,campaign,base,commit,model,agents,url,pid,port,root=sys.argv[1:]
receipt={'campaign':campaign,'phase':'git_published_http_verified_browser_pending','timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'auditedBaseCommit':base,'publishedCommit':commit,'modelSha256':model,'agentsGitBlob':agents,
 'rulesRead':{'agents':'exact repository Git blob verified in Termux','campaignEtiquette':'Home Center live document 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI read during authoring 2026-11-20','topDownEtiquette':'Home Center live document 1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU read during authoring 2026-11-20'},
 'ownerRejectedVersion':'v0.1.2 foot and knee motion','previousComparedVersion':'v0.1.2','mode':'forward-only skinned reference-vs-generated unmodified pelvis and continuous reach-safe foot and knee IK','viewerUrl':url,'viewerPort':int(port),'viewerPid':int(pid),'snapshot':root,
 'networkModelBytesVerified':True,'mutatingExecutionLane':'Termux Git only','modelsAndPriorProofChanged':False,
 'browserRealRigCompleted':False,'browserRealRigCheck':'auto-run 30/60/120 fps on load; not part of Termux HTTP receipt','ownerVisualAcceptance':False,'worldSpacePlantedFootstepController':False}
pathlib.Path(out).write_text(json.dumps(receipt,indent=2))
PY_RECEIPT
echo "REMOTE_COMMIT=$COMMIT"
echo "MODEL_SHA256=$MODEL_SHA"
echo "VIEWER_PORT=$PORT PID=$PID"
echo "VIEWER_URL=$URL"
echo "RECEIPT=$STATE/receipt.json"
echo 'REAL_SKINNED_30_60_120FPS_AND_OWNER_VISUAL_ACCEPTANCE=PENDING'
if command -v termux-open-url >/dev/null;then termux-open-url "$URL" || echo "BROWSER_LAUNCH_FAILED; OPEN $URL";else echo "TERMUX_OPEN_URL_UNAVAILABLE; OPEN $URL";fi
