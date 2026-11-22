#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_CAMERA_RECOVERY_v0.1.28 — camera-only; Termux Git owns mutation.
set -Eeuo pipefail
umask 077
CAMPAIGN=HAREWORKS_CAMERA_RECOVERY_v0.1.28
REPO=https://github.com/Valar05/parametric-parambulator.git
BASE=0b0c2ee6df4d697844e231247d0c6c25550a1293
OLD=tools/hareworks-forward-woman/v0.1.26
NEW=tools/hareworks-forward-woman/v0.1.28
CHECKOUT="$HOME/storage/documents/GodotProjects/parametric-parambulator"
STATE="$HOME/.local/state/hareworks-camera-v0.1.28"
mkdir -p "$STATE"; LOG="$STATE/run.log"; exec > >(tee -a "$LOG") 2>&1
STAGE=boot; NEWCOMMIT=''; SCRIPT_SHA="$(sha256sum "$(readlink -f "${BASH_SOURCE[0]}")" | cut -d' ' -f1)"
receipt(){ local code=$?; python3 - "$STATE/receipt.json" "$CAMPAIGN" "$STAGE" "$code" "$SCRIPT_SHA" "$BASE" "$NEWCOMMIT" <<'PY'
import json,sys,datetime,pathlib
path,campaign,stage,code,script,base,commit=sys.argv[1:]
pathlib.Path(path).write_text(json.dumps(dict(campaign=campaign,stage=stage,exitCode=int(code),scriptSha256=script,sourceCommit=base,commit=commit or None,termuxGitOnly=True,modelUnchanged=True,ownerVisualAccepted=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')
PY
printf 'RECEIPT=%s/receipt.json EXIT=%s STAGE=%s\n' "$STATE" "$code" "$STAGE"; }
trap receipt EXIT
printf 'CAMPAIGN=%s SCRIPT_SHA256=%s SOURCE_COMMIT=%s\n' "$CAMPAIGN" "$SCRIPT_SHA" "$BASE"
[ "${PREFIX:-}" = /data/data/com.termux/files/usr ] && [ -n "${ANDROID_ROOT:-}" ] || { echo BLOCKED_NOT_TERMUX; exit 70; }
for b in git python3 node sha256sum curl; do command -v "$b" >/dev/null || { echo "BLOCKED_MISSING_TOOL=$b"; exit 71; }; done
git lfs version >/dev/null || { echo BLOCKED_MISSING_GIT_LFS; exit 71; }
[ -d "$CHECKOUT/.git" ] && [ ! -L "$CHECKOUT" ] && [ ! -L "$CHECKOUT/.git" ] || { echo BLOCKED_EXPECTED_PERSISTENT_DOCUMENTS_CHECKOUT_NOT_FOUND;exit 72; }
CANON="$(readlink -f "$CHECKOUT")"; [ "$CANON" = "$(readlink -f "$HOME/storage/documents")/GodotProjects/parametric-parambulator" ] || { echo BLOCKED_CHECKOUT_PATH;exit 72; }
git config --global --get-all safe.directory 2>/dev/null | grep -Fxq "$CANON" || git config --global --add safe.directory "$CANON"
cd "$CHECKOUT"; [ "$(git rev-parse --show-toplevel)" = "$CANON" ] || { echo BLOCKED_WRONG_WORKTREE;exit 72; }
case "$(git remote get-url origin)" in "$REPO"|'git@github.com:Valar05/parametric-parambulator.git') :;; *) echo BLOCKED_WRONG_ORIGIN;exit 72;; esac
[ "$(git symbolic-ref --short HEAD)" = main ] || { echo BLOCKED_NOT_MAIN;exit 72; }
export GIT_LFS_SKIP_SMUDGE=1 GIT_TERMINAL_PROMPT=0
STAGE=remote-head; LIVE=''; for attempt in 1 2 3;do LIVE="$(timeout 40 git ls-remote "$REPO" refs/heads/main | cut -f1)" && [ -n "$LIVE" ] && break || true; sleep "$attempt";done
[ -n "$LIVE" ] || { echo BLOCKED_REMOTE_UNREACHABLE;exit 73; }
HEAD="$(git rev-parse HEAD)"
if [ "$HEAD" != "$BASE" ] || [ "$LIVE" != "$BASE" ]; then
  if [ "$HEAD" = "$LIVE" ] && [ -f "$NEW/viewer.mjs" ] && grep -Fq 'HAREWORKS_CAMERA_RECOVERY_v0.1.28' "$NEW/viewer.mjs";then
    STAGE=already-published; NEWCOMMIT="$HEAD"; echo "ALREADY_PUBLISHED_REMOTE=$HEAD";exit 0
  fi
  # A previously committed but unpushed camera version can be resumed safely.
  if [ "$LIVE" = "$BASE" ] && [ "$(git rev-list --parents -n1 "$HEAD" | awk '{print $2}')" = "$BASE" ] && [ -f "$NEW/viewer.mjs" ] && [ "$(git diff-tree --no-commit-id --name-only -r "$HEAD" | grep -v "^$NEW/" | wc -l)" -eq 0 ];then
    STAGE=resume-push; NEWCOMMIT="$HEAD"; git push origin HEAD:refs/heads/main
    [ "$(timeout 40 git ls-remote "$REPO" refs/heads/main | cut -f1)" = "$NEWCOMMIT" ] || { echo BLOCKED_REMOTE_READBACK;exit 79; }
    STAGE=published;echo "REMOTE_READBACK_PASS=$NEWCOMMIT";exit 0
  fi
  echo "BLOCKED_REMOTE_OR_CHECKOUT_DRIFT local=$HEAD remote=$LIVE expected=$BASE";exit 73
fi
STAGE=rules-and-source
[ "$(git hash-object AGENTS.md)" = 547c2af52303f4efb718bbf8f82a698110c7bfca ] || { echo BLOCKED_AGENTS_CHANGED;exit 74; }
[ "$(git hash-object "$OLD/viewer.mjs")" = 6c8008f65f58a7df097044d474a0774fcf241988 ] || { echo BLOCKED_V026_VIEWER_CHANGED;exit 74; }
[ -f "$OLD/index.html" ] && [ -f "$OLD/sidestep-core.mjs" ] && [ -f "$OLD/left-contact.mjs" ] || { echo BLOCKED_SOURCE_FILES_MISSING;exit 74; }
MODEL=assets/hareworks/Hareworks-nine-clips.glb
[ -f "$MODEL" ] && [ "$(sha256sum "$MODEL" | cut -d' ' -f1)" = a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6 ] || { echo BLOCKED_SOURCE_GLB_HASH;exit 74; }
[ ! -e "$NEW" ] && [ -z "$(git ls-tree -r --name-only HEAD -- "$NEW")" ] || { echo BLOCKED_TARGET_COLLISION;exit 75; }
# The verified LFS binary can be reported by Git as ' M' on Android even when its SHA is correct.
python3 - "$MODEL" <<'PY'
import subprocess,sys
model=sys.argv[1]
entries=subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).split(b'\0')
for raw in entries:
 if not raw:continue
 s=raw.decode('utf-8','surrogateescape')
 if s==' M '+model:continue
 # Preserve the untracked files from the failed v0.1.27 checks-stage attempt.
 # They are neither overwritten nor staged. Anything else remains a hard stop.
 if s.startswith('?? tools/hareworks-forward-woman/v0.1.27/'):continue
 raise SystemExit('BLOCKED_DIRTY_WORKTREE '+repr(s))
