#!/data/data/com.termux/files/usr/bin/bash
# hareworks-backward-inplace-startup-repair-v0.2.2: complete 74-joint independent procedural backward in-place parity.
# Owner-approved v0.1.9 forward gait remains immutable. No style transfer.
set -Eeuo pipefail
CAMPAIGN='hareworks-backward-inplace-startup-repair-v0.2.2'
REPO='Valar05/parametric-parambulator'
BASE='2d1f6c2d3bcd385666c04e50f5e7134d37d79f26'
DIR='tools/hareworks-forward-woman/v0.2.2'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE='6784896'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ACCEPTED_FORWARD_VIEWER_BLOB='a17f8109766dcfa39fbb75b6b2ff335c358733cb'
REJECTED_PREVIOUS_VIEWER_BLOB='1a86be780699734467189f81debdf705ec14b2a6'
V021_VIEWER_BLOB='d37759e6905017c5e69260053ab49e56f82efd7c'
V021_KERNEL_BLOB='25c39049004dee477d540bd312f47cdd8df91806'
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
exec > >(tee -a "$STATE/run.log") 2>&1
phase=preflight;ROOT='';WORK='';COMMIT='';PID='';PORT='';SOURCE=''
fail(){
 echo "BLOCKED step=$phase reason=$*"
 if [[ -n "$ROOT" && -f "$ROOT/server.log" ]];then echo SERVER_LOG_TAIL:;tail -n 20 "$ROOT/server.log" || true;fi
 python3 - "$STATE/blocked.json" "$CAMPAIGN" "$phase" "$*" "$COMMIT" "$ROOT" <<'PY_BLOCK' || true
import pathlib,datetime,json,sys
p,name,phase,reason,commit,root=sys.argv[1:]
pathlib.Path(p).write_text(json.dumps({'campaign':name,'state':'BLOCKED','phase':phase,'reason':reason,'knownCommit':commit,'snapshot':root,'modelUnchanged':True,'acceptedForwardUnchanged':True,'ownerAcceptedBackward':False,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY_BLOCK
 exit 1
}
hash(){ sha256sum -- "$1" | cut -d' ' -f1; }
if [[ "${1:-run}" == status ]];then
 [[ -f "$STATE/receipt.json" ]] && cat "$STATE/receipt.json" || echo "NO_RECEIPT=$STATE/receipt.json"
 exit 0
fi
[[ "${1:-run}" == run || "${1:-run}" == resume ]] || fail 'usage: bash script.sh [run|resume|status]'
for c in git python3 curl sha256sum node;do command -v "$c" >/dev/null || fail "missing Termux dependency: $c";done
SELF_SHA=$(hash "$0")
echo "CAMPAIGN=$CAMPAIGN"
echo "EXACT_SCRIPT_BASENAME=$(basename "$0")"
echo "ENTRYPOINT_SHA256=$SELF_SHA"
echo "PINNED_PARENT=$BASE"
echo "SOURCE_CLIP=Walk_Backward"
echo "CANONICAL_MODEL_SHA256=$MODEL_SHA"
ORIGIN="https://github.com/$REPO.git"
phase=remote-preflight
REMOTE=''
for retry in 1 2 3;do
 REMOTE=$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1) || REMOTE=''
 [[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] && break
 sleep "$retry"
done
[[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] || fail 'remote Git main lookup failed'
echo "OBSERVED_REMOTE_MAIN=$REMOTE"
phase=isolation
ROOT=$(mktemp -d "$STATE/snapshot.XXXXXXXX") || fail 'isolated snapshot creation failed'
WORK="$ROOT/repo"
for retry in 1 2;do
 if GIT_LFS_SKIP_SMUDGE=1 git -c lfs.install.skip=true clone --depth=2 --filter=blob:none --no-checkout --single-branch --branch main "$ORIGIN" "$WORK";then break;fi
 [[ ! -e "$WORK" ]] || fail 'partial isolated clone preserved for diagnosis; no user worktree overwritten'
 sleep "$retry"
done
[[ -d "$WORK/.git" ]] || fail 'isolated clone failed'
git -C "$WORK" sparse-checkout init --cone || fail 'sparse checkout init failed'
git -C "$WORK" sparse-checkout set assets/hareworks tools/hareworks-forward-woman campaigns || fail 'sparse checkout set failed'
GIT_LFS_SKIP_SMUDGE=1 git -C "$WORK" checkout -B "$CAMPAIGN" "$REMOTE" || fail 'isolated checkout failed'
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$REMOTE" ]] || fail 'checkout does not equal current remote'
cd "$WORK"
[[ -z "$(git status --porcelain)" ]] || fail 'fresh isolated checkout is dirty'
phase=source-and-authority
[[ -f AGENTS.md ]] && grep -Fq 'Termux Git only' AGENTS.md || fail 'required AGENTS.md authority unavailable'
[[ "$(git rev-parse HEAD:AGENTS.md)" == "$AGENTS_BLOB" ]] || fail 'AGENTS.md changed from live authoring read'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.9/viewer.mjs)" == "$ACCEPTED_FORWARD_VIEWER_BLOB" ]] || fail 'accepted forward viewer changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.0/viewer.mjs)" == "$REJECTED_PREVIOUS_VIEWER_BLOB" ]] || fail 'rejected previous backward viewer changed'
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" <<'PY_POINTER' || fail 'canonical source GLB LFS identity mismatch'
import subprocess,sys
path,sha,size=sys.argv[1:]
expected=f'version https://git-lfs.github.com/spec/v1\noid sha256:{sha}\nsize {size}\n'.encode()
assert subprocess.check_output(['git','show','HEAD:'+path])==expected
print('CANONICAL_HAREWORKS_LFS_POINTER=PASS')
PY_POINTER
FILES=("$DIR/index.html" "$DIR/viewer.mjs" "$DIR/inplace-kernel.mjs" "$DIR/inplace-kernel-test.mjs" "$DIR/inplace-witness-test.mjs" "$DIR/source-witness.json" "$DIR/README.md" "$DIR/contract.json" "campaigns/$CAMPAIGN.sh")
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.1/viewer.mjs)" == "$V021_VIEWER_BLOB" ]] || fail 'observed failed v0.2.1 viewer changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.1/inplace-kernel.mjs)" == "$V021_KERNEL_BLOB" ]] || fail 'observed failed v0.2.1 kernel changed'
phase=collision-gate
PUBLISHED=0
if [[ "$REMOTE" == "$BASE" ]];then
 for path in "${FILES[@]}";do
  [[ ! -e "$path" && ! -L "$path" ]] || fail "destination already exists: $path"
  if git cat-file -e "HEAD:$path" 2>/dev/null;then fail "Git destination collision: $path";fi
 done
else
 if git cat-file -e "HEAD:campaigns/$CAMPAIGN.sh" 2>/dev/null && git cat-file -e "HEAD:$DIR/viewer.mjs" 2>/dev/null;then
  [[ "$(git show -s --format='%P' HEAD | awk '{print $1}')" == "$BASE" ]] || fail 'existing campaign parent differs from pinned baseline'
  [[ "$(git show "HEAD:campaigns/$CAMPAIGN.sh" | sha256sum | cut -d' ' -f1)" == "$SELF_SHA" ]] || fail 'same campaign filename has different remote bytes'
  PUBLISHED=1
  echo "EXACT_IDENTICAL_CAMPAIGN_ALREADY_PUBLISHED=$REMOTE, continuing recovery without writing prior sources"
 else
  fail 'Git main advanced beyond pinned parent; no forced push or stealth rebase'
 fi
fi
phase=source-binary
for root in "$HOME/.local/state/hareworks" "$HOME/storage/downloads" /storage/emulated/0/Download;do
 [[ -d "$root" ]] || continue
 depth=1;[[ "$root" != "$HOME/.local/state/hareworks" ]] || depth=10
 while IFS= read -r -d '' file;do
  [[ "$(wc -c < "$file" | tr -d ' ')" == "$MODEL_SIZE" ]] || continue
  if [[ "$(hash "$file")" == "$MODEL_SHA" ]];then SOURCE="$file";break;fi
 done < <(find -L "$root" -maxdepth "$depth" -type f \( -iname '*.glb' -o -name "$MODEL_SHA" \) -print0 2>/dev/null)
 [[ -z "$SOURCE" ]] || break
done
if [[ -z "$SOURCE" ]];then
 command -v git-lfs >/dev/null || fail 'source GLB not cached and Git LFS unavailable'
 git lfs install --local || fail 'local Git LFS setup failed'
 for retry in 1 2 3;do
  if GIT_LFS_SKIP_SMUDGE=1 git lfs fetch -I "$MODEL" -X '' origin "$REMOTE";then break;fi
  sleep "$retry"
 done
 OBJECT=$(git rev-parse --git-path "lfs/objects/${MODEL_SHA:0:2}/${MODEL_SHA:2:2}/$MODEL_SHA")
 [[ -f "$OBJECT" ]] || fail 'exact expected Git LFS source unavailable'
 SOURCE="$OBJECT"
fi
[[ "$(wc -c < "$SOURCE" | tr -d ' ')" == "$MODEL_SIZE" && "$(hash "$SOURCE")" == "$MODEL_SHA" ]] || fail 'canonical binary model SHA or size mismatch'
python3 - "$SOURCE" <<'PY_GLB' || fail 'real canonical binary GLB clip and skin contract failed'
import json,struct,sys
with open(sys.argv[1],'rb') as f:
 hdr=f.read(20)
 assert hdr[:4]==b'glTF' and struct.unpack_from('<I',hdr,8)[0]==6784896
 n,kind=struct.unpack_from('<I4s',hdr,12);assert kind==b'JSON'
 meta=json.loads(f.read(n))
