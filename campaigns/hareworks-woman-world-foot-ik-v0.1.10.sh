#!/data/data/com.termux/files/usr/bin/bash
# Hareworks world locomotion IK v0.1.10: ONE actor, world Z movement,
# real skinned sole pins in world coordinates, fixed-follow camera.
# No modification of original GLB, accepted v0.1.9 or any other gait.
set -Eeuo pipefail
CAMPAIGN='hareworks-woman-world-foot-ik-v0.1.10'
REPO='Valar05/parametric-parambulator'
BASE='7ebee024ac9f88251ed4e6db6802fcb41589c6e1'
DIR='tools/hareworks-forward-woman/v0.1.10'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
exec > >(tee -a "$STATE/run.log") 2>&1
phase=preflight; ROOT=''; WORK=''; COMMIT=''; PID=''; PORT=''; SOURCE=''; PUBLISHED=0
fail(){
 echo "BLOCKED step=$phase reason=$*"
 python3 - "$STATE/blocked.json" "$CAMPAIGN" "$phase" "$*" "$COMMIT" "$ROOT" <<'PY_BLOCK' || true
import datetime,json,pathlib,sys
p,campaign,phase,error,commit,root=sys.argv[1:]
pathlib.Path(p).write_text(json.dumps({'campaign':campaign,'state':'BLOCKED','phase':phase,'reason':error,'knownCommit':commit,'snapshot':root,'originalModelUnmodified':True,'ownerAcceptedGaitsUnmodified':True,'worldFootIK': 'NOT_CONFIRMED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
PY_BLOCK
 exit 1
}
hash(){ sha256sum -- "$1" | cut -d' ' -f1; }
if [[ "${1:-run}" == status ]];then
 [[ ! -f "$STATE/receipt.json" ]] || cat "$STATE/receipt.json"
 [[ ! -f "$STATE/woman-world-ik-receipt.json" ]] || cat "$STATE/woman-world-ik-receipt.json"
 exit 0
fi
[[ "${1:-run}" == run || "${1:-run}" == resume ]] || fail 'use bash campaign.sh [run|resume|status]'
for c in git python3 node curl sha256sum;do command -v "$c" >/dev/null || fail "Termux dependency absent: $c";done
phase=embedded-python-preflight
python3 - "$0" <<'PY_PREFLIGHT' || fail 'embedded Python code malformed BEFORE checkout'
import ast,pathlib,re,sys
source=pathlib.Path(sys.argv[1]).read_text()
lines=source.splitlines(keepends=True)
checked=[]
for i,line in enumerate(lines):
 m=re.search(r"<<'(?P<tag>PY_[A-Z0-9_]+)'",line)
 if not m:continue
 tag=m.group('tag');rest=''.join(lines[i+1:]);end=rest.find('\n'+tag+'\n')
 if end<0:raise SyntaxError('missing heredoc terminator: '+tag)
 ast.parse(rest[:end],filename=tag);checked.append(tag)
assert len(checked)>=5,('missing embedded Python',checked)
print('ALL_EMBEDDED_PYTHON_AST_PREFLIGHT=PASS',len(checked))
PY_PREFLIGHT
SELF_SHA=$(hash "$0")
echo "CAMPAIGN=$CAMPAIGN"
echo "ENTRYPOINT_SHA256=$SELF_SHA"
echo "PINNED_PARENT=$BASE"
echo "CANONICAL_MODEL_SHA256=$MODEL_SHA"
echo "OBSERVED_RULES_AGENTS_BLOB=$AGENTS_BLOB"
echo 'RULES_CAMPAIGN_ETIQUETTE_HOME_CENTER=1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
echo 'RULES_TOP_DOWN_ETIQUETTE_HOME_CENTER=1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
echo 'WORLD_LOCOMOTION=YES; WORLD_PINNING=YES; ONE_ACTOR=YES; CAMERA_FIXED_FOLLOW=YES; SOURCE_CLIP_RUNTIME_GENERATED_MIXER=NONE'
ORIGIN="https://github.com/$REPO.git"
phase=remote-preflight
REMOTE=''
for attempt in 1 2 3;do
 REMOTE=$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1) || REMOTE=''
 [[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] && break
 sleep "$attempt"
done
[[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] || fail 'unable to read true remote HEAD'
echo "OBSERVED_REMOTE_MAIN=$REMOTE"
phase=isolated-checkout
ROOT=$(mktemp -d "$STATE/snapshot.XXXXXXXX") || fail 'cannot make isolated snapshot'
WORK="$ROOT/repo"
for attempt in 1 2;do
 if GIT_LFS_SKIP_SMUDGE=1 git -c lfs.install.skip=true clone --depth=2 --filter=blob:none --no-checkout --single-branch --branch main "$ORIGIN" "$WORK";then break;fi
 [[ ! -e "$WORK" ]] || fail 'partial isolated clone preserved, no touching user worktree'
 sleep "$attempt"
done
[[ -d "$WORK/.git" ]] || fail 'isolated clone failed'
git -C "$WORK" sparse-checkout init --cone || fail 'sparse setup failed'
git -C "$WORK" sparse-checkout set assets/hareworks tools/hareworks-forward-woman campaigns || fail 'sparse checkout failed'
GIT_LFS_SKIP_SMUDGE=1 git -C "$WORK" checkout -B "$CAMPAIGN" "$REMOTE" || fail 'isolated HEAD materialization failed'
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$REMOTE" ]] || fail 'unexpected isolated Git HEAD'
cd "$WORK"
[[ -z "$(git status --porcelain)" ]] || fail 'isolated checkout dirty; never stash/reset'
phase=source-and-authority
[[ -f AGENTS.md ]] && grep -Fq 'Termux Git only' AGENTS.md || fail 'root AGENTS authority absent'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.9/viewer.mjs)" == "a17f8109766dcfa39fbb75b6b2ff335c358733cb" ]] || fail 'protected source changed: tools/hareworks-forward-woman/v0.1.9/viewer.mjs'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.2/viewer.mjs)" == "61c9bea2aa3c5da5f331c45e2df41077670c3603" ]] || fail 'protected source changed: tools/hareworks-forward-woman/v0.2.2/viewer.mjs'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.6/viewer.mjs)" == "bde7aff0b75252192a64157a8b0f8ce6486e93fb" ]] || fail 'protected source changed: tools/hareworks-forward-woman/v0.2.6/viewer.mjs'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.2.7/viewer.mjs)" == "3ee51e91413fa36844054932954d5f740c70aa50" ]] || fail 'protected source changed: tools/hareworks-forward-woman/v0.2.7/viewer.mjs'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs)" == "8ca6a0c2b1973f71d3f6cb383612635252f9a042" ]] || fail 'protected source changed: tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.9/upper-anchor.mjs)" == "0e8ad937c7d0fbaaec063b88063a4a72a040c02b" ]] || fail 'protected source changed: tools/hareworks-forward-woman/v0.1.9/upper-anchor.mjs'
[[ "$(git rev-parse HEAD:AGENTS.md)" == "547c2af52303f4efb718bbf8f82a698110c7bfca" ]] || fail 'protected source changed: AGENTS.md'
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" <<'PY_LFS' || fail 'canonical model pointer changed'
import subprocess,sys
p,h,n=sys.argv[1:]
want=f'version https://git-lfs.github.com/spec/v1\noid sha256:{h}\nsize {n}\n'.encode()
assert subprocess.check_output(['git','show','HEAD:'+p])==want
print('CANONICAL_GIT_LFS_POINTER=PASS')
PY_LFS
FILES=("$DIR/index.html" "$DIR/viewer.mjs" "$DIR/contact-core.mjs" "$DIR/ik-core.mjs" "$DIR/contact-core-test.mjs" "$DIR/geometry-test.mjs" "$DIR/review-server.py" "$DIR/README.md" "$DIR/contract.json" "campaigns/$CAMPAIGN.sh")
if [[ "$REMOTE" != "$BASE" ]];then
 if git cat-file -e "HEAD:campaigns/$CAMPAIGN.sh" 2>/dev/null && git cat-file -e "HEAD:$DIR/viewer.mjs" 2>/dev/null;then
  [[ "$(git show -s --format='%P' HEAD | awk '{print $1}')" == "$BASE" ]] || fail 'already published campaign not direct child of pinned parent'
  [[ "$(git show "HEAD:campaigns/$CAMPAIGN.sh" | sha256sum | cut -d' ' -f1)" == "$SELF_SHA" ]] || fail 'different bytes already at same campaign path'
  PUBLISHED=1
  echo "EXACT_CAMPAIGN_ALREADY_PUBLISHED=$REMOTE, using readback and recovering the viewer"
 else fail "main advanced beyond pinned baseline, never force-push or overwrite: $REMOTE";fi
else
 phase=pre-publication-collision
 for path in "${FILES[@]}";do
  [[ ! -e "$path" && ! -L "$path" ]] || fail "new destination collision: $path"
  if git cat-file -e "HEAD:$path" 2>/dev/null;then fail "new Git destination collision: $path";fi
 done
