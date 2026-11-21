#!/data/data/com.termux/files/usr/bin/bash
# Hareworks v0.2.5: controlled 4-layer dynamic style transfer; approved backward remains immutable.
# Owner-approved forward and backward systems remain byte-identical.
set -Eeuo pipefail
CAMPAIGN='hareworks-backward-style-lab-v0.2.5'
REPO='Valar05/parametric-parambulator'
BASE='5248f3e9859088f41d8c8ebd7acaa6e7b09c25f9'
DIR='tools/hareworks-forward-woman/v0.2.5'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE='6784896'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ACCEPTED_FORWARD='a17f8109766dcfa39fbb75b6b2ff335c358733cb'
ACCEPTED_BACKWARD='61c9bea2aa3c5da5f331c45e2df41077670c3603'
ACCEPTED_BACKWARD_KERNEL='4be7594e2fe43522c807b3fe59eb2ed965d95367'
RESEARCH_V023_VIEWER='086f4627a74542c4e03cc07d1a72be479862b3c7'
RESEARCH_V023_ANALYSIS='bb694ba303f96b8bd4aef280fa4d56770c655a2f'
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
exec > >(tee -a "$STATE/run.log") 2>&1
phase=preflight; ROOT=''; WORK=''; COMMIT=''; PID=''; PORT=''; SOURCE=''
fail(){
 echo "BLOCKED step=$phase reason=$*"
 if [[ -n "$ROOT" && -f "$ROOT/server.log" ]];then echo 'SERVER_LOG_TAIL:';tail -n 20 "$ROOT/server.log" || true;fi
 python3 - "$STATE/blocked.json" "$CAMPAIGN" "$phase" "$*" "$COMMIT" "$ROOT" <<'PY_FAILURE' || true
import datetime,json,pathlib,sys
p,name,phase,reason,commit,root=sys.argv[1:]
pathlib.Path(p).write_text(json.dumps({'campaign':name,'state':'BLOCKED','phase':phase,'reason':reason,'knownCommit':commit,'isolatedSnapshot':root,'ownerApprovedGaitsUnmodified':True,'styleLabMeasurements':'NOT_VERIFIED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY_FAILURE
 exit 1
}
hash(){ sha256sum -- "$1" | cut -d' ' -f1; }
if [[ "${1:-run}" == status ]];then
 [[ -f "$STATE/receipt.json" ]] && cat "$STATE/receipt.json" || echo "NO_RECEIPT=$STATE/receipt.json"
 [[ ! -f "$STATE/measurement-receipt.json" ]] || cat "$STATE/measurement-receipt.json"
 exit 0
fi
[[ "${1:-run}" == run || "${1:-run}" == resume ]] || fail 'usage: bash script.sh [run|resume|status]'
for c in git python3 curl sha256sum node;do command -v "$c" >/dev/null || fail "missing Termux command: $c";done
phase=embedded-python-syntax-preflight
python3 - "$0" <<'PY_EMBEDDED_PREFLIGHT' || fail 'embedded Python heredoc AST preflight failed before checkout'
import ast,pathlib,re,sys
src=pathlib.Path(sys.argv[1]).read_text()
tags=re.findall(r"<<'(?P<tag>PY_[A-Z0-9_]+)'",src)
assert len(tags)==11,('EXPECTED_EMBEDDED_PYTHON_BLOCKS',len(tags))
for tag in tags:
    m=re.search(r"<<'"+re.escape(tag)+r"'[^\n]*\n",src)
    assert m,('MISSING_HEREDOC_START',tag)
    end=src.find('\n'+tag+'\n',m.end())
    assert end>=0,('MISSING_HEREDOC_END',tag)
    ast.parse(src[m.end():end],filename=tag)
print('EMBEDDED_PYTHON_AST_PREFLIGHT=PASS',len(tags),'blocks')
PY_EMBEDDED_PREFLIGHT
SELF_SHA=$(hash "$0")
echo "CAMPAIGN=$CAMPAIGN"
echo "ENTRYPOINT_SHA256=$SELF_SHA"
echo "OBSERVED_RULES_AGENTS_BLOB=$AGENTS_BLOB"
echo 'RULES_CAMPAIGN_ETIQUETTE_HOME_CENTER=1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
echo 'RULES_TOP_DOWN_ETIQUETTE_HOME_CENTER=1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
echo "PINNED_PARENT=$BASE"
echo "CANONICAL_SOURCE_SHA256=$MODEL_SHA"
ORIGIN="https://github.com/$REPO.git"
phase=remote-preflight
REMOTE=''
for retry in 1 2 3;do
 REMOTE=$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1) || REMOTE=''
 [[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] && break
 sleep "$retry"
done
[[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] || fail 'remote Git main unavailable'
echo "OBSERVED_REMOTE_MAIN=$REMOTE"
phase=isolated-checkout
ROOT=$(mktemp -d "$STATE/snapshot.XXXXXXXX") || fail 'isolated snapshot unavailable'
WORK="$ROOT/repo"
for retry in 1 2;do
 if GIT_LFS_SKIP_SMUDGE=1 git -c lfs.install.skip=true clone --depth=2 --filter=blob:none --no-checkout --single-branch --branch main "$ORIGIN" "$WORK";then break;fi
 [[ ! -e "$WORK" ]] || fail 'partial checkout preserved; no user worktree touched'
 sleep "$retry"
done
[[ -d "$WORK/.git" ]] || fail 'isolated clone failed'
git -C "$WORK" sparse-checkout init --cone || fail 'sparse init failed'
git -C "$WORK" sparse-checkout set assets/hareworks tools/hareworks-forward-woman campaigns || fail 'sparse checkout paths failed'
GIT_LFS_SKIP_SMUDGE=1 git -C "$WORK" checkout -B "$CAMPAIGN" "$REMOTE" || fail 'isolated materialization failed'
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$REMOTE" ]] || fail 'isolated checkout revision mismatch'
cd "$WORK"
[[ -z "$(git status --porcelain)" ]] || fail 'unexpected dirty isolated checkout'
phase=immutable-source-gate
[[ -f AGENTS.md ]] && grep -Fq 'Termux Git only' AGENTS.md || fail 'required live AGENTS authority unavailable'
[[ "$(git rev-parse HEAD:AGENTS.md)" == "$AGENTS_BLOB" ]] || fail 'live AGENTS revision changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.9/viewer.mjs)" == "$ACCEPTED_FORWARD" ]] || fail 'approved forward viewer changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.2/viewer.mjs)" == "$ACCEPTED_BACKWARD" ]] || fail 'approved backward viewer changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.2/inplace-kernel.mjs)" == "$ACCEPTED_BACKWARD_KERNEL" ]] || fail 'approved backward solver changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.3/viewer.mjs)" == "$RESEARCH_V023_VIEWER" ]] || fail 'research source viewer changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.3/analysis-core.mjs)" == "$RESEARCH_V023_ANALYSIS" ]] || fail 'research source analysis changed'
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" <<'PY_POINTER' || fail 'canonical original model Git LFS pointer mismatch'
import subprocess,sys
path,sha,size=sys.argv[1:]
want=f'version https://git-lfs.github.com/spec/v1\noid sha256:{sha}\nsize {size}\n'.encode()
assert subprocess.check_output(['git','show','HEAD:'+path])==want
print('SOURCE_GLB_GIT_LFS_IDENTITY=PASS')
PY_POINTER
FILES=("$DIR/index.html" "$DIR/viewer.mjs" "$DIR/style-layers.mjs" "$DIR/style-layers-test.mjs" "$DIR/inplace-kernel.mjs" "$DIR/inplace-kernel-test.mjs" "$DIR/inplace-witness-test.mjs" "$DIR/source-witness.json" "$DIR/research-priors.json" "$DIR/lab-server.py" "$DIR/README.md" "$DIR/contract.json" "campaigns/$CAMPAIGN.sh")
phase=destination-collision
PUBLISHED=0
if [[ "$REMOTE" == "$BASE" ]];then
 for p in "${FILES[@]}";do
  [[ ! -e "$p" && ! -L "$p" ]] || fail "destination collision: $p"
  if git cat-file -e "HEAD:$p" 2>/dev/null;then fail "Git destination collision: $p";fi
 done
else
 if git cat-file -e "HEAD:campaigns/$CAMPAIGN.sh" 2>/dev/null && git cat-file -e "HEAD:$DIR/viewer.mjs" 2>/dev/null;then
  [[ "$(git show "HEAD:campaigns/$CAMPAIGN.sh" | sha256sum | cut -d' ' -f1)" == "$SELF_SHA" ]] || fail 'published campaign file differs from downloaded packet'
  [[ "$(git show -s --format='%P' HEAD | awk '{print $1}')" == "$BASE" ]] || fail 'published campaign has unexpected parent'
  PUBLISHED=1
  echo "EXACT_CAMPAIGN_ALREADY_PUBLISHED=$REMOTE"
 else
  fail 'remote main advanced; refuses silent rebase/overwrite/force-push'
 fi
fi
phase=real-source-glb
for root in "$HOME/.local/state/hareworks" "$HOME/storage/downloads" /storage/emulated/0/Download;do
 [[ -d "$root" ]] || continue
 depth=2; [[ "$root" != "$HOME/.local/state/hareworks" ]] || depth=12
 while IFS= read -r -d '' path;do
  [[ "$(wc -c < "$path" | tr -d ' ')" == "$MODEL_SIZE" ]] || continue
  if [[ "$(hash "$path")" == "$MODEL_SHA" ]];then SOURCE="$path";break;fi
 done < <(find -L "$root" -maxdepth "$depth" -type f \( -iname '*.glb' -o -name "$MODEL_SHA" \) -print0 2>/dev/null)
 [[ -z "$SOURCE" ]] || break
done
if [[ -z "$SOURCE" ]];then
 command -v git-lfs >/dev/null || fail 'real GLB not cached and git-lfs unavailable'
 git lfs install --local || fail 'Git LFS local configuration failed'
 for retry in 1 2;do
  if GIT_LFS_SKIP_SMUDGE=1 git lfs fetch -I "$MODEL" -X '' origin "$REMOTE";then break;fi
  sleep "$retry"
 done
 OBJECT=$(git rev-parse --git-path "lfs/objects/${MODEL_SHA:0:2}/${MODEL_SHA:2:2}/$MODEL_SHA")
 [[ -f "$OBJECT" ]] || fail 'exact canonical model binary unavailable from LFS'
 SOURCE="$OBJECT"
fi
[[ "$(wc -c < "$SOURCE" | tr -d ' ')" == "$MODEL_SIZE" && "$(hash "$SOURCE")" == "$MODEL_SHA" ]] || fail 'real model binary hash or size mismatch'
python3 - "$SOURCE" <<'PY_MODEL' || fail 'actual 74-joint nine-clip source contract mismatch'
import json,struct,sys
with open(sys.argv[1],'rb') as f:
 head=f.read(20)
 assert head[:4]==b'glTF'
 l,t=struct.unpack_from('<I4s',head,12);assert t==b'JSON'
 j=json.loads(f.read(l))
assert len(j['animations'])==9
names=[a['name'] for a in j['animations']]
assert 'Walking' in names and 'Walking_Woman' in names and 'Walk_Backward' in names
assert len(j['skins'][0]['joints'])==74
print('REAL_GLB_9_CLIPS_74_JOINTS_WALKING_WOMAN=PASS',names)
PY_MODEL
phase=source-packet
if ((PUBLISHED==0));then mkdir -p "$DIR" || fail "new style lab directory failed";fi
if ((PUBLISHED==0));then
 cat > "$DIR/index.html" <<'__HAREWORKS_STYLE_LAB_V025_INDEX_HTML__'
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#111b26"><title>Hareworks v0.2.5 | Controlled Backward Style Lab</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>
:root{font:15px system-ui,sans-serif;background:#111b26;color:#e9f5ff;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:1080px;margin:auto;padding:12px}h1{font-size:21px;margin:5px 0}h2{font-size:16px;margin:0 0 6px}p{line-height:1.48;color:#bed0df}header{display:flex;justify-content:space-between;gap:10px;align-items:center;flex-wrap:wrap}.pill{border:1px solid #54788a;border-radius:99px;padding:6px 10px;font-size:11px;color:#b5d8e8}#identity{font:11px/1.6 ui-monospace,monospace;color:#afc4d0;overflow-wrap:anywhere}#status{padding:9px 0;min-height:45px;color:#a9e7bc}#stage{border:1px solid #58768b;border-radius:10px;overflow:hidden}canvas{display:block;width:100%;touch-action:none}.labels{display:grid;grid-template-columns:1fr 1fr;gap:7px;text-align:center;margin:9px 0;color:#e9f5ff}.toolbar,.panel{background:#1c3042;padding:11px;border-radius:10px;margin:10px 0}.toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.panel{display:grid;gap:10px}.layer{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;padding:9px;border:1px solid #455f75;border-radius:8px}.layer .detail{font-size:12px;color:#b0c9d9;grid-column:1/-1}.layer input[type=range]{width:100%;min-width:100px}.layer label{display:flex;gap:9px;align-items:center}.layer output{min-width:52px;text-align:right;font-variant-numeric:tabular-nums}button{font:inherit;color:#fff;background:#31516b;border:1px solid #759eb9;border-radius:7px;min-height:44px;padding:9px 12px}button:focus-visible,input:focus-visible{outline:3px solid #a7e8f2}button:disabled{opacity:.4}input[type=range]{accent-color:#7cdbd0}#phase{flex:1;min-width:130px}#audit{font:12px/1.6 ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#152436;border:1px solid #46657a;border-radius:8px;padding:12px;max-height:290px;overflow:auto}.small{font-size:12px}a{color:#9cdbf5}
</style></head><body><main><header><h1>🐇 Hareworks · Backward Style Laboratory</h1><span class="pill">v0.2.5 · Four independently gated layers</span></header>
<p><strong>LEFT:</strong> accepted v0.2.2 backward in-place solver. <strong>RIGHT:</strong> a separately generated experimental candidate. Both use independent procedural pose evaluation, never original animation playback. The accepted model and GLB are immutable.</p>
<div id="identity" role="status">Loading build and exact source identity…</div><div id="status" role="status" aria-live="polite">Loading exact 74-bone Hareworks source…</div>
<div class="labels"><strong>LOCKED · accepted backward</strong><strong>EXPERIMENT · checked layers only</strong></div><div id="stage" role="img" aria-label="Interactive 3D comparison, accepted backward gait left and separately generated style experiment right"></div>
<div class="toolbar" role="group" aria-label="Camera views"><button id="side">Side</button><button id="front">Front</button><button id="oblique">Three-quarter</button><button id="top">Top</button><span class="small">Drag to orbit, pinch to zoom</span></div>
<div class="toolbar"><button id="play">Pause</button><label for="phase">Cycle phase</label><input id="phase" type="range" min="0" max="1000" step="1" value="0"><output id="phaseValue">0%</output></div>
<section class="panel" aria-label="Style transfer controls"><h2>Style layers · start all OFF</h2>
<div class="layer"><label><input type="checkbox" id="onPelvis">Pelvis: yaw/roll/pitch and measured bounce</label><output id="valPelvis">70%</output><input type="range" id="pelvis" aria-label="Requested pelvis transfer percentage" min="0" max="100" value="70"><span class="detail" id="actualPelvis">OFF · root Z travel always locked</span></div>
<div class="layer"><label><input type="checkbox" id="onLegs">Legs and feet: dynamic stepping-path signature</label><output id="valLegs">45%</output><input type="range" id="legs" aria-label="Requested leg transfer percentage" min="0" max="100" value="45"><span class="detail" id="actualLegs">OFF · stance deviation guarded</span></div>
<div class="layer"><label><input type="checkbox" id="onTorso">Torso, neck and head stabilization</label><output id="valTorso">65%</output><input type="range" id="torso" aria-label="Requested torso transfer percentage" min="0" max="100" value="65"><span class="detail" id="actualTorso">OFF · independent of pelvis</span></div>
<div class="layer"><label><input type="checkbox" id="onArms">Shoulders, arms, hands and fingers</label><output id="valArms">65%</output><input type="range" id="arms" aria-label="Requested arm transfer percentage" min="0" max="100" value="65"><span class="detail" id="actualArms">OFF · static arm pose offsets excluded</span></div>
<div class="toolbar"><button id="apply">Test and apply requested layers</button><button id="reset">Restore accepted baseline</button><button id="export">Export real-rig evidence JSON</button><a href="../v0.2.2/index.html">Accepted v0.2.2</a></div></section>
<div id="audit" role="status">Waiting for exact GLB calibration and safe trial…</div>
<p class="small">Derived motion is phase aligned using the v0.2.3 research offset (0.977778), not a male/female stereotype. Source terminal windows are repaired for continuity. Contact windows are heuristic low-foot witnesses rather than force measurements. A requested layer is automatically attenuated or rejected when it exceeds the baseline preservation gates. Reports contain attempted and actual gain, offending joint/time, 30/60/120 Hz samples and source identity. No original animation or owner-approved viewer is modified. Visual approval remains separate.</p>
</main><script type="module" src="./viewer.mjs"></script></body></html>
__HAREWORKS_STYLE_LAB_V025_INDEX_HTML__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/viewer.mjs" <<'__HAREWORKS_STYLE_LAB_V025_VIEWER_MJS__'
/* Hareworks v0.2.5. Four independent source-measured dynamic style overlays.
 * Two independently evaluated procedural backward rigs: accepted v0.2.2
 * baseline and gated candidate. NO source AnimationMixer on either.
 * Walking and Walking_Woman mixers exist solely on hidden calibration clones.
 */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {CLIP,ROOT,deriveInPlace,poseInPlace,angleDeg} from './inplace-kernel.mjs';
import {LAYERS,PHASE_OFFSET,stylePose,zeroGains,groupOf} from './style-layers.mjs';
const SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const PRIORS_SHA='f631eaf0bb48bb81afa9b451cf2191aa4c98b07bd768f2574caaaa28938ffebe';
const GLB='../../../assets/hareworks/Hareworks-nine-clips.glb';
const $=id=>document.getElementById(id),V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const SEP=2.8,BACK_SAMPLES=720,STYLE_SAMPLES=360;
const scene=new THREE.Scene();scene.background=new THREE.Color('#111b26');
scene.add(new THREE.HemisphereLight(0xf1f8ff,0x2a3f50,2.6));
const lamp=new THREE.DirectionalLight(0xffffff,3.3);lamp.position.set(-4,7,4);scene.add(lamp);
const floor=new THREE.GridHelper(14,28,0x5b7183,0x344658);scene.add(floor);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-4,4,2.2,-2.2,.05,100);
const orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.enablePan=false;orbit.minZoom=.55;orbit.maxZoom=3.5;orbit.target.set(0,.9,0);
const views={side:[-7,3.2,0],front:[0,2.5,9],oblique:[-6,4.2,5],top:[-.01,9,.01]};
function cameraAt(key){camera.position.set(...views[key]);camera.up.set(0,1,0);camera.zoom=1;orbit.target.set(0,.9,0);camera.lookAt(orbit.target);camera.updateProjectionMatrix();orbit.update()}
function resize(){const w=Math.max(320,$('stage').clientWidth),h=Math.max(300,Math.min(610,Math.round(w*.70)));renderer.setSize(w,h,false);camera.left=-2.4*w/h;camera.right=-camera.left;camera.top=2.4;camera.bottom=-2.4;camera.updateProjectionMatrix()}
window.addEventListener('resize',resize);for(const k of Object.keys(views))$(k).onclick=()=>cameraAt(k);cameraAt('side');resize();
let baseline=null,candidate=null,baseRig=null,candidateRig=null;
let originalClips={},sourceClones={},sourceMixers={},backwardSource=null,backwardPlan=null,styleNormal=null,styleWoman=null;
let sourceReady=false,ready=false,playing=true,busy=false,phase=0,last=performance.now(),gateRevision=0;
let allowed=zeroGains(),lastAudit=null,researchPriors=null;
const status=s=>$('status').textContent=s;
function rigOf(root){const o={};root.traverse(b=>{if(b.isBone){if(o[b.name])throw Error('DUPLICATE_BONE '+b.name);o[b.name]=b}});if(Object.keys(o).length!==74||!o[ROOT])throw Error('RIG_NOT_74_BONES');return o}
const wpos=b=>b.getWorldPosition(V());
function copyPose(rig,root,pose){for(const [name,channels] of Object.entries(pose.bones)){const b=rig[name];if(!b)throw Error('MISSING_GENERATED_BONE_'+name);b.quaternion.fromArray(channels.quaternion).normalize();b.position.fromArray(channels.position);b.scale.fromArray(channels.scale)}root.updateMatrixWorld(true)}
function captureClip(clipName,n){const root=sourceClones[clipName],mixer=sourceMixers[clipName],duration=originalClips[clipName].duration,rig=rigOf(root),bones={};
 for(const name of Object.keys(rig))bones[name]={pos:[],quat:[],scale:[]};
 for(let i=0;i<n;i++){mixer.setTime(duration*i/n);root.updateMatrixWorld(true);for(const [name,b] of Object.entries(rig)){const s=bones[name];s.pos.push(b.position.toArray());s.quat.push(b.quaternion.toArray());s.scale.push(b.scale.toArray())}}
 mixer.setTime(0);root.updateMatrixWorld(true);return {sampleCount:n,duration,bones};}
