#!/data/data/com.termux/files/usr/bin/bash
# Hareworks v0.2.3 source-only research: Walking vs Walking_Woman; all 74 joints.
# Owner-approved forward and backward systems remain byte-identical.
set -Eeuo pipefail
CAMPAIGN='hareworks-walking-style-research-v0.2.3'
REPO='Valar05/parametric-parambulator'
BASE='3e298e9c9d99c6cb372bc5c8b2f9c8cb77d46ab6'
DIR='tools/hareworks-forward-woman/v0.2.3'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE='6784896'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ACCEPTED_FORWARD='a17f8109766dcfa39fbb75b6b2ff335c358733cb'
ACCEPTED_BACKWARD='61c9bea2aa3c5da5f331c45e2df41077670c3603'
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
pathlib.Path(p).write_text(json.dumps({'campaign':name,'state':'BLOCKED','phase':phase,'reason':reason,'knownCommit':commit,'isolatedSnapshot':root,'ownerApprovedGaitsUnmodified':True,'researchMeasurements':'NOT_VERIFIED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
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
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" <<'PY_POINTER' || fail 'canonical original model Git LFS pointer mismatch'
import subprocess,sys
path,sha,size=sys.argv[1:]
want=f'version https://git-lfs.github.com/spec/v1\noid sha256:{sha}\nsize {size}\n'.encode()
assert subprocess.check_output(['git','show','HEAD:'+path])==want
print('SOURCE_GLB_GIT_LFS_IDENTITY=PASS')
PY_POINTER
FILES=("$DIR/index.html" "$DIR/viewer.mjs" "$DIR/analysis-core.mjs" "$DIR/analysis-core-test.mjs" "$DIR/research-server.py" "$DIR/README.md" "$DIR/contract.json" "campaigns/$CAMPAIGN.sh")
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
if ((PUBLISHED==0));then mkdir -p "$DIR" || fail 'new research directory failed';fi
if ((PUBLISHED==0));then
 cat > "$DIR/index.html" <<'__HAREWORKS_RESEARCH_V023_INDEX_HTML__'
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#101a25"><title>Hareworks 0.2.3 | Walking vs Walking_Woman | 74-joint style research</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>:root{font:14px/1.48 system-ui,sans-serif;color:#e7f2fa;background:#101a25;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:1180px;margin:auto;padding:10px}h1{font-size:19px;margin:7px 0 2px}h2{font-size:16px;margin:12px 0 6px}p{margin:5px 0 12px;color:#c4d5e3}small{color:#a9c0d2}#identity{font:11px/1.5 ui-monospace,monospace;overflow-wrap:anywhere;color:#91baca;margin:9px 0}#status{color:#8febbe;padding:7px 0;min-height:36px}#stage{border:1px solid #5c748d;border-radius:10px;overflow:hidden}canvas{display:block;width:100%;touch-action:none}.labels{display:grid;grid-template-columns:1fr 1fr;gap:12px;text-align:center;margin:6px 0 10px}.toolbar{display:flex;flex-wrap:wrap;gap:9px;background:#203247;padding:11px;border-radius:8px;margin:10px 0;align-items:center}button{font:inherit;color:white;background:#2d4b64;border:1px solid #6b94ac;border-radius:7px;padding:10px;min-height:44px}input{accent-color:#78d4ee}input[type=range]{flex:1;min-width:130px}label{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.report{border:1px solid #527089;background:#162737;border-radius:9px;padding:12px;white-space:pre-wrap;font:12px/1.6 ui-monospace,monospace;overflow-wrap:anywhere;max-height:58vh;overflow:auto}table{width:100%;border-collapse:collapse;font-size:12px}td,th{padding:7px 4px;border-bottom:1px solid #3a5366;text-align:left}th{position:sticky;top:0;background:#203247}.tableWrap{overflow:auto;max-height:50vh}a{color:#9adbf3}select{font:inherit;color:white;background:#2d4b64;padding:10px;border:1px solid #7190a8;border-radius:6px}</style></head><body><main>
<h1>🐇 Hareworks · What makes <em>Walking_Woman</em> different?</h1><p><strong>v0.2.3 research only.</strong> Two authentic source clips, no generated gait and no style transfer. Measures all 74 bones, separating initial pose offsets from time-varying motion differences. Same character, same rig.</p>
<div id="identity">Validating source binary and published build…</div><div id="status" role="status" aria-live="polite">Loading and verifying original Hareworks GLB…</div>
<div class="labels"><strong>SOURCE: Walking</strong><strong>SOURCE: Walking_Woman</strong></div><div id="stage" role="img" aria-label="Side-by-side three-dimensional comparison of the two source walk animations"></div>
<div class="toolbar" role="group" aria-label="Camera controls"><button id="side">Side</button><button id="front">Front</button><button id="oblique">Three-quarter</button><button id="top">Top</button><small>Drag to orbit, pinch to zoom</small></div>
<div class="toolbar"><button id="play">Pause</button><label>Normalized gait phase <input id="phase" type="range" min="0" max="999" value="0" step="1" aria-label="Cycle phase"></label><output id="phaseLabel">0%</output><label><input type="checkbox" id="aligned" checked>Phase align by legs</label><label><input type="checkbox" id="inPlace" checked>Display in place</label></div>
<div class="toolbar"><button id="analyze">Recalculate 74-joint research</button><button id="jsonExport">Download full JSON</button><button id="csvExport">Download 74-bone CSV</button><label>Sort <select id="sort"><option value="motionDeltaRmsDeg">Dynamic motion difference</option><option value="staticPoseOffsetDeg">Initial pose difference</option><option value="hipRelativePositionDifferenceRmsUnits">Pelvis-relative position difference</option></select></label></div>
<h2>Research summary</h2><div id="summary" class="report" role="status">Awaiting original skinned source comparison…</div>
<h2>All 74 joints</h2><div class="tableWrap"><table><thead><tr><th>Joint</th><th>Group</th><th>Dynamic Δ RMS</th><th>Initial offset</th><th>Motion ratio W/N</th><th>Hip-relative Δ</th></tr></thead><tbody id="rows"><tr><td colspan="6">Source analysis pending</td></tr></tbody></table></div>
<p><small>Source clips are untouched. The displayed “in place” option subtracts estimated horizontal translation from each preview root only. All measurements use unmodified source bone transforms, compared in the pelvis frame or parent-local frame. Phase alignment is a measured trajectory match, not proof of physical foot contact. Terminal root reset keys are excluded from the research window. A numerical distinction is not automatically a transferable movement rule. Existing accepted forward and backward viewer files are immutable.</small></p>
</main><script type="module" src="./viewer.mjs"></script></body></html>
__HAREWORKS_RESEARCH_V023_INDEX_HTML__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/viewer.mjs" <<'__HAREWORKS_RESEARCH_V023_VIEWER_MJS__'
/* Hareworks v0.2.3 source-only forward gait style research. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {alignPhase,compareClips,poseAt,mod1,angleDeg,conjugate,multiply,rms,range} from './analysis-core.mjs';
const $=id=>document.getElementById(id),V=()=>new THREE.Vector3(),Q=()=>new THREE.Quaternion();
const SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6', URL_GLB='../../../assets/hareworks/Hareworks-nine-clips.glb';
const CLIPS=['Walking','Walking_Woman'],N=360,SEP=2.9;
const scene=new THREE.Scene();scene.background=new THREE.Color('#111c28');scene.add(new THREE.HemisphereLight(0xeaf3ff,0x344459,2.6));
const light=new THREE.DirectionalLight(0xffffff,3.3);light.position.set(-4,7,6);scene.add(light);
const grid=new THREE.GridHelper(13,26,0x6d8699,0x364d60);scene.add(grid);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-4,4,2.5,-2.5,.01,100),orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.enablePan=false;orbit.target.set(0,.95,0);orbit.minZoom=.55;orbit.maxZoom=3.5;
const cameraPos={side:[-7,3.4,0],front:[0,2.5,9],oblique:[-5.5,3.5,5.5],top:[-.01,9,.01]};
function cameraAt(key){camera.position.set(...cameraPos[key]);camera.up.set(0,1,0);camera.zoom=1;camera.lookAt(orbit.target);camera.updateProjectionMatrix();orbit.update()}
function resize(){const w=Math.max(320,$('stage').clientWidth),h=Math.max(290,Math.min(570,Math.round(w*.67)));renderer.setSize(w,h,false);camera.left=-2.3*w/h;camera.right=-camera.left;camera.top=2.3;camera.bottom=-2.3;camera.updateProjectionMatrix();orbit.update()}
window.addEventListener('resize',resize);for(const key of Object.keys(cameraPos))$(key).onclick=()=>cameraAt(key);cameraAt('side');resize();
const models={},rigs={},mixers={},clips={},samples={},rootTrend={};let ready=false,playing=false,phase=0,last=performance.now(),report=null,alignment=null;
const status=s=>$('status').textContent=s;
function rigOf(root){const bones={};root.traverse(x=>{if(x.isBone){if(bones[x.name])throw Error('DUPLICATE_BONE_'+x.name);bones[x.name]=x}});if(Object.keys(bones).length!==74)throw Error('EXPECTED_74_BONES_'+Object.keys(bones).length);for(const name of ['mixamorigHips','mixamorigHead','mixamorigLeftFoot','mixamorigRightFoot','mixamorigLeftArm','mixamorigRightArm','mixamorigLeftForeArm','mixamorigRightForeArm','mixamorigLeftHand','mixamorigRightHand'])if(!bones[name])throw Error('REQUIRED_JOINT_MISSING_'+name);return bones}
function capture(key){const root=models[key],rig=rigs[key],mixer=mixers[key],clip=clips[key],boneNames=Object.keys(rig);
 const data={count:N,boneNames,duration:clip.duration,bones:{},rootPositions:[],rootOrientations:[]};for(const name of boneNames)data.bones[name]=[];
 for(let i=0;i<N;i++){
  const p=i/N;mixer.setTime(p*clip.duration);root.updateMatrixWorld(true);
  const hips=rig.mixamorigHips,hipPos=hips.getWorldPosition(V()),hipQuat=hips.getWorldQuaternion(Q()),inverse=hipQuat.clone().invert();
  data.rootPositions.push(hips.position.toArray());data.rootOrientations.push(hipQuat.toArray());
  for(const name of boneNames){const b=rig[name],wp=b.getWorldPosition(V()),hp=wp.clone().sub(hipPos).applyQuaternion(inverse);
   data.bones[name].push({lq:b.quaternion.toArray(),lp:b.position.toArray(),wp:wp.toArray(),hq:b.getWorldQuaternion(Q()).toArray(),hp:hp.toArray()});
  }
 }
 mixer.setTime(0);root.updateMatrixWorld(true);
 // Measure root trend before the baked terminal reset, as a DISPLAY correction only.
 const p0=data.rootPositions[0],p1=data.rootPositions[Math.floor(N*.89)],f=.89;
 rootTrend[key]=[(p1[0]-p0[0])/f,0,(p1[2]-p0[2])/f];
 return data;
}
function referenceAt(p){for(const key of CLIPS){const q=key==='Walking_Woman'&&$('aligned').checked&&alignment?mod1(p+alignment.womanPhaseOffset):p;
  mixers[key].setTime(q*clips[key].duration);
  if($('inPlace').checked){const hips=rigs[key].mixamorigHips,vec=rootTrend[key];hips.position.x-=vec[0]*q;hips.position.z-=vec[2]*q;}
  models[key].updateMatrixWorld(true);
 }
 $('phaseLabel').textContent=`${Math.round(p*100)}% / aligned woman ${Math.round((alignment?mod1(p+alignment.womanPhaseOffset):p)*100)}%`;
}
function download(data,name,type){const blob=new Blob([data],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');a.download=name;a.href=url;a.click();setTimeout(()=>URL.revokeObjectURL(url),5500)}
function csvEvidence(r){const cols=['bone','group','sampledAlignedPhases','staticPoseOffsetDeg','meanRawPoseDifferenceDeg','motionDeltaRmsDeg','motionDeltaMaxDeg','phaseOfMaxDynamicDifference','normalMotionFromAnchorRmsDeg','womanMotionFromAnchorRmsDeg','motionFromAnchorRmsRatio','hipRelativePositionDifferenceRmsUnits','localTranslationMotionDeltaRmsUnits'];const rows=[cols.join(',')];for(const b of r.perBone){rows.push(cols.map(k=>String(b[k]??'').replaceAll('"','""')).map(v=>`"${v}"`).join(','))}return rows.join('\n')+'\n'}
function sourceGaitTraits(clip,key){
 const usable=Math.floor(N*.93),hip=clip.rootPositions.slice(0,usable),ori=clip.rootOrientations.slice(0,usable);
 const eulers=ori.map(q=>new THREE.Euler().setFromQuaternion(new THREE.Quaternion().fromArray(q),'YXZ'));
 const unwrap=v=>{const out=[];let previous=null;for(let x of v){if(previous!==null){while(x-previous>Math.PI)x-=2*Math.PI;while(x-previous<-Math.PI)x+=2*Math.PI}out.push(x);previous=x}return out};
 const tr=key=>range(unwrap(eulers.map(x=>x[key])))*180/Math.PI;
 const relative=(name,axis)=>clip.bones[name].slice(0,usable).map(s=>s.hp[axis]);
 const head=clip.bones.mixamorigHead,chest=clip.bones.mixamorigSpine2??clip.bones.mixamorigSpine1??clip.bones.mixamorigSpine;
 const angularHead=[];if(head&&chest){const q0=multiply(conjugate(chest[0].hq),head[0].hq);
  for(let i=0;i<usable;i++){const q=multiply(conjugate(chest[i].hq),head[i].hq);angularHead.push(angleDeg(q0,q))}}
 const footEvents={};for(const side of ['Left','Right']){const name='mixamorig'+side+'Foot';const ys=clip.bones[name].slice(0,usable).map(s=>s.wp[1]);let min=0;for(let i=1;i<ys.length;i++)if(ys[i]<ys[min])min=i;footEvents[side.toLowerCase()]={lowestFootPhase:min/N,sourceFootHeight:ys[min],interpretation:'lowest-foot candidate, not proven foot contact'}}
 return {durationSeconds:clip.duration,
  pelvisYawRangeDeg:tr('y'),pelvisPitchRangeDeg:tr('x'),pelvisRollRangeDeg:tr('z'),
  pelvisVerticalBounceUnits:range(hip.map(v=>v[1])),
  pelvisLateralSwayDetrendedUnits:range(hip.map((v,i)=>v[0]-(rootTrend[key][0]*i/N))),
  headSideToSideRelativeToHipsUnits:range(relative('mixamorigHead',0)),
  headOrientationRelativeToChestRmsChangeDeg:rms(angularHead),
  leftFootForeAftHipFrameUnits:range(relative('mixamorigLeftFoot',2)),
  rightFootForeAftHipFrameUnits:range(relative('mixamorigRightFoot',2)),
  leftFootLateralHipFrameUnits:range(relative('mixamorigLeftFoot',0)),
  rightFootLateralHipFrameUnits:range(relative('mixamorigRightFoot',0)),
  footLowPointCandidates:footEvents};
}
function traitSection(r){const a=r.gaitTraits.Walking,b=r.gaitTraits.Walking_Woman;
 const fields=[['Pelvis yaw range','pelvisYawRangeDeg','°'],['Pelvis pitch range','pelvisPitchRangeDeg','°'],['Pelvis roll range','pelvisRollRangeDeg','°'],['Vertical pelvis bounce','pelvisVerticalBounceUnits',' units'],['Detrended sideways pelvis travel','pelvisLateralSwayDetrendedUnits',' units'],['Head lateral excursion vs pelvis','headSideToSideRelativeToHipsUnits',' units'],['Head/chest orientation RMS','headOrientationRelativeToChestRmsChangeDeg','°'],['Left foot fore-aft travel','leftFootForeAftHipFrameUnits',' units'],['Right foot fore-aft travel','rightFootForeAftHipFrameUnits',' units'],['Left foot lateral travel','leftFootLateralHipFrameUnits',' units'],['Right foot lateral travel','rightFootLateralHipFrameUnits',' units']];
 return ['SOURCE GAIT TRAITS: normal vs woman (authored clip measurements):',...fields.map(([label,key,unit])=>` ${label.padEnd(35)} ${a[key]?.toFixed(3)??'n/a'} → ${b[key]?.toFixed(3)??'n/a'}${unit}  (${a[key]>1e-8?((b[key]/a[key]-1)*100).toFixed(0)+'%':'ratio n/a'})`)];
}
function publish(r){const sort=$('sort').value, ranked=[...r.perBone].sort((a,b)=>(b[sort]??-Infinity)-(a[sort]??-Infinity));
 $('rows').replaceChildren();for(const b of ranked){const tr=document.createElement('tr');const vals=[b.bone.replace('mixamorig',''),b.group,b.motionDeltaRmsDeg.toFixed(2)+'°',b.staticPoseOffsetDeg.toFixed(2)+'°',b.motionFromAnchorRmsRatio===null?'n/a':b.motionFromAnchorRmsRatio.toFixed(2)+'×',b.hipRelativePositionDifferenceRmsUnits.toFixed(4)];for(const s of vals){const td=document.createElement('td');td.textContent=s;tr.append(td)}$('rows').append(tr)}
 const arms=r.perBone.filter(b=>/shoulders|upper-arms|forearms|hands/.test(b.group));const groups=Object.entries(r.groups).sort((a,b)=>b[1].meanBoneMotionDeltaRmsDeg-a[1].meanBoneMotionDeltaRmsDeg);
 const landmark=['mixamorigHips','mixamorigSpine','mixamorigNeck','mixamorigHead','mixamorigLeftShoulder','mixamorigRightShoulder','mixamorigLeftArm','mixamorigRightArm','mixamorigLeftForeArm','mixamorigRightForeArm','mixamorigLeftHand','mixamorigRightHand','mixamorigLeftFoot','mixamorigRightFoot'];
 const lines=[`ACTUAL SOURCE CLIPS: Walking ${r.clips.Walking.durationSeconds.toFixed(6)}s vs Walking_Woman ${r.clips.Walking_Woman.durationSeconds.toFixed(6)}s`,`CYCLE DURATION: Woman is ${((1-r.clips.Walking_Woman.durationSeconds/r.clips.Walking.durationSeconds)*100).toFixed(1)}% shorter`,`FIT FOOT-TRAJECTORY OFFSET: ${(r.alignment.womanPhaseOffset*100).toFixed(2)}% of female cycle (cost ${r.alignment.cost.toFixed(4)})`,`ALIGNED SOURCE PHASE PAIRS: ${r.sampledMatchedPhases} | 74/74 joints | last 7% excluded`,`NOTE: Static pose difference != dynamic motion difference. Ranked by dynamic difference, not initial pose.`,``,...traitSection(r),``,`BODY REGION (mean local rotation dynamic delta RMS):`,...groups.map(([k,v])=>` ${k.padEnd(16)} ${v.meanBoneMotionDeltaRmsDeg.toFixed(2).padStart(7)}° across ${v.boneCount} bones`),``,`CORE BODY + ARMS:`,...landmark.map(name=>{const b=r.perBone.find(x=>x.bone===name);return b?` ${name.replace('mixamorig','').padEnd(19)} motion Δ ${b.motionDeltaRmsDeg.toFixed(2)}° | initial offset ${b.staticPoseOffsetDeg.toFixed(2)}° | travel W/N ${(b.hipFramePositionRange.z.woman/(b.hipFramePositionRange.z.normal||1)).toFixed(2)}×`:` ${name}: unavailable`}),``,`MOST DIFFERENT ARM JOINTS (dynamic, not static):`,...arms.sort((a,b)=>b.motionDeltaRmsDeg-a.motionDeltaRmsDeg).slice(0,8).map(b=>` ${b.bone.replace('mixamorig','')} ${b.motionDeltaRmsDeg.toFixed(2)}° RMS; peak at ${Math.round(b.phaseOfMaxDynamicDifference*100)}%`),``,`METHOD: original GLB, local relative-to-first-aligned-pose SO(3) motion + hip-frame world landmarks. No generated clip. No style-transfer claim.`];
 $('summary').textContent=lines.join('\n');status(`RESEARCH COMPLETE · ${r.perBone.length} original joints measured · local report stored on phone: ${r.persistence||'saving'}`);
}
async function persist(r){try{const response=await fetch('./research-report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(r)});if(!response.ok)throw Error('HTTP_'+response.status);const x=await response.json();if(!x.saved)throw Error('NOT_SAVED');r.persistence=`SAVED ${x.path} (${x.sha256?.slice(0,12)})`;return true}catch(e){r.persistence=`browser export available; phone auto-save unavailable: ${e.message}`;return false}}
async function analyse(){if(!ready)return;status('Measuring source motion, including shoulders, elbows, wrists, hands, torso and head…');
 try{await new Promise(r=>setTimeout(r,0));alignment=alignPhase(samples.Walking,samples.Walking_Woman);
  const result=compareClips(samples.Walking,samples.Walking_Woman,alignment);
  const traits={Walking:sourceGaitTraits(samples.Walking,'Walking'),Walking_Woman:sourceGaitTraits(samples.Walking_Woman,'Walking_Woman')};
  const reportData={schema:'hareworks-forward-style-research-v0.2.3',sourceClipNames:CLIPS,sourceModelSHA256:SHA,modelJoints:74,analysisOnly:true,createdNewAnimation:false,sourceClipsUnchanged:true,ownerApprovedForwardUntouched:true,ownerApprovedBackwardUntouched:true,samplingPhaseCount:N,
   clips:Object.fromEntries(CLIPS.map(k=>[k,{durationSeconds:clips[k].duration,sceneRootDetrendingDisplayOnly:rootTrend[k],originalClipTracks:clips[k].tracks.length}])),gaitTraits:traits,alignment,sourceMeasuredPhaseWindow:'0 <= phase < 0.93 for BOTH clips, aligned by pair of pelvis-relative ankle trajectories; excludes terminal reset',
   caveats:['This compares these two authored animations, not sexes in general','All 74 joints share exactly the same skeleton','A source static offset is not evidence of dynamic movement style','Measured foot phase fit is descriptive, not force-contact evidence','No backward gait is modified by this research','No candidate style transfer is applied'],...result};
  report=reportData;publish(report);await persist(report);publish(report);referenceAt(phase);
 }catch(e){status('SOURCE_ANALYSIS_ERROR '+e.message);console.error(e)}
}
$('analyze').onclick=analyse;$('sort').onchange=()=>{if(report)publish(report)};
$('jsonExport').onclick=()=>report?download(JSON.stringify(report,null,2),'hareworks-walking-vs-walking-woman-74joint-v0.2.3.json','application/json'):status('Research report not ready');
$('csvExport').onclick=()=>report?download(csvEvidence(report),'hareworks-walking-vs-walking-woman-74joint-v0.2.3.csv','text/csv'):status('Research report not ready');
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';};
$('phase').oninput=()=>{playing=false;$('play').textContent='Play';phase=Number($('phase').value)/1000;if(ready)referenceAt(phase)};
$('aligned').onchange=$('inPlace').onchange=()=>{if(ready)referenceAt(phase)};
function render(now){requestAnimationFrame(render);const delta=Math.min(.06,Math.max(0,(now-last)/1000));last=now;if(ready&&playing){phase=mod1(phase+delta/clips.Walking.duration);referenceAt(phase);$('phase').value=Math.round(phase*1000)}orbit.update();renderer.render(scene,camera)}
requestAnimationFrame(render);
try{
 const response=await fetch(URL_GLB,{cache:'no-store'});if(!response.ok)throw Error('SOURCE_GLB_HTTP_'+response.status);
 const raw=await response.arrayBuffer();if(raw.byteLength!==6784896)throw Error('SOURCE_BYTES_'+raw.byteLength);
 if(!crypto?.subtle)throw Error('LOCALHOST_CRYPTO_UNAVAILABLE');const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw))).map(x=>x.toString(16).padStart(2,'0')).join('');if(digest!==SHA)throw Error('SOURCE_SHA256_MISMATCH_'+digest);
 const gltf=await new GLTFLoader().parseAsync(raw,new URL('../../../assets/hareworks/',import.meta.url).href);if(gltf.animations.length!==9)throw Error('SOURCE_NINE_CLIPS_REQUIRED');
 for(const key of CLIPS){const clip=gltf.animations.find(x=>x.name===key);if(!clip)throw Error('SOURCE_CLIP_NOT_FOUND_'+key);clips[key]=clip;models[key]=cloneSkeleton(gltf.scene);scene.add(models[key]);models[key].position.z=key==='Walking'?-SEP/2:SEP/2;rigs[key]=rigOf(models[key]);mixers[key]=new THREE.AnimationMixer(models[key]);mixers[key].clipAction(clip).reset().play();mixers[key].setTime(0);}
 for(const key of CLIPS)samples[key]=capture(key);
 ready=true;playing=true;grid.position.y=Math.min(...CLIPS.map(key=>new THREE.Box3().setFromObject(models[key]).min.y));
 $('identity').textContent=`v0.2.3 · SOURCE ${SHA} · original Walking + Walking_Woman clips · 74/74 bones · ${N} original poses/clip · commit ${new URLSearchParams(location.search).get('commit')||'unavailable'} · launcher SHA ${new URLSearchParams(location.search).get('scriptSha')||'unavailable'}`;
 referenceAt(0);cameraAt('side');resize();status('ORIGINAL SOURCE ANIMATIONS VERIFIED · research in progress');await analyse();
}catch(e){status('SOURCE_OR_RIG_ERROR '+e.message);console.error(e)}
__HAREWORKS_RESEARCH_V023_VIEWER_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/analysis-core.mjs" <<'__HAREWORKS_RESEARCH_V023_ANALYSIS_CORE_MJS__'
/* Hareworks v0.2.3 research mathematics. Pure, source-only measurements.
   No pose creation, style transfer or modification of source clips. */
export const mod1 = x => ((x % 1) + 1) % 1;
const finite3 = v => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite);
const finite4 = v => Array.isArray(v) && v.length === 4 && v.every(Number.isFinite);
export function normalized(q) {
  if (!finite4(q)) throw Error('INVALID_SOURCE_QUATERNION');
  const d=Math.hypot(...q); if(d < 1e-9) throw Error('DEGENERATE_SOURCE_QUATERNION');
  return q.map(x=>x/d);
}
export const conjugate=q=>[-q[0],-q[1],-q[2],q[3]];
export function multiply(a,b){const [x,y,z,w]=a,[X,Y,Z,W]=b;return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]}
export function angleDeg(qa,qb) {const a=normalized(qa),b=normalized(qb);let d=Math.abs(a.reduce((s,x,i)=>s+x*b[i],0));return 2*Math.acos(Math.max(0,Math.min(1,d)))*180/Math.PI;}
export function slerp(qa,qb,t){if(!Number.isFinite(t)||t<0||t>1)throw Error('BAD_INTERPOLATION');const a=normalized(qa);let b=normalized(qb);let dot=a.reduce((s,x,i)=>s+x*b[i],0);if(dot<0){b=b.map(x=>-x);dot=-dot}if(dot>.9995){const q=a.map((v,i)=>v+t*(b[i]-v));return normalized(q)}const th=Math.acos(Math.min(1,dot)),si=Math.sin(th);return normalized(a.map((v,i)=>(Math.sin((1-t)*th)*v+Math.sin(t*th)*b[i])/si))}
export function sample(series,p){const n=series.length;if(!n)throw Error('EMPTY_SAMPLE_ARRAY');if(!Number.isFinite(p))throw Error('NONFINITE_PHASE');const index=mod1(p)*n,i=Math.floor(index)%n,t=index-i,j=(i+1)%n;return {i,j,t}}
export function poseAt(clip,name,p){const rows=clip?.bones?.[name],n=clip?.count;if(!rows||!n||rows.length!==n)throw Error('MISSING_BONE_DATA_'+name);const {i,j,t}=sample(rows,p);const a=rows[i],b=rows[j];const blend=(key)=>a[key].map((x,k)=>x+(b[key][k]-x)*t);
 return {lq:slerp(a.lq,b.lq,t),lp:blend('lp'),wp:blend('wp'),hq:blend('hq'),hp:blend('hp')};}
export function rms(v){if(!v.length)return null;return Math.sqrt(v.reduce((s,x)=>s+x*x,0)/v.length)}
export function range(v){return v.length?Math.max(...v)-Math.min(...v):null}
export function groupBone(name){if(/Hips/.test(name))return 'pelvis';if(/Spine/.test(name))return 'torso';if(/Neck|Head/.test(name))return 'head-and-neck';if(/Shoulder/.test(name))return 'shoulders';if(/ForeArm/.test(name))return 'forearms';if(/UpLeg|Leg/.test(name))return 'legs';if(/Foot|Toe/.test(name))return 'feet';if(/Hand/.test(name)&&/Thumb|Index|Middle|Ring|Pinky/.test(name))return 'fingers';if(/Hand/.test(name))return 'hands';if(/Arm/.test(name))return 'upper-arms';return 'other'}
// One global phase shift is inferred from the two pairs of foot trajectories;
// amplitude and center normalization prevent a smaller stride biasing phase.
function footSignal(clip,foot,axis){const arr=clip.bones[foot].map(r=>r.hp[axis]);const valid=arr.slice(0,Math.floor(arr.length*.94));const mean=valid.reduce((s,v)=>s+v,0)/valid.length;const std=Math.max(0.015,rms(valid.map(v=>v-mean)));return {name:foot,axis,mean,std};}
export function alignPhase(normal,woman){
 const foot=['mixamorigLeftFoot','mixamorigRightFoot'];for(const f of foot)if(!normal.bones[f]||!woman.bones[f])throw Error('FOOT_ALIGNMENT_SOURCE_MISSING_'+f);
 const specs=[];for(const name of foot)for(const axis of [0,2])specs.push({a:footSignal(normal,name,axis),b:footSignal(woman,name,axis)});
 const candidates=[];
 for(let shiftIndex=0;shiftIndex<180;shiftIndex++){
  const shift=shiftIndex/180;let sum=0,n=0;
  for(let i=0;i<180;i++){
   const p=i/180,q=mod1(p+shift);if(p>=.93||q>=.93)continue;
   for(const {a,b} of specs){const nVal=(poseAt(normal,a.name,p).hp[a.axis]-a.mean)/a.std;const wVal=(poseAt(woman,b.name,q).hp[b.axis]-b.mean)/b.std;sum+=(nVal-wVal)**2;n++}
  }
  if(n>=250)candidates.push({shift,cost:sum/n,pairs:n});
 }
 if(!candidates.length)throw Error('NO_VALID_PHASE_ALIGNMENT');candidates.sort((a,b)=>a.cost-b.cost);
 const best=candidates[0],alternative=candidates.find(x=>Math.min(mod1(x.shift-best.shift),mod1(best.shift-x.shift))>.09)||candidates[1];
 return {womanPhaseOffset:best.shift,normalPhaseOffset:0,method:'global offset minimizing normalized hip-relative left/right foot X/Z trajectory differences',cost:best.cost,samplePairs:best.pairs,distinctAlternativeCost:alternative?.cost??null,ambiguityRatio:alternative?alternative.cost/best.cost:null,sourceTerminalWindowExcluded:[.93,1]};
}
export function compareClips(normal,woman,align){if(normal.count!==woman.count||normal.boneNames.length!==74||woman.boneNames.length!==74)throw Error('SOURCE_RIG_RESEARCH_CONTRACT');
 const bones=normal.boneNames;for(const name of bones)if(!woman.bones[name])throw Error('SOURCE_BONE_TOPOLOGY_MISMATCH_'+name);
 const phases=[];for(let i=0;i<240;i++){const p=i/240,q=mod1(p+align.womanPhaseOffset);if(p<.93&&q<.93)phases.push({p,q})}if(phases.length<150)throw Error('INSUFFICIENT_ALIGNED_SOURCE_PHASES');
 const out=[];
 for(const name of bones){
  const p0=phases[0],n0=poseAt(normal,name,p0.p),w0=poseAt(woman,name,p0.q);
  const raw=[],dynamic=[],displacementN=[],displacementW=[],relativePositionDelta=[],translationalDelta=[];
  let peakAt=0,maxDynamic=0;const trajectories={normal:{},woman:{}};
  for(const axis of ['x','y','z']){trajectories.normal[axis]=[];trajectories.woman[axis]=[]}
  for(const {p,q} of phases){const a=poseAt(normal,name,p),b=poseAt(woman,name,q);
   const staticRemovedN=multiply(conjugate(normalized(n0.lq)),normalized(a.lq)),staticRemovedW=multiply(conjugate(normalized(w0.lq)),normalized(b.lq));
   const da=angleDeg(staticRemovedN,staticRemovedW);dynamic.push(da);if(da>maxDynamic){maxDynamic=da;peakAt=p}
   raw.push(angleDeg(a.lq,b.lq));displacementN.push(angleDeg(n0.lq,a.lq));displacementW.push(angleDeg(w0.lq,b.lq));
   relativePositionDelta.push(Math.hypot(...a.hp.map((x,i)=>x-b.hp[i])));
   translationalDelta.push(Math.hypot(...a.lp.map((x,i)=>(x-n0.lp[i])-(b.lp[i]-w0.lp[i]))));
   for(let i=0;i<3;i++){trajectories.normal['xyz'[i]].push(a.hp[i]);trajectories.woman['xyz'[i]].push(b.hp[i])}
  }
  const frameRanges={};for(const a of ['x','y','z'])frameRanges[a]={normal:range(trajectories.normal[a]),woman:range(trajectories.woman[a]),difference:range(trajectories.woman[a])-range(trajectories.normal[a])};
  const result={bone:name,group:groupBone(name),sampledAlignedPhases:phases.length,staticPoseOffsetDeg:angleDeg(n0.lq,w0.lq),meanRawPoseDifferenceDeg:raw.reduce((s,x)=>s+x,0)/raw.length,
   motionDeltaRmsDeg:rms(dynamic),motionDeltaMaxDeg:maxDynamic,phaseOfMaxDynamicDifference:peakAt,
   normalMotionFromAnchorRmsDeg:rms(displacementN),womanMotionFromAnchorRmsDeg:rms(displacementW),motionFromAnchorRmsRatio:rms(displacementN)>1e-3?rms(displacementW)/rms(displacementN):null,
   hipRelativePositionDifferenceRmsUnits:rms(relativePositionDelta),localTranslationMotionDeltaRmsUnits:rms(translationalDelta),hipFramePositionRange:frameRanges};
  out.push(result)
 }
 out.sort((a,b)=>b.motionDeltaRmsDeg-a.motionDeltaRmsDeg);
 const groups={};for(const bone of out){let g=groups[bone.group]??={boneCount:0,motionDeltaRmsValues:[],staticPoseOffsets:[]};g.boneCount++;g.motionDeltaRmsValues.push(bone.motionDeltaRmsDeg);g.staticPoseOffsets.push(bone.staticPoseOffsetDeg)}
 for(const g of Object.values(groups)){g.meanBoneMotionDeltaRmsDeg=g.motionDeltaRmsValues.reduce((s,v)=>s+v,0)/g.boneCount;g.meanBoneStaticPoseOffsetDeg=g.staticPoseOffsets.reduce((s,v)=>s+v,0)/g.boneCount;delete g.motionDeltaRmsValues;delete g.staticPoseOffsets}
 return {sampledMatchedPhases:phases.length,perBone:out,groups};
}
__HAREWORKS_RESEARCH_V023_ANALYSIS_CORE_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/analysis-core-test.mjs" <<'__HAREWORKS_RESEARCH_V023_ANALYSIS_CORE_TEST_MJS__'
import assert from 'node:assert/strict';
import {angleDeg,slerp,alignPhase,compareClips,groupBone,mod1} from './analysis-core.mjs';
const q=z=>[0,0,Math.sin(z/2),Math.cos(z/2)];
assert.ok(angleDeg(q(0),q(Math.PI/2))>89.999);
assert.ok(angleDeg(q(0),q(0))<1e-5);
assert.ok(angleDeg(q(0),q(2*Math.PI))<1e-5);
assert.ok(angleDeg(slerp(q(0),q(Math.PI),.5),q(Math.PI/2))<1e-4);
assert.equal(groupBone('mixamorigLeftForeArm'),'forearms');
assert.equal(groupBone('mixamorigRightHandIndex1'),'fingers');
const n=240, names=['mixamorigLeftFoot','mixamorigRightFoot','mixamorigHips','mixamorigHead',...Array.from({length:70},(_,i)=>`Extra_${i}`)];
function fixture(phaseShift=0,armBias=0){const bones={};for(const name of names){bones[name]=[];for(let i=0;i<n;i++){
 const p=mod1(i/n-phaseShift),sgn=name.includes('Left')?1:name.includes('Right')?-1:0;
 const gait=2*Math.PI*p,x=.11*sgn*Math.sin(gait),z=.23*Math.sin(gait+sgn*.5);
 bones[name].push({lq:q((name==='mixamorigHead'?armBias:0)+.12*Math.sin(gait+sgn)),lp:[0,0,0],wp:[x,.9,z],hq:[0,0,0,1],hp:[x,.2+.01*Math.cos(gait),z]});
 }}return {count:n,boneNames:names,bones}}
const a=fixture(),b=fixture(.21,.1),d=alignPhase(a,b);assert.ok(Math.abs(d.womanPhaseOffset-.21)<.02,`phase alignment: ${d.womanPhaseOffset}`);
const report=compareClips(a,b,d);assert.equal(report.perBone.length,74);assert.ok(report.sampledMatchedPhases>150);
const head=report.perBone.find(x=>x.bone==='mixamorigHead');assert.ok(head.staticPoseOffsetDeg>5&&head.staticPoseOffsetDeg<7);assert.ok(head.motionDeltaRmsDeg<.6,`false dynamic difference ${head.motionDeltaRmsDeg}`);
const changed=fixture(.21,.1);changed.bones.mixamorigHead.forEach((x,i)=>x.lq=q(.1+.23*Math.sin(2*Math.PI*mod1(i/n-.21))));
const styled=compareClips(a,changed,d).perBone.find(x=>x.bone==='mixamorigHead');assert.ok(styled.motionDeltaRmsDeg>2,'animated delta must be detected');
assert.throws(()=>compareClips(a,{...b,boneNames:['bad']},d),/SOURCE_RIG_RESEARCH_CONTRACT/);
console.log('HAREWORKS_STYLE_RESEARCH_CORE_PASS: phase alignment, baseline-pose isolation, dynamic shoulder/hand-style detection, full 74-bone metrics, negative fixture');
__HAREWORKS_RESEARCH_V023_ANALYSIS_CORE_TEST_MJS__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/research-server.py" <<'__HAREWORKS_RESEARCH_V023_RESEARCH_SERVER_PY__'
"""Phone-local no-cache research viewer and evidence receiver. No remote services."""
import csv
import datetime
import hashlib
import http.server
import io
import json
import os
import pathlib
import sys
import tempfile
import urllib.parse

MODEL_SHA = 'a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
SCRIPT_PATH = '/tools/hareworks-forward-woman/v0.2.3/research-report'
CSV_FIELDS = ['bone', 'group', 'sampledAlignedPhases', 'staticPoseOffsetDeg',
              'meanRawPoseDifferenceDeg', 'motionDeltaRmsDeg', 'motionDeltaMaxDeg',
              'phaseOfMaxDynamicDifference', 'normalMotionFromAnchorRmsDeg',
              'womanMotionFromAnchorRmsDeg', 'motionFromAnchorRmsRatio',
              'hipRelativePositionDifferenceRmsUnits', 'localTranslationMotionDeltaRmsUnits']


def validate_report(obj):
    assert isinstance(obj, dict)
    assert obj.get('schema') == 'hareworks-forward-style-research-v0.2.3'
    assert obj.get('sourceModelSHA256') == MODEL_SHA
    assert obj.get('sourceClipNames') == ['Walking', 'Walking_Woman']
    assert obj.get('analysisOnly') is True and obj.get('createdNewAnimation') is False
    assert obj.get('modelJoints') == 74
    assert obj.get('sourceClipsUnchanged') is True
    assert obj.get('ownerApprovedForwardUntouched') is True
    assert obj.get('ownerApprovedBackwardUntouched') is True
    assert obj.get('sampledMatchedPhases', 0) >= 150
    assert len(obj.get('perBone', [])) == 74
    assert len(set(x.get('bone') for x in obj['perBone'])) == 74
    for entry in obj['perBone']:
        assert isinstance(entry.get('bone'), str) and 1 <= len(entry['bone']) <= 128
        assert 0 <= float(entry['motionDeltaRmsDeg']) <= 360
        assert 0 <= float(entry['motionDeltaMaxDeg']) <= 360
        assert 0 <= float(entry['staticPoseOffsetDeg']) <= 360
    return obj


def write_atomic(path, data):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.tmp-v023-', delete=False) as f:
        temporary = pathlib.Path(f.name)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


def store_report(raw, state):
    if len(raw) > 3_000_000:
        raise ValueError('OVERSIZED_REPORT')
    report = validate_report(json.loads(raw))
    payload = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False).encode('utf-8') + b'\n'
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(report['perBone'])
    write_atomic(pathlib.Path(state) / 'research-report.json', payload)
    write_atomic(pathlib.Path(state) / 'research-report.csv', buffer.getvalue().encode())
    digest = hashlib.sha256(payload).hexdigest()
    receipt = {
        'campaign': 'hareworks-walking-style-research-v0.2.3',
        'status': 'REAL_BROWSER_74_BONE_SOURCE_RESEARCH_SAVED',
        'sourceModelSha256': MODEL_SHA,
        'sources': ['Walking', 'Walking_Woman'],
        'sourceBones': 74,
        'pairsMeasured': report['sampledMatchedPhases'],
        'reportPath': str(pathlib.Path(state) / 'research-report.json'),
        'csvPath': str(pathlib.Path(state) / 'research-report.csv'),
        'reportSha256': digest,
        'receivedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'sourceClipsModified': False,
        'ownerAcceptedForwardAndBackwardPreserved': True,
        'newAnimationCreated': False,
    }
    write_atomic(pathlib.Path(state) / 'measurement-receipt.json',
                 (json.dumps(receipt, indent=2) + '\n').encode())
    return {'saved': True, 'sha256': digest, 'path': receipt['reportPath'],
            'csvPath': receipt['csvPath']}