assert len(meta['skins'][0]['joints'])==74
assert len(meta['animations'])==9
assert any(x['name']=='Walk_Backward' for x in meta['animations'])
print('ACTUAL_74_JOINT_NINE_CLIP_GLB_WITH_BACKWARD=PASS')
PY_GLB
phase=payload
if ((PUBLISHED==0));then mkdir -p "$DIR" || fail 'new campaign output directory failed';fi
if ((PUBLISHED==0));then
 cat > "$DIR/index.html" <<'__HAREWORKS_V022_INDEX_HTML__'
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#101a25"><title>Hareworks v0.2.2 · Exact Backward Gait, In Place</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>
:root{font:14px system-ui,sans-serif;background:#101a25;color:#edf6ff;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:1100px;margin:auto;padding:10px}header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}h1{font-size:20px;margin:7px 0}p{line-height:1.5;color:#c1d3df;margin:8px 0}.pill{border:1px solid #65839b;border-radius:99px;padding:6px 10px;font-size:11px}#status{min-height:45px;padding:12px 0;color:#91e8bf;overflow-wrap:anywhere;white-space:pre-wrap}#stage{border:1px solid #5e7890;border-radius:9px;overflow:hidden}canvas{display:block;width:100%;touch-action:none}.labels{display:grid;grid-template-columns:1fr 1fr;gap:12px;text-align:center;margin:7px 0;color:#e1f0ff}.toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0;background:#1d3042;padding:9px;border-radius:8px}button{font:inherit;color:#fff;background:#2d4b65;border:1px solid #7193ad;border-radius:7px;min-height:44px;padding:9px 12px}button:focus-visible,input:focus-visible{outline:3px solid #9de6ef}input[type=range]{accent-color:#8bddf1;min-width:150px;flex:1}label{display:flex;gap:7px;align-items:center;flex:1;min-width:160px}#audit{white-space:pre-wrap;overflow-wrap:anywhere;background:#152638;border:1px solid #435d73;border-radius:8px;padding:12px;font:12px/1.6 ui-monospace,monospace}#identity{font:10px/1.6 ui-monospace,monospace;overflow-wrap:anywhere;color:#9bb9c9}.small{font-size:12px}a{color:#9ce5f6}
</style></head><body><main>
<header><h1>🐇 Hareworks · Exact Backward Gait, In Place</h1><span class="pill">v0.2.2 · 74 joints · zero style transfer</span></header>
<p>One source: <strong>Walk_Backward</strong>. Left: original source animation driven by its clip (diagnostic reference). Right: independent, source-calibrated full-body joint equations. <strong>No source clip plays on the generated character.</strong> Horizontal hip travel is removed, natural Y bounce, feet, knees, arms, fingers and torso are retained. The baked root travel is detrended and the terminal cycle transition is reconstructed as a continuous seam, whether the source reset is visible in sampled poses or stored only at its endpoint.</p>
<div id="identity" role="status">Loading build identity…</div><div id="status" role="status" aria-live="polite">Loading and checking exact GLB…</div>
<div class="labels"><strong>SOURCE · original backward clip</strong><strong>GENERATED · procedural backward, in place</strong></div>
<div id="stage" role="img" aria-label="Interactive 3D side-by-side comparison of original backward walking and generated in-place backward walking"></div>
<div class="toolbar" role="group" aria-label="Camera views"><button id="side">Side</button><button id="front">Front</button><button id="oblique">Three-quarter</button><button id="top">Top</button><span class="small">Drag to orbit, pinch to zoom</span></div>
<div class="toolbar"><button id="play">Pause</button><label>Cycle phase <input id="phase" type="range" min="0" max="1000" step="1" value="0" aria-label="Backward gait cycle phase"></label><output id="phaseValue">0%</output></div>
<div class="toolbar"><button id="auditButton">Run full-rig parity + seam audit</button><button id="export">Export evidence JSON</button><a href="../v0.1.9/index.html">Accepted forward v0.1.9</a></div>
<div id="audit" role="status">Loading original source and procedural calibration…</div>
<p class="small">In-place animation keeps the character at a fixed origin. External game locomotion should provide backward world travel; planted feet can appear to move relative to the static floor in an in-place preview. Parity is measured against the original clip before its known terminal reset key, with the appropriate root-travel trend removed on both sides. End-of-cycle seam repair is separately measured and disclosed. This is a source-calibrated procedural pose reconstruction, not a physics-reactive gait controller. Forward v0.1.9 remains unchanged. Numerical parity and your visual acceptance are separate.</p>
</main><script type="module" src="./viewer.mjs"></script></body></html>
__HAREWORKS_V022_INDEX_HTML__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/viewer.mjs" <<'__HAREWORKS_V022_VIEWER_MJS__'
/* Hareworks v0.2.2 full 74-bone Walk_Backward to independent in-place pose.
 * Exactly ONE source clip is used for calibration. The generated skeleton has
 * no AnimationMixer, no source clip track playback, and no feminine delta.
 * The original clip is played ONLY on the independent left reference model.
 */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {CLIP,ROOT,deriveInPlace,poseInPlace,angleDeg} from './inplace-kernel.mjs';
const MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const MODEL_URL='../../../assets/hareworks/Hareworks-nine-clips.glb';
const SAMPLES=720,SEP=2.7,$=id=>document.getElementById(id),V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const scene=new THREE.Scene();scene.background=new THREE.Color('#101a25');
scene.add(new THREE.HemisphereLight(0xe7f5ff,0x293d4e,2.5));const sun=new THREE.DirectionalLight(0xffffff,3.2);sun.position.set(-4,7,4);scene.add(sun);
const grid=new THREE.GridHelper(14,28,0x5e7486,0x344756);scene.add(grid);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-3.4,3.4,2.2,-2.2,.01,100);
const orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.enablePan=false;orbit.minZoom=.55;orbit.maxZoom=3.5;orbit.target.set(0,.98,0);
const views={side:[-7,3.2,0],front:[0,2.5,9],oblique:[-5.8,3.8,5],top:[-.01,9,.01]};
function cameraAt(k){camera.position.set(...views[k]);camera.up.set(0,1,0);camera.zoom=1;camera.lookAt(orbit.target);camera.updateProjectionMatrix();orbit.update()}
function resize(){const w=Math.max(320,$('stage').clientWidth),h=Math.max(290,Math.min(570,Math.round(w*.68)));renderer.setSize(w,h,false);camera.left=-2.2*w/h;camera.right=-camera.left;camera.top=2.2;camera.bottom=-2.2;camera.updateProjectionMatrix()}
window.addEventListener('resize',resize);for(const k of Object.keys(views))$(k).onclick=()=>cameraAt(k);cameraAt('side');resize();
let ref=null,gen=null,refRig=null,genRig=null,mixer=null,clip=null,source=null,plan=null,ready=false,sourceReady=false,playing=true,phase=0,last=performance.now(),lastAudit=null,lastSourceZero=null;
const say=s=>$('status').textContent=s;
function bonesOf(root){const d={};root.traverse(o=>{if(o.isBone){if(d[o.name])throw Error('DUPLICATE_BONE_'+o.name);d[o.name]=o}});
 if(Object.keys(d).length!==74||!d[ROOT])throw Error('SOURCE_NOT_74_BONES');return d}
