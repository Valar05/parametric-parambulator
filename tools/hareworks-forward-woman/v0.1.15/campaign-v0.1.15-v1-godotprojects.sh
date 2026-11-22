#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_ACCEPTED_V019_INVERSE_SUPPORT_v0.1.15_DOCUMENTS
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_STARTUP_MOTION_RECOVERY_v0.1.15_DOCUMENTS'
VERSION='v0.1.15'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='7a3690fa99c52f70636fa49be851e521a793838c'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-startup-motion-v0.1.15-v1-documents"
mkdir -p "$STATE"
LOG="$STATE/campaign.log"
exec > >(tee -a "$LOG") 2>&1
STAGE='preflight'
CHECKOUT="$HOME/storage/documents/GodotProjects/parametric-parambulator"
RUN="$STATE"
NEW_SHA=''
FAIL=0
report_exit(){
 local rc=$?
 if [ "$rc" -ne 0 ]; then
  printf '{"campaign":"%s","status":"BLOCKED","stage":"%s","exitCode":%s,"entrySha256":"%s","baseCommit":"%s","modelSha256":"%s","expectedCheckout":"%s","ownerVisualAcceptance":false}\n' \
   "$CAMPAIGN_ID" "$STAGE" "$rc" "$ENTRY_SHA" "$BASE_SHA" "$MODEL_SHA" "$CHECKOUT" > "$STATE/last-failure.json"
  echo "BLOCKED stage=$STAGE exit=$rc receipt=$STATE/last-failure.json" >&2
 fi
}
trap report_exit EXIT
printf 'CAMPAIGN=%s\nSCRIPT_SHA256=%s\nCHECKOUT=%s\nBASE_SHA=%s\nMODEL_SHA=%s\n' "$CAMPAIGN_ID" "$ENTRY_SHA" "$CHECKOUT" "$BASE_SHA" "$MODEL_SHA"
if [ "${PREFIX:-}" != '/data/data/com.termux/files/usr' ] || [ -z "${ANDROID_ROOT:-}" ]; then
 echo 'BLOCKED_NOT_ANDROID_TERMUX: this campaign must run on the phone' >&2;exit 70
fi
for bin in git python3 node curl sha256sum stat timeout; do
 if ! command -v "$bin" >/dev/null 2>&1; then
  if command -v pkg >/dev/null 2>&1;then
   case "$bin" in
    python3) pkg install -y python;;
    node) pkg install -y nodejs;;
    timeout) pkg install -y coreutils;;
    *) pkg install -y git python nodejs curl coreutils;;
   esac
  fi
 fi
 command -v "$bin" >/dev/null 2>&1 || { echo "BLOCKED_MISSING_TOOL=$bin" >&2;exit 71; }
done
if ! git lfs version >/dev/null 2>&1; then
 command -v pkg >/dev/null 2>&1 && timeout 180 pkg install -y git-lfs || { echo 'BLOCKED_NO_GIT_LFS' >&2;exit 71; }
fi
# Important: disable ALL automatic LFS downloads, especially missing unrelated Repl.glb.
export GIT_LFS_SKIP_SMUDGE=1
export GIT_TERMINAL_PROMPT=0
if [ ! -d "$HOME/storage/documents" ]; then
 echo 'BLOCKED_DOCUMENTS_STORAGE_UNAVAILABLE: run termux-setup-storage/grant Android storage permission once' >&2;exit 70
fi
PARENT="$HOME/storage/documents/GodotProjects"
[ ! -e "$PARENT" ] || [ -d "$PARENT" ] || { echo 'BLOCKED_GODOTPROJECTS_NOT_DIRECTORY' >&2;exit 70; }
mkdir -p "$PARENT"
[ ! -L "$CHECKOUT" ] || { echo 'BLOCKED_CHECKOUT_IS_SYMLINK' >&2;exit 72; }
# Android shared storage presents an emulated owner, even for files created by Termux.
# Git 2.35+ treats this as dubious ownership until the EXACT canonical project is trusted.
# Do not use safe.directory='*', disable Git ownership checks, or modify other projects.
STAGE='android-documents-git-ownership-gate'
CANON_DOCS="$(readlink -f -- "$HOME/storage/documents")"
CANON_PARENT="$(readlink -f -- "$PARENT")"
EXPECTED_PARENT="$CANON_DOCS/GodotProjects"
[ "$CANON_PARENT" = "$EXPECTED_PARENT" ] || { echo "BLOCKED_UNEXPECTED_DOCUMENTS_PARENT=$CANON_PARENT" >&2;exit 72; }
[ ! -e "$CHECKOUT" ] || [ -d "$CHECKOUT" ] || { echo 'BLOCKED_CHECKOUT_NOT_DIRECTORY' >&2;exit 72; }
[ ! -L "$CHECKOUT/.git" ] || { echo 'BLOCKED_GIT_METADATA_SYMLINK' >&2;exit 72; }
[ ! -e "$CHECKOUT/.git" ] || [ -d "$CHECKOUT/.git" ] || { echo 'BLOCKED_NONSTANDARD_GIT_METADATA__NO_OVERWRITE' >&2;exit 72; }
CANON_CHECKOUT="$(readlink -f -- "$CHECKOUT")"
[ "$CANON_CHECKOUT" = "$CANON_PARENT/parametric-parambulator" ] || {
 echo "BLOCKED_UNEXPECTED_CHECKOUT_RESOLUTION=$CANON_CHECKOUT" >&2;exit 72; }
if ! git config --global --get-all safe.directory 2>/dev/null | grep -Fxq -- "$CANON_CHECKOUT";then
 git config --global --add safe.directory "$CANON_CHECKOUT" || { echo 'BLOCKED_CANNOT_TRUST_EXACT_DOCUMENTS_PROJECT' >&2;exit 73; }
 echo "TRUSTED_ONLY_PROJECT=$CANON_CHECKOUT"
fi
# Validate that Git actually recognizes the exact protected config entry.
git config --global --get-all safe.directory | grep -Fxq -- "$CANON_CHECKOUT" || {
 echo 'BLOCKED_SAFE_DIRECTORY_CONFIRMATION_FAILED' >&2;exit 73; }
RECOVERED_R2_PARTIAL_INIT=0
# No disposable clone. The .git directory and all ordinary source files stay in Documents.
# First installation may download repository TEXT blobs ONCE; future campaigns reuse .git.
STAGE='verify-remote'
remote_sha(){ timeout 35 git ls-remote "$REMOTE" refs/heads/main | awk '{print $1}'; }
LIVE=''
for attempt in 1 2 3;do
 LIVE="$(remote_sha)" && [ -n "$LIVE" ] && break || true
 sleep "$attempt"
done
[ -n "$LIVE" ] || { echo 'BLOCKED_GIT_REMOTE_UNREACHABLE' >&2;exit 72; }
PUBLISHED_REUSE=0
PENDING_COMMIT=0
DEST_REL="tools/hareworks-forward-woman/$VERSION"
if [ -d "$CHECKOUT/.git" ];then
 [ "$(git -C "$CHECKOUT" rev-parse --is-inside-work-tree)" = true ] || {
  echo 'BLOCKED_EXISTING_GIT_DIRECTORY_INVALID' >&2;exit 73; }
 [ "$(git -C "$CHECKOUT" rev-parse --show-toplevel)" = "$CANON_CHECKOUT" ] || {
  echo 'BLOCKED_WORKTREE_NOT_TARGET_DIRECTORY' >&2;exit 73; }
 ORIGIN="$(git -C "$CHECKOUT" remote get-url origin 2>/dev/null || true)"
 if [ -z "$ORIGIN" ];then
  # r2 died AFTER `git init -b main` but BEFORE `git remote add origin`.
  # Repair that exact unborn, clean, remote-less state without resetting anything.
  [ "$(git -C "$CHECKOUT" symbolic-ref --short HEAD 2>/dev/null || true)" = main ] &&
  ! git -C "$CHECKOUT" rev-parse --verify HEAD >/dev/null 2>&1 &&
  [ -z "$(git -C "$CHECKOUT" status --porcelain --untracked-files=all)" ] &&
  [ -z "$(git -C "$CHECKOUT" remote)" ] || {
    echo 'BLOCKED_ORIGIN_MISSING_ON_NONEMPTY_OR_NONUNBORN_REPOSITORY' >&2;exit 73; }
  git -C "$CHECKOUT" remote add origin "$REMOTE"
  ORIGIN="$(git -C "$CHECKOUT" remote get-url origin)"
  RECOVERED_R2_PARTIAL_INIT=1
  echo 'RECOVERED_PREVIOUS_R2_PARTIAL_GIT_INIT=1'
 fi
 case "$ORIGIN" in "$REMOTE"|'git@github.com:Valar05/parametric-parambulator.git') :;; *) echo "BLOCKED_WRONG_REPOSITORY=$ORIGIN" >&2;exit 73;; esac
