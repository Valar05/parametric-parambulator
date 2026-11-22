#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_ANATOMICAL_FOOTFALL_v0.1.17_DOCUMENTS
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_ANATOMICAL_FOOTFALL_v0.1.17_DOCUMENTS'
VERSION='v0.1.17'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='57f3e2dae16a6eb3b6614039da7fc158542e3c52'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-anatomical-footfall-v0.1.17-v1-documents"
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
  grep -q 'hareworks-v0.1.17-anatomical-world-footfall' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
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
[ -f tools/hareworks-forward-woman/v0.1.16/viewer.mjs ] || { echo 'BLOCKED_MISSING_SOURCE_GAIT_BASELINE' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.16/viewer.mjs)" = 42d83baf72c4a2cf87b025863a8ac017df0b0d9f ] || { echo 'BLOCKED_PUBLISHED_V016_SOURCE_CHANGED' >&2;exit 74; }
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
 TEMP_MODEL="$MODEL.r17-verified-${ENTRY_SHA:0:12}.tmp"
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
STAGE='generate-v017-anatomical-world-footfall'
SOURCE_REL='tools/hareworks-forward-woman/v0.1.16'
[ -d "$CHECKOUT/$SOURCE_REL" ] || { echo 'BLOCKED_MISSING_PUBLISHED_V016_SOURCE' >&2; exit 77; }
cp -R "$CHECKOUT/$SOURCE_REL" "$DEST_REL"
for old_launcher in "$DEST_REL"/campaign-*.sh;do [ -f "$old_launcher" ] && rm -- "$old_launcher" || :;done
cp "$ENTRY" "$DEST_REL/campaign-v0.1.17-v1-godotprojects.sh"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.2" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3"
cat > "$DEST_REL/speed-gait.mjs" <<'V017_SPEED'
/* v0.1.17: calibrated full left+right gait-cycle step planner.
 * v0.1.16 erroneously multiplied hip-to-ankle Z by 0.66 at ordinary speed,
 * forcing excessive knee flexion. Preserve the source leg's actual anatomical
 * reach and use WORLD footfall distance + cadence to vary travel speed.
 * The viewer keeps the approved v0.1.16 procedural toe/yaw orientation. */
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const smooth=x=>{const t=clamp(x,0,1);return t*t*(3-2*t)};
export const REF_WALK_SPEED=.52;
export function speedGait(speed,referenceStride){
 if(!Number.isFinite(speed)||speed<0||speed>5||!Number.isFinite(referenceStride)||referenceStride<.9||referenceStride>1.55)
  throw Error('V017_FOOTFALL_INPUT_INVALID');
 // Do not extrapolate anatomical stride past the nearly fully extended archived legs.
 // For travel speed .52, exactly retain the accepted v0.1.9 leg trajectory.
 // Slow walk: gently shorten WORLD footfall distance, not hip-to-ankle reach.
 const low=clamp(speed/REF_WALK_SPEED,0,1),high=clamp((speed-REF_WALK_SPEED)/.28,0,1);
 const stride=referenceStride*(.90+.10*low+.012*high);
 const cadence=speed>0?speed/stride:0;
 const lead=smooth((speed-.16)/.64);
 return {speed,stride,cadence,phaseRate:cadence,scale:stride/referenceStride,
   crossover:.014+.014*lead,stanceDuty:.615-.035*lead,
   liftFactor:.90+.12*lead,referenceStride,
   stepDistance:stride/2,
   source:'original v0.1.9 leg reach; world planted footfalls; no leg-Z compression'};
}
export function blendMotion(previous,target,dt){
 if(!previous)return {...target};
 if(!Number.isFinite(dt)||dt<0)throw Error('V017_DYNAMIC_GAIT_DT_INVALID');
 const k=1-Math.exp(-Math.min(dt,.1)/.22),out={...target};
 for(const key of ['stride','scale','crossover','stanceDuty','liftFactor'])
  out[key]=previous[key]+(target[key]-previous[key])*k;
 out.stepDistance=out.stride/2;
 out.cadence=target.speed>0?target.speed/out.stride:0;
 out.phaseRate=out.cadence;
 return out;
}
export function adjustAnkleForSpeed(hip,ankle,side,motion){
 if(!['left','right'].includes(side)||!hip||!ankle||hip.length!==3||ankle.length!==3||!motion)
  throw Error('V017_SOURCE_LANDMARK_INVALID');
 const leading=smooth(((ankle[2]-hip[2])+.07)/.34),sign=side==='left'?-1:1;
 // Preserve ankle Y and Z EXACTLY. Their 3D distance to the hip determines
 // nearly straight support legs. Only gentle runway placement changes X.
 return [ankle[0]+sign*motion.crossover*(.28+.72*leading),ankle[1],ankle[2]];
}
export function transformSourceFoot(s,side,motion){
 if(!motion||!s||!s.ankle||!s.hip)throw Error('V017_SOURCE_FOOT_MISSING');
 const a=adjustAnkleForSpeed(s.hip,s.ankle,side,motion),shiftX=a[0]-s.ankle[0];
 const adapt=name=>{
  const p=s[name];if(!p||p.length!==3)throw Error('V017_SOURCE_NO_'+name);
  // Rigid X shift of all skinned foot patches; never shorten toe/heel rocker.
  return [p[0]+shiftX,p[1],p[2]];
 };
 return {...s,ankle:a,heel:adapt('heel'),sole:adapt('sole'),toe:adapt('toe')};
}
export function rootStepDistance(rootAt,curve,oldPhase,newPhase,motion){
 if(newPhase<oldPhase||!curve||!motion||motion.referenceStride!==curve.stride)
  throw Error('V017_WORLD_ROOT_PHASE_CONTRACT');
 // Full-cycle root displacement changes with speed, while world stance anchors
 // do not. The original phase-varying velocity profile remains intact.
 return (rootAt(curve,newPhase)-rootAt(curve,oldPhase))*motion.scale;
}
V017_SPEED
cat > "$DEST_REL/dynamic-gait-test.mjs" <<'V017_SPEED_TEST'
import assert from 'node:assert/strict';
import {speedGait,blendMotion,transformSourceFoot,rootStepDistance} from './speed-gait.mjs';
const D=1.224546;
const slow=speedGait(.30,D),normal=speedGait(.52,D),fast=speedGait(.8,D);
assert(slow.stride<normal.stride&&normal.stride<fast.stride,'world step distances must differ');
assert(slow.cadence<normal.cadence&&normal.cadence<fast.cadence);
assert.equal(normal.stride,D,'default preserves accepted full leg stride');
assert.equal(normal.scale,1);
assert(slow.scale>.95&&fast.scale<1.02,'stride must stay in real anatomical reach envelope');
assert(Math.abs(normal.stepDistance-D/2)<1e-12);
for(const speed of [.01,.15,.3,.52,.7,.8]){
 const m=speedGait(speed,D),test={hip:[.07,.89,.11],knee:[.02,.5,.21],ankle:[.10,.18,.40],heel:[.11,.1,.32],sole:[.10,.1,.41],toe:[.1,.11,.51]};
 for(const side of ['left','right']){
  const t=transformSourceFoot(test,side,m);
  assert.equal(t.ankle[2],test.ankle[2],'forbidden: hip-to-ankle Z compression');
  assert.equal(t.ankle[1],test.ankle[1],'forbidden: adjust ankle height');
  for(const part of ['heel','sole','toe']){
   assert.equal(t[part][2],test[part][2]);assert.equal(t[part][1],test[part][1]);
  }
 }
 assert(Math.abs(m.cadence*m.stride-speed)<1e-11,'speed is physical travel rate');
}
const curve={stride:D},linear=(_,q)=>D*q;
let state=speedGait(.52,D),q=0,world=0;
for(const requested of [.30,.8,.52,0,.8,.30])for(let j=0;j<240;j++){
 state=blendMotion(state,speedGait(requested,D),1/120);
 const nq=q+state.cadence/120,dist=rootStepDistance(linear,curve,q,nq,state);
 assert(Number.isFinite(dist)&&dist>=-1e-12&&dist<.015);
 world+=dist;q=nq;
}
assert(world>1);
assert.throws(()=>speedGait(NaN,D));
console.log('V017_ACTUAL_FOOTFALL_STRIDE_AND_CADENCE_PASS slow='+slow.stepDistance.toFixed(4)+' middle='+normal.stepDistance.toFixed(4)+' fast='+fast.stepDistance.toFixed(4));
console.log('V017_ORIGINAL_LEG_REACH_UNCOMPRESSED_AND_SPEED_TRANSITIONS_PASS');
V017_SPEED_TEST
cat > "$DEST_REL/source-speed-contact-test.mjs" <<'V017_CONTACT_TEST'
import assert from 'node:assert/strict';
import {SourceFootContact} from './foot-gait.mjs';
import {speedGait,transformSourceFoot} from './speed-gait.mjs';
const n=60,original=Array.from({length:n},(_,i)=>{
 const q=i/n,theta=q*2*Math.PI,ankle=[.11,.18,.37*Math.sin(theta)];
 return {phase:q,hip:[.06,.91,0],knee:[.11,.54,.1],ankle,
   heel:[ankle[0],.01,ankle[2]-.12],sole:[ankle[0],0,ankle[2]],toe:[ankle[0],.01,ankle[2]+.12],q:[0,0,0,1]};
});
let foot=[.1,.19,0],contact=new SourceFootContact({samples:original,
 gait:{start:.1,duty:.58},sourceGround:0,
 readWitness:key=>key==='ankle'?foot.slice():[.04,0,1.2],
 transformSource:(s,gait)=>transformSourceFoot(s,'left',gait)});
