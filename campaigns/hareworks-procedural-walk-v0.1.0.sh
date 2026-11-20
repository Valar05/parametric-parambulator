#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_PROCEDURAL_WALK_v0.1.0 | Android Termux Git-only publication + HTTP review
# Safely generates TEXT files only; never changes existing GLBs or 2D assets.
set -Eeuo pipefail
CAMPAIGN=hareworks-procedural-walk-v0.1.0
REPO=Valar05/parametric-parambulator
BASE=31d8799d8cc4d4be449615cc6d5771d87c792a07
MODEL=assets/hareworks/Hareworks-nine-clips.glb
MODEL_SHA=a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6
MODEL_BYTES=6784896
AGENTS_BLOB=547c2af52303f4efb718bbf8f82a698110c7bfca
DIR=tools/hareworks-procedural-walk/v0.1.0
SCRIPT=campaigns/hareworks-procedural-walk-v0.1.0.sh
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
ROOT="$STATE/work"
RECEIPT="$STATE/receipt.json"
mkdir -p "$STATE"
LOG="$STATE/run.log"
exec > >(tee -a "$LOG") 2>&1
phase=preflight
fail(){
  printf 'BLOCKED step=%s reason=%s\n' "$phase" "$*"
  python3 - "$STATE/blocked.json" "$CAMPAIGN" "$phase" "$*" "$BASE" <<'PYFAIL' 2>/dev/null || true
import datetime,json,pathlib,sys
out,project,phase,reason,base=sys.argv[1:]
pathlib.Path(out).write_text(json.dumps({'campaign':project,'status':'blocked','phase':phase,'reason':reason,'base':base,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PYFAIL
  exit 1
}
sha(){ sha256sum -- "$1" | cut -d' ' -f1; }
OP="${1:-run}"
case "$OP" in run|doctor|resume|status) ;; *) echo 'Usage: bash campaign.sh [run|doctor|resume|status]';exit 2;; esac
for utility in git python3 curl sha256sum;do command -v "$utility" >/dev/null || fail "missing required $utility";done
if [[ "$OP" == status ]];then
  if [[ -f "$RECEIPT" ]];then cat "$RECEIPT";else echo 'NO_PUBLISHED_RECEIPT';fi
  if [[ -f "$STATE/server-ready.json" ]];then
    PORT=$(python3 - "$STATE/server-ready.json" <<'PY'
import json,sys
print(json.load(open(sys.argv[1]))['port'])
PY
)
    if curl -fsS --max-time 3 "http://127.0.0.1:$PORT/$DIR/index.html" >/dev/null 2>&1;then echo "VIEWER_HTTP=ONLINE port=$PORT";else echo 'VIEWER_HTTP=OFFLINE';fi
  fi
  exit 0
fi
SELF_SHA=$(sha "$0")
REMOTE=$(git ls-remote "https://github.com/$REPO.git" refs/heads/main | cut -f1) || fail 'cannot read remote main'
[[ -n "$REMOTE" ]] || fail 'remote main unavailable'
echo "REMOTE_MAIN=$REMOTE SCRIPT_SHA256=$SELF_SHA"
# Find the exact owner-provided source; no need to reclone, rescan unrelated LFS, or change model.
phase=source
SOURCE=''
for p in \
 "$HOME/.local/state/hareworks/hareworks-gait-extraction-v1.0.9/work/$MODEL" \
 "$HOME/.local/state/hareworks/hareworks-gait-extraction-v1.0.8/work/$MODEL" \
 "$HOME/.local/state/hareworks/hareworks-viewer-recovery-v1.0.11/verified-nine-clips.glb";do
  [[ -f "$p" ]] || continue
  [[ "$(wc -c < "$p" | tr -d ' ')" == "$MODEL_BYTES" ]] || continue
  if [[ "$(sha "$p")" == "$MODEL_SHA" ]];then SOURCE="$p";break;fi
done
if [[ -z "$SOURCE" ]];then
  SEARCH=()
  for d in "$HOME/storage/downloads" /storage/emulated/0/Download /sdcard/Download;do
    [[ -d "$d" ]] || continue
    real=$(cd -P -- "$d" 2>/dev/null && pwd) || continue
    case " ${SEARCH[*]-} " in *" $real "*) ;; *) SEARCH+=("$real");; esac
  done
  for d in "${SEARCH[@]-}";do
    [[ -n "$d" ]] || continue
    while IFS= read -r -d '' p;do
      [[ "$(wc -c < "$p" | tr -d ' ')" == "$MODEL_BYTES" ]] || continue
      if [[ "$(sha "$p")" == "$MODEL_SHA" ]];then SOURCE="$p";break;fi
    done < <(find -L "$d" -maxdepth 1 -type f -iname '*.glb' -print0 2>/dev/null)
    [[ -z "$SOURCE" ]] || break
  done
