#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_SOURCE_KNEE_CENTERLINE_REPAIR_v0.1.19_DOCUMENTS
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_SOURCE_KNEE_CENTERLINE_REPAIR_v0.1.19_DOCUMENTS'
VERSION='v0.1.19'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='3318468ea1f76b264b61e319c988caab2a1870c9'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-source-knee-centerline-v0.1.19-v1-documents"
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
  grep -q 'hareworks-v0.1.19-source-locked-knee-centerline' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
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
[ -f tools/hareworks-forward-woman/v0.1.18/viewer.mjs ] || { echo 'BLOCKED_MISSING_SOURCE_GAIT_BASELINE' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.18/viewer.mjs)" = d5146f8559c5bbc2c026fe02d4e7829216c09cfa ] || { echo 'BLOCKED_PUBLISHED_V018_SOURCE_CHANGED' >&2;exit 74; }
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
 TEMP_MODEL="$MODEL.r18-verified-${ENTRY_SHA:0:12}.tmp"
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
STAGE='generate-v018-independent-foot-heading-knee-ik'
SOURCE_REL='tools/hareworks-forward-woman/v0.1.18'
[ -d "$CHECKOUT/$SOURCE_REL" ] || { echo 'BLOCKED_MISSING_PUBLISHED_V018_SOURCE' >&2;exit 77; }
cp -R "$CHECKOUT/$SOURCE_REL" "$DEST_REL"
for old_launcher in "$DEST_REL"/campaign-*.sh;do [ -f "$old_launcher" ] && rm -- "$old_launcher" || :;done
cp "$ENTRY" "$DEST_REL/campaign-v0.1.19-v1-godotprojects.sh"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.2" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3"
# v0.1.18 foot heading and all skinned contact modules are copied BYTE-FOR-BYTE.
# Do not recreate/modify the already-approved foot-yaw correction.
cat > "$DEST_REL/source-knee-plane.mjs" <<'V019_KNEEPLANE'
/* Hareworks v0.1.19: original source knee is the IK bending-plane authority.
 * Distal foot heading never enters this solver. Real two-bone lengths and
 * exact world-space ankle target remain immutable through this computation.
 * The centerline boundary applies in character +X (left) / -X (right),
 * using the actual midpoint between the world-space hip joints.
 */
