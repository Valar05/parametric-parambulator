#!/data/data/com.termux/files/usr/bin/bash
# hareworks-backward-style-transfer-v0.2.0: three-clip direction-preserving local-bone style transfer.
# This packet does NOT modify or republish the owner-accepted forward gait.
set -Eeuo pipefail
CAMPAIGN='hareworks-backward-style-transfer-v0.2.0'
REPO='Valar05/parametric-parambulator'
BASE='56f8abbc6d30a14983d6e94116e9090c365ef182'
DIR='tools/hareworks-forward-woman/v0.2.0'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE='6784896'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ACCEPTED_FORWARD_VIEWER_BLOB='a17f8109766dcfa39fbb75b6b2ff335c358733cb'
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
exec > >(tee -a "$STATE/run.log") 2>&1
phase=preflight;ROOT='';WORK='';COMMIT='';PID='';PORT='';SOURCE=''
fail(){
 echo "BLOCKED step=$phase reason=$*"
 [[ -z "$ROOT" || ! -f "$ROOT/server.log" ]] || { echo SERVER_LOG_TAIL:; tail -n 25 "$ROOT/server.log" || true; }
 python3 - "$STATE/blocked.json" "$CAMPAIGN" "$phase" "$*" "$COMMIT" "$ROOT" <<'PY_BLOCK' || true
import pathlib,datetime,json,sys
p,name,phase,reason,commit,root=sys.argv[1:]
pathlib.Path(p).write_text(json.dumps({'campaign':name,'state':'BLOCKED','phase':phase,'reason':reason,'knownCommit':commit,'snapshot':root,'ownerAcceptedBackward':False,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
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
echo "ENTRYPOINT_SHA256=$SELF_SHA"
echo "PINNED_PARENT=$BASE"
echo "EXPECTED_SOURCE_GLB_SHA256=$MODEL_SHA"
ORIGIN="https://github.com/$REPO.git"
phase=remote-preflight
REMOTE=''
for retry in 1 2 3;do
 REMOTE=$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1) || REMOTE=''
 [[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] && break
 sleep "$retry"
done
[[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] || fail 'remote Git main lookup unavailable'
echo "OBSERVED_REMOTE_MAIN=$REMOTE"
phase=isolation
ROOT=$(mktemp -d "$STATE/snapshot.XXXXXXXX") || fail 'isolated snapshot mkdir failed'
WORK="$ROOT/repo"
for retry in 1 2;do
 if GIT_LFS_SKIP_SMUDGE=1 git -c lfs.install.skip=true clone --depth=1 --filter=blob:none --no-checkout --single-branch --branch main "$ORIGIN" "$WORK";then break;fi
 [[ ! -e "$WORK" ]] || fail 'partial isolated clone; no checkout overwritten'
 sleep "$retry"
done
[[ -d "$WORK/.git" ]] || fail 'isolated clone failed'
git -C "$WORK" sparse-checkout init --cone || fail 'sparse checkout init failed'
git -C "$WORK" sparse-checkout set assets/hareworks tools/hareworks-forward-woman campaigns || fail 'sparse checkout set failed'
GIT_LFS_SKIP_SMUDGE=1 git -C "$WORK" checkout -B "$CAMPAIGN" "$REMOTE" || fail 'isolated checkout failed'
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$REMOTE" ]] || fail 'isolated checkout revision differs'
cd "$WORK"
[[ -z "$(git status --porcelain)" ]] || fail 'unexpected dirty isolated checkout'
phase=source-and-authority
[[ -f AGENTS.md ]] && grep -Fq 'Termux Git only' AGENTS.md || fail 'AGENTS mandatory authority missing'
[[ "$(git rev-parse HEAD:AGENTS.md)" == "$AGENTS_BLOB" ]] || fail 'AGENTS.md changed since fresh rules read'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.9/viewer.mjs)" == "$ACCEPTED_FORWARD_VIEWER_BLOB" ]] || fail 'accepted v0.1.9 forward viewer changed'
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" <<'PY_POINTER' || fail 'Git LFS model pointer does not match canonical source'
import subprocess,sys
path,sha,size=sys.argv[1:]
expected=f'version https://git-lfs.github.com/spec/v1\noid sha256:{sha}\nsize {size}\n'.encode()
actual=subprocess.check_output(['git','show','HEAD:'+path])
assert actual==expected,(actual[:100],expected[:100])
print('CANONICAL_SOURCE_LFS_POINTER=PASS')
PY_POINTER
FILES=("$DIR/index.html" "$DIR/viewer.mjs" "$DIR/transfer-kernel.mjs" "$DIR/transfer-kernel-test.mjs" "$DIR/README.md" "$DIR/contract.json" "campaigns/$CAMPAIGN.sh")
phase=collision-gate
PUBLISHED=0
if [[ "$REMOTE" == "$BASE" ]];then
 for path in "${FILES[@]}";do
  [[ ! -e "$path" && ! -L "$path" ]] || fail "new campaign destination already exists: $path"
  if git cat-file -e "HEAD:$path" 2>/dev/null;then fail "remote Git destination collision: $path";fi
 done
else
 if git cat-file -e "HEAD:campaigns/$CAMPAIGN.sh" 2>/dev/null && git cat-file -e "HEAD:$DIR/viewer.mjs" 2>/dev/null;then
  [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'unexpected existing campaign parent'
  [[ "$(git show "HEAD:campaigns/$CAMPAIGN.sh" | sha256sum | cut -d' ' -f1)" == "$SELF_SHA" ]] || fail 'existing campaign filename differs from downloaded SHA'
  PUBLISHED=1
  echo "EXACT_CAMPAIGN_ALREADY_PUBLISHED=$REMOTE; continuing viewer recovery without mutation"
 else
  fail 'main advanced beyond pinned parent; do not silently rebase or overwrite'
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
 command -v git-lfs >/dev/null || fail 'canonical GLB not cached and git-lfs missing'
 git lfs install --local || fail 'Git LFS local setup failed'
 for retry in 1 2 3;do
  if GIT_LFS_SKIP_SMUDGE=1 git lfs fetch -I "$MODEL" -X '' origin "$REMOTE";then break;fi
  sleep "$retry"
 done
 OBJECT=$(git rev-parse --git-path "lfs/objects/${MODEL_SHA:0:2}/${MODEL_SHA:2:2}/$MODEL_SHA")
 [[ -f "$OBJECT" ]] || fail 'verified canonical LFS binary unavailable'
 SOURCE="$OBJECT"
fi
[[ "$(wc -c < "$SOURCE" | tr -d ' ')" == "$MODEL_SIZE" && "$(hash "$SOURCE")" == "$MODEL_SHA" ]] || fail 'real canonical GLB content hash or size mismatch'
python3 - "$SOURCE" <<'PY_GLB' || fail 'source GLB skeleton/clip/duration contract failed'
import json,struct,sys
p=sys.argv[1]
with open(p,'rb') as f:
 head=f.read(20)
 assert head[:4]==b'glTF' and struct.unpack_from('<I',head,8)[0]==6784896
 sz,kind=struct.unpack_from('<I4s',head,12)
 assert kind==b'JSON'
 metadata=json.loads(f.read(sz))
assert len(metadata['skins'][0]['joints'])==74
assert len(metadata['animations'])==9
by={x['name']:x for x in metadata['animations']}
assert all(x in by for x in ['Walking','Walking_Woman','Walk_Backward'])
assert len(metadata['nodes'])>=74
print('ACTUAL_74_JOINT_NINE_CLIP_GLB=PASS')
PY_GLB
phase=payload
if ((PUBLISHED==0));then mkdir -p "$DIR" || fail 'new campaign folder creation failed';fi
if ((PUBLISHED==0));then
cat > "$DIR/index.html" <<'__HAREWORKS_BACKWARD_V020_INDEX_HTML__'
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#101a25"><title>Hareworks v0.2.0 · Three-way Backward Woman Walk</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>
:root{font:14px system-ui,sans-serif;background:#101a25;color:#edf6ff;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:1100px;margin:auto;padding:10px}h1{font-size:21px;margin:5px 0}p{line-height:1.5;color:#c1d3df;margin:8px 0}.pill{border:1px solid #65839b;border-radius:99px;padding:6px 10px;font-size:11px}header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}#status{min-height:46px;padding:12px 0;color:#8be4bf}#stage{border:1px solid #5e7890;overflow:hidden;border-radius:9px}canvas{width:100%;display:block;touch-action:none}.labels{display:grid;grid-template-columns:1fr 1fr;gap:12px;text-align:center;margin:7px 0;color:#e1f0ff}.toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0;background:#1d3042;padding:9px;border-radius:8px}button{font:inherit;color:#fff;background:#2d4b65;border:1px solid #7193ad;border-radius:7px;min-height:44px;padding:9px 13px}button[aria-pressed=true]{outline:2px solid #9de6ef;background:#3a6676}button:focus-visible,input:focus-visible{outline:3px solid #9de6ef}input[type=range]{accent-color:#8bddf1;min-width:135px;flex:1}label{display:flex;gap:7px;align-items:center;flex:1;min-width:160px}#audit{white-space:pre-wrap;overflow-wrap:anywhere;background:#152638;border:1px solid #435d73;border-radius:8px;padding:12px;font:12px/1.6 ui-monospace,monospace}#identity{font:10px/1.6 ui-monospace,monospace;overflow-wrap:anywhere;color:#9bb9c9}.small{font-size:12px}a{color:#9ce5f6}
</style></head><body><main>
<header><h1>🐇 Hareworks · Backward Woman Style Transfer</h1><span class="pill">v0.2.0 · three source clips · generated fourth gait</span></header>
<p><strong>Not reverse playback.</strong> The third gait is constructed by transferring the local bone-change signature <strong>Walking → Walking_Woman</strong> onto <strong>Walk_Backward</strong>. Two-leg contact events align the otherwise different clip phases. All 74 joints participate; the backward pelvis Z path stays backward.</p>
<div id="identity" role="status">Loading build and source identity…</div><div id="status" role="status" aria-live="polite">Loading exact 6.8 MB skinned GLB…</div>
<div class="toolbar" role="group" aria-label="Comparison modes"><button id="backMode" aria-pressed="true">Backward: source vs new</button><button id="sourceMode" aria-pressed="false">Show forward style sources</button><span class="small" id="comparison">B + [W − N] with contact phase warp</span></div>
<div class="labels"><strong id="leftCaption">SOURCE · normal backward</strong><strong id="rightCaption">RESULT · woman-style backward</strong></div>
<div id="stage" role="img" aria-label="Orbitable 3D comparison of original and three-way-transferred backward walking woman"></div>
<div class="toolbar" role="group" aria-label="Camera views"><strong>View:</strong><button id="side">Side</button><button id="front">Front</button><button id="oblique">Three-quarter</button><button id="top">Overhead</button><span class="small">Drag to orbit, pinch to zoom</span></div>
<div class="toolbar"><button id="play">Pause</button><label>Phase <input id="phase" type="range" min="0" max="1000" step="1" value="0" aria-label="Backward cycle phase"></label><output id="phaseValue">0%</output></div>
<div class="toolbar"><label>Woman-style transfer <input id="strength" type="range" min="0" max="100" step="5" value="100" aria-label="Style transfer strength"></label><output id="strengthValue">100%</output><span class="small">0% is diagnostic original backward; 100% is the commissioned transfer</span></div>
<div class="toolbar"><button id="auditButton">Run full 30/60/120 Hz skinned audit</button><button id="export">Export gait evidence</button><a href="../v0.1.9/index.html">Open accepted forward v0.1.9</a></div>
<div id="audit" role="status">Awaiting GLB and three-way calibration…</div>
<p class="small">The two contact anchors per gait are heuristic grounded-foot windows from the original GLB extraction, not force measurements. The pelvis backward Z component is protected. No new GLB or source animation is authored. Joint parity/continuity tests and owner-visible motion are separate acceptance gates. The generated gait is not a fully reactive locomotion engine, and original source tracks are used only for calibration and reference display.</p>
</main><script type="module" src="./viewer.mjs"></script></body></html>
__HAREWORKS_BACKWARD_V020_INDEX_HTML__
fi
if ((PUBLISHED==0));then
cat > "$DIR/viewer.mjs" <<'__HAREWORKS_BACKWARD_V020_VIEWER_MJS__'
/* Hareworks Backward Woman Style Transfer v0.2.0.
 * Three source clips calibrate the generated result ONCE. The generated rig
 * has NO AnimationMixer and NO runtime source clip playback. Its backwards
 * base is reconstructed from source samples; woman-forward minus normal-
 * forward local bone deltas are contact-phase-warped onto it. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {CLIPS,CONTACT,phaseTriplet,transferPose,sampleBone,quatAngle} from './transfer-kernel.mjs';
const $=id=>document.getElementById(id);
const MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const MODEL_URL='../../../assets/hareworks/Hareworks-nine-clips.glb';
const SAMPLES=240,SEP=2.5;
const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const scene=new THREE.Scene();scene.background=new THREE.Color('#101a25');
scene.add(new THREE.HemisphereLight(0xf1f8ff,0x222f40,2.4));
const light=new THREE.DirectionalLight(0xffffff,3.2);light.position.set(-4,7,5);scene.add(light);
const floor=new THREE.GridHelper(14,28,0x5e7486,0x354753);scene.add(floor);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-3.4,3.4,2.2,-2.2,.01,100);
const orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.enablePan=false;
orbit.minZoom=.6;orbit.maxZoom=3.5;orbit.target.set(0,.98,0);
const cam={side:[-7,3.1,.05],front:[0,2.3,9],oblique:[-5.8,3.8,5],top:[-.02,9,.02]};
function cameraAt(name){camera.position.set(...cam[name]);camera.up.set(0,1,0);camera.zoom=1;orbit.target.set(0,.98,0);camera.lookAt(orbit.target);camera.updateProjectionMatrix();orbit.update()}
function resize(){const w=Math.max(320,$('stage').clientWidth),h=Math.max(290,Math.min(570,Math.round(w*.68)));renderer.setSize(w,h,false);
 camera.left=-2.2*w/h;camera.right=-camera.left;camera.top=2.2;camera.bottom=-2.2;camera.updateProjectionMatrix()}
window.addEventListener('resize',resize);for(const c of Object.keys(cam))$(c).onclick=()=>cameraAt(c);
cameraAt('side');resize();
const scenes={},mixers={},rigs={},sourceClips={},samples={};let generated=null,generatedRig=null,ready=false,playing=true;
let phase=0,last=performance.now(),lastAudit=null,visualMode='back',sourceInfo=null;
function say(t){$('status').textContent=t}
function rigOf(root){const bones={};root.traverse(o=>{if(o.isBone){if(bones[o.name])throw Error('DUPLICATE_RIG_BONE '+o.name);bones[o.name]=o}});
 if(Object.keys(bones).length!==74)throw Error('RIG_NOT_74_BONES '+Object.keys(bones).length);
 for(const name of ['mixamorigHips','mixamorigSpine','mixamorigHead','mixamorigLeftFoot','mixamorigRightFoot','mixamorigLeftLeg','mixamorigRightLeg'])if(!bones[name])throw Error('ESSENTIAL_BONE_MISSING '+name);
 return bones}
function makeClipSample(name){const original=sourceClips[name],root=scenes[name],mixer=mixers[name],bones=rigs[name];
 const names=Object.keys(bones),out={sampleCount:SAMPLES,duration:original.duration,bones:{}};
 for(const bone of names)out.bones[bone]={quat:[],pos:[]};
 for(let i=0;i<SAMPLES;i++){
  mixer.setTime(original.duration*i/SAMPLES);root.updateMatrixWorld(true);
  for(const bone of names){const b=bones[bone];out.bones[bone].quat.push(b.quaternion.toArray());out.bones[bone].pos.push(b.position.toArray())}
 }
 mixer.setTime(0);root.updateMatrixWorld(true);return out;
}
function world(b){return b.getWorldPosition(V())}
function applyStyle(at=phase){
 if(!ready)return null;
 const gain=Number($('strength').value)/100;
 const m=transferPose(samples,at,gain);
 for(const [name,p] of Object.entries(m.bones)){
   const b=generatedRig[name];if(!b)throw Error('GENERATED_BONE_MISSING '+name);
   b.quaternion.fromArray(p.quat).normalize();b.position.fromArray(p.pos);
 }
 generated.updateMatrixWorld(true);
 const t=sourceClips.Walk_Backward.duration*m.phases.backward;
 mixers.Walk_Backward.setTime(t);scenes.Walk_Backward.updateMatrixWorld(true);
 mixers.Walking.setTime(sourceClips.Walking.duration*m.phases.normal);
 mixers.Walking_Woman.setTime(sourceClips.Walking_Woman.duration*m.phases.woman);
 scenes.Walking.updateMatrixWorld(true);scenes.Walking_Woman.updateMatrixWorld(true);
 $('phaseValue').textContent=`${Math.round(at*100)}% · back ${m.phases.backward.toFixed(3)} / normal ${m.phases.normal.toFixed(3)} / woman ${m.phases.woman.toFixed(3)}`;
 return m;
}
function setMode(mode){visualMode=mode;
 for(const [key,root] of Object.entries(scenes))root.visible=(mode==='back'?key==='Walk_Backward':key!=='Walk_Backward');
 if(generated)generated.visible=mode==='back';
 $('backMode').setAttribute('aria-pressed',String(mode==='back'));
 $('sourceMode').setAttribute('aria-pressed',String(mode==='sources'));
 $('leftCaption').textContent=mode==='back'?'SOURCE · normal backward':'SOURCE · normal forward';
 $('rightCaption').textContent=mode==='back'?'RESULT · woman-style backward':'SOURCE · woman forward';
 $('comparison').textContent=mode==='back'?'B + [W − N] with phase-mapped local quaternion differences':'Input difference: Walking → Walking_Woman';
}
function addMark(name,kind,error,rate,t,stats){
 if(!Number.isFinite(error))throw Error('AUDIT_NONFINITE '+name+' '+kind);
 const key=name+':'+kind,o=stats[key]??={bone:name,measurement:kind,count:0,sumSquares:0,max:0,worst:{t:0,rateHz:rate}};
 o.count++;o.sumSquares+=error*error;if(error>o.max){o.max=error;o.worst={t,rateHz:rate}}
}
function runAudit(exportNow=false){
 if(!ready)return;
 const wasPlaying=playing;playing=false;const previous=phase;
 const s={};const trials=[];let maxHipZ=0,sourceStyleCount=0,maxAngularStep=0,seamJump=0;
 try{
 for(const rate of [30,60,120]){
   let prior=null,maxStep=0,count=0;
   for(let i=0;i<Math.floor(sourceClips.Walk_Backward.duration*rate)*2;i++){
    const t=i/(2*rate),p=t/sourceClips.Walk_Backward.duration;if(p>=1)continue;
    const applied=applyStyle(p);const ref=rigs.Walk_Backward,gen=generatedRig;
    // Compare the styled root channel with the independently sampled
    // original backward clip, not with its own generated value.
    const originalInterpolated=sampleBone(samples.Walk_Backward,'mixamorigHips',p).pos[2];
    if(Math.abs(originalInterpolated-gen.mixamorigHips.position.z)>1e-8)throw Error('HIP_Z_LOCK_BROKEN');
    maxHipZ=Math.max(maxHipZ,Math.abs(gen.mixamorigHips.position.z-originalInterpolated));
    sourceStyleCount=Math.max(sourceStyleCount,applied.nonzeroBoneCount);
    const displayOffset=V(0,0,SEP);
    for(const [tag,bone] of [['left-ankle','mixamorigLeftFoot'],['right-ankle','mixamorigRightFoot'],['left-knee','mixamorigLeftLeg'],['right-knee','mixamorigRightLeg'],['hips','mixamorigHips'],['head','mixamorigHead']]){
     const source=world(ref[bone]).add(displayOffset),derived=world(gen[bone]);
     addMark(tag,'worldPosition',source.distanceTo(derived),rate,t,s);
    }
    const current=gen.mixamorigHips.quaternion.clone();
    if(prior)maxStep=Math.max(maxStep,THREE.MathUtils.radToDeg(prior.angleTo(current)));
    prior=current;count++;
   }
   maxAngularStep=Math.max(maxAngularStep,maxStep);trials.push({rateHz:rate,sampledPoses:count,pelvisMaxAngularStepDeg:maxStep});
 }
 const a=applyStyle(0),first=Object.fromEntries(Object.entries(a.bones).map(([k,v])=>[k,v.quat]));
 const b=applyStyle(1-1e-7);
 seamJump=Math.max(...Object.keys(first).map(k=>THREE.MathUtils.radToDeg(quatAngle(first[k],b.bones[k].quat))));
 const measured=Object.values(s).map(o=>({bone:o.bone,measurement:o.measurement,samples:o.count,rms:Math.sqrt(o.sumSquares/o.count),max:o.max,worst:o.worst}));
 measured.sort((a,b)=>b.rms-a.rms);
 const warnings=[];
 if(maxHipZ>1e-7)warnings.push('BACKWARD_PELVIS_Z_CHANGED');
 if(sourceStyleCount<10)warnings.push('STYLE_DELTA_MISSING');
 if(measured.filter(x=>x.bone.endsWith('ankle')).some(x=>x.rms>.11))warnings.push('POSSIBLE_FOOT_CONTACT_DRIFT');
 if(seamJump>8)warnings.push('CYCLE_SEAM_ANGLE_JUMP');
 const report={schema:'hareworks-three-clip-backward-style-v0.2.0',status:warnings.length?'MEASURED_WITH_WARNINGS_OWNER_REVIEW':'MEASURED_OWNER_REVIEW_REQUIRED',
  modelSha256:MODEL_SHA,threeSourceClips:CLIPS,sourceDurations:Object.fromEntries(CLIPS.map(k=>[k,sourceClips[k].duration])),
  comparison:'local delta = inverse(normal forward) * woman forward; generated = normal backward * delta',
  phaseMapping:'two-leg contact-event piecewise normalized phase warp; heuristic skinned witness anchors',anchors:CONTACT,
  styleGain:Number($('strength').value)/100,sourceBoneCount:74,calibrationSamplesPerClip:SAMPLES,
  generatedSourceAnimationTracks:0,rootBackwardDirectionPreserved:true,hipZDrift:maxHipZ,
  styleAffectedBones:sourceStyleCount,continuity:{rates:trials,maxHipAngularStepDeg:maxAngularStep,seamMaxBoneStepDeg:seamJump},
  measuredJointDifferences:measured,warnings,ownerAccepted:false};
 lastAudit=report;
 $('audit').textContent='AUDIT: '+report.status+' · 30/60/120Hz half-frame samples, '+sourceStyleCount+' nonzero style bones.\n'+
  measured.slice(0,7).map(r=>r.bone+' position RMS '+r.rms.toFixed(4)+' / max '+r.max.toFixed(4)).join('\n')+
  '\nCycle seam max joint change '+seamJump.toFixed(2)+'°; pelvis Z protection '+maxHipZ.toFixed(8)+' units.';
 say(warnings.length?'Backward style transfer measured with warnings; inspect derived gait and exported report.':'Three-way transfer measured; visual review required, not accepted automatically.');
 if(exportNow)download(report);
 }catch(e){say('BLOCKED_REAL_RIG_AUDIT '+e.message);console.error(e)}
 finally{phase=previous;try{applyStyle(phase)}catch(e){console.error(e)}playing=wasPlaying}
}
function download(obj){const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download='hareworks-backward-style-v0.2.0-evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000)}
$('auditButton').onclick=()=>runAudit(true);
$('export').onclick=()=>lastAudit?download(lastAudit):say('Run real-rig audit before exporting evidence.');
$('strength').oninput=()=>{$('strengthValue').textContent=$('strength').value+'%';if(ready){applyStyle(phase);say('Style gain changed; repeat the audit for this version of the motion.')}};
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play'};
$('phase').oninput=()=>{playing=false;$('play').textContent='Play';phase=Number($('phase').value)/1000;applyStyle(phase)};
$('backMode').onclick=()=>setMode('back');$('sourceMode').onclick=()=>setMode('sources');
function draw(now){requestAnimationFrame(draw);const dt=Math.min(.075,Math.max(0,(now-last)/1000));last=now;
 if(ready){if(playing){phase=(phase+dt/sourceClips.Walk_Backward.duration)%1;try{applyStyle(phase)}catch(e){playing=false;say('POSE_ERROR '+e.message);console.error(e)}}
 $('phase').value=Math.round(phase*1000)}orbit.update();renderer.render(scene,camera)}
requestAnimationFrame(draw);
function showError(e){say('SOURCE_OR_RIG_ERROR '+(e?.message||String(e)));console.error(e)}
window.addEventListener('unhandledrejection',e=>showError(e.reason));
try{
 const r=await fetch(MODEL_URL,{cache:'no-store'});if(!r.ok)throw Error('GLB_HTTP_'+r.status);
 const buffer=await r.arrayBuffer();if(buffer.byteLength!==6784896)throw Error('GLB_BYTE_COUNT_'+buffer.byteLength);
 if(!crypto?.subtle)throw Error('BROWSER_CRYPTO_SHA256_UNAVAILABLE');
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))).map(x=>x.toString(16).padStart(2,'0')).join('');
 if(digest!==MODEL_SHA)throw Error('SOURCE_GLB_SHA_MISMATCH '+digest);
 const gltf=await new GLTFLoader().parseAsync(buffer,new URL('../../../assets/hareworks/',import.meta.url).href);
 if(gltf.animations.length!==9)throw Error('EXPECTED_NINE_SOURCE_CLIPS');
 for(const key of CLIPS){const clip=gltf.animations.find(x=>x.name===key);if(!clip)throw Error('SOURCE_CLIP_MISSING_'+key);sourceClips[key]=clip;scenes[key]=cloneSkeleton(gltf.scene);scene.add(scenes[key]);rigs[key]=rigOf(scenes[key]);
   mixers[key]=new THREE.AnimationMixer(scenes[key]);mixers[key].clipAction(clip).reset().play();mixers[key].setTime(0);
 }
 generated=cloneSkeleton(gltf.scene);generatedRig=rigOf(generated);scene.add(generated);
 for(const key of CLIPS){samples[key]=makeClipSample(key);if(Object.keys(samples[key].bones).join('|')!==Object.keys(samples.Walking?.bones||samples[key].bones).join('|'))throw Error('SOURCE_BONE_TOPOLOGY_MISMATCH')}
 // Return all models to pristine source time zero before generated runtime.
 for(const key of CLIPS)mixers[key].setTime(0);
 scenes.Walk_Backward.position.z=-SEP/2;scenes.Walking.position.z=-SEP/2;
 scenes.Walking_Woman.position.z=SEP/2;generated.position.z=SEP/2;
 const check=transferPose(samples,.33,1),baseline=transferPose(samples,.33,0);
 if(check.nonzeroBoneCount<10||quatAngle(check.bones.mixamorigSpine.quat,baseline.bones.mixamorigSpine.quat)<.002)throw Error('THREE_WAY_STYLE_DELTA_NOT_APPLIED');
 sourceInfo={styleBoneCount:check.nonzeroBoneCount,peakBone:check.peakBone,peakDeltaDeg:THREE.MathUtils.radToDeg(check.peakDeltaRad),modelSha256:MODEL_SHA};
 floor.position.y=new THREE.Box3().setFromObject(scenes.Walk_Backward).min.y;
 ready=true;setMode('back');applyStyle(0);
 $('identity').textContent=`v0.2.0 · source SHA ${MODEL_SHA.slice(0,12)} · three-clips sampled ${SAMPLES} phases · generated no clip mixer · repo ${new URLSearchParams(location.search).get('commit')?.slice(0,10)||'Termux readback pending'} · script ${new URLSearchParams(location.search).get('scriptSha')?.slice(0,12)||'unknown'}`;
 $('audit').textContent=`THREE-WAY SOURCE READY: ${check.nonzeroBoneCount} bones differ between normal and woman forward; strongest local delta ${check.peakBone} (${sourceInfo.peakDeltaDeg.toFixed(1)}°). Derived backward uses all these differences.`;
 say('SKINNED MODEL VERIFIED · Walking vs Walking_Woman style → Walk_Backward; actual derived gait playing, needs visual acceptance.');
 resize();cameraAt('side');runAudit(false);
}catch(e){showError(e)}
__HAREWORKS_BACKWARD_V020_VIEWER_MJS__
fi
if ((PUBLISHED==0));then
cat > "$DIR/transfer-kernel.mjs" <<'__HAREWORKS_BACKWARD_V020_TRANSFER_KERNEL_MJS__'
/* Hareworks v0.2.0. Source-calibrated three-clip directional style transfer.
 * NORMAL_FORWARD -> WOMAN_FORWARD provides local delta transforms.
 * NORMAL_BACKWARD is the destination pose. No reverse clip is ever substituted.
 * The clip-time axis is warped by source-measured contact-event anchors. */
const TAU=2*Math.PI;
export const CLIPS=['Walking','Walking_Woman','Walk_Backward'];
export const CONTACT={
  // Ground-near start times from exact source GLB's 61-sample v1.0.8
  // skinned-witness extraction; heuristic events, NOT verified force contacts.
  normal:{left:0.316667/1.033333,right:0.766667/1.033333},
  woman:{left:0.29/0.966667,right:0.821667/0.966667},
  backward:{left:0.173333/0.866667,right:0.635556/0.866667},
};
export const mod1=x=>((x%1)+1)%1;
function checkNum(x){if(!Number.isFinite(x))throw Error('NONFINITE_STYLE_INPUT');return x}
export function contactWarp(p,source,target){
 checkNum(p);const [a,b]=[source.left,source.right], [A,B]=[target.left,target.right];
 if(![a,b,A,B].every(x=>Number.isFinite(x)&&x>=0&&x<1)||!(a<b&&A<B))throw Error('BAD_CONTACT_ANCHORS');
 const phase=mod1(p),x=phase<a?phase+1:phase;
 const value=x<=b?A+(x-a)*(B-A)/(b-a):B+(x-b)*(A+1-B)/(a+1-b);
 return mod1(value);
}
export function phaseTriplet(backPhase){
 const backward=mod1(backPhase);
 const normal=contactWarp(backward,CONTACT.backward,CONTACT.normal);
 const woman=contactWarp(normal,CONTACT.normal,CONTACT.woman);
 return {backward,normal,woman};
}
export function quatNormalize(q){
 if(!Array.isArray(q)||q.length!==4||!q.every(Number.isFinite))throw Error('BAD_STYLE_QUAT');
 const n=Math.hypot(...q);if(n<1e-12)throw Error('ZERO_STYLE_QUAT');return q.map(v=>v/n);
}
export const quatConj=q=>[-q[0],-q[1],-q[2],q[3]];
export function quatMul(a,b){const [x,y,z,w]=a,[X,Y,Z,W]=b;
 return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z];}
export function quatSlerp(a0,b0,f){
 let a=quatNormalize(a0),b=quatNormalize(b0);checkNum(f);
 let dot=a.reduce((s,v,i)=>s+v*b[i],0);
 if(dot<0){b=b.map(x=>-x);dot=-dot}
 if(dot>0.9995)return quatNormalize(a.map((v,i)=>v+(b[i]-v)*f));
 const alpha=Math.acos(Math.max(-1,Math.min(1,dot))),sa=Math.sin(alpha);
 const wa=Math.sin((1-f)*alpha)/sa,wb=Math.sin(f*alpha)/sa;
 return quatNormalize(a.map((v,i)=>wa*v+wb*b[i]));
}
export function quatAngle(a0,b0){const a=quatNormalize(a0),b=quatNormalize(b0);let d=Math.abs(a.reduce((s,x,i)=>s+x*b[i],0));return 2*Math.acos(Math.min(1,Math.max(0,d)))}
function lerp3(a,b,t){return a.map((x,i)=>x+(b[i]-x)*t)}
function finite3(a){return Array.isArray(a)&&a.length===3&&a.every(Number.isFinite)}
export function sampleBone(clip,boneName,phase){
 const s=clip?.bones?.[boneName];if(!s)throw Error('MISSING_TRACK_BONE '+boneName);
 const n=clip.sampleCount;if(!Number.isInteger(n)||n<8||s.quat?.length!==n||s.pos?.length!==n)throw Error('CORRUPT_SOURCE_SAMPLE '+boneName);
 const scaled=mod1(phase)*n,i=Math.floor(scaled)%n,j=(i+1)%n,t=scaled-i;
 return {quat:quatSlerp(s.quat[i],s.quat[j],t),pos:lerp3(s.pos[i],s.pos[j],t)};
}
export function transferBone(back,normal,woman,strength,boneName){
 if(![back,normal,woman].every(x=>Array.isArray(x?.quat)&&finite3(x?.pos)))throw Error('TRANSFER_POSE_MISSING');
 checkNum(strength);if(strength<0||strength>1)throw Error('STYLE_GAIN_OUT_OF_RANGE');
 // Quaternion delta is in the bone's own parent-local coordinate space.
 // Correct noncommuting order: B * inverse(N) * W.
 const relative=quatNormalize(quatMul(quatConj(quatNormalize(normal.quat)),quatNormalize(woman.quat)));
 const weighted=quatSlerp([0,0,0,1],relative,strength);
 const quat=quatNormalize(quatMul(back.quat,weighted));
 const pos=back.pos.map((v,i)=>v+strength*(woman.pos[i]-normal.pos[i]));
 // Absolute forward/back locomotion is NEVER inherited from the forward clips.
 // Preserve the backward pelvis Z path; X sway and Y bounce may transfer.
 if(boneName==='mixamorigHips')pos[2]=back.pos[2];
 return {quat,pos,rotationDeltaRad:quatAngle([0,0,0,1],relative)};
}
export function transferPose(clips,backPhase,strength=1){
 const phases=phaseTriplet(backPhase);
 const backward=clips?.Walk_Backward,normal=clips?.Walking,woman=clips?.Walking_Woman;
 if(!backward||!normal||!woman)throw Error('THREE_SOURCE_CLIPS_REQUIRED');
 const bones={};let peakDelta=0,peakBone='',nonzero=0;
 const names=Object.keys(backward.bones);
 if(names.length!==74||Object.keys(normal.bones).length!==74||Object.keys(woman.bones).length!==74)throw Error('THREE_RIGS_MUST_HAVE_74_BONES');
 for(const name of names){
  const base=sampleBone(backward,name,phases.backward);
  const n=sampleBone(normal,name,phases.normal);
  const w=sampleBone(woman,name,phases.woman);
  const styled=transferBone(base,n,w,strength,name);
  bones[name]=styled;
  if(styled.rotationDeltaRad>1e-3){nonzero++}
  if(styled.rotationDeltaRad>peakDelta){peakDelta=styled.rotationDeltaRad;peakBone=name}
 }
 return {bones,phases,strength,peakBone,peakDeltaRad:peakDelta,nonzeroBoneCount:nonzero};
}
__HAREWORKS_BACKWARD_V020_TRANSFER_KERNEL_MJS__
fi
if ((PUBLISHED==0));then
cat > "$DIR/transfer-kernel-test.mjs" <<'__HAREWORKS_BACKWARD_V020_TRANSFER_KERNEL_TEST_MJS__'
import assert from 'node:assert/strict';
import {CLIPS,CONTACT,contactWarp,phaseTriplet,quatMul,quatConj,quatNormalize,quatSlerp,quatAngle,transferBone,transferPose,mod1} from './transfer-kernel.mjs';
const near=(a,b,eps=1e-7)=>Math.abs(a-b)<eps;
const axis=(a,deg)=>{const r=deg*Math.PI/360;return [a[0]*Math.sin(r),a[1]*Math.sin(r),a[2]*Math.sin(r),Math.cos(r)]};
assert.deepEqual(CLIPS,['Walking','Walking_Woman','Walk_Backward']);
for(const x of ['left','right']){
 const p=CONTACT.backward[x];const mapped=phaseTriplet(p);
 assert(near(mapped.normal,CONTACT.normal[x]),'normal contact event '+x);
 assert(near(mapped.woman,CONTACT.woman[x]),'woman contact event '+x);
}
for(let i=0,last=-Infinity;i<500;i++){
 const q=CONTACT.backward.left+i/500*(CONTACT.backward.left+1-CONTACT.backward.left);
 const out=contactWarp(q,CONTACT.backward,CONTACT.normal);
 let unwrapped=out;if(unwrapped<CONTACT.normal.left-1e-4)unwrapped+=1;
 assert(unwrapped>=last-1e-8,'monotone gait phase');last=unwrapped;
}
const I=[0,0,0,1],B=axis([0,0,1],24),N=axis([0,1,0],25),W=quatMul(N,axis([1,0,0],20));
const A={quat:B,pos:[2,3,-0.8]},D={quat:N,pos:[1,2,0.3]},F={quat:W,pos:[1.2,2.15,1.8]};
const p=transferBone(A,D,F,1,'mixamorigSpine');
assert(quatAngle(p.quat,quatMul(B,quatMul(quatConj(N),W)))<1e-6,'noncommuting B*inv(N)*W');
assert.deepEqual(p.pos.map(v=>Math.round(v*100)/100),[2.2,3.15,0.7]);
const h=transferBone(A,D,F,1,'mixamorigHips');assert.equal(h.pos[2],A.pos[2],'backward root travel preserved');
const z=transferBone(A,D,F,0,'mixamorigSpine');assert(quatAngle(z.quat,B)<1e-6&&z.pos.every((v,i)=>near(v,A.pos[i])));
const half=transferBone(A,D,F,.5,'mixamorigSpine');assert(near(quatAngle(B,half.quat),quatAngle(B,p.quat)/2,1e-5));
assert.throws(()=>transferBone(A,D,F,1.01,'mixamorigSpine'),/OUT_OF_RANGE/);
assert.throws(()=>quatNormalize([0,0,0,0]),/ZERO/);
assert(quatAngle(quatSlerp(I,axis([0,1,0],95),.5),axis([0,1,0],47.5))<1e-7);
for(let i=0;i<=100;i++)assert(near(mod1(i/100),mod1((i+100)/100)));
// Construct three 74-bone synthetic clip samples, including an animated source style.
const names=['mixamorigHips',...Array.from({length:73},(_,i)=>'Bone_'+i)];
function synthetic(style=0,base=0){const bones={};for(const name of names){
  const quat=[],pos=[];for(let i=0;i<80;i++){
   const q=i/80;quat.push(quatMul(axis([0,0,1],base+8*Math.sin(2*Math.PI*q)),axis([1,0,0],style+5*Math.sin(2*Math.PI*q+style/90))));
   pos.push([.1*Math.sin(2*Math.PI*q),1+.02*Math.cos(2*Math.PI*q),-q*.4]);
  }bones[name]={quat,pos};}
  return {sampleCount:80,bones};}
const clips={Walk_Backward:synthetic(0,-20),Walking:synthetic(0,5),Walking_Woman:synthetic(9,5)};
const a=transferPose(clips,.32,0),b=transferPose(clips,.32,1);
assert.equal(Object.keys(a.bones).length,74);assert(a.nonzeroBoneCount>10);
assert(quatAngle(a.bones.Bone_0.quat,b.bones.Bone_0.quat)>.02,'style actually transfers');
assert.equal(a.bones.mixamorigHips.pos[2],b.bones.mixamorigHips.pos[2]);
const seam0=transferPose(clips,0,1),seam1=transferPose(clips,1-1e-10,1);
assert(quatAngle(seam0.bones.Bone_0.quat,seam1.bones.Bone_0.quat)<1e-6);
console.log('BACKWARD_STYLE_TRANSFER_TEST_PASS: 3-way local delta, contact anchors, noncommuting quaternion, pelvis Z lock, true derived pose, seam');
__HAREWORKS_BACKWARD_V020_TRANSFER_KERNEL_TEST_MJS__
fi
if ((PUBLISHED==0));then
cat > "$DIR/README.md" <<'__HAREWORKS_BACKWARD_V020_README_MD__'
# Hareworks three-clip backward Woman transfer v0.2.0

## Owner commission

The owner explicitly visually accepted **v0.1.9 generated forward `Walking_Woman`**, calling it a perfect match. Preserve it exactly, including the earlier v0.1.3 lower-body controller, v0.1.2 pelvis motion and v0.1.9 pelvis tilt improvement. This experiment creates **backward walking with a woman's style**, not an ordinary reproduction of the source `Walk_Backward` clip.

## Three-way construction

Verified actual source GLB `assets/hareworks/Hareworks-nine-clips.glb` (SHA256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`) contains exactly nine animation clips. Relevant clips: `Walking` (1.033333 s), `Walking_Woman` (0.966667 s), `Walk_Backward` (0.866667 s). Same 74-bone skeleton.

1. Sample all 74 joint local transforms in `Walking`, `Walking_Woman`, and `Walk_Backward` at 240 evenly spaced periodic phases per clip using the real GLB and Three.js AnimationMixers in the browser. The generated fourth character **has no mixer** and runs no source animation clip tracks after the one-time calibration.
2. For each backward phase, phase-align to forward-normal and woman-forward using piecewise affine warps between the **left/right ground-near contact candidates** identified in the exact-GLB v1.0.8 skinned witness extraction. These are heuristics, not measured forces. Raw timestamps or a simple reverse-phase assumption would not align stance between the different-length animations.
3. Calculate each joint's local rotation delta `inverse(Q_Walking) * Q_Walking_Woman`, and the local position delta `P_Walking_Woman - P_Walking` at the contact-aligned normalized phase.
4. Compose the new backward joint rotation as `Q_Walk_Backward * slerp(identity, delta, strength)`, and position as `P_Walk_Backward + strength * deltaPosition`. The **backward pelvis's local Z component is invariant**: no forward root travel is imported. Its hip X sway, hip Y bounce, and all 74 local rotations remain eligible for transferred style.
5. Use the generated model for backward comparison, with original `Walk_Backward` beside it. A source-pair toggle shows `Walking` alongside `Walking_Woman`, proving the upstream style relationship. A link returns to the immutable v0.1.9 forward viewer.

This is a true three-clip **source-calibrated local-bone delta transfer** in the same skeletal space, not an authored blend clip, a reversed woman's forward animation, or a general physics locomotion controller. It does not modify the original GLB or add another GLB. The generated pose is composed mathematically from sampled source data.

## Acceptance and safety

- First owner acceptance is the **v0.1.9 forward gait only**. A successful v0.2.0 Git commit or smooth numerical curve does NOT mean backward gait acceptance.
- Visual A/B original backward against generated transfer, plus source forward pair. Default style = 100%; 0% is explicitly a negative-control baseline, never a purported female backward gait.
- Retain original backward foot orientation and pelvis backward Z, measure joint-position deviations from the source and continuity at 30/60/120 Hz with half-frame samples and near-cycle seam. Identify possible foot-contact distortion as review warnings, not a silent switch to the unstyled clip.
- Source clips have different periods, and near-ground witness windows are heuristic. The phased style delta may not satisfy new barefoot contact constraints until the owner reviews the result. Do not claim contact dynamics proven by a hip/channel test.
- Abort source load on a missing clip, unexpected 74-joint topology, wrong source GLB hash, corrupt calibration, wrong source-pair identity, or no measurable woman-vs-normal style difference.
- Do not overwrite any historical path. The uniquely versioned Termux campaign publishes only seven text files, verifies the Git remote commit and blob readback, hosts a no-cache viewer with a fresh port, and prints its complete localhost URL and persistent receipt. The actual Android browser is the real-rig execution authority; host tests are not that evidence.

## User control and next iteration

Use side, front, overhead and oblique orbit views, `Backward` and `Forward sources` modes, motion strength slider and per-timestamp scrubber. Run audit and export the JSON. Judge foot planting, backwards travel, feminine weight transfer, arms/torso integration, and smooth cycle boundary before approving. If a style candidate produces an implausible foot movement, revise the style-transfer contact weights or phase mapping, **not** the accepted v0.1.9 forward gait.
__HAREWORKS_BACKWARD_V020_README_MD__
fi
if ((PUBLISHED==0));then
cat > "$DIR/contract.json" <<'__HAREWORKS_BACKWARD_V020_CONTRACT_JSON__'
{
  "campaign": "hareworks-backward-style-transfer-v0.2.0",
  "repository": "Valar05/parametric-parambulator",
  "modelPath": "assets/hareworks/Hareworks-nine-clips.glb",
  "modelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "modelBytes": 6784896,
  "sourceClips": ["Walking", "Walking_Woman", "Walk_Backward"],
  "sourceDurationsSeconds": [1.033333, 0.966667, 0.866667],
  "sourceRigBoneCount": 74,
  "phaseAlignment": "two-event contact-marker piecewise phase warp from exact GLB extraction, heuristic",
  "formula": "q_new_backward = q_backward * slerp(I, inverse(q_normal_forward) * q_woman_forward, strength)",
  "positionFormula": "p_new_backward = p_backward + strength * (p_woman_forward - p_normal_forward)",
  "protectedTranslation": "mixamorigHips.position.z is always sampled from Walk_Backward; no forward travel transplant",
  "acceptedForward": "v0.1.9 visually owner-approved, completely unchanged",
  "mutatedModel": false,
  "createdNewGLB": false,
  "generatedClipPlayback": false,
  "executionLane": "Android Termux Git ONLY",
  "requiredRealRigReview": "30/60/120Hz and half-frames, nonzero style signature, joint deviations and cyclic continuity, backwards foot contact visual owner acceptance",
  "newFiles": [
    "tools/hareworks-forward-woman/v0.2.0/index.html",
    "tools/hareworks-forward-woman/v0.2.0/viewer.mjs",
    "tools/hareworks-forward-woman/v0.2.0/transfer-kernel.mjs",
    "tools/hareworks-forward-woman/v0.2.0/transfer-kernel-test.mjs",
    "tools/hareworks-forward-woman/v0.2.0/README.md",
    "tools/hareworks-forward-woman/v0.2.0/contract.json",
    "campaigns/hareworks-backward-style-transfer-v0.2.0.sh"
  ],
  "ownerAcceptedBackward": false
}
__HAREWORKS_BACKWARD_V020_CONTRACT_JSON__
fi
if ((PUBLISHED==0));then
 cp -- "$0" "campaigns/$CAMPAIGN.sh" || fail 'cannot embed executed entrypoint'
fi
phase=payload-hashes
[[ "$(hash "$DIR/index.html")" == "1851d719f30d0b74e2523029eb5eea1157c309a66c04844f7f6dbba83feba798" ]] || fail 'payload sha mismatch: index.html' 
[[ "$(hash "$DIR/viewer.mjs")" == "e8b6a13f4ab69c24245bdfcf7d0213e725d24eb7ce0a2c763f6c9dd86e401bc9" ]] || fail 'payload sha mismatch: viewer.mjs' 
[[ "$(hash "$DIR/transfer-kernel.mjs")" == "f5f9fda21d58ab43687782d883913f399cce47cc6745fd91f8e62c9d2982485a" ]] || fail 'payload sha mismatch: transfer-kernel.mjs' 
[[ "$(hash "$DIR/transfer-kernel-test.mjs")" == "b51c55ffc4a9418dcf664990c7f3f9bf0fa9e9587eb6015583b76ba30fd583e3" ]] || fail 'payload sha mismatch: transfer-kernel-test.mjs' 
[[ "$(hash "$DIR/README.md")" == "b7de1f394543a492e16ed684db8000a4fd719119944ea8b334848e5c32b12666" ]] || fail 'payload sha mismatch: README.md' 
[[ "$(hash "$DIR/contract.json")" == "e3640100c29eaa6a644f74c330d20658fa3f74cf6194ca26e9b06c9bc758cd23" ]] || fail 'payload sha mismatch: contract.json' 
[[ "$(hash "campaigns/$CAMPAIGN.sh")" == "$SELF_SHA" ]] || fail 'published entrypoint not identical to downloaded script'
phase=static-tests
node --check "$DIR/viewer.mjs" || fail 'viewer JS syntax'
node --check "$DIR/transfer-kernel.mjs" || fail 'transfer JS syntax'
node --check "$DIR/transfer-kernel-test.mjs" || fail 'transfer tests JS syntax'
node "$DIR/transfer-kernel-test.mjs" | tee "$STATE/transfer-kernel-tests.log" || fail 'three-way transfer unit or injection test failure'
node tools/hareworks-forward-woman/v0.1.9/pelvis-tilt-test.mjs > "$STATE/forward-pelvis-regression.log" || fail 'accepted forward pelvis test failed'
node tools/hareworks-forward-woman/v0.1.9/upper-anchor-test.mjs > "$STATE/forward-upper-regression.log" || fail 'accepted upper source anchor test failed'
node tools/hareworks-forward-woman/v0.1.3/foot-kernel-test.mjs > "$STATE/forward-leg-regression.log" || fail 'accepted leg regression test failed'
node tools/hareworks-forward-woman/v0.1.2/pose-kernel-test.mjs > "$STATE/forward-hip-regression.log" || fail 'accepted pelvis regression test failed'
python3 - "$DIR" "$MODEL_SHA" <<'PY_DEPENDENCIES' || fail 'web import and exact clip provenance contract failed'
import pathlib,sys,re,json
folder,expected=sys.argv[1:];p=pathlib.Path(folder)
viewer=(p/'viewer.mjs').read_text();html=(p/'index.html').read_text();contract=json.loads((p/'contract.json').read_text())
assert expected in viewer and expected==contract['modelSha256']
assert contract['sourceClips']==['Walking','Walking_Woman','Walk_Backward']
assert 'generated=cloneSkeleton(gltf.scene)' in viewer and 'transferPose(samples,at,gain)' in viewer
assert 'generatedSourceAnimationTracks' not in viewer or 'no clip' in viewer.lower()
assert 'runAudit(false)' in viewer
assert 'id="backMode"' in html and 'id="sourceMode"' in html and 'id="auditButton"' in html
assert 'href="../v0.1.9/index.html"' in html
for rel in re.findall(r"from\s+'(\.[^']+)'",viewer):
 assert (p/rel).resolve(strict=True).is_file(),rel
assert (p/'transfer-kernel-test.mjs').is_file()
print('THREE_SOURCE_BROWSER_DEPENDENCIES=PASS')
PY_DEPENDENCIES
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.9/viewer.mjs)" == "$ACCEPTED_FORWARD_VIEWER_BLOB" ]] || fail 'accepted forward source changed during payload build'
if ((PUBLISHED==0));then
 phase=scoped-stage
 [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote advanced before commit; no merge or force push'
 git add -- "${FILES[@]}" || fail 'scoped git stage failed'
 python3 - "${FILES[@]}" <<'PY_STAGE' || fail 'staged files extend beyond scoped new seven text paths'
import subprocess,sys
expected=set(sys.argv[1:]);actual=set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines())
assert expected==actual,{'missing':sorted(expected-actual),'additional':sorted(actual-expected)}
assert all(not p.endswith('.glb') for p in actual)
print('ONLY_SEVEN_NEW_CAMPAIGN_TEXT_FILES_STAGED=PASS')
PY_STAGE
 for protected in AGENTS.md "$MODEL" assets/repl/Repl.glb tools/hareworks-forward-woman/v0.1.9/viewer.mjs tools/hareworks-forward-woman/v0.1.9/pelvis-tilt.mjs tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs;do
  git diff --quiet -- "$protected" || fail "protected path was modified: $protected"
  [[ "$(git rev-parse "HEAD:$protected")" == "$(git rev-parse "$BASE:$protected")" ]] || fail "protected historical commit changed: $protected"
 done
 phase=commit
 git -c user.name='Hareworks Termux Campaign' -c user.email='hareworks-campaign@users.noreply.github.com' commit -m 'Three-clip backward woman style transfer from forward gait deltas v0.2.0' || fail 'scoped Git commit failed'
 COMMIT=$(git rev-parse HEAD)
 [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'commit parent differs from pinned audited source'
 phase=publish
 [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote changed after staging; never force push'
 GIT_LFS_SKIP_PUSH=1 git push origin HEAD:refs/heads/main || fail "Git push failed; isolated source commit preserved=$COMMIT"
else
 COMMIT="$REMOTE"
fi
phase=remote-readback
[[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$COMMIT" ]] || fail 'remote main does not equal exact campaign commit'
GIT_LFS_SKIP_SMUDGE=1 git fetch --depth=1 origin main || fail 'remote readback fetch unavailable'
[[ "$(git rev-parse FETCH_HEAD)" == "$COMMIT" ]] || fail 'remote fetched branch not equal published commit'
for path in "${FILES[@]}";do
 [[ "$(git rev-parse "FETCH_HEAD:$path")" == "$(git rev-parse "HEAD:$path")" ]] || fail "remote verified byte mismatch: $path"
done
for path in AGENTS.md "$MODEL" tools/hareworks-forward-woman/v0.1.9/viewer.mjs tools/hareworks-forward-woman/v0.1.9/pelvis-tilt.mjs tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs;do
 [[ "$(git rev-parse "FETCH_HEAD:$path")" == "$(git rev-parse "$BASE:$path")" ]] || fail "protected remote file unexpectedly changed: $path"
done
echo "EXACT_GIT_REMOTE_READBACK=PASS $COMMIT"
phase=viewer-snapshot
# Only this isolated HTTP snapshot gets materialized binary model bytes.
# Git canonical path remains an unmodified LFS pointer in its commit.
cp -- "$SOURCE" "$MODEL" || fail 'HTTP snapshot could not materialize verified source GLB'
[[ "$(hash "$MODEL")" == "$MODEL_SHA" ]] || fail 'HTTP model byte parity mismatch'
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
[[ "$PORT" =~ ^[0-9]+$ ]] && kill -0 "$PID" 2>/dev/null || fail 'fresh HTTP server process not alive'
python3 - "http://127.0.0.1:$PORT" "$DIR" "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" "$STATE/http-manifest.json" <<'PY_HTTP' || fail 'runtime actual HTTP imported resources or GLB invalid'
import hashlib,json,pathlib,re,sys,urllib.parse,urllib.request
origin,folder,model,sha,size,out=sys.argv[1:];size=int(size)
def fetch(url):
 with urllib.request.urlopen(url,timeout=45) as r:
  data=r.read();headers=dict(r.headers)
 return data,headers
root=origin+'/'+folder+'/'
viewer,h=fetch(root+'viewer.mjs');viewer=viewer.decode()
html,headers=fetch(root+'index.html');html=html.decode()
assert 'no-store' in headers.get('Cache-Control','')
assert 'id="sourceMode"' in html and 'id="backMode"' in html and 'src="./viewer.mjs"' in html
assert 'transferPose(samples,at,gain)' in viewer and 'sampleBone(samples.Walk_Backward' in viewer
modules=[root+'viewer.mjs',root+'index.html',root+'transfer-kernel.mjs',root+'transfer-kernel-test.mjs',root+'README.md',root+'contract.json',origin+'/tools/hareworks-forward-woman/v0.1.9/index.html']
modules += [urllib.parse.urljoin(root+'viewer.mjs',x) for x in re.findall(r"from\s+'(\.[^']+)'",viewer)]
for url in modules:
 data,meta=fetch(url)
 assert data,('resource empty',url)
 assert 'no-store' in meta.get('Cache-Control',''),('cache policy',url)
data,modelHeaders=fetch(origin+'/'+model)
assert len(data)==size and hashlib.sha256(data).hexdigest()==sha
assert 'no-store' in modelHeaders.get('Cache-Control','')
pathlib.Path(out).write_text(json.dumps({'state':'HTTP_ASSETS_VERIFIED_ACTUAL_BROWSER_PENDING','resources':modules,'GLB_SHA256':sha,'GLBBytes':len(data),'indexResponseHeaders':headers},indent=2))
print('FRESH_HTTP_EXACT_GLB_AND_THREE_WAY_DEPENDENCIES=PASS')
PY_HTTP
curl -fsSI --max-time 5 "http://127.0.0.1:$PORT/$DIR/index.html" > "$STATE/http-headers.txt" || fail 'fresh HTTP headers unavailable'
URL="http://127.0.0.1:$PORT/$DIR/index.html?commit=$COMMIT&scriptSha=$SELF_SHA&modelSha=$MODEL_SHA"
python3 - "$STATE/receipt.json" "$CAMPAIGN" "$BASE" "$COMMIT" "$SELF_SHA" "$MODEL_SHA" "$AGENTS_BLOB" "$URL" "$PID" "$PORT" "$ROOT" <<'PY_RECEIPT'
import json,sys,datetime,pathlib
path,campaign,parent,commit,entry,model,agents,url,pid,port,snapshot=sys.argv[1:]
report={'campaign':campaign,'state':'GIT_PUBLISHED_HTTP_VERIFIED_ACTUAL_BROWSER_PENDING',
'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
'auditedParentCommit':parent,'publishedCommit':commit,'entrypointSha256':entry,'sourceModelSha256':model,'sourceClips':['Walking','Walking_Woman','Walk_Backward'],
'acceptedForwardGait':'v0.1.9 owner-approved and unmodified','rootAgentsGitBlob':agents,
'rulesRead':{'agents':'live GitHub AGENTS freshly read and exact Git blob verified','campaignEtiquette':'Home Center 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI','topDownEtiquette':'Home Center 1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'},
'algorithm':'backward * inverse(normal forward) * woman forward, source-phase-contact mapped',
'backwardRootPelvisZProtected':True,'newGLBAuthored':False,'generatedClipPlayback':False,
'viewerUrl':url,'viewerPid':int(pid),'viewerPort':int(port),'snapshot':snapshot,
'hostKernelTestsPassed':True,'HTTPActualAssetsVerified':True,'actualSkinnedBrowserVerified':False,'ownerAcceptedBackward':False,
'executionLane':'owner-operated Android Termux Git only'}
pathlib.Path(path).write_text(json.dumps(report,indent=2))
PY_RECEIPT
echo "REMOTE_COMMIT=$COMMIT"
echo "VIEWER_URL=$URL"
echo "VIEWER_PORT=$PORT VIEWER_PID=$PID"
echo "MODEL_SHA256=$MODEL_SHA"
echo "THREE_SOURCE_CLIPS=Walking,Walking_Woman,Walk_Backward"
echo "STYLE_TRANSFER=B_back * inverse(N_forward) * W_forward"
echo "HTTP_MANIFEST=$STATE/http-manifest.json"
echo "RECEIPT=$STATE/receipt.json"
echo 'BACKWARD_GAIT_BROWSER_ACCEPTANCE=PENDING; ACCEPTED_FORWARD_V0.1.9=UNCHANGED'
if command -v termux-open-url >/dev/null;then
 termux-open-url "$URL" || echo "OPEN_REQUEST_FAILED; VIEWER_URL=$URL"
else
 echo "TERMUX_OPEN_URL_UNAVAILABLE; VIEWER_URL=$URL"
fi
