#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_TERRAIN_HIP_REACH_v0.1.23_DOCUMENTS
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_TERRAIN_HIP_REACH_v0.1.23_DOCUMENTS'
VERSION='v0.1.23'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='2e653d892cefcb8f100322cf5a6e8eb8aeaed4ee'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-terrain-hip-reach-v0.1.23-v1-documents"
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
  grep -q 'hareworks-v0.1.23-ground-hip-reach-hill-obstruction' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
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
[ -f tools/hareworks-forward-woman/v0.1.22/viewer.mjs ] || { echo 'BLOCKED_MISSING_SOURCE_GAIT_BASELINE' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.22/viewer.mjs)" = 0a32d8c49749e8678eed248054d2bca48f833f1d ] || { echo 'BLOCKED_PUBLISHED_V023_SOURCE_CHANGED' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.22/terrain-core.mjs)" = 47a476db52f2bede12bf73309aeedb2c579adb3c ] || { echo 'BLOCKED_PUBLISHED_V023_TERRAIN_CHANGED' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.21/foot-gait.mjs)" = ecc036c99f92dfa02b17a9457e76b0998a127c04 ] || { echo 'BLOCKED_PUBLISHED_V021_FOOT_TARGET_CHANGED' >&2;exit 74; }
[ -f tools/hareworks-forward-woman/v0.1.9/viewer.mjs ] || { echo 'BLOCKED_MISSING_ACCEPTED_V023_REFERENCE' >&2;exit 74; }
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
STAGE='generate-v020-stateless-source-knee-recovery'
SOURCE_REL='tools/hareworks-forward-woman/v0.1.22'
[ -d "$CHECKOUT/$SOURCE_REL" ] || { echo 'BLOCKED_MISSING_PUBLISHED_V023_SOURCE' >&2;exit 77; }
cp -R "$CHECKOUT/$SOURCE_REL" "$DEST_REL"
for old_launcher in "$DEST_REL"/campaign-*.sh;do [ -f "$old_launcher" ] && rm -- "$old_launcher" || :;done
cp "$ENTRY" "$DEST_REL/campaign-v0.1.23-v1-godotprojects.sh"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.2" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3"
# Published v0.1.20 copied unchanged first. Protected knee and gait source stay unchanged.
cat > "$DEST_REL/terrain-hip.mjs" <<'V023_HIP'
/* A REAL constrained pelvis-height solve against both world-fixed ankle targets.
 * Never edit a knee pole or move planted contact anchors. All units in GLB world coordinates.
 */