const sub=(a,b)=>a.map((x,i)=>x-b[i]);
const add=(a,b)=>a.map((x,i)=>x+b[i]);
const scale=(a,n)=>a.map(x=>x*n);
const dot=(a,b)=>a.reduce((v,x,i)=>v+x*b[i],0);
const norm=a=>Math.hypot(...a);
const unit=a=>{let d=norm(a);if(d<1e-10)throw Error('KNEE_PLANE_ZERO_AXIS');return scale(a,1/d)};
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const project=(x,u)=>sub(x,scale(u,dot(x,u)));
function enforceSide(radial,center,radius,axis,sideSign,centerX,clearance){
 const outer=project([sideSign,0,0],axis),reach=norm(outer);
 if(reach<1e-6)throw Error('KNEE_CENTERLINE_AXIS_PARALLEL');
 const out=scale(outer,1/reach),signedCenter=sideSign*(center[0]-centerX),maxSide=signedCenter+radius*reach;
 if(maxSide<clearance-1e-8)throw Error('KNEE_CENTERLINE_GEOMETRY_INFEASIBLE_'+maxSide.toFixed(6));
 const currentSide=signedCenter+radius*sideSign*radial[0];
 if(currentSide>=clearance-1e-9)return {radial,corrected:false,maxSide};
 const target=clamp((clearance-signedCenter)/(radius*reach),-1,1);
 const component=sub(radial,scale(out,dot(radial,out)));
 const tangent=norm(component)>1e-8?unit(component):unit(project([0,0,1],axis).map((v,i)=>v-dot(project([0,0,1],axis),out)*out[i]));
 const corrected=unit(add(scale(out,target),scale(tangent,Math.sqrt(Math.max(0,1-target*target)))));
 return {radial:corrected,corrected:true,maxSide};
}
export function sourceKneePlane(hip,ankle,sourceHip,sourceKnee,l1,l2,side,centerX,previousKnee=null,dt=1/120,clearance=.018){
 if(!['left','right'].includes(side)||![hip,ankle,sourceHip,sourceKnee].every(a=>Array.isArray(a)&&a.length===3&&a.every(Number.isFinite))||
  ![l1,l2,centerX,dt,clearance].every(Number.isFinite)||l1<=0||l2<=0||dt<0||clearance<0)
  throw Error('KNEE_PLANE_INPUT_INVALID');
 const sg=side==='left'?1:-1,delta=sub(ankle,hip),distance=norm(delta);
 if(!(distance<l1+l2+1e-5&&distance>Math.abs(l1-l2)+1e-5))
  throw Error('KNEE_PLANE_UNREACHABLE_'+distance.toFixed(5));
 const axis=scale(delta,1/distance),along=(l1*l1-l2*l2+distance*distance)/(2*distance),
  radius=Math.sqrt(Math.max(0,l1*l1-along*along)),center=add(hip,scale(axis,along));
 // Original knee-relative-to-hip vector is correct even though the source
 // reference rig is invisible and rooted at the world origin.
 const sourceDirection=project(sub(sourceKnee,sourceHip),axis);
 if(norm(sourceDirection)<1e-8)throw Error('KNEE_SOURCE_BEND_PLANE_DEGENERATE');
 let radial=unit(sourceDirection),corrected=false;
 if(previousKnee&&previousKnee.length===3&&previousKnee.every(Number.isFinite)&&dt>0){
  const last=project(sub(previousKnee,center),axis);
  if(norm(last)>1e-8){
   const previous=unit(last),angle=Math.acos(clamp(dot(previous,radial),-1,1));
   const maximumAngle=dt*10; // 10 rad/s: stop abrupt pole flipping, not normal walk motion
   if(angle>maximumAngle&&maximumAngle>1e-6){
    const t=maximumAngle/angle,perp=sub(radial,scale(previous,Math.cos(angle)));
    if(norm(perp)>1e-8)radial=unit(add(scale(previous,Math.cos(maximumAngle)),scale(unit(perp),Math.sin(maximumAngle))));
   }
  }
 }
 // Guard applies AFTER continuity damping, never by moving the planted foot.
 if(radius>.0005){const out=enforceSide(radial,center,radius,axis,sg,centerX,clearance);radial=out.radial;corrected=out.corrected;}
 else if(sg*(center[0]-centerX)<clearance-1e-8)throw Error('KNEE_STRAIGHT_LEG_CENTERLINE_INFEASIBLE');
 const knee=add(center,scale(radial,radius));
 const signed=sg*(knee[0]-centerX);
 if(signed<clearance-2e-6)throw Error('KNEE_CROSSED_CENTERLINE_'+side+'_'+signed.toFixed(6));
 const sourcePoint=add(hip,sub(sourceKnee,sourceHip));
 return {knee,sideClearance:signed,centerlineCorrected:corrected,
  sourceKneeDisplacement:norm(sub(knee,sourcePoint)),sourceKnee:sourcePoint,
  hipToKnee:Math.abs(norm(sub(knee,hip))-l1),kneeToAnkle:Math.abs(norm(sub(knee,ankle))-l2)};
}
V019_KNEEPLANE
cat > "$DEST_REL/source-knee-plane-test.mjs" <<'V019_KNEEPLANE_TEST'
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {sourceKneePlane} from './source-knee-plane.mjs';
const archive=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const lengths=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
assert.equal(archive.samples.length,60);
let cases=0,maxError=0,maxJitter=0,minClearance=Infinity,corrections=0,physicallyInfeasible=0;
for(const side of ['left','right']){
 const {upperLength:l1,lowerLength:l2}=lengths[side],sign=side==='left'?1:-1;
 let prior=null;
 // Reconstruct source geometric knees with the original 60-frame phases.
 for(let i=0;i<60;i++){
  const s=archive.samples[i],data=s.legs[side];
  const center=(s.legs.left.hip[0]+s.legs.right.hip[0])/2;
  const a=sourceKneePlane(data.hip,data.ankle,data.hip,data.knee,l1,l2,side,center,null,0);
  const error=Math.hypot(...a.knee.map((v,j)=>v-data.knee[j]));
  maxError=Math.max(maxError,error);minClearance=Math.min(minClearance,a.sideClearance);
  assert(a.sideClearance>.018-1e-6,side+' knee crossed centerline at '+i);
  assert(a.hipToKnee<1e-6&&a.kneeToAnkle<1e-6);
  cases++;
 }
 // Force alternating left-right crossing and contact-driven ankle disturbances.
 // Keep every source ankle within the two anatomical links' feasible reach.
 for(let i=0;i<1200;i++){
  const s=archive.samples[i%60],data=s.legs[side],center=(s.legs.left.hip[0]+s.legs.right.hip[0])/2;
  const displacement=.055*Math.sin(i*.083)+(i%190>130?.07:0);
  const proposed=[data.ankle[0]-sign*displacement,data.ankle[1],data.ankle[2]];
  const d=Math.hypot(...proposed.map((v,j)=>v-data.hip[j]));
  const max=l1+l2-.00035,min=Math.abs(l1-l2)+.00035;
  const a=d>max||d<min?data.hip.map((v,j)=>v+(proposed[j]-v)*Math.max(min,Math.min(max,d))/d):proposed;
  const adversarialKnee=i%230>160?data.knee.map((v,j)=>j===0?v-sign*.32:v):data.knee;
  let k;try{k=sourceKneePlane(data.hip,a,data.hip,adversarialKnee,l1,l2,side,center,prior,1/120,.018)}
  catch(e){if(/KNEE_(CENTERLINE_GEOMETRY|STRAIGHT_LEG_CENTERLINE)_INFEASIBLE/.test(e.message)){physicallyInfeasible++;prior=null;continue}throw e;}
  assert(k.sideClearance>=.018-2e-6,side+' crossing despite guard');
  assert(k.hipToKnee<1e-6&&k.kneeToAnkle<1e-6);
  if(prior){const step=Math.hypot(...k.knee.map((v,j)=>v-prior[j]));maxJitter=Math.max(maxJitter,step)}
  if(k.centerlineCorrected)corrections++;
  prior=k.knee;cases++;
 }
}
assert(maxError<.01,'must reconstruct archived knees, not replace source style');
assert(minClearance>.018,'original source knees are already to the side');
assert(corrections>0,'injected crossing must reach correction rather than a vacuous PASS');
assert.throws(()=>sourceKneePlane([0,0,0],[0,0,3],[0,0,0],[0,.3,.2],.35,.39,'left',0));
assert.throws(()=>sourceKneePlane([0,0,0],[0,0,.2],[0,0,0],[0,.3,.2],.35,.39,'bad',0));
assert.throws(()=>sourceKneePlane([-.30,0,0],[-.31,-.65,0],[-.30,0,0],[-.28,-.3,.2],.35,.39,'left',0),/KNEE_CENTERLINE_GEOMETRY_INFEASIBLE/);
console.log('SOURCE_KNEE_PLANE_60_FRAME_PARITY_PASS maxError='+maxError.toFixed(6)+' minClearance='+minClearance.toFixed(5));
console.log('WORLD_IK_CROSSLINE_GUARD_PASS cases='+cases+' corrections='+corrections+' maxKneeStep='+maxJitter.toFixed(5)+' physicallyImpossibleInjectedCases='+physicallyInfeasible);
V019_KNEEPLANE_TEST
cat > "$DEST_REL/patch.py" <<'V019_PATCH'
#!/usr/bin/env python3
"""Patch an immutable copy of published v0.1.18, never the source or model."""
import pathlib,sys
src=pathlib.Path(sys.argv[1]); dest=pathlib.Path(sys.argv[2]); file=dest/'viewer.mjs';s=file.read_text()
def once(old,new):
 global s
 count=s.count(old)
 if count!=1:raise RuntimeError(f'V019_PINNED_ANCHOR_COUNT_{count}_'+old[:110])
 s=s.replace(old,new,1)