fi
phase=real-model-acquisition
for searchRoot in "$HOME/.local/state/hareworks" "$HOME/storage/downloads" /storage/emulated/0/Download;do
 [[ -d "$searchRoot" ]] || continue
 depth=2;[[ "$searchRoot" != "$HOME/.local/state/hareworks" ]] || depth=10
 while IFS= read -r -d '' f;do
  [[ "$(wc -c < "$f" | tr -d ' ')" == "$MODEL_SIZE" ]] || continue
  if [[ "$(hash "$f")" == "$MODEL_SHA" ]];then SOURCE="$f";break;fi
 done < <(find -L "$searchRoot" -maxdepth "$depth" -type f -name 'Hareworks-nine-clips.glb' -print0 2>/dev/null)
 [[ -z "$SOURCE" ]] || break
done
if [[ -z "$SOURCE" ]];then
 command -v git-lfs >/dev/null || fail 'exact GLB uncached and Git LFS unavailable'
 git lfs install --local || fail 'local LFS setup failed'
 for attempt in 1 2 3;do
  if GIT_LFS_SKIP_SMUDGE=1 git lfs fetch -I "$MODEL" -X '' origin "$REMOTE";then break;fi
  sleep "$attempt"
 done
 OBJECT=$(git rev-parse --git-path "lfs/objects/${MODEL_SHA:0:2}/${MODEL_SHA:2:2}/$MODEL_SHA")
 [[ -f "$OBJECT" ]] || fail 'canonical binary model unavailable from LFS'
 SOURCE="$OBJECT"
fi
[[ "$(wc -c < "$SOURCE" | tr -d ' ')" == "$MODEL_SIZE" && "$(hash "$SOURCE")" == "$MODEL_SHA" ]] || fail 'real GLB SHA or size mismatch'
python3 - "$SOURCE" <<'PY_GLB' || fail 'real binary Hareworks GLB contract invalid'
import json,struct,sys
with open(sys.argv[1],'rb') as f:
 h=f.read(20)
 assert h[:4]==b'glTF' and struct.unpack_from('<I',h,8)[0]==6784896
 n,kind=struct.unpack_from('<I4s',h,12)
 assert kind==b'JSON';meta=json.loads(f.read(n))
assert len(meta['skins'][0]['joints'])==74
assert len(meta['animations'])==9
assert any(a['name']=='Walking_Woman' for a in meta['animations'])
print('ACTUAL_SOURCE_74_BONES_9_CLIPS_WALKING_WOMAN=PASS')
PY_GLB
phase=install-additive-world-ik
if (( PUBLISHED==0 ));then
 mkdir -p "$DIR" || fail 'new version directory unavailable'