fi
# If the original is absent after a phone reset, make exactly one remote object fetch.
if [[ -z "$SOURCE" ]];then
  echo 'LOCAL_MODEL_NOT_FOUND=YES; attempting exact LFS object fetch'
  if ! command -v git-lfs >/dev/null 2>&1;then
    command -v pkg >/dev/null || fail 'git-lfs and pkg missing; cannot fetch pinned model'
    if command -v timeout >/dev/null;then timeout 180 pkg install -y git-lfs || fail 'git-lfs installation unsuccessful';else pkg install -y git-lfs || fail 'git-lfs installation unsuccessful';fi
  fi
  mkdir -p "$STATE/lfs-fetch"
  if [[ ! -d "$STATE/lfs-fetch/.git" ]];then
    GIT_LFS_SKIP_SMUDGE=1 git -c lfs.install.skip=true clone --depth=1 --filter=blob:none --no-checkout --single-branch --branch main "https://github.com/$REPO.git" "$STATE/lfs-fetch" || fail 'LFS recovery clone failed'
  fi
  [[ "$(git -C "$STATE/lfs-fetch" rev-parse HEAD)" == "$REMOTE" ]] || fail 'LFS recovery checkout revision changed'
  git -C "$STATE/lfs-fetch" lfs fetch --object-id origin "$MODEL_SHA" || fail 'exact LFS fetch failed; historical objects not requested'
  OBJ=$(git -C "$STATE/lfs-fetch" rev-parse --git-path "lfs/objects/${MODEL_SHA:0:2}/${MODEL_SHA:2:2}/$MODEL_SHA")
  [[ "$OBJ" = /* ]] || OBJ="$STATE/lfs-fetch/$OBJ"
  [[ -f "$OBJ" ]] && [[ "$(sha "$OBJ")" == "$MODEL_SHA" ]] || fail 'LFS object digest mismatch'
  SOURCE="$OBJ"
fi
[[ "$(sha "$SOURCE")" == "$MODEL_SHA" ]] || fail 'source SHA changed'
[[ "$(wc -c < "$SOURCE" | tr -d ' ')" == "$MODEL_BYTES" ]] || fail 'model byte count changed'
python3 - "$SOURCE" <<'PYSOURCE' || fail 'actual GLB skeleton/clip test failed'
import sys,struct,json
s=open(sys.argv[1],'rb').read()
def inspect(b):
 assert b[:4]==b'glTF' and len(b)==struct.unpack_from('<I',b,8)[0]
 n,kind=struct.unpack_from('<I4s',b,12);assert kind==b'JSON'
 g=json.loads(b[20:20+n]); joints=set(g['skins'][0]['joints'])
 assert len(joints)==74
 names=[a['name'] for a in g['animations']]
 assert len(names)==9 and {'Idle_Turn_Left','Idle_Turn_Right','Walking','Walk_Backward','slide_right'}.issubset(names)
 lookup={n.get('name'):i for i,n in enumerate(g['nodes'])}
 parents={c:i for i,node in enumerate(g['nodes']) for c in node.get('children',[])}
 for side,mid in [('Left','Bone_017'),('Right','Bone_013')]:
  chain=['mixamorig:Hips',f'mixamorig:{side}UpLeg',f'mixamorig:{side}Leg',mid,f'mixamorig:{side}Foot',f'mixamorig:{side}ToeBase']
  ids=[lookup[x] for x in chain]
  assert all(x in joints for x in ids) and all(parents[ids[i]]==ids[i-1] for i in range(1,len(ids)))
 return names
names=inspect(s)
for corrupted in (b'BAD!'+s[4:],s[:12]):
 try: inspect(corrupted)
 except Exception: pass
 else: raise AssertionError('corrupt GLB injection escaped guard')
print('GLB_REAL_SOURCE_AND_NEGATIVE_TESTS=PASS',','.join(names))
PYSOURCE
if [[ "$OP" == doctor ]];then
  [[ "$REMOTE" == "$BASE" || -f "$RECEIPT" ]] || fail 'remote main advanced; review contract'
  echo 'DOCTOR=PASS actual model, negative fixtures, and remote reachable; no repo mutation';exit 0
fi
# A known published receipt skips cloning, committing and pushing on rerun.
PUBLISHED=''
if [[ -f "$RECEIPT" ]];then
  PUBLISHED=$(python3 - "$RECEIPT" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]));print(r.get('publishedCommit','') if r.get('campaign')=='hareworks-procedural-walk-v0.1.0' and r.get('remoteReadback')==True else '')
PY
)
fi
# Recover the precise interrupted-post-push case even when receipt write never ran.
if [[ -z "$PUBLISHED" && "$REMOTE" != "$BASE" && -d "$ROOT/.git" ]];then
  CANDIDATE=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || true)
  if [[ "$CANDIDATE" == "$REMOTE" ]] && [[ "$(git -C "$ROOT" rev-parse HEAD^ 2>/dev/null || true)" == "$BASE" ]] && \
     [[ "$(git -C "$ROOT" show "HEAD:$SCRIPT" 2>/dev/null | sha256sum | cut -d' ' -f1)" == "$SELF_SHA" ]];then
    phase=post-push-reconciliation
    git -C "$ROOT" fetch --depth=1 origin main || fail 'cannot verify published interrupted revision'
    [[ "$(git -C "$ROOT" rev-parse FETCH_HEAD)" == "$CANDIDATE" ]] || fail 'remote commit differs from local recovery candidate'
    for p in "$SCRIPT" "$DIR/index.html" "$DIR/walker.mjs" "$DIR/gait-core.mjs" "$DIR/core-test.mjs" "$DIR/contract.json" "$DIR/reference-summary.json" "$DIR/README.md";do
      [[ "$(git -C "$ROOT" rev-parse "FETCH_HEAD:$p")" == "$(git -C "$ROOT" rev-parse "HEAD:$p")" ]] || fail "interrupted publication readback differs: $p"
    done
    for p in AGENTS.md assets/repl/Repl.glb assets/hareworks/Hareworks.glb "$MODEL" assets/hareworks/.gitattributes;do
      [[ "$(git -C "$ROOT" rev-parse "FETCH_HEAD:$p")" == "$(git -C "$ROOT" rev-parse "$BASE:$p")" ]] || fail "protected file changed in interrupted publication: $p"
    done
    REPL_SHA_RECOVER=$(git -C "$ROOT" show "$BASE:assets/repl/Repl.glb" | python3 -c 'import re,sys,hashlib;x=sys.stdin.buffer.read();m=re.search(rb"oid sha256:([0-9a-f]{64})",x);print(m.group(1).decode() if m else hashlib.sha256(x).hexdigest())')
    python3 - "$RECEIPT" "$CANDIDATE" "$BASE" "$SELF_SHA" "$MODEL_SHA" "$REPL_SHA_RECOVER" "$AGENTS_BLOB" <<'PYRECOVER'
import datetime,json,sys
out,commit,base,script,model,repl,agents=sys.argv[1:]
r={'campaign':'hareworks-procedural-walk-v0.1.0','phase':'recovered_remote_publication_viewer_pending','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'publishedCommit':commit,'pinnedSourceCommit':base,'scriptSha256':script,'nineClipModelSha256':model,'canonicalReplSha256':repl,'agentsGitBlobSha':agents,'remoteReadback':True,'rulesRead':{'AGENTS.md':'pinned Git blob','Campaign Etiquette':'Home Center document read by campaign author 2026-11-20','Top-down Etiquette':'Home Center document read by campaign author 2026-11-20'},'browserLoaded':False,'ownerVisualAcceptance':False}
with open(out,'w') as f:json.dump(r,f,indent=2)
PYRECOVER
    PUBLISHED="$CANDIDATE"
    echo "INTERRUPTED_POST_PUSH_RECOVERED=$PUBLISHED"
  fi
fi
if [[ -n "$PUBLISHED" ]];then
  [[ "$REMOTE" == "$PUBLISHED" ]] || fail "published receipt exists but remote main differs ($REMOTE vs $PUBLISHED)"
  [[ -d "$ROOT/.git" && "$(git -C "$ROOT" rev-parse HEAD)" == "$PUBLISHED" ]] || fail 'published checkout no longer matches receipt; do not replace'
  echo "PUBLICATION_ALREADY_CONFIRMED=$PUBLISHED"
  COMMIT="$PUBLISHED"
else
  [[ "$REMOTE" == "$BASE" ]] || fail "remote main advanced to $REMOTE; pinned base $BASE; no rewrite/force push"
  phase=checkout
  if [[ -e "$ROOT" ]];then
    [[ -d "$ROOT/.git" ]] || fail 'work path collision, no overwrite'
    [[ "$(git -C "$ROOT" remote get-url origin)" == "https://github.com/$REPO.git" ]] || fail 'origin mismatch'
    CUR=$(git -C "$ROOT" rev-parse HEAD)
    if [[ "$CUR" != "$BASE" ]];then
      if [[ "$(git -C "$ROOT" rev-parse HEAD^ 2>/dev/null || true)" == "$BASE" ]] && git -C "$ROOT" cat-file -e "HEAD:$SCRIPT" 2>/dev/null;then
        COMMIT="$CUR"
        [[ "$(git -C "$ROOT" show "HEAD:$SCRIPT" | sha256sum | cut -d' ' -f1)" == "$SELF_SHA" ]] || fail 'interrupted local commit was generated by different campaign bytes'
        echo "RECOVER_LOCAL_COMMIT=$COMMIT"
      else fail 'existing checkout has unexpected HEAD; leave unchanged';fi
    else
      [[ -z "$(git -C "$ROOT" status --porcelain --untracked-files=all)" ]] || fail 'existing base checkout dirty; preserve, inspect blocked receipt'
    fi
  else
    GIT_LFS_SKIP_SMUDGE=1 git -c lfs.install.skip=true clone --depth=1 --filter=blob:none --no-checkout --single-branch --branch main "https://github.com/$REPO.git" "$ROOT" || fail 'clone failed'
    git -C "$ROOT" sparse-checkout init --cone || fail 'sparse init failed'
    git -C "$ROOT" sparse-checkout set tools/hareworks-procedural-walk campaigns || fail 'sparse scope failed'
    GIT_LFS_SKIP_SMUDGE=1 git -C "$ROOT" checkout --detach "$BASE" || fail 'pinned checkout failed'
  fi
  cd "$ROOT"
  [[ "$(git rev-parse "$BASE:AGENTS.md")" == "$AGENTS_BLOB" ]] || fail 'AGENTS.md changed from inspected source'
  [[ -f AGENTS.md ]] && grep -Fq 'Termux Git only' AGENTS.md || fail 'AGENTS gate failed'
  REPL_BLOB=$(git rev-parse "$BASE:assets/repl/Repl.glb")
  HARE_OLD_BLOB=$(git rev-parse "$BASE:assets/hareworks/Hareworks.glb")
  HARE_NINE_BLOB=$(git rev-parse "$BASE:$MODEL")
  ATTR_BLOB=$(git rev-parse "$BASE:assets/hareworks/.gitattributes")
  REPL_CANONICAL_SHA=$(git show "$BASE:assets/repl/Repl.glb" | python3 -c 'import re,sys,hashlib;x=sys.stdin.buffer.read();m=re.search(rb"oid sha256:([0-9a-f]{64})",x);print(m.group(1).decode() if m else hashlib.sha256(x).hexdigest())')
  echo "PROTECTED_REPL_SHA256=$REPL_CANONICAL_SHA GIT_BLOB=$REPL_BLOB"
  python3 - "$MODEL_SHA" "$MODEL_BYTES" <<'PYPTR' || fail 'published model pointer incorrect'
import subprocess,sys
sha,size=sys.argv[1:]
b=subprocess.check_output(['git','show','HEAD:assets/hareworks/Hareworks-nine-clips.glb'])
assert b==f'version https://git-lfs.github.com/spec/v1\noid sha256:{sha}\nsize {size}\n'.encode()
print('PUBLISHED_MODEL_LFS_POINTER=VERIFIED')
PYPTR
  PATHS=("$SCRIPT" "$DIR/index.html" "$DIR/walker.mjs" "$DIR/gait-core.mjs" "$DIR/core-test.mjs" "$DIR/contract.json" "$DIR/reference-summary.json" "$DIR/README.md")
  if [[ -z "${COMMIT:-}" ]];then
    phase=collisions
    for p in "${PATHS[@]}";do
      [[ ! -e "$p" && ! -L "$p" ]] && ! git cat-file -e "$BASE:$p" 2>/dev/null || fail "destination exists: $p"
    done
    phase=author
    mkdir -p "$DIR" campaigns
    cp -- "$0" "$SCRIPT"
cat > "$DIR/index.html" <<'HWEOF_index_html'
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#0d1620"><title>Hareworks | Procedural Walk Lab v0.1.0</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>
:root{font:15px system-ui,sans-serif;color:#eaf0f7;background:#101721;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:1000px;margin:auto;padding:12px;padding-bottom:28px}header{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;justify-content:space-between}h1{font-size:1.25rem;margin:0 0 8px}small,.sub{color:#a8b8ca}#status{padding:9px 0;min-height:35px;color:#acd8d1}#stage{width:100%;border:1px solid #536376;overflow:hidden;border-radius:10px;background:#0e1723}#stage canvas{display:block;width:100%;touch-action:none}.controls{display:flex;justify-content:space-between;gap:12px;align-items:start;flex-wrap:wrap;margin:12px 0}.pad-wrap{flex:1 1 150px;display:flex;flex-direction:column;align-items:center;gap:6px}.pad{width:min(34vw,142px);height:min(34vw,142px);min-width:110px;min-height:110px;position:relative;border:2px solid #76899f;border-radius:50%;background:radial-gradient(circle,#283e50,#182332);touch-action:none;user-select:none;outline-offset:4px}.pad:before,.pad:after{content:"";position:absolute;pointer-events:none;background:#56687a}.pad:before{height:1px;width:80%;left:10%;top:50%}.pad:after{width:1px;height:80%;left:50%;top:10%}.dot{position:absolute;left:calc(50% - 13px);top:calc(50% - 13px);width:26px;height:26px;border-radius:50%;background:#72c8e9;border:2px solid #e3f2f5;box-shadow:0 0 7px #638fa4}.aim .dot{background:#f4b979}.tuning{display:flex;flex-wrap:wrap;gap:14px;margin:12px 0;font-size:13px}.tuning label{display:flex;align-items:center;gap:8px}.tuning input{width:110px;accent-color:#79c9e8}.toolbar{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}button{font:inherit;border:1px solid #71859a;color:#f7f9ff;background:#2d4357;border-radius:8px;min-height:42px;padding:9px 11px;cursor:pointer}button:focus-visible,.pad:focus-visible{outline:3px solid #78c8ec}button:active{background:#486079}#metrics{background:#1b2938;padding:9px;border:1px solid #40556b;border-radius:8px;font:12px ui-monospace,SFMono-Regular,monospace;white-space:pre-wrap}p{line-height:1.5}footer{font-size:12px;color:#aabbcb}.legend{font-size:12px;color:#b6c8d6}.legend span{display:inline-block;width:11px;height:11px;border-radius:100%;margin-right:5px}.pill{font-size:11px;border:1px solid #566c7c;border-radius:20px;padding:4px 8px;color:#c0d8dc}@media(max-width:520px){main{padding:9px}h1{font-size:1.05rem}#status{font-size:13px}.controls{gap:5px}.pad-wrap{flex:1 1 120px}}
</style></head><body><main>
<header><h1>🐇 Hareworks · Procedural Walk Lab</h1><span class="pill">v0.1.0 · LIVE IK candidate</span></header>
<p class="sub">True generated footsteps. Nine source animations remain unchanged; only one frame seeds the neutral pose.</p>
<div id="status" role="status" aria-live="polite">Preparing exact nine-clip model…</div>
<div id="stage" aria-label="Interactive overhead 3D view of the Hareworks engineer"></div>
<div class="legend"><span style="background:#46c5fa"></span>Left planted target &nbsp; <span style="background:#ffc67b"></span>Right planted target. Markers indicate ankle targets, not validated sole contact patches.</div>
<div class="controls">
  <div class="pad-wrap"><strong>Movement</strong><div class="pad" id="move-pad" role="group" aria-label="Movement touch pad" tabindex="0"><div class="dot" id="move-dot"></div></div><small>W A S D / arrows</small></div>
  <div class="pad-wrap aim"><strong>World aiming</strong><div class="pad" id="aim-pad" role="group" aria-label="Aim touch pad" tabindex="0"><div class="dot" id="aim-dot"></div></div><small>Q / E rotate aim</small></div>
</div>
<div class="tuning" aria-label="Experimental gait tuning"><label>Step lead <input id="step-lead" aria-label="Step lead distance" type="range" min="0.12" max="0.40" step="0.02" value="0.24"><output id="step-lead-value">0.24</output></label><label>Aim twist budget <input id="twist-budget" aria-label="Idle aim twist limit" type="range" min="15" max="60" step="5" value="35"><output id="twist-budget-value">35°</output></label><label>Foot lift <input id="foot-lift" aria-label="Swing foot lift" type="range" min="0.05" max="0.22" step="0.01" value="0.13"><output id="foot-lift-value">0.13</output></label></div>
<div class="toolbar"><button id="pause">Pause</button><button id="reset">Reset</button><button id="debug">Toggle markers</button><button id="test">Run actual-rig checks</button><button id="download">Export diagnostics</button></div>
<div id="metrics" aria-label="Live locomotion diagnostics">Awaiting real rig…</div>
<p><strong>How to judge:</strong> walk forward, reverse, strafe, go diagonal, then stop and sweep the aim pad through both sides. Check planted-foot slip, knee inversion, reach, foot yaw, body silhouette and pivot-step readability. The first test is a working prototype, not an accepted animation.</p>
<footer>Built for Android touch and keyboard. Source model SHA-256 <code>a0e0c757…2aec6</code>. Three.js 0.170.0 via CDN. Rendering and owner acceptance remain separate from Git publication and HTTP availability.</footer>
</main><script type="module" src="./walker.mjs"></script></body></html>
HWEOF_index_html
cat > "$DIR/walker.mjs" <<'HWEOF_walker_mjs'
/* Hareworks procedural WALK v0.1.0: independent movement + aim, authored footsteps, full skinned GLB. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clamp,wrap,shortest,smooth,landing,swing,chooseFoot,targetHeading,headingStep,DEFAULTS} from './gait-core.mjs';

const $=id=>document.getElementById(id);
const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const AXIS_Y=V(0,1,0);
const SOURCE_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const NAMES={
  left:['mixamorigLeftUpLeg','mixamorigLeftLeg','Bone_017','mixamorigLeftFoot','mixamorigLeftToeBase'],
  right:['mixamorigRightUpLeg','mixamorigRightLeg','Bone_013','mixamorigRightFoot','mixamorigRightToeBase']
};
// Extracted at Idle_Turn_Left t=0 from the exact nine-clip binary. Per-foot initial seed only.
// These are *not* accepted running floor/contact truths.
const HEURISTIC_SOLE={left:{ankleY:.159439,soleY:.010807},right:{ankleY:.155861,soleY:-.012837}};
function round(v){return Math.round(v*1000)/1000}
function finite(v){return Number.isFinite(v)}
function yaw(v){return Math.atan2(v.x,v.z)}
function boneWorld(b){return b.getWorldPosition(V())}
function worldQuat(b){return b.getWorldQuaternion(new THREE.Quaternion())}

class HareworksController {
  constructor(scene,gltf){
    this.scene=scene;
    this.actor=new THREE.Group();this.actor.name='PROCEDURAL_ACTOR';scene.add(this.actor);
    this.model=gltf.scene;this.actor.add(this.model);
    this.actualClips=gltf.animations.map(c=>c.name);
    if(gltf.animations.length!==9||!['Idle_Turn_Left','Idle_Turn_Right','Walk_Backward','slide_right'].every(n=>this.actualClips.includes(n)))throw Error('SOURCE_CLIP_COUNT_OR_NAMES_INVALID');
    this.seedOneFrame(gltf.animations);
    this.rig=this.discoverRig();
    this.rootRest={position:this.actor.position.clone(),yaw:0};
    this.baseHipsPosition=this.rig.hips.position.clone();
    this.originalQuat=new Map();this.model.traverse(o=>{if(o.isBone)this.originalQuat.set(o,o.quaternion.clone())});
    this.baseWorldFoot={};this.legs={};
    this.actor.updateMatrixWorld(true);
    for(const side of ['left','right']){
      const chain=this.rig.chains[side],ankle=chain[3],wp=boneWorld(ankle);
      const hip=boneWorld(chain[0]),knee=boneWorld(chain[1]),pole=knee.clone().sub(hip).cross(wp.clone().sub(hip)).normalize();
      this.legs[side]={side,chain,ankle,anchor:wp.clone(),rest:wp.clone(),bindPole:pole,worldFootQ:worldQuat(ankle),swing:null,stance:true,cooldown:0,lastResidual:0,lastYawDrift:0};
      this.baseWorldFoot[side]={pos:wp.clone(),quat:worldQuat(ankle)};
    }
    this.floorY=(HEURISTIC_SOLE.left.soleY+HEURISTIC_SOLE.right.soleY)/2;
    this.markers={};
    const colors={left:0x46c5fa,right:0xffc67b};
    for(const side of ['left','right']){
      const marker=new THREE.Mesh(new THREE.SphereGeometry(.045,12,8),new THREE.MeshBasicMaterial({color:colors[side],depthTest:false}));marker.renderOrder=10;
      this.scene.add(marker);this.markers[side]=marker;
    }
    this.lastStepped='right';this.stats={frames:0,steps:0,maxStanceError:0,maxIKResidual:0,maxWorldFootOrientationErrorDeg:0,kneePoleFlipFrames:0,feetInSwing:0};
    this.vel=V();this.bodyYaw=0;this.aimYaw=0;this.elapsed=0;this.lastFootstepAt=-3;this.maxReach=DEFAULTS.reach;
    const l=this.legs.left.rest,r=this.legs.right.rest;
    this.stanceWidth=Math.abs(l.x-r.x);
    this.legLength=Math.min(...['left','right'].map(s=>this.rig.chains[s].slice(0,-2).reduce((acc,b,i)=>acc+boneWorld(b).distanceTo(boneWorld(this.rig.chains[s][i+1])),0)));
    this.maxReach=Math.max(.23,Math.min(.44,this.legLength*.35));
    this.reset();
  }
  seedOneFrame(clips){
    const seed=clips.find(c=>c.name==='Idle_Turn_Left');
    // One-time pose seed for grounded visual setup. Runtime never plays or blends a source animation.
    const mixer=new THREE.AnimationMixer(this.model);mixer.clipAction(seed).reset().play();mixer.setTime(0);this.model.updateMatrixWorld(true);
    const poses=[];this.model.traverse(o=>{if(o.isBone)poses.push([o,o.position.clone(),o.quaternion.clone(),o.scale.clone()])});
    mixer.stopAllAction();mixer.uncacheRoot(this.model);
    for(const [o,p,q,s] of poses){o.position.copy(p);o.quaternion.copy(q);o.scale.copy(s)}
    this.model.updateMatrixWorld(true);
  }
  discoverRig(){
    const map=new Map();this.model.traverse(o=>{if(o.isBone){if(map.has(o.name))throw Error('DUPLICATE_RIG_NAME '+o.name);map.set(o.name,o)}});
    if(map.size!==74)throw Error('RIG_JOINT_COUNT_'+map.size+'_EXPECTED_74');
    const hips=map.get('mixamorigHips');if(!hips)throw Error('MISSING_HIPS');
    const chains={};
    for(const [side,names] of Object.entries(NAMES)){
      const chain=names.map(n=>{const b=map.get(n);if(!b)throw Error('MISSING_RIG_BONE '+n);return b});
      if(chain[0].parent!==hips||chain.some((b,i)=>i&&b.parent!==chain[i-1]))throw Error('RIG_PARENT_CHAIN_'+side);
      const lengths=chain.slice(0,-1).map((b,i)=>boneWorld(b).distanceTo(boneWorld(chain[i+1])));
      if(lengths.some(n=>!Number.isFinite(n)||n<.008))throw Error('RIG_SEGMENT_LENGTH_INVALID_'+side);
      chains[side]=chain;
    }
    const upper=['mixamorigSpine','mixamorigSpine1','mixamorigSpine2','mixamorigNeck','mixamorigHead'].map(n=>map.get(n));
    if(upper.some(x=>!x))throw Error('UPPER_BODY_RIG_MISSING');
    return {hips,chains,upper,all:map};
  }
  reset(){
    for(const [b,q] of this.originalQuat)b.quaternion.copy(q);
    this.rig.hips.position.copy(this.baseHipsPosition);
    this.actor.position.set(0,0,0);this.actor.rotation.y=0;this.actor.updateMatrixWorld(true);
    this.vel.set(0,0,0);this.bodyYaw=0;this.aimYaw=0;this.elapsed=0;this.lastFootstepAt=-3;this.lastStepped='right';
    for(const side of ['left','right']){
      const leg=this.legs[side];leg.anchor.copy(this.baseWorldFoot[side].pos);leg.worldFootQ.copy(this.baseWorldFoot[side].quat);leg.swing=null;leg.stance=true;leg.cooldown=0;leg.lastResidual=0;
    }
    this.stats={frames:0,steps:0,maxStanceError:0,maxIKResidual:0,maxWorldFootOrientationErrorDeg:0,kneePoleFlipFrames:0,feetInSwing:0};
    this.actor.updateMatrixWorld(true);
  }
  setUpperTwist(twist){
    const proportions=[.10,.3,.36,.14,.10];
    for(let i=0;i<this.rig.upper.length;i++){
      const b=this.rig.upper[i];b.quaternion.copy(this.originalQuat.get(b));
      this.model.updateMatrixWorld(true);
      const parentQ=worldQuat(b.parent),yawWorld=new THREE.Quaternion().setFromAxisAngle(AXIS_Y,twist*proportions[i]);
      const localYaw=parentQ.clone().invert().multiply(yawWorld).multiply(parentQ);
      b.quaternion.premultiply(localYaw);
    }
  }
  // Bounded real-bone CCD for the nonuniform five-node chain. The ankle is the
  // positional effector; its world orientation is then restored in stance.
  solveLeg(leg,target,footWorldQ){
    const chain=leg.chain,ankle=leg.ankle;
    for(const b of chain.slice(0,4))b.quaternion.copy(this.originalQuat.get(b));
    let residual=Infinity;
    const maxAngles=[1.0,1.25,.78];
    for(let pass=0;pass<14;pass++){
      for(let i=2;i>=0;i--){
        const bone=chain[i];this.actor.updateMatrixWorld(true);
        const pivot=boneWorld(bone),end=boneWorld(ankle),a=end.sub(pivot),b=target.clone().sub(pivot);
        if(a.lengthSq()<1e-9||b.lengthSq()<1e-9)continue;
        a.normalize();b.normalize();
        // New world orientation, with per-iteration rotation cap.
        const raw=new THREE.Quaternion().setFromUnitVectors(a,b),limited=new THREE.Quaternion();
        limited.slerpQuaternions(new THREE.Quaternion(),raw,Math.min(1,.22/Math.max(1e-9,2*Math.acos(clamp(raw.w,-1,1)))));
        const parentQ=worldQuat(bone.parent),newQ=parentQ.clone().invert().multiply(limited).multiply(worldQuat(bone));
        const base=this.originalQuat.get(bone),theta=base.angleTo(newQ);
        if(theta>maxAngles[i])newQ.slerpQuaternions(base,newQ,maxAngles[i]/theta);
        bone.quaternion.copy(newQ);
      }
      this.actor.updateMatrixWorld(true);residual=boneWorld(ankle).distanceTo(target);
      if(residual<.008)break;
    }
    this.actor.updateMatrixWorld(true);
    const parentQ=worldQuat(ankle.parent);
    ankle.quaternion.copy(parentQ.invert().multiply(footWorldQ));
    this.actor.updateMatrixWorld(true);
    residual=boneWorld(ankle).distanceTo(target);
    leg.lastResidual=residual;
    const actualQ=worldQuat(ankle);
    leg.lastYawDrift=THREE.MathUtils.radToDeg(actualQ.angleTo(footWorldQ));
    this.stats.maxIKResidual=Math.max(this.stats.maxIKResidual,residual);
    this.stats.maxWorldFootOrientationErrorDeg=Math.max(this.stats.maxWorldFootOrientationErrorDeg,leg.lastYawDrift);
    const hip=boneWorld(chain[0]),knee=boneWorld(chain[1]),normal=knee.sub(hip).cross(boneWorld(ankle).sub(hip)).normalize();
    const expected=leg.bindPole.clone().applyAxisAngle(AXIS_Y,this.bodyYaw);
    if(expected.dot(normal)<-.05)this.stats.kneePoleFlipFrames++;
    return residual;
  }
  stepLeg(side,destination){
    const leg=this.legs[side];if(leg.swing)return false;
    leg.swing={from:leg.anchor.clone(),to:destination.clone(),fromQ:leg.worldFootQ.clone(),toQ:new THREE.Quaternion().setFromAxisAngle(AXIS_Y,this.bodyYaw).multiply(this.baseWorldFoot[side].quat),time:0,duration:DEFAULTS.stepDuration};
    leg.stance=false;this.lastStepped=side;this.lastFootstepAt=this.elapsed;this.stats.steps++;
    return true;
  }
  update(dt,input){
    dt=clamp(dt,0,1/30);
    this.elapsed+=dt;this.stats.frames++;
    const desired=V(input.moveX||0,0,input.moveZ||0),inputMag=Math.min(1,desired.length());
    if(inputMag>.001)desired.normalize().multiplyScalar(DEFAULTS.speed*inputMag);
    const blend=1-Math.exp(-8*dt);this.vel.lerp(desired,blend);
    if(this.vel.lengthSq()<.00001&&inputMag===0)this.vel.set(0,0,0);
    this.actor.position.addScaledVector(this.vel,dt);
    const moving=this.vel.length()>.09;
    this.aimYaw=wrap(input.aimYaw??this.aimYaw);
    if(moving){this.bodyYaw=headingStep(this.bodyYaw,yaw(this.vel),DEFAULTS.turnRate,dt)}
    else{
      const t=targetHeading(this.bodyYaw,this.aimYaw,DEFAULTS.aimTwistBudget);
      if(Math.abs(t.excess)>.05)this.bodyYaw=headingStep(this.bodyYaw,this.aimYaw-Math.sign(t.excess)*DEFAULTS.aimTwistBudget,DEFAULTS.actorTurnRate,dt);
    }
    this.actor.rotation.y=this.bodyYaw;
    const aim=targetHeading(this.bodyYaw,this.aimYaw,DEFAULTS.aimTwistBudget);
    // Runtime torso yaw is independent of planar root locomotion.
    this.rig.hips.position.copy(this.baseHipsPosition);
    this.rig.hips.position.y+=moving?.008*Math.sin(this.elapsed*12):0;
    this.setUpperTwist(aim.twist);
    this.actor.updateMatrixWorld(true);
    const planned={};const errors={};
    for(const side of ['left','right']){
      const leg=this.legs[side],rest=leg.rest;
      planned[side]=new THREE.Vector3(...landing(this.actor.position.toArray(),rest.toArray(),this.bodyYaw,this.vel.toArray(),DEFAULTS.stepLead,leg.anchor.y));
      errors[side]=Math.hypot(planned[side].x-leg.anchor.x,planned[side].z-leg.anchor.z);
    }
    if(!Object.values(this.legs).some(l=>l.swing)&&this.elapsed-this.lastFootstepAt>.11){
      const direction=(!moving&&Math.abs(aim.excess)>.01)?Math.sign(aim.excess):0;
      const threshold=moving?this.maxReach:Math.max(.19,this.maxReach*.65);
      if(Math.max(errors.left,errors.right)>threshold){
        const side=chooseFoot(errors.left,errors.right,this.lastStepped,direction);
        const target=planned[side];const d=target.distanceTo(this.legs[side].anchor);
        const maxTravel=this.legLength*.7;
        if(d>maxTravel)target.lerp(this.legs[side].anchor,1-maxTravel/d);
        this.stepLeg(side,target);
      }
    }
    let swinging=0;
    for(const side of ['left','right']){
      const leg=this.legs[side];let target=leg.anchor.clone();
      if(leg.swing){
        swinging++;
        leg.swing.time+=dt;
        const u=clamp(leg.swing.time/leg.swing.duration,0,1);
        target.fromArray(swing(leg.swing.from.toArray(),leg.swing.to.toArray(),u,DEFAULTS.footLift));
        leg.worldFootQ.slerpQuaternions(leg.swing.fromQ,leg.swing.toQ,smooth(u));
        if(u>=1){leg.anchor.copy(leg.swing.to);leg.worldFootQ.copy(leg.swing.toQ);leg.swing=null;leg.stance=true;target.copy(leg.anchor)}
      }
      this.solveLeg(leg,target,leg.worldFootQ);
      if(leg.stance){this.stats.maxStanceError=Math.max(this.stats.maxStanceError,boneWorld(leg.ankle).distanceTo(leg.anchor))}
      this.markers[side].position.copy(leg.anchor);this.markers[side].position.y-=.025;
      this.markers[side].material.opacity=leg.stance?1:.45;this.markers[side].material.transparent=!leg.stance;
    }
    this.stats.feetInSwing=swinging;
    if(![this.actor.position.x,this.actor.position.z,this.bodyYaw,this.aimYaw,...Object.values(this.legs).map(l=>l.lastResidual)].every(finite))throw Error('NONFINITE_RIG_STATE');
  }
  diagnostics(){return {schema:'hareworks-procedural-walk-v0.1.0',modelSha256:SOURCE_SHA,origin:'independent root movement and IK; seeded Idle_Turn_Left at t=0 only',calibration:'PROVISIONAL_NOT_VISUALLY_ACCEPTED',rootPosition:this.actor.position.toArray().map(round),bodyYawDeg:round(THREE.MathUtils.radToDeg(this.bodyYaw)),aimYawDeg:round(THREE.MathUtils.radToDeg(this.aimYaw)),...this.stats,stanceWidth:round(this.stanceWidth),reach:round(this.maxReach),legs:Object.fromEntries(Object.entries(this.legs).map(([side,l])=>[side,{state:l.stance?'stance':'swing',target:l.anchor.toArray().map(round),ankleResidual:round(l.lastResidual),worldFootOrientationErrorDeg:round(l.lastYawDrift)}]))}}
}

const scene=new THREE.Scene();scene.background=new THREE.Color(0x101721);
scene.add(new THREE.HemisphereLight(0xe7e9ff,0x25303d,2.0));
const sunlight=new THREE.DirectionalLight(0xffffff,2.5);sunlight.position.set(-2,6,2);scene.add(sunlight);
const ground=new THREE.GridHelper(30,30,0x667788,0x384654);scene.add(ground);
const camera=new THREE.PerspectiveCamera(43,1,.02,150);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
let controller=null,last=performance.now(),paused=false,debug=true,framesSinceHud=0;
let moveStick={x:0,z:0},keyMove=new Set(),aimYaw=0;
function resize(){const w=$('stage').clientWidth,h=Math.max(300,Math.min(innerHeight*.64,w*.86));renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}
window.addEventListener('resize',resize);
function setupPad(id,onVector){const el=$(id);let pid=null;function update(e){const r=el.getBoundingClientRect(),dx=(e.clientX-(r.left+r.width/2))/(r.width*.39),dy=(e.clientY-(r.top+r.height/2))/(r.height*.39);const mag=Math.max(1,Math.hypot(dx,dy));onVector(dx/mag,-dy/mag)}
  el.addEventListener('pointerdown',e=>{pid=e.pointerId;el.setPointerCapture(pid);update(e)});
  el.addEventListener('pointermove',e=>{if(e.pointerId===pid)update(e)});
  const end=e=>{if(e.pointerId===pid){pid=null;if(id==='move-pad')onVector(0,0)}};
  el.addEventListener('pointerup',end);el.addEventListener('pointercancel',end);
}
setupPad('move-pad',(x,z)=>{moveStick={x,z};$('move-dot').style.transform=`translate(${x*34}px,${-z*34}px)`});
setupPad('aim-pad',(x,z)=>{if(Math.hypot(x,z)>.12)aimYaw=Math.atan2(x,z);$('aim-dot').style.transform=`translate(${x*34}px,${-z*34}px)`});
window.addEventListener('keydown',e=>{if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','KeyQ','KeyE','Space'].includes(e.code)){e.preventDefault();keyMove.add(e.code)}});
window.addEventListener('keyup',e=>keyMove.delete(e.code));
for(const [id,key,fmt] of [['step-lead','stepLead',v=>Number(v).toFixed(2)],['twist-budget','aimTwistBudget',v=>Math.round(v)+'°'],['foot-lift','footLift',v=>Number(v).toFixed(2)]]){const el=$(id);el.addEventListener('input',()=>{DEFAULTS[key]=key==='aimTwistBudget'?THREE.MathUtils.degToRad(Number(el.value)):Number(el.value);$(id+'-value').textContent=fmt(el.value)});}
$('pause').onclick=()=>{paused=!paused;$('pause').textContent=paused?'Resume':'Pause'};
$('reset').onclick=()=>{controller?.reset();aimYaw=0;moveStick={x:0,z:0};$('move-dot').style.transform='';$('aim-dot').style.transform=''};
$('debug').onclick=()=>{debug=!debug;$('metrics').hidden=!debug;for(const m of Object.values(controller?.markers||{}))m.visible=debug};
$('download').onclick=()=>{if(!controller)return;const s=JSON.stringify(controller.diagnostics(),null,2),url=URL.createObjectURL(new Blob([s],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='hareworks-procedural-walk-v0.1.0-diagnostics.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000)};
$('test').onclick=()=>{
  if(!controller)return;paused=true;controller.reset();
  const matrix=[{label:'forward',x:0,z:1,n:210},{label:'release',x:0,z:0,n:70},{label:'backward',x:0,z:-1,n:210},{label:'right-strafe',x:1,z:0,n:210},{label:'diagonal',x:-.7,z: .7,n:210},{label:'idle-aim-left',x:0,z:0,n:210,aim:-Math.PI*.75},{label:'idle-aim-right',x:0,z:0,n:210,aim:Math.PI*.75}];
  const evidence=[];let invalid=null;
  try{for(const phase of matrix){for(let i=0;i<phase.n;i++)controller.update(1/60,{moveX:phase.x,moveZ:phase.z,aimYaw:phase.aim??Math.atan2(phase.x,phase.z||1)});evidence.push({phase:phase.label,...controller.diagnostics()});if(controller.stats.maxIKResidual>0.35){invalid='large IK target error; inspect source geometry and knee constraints';break}if(controller.stats.kneePoleFlipFrames>0){invalid='knee bend pole inversion observed; inspect actual skeleton and adjust anatomical constraints';break}if(invalid)break}}
  catch(e){invalid=e.message}
  const report={schema:'hareworks-procedural-walk-v0.1.0-physical-check',publishedAsset:SOURCE_SHA,tests:evidence,result:invalid?'WARN_REVIEW_REQUIRED':'MEASUREMENT_COMPLETED_REVIEW_REQUIRED',warning:invalid,ownerAccepted:false};
  const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='hareworks-walk-real-rig-check-v0.1.0.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);
  $('status').textContent=`Real-rig movement check: ${report.result}; ${evidence.length}/${matrix.length} phases. Exported evidence. No visual acceptance implied.`;
  controller.reset();paused=false;
};
function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-last)/1000,1/30);last=now;
  if(controller&&!paused){const k=(a,b)=>keyMove.has(a)||keyMove.has(b),x=(k('KeyD','ArrowRight')?1:0)-(k('KeyA','ArrowLeft')?1:0),z=(k('KeyW','ArrowUp')?1:0)-(k('KeyS','ArrowDown')?1:0);
    const v=V(x+moveStick.x,0,z+moveStick.z);if(v.length()>1)v.normalize();
    if(keyMove.has('KeyQ'))aimYaw-=dt*1.8;if(keyMove.has('KeyE'))aimYaw+=dt*1.8;
    try{controller.update(dt,{moveX:v.x,moveZ:v.z,aimYaw})}catch(e){paused=true;$('status').textContent='BLOCKED_RUNTIME '+e.message;console.error(e)}
  }
  if(controller){camera.position.set(controller.actor.position.x,controller.floorY+5.7,controller.actor.position.z-3.4);camera.lookAt(controller.actor.position.x,.8+controller.floorY,controller.actor.position.z)}
  if(controller&&++framesSinceHud%15===0){const d=controller.diagnostics();$('metrics').textContent=`Steps ${d.steps} · Stance ankle residual ${d.maxStanceError.toFixed(3)} · IK target error ${d.maxIKResidual.toFixed(3)} · Twist ${d.bodyYawDeg}° body / ${d.aimYawDeg}° aim · ${d.legs.left.state}/${d.legs.right.state}`;}
  renderer.render(scene,camera)}
requestAnimationFrame(animate);
try{
  $('status').textContent='Loading exact published Hareworks 9-clip GLB (no animation playback)…';
  const gltf=await new GLTFLoader().loadAsync('../../../assets/hareworks/Hareworks-nine-clips.glb');
  controller=new HareworksController(scene,gltf);
  ground.position.y=controller.floorY;
  // Automatic actual-skeleton smoke: bind seed, forward stepping, reversal, idle turn.
  for(let i=0;i<180;i++){const q=i<60?{moveX:0,moveZ:1,aimYaw:0}:i<120?{moveX:0,moveZ:-1,aimYaw:0}:{moveX:0,moveZ:0,aimYaw:Math.PI/2};controller.update(1/60,q)}
  const smoke=controller.diagnostics();
  const smokeWarning=smoke.maxIKResidual>.35?' IK residual needs visual inspection: '+smoke.maxIKResidual.toFixed(3):' Real-rig smoke sampled.';
  console.info('HAREWORKS_REAL_RIG_SMOKE',smoke);controller.reset();
  resize();
  $('status').textContent='PROCEDURAL WALK LIVE · real rig · seed pose only.'+smokeWarning+' Use touch pads/WASD; run real-rig checks.';
  console.info('HAREWORKS_RIG_READY',controller.diagnostics());
}catch(e){$('status').textContent='BLOCKED_MODEL_OR_RIG: '+e.message;console.error(e)}
HWEOF_walker_mjs
cat > "$DIR/gait-core.mjs" <<'HWEOF_gait_core_mjs'
/* Hareworks procedural gait v0.1.0: deterministic, renderer-independent kinematics. */
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export const wrap=a=>Math.atan2(Math.sin(a),Math.cos(a));
export const shortest=(to,from)=>wrap(to-from);
export const smooth=t=>{t=clamp(t,0,1);return t*t*(3-2*t)};
export const add=(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]];
export const sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];
export const scale=(a,s)=>a.map(v=>v*s);
export const lengthXZ=a=>Math.hypot(a[0],a[2]);
export const distXZ=(a,b)=>lengthXZ(sub(a,b));
export const yawOf=(v)=>Math.atan2(v[0],v[2]);
export function rotateY(v,a){const c=Math.cos(a),s=Math.sin(a);return [v[0]*c+v[2]*s,v[1],v[2]*c-v[0]*s]}
export function landing(root,rest,yaw,velocity,lead,groundY){const offset=rotateY(rest,yaw);return [root[0]+offset[0]+velocity[0]*lead,groundY,root[2]+offset[2]+velocity[2]*lead]}
export function swing(start,end,u,lift){const k=smooth(u);return [start[0]+(end[0]-start[0])*k,start[1]+(end[1]-start[1])*k+lift*Math.sin(Math.PI*clamp(u,0,1))**1.2,start[2]+(end[2]-start[2])*k]}
export function chooseFoot(leftError,rightError,last,turnDirection=0){if(turnDirection>0.001)return 'left';if(turnDirection< -0.001)return 'right';if(Math.abs(leftError-rightError)<.035)return last==='left'?'right':'left';return leftError>rightError?'left':'right'}
export function targetHeading(bodyYaw,aimYaw,budget){const d=shortest(aimYaw,bodyYaw);return {twist:clamp(d,-budget,budget),excess:d-clamp(d,-budget,budget)}}
export function headingStep(bodyYaw,target,maxRate,dt){return wrap(bodyYaw+clamp(shortest(target,bodyYaw),-maxRate*dt,maxRate*dt))}
export const DEFAULTS={speed:.84,stepLead:.24,stepDuration:.43,footLift:.13,reach:.35,turnRate:1.15,aimTwistBudget:Math.PI/5,actorTurnRate:.8};
HWEOF_gait_core_mjs
cat > "$DIR/core-test.mjs" <<'HWEOF_core_test_mjs'
import assert from 'node:assert/strict';
import {clamp,wrap,shortest,smooth,rotateY,landing,swing,chooseFoot,targetHeading,headingStep,distXZ,DEFAULTS} from './gait-core.mjs';
const near=(a,b,eps=1e-8)=>assert.ok(Math.abs(a-b)<=eps,`${a} != ${b}`);
near(shortest(-Math.PI+0.1,Math.PI-0.1),.2);
near(wrap(Math.PI*3),Math.PI);
for(let t=0;t<=1;t+=.02){const s=swing([0,0,0],[1,0,0],t,.1);assert.ok(s.every(Number.isFinite));assert.ok(s[1]>=0);if(t===0||t>=.999)near(s[1],0,1e-6)}
let origin=[0,0,0],foot=[-.12,.16,.15];for(let i=0;i<200;i++){origin[2]+=0.01;near(distXZ(foot,[-.12,.16,.15]),0)}
const p=landing([2,0,3],[.2,.16,0],Math.PI/2,[1,0,0],.1,.16);near(p[0],2.1);near(p[2],2.8);
assert.equal(chooseFoot(.2,.2,'left'),'right');assert.equal(chooseFoot(.9,.1,'right'),'left');assert.equal(chooseFoot(0,0,'left',1),'left');assert.equal(chooseFoot(0,0,'right',-1),'right');
const t=targetHeading(0,Math.PI*.9,Math.PI/5);near(t.twist,Math.PI/5);assert.ok(t.excess>0);
let h=0;for(let i=0;i<120;i++)h=headingStep(h,Math.PI/2,.8,1/60);assert.ok(h>1&&h<=Math.PI/2);
for(const v of [[0,0,1],[1,0,0],[-1,0,0],[0,0,-1]])near(distXZ(rotateY(v,.9),[0,0,0]),1);
assert.ok(DEFAULTS.reach>DEFAULTS.footLift);console.log('CORE_TESTS=PASS angle-wrap, swing, world-lock, turn-budget, alternation, directional landing');
HWEOF_core_test_mjs
cat > "$DIR/contract.json" <<'HWEOF_contract_json'
{
  "schema": "hareworks-procedural-walk-campaign-v0.1.0",
  "owner": "Valar05",
  "repo": "Valar05/parametric-parambulator",
  "sourceCommit": "31d8799d8cc4d4be449615cc6d5771d87c792a07",
  "modelPath": "assets/hareworks/Hareworks-nine-clips.glb",
  "modelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "modelBytes": 6784896,
  "lanes": {"mutation":"Termux Git only", "execution":"Android Termux local server and browser"},
  "writeAllowlist": [
    "campaigns/hareworks-procedural-walk-v0.1.0.sh",
    "tools/hareworks-procedural-walk/v0.1.0/index.html",
    "tools/hareworks-procedural-walk/v0.1.0/walker.mjs",
    "tools/hareworks-procedural-walk/v0.1.0/gait-core.mjs",
    "tools/hareworks-procedural-walk/v0.1.0/core-test.mjs",
    "tools/hareworks-procedural-walk/v0.1.0/contract.json",
    "tools/hareworks-procedural-walk/v0.1.0/reference-summary.json",
    "tools/hareworks-procedural-walk/v0.1.0/README.md"
  ],
  "protected": ["AGENTS.md", "assets/repl/Repl.glb", "assets/hareworks/Hareworks.glb", "assets/hareworks/Hareworks-nine-clips.glb", "assets/hareworks/.gitattributes", "tools/hareworks-gait-extraction/v1.0.8"],
  "requiredBehavior": ["real-bone IK, no runtime Mixamo playback", "world-space stance ankle anchors", "independent actor movement and aim headings", "directional stepping", "stationary twist budget and pivot step", "visual and measured diagnostics", "on-device real-rig smoke and test export"],
  "evidenceBoundaries": ["git committed", "remote fetched/read back", "HTTP browser assets served", "runtime loaded GLB and solved bones", "owner visual acceptance"],
  "sourceDoctrine": [
    "https://docs.google.com/document/d/1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI/edit",
    "https://docs.google.com/document/d/1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU/edit",
    "https://docs.google.com/document/d/1BYhmuH21oX1_4SAmuNjCin0A6BJhQi4axQe9quaSs5o/edit",
    "https://docs.google.com/document/d/1BVoKaIG-ivp7Vl39SmrcEbfdAg-CAePjrd6IoRgEyQA/edit"
  ]
}
HWEOF_contract_json
cat > "$DIR/reference-summary.json" <<'HWEOF_reference_summary_json'
{
  "schema": "hareworks-procedural-walk-reference-summary-v0.1.0",
  "evidenceSource": "Owner-uploaded browser export hareworks-nine-clip-gait-and-idle-turn-v1.0.8.json, 2026-11-20",
  "modelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "rigJointCount": 74,
  "measurementStatus": "HEURISTIC_REFERENCE_NOT_GROUND_TRUTH",
  "ownerCorrections": [
    "Walk_Backward contains root motion",
    "slide_right contains root motion"
  ],
  "knownFlaws": [
    "pelvis world displacement must not be called actual root motion",
    "large idle turn yaw paths disagree with net change; do not calibrate turn limit from paths",
    "sole witnesses are partial skinned-vertex estimates and not support-force data",
    "contact candidates not accepted stance labels"
  ],
  "clips": [
    {
      "name": "Running",
      "durationSeconds": 0.633333,
      "samples": 61,
      "pelvisDeltaXYZ": [
        -0.006488,
        0.022055,
        -0.03143
      ],
      "pelvisNetYawDegrees": 5.273678,
      "pelvisYawPathDegrees": 33.352989,
      "groundNearCandidateFractions": {
        "left": 0.409836,
        "right": 0.245902
      },
      "sourceRootMotion": "UNVERIFIED"
    },
    {
      "name": "Walking",
      "durationSeconds": 1.033333,
      "samples": 63,
      "pelvisDeltaXYZ": [
        -0.003491,
        -0.044852,
        -0.027961
      ],
      "pelvisNetYawDegrees": -1.917529,
      "pelvisYawPathDegrees": 22.674214,
      "groundNearCandidateFractions": {
        "left": 0.492063,
        "right": 0.539683
      },
      "sourceRootMotion": "UNVERIFIED"
    },
    {
      "name": "Cautious_Crouch_Walk_Left",
      "durationSeconds": 1.166667,
      "samples": 71,
      "pelvisDeltaXYZ": [
        -0.00293,
        0.13541,
        -0.012971
      ],
      "pelvisNetYawDegrees": 34.746351,
      "pelvisYawPathDegrees": 57.811213,
      "groundNearCandidateFractions": {
        "left": 0.366197,
        "right": 0.774648
      },
      "sourceRootMotion": "UNVERIFIED"
    },
    {
      "name": "Cautious_Crouch_Walk_Left_inplace",
      "durationSeconds": 1.166667,
      "samples": 71,
      "pelvisDeltaXYZ": [
        -0.00293,
        0.131456,
        -0.012971
      ],
      "pelvisNetYawDegrees": 34.746351,
      "pelvisYawPathDegrees": 57.611959,
      "groundNearCandidateFractions": {
        "left": 0.380282,
        "right": 0.774648
      },
      "sourceRootMotion": "UNVERIFIED"
    },
    {
      "name": "Idle_Turn_Left",
      "durationSeconds": 0.933333,
      "samples": 61,
      "pelvisDeltaXYZ": [
        -0.005347,
        -0.013193,
        -0.04997
      ],
      "pelvisNetYawDegrees": 5.754528,
      "pelvisYawPathDegrees": 226.744839,
      "groundNearCandidateFractions": {
        "left": 0.114754,
        "right": 0.52459
      },
      "sourceRootMotion": "UNVERIFIED"
    },
    {
      "name": "Idle_Turn_Right",
      "durationSeconds": 1.1,
      "samples": 67,
      "pelvisDeltaXYZ": [
        -0.00265,
        -0.002658,
        -0.05172
      ],
      "pelvisNetYawDegrees": -2.627017,
      "pelvisYawPathDegrees": 202.892668,
      "groundNearCandidateFractions": {
        "left": 0.701493,
        "right": 0.208955
      },
      "sourceRootMotion": "UNVERIFIED"
    },
    {
      "name": "Walk_Backward",
      "durationSeconds": 0.866667,
      "samples": 61,
      "pelvisDeltaXYZ": [
        -0.003088,
        0.015885,
        -0.016852
      ],
      "pelvisNetYawDegrees": 2.310725,
      "pelvisYawPathDegrees": 18.752462,
      "groundNearCandidateFractions": {
        "left": 0.245902,
        "right": 0.229508
      },
      "sourceRootMotion": "CONFIRMED_BY_OWNER"
    },
    {
      "name": "Walking_Woman",
      "durationSeconds": 0.966667,
      "samples": 61,
      "pelvisDeltaXYZ": [
        -0.008843,
        -0.038906,
        -0.024889
      ],
      "pelvisNetYawDegrees": -10.612163,
      "pelvisYawPathDegrees": 42.328962,
      "groundNearCandidateFractions": {
        "left": 0.491803,
        "right": 0.442623
      },
      "sourceRootMotion": "UNVERIFIED"
    },
    {
      "name": "slide_right",
      "durationSeconds": 1.733333,
      "samples": 105,
      "pelvisDeltaXYZ": [
        -0.002708,
        0.001717,
        -0.014684
      ],
      "pelvisNetYawDegrees": -3.498292,
      "pelvisYawPathDegrees": 183.06142,
      "groundNearCandidateFractions": {
        "left": 0.171429,
        "right": 0.133333
      },
      "sourceRootMotion": "CONFIRMED_BY_OWNER"
    }
  ]
}
HWEOF_reference_summary_json
cat > "$DIR/README.md" <<'HWEOF_README_md'
# Hareworks procedural walk v0.1.0: genuine IK prototype