export const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
export function pelvisReachCorrection(hips,ankles,limits,currentLift,groundAt,dt){
 if(!['left','right'].every(s=>hips[s]?.length===3&&ankles[s]?.length===3&&limits[s]?.length===2))throw Error('HIP_REACH_PAIR_REQUIRED');
 if(![currentLift,dt].every(Number.isFinite)||dt<0)throw Error('HIP_REACH_DT_INVALID');
 let lo=-Infinity,hi=Infinity,rawTerrain=0;
 for(const side of ['left','right']){
  const H=hips[side],A=ankles[side],lengths=limits[side];
  if(![...H,...A,...lengths].every(Number.isFinite)||lengths.some(v=>v<=0))throw Error('HIP_REACH_NONFINITE');
  const lateral2=(A[0]-H[0])**2+(A[2]-H[2])**2;
  const maximum=lengths[0]+lengths[1]-.002;
  if(lateral2>=maximum**2)return {feasible:false,reason:'FOOT_OUTSIDE_HORIZONTAL_REACH_'+side,delta:0,lower:NaN,upper:NaN};
  const y= Math.sqrt(maximum**2-lateral2),center=A[1]-H[1];
  lo=Math.max(lo,center-y);hi=Math.min(hi,center+y);
  rawTerrain+=groundAt(A[0],A[2])/2;
 }
 if(!Number.isFinite(rawTerrain)||lo>hi)return {feasible:false,reason:'NO_COMMON_PELVIS_HEIGHT',delta:0,lower:lo,upper:hi};
 // Terrain under BOTH feet, not just the torso's forward Z centerline.
 // Offset is further constrained by physical two-link reach on BOTH legs.
 const desired=clamp(rawTerrain-currentLift,lo,hi);
 const rate=dt===0?.28:1.5*Math.min(dt,.1),delta=clamp(desired,-rate,rate);
 return {feasible:true,delta,desired,lower:lo,upper:hi,groundAverage:rawTerrain,rateLimited:Math.abs(desired)>rate+1e-9};
}
export function segmentTerrainPenetration(a,b,groundAt,radius=.035,samples=9){
 if(a.length!==3||b.length!==3||![...a,...b,radius].every(Number.isFinite))throw Error('LEG_TERRAIN_INPUT_INVALID');
 let maxDepth=0;
 for(let i=0;i<=samples;i++){
  const u=i/samples,x=a[0]+(b[0]-a[0])*u,z=a[2]+(b[2]-a[2])*u,y=a[1]+(b[1]-a[1])*u;
  maxDepth=Math.max(maxDepth,groundAt(x,z)-(y-radius));
 }
 return maxDepth;
}
V023_HIP
cat > "$DEST_REL/terrain-hip-test.mjs" <<'V023_HIP_TEST'
import assert from 'node:assert/strict';
import {pelvisReachCorrection,segmentTerrainPenetration} from './terrain-hip.mjs';
const h={left:[.10,.90,0],right:[-.10,.90,0]},f={left:[.12,.03,.15],right:[-.12,.05,-.15]},l={left:[.37,.38],right:[.37,.38]};
const noTerrain=()=>0;
let out=pelvisReachCorrection(h,f,l,0,noTerrain,0);assert.equal(out.feasible,true,'pelvis must solve the overextended baseline');assert(out.delta<0,'hips must lower at startup when targets are below reach');
for(const low of [-.18,-.06,0,.05,.16]){
 const H={left:[.10,.65+low,0],right:[-.10,.65+low,0]};
 const F={left:[.12,.06,.12],right:[-.12,.08,-.12]};
 const x=pelvisReachCorrection(H,F,l,low,(xx,z)=>.04-.1*Math.sin(z),1/120);
 assert.equal(x.feasible,true);assert(Math.abs(x.delta)<=1.5/120+1e-8);
 for(const side of ['left','right']){
  const newY=H[side][1]+x.delta,depth=Math.hypot(F[side][0]-H[side][0],F[side][1]-newY,F[side][2]-H[side][2]);
  assert(depth<.752);
 }
}
const H={left:[.1,1,0],right:[-.1,1,0]};
const F={left:[.1,.05,.05],right:[-.1,.05,.05]};
const down=pelvisReachCorrection(H,F,l,0,noTerrain,0);assert(down.feasible&&down.delta<0,'at start must lower pelvis to reach ground');
assert(segmentTerrainPenetration([0,.20,0],[0,.20,1],(_,z)=>z>.5?.3:0)>.13);
assert(segmentTerrainPenetration([0,.6,0],[0,.6,1],()=>0)===0);
assert.throws(()=>pelvisReachCorrection({},F,l,0,noTerrain,0));
console.log('TERRAIN_TWO_LEG_PELVIS_REACH_AND_SHIN_COLLISION_PASS');
V023_HIP_TEST
cat > "$DEST_REL/patch.py" <<'V023_PATCH'
import pathlib,sys
source=pathlib.Path(sys.argv[1]); dest=pathlib.Path(sys.argv[2]);f=dest/'viewer.mjs';s=f.read_text()
def one(a,b):
 global s
 n=s.count(a)
 if n!=1:raise RuntimeError('V023_SOURCE_ANCHOR_COUNT_'+str(n)+'_'+a[:120])
 s=s.replace(a,b,1)