let pin=null,planted=0,updates=0,lastDuty=null;
for(let i=0;i<900;i++){
 const requested=i<300?.30:i<600?.8:.52, gait=speedGait(requested,1.224546);
 const x=contact.step({phase:(i/300)%1,totalPhase:i/300,worldZ:i*.001,gait});
 if(x.planted){if(pin!==null)assert.deepEqual(x.anchor,pin,'planted anchor moved');pin=x.anchor;planted++;}
 else pin=null;
 if(lastDuty!==null&&lastDuty!==contact.activeDuty){updates++;assert(pin!==null);}
 lastDuty=contact.activeDuty;
}
assert(planted>180&&updates>=2&&contact.transitions>3);
console.log('V017_PLANTED_WORLD_CONTACT_STAYS_FIXED_SPEED_CHANGES_PASS transitions='+contact.transitions);
V017_CONTACT_TEST
cat > "$DEST_REL/real-knee-envelope-test.mjs" <<'V017_KNEE_TEST'
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {speedGait,transformSourceFoot} from './speed-gait.mjs';
const data=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const profile=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
assert(data.samples.length===60&&data.sourceSha256===profile.sourceSha256);
const norm=v=>Math.hypot(...v);
const angle=(L1,L2,dist)=>{
 const c=Math.max(-1,Math.min(1,(L1*L1+L2*L2-dist*dist)/(2*L1*L2)));
 return 180-Math.acos(c)*180/Math.PI;
};
for(const speed of [.15,.30,.52,.80]){
 const motion=speedGait(speed,1.224546);
 for(const side of ['left','right']){
  let maxExtra=0,maxDelta=0;
  for(const frame of data.samples){
   const leg=frame.legs[side],L1=profile[side].upperLength,L2=profile[side].lowerLength;
   const src={...leg,heel:leg.ankle,sole:leg.ankle,toe:leg.toe};
   const adapted=transformSourceFoot(src,side,motion);
   const d0=norm(leg.ankle.map((x,i)=>x-leg.hip[i]));
   const d1=norm(adapted.ankle.map((x,i)=>x-leg.hip[i]));
   const extra=angle(L1,L2,d1)-angle(L1,L2,d0);
   maxExtra=Math.max(maxExtra,extra);maxDelta=Math.max(maxDelta,Math.abs(extra));
  }
  assert(maxExtra<5.5&&maxDelta<6.0,'V017_KNEE_SOURCE_DEVIATION_EXCESS '+side+' speed='+speed+' max='+maxExtra);
  console.log('V017_ORIGINAL_RIG_KNEE_ENVELOPE_PASS side='+side+' speed='+speed+' peakExtra='+maxExtra.toFixed(3));
 }
}
V017_KNEE_TEST
cat > "$DEST_REL/patch.py" <<'V017_PATCH'
#!/usr/bin/env python3
"""Pinned v0.1.17-only v0.1.17 correction. Does NOT edit history or model."""
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);dest=Path(sys.argv[2]);p=dest/'viewer.mjs'
s=p.read_text()
def one(old,new):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError('V017_PINNED_VIEWER_ANCHOR_'+str(n)+'_'+old[:90])
 s=s.replace(old,new,1)