def make_handler(root, state, ready):
    class Handler(http.server.SimpleHTTPRequestHandler):
        extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                          '.mjs': 'text/javascript', '.js': 'text/javascript',
                          '.glb': 'model/gltf-binary', '.json': 'application/json'}

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root, **kwargs)

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store, no-cache, max-age=0, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('X-Content-Type-Options', 'nosniff')
            super().end_headers()

        def do_POST(self):
            path = urllib.parse.urlsplit(self.path).path
            if path != SCRIPT_PATH:
                self.send_error(404, 'Unknown research endpoint')
                return
            origin = self.headers.get('Origin', '')
            expected = 'http://127.0.0.1:' + str(self.server.server_address[1])
            if origin and origin != expected:
                self.send_error(403, 'Origin not authorized')
                return
            try:
                n = int(self.headers.get('Content-Length', '0'))
                if not 0 < n <= 3_000_000:
                    self.send_error(413, 'Bad evidence size')
                    return
                result = store_report(self.rfile.read(n), state)
                data = json.dumps(result).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (ValueError, AssertionError, KeyError, TypeError) as ex:
                self.send_error(422, 'Invalid source research payload: ' + str(ex)[:120])

    return Handler


def main():
    root, state, ready = sys.argv[1:]
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), make_handler(root, state, ready))
    write_atomic(ready, json.dumps({'pid': os.getpid(),
                                    'port': server.server_address[1],
                                    'root': root}).encode())
    server.serve_forever()