The preserved 74-joint, nine-clip Hareworks GLB is the only mesh. This campaign publishes **text-only** runtime code. **No GLB, prior source, approved 2D Boneforge work, or Repl file is changed.**

## What runs

The viewer seeds ONE static pose from `Idle_Turn_Left` at t=0 for a grounded starting position, then stops/uncaches animation actions. All subsequent locomotion comes from explicit root velocity and yaw, world-space ankle targets, generated swing curves, and iterative bounded CCD on the **actual five-node hierarchy** (UpLeg > Leg > intermediate > Foot > ToeBase). The ankle world orientation is compensated during stance. Gait core code has deterministic Node tests; the viewer runs a short automatic real-rig smoke and can export a multi-direction real-rig check.

Controls: keyboard WASD/arrows, Q/E aiming, or phone movement and aim touch pads. The movement heading and aim heading are independent. At rest, aim twists the upper body up to a *provisional* budget; beyond it, body yaw starts moving, and a foot is repositioned as necessary.

## Boundaries and limitations

- This is a kinematic preview, **not a solved balance simulation**, validated ankle/sole force model, accepted anatomical ROM, or polished idle-turn animation.
- The foot target is the **ankle**, not a fully reconstructed contact patch. Per-foot seed sole heights come from the owner-uploaded heuristic v1.0.8 browser export; these are provisional.
- A bounded CCD solver may leave residual if a destination is unreachable. The viewer exposes that residual; it must not be hidden by weakening assertions or claiming a valid planted sole.
- Source clips, including `Walk_Backward` and `slide_right`, can have root motion; their pelvis/world translations are not direct proof of actual root motion or stance slip. They are only *reference priors*, not runtime animation.
- The yaw-path anomalies in the turn extractor are **not** used to set accepted twist thresholds. The initial budget is an experimental knob.
- This baseline is a **biped**, not a horse or six-legged crab. Reuse their phase planning/contact disciplines, not equine duty factors or hexapod footstep timing.
- Rendering depends on Three.js 0.170.0 from its CDN. Network is needed for a first browser load. HTTP success is not WebGL success.

