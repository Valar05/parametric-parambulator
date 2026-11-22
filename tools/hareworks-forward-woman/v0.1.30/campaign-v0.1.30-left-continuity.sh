#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_LEFT_CONTINUITY_v0.1.30 — continuity-only; Termux Git owns mutation.
set -Eeuo pipefail
umask 077
CAMPAIGN=HAREWORKS_LEFT_CONTINUITY_v0.1.30
REPO=https://github.com/Valar05/parametric-parambulator.git
BASE=3e7a5647665b35847a6040b6b1e7b8be266e14a1
OLD=tools/hareworks-forward-woman/v0.1.28
NEW=tools/hareworks-forward-woman/v0.1.30
CHECKOUT="$HOME/storage/documents/GodotProjects/parametric-parambulator"
STATE="$HOME/.local/state/hareworks-left-continuity-v0.1.30"
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
  if [ "$HEAD" = "$LIVE" ] && [ -f "$NEW/viewer.mjs" ] && grep -Fq 'HAREWORKS_LEFT_CONTINUITY_v0.1.30' "$NEW/viewer.mjs";then
    STAGE=already-published; NEWCOMMIT="$HEAD"; echo "ALREADY_PUBLISHED_REMOTE=$HEAD";exit 0
  fi
  # A previously committed but unpushed continuity version can be resumed safely.
  if [ "$LIVE" = "$BASE" ] && [ "$(git rev-list --parents -n1 "$HEAD" | awk '{print $2}')" = "$BASE" ] && [ -f "$NEW/viewer.mjs" ] && [ "$(git diff-tree --no-commit-id --name-only -r "$HEAD" | grep -v "^$NEW/" | wc -l)" -eq 0 ];then
    STAGE=resume-push; NEWCOMMIT="$HEAD"; git push origin HEAD:refs/heads/main
    [ "$(timeout 40 git ls-remote "$REPO" refs/heads/main | cut -f1)" = "$NEWCOMMIT" ] || { echo BLOCKED_REMOTE_READBACK;exit 79; }
    STAGE=published;echo "REMOTE_READBACK_PASS=$NEWCOMMIT";exit 0
  fi
  echo "BLOCKED_REMOTE_OR_CHECKOUT_DRIFT local=$HEAD remote=$LIVE expected=$BASE";exit 73
fi
STAGE=rules-and-source
[ "$(git hash-object AGENTS.md)" = 547c2af52303f4efb718bbf8f82a698110c7bfca ] || { echo BLOCKED_AGENTS_CHANGED;exit 74; }
[ "$(git hash-object "$OLD/viewer.mjs")" = 21ee10d9861b407dc1dae0e0ef09fed0c9de6677 ] || { echo BLOCKED_V028_VIEWER_CHANGED;exit 74; }
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
 if s.startswith('?? tools/hareworks-forward-woman/v0.1.29/'):continue
 raise SystemExit('BLOCKED_DIRTY_WORKTREE '+repr(s))
if subprocess.run(['git','diff','--cached','--quiet']).returncode:raise SystemExit('BLOCKED_STAGED_CHANGES')
print('CLEAN_SCOPE_PASS')
PY
STAGE=build
cp -R "$OLD" "$NEW"
cp "$(readlink -f "${BASH_SOURCE[0]}")" "$NEW/campaign-v0.1.30-left-continuity.sh"
python3 - "$NEW/viewer.mjs" "$NEW/index.html" <<'PATCH'
from pathlib import Path
import sys
p,h=map(Path,sys.argv[1:]); s=p.read_text(); html=h.read_text()
def replace(old,new):
 global s
 n=s.count(old)
 if n!=1:raise SystemExit('BLOCKED_PATCH_ANCHOR '+str(n)+' '+old[:65])
 s=s.replace(old,new)
