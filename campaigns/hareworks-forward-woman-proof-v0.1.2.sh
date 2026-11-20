#!/data/data/com.termux/files/usr/bin/bash
# Hareworks forward Woman proof v0.1.2. Reference vs independent procedural pelvis
# and foot orientation; orbit camera; NO forward world locomotion/turning/strafe.
# Only approved mutation/execution: Termux Git. Previous source remains immutable.
set -Eeuo pipefail
CAMPAIGN='hareworks-forward-woman-proof-v0.1.2'
REPO='Valar05/parametric-parambulator'
BASE='f322307c46e561443c3e0177ef309332fb51834d'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_BYTES=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
LOCKED_PREV_KERNEL='1ef0a40d0ccb156cecad0644d7399a64983ce468'
LOCKED_PREV_PROFILE='8071c18019f02fe3e56e4a89ed9b31bc5c3ae106'
DIR='tools/hareworks-forward-woman/v0.1.2'
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
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.1/gait-kernel.mjs)" == "$LOCKED_PREV_KERNEL" ]] || fail 'accepted procedural leg source changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.1/profile.json)" == "$LOCKED_PREV_PROFILE" ]] || fail 'accepted leg profile changed'
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_BYTES" <<'PY_PTR' || fail 'source LFS pointer changed'
import subprocess,sys
path,oid,size=sys.argv[1:]
pointer=subprocess.check_output(['git','show','HEAD:'+path]);expected=(f'version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize {size}\n').encode()
assert pointer==expected,(pointer[:100],expected)
print('PUBLISHED_SOURCE_POINTER=PASS')
PY_PTR
FILES=("$DIR/index.html" "$DIR/viewer.mjs" "$DIR/pose-kernel.mjs" "$DIR/pose-kernel-test.mjs" "$DIR/motion-profile.json" "$DIR/reference-samples.json" "$DIR/README.md" "$DIR/contract.json" "campaigns/$CAMPAIGN.sh")
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
 cat > "$DIR/index.html" <<'__HAREWORKS_FW_V012_0__'
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#101821"><title>Hareworks | Independent Woman Leg / Pelvis Proof v0.1.2</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>
:root{font:14px system-ui,sans-serif;color:#edf5ff;background:#101821;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:1150px;margin:auto;padding:12px}h1{font-size:19px;margin:3px 0}header{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center}p{line-height:1.45;color:#bcd0df;margin:8px 0}.pill{border:1px solid #51667c;padding:5px 9px;border-radius:20px;color:#cde1ef;font-size:11px}#status{padding:10px 0;color:#a4e9d7;min-height:43px}#stage{border:1px solid #506579;border-radius:10px;overflow:hidden;background:#09121b}#stage canvas{width:100%;display:block;touch-action:none}.labels{display:grid;grid-template-columns:1fr 1fr;text-align:center;gap:10px;margin:8px 0;color:#d8eaf6;font-size:12px}.toolbar,.cameraBar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}.cameraBar{background:#182a39;padding:8px;border-radius:8px}button{font:inherit;background:#2a455d;color:white;border:1px solid #617f98;border-radius:7px;min-height:42px;padding:9px 12px}button:focus-visible{outline:3px solid #7ae1fa}button:active{background:#456780}#metrics{white-space:pre-wrap;background:#1a2c3b;padding:10px;border-radius:7px;border:1px solid #435b6a;font:12px/1.5 ui-monospace,monospace;overflow-wrap:anywhere}small{color:#a8bacb}#frame{accent-color:#80dff3;flex:1;min-width:150px}label{display:flex;align-items:center;gap:7px}#frameNumber{min-width:6ch;text-align:right}#instructions{font-size:12px}@media(max-width:540px){main{padding:8px}.labels{font-size:11px}button{padding:8px 10px}h1{font-size:17px}}
</style></head><body><main>
<header><h1>🐇 Hareworks · Independent Forward Woman Proof</h1><span class="pill">v0.1.2 · one forward cycle · 30 fps</span></header>
<p>Left: the original <strong>Walking_Woman</strong>. Right: <strong>generated hip motion, ankle trajectories, anatomical knee IK and foot orientation</strong>. The generated side borrows only non-leg upper-body animation; no animated pelvis or leg tracks. Both use the same unchanged skinned GLB.</p>
<div class="labels"><strong>REFERENCE · source clip</strong><strong>GENERATED · fitted phase equations</strong></div>
<div id="status" role="status" aria-live="polite">Loading exact Hareworks source…</div>
<div id="stage" role="img" aria-label="Orbitable synchronized reference and procedural Hareworks 3D woman walking in place"></div>
<div class="cameraBar" role="group" aria-label="Camera controls"><strong>Camera:</strong><button id="side">Side</button><button id="front">Front</button><button id="top">Overhead</button><button id="oblique">Three-quarter</button><button id="resetCamera">Reset orbit</button><span id="instructions">Drag to orbit · pinch/scroll to zoom</span></div>
<div class="toolbar"><button id="play">Play one cycle</button><button id="previous">◀ Frame</button><button id="next">Frame ▶</button><label>Frame <input type="range" min="0" max="28" step="1" value="0" id="frame" aria-label="Walk cycle frame"><output id="frameNumber">0/28</output></label><button id="test">30 fps real-rig comparison</button><button id="markers">Toggle joint markers</button><button id="export">Export evidence</button></div>
<div id="metrics" role="status" aria-live="off">Waiting for rig…</div>
<p><strong>Acceptance question:</strong> do both legs, pelvis, foot pitch and heel/toe action visually match from side, front and overhead? This is a one-cycle <em>in-place leg-and-pelvis reproduction</em>, not world-space planted locomotion, strafing, turning or a complete game controller.</p>
<small>30 fps frame stepping is deliberate. The source extraction has an anomalous endpoint at exactly t=duration; the viewer excludes it. The model is hash-verified by the Termux launcher. Browser import uses Three.js 0.170.0 via CDN; camera requires pointer/touch events. Source GLB, v0.1.1, and other project assets are never modified.</small>
</main><script type="module" src="./viewer.mjs"></script></body></html>
__HAREWORKS_FW_V012_0__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/viewer.mjs" <<'__HAREWORKS_FW_V012_1__'
/* v0.1.2: ONE forward cycle, original reference against generated pelvis, IK
 * and foot motion. Reference tracks are never used as inputs to generated
 * pelvis, leg or ankle orientation. Upper body tracks remain reference-derived.
 * This does NOT claim root travel, planted sole contact or full procedural walk. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {trajectory,worldOffset} from '../v0.1.1/gait-kernel.mjs';
import {independentPose,validateProfile,angleDiff,clamp} from './pose-kernel.mjs';

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
function kneePoint(hip,ankle,l1,l2,pole,yaw){
 const axis=ankle.clone().sub(hip),d=axis.length();
 if(!(d<l1+l2-.003&&d>Math.abs(l1-l2)+.003))throw Error('UNREACHABLE_KNEE '+d.toFixed(5));
 axis.divideScalar(d);
 const a=(l1*l1-l2*l2+d*d)/(2*d),h=Math.sqrt(Math.max(0,l1*l1-a*a));
 const tangent=V(...pole).applyAxisAngle(YA,yaw).addScaledVector(axis,-V(...pole).applyAxisAngle(YA,yaw).dot(axis));
 if(tangent.lengthSq()<1e-9)throw Error('ANATOMICAL_POLE_SINGULAR');
 return hip.clone().addScaledVector(axis,a).addScaledVector(tangent.normalize(),h);
}
function setFootProcedural(leg,desiredToeVector,desiredYaw){
 const actualVector=world(leg.toe).sub(world(leg.ankle));
 const wanted=V(...desiredToeVector);
 if(actualVector.lengthSq()<1e-8||wanted.lengthSq()<1e-8)throw Error('ZERO_FOOT_VECTOR');
 const dir=wanted.clone().normalize();
 let footQ=Q().setFromUnitVectors(actualVector.normalize(),dir).multiply(wq(leg.ankle));
 // Twist around the toe direction, preserving its orientation, to match a
 // separate fitted world-yaw curve. No source/ref ankle quaternion is read.
 for(let i=0;i<5;i++){
  const err=angleDiff(desiredYaw,forwardYaw(footQ));
  if(Math.abs(err)<.0005)break;
  const step=.012;
  const plus=Q().setFromAxisAngle(dir,step).multiply(footQ);
  const minus=Q().setFromAxisAngle(dir,-step).multiply(footQ);
  const derivative=angleDiff(forwardYaw(plus),forwardYaw(minus))/(2*step);
  if(!Number.isFinite(derivative)||Math.abs(derivative)<.15)break;
  footQ.premultiply(Q().setFromAxisAngle(dir,clamp(err/derivative,-.35,.35))).normalize();
 }
 setWorldBoneRotation(leg.ankle,footQ);
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
let reference,generated,refRig,genRig,refMixer,genMixer,clip,profile,legProfile,seed,refBase,genBase;
let running=false,playing=false,frame=0,last=performance.now(),elapsed=0,markersVisible=false,markers=[],lastReport=null;
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
function applyGeneratedPose(t){
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
  const leg=genRig.legs[side],f=trajectory(sourceTime,legProfile,side),cfg=legProfile[side];
  const H=world(leg.up),vec=V(...worldOffset(f,pelvisYaw,H.y));
  const A=H.clone().add(vec);
  const l1=world(leg.up).distanceTo(world(leg.knee));
  const l2=world(leg.knee).distanceTo(world(leg.ankle));
  if(Math.abs(l1-cfg.upperLength)>.009||Math.abs(l2-cfg.lowerLength)>.009)throw Error('LINK_LENGTH_MISMATCH_'+side);
  const K=kneePoint(H,A,l1,l2,cfg.pole,pelvisYaw);
  turnBoneToward(leg.up,world(leg.knee),K);generated.updateMatrixWorld(true);
  turnBoneToward(leg.knee,world(leg.ankle),A);generated.updateMatrixWorld(true);
  const target=prediction.feet[side];
  setFootProcedural(leg,target.toeVector,target.ankleYaw);generated.updateMatrixWorld(true);
  const actualAnkle=world(leg.ankle),actualKnee=world(leg.knee),actualToe=world(leg.toe);
  const toeVector=actualToe.clone().sub(actualAnkle);
  const r={side,relativeForward:f.z,hip:world(leg.up).toArray(),knee:actualKnee.toArray(),ankle:actualAnkle.toArray(),toe:actualToe.toArray(),
   ikResidual:actualAnkle.distanceTo(A),toeVectorDifferenceToCurve:toeVector.distanceTo(V(...target.toeVector)),
   ankleYawDifferenceToCurveDeg:rad(angleDiff(forwardYaw(wq(leg.ankle)),target.ankleYaw))};
  if(![r.ikResidual,r.toeVectorDifferenceToCurve,r.ankleYawDifferenceToCurveDeg,...r.hip,...r.knee,...r.ankle,...r.toe].every(Number.isFinite))throw Error('NONFINITE_GENERATED_POSE');
  if(r.ikResidual>.012)throw Error('IK_TARGET_RESIDUAL '+side+' '+r.ikResidual.toFixed(5));
  rows.push(r);
 }
 return {t:sourceTime,profilePhase:prediction.q,pelvis:world(genRig.hips).toArray(),pelvisYaw:pelvisYaw,legs:rows};
}
function evaluate(f){
 if(!running)return null;
 const t=f/FPS;refMixer.setTime(t);reference.updateMatrixWorld(true);
 const generatedPose=applyGeneratedPose(t);
 const refPelvis=world(refRig.hips).add(V(0,0,SEP));
 const metrics={frame:f,t,hipDiff:world(genRig.hips).distanceTo(refPelvis),pelvisYawDiffDeg:rad(angleDiff(generatedPose.pelvisYaw,forwardYaw(wq(refRig.hips)))),legs:{}};
 for(const s of ['left','right']){
  const gen=genRig.legs[s],ref=refRig.legs[s],r=generatedPose.legs.find(x=>x.side===s);
  const refKnee=world(ref.knee).add(V(0,0,SEP)),refAnkle=world(ref.ankle).add(V(0,0,SEP)),refToe=world(ref.toe).add(V(0,0,SEP));
  metrics.legs[s]={forward:r.relativeForward,kneeDiff:world(gen.knee).distanceTo(refKnee),ankleDiff:world(gen.ankle).distanceTo(refAnkle),toeDiff:world(gen.toe).distanceTo(refToe),ikResidual:r.ikResidual,
   ankleYawDifferenceToReferenceDeg:rad(angleDiff(forwardYaw(wq(gen.ankle)),forwardYaw(wq(ref.ankle)))),
   toeVectorCurveResidual:r.toeVectorDifferenceToCurve,ankleYawCurveResidualDeg:r.ankleYawDifferenceToCurveDeg,
   upperQuat:gen.up.quaternion.toArray(),lowerQuat:gen.knee.quaternion.toArray(),footQuat:gen.ankle.quaternion.toArray()};
 }
 showMarkers();return metrics;
}
function display(m){if(!m)return;
 $('frame').value=m.frame;$('frameNumber').textContent=`${m.frame}/${nFrames-1}`;
 $('metrics').textContent=`Frame ${m.frame}/${nFrames-1}, time ${m.t.toFixed(3)}s\nGenerated hips Δ ${m.hipDiff.toFixed(4)} units / yaw Δ ${m.pelvisYawDiffDeg.toFixed(2)}°\nLEFT   forward ${m.legs.left.forward.toFixed(3)}   ankle Δ ${m.legs.left.ankleDiff.toFixed(3)}  knee Δ ${m.legs.left.kneeDiff.toFixed(3)}  toe Δ ${m.legs.left.toeDiff.toFixed(3)}\nRIGHT  forward ${m.legs.right.forward.toFixed(3)}   ankle Δ ${m.legs.right.ankleDiff.toFixed(3)}  knee Δ ${m.legs.right.kneeDiff.toFixed(3)}  toe Δ ${m.legs.right.toeDiff.toFixed(3)}\nFoot yaw reference Δ ${m.legs.left.ankleYawDifferenceToReferenceDeg.toFixed(1)}° / ${m.legs.right.ankleYawDifferenceToReferenceDeg.toFixed(1)}°\nAnkle IK residual ${m.legs.left.ikResidual.toFixed(5)} / ${m.legs.right.ikResidual.toFixed(5)}`;
}
function sampleFrame(f){frame=(f+nFrames)%nFrames;try{display(evaluate(frame))}catch(e){playing=false;$('status').textContent='BLOCKED_REAL_RIG '+e.message;console.error(e)}}
function render(now){requestAnimationFrame(render);let dt=Math.min(.1,(now-last)/1000);last=now;
 if(playing&&running){elapsed+=dt;if(elapsed>=1/FPS){const steps=Math.max(1,Math.min(2,Math.floor(elapsed*FPS)));elapsed-=steps/FPS;frame=Math.min(frame+steps,nFrames-1);sampleFrame(frame);if(frame===nFrames-1){playing=false;$('play').textContent='Replay cycle'}}}
 orbit.update();renderer.render(scene,camera);
}
requestAnimationFrame(render);
$('play').onclick=()=>{if(!running)return;if(!playing&&frame===nFrames-1)sampleFrame(0);playing=!playing;$('play').textContent=playing?'Pause':'Play cycle'};
$('previous').onclick=()=>{playing=false;$('play').textContent='Play cycle';sampleFrame(frame-1)};
$('next').onclick=()=>{playing=false;$('play').textContent='Play cycle';sampleFrame(frame+1)};
$('frame').oninput=()=>{playing=false;$('play').textContent='Play cycle';sampleFrame(Number($('frame').value))};
$('markers').onclick=()=>{markersVisible=!markersVisible;showMarkers()};
const jsonDownload=(filename,obj)=>{const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),4000)};
$('export').onclick=()=>{if(!lastReport){$('status').textContent='Run the 30 fps real-rig comparison first to create exportable evidence.';return}jsonDownload('hareworks-independent-woman-v0.1.2.json',lastReport)};
$('test').onclick=()=>{
 if(!running)return;playing=false;let rows=[],errors=[];
 const max={pelvis:0,ankle:0,knee:0,toe:0,footYaw:0,IK:0,quatStep:0},maxFront={left:-Infinity,right:-Infinity};
 try{for(let i=0;i<nFrames;i++){
  const r=evaluate(i);rows.push(r);max.pelvis=Math.max(max.pelvis,r.hipDiff);
  for(const s of ['left','right']){const v=r.legs[s];max.ankle=Math.max(max.ankle,v.ankleDiff);max.knee=Math.max(max.knee,v.kneeDiff);max.toe=Math.max(max.toe,v.toeDiff);max.footYaw=Math.max(max.footYaw,Math.abs(v.ankleYawDifferenceToReferenceDeg));max.IK=Math.max(max.IK,v.ikResidual);maxFront[s]=Math.max(maxFront[s],v.forward);
   if(i>0){for(const key of ['upperQuat','lowerQuat','footQuat']){const previous=new THREE.Quaternion().fromArray(rows[i-1].legs[s][key]),current=new THREE.Quaternion().fromArray(v[key]);max.quatStep=Math.max(max.quatStep,rad(previous.angleTo(current)))}}
  }
 }}catch(e){errors.push({frame:rows.length,message:e.message})}
 if(maxFront.left<.30||maxFront.right<.30)errors.push({message:'FEET_DO_NOT_REACH_AHEAD_OF_HIPS',maxFront});
 if(max.quatStep>60)errors.push({message:'JOINT_ROTATION_SNAP_OVER_60_DEG_PER_30FPS_FRAME',value:max.quatStep});
 if(max.IK>.012)errors.push({message:'ANATOMICAL_IK_SOLVER_RESIDUAL',value:max.IK});
 const report={schema:'hareworks-forward-woman-v0.1.2-real-rig',sourceSha256:SOURCE,referenceClip:'Walking_Woman',generatedLegTracks:0,generatedHipTracks:0,
  generatedPelvis:'phase-parametric fitted movement (independent)',generatedAnkleYaw:'phase-parametric toe-vector/yaw solved rotation (independent)',
  upperBodyTracks:'source upper-body clips remain',fps:FPS,frameCount:rows.length,expectedFrames:nFrames,
  maximumErrors:max,frontReach:maxFront,errors,rows,ownerAccepted:false,worldFootPlantImplemented:false,
  result:errors.length?'BLOCKED_GEOMETRIC_GATE':'MEASURED_REQUIRES_OWNER_VISUAL_REVIEW'};
 lastReport=report;sampleFrame(0);
 $('status').textContent=report.result+' · '+rows.length+'/'+nFrames+' frames · '+(errors.length?JSON.stringify(errors[0]):'both feet advance ahead of hips; orbit to inspect knees and toes');
 console.info('HAREWORKS_PROCEDURAL_POSE_GATE',report);
 jsonDownload('hareworks-independent-woman-v0.1.2.json',report);
};

try{
 const paths=['./motion-profile.json','../v0.1.1/profile.json'];
 const loaded=await Promise.all([...paths.map(p=>fetch(p).then(r=>{if(!r.ok)throw Error('FETCH_'+p+'_'+r.status);return r.json()})),new GLTFLoader().loadAsync('../../../assets/hareworks/Hareworks-nine-clips.glb')]);
 [profile,legProfile]=loaded;const gltf=loaded[2];validateProfile(profile);
 if(legProfile.modelSha256!==SOURCE||profile.sourceSha256!==SOURCE)throw Error('MODEL_PARAMETER_SHA_MISMATCH');
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
 $('status').textContent=`REAL SKINNED GLB READY · ${excludedLeg.length} leg tracks and ${excludedHip.length} hip tracks excluded from generated animation; ${allowedTracks.length} upper-body tracks retained. Orbit viewer to judge results. Visual acceptance pending.`;
 console.info('HAREWORKS_v012_TRACK_AUDIT',{excludedLeg:excludedLeg.length,excludedHip:excludedHip.length,upperBody:allowedTracks.length,sourceSha:SOURCE});
}catch(e){running=false;$('status').textContent='BLOCKED_SOURCE_OR_RIG '+e.message;console.error(e)}
__HAREWORKS_FW_V012_1__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/pose-kernel.mjs" <<'__HAREWORKS_FW_V012_2__'
/* v0.1.2: source-calibrated, phase-driven procedural pelvis + foot pose.
 * No keyframe sampling at runtime; explicit parameter curves, not clip tracks.
 * One forward Walking_Woman cycle ONLY. No world contact, aim or turn controller. */
export const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
export const angleDiff=(a,b)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
export const phase=(t,d)=>clamp(t/d,0,1-1e-10);
export function curve(c,q){
 let v=c.start;
 for(let i=0;i<c.sin.length;i++){
   const n=i+1,theta=2*Math.PI*n*q;
   v+=c.sin[i]*Math.sin(theta)+c.cosMinusOne[i]*(Math.cos(theta)-1);
 }
 return v;
}
export function independentPose(p,t){
 const q=phase(t,p.duration);
 const pelvis=[curve(p.pelvis.x,q),curve(p.pelvis.y,q),curve(p.pelvis.z,q)];
 const yaw=curve(p.pelvis.yaw,q);
 const feet={};
 for(const side of ['left','right']){
  const f=p.feet[side];
  feet[side]={toeVector:[curve(f.toeVectorX,q),curve(f.toeVectorY,q),curve(f.toeVectorZ,q)],ankleYaw:curve(f.ankleYaw,q)};
 }
 return {q,pelvis,pelvisYaw:yaw,feet};
}
export function validateProfile(p){
 if(p.schema!=='hareworks-forward-woman-independent-pelvis-foot-v0.1.2')throw Error('POSE_PROFILE_SCHEMA');
 if(p.clip!=='Walking_Woman'||p.sourceSha256!=='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6')throw Error('POSE_PROFILE_SOURCE');
 if(Math.abs(p.duration-.966667)>.0001)throw Error('POSE_PROFILE_DURATION');
 for(const ch of [p.pelvis.x,p.pelvis.y,p.pelvis.z,p.pelvis.yaw,...['left','right'].flatMap(side=>['toeVectorX','toeVectorY','toeVectorZ','ankleYaw'].map(name=>p.feet[side][name]))]){
  if(!Number.isFinite(ch.start)||ch.sin.length!==4||ch.cosMinusOne.length!==4||![...ch.sin,...ch.cosMinusOne].every(Number.isFinite))throw Error('POSE_PROFILE_COEFFICIENTS');
 }
 return true;
}
__HAREWORKS_FW_V012_2__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/pose-kernel-test.mjs" <<'__HAREWORKS_FW_V012_3__'
/* Intentionally tests actual source measurements not a manufactured constant. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {curve,phase,independentPose,validateProfile,angleDiff} from './pose-kernel.mjs';
const profile=JSON.parse(fs.readFileSync(new URL('./motion-profile.json',import.meta.url)));
const source=JSON.parse(fs.readFileSync(new URL('./reference-samples.json',import.meta.url)));
validateProfile(profile);
assert.equal(source.sourceSha256,profile.sourceSha256);
assert.equal(source.samples.length,60);
assert.ok(source.samples.at(-1).t<profile.duration);
const dev={};
for(let i=1;i<60;i+=2){const row=source.samples[i],p=independentPose(profile,row.t);
 const fields={pelvisX:[p.pelvis[0],row.pelvis[0]],pelvisY:[p.pelvis[1],row.pelvis[1]],pelvisZ:[p.pelvis[2],row.pelvis[2]],pelvisYaw:[p.pelvisYaw,row.pelvisYaw]};
 for(const side of ['left','right']){
  for(let j=0;j<3;j++)fields[side+'Toe'+j]=[p.feet[side].toeVector[j],row.feet[side].toeVector[j]];
  fields[side+'AnkleYaw']=[p.feet[side].ankleYaw,row.feet[side].ankleYaw];
 }
 for(const [k,[a,b]] of Object.entries(fields)){
  const err=k.includes('Yaw')?Math.abs(angleDiff(a,b)):Math.abs(a-b);
  (dev[k]??=[]).push(err);
 }
}
const stats=Object.fromEntries(Object.entries(dev).map(([k,v])=>[k,{rms:Math.sqrt(v.reduce((a,b)=>a+b*b,0)/v.length),max:Math.max(...v)}]));
for(const [k,v] of Object.entries(stats)){
 let lim=k.includes('Yaw')?.2:k.startsWith('pelvis')?.035:.04;
 assert.ok(v.max<lim,`${k}: held-out maximum ${v.max} > ${lim}`);
}
for(const side of ['left','right']){
 const start=independentPose(profile,0).feet[side];const e=independentPose(profile,profile.duration-1e-8).feet[side];
 assert.ok(start.toeVector.every((v,i)=>Math.abs(v-e.toeVector[i])<1e-5));
 assert.ok(Math.abs(angleDiff(start.ankleYaw,e.ankleYaw))<1e-5);
}
for(let frame=0;frame<30;frame++){
 const t=frame/30,p=independentPose(profile,t);
 assert.ok([...p.pelvis,p.pelvisYaw,...Object.values(p.feet).flatMap(f=>[...f.toeVector,f.ankleYaw])].every(Number.isFinite));
}
assert.ok(Math.abs(phase(profile.duration,profile.duration)-1)<1e-8);
console.log(JSON.stringify({result:'PASS',sampleCount:60,independentHeldOutSamples:30,generatedFramesAt30fps:30,maxErrors:stats,limitations:'fit and phase math only; actual GLB skin and visual acceptance require browser'},null,2));
__HAREWORKS_FW_V012_3__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/motion-profile.json" <<'__HAREWORKS_FW_V012_4__'
{
  "schema": "hareworks-forward-woman-independent-pelvis-foot-v0.1.2",
  "sourceSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "sourceSchema": "hareworks-gait-and-idle-turn-v1.0.8",
  "clip": "Walking_Woman",
  "duration": 0.966667,
  "fitMethod": "four sine and four (cos-1) harmonics, fit to 30 alternating frames, 30 held-out frames; anchored at t=0 with periodic continuity; misleading discontinuous endpoint excluded",
  "coordinateFrame": "GLTF world +Y up, +Z forward; source reference model origin, independent of side-by-side display offsets",
  "pelvis": {
    "x": {
      "start": 0.012163,
      "sin": [
        0.001475575,
        0.000155142,
        0.001759443,
        -3.5367e-05
      ],
      "cosMinusOne": [
        -0.01921953,
        0.00093039,
        -0.000521192,
        0.000239871
      ]
    },
    "y": {
      "start": 1.005117,
      "sin": [
        -0.000109938,
        0.00889427,
        -0.000196938,
        0.000930304
      ],
      "cosMinusOne": [
        -0.000526119,
        0.01685711,
        0.000959503,
        -0.001330693
      ]
    },
    "z": {
      "start": 0.114537,
      "sin": [
        -0.003670381,
        -0.011920402,
        3.1591e-05,
        -0.000146197
      ],
      "cosMinusOne": [
        -0.007734078,
        -0.004222579,
        -0.001298296,
        -0.002522193
      ]
    },
    "yaw": {
      "start": 0.185217187,
      "sin": [
        -0.098827339,
        -0.00151022,
        0.014212,
        0.00107556
      ],
      "cosMinusOne": [
        0.098433407,
        0.014129334,
        0.023549355,
        0.005990104
      ]
    }
  },
  "feet": {
    "left": {
      "toeVectorX": {
        "start": 0.029435,
        "sin": [
          0.0043825,
          0.006334657,
          0.004487507,
          -6.512e-06
        ],
        "cosMinusOne": [
          -0.002765975,
          0.002125371,
          0.002745245,
          0.002462342
        ]
      },
      "toeVectorY": {
        "start": -0.09285,
        "sin": [
          0.004774215,
          -0.004748215,
          -0.010368439,
          -0.005216561
        ],
        "cosMinusOne": [
          0.005918738,
          -0.002996904,
          -0.004937331,
          -0.001544144
        ]
      },
      "toeVectorZ": {
        "start": -0.040536,
        "sin": [
          0.042517921,
          0.0292223,
          0.004106118,
          -0.001871619
        ],
        "cosMinusOne": [
          -0.037909216,
          -0.017890218,
          -0.001812765,
          0.004543984
        ]
      },
      "ankleYaw": {
        "start": 2.69436898,
        "sin": [
          0.031504547,
          0.022889011,
          0.035204745,
          0.011015732
        ],
        "cosMinusOne": [
          0.03254269,
          0.048905346,
          0.029024304,
          0.000415883
        ]
      }
    },
    "right": {
      "toeVectorX": {
        "start": -0.039464,
        "sin": [
          0.000353886,
          -0.005097988,
          0.00475305,
          -0.000144409
        ],
        "cosMinusOne": [
          -0.006217314,
          -0.003777912,
          0.003483705,
          -0.001187136
        ]
      },
      "toeVectorY": {
        "start": -0.097577,
        "sin": [
          -0.004668954,
          -0.003138845,
          0.010599704,
          -0.007008285
        ],
        "cosMinusOne": [
          -0.005044143,
          -0.001858262,
          0.004404747,
          -0.001159044
        ]
      },
      "toeVectorZ": {
        "start": 0.040789,
        "sin": [
          -0.041547867,
          0.032274259,
          -0.005623962,
          -0.003365206
        ],
        "cosMinusOne": [
          0.040112697,
          -0.022292211,
          0.003785121,
          0.004127944
        ]
      },
      "ankleYaw": {
        "start": -2.542201418,
        "sin": [
          0.016821225,
          -0.056965558,
          0.071218309,
          -0.040098851
        ],
        "cosMinusOne": [
          0.004317916,
          -0.009739354,
          0.014453558,
          -0.016060594
        ]
      }
    }
  },
  "holdoutErrors": {
    "pelvisx": {
      "rmse": 0.0003251,
      "worst": 0.0006912
    },
    "pelvisy": {
      "rmse": 0.0014499,
      "worst": 0.0029979
    },
    "pelvisz": {
      "rmse": 0.0010311,
      "worst": 0.0030034
    },
    "pelvisYaw": {
      "rmse": 0.0057872,
      "worst": 0.0105819
    },
    "leftToex": {
      "rmse": 0.0020791,
      "worst": 0.004478
    },
    "leftToey": {
      "rmse": 0.0015998,
      "worst": 0.0033382
    },
    "leftToez": {
      "rmse": 0.0012333,
      "worst": 0.0035204
    },
    "leftAnkleYaw": {
      "rmse": 0.0173458,
      "worst": 0.0577148
    },
    "rightToex": {
      "rmse": 0.0017442,
      "worst": 0.0040354
    },
    "rightToey": {
      "rmse": 0.0020263,
      "worst": 0.0075262
    },
    "rightToez": {
      "rmse": 0.0023703,
      "worst": 0.0058638
    },
    "rightAnkleYaw": {
      "rmse": 0.0252032,
      "worst": 0.0819964
    }
  },
  "validation": {
    "referenceSampleCount": 60,
    "discardedResetEndpoint": true,
    "holdoutSampleCount": 30,
    "maxAllowedPelvisPositionHoldoutError": 0.035,
    "maxAllowedPelvisYawHoldoutErrorRad": 0.18,
    "maxAllowedToeVectorHoldoutError": 0.04,
    "maxAllowedAnkleYawHoldoutErrorRad": 0.2,
    "ownerVisualAcceptance": false
  }
}
__HAREWORKS_FW_V012_4__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/reference-samples.json" <<'__HAREWORKS_FW_V012_5__'
{"schema":"hareworks-woman-pose-samples-v0.1.2","sourceSha256":"a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6","sourceReportSchema":"hareworks-gait-and-idle-turn-v1.0.8","clip":"Walking_Woman","samples":[{"t":0,"pelvis":[0.012163,1.005117,0.114537],"pelvisYaw":0.18521718701095075,"feet":{"left":{"toeVector":[0.029435,-0.09285,-0.040536],"ankleYaw":2.694368979991726},"right":{"toeVector":[-0.039464,-0.097577,0.040789],"ankleYaw":-2.5422014183136956}}},{"t":0.016111,"pelvis":[0.012982,1.00636,0.113921],"pelvisYaw":0.1703646634613494,"feet":{"left":{"toeVector":[0.029815,-0.096939,-0.029057],"ankleYaw":2.7229280100134465},"right":{"toeVector":[-0.039523,-0.098008,0.039682],"ankleYaw":-2.5429995333591315}}},{"t":0.032222,"pelvis":[0.0138,1.007604,0.113304],"pelvisYaw":0.15558625778186014,"feet":{"left":{"toeVector":[0.029869,-0.099722,-0.017144],"ankleYaw":2.742041014747247},"right":{"toeVector":[-0.039528,-0.098453,0.03856],"ankleYaw":-2.543465488319036}}},{"t":0.048333,"pelvis":[0.014793,1.006779,0.112749],"pelvisYaw":0.1343668258485819,"feet":{"left":{"toeVector":[0.030676,-0.100792,-0.005516],"ankleYaw":2.74381134821988},"right":{"toeVector":[-0.03931,-0.098585,0.038443],"ankleYaw":-2.5372512667834513}}},{"t":0.064444,"pelvis":[0.015799,1.005801,0.112199],"pelvisYaw":0.11275899426403757,"feet":{"left":{"toeVector":[0.031127,-0.100619,0.006118],"ankleYaw":2.7392524509451115},"right":{"toeVector":[-0.038978,-0.098745,0.038374],"ankleYaw":-2.5303919519881988}}},{"t":0.080556,"pelvis":[0.016889,1.003762,0.111987],"pelvisYaw":0.08824782894604943,"feet":{"left":{"toeVector":[0.031801,-0.099059,0.017505],"ankleYaw":2.725322580441702},"right":{"toeVector":[-0.038575,-0.098915,0.038342],"ankleYaw":-2.5297427384777578}}},{"t":0.096667,"pelvis":[0.017993,1.001553,0.111831],"pelvisYaw":0.06334889889703664,"feet":{"left":{"toeVector":[0.032196,-0.096309,0.028609],"ankleYaw":2.7064068182085825},"right":{"toeVector":[-0.038045,-0.099147,0.038273],"ankleYaw":-2.5301929433591637}}},{"t":0.112778,"pelvis":[0.019069,0.998855,0.112335],"pelvisYaw":0.039547131887606085,"feet":{"left":{"toeVector":[0.03218,-0.092603,0.038982],"ankleYaw":2.6825717694809366},"right":{"toeVector":[-0.038022,-0.099385,0.037671],"ankleYaw":-2.534423171718691}}},{"t":0.128889,"pelvis":[0.020138,0.996029,0.113011],"pelvisYaw":0.01604597375552917,"feet":{"left":{"toeVector":[0.031885,-0.087929,0.04881],"ankleYaw":2.6539892659933897},"right":{"toeVector":[-0.038034,-0.099669,0.036901],"ankleYaw":-2.5396367579516768}}},{"t":0.145,"pelvis":[0.021199,0.992786,0.114506],"pelvisYaw":-0.004067708635633959,"feet":{"left":{"toeVector":[0.031319,-0.082865,0.057298],"ankleYaw":2.6231797352459303},"right":{"toeVector":[-0.038378,-0.100227,0.034987],"ankleYaw":-2.5443066864440547}}},{"t":0.161111,"pelvis":[0.022256,0.989384,0.116313],"pelvisYaw":-0.022900186095453707,"feet":{"left":{"toeVector":[0.030574,-0.077288,0.06498],"ankleYaw":2.5884981958585858},"right":{"toeVector":[-0.03879,-0.100867,0.032611],"ankleYaw":-2.548615423972925}}},{"t":0.177222,"pelvis":[0.023723,0.984884,0.118949],"pelvisYaw":-0.03935702071182589,"feet":{"left":{"toeVector":[0.029373,-0.072627,0.070662],"ankleYaw":2.5568784597523635},"right":{"toeVector":[-0.038854,-0.101717,0.029768],"ankleYaw":-2.5499059737686354}}},{"t":0.193333,"pelvis":[0.025405,0.979806,0.122022],"pelvisYaw":-0.05456276410968913,"feet":{"left":{"toeVector":[0.027925,-0.068456,0.075262],"ankleYaw":2.526561551381152},"right":{"toeVector":[-0.038683,-0.102645,0.026642],"ankleYaw":-2.549544521591116}}},{"t":0.209444,"pelvis":[0.026977,0.975137,0.124601],"pelvisYaw":-0.06616825376061237,"feet":{"left":{"toeVector":[0.026012,-0.066966,0.077262],"ankleYaw":2.511149475257424},"right":{"toeVector":[-0.038397,-0.103882,0.021828],"ankleYaw":-2.5539397158595745}}},{"t":0.225556,"pelvis":[0.02847,0.970759,0.126832],"pelvisYaw":-0.07523209074600297,"feet":{"left":{"toeVector":[0.023801,-0.067478,0.077529],"ankleYaw":2.5080908384210727},"right":{"toeVector":[-0.038024,-0.105107,0.015784],"ankleYaw":-2.56090199099504}}},{"t":0.241667,"pelvis":[0.030041,0.969034,0.128941],"pelvisYaw":-0.08018560374337601,"feet":{"left":{"toeVector":[0.022313,-0.070458,0.075288],"ankleYaw":2.5206335590657254},"right":{"toeVector":[-0.035529,-0.106932,0.006748],"ankleYaw":-2.570025388679678}}},{"t":0.257778,"pelvis":[0.031684,0.969785,0.130935],"pelvisYaw":-0.08132579694623228,"feet":{"left":{"toeVector":[0.021505,-0.075519,0.070462],"ankleYaw":2.5443837217675727},"right":{"toeVector":[-0.031071,-0.108397,-0.005194],"ankleYaw":-2.578919114161866}}},{"t":0.273889,"pelvis":[0.033424,0.970805,0.133646],"pelvisYaw":-0.08179323469318528,"feet":{"left":{"toeVector":[0.022265,-0.080483,0.064476],"ankleYaw":2.564517200839358},"right":{"toeVector":[-0.027267,-0.108099,-0.017703],"ankleYaw":-2.5846708283138216}}},{"t":0.29,"pelvis":[0.035285,0.972156,0.137238],"pelvisYaw":-0.08144076459075932,"feet":{"left":{"toeVector":[0.024969,-0.085131,0.057094],"ankleYaw":2.5800443153942907},"right":{"toeVector":[-0.024296,-0.105887,-0.030657],"ankleYaw":-2.5867906905517755}}},{"t":0.306111,"pelvis":[0.03737,0.973717,0.140539],"pelvisYaw":-0.08104877534836259,"feet":{"left":{"toeVector":[0.026394,-0.089162,0.049838],"ankleYaw":2.5910389548310375},"right":{"toeVector":[-0.02115,-0.101883,-0.043759],"ankleYaw":-2.571949852341141}}},{"t":0.322222,"pelvis":[0.039822,0.975619,0.143366],"pelvisYaw":-0.08055745974902692,"feet":{"left":{"toeVector":[0.025715,-0.09282,0.043055],"ankleYaw":2.5985576505414696},"right":{"toeVector":[-0.018007,-0.095691,-0.057108],"ankleYaw":-2.5293702750283193}}},{"t":0.338333,"pelvis":[0.042352,0.977902,0.145681],"pelvisYaw":-0.07862202063464137,"feet":{"left":{"toeVector":[0.025785,-0.094903,0.038197],"ankleYaw":2.6013800003497805},"right":{"toeVector":[-0.015136,-0.087554,-0.069624],"ankleYaw":-2.4692858168658343}}},{"t":0.354444,"pelvis":[0.045057,0.98103,0.146859],"pelvisYaw":-0.07341394120544903,"feet":{"left":{"toeVector":[0.027401,-0.09447,0.038145],"ankleYaw":2.598965515871703},"right":{"toeVector":[-0.012507,-0.077486,-0.081127],"ankleYaw":-2.3789834497441547}}},{"t":0.370556,"pelvis":[0.047523,0.984087,0.147411],"pelvisYaw":-0.06890731308659537,"feet":{"left":{"toeVector":[0.028615,-0.094118,0.038123],"ankleYaw":2.5966903286815346},"right":{"toeVector":[-0.011702,-0.069087,-0.088501],"ankleYaw":-2.2993348390787114}}},{"t":0.386667,"pelvis":[0.049243,0.986922,0.145994],"pelvisYaw":-0.06651876229025133,"feet":{"left":{"toeVector":[0.028705,-0.094089,0.03813],"ankleYaw":2.59613492648583},"right":{"toeVector":[-0.015295,-0.07045,-0.086863],"ankleYaw":-2.309823221674752}}},{"t":0.402778,"pelvis":[0.050794,0.989833,0.144425],"pelvisYaw":-0.06486321870242424,"feet":{"left":{"toeVector":[0.028758,-0.094061,0.038157],"ankleYaw":2.5950155755298727},"right":{"toeVector":[-0.018945,-0.072225,-0.084657],"ankleYaw":-2.3303904357469407}}},{"t":0.418889,"pelvis":[0.051535,0.993106,0.142124],"pelvisYaw":-0.06661198571705809,"feet":{"left":{"toeVector":[0.028672,-0.094032,0.038295],"ankleYaw":2.5899809759895596},"right":{"toeVector":[-0.023135,-0.07616,-0.080042],"ankleYaw":-2.3957630539526096}}},{"t":0.435,"pelvis":[0.052177,0.996379,0.139821],"pelvisYaw":-0.06843325363276435,"feet":{"left":{"toeVector":[0.028559,-0.094035,0.038369],"ankleYaw":2.585157093213729},"right":{"toeVector":[-0.027222,-0.079965,-0.07488],"ankleYaw":-2.460044264987487}}},{"t":0.451111,"pelvis":[0.051963,0.999652,0.137515],"pelvisYaw":-0.07086689273178969,"feet":{"left":{"toeVector":[0.028355,-0.094271,0.037939],"ankleYaw":2.5801261586454785},"right":{"toeVector":[-0.029944,-0.086016,-0.066685],"ankleYaw":-2.5165969473932677}}},{"t":0.467222,"pelvis":[0.051733,1.002862,0.135219],"pelvisYaw":-0.07300061799414023,"feet":{"left":{"toeVector":[0.028126,-0.094514,0.037504],"ankleYaw":2.5753055690786533},"right":{"toeVector":[-0.032511,-0.091311,-0.05786],"ankleYaw":-2.564364891065832}}},{"t":0.483333,"pelvis":[0.051089,1.004341,0.1332],"pelvisYaw":-0.06674595316262086,"feet":{"left":{"toeVector":[0.028084,-0.094721,0.037011],"ankleYaw":2.5738313031988347},"right":{"toeVector":[-0.033964,-0.097348,-0.045957],"ankleYaw":-2.5992596059265862}}},{"t":0.499444,"pelvis":[0.050444,1.00582,0.131181],"pelvisYaw":-0.060508556666022624,"feet":{"left":{"toeVector":[0.027978,-0.094945,0.036514],"ankleYaw":2.5724320471868922},"right":{"toeVector":[-0.035007,-0.101979,-0.033424],"ankleYaw":-2.6231781469034465}}},{"t":0.515556,"pelvis":[0.049531,1.0066,0.129921],"pelvisYaw":-0.046455523443138615,"feet":{"left":{"toeVector":[0.028035,-0.095159,0.035906],"ankleYaw":2.573272204534478},"right":{"toeVector":[-0.035825,-0.104947,-0.021093],"ankleYaw":-2.6503949429190867}}},{"t":0.531667,"pelvis":[0.048608,1.007355,0.128689],"pelvisYaw":-0.032165385741569796,"feet":{"left":{"toeVector":[0.028007,-0.095402,0.035277],"ankleYaw":2.5741840482868708},"right":{"toeVector":[-0.036263,-0.106557,-0.00854],"ankleYaw":-2.6697658184106148}}},{"t":0.547778,"pelvis":[0.047144,1.007426,0.127738],"pelvisYaw":-0.014379200353257515,"feet":{"left":{"toeVector":[0.027811,-0.095707,0.0346],"ankleYaw":2.5674101352849252},"right":{"toeVector":[-0.036404,-0.106779,0.003916],"ankleYaw":-2.6829966440454394}}},{"t":0.563889,"pelvis":[0.045617,1.007418,0.12682],"pelvisYaw":0.003779672967327321,"feet":{"left":{"toeVector":[0.02748,-0.096062,0.033874],"ankleYaw":2.5596916752321928},"right":{"toeVector":[-0.036305,-0.105638,0.016272],"ankleYaw":-2.690437583167708}}},{"t":0.58,"pelvis":[0.044149,1.006031,0.126472],"pelvisYaw":0.020767026397290802,"feet":{"left":{"toeVector":[0.027285,-0.096475,0.032843],"ankleYaw":2.5527822885525477},"right":{"toeVector":[-0.035433,-0.102774,0.030404],"ankleYaw":-2.6723265300062997}}},{"t":0.596111,"pelvis":[0.042693,1.004357,0.126242],"pelvisYaw":0.0375179887599168,"feet":{"left":{"toeVector":[0.027036,-0.096923,0.031711],"ankleYaw":2.5460360978924492},"right":{"toeVector":[-0.034546,-0.097874,0.044379],"ankleYaw":-2.643562677683128}}},{"t":0.612222,"pelvis":[0.041095,1.000938,0.127277],"pelvisYaw":0.05405104495975427,"feet":{"left":{"toeVector":[0.027047,-0.097476,0.029956],"ankleYaw":2.544359850454539},"right":{"toeVector":[-0.032826,-0.092224,0.056208],"ankleYaw":-2.622319636838922}}},{"t":0.628333,"pelvis":[0.039451,0.996964,0.128713],"pelvisYaw":0.07052816708318371,"feet":{"left":{"toeVector":[0.027055,-0.09806,0.027977],"ankleYaw":2.5444256321912686},"right":{"toeVector":[-0.031084,-0.085483,0.066849],"ankleYaw":-2.5991588200753117}}},{"t":0.644444,"pelvis":[0.037911,0.990743,0.129918],"pelvisYaw":0.08744214544109562,"feet":{"left":{"toeVector":[0.027185,-0.098642,0.025713],"ankleYaw":2.5470752393532563},"right":{"toeVector":[-0.029325,-0.07969,0.074377],"ankleYaw":-2.5624551755793563}}},{"t":0.660556,"pelvis":[0.036417,0.983511,0.131018],"pelvisYaw":0.10455115079509175,"feet":{"left":{"toeVector":[0.027318,-0.099203,0.0233],"ankleYaw":2.5509200591938037},"right":{"toeVector":[-0.027413,-0.074321,0.080419],"ankleYaw":-2.5185255203993213}}},{"t":0.676667,"pelvis":[0.034927,0.977952,0.13213],"pelvisYaw":0.11909438630089914,"feet":{"left":{"toeVector":[0.02743,-0.100111,0.018865],"ankleYaw":2.5530807148196626},"right":{"toeVector":[-0.025647,-0.071026,0.083903],"ankleYaw":-2.487120949520451}}},{"t":0.692778,"pelvis":[0.033439,0.973417,0.133248],"pelvisYaw":0.1320793318439705,"feet":{"left":{"toeVector":[0.027522,-0.100996,0.013149],"ankleYaw":2.5532110273844797},"right":{"toeVector":[-0.023995,-0.069136,0.085945],"ankleYaw":-2.4650724407601796}}},{"t":0.708889,"pelvis":[0.031914,0.970871,0.134421],"pelvisYaw":0.1405026901661199,"feet":{"left":{"toeVector":[0.026669,-0.101934,0.005359],"ankleYaw":2.551637688648873},"right":{"toeVector":[-0.022342,-0.071681,0.084291],"ankleYaw":-2.465097567417024}}},{"t":0.725,"pelvis":[0.030358,0.969941,0.13564],"pelvisYaw":0.145229265068788,"feet":{"left":{"toeVector":[0.025002,-0.102411,-0.004178],"ankleYaw":2.5470081378248617},"right":{"toeVector":[-0.02074,-0.077597,0.079315],"ankleYaw":-2.479777450367461}}},{"t":0.741111,"pelvis":[0.028583,0.970012,0.137112],"pelvisYaw":0.14871059287345206,"feet":{"left":{"toeVector":[0.022914,-0.101929,-0.014697],"ankleYaw":2.5442004512072467},"right":{"toeVector":[-0.021652,-0.083341,0.072991],"ankleYaw":-2.495795886373065}}},{"t":0.757222,"pelvis":[0.026573,0.971155,0.138856],"pelvisYaw":0.1508513455649889,"feet":{"left":{"toeVector":[0.020356,-0.100175,-0.026094],"ankleYaw":2.542474248951765},"right":{"toeVector":[-0.025282,-0.088592,0.065227],"ankleYaw":-2.5127425739464835}}},{"t":0.773333,"pelvis":[0.024444,0.972349,0.140662],"pelvisYaw":0.1527415502191336,"feet":{"left":{"toeVector":[0.017899,-0.096945,-0.037574],"ankleYaw":2.533341654991015},"right":{"toeVector":[-0.029233,-0.09347,0.056134],"ankleYaw":-2.5276085990106383}}},{"t":0.789444,"pelvis":[0.022146,0.973613,0.142556],"pelvisYaw":0.15427078139492897,"feet":{"left":{"toeVector":[0.01601,-0.091995,-0.049105],"ankleYaw":2.5131840278929793},"right":{"toeVector":[-0.033587,-0.097796,0.045279],"ankleYaw":-2.540665028562988}}},{"t":0.805556,"pelvis":[0.019839,0.974982,0.144043],"pelvisYaw":0.15472449904139382,"feet":{"left":{"toeVector":[0.012977,-0.085642,-0.060229],"ankleYaw":2.4910920862651573},"right":{"toeVector":[-0.036388,-0.09969,0.03847],"ankleYaw":-2.542792581523174}}},{"t":0.821667,"pelvis":[0.017512,0.976551,0.144754],"pelvisYaw":0.15310274800675094,"feet":{"left":{"toeVector":[0.007418,-0.077806,-0.070864],"ankleYaw":2.4748723471296135},"right":{"toeVector":[-0.036075,-0.099213,0.039971],"ankleYaw":-2.53231856950714}}},{"t":0.837778,"pelvis":[0.015392,0.978323,0.14462],"pelvisYaw":0.15188592921514776,"feet":{"left":{"toeVector":[0.003207,-0.070269,-0.078629],"ankleYaw":2.4668911574639627},"right":{"toeVector":[-0.035863,-0.098807,0.04115],"ankleYaw":-2.5235313725358526}}},{"t":0.853889,"pelvis":[0.013813,0.980628,0.142266],"pelvisYaw":0.15173057034725415,"feet":{"left":{"toeVector":[0.001673,-0.066943,-0.081526],"ankleYaw":2.5028840940745756},"right":{"toeVector":[-0.036014,-0.098589,0.04154],"ankleYaw":-2.5185787301817935}}},{"t":0.87,"pelvis":[0.01242,0.983365,0.139572],"pelvisYaw":0.15261736282614055,"feet":{"left":{"toeVector":[0.001536,-0.065059,-0.083039],"ankleYaw":2.5430637691888367},"right":{"toeVector":[-0.036256,-0.098396,0.041786],"ankleYaw":-2.5167414311829805}}},{"t":0.886111,"pelvis":[0.011741,0.987759,0.135576],"pelvisYaw":0.15757728096683843,"feet":{"left":{"toeVector":[0.007658,-0.06823,-0.080103],"ankleYaw":2.582024467369112},"right":{"toeVector":[-0.036898,-0.098268,0.041524],"ankleYaw":-2.5259201832471567}}},{"t":0.902222,"pelvis":[0.011154,0.992091,0.131513],"pelvisYaw":0.16320420272950079,"feet":{"left":{"toeVector":[0.013748,-0.071373,-0.076468],"ankleYaw":2.622009500737217},"right":{"toeVector":[-0.0376,-0.098131,0.041217],"ankleYaw":-2.535365428455789}}},{"t":0.918333,"pelvis":[0.011137,0.996036,0.127041],"pelvisYaw":0.17314247375835626,"feet":{"left":{"toeVector":[0.019762,-0.077174,-0.069168],"ankleYaw":2.6667510857334866},"right":{"toeVector":[-0.038366,-0.098003,0.040813],"ankleYaw":-2.5437144997272285}}},{"t":0.934444,"pelvis":[0.011156,0.99989,0.122599],"pelvisYaw":0.18249014861723536,"feet":{"left":{"toeVector":[0.025476,-0.082156,-0.061089],"ankleYaw":2.7028304432345016},"right":{"toeVector":[-0.039152,-0.097849,0.040435],"ankleYaw":-2.551200776286271}}},{"t":0.950556,"pelvis":[0.01166,1.002504,0.118568],"pelvisYaw":0.18385672187871982,"feet":{"left":{"toeVector":[0.027566,-0.088069,-0.051132],"ankleYaw":2.701096698427209},"right":{"toeVector":[-0.03931,-0.097714,0.040608],"ankleYaw":-2.5468405151898703}}}],"note":"60 source measurements for an independent fit holdout, not runtime keyframes. Discontinuous t=duration endpoint excluded."}
__HAREWORKS_FW_V012_5__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/README.md" <<'__HAREWORKS_FW_V012_6__'
# Hareworks Forward Woman Proof v0.1.2 | Independent pelvis and foot orientation

## Owner objective

Demonstrate that the actual skinned Hareworks woman's **forward walk** can be reconstructed with procedural leg trajectories and IK **without copying source pelvis and ankle orientation tracks** on the generated character. Allow camera orbiting to judge its motion. Do **not** add turning, strafing, aiming, root traveling, or a full locomotion system yet. The rejected v0.1.0 walker remains rejected; this is a separate proof.

## Exact sources and authority

- Repository: `Valar05/parametric-parambulator`, audited base `f322307c46e561443c3e0177ef309332fb51834d`.
- Original nine-clip Hareworks source preserved, SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`, 6,784,896 bytes.
- Existing v0.1.1 `gait-kernel.mjs` and `profile.json` remain authoritative for the **previously reviewed** forward ankle trajectory / analytic knee IK. Do not edit them.
- `hareworks-gait-and-idle-turn-v1.0.8.json`, extracted from that source, supplies 61 samples of `Walking_Woman`. The last sample at `t=duration` resets to a different pose. The new pelvis/foot harmonic fit is trained on **30 alternating samples of the 60 continuous frames**, with **30 held-out samples**. This is documented rather than smoothing across a false continuous endpoint.
- Read live `AGENTS.md`, Campaign Etiquette, Top-Down Etiquette; honor Termux Git-only publication, exact remote readback, and owner's visual acceptance.

## Generated motion

Left model plays original `Walking_Woman`. Right model retains the model's unchanged mesh, 74-joint skin, and nonleg upper-body source animation only. Source clip tracks for the hips, their ancestors, and **all leg bones** are excluded from its AnimationMixer. The generated pelvis position/yaw are computed from `motion-profile.json` Fourier phase curves and applied to the hips in their parent's local space. The ankle trajectories and analytically determined knee bends continue to use the unchanged v0.1.1 phase kernel. The ankles are rotated from procedural toe-direction and world-yaw curves, **not reference ankle quaternions**. The remaining toe joint's *local* seed rotation is unchanged; the completed skinned boot, ankle and toe must be visually inspected.

The new `pose-kernel-test.mjs` compares source-fit curves with the **30 measured holdout samples** at ~60Hz spacing and enumerates 30 FPS generated frames. It does not claim physical acceptance. The viewer offers side/front/top/three-quarter camera presets, touch-drag orbit, pinch zoom, a frame scrubber, 30 FPS step review, and exported real-bone traces. It rejects unreachable knee geometry, >0.012 ankle target residual, 60° or greater joint rotation per 30fps frame, and insufficient forward ankle travel as **mechanical gates**. Real-rig discrepancies otherwise remain visible and subject to owner review.

## Explicit limitations

This is still **in-place** source-style motion: upper torso/arms/head remain reference animated; it does **not** create independently traveling root motion, verified planted sole contacts, foot support dynamics, or a ready gameplay controller. New pelvis/foot orientation curves are a **reference-calibrated parametric reconstruction**, not generic human locomotion or learned dynamics. Positive fit results and HTTP checks do not establish believable skinned walking until the owner accepts the orbitable comparison.

## Execution evidence boundary

One SHA-checked downloadable Termux `.sh` authoring entrypoint, one isolated clone, exact new destination collisions checked before writes, text-only commit, no GLB mutation, no force push, remote SHA and blob readback, original LFS source verified and served over HTTP, JSON receipt and logs. Rerunning the same packet recovers the exact already-published candidate rather than creating a competing commit. Publication and browser HTTP availability are distinct from 30 FPS rig check and visual approval.
__HAREWORKS_FW_V012_6__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/contract.json" <<'__HAREWORKS_FW_V012_7__'
{
  "campaign": "hareworks-forward-woman-proof-v0.1.2",
  "repository": "Valar05/parametric-parambulator",
  "auditedParentCommit": "f322307c46e561443c3e0177ef309332fb51834d",
  "modelPath": "assets/hareworks/Hareworks-nine-clips.glb",
  "modelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "modelBytes": 6784896,
  "executionLane": "Android Termux Git only",
  "sourceClip": "Walking_Woman",
  "goal": "Reference-versus-generated skinned forward-walk proof with independent pelvis and ankle orientation, orbit camera, 30fps review; no locomotion expansion",
  "immutablePaths": [
    "AGENTS.md",
    "assets/repl/Repl.glb",
    "assets/hareworks/Hareworks.glb",
    "assets/hareworks/Hareworks-nine-clips.glb",
    "tools/hareworks-forward-woman/v0.1.1"
  ],
  "newOutputs": [
    "tools/hareworks-forward-woman/v0.1.2/index.html",
    "tools/hareworks-forward-woman/v0.1.2/viewer.mjs",
    "tools/hareworks-forward-woman/v0.1.2/pose-kernel.mjs",
    "tools/hareworks-forward-woman/v0.1.2/pose-kernel-test.mjs",
    "tools/hareworks-forward-woman/v0.1.2/motion-profile.json",
    "tools/hareworks-forward-woman/v0.1.2/reference-samples.json",
    "tools/hareworks-forward-woman/v0.1.2/README.md",
    "tools/hareworks-forward-woman/v0.1.2/contract.json",
    "campaigns/hareworks-forward-woman-proof-v0.1.2.sh"
  ],
  "successGates": [
    "exact source SHA and GLB structure",
    "60-frame reference profile and 30-sample holdout verified",
    "30fps generated forward ankle reach and continuous joints check in actual browser",
    "source hip/root and leg tracks explicitly excluded from generated mixer",
    "Git publication through Termux Git with exact remote readback",
    "interactive orbit camera and skinned visual owner review"
  ],
  "nonclaims": ["world-space planted walk", "full independent upper body", "strafing", "turning", "owner visual acceptance"]
}
__HAREWORKS_FW_V012_7__
fi
if ((PUBLISHED==0));then
 cp -- "$0" "campaigns/$CAMPAIGN.sh" || fail 'cannot install exact launcher source'
fi
phase='packet-hash'
# Every embedded payload file is held to its author-verified SHA, including
# recovery runs that skip writing new code. Requiring exact bytes prevents drift.
[[ "$(hash "$DIR/index.html")" == 'dcec759f82e98b386fd1731a4a7bf10c5166c954a97b170e8a4c3987a89cebb8' ]] || fail 'packet source digest mismatch index.html'
[[ "$(hash "$DIR/viewer.mjs")" == '4eacc88605503b0cd10924755e63b703dd3edc5f3a2b49433f3f9e4d9f854b03' ]] || fail 'packet source digest mismatch viewer.mjs'
[[ "$(hash "$DIR/pose-kernel.mjs")" == '649f6d0b0a0ebb99f01554bbfbadc32168c06b93beb67126c02ab5e4c2c0aa9f' ]] || fail 'packet source digest mismatch pose-kernel.mjs'
[[ "$(hash "$DIR/pose-kernel-test.mjs")" == 'a1c64a7d8efea9efe5e36b8644fce44ff393e4a3df58e3810754dbfbd8e0d7a1' ]] || fail 'packet source digest mismatch pose-kernel-test.mjs'
[[ "$(hash "$DIR/motion-profile.json")" == '93bf8471a3e21663a0a574460c07261cefcc23d1663f2a9a51284d5380ec6df7' ]] || fail 'packet source digest mismatch motion-profile.json'
[[ "$(hash "$DIR/reference-samples.json")" == 'a6215a2a7b3b8af7f207eb7248e53a67b7621340f34e641e9bf5940915648df5' ]] || fail 'packet source digest mismatch reference-samples.json'
[[ "$(hash "$DIR/README.md")" == '26347557b4805db4d8f08ef9be1ed41ca00a64504095ca88f5df17d8204546c9' ]] || fail 'packet source digest mismatch README.md'
[[ "$(hash "$DIR/contract.json")" == '8354ba998d2e817aa42eafd09508c1f26865c03274c762d4242851b9b3c16931' ]] || fail 'packet source digest mismatch contract.json'
[[ "$(hash "campaigns/$CAMPAIGN.sh")" == "$(hash "$0")" ]] || fail 'launcher/repository packet differs'
phase='validation'
python3 - "$DIR/motion-profile.json" "$DIR/reference-samples.json" "$DIR/contract.json" "$MODEL_SHA" <<'PY_VERIFY' || fail 'independent 30fps source fit and contract invalid'
import json,sys,math
p,r,c=(json.load(open(x)) for x in sys.argv[1:4]); source=sys.argv[4]
assert p['sourceSha256']==r['sourceSha256']==c['modelSha256']==source
assert p['clip']==r['clip']=='Walking_Woman' and len(r['samples'])==60
assert all(r['samples'][i]['t']<r['samples'][i+1]['t'] for i in range(59))
assert r['samples'][-1]['t']<p['duration']
def curve(ch,q):return ch['start']+sum(ch['sin'][k-1]*math.sin(2*math.pi*k*q)+ch['cosMinusOne'][k-1]*(math.cos(2*math.pi*k*q)-1) for k in range(1,5))
for i in range(1,60,2):
 row=r['samples'][i];q=row['t']/p['duration']
 for k,j in (('x',0),('y',1),('z',2)):
  assert abs(curve(p['pelvis'][k],q)-row['pelvis'][j])<.035
 assert abs(curve(p['pelvis']['yaw'],q)-row['pelvisYaw'])<.2
 for side in ('left','right'):
  for j,axis in enumerate('XYZ'):
   assert abs(curve(p['feet'][side]['toeVector'+axis],q)-row['feet'][side]['toeVector'][j])<.04
  assert abs(curve(p['feet'][side]['ankleYaw'],q)-row['feet'][side]['ankleYaw'])<.2
print('REAL_SOURCE_HOLDOUT=PASS 30 withheld samples across pelvis, toe vectors and ankle yaws')
PY_VERIFY
if command -v node >/dev/null;then
 node --check "$DIR/pose-kernel.mjs" || fail 'pose-kernel JS syntax failure'
 node --check "$DIR/viewer.mjs" || fail 'viewer JS syntax failure'
 node --check "$DIR/pose-kernel-test.mjs" || fail 'test JS syntax failure'
 node "$DIR/pose-kernel-test.mjs" > "$STATE/fit-test.json" || fail 'actual held-out motion fit test failed'
 node tools/hareworks-forward-woman/v0.1.1/kinematics-test.mjs > "$STATE/prior-geometry-test.json" || fail 'accepted v0.1.1 gait test regressed'
 echo 'SOURCE_FIT_30FPS_AND_LEG_BASELINE=PASS'
else
 echo 'NODE_NOT_INSTALLED=YES; Python independently validated the sampled pelvis and foot fit; browser rig gate still mandatory'
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
 for f in AGENTS.md assets/repl/Repl.glb assets/hareworks/Hareworks.glb "$MODEL" tools/hareworks-forward-woman/v0.1.1/profile.json tools/hareworks-forward-woman/v0.1.1/gait-kernel.mjs;do
  git diff --quiet -- "$f" || fail "protected worktree content changed: $f"
  [[ "$(git rev-parse "HEAD:$f")" == "$(git rev-parse "$BASE:$f")" ]] || fail "protected Git blob changed: $f"
 done
 phase='commit'
 git -c user.name='Hareworks Termux Campaign' -c user.email='hareworks-campaign@users.noreply.github.com' commit -m 'Proof Hareworks forward woman procedural pelvis and ankle pose v0.1.2' || fail 'commit failed'
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
for f in AGENTS.md assets/repl/Repl.glb assets/hareworks/Hareworks.glb "$MODEL" tools/hareworks-forward-woman/v0.1.1/gait-kernel.mjs tools/hareworks-forward-woman/v0.1.1/profile.json;do
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
 'ownerRejectedVersion':'v0.1.0','previousComparedVersion':'v0.1.1','mode':'forward-only skinned reference-vs-generated pelvis, foot yaw and leg IK','viewerUrl':url,'viewerPort':int(port),'viewerPid':int(pid),'snapshot':root,
 'networkModelBytesVerified':True,'mutatingExecutionLane':'Termux Git only','modelsAndPriorProofChanged':False,
 'browserRealRigCompleted':False,'ownerVisualAcceptance':False,'worldSpacePlantedFootstepController':False}
pathlib.Path(out).write_text(json.dumps(receipt,indent=2))
PY_RECEIPT
echo "REMOTE_COMMIT=$COMMIT"
echo "MODEL_SHA256=$MODEL_SHA"
echo "VIEWER_PORT=$PORT PID=$PID"
echo "VIEWER_URL=$URL"
echo "RECEIPT=$STATE/receipt.json"
echo 'REAL_SKINNED_ORBIT_30FPS_VISUAL_ACCEPTANCE=PENDING'
if command -v termux-open-url >/dev/null;then termux-open-url "$URL" || echo "BROWSER_LAUNCH_FAILED; OPEN $URL";else echo "TERMUX_OPEN_URL_UNAVAILABLE; OPEN $URL";fi