## Verification and review

The Termux campaign verifies a pinned Git parent, actual source bytes and GLB JSON rig/clip properties, clean collision gates, scope-limited staging, Node syntax and numeric core tests, exact push/readback, and exact GLB digest over HTTP. The browser also loads/solves the real rig and can export real-rig directional-check JSON. **Human acceptance remains pending.** Review forward/back, strafe, diagonals, release, idle twist and foot repositioning at phone scale; inspect knee bends, toe/heel floor contact, ankle residuals, foot orientation, reach and silhouette. An attractive initial stance is not proof of a correct walk cycle.

On rerun, use `status` or `resume` with the same script. A complete published receipt can re-launch the viewer without a new commit. Interrupted/dirty checkout state is preserved, never silently overwritten.
HWEOF_README_md
    for p in "${PATHS[@]}";do [[ -s "$p" ]] || fail "authored file missing: $p";done
    [[ "$(sha "$SCRIPT")" == "$SELF_SHA" ]] || fail 'campaign self-copy changed'
    phase=test
    if ! command -v node >/dev/null 2>&1;then
      command -v pkg >/dev/null || fail 'Node missing and pkg unavailable'
      if command -v timeout >/dev/null;then timeout 240 pkg install -y nodejs || fail 'Node install failed';else pkg install -y nodejs || fail 'Node install failed';fi
    fi
    node --check "$DIR/gait-core.mjs" || fail 'core JS syntax failed'
    node --check "$DIR/walker.mjs" || fail 'walker JS syntax failed'
    node --check "$DIR/core-test.mjs" || fail 'test JS syntax failed'
    node "$DIR/core-test.mjs" || fail 'deterministic unit tests failed'
    python3 - "$DIR/contract.json" "$DIR/reference-summary.json" <<'PYCONTRACT' || fail 'contract or source evidence invalid'