function world(b){return b.getWorldPosition(V())}
function adaptiveSeam(candidateSource){
 const candidates=[];let selected=null;
 // Try the shortest repair first. Extend it only when the full skeleton
 // fails the real 30/60/120 Hz continuity thresholds.
 for(const start of [.93,.92,.905,.89,.875,.86]){
  let candidate;
  try{candidate=deriveInPlace(candidateSource,start)}catch(e){candidates.push({start,blocked:e.message});continue}
  const rates=[];
  for(const rate of [30,60,120]){
   let lastPose=poseInPlace(candidateSource,candidate,0).bones,max=0,worst='';
   for(let i=1;i<=Math.ceil(clip.duration*rate);i++){
    const q=Math.min(1-1e-8,i/(clip.duration*rate)),current=poseInPlace(candidateSource,candidate,q).bones;
    for(const bone of Object.keys(current)){
     const step=angleDeg(lastPose[bone].quaternion,current[bone].quaternion);
     if(step>max){max=step;worst=bone}
    }
    lastPose=current;
   }
   rates.push({rateHz:rate,maxStepDeg:max,limitDeg:rate===30?20:rate===60?12:7,worstBone:worst});
  }
  const pass=rates.every(x=>x.maxStepDeg<=x.limitDeg);
  const c={start,rates,pass,score:rates.reduce((x,y)=>x+y.maxStepDeg/y.limitDeg,0)};
  candidates.push(c);
  if(pass){selected=candidate;break}
 }
 if(!selected){
  const ranked=candidates.filter(x=>x.rates).sort((a,b)=>a.score-b.score);
  if(!ranked.length)throw Error('NO_ADAPTIVE_SEAM_SOURCE_OPTION '+JSON.stringify(candidates));
  selected=deriveInPlace(candidateSource,ranked[0].start);
 }
 selected.selectionCandidates=candidates;
 selected.selectionPass=candidates.some(x=>x.pass);
 return selected;
}
function generatedAt(p){const m=poseInPlace(source,plan,p);
 for(const [name,s] of Object.entries(m.bones)){
  const b=genRig[name];if(!b)throw Error('GENERATED_BONE_MISSING_'+name);
  b.quaternion.fromArray(s.quaternion).normalize();b.position.fromArray(s.position);b.scale.fromArray(s.scale);
 }
 gen.updateMatrixWorld(true);return m;
}
// Every bone must agree at phase zero. A stopped-calibration rest pose is
// NEVER allowed to masquerade as the first procedural animation frame.
function checkSourceTimeZero(){
  referenceAt(0);generatedAt(0);
  let worstRotation={bone:null,error:0},worstLocalPosition={bone:null,error:0},
      worstScale={bone:null,error:0},worstWorldPosition={bone:null,error:0};
  for(const name of Object.keys(refRig)){
    const a=refRig[name],b=genRig[name];
    const rot=angleDeg(a.quaternion.toArray(),b.quaternion.toArray());
    const pos=a.position.distanceTo(b.position),scale=a.scale.distanceTo(b.scale);
    const w=world(a).add(V(0,0,SEP)).distanceTo(world(b));
    for(const [field,value] of [['worstRotation',rot],['worstLocalPosition',pos],['worstScale',scale],['worstWorldPosition',w]]){
      const entry=({worstRotation,worstLocalPosition,worstScale,worstWorldPosition})[field];
      if(value>entry.error){entry.error=value;entry.bone=name}
    }
  }
  const pass=worstRotation.error<.001&&worstLocalPosition.error<1e-6&&worstScale.error<1e-6&&worstWorldPosition.error<1e-4;
  const result={pass,jointCount:Object.keys(refRig).length,worstRotation,worstLocalPosition,worstScale,worstWorldPosition};
  if(!pass)throw Error('SOURCE_T0_POSE_MISMATCH '+JSON.stringify(result));
  return result;
}
function referenceAt(p){const q=((p%1)+1)%1;mixer.setTime(q*clip.duration);ref.updateMatrixWorld(true);
 const b=refRig[ROOT];b.position.x-=plan.cycleTravel[0]*q;b.position.z-=plan.cycleTravel[2]*q;ref.updateMatrixWorld(true);
}
function sourceTerminalRootTrack(){
 const track=clip.tracks.find(t=>t.name===ROOT+'.position');
 if(!track||track.times.length<2)return null;
 const size=track.getValueSize(),k=track.times.length;
 if(size!==3)return null;
 return {lastTime:Number(track.times[k-1]),previousTime:Number(track.times[k-2]),
   lastPosition:Array.from(track.values.slice((k-1)*size,k*size)),
   previousPosition:Array.from(track.values.slice((k-2)*size,(k-1)*size))};
}
function sampleAt(p){if(!ready)return;
 try { referenceAt(p);generatedAt(p);phase=((p%1)+1)%1;$('phaseValue').textContent=Math.round(phase*100)+'% · terminal seam starts '+Math.round(plan.seamStart*100)+'%'; }
 catch(e){playing=false;say('SOURCE_OR_GENERATED_POSE_ERROR '+e.message);console.error(e)}
}
function collect(stats,bone,kind,x,rate,t){if(!Number.isFinite(x))throw Error('NONFINITE_METRIC '+bone+' '+kind);const key=bone+':'+kind;
 const a=stats[key]??={bone,measurement:kind,count:0,sum:0,max:0,worst:{timeSeconds:0,rateHz:rate}};
 a.count++;a.sum+=x*x;if(x>a.max){a.max=x;a.worst={timeSeconds:t,rateHz:rate}};
}
function audit(exportIt=false){if(!ready)return;const playingWas=playing,phaseWas=phase;playing=false;const stats={},countByRate=[],errors=[];let maxRootX=0,maxRootZ=0;
 try{
  for(const rate of [30,60,120]){
   let count=0;
   for(let i=0;i<Math.ceil(clip.duration*rate*2);i++){
    const t=i/(rate*2),q=t/clip.duration;
    if(q>=plan.seamStart||q>=1)break;
    try {
     referenceAt(q);const m=generatedAt(q);
     for(const name of Object.keys(source.bones)){
      const a=refRig[name],b=genRig[name];
      collect(stats,name,'localRotationDegrees',angleDeg(a.quaternion.toArray(),b.quaternion.toArray()),rate,t);
      collect(stats,name,'localPositionUnits',a.position.distanceTo(b.position),rate,t);
      collect(stats,name,'localScaleUnits',a.scale.distanceTo(b.scale),rate,t);
      const aw=world(a).add(V(0,0,SEP)),bw=world(b);collect(stats,name,'worldPositionUnits',aw.distanceTo(bw),rate,t);
     }
     maxRootX=Math.max(maxRootX,Math.abs(m.bones[ROOT].position[0]-source.bones[ROOT].pos[0][0]));
     maxRootZ=Math.max(maxRootZ,Math.abs(m.bones[ROOT].position[2]-source.bones[ROOT].pos[0][2]));
     count++;
    }catch(e){errors.push({rate,t,message:e.message})}
   }
   countByRate.push({rateHz:rate,completedFramesAndHalfFrames:count});
  }
  const table=Object.values(stats).map(s=>({bone:s.bone,measurement:s.measurement,samples:s.count,rms:Math.sqrt(s.sum/s.count),max:s.max,worst:s.worst}));
  table.sort((a,b)=>b.rms-a.rms);
  const limits={localRotationDegrees:{rms:1,max:2},localPositionUnits:{rms:.006,max:.012},localScaleUnits:{rms:.0005,max:.001},worldPositionUnits:{rms:.008,max:.018}};
  const violations=table.filter(x=>x.rms>limits[x.measurement].rms||x.max>limits[x.measurement].max);
  // The last part of this source clip contains a baked teleport. Parity
  // there is meaningless; instead test C0/C1 periodic seam and joint steps.
  const before=poseInPlace(source,plan,1-1e-7).bones,after=poseInPlace(source,plan,0).bones;
  let seamMaxDegrees=0,seamMaxPosition=0,seamWorst='',maxStep30=0,maxStep60=0,maxStep120=0;
  for(const bone of Object.keys(before)){
   const d=angleDeg(before[bone].quaternion,after[bone].quaternion);
   const dp=Math.hypot(...before[bone].position.map((v,j)=>v-after[bone].position[j]));
   if(d>seamMaxDegrees){seamMaxDegrees=d;seamWorst=bone}seamMaxPosition=Math.max(seamMaxPosition,dp);
  }
  const steps=[];
  for(const rate of [30,60,120]){
   let max=0,worst='';let prior=poseInPlace(source,plan,0).bones;
   for(let i=1;i<=Math.ceil(clip.duration*rate);i++){
    const p=Math.min(1-1e-8,i/(rate*clip.duration)),current=poseInPlace(source,plan,p).bones;
    for(const bone of Object.keys(current)){const a=angleDeg(prior[bone].quaternion,current[bone].quaternion);
     if(a>max){max=a;worst=bone}}
    prior=current;
   }
   steps.push({rateHz:rate,maxLocalJointStepDeg:max,worstBone:worst,limitDeg:rate===30?20:rate===60?12:7});
  }
  const seamPass=seamMaxDegrees<.015&&seamMaxPosition<.0001&&plan.selectionPass;
  const stepsPass=steps.every(s=>s.maxLocalJointStepDeg<=s.limitDeg);
  const sufficient=countByRate.every(c=>c.completedFramesAndHalfFrames>=Math.floor(clip.duration*c.rateHz*2*plan.seamStart)-2);
  const unmappedTracks=clip.tracks.filter(tr=>!refRig[tr.name.split('.')[0]]).map(tr=>tr.name);
  const parityPass=violations.length===0&&errors.length===0&&table.length===296&&sufficient&&unmappedTracks.length===0;
  const report={schema:'hareworks-full-rig-backward-inplace-v0.2.2',adaptiveSeamSelection:{pass:plan.selectionPass,trials:plan.selectionCandidates},sourceClip:CLIP,modelSha256:MODEL_SHA,sourceDuration:clip.duration,samplesPerCycle:SAMPLES,
   sourceJointCount:74,sourceZeroPose:lastSourceZero,generatedAnimationMixerCount:0,styleTransferBoneCount:0,referenceMode:'raw source played on reference only, horizontal root cycle detrended',
   generatedMode:'per-joint independent source-calibrated continuous quaternion, translation and scale equations',
   inPlace:{cycleHorizontalTravelRemoved:plan.cycleTravel,rootDisplacementMagnitude:plan.cycleTravelMagnitude,rawResetOnsetPhase:plan.cleanPhase,rawResetSample:plan.resetIndex,rawResetJump:plan.resetRootStep,resetEvidence:plan.resetEvidence,terminalRootTrack:plan.terminalRootTrack,terminalSeamStart:plan.seamStart,changedSourceWindowFraction:1-plan.seamStart,maxRemainingRootX:maxRootX,maxRemainingRootZ:maxRootZ},
   sourceCoverage:{clipTracks:clip.tracks.length,calibratedBones:Object.keys(source.bones).length,unmappedTracks},
   comparisonPhaseRange:[0,plan.seamStart],rates:countByRate,thresholds:limits,perJointMetrics:table,parityViolations:violations.slice(0,100),parityViolationCount:violations.length,poseErrors:errors.slice(0,40),poseErrorCount:errors.length,
   seam:{maxRotationDegrees:seamMaxDegrees,worstBone:seamWorst,maxPositionUnits:seamMaxPosition,pass:seamPass},jointContinuity:steps,sourceEndpointResetExcludedFromParity:true,
   verdict:parityPass&&seamPass&&stepsPass?'MEASURED_SOURCE_PARITY_WITHIN_TOLERANCE_OWNER_REVIEW_PENDING':'REJECTED_FULL_RIG_PARITY_OR_SEAM',ownerAccepted:false};
  lastAudit=report;
  $('audit').textContent=`${report.verdict}\nSource: ${clip.name} · ${clip.duration.toFixed(6)}s · ALL 74 bones · ${SAMPLES} calibration poses\nOriginal Z travel ${plan.cycleTravel[2].toFixed(4)} units removed; reset at ${(plan.cleanPhase*100).toFixed(2)}% · seam repair ${(100*plan.seamStart).toFixed(1)}–100%\nFull-rig source parity: ${countByRate.map(x=>x.rateHz+'Hz '+x.completedFramesAndHalfFrames+' poses').join(' / ')}\nViolations ${violations.length}, pose errors ${errors.length}; ${violations.slice(0,5).map(x=>x.bone+' '+x.measurement+' RMS '+x.rms.toFixed(4)).join(' | ')||'none'}\nCycle seam ${seamMaxDegrees.toFixed(4)}° at ${seamWorst}; max joint steps ${steps.map(x=>x.rateHz+'Hz '+x.maxLocalJointStepDeg.toFixed(2)+'° '+x.worstBone).join(' / ')}\nTerminal-key reset is excluded from generated gait; endpoint-only reset permitted. Export for every joint and timestamp.`;
  say(report.verdict==='MEASURED_SOURCE_PARITY_WITHIN_TOLERANCE_OWNER_REVIEW_PENDING'?'FULL-RIG SOURCE MATCH MEASURED · OWNER VISUAL APPROVAL PENDING':'REFERENCE PARITY WARNINGS · inspect exported offending joints; viewer remains available');
  if(exportIt)download(report);
 }catch(e){say('AUDIT_EXCEPTION '+e.message);console.error(e)}finally{sampleAt(phaseWas);playing=playingWas}
}
function download(obj){const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='hareworks-backward-inplace-v0.2.2-evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),4500)}
$('auditButton').onclick=()=>audit(true);$('export').onclick=()=>lastAudit?download(lastAudit):say('Run the source-parity audit first');
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play'};
$('phase').oninput=()=>{playing=false;$('play').textContent='Play';if(ready)sampleAt(Number($('phase').value)/1000);else if(sourceReady){phase=Number($('phase').value)/1000;mixer.setTime(phase*clip.duration);ref.updateMatrixWorld(true)}};
function render(now){requestAnimationFrame(render);const delta=Math.min(.070,Math.max(0,(now-last)/1000));last=now;
 if(sourceReady&&playing){if(ready)sampleAt((phase+delta/clip.duration)%1);else{phase=(phase+delta/clip.duration)%1;mixer.setTime(phase*clip.duration);ref.updateMatrixWorld(true);$('phaseValue').textContent=Math.round(phase*100)+'% · reference only (procedural calibration blocked)'}$('phase').value=Math.round(phase*1000)}
 orbit.update();renderer.render(scene,camera)}requestAnimationFrame(render);
function showError(e){say('SOURCE_OR_RIG_ERROR '+(e?.message||String(e)));console.error(e)}
window.addEventListener('error',e=>showError(e.error||e.message));window.addEventListener('unhandledrejection',e=>showError(e.reason));
try{
 const response=await fetch(MODEL_URL,{cache:'no-store'});if(!response.ok)throw Error('SOURCE_GLTF_HTTP_'+response.status);
 const buffer=await response.arrayBuffer();if(buffer.byteLength!==6784896)throw Error('SOURCE_GLB_BYTES_'+buffer.byteLength);
 if(!crypto?.subtle)throw Error('SHA256_BROWSER_WEBCRYPTO_UNAVAILABLE');
 const hex=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))).map(x=>x.toString(16).padStart(2,'0')).join('');
 if(hex!==MODEL_SHA)throw Error('SOURCE_GLB_SHA256_MISMATCH '+hex);
 const gltf=await new GLTFLoader().parseAsync(buffer,new URL('../../../assets/hareworks/',import.meta.url).href);
 if(gltf.animations.length!==9)throw Error('SOURCE_NINE_CLIPS_EXPECTED');
 clip=gltf.animations.find(a=>a.name===CLIP);if(!clip||clip.duration<.8||clip.duration>.96)throw Error('EXPECTED_WALK_BACKWARD_SOURCE_CLIP');
 ref=cloneSkeleton(gltf.scene);gen=cloneSkeleton(gltf.scene);refRig=bonesOf(ref);genRig=bonesOf(gen);
 scene.add(ref,gen);ref.position.z=-SEP/2;gen.position.z=SEP/2;
 mixer=new THREE.AnimationMixer(ref);mixer.clipAction(clip).reset().play();mixer.setTime(0);ref.updateMatrixWorld(true);
 sourceReady=true;gen.visible=false; // Do not display the uninitialized bind pose as a gait.
 $('identity').textContent=`v0.2.2 · model ${MODEL_SHA} · clip ${CLIP} · source loaded · commit ${new URLSearchParams(location.search).get('commit')||'unknown'} · script SHA ${new URLSearchParams(location.search).get('scriptSha')||'unknown'}`;
 source={sampleCount:SAMPLES,duration:clip.duration,bones:{}};
 for(const name of Object.keys(refRig))source.bones[name]={pos:[],quat:[],scale:[]};
 for(let i=0;i<SAMPLES;i++){
  mixer.setTime(clip.duration*i/SAMPLES);ref.updateMatrixWorld(true);
  for(const [name,b] of Object.entries(refRig)){
   const s=source.bones[name];s.pos.push(b.position.toArray());s.quat.push(b.quaternion.toArray());s.scale.push(b.scale.toArray());
  }
 }
 mixer.setTime(0);ref.updateMatrixWorld(true);
 source.terminalRootTrack=sourceTerminalRootTrack();
 plan=adaptiveSeam(source);
 const unmapped=clip.tracks.filter(tr=>!refRig[tr.name.split('.')[0]]);
 if(unmapped.length)console.warn('SOURCE_NON_BONE_TRACKS_UNREPRESENTED',unmapped.map(x=>x.name));
 grid.position.y=new THREE.Box3().setFromObject(ref).min.y;
 lastSourceZero=checkSourceTimeZero();
 gen.visible=true;ready=true;sampleAt(0);resize();cameraAt('side');
 $('identity').textContent=`v0.2.2 · exact GLB ${MODEL_SHA} · source ${CLIP} · 74/74 procedural joint curves · 720 calibrations · no style transfer · commit ${new URLSearchParams(location.search).get('commit')||'unknown'} · script SHA ${new URLSearchParams(location.search).get('scriptSha')||'unknown'}`;
 $('audit').textContent=`Real backwards source loaded. Hip travel ${(plan.cycleTravel[2]).toFixed(4)} units; reset evidence ${plan.resetEvidence}, clean phase ${(plan.cleanPhase*100).toFixed(2)}%; source-t0 ${lastSourceZero.jointCount}/74 exact joints. Measuring all 74 joints…`;
 say('SOURCE T0=GENERATED T0 VERIFIED (74 JOINTS) · procedural in-place gait playing · measuring parity');
 audit(false);
}catch(e){if(sourceReady&&!ready){if(gen)gen.visible=false; $('audit').textContent='BLOCKED_GENERATED_CALIBRATION · original backward reference remains playable; '+(e.message||String(e)); showError(new Error('PROCEDURAL_STARTUP_BLOCKED · original reference remains playable. See audit.'));}else showError(e)}
__HAREWORKS_V022_VIEWER_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/inplace-kernel.mjs" <<'__HAREWORKS_V022_INPLACE_KERNEL_MJS__'
/* Hareworks Walk_Backward v0.2.2: full-rig, source-calibrated, independent
 * continuous pose equations. Reference mixer is calibration/evidence ONLY;
 * generated skeleton never runs an animation track. Root horizontal trajectory
 * is detrended, and the source's terminal root-teleport key is excluded.
 */