assert 'OrbitControls' in s and 'kneeFromTarget' in s
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
assert 'distalHeading(side,footFit,pelvisProfile)' in s
assert 'new THREE.AnimationMixer(actor)' not in s
once('/* v0.1.18. ONE moving Walking_Woman.', '/* v0.1.19. ONE moving Walking_Woman.')
once("import {kneeFromTarget} from './ik-core.mjs';", "import {kneeFromTarget} from './ik-core.mjs';\nimport {sourceKneePlane} from './source-knee-plane.mjs';")
once('let maxDistalKneeDelta=0,maxKneeFlexDelta=0,unstyledWitnessCache=null;',
'''let maxDistalKneeDelta=0,maxKneeFlexDelta=0,unstyledWitnessCache=null;
// Source knee alignment is separate from foot styling and world ankle pinning.
let priorWorldKnee={left:null,right:null},minSignedKneeCenterline=Infinity,
    maxKneeSourcePositionDelta=0,maxKneeWorldStep=0,kneeCenterlineCorrections=0;''')
# Do not update foot yaw in either the primary IK or the preview.
once('const K=V(...kneeFromTarget(H.toArray(),desiredAnkle.toArray(),c.upperLength,c.lowerLength,rotateY(pole,yaw)));',
'''// IMPORTANT: the old knee pole produced centerline violations whenever the
  // planted foot constrained the ankle. Drive the pole from the original
  // source KNEE itself, then keep that knee on its anatomical side.
  const hipCenterX=(wpos(legs.left.up).x+wpos(legs.right.up).x)*.5;
  const solved=sourceKneePlane(H.toArray(),desiredAnkle.toArray(),t.source.hip,t.source.knee,
   c.upperLength,c.lowerLength,side,hipCenterX,priorWorldKnee[side],1/120,.018);
  const K=V(...solved.knee);
  minSignedKneeCenterline=Math.min(minSignedKneeCenterline,solved.sideClearance);
  maxKneeSourcePositionDelta=Math.max(maxKneeSourcePositionDelta,solved.sourceKneeDisplacement);
  if(solved.centerlineCorrected)kneeCenterlineCorrections++;''')