one('/* v0.1.22. ONE moving Walking_Woman.','/* v0.1.23. ONE moving Walking_Woman.')
one("import {TERRAIN_MODES,isProfileTerrain,terrainHeight,terrainNormal,terrainBodyLift,terrainGrid,longitudinalProfile} from './terrain-core.mjs';",
"import {TERRAIN_MODES,isProfileTerrain,terrainHeight,terrainNormal,terrainBodyLift,terrainGrid,longitudinalProfile} from './terrain-core.mjs';\nimport {pelvisReachCorrection,segmentTerrainPenetration} from './terrain-hip.mjs';")
one('let groundLift=0,terrainMesh=null,terrainWire=null,terrainSlice=null,terrainCenterZ=0;',
'let groundLift=0,terrainMesh=null,terrainWire=null,terrainSlice=null,terrainCenterZ=0;\nlet hipReachLimitCount=0,maxShinTerrainCollision=0,lastHipSolve=null;')
one(' const targets=contactTargets();adjustReach(targets);const feet={};',
''' const targets=contactTargets();
 // Contact anchors are sampled ONCE. Now move the pelvis within both actual
 // two-link reach envelopes. This is no longer just terrainAt(0,worldZ).
 const hips=Object.fromEntries(['left','right'].map(side=>[side,wpos(legs[side].up).toArray()]));
 const ankles=Object.fromEntries(['left','right'].map(side=>[side,targets[side].ankleTarget]));
 const lengths=Object.fromEntries(['left','right'].map(side=>[side,[legs[side].upperLength,legs[side].lowerLength]]));
 lastHipSolve=pelvisReachCorrection(hips,ankles,lengths,groundLift,terrainAt,dt);
 if(lastHipSolve.feasible){groundLift+=lastHipSolve.delta;frameBody(phase)}
 else hipReachLimitCount++;
 adjustReach(targets);const feet={};''')
one(' const terrainIntrusion=Math.max(0,...footPatches.map(p=>terrainAt(p.x,p.z)-p.y));',
''' const terrainIntrusion=Math.max(0,...footPatches.map(p=>terrainAt(p.x,p.z)-p.y));
 // Detect hillside intersections at the shin, not only the three shoe patches.
 const shinCollision=segmentTerrainPenetration(wpos(c.knee).toArray(),wpos(c.foot).toArray(),terrainAt);
 maxShinTerrainCollision=Math.max(maxShinTerrainCollision,shinCollision);''')
one('  kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch,terrainClearances,',
'  kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch,terrainClearances,shinCollision,')
one(' terrainMode,terrainStrength,bodyTerrainLift:groundLift};',
' terrainMode,terrainStrength,bodyTerrainLift:groundLift,hipReachLimitCount,maxShinTerrainCollision,hipSolve:lastHipSolve};')
one('function clearStats(){priorWorldKnee={left:null,right:null};',
'function clearStats(){hipReachLimitCount=0;maxShinTerrainCollision=0;lastHipSolve=null;priorWorldKnee={left:null,right:null};')
one('TERRAIN penetration ${maxPenetration.toFixed(5)} u',
'TERRAIN penetration ${maxPenetration.toFixed(5)} u · shin hillside intrusion ${maxShinTerrainCollision.toFixed(4)} u · hip reach limits ${hipReachLimitCount}')
one('terrainMode,terrainStrength,terrainWidthInvariant:profileMode(),',
 'terrainMode,terrainStrength,terrainHipReachSolver:true,maxShinTerrainCollision,hipReachLimitCount,terrainWidthInvariant:profileMode(),')
one('const physicalPass=worst.left<=.025&&worst.right<=.025&&',
 'const physicalPass=maxShinTerrainCollision<=.035&&hipReachLimitCount===0&&worst.left<=.025&&worst.right<=.025&&')