if subprocess.run(['git','diff','--cached','--quiet']).returncode:raise SystemExit('BLOCKED_STAGED_CHANGES')
print('CLEAN_SCOPE_PASS')
PY
STAGE=build
cp -R "$OLD" "$NEW"
cp "$(readlink -f "${BASH_SOURCE[0]}")" "$NEW/campaign-v0.1.28-camera-recovery.sh"
# v0.1.26 is immutable. New camera-only viewer and HTML are versioned separately.
python3 - "$NEW/viewer.mjs" "$NEW/index.html" <<'PY'
from pathlib import Path
import sys
p,h=map(Path,sys.argv[1:]); s=p.read_text(); html=h.read_text()
def replace(old,new,count=1):
 global s
 n=s.count(old)
 if n!=count:raise SystemExit(f'BLOCKED_SOURCE_PATCH_ANCHOR count={n} expected={count} key={old[:80]!r}')
 s=s.replace(old,new)
start=s.index('const camera=new THREE.OrthographicCamera(')
end=s.index('let source=null,actor=null,',start)
camera=r'''// HAREWORKS_CAMERA_RECOVERY_v0.1.28. Camera state is independent of gait state.
const camera=new THREE.OrthographicCamera(-3,3,2,-2,0.01,1000);
const orbit=new OrbitControls(camera,renderer.domElement);
orbit.enableRotate=true;orbit.enableZoom=true;orbit.enablePan=true;
orbit.screenSpacePanning=true;orbit.enableDamping=true;orbit.dampingFactor=.09;
orbit.minZoom=.1;orbit.maxZoom=24;
const views={oblique:[-3.8,2.8,5.0],front:[0,2.6,6.5],side:[-6.5,2.5,0],top:[-.01,8,.01]};
let currentView='oblique',followEnabled=true,fitHeight=3.5,knownBounds=null,lastActorPosition=null;
function measuredBounds(){
  if(!actor)return null;
  actor.updateMatrixWorld(true);
  const b=new THREE.Box3();let count=0;
  actor.traverse(o=>{if(!o.isSkinnedMesh)return;
    o.computeBoundingBox();const local=o.boundingBox;
    if(local&&!local.isEmpty()){
      const world=local.clone().applyMatrix4(o.matrixWorld);
      if([world.min.x,world.min.y,world.min.z,world.max.x,world.max.y,world.max.z].every(Number.isFinite)){
        b.union(world);count++;
      }
    }
  });
  if(!count||b.isEmpty())throw Error('CAMERA_NO_VALID_SKINNED_BOUNDS');
  const size=b.getSize(V());
  if(!(size.length()>.01&&size.length()<100))throw Error('CAMERA_INVALID_SKINNED_EXTENTS_'+size.toArray());
  return b;
}
function resize(){
  const w=Math.max(300,$('stage').clientWidth),h=Math.max(320,Math.min(720,Math.round(w*.78)));
  renderer.setSize(w,h,false);
  const half=fitHeight/2,aspect=w/h;
  camera.top=half;camera.bottom=-half;camera.left=-half*aspect;camera.right=half*aspect;
  camera.updateProjectionMatrix();
}
function cameraAt(name){
  currentView=name;
  const target=orbit.target.clone();
  const radius=knownBounds?knownBounds.getSize(V()).length():2;
  const dir=new THREE.Vector3(...views[name]).normalize();
  camera.position.copy(target).addScaledVector(dir,Math.max(5,radius*3));
  camera.up.set(0,1,0);camera.near=.01;camera.far=Math.max(100,radius*20);
  camera.lookAt(target);camera.updateProjectionMatrix();orbit.update();
}
function fitCamera(){
  knownBounds=measuredBounds();
  const center=knownBounds.getCenter(V()),size=knownBounds.getSize(V());
  const width=Math.max(300,$('stage').clientWidth),height=Math.max(320,Math.min(720,Math.round(width*.78)));
  const aspect=width/height;
  fitHeight=Math.max(.25,Math.max(size.y,size.x/aspect,size.z/aspect)*1.35);
  orbit.target.copy(center);
  lastActorPosition=actor.position.clone();
  resize();cameraAt(currentView);
  camera.zoom=1;camera.updateProjectionMatrix();orbit.saveState();
  $('cameraInfo').textContent='Camera fit · skinned extents '+size.toArray().map(n=>n.toFixed(2)).join(' × ')+' · near '+camera.near+' · far '+camera.far;
}
function follow(){
  if(!actor||!followEnabled)return;
  if(!lastActorPosition){lastActorPosition=actor.position.clone();return;}
  const delta=actor.position.clone().sub(lastActorPosition);
  orbit.target.add(delta);camera.position.add(delta);lastActorPosition.copy(actor.position);
}
window.addEventListener('resize',resize);resize();
'''
s=s[:start]+camera+s[end:]
replace('cameraAt(currentView);\nconst wpos=', 'const wpos=')
replace("function reset(){cycles=0;worldX=0;resetContact();if(ready){redraw();cameraAt('front');}}", "function reset(){cycles=0;worldX=0;resetContact();if(ready){lastActorPosition=actor.position.clone();redraw();}}")
replace("for(const key of Object.keys(views))$(key).onclick=()=>cameraAt(key);", """for(const key of Object.keys(views))$(key).onclick=()=>cameraAt(key);
$('fit').onclick=()=>{if(ready)fitCamera();};
$('follow').onclick=()=>{followEnabled=!followEnabled;$('follow').textContent=followEnabled?'Follow: on':'Follow: off';lastActorPosition=actor?.position.clone()||null;};""")
replace("ready=true;reset();sourceAt(0);source.visible=false;actor.visible=true;", "ready=true;reset();sourceAt(0);source.visible=false;actor.visible=true;fitCamera();")
replace("$('identity').textContent=`v0.1.26", "$('identity').textContent=`v0.1.28 camera rescue · gait from v0.1.26")
replace("status('TRUE LEFT CLIP DERIVED · GENERATED 74-BONE PROCEDURAL GAIT ACTIVE · IK ankle pin audit PENDING');", "status('CAMERA RESTORED · SKINNED MESH FIT · PROCEDURAL LEFT GAIT UNCHANGED · OWNER REVIEW PENDING');")
p.write_text(s)
old='<div class="bar" role="group" aria-label="Camera orbit presets"><strong>Orbit:</strong><button id="front">Front</button><button id="side">Side</button><button id="oblique">Three-quarter</button><button id="top">Top</button><span>Drag orbit · pinch zoom · follow actor</span></div>'
new='<div class="bar" role="group" aria-label="Camera orbit presets"><strong>Camera:</strong><button id="front">Front</button><button id="side">Side</button><button id="oblique">Three-quarter</button><button id="top">Top</button><button id="fit">Fit model</button><button id="follow">Follow: on</button><span>Drag orbit · pinch zoom · two fingers pan · camera persists through gait reset</span><output id="cameraInfo" class="small" aria-live="polite">Camera fitting after GLB loads</output></div>'
if html.count(old)!=1:raise SystemExit('BLOCKED_HTML_CAMERA_ANCHOR')
html=html.replace(old,new).replace('v0.1.26 · real source clips · one visible rig','v0.1.28 · camera repaired · gait unchanged').replace('<title>Hareworks v0.1.26','<title>Hareworks v0.1.28').replace('v0.1.26-real-left-source-procedural-ik','v0.1.28-camera-recovery')
h.write_text(html)
print('CAMERA_ONLY_PATCH_PASS')
PY
cat > "$NEW/CAMERA_RECOVERY.md" <<'MD'
# Hareworks v0.1.28 camera-only recovery