# Save last knee only once, after all IK iterations and distal foot heading.
once('maxDistalKneeDelta=Math.max(maxDistalKneeDelta,kneeChanged);',
'''maxDistalKneeDelta=Math.max(maxDistalKneeDelta,kneeChanged);
 const currentKnee=wpos(c.knee),hipCenterX=(wpos(legs.left.up).x+wpos(legs.right.up).x)*.5;
 const signedKnee=(side==='left'?1:-1)*(currentKnee.x-hipCenterX);
 if(signedKnee<.0179)throw Error('REAL_KNEE_CROSSED_PELVIS_CENTERLINE_'+side+'_'+signedKnee.toFixed(6));
 if(priorWorldKnee[side])maxKneeWorldStep=Math.max(maxKneeWorldStep,currentKnee.distanceTo(V(...priorWorldKnee[side])));
 priorWorldKnee[side]=currentKnee.toArray();''')
once('function clearStats(){maxDistalKneeDelta=0;maxKneeFlexDelta=0;',
'''function clearStats(){priorWorldKnee={left:null,right:null};minSignedKneeCenterline=Infinity;
 maxKneeSourcePositionDelta=0;maxKneeWorldStep=0;kneeCenterlineCorrections=0;
 maxDistalKneeDelta=0;maxKneeFlexDelta=0;''')
once('FOOT_YAW_TO_KNEE_IK_COUPLING ${maxDistalKneeDelta.toFixed(8)} u · max knee vs source flexion ${maxKneeFlexDelta.toFixed(2)}°',
'KNEE_CENTERLINE_CLEARANCE ${Number.isFinite(minSignedKneeCenterline)?minSignedKneeCenterline.toFixed(4):"pending"} u · centerline corrections ${kneeCenterlineCorrections} · max knee step ${maxKneeWorldStep.toFixed(4)} u · knee source delta ${maxKneeSourcePositionDelta.toFixed(4)} u\\nFOOT_YAW_TO_KNEE_IK_COUPLING ${maxDistalKneeDelta.toFixed(8)} u · max knee vs source flexion ${maxKneeFlexDelta.toFixed(2)}°')
# A crossing is a HARD physical failure; no PASS when the style guard is violated.
once('maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&maxKneeFlexDelta<6;',
'maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&maxKneeFlexDelta<6&&minSignedKneeCenterline>=.0179;')
once('kneeIKDecoupledFromFootYaw:true,maxDistalKneeDelta,maxKneeFlexDelta,observations:samples};',
'''kneeIKDecoupledFromFootYaw:true,maxDistalKneeDelta,maxKneeFlexDelta,
    minSignedKneeCenterline,maxKneeSourcePositionDelta,maxKneeWorldStep,
    kneeCenterlineCorrections,kneeSourceAuthority:'60-frame Walking_Woman real knee witnesses',observations:samples};''')