# All accepted v0.1.16 runway toe-vector and foot-yaw calculations remain.
assert s.count('runwayFootQ(')>=2
assert "OrbitControls" in s
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
# The old code compressed source ankle hip-relative Z to reduce stride. The new
# speed-gait module deliberately DOES NOT edit ankle Z/Y. Root distance varies.
one('/* v0.1.16. ONE moving Walking_Woman.',
    '/* v0.1.17. ONE moving Walking_Woman.')
one('let dynamicMotion=null; // speed-dependent stride geometry, cadence and crossover; not clip-time scaling',
    'let dynamicMotion=null; // speed changes measured world footfall spacing, never compresses the leg')
# Restore accepted source foot yaw in BOTH physical IK and fallback preview;
# the v0.1.16 foot-orientation code itself is deliberately byte-identical.
one('const target=H.clone().add(V(...rotateY(v.ankleLocal,yaw)));',
    'const target=H.clone().add(V(...rotateY(v.ankleLocal,yaw)));') if False else None
# Correct HUD to distinguish actual planned full-cycle distance, half-cycle
# landing separation and cadence. No claim made from a slider label alone.
one('cadence ${cadenceFor(speed,dynamicMotion?.stride||stride).toFixed(3)} cycles/s, stride ${(dynamicMotion?.stride||stride).toFixed(3)}',
    'cadence ${cadenceFor(speed,dynamicMotion?.stride||stride).toFixed(3)} cycles/s, planned step ${(dynamicMotion?.stepDistance||stride/2).toFixed(3)} u, measured step ${latestStepSpacing===null?"pending":latestStepSpacing.toFixed(3)} u, full cycle ${(dynamicMotion?.stride||stride).toFixed(3)}')