cat > "$DIR/index.html" <<'__HAREWORKS_WORLD_IK_0110_0__'
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#101923"><title>Hareworks v0.1.10 | Real World Foot IK</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>:root{font:15px system-ui,sans-serif;background:#101923;color:#e9f4ff;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:900px;margin:auto;padding:12px}h1{font-size:21px;margin:6px 0}p{color:#bdcfdd;line-height:1.5}.tag{font-size:12px;color:#b6e7ce;border:1px solid #507b73;padding:4px 8px;border-radius:18px}#identity{font:11px/1.6 ui-monospace,monospace;color:#abc6d2;overflow-wrap:anywhere}#status{padding:8px 0;min-height:42px;color:#b0ecce}#stage{border:1px solid #526f83;border-radius:10px;overflow:hidden}canvas{width:100%;display:block;touch-action:none}.bar{display:flex;gap:9px;align-items:center;flex-wrap:wrap;background:#203244;padding:10px;margin:10px 0;border-radius:9px}button,input{font:inherit}button{color:#f4f9ff;background:#30516d;border:1px solid #779ab4;border-radius:8px;min-height:45px;padding:8px 12px}button:focus-visible,input:focus-visible{outline:3px solid #7ce6d4}label{display:flex;gap:7px;align-items:center}input[type=range]{flex:1;min-width:140px;accent-color:#7ce6d4}#metrics{background:#172c3b;border:1px solid #44657a;border-radius:9px;padding:12px;white-space:pre-wrap;font:12px/1.55 ui-monospace,monospace;overflow-wrap:anywhere;max-height:330px;overflow:auto}.small{font-size:12px}a{color:#a9dffa}</style></head><body><main>
<header><h1>🐇 Walking_Woman · World-Space IK</h1><span class="tag">v0.1.10 · one character</span></header>
<p>One independently posed skinned Hareworks character walking <strong>forward through the world</strong>. Feet use actual persistent world-space sole anchors during stance. The camera follows a fixed offset while the ground moves past. No reference character. No source animation mixer on the running character.</p>
<div id="identity">Verifying exact source model…</div><div id="status" role="status" aria-live="polite">Loading skeleton and real skinned sole witnesses…</div>
<div id="stage" role="img" aria-label="Single moving 3D character with world-pinned feet and fixed-follow camera"></div>
<div class="bar"><button id="play">Pause</button><button id="reset">Reset world run</button><label for="speed">Travel speed</label><input id="speed" type="range" min="0" max="0.8" value="0.52" step="0.02"><output id="speedOut">0.52 u/s</output></div>
<div class="bar" role="group" aria-label="Fixed-follow camera presets"><strong>Camera pinned:</strong><button id="oblique">Three-quarter</button><button id="side">Side</button><button id="front">Front</button><button id="top">Top</button></div>
<div class="bar"><label><input id="showContacts" type="checkbox" checked> Show world contact anchors</label><button id="audit">Run 3-cycle skinned foot-pin audit</button><button id="export">Export evidence JSON</button></div>
<div id="metrics" role="status">Actual world-sole audit pending. Green = stance pin, orange = swing target.</div>
<p class="small"><strong>Meaning of a real pin:</strong> an anchor is captured once at touchdown and its world coordinates are NOT recalculated from the traveling pelvis during stance. The thigh/shin angles are solved anew every physics step from that target. Contact error is measured from actual skinned sole vertices, not merely a bone pivot. The model moves in world Z; the camera tracks the model at a fixed offset, not the animated pelvis. Original v0.1.9 remains unchanged. Browser audit and owner visual acceptance are separate.</p>
</main><script type="module" src="./viewer.mjs"></script></body></html>
__HAREWORKS_WORLD_IK_0110_0__
[[ "$(hash "$DIR/index.html")" == "50a66edddf75e0d2c19212d973022de643349437604088724f7829550fb25415" ]] || fail "EMBEDDED_PAYLOAD_SHA_INVALID_index.html"
cat > "$DIR/viewer.mjs" <<'__HAREWORKS_WORLD_IK_0110_1__'
/* v0.1.10. ONE moving Walking_Woman. REAL world-fixed skinned-sole contacts.
   Generated actor has NO AnimationMixer, NO per-frame original clip sampling,
   NO source leg joint tracks. Pelvis+upper motions are fitted once at startup.
   Leg joint rotations are freshly computed from anchored world foot targets. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {fitSourceAnchoredTrack,evalSourceAnchoredTrack} from '../v0.1.9/upper-anchor.mjs';
import {independentPose,validateProfile} from '../v0.1.2/pose-kernel.mjs';
import {legAt,rotateY,validateFootProfile} from '../v0.1.3/foot-kernel.mjs';
import {kneeFromTarget} from './ik-core.mjs';
import {WorldContact,mod1,clamp,swingProgress,nextStartDelta,followCamera} from './contact-core.mjs';
const $=id=>document.getElementById(id),V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z),Q=()=>new THREE.Quaternion();
const SOURCE_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const MODEL='../../../assets/hareworks/Hareworks-nine-clips.glb',BONES=74,CLIP='Walking_Woman';
const names={left:['mixamorigLeftUpLeg','mixamorigLeftLeg','Bone_017','mixamorigLeftFoot','mixamorigLeftToeBase'],right:['mixamorigRightUpLeg','mixamorigRightLeg','Bone_013','mixamorigRightFoot','mixamorigRightToeBase']};
const scene=new THREE.Scene();scene.background=new THREE.Color('#102030');scene.add(new THREE.HemisphereLight(0xf3f9ff,0x34485d,2.5));
const sun=new THREE.DirectionalLight(0xffffff,3.1);sun.position.set(-4,8,4);scene.add(sun);
const ground=new THREE.GridHelper(180,180,0x6b8696,0x354858);scene.add(ground);
for(let i=0;i<24;i++){const marker=new THREE.Mesh(new THREE.BoxGeometry(.075,.025,.075),new THREE.MeshBasicMaterial({color:i%2?0x42768b:0x6ea9a9}));marker.position.set(-1.3,.015,i*1.5);scene.add(marker)}
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-3,3,2,-2,.01,300);const cameraOffsets={oblique:[-4.8,3.15,5.7],side:[-6.4,2.75,0],front:[0,2.9,7.0],top:[-.01,8,.01]};let view='oblique';
function resize(){const w=Math.max(300,$('stage').clientWidth),h=Math.max(310,Math.min(690,Math.round(w*.76)));renderer.setSize(w,h,false);camera.top=2.2;camera.bottom=-2.2;camera.left=-2.2*w/h;camera.right=-camera.left;camera.updateProjectionMatrix()}
addEventListener('resize',resize);resize();const status=x=>$('status').textContent=x;
let actor=null,rig=null,legs=null,fit=null,pelvisProfile=null,footProfile=null,clipDuration=0,rest=null,patches=null,worldContacts=null,footOrient=null;
let ready=false,playing=true,speed=.52,phase=0,worldZ=0,frameTimer=performance.now(),accumulator=0,groundOffset=0,runFrames=0,report=null,lastStats=null;
let maxDrift=0,maxIK=0,maxPenetration=0,unreachable=0,contactCount=0,swingCount=0,transitions=0,lastAnchorLocations={},failedFrames=0;
const drawPins={};for(const side of ['left','right']){const m=new THREE.Mesh(new THREE.SphereGeometry(.045,12,10),new THREE.MeshBasicMaterial({color:side==='left'?0x6bf5bf:0xb8fa83,depthTest:false}));m.renderOrder=15;scene.add(m);drawPins[side]=m;}
const wpos=b=>b.getWorldPosition(V());const wq=b=>b.getWorldQuaternion(Q());
function bonesOf(o){let found={};o.traverse(b=>{if(b.isBone){if(found[b.name])throw Error('DUPLICATE_BONE_'+b.name);found[b.name]=b}});if(Object.keys(found).length!==BONES)throw Error('EXPECTED_74_JOINTS_GOT_'+Object.keys(found).length);return found}
const skinned=o=>{let a=[];o.traverse(x=>{if(x.isSkinnedMesh){x.frustumCulled=false;a.push(x)}});return a};
function pickSolePatch(meshes,foot){const anchor=wpos(foot),near=[];
 for(let mi=0;mi<meshes.length;mi++){const m=meshes[mi],attribute=m.geometry.getAttribute('position');if(!attribute)continue;
  const step=Math.max(1,Math.floor(attribute.count/16000));for(let j=0;j<attribute.count;j+=step){const p=m.getVertexPosition(j,V());m.localToWorld(p);const d=p.distanceToSquared(anchor);if(d<.32*.32)near.push({mi,j,point:p.toArray(),d})}}
 if(near.length<15)throw Error('SKINNED_SOLE_VERTICES_NOT_FOUND_'+foot.name+'_'+near.length);
 near.sort((a,b)=>a.d-b.d);const candidates=near.slice(0,180),low=Math.min(...candidates.map(a=>a.point[1]));
 const chosen=candidates.filter(p=>p.point[1]<=low+.02).slice(0,20);if(chosen.length<4)throw Error('SOLE_PATCH_TOO_SMALL_'+foot.name);
 return {indexes:chosen.map(p=>({mi:p.mi,j:p.j})),low,count:chosen.length};
}
function soleWorld(meshes,patch){const out=V();for(const {mi,j} of patch.indexes){const m=meshes[mi];if(!m)throw Error('SOLE_SKINNED_MESH_MISMATCH');const p=m.getVertexPosition(j,V());m.localToWorld(p);out.add(p)}return out.multiplyScalar(1/patch.indexes.length)}
function setWorldQ(b,desired){b.quaternion.copy(wq(b.parent).invert().multiply(desired)).normalize()}
function turnToward(b,from,to){const origin=wpos(b),a=from.clone().sub(origin),c=to.clone().sub(origin);
 if(a.lengthSq()<1e-10||c.lengthSq()<1e-10)throw Error('IK_ZERO_BONE_VECTOR_'+b.name);
 const delta=Q().setFromUnitVectors(a.normalize(),c.normalize());setWorldQ(b,delta.multiply(wq(b)))}
const copyLocal=(b,p)=>{b.position.fromArray(p.p);b.quaternion.fromArray(p.q);b.scale.fromArray(p.s)};
function captureSeed(){const out={};for(const [name,b] of Object.entries(rig))out[name]={p:b.position.toArray(),q:b.quaternion.toArray(),s:b.scale.toArray()};return out}
function sampleFitted(source,mixer,sourceRig,count=120){const tracked=[sourceRig.mixamorigHips];sourceRig.mixamorigSpine.traverse(b=>{if(b.isBone)tracked.push(b)});
 const data=new Map(tracked.map(b=>[b.name,[]]));for(let i=0;i<count;i++){mixer.setTime(i*clipDuration/count);source.updateMatrixWorld(true);for(const b of tracked)data.get(b.name).push({quaternion:b.quaternion.toArray(),position:b.position.toArray()})}
 mixer.setTime(0);source.updateMatrixWorld(true);return Object.fromEntries([...data.entries()].map(([name,samples])=>[name,fitSourceAnchoredTrack(samples,12)]))}
function frameBody(p){const fitPhase=mod1(p),pelvis=independentPose(pelvisProfile,fitPhase*clipDuration),zero=independentPose(pelvisProfile,0);
 for(const [name,r] of Object.entries(rest))if(name in rig&&!(name in fit)&&name!=='mixamorigHips')copyLocal(rig[name],r);
 for(const [name,track] of Object.entries(fit)){const b=rig[name],s=evalSourceAnchoredTrack(track,fitPhase,12,1);b.quaternion.fromArray(s.quaternion).normalize();b.position.fromArray(s.position)}
 const hip=rig.mixamorigHips,p0=rest.mixamorigHips.p;hip.position.set(p0[0]+pelvis.pelvis[0]-zero.pelvis[0],p0[1]+pelvis.pelvis[1]-zero.pelvis[1],p0[2]+pelvis.pelvis[2]-zero.pelvis[2]);
 actor.position.z=worldZ;actor.position.y=-groundOffset;actor.updateMatrixWorld(true);}
function nominalLanding(side,phaseNow){const f=worldContacts[side],dtPhase=nextStartDelta(phaseNow,f.start),landingPhase=mod1(phaseNow+dtPhase);
 const current=independentPose(pelvisProfile,phaseNow*clipDuration),future=independentPose(pelvisProfile,landingPhase*clipDuration);
 const c=legs[side],H=wpos(c.up),offset=legAt(footProfile,side,landingPhase*clipDuration).ankleLocal;
 const yawFuture=future.pelvisYaw;const ankle=H.add(V(future.pelvis[0]-current.pelvis[0],future.pelvis[1]-current.pelvis[1],future.pelvis[2]-current.pelvis[2] +speed*clipDuration*dtPhase));ankle.add(V(...rotateY(offset,yawFuture)));
 const soleLocal=c.soleLocal.clone().multiply(c.foot.getWorldScale(V())).applyQuaternion(c.stanceQ);
 const target=ankle.add(soleLocal);target.y=0;return target.toArray();}
function contactTargets(){const out={};for(const side of ['left','right']){const c=worldContacts[side];const target=c.step({phase,nominalLanding:nominalLanding(side,phase),footLift:.12});out[side]=target;}return out}
function ankleForSole(c,worldSole,worldFootQ){const offset=c.soleLocal.clone().multiply(c.foot.getWorldScale(V())).applyQuaternion(worldFootQ);return worldSole.clone().sub(offset)}
function adjustReach(targets){let correction=0;for(const side of ['left','right']){const leg=legs[side],target=V(...targets[side].target),q=leg.stanceQ;
 const a=ankleForSole(leg,target,q),h=wpos(leg.up),r=leg.upperLength+leg.lowerLength-.014,d=h.distanceTo(a);correction=Math.max(correction,Math.max(0,d-r))}
 if(correction>0){const moved=Math.min(.14,correction+.002);rig.mixamorigHips.position.y-=moved;actor.updateMatrixWorld(true);if(correction>.14)unreachable++;}}
function solveLeg(side,worldSole,planted,footPhase){const c=legs[side],target=V(...worldSole),desiredQ=c.stanceQ.clone();
 if(!planted){const u=swingProgress(footPhase,worldContacts[side].start,worldContacts[side].duty);desiredQ.premultiply(Q().setFromAxisAngle(V(1,0,0),-.10*Math.sin(Math.PI*u)));}
 let desiredAnkle=ankleForSole(c,target,desiredQ),best=Infinity;
 for(let iter=0;iter<4;iter++){
  for(const b of c.chain)copyLocal(b,rest[b.name]);actor.updateMatrixWorld(true);
  const H=wpos(c.up),K0=wpos(c.knee),A0=wpos(c.foot),pole=legAt(footProfile,side,phase*clipDuration).poleLocal;
  const yaw=independentPose(pelvisProfile,phase*clipDuration).pelvisYaw;
  let knee;try{knee=V(...kneeFromTarget(H.toArray(),desiredAnkle.toArray(),c.upperLength,c.lowerLength,rotateY(pole,yaw)));}
  catch(e){const dir=desiredAnkle.clone().sub(H),max=c.upperLength+c.lowerLength-.005,min=Math.abs(c.upperLength-c.lowerLength)+.005;dir.setLength(clamp(dir.length(),min,max));desiredAnkle.copy(H).add(dir);unreachable++;knee=V(...kneeFromTarget(H.toArray(),desiredAnkle.toArray(),c.upperLength,c.lowerLength,rotateY(pole,yaw)));}
  turnToward(c.up,K0,knee);actor.updateMatrixWorld(true);
  turnToward(c.knee,wpos(c.foot),desiredAnkle);actor.updateMatrixWorld(true);
  setWorldQ(c.foot,desiredQ);actor.updateMatrixWorld(true);
  const actual=soleWorld(c.meshes,c.patch),e=target.clone().sub(actual);best=e.length();
  if(best<.0018)break;desiredAnkle.add(e.multiplyScalar(.95));
 }
 const actual=soleWorld(c.meshes,c.patch),drift=actual.distanceTo(target);
 if(planted){maxDrift=Math.max(maxDrift,drift);contactCount++;if(actual.y<-.012)maxPenetration=Math.max(maxPenetration,-actual.y)}else swingCount++;
 maxIK=Math.max(maxIK,drift);drawPins[side].position.copy(V(...worldSole));drawPins[side].visible=$('showContacts').checked;drawPins[side].material.color.setHex(planted?0x65f2b7:0xffb65f);
 return {planted,drift,sole:actual.toArray(),target:target.toArray(),anchor:worldContacts[side].anchor.slice(),reach:c.upperLength+c.lowerLength};
}
function physicsStep(dt){const cadence=speed<=0?0:speed/.52/clipDuration;
 phase=mod1(phase+cadence*dt);worldZ+=speed*dt;frameBody(phase);
 const targets=contactTargets();adjustReach(targets);const feet={};for(const side of ['left','right'])feet[side]=solveLeg(side,targets[side].target,targets[side].planted,phase);
 transitions=worldContacts.left.transitions+worldContacts.right.transitions;runFrames++;lastStats={phase,worldTravelZ:worldZ,speed,cadence,worldRootZ:actor.position.z,feet,transitions,maxSkinnedStanceDrift:maxDrift,maxSkinnedTargetError:maxIK,maxNewFloorPenetration:maxPenetration,reachAdjustments:unreachable,contactFrames:contactCount,swingFrames:swingCount,solvedIKPerFrame:true,generatedAnimationMixerCount:0};
 return lastStats;}
const cameraTarget=V();let stableOffset=V();function pinCamera(){if(!actor)return;const pinned=followCamera(actor.position.toArray(),cameraOffsets[view],.90);cameraTarget.fromArray(pinned.target);stableOffset.fromArray(cameraOffsets[view]);camera.position.fromArray(pinned.position);camera.up.set(0,1,0);camera.lookAt(cameraTarget);camera.updateProjectionMatrix();}
function renderMetrics(prefix='LIVE'){if(!lastStats)return;const feet=lastStats.feet;
 $('metrics').textContent=`${prefix} · WORLD-SPACE FOOT CONTACT / TRUE IK\nTravel Z ${worldZ.toFixed(3)} u · cycle ${(phase*100).toFixed(1)}% · speed ${speed.toFixed(2)} u/s\nLEFT ${feet.left.planted?'PINNED':'SWING'} sole drift ${feet.left.drift.toFixed(4)} u; RIGHT ${feet.right.planted?'PINNED':'SWING'} sole drift ${feet.right.drift.toFixed(4)} u\nMax stance skinned sole drift ${maxDrift.toFixed(5)} u · max target IK residual ${maxIK.toFixed(5)} u\nFloor penetration ${maxPenetration.toFixed(5)} u · reach adjustments ${unreachable}\nTouchdown transitions ${transitions}, contact samples ${contactCount}; generated clip mixer = 0\nCAMERA: pinned to actor world Z, stable height and angle. Ground markers stay world-fixed.`}
function clearStats(){maxDrift=0;maxIK=0;maxPenetration=0;unreachable=0;contactCount=0;swingCount=0;transitions=0;runFrames=0;lastStats=null;}
function initRun(){if(!ready)return;phase=0;worldZ=0;clearStats();frameBody(0);const m=skinned(actor),next={};for(const side of ['left','right']){const c=legs[side],sole=soleWorld(m,c.patch);next[side]=new WorldContact({side,start:c.contactStart,duty:.55,sole:sole.toArray(),groundY:0});}
 worldContacts=next;physicsStep(0);pinCamera();renderMetrics('RESET');}
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';status(playing?'RUNNING · world travel and anchored soles':'PAUSED · world contact anchors retained')};
$('reset').onclick=()=>{initRun();status('WORLD RUN RESET · actor, anchors and camera synchronized')};
$('speed').oninput=()=>{speed=Number($('speed').value);$('speedOut').textContent=speed.toFixed(2)+' u/s'};
$('showContacts').onchange=()=>{for(const side of ['left','right'])drawPins[side].visible=$('showContacts').checked};
for(const k of Object.keys(cameraOffsets))$(k).onclick=()=>{view=k;pinCamera()};
$('export').onclick=()=>{if(!report){status('Run real skinned foot-pin audit first.');return}const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='hareworks-woman-world-foot-ik-v0.1.10.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),6000)};
$('audit').onclick=async()=>{if(!ready)return;const was=playing;playing=false;status('Auditing 3 real world-travel cycles, 120 Hz and skinned sole patches…');const oldSpeed=speed;speed=.52;
 try{initRun();const n=Math.ceil(clipDuration*3*120);let worstPerFoot={left:0,right:0},anchorMaxStep=0,previous={left:null,right:null},sampled=[];
  for(let i=0;i<n;i++){const m=physicsStep(1/120);for(const side of ['left','right']){const f=m.feet[side];if(f.planted){worstPerFoot[side]=Math.max(worstPerFoot[side],f.drift);if(previous[side])anchorMaxStep=Math.max(anchorMaxStep,Math.hypot(...f.anchor.map((x,j)=>x-previous[side][j])));previous[side]=f.anchor.slice()}else previous[side]=null;}
   if(i%15===0)sampled.push({time:i/120,worldZ:m.worldTravelZ,phase:m.phase,left:m.feet.left,right:m.feet.right,cameraTrackingOffset:cameraOffsets[view]});if(i%35===0)await new Promise(requestAnimationFrame);}
  pinCamera();const cameraError=Math.abs((camera.position.z-actor.position.z)-cameraOffsets[view][2]);
  const pass=worstPerFoot.left<=.025&&worstPerFoot.right<=.025&&maxPenetration<=.020&&anchorMaxStep<=1e-8&&worldZ>.9&&cameraError<1e-8&&unreachable===0;
  report={schema:'hareworks-woman-world-pinned-ik-v0.1.10',sourceSha256:SOURCE_SHA,sourceClip:CLIP,rigBones:74,generatedAnimationMixerCount:0,calibrationOnlySourceMixer:true,oneVisibleCharacter:true,rootMovementIsWorldTravel:true,cameraFixedFollow:true,stanceAnchorCoordinateSystem:'WORLD',contactPatch:'actual skinned mesh.getVertexPosition() samples',physicsRateHz:120,sampledFrames:n,worldTravelZ:worldZ,referenceRigWasNotDisplayed:true,solver:'two-bone knee IK + world foot orientation + iterative skinned sole witness residual correction',maxSkinnedSoleDriftPerSide:worstPerFoot,maximumContactAnchorTranslation:anchorMaxStep,maxFootPenetration:maxPenetration,maxIKResidual:maxIK,reachAdjustments:unreachable,cameraWorldFollowError:cameraError,touchdownTransitions:transitions,status:pass?'WORLD_IK_GATE_PASS_OWNER_REVIEW_PENDING':'WORLD_IK_GATE_WARN_OWNER_REVIEW_REQUIRED',ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,observations:sampled};
  $('metrics').textContent=`${report.status}\nREAL skinned soles: L ${worstPerFoot.left.toFixed(5)} u; R ${worstPerFoot.right.toFixed(5)} u (limit 0.025)\nFoot anchors max motion DURING stance ${anchorMaxStep.toFixed(9)} u (required 0)\nRoot traveled ${worldZ.toFixed(3)} units; camera follow error ${cameraError.toExponential(2)}\nFoot penetration ${maxPenetration.toFixed(5)}; reach adjustments ${unreachable}; ${n} frames at 120 Hz.\nThe approved v0.1.9 is not modified. Export JSON for per-frame world evidence.`;
  try{const response=await fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(report)});if(!response.ok)throw Error('HTTP_'+response.status);const receipt=await response.json();status(report.status+' · phone evidence saved '+receipt.sha256.slice(0,12))}catch(e){status(report.status+' · autosave unavailable '+e.message+' · Export evidence available')}
 }catch(e){status('IK_AUDIT_ERROR '+e.message);console.error(e)}finally{const summary=$('metrics').textContent;speed=oldSpeed;initRun();$('metrics').textContent=summary;playing=was;$('play').textContent=playing?'Pause':'Play';}}
function frame(now){requestAnimationFrame(frame);const delta=Math.min(.055,Math.max(0,(now-frameTimer)/1000));frameTimer=now;
 if(ready&&playing){accumulator=Math.min(.06,accumulator+delta);try{let count=0;while(accumulator>=1/120&&count<9){physicsStep(1/120);accumulator-=1/120;count++}pinCamera();if(runFrames%30===0)renderMetrics();}catch(e){playing=false;failedFrames++;status('IK_RUNTIME_WARN '+e.message+' · last valid model remains visible');console.error(e)}}renderer.render(scene,camera);}
requestAnimationFrame(frame);
try{
 const response=await fetch(MODEL,{cache:'no-store'});if(!response.ok)throw Error('SOURCE_HTTP_'+response.status);const bytes=await response.arrayBuffer();if(bytes.byteLength!==6784896)throw Error('SOURCE_SIZE_'+bytes.byteLength);
 const sha=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');if(sha!==SOURCE_SHA)throw Error('SOURCE_SHA_MISMATCH '+sha);
 const [p,f]=await Promise.all([fetch('../v0.1.2/motion-profile.json',{cache:'no-store'}).then(x=>x.json()),fetch('../v0.1.3/foot-profile.json',{cache:'no-store'}).then(x=>x.json())]);validateProfile(p);validateFootProfile(f);pelvisProfile=p;footProfile=f;
 const gltf=await new GLTFLoader().parseAsync(bytes,new URL('../../../assets/hareworks/',import.meta.url).href);const sourceClip=gltf.animations.find(a=>a.name===CLIP);if(!sourceClip||gltf.animations.length!==9)throw Error('SOURCE_WALKING_WOMAN_REQUIRED');clipDuration=sourceClip.duration;
 const source=cloneSkeleton(gltf.scene);actor=cloneSkeleton(gltf.scene);const srcRig=bonesOf(source);rig=bonesOf(actor);const mixer=new THREE.AnimationMixer(source);mixer.clipAction(sourceClip).reset().play();mixer.setTime(0);source.updateMatrixWorld(true);
 for(const [name,b] of Object.entries(rig)){const a=srcRig[name];b.position.copy(a.position);b.quaternion.copy(a.quaternion);b.scale.copy(a.scale)}actor.updateMatrixWorld(true);rest=captureSeed();
 fit=sampleFitted(source,mixer,srcRig);mixer.setTime(0);source.updateMatrixWorld(true);
 const actorMeshes=skinned(actor),refMeshes=skinned(source);if(actorMeshes.length!==refMeshes.length||actorMeshes.length<1)throw Error('SKINNED_MESH_1_TO_1_REQUIRED');
 legs={};patches={};for(const [side,arr] of Object.entries(names)){const b=arr.map(n=>rig[n]);if(b.some(x=>!x))throw Error('LEG_JOINTS_MISSING_'+side);const [up,knee,bridge,foot,toe]=b;
  if(up.parent!==rig.mixamorigHips||knee.parent!==up||bridge.parent!==knee||foot.parent!==bridge||toe.parent!==foot)throw Error('LEG_CHAIN_TOPOLOGY_'+side);
  const patch=pickSolePatch(actorMeshes,foot),sole=soleWorld(actorMeshes,patch),soleLocal=foot.worldToLocal(sole.clone());
  const upperLength=wpos(up).distanceTo(wpos(knee)),lowerLength=wpos(knee).distanceTo(wpos(foot));if(upperLength<.20||lowerLength<.20)throw Error('ANATOMICAL_LINKS_INVALID_'+side);
  if(Math.abs(upperLength-footProfile[side].upperLength)>.009||Math.abs(lowerLength-footProfile[side].lowerLength)>.009)throw Error('SOURCE_FOOT_PROFILE_LENGTH_MISMATCH_'+side);
  legs[side]={side,chain:b,up,knee,bridge,foot,toe,patch,meshes:actorMeshes,soleLocal,upperLength,lowerLength,stanceQ:wq(foot),contactStart:0};patches[side]=patch;}
 // Calibrate source contact LOW phases from REAL skinned patch vertices,
 // not the animated foot pivot. Runtime NEVER consults these source clips.
 const lows={left:{y:Infinity,phase:0},right:{y:Infinity,phase:0}};let absoluteGround=Infinity;
 for(let i=0;i<240;i++){mixer.setTime(clipDuration*i/240);source.updateMatrixWorld(true);for(const side of ['left','right']){const c=legs[side],y=soleWorld(refMeshes,c.patch).y;absoluteGround=Math.min(absoluteGround,y);if(y<lows[side].y){lows[side]={y,phase:i/240}}}}
 for(const side of ['left','right']){const c=legs[side];c.contactStart=mod1(lows[side].phase-.23);mixer.setTime(clipDuration*lows[side].phase);source.updateMatrixWorld(true);c.stanceQ=wq(srcRig[c.foot.name]);}
 groundOffset=absoluteGround;mixer.stopAllAction();mixer.uncacheRoot(source); // calibration only, NEVER drives actor
 actor.position.y=-groundOffset;scene.add(actor);actor.updateMatrixWorld(true);
 const footPhases=Object.fromEntries(Object.entries(lows).map(([side,v])=>[side,{lowPhase:v.phase,stanceStart:legs[side].contactStart}]));
 ready=true;initRun();pinCamera();status('REAL RIG ACTIVE · one moving actor · fixed-follow camera · world-locked skinned soles');
 $('identity').textContent=`v0.1.10 · SHA ${SOURCE_SHA} · exact Walking_Woman · 74 bones · two-bone world IK · one actor · root WORLD travel · source mixer CALIBRATION ONLY · low-foot phases ${JSON.stringify(footPhases)} · commit ${new URLSearchParams(location.search).get('commit')||'unknown'} · entry ${new URLSearchParams(location.search).get('scriptSha')||'unknown'}`;
}catch(e){status('REAL_MODEL_CALIBRATION_BLOCKED '+e.message);console.error(e)}
__HAREWORKS_WORLD_IK_0110_1__
[[ "$(hash "$DIR/viewer.mjs")" == "46270581917f31ab52d0e7d34896bd4b5afcdb6164787c5690bbacaa6b5a9edd" ]] || fail "EMBEDDED_PAYLOAD_SHA_INVALID_viewer.mjs"
cat > "$DIR/contact-core.mjs" <<'__HAREWORKS_WORLD_IK_0110_2__'
/* Hareworks v0.1.10: WORLD-SPACE contact authority, not source pose playback. */
export const mod1=x=>((x%1)+1)%1;
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export const smooth=x=>{const t=clamp(x,0,1);return t*t*(3-2*t)};
export const mix=(a,b,t)=>a.map((v,i)=>v*(1-t)+b[i]*t);
export function forwardPhase(q,start){return mod1(q-start)}
export function stanceAt(q,start,duty){if(!(duty>.1&&duty<.85))throw Error('BAD_STANCE_DUTY');return forwardPhase(q,start)<duty}
export function swingProgress(q,start,duty){const s=forwardPhase(q,start);return clamp((s-duty)/(1-duty),0,1)}
export function swingPoint(from,to,progress,lift){const s=smooth(progress),v=mix(from,to,s);v[1]+=Math.sin(Math.PI*clamp(progress,0,1))*lift;return v}
export function nextStartDelta(q,start){const p=mod1(start-q);return p<1e-10?1:p}
export function followCamera(root,offset,focusHeight=.9){if(root.length!==3||offset.length!==3||![...root,...offset,focusHeight].every(Number.isFinite))throw Error('BAD_CAMERA_FOLLOW');return {position:[root[0]+offset[0],root[1]+focusHeight+offset[1],root[2]+offset[2]],target:[root[0],root[1]+focusHeight,root[2]]}}
// One world anchor persists for the whole stance. No source animation input.
export class WorldContact {
 constructor({side,start,duty=.55,sole,groundY}){
  if(!Array.isArray(sole)||sole.length!==3||!sole.every(Number.isFinite))throw Error('INITIAL_SOLE_INVALID');
  this.side=side;this.start=mod1(start);this.duty=duty;this.groundY=groundY;
  this.anchor=sole.slice();this.target=sole.slice();this.swingFrom=sole.slice();this.swingTo=sole.slice();
  this.isStance=stanceAt(0,this.start,this.duty);this.transitions=0;this.lastPlanted=null;
 }
 step({phase,nominalLanding,footLift=.11}){
  if(!Number.isFinite(phase)||!Array.isArray(nominalLanding)||nominalLanding.length!==3||!nominalLanding.every(Number.isFinite))throw Error('FOOT_TARGET_INVALID');
  const planted=stanceAt(phase,this.start,this.duty);
  if(planted!==this.isStance){
   if(planted){this.anchor=this.swingTo.slice();this.anchor[1]=this.groundY;this.lastPlanted=this.anchor.slice();}
   else{this.swingFrom=this.anchor.slice();this.swingTo=nominalLanding.slice();this.swingTo[1]=this.groundY;}
   this.isStance=planted;this.transitions++;
  }
  if(planted)this.target=this.anchor.slice();
  else{const u=swingProgress(phase,this.start,this.duty);this.target=swingPoint(this.swingFrom,this.swingTo,u,footLift)}
  return {target:this.target.slice(),planted,anchor:this.anchor.slice(),transitions:this.transitions};
 }
}
__HAREWORKS_WORLD_IK_0110_2__
[[ "$(hash "$DIR/contact-core.mjs")" == "564a056484b42d973e174a56a9975fadc358f1076bf60a60ae9349c8d01f7ab0" ]] || fail "EMBEDDED_PAYLOAD_SHA_INVALID_contact-core.mjs"
cat > "$DIR/ik-core.mjs" <<'__HAREWORKS_WORLD_IK_0110_3__'
/* True world-space two-segment inverse kinematics, no animation-pose lookup. */
const add=(a,b)=>a.map((x,i)=>x+b[i]);
const sub=(a,b)=>a.map((x,i)=>x-b[i]);
const scale=(v,s)=>v.map(x=>x*s);
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const norm=a=>Math.hypot(...a);
export function kneeFromTarget(hip,ankle,l1,l2,pole,eps=1e-5){
 if(![l1,l2].every(x=>Number.isFinite(x)&&x>0)||![hip,ankle,pole].every(a=>Array.isArray(a)&&a.length===3&&a.every(Number.isFinite)))throw Error('INVALID_WORLD_IK_INPUT');
 const axis=sub(ankle,hip),distance=norm(axis),limit=l1+l2;
 if(!(distance<limit+eps&&distance>Math.abs(l1-l2)+eps))throw Error('UNREACHABLE_WORLD_IK_'+distance.toFixed(6)+'_MAX_'+limit.toFixed(6));
 const u=scale(axis,1/distance),along=(l1*l1-l2*l2+distance*distance)/(2*distance),height=Math.sqrt(Math.max(0,l1*l1-along*along));
 const planar=sub(pole,scale(u,dot(pole,u))),p=norm(planar);
 if(p<1e-6)throw Error('IK_POLE_SINGULAR');
 return add(add(hip,scale(u,along)),scale(planar,height/p));
}
__HAREWORKS_WORLD_IK_0110_3__
[[ "$(hash "$DIR/ik-core.mjs")" == "3ef7754dc8ca9cca22112c8e7ad3c4b5ecf070dc2e0d7b062a3ced16dc8c7f73" ]] || fail "EMBEDDED_PAYLOAD_SHA_INVALID_ik-core.mjs"
cat > "$DIR/contact-core-test.mjs" <<'__HAREWORKS_WORLD_IK_0110_4__'
import assert from 'node:assert/strict';
import {WorldContact,mod1,stanceAt,swingPoint,nextStartDelta,swingProgress,followCamera} from './contact-core.mjs';
assert.equal(mod1(-.25),.75);
const cam0=followCamera([0,0,0],[-5,3,6]);const cam1=followCamera([0,0,4],[-5,3,6]);assert.deepEqual(cam1.position.map((v,i)=>v-cam0.position[i]),[0,0,4]);assert.deepEqual(cam1.position.map((v,i)=>v-cam1.target[i]),[-5,3,6]);
assert.equal(stanceAt(.95,.8,.55),true);
assert.equal(stanceAt(.4,.8,.55),false);
assert.equal(nextStartDelta(.3,.8),.5);
assert(Math.abs(swingPoint([0,0,0],[0,0,1],.5,.13)[1]-.13)<1e-10);
const c=new WorldContact({side:'left',start:0,duty:.55,sole:[0,0,0],groundY:0});
let max=0,range=0;
for(let cycle=0;cycle<3;cycle++)for(let i=0;i<240;i++){
 const p=i/240,body=cycle+p,result=c.step({phase:p,nominalLanding:[0,0,body+.45],footLift:.12});
 if(result.planted){const delta=Math.hypot(...result.target.map((v,j)=>v-result.anchor[j]));max=Math.max(max,delta)}
 range=Math.max(range,body);
}
assert.equal(max,0,'world stance target must not depend on traveling root');
assert(c.transitions>=5,'alternating stance/swing must actually occur');
assert(range>2,'root must travel even while anchor stays fixed');
const s=new WorldContact({side:'right',start:.4,duty:.55,sole:[.2,0,0],groundY:0});
assert.equal(s.isStance,false);
for(let i=0;i<=120;i++)s.step({phase:i/120,nominalLanding:[.2,0,i/120+.2]});
assert(s.transitions>=2);
for(const x of [-2,-1,0,.01,.5,.999,3.2])assert(swingProgress(x,.3,.55)>=0);
assert.throws(()=>new WorldContact({side:'bad',start:0,sole:[NaN,0,0]}));
assert.throws(()=>c.step({phase:.2,nominalLanding:[0,NaN,0]}));
console.log('WORLD_CONTACT_TEST_PASS transitions='+c.transitions+' maxPinnedTargetDrift='+max+' movingRoot='+range);
__HAREWORKS_WORLD_IK_0110_4__
[[ "$(hash "$DIR/contact-core-test.mjs")" == "44202a5eec8c3f8ba4ba1cc7025fac0662326e3fbcc23432ee4e1a2df2d8fddb" ]] || fail "EMBEDDED_PAYLOAD_SHA_INVALID_contact-core-test.mjs"
cat > "$DIR/geometry-test.mjs" <<'__HAREWORKS_WORLD_IK_0110_5__'
import assert from 'node:assert/strict';
import {kneeFromTarget} from './ik-core.mjs';
const L1=.3567690913,L2=.3803240094;
const H0=[-.15,.85,0],H1=[-.15,.81,.12],A=[-.15,.18,.05],pole=[-.2,.1,.8];
const K0=kneeFromTarget(H0,A,L1,L2,pole),K1=kneeFromTarget(H1,A,L1,L2,pole);
const distance=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
for(const [h,k] of [[H0,K0],[H1,K1]]){assert(Math.abs(distance(h,k)-L1)<1e-8);assert(Math.abs(distance(k,A)-L2)<1e-8)}
assert(distance(K0,K1)>.01,'IK knee must respond to translated hip while ankle remains WORLD anchored');
assert.throws(()=>kneeFromTarget(H0,[3,0,0],L1,L2,pole),/UNREACHABLE/);
console.log('TRUE_TWO_BONE_WORLD_TARGET_GEOMETRY_PASS');
__HAREWORKS_WORLD_IK_0110_5__
[[ "$(hash "$DIR/geometry-test.mjs")" == "854e119b7ab0128b518327891c8636159f255434aec2c8a97a21eca41da0ba04" ]] || fail "EMBEDDED_PAYLOAD_SHA_INVALID_geometry-test.mjs"
cat > "$DIR/review-server.py" <<'__HAREWORKS_WORLD_IK_0110_6__'
"""Local-only exact build server and evidence sink. Does not publish model bytes."""
import hashlib
import http.server
import json
import os
import pathlib
import sys
root,ready,state=sys.argv[1:]
MODEL='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=root,**kwargs)
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
        self.send_header('Pragma','no-cache')
        super().end_headers()
    def do_POST(self):
        if not self.path.endswith('/evidence'):
            self.send_error(404);return
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<250 or n>2000000:raise ValueError('invalid evidence length')
            payload=self.rfile.read(n);data=json.loads(payload)
            if data.get('schema')!='hareworks-woman-world-pinned-ik-v0.1.10':raise ValueError('wrong schema')
            if data.get('sourceSha256')!=MODEL:raise ValueError('wrong original model')
            if data.get('sourceClip')!='Walking_Woman' or data.get('rigBones')!=74:raise ValueError('wrong source or rig')
            if data.get('generatedAnimationMixerCount')!=0 or data.get('oneVisibleCharacter') is not True:raise ValueError('requested execution lane absent')
            if data.get('cameraFixedFollow') is not True or data.get('stanceAnchorCoordinateSystem')!='WORLD':raise ValueError('camera or world lock absent')
            if data.get('physicsRateHz')!=120 or int(data.get('sampledFrames',0))<300:raise ValueError('incomplete physical audit')
            for field in ['worldTravelZ','maximumContactAnchorTranslation','maxFootPenetration','maxIKResidual','cameraWorldFollowError']:
                v=data.get(field)
                if not isinstance(v,(float,int)) or not (-1e8<v<1e8):raise ValueError('invalid '+field)
            if data.get('status') not in ['WORLD_IK_GATE_PASS_OWNER_REVIEW_PENDING','WORLD_IK_GATE_WARN_OWNER_REVIEW_REQUIRED']:raise ValueError('invalid audit status')
            out=pathlib.Path(state);out.mkdir(parents=True,exist_ok=True)
            path=out/'woman-world-ik-evidence.json';path.write_bytes(payload)
            receipt={'state':'REAL_BROWSER_SKINNED_WORLD_PIN_AUDIT_SAVED_NOT_OWNER_APPROVED','sha256':hashlib.sha256(payload).hexdigest(),'path':str(path),'sourceSHA256':MODEL,'ownerAccepted':False,'auditedPass':data['status']=='WORLD_IK_GATE_PASS_OWNER_REVIEW_PENDING'}
            (out/'woman-world-ik-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
            result=json.dumps(receipt).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(result)));self.end_headers();self.wfile.write(result)
        except Exception as e:self.send_error(422,'evidence rejected: '+str(e)[:80])
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
pathlib.Path(ready).write_text(json.dumps({'pid':os.getpid(),'port':server.server_address[1],'root':root,'state':state}))
server.serve_forever()
__HAREWORKS_WORLD_IK_0110_6__
[[ "$(hash "$DIR/review-server.py")" == "c3e4574035472029ddec4e713d6f4f4de734b5eb829bdca459e79194f54248b7" ]] || fail "EMBEDDED_PAYLOAD_SHA_INVALID_review-server.py"
cat > "$DIR/README.md" <<'__HAREWORKS_WORLD_IK_0110_7__'
# Hareworks Walking_Woman world-space locomotion and true foot IK v0.1.10