if __name__ == '__main__':
    main()
__HAREWORKS_RESEARCH_V023_RESEARCH_SERVER_PY__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/README.md" <<'__HAREWORKS_RESEARCH_V023_README_MD__'
# Hareworks v0.2.3: `Walking` versus `Walking_Woman` research

Research mission: determine, with actual source-GLB measurements, which **time-varying motion traits** distinguish two authored forward gait clips. This is not a backward gait, a style-transfer implementation or a claim about sexes generally. Preserve the owner-approved generated forward gait (`tools/hareworks-forward-woman/v0.1.9`) and owner-accepted generated backward in-place gait (`v0.2.2`) byte-for-byte.

## Primary source and evidence

The exact Git LFS model is `assets/hareworks/Hareworks-nine-clips.glb`, SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`, 6,784,896 bytes, nine source animation clips, same 74-bone skeleton. The browser verifies the **whole downloaded GLB's SHA**, instantiates two independent original source-clip mixers, samples **360 reference poses per clip**, and does not generate or play any candidate motion. The scripts, existing assets and historical proofs are immutable.

- Compare cycles at **phase-aligned** times: search a measured global phase offset that best aligns the two left/right foot paths relative to the pelvis; explain that this is kinematic alignment and not proof of force contact. Exclude the last 7% of both cycles where source/root reset artifacts can corrupt measurements. Record duration separately.
- For every single bone, report static initial pose difference, raw pose difference and **dynamic motion difference** after subtracting the two initial orientations independently. RMS/max and phase of maximum error are included. A different starting pose does not constitute a dynamic difference.
- Capture full three-dimensional hip-relative head, shoulders, forearms, hands, fingers and feet displacement in the **pelvis coordinate frame**, where model root travel and pelvis orientation are normalized out. Report motion amplitude/range for X/Y/Z and ratios. Distinguish local rotational style and world trajectory shape.
- Group per-joint findings by pelvis, torso, head/neck, shoulders, upper arms, forearms, hands, fingers, legs and feet. Preserve actual left/right asymmetries rather than manufacture symmetry.
- Original source `Walking` and `Walking_Woman` play side by side, orbit and scrub independently through synchronized normalized phases. Optional display-only root-trend subtraction does not affect source measurements. Controls include raw-phase vs measured phase alignment, JSON/CSV downloads, and sortable per-joint table.
- On successful runtime browser analysis, the local phone server **automatically saves** `research-report.json`, `research-report.csv` and `measurement-receipt.json` beneath the campaign's persistent state path. A successful packet, Git push or HTTP GET is **not** evidence of real browser analysis. Export buttons remain available if POST is blocked.

## Limits

The report describes these two source clips, not innate male or female gait. Foot event synchronization is an approximation based on observed kinematics, not a contact-force sensor. It is not evidence that copying delta quaternions onto `Walk_Backward` will produce attractive or physically sound movement. No outputs are applied to any generated motion. No automatic changes to locomotion. Any future transfer requires a separate owner-authorized, visually reviewed campaign.

## Execution

One SHA-verified Android Termux `.sh` in the authoritative `Valar05/parametric-parambulator` Git lane. Fresh, rules-verified isolated checkout, source-GLB binary verification, collision gate, pure math tests with altered-motion and no-motion negative control, HTML/JS/import/hash checks, scoped commit/push, remote readback and a unique localhost no-cache server. Source revision and entry script hash are visible in the viewer; the complete URL is emitted by the actual phone execution, not guessed.

The terminal receipt records `Git published / HTTP ready / browser research pending`. Only a validated, source-backed POST updates the separate measurement receipt. The owner's existing visual acceptance for the forward and backward motions remains in force; this research has no motion-acceptance outcome.
__HAREWORKS_RESEARCH_V023_README_MD__
fi
if ((PUBLISHED==0));then
 cat > "$DIR/contract.json" <<'__HAREWORKS_RESEARCH_V023_CONTRACT_JSON__'
{
  "campaign": "hareworks-walking-style-research-v0.2.3",
  "repository": "Valar05/parametric-parambulator",
  "parentCommit": "3e298e9c9d99c6cb372bc5c8b2f9c8cb77d46ab6",
  "sourceModel": "assets/hareworks/Hareworks-nine-clips.glb",
  "sourceSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "sourceModelBytes": 6784896,
  "sourceClips": ["Walking", "Walking_Woman"],
  "sourceBoneCount": 74,
  "sourcePoseSamplesPerClip": 360,
  "phaseAlignment": "measured global phase offset using hip-frame left and right feet, no force-contact claim",
  "terminalResetPolicy": "exclude last seven percent of each clip in matched-source research",
  "measurements": ["initial local rotation offset", "dynamic local orientation difference after source-specific zero anchoring", "source body motion amplitudes", "pelvis-frame 3D landmark paths", "all 74 bone metrics", "regional aggregation", "phase of peak motion difference"],
  "output": ["browser summary", "JSON", "CSV", "automatic Termux research-report.json and research-report.csv", "measurement-receipt.json"],
  "motionMutation": false,
  "generatedAnimation": false,
  "preserveAcceptedForward": "tools/hareworks-forward-woman/v0.1.9 unchanged",
  "preserveAcceptedBackward": "tools/hareworks-forward-woman/v0.2.2 unchanged",
  "ownerAcceptance": "already accepted forward v0.1.9 and backward v0.2.2; research only",
  "executionLane": "Android Termux Git ONLY",
  "rules": {"AGENTS.mdBlob": "547c2af52303f4efb718bbf8f82a698110c7bfca", "campaignEtiquetteHomeCenterId": "1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI", "topDownEtiquetteHomeCenterId": "1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU"}
}
__HAREWORKS_RESEARCH_V023_CONTRACT_JSON__
fi
if ((PUBLISHED==0));then
 cp -- "$0" "campaigns/$CAMPAIGN.sh" || fail 'cannot install exact executed source as Git packet'
fi
phase=embedded-integrity
[[ "$(hash "$DIR/index.html")" == "9ed5581f75aaeadb9271439531cf6d0c835388466ce4d4110dcc4dc90a059d8d" ]] || fail 'embedded byte mismatch: index.html'
[[ "$(hash "$DIR/viewer.mjs")" == "98de8cc75e23e120b20dac06f61d980047329c6c51844a893de72cf73b06561b" ]] || fail 'embedded byte mismatch: viewer.mjs'
[[ "$(hash "$DIR/analysis-core.mjs")" == "0d1dca4c67e711dbf801291f60758a05a76667a0e30920317eb3ad08c0f1d32a" ]] || fail 'embedded byte mismatch: analysis-core.mjs'
[[ "$(hash "$DIR/analysis-core-test.mjs")" == "6595ab65217549521ab8672f7f34c91e2ca680a4dee8a8c3f5bffe6cc81a330f" ]] || fail 'embedded byte mismatch: analysis-core-test.mjs'
[[ "$(hash "$DIR/research-server.py")" == "001cf40320e61c0cb032ec28a0c23eb668887003cfc3c5d9d73d34cc48ef4c44" ]] || fail 'embedded byte mismatch: research-server.py'
[[ "$(hash "$DIR/README.md")" == "299649993f9019e0fd2cb0192001f5e065c14bd125c6a22805f6ff141b44e2b5" ]] || fail 'embedded byte mismatch: README.md'
[[ "$(hash "$DIR/contract.json")" == "8dec77b5cea86cad8e09128a3f9377a5a3905e0cf6f096a6d564d9e0843454c8" ]] || fail 'embedded byte mismatch: contract.json'
[[ "$(hash "campaigns/$CAMPAIGN.sh")" == "$SELF_SHA" ]] || fail 'Git campaign differs from attached executed bytes'
phase=host-validation
for js in "$DIR/viewer.mjs" "$DIR/analysis-core.mjs" "$DIR/analysis-core-test.mjs";do node --check "$js" || fail "JS syntax failed: $js";done
node "$DIR/analysis-core-test.mjs" | tee "$STATE/source-style-unit-tests.log" || fail 'source-style mathematical controls failed'
python3 -m py_compile "$DIR/research-server.py" || fail 'evidence receiver Python syntax failed'
python3 - "$DIR" "$MODEL" "$MODEL_SHA" <<'PY_DEPENDENCIES' || fail 'source-only imports and output contracts invalid'
import pathlib,re,json,sys
p=pathlib.Path(sys.argv[1]);model=pathlib.Path(sys.argv[2]);sha=sys.argv[3]
js=(p/'viewer.mjs').read_text();html=(p/'index.html').read_text();contract=json.loads((p/'contract.json').read_text())
assert contract['sourceSha256']==sha and contract['sourceClips']==['Walking','Walking_Woman']
assert 'analysisOnly' in js and 'createdNewAnimation:false' in js
assert 'compareClips(' in js and 'alignPhase(' in js and 'referenceAt(' in js
assert 'id="jsonExport"' in html and 'id="csvExport"' in html and 'id="rows"' in html
assert 'src="./viewer.mjs"' in html
for x in re.findall(r"from\s+[\x27\x22](\.[^\x27\x22]+)[\x27\x22]",js):
 assert (p/x).resolve(strict=True).is_file(),('missing module',x)
assert model.exists()
print('BROWSER_MODULE_AND_SOURCE_RESEARCH_CONTRACT=PASS')
PY_DEPENDENCIES
python3 - "$DIR" "$STATE" <<'PY_SERVER_TEST' || fail 'evidence receiver success and rejection path failed'
import importlib.util,sys,tempfile,pathlib,json
name=sys.argv[1]+'/research-server.py'
spec=importlib.util.spec_from_file_location('hareworks_v023_research_server',name)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 q={'schema':'hareworks-forward-style-research-v0.2.3','sourceModelSHA256':m.MODEL_SHA,'sourceClipNames':['Walking','Walking_Woman'],'analysisOnly':True,'createdNewAnimation':False,'modelJoints':74,'sourceClipsUnchanged':True,'ownerApprovedForwardUntouched':True,'ownerApprovedBackwardUntouched':True,'sampledMatchedPhases':190,
  'perBone':[{'bone':f'SyntheticBone_{i}', 'motionDeltaRmsDeg':i/10, 'motionDeltaMaxDeg':i/10+1,'staticPoseOffsetDeg':2} for i in range(74)]}
 raw=json.dumps(q).encode();r=m.store_report(raw,d)
 assert r['saved'] and (pathlib.Path(d)/'research-report.json').exists() and (pathlib.Path(d)/'research-report.csv').exists()
 bad=dict(q);bad['sourceModelSHA256']='bad'
 try:m.store_report(json.dumps(bad).encode(),d)
 except AssertionError:pass
 else:raise AssertionError('wrong model accepted')
 bad=dict(q);bad['perBone']=q['perBone'][:-1]
 try:m.store_report(json.dumps(bad).encode(),d)
 except AssertionError:pass
 else:raise AssertionError('incomplete rig accepted')
 print('PHONE_EVIDENCE_RECEIVER=PASS: writes JSON/CSV/receipt, rejects fake model/incomplete rig')
PY_SERVER_TEST
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
assert len(actual)==8
print('STAGED_ONLY_EIGHT_NEW_RESEARCH_TEXT_FILES=PASS')
PY_STAGE
 for p in AGENTS.md "$MODEL" tools/hareworks-forward-woman/v0.1.9/viewer.mjs tools/hareworks-forward-woman/v0.2.2/viewer.mjs;do
  git diff --quiet -- "$p" || fail "protected source worktree modified: $p"
  [[ "$(git rev-parse "HEAD:$p")" == "$(git rev-parse "$BASE:$p")" ]] || fail "protected prior revision changed: $p"
 done
 phase=commit
 git -c user.name='Hareworks Research Termux Campaign' -c user.email='hareworks-research@users.noreply.github.com' commit -m 'Research source Walking vs Walking_Woman across all 74 Hareworks bones v0.2.3' || fail 'scoped Git commit failed'
 COMMIT=$(git rev-parse HEAD)
 [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'commit parent unexpected'
 phase=publish
 [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote advanced, refusing force-push'
 GIT_LFS_SKIP_PUSH=1 git push origin HEAD:refs/heads/main || fail "push failed; isolated commit remains $COMMIT"
else COMMIT="$REMOTE";fi
phase=remote-readback
[[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$COMMIT" ]] || fail 'remote main does not match research commit'
GIT_LFS_SKIP_SMUDGE=1 git fetch --depth=2 origin main || fail 'readback fetch failed'
[[ "$(git rev-parse FETCH_HEAD)" == "$COMMIT" ]] || fail 'fetched main is not committed research packet'
for p in "${FILES[@]}";do
 [[ "$(git rev-parse "FETCH_HEAD:$p")" == "$(git rev-parse "HEAD:$p")" ]] || fail "remote file byte identity differs: $p"
done
for p in AGENTS.md "$MODEL" tools/hareworks-forward-woman/v0.1.9/viewer.mjs tools/hareworks-forward-woman/v0.2.2/viewer.mjs;do
 [[ "$(git rev-parse "FETCH_HEAD:$p")" == "$(git rev-parse "$BASE:$p")" ]] || fail "approved source changed on remote: $p"
done
echo "EXACT_REMOTE_READBACK=PASS $COMMIT"
phase=phone-source-research-viewer
cp -- "$SOURCE" "$MODEL" || fail 'cannot materialize original GLB into disposable HTTP snapshot'
[[ "$(hash "$MODEL")" == "$MODEL_SHA" ]] || fail 'HTTP model snapshot SHA mismatch'
READY="$ROOT/research-server-ready.json"
nohup python3 "$DIR/research-server.py" "$WORK" "$STATE" "$READY" > "$ROOT/server.log" 2>&1 </dev/null &
PID=$!
for t in 1 2 3 4 5 6 7 8 9 10;do
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
[[ "$PORT" =~ ^[0-9]+$ ]] && kill -0 "$PID" 2>/dev/null || fail 'fresh research HTTP server failed'
python3 - "http://127.0.0.1:$PORT" "$DIR" "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" "$STATE/http-manifest.json" <<'PY_HTTP' || fail 'HTTP required research resources / original GLB failed'
import hashlib,json,pathlib,re,sys,urllib.parse,urllib.request
origin,dir,model,sha,size,out=sys.argv[1:]
def get(url):
 with urllib.request.urlopen(url,timeout=40) as r:
  assert 'no-store' in r.headers.get('Cache-Control',''),('cache control',url)
  return r.read()
root=origin+'/'+dir+'/'
viewer=get(root+'viewer.mjs').decode();html=get(root+'index.html').decode()
assert 'Walking_Woman' in viewer and 'Walking' in viewer
assert 'id="analyze"' in html and 'id="jsonExport"' in html
urls=[root+x for x in ['index.html','viewer.mjs','analysis-core.mjs','analysis-core-test.mjs','README.md','contract.json']]
urls += [urllib.parse.urljoin(root+'viewer.mjs',x) for x in re.findall(r"from\s+[\x27\x22](\.[^\x27\x22]+)[\x27\x22]",viewer)]
for url in sorted(set(urls)): assert get(url),('source research HTTP asset missing',url)
blob=get(origin+'/'+model)
assert len(blob)==int(size) and hashlib.sha256(blob).hexdigest()==sha
record={'status':'HTTP_SOURCE_FILES_AND_CANONICAL_BINARY_VERIFIED_BROWSER_MEASUREMENTS_PENDING','sourceClips':['Walking','Walking_Woman'],'modelSha256':sha,'modelBytes':len(blob),'resources':sorted(set(urls)),'researchResult':'NOT_YET_MEASURED_IN_BROWSER'}
pathlib.Path(out).write_text(json.dumps(record,indent=2))
print('SOURCE_RESEARCH_HTTP_CANONICAL_GLB_AND_MODULES_PASS',len(set(urls)),'requests')
PY_HTTP
curl -fsSI --max-time 5 "http://127.0.0.1:$PORT/$DIR/index.html" > "$STATE/http-headers.txt" || fail 'viewer HTTP headers missing'
URL="http://127.0.0.1:$PORT/$DIR/index.html?commit=$COMMIT&scriptSha=$SELF_SHA&modelSha=$MODEL_SHA"
python3 - "$STATE/receipt.json" "$CAMPAIGN" "$BASE" "$COMMIT" "$SELF_SHA" "$MODEL_SHA" "$AGENTS_BLOB" "$URL" "$PID" "$PORT" "$ROOT" <<'PY_RECEIPT'
import datetime,json,pathlib,sys
path,campaign,parent,commit,entry,model,agents,url,pid,port,snapshot=sys.argv[1:]
r={'campaign':campaign,'status':'GIT_PUBLISHED_READBACK_HTTP_VERIFIED_BROWSER_MEASUREMENT_PENDING',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'auditedParent':parent,'publishedCommit':commit,
 'entrypointSHA256':entry,'sourceModelSHA256':model,'rootAgentsGitBlob':agents,
 'liveRules':{'AGENTS.md':'pinned Git blob verified','Campaign Etiquette':'Home Center 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI','Top-down Etiquette':'Home Center 1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'},
 'sourceClips':['Walking','Walking_Woman'],'sourceBones':74,'generatedMotion':False,
 'approvedForwardChanged':False,'approvedBackwardChanged':False,'originalGlbChanged':False,
 'browserResearchCompleted':False,'viewerURL':url,'viewerPID':int(pid),'viewerPort':int(port),
 'persistentReportJsonPath':str(pathlib.Path(path).parent/'research-report.json'),
 'persistentReportCsvPath':str(pathlib.Path(path).parent/'research-report.csv'),
 'browserMeasurementReceiptPath':str(pathlib.Path(path).parent/'measurement-receipt.json'),
 'isolatedSnapshot':snapshot,'executionLane':'Android Termux Git only',
 'ownerAcceptedMotionPreserved':True,'researchOnly':True}
pathlib.Path(path).write_text(json.dumps(r,indent=2)+'\n')
PY_RECEIPT
echo "REMOTE_COMMIT=$COMMIT"
echo "MODEL_SHA256=$MODEL_SHA"
echo 'SOURCE_CLIPS=Walking,Walking_Woman'
echo 'RESEARCH_JOINTS=74'
echo "VIEWER_URL=$URL"
echo "VIEWER_PORT=$PORT VIEWER_PID=$PID"
echo "RECEIPT=$STATE/receipt.json"
echo "RESEARCH_JSON_AFTER_BROWSER=$STATE/research-report.json"
echo "RESEARCH_CSV_AFTER_BROWSER=$STATE/research-report.csv"
echo "MEASUREMENT_RECEIPT_AFTER_BROWSER=$STATE/measurement-receipt.json"
echo 'SOURCE_RESEARCH_PENDING_BROWSER_AUTOSAVE; OWNER_GAITS_UNMODIFIED=YES'
if command -v termux-open-url >/dev/null;then
 termux-open-url "$URL" || echo "PHONE_BROWSER_OPEN_FAILED; open VIEWER_URL=$URL"
else echo "TERMUX_OPEN_URL_MISSING; open VIEWER_URL=$URL";fi