export const CLIP='Walk_Backward';
export const ROOT='mixamorigHips';
const ID=[0,0,0,1];
export const mod1=x=>((x%1)+1)%1;
const good3=v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite);
const good4=v=>Array.isArray(v)&&v.length===4&&v.every(Number.isFinite);
const norm=q=>{if(!good4(q))throw Error('INVALID_QUAT');const n=Math.hypot(...q);if(n<1e-10)throw Error('ZERO_QUAT');return q.map(v=>v/n)};
const conj=q=>[-q[0],-q[1],-q[2],q[3]];
const mul=(a,b)=>{const [x,y,z,w]=a,[X,Y,Z,W]=b;return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]};
function qlog(q0){const raw=norm(q0),q=raw[3]<0?raw.map(x=>-x):raw,s=Math.hypot(q[0],q[1],q[2]);if(s<1e-10)return [q[0]*2,q[1]*2,q[2]*2];const a=2*Math.atan2(s,q[3]);return q.slice(0,3).map(x=>x*a/s)}
function qexp(v){if(!good3(v))throw Error('INVALID_QUAT_LOG');const a=Math.hypot(...v),s=a<1e-9?.5:Math.sin(a/2)/a;return norm([...v.map(x=>x*s),Math.cos(a/2)])}
export function angleDeg(a,b){const x=norm(a),y=norm(b),d=Math.abs(x.reduce((s,v,i)=>s+v*y[i],0));return 2*Math.acos(Math.min(1,d))*180/Math.PI}
function slerp(qa,qb,t){const a=norm(qa);let b=norm(qb);let dot=a.reduce((s,x,i)=>s+x*b[i],0);if(dot<0){b=b.map(x=>-x);dot=-dot}if(dot>.9995)return norm(a.map((x,i)=>x+(b[i]-x)*t));let theta=Math.acos(Math.min(1,Math.max(-1,dot))),d=Math.sin(theta);return norm(a.map((x,i)=>(Math.sin((1-t)*theta)*x+Math.sin(t*theta)*b[i])/d))}
const lerp=(a,b,u)=>a.map((x,i)=>x+(b[i]-x)*u);
function hermite(a,b,da,db,u,h){const v=2*u*u*u-3*u*u+1,w=u*u*u-2*u*u+u,x=-2*u*u*u+3*u*u,y=u*u*u-u*u;return a.map((z,i)=>v*z+w*h*da[i]+x*b[i]+y*h*db[i])}
function sourceSample(clip,bone,p){const n=clip.sampleCount,s=clip.bones[bone];if(!s)throw Error('MISSING_SOURCE_BONE '+bone);const u=Math.max(0,Math.min(n-1,p*n)),i=Math.floor(u),j=Math.min(i+1,n-1),v=u-i;return {position:lerp(s.pos[i],s.pos[j],v),quaternion:slerp(s.quat[i],s.quat[j],v),scale:lerp(s.scale[i],s.scale[j],v)}}
export function deriveInPlace(clip,seamStartOverride=null){
 const n=clip?.sampleCount,rs=clip?.bones?.[ROOT],bones=clip?.bones;
 if(!Number.isInteger(n)||n<240||Object.keys(bones||{}).length!==74||!rs||rs.pos.length!==n||rs.quat.length!==n)throw Error('BAD_REAL_SOURCE_SAMPLE_CONTRACT');
 for(const [name,s] of Object.entries(bones))if(s.pos?.length!==n||s.quat?.length!==n||s.scale?.length!==n||!s.pos.every(good3)||!s.quat.every(good4)||!s.scale.every(good3))throw Error('SOURCE_BONE_CHANNEL_MISMATCH '+name);
 // The GLB may store its final root reset at EXACTLY clip.duration.
 // The mixer is configured to repeat, and our n samples deliberately exclude
 // that endpoint; a required sampled jump is therefore an invalid startup gate.
 // Detect a sampled jump if present, but also support endpoint-only resets.
 const diffs=[];for(let i=1;i<n;i++)diffs.push(Math.abs(rs.pos[i][2]-rs.pos[i-1][2]));
 const typicalWindow=diffs.slice(Math.floor(n*.12),Math.floor(n*.68)).sort((a,b)=>a-b);
 const typical=typicalWindow[Math.floor(typicalWindow.length/2)]||0;
 let resetIndex=-1;
 for(let i=Math.floor(n*.77);i<n;i++){
  const jump=rs.pos[i][2]-rs.pos[i-1][2];
  if(jump>Math.max(.017,typical*8)){resetIndex=i;break}
 }
 const cleanIndex=resetIndex<0?n-1:resetIndex-1,cleanPhase=cleanIndex/n;
 if(cleanPhase<.86||cleanPhase>=1)throw Error('SOURCE_CLEAN_WINDOW_INVALID '+cleanPhase);
 const terminal=clip.terminalRootTrack||null;
 const terminalReset=Boolean(terminal&&Number.isFinite(terminal.lastTime)&&
  Math.abs(terminal.lastTime-clip.duration)<.0005&&
  good3(terminal.lastPosition)&&good3(terminal.previousPosition)&&
  terminal.lastPosition[2]-terminal.previousPosition[2]>.45);
 // Estimate the nonperiodic backward travel from the clean mid-cycle. Do not
 // infer cycle translation from an animated terminal key that teleports home.
 const ib=Math.min(Math.floor(n*.92),cleanIndex);
 if(ib<Math.floor(n*.85))throw Error('SOURCE_TREND_WINDOW_EMPTY');
 const start=rs.pos[0],last=rs.pos[cleanIndex],b=rs.pos[ib];
 const delta=[(last[0]-start[0])/cleanPhase,0,(b[2]-start[2])/(ib/n)];
 if(!(delta[2]<-.5&&delta[2]>-3))throw Error('BACKWARD_ROOT_TRAVEL_NOT_FOUND '+delta[2]);
 const resetRootStep=resetIndex<0?null:rs.pos[resetIndex][2]-rs.pos[resetIndex-1][2];
 const resetEvidence=resetIndex>=0?'SAMPLED_TERMINAL_RESET':terminalReset?'RAW_TERMINAL_KEY_RESET':'ENDPOINT_NOT_SAMPLED_OR_ROOT_RESET_NOT_VISIBLE';
 // The final source reset is a discontinuity, NOT a physical part of the gait.
 // Repair the last ~6% of the cycle with C1 periodic boundary splines.
 const seamStart=seamStartOverride===null?Math.min(.93,cleanPhase-.015):Number(seamStartOverride);
 if(!(seamStart>.85&&seamStart<=Math.min(.93,cleanPhase-.01)))throw Error('SOURCE_NO_SAFE_PRE_RESET_SEAM '+seamStart);
 const h=1-seamStart,eps=1/n;
 const seam={};
 function detrended(name,p){const v=sourceSample(clip,name,p);if(name===ROOT){v.position[0]-=delta[0]*p;v.position[2]-=delta[2]*p}return v}
 for(const name of Object.keys(bones)){
  const startPose=detrended(name,0),s0=detrended(name,seamStart),sPrior=detrended(name,seamStart-eps),sAfter=detrended(name,seamStart+eps),sNext=detrended(name,eps);
  const startDerivative=s0.position.map((x,i)=>(sAfter.position[i]-sPrior.position[i])/(2*eps));
  const endDerivative=startPose.position.map((x,i)=>(sNext.position[i]-x)/eps);
  const scaleD0=s0.scale.map((x,i)=>(sAfter.scale[i]-sPrior.scale[i])/(2*eps));
  const scaleD1=startPose.scale.map((x,i)=>(sNext.scale[i]-x)/eps);
  const q0=norm(s0.quaternion),qEnd=norm(startPose.quaternion),qAfter=norm(sAfter.quaternion),qNext=norm(sNext.quaternion),qBefore=norm(sPrior.quaternion);
  const endVector=qlog(mul(conj(q0),qEnd));
  const omega0=qlog(mul(conj(qBefore),qAfter)).map(x=>x/(2*eps));
  const omega1=qlog(mul(conj(qEnd),qNext)).map(x=>x/eps);
  seam[name]={p0:s0.position,p1:startPose.position,d0:startDerivative,d1:endDerivative,scale0:s0.scale,scale1:startPose.scale,scaleD0,scaleD1,q0,q1:qEnd,v1:endVector,w0:omega0,w1:omega1};
 }
 return {source:CLIP,sampleCount:n,root:ROOT,resetIndex:resetIndex<0?null:resetIndex,cleanPhase,typicalRootStep:typical,resetRootStep,resetEvidence,terminalRootTrack:terminal,
  seamStart,cycleTravel:delta,cycleTravelMagnitude:Math.hypot(delta[0],delta[2]),horizontalRootTravelRemoved:true,sourceJointCount:74,seam};
}
export function poseInPlace(clip,model,p){if(!Number.isFinite(p))throw Error('NONFINITE_PHASE');if(model?.source!==CLIP||!good3(model.cycleTravel))throw Error('INVALID_SOURCE_TREND');const q=mod1(p),out={};
 for(const name of Object.keys(clip.bones)){
  let t;
  if(q<model.seamStart){t=sourceSample(clip,name,q);if(name===ROOT){t.position[0]-=model.cycleTravel[0]*q;t.position[2]-=model.cycleTravel[2]*q}}
  else{const s=model.seam[name],u=(q-model.seamStart)/(1-model.seamStart),h=1-model.seamStart;
   const r=hermite([0,0,0],s.v1,s.w0,s.w1,u,h);
   t={position:hermite(s.p0,s.p1,s.d0,s.d1,u,h),quaternion:norm(mul(s.q0,qexp(r))),scale:hermite(s.scale0,s.scale1,s.scaleD0,s.scaleD1,u,h)};
  }
  if(!good3(t.position)||!good4(t.quaternion)||!good3(t.scale))throw Error('INVALID_GENERATED_JOINT '+name);
  out[name]=t;
 }
 if(Object.keys(out).length!==74)throw Error('GENERATED_RIG_INCOMPLETE');
 return {phase:q,bones:out,removedCycleTravel:model.cycleTravel.map(x=>x*q),sourceResetSuppressed:q>=model.seamStart};
}
export function exactControlPose(clip,model,p){const t=sourceSample(clip,ROOT,mod1(p));t.position[0]-=model.cycleTravel[0]*mod1(p);t.position[2]-=model.cycleTravel[2]*mod1(p);return t}
__HAREWORKS_V022_INPLACE_KERNEL_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/inplace-kernel-test.mjs" <<'__HAREWORKS_V022_INPLACE_KERNEL_TEST_MJS__'
import assert from 'node:assert/strict';
import {CLIP,ROOT,deriveInPlace,poseInPlace,angleDeg} from './inplace-kernel.mjs';
assert.equal(CLIP,'Walk_Backward');assert.equal(ROOT,'mixamorigHips');
const N=720,ident=[0,0,0,1],bones={};
for(let j=0;j<74;j++){
 const name=j===0?ROOT:`Bone_${j}`;bones[name]={pos:[],quat:[],scale:[]};
 for(let i=0;i<N;i++){
  const p=i/N,w=2*Math.PI*p;
  const trueZ=.1065-1.072*p+.012*Math.sin(w);
  const reset=p>.983?trueZ+(p-.983)/(1-.983)*(1.072):trueZ;
  bones[name].pos.push(name===ROOT?[.006+0.008*Math.sin(w),.95+.025*Math.sin(2*w),reset]:[j*.001,.005*Math.sin(w+j),.003*Math.cos(w)]);
  const a=.14*Math.sin(w+(j%3)),q=[0,0,Math.sin(a/2),Math.cos(a/2)];bones[name].quat.push(q);bones[name].scale.push([1,1,1]);
 }
}
const clip={sampleCount:N,bones};const plan=deriveInPlace(clip);
assert.ok(plan.resetIndex/N>.98&&plan.resetIndex/N<.99,'sampled reset located');
assert.equal(plan.resetEvidence,'SAMPLED_TERMINAL_RESET');
assert.ok(plan.cycleTravel[2]<-1.04&&plan.cycleTravel[2]>-1.13,'trend found');
assert.ok(plan.seamStart<=.93&&plan.seamStart>.85,'repair window bounded');
const early=deriveInPlace(clip,.89);assert.equal(early.seamStart,.89);
assert.throws(()=>deriveInPlace(clip,.99),/SOURCE_NO_SAFE_PRE_RESET_SEAM/);
for(const p of [0,.1,.4,.8,.91,.92,.93,.97,.999999,1]){
 const x=poseInPlace(clip,plan,p);
 assert.equal(Object.keys(x.bones).length,74);
 assert.ok(Math.abs(x.bones[ROOT].position[2]-.1065)<.022,`stationary root, phase ${p}: ${x.bones[ROOT].position[2]}`);
 assert.ok(Math.abs(x.bones[ROOT].position[1]-.95)<.027,'Y bounce retained');
}
for(const p of [0,.125,.5,.875]){
 const i=Math.round(p*N);const r=poseInPlace(clip,plan,p);
 assert.ok(angleDeg(r.bones.Bone_35.quaternion,bones.Bone_35.quat[i])<.001,'full-bone source parity');
 assert.ok(Math.abs(r.bones.Bone_35.position[0]-bones.Bone_35.pos[i][0])<1e-8,'full-bone source translation parity');
}
const l=poseInPlace(clip,plan,1-1e-8),f=poseInPlace(clip,plan,0);
for(const name of Object.keys(bones)){
 assert.ok(angleDeg(l.bones[name].quaternion,f.bones[name].quaternion)<.005,`seam rotation ${name}`);
 assert.ok(Math.hypot(...l.bones[name].position.map((x,i)=>x-f.bones[name].position[i]))<.0001,`seam position ${name}`);
}
const damaged=structuredClone(clip);damaged.bones[ROOT].pos=damaged.bones[ROOT].pos.map(p=>[p[0],p[1],-p[2]]);
assert.throws(()=>deriveInPlace(damaged),/BACKWARD_ROOT_TRAVEL_NOT_FOUND/);
assert.throws(()=>poseInPlace(clip,plan,Number.NaN),/NONFINITE_PHASE/);
// A bone whose stored source quaternion changes sign must still take the
// shortest SO(3) path at the repaired cycle seam, never a 360-degree spin.
const flipped=structuredClone(clip);flipped.bones.Bone_42.quat=flipped.bones.Bone_42.quat.map((q,i)=>i<20?q.map(x=>-x):q);
const ff=deriveInPlace(flipped);const a=poseInPlace(flipped,ff,.965).bones.Bone_42.quaternion;
const b=poseInPlace(flipped,ff,.99).bones.Bone_42.quaternion;
assert.ok(angleDeg(a,b)<5,'shortest path despite quaternion sign variation');
assert.throws(()=>deriveInPlace({sampleCount:5,bones:{}}),/BAD_REAL_SOURCE_SAMPLE_CONTRACT/);
// Embedded real extraction probes: reset from -0.953415 near t=.852222 to +.089648 at .866667.
assert.ok(.089648-(-.953415)>1,'real GLB last-key reset proved by source extraction');
console.log('FULL_74_JOINT_BACKWARD_PROCEDURAL_TESTS_PASS: automatic real reset detection, nonwrapped trend, source parity, seam closure, negative controls');