s=s.replace('v0.1.18','v0.1.19').replace('V0.1.18','V0.1.19')
assert 'sourceKneePlane(' in s and s.count('sourceKneePlane(')==1
assert 'distalHeading(side,footFit,pelvisProfile)' in s
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
file.write_text(s.rstrip()+'\n')
for name in ('index.html','review-server.py'):
 p=dest/name
 t=p.read_text().replace('v0.1.18','v0.1.19').replace('V0.1.18','V0.1.19').replace('v0.1.18-knee-independent-right-foot','v0.1.19-source-knee-plane')
 p.write_text(t.rstrip()+'\n')
# Original 0.1.18 heading, foot-gait, root and speed modules are byte-identical.
for f in dest.rglob('*'):
 if f.is_file() and f.suffix in ('.mjs','.py','.json','.md','.html','.sh'):
  f.write_bytes(f.read_bytes().rstrip(b'\r\n')+b'\n')
print('V019_SOURCE_KNEE_TARGET_CENTERLINE_GUARD_PATCH_PASS; FOOT_HEADING_UNCHANGED')
V019_PATCH
cat > "$DEST_REL/contract.json" <<'V019_CONTRACT'
{
  "schema": "hareworks-v0.1.19-source-locked-knee-centerline",
  "repo": "Valar05/parametric-parambulator",
  "parent": "3318468ea1f76b264b61e319c988caab2a1870c9",
  "sourceController": "tools/hareworks-forward-woman/v0.1.18/viewer.mjs",
  "sourceControllerBlob": "d5146f8559c5bbc2c026fe02d4e7829216c09cfa",
  "sourceArchiveBlob": "f6e8940b5eaeaf154a126eaa5221dcfcab0d94d1",
  "sourceFootProfileBlob": "6febeaa8ff461806b590748dfca6461f4d8df1db",
  "modelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "rulesAGENTSBlob": "547c2af52303f4efb718bbf8f82a698110c7bfca",
  "rulesCampaignEtiquetteDoc": "1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI",
  "rulesTopdownDoc": "1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU",
  "executionLane": "Android Termux Git only",
  "mutablePaths": [
    "tools/hareworks-forward-woman/v0.1.19/"
  ],
  "ownerApproved": "v0.1.18 left/right foot headings unchanged; v0.1.9 source leg shape, root world contact and orbit camera",
  "ownerRejected": "v0.1.18 knees visibly wobble and cross pelvis centerline, visual result unchanged",
  "physicalMechanic": "source real 60-frame knee direction projected onto actual anatomical two-link circle with enforced same-side pelvis boundary; planted ankle anchors and distal heading preserved",
  "clearanceFromMidHipCenter": 0.018,
  "modelModified": false,
  "ownerVisualAcceptance": false,
  "acceptance": "actual 120Hz GLB knee centerline, temporal consistency, sole/pivot drift and owner video"
}
V019_CONTRACT
cat > "$DEST_REL/README.md" <<'V019_README'
# Hareworks v0.1.19: Source-locked knee plane, no pelvis centerline crossing

Owner rejected v0.1.18 visual motion: knees remain wobbly and pass far across the centerline. Previous distal-style decoupling passed its own test but did NOT constrain the knee's actual world-space side position. This version corrects the proximal joint target rather than changing the already-liked foot direction.

* Source authority: original 60-frame Walking_Woman skinned hip, knee and ankle witnesses from published original model. For each real IK step, project the SOURCE hip-to-knee direction into the current hip-to-ankle 2-bone bending circle. This restores the original anatomical knee plane even when the world-planted ankle differs from the phase-fit ankle.
* Constrain each knee to remain at least .018 model units on its own side of the midpoint between the actual left/right hip roots; use the closest feasible point on the true two-bone knee circle, never fake a knee coordinate or move the planted foot. Report if geometry is physically infeasible rather than claiming completion.
* Limit knee-pole radial direction changes to 10 rad/s between physical IK frames, then enforce the centerline bound. Measure maximum knee displacement per 120Hz step, original-knee deviation, side clearance and correction count.
* Foot heading: `foot-heading.mjs` and the entire distal-styling block remain unchanged from published v0.1.18. Preserve original model, root path, dynamic speed, foot contact geometry and camera OrbitControls.
* Git authority: one versioned Termux script, checked existing Documents checkout, immutable source GLB SHA, new `v0.1.19` path only, remote commit and exact readback. Real browser audit and owner visual acceptance are NOT inferred from numerical tests or publication.