import json,sys
c=json.load(open(sys.argv[1]));d=json.load(open(sys.argv[2]))
assert c['modelSha256']==d['modelSha256']
assert len(c['writeAllowlist'])==8 and len(set(c['writeAllowlist']))==8
assert len(d['clips'])==9 and {'Idle_Turn_Left','Idle_Turn_Right','Walk_Backward','slide_right'}<={x['name'] for x in d['clips']}
assert all(x['sourceRootMotion']=='CONFIRMED_BY_OWNER' for x in d['clips'] if x['name'] in ('Walk_Backward','slide_right'))
print('CONTRACT_AND_NINE_CLIP_EVIDENCE=PASS')
PYCONTRACT
    [[ "$(git rev-parse "$BASE:assets/repl/Repl.glb")" == "$REPL_BLOB" ]] || fail 'Repl source changed'
    [[ "$(git rev-parse "$BASE:assets/hareworks/Hareworks.glb")" == "$HARE_OLD_BLOB" ]] || fail 'seven-clip source changed'
    [[ "$(git rev-parse "$BASE:$MODEL")" == "$HARE_NINE_BLOB" ]] || fail 'nine-clip source changed'
    phase=stage
    git add -- "${PATHS[@]}" || fail 'staging failed'
    python3 - "${PATHS[@]}" <<'PYSTAGE' || fail 'unexpected staged paths'