// Actual failure regression: when the terminal key is excluded from 720
// periodic samples, calibration MUST still start and source phase zero match.
const endpointOnly=structuredClone(clip);
for(let i=0;i<N;i++){
 const ph=i/N,w=2*Math.PI*ph;
 endpointOnly.bones[ROOT].pos[i][2]=.1065-1.072*ph+.012*Math.sin(w);
}
endpointOnly.terminalRootTrack={lastTime:.866667,previousTime:.852222,lastPosition:[.00332,.966211,.089648],previousPosition:[.006871,.945517,-.953415]};
endpointOnly.duration=.866667;
const ep=deriveInPlace(endpointOnly);
assert.equal(ep.resetIndex,null,'endpoint jump need not appear in source sampled timeline');
assert.equal(ep.resetEvidence,'RAW_TERMINAL_KEY_RESET');
assert.ok(ep.cycleTravel[2]<-.5,'travel derived even without sampled reset');
const unproven=structuredClone(endpointOnly);delete unproven.terminalRootTrack;
const ung=deriveInPlace(unproven);
assert.equal(ung.resetEvidence,'ENDPOINT_NOT_SAMPLED_OR_ROOT_RESET_NOT_VISIBLE');
const t0=poseInPlace(endpointOnly,ep,0);
for(const [name,b] of Object.entries(endpointOnly.bones)){
 assert.ok(angleDeg(t0.bones[name].quaternion,b.quat[0])<.001,name+' time zero rotation');
 for(let k=0;k<3;k++){
  assert.ok(Math.abs(t0.bones[name].position[k]-b.pos[0][k])<1e-9,name+' time zero position');
  assert.ok(Math.abs(t0.bones[name].scale[k]-b.scale[0][k])<1e-9,name+' time zero scale');
 }
}
console.log('ENDPOINT_ONLY_RESET_STARTUP_PASS source t0 all 74 bones match; no mandatory sampled jump');
__HAREWORKS_V022_INPLACE_KERNEL_TEST_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/inplace-witness-test.mjs" <<'__HAREWORKS_V022_INPLACE_WITNESS_TEST_MJS__'
import fs from 'node:fs';import assert from 'node:assert/strict';
import {deriveInPlace,poseInPlace,ROOT} from './inplace-kernel.mjs';
const w=JSON.parse(fs.readFileSync(new URL('./source-witness.json',import.meta.url)));
assert.equal(w.sourceSha256,'a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6');
assert.equal(w.clip,'Walk_Backward');assert.equal(w.samples.length,61);
const N=720,bones={};for(let b=0;b<74;b++){const name=b===0?ROOT:'Bone_'+b;bones[name]={pos:[],quat:[],scale:[]};
 for(let i=0;i<N;i++){
  const t=(i/N)*w.duration;const ind=Math.max(0,Math.min(59,w.samples.findIndex((s,j)=>j<60&&s.t<=t&&w.samples[j+1].t>=t)));const k=ind<0?59:ind;
  const a=w.samples[k],z=w.samples[k+1],f=Math.max(0,Math.min(1,(t-a.t)/(z.t-a.t)));
  const xyz=a.p.map((x,k)=>x+(z.p[k]-x)*f);bones[name].pos.push(name===ROOT?xyz:[0,b*.001,0]);
  bones[name].quat.push([0,0,0,1]);bones[name].scale.push([1,1,1]);
 }
}
const cal={sampleCount:N,bones};const plan=deriveInPlace(cal);
assert.ok(plan.cleanPhase>.97&&plan.cleanPhase<.99,'safely detected terminal reset in actual source curve');
assert.ok(plan.cycleTravel[2]<-1.04&&plan.cycleTravel[2]>-1.12,'travel recovered from actual source curve');
assert.ok(plan.resetRootStep===null||plan.resetRootStep>.05,'sampled reset only when observed');
const checkpoints=[0,.2,.55,.9,.999999];for(const p of checkpoints){let r=poseInPlace(cal,plan,p).bones[ROOT].position;assert.ok(Math.abs(r[2]-.1065)<.06,`in-place root from actual source at phase=${p}: ${r[2]}`)}
console.log('REAL_61_SOURCE_WITNESS_TEST_PASS 74 synthetic joint scaffolds; observed root reset verified, actual GLB browser parity still pending');
__HAREWORKS_V022_INPLACE_WITNESS_TEST_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/source-witness.json" <<'__HAREWORKS_V022_SOURCE_WITNESS_JSON__'
{
  "schema": "hareworks-v0.2.2-original-v0.2.1-source-witness-unchanged",
  "sourceSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "clip": "Walk_Backward",
  "duration": 0.866667,
  "extraction": "Hareworks nine-clip gait and idle-turn v1.0.8, browser exact-source 61 tracks",
  "samples": [
    {
      "t": 0,
      "p": [
        0.006408,
        0.950326,
        0.1065
      ]
    },
    {
      "t": 0.014444,
      "p": [
        0.006789,
        0.948938,
        0.091231
      ]
    },
    {
      "t": 0.028889,
      "p": [
        0.007171,
        0.94755,
        0.075962
      ]
    },
    {
      "t": 0.043333,
      "p": [
        0.007858,
        0.945536,
        0.060687
      ]
    },
    {
      "t": 0.057778,
      "p": [
        0.00868,
        0.943245,
        0.045408
      ]
    },
    {
      "t": 0.072222,
      "p": [
        0.009666,
        0.940615,
        0.030029
      ]
    },
    {
      "t": 0.086667,
      "p": [
        0.010911,
        0.937444,
        0.014491
      ]
    },
    {
      "t": 0.101111,
      "p": [
        0.012185,
        0.934248,
        -0.001096
      ]
    },
    {
      "t": 0.115556,
      "p": [
        0.013792,
        0.930751,
        -0.017264
      ]
    },
    {
      "t": 0.13,
      "p": [
        0.015399,
        0.927253,
        -0.033432
      ]
    },
    {
      "t": 0.144444,
      "p": [
        0.017197,
        0.924267,
        -0.050445
      ]
    },
    {
      "t": 0.158889,
      "p": [
        0.019052,
        0.921433,
        -0.06771
      ]
    },
    {
      "t": 0.173333,
      "p": [
        0.020824,
        0.91972,
        -0.085925
      ]
    },
    {
      "t": 0.187778,
      "p": [
        0.0225,
        0.919312,
        -0.105249
      ]
    },
    {
      "t": 0.202222,
      "p": [
        0.024125,
        0.919109,
        -0.124789
      ]
    },
    {
      "t": 0.216667,
      "p": [
        0.025477,
        0.920034,
        -0.145519
      ]
    },
    {
      "t": 0.231111,
      "p": [
        0.026829,
        0.920959,
        -0.166249
      ]
    },
    {
      "t": 0.245556,
      "p": [
        0.027987,
        0.922396,
        -0.187168
      ]
    },
    {
      "t": 0.26,
      "p": [
        0.029109,
        0.923925,
        -0.208122
      ]
    },
    {
      "t": 0.274444,
      "p": [
        0.030148,
        0.925616,
        -0.228668
      ]
    },
    {
      "t": 0.288889,
      "p": [
        0.031115,
        0.927446,
        -0.248863
      ]
    },
    {
      "t": 0.303333,
      "p": [
        0.032061,
        0.92932,
        -0.268706
      ]
    },
    {
      "t": 0.317778,
      "p": [
        0.032932,
        0.931345,
        -0.287374
      ]
    },
    {
      "t": 0.332222,
      "p": [
        0.033803,
        0.933371,
        -0.306043
      ]
    },
    {
      "t": 0.346667,
      "p": [
        0.034478,
        0.935709,
        -0.323215
      ]
    },
    {
      "t": 0.361111,
      "p": [
        0.035136,
        0.938075,
        -0.340263
      ]
    },
    {
      "t": 0.375556,
      "p": [
        0.035556,
        0.940282,
        -0.356896
      ]
    },
    {
      "t": 0.39,
      "p": [
        0.035829,
        0.942392,
        -0.373271
      ]
    },
    {
      "t": 0.404444,
      "p": [
        0.036023,
        0.944292,
        -0.389557
      ]
    },
    {
      "t": 0.418889,
      "p": [
        0.036038,
        0.945723,
        -0.405642
      ]
    },
    {
      "t": 0.433333,
      "p": [
        0.036053,
        0.947154,
        -0.421727
      ]
    },
    {
      "t": 0.447778,
      "p": [
        0.035805,
        0.947591,
        -0.437695
      ]
    },
    {
      "t": 0.462222,
      "p": [
        0.035557,
        0.948029,
        -0.453664
      ]
    },
    {
      "t": 0.476667,
      "p": [
        0.035115,
        0.947607,
        -0.46965
      ]
    },
    {
      "t": 0.491111,
      "p": [
        0.034587,
        0.946803,
        -0.485644
      ]
    },
    {
      "t": 0.505556,
      "p": [
        0.03395,
        0.945391,
        -0.501725
      ]
    },
    {
      "t": 0.52,
      "p": [
        0.03314,
        0.943007,
        -0.517946
      ]
    },
    {
      "t": 0.534444,
      "p": [
        0.03232,
        0.940579,
        -0.534176
      ]
    },
    {
      "t": 0.548889,
      "p": [
        0.031375,
        0.937623,
        -0.550523
      ]
    },
    {
      "t": 0.563333,
      "p": [
        0.03043,
        0.934668,
        -0.566871
      ]
    },
    {
      "t": 0.577778,
      "p": [
        0.029274,
        0.931918,
        -0.583818
      ]
    },
    {
      "t": 0.592222,
      "p": [
        0.028055,
        0.92923,
        -0.600945
      ]
    },
    {
      "t": 0.606667,
      "p": [
        0.026698,
        0.926921,
        -0.618642
      ]
    },
    {
      "t": 0.621111,
      "p": [
        0.02518,
        0.925054,
        -0.637003
      ]
    },
    {
      "t": 0.635556,
      "p": [
        0.023624,
        0.923363,
        -0.65559
      ]
    },
    {
      "t": 0.65,
      "p": [
        0.021862,
        0.92264,
        -0.675423
      ]
    },
    {
      "t": 0.664444,
      "p": [
        0.020101,
        0.921917,
        -0.695256
      ]
    },
    {
      "t": 0.678889,
      "p": [
        0.018278,
        0.922174,
        -0.716307
      ]
    },
    {
      "t": 0.693333,
      "p": [
        0.016445,
        0.922609,
        -0.73758
      ]
    },
    {
      "t": 0.707778,
      "p": [
        0.014779,
        0.923519,
        -0.759082
      ]
    },
    {
      "t": 0.722222,
      "p": [
        0.013255,
        0.924837,
        -0.78078
      ]
    },
    {
      "t": 0.736667,
      "p": [
        0.011828,
        0.926267,
        -0.802265
      ]
    },
    {
      "t": 0.751111,
      "p": [
        0.010726,
        0.928073,
        -0.823039
      ]
    },
    {
      "t": 0.765556,
      "p": [
        0.009623,
        0.929879,
        -0.843812
      ]
    },
    {
      "t": 0.78,
      "p": [
        0.008918,
        0.932254,
        -0.863339
      ]
    },
    {
      "t": 0.794444,
      "p": [
        0.008245,
        0.934677,
        -0.882762
      ]
    },
    {
      "t": 0.808889,
      "p": [
        0.007772,
        0.937351,
        -0.901276
      ]
    },
    {
      "t": 0.823333,
      "p": [
        0.007425,
        0.940182,
        -0.919222
      ]
    },
    {
      "t": 0.837778,
      "p": [
        0.007111,
        0.942936,
        -0.936769
      ]
    },
    {
      "t": 0.852222,
      "p": [
        0.006871,
        0.945517,
        -0.953415
      ]
    },
    {
      "t": 0.866667,
      "p": [
        0.00332,
        0.966211,
        0.089648
      ]
    }
  ]
}
__HAREWORKS_V022_SOURCE_WITNESS_JSON__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/README.md" <<'__HAREWORKS_V022_README_MD__'
# Hareworks Walk_Backward: full-body in-place parity v0.2.2