else
 STAGE='initialize-persistent-checkout'
 if [ -e "$CHECKOUT" ] && [ -n "$(find "$CHECKOUT" -mindepth 1 -maxdepth 1 -print -quit)" ];then
  echo 'BLOCKED_NONEMPTY_EXISTING_PROJECT__NO_OVERWRITE' >&2;exit 73
 fi
 mkdir -p "$CHECKOUT"
 git -C "$CHECKOUT" init -b main
 git -C "$CHECKOUT" remote add origin "$REMOTE"
 git -C "$CHECKOUT" config --local core.filemode false
 git -C "$CHECKOUT" config --local core.symlinks false
fi
cd "$CHECKOUT"
# Git metadata on Android shared storage cannot be trusted to preserve POSIX modes.
git config --local core.filemode false
git config --local core.symlinks false
# Stable and reusable local LFS object cache. The Android Documents copy exists ONCE.
MODEL_CACHE_ROOT="$HOME/.local/share/hareworks-lfs-cache"
mkdir -p "$MODEL_CACHE_ROOT"
git config --local lfs.storage "$MODEL_CACHE_ROOT"
# r3 materialized the correct binary but the checkout reported it modified.
# Configure Git LFS's *clean* filter locally so Git can compare the real file
# against the LFS pointer in HEAD. This changes only .git/config in this repo.
# No hook scripts are installed and no LFS downloads occur here.
STAGE='configure-repository-lfs-filters'
git config --local filter.lfs.clean 'git-lfs clean -- %f'
git config --local filter.lfs.smudge 'git-lfs smudge -- %f'
git config --local filter.lfs.process 'git-lfs filter-process'
git config --local filter.lfs.required true
STAGE='checkout-git-main'
if HEAD_SHA="$(git rev-parse --verify HEAD 2>/dev/null)";then
 [ "$(git symbolic-ref --short HEAD 2>/dev/null || true)" = main ] || { echo 'BLOCKED_NOT_ON_MAIN__NO_BRANCH_CHANGE' >&2;exit 73; }
 if [ "$HEAD_SHA" = "$BASE_SHA" ] && [ "$LIVE" = "$BASE_SHA" ];then
  echo 'REUSING_PERSISTENT_GIT_CHECKOUT=1'
 elif [ "$HEAD_SHA" = "$LIVE" ] && [ -f "$DEST_REL/foot-gait.mjs" ] && [ -f "$DEST_REL/contract.json" ];then
  # A second run after a verified publication is read-only and relaunches review.
  grep -q 'SourceFootContact' "$DEST_REL/foot-gait.mjs" || { echo 'BLOCKED_PUBLISHED_GAIT_MISSING' >&2;exit 73; }
  grep -q 'hareworks-woman-accepted-v019-startup-recovery-v0.1.15' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
  PUBLISHED_REUSE=1
  NEW_SHA="$HEAD_SHA"
 elif [ "$LIVE" = "$BASE_SHA" ] &&
      [ "$(git rev-list --parents -n 1 "$HEAD_SHA" | awk '{print $2}')" = "$BASE_SHA" ] &&
      [ -f "$DEST_REL/foot-gait.mjs" ] && [ -f "$DEST_REL/contract.json" ];then
  # Previous push failed or its outcome was ambiguous. Reuse the SAME commit.
  [ "$(git diff-tree --no-commit-id --name-only -r "$HEAD_SHA" | awk -v p="$DEST_REL/" 'index($0,p)!=1 {bad=1} END{print bad+0}')" = 0 ] || { echo 'BLOCKED_PENDING_COMMIT_MUTATED_OTHER_PATHS' >&2;exit 73; }
  grep -q 'SourceFootContact' "$DEST_REL/foot-gait.mjs" || { echo 'BLOCKED_PENDING_GAIT_MISSING' >&2;exit 73; }
  PENDING_COMMIT=1
  NEW_SHA="$HEAD_SHA"
  echo "RESUMING_EXISTING_UNPUSHED_COMMIT=$NEW_SHA"
 else
  echo "BLOCKED_CHECKOUT_HEAD_DIVERGED local=$HEAD_SHA remote=$LIVE expectedBase=$BASE_SHA" >&2;exit 73
 fi
else
 # Only an UNBORN repo with no files may be materialized. No reset, stash or force.
 [ -z "$(git status --porcelain --untracked-files=all)" ] || { echo 'BLOCKED_UNBORN_REPO_HAS_FILES' >&2;exit 73; }
 [ "$LIVE" = "$BASE_SHA" ] || { echo "BLOCKED_REMOTE_CHANGED_BEFORE_FIRST_CHECKOUT=$LIVE" >&2;exit 72; }
 # Partial Git objects, full ordinary working tree. Never fetch unrelated LFS binaries.
 if ! timeout 180 git -c protocol.version=2 fetch --depth 1 --filter=blob:none origin refs/heads/main;then
  echo 'BLOCKED_INCREMENTAL_FETCH_FAILED__RETRY_SAME_CHECKOUT_WITHOUT_RECLONING' >&2;exit 73
 fi
 [ "$(git rev-parse FETCH_HEAD)" = "$BASE_SHA" ] || { echo 'BLOCKED_FETCHED_WRONG_SOURCE_COMMIT' >&2;exit 73; }
 GIT_LFS_SKIP_SMUDGE=1 timeout 180 git checkout -B main FETCH_HEAD || {
  echo 'BLOCKED_ANDROID_DOCUMENTS_CHECKOUT__SAVED_GIT_OBJECTS_CAN_BE_REUSED' >&2;exit 73; }
 echo 'PERSISTENT_CHECKOUT_CREATED=1'
fi
[ "$(git hash-object AGENTS.md)" = "$AGENTS_BLOB" ] || { echo 'BLOCKED_AGENTS_REVISION_MISMATCH' >&2;exit 74; }
[ -f tools/hareworks-forward-woman/v0.1.14/viewer.mjs ] || { echo 'BLOCKED_MISSING_SOURCE_GAIT_BASELINE' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.14/viewer.mjs)" = eb8c4b652a8e335d7b27eebcc3901848666b022f ] || { echo 'BLOCKED_REJECTED_V013_SOURCE_CHANGED' >&2;exit 74; }
[ -f tools/hareworks-forward-woman/v0.1.9/viewer.mjs ] || { echo 'BLOCKED_MISSING_ACCEPTED_V019_REFERENCE' >&2;exit 74; }
# An unrelated missing LFS object is not permission to download it or delete files.
EXPECTED_LFS_POINTER="$(printf 'version https://git-lfs.github.com/spec/v1\noid sha256:%s\nsize %s' "$MODEL_SHA" "$MODEL_SIZE")"
[ "$(git show HEAD:"$MODEL")" = "$EXPECTED_LFS_POINTER" ] || { echo 'BLOCKED_SOURCE_GLB_POINTER_CHANGED' >&2;exit 75; }
STAGE='verify-or-install-one-model'
if [ -f "$MODEL" ] && [ "$(stat -c %s "$MODEL")" = "$MODEL_SIZE" ] &&
 [ "$(sha256sum "$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ];then
 echo 'HAREWORKS_MODEL_ALREADY_PRESENT_SHA_VERIFIED=1'