one("$('motionStatus').textContent='UNPINNED DYNAMIC GEOMETRY PREVIEW · target stride '+(dynamicMotion?.stride||0).toFixed(3)+' u/full cycle · no contact proof';",
"$('motionStatus').textContent='PHYSICAL TERRAIN IK UNAVAILABLE · UNPINNED PREVIEW ONLY · '+previewStage+' · '+previewFault+' · no contact proof';")
one("$('identity').textContent='v0.1.22 · ORIGINAL SKINNED 3D MODEL HASH '+SOURCE_SHA+' · STRESS PROFILE SOURCE AND CONTACT AUDIT PENDING';",
"$('identity').textContent='v0.1.23 · REAL GLB '+SOURCE_SHA+' · TERRAIN HIP + SHIN PROBE · browser physics pending';")
s=s.replace('v0.1.22','v0.1.23').replace('V0.1.22','V0.1.23')
assert 'chooseSourceKnee' in s and 'distalHeading(side,footFit,pelvisProfile)' in s
f.write_text(s.rstrip()+'\n')
p=dest/'index.html';h=p.read_text().replace('v0.1.22','v0.1.23').replace('V0.1.22','V0.1.23');h=h.replace('Physically sampled', 'Physically sampled')
h=h.replace('The travel-speed slider changes physical world footfall spacing and cadence.', 'The travel-speed slider changes physical world footfall spacing and cadence. On steep terrain, the pelvis solves against both leg-reach limits and displays shin obstruction warnings; unpinned preview is NOT a ground test.')
p.write_text(h.rstrip()+'\n')
p=dest/'review-server.py';p.write_text(p.read_text().replace('v0.1.22','v0.1.23').replace('V0.1.22','V0.1.23').rstrip()+'\n')
print('V023_TWO_LEG_PELVIS_AND_HILLSIDE_COLLISION_PATCH_PASS')
V023_PATCH
cat > "$DEST_REL/contract.json" <<'V023_CONTRACT'
{
  "schema":"hareworks-v0.1.23-ground-hip-reach-hill-obstruction",
  "repo":"Valar05/parametric-parambulator",
  "sourceCommit":"2e653d892cefcb8f100322cf5a6e8eb8aeaed4ee",
  "sourceControllerBlob":"0a32d8c49749e8678eed248054d2bca48f833f1d",
  "modelSha256":"a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "AGENTSBlob":"547c2af52303f4efb718bbf8f82a698110c7bfca",
  "rulesCampaignEtiquetteDoc":"1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI",
  "executionLane":"Android Termux Git only",
  "mutablePaths":["tools/hareworks-forward-woman/v0.1.23/"],
  "ownerVerdict":"v0.1.22 hills clip and actual run is labeled UNPINNED: cannot claim physical terrain IK",
  "physicalImprovement":"joint reachable pelvis height against both actual ankle world targets; unchanged knee pole, ankle yaw and stance contact anchors",
  "hillCollision":"actual skinned shin segment terrain probe; report intrusion rather than false physical PASS",
  "preserve":"v0.1.20 anterior knee pole and original stride, v0.1.18 foot orientation, terrain geometry, speed controls and OrbitControls",
  "noGuarantee":"browser source startup may still block at high stress, full step planner is not implemented",
  "ownerVisualAcceptance":false
}
V023_CONTRACT
cat > "$DEST_REL/README.md" <<'V023_README'
# Hareworks v0.1.23: actual terrain hip-height IK and hillside collision measurement

Owner video 7739.mp4 showed **UNPINNED DYNAMIC GEOMETRY PREVIEW**, not physical IK; this is a failure of the physical initialization/runtime gate, not terrain IK success. Owner asks for hips that lower as needed to reach the ground, and visible hillside mesh collision prevention.