Source: v0.1.26 on main commit 0b0c2ee6df4d697844e231247d0c6c25550a1293.
The viewer is derived from unchanged v0.1.26. No gait math, source calibration, IK, model, protected older version, or animation tracks changed.
The prior camera disabled pan, fixed an undersized/poorly framed orthographic viewport, and reset orientation when the gait reset. This revision derives bounds from the actual posed SkinnedMesh vertices, fits orthographic extents, points the camera outside the character and restores pan/orbit/zoom with explicit Fit/Follow controls.
Actual phone rendering and owner acceptance remain pending until the Termux campaign publishes and the owner sees the viewer.
MD
STAGE=checks
node --check "$NEW/viewer.mjs";node --check "$NEW/left-contact.mjs";node --check "$NEW/sidestep-core.mjs"
python3 - "$OLD" "$NEW" <<'PY'
from pathlib import Path
import hashlib,sys
old,new=map(Path,sys.argv[1:]); previous={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in old.iterdir() if p.is_file()}
current={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in new.iterdir() if p.is_file()}
changed={n for n in previous if previous[n]!=current.get(n)}
assert changed=={'viewer.mjs','index.html'},changed
for n in ['sidestep-core.mjs','left-contact.mjs','sidestep-core-test.mjs','left-contact-test.mjs']:
 assert previous[n]==current[n],n