# Keep original source-calibrated pose, 74-bone source parity and camera.
replace("const status=x=>$('status').textContent=x;", """const status=x=>$('status').textContent=x;
// HAREWORKS_LEFT_CONTINUITY_v0.1.30. Soft IK fades, source pose unchanged.
import {stanceWeight,correctionWeight} from './continuity-core.mjs';""")
start=s.index('function applyIK(side,target){')
end=s.index('function poseProcedural(',start)
s=s[:start]+"""function applyIK(side,target,stanceBlend){
 const [un,kn,fn]=limbs[side],up=actorRig[un],knee=actorRig[kn],foot=actorRig[fn];
 const H=wpos(up),K=wpos(knee),A=wpos(foot),delta=A.distanceTo(target);
 maxContactError=Math.max(maxContactError,delta);
 // Full source pose stays authoritative. Gain goes to zero BEFORE the old hard
 // correction and knee limits; no branch may suddenly replace a large IK pose.
 if(stanceBlend<=0||delta<1e-7)return false;
 let gain=stanceBlend*correctionWeight(delta,CONTACT_MAX_CORRECTION);
 // Taper correction near both two-link reach limits, before validity flips.
 const l1=H.distanceTo(K),l2=K.distanceTo(A),reach=H.distanceTo(target);
 const reachMargin=Math.min(l1+l2-reach,reach-Math.abs(l1-l2));
 gain*=Math.max(0,Math.min(1,reachMargin/.025));
 if(gain<1e-6)return false;
 const full=projectedSourceKnee(H.toArray(),K.toArray(),A.toArray(),target.toArray());
 if(!full.valid){lastFailure='SOURCE_IK_REACH_'+side;return false;}
 gain*=correctionWeight(full.sourceKneeDisplacement,KNEE_MAX_CORRECTION);
 if(gain<1e-6)return false;
 const blended=A.clone().lerp(target,gain);
 const ik=projectedSourceKnee(H.toArray(),K.toArray(),A.toArray(),blended.toArray());
 if(!ik.valid){lastFailure='SOURCE_IK_BLENDED_REACH_'+side;return false;}
 const footQ=wq(foot).clone();
 // Stance and feasibility smoothness are expressed as an ankle target in world
 // coordinates; source knee bending direction and foot orientation are retained.
 aimJoint(up,K,V(...ik.knee));actor.updateMatrixWorld(true);
 aimJoint(knee,wpos(foot),blended);actor.updateMatrixWorld(true);
 setWorldQ(foot,footQ);actor.updateMatrixWorld(true);
 maxKneeShift=Math.max(maxKneeShift,ik.sourceKneeDisplacement);
 return true;
}
""" + s[end:]
replace('let settled=confidence?applyIK(side,entry.world):false;', 'let settled=confidence?applyIK(side,entry.world,stanceWeight(p,sourceContacts[side])):false;')
replace("mode==='procedural'", "mode==='procedural'") if False else None
replace("status(mode==='source'?'ORIGINAL IN-PLACE LEFT CLIP: SOURCE ANIMATION REFERENCE':'PROCEDURAL LEFT: MATHEMATICAL 74-BONE GAIT + WORLD-X CONTACT IK');", "status(mode==='source'?'ORIGINAL LEFT SOURCE':mode==='raw'?'GENERATED LEFT: IK DISABLED FOR DIAGNOSIS':'GENERATED LEFT: SOFT ANKLE IK · SOURCE GAIT UNCHANGED');")
replace("$('identity').textContent=`v0.1.28 camera rescue", "$('identity').textContent=`v0.1.30 continuous IK · preserved v0.1.28 camera")
html=html.replace('<title>Hareworks v0.1.28', '<title>Hareworks v0.1.30').replace('v0.1.28 · camera repaired · gait unchanged','v0.1.30 · contact transitions softened · camera retained').replace('v0.1.28-camera-recovery','v0.1.30-left-continuity')
old='<option value="procedural">Generated procedural left (default)</option><option value="source">Original source clip (comparison only)</option>'
new='<option value="procedural">Generated left + softened IK (default)</option><option value="raw">Generated left WITHOUT IK (diagnostic)</option><option value="source">Original source clip (comparison only)</option>'
if html.count(old)!=1:raise SystemExit('BLOCKED_MODE_HTML_ANCHOR')
html=html.replace(old,new)
p.write_text(s);h.write_text(html)
print('CONTINUITY_PATCH_PASS')
PATCH
cat > "$NEW/continuity-core.mjs" <<'JS'
// Smooth input gain for source-derived ankle pinning. No side effects.
export const clamp01=x=>Math.max(0,Math.min(1,x));
export const smoothstep=x=>{const t=clamp01(x);return t*t*(3-2*t);};
export function stanceWeight(phase,window){
 if(!Number.isFinite(phase)||!window||!(window.duty>0&&window.duty<1))throw Error('INVALID_STANCE_WINDOW');
 const q=((phase-window.start)%1+1)%1;
 if(q>=window.duty)return 0;
 const ramp=Math.min(window.duty*.24,.12);
 return smoothstep(q/ramp)*smoothstep((window.duty-q)/ramp);
}
export function correctionWeight(distance,maximum){
 if(!Number.isFinite(distance)||!(maximum>0))throw Error('INVALID_CORRECTION');
 // Fade BEFORE threshold: 65% -> 100% of the established hard envelope.
 return 1-smoothstep((distance/maximum-.65)/.35);
}
JS
cat > "$NEW/continuity-core-test.mjs" <<'JS'
import assert from 'node:assert/strict';
import {stanceWeight,correctionWeight} from './continuity-core.mjs';
for(const start of [.03,.4,.93]){
 const window={start,duty:.46};
 const w=(t)=>stanceWeight((start+t+1)%1,window);
 assert(w(0)<1e-9);assert(w(.46)<1e-9);assert(w(.23)>.99);
 for(const edge of [0,.46])assert(Math.abs(w(edge+1e-6)-w(edge-1e-6))<.000001);
 let maxJump=0;for(let i=1;i<=10000;i++)maxJump=Math.max(maxJump,Math.abs(w(i/10000)-w((i-1)/10000)));
 assert(maxJump<.002,maxJump);
}
for(const limit of [.035,.085]){
 assert.equal(correctionWeight(0,limit),1);
 assert.equal(correctionWeight(limit,limit),0);
 for(let i=1;i<=10000;i++)assert(Math.abs(correctionWeight(i/10000*limit,limit)-correctionWeight((i-1)/10000*limit,limit))<.002);
}
console.log('CONTACT_TRANSITION_C0_CONTINUITY_PASS');
JS
cat > "$NEW/CONTINUITY_RECOVERY.md" <<'MD'
# v0.1.30 left gait contact continuity