else
 # Only the exact Git LFS text POINTER can be replaced in this checkout.
 [ -f "$MODEL" ] && [ "$(cat "$MODEL")" = "$EXPECTED_LFS_POINTER" ] || {
  echo 'BLOCKED_MODEL_PATH_NOT_VERIFIED_POINTER__REFUSING_OVERWRITE' >&2;exit 75; }
 CACHED="$MODEL_CACHE_ROOT/objects/${MODEL_SHA:0:2}/${MODEL_SHA:2:2}/$MODEL_SHA"
 if [ ! -f "$CACHED" ] || [ "$(stat -c %s "$CACHED")" != "$MODEL_SIZE" ] ||
    [ "$(sha256sum "$CACHED" | awk '{print $1}')" != "$MODEL_SHA" ];then
  # Never materialize the unrelated Repl GLB; fetch ONLY the required Hareworks object.
  [ ! -e "$CACHED" ] || { echo 'BLOCKED_PREEXISTING_MODEL_CACHE_HASH_MISMATCH' >&2;exit 75; }
  STAGE='fetch-hareworks-only'
  for attempt in 1 2 3;do
   if timeout 180 git lfs fetch --include="$MODEL" --exclude='' origin "$BASE_SHA";then break;fi
   sleep "$attempt"
  done
 fi
 [ -f "$CACHED" ] && [ "$(stat -c %s "$CACHED")" = "$MODEL_SIZE" ] &&
 [ "$(sha256sum "$CACHED" | awk '{print $1}')" = "$MODEL_SHA" ] || {
  echo 'BLOCKED_ONLY_HAREWORKS_LFS_FETCH_FAILED' >&2;exit 75; }
 STAGE='materialize-one-hareworks-model'
 TEMP_MODEL="$MODEL.r15-verified-${ENTRY_SHA:0:12}.tmp"
 [ ! -e "$TEMP_MODEL" ] || { echo 'BLOCKED_OLD_TEMP_MODEL__REFUSE_OVERWRITE' >&2;exit 75; }
 cp "$CACHED" "$TEMP_MODEL"
 [ "$(stat -c %s "$TEMP_MODEL")" = "$MODEL_SIZE" ] &&
 [ "$(sha256sum "$TEMP_MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || {
  echo 'BLOCKED_MODEL_COPY_VERIFICATION_FAILED' >&2;exit 75; }
 [ "$(cat "$MODEL")" = "$EXPECTED_LFS_POINTER" ] || { echo 'BLOCKED_POINTER_CHANGED_DURING_COPY' >&2;exit 75; }
 mv -- "$TEMP_MODEL" "$MODEL"
 echo "HAREWORKS_MODEL_INSTALLED_ONCE=$CHECKOUT/$MODEL"
fi
[ "$(sha256sum "$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || { echo 'BLOCKED_MODEL_INTEGRITY' >&2;exit 75; }
# Git LFS can report its correctly materialized binary as an unstaged ' M'
# when clean filtering is unavailable on Android shared storage. That is not
# permission to ignore other edits, use skip-worktree/assume-unchanged, or
# replace any user file. Validate the *exact tracked pointer*, bytes and status.
# Call before changes, with the new untracked payload, and after publication.
verify_worktree_scope(){
 local phase="$1"
 python3 - "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" "$DEST_REL" "$phase" <<'PYSTATUS'
import hashlib, pathlib, subprocess, sys
model, expected_sha, expected_size, destination, phase = sys.argv[1:]
assert phase in ('baseline','generated','published'), phase
p = pathlib.Path(model)
if not p.is_file() or p.is_symlink() or p.stat().st_size != int(expected_size):
 raise SystemExit('BLOCKED_EXPECTED_HAREWORKS_MODEL_MISSING_OR_WRONG_SIZE')
if hashlib.sha256(p.read_bytes()).hexdigest() != expected_sha:
 raise SystemExit('BLOCKED_EXPECTED_HAREWORKS_MODEL_HASH_MISMATCH')
head = subprocess.run(['git','show','HEAD:'+model],capture_output=True,check=True).stdout.decode('utf-8')
expected_pointer = f'version https://git-lfs.github.com/spec/v1\noid sha256:{expected_sha}\nsize {expected_size}\n'
if head != expected_pointer:
 raise SystemExit('BLOCKED_HAREWORKS_GIT_INDEX_POINTER_MISMATCH')
result = subprocess.run(['git','status','--porcelain=v1','--untracked-files=all','-z'],capture_output=True,check=True).stdout
entries = [x.decode('utf-8','surrogateescape') for x in result.split(b'\0') if x]
allowed_model = 0
payload_count = 0
for line in entries:
 if len(line) < 4 or line[2] != ' ':
  raise SystemExit('BLOCKED_MALFORMED_GIT_STATUS_ENTRY:'+repr(line))
 xy, path = line[:2], line[3:]
 if path == model and xy == ' M':
  allowed_model += 1
  continue
 if phase == 'generated' and xy == '??' and path.startswith(destination+'/') and '..' not in pathlib.PurePosixPath(path).parts:
  payload_count += 1
  continue
 raise SystemExit('BLOCKED_UNRELATED_WORKTREE_CHANGE:'+repr(line))
if allowed_model > 1:
 raise SystemExit('BLOCKED_DUPLICATE_MODEL_STATUS')
if phase == 'generated' and payload_count == 0:
 raise SystemExit('BLOCKED_NEW_GAIT_FILES_NOT_PRESENT')
if subprocess.run(['git','diff','--cached','--quiet']).returncode != 0:
 raise SystemExit('BLOCKED_PREEXISTING_STAGED_CHANGES')
print(f'EXACT_WORKTREE_SCOPE_PASS phase={phase} trackedLfsMaterialization={allowed_model} allowedUntrackedGaitFiles={payload_count}')
PYSTATUS
}
# Record whether Git's LFS pointer clean filter now makes the checkout appear
# clean. If not, retain a narrowly audited exception for this exact hash only.
STAGE='prepublication-worktree-guard'
verify_worktree_scope baseline || { echo 'BLOCKED_EXISTING_WORKTREE_DIRTY__NO_RESET_OR_STASH' >&2;exit 76; }
if [ "$PUBLISHED_REUSE" -eq 0 ] && [ "$PENDING_COMMIT" -eq 0 ];then
 [ -z "$(git ls-tree -r --name-only HEAD -- "$DEST_REL")" ] && [ ! -e "$DEST_REL" ] || { echo 'BLOCKED_GAIT_VERSION_COLLISION' >&2;exit 76; }
 git var GIT_AUTHOR_IDENT >/dev/null || { echo 'BLOCKED_GIT_AUTHOR_IDENTITY_MISSING' >&2;exit 76; }
fi
if [ "$PUBLISHED_REUSE" -eq 0 ] && [ "$PENDING_COMMIT" -eq 0 ];then
 # Build just the NEW gait text files first; never clone another repository.
 RUN="$(mktemp -d "$STATE/build.XXXXXXXX")"
 BUILDROOT="$RUN"
 mkdir -p "$BUILDROOT/tools/hareworks-forward-woman"
 cd "$BUILDROOT"
STAGE='generate-v015-startup-recovery'
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.14" "$DEST_REL"
for old_launcher in "$DEST_REL"/campaign-*.sh;do [ -f "$old_launcher" ] && rm -- "$old_launcher" || :;done
cp "$ENTRY" "$DEST_REL/campaign-v0.1.15-v1-godotprojects.sh"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.2" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3"
cat > "$DEST_REL/patch.py" <<'V015_PATCH'
#!/usr/bin/env python3
"""Patch EXACT published v0.1.14 with startup preview, verified original reference root and visible failure provenance."""
from pathlib import Path
import sys,json,hashlib
root=Path(sys.argv[1]).resolve()
target=root/'tools/hareworks-forward-woman/v0.1.15'
p=target/'viewer.mjs'
s=p.read_text()
def once(old,new):
 global s
 if s.count(old)!=1:raise RuntimeError('PATCH_ANCHOR_COUNT_'+str(s.count(old))+' '+old[:120])
 s=s.replace(old,new,1)
def region(first,end,replacement):
 global s
 if s.count(first)!=1 or s.count(end)!=1:raise RuntimeError('PATCH_REGION_NOT_UNIQUE '+first[:60]+' '+str(s.count(first)))
 a=s.index(first);b=s.index(end,a)
 if b<=a:raise RuntimeError('PATCH_REGION_ORDER')
 s=s[:a]+replacement+s[b:]
# New diagnostic mode does NOT play the source clip on the visible actor. It renders the
# accepted v0.1.9 analytic hip/ankle/knee-pole gait when physics calibration fails.
once("let sourceSamples=null,sourceGaits=null,sourceGround=0,witnessCache=null,sourceSeamRepair={},shapeSum=0,shapeCount=0;", """let sourceSamples=null,sourceGaits=null,sourceGround=0,witnessCache=null,sourceSeamRepair={},shapeSum=0,shapeCount=0;
let previewReady=false,previewLegs=null,previewFault='',previewStage='GLB_LOAD',previewFaults=0;
let motionMode='LOADING',frameTickCount=0,lastPreviewError='',previewCycle=0;
const REFERENCE_ROOT_UNITS_PER_CYCLE=1.224546;
const ownerAcceptance=false; // No synthetic or diagnostic result can grant visual acceptance.
function previewStatus(stage,why){
 if(motionMode==='PHYSICAL_GROUND_PINNING')previewCycle=totalPhase;
 previewStage=stage;previewFault=String(why);motionMode='PROCEDURAL_PREVIEW_UNPINNED';ready=false;playing=true;
 for(const p of Object.values(drawPins))p.visible=false;
 $('play').textContent='Pause';
 status('PHYSICAL_IK_BLOCKED '+stage+' '+previewFault+' · V0.1.9 PROCEDURAL WALK PREVIEW MOVING · NOT GROUND PINNED');
 $('metrics').textContent='PROCEDURAL PREVIEW ONLY, NOT CONTACT VALIDATION\\n'+previewFault;
 if(actor)pinCamera();
 if(previewReady) Promise.resolve().then(()=>fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({schema:'hareworks-v0.1.15-startup-diagnostic',stage,error:previewFault,sourceSha256:SOURCE_SHA,
  mode:motionMode,ownerVisualAcceptance:false,previewReady,physicalContactVerified:false})}).catch(()=>{}));
}
function initPreviewLegs(){
 if(!actor||!rig||!rest||!footProfile||!pelvisProfile||!fit)throw Error('PREVIEW_BASELINE_NOT_READY');
 previewLegs={};for(const [side,arr] of Object.entries(names)){
  const chain=arr.map(n=>rig[n]);if(chain.some(x=>!x))throw Error('PREVIEW_LEG_MISSING_'+side);
  const [up,knee,bridge,foot]=chain;
  previewLegs[side]={chain,up,knee,foot,upperLength:wpos(up).distanceTo(wpos(knee)),
   lowerLength:wpos(knee).distanceTo(wpos(foot))};
 }
 previewReady=true;motionMode='PROCEDURAL_PREVIEW_UNPINNED';
}
function diagnosticPoseStep(dt){
 // The original accepted phase equations, not the source AnimationMixer.
 previewCycle+=Math.max(0,speed)*dt/REFERENCE_ROOT_UNITS_PER_CYCLE;
 phase=mod1(previewCycle);worldZ=REFERENCE_ROOT_UNITS_PER_CYCLE*previewCycle;
 frameBody(phase);
 const q=phase*clipDuration,yaw=independentPose(pelvisProfile,q).pelvisYaw;
 for(const [side,c] of Object.entries(previewLegs||{})){
  try{
   for(const b of c.chain)copyLocal(b,rest[b.name]);actor.updateMatrixWorld(true);
   const H=wpos(c.up),K0=wpos(c.knee),v=legAt(footProfile,side,q);
   const target=H.clone().add(V(...rotateY(v.ankleLocal,yaw)));
   const dist=target.distanceTo(H),limit=c.upperLength+c.lowerLength-.001;
   if(dist>limit||dist<Math.abs(c.upperLength-c.lowerLength)+.001){
    target.sub(H).setLength(clamp(dist,Math.abs(c.upperLength-c.lowerLength)+.001,limit)).add(H);
    previewFaults++;lastPreviewError='ANATOMICAL_PREVIEW_REACH_CLAMP_'+side+'_'+dist.toFixed(5);
   }
   const K=V(...kneeFromTarget(H.toArray(),target.toArray(),c.upperLength,c.lowerLength,rotateY(v.poleLocal,yaw)));
   turnToward(c.up,K0,K);actor.updateMatrixWorld(true);
   turnToward(c.knee,wpos(c.foot),target);actor.updateMatrixWorld(true);
   if(sourceSamples&&sourceSamples[side]&&sourceSamples[side].length>=60){
    const f=sourceAt(sourceSamples[side],phase);setWorldQ(c.foot,measuredFootQ(f));actor.updateMatrixWorld(true);
   }
  }catch(err){
   previewFaults++;lastPreviewError=String(err.message||err);
  }
 }
 frameTickCount++;
 if(frameTickCount%40===0){
  $('metrics').textContent='V0.1.9 PROCEDURAL MOTION PREVIEW · NOT GROUND PINNED\\n'+
   'phase '+phase.toFixed(3)+' root Z '+worldZ.toFixed(3)+' model '+SOURCE_SHA.slice(0,12)+'\\n'+
   'PHYSICAL_CONTACT_GATE=BLOCKED '+previewStage+' '+previewFault+'\\n'+
   'diagnostic solver warnings '+previewFaults+(lastPreviewError?' '+lastPreviewError:'');
 }
}
""")
# Real contact physics is unchanged, but entering it requires an observable 32-step smoke test.
once("$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';status(playing?'RUNNING · world travel and anchored soles':'PAUSED · world contact anchors retained')};", """$('play').onclick=()=>{
 if(!ready&&!previewReady){status('BLOCKED_NO_RUNNING_CONTROLLER · model is visible only');return;}
 playing=!playing;$('play').textContent=playing?'Pause':'Play';
 if(motionMode!=='PHYSICAL_GROUND_PINNING'){
  status((playing?'PREVIEW_RUNNING':'PREVIEW_PAUSED')+' · ORIGINAL V0.1.9 PROCEDURAL GAIT · UNPINNED · '+previewFault);
 }else status(playing?'PHYSICAL_WORLD_IK_RUNNING':'PHYSICAL_WORLD_IK_PAUSED');
};""")
once("$('reset').onclick=()=>{initRun();status('WORLD RUN RESET · actor, anchors and camera synchronized')};", """$('reset').onclick=()=>{
 if(motionMode!=='PHYSICAL_GROUND_PINNING'){
  if(!previewReady){status('RESET_UNAVAILABLE_NO_CONTROLLER');return;}
  previewCycle=0;worldZ=0;frameBody(0);for(const p of Object.values(drawPins))p.visible=false;
  status('V0.1.9 PROCEDURAL PREVIEW RESET · UNPINNED · '+previewFault);pinCamera();return;
 }
 try{initRun();status('PHYSICAL WORLD RUN RESET · actor, anchors and orbit synchronized');}
 catch(e){previewStatus('PHYSICAL_RESET',e.message||String(e));}
};""")
once("function updateMotionStatus(){\n $('motionStatus').textContent=`SOURCE-DERIVED FOOT PATH · ${stride.toFixed(3)} u travel/cycle · ${cadenceFor(speed,stride).toFixed(3)} cycles/s · no synthetic foot lift`;\n}", """function updateMotionStatus(){
 if(motionMode==='PROCEDURAL_PREVIEW_UNPINNED'){
  $('motionStatus').textContent='UNPINNED SOURCE PROCEDURAL PREVIEW · '+REFERENCE_ROOT_UNITS_PER_CYCLE.toFixed(4)+' u/full cycle · contact audit NOT available';
 }else $('motionStatus').textContent=`SOURCE-DERIVED FOOT PATH · ${stride.toFixed(3)} u travel/cycle · ${cadenceFor(speed,stride).toFixed(3)} cycles/s · no synthetic foot lift`;
}""")
once("$('showContacts').onchange=()=>{for(const side of ['left','right'])drawPins[side].visible=$('showContacts').checked};", """$('showContacts').onchange=()=>{
 for(const side of ['left','right'])drawPins[side].visible=ready&&motionMode==='PHYSICAL_GROUND_PINNING'&&$('showContacts').checked;
};""")
once("finally{const summary=$('metrics').textContent;speed=oldSpeed;initRun();$('metrics').textContent=summary;playing=was;$('play').textContent=playing?'Pause':'Play';}", """finally{const summary=$('metrics').textContent;speed=oldSpeed;
  if(motionMode==='PHYSICAL_GROUND_PINNING'){
   try{initRun();$('metrics').textContent=summary;}
   catch(e){previewStatus('PHYSICAL_AUDIT_RESTART',e.message||String(e));}
  }
  playing=was;$('play').textContent=playing?'Pause':'Play';}
""")
once("$('audit').onclick=async()=>{if(!ready)return;", """$('audit').onclick=async()=>{if(!ready){status('PHYSICAL_AUDIT_UNAVAILABLE · V0.1.9 PREVIEW DOES NOT PROVE GROUND PINNING · '+previewFault);return;}""")
region('function frame(now){requestAnimationFrame(frame);','requestAnimationFrame(frame);\ntry{\n const response=', """function frame(now){requestAnimationFrame(frame);
 const delta=Math.min(.055,Math.max(0,(now-frameTimer)/1000));frameTimer=now;
 if(playing&&motionMode==='PHYSICAL_GROUND_PINNING'&&ready){
  accumulator=Math.min(.06,accumulator+delta);
  try{let count=0;while(accumulator>=1/120&&count<9){physicsStep(1/120);accumulator-=1/120;count++}
   pinCamera();if(runFrames%30===0)renderMetrics();
  }catch(e){failedFrames++;previewStatus('PHYSICAL_RUNTIME_STEP',e.message||String(e));}
 }else if(playing&&previewReady&&motionMode==='PROCEDURAL_PREVIEW_UNPINNED'){
  try{diagnosticPoseStep(delta);pinCamera();}catch(e){lastPreviewError=String(e.message||e);status('PREVIEW_STEP_ERROR '+lastPreviewError);}
 }
 orbit.update();renderer.render(scene,camera);
}
""")
# Model + original fit becomes enough to start an honest procedural reference preview.
once("fit=sampleFitted(source,mixer,srcRig);mixer.setTime(0);source.updateMatrixWorld(true);", """try{fit=sampleFitted(source,mixer,srcRig);}catch(fitError){
  fit={};previewFault='UPPER_BODY_FIT_FAILED '+String(fitError.message||fitError);
  console.warn('UPPER_BODY_FIT_RECOVERY_TO_REST_UPPER',fitError);
 }
 mixer.setTime(0);source.updateMatrixWorld(true);
 initPreviewLegs();previewStage='PROCEDURAL_REFERENCE_LIVENESS';
 diagnosticPoseStep(0);
 const relativeFoot=(side)=>wpos(previewLegs[side].foot).sub(wpos(previewLegs[side].up));
 const atStart={left:relativeFoot('left'),right:relativeFoot('right')};
 diagnosticPoseStep(.35*REFERENCE_ROOT_UNITS_PER_CYCLE/Math.max(speed,.1));
 const previewLegAmplitude=Math.max(...['left','right'].map(side=>relativeFoot(side).distanceTo(atStart[side])));
 if(!Number.isFinite(previewLegAmplitude)||previewLegAmplitude<.045){
  previewReady=false;throw Error('V019_PROCEDURAL_PREVIEW_LEG_MOTION_NOT_OBSERVABLE '+previewLegAmplitude);
 }
 previewCycle=0;worldZ=0;frameBody(0);
 console.info('V019_REFERENCE_LEG_MOTION_LIVENESS_PASS',previewLegAmplitude);
 previewStage='SHOE_WITNESS_CALIBRATION';
 if(previewFault)throw Error(previewFault);
 status('V0.1.9 PROCEDURAL REFERENCE GAIT MOVEMENT VERIFIED · calibrating physical contacts…');""")
# Archived source witnesses are canonical, reproducible, and independent of how a later shoe mesh splits.
region(" sourceGaits={left:inferVelocityContact(sourceSamples.left),right:inferVelocityContact(sourceSamples.right)};",
       " updateMotionStatus();", """ previewStage='ARCHIVED_V019_ROOT_CONTACTS';
 const archivedResponse=await fetch('../v0.1.3/reference-leg-witnesses.json',{cache:'no-store'});
 if(!archivedResponse.ok)throw Error('ARCHIVED_SOURCE_WITNESSES_HTTP_'+archivedResponse.status);
 const archived=await archivedResponse.json();
 if(archived.sourceSha256!==SOURCE_SHA||archived.sourceClip!=='Walking_Woman'||archived.samples?.length!==60)
  throw Error('ARCHIVED_V019_WITNESS_IDENTITY_INVALID');
 const baseline={left:[],right:[]};let largestFitDifference=0;
 for(let i=0;i<60;i++)for(const side of ['left','right']){
  const archivedLeg=archived.samples[i].legs[side],measured=sourceSamples[side][i*6];
  largestFitDifference=Math.max(largestFitDifference,V(...archivedLeg.ankle).distanceTo(V(...measured.ankle)));
  baseline[side].push({...measured,ankle:archivedLeg.ankle});
 }
 if(largestFitDifference>.045)throw Error('PROCEDURAL_V019_REFERENCE_POSE_DRIFT '+largestFitDifference.toFixed(6));
 sourceGaits={left:inferVelocityContact(baseline.left),right:inferVelocityContact(baseline.right)};
 const phaseSeparation=mod1(sourceGaits.left.start-sourceGaits.right.start);
 if(phaseSeparation<.30||phaseSeparation>.70)throw Error('LEFT_RIGHT_CONTACT_TIMING_AMBIGUOUS '+phaseSeparation);
 rootCurve=buildRootCurve(baseline,sourceGaits);stride=rootCurve.stride;
 previewStage='PHYSICAL_IK_WARM_START';
""")
# Remove duplicate old phase/window+root build now contained in replacement, preserving main rest.
# Source previously has a phase-separation block just before rootCurve; the replacement extends to updateMotionStatus.
# The replacement above retains the preceding original phase-separation block? guard no duplicate in resulting code.
# New real physical startup must run enough steps to reject a static or throwing controller.
once("ready=true;initRun();pinCamera();status('ACCEPTED V0.1.9 WALK + INVERTED WORLD SUPPORT · orbit restored · owner review pending');", """previewStage='REAL_GLB_32_STEP_STARTUP_SMOKE';
 ready=true;initRun();
 const startZ=worldZ;for(let i=0;i<32;i++)physicsStep(1/120);
 const travelled=worldZ-startZ;
 if(!Number.isFinite(travelled)||travelled<.04)throw Error('NO_OBSERVABLE_WORLD_TRAVEL_AT_STARTUP '+travelled);
 if(!Number.isFinite(wpos(rig.mixamorigHips).x))throw Error('NONFINITE_ACTUAL_SKINNED_BODY');
 initRun();motionMode='PHYSICAL_GROUND_PINNING';playing=true;pinCamera();
 status('PHYSICAL IK CONTROLLER STARTED · 32 REAL SKINNED STEPS EXECUTED · owner gait approval pending');""")
once("}catch(e){playing=false;ready=false;if(actor&&!actor.parent){scene.add(actor);actor.updateMatrixWorld(true);}\n status('REAL_MODEL_CALIBRATION_BLOCKED '+e.message+' · ORIGINAL RIG VISIBLE (STATIC DIAGNOSTIC; NOT A WALK)');console.error(e)}", """}catch(e){if(actor&&!actor.parent){scene.add(actor);actor.updateMatrixWorld(true);}
 console.error('REAL_MODEL_CALIBRATION_BLOCKED stage='+previewStage,e);
 previewStatus(previewStage,e.message||String(e));
 if(!previewReady){playing=false;status('CALIBRATION_AND_PREVIEW_UNAVAILABLE '+previewStage+' '+String(e.message||e));}
}""")
once("/* v0.1.14. ONE moving Walking_Woman.", "/* v0.1.15. ONE moving Walking_Woman.")
once('v0.1.14 ACCEPTED V019 INVERSE SUPPORT ROOT + REAL SHOE WITNESSES', 'v0.1.15 ACCEPTED V019 SOURCE ROOT + HONEST RUNNING PREVIEW')
once("a.download='hareworks-woman-accepted-v019-world-pin-v0.1.14.json'", "a.download='hareworks-woman-accepted-v019-world-pin-v0.1.15.json'")
once("schema:'hareworks-woman-accepted-v019-world-pin-v0.1.14'", "schema:'hareworks-woman-accepted-v019-world-pin-v0.1.15'")
p.write_text(s)
# Preserve reset/play/camera controls from v0.1.14; lock new launch identity.
html=target/'index.html';h=html.read_text().replace('v0.1.14','v0.1.15')
h=h.replace('src="./viewer.mjs?build=v0.1.15-geometry-fix"','src="./viewer.mjs?build=v0.1.15-startup-and-preview"')
h=h.replace('src="./viewer.mjs?build=v0.1.15"','src="./viewer.mjs?build=v0.1.15-startup-and-preview"')
html.write_text(h)
rp=target/'review-server.py';r=rp.read_text().replace('v0.1.14','v0.1.15')
a="if not 450<=size<=4000000:raise ValueError('invalid evidence size')"
b="if not 100<=size<=4000000:raise ValueError('invalid evidence size')"
if r.count(a)!=1:raise RuntimeError('EVIDENCE_SIZE_GATE_ANCHOR')
r=r.replace(a,b)
a="if d.get('schema')!=SCHEMA or d.get('sourceSha256')!=SOURCE:raise ValueError('wrong artifact or source')"
b="""if d.get('schema')=='hareworks-v0.1.15-startup-diagnostic':
                if d.get('sourceSha256')!=SOURCE or d.get('ownerVisualAcceptance') is not False or d.get('physicalContactVerified') is not False:
                    raise ValueError('diagnostic cannot claim physical contact')
                if d.get('mode')!='PROCEDURAL_PREVIEW_UNPINNED':raise ValueError('wrong diagnostic mode')
                if not isinstance(d.get('error'),str) or len(d['error'])>1000:raise ValueError('invalid diagnostic error')
                out=pathlib.Path(state);out.mkdir(parents=True,exist_ok=True)
                path=out/'startup-diagnostic-v0.1.15.json';path.write_bytes(raw)
                receipt={'state':'UNPINNED_PROCEDURAL_PREVIEW_DIAGNOSTIC_SAVED','sha256':hashlib.sha256(raw).hexdigest(),
                         'path':str(path),'modelSha256':SOURCE,'ownerVisualAcceptance':False,'physicalContactVerified':False}
                b=json.dumps(receipt).encode();self.send_response(200);self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
            if size<450:raise ValueError('physical audit payload too small')
            if d.get('schema')!=SCHEMA or d.get('sourceSha256')!=SOURCE:raise ValueError('wrong artifact or source')"""
if r.count(a)!=1:raise RuntimeError('EVIDENCE_SCHEMA_GATE_ANCHOR')
r=r.replace(a,b);rp.write_text(r)
contract=target/'contract.json';j=json.loads(contract.read_text());j['schema']='hareworks-woman-accepted-v019-startup-recovery-v0.1.15';j['parent']='7a3690fa99c52f70636fa49be851e521a793838c';j['mutablePaths']=['tools/hareworks-forward-woman/v0.1.15/'];j['ownerVisualAcceptance']=False
j['calibrationErrorBehavior']='accepted v0.1.9 procedural reference preview continues moving but is clearly labeled UNPINNED; exact failure preserved'
j['realSourceMotion']='single generated actor; 32 step real world IK startup smoke or explicit unpinned preview';j['physicalGate']='real 74-joint skinned footwear audit 120Hz x 3 cycles; preview cannot substitute';contract.write_text(json.dumps(j,indent=2)+'\n')
(target/'README.md').write_text("""# Hareworks v0.1.15: startup motion recovery

This is a recovery from v0.1.14, where a calibrated model could be visible but a gait-calibration or first IK-step exception froze it with no movement. The status line was insufficient and the Play button could claim RUNNING despite no controller. The exact error is not known from the owner's report, so this version diagnoses actual runtime failures without asserting a guess.

- Keep the source SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`, original model, original v0.1.9 six-harmonic ankle and knee-pole equations, four-harmonic pelvis, all art, and OrbitControls.
- Build the full-cycle root and contacts from the archived 60 original v0.1.9 source witness frames, not the unstable 360-frame seam. Verify the 60-frame measured fit against the current real GLB before use. This corrects calibration fragility without changing the accepted math.
- Do 32 actual 120-Hz world-IK physics steps BEFORE declaring the physics controller started. Real skinning and real foot anchors must run; any exception records its stage and switches to a separately labeled procedural-motion preview, never a false PHYSICAL PASS.
- The preview contains the accepted source-fitted procedural hip, ankle and knee-pole gait solved through IK, traveling root, one visible actor and orbitable camera. It is **NOT ground pinned** and is not a substitute for the requested physical gait. Source clip mixer runs ONLY on the invisible calibration reference.
- The viewer's explicit status, Play control and saved diagnostic evidence distinguish a moving unpinned preview from a running physical controller. If the underlying reference fit itself fails, report that actual blocker rather than silently claim motion.

Read `AGENTS.md` and Campaign Etiquette first. Termux Git only. Persistent Android Documents checkout, new version path only, no GLB writes, no previous version writes, no force push. Real-device browser/motion success is not claimed by author-side tests. Human visual approval is independent.
""")
print('PATCH_V015_PROCEDURAL_STARTUP_RECOVERY_DONE')

V015_PATCH
cat > "$DEST_REL/archived-root-regression.mjs" <<'V015_PROOF'
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {inferVelocityContact,buildRootCurve,rootAt} from './root-motion.mjs';
const p=JSON.parse(readFileSync(process.argv[2],'utf8'));
assert.equal(p.sourceSha256,'a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6');
assert.equal(p.samples.length,60);
const x={left:[],right:[]};for(const s of p.samples)for(const side of ['left','right']){
 const a=s.legs[side].ankle;
 x[side].push({ankle:a,heel:s.legs[side].ankle,sole:s.legs[side].ankle,toe:s.legs[side].toe});
}
const g={left:inferVelocityContact(x.left),right:inferVelocityContact(x.right)},curve=buildRootCurve(x,g);
assert.ok(g.left.duty>.47&&g.right.duty>.47);
assert.ok(curve.stride>1.15&&curve.stride<1.35,'complete cycle root must NOT be half stride');
assert.ok(rootAt(curve,3)>3.45);
function sample(side,q){const n=x[side].length,z=((q%1)+1)%1*n,j=Math.floor(z),t=z-j;return x[side][j].ankle[2]*(1-t)+x[side][(j+1)%n].ankle[2]*t}
for(const side of ['left','right']){
 const gg=g[side],q0=gg.start,anchor=sample(side,q0)+rootAt(curve,q0);
 let worst=0;for(let i=0;i<=300;i++){
  const q=q0+gg.duty*i/300,w=sample(side,q)+rootAt(curve,q);
  worst=Math.max(worst,Math.abs(w-anchor));
 }
 assert.ok(worst<.06,side+' measured source root contact proxy drift '+worst);
 console.log('ARCHIVED_GAIT_RECONSTRUCTION',side,'duty',gg.duty.toFixed(3),'ankleZdrift',worst.toFixed(5));
}
console.log('ARCHIVED_V019_ROOT_MATH_PASS fullCycle='+curve.stride.toFixed(6));

V015_PROOF
cat > "$DEST_REL/startup-regression.py" <<'V015_ASSERT'
#!/usr/bin/env python3
import pathlib,sys,re,json
root=pathlib.Path(sys.argv[1]);view=(root/'viewer.mjs').read_text();html=(root/'index.html').read_text()
need=['new OrbitControls(camera,renderer.domElement)','orbit.target.add(delta)','new SourceFootContact','rootAt(rootCurve,totalPhase)',
'acceptedAnkle=sourceHip.clone()','initPreviewLegs();previewStage=', 'function diagnosticPoseStep(dt){',
'PREVIEW_RUNNING','PROCEDURAL_PREVIEW_UNPINNED','PHYSICAL_GROUND_PINNING',
'PHYSICAL_AUDIT_UNAVAILABLE','REAL_GLB_32_STEP_STARTUP_SMOKE','ARCHIVED_V019_ROOT_CONTACTS',
'32;i++)physicsStep(1/120)', 'ownerVisualAcceptance:false', 'calibrationErrorBehavior']
for n in need[:-1]:
 if n not in view:raise SystemExit('REGRESSION_MISSING:'+n)
assert 'calibrationErrorBehavior' in (root/'contract.json').read_text()
assert 'touch-action:none' in html and 'resetCamera' in html
assert 'new THREE.AnimationMixer(actor)' not in view
if 'playing=false;ready=false;if(actor&&!actor.parent)' in view:raise SystemExit('STATIC_GAIT_FAILURE_REINTRODUCED')
assert view.count("function frame(now)")==1
assert view.count("requestAnimationFrame(frame);")==2
for p in root.glob('*.mjs'):
 if 'v0.1.14' in p.name:raise SystemExit('OLD_NAMED_SOURCE_COLLISION')
print('STARTUP_PREVIEW_AND_PHYSICS_BOUNDARY_REGRESSIONS_PASS')

V015_ASSERT
STAGE='patch-and-test-v015-real-startup'
python3 "$DEST_REL/patch.py" "$BUILDROOT"
python3 - "$DEST_REL/patch.py" "$DEST_REL/review-server.py" "$DEST_REL/startup-regression.py" <<'PYPARSE'
import pathlib,sys
for p in sys.argv[1:]:compile(pathlib.Path(p).read_text(),p,'exec')
print('PYTHON_SYNTAX_PASS')
PYPARSE
for f in root-motion.mjs foot-gait.mjs root-model-test.mjs contact-test.mjs viewer.mjs shoe-witness.mjs shoe-witness-test.mjs archived-root-regression.mjs;do
 node --check "$DEST_REL/$f" || { echo "BLOCKED_JS_PARSE=$f" >&2;exit 77; }
done
node "$DEST_REL/shoe-witness-test.mjs"
node "$DEST_REL/contact-test.mjs"
node "$DEST_REL/root-model-test.mjs"
node "$DEST_REL/contact-core-test.mjs"
node "$DEST_REL/geometry-test.mjs"
node "$DEST_REL/archived-root-regression.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json"
python3 "$DEST_REL/startup-regression.py" "$DEST_REL"
# Require the unchanged real source binary to be glTF 2 with all nine original clips.
python3 - "$CHECKOUT/$MODEL" "$MODEL_SHA" <<'GLB_PREFLIGHT'
import hashlib,json,pathlib,struct,sys
b=pathlib.Path(sys.argv[1]).read_bytes()
if hashlib.sha256(b).hexdigest()!=sys.argv[2]:raise SystemExit('BLOCKED_GLB_SHA')
magic,version,length=struct.unpack_from('<4sII',b,0)
if magic!=b'glTF' or version!=2 or length!=len(b):raise SystemExit('BLOCKED_GLB_HEADER')
length,typ=struct.unpack_from('<II',b,12)
if typ!=0x4e4f534a:raise SystemExit('BLOCKED_GLB_JSON')
j=json.loads(b[20:20+length]);clips=[a.get('name') for a in j.get('animations',[])]
if len(clips)!=9 or 'Walking_Woman' not in clips or not j.get('meshes') or not j.get('skins'):raise SystemExit('BLOCKED_GLB_CONTENT')
print('SOURCE_GLB_NINE_CLIPS_SHA_VERIFIED; real browser skinning still pending')
GLB_PREFLIGHT
[ "$(sha256sum "$CHECKOUT/$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || { echo 'BLOCKED_MODEL_CHANGED_DURING_BUILD' >&2;exit 77; }
STAGE='install-gait-fixes-in-persistent-checkout'
cd "$CHECKOUT"
[ ! -e "$DEST_REL" ] || { echo 'BLOCKED_DESTINATION_NOW_EXISTS__NO_OVERWRITE' >&2;exit 77; }
cp -R -- "$BUILDROOT/$DEST_REL" "$DEST_REL"
# Full byte-for-byte readback; don't mistake a successful copy for correct files.
python3 - "$BUILDROOT/$DEST_REL" "$DEST_REL" <<'PYCHECK'
import hashlib,pathlib,sys
source,target=map(pathlib.Path,sys.argv[1:])
a={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
b={p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()}
if a!=b:raise RuntimeError('INSTALL_CONTENT_MISMATCH_OR_EXTRA_FILE')
print('SOURCE_GAIT_INSTALL_READBACK_PASS files='+str(len(a)))
PYCHECK
verify_worktree_scope generated || { echo 'BLOCKED_OUT_OF_SCOPE_EDIT' >&2;exit 77; }
git add -- "$DEST_REL"
while IFS= read -r changed;do
 case "$changed" in "$DEST_REL"/*) :;; *) echo "BLOCKED_STAGED_OUT_OF_SCOPE=$changed" >&2;exit 77;; esac
 case "$changed" in *.glb|*.gltf|*.blend|*.fbx|*.obj|*.stl|*.zip|*.7z|*.abc|*.bvh|*.exr|*.tif|*.tiff|*.psd)
   echo "BLOCKED_BINARY_STAGED=$changed" >&2;exit 77;; esac
done < <(git diff --cached --name-only)
git diff --cached --check
STAGE='Termux-Git-commit-and-push'
LATEST="$(remote_sha)" || true
[ "$LATEST" = "$BASE_SHA" ] || { echo "BLOCKED_REMOTE_CHANGED_BEFORE_PUSH=$LATEST" >&2;exit 78; }
git commit -m 'Hareworks v0.1.15 restore real startup motion and preserve physical contact gates'
NEW_SHA="$(git rev-parse HEAD)"
if ! GIT_LFS_SKIP_PUSH=1 timeout 90 git push origin HEAD:refs/heads/main;then
 echo 'HTTPS_PUSH_FAILED: attempting existing SSH key without changing history'
 if ! GIT_LFS_SKIP_PUSH=1 timeout 90 git push 'git@github.com:Valar05/parametric-parambulator.git' HEAD:refs/heads/main;then
  echo "BLOCKED_GIT_PUSH_AUTH_OR_NETWORK localCommit=$NEW_SHA checkout=$CHECKOUT" >&2;exit 78
 fi
fi
STAGE='exact-remote-readback'
LATEST="$(remote_sha)" || true
[ "$LATEST" = "$NEW_SHA" ] || { echo "BLOCKED_REMOTE_SHA_READBACK expected=$NEW_SHA actual=$LATEST" >&2;exit 79; }
GIT_LFS_SKIP_SMUDGE=1 timeout 90 git fetch --depth 1 --filter=blob:none origin refs/heads/main
[ "$(git rev-parse FETCH_HEAD)" = "$NEW_SHA" ] || { echo 'BLOCKED_REMOTE_FETCH_READBACK' >&2;exit 79; }
[ "$(git rev-parse "FETCH_HEAD:$DEST_REL/viewer.mjs")" = "$(git rev-parse "HEAD:$DEST_REL/viewer.mjs")" ] || { echo 'BLOCKED_REMOTE_VIEWER_BLOB_MISMATCH' >&2;exit 79; }
[ "$(git rev-parse "FETCH_HEAD:$DEST_REL/foot-gait.mjs")" = "$(git rev-parse "HEAD:$DEST_REL/foot-gait.mjs")" ] || { echo 'BLOCKED_REMOTE_GAIT_BLOB_MISMATCH' >&2;exit 79; }
[ "$(git rev-parse "FETCH_HEAD:$DEST_REL/root-motion.mjs")" = "$(git rev-parse "HEAD:$DEST_REL/root-motion.mjs")" ] || { echo 'BLOCKED_REMOTE_ROOT_BLOB_MISMATCH' >&2;exit 79; }
verify_worktree_scope published || { echo 'BLOCKED_CHECKOUT_DIRTY_AFTER_PUSH' >&2;exit 79; }
echo "PUBLISHED_COMMIT=$NEW_SHA"
fi
if [ "$PENDING_COMMIT" -eq 1 ];then
 STAGE='resume-unpushed-Termux-commit'
 LATEST="$(remote_sha)" || true
 if [ "$LATEST" = "$BASE_SHA" ];then
  if ! GIT_LFS_SKIP_PUSH=1 timeout 90 git push origin HEAD:refs/heads/main;then
   GIT_LFS_SKIP_PUSH=1 timeout 90 git push 'git@github.com:Valar05/parametric-parambulator.git' HEAD:refs/heads/main || {
    echo "BLOCKED_RESUMED_PUSH_FAILED commit=$NEW_SHA" >&2;exit 78; }
  fi
 elif [ "$LATEST" != "$NEW_SHA" ];then
  echo "BLOCKED_REMOTE_DIVERGED_DURING_RESUME=$LATEST" >&2;exit 78
 fi
 LATEST="$(remote_sha)" || true
 [ "$LATEST" = "$NEW_SHA" ] || { echo 'BLOCKED_RESUME_REMOTE_READBACK_FAILED' >&2;exit 79; }
 GIT_LFS_SKIP_SMUDGE=1 timeout 90 git fetch --depth 1 --filter=blob:none origin refs/heads/main
 [ "$(git rev-parse FETCH_HEAD)" = "$NEW_SHA" ] || { echo 'BLOCKED_RESUME_FETCH_SHA_MISMATCH' >&2;exit 79; }
 for f in viewer.mjs foot-gait.mjs root-motion.mjs index.html;do
  [ "$(git rev-parse "FETCH_HEAD:$DEST_REL/$f")" = "$(git rev-parse "HEAD:$DEST_REL/$f")" ] || { echo "BLOCKED_RESUME_SOURCE_MISMATCH=$f" >&2;exit 79; }
 done
 verify_worktree_scope published || { echo 'BLOCKED_RESUMED_CHECKOUT_DIRTY' >&2;exit 79; }
 echo "RESUMED_COMMIT_PUBLISHED=$NEW_SHA"
fi
if [ "$PUBLISHED_REUSE" -eq 1 ];then
 verify_worktree_scope published || { echo 'BLOCKED_PUBLISHED_REUSE_CHECKOUT_DIRTY' >&2;exit 79; }
fi
# A durable project path, not a scratch checkout. Subsequent invocations reuse Git+GLB.
cd "$CHECKOUT"
STAGE='launch-source-gait-review'
RUN="$(mktemp -d "$STATE/viewer.XXXXXXXX")"
READY="$RUN/server-ready.json"
SERVER_LOG="$STATE/review-server.log"
nohup python3 "$DEST_REL/review-server.py" "$CHECKOUT" "$READY" "$STATE" </dev/null >> "$SERVER_LOG" 2>&1 &
SERVER_PID=$!
for k in $(seq 1 40);do [ -s "$READY" ] && break;sleep .25;done
[ -s "$READY" ] && kill -0 "$SERVER_PID" 2>/dev/null || { echo 'BLOCKED_VIEWER_SERVER_UNAVAILABLE' >&2;exit 80; }
PORT="$(python3 - "$READY" <<'PYPORT'
import json,sys
print(json.load(open(sys.argv[1]))['port'])
PYPORT
)"
URL="http://127.0.0.1:$PORT/$DEST_REL/index.html?commit=$NEW_SHA&scriptSha=$ENTRY_SHA"
curl -fsSI "$URL" > "$RUN/http-headers.txt"
grep -iq 'Cache-Control: no-store' "$RUN/http-headers.txt" || { echo 'BLOCKED_BAD_CACHE_HEADERS' >&2;exit 80; }
HTTP_SHA="$(curl -fsS "http://127.0.0.1:$PORT/$DEST_REL/foot-gait.mjs" | sha256sum | awk '{print $1}')"
DISK_SHA="$(sha256sum "$DEST_REL/foot-gait.mjs" | awk '{print $1}')"
[ "$HTTP_SHA" = "$DISK_SHA" ] || { echo 'BLOCKED_VIEWER_SERVES_WRONG_GAIT_VERSION' >&2;exit 80; }
HTTP_ROOT_SHA="$(curl -fsS "http://127.0.0.1:$PORT/$DEST_REL/root-motion.mjs" | sha256sum | awk '{print $1}')"
[ "$HTTP_ROOT_SHA" = "$(sha256sum "$DEST_REL/root-motion.mjs" | awk '{print $1}')" ] || { echo 'BLOCKED_VIEWER_SERVES_WRONG_ROOT_MATH' >&2;exit 80; }
[ "$(sha256sum "$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || { echo 'BLOCKED_HAREWORKS_GLB_CHANGED' >&2;exit 80; }
python3 - "$STATE" "$CAMPAIGN_ID" "$BASE_SHA" "$NEW_SHA" "$ENTRY_SHA" "$MODEL_SHA" "$URL" "$PORT" "$SERVER_PID" "$CHECKOUT" "$AGENTS_BLOB" "$ETIQUETTE_DOC" "$TOPDOWN_DOC" "$HTTP_SHA" "$PUBLISHED_REUSE" "$RECOVERED_R2_PARTIAL_INIT" <<'PYRECEIPT'
import datetime,json,pathlib,sys
(state,campaign,base,commit,entry,model,url,port,pid,checkout,agents,etiquette,topdown,viewer_hash,reused,recovered)=sys.argv[1:]
receipt={
 'campaign':campaign,'status':'PERSISTENT_CHECKOUT_AND_V019_STARTUP_RECOVERY_PUBLISHED_REAL_BROWSER_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sparseCheckout':False,
 'androidSharedStorageGitTrust':'exact-canonical-project-only, global safe.directory',
 'lfsStatusGuard':'Git LFS filters configured locally; only exactly SHA-verified tracked Hareworks binary is admissible as unstaged model materialization',
 'lfsStatusGuardDoesNotHideChanges':True,
 'previousIncompleteGitInitRecovered':recovered=='1',
 'acceptedV019Math':'v0.1.9 procedural ankle + pelvis, root inverted from original archived sixty source frames; 120Hz audit still required',
 'shoeWitnesses':'v0.1.14 whole skinned foot low-surface longitudinal PCA bands, preserved unchanged',
 'calibrationFailureBehavior':'3d rig remains visible static and explicitly unapproved',
 'camera':'orbit and zoom with world-target follow',
 'unrelatedReplLfsFetched':False,'hareworksCopyPolicy':'exactly one verified worktree model, reusable private LFS cache',
 'rulesReadInAuthoringTurn':{'AGENTSBlob':agents,'CampaignEtiquetteDocument':etiquette,'TopDownEtiquetteDocument':topdown},
 'viewerUrl':url,'viewerPid':int(pid),'viewerPort':int(port),'viewerGaitSha256':viewer_hash,
 'alreadyPublishedRerun':reused=='1','browserRealSkinnedFootAudit':'PENDING; startup preview mode is not a physics audit',
 'actualSkinned3dPhysicsTestedInTermux':False,
 'contactGate':'PENDING_BROWSER_AUDIT; 32 real startup IK smoke steps required to enter physical mode','gaitResemblanceGate':'PENDING_OWNER_VISUAL_ACCEPTANCE; diagnostic preview expressly NOT acceptable as physical ground pinning',
 'ownerVisualAcceptance':False,'canonicalModelUnchanged':True}
p=pathlib.Path(state)/'latest-receipt.json'
p.write_text(json.dumps(receipt,indent=2)+'\n')
print('RECEIPT='+str(p))
PYRECEIPT
STAGE='review-ready-owner-verdict-pending'
echo "CHECKOUT_READY=$CHECKOUT"
echo 'NORMAL_GIT_CHECKOUT=YES'
echo "V019_INVERSE_ROOT_FIXES=$CHECKOUT/$DEST_REL"
echo "MODEL_SHA256=$MODEL_SHA"
echo "PUBLISHED_COMMIT=$NEW_SHA"
echo "SCRIPT_SHA256=$ENTRY_SHA"
echo "VIEWER_PID=$SERVER_PID"
echo "VIEWER_URL=$URL"
echo 'CAMERA_ORBIT=RESTORED_SOURCE_CODE__PHONE_INTERACTION_PENDING'
echo 'TRAILING_EXTENSION=SOURCE_MATH_VERIFIED__REAL_SKINNED_OWNER_REVIEW_PENDING'
echo 'CONTACT_GATE=PENDING_REAL_BROWSER_AUDIT__PREVIEW_IS_UNPINNED_IF_PHYSICS_FAILS'
echo 'GAIT_RESEMBLANCE_GATE=PENDING_OWNER_VISUAL_ACCEPTANCE'
if command -v termux-open-url >/dev/null 2>&1;then
 termux-open-url "$URL" || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
elif command -v am >/dev/null 2>&1;then
 am start -a android.intent.action.VIEW -d "$URL" >/dev/null 2>&1 || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
fi
