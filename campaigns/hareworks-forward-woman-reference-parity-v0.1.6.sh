#!/data/data/com.termux/files/usr/bin/bash
# Hareworks v0.1.6: reference-vs-generated REAL-rig parity audit.
# SHA-guarded user Termux Git is the sole authorized mutation/execution lane.
set -Eeuo pipefail
CAMPAIGN='hareworks-forward-woman-reference-parity-v0.1.6'
REPO='Valar05/parametric-parambulator'
BASE='2397fd17b4a20bf99116f5eef28f69a52a00238b'
DIR='tools/hareworks-forward-woman/v0.1.6'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE='6784896'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
V015_VIEWER_BLOB='19a793e70d5e8a6c5e6fb9528a1fc5b7d7bb1b59'
V015_UPPER_BLOB='e5f04a8042d220118125cd736ddbe2502529fadf'
V013_LEG_BLOB='8ca6a0c2b1973f71d3f6cb383612635252f9a042'
V012_PELVIS_BLOB='4d43c5864de31ec93563c42a910863579138e4c5'
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
exec > >(tee -a "$STATE/run.log") 2>&1
phase=preflight;ROOT='';WORK='';COMMIT='';PID='';PORT='';SOURCE=''
fail(){
  echo "BLOCKED step=$phase reason=$*"
  if [[ -f "$ROOT/server.log" ]];then echo 'SERVER_LOG_TAIL:';tail -n 20 "$ROOT/server.log" || true;fi
  python3 - "$STATE/blocked.json" "$CAMPAIGN" "$phase" "$*" "$COMMIT" "$ROOT" <<'PY_BLOCK' || true
import datetime,json,pathlib,sys
out,campaign,phase,reason,commit,snapshot=sys.argv[1:]
pathlib.Path(out).write_text(json.dumps({'campaign':campaign,'state':'BLOCKED','phase':phase,'reason':reason,'publishedCommitIfKnown':commit,'snapshot':snapshot,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ownerAccepted':False},indent=2))
PY_BLOCK
  exit 1
}
hash(){ sha256sum -- "$1" | cut -d' ' -f1; }
if [[ "${1:-run}" == status ]];then
  [[ -f "$STATE/receipt.json" ]] && cat "$STATE/receipt.json" || echo "NO_RECEIPT=$STATE/receipt.json"
  exit 0
fi
[[ "${1:-run}" == run || "${1:-run}" == resume ]] || fail 'usage: bash script.sh [run|resume|status]'
for c in git python3 curl sha256sum node;do command -v "$c" >/dev/null || fail "missing: $c";done
SELF_SHA=$(hash "$0")
echo "CAMPAIGN=$CAMPAIGN"
echo "ENTRYPOINT_SHA256=$SELF_SHA"
echo "AUDITED_BASE=$BASE"
echo "KNOWN_MODEL_SHA256=$MODEL_SHA"
ORIGIN="https://github.com/$REPO.git"
REMOTE=''
for retry in 1 2 3;do
  REMOTE=$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1) || REMOTE=''
  [[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] && break
  sleep "$retry"
done
[[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] || fail 'Git main lookup failed'
echo "OBSERVED_REMOTE_MAIN=$REMOTE"
phase=isolation
ROOT=$(mktemp -d "$STATE/snapshot.XXXXXXXX") || fail 'temporary isolated snapshot failed'
WORK="$ROOT/repo"
for retry in 1 2;do
  if GIT_LFS_SKIP_SMUDGE=1 git -c lfs.install.skip=true clone --depth=1 --filter=blob:none --no-checkout --single-branch --branch main "$ORIGIN" "$WORK";then break;fi
  [[ ! -e "$WORK" ]] || fail 'partial isolated clone; snapshot preserved, no dirty checkout overwritten'
  sleep "$retry"
done
[[ -d "$WORK/.git" ]] || fail 'clone failed'
git -C "$WORK" sparse-checkout init --cone || fail 'sparse-checkout init failed'
git -C "$WORK" sparse-checkout set assets/hareworks tools/hareworks-forward-woman campaigns || fail 'sparse paths failed'
GIT_LFS_SKIP_SMUDGE=1 git -C "$WORK" checkout -B "$CAMPAIGN" "$REMOTE" || fail 'isolated checkout failed'
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$REMOTE" ]] || fail 'checked-out commit differs from remote main'
cd "$WORK"
phase=policy-and-baseline
[[ -f AGENTS.md ]] && grep -Fq 'Termux Git only' AGENTS.md || fail 'AGENTS.md authority missing'
[[ "$(git rev-parse HEAD:AGENTS.md)" == "$AGENTS_BLOB" ]] || fail 'AGENTS.md unexpected blob'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.5/viewer.mjs)" == "$V015_VIEWER_BLOB" ]] || fail 'v0.1.5 audited viewer changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.5/upper-kernel.mjs)" == "$V015_UPPER_BLOB" ]] || fail 'v0.1.5 upper kernel changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs)" == "$V013_LEG_BLOB" ]] || fail 'v0.1.3 leg solver changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.2/motion-profile.json)" == "$V012_PELVIS_BLOB" ]] || fail 'v0.1.2 pelvis profile changed'
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" <<'PY_POINTER' || fail 'original GLB published LFS pointer mismatch'
import subprocess,sys
path,sha,size=sys.argv[1:]
expected=f'version https://git-lfs.github.com/spec/v1\noid sha256:{sha}\nsize {size}\n'.encode()
assert subprocess.check_output(['git','show','HEAD:'+path])==expected
print('SOURCE_LFS_POINTER=PASS')
PY_POINTER
FILES=("$DIR/index.html" "$DIR/viewer.mjs" "$DIR/parity-math.mjs" "$DIR/parity-math-test.mjs" "$DIR/README.md" "$DIR/contract.json" "campaigns/$CAMPAIGN.sh")
phase=collision-gate
PUBLISHED=0
if [[ "$REMOTE" == "$BASE" ]];then
  for p in "${FILES[@]}";do
    [[ ! -e "$p" && ! -L "$p" ]] || fail "destination exists: $p"
    if git cat-file -e "HEAD:$p" 2>/dev/null;then fail "Git collision: $p";fi
  done