This campaign is a bounded incremental physical attempt. Contact targets are captured once in world space. At each 120Hz physical step, solve the intersection of the two true world-space leg-reach intervals and ground samples under both actual ankle targets. Move the pelvis within the common interval and bounded velocity; retain planted foot anchors and anterior knee-pole source shape. Measure the actual shin-to-terrain segment intrusion in addition to heel/sole/toe; a positive collision is reported and disqualifies a physical-contact PASS. Preserve all source and styling modules unchanged except the v0.1.23 viewer and immutable new pelvis solver. The actual uphill toe-to-rock collision response and full adaptive stepping planner are subsequent improvements; this is not claimed to solve arbitrary high obstacles.

The original game GLB and all existing gait versions remain untouched. This is a single versioned Android Termux Git campaign, exact upstream SHA, scoped new path, required tests, remote readback and visible cache-busted browser build. If physical startup fails, the preview is explicitly UNPINNED with the actual stage/error; no PASS or gait-owner approval is implied.
V023_README
# Model and immutable source file provenance before the test runner.
[ "$(git -C "$CHECKOUT" hash-object tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json)" = f6e8940b5eaeaf154a126eaa5221dcfcab0d94d1 ] || { echo 'BLOCKED_SOURCE_KNEE_REFERENCE_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object tools/hareworks-forward-woman/v0.1.3/foot-profile.json)" = 6febeaa8ff461806b590748dfca6461f4d8df1db ] || { echo 'BLOCKED_SOURCE_LEG_LINKS_CHANGED' >&2;exit 77; }
# Previously accepted foot heading and current knee governor stay byte-identical.
[ "$(git -C "$CHECKOUT" hash-object "$BUILDROOT/$DEST_REL/foot-heading.mjs")" = "$(git -C "$CHECKOUT" hash-object "$CHECKOUT/tools/hareworks-forward-woman/v0.1.18/foot-heading.mjs")" ] || { echo 'BLOCKED_APPROVED_FOOT_HEADING_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object "$BUILDROOT/$DEST_REL/source-knee-governor.mjs")" = eefc2b0b867778bb384eafe95af4e63d7caa2f6b ] || { echo 'BLOCKED_ACCEPTED_V020_KNEE_SOLVER_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object "$BUILDROOT/$DEST_REL/speed-gait.mjs")" = 0a06cf25367bbf945155cfd4756954a54194fec6 ] || { echo 'BLOCKED_ACCEPTED_SPEED_GAIT_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object "$BUILDROOT/$DEST_REL/foot-gait.mjs")" = ecc036c99f92dfa02b17a9457e76b0998a127c04 ] || { echo 'BLOCKED_TERRAIN_CAMPAIGN_MUTATED_FOOT_CONTACT' >&2;exit 77; }
python3 "$DEST_REL/patch.py" "$CHECKOUT" "$DEST_REL"
STAGE='test-terrain-world-ik'
# v016 already patched using exact published v015 source
:
python3 - "$DEST_REL/patch.py" "$DEST_REL/review-server.py" "$DEST_REL/startup-regression.py" <<'PYPARSE'
import pathlib,sys
for p in sys.argv[1:]:compile(pathlib.Path(p).read_text(),p,'exec')
print('PYTHON_SYNTAX_PASS')
PYPARSE
for f in root-motion.mjs foot-gait.mjs root-model-test.mjs contact-test.mjs viewer.mjs shoe-witness.mjs shoe-witness-test.mjs archived-root-regression.mjs foot-heading.mjs foot-heading-test.mjs source-knee-governor.mjs source-knee-governor-test.mjs knee-source-invariant-test.mjs speed-gait.mjs terrain-core.mjs terrain-core-test.mjs terrain-hip.mjs terrain-hip-test.mjs flat-parity-test.mjs;do
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
node "$DEST_REL/source-knee-governor-test.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/foot-profile.json"
node "$DEST_REL/source-speed-contact-test.mjs"
# Independent flat-source numerical parity across 1200 frames before testing rough terrain.
mkdir -p "$BUILDROOT/tools/hareworks-forward-woman/v0.1.20"
cp "$CHECKOUT/tools/hareworks-forward-woman/v0.1.20/foot-gait.mjs" "$CHECKOUT/tools/hareworks-forward-woman/v0.1.20/root-motion.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.20/"
node "$DEST_REL/flat-parity-test.mjs"
node "$DEST_REL/terrain-core-test.mjs"
node "$DEST_REL/terrain-hip-test.mjs"
# Hold the prior deterministic surface as an immutable reference; stronger profiles must be measurable.
[ "$(git -C "$CHECKOUT" hash-object "$CHECKOUT/$SOURCE_REL/terrain-core.mjs")" = 47a476db52f2bede12bf73309aeedb2c579adb3c ] || { echo 'BLOCKED_SOURCE_TERRAIN_NOT_VERIFIED' >&2;exit 77; }
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
git commit -m 'Hareworks v0.1.23 solve terrain hip reach and audit hillside obstruction'
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
[ "$(git rev-parse "FETCH_HEAD:$DEST_REL/source-knee-governor.mjs")" = "$(git rev-parse "HEAD:$DEST_REL/source-knee-governor.mjs")" ] || { echo 'BLOCKED_REMOTE_KNEE_GOVERNOR_BLOB_MISMATCH' >&2;exit 79; }
for terrain_file in terrain-core.mjs terrain-core-test.mjs terrain-hip.mjs terrain-hip-test.mjs flat-parity-test.mjs foot-heading.mjs patch.py index.html review-server.py;do
 [ "$(git rev-parse "FETCH_HEAD:$DEST_REL/$terrain_file")" = "$(git rev-parse "HEAD:$DEST_REL/$terrain_file")" ] || { echo "BLOCKED_REMOTE_TERRAIN_BLOB_MISMATCH=$terrain_file" >&2;exit 79; }