import subprocess,sys
wanted=set(sys.argv[1:]);actual=set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines())
assert wanted==actual,(wanted-actual,actual-wanted)
print('STAGED_PATHS=PASS',len(actual))
PYSTAGE
    phase=commit
    git -c user.name='Hareworks Termux Campaign' -c user.email='hareworks-campaign@users.noreply.github.com' commit -m 'Add Hareworks procedural IK walk and stationary aim lab v0.1.0' || fail 'commit failed'
    COMMIT=$(git rev-parse HEAD)
    [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'unexpected parent'
  fi
  phase=publish
  [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'main advanced before publication; no force push'
  # No LFS paths are staged; skip pre-push historical object scanning only.
  GIT_LFS_SKIP_PUSH=1 git push origin HEAD:refs/heads/main || fail "push failed; local commit preserved $COMMIT"
  phase=readback
  [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$COMMIT" ]] || fail 'remote SHA mismatch'
  GIT_LFS_SKIP_SMUDGE=1 git fetch --depth=1 origin main || fail 'remote readback fetch failed'
  [[ "$(git rev-parse FETCH_HEAD)" == "$COMMIT" ]] || fail 'fetched remote revision mismatch'
  for p in "${PATHS[@]}";do
    [[ "$(git show "FETCH_HEAD:$p" | sha256sum | cut -d' ' -f1)" == "$(sha "$p")" ]] || fail "remote file differs: $p"
  done
  for p in AGENTS.md assets/repl/Repl.glb assets/hareworks/Hareworks.glb "$MODEL" assets/hareworks/.gitattributes;do
    [[ "$(git rev-parse "FETCH_HEAD:$p")" == "$(git rev-parse "$BASE:$p")" ]] || fail "protected file changed: $p"
  done
  echo "GIT_REMOTE_READBACK=PASS $COMMIT"
  python3 - "$RECEIPT" "$COMMIT" "$BASE" "$SELF_SHA" "$MODEL_SHA" "$REPL_CANONICAL_SHA" "$AGENTS_BLOB" <<'PYPUBLISH'
import datetime,json,sys
out,commit,base,script,model,repl,agents=sys.argv[1:]
r={'campaign':'hareworks-procedural-walk-v0.1.0','phase':'remote_published_viewer_pending','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'publishedCommit':commit,'pinnedSourceCommit':base,'scriptSha256':script,'nineClipModelSha256':model,'canonicalReplSha256':repl,'agentsGitBlobSha':agents,'remoteReadback':True,'rulesRead':{'AGENTS.md':'pinned exact Git blob','Campaign Etiquette':'Home Center 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI read by campaign author 2026-11-20','Top-down Etiquette':'Home Center 1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU read by campaign author 2026-11-20'},'browserLoaded':False,'physicalIKReviewAccepted':False,'ownerVisualAcceptance':False}
with open(out,'w') as f:json.dump(r,f,indent=2)
PYPUBLISH
fi
# Exact source is served via separate source-file routing: no Git/LFS worktree edits.
phase=viewer
[[ -z "$(git -C "$ROOT" status --porcelain --untracked-files=all)" ]] || fail 'published checkout dirty; never serve unverified local edits'
[[ "$(git -C "$ROOT" rev-parse HEAD)" == "$COMMIT" ]] || fail 'viewer checkout commit mismatch'
if [[ -f "$STATE/server-ready.json" ]];then
  P=$(python3 - "$STATE/server-ready.json" <<'PYPORT'
import json,sys
print(json.load(open(sys.argv[1])).get('port',''))
PYPORT
)
  if [[ -n "$P" ]] && curl -fsS --max-time 3 "http://127.0.0.1:$P/$DIR/index.html" >/dev/null 2>&1;then
    URL="http://127.0.0.1:$P/$DIR/index.html?commit=$COMMIT"
    echo "VIEWER_REUSED=$URL"
    command -v termux-open-url >/dev/null && termux-open-url "$URL" || true
    exit 0
  fi
fi
cat > "$STATE/server.py" <<'PYSERVER'
import http.server,json,os,pathlib,sys,urllib.parse
root,source,ready,size=sys.argv[1:]
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=root,**kwargs)
 def do_GET(self):
  path=urllib.parse.urlsplit(self.path).path
  if path=='/assets/hareworks/Hareworks-nine-clips.glb':
   self.send_response(200);self.send_header('Content-Type','model/gltf-binary');self.send_header('Content-Length',size);self.send_header('Cache-Control','no-store');self.end_headers()
   with open(source,'rb') as stream:self.copyfile(stream,self.wfile)
  else:super().do_GET()
 def end_headers(self):
  self.send_header('Cache-Control','no-store, max-age=0');super().end_headers()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
pathlib.Path(ready).write_text(json.dumps({'port':server.server_address[1],'pid':os.getpid(),'repoRoot':root,'modelSource':source}))
server.serve_forever()
PYSERVER
rm -f "$STATE/server-ready.json"
nohup python3 "$STATE/server.py" "$ROOT" "$SOURCE" "$STATE/server-ready.json" "$MODEL_BYTES" >"$STATE/server.log" 2>&1 </dev/null &
PID=$!
READY=0;PORT=''
for i in 1 2 3 4 5 6 7 8 9 10;do
  if [[ -f "$STATE/server-ready.json" ]];then
    PORT=$(python3 - "$STATE/server-ready.json" <<'PYPORT'
import json,sys
print(json.load(open(sys.argv[1]))['port'])
PYPORT
)
    if curl -fsS --max-time 3 "http://127.0.0.1:$PORT/$DIR/index.html" >/dev/null 2>&1 && curl -fsS --max-time 3 "http://127.0.0.1:$PORT/$DIR/walker.mjs" >/dev/null 2>&1;then READY=1;break;fi
  fi
  sleep 1
done
[[ "$READY" == 1 ]] && kill -0 "$PID" 2>/dev/null || fail "viewer failed HTTP; see $STATE/server.log"
HTTP_SHA=$(curl -fsS --max-time 40 "http://127.0.0.1:$PORT/$MODEL" | sha256sum | cut -d' ' -f1) || fail 'HTTP model GET failed'
[[ "$HTTP_SHA" == "$MODEL_SHA" ]] || fail "HTTP model SHA incorrect: $HTTP_SHA"
URL="http://127.0.0.1:$PORT/$DIR/index.html?commit=$COMMIT"
python3 - "$RECEIPT" "$URL" "$PID" "$HTTP_SHA" "$ROOT" <<'PYDONE'
import datetime,json,sys
out,url,pid,sha,root=sys.argv[1:]
r=json.load(open(out));r.update({'phase':'viewer_http_ready_real_rig_browser_review_pending','viewerUrl':url,'viewerPid':int(pid),'modelHttpSha256':sha,'sourceCheckout':root,'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'browserLoaded':False,'ownerVisualAcceptance':False})
with open(out,'w') as f:json.dump(r,f,indent=2)
PYDONE
echo "REMOTE_COMMIT=$COMMIT"
echo "MODEL_HTTP_SHA256=PASS $HTTP_SHA"
echo "VIEWER_URL=$URL"
echo "VIEWER_PID=$PID PORT=$PORT"
echo "RECEIPT=$RECEIPT"
echo 'BROWSER_REAL_RIG_SMOKE_AND_OWNER_VISUAL_ACCEPTANCE=PENDING'
if command -v termux-open-url >/dev/null;then termux-open-url "$URL" || echo "BROWSER_OPEN_FAILED=YES URL=$URL";else echo "TERMUX_OPEN_URL_UNAVAILABLE URL=$URL";fi