Based exactly on published v0.1.28. Change only the procedural viewer and UI, plus this new pure mathematical helper, its test and campaign. Original source reconstruction core, all GLB files, prior viewers, camera functions and original source animation untouched.

The former IK implementation applied full correction instantly during a stance window, then removed it at lift-off, and refused large corrections at thresholds. This patch fades both stance contact and correction envelopes using continuous smoothstep curves, preserving source knee plane and original foot orientation. Added a generated-without-IK diagnostic for isolating source seam behavior. No claim of proven mesh-space contact physics or human acceptance. Source parity before IK remains unchanged.
MD
STAGE=checks
node --check "$NEW/viewer.mjs"
node --check "$NEW/continuity-core.mjs"
node "$NEW/continuity-core-test.mjs"
node "$NEW/sidestep-core-test.mjs"
node "$NEW/left-contact-test.mjs"
python3 - "$OLD" "$NEW" <<'TEST'
from pathlib import Path
import hashlib,sys
old,new=map(Path,sys.argv[1:])
a={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in old.iterdir() if p.is_file()}
b={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in new.iterdir() if p.is_file()}
changed={n for n in a if a[n]!=b.get(n)}
assert changed=={'viewer.mjs','index.html'},changed
for name in ['sidestep-core.mjs','left-contact.mjs','review-server.py','source-witness.json']:
 assert a[name]==b[name],name
s=(new/'viewer.mjs').read_text();h=(new/'index.html').read_text()
assert 'function fitCamera()' in s and 'orbit.enablePan=true' in s
assert 'stanceWeight(p,sourceContacts[side])' in s
assert 'correctionWeight(full.sourceKneeDisplacement,KNEE_MAX_CORRECTION)' in s
assert "mode==='procedural'" in s and 'value="raw"' in h
assert 'HAREWORKS_LEFT_CONTINUITY_v0.1.30' in s
assert (new/'campaign-v0.1.30-left-continuity.sh').exists()
print('PRESERVED_MODEL_GAIT_CAMERA_CONTRACT_PASS')
TEST
STAGE=prepublish
python3 - "$MODEL" "$NEW" <<'GUARD'
import subprocess,sys
model,destination=sys.argv[1:]
for raw in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).split(b'\0'):
 if not raw:continue
 s=raw.decode('utf-8','surrogateescape')
 if s==' M '+model:continue
 if s.startswith('?? '+destination+'/'):continue
 if s.startswith('?? tools/hareworks-forward-woman/v0.1.27/'):continue
 if s.startswith('?? tools/hareworks-forward-woman/v0.1.29/'):continue
 raise SystemExit('BLOCKED_UNEXPECTED_CHANGE '+repr(s))
GUARD
STAGE=commit
git add -- "$NEW"
[ -z "$(git diff --cached --name-only | grep -v "^$NEW/")" ] || { echo BLOCKED_STAGING_SCOPE;exit 77; }
git -c user.name="Hareworks Termux Campaign" -c user.email="hareworks-campaign@users.noreply.github.com" commit -m 'Hareworks v0.1.30 smooth ankle contact transitions without gait/camera regressions'
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
PORT="$(python3 - "$READY" <<'P'
import json,sys
print(json.load(open(sys.argv[1]))['port'])
P
)"
URL="http://127.0.0.1:$PORT/$NEW/index.html?commit=$NEWCOMMIT&scriptSha=$SCRIPT_SHA"
for f in viewer.mjs index.html continuity-core.mjs left-contact.mjs sidestep-core.mjs;do
 LIVE_SHA="$(curl -fsS "http://127.0.0.1:$PORT/$NEW/$f" | sha256sum | cut -d' ' -f1)"
 DISK_SHA="$(sha256sum "$NEW/$f" | cut -d' ' -f1)"
 [ "$LIVE_SHA" = "$DISK_SHA" ] || { echo "BLOCKED_HTTP_ASSET_HASH=$f";exit 80; }
done
STAGE=published
printf 'REMOTE_READBACK_PASS=%s\nVIEWER_URL=%s\nOWNER_VISUAL_ACCEPTED=false\n' "$NEWCOMMIT" "$URL"
if command -v termux-open-url >/dev/null 2>&1;then termux-open-url "$URL" || true;fi