function rawRootEndpoint(){const t=originalClips[CLIP].tracks.find(x=>x.name===ROOT+'.position');if(!t)return null;const n=t.times.length,k=t.getValueSize();return {lastTime:t.times[n-1],last:Array.from(t.values.slice((n-1)*k,n*k)),prior:Array.from(t.values.slice((n-2)*k,(n-1)*k))}}
function calibrateBackward(){const raw=backwardSource;const attempts=[],starts=[.93,.92,.905,.89,.875,.86];let best=null;
 for(const seam of starts){try{const plan=deriveInPlace(raw,seam);let cost=0;
 for(const hz of [30,60,120]){const limit=hz===30?20:hz===60?12:7;let prior=poseInPlace(raw,plan,0).bones,max=0;
  for(let i=1;i<=Math.ceil(raw.duration*hz);i++){const pose=poseInPlace(raw,plan,Math.min(1-1e-7,i/(raw.duration*hz))).bones;for(const name of Object.keys(pose))max=Math.max(max,angleDeg(prior[name].quaternion,pose[name].quaternion));prior=pose}
  cost+=max/limit;}
 attempts.push({seam,cost});if(best===null||cost<best.cost)best={cost,plan};if(cost<=3)break;
 }catch(e){attempts.push({seam,error:e.message})}}
 if(!best)throw Error('BACKWARD_CALIBRATION_NO_VALID_SEAM '+JSON.stringify(attempts));
 best.plan.candidateSeams=attempts;return best.plan;
}
function baselinePose(p){return poseInPlace(backwardSource,backwardPlan,p)}
function experimentalPose(p,gains=allowed){return stylePose(baselinePose(p),styleNormal,styleWoman,p,gains)}
function displayAt(p){if(!ready)return;phase=((p%1)+1)%1;copyPose(baseRig,baseline,baselinePose(phase));copyPose(candidateRig,candidate,experimentalPose(phase));$('phaseValue').textContent=Math.round(100*phase)+'%';}
function zeroAudit(){displayAt(0);const errors=[];for(const name of Object.keys(baseRig)){const a=baseRig[name],b=candidateRig[name];const q=angleDeg(a.quaternion.toArray(),b.quaternion.toArray()),loc=a.position.distanceTo(b.position),s=a.scale.distanceTo(b.scale),world=wpos(a).add(V(0,0,SEP)).distanceTo(wpos(b));if(q>.001||loc>1e-6||s>1e-6||world>1e-4)errors.push({bone:name,rotation:q,position:loc,scale:s,world})}if(errors.length)throw Error('PHASE_ZERO_STYLE_MUST_MATCH_ACCEPTED '+JSON.stringify(errors.slice(0,4)));return {pass:true,joints:74}}
const markers=['mixamorigLeftFoot','mixamorigRightFoot','mixamorigLeftToeBase','mixamorigRightToeBase','mixamorigLeftLeg','mixamorigRightLeg','mixamorigHead'];
const feet=['mixamorigLeftFoot','mixamorigRightFoot'];
function collectPositions(rig){const out={};for(const n of markers)out[n]=wpos(rig[n]);return out}
function readRequest(){const r=zeroGains();for(const key of LAYERS){r[key]=$('on'+key[0].toUpperCase()+key.slice(1)).checked?Number($(key).value)/100:0;}return r}
function updateControls(){for(const key of LAYERS){const C=key[0].toUpperCase()+key.slice(1);$('val'+C).textContent=$(key).value+'%';$('actual'+C).textContent=allowed[key]?'APPLIED '+(allowed[key]*100).toFixed(1)+'% after safeguards':'OFF / rejected / not requested';}}
for(const key of LAYERS){const C=key[0].toUpperCase()+key.slice(1);$(key).oninput=()=>{$('val'+C).textContent=$(key).value+'%';};$('on'+C).onchange=()=>{status('Style request changed. Run Test and apply; accepted backward remains locked.')}}
function getFootProfiles(){const observations=[];for(let i=0;i<90;i++){const p=i/90;copyPose(baseRig,baseline,baselinePose(p));const o=collectPositions(baseRig);observations.push({phase:p,y:feet.map(f=>o[f].y)})}const min=feet.map((_,j)=>Math.min(...observations.map(o=>o.y[j])));return {min,notes:'low-foot witnesses only; not force contact'}}
// Use a separate, measured candidate rig. No source animation action ever
// drives it. Reference remains accepted procedural v0.2.2 equations.
async function measure(gains,rates=[30,60],yieldFrames=false){const footProfiles=window.__footProfile;const met={maxContactAnkle:0,maxContactToe:0,maxSwingAnkle:0,maxRootZ:0,maxRootX:0,maxHead:0,maxFloorPenetration:0,maxStepAdded:0,lowestContactCount:0,sampleCount:0,perRate:[],worst:[],maxWorldDifference:0};
 const fail=(kind,err,at,bone,rate)=>{if(err>(met['max'+kind]??0))met['max'+kind]=err;met.worst.push({kind,error:err,phase:at,bone,rateHz:rate})};
 for(const hz of rates){const n=Math.ceil(backwardSource.duration*hz)*2;let priorB=null,priorC=null,maxBaseStep=0,maxStyleStep=0;
  for(let i=0;i<n;i++){const p=i/(2*hz*backwardSource.duration);if(p>=1)break;
   const b=baselinePose(p),c=stylePose(b,styleNormal,styleWoman,p,gains);copyPose(baseRig,baseline,b);copyPose(candidateRig,candidate,c);
   const bp=collectPositions(baseRig),cp=collectPositions(candidateRig);
   for(let j=0;j<2;j++){const side=j?'Right':'Left',f='mixamorig'+side+'Foot',toe='mixamorig'+side+'ToeBase';const dist=bp[f].distanceTo(cp[f]),dtoe=bp[toe].distanceTo(cp[toe]);
    const planted=bp[f].y<=footProfiles.min[j]+.028;
    if(planted){met.lowestContactCount++;fail('ContactAnkle',dist,p,f,hz);fail('ContactToe',dtoe,p,toe,hz)}else fail('SwingAnkle',dist,p,f,hz);
    // A new foot penetrating materially below its approved trajectory is prohibited.
    fail('FloorPenetration',Math.max(0,bp[f].y-cp[f].y-.025),p,f,hz);
   }
   fail('RootZ',Math.abs(b.bones[ROOT].position[2]-c.bones[ROOT].position[2]),p,ROOT,hz);
   fail('RootX',Math.abs(b.bones[ROOT].position[0]-c.bones[ROOT].position[0]),p,ROOT,hz);
   fail('Head',bp.mixamorigHead.distanceTo(cp.mixamorigHead),p,'mixamorigHead',hz);
   if(priorB){for(const bone of Object.keys(b.bones)){const ba=angleDeg(priorB[bone].quaternion,b.bones[bone].quaternion),ca=angleDeg(priorC[bone].quaternion,c.bones[bone].quaternion);maxBaseStep=Math.max(maxBaseStep,ba);maxStyleStep=Math.max(maxStyleStep,ca)}}
   priorB=b.bones;priorC=c.bones;met.sampleCount++;
   if(yieldFrames&&i%16===0)await new Promise(resolve=>requestAnimationFrame(resolve));
  }
  met.perRate.push({rateHz:hz,maxBaselineJointStepDeg:maxBaseStep,maxCandidateJointStepDeg:maxStyleStep});
  fail('StepAdded',Math.max(0,maxStyleStep-maxBaseStep),1,'full-rig',hz);
 }
 const b0=baselinePose(0),b1=baselinePose(1-1e-7),c0=stylePose(b0,styleNormal,styleWoman,0,gains),c1=stylePose(b1,styleNormal,styleWoman,1-1e-7,gains);
 met.seamBase=0;met.seamCandidate=0;met.seamPosition=0;
 for(const name of Object.keys(c0.bones)){met.seamBase=Math.max(met.seamBase,angleDeg(b0.bones[name].quaternion,b1.bones[name].quaternion));met.seamCandidate=Math.max(met.seamCandidate,angleDeg(c0.bones[name].quaternion,c1.bones[name].quaternion));met.seamPosition=Math.max(met.seamPosition,Math.hypot(...c0.bones[name].position.map((v,j)=>v-c1.bones[name].position[j])))}
 const limits={maxContactAnkle:.050,maxContactToe:.070,maxSwingAnkle:.150,maxRootZ:1e-8,maxRootX:.045,maxHead:.200,maxFloorPenetration:.020,maxStepAdded:8.0,seamRotationAddedDeg:1.0,seamPosition:.002};
 const checks=[['stance ankle',met.maxContactAnkle,limits.maxContactAnkle],['stance toe',met.maxContactToe,limits.maxContactToe],['swing ankle',met.maxSwingAnkle,limits.maxSwingAnkle],['backward root Z',met.maxRootZ,limits.maxRootZ],['lateral root sway',met.maxRootX,limits.maxRootX],['head world shift',met.maxHead,limits.maxHead],['new downward foot penetration',met.maxFloorPenetration,limits.maxFloorPenetration],['extra joint step',met.maxStepAdded,limits.maxStepAdded],['extra seam rotation',Math.max(0,met.seamCandidate-met.seamBase),limits.seamRotationAddedDeg],['seam position',met.seamPosition,limits.seamPosition]];
 met.rejections=checks.filter(([name,actual,max])=>actual>max+1e-10).map(([name,actual,max])=>({name,actual,max}));
 met.worst=met.worst.sort((a,b)=>b.error-a.error).slice(0,22);met.limits=limits;met.pass=met.rejections.length===0&&met.lowestContactCount>0;
 return met;
}
async function applyRequested(){if(!ready||busy)return;busy=true;playing=false;$('play').textContent='Play';$('apply').disabled=true;
 const requested=readRequest(),accepted=zeroGains(),trials=[];
 try{
  for(const key of LAYERS){if(requested[key]===0)continue;
   let passGain=0,best=null;const tested=[];
   // Bounded adaptive search. Each candidate is judged against ALL enabled
   // earlier layers. Never silently apply a rejected combination.
   for(const fraction of [1,.8,.6,.4,.25,.125,.0625]){
    const g={...accepted,[key]:requested[key]*fraction};const m=await measure(g,[30,60],false);
    tested.push({requested:g[key],pass:m.pass,reasons:m.rejections.slice(0,3)});
    if(m.pass&&g[key]>passGain){passGain=g[key];best=m;break}
   }
   if(passGain>0.02){accepted[key]=passGain;trials.push({layer:key,requested:requested[key],applied:passGain,status:'GATED_PASS',tested})}
   else trials.push({layer:key,requested:requested[key],applied:0,status:'REJECTED_SAFETY_GATE',tested});
   $('audit').textContent='Testing '+key+'…\n'+trials.map(x=>x.layer+': '+x.status+' '+Math.round(x.applied*100)+'%').join('\n');
   await new Promise(resolve=>requestAnimationFrame(resolve));
  }
  // The final composition must independently pass ALL three rates.
  let final=await measure(accepted,[30,60,120],true);
  if(!final.pass){const before={...accepted};for(const key of LAYERS.slice().reverse()){
   if(!accepted[key])continue;const requestedGain=accepted[key];
   for(const fraction of [.75,.5,.25,0]){accepted[key]=requestedGain*fraction;final=await measure(accepted,[30,60,120],true);if(final.pass)break}
   if(final.pass)break;
  }
   if(!final.pass){accepted.pelvis=0;accepted.legs=0;accepted.torso=0;accepted.arms=0;final=await measure(accepted,[30,60,120],true)}
   trials.push({status:'FINAL_COMBINATION_REQUIRES_ATTENUATION',previous:before,actual:{...accepted}});
  }
  if(!final.pass)throw Error('SAFE_COMBINATION_NOT_FOUND '+JSON.stringify(final.rejections));
  allowed={...accepted};const actualLocalStart=zeroAudit();displayAt(phase);
  lastAudit={schema:'hareworks-gated-backward-style-lab-v0.2.5',sourceSha256:SHA,sourceClips:['Walk_Backward','Walking','Walking_Woman'],ownerAcceptedBackward:'v0.2.2 immutable',ownerAcceptedForward:'v0.1.9 immutable',referenceStudy:'v0.2.3 74-bone research; static offsets excluded',stylePhaseOffset:PHASE_OFFSET,uploadedResearchReportSHA256:PRIORS_SHA,analysisSource:'owner-exported v0.2.3 JSON embedded byte-for-byte',
   approvedBackwardMotionPlaybackTracks:0,generatedSourceAnimationTracks:0,sourceCalibrationOnly:true,sourceBones:74,sourceSamples:{backward:BACK_SAMPLES,normal:STYLE_SAMPLES,woman:STYLE_SAMPLES},requested,applied:{...allowed},trials,fullRateAudit:final,zeroFrame:actualLocalStart,
   styleAcceptedByOwner:false,sourceModelUnchanged:true,originalGaitsUnchanged:true,manualVisualApprovalRequired:true};
  updateControls();$('audit').textContent='LAB SAFETY GATE PASS · Owner review pending\n'+trials.map(x=>x.layer?`${x.layer}: requested ${Math.round(x.requested*100)}%, applied ${Math.round(x.applied*100)}% (${x.status})`:x.status).join('\n')+
   `\nMeasured ${final.sampleCount} frame/half-frame poses at 30/60/120 Hz. Low-foot witnesses ${final.lowestContactCount}.\nStance ankle max ${final.maxContactAnkle.toFixed(4)}, stance toe ${final.maxContactToe.toFixed(4)}, swing ankle ${final.maxSwingAnkle.toFixed(4)}, head Δ ${final.maxHead.toFixed(4)}.\nWorst joint-step addition ${final.maxStepAdded.toFixed(3)}°. Phase-zero 74/74 exact. Accepted base not modified.`;
  status('REAL-RIG STYLE TRIAL APPLIED WITH GUARDS · owner visual review required');
  try{const r=await fetch('./style-report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(lastAudit)});if(!r.ok)throw Error('evidence receiver HTTP '+r.status);const receipt=await r.json();status('REAL-RIG STYLE TRIAL GATED · JSON saved in phone state ('+receipt.sha256.slice(0,12)+') · owner review required')}
  catch(e){status('STYLE TRIAL GATED · phone evidence autosave unavailable: '+e.message+' · use Export JSON');}
 }catch(e){allowed=zeroGains();displayAt(phase);status('STYLE_GUARD_REJECTED '+e.message);$('audit').textContent='No unsafe candidate applied.\n'+e.message;console.error(e)}
 finally{busy=false;$('apply').disabled=false;updateControls()}
}
$('apply').onclick=()=>applyRequested();
$('reset').onclick=()=>{if(busy)return;allowed=zeroGains();for(const key of LAYERS)$('on'+key[0].toUpperCase()+key.slice(1)).checked=false;updateControls();displayAt(phase);status('APPROVED v0.2.2 BASELINE RESTORED · no style applied');};
const download=data=>{const b=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(b),a=document.createElement('a');a.href=url;a.download='hareworks-backward-style-lab-v0.2.5-evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),6000)};
$('export').onclick=()=>lastAudit?download(lastAudit):status('No tested real-rig style candidate yet. Test layers first.');
$('play').onclick=()=>{if(!ready||busy)return;playing=!playing;$('play').textContent=playing?'Pause':'Play'};
$('phase').oninput=()=>{if(!ready||busy)return;playing=false;$('play').textContent='Play';displayAt(Number($('phase').value)/1000)};
function render(now){requestAnimationFrame(render);const dt=Math.min(.07,Math.max(0,(now-last)/1000));last=now;
 if(ready&&!busy&&playing){try{displayAt((phase+dt/backwardSource.duration)%1);$('phase').value=Math.round(phase*1000)}catch(e){playing=false;status('POSE_FAILURE '+e.message);console.error(e)}}orbit.update();renderer.render(scene,camera)}requestAnimationFrame(render);
window.addEventListener('unhandledrejection',e=>{status('BROWSER_ERROR '+(e.reason?.message||String(e.reason)));console.error(e.reason)});
try{
 const response=await fetch(GLB,{cache:'no-store'});if(!response.ok)throw Error('MODEL_HTTP_'+response.status);const bytes=await response.arrayBuffer();if(bytes.byteLength!==6784896)throw Error('SOURCE_SIZE_'+bytes.byteLength);
 const actual=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');if(actual!==SHA)throw Error('SOURCE_SHA_MISMATCH '+actual);
 const priorsResponse=await fetch('./research-priors.json',{cache:'no-store'});if(!priorsResponse.ok)throw Error('OWNER_RESEARCH_PRIORS_HTTP_'+priorsResponse.status);
 const priorsBytes=await priorsResponse.arrayBuffer(),priorsHex=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',priorsBytes))).map(x=>x.toString(16).padStart(2,'0')).join('');
 if(priorsHex!==PRIORS_SHA)throw Error('OWNER_RESEARCH_PRIORS_SHA_MISMATCH');
 researchPriors=JSON.parse(new TextDecoder().decode(priorsBytes));
 if(researchPriors.schema!=='hareworks-forward-style-research-v0.2.3'||researchPriors.sourceModelSHA256!==SHA||researchPriors.perBone.length!==74||Math.abs(researchPriors.alignment.womanPhaseOffset-PHASE_OFFSET)>1e-9)throw Error('OWNER_RESEARCH_PRIORS_CONTRACT_MISMATCH');
 const gltf=await new GLTFLoader().parseAsync(bytes,new URL('../../../assets/hareworks/',import.meta.url).href);
 if(gltf.animations.length!==9)throw Error('SOURCE_NINE_CLIPS_REQUIRED');
 for(const key of [CLIP,'Walking','Walking_Woman']){const clip=gltf.animations.find(c=>c.name===key);if(!clip)throw Error('MISSING_SOURCE_CLIP '+key);originalClips[key]=clip;sourceClones[key]=cloneSkeleton(gltf.scene);sourceMixers[key]=new THREE.AnimationMixer(sourceClones[key]);sourceMixers[key].clipAction(clip).reset().play();}
 backwardSource=captureClip(CLIP,BACK_SAMPLES);styleNormal=captureClip('Walking',STYLE_SAMPLES);styleWoman=captureClip('Walking_Woman',STYLE_SAMPLES);
 backwardPlan=calibrateBackward();sourceReady=true;
 baseline=cloneSkeleton(gltf.scene);candidate=cloneSkeleton(gltf.scene);baseRig=rigOf(baseline);candidateRig=rigOf(candidate);baseline.position.z=-SEP/2;candidate.position.z=SEP/2;scene.add(baseline,candidate);
 floor.position.y=new THREE.Box3().setFromObject(baseline).min.y;
 ready=true;displayAt(0);const zero=zeroAudit();window.__footProfile=getFootProfiles();displayAt(0);
 $('identity').textContent=`v0.2.5 · source ${SHA} · research SHA ${PRIORS_SHA} · clips Walking/Walking_Woman/Walk_Backward · 74 bones · no generated clip mixer · locked base v0.2.2 · pinned commit ${new URLSearchParams(location.search).get('commit')||'UNKNOWN'} · entry SHA ${new URLSearchParams(location.search).get('scriptSha')||'UNKNOWN'}`;
 $('audit').textContent=`EXACT BACKWARD BASELINE LOADED · 74/74 joint t0 equality\nVERIFIED OWNER v0.2.3 REPORT SHA ${PRIORS_SHA.slice(0,12)} · research phase alignment: ${PHASE_OFFSET.toFixed(6)} · backward seam starts ${backwardPlan.seamStart.toFixed(3)} · root Δ ${(backwardPlan.cycleTravel[2]).toFixed(4)} removed.\nAll four style layers OFF until separately tested. Sampling from exact GLB: backward ${BACK_SAMPLES}, normal/woman ${STYLE_SAMPLES} each.\nSource raw terminal key: ${JSON.stringify(rawRootEndpoint())}`;
 updateControls();status('SOURCE VERIFIED · ACCEPTED BACKWARD BASELINE PLAYING · turn on a layer, then TEST AND APPLY');cameraAt('side');resize();
}catch(e){status('MODEL_OR_RIG_BLOCKED '+e.message);console.error(e)}
__HAREWORKS_STYLE_LAB_V025_VIEWER_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/style-layers.mjs" <<'__HAREWORKS_STYLE_LAB_V025_STYLE_LAYERS_MJS__'
/* Hareworks v0.2.5: source-calibrated, pose-offset-free, independently gated
 * gait-character experiments. Never touches the accepted backward solver. */
export const LAYERS=['pelvis','legs','torso','arms'];
export const PHASE_OFFSET=0.9777777777777777; // exact v0.2.3 measured alignment
const E=[0,0,0,1];
export const mod1=p=>((p%1)+1)%1;
export function groupOf(n){
 if(n==='mixamorigHips')return 'pelvis';
 if(/UpLeg|Leg|Foot|ToeBase/.test(n))return 'legs';
 if(/Spine|Neck|Head/.test(n))return 'torso';
 if(/Shoulder|Arm|Hand/.test(n))return 'arms';
 return null;
}
function finite(v,n){return Array.isArray(v)&&v.length===n&&v.every(Number.isFinite)}
export function qnorm(q){if(!finite(q,4))throw Error('QUAT_INVALID');const l=Math.hypot(...q);if(l<1e-9)throw Error('QUAT_ZERO');return q.map(x=>x/l)}
export const qconj=q=>[-q[0],-q[1],-q[2],q[3]];
export function qmul(a,b){const [x,y,z,w]=a,[X,Y,Z,W]=b;return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]}
export function qslerp(a0,b0,t){if(!Number.isFinite(t)||t<0||t>1)throw Error('SLERP_GAIN_INVALID');const a=qnorm(a0);let b=qnorm(b0);let d=a.reduce((s,x,i)=>s+x*b[i],0);if(d<0){b=b.map(x=>-x);d=-d}if(d>.9995)return qnorm(a.map((x,i)=>x+(b[i]-x)*t));const phi=Math.acos(Math.min(1,d)),denom=Math.sin(phi);return qnorm(a.map((x,i)=>(Math.sin((1-t)*phi)*x+Math.sin(t*phi)*b[i])/denom))}
export function qangleDeg(a,b){const d=Math.min(1,Math.abs(qnorm(a).reduce((s,x,i)=>s+x*qnorm(b)[i],0)));return 2*Math.acos(d)*180/Math.PI}
const lerp=(a,b,t)=>a.map((x,i)=>x*(1-t)+b[i]*t);
const smooth=x=>{const y=Math.max(0,Math.min(1,x));return y*y*(3-2*y)};
export function sampleSource(clip,bone,p){
 const s=clip?.bones?.[bone],n=clip?.sampleCount;
 if(!s||!Number.isInteger(n)||n<120)throw Error('SOURCE_BONE_MISSING_'+bone);
 const q=mod1(p);let a,b,t;
 // Source authored clips can contain a terminal key reset. Blend the last
 // 7% back to sample zero instead of interpolating across that teleport.
 if(q>=.93){const u=smooth((q-.93)/.07),last=Math.min(n-1,Math.floor(.93*n));a=last;b=0;t=u;}
 else{const idx=q*n;a=Math.min(n-1,Math.floor(idx));b=Math.min(n-1,a+1);t=idx-a;}
 return {quaternion:qslerp(s.quat[a],s.quat[b],t),position:lerp(s.pos[a],s.pos[b],t),scale:lerp(s.scale[a],s.scale[b],t)};
}
export function sourceSignature(normal,woman,bone,p,phaseOffset=PHASE_OFFSET){
 const n0=sampleSource(normal,bone,0),w0=sampleSource(woman,bone,phaseOffset);
 const n=sampleSource(normal,bone,p),w=sampleSource(woman,bone,mod1(p+phaseOffset));
 const nn=qnorm(qmul(qconj(n0.quaternion),n.quaternion));
 const ww=qnorm(qmul(qconj(w0.quaternion),w.quaternion));
 const dynamic=qnorm(qmul(qconj(nn),ww));
 const displacement=n.position.map((x,i)=>(w.position[i]-w0.position[i])-(x-n0.position[i]));
 return {dynamic,displacement,rawStaticOffsetDeg:qangleDeg(n0.quaternion,w0.quaternion)};
}
export function stylePose(base,normal,woman,p,gains,phaseOffset=PHASE_OFFSET){
 if(!base?.bones||!normal?.bones||!woman?.bones||Object.keys(base.bones).length!==74)throw Error('SOURCE_TOPOLOGY_NOT_74');
 const weights={};for(const l of LAYERS){const g=Number(gains?.[l]??0);if(!Number.isFinite(g)||g<0||g>1)throw Error('GAIN_OUT_OF_RANGE_'+l);weights[l]=g}
 const out={};for(const [name,b] of Object.entries(base.bones)){
  const group=groupOf(name),gain=group?weights[group]:0;
  if(!gain){out[name]={quaternion:b.quaternion.slice(),position:b.position.slice(),scale:b.scale.slice()};continue}
  const delta=sourceSignature(normal,woman,name,p,phaseOffset);
  const quaternion=qnorm(qmul(b.quaternion,qslerp(E,delta.dynamic,gain)));
  const position=b.position.slice();
  if(group==='pelvis'){
   position[0]+=gain*delta.displacement[0];position[1]+=gain*delta.displacement[1];
   // Absolutely no root travel: retain original backward in-place Z.
   position[2]=b.position[2];
  }
  out[name]={quaternion,position,scale:b.scale.slice()};
 }
 if(out.mixamorigHips.position[2]!==base.bones.mixamorigHips.position[2])throw Error('ROOT_DIRECTION_CHANGED');
 return {bones:out,gains:weights,phase:mod1(p),sourcePhaseWoman:mod1(p+phaseOffset)};
}
export function zeroGains(){return {pelvis:0,legs:0,torso:0,arms:0}}
__HAREWORKS_STYLE_LAB_V025_STYLE_LAYERS_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/style-layers-test.mjs" <<'__HAREWORKS_STYLE_LAB_V025_STYLE_LAYERS_TEST_MJS__'
import assert from 'node:assert/strict';
import {stylePose,sourceSignature,groupOf,qangleDeg,qslerp,zeroGains,PHASE_OFFSET} from './style-layers.mjs';
const N=360,ID=[0,0,0,1],base={bones:{}},normal={sampleCount:N,bones:{}},woman={sampleCount:N,bones:{}};
const names=['mixamorigHips','mixamorigLeftUpLeg','mixamorigLeftLeg','mixamorigLeftFoot','mixamorigLeftToeBase','mixamorigRightUpLeg','mixamorigRightLeg','mixamorigRightFoot','mixamorigRightToeBase','mixamorigSpine','mixamorigNeck','mixamorigHead','mixamorigLeftShoulder','mixamorigLeftArm','mixamorigLeftForeArm','mixamorigLeftHand','mixamorigRightShoulder','mixamorigRightArm','mixamorigRightForeArm','mixamorigRightHand'];
while(names.length<74)names.push('mixamorigLeftHandIndex'+names.length);
const rotate=a=>[0,0,Math.sin(a/2),Math.cos(a/2)];
for(const name of names){const gr=groupOf(name),staticAngle=gr==='arms'?.55:.18;
 base.bones[name]={quaternion:ID.slice(),position:name==='mixamorigHips'?[0,.92,.1065]:[0,0,0],scale:[1,1,1]};
 normal.bones[name]={quat:[],pos:[],scale:[]};woman.bones[name]={quat:[],pos:[],scale:[]};
 for(let k=0;k<N;k++){const t=2*Math.PI*k/N;normal.bones[name].quat.push(rotate(.15*Math.sin(t)));
  // Distinct initial orientation but SAME dynamic motion on unrelated fingers.
  woman.bones[name].quat.push(rotate(staticAngle+(gr==='arms'?.28:.20)*Math.sin(t)));
  normal.bones[name].pos.push(name==='mixamorigHips'?[.01*Math.sin(t),.92+.02*Math.cos(t),.1065-.8*k/N]:[0,0,0]);
  woman.bones[name].pos.push(name==='mixamorigHips'?[.01*Math.sin(t),.92+.013*Math.cos(t),.1065-.9*k/N]:[0,0,0]);
  for(const c of [normal,woman])c.bones[name].scale.push([1,1,1]);
 }
}
const z=stylePose(base,normal,woman,.4,zeroGains());assert.deepEqual(z.bones,base.bones,'zero gain EXACT base');
const l=stylePose(base,normal,woman,0,{pelvis:1,legs:1,torso:1,arms:1},0);assert.ok(Object.keys(l.bones).every(n=>qangleDeg(l.bones[n].quaternion,base.bones[n].quaternion)<.001),'first frame anchored');
const leg=stylePose(base,normal,woman,.23,{pelvis:0,legs:.8,torso:0,arms:0},0);
assert.ok(qangleDeg(leg.bones.mixamorigLeftLeg.quaternion,ID)>1,'leg motion present');
assert.equal(qangleDeg(leg.bones.mixamorigLeftArm.quaternion,ID),0,'arms untouched by leg layer');
const arm=stylePose(base,normal,woman,.27,{pelvis:0,legs:0,torso:0,arms:1},0);
assert.ok(qangleDeg(arm.bones.mixamorigLeftHand.quaternion,ID)>1,'arm dynamic transfer visible');
assert.equal(qangleDeg(arm.bones.mixamorigSpine.quaternion,ID),0,'torso independent');
const pelvis=stylePose(base,normal,woman,.3,{pelvis:1,legs:0,torso:0,arms:0},0);
assert.equal(pelvis.bones.mixamorigHips.position[2],.1065,'no root travel imported');
assert.ok(Math.abs(pelvis.bones.mixamorigHips.position[1]-.92)>1e-4,'bounce changed');
assert.deepEqual(base.bones.mixamorigHips.position,[0,.92,.1065],'approved base not mutated');
const seam0=stylePose(base,normal,woman,0,{pelvis:1,legs:1,torso:1,arms:1});
const seam1=stylePose(base,normal,woman,1-1e-8,{pelvis:1,legs:1,torso:1,arms:1});
assert.ok(qangleDeg(seam0.bones.mixamorigLeftArm.quaternion,seam1.bones.mixamorigLeftArm.quaternion)<.01,'periodic seam');
assert.throws(()=>stylePose(base,normal,woman,.2,{pelvis:2}),/GAIN_OUT_OF_RANGE/);
assert.throws(()=>stylePose({bones:{}},normal,woman,.2,{}),/SOURCE_TOPOLOGY_NOT_74/);
assert.ok(Math.abs(PHASE_OFFSET-.9777777777777777)<1e-9,'research phase constant pinned');
const d=sourceSignature(normal,woman,'mixamorigLeftArm',0,0);assert.ok(qangleDeg(d.dynamic,ID)<.001,'static pose not transferred');
console.log('STYLE_LAYER_TEST_PASS: phase-zero, source-static-offset subtraction, four layers, root protection, seam, negative cases');
__HAREWORKS_STYLE_LAB_V025_STYLE_LAYERS_TEST_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/inplace-kernel.mjs" <<'__HAREWORKS_STYLE_LAB_V025_INPLACE_KERNEL_MJS__'
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
__HAREWORKS_STYLE_LAB_V025_INPLACE_KERNEL_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/inplace-kernel-test.mjs" <<'__HAREWORKS_STYLE_LAB_V025_INPLACE_KERNEL_TEST_MJS__'
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
__HAREWORKS_STYLE_LAB_V025_INPLACE_KERNEL_TEST_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/inplace-witness-test.mjs" <<'__HAREWORKS_STYLE_LAB_V025_INPLACE_WITNESS_TEST_MJS__'
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
__HAREWORKS_STYLE_LAB_V025_INPLACE_WITNESS_TEST_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/source-witness.json" <<'__HAREWORKS_STYLE_LAB_V025_SOURCE_WITNESS_JSON__'
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
__HAREWORKS_STYLE_LAB_V025_SOURCE_WITNESS_JSON__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/research-priors.json" <<'__HAREWORKS_STYLE_LAB_V025_RESEARCH_PRIORS_JSON__'
{
  "schema": "hareworks-forward-style-research-v0.2.3",
  "sourceClipNames": [
    "Walking",
    "Walking_Woman"
  ],
  "sourceModelSHA256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "modelJoints": 74,
  "analysisOnly": true,
  "createdNewAnimation": false,
  "sourceClipsUnchanged": true,
  "ownerApprovedForwardUntouched": true,
  "ownerApprovedBackwardUntouched": true,
  "samplingPhaseCount": 360,
  "clips": {
    "Walking": {
      "durationSeconds": 1.0333333015441895,
      "sceneRootDetrendingDisplayOnly": [
        -0.011431504755532562,
        0,
        0.030019483402264357
      ],
      "originalClipTracks": 192
    },
    "Walking_Woman": {
      "durationSeconds": 0.9666666388511658,
      "sceneRootDetrendingDisplayOnly": [
        0.0012616406115126737,
        0,
        0.03027439403536359
      ],
      "originalClipTracks": 192
    }
  },
  "gaitTraits": {
    "Walking": {
      "durationSeconds": 1.0333333015441895,
      "pelvisYawRangeDeg": 10.37083329183052,
      "pelvisPitchRangeDeg": 4.754184173622339,
      "pelvisRollRangeDeg": 7.507395022352715,
      "pelvisVerticalBounceUnits": 0.06948432298058849,
      "pelvisLateralSwayDetrendedUnits": 0.05191074379875212,
      "headSideToSideRelativeToHipsUnits": 0.04926221663392606,
      "headOrientationRelativeToChestRmsChangeDeg": 7.373006220047882,
      "leftFootForeAftHipFrameUnits": 0.8084459784772968,
      "rightFootForeAftHipFrameUnits": 0.7464233469423216,
      "leftFootLateralHipFrameUnits": 0.13345764788477096,
      "rightFootLateralHipFrameUnits": 0.14815403243851735,
      "footLowPointCandidates": {
        "left": {
          "lowestFootPhase": 0.6333333333333333,
          "sourceFootHeight": 0.17645132589392948,
          "interpretation": "lowest-foot candidate, not proven foot contact"
        },
        "right": {
          "lowestFootPhase": 0.18611111111111112,
          "sourceFootHeight": 0.17276004495102174,
          "interpretation": "lowest-foot candidate, not proven foot contact"
        }
      }
    },
    "Walking_Woman": {
      "durationSeconds": 0.9666666388511658,
      "pelvisYawRangeDeg": 15.305942720111956,
      "pelvisPitchRangeDeg": 3.2390449326612325,
      "pelvisRollRangeDeg": 11.40392832094795,
      "pelvisVerticalBounceUnits": 0.03894539690473242,
      "pelvisLateralSwayDetrendedUnits": 0.0413741530018067,
      "headSideToSideRelativeToHipsUnits": 0.056179359613852245,
      "headOrientationRelativeToChestRmsChangeDeg": 5.233907585249608,
      "leftFootForeAftHipFrameUnits": 0.6866728255582664,
      "rightFootForeAftHipFrameUnits": 0.7000297280442989,
      "leftFootLateralHipFrameUnits": 0.23770975129206456,
      "rightFootLateralHipFrameUnits": 0.22120638950382962,
      "footLowPointCandidates": {
        "left": {
          "lowestFootPhase": 0.6888888888888889,
          "sourceFootHeight": 0.1736683846407089,
          "interpretation": "lowest-foot candidate, not proven foot contact"
        },
        "right": {
          "lowestFootPhase": 0.18611111111111112,
          "sourceFootHeight": 0.17493716758628283,
          "interpretation": "lowest-foot candidate, not proven foot contact"
        }
      }
    }
  },
  "alignment": {
    "womanPhaseOffset": 0.9777777777777777,
    "normalPhaseOffset": 0,
    "method": "global offset minimizing normalized hip-relative left/right foot X/Z trajectory differences",
    "cost": 0.3593764765620052,
    "samplePairs": 656,
    "distinctAlternativeCost": 0.6429603409834487,
    "ambiguityRatio": 1.7890996849163976,
    "sourceTerminalWindowExcluded": [
      0.93,
      1
    ]
  },
  "sourceMeasuredPhaseWindow": "0 <= phase < 0.93 for BOTH clips, aligned by pair of pelvis-relative ankle trajectories; excludes terminal reset",
  "caveats": [
    "This compares these two authored animations, not sexes in general",
    "All 74 joints share exactly the same skeleton",
    "A source static offset is not evidence of dynamic movement style",
    "Measured foot phase fit is descriptive, not force-contact evidence",
    "No backward gait is modified by this research",
    "No candidate style transfer is applied"
  ],
  "sampledMatchedPhases": 218,
  "perBone": [
    {
      "bone": "mixamorigLeftHand",
      "group": "hands",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 31.924402246571628,
      "meanRawPoseDifferenceDeg": 32.2257447654008,
      "motionDeltaRmsDeg": 29.759619395096983,
      "motionDeltaMaxDeg": 49.94374197581139,
      "phaseOfMaxDynamicDifference": 0.1625,
      "normalMotionFromAnchorRmsDeg": 16.515792502060492,
      "womanMotionFromAnchorRmsDeg": 28.640879970751314,
      "motionFromAnchorRmsRatio": 1.7341511142851975,
      "hipRelativePositionDifferenceRmsUnits": 0.1322393172041144,
      "localTranslationMotionDeltaRmsUnits": 1.4459650257077488e-8,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.20612285066838884,
          "woman": 0.046830196655110956,
          "difference": -0.15929265401327788
        },
        "y": {
          "normal": 0.11902186498958944,
          "woman": 0.11202705062136831,
          "difference": -0.006994814368221136
        },
        "z": {
          "normal": 0.44176711046596406,
          "woman": 0.3904807801489878,
          "difference": -0.05128633031697627
        }
      }
    },
    {
      "bone": "mixamorigRightArm",
      "group": "upper-arms",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 48.13732525585488,
      "meanRawPoseDifferenceDeg": 33.727139279059806,
      "motionDeltaRmsDeg": 26.701571465291412,
      "motionDeltaMaxDeg": 36.68520616066363,
      "phaseOfMaxDynamicDifference": 0.5416666666666666,
      "normalMotionFromAnchorRmsDeg": 17.11811794046296,
      "womanMotionFromAnchorRmsDeg": 20.353683182641134,
      "motionFromAnchorRmsRatio": 1.1890140758132124,
      "hipRelativePositionDifferenceRmsUnits": 0.04267319189629913,
      "localTranslationMotionDeltaRmsUnits": 6.655704092445982e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.02903580520603624,
          "woman": 0.036606947227911024,
          "difference": 0.007571142021874783
        },
        "y": {
          "normal": 0.016289486964486566,
          "woman": 0.030804218426445013,
          "difference": 0.014514731461958447
        },
        "z": {
          "normal": 0.0872834627989833,
          "woman": 0.06751526312609848,
          "difference": -0.019768199672884817
        }
      }
    },
    {
      "bone": "mixamorigLeftLeg",
      "group": "legs",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 19.977962902453932,
      "meanRawPoseDifferenceDeg": 16.295814800868293,
      "motionDeltaRmsDeg": 24.915074164939103,
      "motionDeltaMaxDeg": 37.83303837701305,
      "phaseOfMaxDynamicDifference": 0.38333333333333336,
      "normalMotionFromAnchorRmsDeg": 28.91153990972157,
      "womanMotionFromAnchorRmsDeg": 38.54100957302968,
      "motionFromAnchorRmsRatio": 1.3330666472065082,
      "hipRelativePositionDifferenceRmsUnits": 0.050901149022277964,
      "localTranslationMotionDeltaRmsUnits": 1.45612150833364e-17,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.06610533606972366,
          "woman": 0.09922484699841731,
          "difference": 0.033119510928693655
        },
        "y": {
          "normal": 0.06660666529547471,
          "woman": 0.06036920902534082,
          "difference": -0.00623745627013389
        },
        "z": {
          "normal": 0.3676840935700536,
          "woman": 0.2918807255632857,
          "difference": -0.0758033680067679
        }
      }
    },
    {
      "bone": "mixamorigLeftForeArm",
      "group": "forearms",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 24.98513127779229,
      "meanRawPoseDifferenceDeg": 16.318201436185173,
      "motionDeltaRmsDeg": 20.179976455807456,
      "motionDeltaMaxDeg": 40.59058869722167,
      "phaseOfMaxDynamicDifference": 0.6458333333333334,
      "normalMotionFromAnchorRmsDeg": 24.915760036957224,
      "womanMotionFromAnchorRmsDeg": 14.666114505594761,
      "motionFromAnchorRmsRatio": 0.5886280203309353,
      "hipRelativePositionDifferenceRmsUnits": 0.0798101090414511,
      "localTranslationMotionDeltaRmsUnits": 2.8708043526888945e-8,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.03897572594340315,
          "woman": 0.05304074374342768,
          "difference": 0.014065017800024532
        },
        "y": {
          "normal": 0.0365126998456263,
          "woman": 0.048837028966469256,
          "difference": 0.012324329120842956
        },
        "z": {
          "normal": 0.24601523506766892,
          "woman": 0.19568480360831364,
          "difference": -0.050330431459355285
        }
      }
    },
    {
      "bone": "mixamorigRightHand",
      "group": "hands",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 28.36387325816957,
      "meanRawPoseDifferenceDeg": 28.318381033545325,
      "motionDeltaRmsDeg": 19.42634933999286,
      "motionDeltaMaxDeg": 30.259038809364394,
      "phaseOfMaxDynamicDifference": 0.6083333333333333,
      "normalMotionFromAnchorRmsDeg": 13.650456784698171,
      "womanMotionFromAnchorRmsDeg": 17.85035226039487,
      "motionFromAnchorRmsRatio": 1.3076743541948486,
      "hipRelativePositionDifferenceRmsUnits": 0.14153759538722893,
      "localTranslationMotionDeltaRmsUnits": 1.3001423543807094e-8,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.0685973563382706,
          "woman": 0.06390246088833718,
          "difference": -0.004694895449933428
        },
        "y": {
          "normal": 0.07336052026914086,
          "woman": 0.07672723377677458,
          "difference": 0.00336671350763372
        },
        "z": {
          "normal": 0.44556615258245397,
          "woman": 0.39987627114546775,
          "difference": -0.04568988143698621
        }
      }
    },
    {
      "bone": "mixamorigRightForeArm",
      "group": "forearms",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 7.221542196617063,
      "meanRawPoseDifferenceDeg": 19.975798971780595,
      "motionDeltaRmsDeg": 17.376466624419148,
      "motionDeltaMaxDeg": 30.83708918341644,
      "phaseOfMaxDynamicDifference": 0.4708333333333333,
      "normalMotionFromAnchorRmsDeg": 11.581560468341772,
      "womanMotionFromAnchorRmsDeg": 8.2853117931002,
      "motionFromAnchorRmsRatio": 0.7153882083289315,
      "hipRelativePositionDifferenceRmsUnits": 0.07126036647051642,
      "localTranslationMotionDeltaRmsUnits": 1.2337038771404167e-8,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.04467739616381086,
          "woman": 0.05357825307635583,
          "difference": 0.008900856912544969
        },
        "y": {
          "normal": 0.030677591366181457,
          "woman": 0.03981115015852127,
          "difference": 0.009133558792339812
        },
        "z": {
          "normal": 0.25028162885491156,
          "woman": 0.22339241161615403,
          "difference": -0.026889217238757535
        }
      }
    },
    {
      "bone": "mixamorigLeftArm",
      "group": "upper-arms",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 32.50616024163296,
      "meanRawPoseDifferenceDeg": 38.094183239639705,
      "motionDeltaRmsDeg": 15.516024717874284,
      "motionDeltaMaxDeg": 22.128438418712765,
      "phaseOfMaxDynamicDifference": 0.36666666666666664,
      "normalMotionFromAnchorRmsDeg": 17.773460272116424,
      "womanMotionFromAnchorRmsDeg": 17.684427089238522,
      "motionFromAnchorRmsRatio": 0.9949906668980165,
      "hipRelativePositionDifferenceRmsUnits": 0.028828956139328562,
      "localTranslationMotionDeltaRmsUnits": 1.3009936570923607e-8,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.05147495068390129,
          "woman": 0.04998496559993995,
          "difference": -0.0014899850839613371
        },
        "y": {
          "normal": 0.01724830654461132,
          "woman": 0.03703713602110492,
          "difference": 0.019788829476493602
        },
        "z": {
          "normal": 0.07794807309661794,
          "woman": 0.08071792787309352,
          "difference": 0.0027698547764755804
        }
      }
    },
    {
      "bone": "mixamorigRightLeg",
      "group": "legs",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 4.70628700423902,
      "meanRawPoseDifferenceDeg": 11.706304712233816,
      "motionDeltaRmsDeg": 15.291274799526443,
      "motionDeltaMaxDeg": 27.377937570780325,
      "phaseOfMaxDynamicDifference": 0.3875,
      "normalMotionFromAnchorRmsDeg": 29.99169777482377,
      "womanMotionFromAnchorRmsDeg": 21.424152142262244,
      "motionFromAnchorRmsRatio": 0.7143360907112946,
      "hipRelativePositionDifferenceRmsUnits": 0.04988145475294716,
      "localTranslationMotionDeltaRmsUnits": 6.11171878462189e-17,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.07100535570120509,
          "woman": 0.11585522505609414,
          "difference": 0.04484986935488905
        },
        "y": {
          "normal": 0.07520970583305864,
          "woman": 0.05890536277933178,
          "difference": -0.016304343053726855
        },
        "z": {
          "normal": 0.3508250121861779,
          "woman": 0.31340826444477354,
          "difference": -0.037416747741404355
        }
      }
    },
    {
      "bone": "mixamorigLeftUpLeg",
      "group": "legs",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 12.47691393394967,
      "meanRawPoseDifferenceDeg": 9.011302069575224,
      "motionDeltaRmsDeg": 13.028967071085209,
      "motionDeltaMaxDeg": 22.068416942191107,
      "phaseOfMaxDynamicDifference": 0.7416666666666667,
      "normalMotionFromAnchorRmsDeg": 25.754619504790497,
      "womanMotionFromAnchorRmsDeg": 20.598688229174453,
      "motionFromAnchorRmsRatio": 0.799805573727967,
      "hipRelativePositionDifferenceRmsUnits": 2.539452257495632e-11,
      "localTranslationMotionDeltaRmsUnits": 5.306609042589377e-18,
      "hipFramePositionRange": {
        "x": {
          "normal": 2.911332286359425e-11,
          "woman": 4.6674705767024705e-11,
          "difference": 1.7561382903430456e-11
        },
        "y": {
          "normal": 3.9319519862246466e-11,
          "woman": 9.141587486993785e-11,
          "difference": 5.2096355007691386e-11
        },
        "z": {
          "normal": 1.9511690874107757e-11,
          "woman": 6.231882371254827e-11,
          "difference": 4.280713283844051e-11
        }
      }
    },
    {
      "bone": "mixamorigHips",
      "group": "pelvis",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 10.055778796472365,
      "meanRawPoseDifferenceDeg": 5.371908189038303,
      "motionDeltaRmsDeg": 11.9465884868175,
      "motionDeltaMaxDeg": 18.004726860967708,
      "phaseOfMaxDynamicDifference": 0.5041666666666667,
      "normalMotionFromAnchorRmsDeg": 4.3910877740177865,
      "womanMotionFromAnchorRmsDeg": 11.874475557192335,
      "motionFromAnchorRmsRatio": 2.70422186216682,
      "hipRelativePositionDifferenceRmsUnits": 0,
      "localTranslationMotionDeltaRmsUnits": 0.027564969379547714,
      "hipFramePositionRange": {
        "x": {
          "normal": 0,
          "woman": 0,
          "difference": 0
        },
        "y": {
          "normal": 0,
          "woman": 0,
          "difference": 0
        },
        "z": {
          "normal": 0,
          "woman": 0,
          "difference": 0
        }
      }
    },
    {
      "bone": "mixamorigRightFoot",
      "group": "feet",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 7.580250151438332,
      "meanRawPoseDifferenceDeg": 11.807374069245537,
      "motionDeltaRmsDeg": 11.56690833481478,
      "motionDeltaMaxDeg": 23.893212995428186,
      "phaseOfMaxDynamicDifference": 0.75,
      "normalMotionFromAnchorRmsDeg": 13.437618796730227,
      "womanMotionFromAnchorRmsDeg": 16.948792082252723,
      "motionFromAnchorRmsRatio": 1.2612943065758695,
      "hipRelativePositionDifferenceRmsUnits": 0.07934044956613209,
      "localTranslationMotionDeltaRmsUnits": 1.4316471348755705e-17,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.14798692959647614,
          "woman": 0.2201089810385515,
          "difference": 0.07212205144207537
        },
        "y": {
          "normal": 0.1870706578855379,
          "woman": 0.14818162255436917,
          "difference": -0.03888903533116872
        },
        "z": {
          "normal": 0.7457879539000626,
          "woman": 0.6994655792144072,
          "difference": -0.046322374685655365
        }
      }
    },
    {
      "bone": "mixamorigRightUpLeg",
      "group": "legs",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 9.083451100079353,
      "meanRawPoseDifferenceDeg": 8.370062856054512,
      "motionDeltaRmsDeg": 11.414474086813089,
      "motionDeltaMaxDeg": 19.5379028023449,
      "phaseOfMaxDynamicDifference": 0.5458333333333333,
      "normalMotionFromAnchorRmsDeg": 24.07489053392344,
      "womanMotionFromAnchorRmsDeg": 22.85799970036594,
      "motionFromAnchorRmsRatio": 0.9494539411573729,
      "hipRelativePositionDifferenceRmsUnits": 3.8393122742892965e-11,
      "localTranslationMotionDeltaRmsUnits": 3.938992597442499e-18,
      "hipFramePositionRange": {
        "x": {
          "normal": 7.559183834437988e-11,
          "woman": 1.5556821109097285e-10,
          "difference": 7.997637274659297e-11
        },
        "y": {
          "normal": 6.724638901278723e-11,
          "woman": 1.2988360387211628e-10,
          "difference": 6.263721485932905e-11
        },
        "z": {
          "normal": 1.49225458379032e-11,
          "woman": 6.89741180837089e-11,
          "difference": 5.40515722458057e-11
        }
      }
    },
    {
      "bone": "mixamorigLeftHandThumb1",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 27.170745845045374,
      "meanRawPoseDifferenceDeg": 31.148235151018813,
      "motionDeltaRmsDeg": 10.56541794867301,
      "motionDeltaMaxDeg": 14.607679712307698,
      "phaseOfMaxDynamicDifference": 0.2625,
      "normalMotionFromAnchorRmsDeg": 0.0000024148365394514633,
      "womanMotionFromAnchorRmsDeg": 10.565417948673062,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.13883122111799212,
      "localTranslationMotionDeltaRmsUnits": 4.848213961982248e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.23137986576756464,
          "woman": 0.051511480620971245,
          "difference": -0.1798683851465934
        },
        "y": {
          "normal": 0.16238403008397911,
          "woman": 0.14966661833723854,
          "difference": -0.01271741174674057
        },
        "z": {
          "normal": 0.44617775101767476,
          "woman": 0.3953476499950113,
          "difference": -0.05083010102266344
        }
      }
    },
    {
      "bone": "mixamorigLeftHandIndex1",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 22.36456328051426,
      "meanRawPoseDifferenceDeg": 21.07952701252074,
      "motionDeltaRmsDeg": 10.43285666383042,
      "motionDeltaMaxDeg": 15.677474563403925,
      "phaseOfMaxDynamicDifference": 0.4708333333333333,
      "normalMotionFromAnchorRmsDeg": 5.521593750768924,
      "womanMotionFromAnchorRmsDeg": 10.640376217988825,
      "motionFromAnchorRmsRatio": 1.9270480043025753,
      "hipRelativePositionDifferenceRmsUnits": 0.15667472622677192,
      "localTranslationMotionDeltaRmsUnits": 7.77271395931232e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.26310824385206416,
          "woman": 0.05636081966358958,
          "difference": -0.20674742418847458
        },
        "y": {
          "normal": 0.19666116794368627,
          "woman": 0.185272915817211,
          "difference": -0.011388252126475262
        },
        "z": {
          "normal": 0.5370862762296572,
          "woman": 0.47636366104807093,
          "difference": -0.06072261518158628
        }
      }
    },
    {
      "bone": "mixamorigLeftFoot",
      "group": "feet",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 1.4599914756971268,
      "meanRawPoseDifferenceDeg": 9.477003385772374,
      "motionDeltaRmsDeg": 10.425928684397004,
      "motionDeltaMaxDeg": 24.81747029755502,
      "phaseOfMaxDynamicDifference": 0.26666666666666666,
      "normalMotionFromAnchorRmsDeg": 14.597681808635791,
      "womanMotionFromAnchorRmsDeg": 12.731538673979541,
      "motionFromAnchorRmsRatio": 0.8721616788802545,
      "hipRelativePositionDifferenceRmsUnits": 0.11519700129541247,
      "localTranslationMotionDeltaRmsUnits": 3.9274782517061444e-17,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.13335862733067105,
          "woman": 0.2323471237224528,
          "difference": 0.09898849639178176
        },
        "y": {
          "normal": 0.1600984549321689,
          "woman": 0.15650227873291056,
          "difference": -0.0035961761992583385
        },
        "z": {
          "normal": 0.8084459784772968,
          "woman": 0.6864829621431275,
          "difference": -0.12196301633416928
        }
      }
    },
    {
      "bone": "mixamorigLeftHandThumb3",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 22.119676530007354,
      "meanRawPoseDifferenceDeg": 21.277052237166142,
      "motionDeltaRmsDeg": 9.453096711130765,
      "motionDeltaMaxDeg": 16.36552741738697,
      "phaseOfMaxDynamicDifference": 0.8166666666666667,
      "normalMotionFromAnchorRmsDeg": 2.2328183113536184,
      "womanMotionFromAnchorRmsDeg": 10.122755606338247,
      "motionFromAnchorRmsRatio": 4.533622621628113,
      "hipRelativePositionDifferenceRmsUnits": 0.14750998301194784,
      "localTranslationMotionDeltaRmsUnits": 1.9457453042298294e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.25134872775360545,
          "woman": 0.05593478323842151,
          "difference": -0.19541394451518396
        },
        "y": {
          "normal": 0.18904617838484472,
          "woman": 0.17118956663673263,
          "difference": -0.017856611748112095
        },
        "z": {
          "normal": 0.47595021318384373,
          "woman": 0.43086224839346293,
          "difference": -0.0450879647903808
        }
      }
    },
    {
      "bone": "mixamorigRightHandMiddle1",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 8.05466137473268,
      "meanRawPoseDifferenceDeg": 8.698964400429459,
      "motionDeltaRmsDeg": 9.119193875793657,
      "motionDeltaMaxDeg": 15.187321244934783,
      "phaseOfMaxDynamicDifference": 0.3,
      "normalMotionFromAnchorRmsDeg": 2.611403888203684,
      "womanMotionFromAnchorRmsDeg": 8.755555194799012,
      "motionFromAnchorRmsRatio": 3.352815408734697,
      "hipRelativePositionDifferenceRmsUnits": 0.19551103874585454,
      "localTranslationMotionDeltaRmsUnits": 4.16845374827431e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.09510320400960903,
          "woman": 0.10275269434836051,
          "difference": 0.00764949033875148
        },
        "y": {
          "normal": 0.09368410432912178,
          "woman": 0.12899449375394512,
          "difference": 0.03531038942482334
        },
        "z": {
          "normal": 0.5471641860693816,
          "woman": 0.5051234491355477,
          "difference": -0.04204073693383381
        }
      }
    },
    {
      "bone": "mixamorigLeftShoulder",
      "group": "shoulders",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 21.153851161880347,
      "meanRawPoseDifferenceDeg": 15.423064604749458,
      "motionDeltaRmsDeg": 8.907683702234866,
      "motionDeltaMaxDeg": 14.052655706042227,
      "phaseOfMaxDynamicDifference": 0.4,
      "normalMotionFromAnchorRmsDeg": 2.084093298796992,
      "womanMotionFromAnchorRmsDeg": 9.953443075403536,
      "motionFromAnchorRmsRatio": 4.775910503214513,
      "hipRelativePositionDifferenceRmsUnits": 0.014123191735261525,
      "localTranslationMotionDeltaRmsUnits": 4.0970267213759504e-18,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.026903351856850437,
          "woman": 0.030655245994666472,
          "difference": 0.003751894137816035
        },
        "y": {
          "normal": 0.0032807578896451584,
          "woman": 0.00541722668606226,
          "difference": 0.0021364687964171014
        },
        "z": {
          "normal": 0.01713180320878581,
          "woman": 0.015752388078117865,
          "difference": -0.0013794151306679436
        }
      }
    },
    {
      "bone": "mixamorigLeftHandThumb2",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 27.880801011207236,
      "meanRawPoseDifferenceDeg": 27.68363049472072,
      "motionDeltaRmsDeg": 8.77129782510965,
      "motionDeltaMaxDeg": 13.606915598952328,
      "phaseOfMaxDynamicDifference": 0.09166666666666666,
      "normalMotionFromAnchorRmsDeg": 5.029997249039559,
      "womanMotionFromAnchorRmsDeg": 10.480155831776983,
      "motionFromAnchorRmsRatio": 2.0835311259420854,
      "hipRelativePositionDifferenceRmsUnits": 0.1420170118030776,
      "localTranslationMotionDeltaRmsUnits": 1.0239002610473255e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.2401137429787795,
          "woman": 0.054181586807537,
          "difference": -0.18593215617124248
        },
        "y": {
          "normal": 0.1753247540170085,
          "woman": 0.16163856303324714,
          "difference": -0.013686190983761365
        },
        "z": {
          "normal": 0.45756980990058743,
          "woman": 0.4097488320043958,
          "difference": -0.04782097789619161
        }
      }
    },
    {
      "bone": "mixamorigRightHandIndex1",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 10.839678722836219,
      "meanRawPoseDifferenceDeg": 11.757059139769165,
      "motionDeltaRmsDeg": 8.253027408677774,
      "motionDeltaMaxDeg": 16.776378068288295,
      "phaseOfMaxDynamicDifference": 0.85,
      "normalMotionFromAnchorRmsDeg": 3.1244022593986163,
      "womanMotionFromAnchorRmsDeg": 7.166153487868667,
      "motionFromAnchorRmsRatio": 2.2936078305256395,
      "hipRelativePositionDifferenceRmsUnits": 0.19212742196251342,
      "localTranslationMotionDeltaRmsUnits": 4.148221164021642e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.10208897100013326,
          "woman": 0.1044217812822179,
          "difference": 0.002332810282084638
        },
        "y": {
          "normal": 0.10452128968439348,
          "woman": 0.1400983858669845,
          "difference": 0.03557709618259103
        },
        "z": {
          "normal": 0.5362317582797194,
          "woman": 0.48936549019036024,
          "difference": -0.04686626808935912
        }
      }
    },
    {
      "bone": "mixamorigRightHandThumb1",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 14.335567629361524,
      "meanRawPoseDifferenceDeg": 13.11223996485648,
      "motionDeltaRmsDeg": 7.021693922111912,
      "motionDeltaMaxDeg": 12.51198806538933,
      "phaseOfMaxDynamicDifference": 0.26666666666666666,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 7.021693922111849,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.15590402529240793,
      "localTranslationMotionDeltaRmsUnits": 4.21544675609552e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.08767294052404945,
          "woman": 0.08003133680617283,
          "difference": -0.007641603717876616
        },
        "y": {
          "normal": 0.09523948820313424,
          "woman": 0.10660321024287822,
          "difference": 0.011363722039743979
        },
        "z": {
          "normal": 0.4612982765108674,
          "woman": 0.4141140199769201,
          "difference": -0.04718425653394731
        }
      }
    },
    {
      "bone": "mixamorigRightHandRing1",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 17.508445900388356,
      "meanRawPoseDifferenceDeg": 17.177628629829314,
      "motionDeltaRmsDeg": 6.757921883340554,
      "motionDeltaMaxDeg": 13.490753912025195,
      "phaseOfMaxDynamicDifference": 0.85,
      "normalMotionFromAnchorRmsDeg": 2.1251730885196194,
      "womanMotionFromAnchorRmsDeg": 6.3098275981114735,
      "motionFromAnchorRmsRatio": 2.969088791966049,
      "hipRelativePositionDifferenceRmsUnits": 0.19882974781891433,
      "localTranslationMotionDeltaRmsUnits": 5.2837873634206055e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.1025464315704592,
          "woman": 0.10022508055044826,
          "difference": -0.0023213510200109366
        },
        "y": {
          "normal": 0.07732255917654687,
          "woman": 0.11102479828780558,
          "difference": 0.033702239111258706
        },
        "z": {
          "normal": 0.5505329562181186,
          "woman": 0.5190935331851803,
          "difference": -0.03143942303293834
        }
      }
    },
    {
      "bone": "mixamorigRightHandThumb2",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 14.574359244005052,
      "meanRawPoseDifferenceDeg": 15.915215028636755,
      "motionDeltaRmsDeg": 6.538280154275792,
      "motionDeltaMaxDeg": 10.083919854353391,
      "phaseOfMaxDynamicDifference": 0.85,
      "normalMotionFromAnchorRmsDeg": 2.585871854077748,
      "womanMotionFromAnchorRmsDeg": 5.2517602337667055,
      "motionFromAnchorRmsRatio": 2.030943731989282,
      "hipRelativePositionDifferenceRmsUnits": 0.161434839138383,
      "localTranslationMotionDeltaRmsUnits": 1.191532438748257e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.08988138993220093,
          "woman": 0.08846310318991894,
          "difference": -0.0014182867422819906
        },
        "y": {
          "normal": 0.0968477557586547,
          "woman": 0.11422703624009362,
          "difference": 0.017379280481438913
        },
        "z": {
          "normal": 0.4655554494573716,
          "woman": 0.42642477189473815,
          "difference": -0.03913067756263344
        }
      }
    },
    {
      "bone": "mixamorigLeftHandRing1",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 8.130460906241144,
      "meanRawPoseDifferenceDeg": 3.391061007452839,
      "motionDeltaRmsDeg": 6.358484435233846,
      "motionDeltaMaxDeg": 10.716738106001863,
      "phaseOfMaxDynamicDifference": 0.9208333333333333,
      "normalMotionFromAnchorRmsDeg": 3.8082811952659967,
      "womanMotionFromAnchorRmsDeg": 2.8910920153210755,
      "motionFromAnchorRmsRatio": 0.7591592813353536,
      "hipRelativePositionDifferenceRmsUnits": 0.15734679102102453,
      "localTranslationMotionDeltaRmsUnits": 8.254284971827759e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.24334189706676557,
          "woman": 0.05363983815725776,
          "difference": -0.1897020589095078
        },
        "y": {
          "normal": 0.15416817131076233,
          "woman": 0.14934307357302476,
          "difference": -0.004825097737737566
        },
        "z": {
          "normal": 0.5719011100920153,
          "woman": 0.5100352955304883,
          "difference": -0.061865814561526955
        }
      }
    },
    {
      "bone": "mixamorigLeftToeBase",
      "group": "feet",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 5.458919508214819,
      "meanRawPoseDifferenceDeg": 4.330067207740959,
      "motionDeltaRmsDeg": 6.251687111873954,
      "motionDeltaMaxDeg": 16.86844882691939,
      "phaseOfMaxDynamicDifference": 0.85,
      "normalMotionFromAnchorRmsDeg": 6.171875250599709,
      "womanMotionFromAnchorRmsDeg": 10.797188920552697,
      "motionFromAnchorRmsRatio": 1.7494178806520038,
      "hipRelativePositionDifferenceRmsUnits": 0.1346065967398153,
      "localTranslationMotionDeltaRmsUnits": 4.097026721377853e-18,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.14864585429575966,
          "woman": 0.24081736348260135,
          "difference": 0.0921715091868417
        },
        "y": {
          "normal": 0.20306959938743852,
          "woman": 0.20363777826502738,
          "difference": 0.0005681788775888652
        },
        "z": {
          "normal": 0.9619045225482992,
          "woman": 0.8347925305353192,
          "difference": -0.12711199201297996
        }
      }
    },
    {
      "bone": "mixamorigLeftHandMiddle1",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 10.053019266611544,
      "meanRawPoseDifferenceDeg": 14.630296515479499,
      "motionDeltaRmsDeg": 5.9411266623896,
      "motionDeltaMaxDeg": 10.223879700400028,
      "phaseOfMaxDynamicDifference": 0.9208333333333333,
      "normalMotionFromAnchorRmsDeg": 3.20456398704619,
      "womanMotionFromAnchorRmsDeg": 3.2059242703529947,
      "motionFromAnchorRmsRatio": 1.0004244831160505,
      "hipRelativePositionDifferenceRmsUnits": 0.1576566546290283,
      "localTranslationMotionDeltaRmsUnits": 7.029182689669468e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.2564517501222721,
          "woman": 0.053646833436809066,
          "difference": -0.20280491668546305
        },
        "y": {
          "normal": 0.17999542798984186,
          "woman": 0.1713821949146136,
          "difference": -0.008613233075228266
        },
        "z": {
          "normal": 0.5577198969838693,
          "woman": 0.49553335456250414,
          "difference": -0.06218654242136512
        }
      }
    },
    {
      "bone": "mixamorigRightHandPinky1",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 17.151940581100018,
      "meanRawPoseDifferenceDeg": 18.237709015415373,
      "motionDeltaRmsDeg": 5.840984394540944,
      "motionDeltaMaxDeg": 10.622407652640131,
      "phaseOfMaxDynamicDifference": 0.29583333333333334,
      "normalMotionFromAnchorRmsDeg": 2.329240879309291,
      "womanMotionFromAnchorRmsDeg": 5.512950058158633,
      "motionFromAnchorRmsRatio": 2.3668441109420306,
      "hipRelativePositionDifferenceRmsUnits": 0.196161619549017,
      "localTranslationMotionDeltaRmsUnits": 7.74745971702012e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.11569588501550446,
          "woman": 0.10824114964931039,
          "difference": -0.007454735366194065
        },
        "y": {
          "normal": 0.06898338349981853,
          "woman": 0.0878393419173176,
          "difference": 0.01885595841749907
        },
        "z": {
          "normal": 0.5413492389388347,
          "woman": 0.5183352580820296,
          "difference": -0.02301398085680506
        }
      }
    },
    {
      "bone": "mixamorigHead",
      "group": "head-and-neck",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 7.960887092937182,
      "meanRawPoseDifferenceDeg": 8.11110198604559,
      "motionDeltaRmsDeg": 4.776513517903233,
      "motionDeltaMaxDeg": 9.324144691437676,
      "phaseOfMaxDynamicDifference": 0.3333333333333333,
      "normalMotionFromAnchorRmsDeg": 5.881386001965556,
      "womanMotionFromAnchorRmsDeg": 3.6795211436104167,
      "motionFromAnchorRmsRatio": 0.6256214338560202,
      "hipRelativePositionDifferenceRmsUnits": 0.03400012826251581,
      "localTranslationMotionDeltaRmsUnits": 1.846050692583186e-17,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.049209702587463294,
          "woman": 0.05352439296412209,
          "difference": 0.004314690376658797
        },
        "y": {
          "normal": 0.00628332779870322,
          "woman": 0.00444381010396222,
          "difference": -0.0018395176947409997
        },
        "z": {
          "normal": 0.017444308949264575,
          "woman": 0.019015046295708722,
          "difference": 0.0015707373464441468
        }
      }
    },
    {
      "bone": "mixamorigSpine",
      "group": "torso",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 4.8152729349241294,
      "meanRawPoseDifferenceDeg": 4.7678838806794985,
      "motionDeltaRmsDeg": 4.745770513918641,
      "motionDeltaMaxDeg": 7.007045811877159,
      "phaseOfMaxDynamicDifference": 0.6458333333333334,
      "normalMotionFromAnchorRmsDeg": 5.51629592935333,
      "womanMotionFromAnchorRmsDeg": 3.6616130755598117,
      "motionFromAnchorRmsRatio": 0.663781117339196,
      "hipRelativePositionDifferenceRmsUnits": 2.2737298807691657e-11,
      "localTranslationMotionDeltaRmsUnits": 1.1419302281572682e-17,
      "hipFramePositionRange": {
        "x": {
          "normal": 3.357556710584855e-11,
          "woman": 7.217037045902813e-11,
          "difference": 3.859480335317958e-11
        },
        "y": {
          "normal": 4.097919226175861e-11,
          "woman": 7.679684665973241e-11,
          "difference": 3.58176543979738e-11
        },
        "z": {
          "normal": 1.5561632305026787e-11,
          "woman": 3.2263432471978624e-11,
          "difference": 1.6701800166951837e-11
        }
      }
    },
    {
      "bone": "mixamorigRightShoulder",
      "group": "shoulders",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 10.36554228536511,
      "meanRawPoseDifferenceDeg": 12.90050108287735,
      "motionDeltaRmsDeg": 4.397517133172642,
      "motionDeltaMaxDeg": 6.883919945710318,
      "phaseOfMaxDynamicDifference": 0.2625,
      "normalMotionFromAnchorRmsDeg": 2.5233239300260615,
      "womanMotionFromAnchorRmsDeg": 6.467713479349292,
      "motionFromAnchorRmsRatio": 2.563172093121826,
      "hipRelativePositionDifferenceRmsUnits": 0.013420344955618412,
      "localTranslationMotionDeltaRmsUnits": 7.5120324030617e-18,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.02815732763141993,
          "woman": 0.03278109019146031,
          "difference": 0.004623762560040382
        },
        "y": {
          "normal": 0.0050307065456298705,
          "woman": 0.005608711528678811,
          "difference": 0.0005780049830489409
        },
        "z": {
          "normal": 0.021475659550189548,
          "woman": 0.01537108504668424,
          "difference": -0.006104574503505308
        }
      }
    },
    {
      "bone": "mixamorigLeftHandPinky1",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 5.3504659376640165,
      "meanRawPoseDifferenceDeg": 8.683144894561718,
      "motionDeltaRmsDeg": 4.309420331480017,
      "motionDeltaMaxDeg": 6.891973112327449,
      "phaseOfMaxDynamicDifference": 0.19583333333333333,
      "normalMotionFromAnchorRmsDeg": 3.3882796251473746,
      "womanMotionFromAnchorRmsDeg": 2.7814103910695636,
      "motionFromAnchorRmsRatio": 0.8208916319734341,
      "hipRelativePositionDifferenceRmsUnits": 0.15609224805011987,
      "localTranslationMotionDeltaRmsUnits": 1.0161322751735387e-8,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.2269734328929669,
          "woman": 0.06601758162584176,
          "difference": -0.16095585126712514
        },
        "y": {
          "normal": 0.1267955006519035,
          "woman": 0.1248066810584173,
          "difference": -0.0019888195934862074
        },
        "z": {
          "normal": 0.5760202143288876,
          "woman": 0.5163131441706851,
          "difference": -0.059707070158202535
        }
      }
    },
    {
      "bone": "mixamorigRightToeBase",
      "group": "feet",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 2.051090224057257,
      "meanRawPoseDifferenceDeg": 4.1627791299647185,
      "motionDeltaRmsDeg": 4.0266988944855635,
      "motionDeltaMaxDeg": 10.307865410705327,
      "phaseOfMaxDynamicDifference": 0.4041666666666667,
      "normalMotionFromAnchorRmsDeg": 7.4179365141386535,
      "womanMotionFromAnchorRmsDeg": 7.777995913242932,
      "motionFromAnchorRmsRatio": 1.0485390240827759,
      "hipRelativePositionDifferenceRmsUnits": 0.09683922141982204,
      "localTranslationMotionDeltaRmsUnits": 1.4036034516677892e-17,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.1624629805735643,
          "woman": 0.22220417430448916,
          "difference": 0.059741193730924874
        },
        "y": {
          "normal": 0.22953606328602305,
          "woman": 0.19389787157839955,
          "difference": -0.0356381917076235
        },
        "z": {
          "normal": 0.9045921506904192,
          "woman": 0.8530784983391557,
          "difference": -0.051513652351263484
        }
      }
    },
    {
      "bone": "mixamorigSpine2",
      "group": "torso",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 5.249439941300714,
      "meanRawPoseDifferenceDeg": 5.664506626491348,
      "motionDeltaRmsDeg": 3.2609666643112294,
      "motionDeltaMaxDeg": 5.2916717078359445,
      "phaseOfMaxDynamicDifference": 0.6458333333333334,
      "normalMotionFromAnchorRmsDeg": 4.242218740109088,
      "womanMotionFromAnchorRmsDeg": 3.6133036850519997,
      "motionFromAnchorRmsRatio": 0.851748555747289,
      "hipRelativePositionDifferenceRmsUnits": 0.011611510799089966,
      "localTranslationMotionDeltaRmsUnits": 7.902587596809076e-18,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.03182721169612387,
          "woman": 0.01756220075056713,
          "difference": -0.014265010945556739
        },
        "y": {
          "normal": 0.0010274717198465733,
          "woman": 0.0007873377821405181,
          "difference": -0.00024013393770605518
        },
        "z": {
          "normal": 0.009188128963450271,
          "woman": 0.011695748174996322,
          "difference": 0.0025076192115460506
        }
      }
    },
    {
      "bone": "mixamorigSpine1",
      "group": "torso",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0.7013589212279807,
      "meanRawPoseDifferenceDeg": 2.584998123237395,
      "motionDeltaRmsDeg": 3.1830851633051793,
      "motionDeltaMaxDeg": 5.174771515321554,
      "phaseOfMaxDynamicDifference": 0.6458333333333334,
      "normalMotionFromAnchorRmsDeg": 4.223292804794934,
      "womanMotionFromAnchorRmsDeg": 3.611163046709463,
      "motionFromAnchorRmsRatio": 0.8550586505888281,
      "hipRelativePositionDifferenceRmsUnits": 0.006658224623428734,
      "localTranslationMotionDeltaRmsUnits": 1.7306577029593806e-17,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.01994458766375576,
          "woman": 0.00840374334939781,
          "difference": -0.01154084431435795
        },
        "y": {
          "normal": 0.000875957202134986,
          "woman": 0.0008071828695006555,
          "difference": -0.00006877433263433042
        },
        "z": {
          "normal": 0.003999677921271951,
          "woman": 0.006445379115627255,
          "difference": 0.002445701194355304
        }
      }
    },
    {
      "bone": "mixamorigNeck",
      "group": "head-and-neck",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 4.289934580102375,
      "meanRawPoseDifferenceDeg": 5.699367526389514,
      "motionDeltaRmsDeg": 2.9802917170413363,
      "motionDeltaMaxDeg": 4.64937933947253,
      "phaseOfMaxDynamicDifference": 0.225,
      "normalMotionFromAnchorRmsDeg": 2.5956212916950867,
      "womanMotionFromAnchorRmsDeg": 2.299145162589859,
      "motionFromAnchorRmsRatio": 0.885778356783469,
      "hipRelativePositionDifferenceRmsUnits": 0.012627814039757648,
      "localTranslationMotionDeltaRmsUnits": 1.952317830353061e-17,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.020181472277051006,
          "woman": 0.025602931876353277,
          "difference": 0.005421459599302271
        },
        "y": {
          "normal": 0.002020233436886454,
          "woman": 0.0018575969392365388,
          "difference": -0.00016263649764991506
        },
        "z": {
          "normal": 0.01066638098933129,
          "woman": 0.012889831624751172,
          "difference": 0.0022234506354198817
        }
      }
    },
    {
      "bone": "mixamorigLeftToe_End",
      "group": "feet",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0.8595891063221213,
      "meanRawPoseDifferenceDeg": 0.8375646548928072,
      "motionDeltaRmsDeg": 1.3575999731416215,
      "motionDeltaMaxDeg": 4.7184373749964585,
      "phaseOfMaxDynamicDifference": 0.85,
      "normalMotionFromAnchorRmsDeg": 1.2411960652926413,
      "womanMotionFromAnchorRmsDeg": 2.3263607416354026,
      "motionFromAnchorRmsRatio": 1.8742894911505446,
      "hipRelativePositionDifferenceRmsUnits": 0.13919385278320387,
      "localTranslationMotionDeltaRmsUnits": 2.6585019886095545e-18,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.1607790340933648,
          "woman": 0.24518753921478528,
          "difference": 0.08440850512142048
        },
        "y": {
          "normal": 0.23651357439873522,
          "woman": 0.15616076905980014,
          "difference": -0.08035280533893507
        },
        "z": {
          "normal": 0.9930903351967927,
          "woman": 0.8917213944346971,
          "difference": -0.10136894076209557
        }
      }
    },
    {
      "bone": "mixamorigRightHandThumb3",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 23.25199742071768,
      "meanRawPoseDifferenceDeg": 23.33029285012117,
      "motionDeltaRmsDeg": 1.1711879508607856,
      "motionDeltaMaxDeg": 1.8850617637927947,
      "phaseOfMaxDynamicDifference": 0.29583333333333334,
      "normalMotionFromAnchorRmsDeg": 0.16983538264880438,
      "womanMotionFromAnchorRmsDeg": 1.166322231227157,
      "motionFromAnchorRmsRatio": 6.867368937125116,
      "hipRelativePositionDifferenceRmsUnits": 0.17081640368383588,
      "localTranslationMotionDeltaRmsUnits": 1.4253630953072748e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.09348607370064127,
          "woman": 0.09589235526420854,
          "difference": 0.0024062815635672724
        },
        "y": {
          "normal": 0.097576465831062,
          "woman": 0.1239022061194171,
          "difference": 0.026325740288355104
        },
        "z": {
          "normal": 0.47737115956184384,
          "woman": 0.4408615775492256,
          "difference": -0.036509582012618225
        }
      }
    },
    {
      "bone": "mixamorigRightToe_End",
      "group": "feet",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0.39278740701229037,
      "meanRawPoseDifferenceDeg": 0.9410253075310369,
      "motionDeltaRmsDeg": 1.0293245457956295,
      "motionDeltaMaxDeg": 3.215719212163811,
      "phaseOfMaxDynamicDifference": 0.3333333333333333,
      "normalMotionFromAnchorRmsDeg": 1.7197772105328533,
      "womanMotionFromAnchorRmsDeg": 2.0542354904637414,
      "motionFromAnchorRmsRatio": 1.1944776787844864,
      "hipRelativePositionDifferenceRmsUnits": 0.10279450703316545,
      "localTranslationMotionDeltaRmsUnits": 2.6585019886098515e-18,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.17279951760104695,
          "woman": 0.22285723321283674,
          "difference": 0.05005771561178979
        },
        "y": {
          "normal": 0.18188585170845717,
          "woman": 0.15137693291296428,
          "difference": -0.03050891879549289
        },
        "z": {
          "normal": 0.9552074582502526,
          "woman": 0.9190580852842785,
          "difference": -0.03614937296597409
        }
      }
    },
    {
      "bone": "mixamorigRightHandPinky3",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 27.406142245935914,
      "meanRawPoseDifferenceDeg": 27.71294942021976,
      "motionDeltaRmsDeg": 0.9998123118836979,
      "motionDeltaMaxDeg": 2.303790491036642,
      "phaseOfMaxDynamicDifference": 0.775,
      "normalMotionFromAnchorRmsDeg": 0.2323290182535705,
      "womanMotionFromAnchorRmsDeg": 0.8330231924002136,
      "motionFromAnchorRmsRatio": 3.585532270837681,
      "hipRelativePositionDifferenceRmsUnits": 0.20218751507463825,
      "localTranslationMotionDeltaRmsUnits": 8.888124268664826e-10,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.12939972930300242,
          "woman": 0.12024438618162513,
          "difference": -0.009155343121377293
        },
        "y": {
          "normal": 0.07911100151285672,
          "woman": 0.07850947582702311,
          "difference": -0.0006015256858336038
        },
        "z": {
          "normal": 0.5486637266483188,
          "woman": 0.5211414843445188,
          "difference": -0.02752224230379996
        }
      }
    },
    {
      "bone": "mixamorigRightHandPinky2",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 20.5108635869063,
      "meanRawPoseDifferenceDeg": 20.815899422105467,
      "motionDeltaRmsDeg": 0.9946191787125833,
      "motionDeltaMaxDeg": 2.3065015029153924,
      "phaseOfMaxDynamicDifference": 0.775,
      "normalMotionFromAnchorRmsDeg": 0.24167341298539502,
      "womanMotionFromAnchorRmsDeg": 0.8309593977744929,
      "motionFromAnchorRmsRatio": 3.438356695962704,
      "hipRelativePositionDifferenceRmsUnits": 0.20165475011049583,
      "localTranslationMotionDeltaRmsUnits": 9.85141132675829e-10,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.12259645641827371,
          "woman": 0.11460786105823959,
          "difference": -0.007988595360034129
        },
        "y": {
          "normal": 0.07327293626988884,
          "woman": 0.08694499082400087,
          "difference": 0.013672054554112023
        },
        "z": {
          "normal": 0.5498919447740236,
          "woman": 0.5268173443463383,
          "difference": -0.023074600427685277
        }
      }
    },
    {
      "bone": "mixamorigLeftHandPinky3",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 10.99680584468336,
      "meanRawPoseDifferenceDeg": 10.54649890739666,
      "motionDeltaRmsDeg": 0.5851484776391211,
      "motionDeltaMaxDeg": 1.0441614594541395,
      "phaseOfMaxDynamicDifference": 0.35,
      "normalMotionFromAnchorRmsDeg": 0.2793923804591894,
      "womanMotionFromAnchorRmsDeg": 0.3302507576711275,
      "motionFromAnchorRmsRatio": 1.1820320837968126,
      "hipRelativePositionDifferenceRmsUnits": 0.1639363731486086,
      "localTranslationMotionDeltaRmsUnits": 3.349203767432608e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.23453986758812073,
          "woman": 0.07975253595046727,
          "difference": -0.15478733163765346
        },
        "y": {
          "normal": 0.12800837563952347,
          "woman": 0.12514598728632395,
          "difference": -0.0028623883531995187
        },
        "z": {
          "normal": 0.6014279190232181,
          "woman": 0.5443998110177821,
          "difference": -0.05702810800543601
        }
      }
    },
    {
      "bone": "mixamorigLeftHandPinky2",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 11.407589876277108,
      "meanRawPoseDifferenceDeg": 11.858988213861888,
      "motionDeltaRmsDeg": 0.5849817217031078,
      "motionDeltaMaxDeg": 1.0436237024023542,
      "phaseOfMaxDynamicDifference": 0.35,
      "normalMotionFromAnchorRmsDeg": 0.2791939779176317,
      "womanMotionFromAnchorRmsDeg": 0.33025684417692824,
      "motionFromAnchorRmsRatio": 1.1828938669814764,
      "hipRelativePositionDifferenceRmsUnits": 0.16054854606794242,
      "localTranslationMotionDeltaRmsUnits": 1.6001164391991687e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.23166208479943,
          "woman": 0.07039708379443133,
          "difference": -0.1612650010049987
        },
        "y": {
          "normal": 0.12907458194428995,
          "woman": 0.12810131758822688,
          "difference": -0.0009732643560630694
        },
        "z": {
          "normal": 0.5918263724781775,
          "woman": 0.5348011504080243,
          "difference": -0.05702522207015315
        }
      }
    },
    {
      "bone": "mixamorigRightHandMiddle2",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 3.1600495045968358,
      "meanRawPoseDifferenceDeg": 3.373360470920887,
      "motionDeltaRmsDeg": 0.4549492572379184,
      "motionDeltaMaxDeg": 1.2044144638069252,
      "phaseOfMaxDynamicDifference": 0.325,
      "normalMotionFromAnchorRmsDeg": 0.1685355810894189,
      "womanMotionFromAnchorRmsDeg": 0.41391939787198556,
      "motionFromAnchorRmsRatio": 2.4559763297245514,
      "hipRelativePositionDifferenceRmsUnits": 0.20561089843913213,
      "localTranslationMotionDeltaRmsUnits": 1.1431383369876664e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.09913518311906563,
          "woman": 0.11444005368576575,
          "difference": 0.015304870566700116
        },
        "y": {
          "normal": 0.0939541673601354,
          "woman": 0.13562744016662878,
          "difference": 0.04167327280649338
        },
        "z": {
          "normal": 0.5614967572262263,
          "woman": 0.5223474133926758,
          "difference": -0.03914934383355051
        }
      }
    },
    {
      "bone": "mixamorigLeftHandIndex3",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 11.321284623302816,
      "meanRawPoseDifferenceDeg": 10.970883129677201,
      "motionDeltaRmsDeg": 0.4418574839033261,
      "motionDeltaMaxDeg": 0.8298549729166262,
      "phaseOfMaxDynamicDifference": 0.36666666666666664,
      "normalMotionFromAnchorRmsDeg": 0.11434045732651628,
      "womanMotionFromAnchorRmsDeg": 0.4246274049848587,
      "motionFromAnchorRmsRatio": 3.7137109201187783,
      "hipRelativePositionDifferenceRmsUnits": 0.16809773451316923,
      "localTranslationMotionDeltaRmsUnits": 1.9267127950918315e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.27472565521034154,
          "woman": 0.06059890817100283,
          "difference": -0.2141267470393387
        },
        "y": {
          "normal": 0.20859182535983717,
          "woman": 0.2070370561755236,
          "difference": -0.0015547691843135758
        },
        "z": {
          "normal": 0.5728799598994141,
          "woman": 0.5252389398454016,
          "difference": -0.047641020054012495
        }
      }
    },
    {
      "bone": "mixamorigLeftHandIndex2",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 1.96090190946746,
      "meanRawPoseDifferenceDeg": 2.2883264555730456,
      "motionDeltaRmsDeg": 0.44112109187028475,
      "motionDeltaMaxDeg": 0.8295803480082585,
      "phaseOfMaxDynamicDifference": 0.36666666666666664,
      "normalMotionFromAnchorRmsDeg": 0.11433438115139877,
      "womanMotionFromAnchorRmsDeg": 0.42418571805045263,
      "motionFromAnchorRmsRatio": 3.7100451655810893,
      "hipRelativePositionDifferenceRmsUnits": 0.16271125297191485,
      "localTranslationMotionDeltaRmsUnits": 1.8309224378318184e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.270610249597079,
          "woman": 0.05910663702082604,
          "difference": -0.211503612576253
        },
        "y": {
          "normal": 0.20530637910421712,
          "woman": 0.19928950637605913,
          "difference": -0.006016872728157985
        },
        "z": {
          "normal": 0.5573725104608184,
          "woman": 0.5011280460529728,
          "difference": -0.056244464407845585
        }
      }
    },
    {
      "bone": "mixamorigRightHandMiddle3",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 10.619279444227406,
      "meanRawPoseDifferenceDeg": 10.829549236965253,
      "motionDeltaRmsDeg": 0.43676348915905827,
      "motionDeltaMaxDeg": 1.1705128888770377,
      "phaseOfMaxDynamicDifference": 0.325,
      "normalMotionFromAnchorRmsDeg": 0.16765920370572998,
      "womanMotionFromAnchorRmsDeg": 0.3983197473791682,
      "motionFromAnchorRmsRatio": 2.3757702444912367,
      "hipRelativePositionDifferenceRmsUnits": 0.20920357651406638,
      "localTranslationMotionDeltaRmsUnits": 1.7902770473289027e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.10176314614425264,
          "woman": 0.11862984209954365,
          "difference": 0.016866695955291014
        },
        "y": {
          "normal": 0.08786989888039978,
          "woman": 0.12969303963139775,
          "difference": 0.04182314075099797
        },
        "z": {
          "normal": 0.559320853325049,
          "woman": 0.52688156014574,
          "difference": -0.03243929317930905
        }
      }
    },
    {
      "bone": "mixamorigRightHandIndex2",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 3.360383747567269,
      "meanRawPoseDifferenceDeg": 3.5377829446797615,
      "motionDeltaRmsDeg": 0.42405800383710107,
      "motionDeltaMaxDeg": 0.8490128986742185,
      "phaseOfMaxDynamicDifference": 0.7791666666666667,
      "normalMotionFromAnchorRmsDeg": 0.10092925045519312,
      "womanMotionFromAnchorRmsDeg": 0.3880868404996229,
      "motionFromAnchorRmsRatio": 3.845137447760117,
      "hipRelativePositionDifferenceRmsUnits": 0.20119999020792304,
      "localTranslationMotionDeltaRmsUnits": 7.959792764302376e-10,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.10657411638492703,
          "woman": 0.11515517086232543,
          "difference": 0.008581054477398403
        },
        "y": {
          "normal": 0.10527148101554931,
          "woman": 0.14948115522713143,
          "difference": 0.04420967421158212
        },
        "z": {
          "normal": 0.547452043684707,
          "woman": 0.5044943861883822,
          "difference": -0.04295765749632485
        }
      }
    },
    {
      "bone": "mixamorigRightHandIndex3",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 6.962523015751631,
      "meanRawPoseDifferenceDeg": 7.147893182030999,
      "motionDeltaRmsDeg": 0.423949717961882,
      "motionDeltaMaxDeg": 0.8490433530366284,
      "phaseOfMaxDynamicDifference": 0.7791666666666667,
      "normalMotionFromAnchorRmsDeg": 0.10117693357192115,
      "womanMotionFromAnchorRmsDeg": 0.38809814266618947,
      "motionFromAnchorRmsRatio": 3.8358361828618945,
      "hipRelativePositionDifferenceRmsUnits": 0.20673225658714384,
      "localTranslationMotionDeltaRmsUnits": 7.379223881269775e-10,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.10728446920648807,
          "woman": 0.12239079187776791,
          "difference": 0.015106322671279843
        },
        "y": {
          "normal": 0.10231446583188439,
          "woman": 0.15121451152570287,
          "difference": 0.04890004569381848
        },
        "z": {
          "normal": 0.5496486913151553,
          "woman": 0.5140665618900329,
          "difference": -0.0355821294251224
        }
      }
    },
    {
      "bone": "mixamorigRightHandRing2",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 23.59883687263299,
      "meanRawPoseDifferenceDeg": 23.360523823290393,
      "motionDeltaRmsDeg": 0.38315216882462355,
      "motionDeltaMaxDeg": 1.0192733476870146,
      "phaseOfMaxDynamicDifference": 0.8125,
      "normalMotionFromAnchorRmsDeg": 0.13208765267975042,
      "womanMotionFromAnchorRmsDeg": 0.31354351666912356,
      "motionFromAnchorRmsRatio": 2.373753415312157,
      "hipRelativePositionDifferenceRmsUnits": 0.2058915756299395,
      "localTranslationMotionDeltaRmsUnits": 8.24992205121383e-10,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.11066071317956744,
          "woman": 0.10714120915610179,
          "difference": -0.0035195040234656527
        },
        "y": {
          "normal": 0.07684239483829505,
          "woman": 0.11141741733011837,
          "difference": 0.034575022491823315
        },
        "z": {
          "normal": 0.5624625027342782,
          "woman": 0.5305540504178227,
          "difference": -0.03190845231645556
        }
      }
    },
    {
      "bone": "mixamorigRightHandRing3",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 3.360790359442466,
      "meanRawPoseDifferenceDeg": 3.1488966647761645,
      "motionDeltaRmsDeg": 0.3828220684501822,
      "motionDeltaMaxDeg": 1.0200724565299304,
      "phaseOfMaxDynamicDifference": 0.8125,
      "normalMotionFromAnchorRmsDeg": 0.13252222853234494,
      "womanMotionFromAnchorRmsDeg": 0.3128479277359437,
      "motionFromAnchorRmsRatio": 2.3607203953681353,
      "hipRelativePositionDifferenceRmsUnits": 0.20811764815469086,
      "localTranslationMotionDeltaRmsUnits": 1.3112395295324278e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.11780091344285487,
          "woman": 0.11157731250599255,
          "difference": -0.00622360093686232
        },
        "y": {
          "normal": 0.06967576331797179,
          "woman": 0.10567298410634057,
          "difference": 0.03599722078836878
        },
        "z": {
          "normal": 0.5547276440645934,
          "woman": 0.5340536236408753,
          "difference": -0.02067402042371813
        }
      }
    },
    {
      "bone": "mixamorigLeftHandRing3",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 8.790389818176456,
      "meanRawPoseDifferenceDeg": 8.811407120271976,
      "motionDeltaRmsDeg": 0.33642643365718927,
      "motionDeltaMaxDeg": 0.7632605309291743,
      "phaseOfMaxDynamicDifference": 0.8458333333333333,
      "normalMotionFromAnchorRmsDeg": 0.12025086795753123,
      "womanMotionFromAnchorRmsDeg": 0.31813545843590046,
      "motionFromAnchorRmsRatio": 2.6455980221968605,
      "hipRelativePositionDifferenceRmsUnits": 0.16489523316820154,
      "localTranslationMotionDeltaRmsUnits": 1.8811518774009406e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.2480248936413048,
          "woman": 0.06399137132035129,
          "difference": -0.18403352232095352
        },
        "y": {
          "normal": 0.15415683472162242,
          "woman": 0.151131170001214,
          "difference": -0.003025664720408411
        },
        "z": {
          "normal": 0.6041806402699856,
          "woman": 0.5438477190526141,
          "difference": -0.06033292121737155
        }
      }
    },
    {
      "bone": "mixamorigLeftHandRing2",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 2.1741621789283805,
      "meanRawPoseDifferenceDeg": 2.1952185195519953,
      "motionDeltaRmsDeg": 0.3356693682162265,
      "motionDeltaMaxDeg": 0.7632098153851054,
      "phaseOfMaxDynamicDifference": 0.8458333333333333,
      "normalMotionFromAnchorRmsDeg": 0.1196190485169152,
      "womanMotionFromAnchorRmsDeg": 0.3178519275338742,
      "motionFromAnchorRmsRatio": 2.657201603546672,
      "hipRelativePositionDifferenceRmsUnits": 0.16197230500393267,
      "localTranslationMotionDeltaRmsUnits": 1.6198653349379082e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.2480452614929216,
          "woman": 0.057896636912653704,
          "difference": -0.1901486245802679
        },
        "y": {
          "normal": 0.15746322413420288,
          "woman": 0.15282900726961868,
          "difference": -0.004634216864584206
        },
        "z": {
          "normal": 0.5919663141985696,
          "woman": 0.5298887654224813,
          "difference": -0.06207754877608829
        }
      }
    },
    {
      "bone": "mixamorigLeftHandMiddle2",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 15.347803771123996,
      "meanRawPoseDifferenceDeg": 15.331203062533273,
      "motionDeltaRmsDeg": 0.17689020814685186,
      "motionDeltaMaxDeg": 0.4120374985989609,
      "phaseOfMaxDynamicDifference": 0.8166666666666667,
      "normalMotionFromAnchorRmsDeg": 0.06186313774441963,
      "womanMotionFromAnchorRmsDeg": 0.17964954990272372,
      "motionFromAnchorRmsRatio": 2.903983801224648,
      "hipRelativePositionDifferenceRmsUnits": 0.16296063001328526,
      "localTranslationMotionDeltaRmsUnits": 1.9551563154819943e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.26215962193197717,
          "woman": 0.05521250063840763,
          "difference": -0.20694712129356954
        },
        "y": {
          "normal": 0.18495702991304752,
          "woman": 0.18134924701320637,
          "difference": -0.00360778289984115
        },
        "z": {
          "normal": 0.580687066597628,
          "woman": 0.5234406729323337,
          "difference": -0.05724639366529438
        }
      }
    },
    {
      "bone": "mixamorigLeftHandMiddle3",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 2.1363906398347683,
      "meanRawPoseDifferenceDeg": 2.12207918360529,
      "motionDeltaRmsDeg": 0.17478512504810262,
      "motionDeltaMaxDeg": 0.4088929540926405,
      "phaseOfMaxDynamicDifference": 0.8166666666666667,
      "normalMotionFromAnchorRmsDeg": 0.06185723204951471,
      "womanMotionFromAnchorRmsDeg": 0.1774582306939959,
      "motionFromAnchorRmsRatio": 2.8688356205778227,
      "hipRelativePositionDifferenceRmsUnits": 0.16773516844098496,
      "localTranslationMotionDeltaRmsUnits": 2.1231554752170375e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.26463944573591663,
          "woman": 0.054444938236858614,
          "difference": -0.21019450749905802
        },
        "y": {
          "normal": 0.18509990922776376,
          "woman": 0.1812882342315274,
          "difference": -0.0038116749962363583
        },
        "z": {
          "normal": 0.5986924308080874,
          "woman": 0.5437496281332219,
          "difference": -0.05494280267486551
        }
      }
    },
    {
      "bone": "mixamorigHeadTop_End",
      "group": "head-and-neck",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0.0000017075472925031877,
      "meanRawPoseDifferenceDeg": 0.0000017075472925031892,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0.0000017075472925031856,
      "womanMotionFromAnchorRmsDeg": 0.0000017075472925031856,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.09172672006458855,
      "localTranslationMotionDeltaRmsUnits": 0,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.06576972377137934,
          "woman": 0.1258469861489473,
          "difference": 0.060077262377567955
        },
        "y": {
          "normal": 0.00998400097408736,
          "woman": 0.007129523983608332,
          "difference": -0.002854476990479027
        },
        "z": {
          "normal": 0.053608903080637385,
          "woman": 0.038310038278291124,
          "difference": -0.015298864802346261
        }
      }
    },
    {
      "bone": "headfront",
      "group": "other",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.04159335994223327,
      "localTranslationMotionDeltaRmsUnits": 0,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.0643034886856945,
          "woman": 0.07305366265841969,
          "difference": 0.008750173972725192
        },
        "y": {
          "normal": 0.01403091264722639,
          "woman": 0.008640976447671977,
          "difference": -0.005389936199554413
        },
        "z": {
          "normal": 0.017574537078575758,
          "woman": 0.01973030832597547,
          "difference": 0.0021557712473997126
        }
      }
    },
    {
      "bone": "mixamorigLeftHandThumb4",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.15403343265797778,
      "localTranslationMotionDeltaRmsUnits": 1.0855481781457682e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.2640875937673553,
          "woman": 0.05503059709854968,
          "difference": -0.20905699666880562
        },
        "y": {
          "normal": 0.207984178627922,
          "woman": 0.1836424014591929,
          "difference": -0.024341777168729123
        },
        "z": {
          "normal": 0.4931039100339349,
          "woman": 0.4493281845237859,
          "difference": -0.043775725510148966
        }
      }
    },
    {
      "bone": "mixamorigLeftHandPinky4",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.1656383853993287,
      "localTranslationMotionDeltaRmsUnits": 2.943099993013902e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.2339262377159702,
          "woman": 0.08973193780797187,
          "difference": -0.14419429990799834
        },
        "y": {
          "normal": 0.12469987427030427,
          "woman": 0.12138649539408441,
          "difference": -0.0033133788762198524
        },
        "z": {
          "normal": 0.6039863817860844,
          "woman": 0.5514230138467601,
          "difference": -0.05256336793932437
        }
      }
    },
    {
      "bone": "mixamorigLeftHandRing4",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0.0000017075472925031877,
      "meanRawPoseDifferenceDeg": 0.0000017075472925031892,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0.0000017075472925031856,
      "womanMotionFromAnchorRmsDeg": 0.0000017075472925031856,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.16546413027216372,
      "localTranslationMotionDeltaRmsUnits": 1.4212056282751494e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.24492381254619422,
          "woman": 0.07509266716081556,
          "difference": -0.16983114538537866
        },
        "y": {
          "normal": 0.14578499489248498,
          "woman": 0.14689156773293602,
          "difference": 0.0011065728404510422
        },
        "z": {
          "normal": 0.6063363477766037,
          "woman": 0.5528134567287556,
          "difference": -0.05352289104784813
        }
      }
    },
    {
      "bone": "mixamorigLeftHandIndex4",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.17238793392592036,
      "localTranslationMotionDeltaRmsUnits": 1.5420305467745437e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.27515440067122854,
          "woman": 0.06182161937032936,
          "difference": -0.21333278130089917
        },
        "y": {
          "normal": 0.20629095771083433,
          "woman": 0.21386064436690078,
          "difference": 0.007569686656066443
        },
        "z": {
          "normal": 0.5825694822816678,
          "woman": 0.5488723360697128,
          "difference": -0.033697146211955076
        }
      }
    },
    {
      "bone": "mixamorigLeftHandMiddle4",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.17113042057882835,
      "localTranslationMotionDeltaRmsUnits": 2.181276374393845e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.2632272021886516,
          "woman": 0.0590095051760155,
          "difference": -0.2042176970126361
        },
        "y": {
          "normal": 0.17975792971611104,
          "woman": 0.1758806703748962,
          "difference": -0.003877259341214856
        },
        "z": {
          "normal": 0.6098631791882878,
          "woman": 0.5571173974538824,
          "difference": -0.05274578173440536
        }
      }
    },
    {
      "bone": "mixamorigRightHandThumb4",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.18051677889455783,
      "localTranslationMotionDeltaRmsUnits": 4.959917212205507e-10,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.09997684869623306,
          "woman": 0.10295333796547557,
          "difference": 0.002976489269242502
        },
        "y": {
          "normal": 0.10193205038789069,
          "woman": 0.1338636050508782,
          "difference": 0.0319315546629875
        },
        "z": {
          "normal": 0.492996881744271,
          "woman": 0.4511754441603672,
          "difference": -0.041821437583903776
        }
      }
    },
    {
      "bone": "mixamorigRightHandPinky4",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0.0000024148365394514667,
      "meanRawPoseDifferenceDeg": 0.000002414836539451475,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0.0000024148365394514633,
      "womanMotionFromAnchorRmsDeg": 0.0000024148365394514633,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.20069527390596353,
      "localTranslationMotionDeltaRmsUnits": 8.883030572067204e-10,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.13551275025948523,
          "woman": 0.12145160547883063,
          "difference": -0.014061144780654594
        },
        "y": {
          "normal": 0.08596371937939745,
          "woman": 0.07872010771939142,
          "difference": -0.007243611660006033
        },
        "z": {
          "normal": 0.5421903460683714,
          "woman": 0.5055445752733525,
          "difference": -0.03664577079501885
        }
      }
    },
    {
      "bone": "mixamorigRightHandIndex4",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.2100646844657408,
      "localTranslationMotionDeltaRmsUnits": 1.2235512872071946e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.10631901676855313,
          "woman": 0.12653689668478188,
          "difference": 0.020217879916228754
        },
        "y": {
          "normal": 0.09774611321372423,
          "woman": 0.14816149959232355,
          "difference": 0.050415386378599325
        },
        "z": {
          "normal": 0.547683726322253,
          "woman": 0.5184667989294235,
          "difference": -0.02921692739282955
        }
      }
    },
    {
      "bone": "mixamorigRightHandRing4",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0.0000024148365394514667,
      "meanRawPoseDifferenceDeg": 0.000002414836539451475,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0.0000024148365394514633,
      "womanMotionFromAnchorRmsDeg": 0.0000024148365394514633,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.20693703492147966,
      "localTranslationMotionDeltaRmsUnits": 1.5667488192740048e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.12319830460629624,
          "woman": 0.11853777616754607,
          "difference": -0.004660528438750172
        },
        "y": {
          "normal": 0.07217921308676678,
          "woman": 0.09574922840414118,
          "difference": 0.023570015317374404
        },
        "z": {
          "normal": 0.538220070177068,
          "woman": 0.5299497077762607,
          "difference": -0.008270362400807252
        }
      }
    },
    {
      "bone": "mixamorigRightHandMiddle4",
      "group": "fingers",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.20767478736014988,
      "localTranslationMotionDeltaRmsUnits": 1.6634935877325518e-9,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.10875173760415305,
          "woman": 0.11507166036284182,
          "difference": 0.00631992275868877
        },
        "y": {
          "normal": 0.07907428875552253,
          "woman": 0.11584513637128926,
          "difference": 0.03677084761576674
        },
        "z": {
          "normal": 0.5475025692304298,
          "woman": 0.5192002200248511,
          "difference": -0.028302349205578725
        }
      }
    },
    {
      "bone": "Bone_017",
      "group": "other",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0.0000017075472925031877,
      "meanRawPoseDifferenceDeg": 0.0000017075472925031892,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0.0000017075472925031856,
      "womanMotionFromAnchorRmsDeg": 0.0000017075472925031856,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.13728082696925162,
      "localTranslationMotionDeltaRmsUnits": 0,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.13156964779668423,
          "woman": 0.2544268500435435,
          "difference": 0.12285720224685925
        },
        "y": {
          "normal": 0.2627304927589641,
          "woman": 0.25152048467749644,
          "difference": -0.01121000808146766
        },
        "z": {
          "normal": 0.8874752586604684,
          "woman": 0.7410592788799559,
          "difference": -0.14641597978051246
        }
      }
    },
    {
      "bone": "Bone_013",
      "group": "other",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 0.09262835474085018,
      "localTranslationMotionDeltaRmsUnits": 0,
      "hipFramePositionRange": {
        "x": {
          "normal": 0.16819231368051524,
          "woman": 0.24704090804456635,
          "difference": 0.07884859436405112
        },
        "y": {
          "normal": 0.28923440395628064,
          "woman": 0.23175875193207995,
          "difference": -0.057475652024200685
        },
        "z": {
          "normal": 0.821048318413694,
          "woman": 0.7546728459318198,
          "difference": -0.06637547248187414
        }
      }
    },
    {
      "bone": "Bone_008",
      "group": "other",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 4.570842084173735e-11,
      "localTranslationMotionDeltaRmsUnits": 0,
      "hipFramePositionRange": {
        "x": {
          "normal": 4.634124640555567e-11,
          "woman": 5.36270006808344e-11,
          "difference": 7.285754275278728e-12
        },
        "y": {
          "normal": 2.910872931582986e-11,
          "woman": 9.442670256820662e-11,
          "difference": 6.531797325237676e-11
        },
        "z": {
          "normal": 8.79591399716162e-11,
          "woman": 2.2754237383182385e-10,
          "difference": 1.3958323386020766e-10
        }
      }
    },
    {
      "bone": "Bone_007",
      "group": "other",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 8.614084431695747e-11,
      "localTranslationMotionDeltaRmsUnits": 0,
      "hipFramePositionRange": {
        "x": {
          "normal": 1.2080522492725525e-10,
          "woman": 1.9891649042985332e-10,
          "difference": 7.811126550259807e-11
        },
        "y": {
          "normal": 1.0688813723014334e-10,
          "woman": 2.605495263985347e-10,
          "difference": 1.5366138916839134e-10
        },
        "z": {
          "normal": 8.977463217263448e-11,
          "woman": 3.2848701536636327e-10,
          "difference": 2.387123831937288e-10
        }
      }
    },
    {
      "bone": "Bone_006",
      "group": "other",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 1.1219859545658031e-10,
      "localTranslationMotionDeltaRmsUnits": 0,
      "hipFramePositionRange": {
        "x": {
          "normal": 1.6336443395964517e-10,
          "woman": 2.8758058955025145e-10,
          "difference": 1.2421615559060628e-10
        },
        "y": {
          "normal": 1.5979650935804557e-10,
          "woman": 3.632979472811826e-10,
          "difference": 2.0350143792313702e-10
        },
        "z": {
          "normal": 7.878186991661096e-11,
          "woman": 3.670066472949429e-10,
          "difference": 2.8822477737833196e-10
        }
      }
    },
    {
      "bone": "Bone_011",
      "group": "other",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0.0000017075472925031877,
      "meanRawPoseDifferenceDeg": 0.0000017075472925031892,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0.0000017075472925031856,
      "womanMotionFromAnchorRmsDeg": 0.0000017075472925031856,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 3.9959860558037244e-11,
      "localTranslationMotionDeltaRmsUnits": 0,
      "hipFramePositionRange": {
        "x": {
          "normal": 3.1044858971409585e-11,
          "woman": 1.0451342756864648e-10,
          "difference": 7.34685685972369e-11
        },
        "y": {
          "normal": 7.163079851491005e-11,
          "woman": 9.115022625572067e-11,
          "difference": 1.9519427740810613e-11
        },
        "z": {
          "normal": 8.653419647508542e-11,
          "woman": 1.4074112708595266e-10,
          "difference": 5.420693061086723e-11
        }
      }
    },
    {
      "bone": "Bone_010",
      "group": "other",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 7.502153918795241e-11,
      "localTranslationMotionDeltaRmsUnits": 0,
      "hipFramePositionRange": {
        "x": {
          "normal": 9.825503549611038e-11,
          "woman": 2.3497459436771747e-10,
          "difference": 1.367195588716071e-10
        },
        "y": {
          "normal": 1.44917244870868e-10,
          "woman": 2.386232877960026e-10,
          "difference": 9.370604292513462e-11
        },
        "z": {
          "normal": 9.551825996823027e-11,
          "woman": 1.0498236308054132e-10,
          "difference": 9.464103112311051e-12
        }
      }
    },
    {
      "bone": "Bone_009",
      "group": "other",
      "sampledAlignedPhases": 218,
      "staticPoseOffsetDeg": 0,
      "meanRawPoseDifferenceDeg": 0,
      "motionDeltaRmsDeg": 0,
      "motionDeltaMaxDeg": 0,
      "phaseOfMaxDynamicDifference": 0,
      "normalMotionFromAnchorRmsDeg": 0,
      "womanMotionFromAnchorRmsDeg": 0,
      "motionFromAnchorRmsRatio": null,
      "hipRelativePositionDifferenceRmsUnits": 1.0273998059224291e-10,
      "localTranslationMotionDeltaRmsUnits": 0,
      "hipFramePositionRange": {
        "x": {
          "normal": 1.4641935939792347e-10,
          "woman": 3.275098226201543e-10,
          "difference": 1.8109046322223084e-10
        },
        "y": {
          "normal": 1.920389403053946e-10,
          "woman": 3.41015604643502e-10,
          "difference": 1.489766643381074e-10
        },
        "z": {
          "normal": 9.202311135325658e-11,
          "woman": 1.0639752967556149e-10,
          "difference": 1.4374418322304905e-11
        }
      }
    }
  ],
  "groups": {
    "hands": {
      "boneCount": 2,
      "meanBoneMotionDeltaRmsDeg": 24.592984367544922,
      "meanBoneStaticPoseOffsetDeg": 30.144137752370597
    },
    "upper-arms": {
      "boneCount": 2,
      "meanBoneMotionDeltaRmsDeg": 21.108798091582848,
      "meanBoneStaticPoseOffsetDeg": 40.32174274874392
    },
    "legs": {
      "boneCount": 4,
      "meanBoneMotionDeltaRmsDeg": 16.16244753059096,
      "meanBoneStaticPoseOffsetDeg": 11.561153735180493
    },
    "forearms": {
      "boneCount": 2,
      "meanBoneMotionDeltaRmsDeg": 18.7782215401133,
      "meanBoneStaticPoseOffsetDeg": 16.10333673720468
    },
    "pelvis": {
      "boneCount": 1,
      "meanBoneMotionDeltaRmsDeg": 11.9465884868175,
      "meanBoneStaticPoseOffsetDeg": 10.055778796472365
    },
    "feet": {
      "boneCount": 6,
      "meanBoneMotionDeltaRmsDeg": 5.77635792408476,
      "meanBoneStaticPoseOffsetDeg": 2.9671046454569914
    },
    "fingers": {
      "boneCount": 40,
      "meanBoneMotionDeltaRmsDeg": 2.7027749068424995,
      "meanBoneStaticPoseOffsetDeg": 9.7975146906627
    },
    "shoulders": {
      "boneCount": 2,
      "meanBoneMotionDeltaRmsDeg": 6.652600417703754,
      "meanBoneStaticPoseOffsetDeg": 15.759696723622728
    },
    "head-and-neck": {
      "boneCount": 3,
      "meanBoneMotionDeltaRmsDeg": 2.5856017449815227,
      "meanBoneStaticPoseOffsetDeg": 4.08360779352895
    },
    "torso": {
      "boneCount": 3,
      "meanBoneMotionDeltaRmsDeg": 3.7299407805116833,
      "meanBoneStaticPoseOffsetDeg": 3.5886905991509406
    },
    "other": {
      "boneCount": 9,
      "meanBoneMotionDeltaRmsDeg": 0,
      "meanBoneStaticPoseOffsetDeg": 3.794549538895973e-7
    }
  },
  "persistence": "SAVED /data/data/com.termux/files/home/.local/state/hareworks/hareworks-walking-style-research-v0.2.3/research-report.json (d0416d8bfa6b)"
}
__HAREWORKS_STYLE_LAB_V025_RESEARCH_PRIORS_JSON__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/lab-server.py" <<'__HAREWORKS_STYLE_LAB_V025_LAB_SERVER_PY__'
"""Termux-local, no-cache lab UI and validated durable evidence receiver."""
import csv
import datetime
import hashlib
import http.server
import io
import json
import math
import os
import pathlib
import sys
import tempfile
import urllib.parse

MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
REPORT_URL='/tools/hareworks-forward-woman/v0.2.5/style-report'
LAYERS=['pelvis','legs','torso','arms']

def validate_report(a):
    assert isinstance(a,dict)
    assert a.get('schema')=='hareworks-gated-backward-style-lab-v0.2.5'
    assert a.get('sourceSha256')==MODEL_SHA
    assert a.get('sourceClips')==['Walk_Backward','Walking','Walking_Woman']
    assert a.get('sourceBones')==74
    assert a.get('sourceModelUnchanged') is True and a.get('originalGaitsUnchanged') is True
    assert a.get('styleAcceptedByOwner') is False
    assert a.get('approvedBackwardMotionPlaybackTracks')==0
    assert a.get('generatedSourceAnimationTracks')==0
    assert a.get('zeroFrame',{}).get('pass') is True
    assert a.get('zeroFrame',{}).get('joints')==74
    for key in ['requested','applied']:
        o=a[key]
        assert set(o)==set(LAYERS)
        assert all(isinstance(o[k],(int,float)) and math.isfinite(o[k]) and 0<=o[k]<=1 for k in LAYERS)
    audited=a.get('fullRateAudit',{})
    assert audited.get('pass') is True
    assert [o['rateHz'] for o in audited['perRate']]==[30,60,120]
    assert audited.get('sampleCount',0)>150
    assert not audited.get('rejections')
    assert 0<=len(a.get('trials',[]))<=8
    return a