one('stride ${(dynamicMotion?.stride||stride).toFixed(3)} u/full cycle · cadence',
    'full-cycle root stride ${(dynamicMotion?.stride||stride).toFixed(3)} u, planned half-cycle step ${(dynamicMotion?.stepDistance||stride/2).toFixed(3)} u · cadence')
# The speed-audit previously tested 1.18u/s despite UI max .8u/s. Audit REAL
# selectable speeds only, with the actual skinned IK and measured per-cycle root.
# Measure actual alternating-foot touchdown spacing; planned step length alone is not a real step.
one('const trackedFollow=V(0,.90,0);',
    'let footfallHistory=[],lastContactTransition={left:-1,right:-1},latestStepSpacing=null;\nconst trackedFollow=V(0,.90,0);')
one('const targets=contactTargets();adjustReach(targets);const feet={};',
    '''const targets=contactTargets();adjustReach(targets);const feet={};
 for(const side of ['left','right']){
  const c=worldContacts[side],t=targets[side];
  if(t.planted&&c.transitions!==lastContactTransition[side]&&t.anchor){
   lastContactTransition[side]=c.transitions;
   const touchdown={side,z:t.anchor[2],phase:totalPhase};
   const prev=footfallHistory.at(-1);
   if(prev&&prev.side!==side)latestStepSpacing=Math.abs(touchdown.z-prev.z);
   footfallHistory.push(touchdown);if(footfallHistory.length>16)footfallHistory.shift();
  }
 }''')
one('function clearStats(){maxDrift=0;',
    'function clearStats(){footfallHistory=[];lastContactTransition={left:-1,right:-1};latestStepSpacing=null;maxDrift=0;')
one('for(const requested of [.30,.52,1.18]){',
    'for(const requested of [.30,.52,.80]){')
one('speedMatrix.push({requested,realTime,travel:worldZ,',
    'speedMatrix.push({requested,realTime,travel:worldZ,measuredLastFootfall:latestStepSpacing,')
# Keep the real 120Hz physics, planted world contacts and owner verdict separate.
assert 'physicsStep(1/120)' in s
assert "motionMode='PHYSICAL_GROUND_PINNING'" in s
assert 'window' not in s[:0]
s=s.replace('v0.1.16','v0.1.17').replace('V0.1.16','V0.1.17')
p.write_text(s.rstrip()+'\n')
# Retain all v0.1.16 foot orientation/IK/ground pinning modules unchanged;
# the root's physical distance/cadence comes only from new speed-gait.mjs.
p=dest/'index.html';t=p.read_text().replace('v0.1.16','v0.1.17')
t=t.replace('The travel-speed slider changes stride length, cadence, lateral crossover and landing geometry.',
'''The travel-speed slider changes physical world footfall spacing and cadence. Anatomical leg reach stays faithful to the source at the default speed, with actual ground contacts preserved.''')
t=t.replace('v0.1.16-dynamic-physics','v0.1.17-anatomical-footfalls')
p.write_text(t.rstrip()+'\n')
p=dest/'review-server.py';t=p.read_text().replace('v0.1.16','v0.1.17');p.write_text(t.rstrip()+'\n')
# Remove old version's author-specific regression module when superseded.
for file in ['dynamic-gait-test.mjs','source-speed-contact-test.mjs']:
 assert (dest/file).is_file()
# Never touch copied originals anywhere outside this new directory.
for file in dest.rglob('*'):
 if file.is_file() and file.suffix in ('.mjs','.py','.json','.md','.html','.sh'):
  file.write_bytes(file.read_bytes().rstrip(b'\r\n')+b'\n')