else
  if git cat-file -e "HEAD:campaigns/$CAMPAIGN.sh" 2>/dev/null && git cat-file -e "HEAD:$DIR/viewer.mjs" 2>/dev/null;then
    [[ "$(git show "HEAD:campaigns/$CAMPAIGN.sh" | sha256sum | cut -d' ' -f1)" == "$SELF_SHA" ]] || fail 'remote same campaign name is different bytes'
    [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'published revision parent changed; refuse ambiguous resume'
    PUBLISHED=1
    echo "EXACT_CAMPAIGN_ALREADY_PUBLISHED=$REMOTE; no new commit"
  else
    fail 'remote main advanced; no rebase, force push or overwrite'
  fi
fi
phase=source-model
# Locate previously verified source first, then fetch exact LFS identity if needed.
for base in "$HOME/.local/state/hareworks" "$HOME/storage/downloads" /storage/emulated/0/Download;do
  [[ -d "$base" ]] || continue
  maxdepth=1;[[ "$base" == "$HOME/.local/state/hareworks" ]] && maxdepth=10
  while IFS= read -r -d '' f;do
    [[ "$(wc -c < "$f" | tr -d ' ')" == "$MODEL_SIZE" ]] || continue
    if [[ "$(hash "$f")" == "$MODEL_SHA" ]];then SOURCE="$f";break;fi
  done < <(find -L "$base" -maxdepth "$maxdepth" -type f \( -iname '*.glb' -o -name "$MODEL_SHA" \) -print0 2>/dev/null)
  [[ -z "$SOURCE" ]] || break
done
if [[ -z "$SOURCE" ]];then
  command -v git-lfs >/dev/null || fail 'canonical GLB unavailable and git-lfs not installed'
  git lfs install --local || fail 'Git LFS configuration failed'
  for retry in 1 2;do
    if GIT_LFS_SKIP_SMUDGE=1 git lfs fetch -I "$MODEL" -X '' origin "$REMOTE";then break;fi
    sleep "$retry"
  done
  OBJ=$(git rev-parse --git-path "lfs/objects/${MODEL_SHA:0:2}/${MODEL_SHA:2:2}/$MODEL_SHA")
  [[ -f "$OBJ" ]] || fail 'exact LFS model object unavailable'
  SOURCE="$OBJ"
fi
[[ "$(wc -c < "$SOURCE" | tr -d ' ')" == "$MODEL_SIZE" && "$(hash "$SOURCE")" == "$MODEL_SHA" ]] || fail 'actual canonical GLB hash or size mismatch'
python3 - "$SOURCE" <<'PY_GLB' || fail 'real GLB skin or clip contract failed'
import struct,json,sys
with open(sys.argv[1],'rb') as f:b=f.read()
assert b[:4]==b'glTF' and len(b)==struct.unpack_from('<I',b,8)[0]
length,kind=struct.unpack_from('<I4s',b,12);assert kind==b'JSON'
g=json.loads(b[20:20+length]);assert len(g['skins'][0]['joints'])==74
assert len(g['animations'])==9 and 'Walking_Woman' in [a['name'] for a in g['animations']]
print('REAL_CANONICAL_GLTF_74_JOINTS_9_CLIPS=PASS')
PY_GLB
phase=packet
if ((PUBLISHED==0));then mkdir -p "$DIR" campaigns;fi
if ((PUBLISHED==0));then
 cat > "$DIR/index.html" <<'__HAREWORKS_PARITY_V016_INDEX_HTML__'
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#101821"><title>Hareworks | Woman Upper Continuity Proof v0.1.6</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>
:root{font:14px system-ui,sans-serif;color:#edf5ff;background:#101821;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:1150px;margin:auto;padding:12px}h1{font-size:19px;margin:3px 0}header{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center}p{line-height:1.45;color:#bcd0df;margin:8px 0}.pill{border:1px solid #51667c;padding:5px 9px;border-radius:20px;color:#cde1ef;font-size:11px}#status{padding:10px 0;color:#a4e9d7;min-height:43px}#stage{border:1px solid #506579;border-radius:10px;overflow:hidden;background:#09121b}#stage canvas{width:100%;display:block;touch-action:none}.labels{display:grid;grid-template-columns:1fr 1fr;text-align:center;gap:10px;margin:8px 0;color:#d8eaf6;font-size:12px}.toolbar,.cameraBar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}.cameraBar{background:#182a39;padding:8px;border-radius:8px}button{font:inherit;background:#2a455d;color:white;border:1px solid #617f98;border-radius:7px;min-height:42px;padding:9px 12px}button:focus-visible{outline:3px solid #7ae1fa}button:active{background:#456780}#parityReport{white-space:pre-wrap;background:#263340;color:#f2f5f8;padding:10px;border-left:3px solid #eab45b;margin:8px 0;font:12px/1.55 ui-monospace,monospace}#metrics{white-space:pre-wrap;background:#1a2c3b;padding:10px;border-radius:7px;border:1px solid #435b6a;font:12px/1.5 ui-monospace,monospace;overflow-wrap:anywhere}small{color:#a8bacb}select{background:#213e54;color:#eaf6ff;border:1px solid #66879e;border-radius:5px;padding:6px}#frame{accent-color:#80dff3;flex:1;min-width:150px}label{display:flex;align-items:center;gap:7px}#frameNumber{min-width:6ch;text-align:right}#instructions{font-size:12px}@media(max-width:540px){main{padding:8px}.labels{font-size:11px}button{padding:8px 10px}h1{font-size:17px}}
</style></head><body><main>
<header><h1>🐇 Hareworks · Independent Forward Woman Proof</h1><span class="pill">v0.1.6 · preserve lower-body · 30/60/120 fps upper continuity</span></header>
<p>Left: the original <strong>Walking_Woman</strong>. Right: <strong>unchanged v0.1.2 generated pelvis, new reach-safe ankle trajectory, continuous knee-plane IK and analytically oriented feet</strong>. Upper body is Fourier-fitted; none of the source tracks play on generated. This campaign measures fidelity and rejects mismatches. v0.1.2 feet were visually rejected for snapping. Both use the same unchanged skinned GLB.</p>
<div class="labels"><strong>REFERENCE · source clip</strong><strong>GENERATED · fitted phase equations</strong></div>
<div id="status" role="status" aria-live="polite">Loading exact Hareworks source…</div>
<div id="stage" role="img" aria-label="Orbitable synchronized reference and procedural Hareworks 3D woman walking in place"></div>
<div class="cameraBar" role="group" aria-label="Camera controls"><strong>Camera:</strong><button id="side">Side</button><button id="front">Front</button><button id="top">Overhead</button><button id="oblique">Three-quarter</button><button id="resetCamera">Reset orbit</button><span id="instructions">Drag to orbit · pinch/scroll to zoom</span></div>
<div class="cameraBar" role="group" aria-label="Upper body procedural smoothing controls"><strong>Generated upper body:</strong><label>Motion <select id="upperStrength" aria-label="Upper body motion amplitude"><option value="0.70">Restrained (70%)</option><option value="0.85">Natural (85%)</option><option value="1.0" selected>Full (100%)</option><option value="0">Still (diagnostic)</option></select></label><label>Curve detail <select id="upperHarmonics" aria-label="Harmonics used to reconstruct the upper body"><option value="2">Smooth</option><option value="3">Balanced</option><option value="4" selected>Detailed</option></select></label><small>Reference left plays original clip. Right fits upper pose to periodic joint curves without source track playback.</small></div>
<div class="toolbar"><button id="play">Play one cycle</button><label>Playback <select id="playRate" aria-label="Playback sampling rate"><option value="60" selected>60 fps</option><option value="30">30 fps</option><option value="120">120 fps</option></select></label><label><input id="loop" type="checkbox" checked> Loop</label><button id="previous">◀ Frame</button><button id="next">Frame ▶</button><label>Frame <input type="range" min="0" max="28" step="1" value="0" id="frame" aria-label="Walk cycle frame"><output id="frameNumber">0/28</output></label><button id="test">Continuity test</button><button id="parity">Measure reference parity</button><button id="markers">Toggle joint markers</button><button id="export">Export evidence</button></div>
<div id="parityReport" role="status" aria-live="polite">Awaiting exact-model parity measurements…</div><div id="metrics" role="status" aria-live="off">Waiting for rig…</div>
<p><strong>Verification-first:</strong> The viewer samples every fitted upper bone plus both ankles/knees at matching times on the exact skinned GLB, in 30/60/120Hz and half-frames. Rotation tolerance: 2° RMS, 5° max; joint-world-position tolerance: .01 model units RMS. It reports all failing joints and timestamps, not just movement smoothness.</p>
<p><strong>Acceptance question:</strong> do the generated feet, knees, pitch and toe action match without popping, including near full extension and the cycle seam from side, front and overhead? This is a one-cycle <em>in-place leg-and-pelvis reproduction</em>, not world-space planted locomotion, strafing, turning or a complete game controller.</p>
<small>30 fps frame stepping remains available; high-rate playback defaults to 60 fps. The source extraction has an anomalous endpoint at exactly t=duration; the viewer excludes it. The gate samples 30, 60 and 120 Hz, checks joint rotations and tests atomic rollback. The model is hash-verified by the Termux launcher; real skinned acceptance is pending. Browser import uses Three.js 0.170.0 via CDN; camera requires pointer/touch events. Source GLB, v0.1.1, and other project assets are never modified.</small>
</main><script>window.addEventListener('error',e=>{const s=document.getElementById('status');if(s)s.textContent='BROWSER_SCRIPT_ERROR '+(e.message||'module failure')});window.addEventListener('unhandledrejection',e=>{const s=document.getElementById('status');if(s)s.textContent='BROWSER_IMPORT_ERROR '+(e.reason?.message||e.reason)});</script><script type="module" src="./viewer.mjs"></script></body></html>
__HAREWORKS_PARITY_V016_INDEX_HTML__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/viewer.mjs" <<'__HAREWORKS_PARITY_V016_VIEWER_MJS__'
/* v0.1.6: preserve v0.1.3 leg/foot/pelvis posing byte-for-byte at the
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
import {quatMultiply,quatConjugate,quatLog,quatExp,fitVectorSeries,evalVectorSeries,quatAngle} from '../v0.1.5/upper-kernel.mjs';
import {createAudit, observe, finalizeAudit, rankOffenders} from './parity-math.mjs';

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
let nFrames=29,lastParityReport=null;
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
 $('metrics').textContent=`v0.1.6 generated upper: periodic ${$('upperHarmonics').value}-harmonic fit / ${$('upperStrength').value} amplitude, NO upper clip playback\nFrame ${m.frame}/${nFrames-1}, time ${m.t.toFixed(3)}s\nGenerated hips Δ ${m.hipDiff.toFixed(4)} units / yaw Δ ${m.pelvisYawDiffDeg.toFixed(2)}°\nLEFT   forward ${m.legs.left.forward.toFixed(3)}   ankle Δ ${m.legs.left.ankleDiff.toFixed(3)}  knee Δ ${m.legs.left.kneeDiff.toFixed(3)}  toe Δ ${m.legs.left.toeDiff.toFixed(3)}\nRIGHT  forward ${m.legs.right.forward.toFixed(3)}   ankle Δ ${m.legs.right.ankleDiff.toFixed(3)}  knee Δ ${m.legs.right.kneeDiff.toFixed(3)}  toe Δ ${m.legs.right.toeDiff.toFixed(3)}\nFoot yaw reference Δ ${m.legs.left.ankleYawDifferenceToReferenceDeg.toFixed(1)}° / ${m.legs.right.ankleYawDifferenceToReferenceDeg.toFixed(1)}°\nAnkle IK residual ${m.legs.left.ikResidual.toFixed(5)} / ${m.legs.right.ikResidual.toFixed(5)}`;
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
$('export').onclick=()=>{if(lastParityReport){jsonDownload('hareworks-forward-woman-parity-v0.1.6.json',lastParityReport);return;}if(lastReport)jsonDownload('hareworks-upper-continuity-v0.1.6.json',lastReport);else $('status').textContent='No measurements yet.';};
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
 const report={schema:'hareworks-forward-woman-v0.1.6-real-rig',sourceSha256:SOURCE,sourceClip:'Walking_Woman',pelvisImplementation:'v0.1.2 unchanged',legAnimationTracks:0,ankleTargets:'six-harmonic phase equation',anatomicalKneePoles:'six-harmonic phase equation',footOrientation:'analytical toe align and yaw twist',worldRootMotion:false,
  fpsRates:[30,60,120],rateReports,maxFront,minReach,maximumErrors:max,upperBody:{mode:'periodic phase fit from source joints, generated source track count 0',strength:Number($('upperStrength').value),harmonics:Number($('upperHarmonics').value),jointCount:upperProfile.length,rateAudits:upperRates},atomicInjection:injection,errors,rows,ownerAccepted:false,
  result:errors.length?'BLOCKED_REAL_RIG_PHYSICAL_GATE':'MEASURED_REQUIRES_OWNER_VISUAL_REVIEW'};
 lastReport=report;sampleFrame(0);
 $('status').textContent=report.result+' · '+rateReports.map(r=>r.completed+'/'+r.expected+' @'+r.fps).join(', ')+' · upper 30Hz max '+report.upperBody.rateAudits[0].maxStepDeg.toFixed(1)+'° ('+report.upperBody.rateAudits[0].worstBone+') · '+(errors[0]?.message||'review upper motion from side and oblique');
 console.info('HAREWORKS_v014_REAL_RIG_GATE',report);
 if(!auto)jsonDownload('hareworks-upper-continuity-v0.1.6.json',report);
}
$('test').onclick=()=>runRealRigGate(false);

// Source-vs-generated parity is a separate acceptance gate from smoothness.
// Sample ACTUAL posed bones in both skinned models; never compare two fits.
function compareCurrentToReference(audit,rate,t,m) {
  const refShift=V(0,0,SEP);
  for (const b of upperProfile) {
    const r=refRig.bones.get(b.name),g=b.bone;
    if (!r || !g) throw Error('PARITY_JOINT_MISSING_'+b.name);
    observe(audit,b.name,'localRotationDeg',rad(r.quaternion.angleTo(g.quaternion)),rate,t);
    observe(audit,b.name,'worldRotationDeg',rad(wq(r).angleTo(wq(g))),rate,t);
    observe(audit,b.name,'localPosition',r.position.distanceTo(g.position),rate,t);
    observe(audit,b.name,'worldPosition',world(r).add(refShift).distanceTo(world(g)),rate,t);
  }
  for (const side of ['left','right']) {
    const lm=m.legs[side];
    observe(audit,side+'-ankle','worldPosition',lm.ankleDiff,rate,t);
    observe(audit,side+'-knee','worldPosition',lm.kneeDiff,rate,t);
  }
}
function measurePreset(strength,harmonics) {
  $('upperStrength').value=String(strength);
  $('upperHarmonics').value=String(harmonics);
  const audit=createAudit();const errors=[];const counts=[];
  for(const rate of [30,60,120]) {
    let n=0;
    // Include exact frame samples and midframes; do not sample the reset endpoint.
    for(let i=0;i<Math.floor(clip.duration*rate)*2;i++) {
      const t=i/(2*rate);
      if(t>=clip.duration-1e-8)break;
      try { const metrics=evaluateTime(t);compareCurrentToReference(audit,rate,t,metrics);n++; }
      catch(e) {errors.push({rateHz:rate,t,kind:'REAL_SKINNED_EVALUATION',message:e.message});}
    }
    // Near seam at each rate and at t=0 (separate from the source's anomalous endpoint).
    for(const t of [0,clip.duration-1e-6]){
      try{const metrics=evaluateTime(t);compareCurrentToReference(audit,rate,t,metrics);n++;}
      catch(e){errors.push({rateHz:rate,t,kind:'SEAM_EVALUATION',message:e.message});}
    }
    counts.push({rateHz:rate,sampledPoses:n});
  }
  const summary=finalizeAudit(audit);
  const failures=[];
  // These are provisional reproduction tolerances. No hidden widening on failure.
  for(const [bone,kinds] of Object.entries(summary)) {
    const upper=upperProfile.some(b=>b.name===bone);
    if(upper) {
      const rot=kinds.localRotationDeg, pos=kinds.worldPosition;
      if(!rot||rot.rms>2||rot.max>5)failures.push({bone,measurement:'localRotationDeg',rms:rot?.rms,max:rot?.max,limitRms:2,limitMax:5});
      if(!pos||pos.rms>.01)failures.push({bone,measurement:'worldPosition',rms:pos?.rms,limitRms:.01});
    } else if(!kinds.worldPosition||kinds.worldPosition.rms>.01) {
      failures.push({bone,measurement:'lowerBodyWorldPosition',rms:kinds.worldPosition?.rms,limitRms:.01});
    }
  }
  if(!Object.keys(summary).length)failures.push({kind:'NO_VALID_SAMPLES'});
  if(errors.length)failures.push({kind:'RIG_EVALUATION_ERRORS',count:errors.length});
  const offenders=rankOffenders(summary,'localRotationDeg',12);
  const positionOffenders=rankOffenders(summary,'worldPosition',12);
  return {preset:{strength,harmonics},fps:[30,60,120],counts,poseErrors:errors.slice(0,60),poseErrorCount:errors.length,
    thresholds:{upperRotationRmsDeg:2,upperRotationMaxDeg:5,worldJointPositionRms:.01,lowerJointPositionRms:.01},
    jointCount:Object.keys(summary).length,allMeasurements:summary,offenders,positionOffenders,
    failures:failures.slice(0,100),failureCount:failures.length,
    verdict:failures.length?'REJECTED_PARITY_OUTSIDE_TOLERANCE':'MEASURED_WITHIN_PROVISIONAL_TOLERANCE_OWNER_REVIEW_REQUIRED'};
}
function runParityAudit(exportNow=false){
  if(!running)return;
  const saved={strength:$('upperStrength').value,harmonics:$('upperHarmonics').value,time:cycleT,playing};
  playing=false;
  let report;
  try {
    const trials=[];
    trials.push(measurePreset(.7,3)); // exact previous v0.1.5 default
    trials.push(measurePreset(1,4)); // highest-fidelity existing curve setting
    report={schema:'hareworks-reference-parity-v0.1.6',modelSha256:SOURCE,sourceClip:'Walking_Woman',
      auditedPublishedImplementation:'v0.1.5 pose equations unchanged',
      evidence:'exact GLB / reference animation vs generated skinned bone transforms at matched timestamps',
      referenceModelOffsetRemoved:true,referenceNotUsedAsGeneratedRuntimeTracks:true,
      sampledRatesHz:[30,60,120],halfFrames:true,sourceEndpointExcluded:true,
      variants:trials,ownerVisualAcceptance:false,requestedOutcome:'small_error_reference_replication',
      note:'This measures accuracy, not independently moving world-space locomotion.'};
    lastParityReport=report;
    if(lastReport)lastReport.referenceParity=report;
    const best=trials.reduce((a,b)=>a.failureCount<=b.failureCount?a:b);
    const worst=best.offenders[0];const pos=best.positionOffenders[0];
    $('parityReport').textContent=`REFERENCE PARITY v0.1.6 | exact source vs skinned generated\n`+
      trials.map(x=>`Amplitude ${x.preset.strength}, harmonics ${x.preset.harmonics}: ${x.verdict}, ${x.failureCount} violations, ${x.poseErrorCount} pose errors`).join('\n')+
      `\nBest-by-failures worst local bone rotation: ${worst?.bone||'none'} RMS ${worst?.rms?.toFixed(2)||'?'}° max ${worst?.max?.toFixed(2)||'?'}° at ${worst?.worst?.t?.toFixed(3)||'?'}s`+
      `\nWorst world joint displacement: ${pos?.bone||'none'} RMS ${pos?.rms?.toFixed(4)||'?'} max ${pos?.max?.toFixed(4)||'?'}`+
      `\n30/60/120Hz plus half-frames; all joint results in Export evidence. No automatic tolerance relaxation.`;
    $('status').textContent=trials.every(x=>!x.failureCount)?'REFERENCE_PARITY_MEASURED_WITHIN_TOLERANCE · owner review pending':'REJECTED_REFERENCE_PARITY · select Export evidence for failing joints/timestamps';
    if(exportNow)jsonDownload('hareworks-forward-woman-parity-v0.1.6.json',report);
  }catch(e){$('parityReport').textContent='PARITY_GATE_EXCEPTION '+e.message;console.error(e)}
  finally{
    $('upperStrength').value=saved.strength;$('upperHarmonics').value=saved.harmonics;
    try{sampleTime(saved.time)}catch(e){console.error(e)}
    playing=saved.playing;
  }
  return report;
}
$('parity').onclick=()=>runParityAudit(true);


try{
 const paths=['../v0.1.2/motion-profile.json','../v0.1.3/foot-profile.json'];
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
 $('status').textContent=`REAL SKINNED GLB READY v0.1.6 · unchanged v0.1.3 legs + v0.1.2 hips; ${allowedTracks.length} source upper tracks calibrated, ZERO played on generated upper. Orbit to review shoulder, arm and head continuity.`;
 runRealRigGate(true);
 runParityAudit(false);
 console.info('HAREWORKS_v014_TRACK_AUDIT',{excludedLeg:excludedLeg.length,excludedHip:excludedHip.length,upperBodyFitted:allowedTracks.length,upperProfile:upperAudit,sourceSha:SOURCE});
}catch(e){running=false;$('status').textContent='BLOCKED_SOURCE_OR_RIG '+e.message;console.error(e)}
__HAREWORKS_PARITY_V016_VIEWER_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/parity-math.mjs" <<'__HAREWORKS_PARITY_V016_PARITY_MATH_MJS__'
/* Exact-time source-versus-generated scalar error accumulator. Pure JS.
   The caller must sample independently posed real rig joints. */
export function createAudit(){return Object.create(null)}
export function observe(audit,bone,measurement,error,rateHz,timeSeconds){
 if(!bone||!measurement||!Number.isFinite(error)||error<0||!Number.isFinite(rateHz)||rateHz<=0||!Number.isFinite(timeSeconds)||timeSeconds<0)throw Error('PARITY_INVALID_OBSERVATION');
 const group=audit[bone]??(audit[bone]=Object.create(null));
 const a=group[measurement]??(group[measurement]={n:0,sumSq:0,max:-Infinity,worst:null,byRate:Object.create(null)});
 a.n++;a.sumSq+=error*error;
 if(error>a.max){a.max=error;a.worst={t:timeSeconds,rateHz,error}}
 const r=a.byRate[rateHz]??(a.byRate[rateHz]={n:0,sumSq:0,max:0});
 r.n++;r.sumSq+=error*error;r.max=Math.max(r.max,error);
}
export function finalizeAudit(audit){
 const out=Object.create(null);
 for(const [bone,kinds] of Object.entries(audit)){
  out[bone]=Object.create(null);
  for(const [kind,a] of Object.entries(kinds)){
   if(!a.n)throw Error('PARITY_EMPTY_METRIC');
   const byRate=Object.create(null);
   for(const [rate,r] of Object.entries(a.byRate))byRate[rate]={n:r.n,rms:Math.sqrt(r.sumSq/r.n),max:r.max};
   out[bone][kind]={samples:a.n,rms:Math.sqrt(a.sumSq/a.n),max:a.max,worst:a.worst,byRate};
  }
 }
 return out;
}
export function rankOffenders(report,metric,count=10){
 return Object.entries(report).filter(([_,m])=>m[metric]).map(([bone,m])=>({bone,...m[metric]})).sort((a,b)=>b.rms-a.rms).slice(0,count);
}
__HAREWORKS_PARITY_V016_PARITY_MATH_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/parity-math-test.mjs" <<'__HAREWORKS_PARITY_V016_PARITY_MATH_TEST_MJS__'
import assert from 'node:assert/strict';
import {createAudit,observe,finalizeAudit,rankOffenders} from './parity-math.mjs';
const a=createAudit();
observe(a,'mixamorigLeftArm','localRotationDeg',1,30,0);
observe(a,'mixamorigLeftArm','localRotationDeg',3,60,.1);
observe(a,'mixamorigLeftArm','worldPosition',.003,30,0);
observe(a,'mixamorigRightArm','localRotationDeg',12,120,.2);
const result=finalizeAudit(a);
assert.equal(result.mixamorigLeftArm.localRotationDeg.samples,2);
assert.ok(Math.abs(result.mixamorigLeftArm.localRotationDeg.rms-Math.sqrt(5))<1e-10);
assert.equal(result.mixamorigLeftArm.localRotationDeg.max,3);
assert.equal(result.mixamorigLeftArm.localRotationDeg.worst.t,.1);
assert.equal(result.mixamorigLeftArm.localRotationDeg.byRate['30'].n,1);
assert.equal(rankOffenders(result,'localRotationDeg')[0].bone,'mixamorigRightArm');
assert.ok(result.mixamorigRightArm.localRotationDeg.rms>2,'deliberately altered arm must violate 2deg RMS');
assert.ok(result.mixamorigRightArm.localRotationDeg.max>5,'deliberately altered arm must violate 5deg maximum');
for (const bad of [NaN,Infinity,-1])assert.throws(()=>observe(a,'bone','localRotationDeg',bad,120,.3),/INVALID/);
assert.deepEqual(Object.keys(finalizeAudit(createAudit())),[]);
console.log('PARITY_ACCUMULATOR_PASS positive, injected wrong-bone negative, RMS/rate, worst frame, finite guards');
__HAREWORKS_PARITY_V016_PARITY_MATH_TEST_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/README.md" <<'__HAREWORKS_PARITY_V016_README_MD__'
# Hareworks `Walking_Woman` real-rig parity gate v0.1.6

Purpose: independently audit the existing v0.1.5 mathematical reconstruction against the original `Walking_Woman` animated skeleton at identical timestamps, using the exact 74-bone skinned Hareworks source. User found upper-body motion visually worse than source. Preserve v0.1.3 leg IK, v0.1.2 pelvis and v0.1.5 upper solver; do not author new motion curves.

The original on left plays source clip. Generated on right has source-fitted pelvis, feet, and upper body, with NO animated source tracks running on generated after calibration. The diagnostic measures each fitted upper joint's local quaternion angular error, world quaternion angular error, local translation difference, and world position error after removing the side-by-side display offset. Both ankles and knees are measured from the real posed rig. Sample rates are 30/60/120Hz with midframes and near-boundary.

Compare default 0.70 amplitude/3 harmonics (the prior candidate) against 1.00 amplitude/4 harmonics (the highest fidelity allowed by the existing controller), no retuning or silent switch during a result. The viewer displays 1.00/4 by default for review. The exported JSON includes every fitted upper bone's RMS/max/worst timestamp and explicit failure reasons, with provisional hard thresholds: upper local rotation <=2 degrees RMS and <=5 degrees max, upper and lower world joint position <=0.01 model units RMS. Any exceedance is REJECTED_PARITY_OUTSIDE_TOLERANCE; do not call it matched or accepted. Real visual approval remains distinct.

The original GLB, all previous proof files and animation tracks are immutable. The versioned campaign is authored with live AGENTS / Campaign Etiquette / Top-down Etiquette read and pins Git parent 2397fd17b4a20bf99116f5eef28f69a52a00238b, known source LFS SHA a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6. Publication and proof viewer startup via owner-operated, SHA-verified Android Termux Git only.

The operator script must pass JS syntax, parity math fixtures (including injected wrong bone), original lower/upper regression tests, GLB byte/rig preflight, exact Git commit/readback, fresh HTTP no-cache resource checks; then Android browser carries the final actual-rig numerical gate and owner visual review. It prints the actual URL, not an invented port.
__HAREWORKS_PARITY_V016_README_MD__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/contract.json" <<'__HAREWORKS_PARITY_V016_CONTRACT_JSON__'
{
  "campaign": "hareworks-forward-woman-reference-parity-v0.1.6",
  "repository": "Valar05/parametric-parambulator",
  "auditedParentCommit": "2397fd17b4a20bf99116f5eef28f69a52a00238b",
  "sourceSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "sourceModelPath": "assets/hareworks/Hareworks-nine-clips.glb",
  "sourceClip": "Walking_Woman",
  "ownerAcceptance": "pending, v0.1.5 visually rejected upper body",
  "scope": "verification of reference vs generated upper and lower real-rig joints, no algorithm modification",
  "executionLane": "Android Termux Git only",
  "newOutputs": [
    "tools/hareworks-forward-woman/v0.1.6/index.html",
    "tools/hareworks-forward-woman/v0.1.6/viewer.mjs",
    "tools/hareworks-forward-woman/v0.1.6/parity-math.mjs",
    "tools/hareworks-forward-woman/v0.1.6/parity-math-test.mjs",
    "tools/hareworks-forward-woman/v0.1.6/README.md",
    "tools/hareworks-forward-woman/v0.1.6/contract.json",
    "campaigns/hareworks-forward-woman-reference-parity-v0.1.6.sh"
  ],
  "thresholds": {
    "localRotationRmsDeg": 2,
    "localRotationMaxDeg": 5,
    "jointWorldPositionRms": 0.01
  },
  "protected": [
    "AGENTS.md",
    "assets/hareworks/Hareworks-nine-clips.glb",
    "tools/hareworks-forward-woman/v0.1.2",
    "tools/hareworks-forward-woman/v0.1.3",
    "tools/hareworks-forward-woman/v0.1.4",
    "tools/hareworks-forward-woman/v0.1.5"
  ],
  "review": "rendered model and human visual inspection still required"
}
__HAREWORKS_PARITY_V016_CONTRACT_JSON__
fi
if ((PUBLISHED==0));then
 cp -- "$0" "campaigns/$CAMPAIGN.sh" || fail 'cannot copy SHA verified campaign into scoped Git path'
fi
phase=packet-hashes
[[ "$(hash "$DIR/index.html")" == "e30a4f240f4109e793e8c23a31bd6da07cd33b20bdd6886c1d6392f3fd06d7fa" ]] || fail "embedded file digest mismatch: index.html"
[[ "$(hash "$DIR/viewer.mjs")" == "4b3b62293f8d8ff3be98517d7f97a756af3aeb92f457cd52081d1ee93c9709c0" ]] || fail "embedded file digest mismatch: viewer.mjs"
[[ "$(hash "$DIR/parity-math.mjs")" == "a766978cfff2ae92e117c5e3c5038ca0c03baa7eb3e2ee933c6a97dc1366fba9" ]] || fail "embedded file digest mismatch: parity-math.mjs"
[[ "$(hash "$DIR/parity-math-test.mjs")" == "9a30b3bce47b91ce5f23df540e2b6128a6bb0afec8e16b59bba670d006a2df07" ]] || fail "embedded file digest mismatch: parity-math-test.mjs"
[[ "$(hash "$DIR/README.md")" == "da73ddfa0c772eb4326ec63787e3a97324afc589ba27487169d30f1f67afa3a2" ]] || fail "embedded file digest mismatch: README.md"
[[ "$(hash "$DIR/contract.json")" == "371ce3c1f80dfd573795edb8c8755c72697828e17cb4c4f22b4343e0e5df8a3f" ]] || fail "embedded file digest mismatch: contract.json"
[[ "$(hash "campaigns/$CAMPAIGN.sh")" == "$SELF_SHA" ]] || fail 'on-disk campaign source differs from attached bytes'
phase=validation
for js in "$DIR/viewer.mjs" "$DIR/parity-math.mjs" "$DIR/parity-math-test.mjs";do node --check "$js" || fail "JS syntax: $js";done
node "$DIR/parity-math-test.mjs" | tee "$STATE/parity-math-tests.log" || fail 'reference parity math negative fixture failed'
node tools/hareworks-forward-woman/v0.1.5/upper-kernel-test.mjs > "$STATE/upper-regression.log" || fail 'preserved v0.1.5 upper kernel regressed'
node tools/hareworks-forward-woman/v0.1.3/foot-kernel-test.mjs > "$STATE/leg-regression.log" || fail 'preserved leg regression failed'
node tools/hareworks-forward-woman/v0.1.2/pose-kernel-test.mjs > "$STATE/pelvis-regression.log" || fail 'preserved pelvis regression failed'
python3 - "$DIR" "$MODEL" "$MODEL_SHA" <<'PY_DEPS' || fail 'runtime dependency manifest invalid'
import pathlib,re,json,sys
p=pathlib.Path(sys.argv[1]);model=pathlib.Path(sys.argv[2]);sha=sys.argv[3]
src=(p/'viewer.mjs').read_text();html=(p/'index.html').read_text()
assert "../v0.1.5/upper-kernel.mjs" in src
assert "../v0.1.3/foot-kernel.mjs" in src
assert "../v0.1.2/pose-kernel.mjs" in src
assert "../v0.1.3/foot-profile.json" in src
assert 'runParityAudit(false)' in src and 'compareCurrentToReference' in src
for x in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",src):
 assert (p/x).resolve(strict=True).is_file(),('missing JS dependency',x)
for x in re.findall(r"const paths=\['([^']+)','([^']+)'\];",src):
 for item in x:
  d=json.loads((p/item).read_text());assert d['sourceSha256']==sha and d['clip']=='Walking_Woman'
assert 'id="parity"' in html and 'id="parityReport"' in html
assert 'src="./viewer.mjs"' in html
assert 'v0.1.6' in html and 'v0.1.6' in src
assert 'motion-profile.json' in src and 'foot-profile.json' in src
assert model.exists()
print('BROWSER_JS_JSON_MODEL_IMPORT_CONTRACT=PASS')
PY_DEPS
# Ensure generated motion algorithms have NOT changed, even if their tests pass.
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.5/upper-kernel.mjs)" == "$V015_UPPER_BLOB" ]] || fail 'upper solver mutated during packet production'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs)" == "$V013_LEG_BLOB" ]] || fail 'lower solver mutated during packet production'
if ((PUBLISHED==0));then
  phase=scoped-git-stage
  [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'GitHub main changed before publication'
  git add -- "${FILES[@]}" || fail 'scoped git add failed'
  python3 - "${FILES[@]}" <<'PY_SCOPE' || fail 'staged set differs from allowed seven text files'
import subprocess,sys
expected=set(sys.argv[1:]);actual=set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines())
assert expected==actual,{'missing':sorted(expected-actual),'unexpected':sorted(actual-expected)}
assert all(not p.endswith('.glb') for p in actual)
print('STAGED_ONLY_SEVEN_NEW_TEXT_FILES=PASS')
PY_SCOPE
  for protected in AGENTS.md "$MODEL" assets/repl/Repl.glb assets/hareworks/Hareworks.glb tools/hareworks-forward-woman/v0.1.5/viewer.mjs tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs tools/hareworks-forward-woman/v0.1.2/motion-profile.json;do
    git diff --quiet -- "$protected" || fail "immutable worktree file changed: $protected"
    [[ "$(git rev-parse "HEAD:$protected")" == "$(git rev-parse "$BASE:$protected")" ]] || fail "protected Git baseline changed: $protected"
  done
  phase=commit
  git -c user.name='Hareworks Termux Campaign' -c user.email='hareworks-campaign@users.noreply.github.com' commit -m 'Measure real-rig Hareworks Walking_Woman reference parity v0.1.6' || fail 'commit failed'
  COMMIT=$(git rev-parse HEAD)
  [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'commit parent mismatch'
  phase=publish
  [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote advanced: no force-push or silent rebase'
  GIT_LFS_SKIP_PUSH=1 git push origin HEAD:refs/heads/main || fail "Git push failed; isolated local commit preserved $COMMIT"
else
  COMMIT="$REMOTE"
fi
phase=remote-readback
[[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$COMMIT" ]] || fail 'published main commit not confirmed'
GIT_LFS_SKIP_SMUDGE=1 git fetch --depth=1 origin main || fail 'remote readback fetch failed'
[[ "$(git rev-parse FETCH_HEAD)" == "$COMMIT" ]] || fail 'remote branch points to different commit'
for p in "${FILES[@]}";do
  [[ "$(git rev-parse "FETCH_HEAD:$p")" == "$(git rev-parse "HEAD:$p")" ]] || fail "remote new file differs from exact intended blob: $p"
done
for p in AGENTS.md "$MODEL" tools/hareworks-forward-woman/v0.1.5/viewer.mjs tools/hareworks-forward-woman/v0.1.5/upper-kernel.mjs tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs;do
  [[ "$(git rev-parse "FETCH_HEAD:$p")" == "$(git rev-parse "$BASE:$p")" ]] || fail "remote protected file changed: $p"
done
echo "EXACT_REMOTE_READBACK=PASS $COMMIT"
phase=viewer
# Never modify repository source GLB. Temporary checkout has only an LFS pointer;
# mounting verified bytes here affects this disposable HTTP snapshot alone.
cp -- "$SOURCE" "$MODEL" || fail 'source model HTTP snapshot copy failed'
[[ "$(hash "$MODEL")" == "$MODEL_SHA" ]] || fail 'HTTP source GLB snapshot hash mismatch'
cat > "$ROOT/server.py" <<'PY_SERVER'
import http.server,json,os,pathlib,sys
root,ready=sys.argv[1:]
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=root,**kw)
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
for i in 1 2 3 4 5 6 7 8 9 10;do
  if [[ -f "$READY" ]];then
    PORT=$(python3 - "$READY" <<'PY_PORT'
import json,sys
print(json.load(open(sys.argv[1]))['port'])
PY_PORT
)
  fi
  if [[ "$PORT" =~ ^[0-9]+$ ]] && curl -fsS --max-time 3 "http://127.0.0.1:$PORT/$DIR/index.html" >/dev/null 2>&1;then break;fi
  sleep 1
done
[[ "$PORT" =~ ^[0-9]+$ ]] && kill -0 "$PID" 2>/dev/null || fail 'local viewer HTTP server did not start'
python3 - "http://127.0.0.1:$PORT" "$DIR" "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" "$STATE/http-manifest.json" <<'PY_HTTP' || fail 'HTTP real browser required-resources check failed'
import hashlib,json,pathlib,re,sys,urllib.parse,urllib.request
origin,dir,model,sha,size,out=sys.argv[1:];size=int(size)
get=lambda url:urllib.request.urlopen(url,timeout=35).read()
root=origin+'/'+dir+'/'
viewer=get(root+'viewer.mjs').decode()
html=get(root+'index.html').decode()
assert 'id="parity"' in html and 'id="parityReport"' in html
assert 'src="./viewer.mjs"' in html
assert 'runParityAudit(false)' in viewer
urls=[root+'viewer.mjs',root+'index.html',root+'parity-math.mjs',root+'parity-math-test.mjs']
urls += [urllib.parse.urljoin(root+'viewer.mjs',m) for m in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",viewer)]
m=re.search(r"const paths=\['([^']+)','([^']+)'\];",viewer);assert m
profiles=[urllib.parse.urljoin(root+'viewer.mjs',u) for u in m.groups()]
for url in urls+profiles: assert get(url),('missing requested browser asset',url)
for url in profiles:
 p=json.loads(get(url));assert p['sourceSha256']==sha and p['clip']=='Walking_Woman'
blob=get(origin+'/'+model)
assert len(blob)==size and hashlib.sha256(blob).hexdigest()==sha
report={'status':'HTTP_ASSETS_VERIFIED_BROWSER_WEBGL_PENDING','requestedModules':urls,'requestedProfiles':profiles,'GLBSHA256':sha,'GLBBytes':len(blob)}
pathlib.Path(out).write_text(json.dumps(report,indent=2))
print('HTTP_EXACT_MODEL_AND_BROWSER_IMPORTS=PASS',len(urls+profiles),'HTTP resources')
PY_HTTP
curl -fsSI --max-time 5 "http://127.0.0.1:$PORT/$DIR/index.html" > "$STATE/http-headers.txt" || fail 'viewer headers unavailable'
URL="http://127.0.0.1:$PORT/$DIR/index.html?build=$COMMIT"
python3 - "$STATE/receipt.json" "$CAMPAIGN" "$BASE" "$COMMIT" "$SELF_SHA" "$MODEL_SHA" "$AGENTS_BLOB" "$URL" "$PID" "$PORT" "$ROOT" <<'PY_RECEIPT'
import datetime,json,pathlib,sys
path,campaign,parent,commit,entry,model,agents,url,pid,port,snapshot=sys.argv[1:]
r={'campaign':campaign,'state':'git_published_HTTP_verified_actual_browser_parity_pending','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
'auditedParentCommit':parent,'publishedCommit':commit,'entrypointSha256':entry,'sourceModelSha256':model,'sourceClip':'Walking_Woman','rootAgentsGitBlob':agents,
'rulesRead':{'agents':'live exact blob verified at authoring and on Termux','campaignEtiquette':'Home Center document 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI','topDownEtiquette':'Home Center document 1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'},
'unchangedPelvisLegUpperAlgorithms':True,'tests':'node parity accumulator plus previous gait kernels and HTTP resource check','viewerUrl':url,'viewerPid':int(pid),'viewerPort':int(port),'snapshot':snapshot,
'actualSkinnedBrowserParityCompleted':False,'ownerAccepted':False,'executionLane':'Android Termux Git only','requestedOutcome':'small-error match reference upper and lower body'}
pathlib.Path(path).write_text(json.dumps(r,indent=2))
PY_RECEIPT
echo "REMOTE_COMMIT=$COMMIT"
echo "VIEWER_URL=$URL"
echo "VIEWER_PORT=$PORT VIEWER_PID=$PID"
echo "MODEL_SHA256=$MODEL_SHA"
echo "SOURCE_CLIP=Walking_Woman"
echo "HTTP_MANIFEST=$STATE/http-manifest.json"
echo "RECEIPT=$STATE/receipt.json"
echo 'REAL_SKINNED_REFERENCE_PARITY=MEASURED_IN_BROWSER_ONLY; OWNER_ACCEPTANCE=PENDING'
if command -v termux-open-url >/dev/null;then
 termux-open-url "$URL" || echo "OPEN_REQUEST_FAILED; open VIEWER_URL=$URL"
else
 echo "TERMUX_OPEN_URL_UNAVAILABLE; open VIEWER_URL=$URL"
fi