s=(new/'viewer.mjs').read_text();h=(new/'index.html').read_text()
for token in ['orbit.enablePan=true','function fitCamera()','function measuredBounds()','function follow()','lastActorPosition','CAMERA RESTORED','cameraInfo']:
 assert token in (s+h),token
assert "cameraAt('front');" not in s
assert s.index('let source=null,actor=null,') < s.index('ready=true;reset();'), 'actor declared before initialization'
assert 'const dir=new THREE.Vector3(...views[name]).normalize();' in s
assert 'camera.position.copy(target).addScaledVector(dir,' in s
assert 'cameraAt(currentView);\nconst wpos=' not in s, 'TDZ startup regression'
assert 'CAMERA RESTORED' in s
assert 'HAREWORKS_CAMERA_RECOVERY_v0.1.28' in s
assert (new/'campaign-v0.1.28-camera-recovery.sh').is_file()
print('CAMERA_NO_GAIT_REGRESSION_PASS modified=viewer.mjs,index.html')
PY
node "$NEW/sidestep-core-test.mjs"
node "$NEW/left-contact-test.mjs"
STAGE=prepublish
python3 - "$MODEL" "$NEW" <<'PY'
import subprocess,sys
model,destination=sys.argv[1:]
for raw in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).split(b'\0'):
 if not raw:continue
 s=raw.decode('utf-8','surrogateescape')
 if s==' M '+model:continue
 if s.startswith('?? '+destination+'/'):continue
 if s.startswith('?? tools/hareworks-forward-woman/v0.1.27/'):continue
 raise SystemExit('BLOCKED_UNEXPECTED_CHANGE '+repr(s))