## Owner decision

The owner **rejected v0.2.0's three-way feminine style transfer** as visually bad and explicitly reported that the backward animation's baked root travel remained. A change to wrist amplitude or a few upper-body channels is not the task. The new, narrowly scoped mission is to reproduce the source `Walk_Backward` **as accurately as practical across all 74 joints**, but **in place**. A later style transfer is out of scope until the base gait receives its own visual acceptance.

The owner has visually **accepted v0.1.9 `Walking_Woman` forward gait as a perfect match**. That viewer, v0.1.2 pelvis/v0.1.3 legs/v0.1.8 upper source-anchored equations, prior source clips and canonical model are unchanged.

## Exact source and repair

Canonical source GLB: `assets/hareworks/Hareworks-nine-clips.glb`, SHA256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`, 6,784,896 bytes, 74 joints, 9 source clips. Only `Walk_Backward` is calibrated. The original user-generated source extraction v1.0.8 confirms the hips travel from roughly `+0.1065` Z at t=0 to `-0.953415` Z at t≈0.852222s, before the **source clip's terminal reset key** returns them to +0.089648 at t=0.866667s. The reset is not physical locomotion.

1. Read the real GLB in the Android browser, SHA-256 verify bytes, and sample the source `Walk_Backward` clip at 720 poses across one cycle. Record ALL 74 local bone quaternions, positions, and scales, not just wrists or feet. These samples are only **one-time calibration evidence**.
2. Build a deterministic independent continuous phase→pose evaluator for every bone using local quaternion slerp and local position/scale interpolation. At runtime the generated rig does **not** have an AnimationMixer or any source animation tracks. This is source-calibrated kinematic reconstruction, not a dynamic physics simulator or a novel generalized motion controller.
3. Detect the genuine late `mixamorigHips` Z teleport from an outlier in its forward-time derivative. Fit the unwrapped horizontal cycle travel from the clean pre-reset section. Subtract that **X/Z trend only**, retaining pelvis Y bobbing, all 74 joint rotations and all joint articulation. Keep an isolated original reference on the left, source-posed for comparison and with the same horizontal detrend.
4. Adaptively choose a source-faithful terminal repair region (starting at 93%, extending as needed for 30/60/120Hz joint continuity) and repair the final region with a periodic C1 quaternion-vector and translation/scale Hermite bridge derived from the source's terminal *clean* joint poses and the source's first poses/velocities. Do not interpolate through the source's bogus reset key, which would produce a roughly 1 m hitch. Every repaired frame is marked as the terminal seam region and is excluded from the normal-source parity score.
5. Audit ALL 74 skinned bones at matching 30/60/120 Hz plus half-frames before the seam, comparing local quaternion, translation, scale, and resulting world-space joint positions. Report per-joint RMS, maximum and worst timestamp; verify generated seam closure and 30/60/120Hz step continuity. Parity warnings are visible rather than hiding the character.

**Critical physical distinction:** an in-place animation will move feet against a motionless display grid; game movement applies external world travel. This campaign does not promise stationary world foot contacts while preventing the model from translating. The intended acceptance is a fixed-origin, source-faithful backward cycle with a smooth seam.

## Delivery and limits

The Android Termux Git campaign has one versioned shell entrypoint. It verifies remote parent, pinned `AGENTS.md`, exact GLB LFS pointer and binary hash, collision-free new paths, preserved approved forward viewer blob, JS/kernel negative tests and real-extraction witness, per-file hashes, scoped Git commit/push, remote file byte readback, no-cache HTTP availability and a dynamically assigned local viewer URL. Only `tools/hareworks-forward-woman/v0.2.2/**` and the corresponding new campaign script are allowed Git mutations. It does not write a new GLB or edit a historical version.

Browser source calibration, actual skinned parity, device rendering, and owner visual approval remain distinct gates. A synthetic or source-extraction fixture pass is **not** proof the actual runtime gait matches. Source parity cannot legitimately be claimed for the intentionally rewritten last seam interval. Future feminine interpretation must be a separate authorized campaign after the backward source baseline is visually accepted.

## v0.2.2 startup repair (owner Android screenshot 5408.png)

The real browser v0.2.1 stopped with `SOURCE_TERMINAL_ROOT_RESET_NOT_DETECTED`, leaving the source first frame and the generated rig unposed in its bind/rest configuration. The GLB terminal reset can occur exactly at clip.duration, while the 720 source calibration samples intentionally omit that key. The old mandatory sampled-jump gate was invalid. This revision makes the sampled jump optional, records raw root track terminal-key evidence separately, and computes backward travel from a clean mid-cycle window. The continuous terminal seam still covers the end of the cycle.

The viewer first loads the actual GLB and lets the original reference run independently even if procedural calibration fails. It hides the uninitialized generated bind pose. Successful startup MUST compare all 74 bones at phase zero for local rotation, translation, scale and world positions, rejecting mismatches rather than showing a false gait. Generated uses no source mixer; no feminine style delta. Real phone proof remains pending.
__HAREWORKS_V022_README_MD__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/contract.json" <<'__HAREWORKS_V022_CONTRACT_JSON__'
{
  "campaign": "hareworks-backward-inplace-startup-repair-v0.2.2",
  "repo": "Valar05/parametric-parambulator",
  "parent": "2d1f6c2d3bcd385666c04e50f5e7134d37d79f26",
  "modelPath": "assets/hareworks/Hareworks-nine-clips.glb",
  "modelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "modelBytes": 6784896,
  "sourceClip": "Walk_Backward",
  "sourceDurationSeconds": 0.866667,
  "sourceJoints": 74,
  "sourceClips": 9,
  "sourceCalibrationSamples": 720,
  "generatedRuntimeSourceAnimationMixerCount": 0,
  "styleTransfer": false,
  "sourceTrackCalibrationOnly": true,
  "inPlace": "automatically detect and remove horizontal cycle trend from hips, preserve vertical bounce, repair terminal reset via C1 seam",
  "acceptance": "30 60 120 hz and midframes all 74 bones local rotation/translation/scale and world position plus cyclic step checks and owner visual verdict",
  "ownerApprovedForwardViewerBlob": "a17f8109766dcfa39fbb75b6b2ff335c358733cb",
  "mutatedGlb": false,
  "preservedForwardGait": true,
  "executionLane": "Android Termux Git only",
  "rulesRead": {
    "agentsGitBlob": "547c2af52303f4efb718bbf8f82a698110c7bfca",
    "campaignEtiquetteId": "1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI",
    "topDownEtiquetteId": "1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU"
  },
  "ownerAcceptedBackward": false,
  "files": [
    "tools/hareworks-forward-woman/v0.2.2/index.html",
    "tools/hareworks-forward-woman/v0.2.2/viewer.mjs",
    "tools/hareworks-forward-woman/v0.2.2/inplace-kernel.mjs",
    "tools/hareworks-forward-woman/v0.2.2/inplace-kernel-test.mjs",
    "tools/hareworks-forward-woman/v0.2.2/inplace-witness-test.mjs",
    "tools/hareworks-forward-woman/v0.2.2/source-witness.json",
    "tools/hareworks-forward-woman/v0.2.2/README.md",
    "tools/hareworks-forward-woman/v0.2.2/contract.json",
    "campaigns/hareworks-backward-inplace-startup-repair-v0.2.2.sh"
  ],
  "adaptiveSeamSearch": "based on actual clean source samples; sampled terminal reset NOT required; 30/60/120Hz continuity remains measured",
  "startupRepair": "detect endpoint-only reset in raw root track or accept source root trend without sampled reset; initialize both sides from time-zero source pose; reference remains playable on procedural-calibration failure"
}
__HAREWORKS_V022_CONTRACT_JSON__
fi
if ((PUBLISHED==0));then
 cp -- "$0" "campaigns/$CAMPAIGN.sh" || fail 'executed script not copied into scoped Git path'
fi
phase=packet-digest
[[ "$(hash "$DIR/index.html")" == "0d073a6edd7fdf4b33d4507bb4811e5ea86003e9d26c13b7713732d97b3280cf" ]] || fail 'embedded file digest mismatch: index.html' 
[[ "$(hash "$DIR/viewer.mjs")" == "4666f0b9181b5a9371ba2dcc5b6c5c2c32226c6f1fe34c518dd44adcac3a488d" ]] || fail 'embedded file digest mismatch: viewer.mjs' 
[[ "$(hash "$DIR/inplace-kernel.mjs")" == "a636a730ae770c90f1d7dc8441982b89e0dd28a1d79ac8b71f3a1b0c2f0f6cb3" ]] || fail 'embedded file digest mismatch: inplace-kernel.mjs' 
[[ "$(hash "$DIR/inplace-kernel-test.mjs")" == "19e50a36ba0ab5c5753142655af5a0b49a8b2468168d0c28bd76e73b3d78ab9f" ]] || fail 'embedded file digest mismatch: inplace-kernel-test.mjs' 
[[ "$(hash "$DIR/inplace-witness-test.mjs")" == "7e7a7aa7202fbcb4ef783a960aa8da8d1c94c864cd462c5eee97a4ea3da144e7" ]] || fail 'embedded file digest mismatch: inplace-witness-test.mjs' 
[[ "$(hash "$DIR/source-witness.json")" == "e5d57d2528b873836b759138eb318514fe80dcac07f19844d9ece5350d636408" ]] || fail 'embedded file digest mismatch: source-witness.json' 
[[ "$(hash "$DIR/README.md")" == "97631d96e98195c052816c90deaa25440eef786942756db40c36311e7996d3d9" ]] || fail 'embedded file digest mismatch: README.md' 
[[ "$(hash "$DIR/contract.json")" == "e9439f7321b52d9e3d4594f2537bfdcf2c20505089e292a4ad98c39c1f9f0c30" ]] || fail 'embedded file digest mismatch: contract.json' 
[[ "$(hash "campaigns/$CAMPAIGN.sh")" == "$SELF_SHA" ]] || fail 'Git campaign entrypoint not identical to user downloaded script'
phase=tests
for js in "$DIR/viewer.mjs" "$DIR/inplace-kernel.mjs" "$DIR/inplace-kernel-test.mjs" "$DIR/inplace-witness-test.mjs";do
 node --check "$js" || fail "JavaScript syntax: $js"
done
node "$DIR/inplace-kernel-test.mjs" | tee "$STATE/full-rig-unit-test.log" || fail 'full-rig reset/seam and negative tests failed'
node "$DIR/inplace-witness-test.mjs" | tee "$STATE/source-witness-test.log" || fail 'exact GLB-extraction witness regression failed'
node tools/hareworks-forward-woman/v0.1.9/pelvis-tilt-test.mjs > "$STATE/accepted-forward-pelvis-test.log" || fail 'accepted forward pelvis module regression'
node tools/hareworks-forward-woman/v0.1.9/upper-anchor-test.mjs > "$STATE/accepted-forward-upper-test.log" || fail 'accepted forward upper module regression'
node tools/hareworks-forward-woman/v0.1.3/foot-kernel-test.mjs > "$STATE/accepted-forward-legs-test.log" || fail 'accepted forward leg kernel regression'
node tools/hareworks-forward-woman/v0.1.2/pose-kernel-test.mjs > "$STATE/accepted-forward-pose-test.log" || fail 'accepted forward pose kernel regression'
python3 - "$DIR" "$MODEL_SHA" <<'PY_CONTRACT' || fail 'browser dependency/source contract failed'
import pathlib,sys,re,json
folder,sha=sys.argv[1:];p=pathlib.Path(folder)
js=(p/'viewer.mjs').read_text();html=(p/'index.html').read_text();contract=json.loads((p/'contract.json').read_text());w=json.loads((p/'source-witness.json').read_text())
assert contract['modelSha256']==sha and w['sourceSha256']==sha
assert contract['sourceClip']=='Walk_Backward'==w['clip']
assert contract['sourceCalibrationSamples']==720
assert contract['generatedRuntimeSourceAnimationMixerCount']==0 and not contract['styleTransfer']
assert 'new THREE.AnimationMixer(ref)' in js and 'new THREE.AnimationMixer(gen)' not in js
assert 'adaptiveSeam(source)' in js and 'poseInPlace(source,plan,p)' in js and 'checkSourceTimeZero()' in js and 'sourceReady=true' in js
assert 'SAMPLES=720' in js and 'audit(false)' in js
assert 'id="auditButton"' in html and 'id="stage"' in html and 'id="identity"' in html
assert 'src="./viewer.mjs"' in html
assert len(w['samples'])==61 and w['samples'][-1]['p'][2]-w['samples'][-2]['p'][2]>1
for rel in re.findall(r"from\s+[\x27\x22](\.[^\x27\x22]+)[\x27\x22]",js):
 assert (p/rel).resolve(strict=True).is_file(),rel
assert 'Walking_Woman' not in js and 'transferPose' not in js
print('ONE_SOURCE_ALL_BONES_BROWSER_DEPENDENCIES_AND_NEGATIVE_TRANSFER_GUARD=PASS')
PY_CONTRACT
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.9/viewer.mjs)" == "$ACCEPTED_FORWARD_VIEWER_BLOB" ]] || fail 'accepted forward source unexpectedly changed'
if ((PUBLISHED==0));then
 phase=scoped-stage
 [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote advanced, no force push or silent rebase'
 git add -- "${FILES[@]}" || fail 'scoped stage failed'
 python3 - "${FILES[@]}" <<'PY_STAGE' || fail 'new staged files differ from allowlist'
import subprocess,sys
want=set(sys.argv[1:]);have=set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines())
assert want==have,{'missing':sorted(want-have),'unexpected':sorted(have-want)}
assert all(not p.endswith('.glb') for p in have)
print('ONLY_NINE_NEW_ALLOWLISTED_TEXT_FILES_STAGED=PASS')
PY_STAGE
 for protected in AGENTS.md "$MODEL" tools/hareworks-forward-woman/v0.1.9/viewer.mjs tools/hareworks-forward-woman/v0.1.9/pelvis-tilt.mjs tools/hareworks-forward-woman/v0.2.0/viewer.mjs tools/hareworks-forward-woman/v0.2.1/viewer.mjs tools/hareworks-forward-woman/v0.2.1/inplace-kernel.mjs tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs;do
  git diff --quiet -- "$protected" || fail "protected path changed: $protected"
  [[ "$(git rev-parse "HEAD:$protected")" == "$(git rev-parse "$BASE:$protected")" ]] || fail "protected Git blob baseline changed: $protected"
 done
 phase=commit
 git -c user.name='Hareworks Termux Campaign' -c user.email='hareworks-campaign@users.noreply.github.com' commit -m 'Fix endpoint-only reset calibration and t0 pose mismatch v0.2.2' || fail 'Git commit failed'
 COMMIT=$(git rev-parse HEAD)
 [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'commit does not descend from pinned parent'
 phase=publish
 [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote main advanced before push'
 GIT_LFS_SKIP_PUSH=1 git push origin HEAD:refs/heads/main || fail "Git push failed; preserved local campaign commit=$COMMIT"
else
 COMMIT="$REMOTE"
fi
phase=remote-readback
[[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$COMMIT" ]] || fail 'remote main readback differs from campaign revision'
GIT_LFS_SKIP_SMUDGE=1 git fetch --depth=1 origin main || fail 'remote readback fetch failed'
[[ "$(git rev-parse FETCH_HEAD)" == "$COMMIT" ]] || fail 'fetched branch is not commit'
for path in "${FILES[@]}";do
 [[ "$(git rev-parse "FETCH_HEAD:$path")" == "$(git rev-parse "HEAD:$path")" ]] || fail "remote published file differs from exact intended bytes: $path"
done
for path in AGENTS.md "$MODEL" tools/hareworks-forward-woman/v0.1.9/viewer.mjs tools/hareworks-forward-woman/v0.1.9/pelvis-tilt.mjs tools/hareworks-forward-woman/v0.2.0/viewer.mjs tools/hareworks-forward-woman/v0.2.1/viewer.mjs tools/hareworks-forward-woman/v0.2.1/inplace-kernel.mjs;do
 [[ "$(git rev-parse "FETCH_HEAD:$path")" == "$(git rev-parse "$BASE:$path")" ]] || fail "remote approved source changed: $path"
done
echo "EXACT_REMOTE_GIT_COMMIT_AND_BLOB_READBACK=PASS $COMMIT"
phase=viewer-snapshot
# Source model bytes are materialized only in the isolated HTTP snapshot, not Git.
cp -- "$SOURCE" "$MODEL" || fail 'source GLB viewer snapshot copy failed'
[[ "$(hash "$MODEL")" == "$MODEL_SHA" ]] || fail 'browser HTTP copy lost exact model bytes'
cat > "$ROOT/server.py" <<'PY_SERVER'
import http.server,json,os,pathlib,sys
root,ready=sys.argv[1:]
class Handler(http.server.SimpleHTTPRequestHandler):
 extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=root,**kwargs)
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
[[ "$PORT" =~ ^[0-9]+$ ]] && kill -0 "$PID" 2>/dev/null || fail 'fresh no-cache viewer HTTP server not running'
python3 - "http://127.0.0.1:$PORT" "$DIR" "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" "$STATE/http-manifest.json" <<'PY_HTTP' || fail 'HTTP exact requested browser JS and source model resource check failed'
import hashlib,json,pathlib,re,sys,urllib.parse,urllib.request
origin,dir,model,sha,size,out=sys.argv[1:];size=int(size)
def get(url):
 with urllib.request.urlopen(url,timeout=35) as r:
  assert 'no-store' in r.headers.get('Cache-Control',''),('missing no-cache',url)
  return r.read()
root=origin+'/'+dir+'/'
html=get(root+'index.html').decode();js=get(root+'viewer.mjs').decode()
assert 'src="./viewer.mjs"' in html and 'id="stage"' in html and 'id="auditButton"' in html
assert 'generatedAt(p)' in js and 'adaptiveSeam(source)' in js
urls=[root+'viewer.mjs',root+'inplace-kernel.mjs',root+'inplace-kernel-test.mjs',root+'inplace-witness-test.mjs',root+'source-witness.json',root+'index.html']
urls += [urllib.parse.urljoin(root+'viewer.mjs',m) for m in re.findall(r"from\s+[\x27\x22](\.[^\x27\x22]+)[\x27\x22]",js)]
for url in sorted(set(urls)):assert get(url),('browser dependency missing',url)
blob=get(origin+'/'+model)
assert len(blob)==size and hashlib.sha256(blob).hexdigest()==sha
report={'status':'EXACT_RESOURCES_HTTP_VERIFIED_BROWSER_WEBGL_PENDING','sourceClip':'Walk_Backward','modelSHA256':sha,'modelBytes':len(blob),'requestedURLs':sorted(set(urls)),'runtimeBrowserAuditPending':True}
pathlib.Path(out).write_text(json.dumps(report,indent=2))
print('FULL_74_BONE_BROWSER_MODULES_AND_REAL_GLB_HTTP_PASS',len(set(urls)),'resources')
PY_HTTP
curl -fsSI --max-time 5 "http://127.0.0.1:$PORT/$DIR/index.html" > "$STATE/http-headers.txt" || fail 'HTTP headers not read back'
URL="http://127.0.0.1:$PORT/$DIR/index.html?commit=$COMMIT&scriptSha=$SELF_SHA&modelSha=$MODEL_SHA"
python3 - "$STATE/receipt.json" "$CAMPAIGN" "$BASE" "$COMMIT" "$SELF_SHA" "$MODEL_SHA" "$AGENTS_BLOB" "$URL" "$PID" "$PORT" "$ROOT" <<'PY_RECEIPT'
import datetime,json,pathlib,sys
path,campaign,parent,commit,entry,model,agents,url,pid,port,snapshot=sys.argv[1:]
report={'campaign':campaign,'state':'Git_published_readback_HTTP_verified_real_browser_74_bone_parity_pending','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'originalParent':parent,'exactPublishedCommit':commit,'entrypointSHA256':entry,'sourceModelSha256':model,'rootAgentsGitBlob':agents,
 'rulesRead':{'AGENTS.md':'fresh remote and pinned blob verified','Campaign Etiquette':'Home Center id 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI','Top-down Etiquette':'Home Center id 1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'},
 'sourceClip':'Walk_Backward','sourceClipsUsed':1,'generatedMixerCount':0,'generatedJoints':74,'calibrationRatePerCycle':720,'rootTravel':'X/Z trend stripped; sampled reset optional, raw terminal-key evidence captured, terminal continuity fitted',
 'preservedAcceptedForward':True,'preservedSourceGlb':True,'styleTransferApplied':False,'browserURL':url,'browserPort':int(port),'browserPID':int(pid),'isolatedSnapshot':snapshot,
 'hostUnitTests':'PASS, including endpoint-only reset, exact time-zero pose, original 61-source witness and injected invalid roots','HTTPModelAndModuleManifest':'verified','actualBrowserSkinnedParity':'NOT_YET_CONFIRMED','sourceFirstFrameParity':'BROWSER_GATE_REQUIRED','ownerVisualAcceptance':'PENDING','authorizedExecutionLane':'Android Termux Git ONLY'}
pathlib.Path(path).write_text(json.dumps(report,indent=2))
PY_RECEIPT
echo "REMOTE_COMMIT=$COMMIT"
echo "VIEWER_URL=$URL"
echo "VIEWER_PORT=$PORT VIEWER_PID=$PID"
echo "MODEL_SHA256=$MODEL_SHA"
echo "SOURCE_CLIP=Walk_Backward"
echo "HTTP_MANIFEST=$STATE/http-manifest.json"
echo "RECEIPT=$STATE/receipt.json"
echo 'REAL_74_BONE_BROWSER_PARITY=MEASURED_ONLY_AFTER_BROWSER_RUN; OWNER_VISUAL_ACCEPTANCE=PENDING'
if command -v termux-open-url >/dev/null;then
 termux-open-url "$URL" || echo "OPEN_REQUEST_FAILED; open VIEWER_URL=$URL"
else
 echo "TERMUX_OPEN_URL_UNAVAILABLE; open VIEWER_URL=$URL"
fi