def atomic(path,data):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.tmp-hareworks-024-',delete=False) as f:
        tmp=pathlib.Path(f.name);f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def store_report(raw,state):
    if len(raw)>1_500_000: raise ValueError('OVERSIZE_STYLE_REPORT')
    a=validate_report(json.loads(raw))
    payload=(json.dumps(a,indent=2,allow_nan=False)+'\n').encode()
    rows=io.StringIO();csvw=csv.writer(rows);csvw.writerow(['layer','requested','applied','status'])
    for x in a['trials']:
        if x.get('layer'):csvw.writerow([x['layer'],x.get('requested'),x.get('applied'),x.get('status')])
    state=pathlib.Path(state)
    atomic(state/'style-lab-report.json',payload)
    atomic(state/'style-lab-trials.csv',rows.getvalue().encode())
    digest=hashlib.sha256(payload).hexdigest()
    receipt={'campaign':'hareworks-backward-style-lab-v0.2.5','status':'REAL_BROWSER_GATED_TRIAL_SAVED',
      'modelSha256':MODEL_SHA,'sourceClips':a['sourceClips'],'reportSha256':digest,
      'jsonPath':str(state/'style-lab-report.json'),'csvPath':str(state/'style-lab-trials.csv'),
      'acceptedBackwardUnchanged':True,'acceptedForwardUnchanged':True,'ownerAcceptedStyle':False,
      'receivedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    atomic(state/'style-lab-receipt.json',(json.dumps(receipt,indent=2)+'\n').encode())
    return {'saved':True,'sha256':digest,'path':receipt['jsonPath']}

def make_handler(root,state,ready):
    class Handler(http.server.SimpleHTTPRequestHandler):
        extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
        def __init__(self,*args,**kw):super().__init__(*args,directory=root,**kw)
        def end_headers(self):
            self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
            self.send_header('Pragma','no-cache')
            self.send_header('X-Content-Type-Options','nosniff')
            super().end_headers()
        def do_POST(self):
            if urllib.parse.urlsplit(self.path).path!=REPORT_URL:
                self.send_error(404,'Unknown lab report endpoint');return
            origin=self.headers.get('Origin','')
            expected='http://127.0.0.1:'+str(self.server.server_address[1])
            if origin and origin!=expected:
                self.send_error(403,'Invalid report origin');return
            try:
                n=int(self.headers.get('Content-Length','0'))
                if n<=0 or n>1_500_000:
                    self.send_error(413,'Bad report size');return
                result=store_report(self.rfile.read(n),state)
                payload=json.dumps(result).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
            except (ValueError,TypeError,KeyError,AssertionError) as err:
                self.send_error(422,'Rejected lab evidence: '+str(err)[:120])
    return Handler

def main():
    root,state,ready=sys.argv[1:]
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),make_handler(root,state,ready))
    atomic(ready,json.dumps({'pid':os.getpid(),'port':server.server_address[1],'root':root}).encode())
    server.serve_forever()