done
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
 for f in viewer.mjs foot-gait.mjs root-motion.mjs source-knee-governor.mjs terrain-core.mjs terrain-core-test.mjs terrain-hip.mjs terrain-hip-test.mjs flat-parity-test.mjs index.html;do
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
HTTP_TERRAIN_SHA="$(curl -fsS "http://127.0.0.1:$PORT/$DEST_REL/terrain-core.mjs" | sha256sum | awk '{print $1}')"
[ "$HTTP_TERRAIN_SHA" = "$(sha256sum "$DEST_REL/terrain-core.mjs" | awk '{print $1}')" ] || { echo 'BLOCKED_VIEWER_SERVES_WRONG_TERRAIN_MODULE' >&2;exit 80; }
HTTP_VIEWER_SHA="$(curl -fsS "http://127.0.0.1:$PORT/$DEST_REL/viewer.mjs" | sha256sum | awk '{print $1}')"
[ "$HTTP_VIEWER_SHA" = "$(sha256sum "$DEST_REL/viewer.mjs" | awk '{print $1}')" ] || { echo 'BLOCKED_VIEWER_SERVES_WRONG_LIVE_CONTROLLER' >&2;exit 80; }
[ "$(sha256sum "$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || { echo 'BLOCKED_HAREWORKS_GLB_CHANGED' >&2;exit 80; }
python3 - "$STATE" "$CAMPAIGN_ID" "$BASE_SHA" "$NEW_SHA" "$ENTRY_SHA" "$MODEL_SHA" "$URL" "$PORT" "$SERVER_PID" "$CHECKOUT" "$AGENTS_BLOB" "$ETIQUETTE_DOC" "$TOPDOWN_DOC" "$HTTP_SHA" "$PUBLISHED_REUSE" "$RECOVERED_R2_PARTIAL_INIT" <<'PYRECEIPT'
import datetime,json,pathlib,sys
(state,campaign,base,commit,entry,model,url,port,pid,checkout,agents,etiquette,topdown,viewer_hash,reused,recovered)=sys.argv[1:]
receipt={
 'campaign':campaign,'status':'PERSISTENT_CHECKOUT_AND_V023_TERRAIN_HIP_SOLVER_PUBLISHED_BROWSER_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sparseCheckout':False,
 'androidSharedStorageGitTrust':'exact-canonical-project-only, global safe.directory',
 'lfsStatusGuard':'Git LFS filters configured locally; only exactly SHA-verified tracked Hareworks binary is admissible as unstaged model materialization',
 'lfsStatusGuardDoesNotHideChanges':True,
 'previousIncompleteGitInitRecovered':recovered=='1',
 'protectedGait':'v0.1.22 knee, foot-heading, contacts and roots unchanged; pelvis reach solver and shin-collision audits added as v0.1.23',
 'shoeWitnesses':'v0.1.14 whole skinned foot low-surface longitudinal PCA bands, preserved unchanged',
 'calibrationFailureBehavior':'source procedural preview moving but explicitly UNPINNED and unapproved',
 'camera':'orbit and zoom with world-target follow',
 'unrelatedReplLfsFetched':False,'hareworksCopyPolicy':'exactly one verified worktree model, reusable private LFS cache',
 'rulesReadInAuthoringTurn':{'AGENTSBlob':agents,'CampaignEtiquetteDocument':etiquette,'TopDownEtiquetteDocument':topdown},
 'viewerUrl':url,'viewerPid':int(pid),'viewerPort':int(port),'viewerGaitSha256':viewer_hash,
 'alreadyPublishedRerun':reused=='1','browserRealSkinnedFootAudit':'PENDING; startup preview mode is not a physics audit',
 'actualSkinned3dPhysicsTestedInTermux':False,
 'contactGate':'PENDING_BROWSER_STRESS_AUDIT; actual heel/sole/toe terrain clearance is not established by script syntax tests','gaitResemblanceGate':'PENDING_OWNER_VISUAL_ACCEPTANCE; diagnostic preview expressly NOT acceptable as physical ground pinning',
 'ownerVisualAcceptance':False,'canonicalModelUnchanged':True}
p=pathlib.Path(state)/'latest-receipt.json'
p.write_text(json.dumps(receipt,indent=2)+'\n')
print('RECEIPT='+str(p))
PYRECEIPT
STAGE='review-ready-owner-verdict-pending'
echo "CHECKOUT_READY=$CHECKOUT"
echo 'NORMAL_GIT_CHECKOUT=YES'
echo "TERRAIN_IK_REVIEW_ROOT=$CHECKOUT/$DEST_REL"
echo "MODEL_SHA256=$MODEL_SHA"
echo "PUBLISHED_COMMIT=$NEW_SHA"
echo "SCRIPT_SHA256=$ENTRY_SHA"
echo "VIEWER_PID=$SERVER_PID"
echo "VIEWER_URL=$URL"
echo "PHYSICAL_TERRAIN_JS_SHA256=$HTTP_TERRAIN_SHA"
echo "LIVE_VIEWER_JS_SHA256=$HTTP_VIEWER_SHA"
echo 'CAMERA_ORBIT=RESTORED_SOURCE_CODE__PHONE_INTERACTION_PENDING'
echo 'TERRAIN_SURFACES=PROFILE_RIDGES_PROFILE_STEPS_PROFILE_RAMP_PLUS_LEGACY__MAX_STRENGTH_300_PERCENT'
echo 'CONTACT_GATE=PENDING_REAL_BROWSER_STRESS_AUDIT__PREVIEW_IS_UNPINNED_IF_PHYSICS_FAILS'
echo 'GAIT_RESEMBLANCE_GATE=PENDING_OWNER_VISUAL_ACCEPTANCE'
if command -v termux-open-url >/dev/null 2>&1;then
 termux-open-url "$URL" || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
elif command -v am >/dev/null 2>&1;then
 am start -a android.intent.action.VIEW -d "$URL" >/dev/null 2>&1 || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
fi