## Owner's authorized deliverable

One visible character. It must translate forward through an actual 3D world, while the camera follows at a pinned offset (no camera bob), and the actual skinned soles remain fixed at persistent world coordinates through stance. During swing, each sole gets a new landing target. Leg bones are freshly solved from world-space foot targets, not copied from an animation. Source animation is allowed for STARTUP calibration of pelvis/upper body and low-foot contact phases only. Arms are deferred to independent IK.

**This specifically replaces the earlier in-place v0.1.9 proof as the active evaluation implementation.** The original approved v0.1.9 source files are not modified; the user may still use them for visual reference. No second actor is rendered. The accepted v0.2.2 backward, v0.2.7 left step, and pelvis-only v0.2.6 experiment are unmodified and NOT claimed as real locomotion IK.

## Actual driver

- Original canonical `assets/hareworks/Hareworks-nine-clips.glb`, SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`, size 6,784,896, 74 bones, nine clips. Exact model checked before publication and in browser.
- Temporary hidden source clone uses the original `Walking_Woman` AnimationMixer during INITIAL calibration only: 120 samples for source-anchored periodic pelvis and spine/subtree pose curves; 240 samples to establish skinned sole low-height phases. The source clone/mixer are disposed. **Visible runtime character never plays a source animation clip.**
- The visible root moves in **world Z** by integrating `speed*dt`. Speed and cadence are linked; terrain markers and the ground grid stay fixed in world space.
- Skinned-sole patches are chosen from actual canonical mesh vertices near each foot, via `SkinnedMesh.getVertexPosition` and mesh transforms. Each stance contact stores a WORLD anchor that remains unchanged despite root movement. On liftoff, a spline travels from old anchor to a predicted world landing plus toe clearance. The next stance latches that landing.
- At 120 Hz each thigh and calf are restored to calibration rest, then independently rotated from analytic world ankle target and anatomical knee pole using a TWO-BONE IK solve. Foot WORLD orientation is resolved; measured skinned-sole residuals are iteratively corrected (up to 4 passes). Upper body follows periodic fitted curves, not source tracks. A limited pelvis reach adjustment is disclosed if a target would otherwise be outside the skeletal reach.
- Camera presets are a FIXED FOLLOW camera tied to `actor.position`, never pelvis height or yaw. The single actor stays near center while the world scrolls under it.
- Real browser three-cycle audit advances 120 Hz in one virtual timeline; measures each skinned foot patch's displacement from its fixed anchor during stance, anchor world-motion, world Z travel, penetrating sole sample, reach adjustments and follow-camera relative error. Browser writes a durable JSON evidence artifact to the phone Termux campaign state; a ZIP, build receipt or unit test is not visual or physical proof.

## Hard caveats / explicit scope

This is a first integrated world-IK implementation to test on the real phone GLB. The stance windows come from low-sole phases (heuristic contact inference), not force sensors. Skinned vertices are sampled around the shoe, not proven full sole support polygons. The future landing position is predicted from the accepted pelvis/foot Fourier curves and world velocity. It may need parameter tuning based on the real 120 Hz measurements and the owner's visual inspection. A pre-rendered screenshot, local fixture or source checksum cannot establish successful mobile pinning.

**Success gate:** Real browser audit with both feet skinned-sole drift <=0.025 model units in stance, no anchor motion inside stance beyond numerical noise, actual world movement >0.9 model units across 3 cycles, camera follow error near zero, no reach rejections, and owner visual approval. Measurement failures are visible, not hidden. Camera never moves due to pelvis bob. The allowed travel input is 0–0.8 model units/second.

## Publication

Only Android Termux Git may install/commit/push through the user's phone, from an isolated verified checkout with fresh remote HEAD verification, a protected source list and a unique destination collision gate. Nothing touches the GLB or accepted earlier gait implementations. The packet includes test-driven pure contact and analytic IK geometry, syntax checks, browser source-hash checks, exact HTTP readback and a persistent Termux receipt. The full viewer URL (dynamic localhost port) is printed only after the phone executes the campaign.

Mandatory fresh authority: AGENTS.md Git blob `547c2af52303f4efb718bbf8f82a698110c7bfca`; Campaign Etiquette Home Center `1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI`; Top-down Etiquette Home Center `1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU`.
__HAREWORKS_WORLD_IK_0110_7__
[[ "$(hash "$DIR/README.md")" == "5cebc611841b6f83f7c442aafd7904347c1310080097fac240a00d163df44f46" ]] || fail "EMBEDDED_PAYLOAD_SHA_INVALID_README.md"
cat > "$DIR/contract.json" <<'__HAREWORKS_WORLD_IK_0110_8__'
{
  "schema": "hareworks-woman-world-pinned-ik-campaign-v0.1.10",
  "repo": "Valar05/parametric-parambulator",
  "parent": "7ebee024ac9f88251ed4e6db6802fcb41589c6e1",
  "ownerGoal": "One Walking_Woman character moving through world, world-space sole pinning, true realtime two-bone IK and fixed-follow camera, exactly like Repl behavior",
  "executionLane": "Android Termux Git only",
  "originalModel": "assets/hareworks/Hareworks-nine-clips.glb",
  "modelSHA256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "modelBytes": 6784896,
  "referenceClip": "Walking_Woman",
  "sourceAnimatedAtRuntimeOnGenerated": false,
  "sourceAnimationUsedForStartupCalibrationOnly": true,
  "visibleCharacters": 1,
  "worldMovement": true,
  "cameraFixedFollow": true,
  "worldAnchorsPersistDuringStance": true,
  "actualSkinnedFootPatchAudited": true,
  "ik": "Two-bone world hip-knee-ankle plus iterative true skinned sole correction, per 120Hz step",
  "armIK": "reserved for future, not implemented",
  "acceptedVersionsUntouched": ["v0.1.9 Walking_Woman visual", "v0.2.2 backward", "v0.2.7 left", "v0.2.6 pelvis style lab"],
  "maxSkinnedStanceDrift": 0.025,
  "worldTravelAt3CyclesMin": 0.9,
  "cameraRelativeDriftMax": 0.000001,
  "physicsRateHz": 120,
  "rulesAGENTSBlob": "547c2af52303f4efb718bbf8f82a698110c7bfca",
  "rulesCampaignEtiquette": "1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI",
  "rulesTopDownEtiquette": "1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU",
  "state": "script prepared, real skinned phone runtime and owner visual acceptance pending"
}
__HAREWORKS_WORLD_IK_0110_8__
[[ "$(hash "$DIR/contract.json")" == "35e4ce8e74366d0c149d0dc1c097ae57f10f560939552b9cdb8f5c2aed722b7c" ]] || fail "EMBEDDED_PAYLOAD_SHA_INVALID_contract.json"
cp -- "$0" "campaigns/$CAMPAIGN.sh" || fail "campaign source mirror failed"
[[ "$(hash "campaigns/$CAMPAIGN.sh")" == "$SELF_SHA" ]] || fail "mirror script SHA mismatch"
 git add -- "${FILES[@]}" || fail 'cannot stage new versioned files'
 python3 - "${FILES[@]}" <<'PY_STAGE' || fail 'staged paths differ from authorized list'
import subprocess,sys
expected=set(sys.argv[1:]);got=set(subprocess.check_output(['git','diff','--cached','--name-only']).decode().splitlines())
assert expected==got,('UNAUTHORIZED_STAGED_FILES',sorted(got^expected))
print('SCOPED_STAGED_FILES=PASS',len(got))
PY_STAGE
 node "$DIR/contact-core-test.mjs" || fail 'world anchor and pinned camera tests failed'
 node "$DIR/geometry-test.mjs" || fail 'real analytic two-bone geometry test failed'
 for file in "$DIR/viewer.mjs" "$DIR/contact-core.mjs" "$DIR/ik-core.mjs";do node --check "$file" || fail "JS syntax failed $file";done
 PYTHONPYCACHEPREFIX="$STATE/pycache" python3 -m py_compile "$DIR/review-server.py" || fail 'server source invalid'
 python3 - "$DIR" <<'PY_WEB_STATIC' || fail 'single character and model reference static contract failed'
import pathlib,sys
p=pathlib.Path(sys.argv[1]);viewer=(p/'viewer.mjs').read_text();html=(p/'index.html').read_text()
assert 'const source=cloneSkeleton(gltf.scene);actor=cloneSkeleton(gltf.scene)' in viewer
assert 'new THREE.AnimationMixer(source)' in viewer
assert 'new THREE.AnimationMixer(actor)' not in viewer
assert 'new WorldContact' in viewer and 'soleWorld(' in viewer
assert 'kneeFromTarget(' in viewer and 'physicsStep(1/120)' in viewer
assert 'followCamera(' in viewer and 'id="stage"' in html
assert 'two characters' not in html.lower()
print('ONE_ACTOR_WORLD_IK_AND_CAMERA_STATIC_GATE_PASS')
PY_WEB_STATIC
 phase=commit-and-push
 git commit -m "Hareworks v0.1.10: one traveling woman with world-pinned skinned soles and true IK" || fail 'Termux git commit failed'
 COMMIT=$(git rev-parse HEAD)
 [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'new commit parent changed unexpectedly'
 [[ -z "$(git status --porcelain)" ]] || fail 'unexpected dirty isolated Git after commit'
 pushed=0
 for attempt in 1 2 3;do
  if git push origin HEAD:refs/heads/main;then pushed=1;break;fi
  found=$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1) || found=''
  if [[ "$found" == "$COMMIT" ]];then pushed=1;break;fi
  [[ "$found" == "$BASE" ]] || fail 'concurrent main movement, no force push'
  sleep "$attempt"
 done
 (( pushed==1 )) || fail 'commit remains in preserved isolated snapshot; remote publication NOT confirmed'
else COMMIT="$REMOTE";node "$DIR/contact-core-test.mjs" || fail 'published world contact test failed';node "$DIR/geometry-test.mjs" || fail 'published IK test failed';fi
phase=remote-readback
FOUND=''
for attempt in 1 2 3;do FOUND=$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1) || FOUND='';[[ "$FOUND" == "$COMMIT" ]] && break;sleep "$attempt";done
[[ "$FOUND" == "$COMMIT" ]] || fail 'remote Git main is not verified published commit'
git fetch -q origin "$COMMIT" || fail 'cannot fetch published remote commit for exact blob readback'
python3 - "$DIR" "$CAMPAIGN" <<'PY_READBACK' || fail 'remote exact published files differ from staging'
import hashlib,pathlib,subprocess,sys
root,campaign=sys.argv[1:]
paths=[str(x) for x in pathlib.Path(root).iterdir() if x.is_file() and x.name!='__pycache__']
paths.append('campaigns/'+campaign+'.sh')
for p in paths:
 a=pathlib.Path(p).read_bytes();b=subprocess.check_output(['git','show','FETCH_HEAD:'+p])
 assert hashlib.sha256(a).digest()==hashlib.sha256(b).digest(),('remote readback failed',p)
print('REMOTE_EXACT_FILE_READBACK_PASS',len(paths))
PY_READBACK
for path in tools/hareworks-forward-woman/v0.1.9/viewer.mjs tools/hareworks-forward-woman/v0.2.2/viewer.mjs tools/hareworks-forward-woman/v0.2.6/viewer.mjs tools/hareworks-forward-woman/v0.2.7/viewer.mjs tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs tools/hareworks-forward-woman/v0.1.9/upper-anchor.mjs AGENTS.md "$MODEL";do
 [[ "$(git rev-parse HEAD^:"$path")" == "$(git rev-parse HEAD:"$path")" ]] || fail "accepted source changed: $path"
done
phase=distinct-no-cache-phone-viewer
# This is a separate isolated checkout, never a working tree used by the owner.
cp -- "$SOURCE" "$MODEL" || fail 'real model local HTTP snapshot copy failed'
[[ "$(hash "$MODEL")" == "$MODEL_SHA" ]] || fail 'local viewer model identity lost'
READY="$ROOT/server-ready.json"
nohup python3 "$DIR/review-server.py" "$WORK" "$READY" "$STATE" > "$ROOT/server.log" 2>&1 </dev/null &
PID=$!
for i in 1 2 3 4 5 6 7 8 9 10 11 12;do
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
[[ "$PORT" =~ ^[0-9]+$ ]] && kill -0 "$PID" 2>/dev/null || fail 'phone HTTP server did not open fresh port'
python3 - "http://127.0.0.1:$PORT" "$DIR" "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" "$STATE/http-manifest.json" <<'PY_HTTP' || fail 'HTTP source, dependencies or original GLB mismatch'
import hashlib,json,pathlib,sys,urllib.request
origin,dir,model,sha,size,out=sys.argv[1:]
def get(url):
 with urllib.request.urlopen(url,timeout=40) as r:
  assert 'no-store' in r.headers.get('Cache-Control',''),('cache',url)
  return r.read()
root=origin+'/'+dir+'/'
resources=['index.html','viewer.mjs','contact-core.mjs','ik-core.mjs','contact-core-test.mjs','geometry-test.mjs','review-server.py','README.md','contract.json']
urls=[root+x for x in resources]+[origin+'/tools/hareworks-forward-woman/v0.1.9/upper-anchor.mjs',origin+'/tools/hareworks-forward-woman/v0.1.5/upper-kernel.mjs',origin+'/tools/hareworks-forward-woman/v0.1.2/pose-kernel.mjs',origin+'/tools/hareworks-forward-woman/v0.1.2/motion-profile.json',origin+'/tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs',origin+'/tools/hareworks-forward-woman/v0.1.3/foot-profile.json']
for url in urls: assert get(url),('HTTP dependency absent',url)
blob=get(origin+'/'+model)
assert len(blob)==int(size) and hashlib.sha256(blob).hexdigest()==sha
record={'status':'HTTP_FULL_SOURCE_MODEL_AND_SINGLE_ACTOR_MODULE_GRAPH_VERIFIED_BROWSER_SKINNED_IK_PENDING','modelSHA256':sha,'bytes':len(blob),'resources':urls,'browserSkinnedFootPinAudit':'PENDING','ownerVisualApproval':'PENDING'}
pathlib.Path(out).write_text(json.dumps(record,indent=2)+'\n')
print('REAL_PHONE_HTTP_MODEL_AND_DEPENDENCIES_PASS',len(urls))
PY_HTTP
curl -fsSI --max-time 5 "http://127.0.0.1:$PORT/$DIR/index.html" > "$STATE/http-headers.txt" || fail 'HTTP response headers missing'
URL="http://127.0.0.1:$PORT/$DIR/index.html?commit=$COMMIT&scriptSha=$SELF_SHA&modelSha=$MODEL_SHA"
python3 - "$STATE/receipt.json" "$CAMPAIGN" "$BASE" "$COMMIT" "$SELF_SHA" "$MODEL_SHA" "$AGENTS_BLOB" "$URL" "$PID" "$PORT" "$ROOT" <<'PY_RECEIPT'
import datetime,json,pathlib,sys
p,campaign,parent,commit,script,model,agents,url,pid,port,snapshot=sys.argv[1:]
receipt={'campaign':campaign,'state':'REMOTE_GIT_PUBLISHED_HTTP_REAL_MODEL_VERIFIED_BROWSER_TRUE_SKINNED_PINNING_PENDING',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'auditedParent':parent,'remotePublishedCommit':commit,'scriptSHA256':script,'originalSourceModelSHA256':model,
 'AGENTSBlobVerified':agents,'freshAuthority':{'AGENTS':'remote Git blob','Campaign Etiquette Home Center':'1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI','Top-down Etiquette Home Center':'1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'},
 'originalGLBMutated':False,'acceptedForwardV019Mutated':False,'acceptedBackwardV022Mutated':False,'acceptedLeftV027Mutated':False,
 'visibleCharacters':1,'worldRootTranslation':True,'cameraFixedFollow':True,'sourceClipRuntimeGeneratedMixer':False,'worldAnchorOnTouchdown':True,'twoBoneIKPerStep':True,'trueSkinnedSoleMeasurement':True,
 'NodePureMotionTests':'PASS','realGLBSourceIdentity':'VERIFIED','HTTPModelAndModuleManifest':'PASS','realBrowserSkinnedFootPinAudit':'PENDING','ownerVisualAcceptance':'PENDING',
 'viewerURL':url,'viewerPID':int(pid),'viewerPort':int(port),'isolatedSnapshot':snapshot,'executionLane':'Android Termux Git ONLY','browserEvidencePath':str(pathlib.Path(p).parent/'woman-world-ik-evidence.json')}
pathlib.Path(p).write_text(json.dumps(receipt,indent=2)+'\n')
PY_RECEIPT
echo "REMOTE_COMMIT=$COMMIT"
echo "CANONICAL_MODEL_SHA256=$MODEL_SHA"
echo "WORLD_GAIT_MODE=ONE_CHARACTER_MOVING_WITH_PINNED_WORLD_SOLES_AND_FOLLOW_CAMERA"
echo "VIEWER_URL=$URL"
echo "VIEWER_PORT=$PORT VIEWER_PID=$PID"
echo "RECEIPT=$STATE/receipt.json"
echo "BROWSER_SKINNED_AUDIT_AFTER_RUN=$STATE/woman-world-ik-evidence.json"
echo "BROWSER_MEASUREMENT_RECEIPT_AFTER_RUN=$STATE/woman-world-ik-receipt.json"
echo 'REAL_SKINNED_SOLE_PINNING=PENDING_BROWSER_MEASUREMENT OWNER_ACCEPTANCE=PENDING'
if command -v termux-open-url >/dev/null;then
 termux-open-url "$URL" || echo "TERMUX_OPEN_FAILED; open VIEWER_URL=$URL"
else echo "TERMUX_OPEN_NOT_INSTALLED; open VIEWER_URL=$URL";fi