PY
STAGE=commit
git add -- "$NEW"
[ -z "$(git diff --cached --name-only | grep -v "^$NEW/")" ] || { echo BLOCKED_STAGING_SCOPE;exit 77; }
git -c user.name="Hareworks Termux Campaign" -c user.email="hareworks-campaign@users.noreply.github.com" commit -m 'Hareworks v0.1.28 restore skinned camera fit orbit pan and zoom'
NEWCOMMIT="$(git rev-parse HEAD)"
STAGE=push
git push origin HEAD:refs/heads/main
STAGE=remote-readback
REMOTE_AFTER="$(timeout 40 git ls-remote "$REPO" refs/heads/main | cut -f1)"
[ "$REMOTE_AFTER" = "$NEWCOMMIT" ] || { echo "BLOCKED_REMOTE_READBACK actual=$REMOTE_AFTER expected=$NEWCOMMIT";exit 79; }
STAGE=launch-review
READY="$STATE/server-ready.json"; rm -f "$READY"
nohup python3 "$NEW/review-server.py" "$CHECKOUT" "$READY" "$STATE" </dev/null >> "$STATE/review-server.log" 2>&1 &
PID=$!
for k in $(seq 1 40);do [ -s "$READY" ] && break;sleep .25;done
[ -s "$READY" ] && kill -0 "$PID" 2>/dev/null || { echo BLOCKED_REVIEW_SERVER;exit 80; }
PORT="$(python3 - "$READY" <<'PYPORT'
import json,sys
print(json.load(open(sys.argv[1]))['port'])
PYPORT
)"
URL="http://127.0.0.1:$PORT/$NEW/index.html?commit=$NEWCOMMIT&scriptSha=$SCRIPT_SHA"
for f in viewer.mjs index.html left-contact.mjs sidestep-core.mjs;do
 LIVE_SHA="$(curl -fsS "http://127.0.0.1:$PORT/$NEW/$f" | sha256sum | cut -d' ' -f1)"
 DISK_SHA="$(sha256sum "$NEW/$f" | cut -d' ' -f1)"
 [ "$LIVE_SHA" = "$DISK_SHA" ] || { echo "BLOCKED_HTTP_ASSET_HASH=$f";exit 80; }
done
STAGE=published
printf 'REMOTE_READBACK_PASS=%s\nVIEWER_URL=%s\nVIEWER_PID=%s\nOWNER_VISUAL_ACCEPTED=false\n' "$NEWCOMMIT" "$URL" "$PID"
if command -v termux-open-url >/dev/null 2>&1;then termux-open-url "$URL" || true;fi