print('V017_PINNED_PATCH_PASS source=v0.1.16 footYaw=UNCHANGED hipAnkleZ=SOURCE_PRESERVED')
V017_PATCH
cat > "$DEST_REL/README.md" <<'V017_README'
# Hareworks v0.1.17: anatomical reach + measured world footfall stride

User rejected v0.1.17: knee flexion became much larger, while the visible stride did not behave dynamically. User specifically approved the v0.1.17 foot direction. Preserve it.

**Root cause:** v0.1.17 multiplied the source ankle's hip-relative forward position by `0.42 + 0.58*(speed/1.26677)`, producing a 0.658 stretch at the default `0.52` viewer speed. Inverse kinematics collapsed the knees. The apparent stride metric changed but source leg reach was destroyed.

**Correction:** Speed now controls target WORLD footfall separation and physical left+right cycle cadence, not the length of the thigh/shin geometry. At the default speed (`0.52 u/s`) the original v0.1.9 hip-to-ankle Y and Z are retained exactly, with gentle lateral runway crossover. At slower/faster speed the plan varies root travel per complete gait cycle, then cadence solves `speed = cadence * worldCycleDistance`. Planted skinned foot anchors remain unchanged when speed varies. Upper body, source knee pole and foot orientation from v0.1.17 are retained. The achievable speed range is bounded by measured anatomical reach; no extra limb straightening beyond physical length is implied.

Tests: compare original archived 60 source frames against speed-adjusted hip/ankle flexion in both legs. At each speed, verify foot-target Y/Z preserved and heel/sole/toe longitudinal rocker intact. Run nominal world-root and contact-step tests plus real 120Hz skinned browser audit for multiple speeds. Real-world visual verdict is the owner's, not numerical tests.

Authorized execution: verified single Android Termux Git entry, existing persistent `Documents/GodotProjects/parametric-parambulator`, versioned new v0.1.17 source only. No model edit, no historical gait edits, no reset, no force push. Exact remote Git readback is required.
V017_README
cat > "$DEST_REL/contract.json" <<'V017_CONTRACT'
{
  "schema":"hareworks-v0.1.17-anatomical-world-footfall",
  "repo":"Valar05/parametric-parambulator",
  "parent":"57f3e2dae16a6eb3b6614039da7fc158542e3c52",
  "sourceController":"tools/hareworks-forward-woman/v0.1.17/viewer.mjs",
  "sourceControllerBlob":"42d83baf72c4a2cf87b025863a8ac017df0b0d9f",
  "modelSha256":"a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "rulesAGENTSBlob":"547c2af52303f4efb718bbf8f82a698110c7bfca",
  "rulesCampaignEtiquetteDoc":"1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI",
  "rulesTopDownEtiquetteDoc":"1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU",
  "executionLane":"Android Termux Git only",
  "mutablePaths":["tools/hareworks-forward-woman/v0.1.17/"],
  "userApproved":"v0.1.17 foot toe direction / yaw, v0.1.9 runway movement baseline, orbit camera",
  "userRejected":"v0.1.17 overbent knees and speed slider not truly adaptive",
  "physicalMechanic":"world space stance anchors, measured source ankle trajectory, adaptive root travel and cadence; no ankle-Z compression",
  "review":"real 120Hz GLB leg, sole, heel, toe and footfall audits at speeds .30/.52/.80; visual acceptance pending",
  "canonicalModelModified":false,
  "ownerVisualAcceptance":false
}
V017_CONTRACT
python3 "$DEST_REL/patch.py" "$CHECKOUT" "$DEST_REL"
STAGE='patch-and-test-v017-anatomical-footfall'
# v016 already patched using exact published v015 source
:
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
node "$DEST_REL/dynamic-gait-test.mjs"
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
git commit -m 'Hareworks v0.1.17 preserve anatomical knee extension, physical footfall stride'
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
 'campaign':campaign,'status':'PERSISTENT_CHECKOUT_AND_V017_ANATOMICAL_FOOTFALL_PUBLISHED_REAL_BROWSER_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sparseCheckout':False,
 'androidSharedStorageGitTrust':'exact-canonical-project-only, global safe.directory',
 'lfsStatusGuard':'Git LFS filters configured locally; only exactly SHA-verified tracked Hareworks binary is admissible as unstaged model materialization',
 'lfsStatusGuardDoesNotHideChanges':True,
 'previousIncompleteGitInitRecovered':recovered=='1',
 'acceptedV019Math':'v0.1.9 original ankle + pelvis source Y/Z reach protected; speed controls world footfall and cadence; real 120Hz GLB audit pending',
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
echo "ANATOMICAL_WORLD_FOOTFALL_ROOT=$CHECKOUT/$DEST_REL"
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
