#!/data/data/com.termux/files/usr/bin/bash
# Hareworks forward Woman v0.1.4: preserve lower body, repair upper continuity.
# Real 74-joint source, explicit upper Fourier fit, 30/60/120fps review.
# Only approved mutation/execution: Termux Git. Previous source remains immutable.
set -Eeuo pipefail
CAMPAIGN='hareworks-forward-woman-proof-v0.1.4'
REPO='Valar05/parametric-parambulator'
BASE='e7794120d5875aa1a56a4bc23bef46c4002fccfd'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_BYTES=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
LOCKED_V013_VIEWER='c67da8724ed8d6bbf346a77db9a1d13cd3c7e220'
LOCKED_V013_FOOT='8ca6a0c2b1973f71d3f6cb383612635252f9a042'
LOCKED_V013_FOOT_PROFILE='80deb7b695ec057ec993ae316a2ab01ce5ad59e950988bb4635d5bef513ea1c8'
LOCKED_V012_PELVIS='4d43c5864de31ec93563c42a910863579138e4c5'
DIR='tools/hareworks-forward-woman/v0.1.4'
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
exec > >(tee -a "$STATE/run.log") 2>&1
phase='preflight'
fail(){
  echo "BLOCKED step=$phase reason=$*"
  if [[ "$phase" == viewer && -n "${ROOT:-}" && -f "$ROOT/server.log" ]];then
    echo 'VIEWER_SERVER_LOG_TAIL:'; tail -n 30 "$ROOT/server.log" || true
  fi
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
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.3/viewer.mjs)" == "$LOCKED_V013_VIEWER" ]] || fail 'accepted lower-body viewer changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs)" == "$LOCKED_V013_FOOT" ]] || fail 'accepted lower-body solver changed'
[[ "$(git show HEAD:tools/hareworks-forward-woman/v0.1.3/foot-profile.json | sha256sum | cut -d' ' -f1)" == "$LOCKED_V013_FOOT_PROFILE" ]] || fail 'accepted lower-body profile changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.2/motion-profile.json)" == "$LOCKED_V012_PELVIS" ]] || fail 'pelvis profile changed, preserve owner-accepted hips'
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_BYTES" <<'PY_PTR' || fail 'source LFS pointer changed'
import subprocess,sys
path,oid,size=sys.argv[1:]
pointer=subprocess.check_output(['git','show','HEAD:'+path]);expected=(f'version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize {size}\n').encode()
assert pointer==expected,(pointer[:100],expected)
print('PUBLISHED_SOURCE_POINTER=PASS')
PY_PTR
FILES=("$DIR/index.html" "$DIR/viewer.mjs" "$DIR/upper-kernel.mjs" "$DIR/upper-kernel-test.mjs" "$DIR/README.md" "$DIR/contract.json" "campaigns/$CAMPAIGN.sh")
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
 cat > "$DIR/index.html" <<'__HAREWORKS_UPPER_V014_0__'
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#101821"><title>Hareworks | Woman Upper Continuity Proof v0.1.4</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>
:root{font:14px system-ui,sans-serif;color:#edf5ff;background:#101821;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:1150px;margin:auto;padding:12px}h1{font-size:19px;margin:3px 0}header{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center}p{line-height:1.45;color:#bcd0df;margin:8px 0}.pill{border:1px solid #51667c;padding:5px 9px;border-radius:20px;color:#cde1ef;font-size:11px}#status{padding:10px 0;color:#a4e9d7;min-height:43px}#stage{border:1px solid #506579;border-radius:10px;overflow:hidden;background:#09121b}#stage canvas{width:100%;display:block;touch-action:none}.labels{display:grid;grid-template-columns:1fr 1fr;text-align:center;gap:10px;margin:8px 0;color:#d8eaf6;font-size:12px}.toolbar,.cameraBar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}.cameraBar{background:#182a39;padding:8px;border-radius:8px}button{font:inherit;background:#2a455d;color:white;border:1px solid #617f98;border-radius:7px;min-height:42px;padding:9px 12px}button:focus-visible{outline:3px solid #7ae1fa}button:active{background:#456780}#metrics{white-space:pre-wrap;background:#1a2c3b;padding:10px;border-radius:7px;border:1px solid #435b6a;font:12px/1.5 ui-monospace,monospace;overflow-wrap:anywhere}small{color:#a8bacb}select{background:#213e54;color:#eaf6ff;border:1px solid #66879e;border-radius:5px;padding:6px}#frame{accent-color:#80dff3;flex:1;min-width:150px}label{display:flex;align-items:center;gap:7px}#frameNumber{min-width:6ch;text-align:right}#instructions{font-size:12px}@media(max-width:540px){main{padding:8px}.labels{font-size:11px}button{padding:8px 10px}h1{font-size:17px}}
</style></head><body><main>
<header><h1>🐇 Hareworks · Independent Forward Woman Proof</h1><span class="pill">v0.1.4 · preserve lower-body · 30/60/120 fps upper continuity</span></header>
<p>Left: the original <strong>Walking_Woman</strong>. Right: <strong>unchanged v0.1.2 generated pelvis, new reach-safe ankle trajectory, continuous knee-plane IK and analytically oriented feet</strong>. The generated side borrows only non-leg upper-body animation; no animated pelvis or leg tracks. v0.1.2 feet were visually rejected for snapping. Both use the same unchanged skinned GLB.</p>
<div class="labels"><strong>REFERENCE · source clip</strong><strong>GENERATED · fitted phase equations</strong></div>
<div id="status" role="status" aria-live="polite">Loading exact Hareworks source…</div>
<div id="stage" role="img" aria-label="Orbitable synchronized reference and procedural Hareworks 3D woman walking in place"></div>
<div class="cameraBar" role="group" aria-label="Camera controls"><strong>Camera:</strong><button id="side">Side</button><button id="front">Front</button><button id="top">Overhead</button><button id="oblique">Three-quarter</button><button id="resetCamera">Reset orbit</button><span id="instructions">Drag to orbit · pinch/scroll to zoom</span></div>
<div class="cameraBar" role="group" aria-label="Upper body procedural smoothing controls"><strong>Generated upper body:</strong><label>Motion <select id="upperStrength" aria-label="Upper body motion amplitude"><option value="0.70" selected>Restrained (70%)</option><option value="0.85">Natural (85%)</option><option value="1.0">Full (100%)</option><option value="0">Still (diagnostic)</option></select></label><label>Curve detail <select id="upperHarmonics" aria-label="Harmonics used to reconstruct the upper body"><option value="2">Smooth</option><option value="3" selected>Balanced</option><option value="4">Detailed</option></select></label><small>Reference left plays original clip. Right fits upper pose to periodic joint curves without source track playback.</small></div>
<div class="toolbar"><button id="play">Play one cycle</button><label>Playback <select id="playRate" aria-label="Playback sampling rate"><option value="60" selected>60 fps</option><option value="30">30 fps</option><option value="120">120 fps</option></select></label><label><input id="loop" type="checkbox" checked> Loop</label><button id="previous">◀ Frame</button><button id="next">Frame ▶</button><label>Frame <input type="range" min="0" max="28" step="1" value="0" id="frame" aria-label="Walk cycle frame"><output id="frameNumber">0/28</output></label><button id="test">Full 30/60/120 fps real-rig gate</button><button id="markers">Toggle joint markers</button><button id="export">Export evidence</button></div>
<div id="metrics" role="status" aria-live="off">Waiting for rig…</div>
<p><strong>Acceptance question:</strong> do the generated feet, knees, pitch and toe action match without popping, including near full extension and the cycle seam from side, front and overhead? This is a one-cycle <em>in-place leg-and-pelvis reproduction</em>, not world-space planted locomotion, strafing, turning or a complete game controller.</p>
<small>30 fps frame stepping remains available; high-rate playback defaults to 60 fps. The source extraction has an anomalous endpoint at exactly t=duration; the viewer excludes it. The gate samples 30, 60 and 120 Hz, checks joint rotations and tests atomic rollback. The model is hash-verified by the Termux launcher; real skinned acceptance is pending. Browser import uses Three.js 0.170.0 via CDN; camera requires pointer/touch events. Source GLB, v0.1.1, and other project assets are never modified.</small>
</main><script type="module" src="./viewer.mjs"></script></body></html>
__HAREWORKS_UPPER_V014_0__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/viewer.mjs" <<'__HAREWORKS_UPPER_V014_1__'
/* v0.1.4: preserve v0.1.3 leg/foot/pelvis posing byte-for-byte at the
 * procedural stage. Replace only generated character's clip-driven upper
 * body with a smooth, periodic, phase-fitted rotation-vector controller.
 * Reference remains original Walking_Woman. No root travel, lateral gait,
 * physical sole contact or independently travelling procedural walk claimed. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {independentPose,validateProfile,angleDiff} from '../v0.1.2/pose-kernel.mjs';
import {legAt,rotateY,kneeFromTarget,validateFootProfile} from '../v0.1.3/foot-kernel.mjs';
import {quatMultiply,quatConjugate,quatLog,quatExp,fitVectorSeries,evalVectorSeries,quatAngle} from './upper-kernel.mjs';

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
let reference,generated,refRig,genRig,refMixer,clip,profile,footProfile,seed,upperProfile,upperAudit;
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
// Source upper-body tracks are sampled ONCE as fitting evidence. Their
// keyframes never run on the generated character during playback. They are
// reconstructed by short periodic local rotation-vector functions.
function buildUpperProfile(boneNames,sampleCount=120,maxHarmonics=4){
 const bones=boneNames.map(name=>{
  const r=refRig.bones.get(name),g=genRig.bones.get(name);
  if(!r||!g||!g.isBone||!r.isBone)throw Error('UPPER_BONE_MISSING_'+name);
  return {name,reference:r,generated:g,seed:pose(g),rot:[],pos:[]};
 });
 const zero=clip.duration;
 for(let i=0;i<sampleCount;i++){
  refMixer.setTime(zero*i/sampleCount);reference.updateMatrixWorld(true);
  for(const b of bones){
   const q0=b.seed.quaternion.toArray(),q=b.reference.quaternion.toArray();
   b.rot.push(quatLog(quatMultiply(quatConjugate(q0),q)));
   b.pos.push(b.reference.position.clone().sub(b.seed.position).toArray());
  }
 }
 refMixer.setTime(0);reference.updateMatrixWorld(true);
 return bones.map(b=>({name:b.name,bone:b.generated,seed:b.seed,rotation:fitVectorSeries(b.rot,maxHarmonics),
    translation:fitVectorSeries(b.pos,maxHarmonics),sourceSampleRotations:b.rot.map(v=>v.slice())}));
}
function applyUpperBody(t){
 const strength=Number($('upperStrength').value),harmonics=Number($('upperHarmonics').value);
 const q=t/clip.duration;
 for(const item of upperProfile){
  const rot=evalVectorSeries(item.rotation,q,harmonics,strength);
  item.bone.quaternion.fromArray(quatMultiply(item.seed.quaternion.toArray(),quatExp(rot))).normalize();
  const dp=evalVectorSeries(item.translation,q,harmonics,strength);
  item.bone.position.copy(item.seed.position).add(V(...dp));
  item.bone.scale.copy(item.seed.scale);
 }
}
function upperFrameSnapshot(){
 const out={};for(const item of upperProfile)out[item.name]=item.bone.quaternion.toArray();
 return out;
}
function upperStepAudit(rate){
 const n=Math.floor((clip.duration-1e-4)*rate)+1;
 let before=null,maxStep=0,offender=null;const perBone={};
 for(let i=0;i<=n;i++){
  const t=i===n?0:i/rate;
  applyUpperBody(t);const sample=upperFrameSnapshot();
  if(before)for(const name of Object.keys(sample)){
   const deg=THREE.MathUtils.radToDeg(quatAngle(before[name],sample[name]));
   perBone[name]=Math.max(perBone[name]||0,deg);
   if(deg>maxStep){maxStep=deg;offender=name}
  }
  before=sample;
 }
 const offenders=Object.entries(perBone).sort((a,b)=>b[1]-a[1]).slice(0,10).map(([name,maxStepDeg])=>({name,maxStepDeg}));
 return {rateHz:rate,samples:n,maxStepDeg:maxStep,worstBone:offender,topTen:offenders};
}
function applyGeneratedPose(t,fault=null){
 const sourceTime=Math.min(t,clip.duration-1e-6);
 const prediction=independentPose(profile,sourceTime);
 applyUpperBody(sourceTime);
 for(const [b,p] of seed.legPose)restore(b,p);
 restore(genRig.hips,seed.hip);
 // The pelvis offset is in measured world units, transformed into the local
 // space of the hips parent. No source clip hip tracks run on generated.
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
 $('metrics').textContent=`v0.1.4 generated upper: periodic ${$('upperHarmonics').value}-harmonic fit / ${$('upperStrength').value} amplitude, NO upper clip playback\nFrame ${m.frame}/${nFrames-1}, time ${m.t.toFixed(3)}s\nGenerated hips Δ ${m.hipDiff.toFixed(4)} units / yaw Δ ${m.pelvisYawDiffDeg.toFixed(2)}°\nLEFT   forward ${m.legs.left.forward.toFixed(3)}   ankle Δ ${m.legs.left.ankleDiff.toFixed(3)}  knee Δ ${m.legs.left.kneeDiff.toFixed(3)}  toe Δ ${m.legs.left.toeDiff.toFixed(3)}\nRIGHT  forward ${m.legs.right.forward.toFixed(3)}   ankle Δ ${m.legs.right.ankleDiff.toFixed(3)}  knee Δ ${m.legs.right.kneeDiff.toFixed(3)}  toe Δ ${m.legs.right.toeDiff.toFixed(3)}\nFoot yaw reference Δ ${m.legs.left.ankleYawDifferenceToReferenceDeg.toFixed(1)}° / ${m.legs.right.ankleYawDifferenceToReferenceDeg.toFixed(1)}°\nAnkle IK residual ${m.legs.left.ikResidual.toFixed(5)} / ${m.legs.right.ikResidual.toFixed(5)}`;
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
for(const id of ['upperStrength','upperHarmonics'])$(id).addEventListener('change',()=>{if(running){sampleTime(cycleT);$('status').textContent='UPPER RECONSTRUCTION SETTINGS CHANGED · run real-rig checks again to measure continuity';}});
const jsonDownload=(filename,obj)=>{const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),4000)};
$('export').onclick=()=>{if(!lastReport){$('status').textContent='Run the 30 fps real-rig comparison first to create exportable evidence.';return}jsonDownload('hareworks-upper-continuity-v0.1.4.json',lastReport)};
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
   try{evaluateTime(rows[Math.min(rows.length-1,4)]?.t ?? (4/30),'unreachable');injection='FAULT_WAS_NOT_REJECTED'}
   catch(e){injection=/UNREACHABLE_KNEE/.test(e.message)&&poseMatches(before)?'ROLLBACK_PASS':'ROLLBACK_FAIL '+e.message}
 }catch(e){injection='ROLLBACK_EXCEPTION '+e.message}
 if(injection!=='ROLLBACK_PASS')errors.push({message:'ATOMIC_INJECTED_FAILURE',detail:injection});
 const upperRates=[30,60,120].map(upperStepAudit);
 for(const [rate,limit] of [[30,18],[60,11],[120,7]]){const measured=upperRates.find(r=>r.rateHz===rate);if(!Number.isFinite(measured.maxStepDeg)||measured.maxStepDeg>limit)errors.push({message:'UPPER_JOINT_SNAP',rate,maxStepDeg:measured.maxStepDeg,limit,worstBone:measured.worstBone});}
 const report={schema:'hareworks-forward-woman-v0.1.4-real-rig',sourceSha256:SOURCE,sourceClip:'Walking_Woman',pelvisImplementation:'v0.1.2 unchanged',legAnimationTracks:0,ankleTargets:'six-harmonic phase equation',anatomicalKneePoles:'six-harmonic phase equation',footOrientation:'analytical toe align and yaw twist',worldRootMotion:false,
  fpsRates:[30,60,120],rateReports,maxFront,minReach,maximumErrors:max,upperBody:{mode:'periodic phase fit from source joints, generated source track count 0',strength:Number($('upperStrength').value),harmonics:Number($('upperHarmonics').value),jointCount:upperProfile.length,rateAudits:upperRates},atomicInjection:injection,errors,rows,ownerAccepted:false,
  result:errors.length?'BLOCKED_REAL_RIG_PHYSICAL_GATE':'MEASURED_REQUIRES_OWNER_VISUAL_REVIEW'};
 lastReport=report;sampleFrame(0);
 $('status').textContent=report.result+' · '+rateReports.map(r=>r.completed+'/'+r.expected+' @'+r.fps).join(', ')+' · upper 30Hz max '+report.upperBody.rateAudits[0].maxStepDeg.toFixed(1)+'° ('+report.upperBody.rateAudits[0].worstBone+') · '+(errors[0]?.message||'review upper motion from side and oblique');
 console.info('HAREWORKS_v014_REAL_RIG_GATE',report);
 if(!auto)jsonDownload('hareworks-upper-continuity-v0.1.4.json',report);
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
 const upperNames=[...new Set(allowedTracks.map(tr=>tr.name.split('.')[0]))];
 upperProfile=buildUpperProfile(upperNames);
 upperAudit={upperSourceTracks:allowedTracks.length,generatedClipUpperTracks:0,fitSamples:120,upperBoneCount:upperProfile.length,sourceClip:clip.name};
 profile.zeroPelvis=[profile.pelvis.x.start,profile.pelvis.y.start,profile.pelvis.z.start];profile.zeroPelvisYaw=profile.pelvis.yaw.start;
 addMarkers(refRig,{left:0x1ecbff,right:0xffb767});addMarkers(genRig,{left:0x1ecbff,right:0xffb767});
 floor.position.y=new THREE.Box3().setFromObject(reference).min.y;
 nFrames=Math.floor(clip.duration*FPS)+1;while((nFrames-1)/FPS>=clip.duration-1e-6)nFrames--;
 $('frame').max=nFrames-1;
 running=true;display(evaluate(0));resize();cameraPreset('side');
 $('status').textContent=`REAL SKINNED GLB READY v0.1.4 · unchanged v0.1.3 legs + v0.1.2 hips; ${allowedTracks.length} source upper tracks calibrated, ZERO played on generated upper. Orbit to review shoulder, arm and head continuity.`;
 runRealRigGate(true);
 console.info('HAREWORKS_v014_TRACK_AUDIT',{excludedLeg:excludedLeg.length,excludedHip:excludedHip.length,upperBodyFitted:allowedTracks.length,upperProfile:upperAudit,sourceSha:SOURCE});
}catch(e){running=false;$('status').textContent='BLOCKED_SOURCE_OR_RIG '+e.message;console.error(e)}
__HAREWORKS_UPPER_V014_1__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/upper-kernel.mjs" <<'__HAREWORKS_UPPER_V014_2__'
/* Forward Woman v0.1.4: upper-body motion is Fourier-reconstructed from the
 * reference's local-space joint rotations once at startup. Generated upper
 * pose NEVER plays upper animation tracks after fitting. All calculations
 * operate on signed quaternion differences in the original joint local frame.
 * This module is pure and has no Three.js or browser dependency. */
export const TAU = Math.PI * 2;
export function finite3(v) { return Array.isArray(v)&&v.length===3&&v.every(Number.isFinite) }
export function quatConjugate(q) { return [-q[0],-q[1],-q[2],q[3]] }
export function quatMultiply(a,b){
 const [x,y,z,w]=a,[X,Y,Z,W]=b;
 return [w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X, w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z];
}
export function quatLog(raw) {
 if(!Array.isArray(raw)||raw.length!==4||!raw.every(Number.isFinite))throw Error('UPPER_QUAT_INVALID');
 const d=Math.hypot(...raw);if(d<1e-10)throw Error('UPPER_QUAT_ZERO');
 let [x,y,z,w]=raw.map(v=>v/d);
 // q and -q denote the same rotation: choose shortest local rotation.
 if(w<0){x=-x;y=-y;z=-z;w=-w}
 const n=Math.hypot(x,y,z);
 if(n<1e-11)return [2*x,2*y,2*z];
 const a=2*Math.atan2(n,w);
 return [x*a/n,y*a/n,z*a/n];
}
export function quatExp(v) {
 if(!finite3(v))throw Error('UPPER_ROT_VECTOR_INVALID');
 const a=Math.hypot(...v);const h=a*.5;
 const s=a<1e-9?.5:Math.sin(h)/a;
 return [v[0]*s,v[1]*s,v[2]*s,Math.cos(h)];
}
export function quatAngle(a,b){let d=Math.abs(a.reduce((s,x,i)=>s+x*b[i],0));d=Math.min(1,d);return 2*Math.acos(d)}
export function fitHarmonics(values,maxHarmonics=4){
 if(!Array.isArray(values)||values.length<2*maxHarmonics+4||!values.every(Number.isFinite))throw Error('UPPER_BAD_SAMPLE_SET');
 const n=values.length,mean=values.reduce((s,v)=>s+v,0)/n;
 const sin=[],cos=[];
 for(let h=1;h<=maxHarmonics;h++){
  let a=0,b=0;for(let i=0;i<n;i++){const p=TAU*h*i/n;a+=values[i]*Math.sin(p);b+=values[i]*Math.cos(p)}
  sin.push(2*a/n);cos.push(2*b/n);
 }
 // Force exact t=0 seed; periodic with equal derivatives at the seam.
 return {sin,cos,zero:mean+cos.reduce((s,x)=>s+x,0)};
}
export function evalHarmonics(c,q,limit=4) {
 if(!Number.isFinite(q))throw Error('UPPER_PHASE_NONFINITE');
 const p=((q%1)+1)%1, count=Math.min(limit,c.sin.length);
 let value=0;
 for(let i=0;i<count;i++){
  const a=TAU*(i+1)*p;
  value+=c.sin[i]*Math.sin(a)+c.cos[i]*(Math.cos(a)-1);
 }
 return value;
}
export function fitVectorSeries(samples,maxHarmonics=4){
 if(!samples.length||!samples.every(finite3))throw Error('UPPER_VECTOR_SAMPLE_INVALID');
 return [0,1,2].map(k=>fitHarmonics(samples.map(x=>x[k]),maxHarmonics));
}
export function evalVectorSeries(coeff,q,limit=4,strength=1){
 if(!Number.isFinite(strength)||strength<0||strength>1.5)throw Error('UPPER_STRENGTH_INVALID');
 return coeff.map(c=>evalHarmonics(c,q,limit)*strength);
}
export function angularStepSeries(rotVectors, seedQuat, stepHz=120){
 let max=0;let before=null;
 for(let i=0;i<=stepHz;i++){
  const v=rotVectors(i/stepHz),next=quatMultiply(seedQuat,quatExp(v));
  if(before)max=Math.max(max,quatAngle(before,next));
  before=next;
 }
 return max;
}
__HAREWORKS_UPPER_V014_2__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/upper-kernel-test.mjs" <<'__HAREWORKS_UPPER_V014_3__'
import assert from 'node:assert/strict';
import {TAU,quatMultiply,quatConjugate,quatLog,quatExp,quatAngle,fitHarmonics,evalHarmonics,fitVectorSeries,evalVectorSeries,angularStepSeries} from './upper-kernel.mjs';
const near=(a,b,e=1e-7)=>assert.ok(Math.abs(a-b)<e,`${a} != ${b}`);
const s=[0.22,-.13,.33],q=quatExp(s);const id=quatMultiply(q,quatConjugate(q));near(id[3],1);for(let i=0;i<3;i++)near(id[i],0);
const r=quatLog(q);for(let i=0;i<3;i++)near(r[i],s[i]);near(quatAngle(q,q.map(x=>-x)),0);
const N=240,values=Array.from({length:N},(_,i)=>.2*Math.sin(TAU*i/N)+.09*Math.cos(2*TAU*i/N)-.07*Math.sin(3*TAU*i/N));
const c=fitHarmonics(values,4);near(evalHarmonics(c,0),0);near(evalHarmonics(c,1),0);near(evalHarmonics(c,-1),0);
for(let i=0;i<N;i++){const t=i/N;near(evalHarmonics(c,t),values[i]-values[0],1e-7)}
for(let limit=1;limit<=4;limit++){near(evalHarmonics(c,0,limit),0);near(evalHarmonics(c,1,limit),0)}
const probes=Array.from({length:N},(_,i)=>[values[i],values[(i+N/2)%N]*.4,values[i]*.2]);
const fitted=fitVectorSeries(probes);const at=t=>evalVectorSeries(fitted,t,3,.75);
near(at(0)[0],0);near(at(1)[0],0);assert.ok(angularStepSeries(at,[0,0,0,1],120)<.10);
assert.throws(()=>fitHarmonics([NaN,1,2,3],1),/UPPER_BAD/);
assert.throws(()=>evalVectorSeries(fitted,.3,4,-1),/UPPER_STRENGTH/);
assert.throws(()=>quatLog([0,0,0,0]),/UPPER_QUAT_ZERO/);
console.log('UPPER_PHASE_FIT=PASS quaternion log/exp, sign parity, anchored periodic loops, constrained harmonic modes, synthetic 120Hz continuity, malformed-data rejection');
__HAREWORKS_UPPER_V014_3__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/README.md" <<'__HAREWORKS_UPPER_V014_4__'
# Hareworks forward Woman upper-body continuity v0.1.4

## Commissioned result and precise boundaries

The owner's high-frame-rate recording `5366.mp4` shows much improved **lower-body** motion on v0.1.3, but jarring upper-body movement. The user said "But lower I think looks good though". This campaign must preserve all lower-body mechanics: the immutable v0.1.3 `foot-kernel.mjs`, `foot-profile.json` and its IK statements, plus the v0.1.2 pelvis motion profile and equations. No model or animation asset is modified. The forward-only, in-place `Walking_Woman` clip comparison remains the only demonstration. No turning, strafing, world-space footsteps, other gait authoring, or new character.

## Change

The reference skinned character (left) continues to play the unmodified source `Walking_Woman` animation, including upper body. The generated character (right) no longer plays *any* source animation tracks during runtime. Instead, on loading the exact GLB, it **samples the source upper-body bones once** at 120 uniformly spaced points for joint-level calibration. For each eligible local bone quaternion, it converts the relative rotation into a shortest-path rotation vector, fits a compact periodic Fourier representation, and reconstructs a smooth local quaternion at arbitrary gait phase. The local positional deltas are likewise phase-fitted. The generator does not read clip upper rotations during rendering, so this is source-calibrated procedural playback, **not** a general reactive arm or balance system. No hips, legs, feet or toes are touched by the upper-body stage. Upper-body amplitude defaults to 70%, and harmonic detail to 3; alternate selectable levels (0, 70, 85, 100%, and 2/3/4 harmonics) enable direct visual comparisons, not independent acceptance claims. Shortest quaternion arcs, t=0 anchoring, periodic curves, and seam continuity avoid abrupt wrap corrections.

## Honest gates

- Offline Node test: quaternion signs, log/exp, 120 Hz periodic seam, smooth harmonic shape, invalid input rejection.
- Exact source/model verification: 74 joints, nine clips including `Walking_Woman`, canonical GLB SHA256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6` and 6,784,896 bytes, unchanged source and historic versions.
- Browser on actual skinned GLB: 30, 60, 120 fps gait cycles, joint continuity and reference differences, preserved leg and pelvis metrics, per-bone upper-body max quaternion steps, maximum offenders, actual fault injection and rollback diagnostics. The upper step limits (18°, 11°, 7° at 30/60/120) are **provisional review thresholds**, not accepted biomechanical rules. Exceedance remains a visible BLOCKED warning; the viewer still renders for diagnosis.
- The v0.1.3 acceptance is only the owner's "lower looks good" observation. This does not authorize changing leg paths or imply completed, realistic root locomotion.
- **No real-model viewer execution or visual acceptance is claimed until the Android browser runs.** No locally generated script, static screenshot, node test or Git readback substitutes for that evidence.

## Operator handoff

Execute the single SHA-verified `hareworks-forward-woman-proof-v0.1.4.sh` in Termux. It checks pinned Git parent and rules, validates exact original model locally or via LFS, checks unique destination paths, stages seven text files only, pushes without force, verifies remote SHA and blob parity, starts an isolated no-cache HTTP viewer and prints its actual full URL, PID, port, model hash, source revision and receipt. If publication already happened, the identical script can be rerun to recover the viewer without a new commit. A failed server check must report the exact HTTP path and `server.log`; it must never silently claim browser success.

Mandatory rules freshly read: GitHub `AGENTS.md` at parent `e7794120d5875aa1a56a4bc23bef46c4002fccfd` (Git blob `547c2af52303f4efb718bbf8f82a698110c7bfca`), Home Center Campaign Etiquette `1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI`, Top-Down Etiquette `1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU`.
__HAREWORKS_UPPER_V014_4__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/contract.json" <<'__HAREWORKS_UPPER_V014_5__'
{
  "campaign": "hareworks-forward-woman-proof-v0.1.4",
  "repo": "Valar05/parametric-parambulator",
  "auditedParentCommit": "e7794120d5875aa1a56a4bc23bef46c4002fccfd",
  "immutableModelPath": "assets/hareworks/Hareworks-nine-clips.glb",
  "immutableModelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "immutableModelBytes": 6784896,
  "sourceClip": "Walking_Woman",
  "newOutputs": ["tools/hareworks-forward-woman/v0.1.4/index.html", "tools/hareworks-forward-woman/v0.1.4/viewer.mjs", "tools/hareworks-forward-woman/v0.1.4/upper-kernel.mjs", "tools/hareworks-forward-woman/v0.1.4/upper-kernel-test.mjs", "tools/hareworks-forward-woman/v0.1.4/README.md", "tools/hareworks-forward-woman/v0.1.4/contract.json", "campaigns/hareworks-forward-woman-proof-v0.1.4.sh"],
  "protected": ["AGENTS.md", "assets/repl/Repl.glb", "assets/hareworks/Hareworks.glb", "assets/hareworks/Hareworks-nine-clips.glb", "tools/hareworks-forward-woman/v0.1.2", "tools/hareworks-forward-woman/v0.1.3"],
  "unchangedLegAndPelvis": ["tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs", "tools/hareworks-forward-woman/v0.1.3/foot-profile.json", "tools/hareworks-forward-woman/v0.1.2/pose-kernel.mjs", "tools/hareworks-forward-woman/v0.1.2/motion-profile.json"],
  "mission": "forward Woman upper-body continuity only, preserve lower body, procedural phase fit from source bone measurements",
  "runLane": "Android Termux Git only",
  "requiredBrowserEvidence": "actual source-skinned GLB upper continuity at 30/60/120Hz, rollback injection and full visual comparison",
  "accepted": false
}
__HAREWORKS_UPPER_V014_5__
fi
if ((PUBLISHED==0));then
 cp -- "$0" "campaigns/$CAMPAIGN.sh" || fail 'cannot install exact launcher source'
fi
phase='packet-hash'
[[ "$(hash "$DIR/index.html")" == '4c1993f22eee0746a5949775922e3f028f325ab5df5d8bedecb648433b936220' ]] || fail 'packet SHA mismatch: index.html'
[[ "$(hash "$DIR/viewer.mjs")" == '7ba8dbfe3f132e74c533133fd61a00ccf1364c5bbfe2bb4aac393ab8f6612a53' ]] || fail 'packet SHA mismatch: viewer.mjs'
[[ "$(hash "$DIR/upper-kernel.mjs")" == 'c075094cf4b1355b5363f64ef850e6a85484ef027a8082443c7c177d7c233324' ]] || fail 'packet SHA mismatch: upper-kernel.mjs'
[[ "$(hash "$DIR/upper-kernel-test.mjs")" == 'c45e57c74fc3492dbc1b94381588646e0d7ee881581065c7c8041f0ed8928ef6' ]] || fail 'packet SHA mismatch: upper-kernel-test.mjs'
[[ "$(hash "$DIR/README.md")" == '505d6b33f391956d01e4b8c7305411b5a6c318576ef2595ad49e69ea273e3505' ]] || fail 'packet SHA mismatch: README.md'
[[ "$(hash "$DIR/contract.json")" == 'c153fce1b8686a94f11a499aa8d4f9bf085208b3aa6cca383543e2d0689aae84' ]] || fail 'packet SHA mismatch: contract.json'
[[ "$(hash "campaigns/$CAMPAIGN.sh")" == "$(hash "$0")" ]] || fail 'launcher/repository packet differs'
phase='validation'
# Actual source joint chain integrity was checked above. Repeat regression gates
# on ALL previous authored solvers; none of those code/data files is modified.
for f in "$DIR/viewer.mjs" "$DIR/upper-kernel.mjs" "$DIR/upper-kernel-test.mjs";do node --check "$f" || fail "JavaScript syntax invalid: $f";done
node "$DIR/upper-kernel-test.mjs" | tee "$STATE/upper-kernel-test.log" || fail 'upper harmonic quaternion tests failed'
node tools/hareworks-forward-woman/v0.1.3/foot-kernel-test.mjs > "$STATE/previous-lower-body-test.log" || fail 'v0.1.3 leg/foot regression'
node tools/hareworks-forward-woman/v0.1.2/pose-kernel-test.mjs > "$STATE/previous-pelvis-test.log" || fail 'v0.1.2 pelvis regression'
python3 - "$DIR/viewer.mjs" "$DIR/index.html" "$DIR/contract.json" <<'PY_MISSION' || fail 'upper-only semantic source or HTML contract invalid'
import json,re,sys,subprocess
viewer,html,contract=(open(f).read() for f in sys.argv[1:]);c=json.loads(contract)
assert c['campaign']=='hareworks-forward-woman-proof-v0.1.4'
assert 'genMixer.setTime(' not in viewer and 'genMixer=new THREE.AnimationMixer(generated)' not in viewer
assert 'buildUpperProfile(upperNames)' in viewer and 'applyUpperBody(sourceTime)' in viewer
for id in ('upperStrength','upperHarmonics','test','export','play','stage','side','oblique'):
 assert f'id="{id}"' in html,(id,'missing HTML control')
# Compare actual procedural lower-body solver statements, not a green constant.
old=subprocess.check_output(['git','show','HEAD:tools/hareworks-forward-woman/v0.1.3/viewer.mjs'],text=True)
pattern=r" for\(const side of \['left','right'\]\)\{\n  const leg=genRig.legs\[side\],f=legAt\(footProfile.*?\n  rows.push\(r\);\n \}"
a=re.findall(pattern,old,re.S);b=re.findall(pattern,viewer,re.S)
assert len(a)==len(b)==1 and a[0]==b[0], 'protected leg IK target/rotation code changed'
assert "const prediction=independentPose(profile,sourceTime);" in viewer
assert "genRig.hips.quaternion.copy(localYaw.multiply(seed.hip.quaternion)).normalize();" in viewer
assert "const allowedTracks=clip.tracks.filter" in viewer
assert "upperProfile=buildUpperProfile(upperNames)" in viewer
print('PROTECTED_LOWER_KINEMATICS=BYTE_IDENTICAL, NEW_UPPER_CLIP_PLAYBACK=ZERO')
PY_MISSION
echo 'OFFLINE_UPPER_AND_PRESERVED_LEG_PELVIS_TESTS=PASS, BROWSER_SKINNED_REVIEW=PENDING'
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
 for f in AGENTS.md assets/repl/Repl.glb assets/hareworks/Hareworks.glb "$MODEL" tools/hareworks-forward-woman/v0.1.2/motion-profile.json tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs tools/hareworks-forward-woman/v0.1.3/foot-profile.json tools/hareworks-forward-woman/v0.1.3/viewer.mjs;do
  git diff --quiet -- "$f" || fail "protected worktree content changed: $f"
  [[ "$(git rev-parse "HEAD:$f")" == "$(git rev-parse "$BASE:$f")" ]] || fail "protected Git blob changed: $f"
 done
 phase='commit'
 git -c user.name='Hareworks Termux Campaign' -c user.email='hareworks-campaign@users.noreply.github.com' commit -m 'Refine Hareworks Woman upper body only and preserve v0.1.3 legs v0.1.4' || fail 'commit failed'
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
for f in AGENTS.md assets/repl/Repl.glb assets/hareworks/Hareworks.glb "$MODEL" tools/hareworks-forward-woman/v0.1.2/motion-profile.json tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs tools/hareworks-forward-woman/v0.1.3/foot-profile.json tools/hareworks-forward-woman/v0.1.3/viewer.mjs;do
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
  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
  self.send_header('Pragma','no-cache')
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
     curl -fsS --max-time 3 "http://127.0.0.1:$PORT/$DIR/upper-kernel.mjs" >/dev/null 2>&1 && \
     curl -fsS --max-time 3 "http://127.0.0.1:$PORT/tools/hareworks-forward-woman/v0.1.2/motion-profile.json" >/dev/null 2>&1 && \
     curl -fsS --max-time 3 "http://127.0.0.1:$PORT/tools/hareworks-forward-woman/v0.1.2/pose-kernel.mjs" >/dev/null 2>&1 && \
     curl -fsS --max-time 3 "http://127.0.0.1:$PORT/tools/hareworks-forward-woman/v0.1.3/foot-profile.json" >/dev/null 2>&1 && \
     curl -fsS --max-time 3 "http://127.0.0.1:$PORT/tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs" >/dev/null 2>&1;then READY_OK=1;break;fi
 fi
 sleep 1
done
[[ "$READY_OK" == 1 ]] && kill -0 "$PID" 2>/dev/null || fail 'HTTP viewer server failed; verified paths and snapshot/server.log in failure receipt' 
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
 'ownerObservation':'v0.1.3 lower looks good, upper snaps','previousComparedVersion':'v0.1.3','mode':'forward-only source-calibrated smooth upper; EXACT unchanged v0.1.3 lower/foot and v0.1.2 pelvis','viewerUrl':url,'viewerPort':int(port),'viewerPid':int(pid),'snapshot':root,
 'networkModelBytesVerified':True,'mutatingExecutionLane':'Termux Git only','modelsAndPriorProofChanged':False,
 'browserRealRigCompleted':False,'browserRealRigCheck':'auto-run 30/60/120 fps, upper quaternion continuity + leg and pelvis regression; not part of HTTP receipt','ownerVisualAcceptance':False,'worldSpacePlantedFootstepController':False}
pathlib.Path(out).write_text(json.dumps(receipt,indent=2))
PY_RECEIPT
echo "REMOTE_COMMIT=$COMMIT"
echo "MODEL_SHA256=$MODEL_SHA"
echo "VIEWER_PORT=$PORT PID=$PID"
echo "VIEWER_SOURCE_COMMIT=$COMMIT"
echo "VIEWER_HTML_PATH=$DIR/index.html"
echo "VIEWER_URL=$URL"
echo "RECEIPT=$STATE/receipt.json"
echo 'REAL_SKINNED_UPPER_CONTINUITY_30_60_120FPS_AND_OWNER_VISUAL_ACCEPTANCE=PENDING'
if command -v termux-open-url >/dev/null;then termux-open-url "$URL" || echo "BROWSER_LAUNCH_FAILED; OPEN $URL";else echo "TERMUX_OPEN_URL_UNAVAILABLE; OPEN $URL";fi