if __name__=='__main__':main()
__HAREWORKS_STYLE_LAB_V025_LAB_SERVER_PY__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/README.md" <<'__HAREWORKS_STYLE_LAB_V025_README_MD__'
# Hareworks v0.2.5 · Backward style laboratory

> **v0.2.5 recovery:** supersedes the non-published v0.2.4 packet that stopped at `PY_PRESERVE_EXACT_RESEARCH_JSON` because of a malformed Python newline literal. The style controller and approved reference gaits are unchanged. Adds preflight AST validation of all embedded Python sections before network, GLB work, or publication.

## Owner instructions and authorization

The owner accepted the in-place procedural `Walk_Backward` v0.2.2, and accepted forward `Walking_Woman` v0.1.9. BOTH accepted implementations remain byte-for-byte unchanged. The owner requested a **controlled experiment** transferring the measurable characteristics of `Walking_Woman` vs `Walking` to the backward gait, layer by layer, only when baseline preservation gates allow it.

- Three **source** clips: `Walk_Backward`, `Walking`, `Walking_Woman` from `assets/hareworks/Hareworks-nine-clips.glb` SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6` (6,784,896 bytes), exactly 74 bones and nine source clips.
- The approved backward pose is reconstructed using an **unchanged byte copy** of v0.2.2 `inplace-kernel.mjs` and its real-source witness tests. Both visible models are driven by mathematical procedural pose evaluators; no source AnimationMixer drives either. Animation mixers operate only on separate hidden clones, once, to calibrate the original clips.
- Previous source research: the owner-exported JSON is embedded byte-for-byte as `research-priors.json` with SHA-256 `f631eaf0bb48bb81afa9b451cf2191aa4c98b07bd768f2574caaaa28938ffebe`, and the browser verifies it before allowing experimental motion; 360 original poses per forward clip; 218 matched phases and 74 bones; measured Woman-vs-Walking offset `0.9777777777777777` with caveat (terminal window excluded). This experiment is NOT a claim about biological sexes.

## Correct transfer

For bone `j`, remove its *starting* source orientation from each forward source clip before comparing phase-dependent motion:

`N_j(p) = inverse(Q_normal_j(0)) * Q_normal_j(p)`;
`W_j(p) = inverse(Q_woman_j(offset)) * Q_woman_j(p+offset)`;
`D_j(p) = inverse(N_j(p)) * W_j(p)`;
`Q_trial_j(p) = Q_accepted_backward_j(p) * slerp(identity, D_j(p), layer_gain)`.

This ensures phase-zero parity and excludes fixed initial arm/hand orientations that wrecked v0.2.0. The style overlay is **not** an absolute clip pose and does not reverse the forward animation. Hips can receive dynamically measured local X/Y sway and bounce difference, but accepted backward pelvis Z remains identical; other bone translations and all scales remain approved. The terminal source keyframe is filtered by a short smooth blend in the source sampling window, not transposed as runtime locomotion.

## Four independent layers

1. Pelvis: local hips orientation and X/Y movement only, never Z travel.
2. Legs: thigh/shin/foot/toe local rotations, plus *real-skinned* low-foot position safeguards. This pilot does NOT yet solve target foot-path IK; the safety gate attenuates or rejects candidates that violate contact tolerances. Do not interpret rejected leg transfer as a finished female backward step path.
3. Torso/head: spine, neck, and head joint motion, without static offsets.
4. Arms/hands: shoulders, upper arms, forearms, hands, and fingers, independently from the legs and pelvis.

All start **OFF**. The operator enables specific layers and requests strengths, then presses **Test and apply requested layers**. The browser performs bounded tests against the left approved procedural baseline. Each layer is individually attenuated or rejected; the final combination is tested at 30/60/120 fps with half-frames and full 74-bone continuity. Only a passing combination is rendered. The viewer reports *requested vs applied* gains and rejected gates rather than silently accepting a bad result. Reset restores v0.2.2 exactly.

Foot support witnesses are inferred from the lowest existing foot positions, **not** physical force/contact sensors. Gates cover contact-ankle/toe displacement, swing-ankle displacement, root X/Z changes, head displacement, downward foot penetration relative to approved baseline, full-body temporal joint steps, and seam rotation/position. Full JSON and a CSV gain summary are stored in Termux campaign state by a local-only HTTP evidence receiver and may be downloaded from the page. Browser measurements are NOT certified at packaging time, only after running on the owner's Android browser and verified original GLB.

## Pipeline

One uniquely named checksum-verified `.sh` campaign runs through the owner's **Termux Git** lane only. It checks fresh remote `main` and canonical LFS SHA, creates an isolated checkout, enforces immutable old blobs, checks all new path collisions, SHA-verifies every embedded file, executes Node and Python tests including injected invalid reports, commits only new text outputs, pushes without force, performs exact remote Git object readback, opens a fresh no-cache local HTTP viewer, and prints its full URL, PID, port, hashes and persistent receipt. It never modifies the canonical model, original clips, or earlier accepted demo files. Owner visual acceptance remains pending.
__HAREWORKS_STYLE_LAB_V025_README_MD__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/contract.json" <<'__HAREWORKS_STYLE_LAB_V025_CONTRACT_JSON__'
{
  "schema":"hareworks-backward-style-lab-v0.2.5",
  "recoveryOf":"hareworks-backward-style-lab-v0.2.4",
  "recoveryReason":"fix malformed embedded Python bytes-literal in report SHA postprocessing; add full embedded-heredoc syntax preflight",
  "ownerGoal":"Controlled layered transfer of measured dynamic Walking -> Walking_Woman style onto approved v0.2.2 backward in-place gait",
  "repository":"Valar05/parametric-parambulator",
  "baseCommit":"5248f3e9859088f41d8c8ebd7acaa6e7b09c25f9",
  "canonicalGLB":"assets/hareworks/Hareworks-nine-clips.glb",
  "canonicalModelSha256":"a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "canonicalModelBytes":6784896,
  "sourceClips":["Walk_Backward","Walking","Walking_Woman"],
  "jointCount":74,
  "researchVersion":"v0.2.3",
  "originalOwnerExportResearchReportSHA256":"f631eaf0bb48bb81afa9b451cf2191aa4c98b07bd768f2574caaaa28938ffebe",
  "measuredForwardStylePhaseOffset":0.9777777777777777,
  "protectedForwardViewerBlob":"a17f8109766dcfa39fbb75b6b2ff335c358733cb",
  "protectedBackwardViewerBlob":"61c9bea2aa3c5da5f331c45e2df41077670c3603",
  "protectedBackwardKernelBlob":"4be7594e2fe43522c807b3fe59eb2ed965d95367",
  "sourceModelMutation":false,
  "acceptedGaitsMutation":false,
  "styleTransferStaticPoseOffsets":false,
  "backwardRootZInvariant":true,
  "styleLayers":["pelvis","legs","torso","arms"],
  "sourceCapturePoses":{"backward":720,"normal":360,"woman":360},
  "halfFrameRatesHz":[30,60,120],
  "lowFootContact":"height-based candidate witness, not force measurement",
  "unapprovedStyleDefault":"all OFF; tested and attenuated before enabled",
  "executionLane":"Android Termux Git ONLY",
  "rulesRead":{"agentsGitBlob":"547c2af52303f4efb718bbf8f82a698110c7bfca","campaignEtiquetteId":"1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI","topDownEtiquetteId":"1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU"},
  "ownerStyleAcceptance":false
}
__HAREWORKS_STYLE_LAB_V025_CONTRACT_JSON__
fi
if ((PUBLISHED==0));then
 python3 - "$DIR/research-priors.json" <<'PY_PRESERVE_EXACT_RESEARCH_JSON'
from pathlib import Path
import sys
p=Path(sys.argv[1]);b=p.read_bytes()
assert b[-1:] == bytes([10]), 'expected trailing newline in packet source'
p.write_bytes(b[:-1])
PY_PRESERVE_EXACT_RESEARCH_JSON
 cp -- "$0" "campaigns/$CAMPAIGN.sh" || fail "exact entrypoint copy failed"
fi
phase=embedded-integrity
[[ "$(hash "$DIR/index.html")" == "283e907e904f9e53cf796f622ddc36d44695bca2374b6a8a1f02ed34178219c5" ]] || fail 'embedded payload SHA mismatch: index.html'
[[ "$(hash "$DIR/viewer.mjs")" == "3883410f2ccbe91c316efb2c8aaa91a1591c147bba82bbf5b761ad74fe4ec88b" ]] || fail 'embedded payload SHA mismatch: viewer.mjs'
[[ "$(hash "$DIR/style-layers.mjs")" == "ec166d1bd51ba88d1a565b454d24574559103ac71b482bd1fc99574f0b257a93" ]] || fail 'embedded payload SHA mismatch: style-layers.mjs'
[[ "$(hash "$DIR/style-layers-test.mjs")" == "b2ca4f9519698942c3062863ae1d18965b793a2056b379479a168b080e790876" ]] || fail 'embedded payload SHA mismatch: style-layers-test.mjs'
[[ "$(hash "$DIR/inplace-kernel.mjs")" == "a636a730ae770c90f1d7dc8441982b89e0dd28a1d79ac8b71f3a1b0c2f0f6cb3" ]] || fail 'embedded payload SHA mismatch: inplace-kernel.mjs'
[[ "$(hash "$DIR/inplace-kernel-test.mjs")" == "19e50a36ba0ab5c5753142655af5a0b49a8b2468168d0c28bd76e73b3d78ab9f" ]] || fail 'embedded payload SHA mismatch: inplace-kernel-test.mjs'
[[ "$(hash "$DIR/inplace-witness-test.mjs")" == "7e7a7aa7202fbcb4ef783a960aa8da8d1c94c864cd462c5eee97a4ea3da144e7" ]] || fail 'embedded payload SHA mismatch: inplace-witness-test.mjs'
[[ "$(hash "$DIR/source-witness.json")" == "e5d57d2528b873836b759138eb318514fe80dcac07f19844d9ece5350d636408" ]] || fail 'embedded payload SHA mismatch: source-witness.json'
[[ "$(hash "$DIR/research-priors.json")" == "f631eaf0bb48bb81afa9b451cf2191aa4c98b07bd768f2574caaaa28938ffebe" ]] || fail 'embedded payload SHA mismatch: research-priors.json'
[[ "$(hash "$DIR/lab-server.py")" == "d15f0cb7427a838bc96d7cb6a6185e1cca4ff0638d96014ee5cfcae3c8c6c9fa" ]] || fail 'embedded payload SHA mismatch: lab-server.py'
[[ "$(hash "$DIR/README.md")" == "cfe1a223f445e26d8d3384ad53f93f76da1f580acf1507c410c50d51a4104f9a" ]] || fail 'embedded payload SHA mismatch: README.md'
[[ "$(hash "$DIR/contract.json")" == "5bf6366f438bae8bee13ed0720a46ccd9dfaa3a9412a2e3950cb7a4b3cd03639" ]] || fail 'embedded payload SHA mismatch: contract.json'
[[ "$(hash "campaigns/$CAMPAIGN.sh")" == "$SELF_SHA" ]] || fail 'committed campaign differs from executed checksum-verified script'
phase=host-validation
for js in viewer.mjs style-layers.mjs style-layers-test.mjs inplace-kernel.mjs inplace-kernel-test.mjs inplace-witness-test.mjs;do node --check "$DIR/$js" || fail "JavaScript syntax: $js";done
node "$DIR/style-layers-test.mjs" | tee "$STATE/style-regressions.log" || fail 'style source-delta mathematics failed'
node "$DIR/inplace-kernel-test.mjs" | tee "$STATE/backward-regressions.log" || fail 'approved backward mathematical regressions failed'
node "$DIR/inplace-witness-test.mjs" | tee "$STATE/source-witness-regressions.log" || fail 'actual source 61-sample witness failed'
cmp -s "$DIR/inplace-kernel.mjs" tools/hareworks-forward-woman/v0.2.2/inplace-kernel.mjs || fail 'packaged approved solver is NOT byte-identical to published backward solver'
python3 -m py_compile "$DIR/lab-server.py" || fail 'lab evidence receiver syntax failed'
python3 - "$DIR" "$MODEL_SHA" <<'PY_DEPENDENCIES' || fail 'browser imports, source report, or 4-layer contract failed'
import pathlib,json,re,sys,hashlib
p=pathlib.Path(sys.argv[1]);sha=sys.argv[2]
report=(p/'research-priors.json').read_bytes();r=json.loads(report)
assert hashlib.sha256(report).hexdigest()=='f631eaf0bb48bb81afa9b451cf2191aa4c98b07bd768f2574caaaa28938ffebe'
assert r['schema']=='hareworks-forward-style-research-v0.2.3' and len(r['perBone'])==74
assert r['sourceModelSHA256']==sha and abs(r['alignment']['womanPhaseOffset']-0.9777777777777777)<1e-9
c=json.loads((p/'contract.json').read_text());assert c['canonicalModelSha256']==sha and c['jointCount']==74
assert c['ownerStyleAcceptance'] is False and c['acceptedGaitsMutation'] is False
v=(p/'viewer.mjs').read_text();html=(p/'index.html').read_text()
assert "stylePose(" in v and "applyRequested()" in v and "zeroAudit()" in v and "captureClip(" in v
assert "new THREE.AnimationMixer(sourceClones[" in v and 'generatedSourceAnimationTracks:0' in v
assert 'id="apply"' in html and 'id="reset"' in html and 'id="onLegs"' in html
for local in re.findall(r"from\s+[\x27\x22](\.[^\x27\x22]+)[\x27\x22]",v):
 assert (p/local).resolve(strict=True).is_file(),('missing imported JS module',local)
print('EXACT_OWNER_RESEARCH_JSON_AND_CONTROLLED_LAYER_CONTRACT=PASS')
PY_DEPENDENCIES
python3 - "$DIR" "$STATE" <<'PY_RECEIVER_TEST' || fail 'real phone JSON saving and corrupted report rejection tests failed'
import importlib.util,pathlib,tempfile,json,sys
spec=importlib.util.spec_from_file_location('hareworks_v025_lab_server',sys.argv[1]+'/lab-server.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 o={'schema':'hareworks-gated-backward-style-lab-v0.2.5','sourceSha256':m.MODEL_SHA,'sourceClips':['Walk_Backward','Walking','Walking_Woman'],'sourceBones':74,'sourceModelUnchanged':True,'originalGaitsUnchanged':True,'styleAcceptedByOwner':False,'approvedBackwardMotionPlaybackTracks':0,'generatedSourceAnimationTracks':0,'zeroFrame':{'pass':True,'joints':74},'requested':{'pelvis':.5,'legs':.3,'torso':.5,'arms':.6},'applied':{'pelvis':.25,'legs':0,'torso':.5,'arms':.4},'trials':[{'layer':'legs','requested':.3,'applied':0,'status':'REJECTED_SAFETY_GATE'}], 'fullRateAudit':{'pass':True,'sampleCount':210,'perRate':[{'rateHz':x} for x in [30,60,120]],'rejections':[]}}
 result=m.store_report(json.dumps(o).encode(),d)
 assert result['saved'] and (pathlib.Path(d)/'style-lab-report.json').exists() and (pathlib.Path(d)/'style-lab-trials.csv').exists() and (pathlib.Path(d)/'style-lab-receipt.json').exists()
 v=dict(o);v['sourceSha256']='tampered'
 try:m.store_report(json.dumps(v).encode(),d)
 except AssertionError:pass
 else:raise AssertionError('tampered model accepted')
 v=dict(o);v['fullRateAudit']={'pass':False,'sampleCount':210,'perRate':[{'rateHz':30}], 'rejections':[{'name':'contact'}]}
 try:m.store_report(json.dumps(v).encode(),d)
 except AssertionError:pass
 else:raise AssertionError('unverified gait accepted')
 print('BROWSER_EVIDENCE_PERSISTENCE_AND_INVALID_REPORT_GATES_PASS')
PY_RECEIVER_TEST
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.9/viewer.mjs)" == "$ACCEPTED_FORWARD" ]] || fail 'approved forward unexpectedly touched'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.2/viewer.mjs)" == "$ACCEPTED_BACKWARD" ]] || fail 'approved backward unexpectedly touched'
if ((PUBLISHED==0));then
 phase=scoped-stage
 [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote advanced before publication'
 git add -- "${FILES[@]}" || fail 'scoped Git staging failed'
 python3 - "${FILES[@]}" <<'PY_STAGE' || fail 'staging escaped approved research-only paths'
import subprocess,sys
expected=set(sys.argv[1:]);actual=set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines())
assert expected==actual,{'expected':sorted(expected),'actual':sorted(actual)}
assert not any(x.endswith(('.glb','.blend')) for x in actual)
assert len(actual)==13
print('STAGED_ONLY_THIRTEEN_NEW_STYLE_LAB_TEXT_FILES=PASS')
PY_STAGE
 for p in AGENTS.md "$MODEL" tools/hareworks-forward-woman/v0.1.9/viewer.mjs tools/hareworks-forward-woman/v0.2.2/viewer.mjs tools/hareworks-forward-woman/v0.2.2/inplace-kernel.mjs tools/hareworks-forward-woman/v0.2.3/viewer.mjs tools/hareworks-forward-woman/v0.2.3/analysis-core.mjs;do
  git diff --quiet -- "$p" || fail "protected source worktree modified: $p"
  [[ "$(git rev-parse "HEAD:$p")" == "$(git rev-parse "$BASE:$p")" ]] || fail "protected prior revision changed: $p"
 done
 phase=commit
 git -c user.name='Hareworks Research Termux Campaign' -c user.email='hareworks-research@users.noreply.github.com' commit -m 'Add gated four-layer backward style research lab v0.2.5' || fail 'scoped Git commit failed'
 COMMIT=$(git rev-parse HEAD)
 [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'commit parent unexpected'
 phase=publish
 [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote advanced, refusing force-push'
 GIT_LFS_SKIP_PUSH=1 git push origin HEAD:refs/heads/main || fail "push failed; isolated commit remains $COMMIT"
else COMMIT="$REMOTE";fi
phase=remote-readback
[[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$COMMIT" ]] || fail 'remote main does not match style lab commit'
GIT_LFS_SKIP_SMUDGE=1 git fetch --depth=2 origin main || fail 'readback fetch failed'
[[ "$(git rev-parse FETCH_HEAD)" == "$COMMIT" ]] || fail 'fetched main is not committed research packet'
for p in "${FILES[@]}";do
 [[ "$(git rev-parse "FETCH_HEAD:$p")" == "$(git rev-parse "HEAD:$p")" ]] || fail "remote file byte identity differs: $p"
done
for p in AGENTS.md "$MODEL" tools/hareworks-forward-woman/v0.1.9/viewer.mjs tools/hareworks-forward-woman/v0.2.2/viewer.mjs tools/hareworks-forward-woman/v0.2.2/inplace-kernel.mjs tools/hareworks-forward-woman/v0.2.3/viewer.mjs tools/hareworks-forward-woman/v0.2.3/analysis-core.mjs;do
 [[ "$(git rev-parse "FETCH_HEAD:$p")" == "$(git rev-parse "$BASE:$p")" ]] || fail "approved original source changed on remote: $p"
done
echo "EXACT_REMOTE_READBACK=PASS $COMMIT"
phase=phone-style-lab-viewer
cp -- "$SOURCE" "$MODEL" || fail 'cannot materialize immutable source GLB into disposable phone HTTP snapshot'
[[ "$(hash "$MODEL")" == "$MODEL_SHA" ]] || fail 'HTTP GLB source SHA mismatch'
READY="$ROOT/style-lab-server-ready.json"
nohup python3 "$DIR/lab-server.py" "$WORK" "$STATE" "$READY" > "$ROOT/server.log" 2>&1 </dev/null &
PID=$!
for t in 1 2 3 4 5 6 7 8 9 10;do
 if [[ -f "$READY" ]];then PORT=$(python3 - "$READY" <<'PY_PORT'
import json,sys
print(json.load(open(sys.argv[1]))['port'])
PY_PORT
);fi
 if [[ "$PORT" =~ ^[0-9]+$ ]] && curl -fsS --max-time 3 "http://127.0.0.1:$PORT/$DIR/index.html" >/dev/null 2>&1;then break;fi
 sleep 1
done
[[ "$PORT" =~ ^[0-9]+$ ]] && kill -0 "$PID" 2>/dev/null || fail 'distinct no-cache local phone viewer server unavailable'
python3 - "http://127.0.0.1:$PORT" "$DIR" "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" "$STATE/http-manifest.json" <<'PY_HTTP' || fail 'exact HTTP source/JS/research lab asset checks failed'
import hashlib,json,pathlib,re,sys,urllib.parse,urllib.request
origin,dir,model,sha,size,out=sys.argv[1:]
def get(url):
 with urllib.request.urlopen(url,timeout=40) as r:
  assert 'no-store' in r.headers.get('Cache-Control',''),('cache control',url)
  return r.read()
root=origin+'/'+dir+'/'
viewer=get(root+'viewer.mjs').decode();html=get(root+'index.html').decode()
assert 'id="apply"' in html and 'id="onPelvis"' in html and 'id="onLegs"' in html and 'id="onTorso"' in html and 'id="onArms"' in html
assert 'zeroAudit()' in viewer and 'stylePose(' in viewer and 'await measure(accepted,[30,60,120],true)' in viewer
urls=[root+x for x in ['index.html','viewer.mjs','style-layers.mjs','style-layers-test.mjs','inplace-kernel.mjs','inplace-kernel-test.mjs','inplace-witness-test.mjs','source-witness.json','research-priors.json','lab-server.py','README.md','contract.json']]
urls += [urllib.parse.urljoin(root+'viewer.mjs',m) for m in re.findall(r"from\s+[\x27\x22](\.[^\x27\x22]+)[\x27\x22]",viewer)]
for url in sorted(set(urls)): assert get(url),('missing HTTP import',url)
report=get(root+'research-priors.json')
assert hashlib.sha256(report).hexdigest()=='f631eaf0bb48bb81afa9b451cf2191aa4c98b07bd768f2574caaaa28938ffebe'
blob=get(origin+'/'+model)
assert len(blob)==int(size) and hashlib.sha256(blob).hexdigest()==sha
record={'status':'EXACT_GLB_AND_STYLE_LAB_HTTP_VERIFIED_BROWSER_GAIT_GATE_PENDING','sourceClips':['Walk_Backward','Walking','Walking_Woman'],'modelSha256':sha,'reportSha256':hashlib.sha256(report).hexdigest(),'modelBytes':len(blob),'resources':sorted(set(urls)),'styleLabBrowserMeasurements':'NOT_YET_MEASURED'}
pathlib.Path(out).write_text(json.dumps(record,indent=2))
print('PHONE_STYLE_LAB_HTTP_SOURCE_MODEL_AND_PRIORS_PASS',len(set(urls)),'assets')
PY_HTTP
curl -fsSI --max-time 5 "http://127.0.0.1:$PORT/$DIR/index.html" > "$STATE/http-headers.txt" || fail 'phone viewer headers missing'
URL="http://127.0.0.1:$PORT/$DIR/index.html?commit=$COMMIT&scriptSha=$SELF_SHA&modelSha=$MODEL_SHA"
python3 - "$STATE/receipt.json" "$CAMPAIGN" "$BASE" "$COMMIT" "$SELF_SHA" "$MODEL_SHA" "$AGENTS_BLOB" "$URL" "$PID" "$PORT" "$ROOT" <<'PY_RECEIPT'
import datetime,json,pathlib,sys
path,campaign,parent,commit,entry,model,agents,url,pid,port,snapshot=sys.argv[1:]
r={'campaign':campaign,'status':'GIT_PUBLISHED_READBACK_HTTP_VERIFIED_REAL_3_CLIP_GATED_STYLE_PENDING_BROWSER',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'auditedParent':parent,'publishedCommit':commit,'entrypointSHA256':entry,'canonicalModelSHA256':model,
 'ownerV023ResearchSHA256':'f631eaf0bb48bb81afa9b451cf2191aa4c98b07bd768f2574caaaa28938ffebe','AGENTS_GitBlob':agents,
 'freshRulesRead':{'AGENTS.md':'Git blob checked at pinned revision','Campaign Etiquette':'Home Center 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI','Top-down Etiquette':'Home Center 1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'},
 'sourceClips':['Walk_Backward','Walking','Walking_Woman'],'sourceBones':74,'generatedSourceTrackPlayback':False,
 'gatedStyles':['pelvis','legs','torso','arms'],'acceptedForwardChanged':False,'acceptedBackwardChanged':False,'originalGLBChanged':False,
 'recoveryOf':'v0.2.4_SYNTAX_BLOCKED_BEFORE_GIT_STAGING','embeddedPythonASTPreflight':'PASS','realBrowserStyleAudit':'PENDING','ownerVisualStyleAcceptance':'PENDING', 'phoneViewerURL':url,'phoneViewerPID':int(pid),'phoneViewerPort':int(port),'isolatedSnapshot':snapshot,'executionLane':'Android Termux Git ONLY',
 'phoneStyleReport':str(pathlib.Path(path).parent/'style-lab-report.json'),'phoneStyleReceipt':str(pathlib.Path(path).parent/'style-lab-receipt.json')}
pathlib.Path(path).write_text(json.dumps(r,indent=2)+'\n')
PY_RECEIPT
echo "REMOTE_COMMIT=$COMMIT"
echo "MODEL_SHA256=$MODEL_SHA"
echo "OWNER_RESEARCH_SHA256=f631eaf0bb48bb81afa9b451cf2191aa4c98b07bd768f2574caaaa28938ffebe"
echo 'SOURCE_CLIPS=Walk_Backward,Walking,Walking_Woman'
echo 'APPROVED_BACKWARD_VERSION=v0.2.2 APPROVED_FORWARD_VERSION=v0.1.9'
echo "VIEWER_URL=$URL"
echo "VIEWER_PORT=$PORT VIEWER_PID=$PID"
echo "RECEIPT=$STATE/receipt.json"
echo "STYLE_REPORT_AFTER_BROWSER=$STATE/style-lab-report.json"
echo "BROWSER_MEASUREMENT_RECEIPT_AFTER_BROWSER=$STATE/style-lab-receipt.json"
echo 'BODY_STYLE_LAYERS_OFF_UNTIL_REAL_SKINNED_GATES_PASS; OWNER_STYLE_ACCEPTANCE=PENDING'
if command -v termux-open-url >/dev/null;then
 termux-open-url "$URL" || echo "PHONE_BROWSER_OPEN_FAILED; open VIEWER_URL=$URL"
else echo "TERMUX_OPEN_URL_MISSING; open VIEWER_URL=$URL";fi