This is not a completed or approved gait until the actual skinned browser model passes and the owner reviews the movement.
V019_README
# Model and immutable source file provenance before the test runner.
[ "$(git -C "$CHECKOUT" hash-object tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json)" = f6e8940b5eaeaf154a126eaa5221dcfcab0d94d1 ] || { echo 'BLOCKED_SOURCE_KNEE_REFERENCE_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object tools/hareworks-forward-woman/v0.1.3/foot-profile.json)" = 6febeaa8ff461806b590748dfca6461f4d8df1db ] || { echo 'BLOCKED_SOURCE_LEG_LINKS_CHANGED' >&2;exit 77; }
# Foot heading stays byte-identical to the version the user accepted.
[ "$(git -C "$CHECKOUT" hash-object "$BUILDROOT/$DEST_REL/foot-heading.mjs")" = "$(git -C "$CHECKOUT" hash-object "$CHECKOUT/tools/hareworks-forward-woman/v0.1.18/foot-heading.mjs")" ] || { echo 'BLOCKED_APPROVED_FOOT_HEADING_CHANGED' >&2;exit 77; }
python3 "$DEST_REL/patch.py" "$CHECKOUT" "$DEST_REL"
STAGE='patch-and-test-v018-independent-foot-heading-knee-ik'
# v016 already patched using exact published v015 source
:
python3 - "$DEST_REL/patch.py" "$DEST_REL/review-server.py" "$DEST_REL/startup-regression.py" <<'PYPARSE'
import pathlib,sys
for p in sys.argv[1:]:compile(pathlib.Path(p).read_text(),p,'exec')
print('PYTHON_SYNTAX_PASS')
PYPARSE
for f in root-motion.mjs foot-gait.mjs root-model-test.mjs contact-test.mjs viewer.mjs shoe-witness.mjs shoe-witness-test.mjs archived-root-regression.mjs foot-heading.mjs foot-heading-test.mjs source-knee-plane.mjs source-knee-plane-test.mjs knee-source-invariant-test.mjs speed-gait.mjs;do
 node --check "$DEST_REL/$f" || { echo "BLOCKED_JS_PARSE=$f" >&2;exit 77; }
done
node "$DEST_REL/shoe-witness-test.mjs"
node "$DEST_REL/contact-test.mjs"
node "$DEST_REL/root-model-test.mjs"
node "$DEST_REL/contact-core-test.mjs"
node "$DEST_REL/geometry-test.mjs"
node "$DEST_REL/archived-root-regression.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json"
node "$DEST_REL/dynamic-gait-test.mjs"
node "$DEST_REL/foot-heading-test.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2/motion-profile.json"
node "$DEST_REL/knee-source-invariant-test.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/foot-profile.json"
node "$DEST_REL/source-knee-plane-test.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/foot-profile.json"
node "$DEST_REL/source-speed-contact-test.mjs"
node "$DEST_REL/real-knee-envelope-test.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/foot-profile.json"
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
STAGE='install-dynamic-gait-in-persistent-checkout'
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
git commit -m 'Hareworks v0.1.19 restore source knee plane and guard pelvis crossing'
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
[ "$(git rev-parse "FETCH_HEAD:$DEST_REL/source-knee-plane.mjs")" = "$(git rev-parse "HEAD:$DEST_REL/source-knee-plane.mjs")" ] || { echo 'BLOCKED_REMOTE_KNEE_PLANE_BLOB_MISMATCH' >&2;exit 79; }
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
 'campaign':campaign,'status':'PERSISTENT_CHECKOUT_AND_V019_SOURCE_KNEE_SIDE_GUARD_PUBLISHED_BROWSER_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sparseCheckout':False,
 'androidSharedStorageGitTrust':'exact-canonical-project-only, global safe.directory',
 'lfsStatusGuard':'Git LFS filters configured locally; only exactly SHA-verified tracked Hareworks binary is admissible as unstaged model materialization',
 'lfsStatusGuardDoesNotHideChanges':True,
 'previousIncompleteGitInitRecovered':recovered=='1',
 'acceptedV019Math':'v0.1.9 original ankle/pelvis plus 60-frame real-source knee plane restored; distal foot yaw unchanged; physical centerline guard runs every frame; real browser audit pending',
 'shoeWitnesses':'v0.1.14 whole skinned foot low-surface longitudinal PCA bands, preserved unchanged',
 'calibrationFailureBehavior':'source procedural preview moving but explicitly UNPINNED and unapproved',
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
echo "SOURCE_LOCKED_KNEE_GAIT_ROOT=$CHECKOUT/$DEST_REL"
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
