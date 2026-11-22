#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_BACKWARD_DIRECTION_v0.1.24_R3_DOCUMENTS
# r3 recovery: keep verified r2 BUILDROOT fixes and replace the stale copied
# v0.1.13 foot-gait test with a v0.1.23/24 API-correct unit regression.
# Previous r2 run stopped before installation/push on a missing named export.
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_BACKWARD_DIRECTION_v0.1.24_R3_DOCUMENTS'
VERSION='v0.1.24'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='ed4bae4ffbe713fc3170f4028708ff8a9992bbab'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-backward-direction-v0.1.24-r3-documents"
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
  grep -q 'hareworks-v0.1.24-directional-backward-second-slot' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
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
[ -f tools/hareworks-forward-woman/v0.1.23/viewer.mjs ] || { echo 'BLOCKED_MISSING_SOURCE_GAIT_BASELINE' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.23/viewer.mjs)" = 55d4073a74ad7d26a8ded6d68288f1f8555f9e58 ] || { echo 'BLOCKED_PUBLISHED_V023_SOURCE_CHANGED' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.23/terrain-core.mjs)" = 47a476db52f2bede12bf73309aeedb2c579adb3c ] || { echo 'BLOCKED_PUBLISHED_V023_TERRAIN_CHANGED' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.23/foot-gait.mjs)" = ecc036c99f92dfa02b17a9457e76b0998a127c04 ] || { echo 'BLOCKED_PUBLISHED_V021_FOOT_TARGET_CHANGED' >&2;exit 74; }
[ -f tools/hareworks-forward-woman/v0.1.9/viewer.mjs ] || { echo 'BLOCKED_MISSING_ACCEPTED_V024_REFERENCE' >&2;exit 74; }
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
 TEMP_MODEL="$MODEL.r24-verified-${ENTRY_SHA:0:12}.tmp"
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
STAGE='generate-v024-backward-procedural-controller'
SOURCE_REL='tools/hareworks-forward-woman/v0.1.23'
[ -d "$CHECKOUT/$SOURCE_REL" ] || { echo 'BLOCKED_SOURCE_V023_MISSING' >&2;exit 77; }
cp -R "$CHECKOUT/$SOURCE_REL" "$DEST_REL"
for old_launcher in "$DEST_REL"/campaign-*.sh;do [ -f "$old_launcher" ] && rm -- "$old_launcher" || :;done
cp "$ENTRY" "$DEST_REL/campaign-v0.1.24-r3-current-api-test-recovery.sh"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.2" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3"
# Path authority: before installation, DEST_REL exists ONLY inside BUILDROOT.
# The first phone run failed because the regression check mistakenly used
# git -C "$CHECKOUT" to locate a newly generated, as-yet-unpublished file.
STAGE='verify-v024-r3-staging-copy-before-patch'
[ "$(pwd -P)" = "$(readlink -f "$BUILDROOT")" ] || { echo 'BLOCKED_STAGING_CWD_MISMATCH' >&2;exit 77; }
[ ! -e "$CHECKOUT/$DEST_REL" ] || { echo 'BLOCKED_STAGING_ALREADY_IN_LIVE_CHECKOUT' >&2;exit 77; }
python3 - "$CHECKOUT/$SOURCE_REL" "$BUILDROOT/$DEST_REL" <<'V024_STAGING'
import hashlib,pathlib,sys
src,dst=[pathlib.Path(q) for q in sys.argv[1:]]
source={p.relative_to(src).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in src.rglob('*') if p.is_file() and not p.name.startswith('campaign-')}
staged={p.relative_to(dst).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dst.rglob('*') if p.is_file() and not p.name.startswith('campaign-')}
if source!=staged:
 missing=sorted(set(source)-set(staged));extra=sorted(set(staged)-set(source));changed=sorted(p for p in set(source)&set(staged) if source[p]!=staged[p])
 raise SystemExit('BLOCKED_STAGING_SOURCE_COPY_INCOMPLETE missing='+str(missing)+' extra='+str(extra)+' changed='+str(changed))
for mandatory in ('viewer.mjs','foot-heading.mjs','source-knee-governor.mjs','foot-gait.mjs','terrain-core.mjs','terrain-hip.mjs','review-server.py','index.html'):
 if mandatory not in staged:raise SystemExit('BLOCKED_STAGING_MANDATORY_MISSING_'+mandatory)
print('V024_R3_STAGING_COPY_BYTE_PARITY_PASS modules='+str(len(staged)))
V024_STAGING
STAGE='generate-v024-backward-procedural-controller'
cat > "$DEST_REL/reverse-gait.mjs" <<'V024_MODULE'
/* Hareworks v0.1.24: second cardinal locomotion slot, backward -Z.
 * The actor keeps forward +Z facing. The source data are startup calibration
 * samples, never an animation played on the visible rig. Backward contact
 * chronology is the reverse of the measured source chronology, with a reversed
 * root-velocity integral and reversed toe-to-heel rocker order.
 */
import {rootAt,phase01} from './root-motion.mjs';
export const DIRECTION_SLOTS=Object.freeze(['forward','backward']);
export function signForDirection(slot){
 if(!DIRECTION_SLOTS.includes(slot))throw Error('BACKWARD_UNKNOWN_DIRECTION_'+slot);
 return slot==='backward'?-1:1;
}
export function sourcePhase(slot,totalPhase){
 signForDirection(slot);
 return phase01(slot==='backward'?-totalPhase:totalPhase);
}
export function reversedSamples(bySide){
 if(!bySide||!['left','right'].every(s=>Array.isArray(bySide[s])&&bySide[s].length>=60))throw Error('BACKWARD_SOURCE_SAMPLES_MISSING');
 const out={};
 for(const side of ['left','right']){
  const a=bySide[side],n=a.length;
  out[side]=Array.from({length:n},(_,i)=>{
   const s=a[(n-i)%n];
   for(const key of ['ankle','hip','knee','heel','sole','toe'])
    if(!Array.isArray(s[key])||s[key].length!==3||!s[key].every(Number.isFinite))throw Error('BACKWARD_INVALID_SOURCE_'+key);
   if(!Array.isArray(s.q)||s.q.length!==4)throw Error('BACKWARD_INVALID_SOURCE_FOOT_QUATERNION');
   return {phase:i/n,ankle:s.ankle.slice(),hip:s.hip.slice(),knee:s.knee.slice(),
    heel:s.heel.slice(),sole:s.sole.slice(),toe:s.toe.slice(),q:s.q.slice()};
  });
 }
 return out;
}
export function reversedWindows(gaits){
 if(!gaits||!['left','right'].every(s=>gaits[s]&&Number.isFinite(gaits[s].start)&&Number.isFinite(gaits[s].duty)&&gaits[s].duty>.45&&gaits[s].duty<.73))
  throw Error('BACKWARD_SOURCE_STANCE_WINDOWS_INVALID');
 return Object.fromEntries(['left','right'].map(side=>{
  const g=gaits[side];return [side,{...g,start:phase01(-g.start-g.duty),
   method:'source-measured stance reversed in phase; foot rocker toe to heel'}];
 }));
}
export function backwardRootDelta(rootFn,curve,previous,next,motion){
 if(!curve||!motion||motion.referenceStride!==curve.stride||!Number.isFinite(previous)||!Number.isFinite(next)||next<previous)throw Error('BACKWARD_ROOT_CONTRACT_INVALID');
 const delta=(rootFn(curve,-next)-rootFn(curve,-previous))*motion.scale;
 if(!Number.isFinite(delta)||delta>Math.max(.005,(next-previous)*.25))throw Error('BACKWARD_ROOT_NONPHYSICAL_LOCAL_SPIKE');
 return delta;
}
export function signedTravelPass(slot,distance,expected,margin=.17){
 const sign=signForDirection(slot);
 if(!Number.isFinite(distance)||!Number.isFinite(expected)||expected<0)return false;
 return Math.abs(distance-sign*expected)<=margin;
}
V024_MODULE
cat > "$DEST_REL/reverse-gait-test.mjs" <<'V024_TEST'
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {sourcePhase,reversedSamples,reversedWindows,backwardRootDelta,signedTravelPass,signForDirection} from './reverse-gait.mjs';
import {rootAt} from './root-motion.mjs';
const N=360;
const source={left:[],right:[]};
for(let i=0;i<N;i++){
 const q=i/N;
 for(const side of ['left','right']){
  const p=q+(side==='left'?0:.5),z=-.21*Math.sin(2*Math.PI*p);
  source[side].push({phase:q,hip:[side==='left'?.08:-.08,.9,.08],knee:[side==='left'?.09:-.09,.6,.11],ankle:[side==='left'?.1:-.1,.20,z],
   heel:[side==='left'?.1:-.1,.05,z+.08],sole:[side==='left'?.1:-.1,.04,z],toe:[side==='left'?.1:-.1,.06,z-.08],q:[0,0,0,1]});
 }
}
const backwards=reversedSamples(source);
for(const side of ['left','right']){
 assert.notEqual(backwards[side],source[side]);
 for(let i=0;i<N;i++){
  let orig=source[side][(N-i)%N],b=backwards[side][i];
  for(const key of ['ankle','hip','knee','heel','sole','toe','q'])assert.deepEqual(b[key],orig[key]);
  assert.equal(b.phase,i/N);
 }
 // Stance relative ankle velocity reverses sign even though shoe headings do not.
 const forward=source[side][60].ankle[2]-source[side][59].ankle[2];
 const reverse=backwards[side][60].ankle[2]-backwards[side][59].ankle[2];
 assert(forward*reverse<0,side+' velocity not reversed');
}
const g={left:{start:.1,duty:.60},right:{start:.6,duty:.60}};
const rg=reversedWindows(g);
const circularDistance=(a,b)=>{const d=Math.abs(a-b)%1;return Math.min(d,1-d);};
assert(Math.abs(rg.left.start-.30)<1e-12);
assert(Math.abs(rg.right.start-.80)<1e-12);
for(const side of ['left','right'])for(let i=0;i<N;i++){
 let q=i/N,original=(q-g[side].start+1)%1<g[side].duty;
 let newQ=(1-q)%1,backward=(q-rg[side].start+1)%1<rg[side].duty;
 // Avoid the exact boundaries, where discrete samples differ by one tick.
 if(Math.min(circularDistance(q,g[side].start),circularDistance(q,g[side].start+g[side].duty))>.008)
  assert.equal(original,((1-q-rg[side].start+2)%1)<rg[side].duty,'involutive phase reversal');
}
assert.equal(sourcePhase('backward',.25),.75);
assert.equal(sourcePhase('forward',.25),.25);
assert.equal(signForDirection('backward'),-1);
assert.throws(()=>sourcePhase('left',.25));
const positions=Array.from({length:121},(_,i)=>1.24*(i/120)+.045*Math.sin(2*Math.PI*i/120));
const curve={n:120,stride:1.24,positions};
const m={referenceStride:1.24,scale:1};
for(let i=0;i<720;i++){
 const old=i/120,now=(i+1)/120;
 const dz=backwardRootDelta(rootAt,curve,old,now,m);
 assert(dz<=0,'backward world root must travel negative');
 const opposite=rootAt(curve,-now)-rootAt(curve,-old);
 assert(Math.abs(dz-opposite)<1e-9);
}
assert(Math.abs(backwardRootDelta(rootAt,curve,0,3,m)+3*curve.stride)<1e-8);
assert(signedTravelPass('backward',-.52,.52,.01));
assert(!signedTravelPass('backward',.52,.52,.01));
assert(signedTravelPass('forward',.52,.52,.01));
const archivePath=process.argv[2];
if(archivePath){
 const archive=JSON.parse(fs.readFileSync(archivePath,'utf8'));
 assert.equal(archive.sourceClip,'Walking_Woman');
 assert.equal(archive.samples.length,60);
 for(const side of ['left','right']){
  let signBefore=0,signAfter=0;
  const src=archive.samples.map(s=>s.legs[side].ankle[2]);
  const rv=src.map((_,i)=>src[(60-i)%60]);
  for(let i=0;i<60;i++){
   const k=(i+1)%60;signBefore+=Math.abs(src[k]-src[i]);signAfter+=Math.abs(rv[k]-rv[i]);
  }
  assert(Math.abs(signBefore-signAfter)<1e-9);
 }
}
console.log('V024_BACKWARD_PHASE_ROOT_CONTACT_TEST_PASS samples='+N+' sourceArchive='+Boolean(archivePath));
V024_TEST
cat > "$DEST_REL/backward-contact-test.mjs" <<'V024_CONTACT_TEST'
import assert from 'node:assert/strict';
import {SourceFootContact} from './foot-gait.mjs';
const n=120;
const make=()=>Array.from({length:n},(_,i)=>{
 const q=i/n,p=(q-.10+1)%1;
 let h=.01,t=.01;
 if(p<.17){h=.06;t=0;}
 else if(p>.43&&p<.60){h=0;t=.06;}
 return {phase:q,hip:[0,.9,0],knee:[0,.55,.06],ankle:[0,.2,Math.cos(2*Math.PI*q)*.15],
  heel:[0,h,0],sole:[0,0,0],toe:[0,t,0],q:[0,0,0,1]};
});
const samples=make(),gait={start:.1,duty:.60},readWitness=kind=>[0,0,0];
const back=new SourceFootContact({samples,gait,sourceGround:0,readWitness,rootAt:()=>0,reverseRocker:true});
const first=back.step({phase:.12,totalPhase:.12,worldZ:0});
const middle=back.step({phase:.35,totalPhase:.35,worldZ:0});
const last=back.step({phase:.60,totalPhase:.60,worldZ:0});
assert.equal(first.pivot,'toe','backward initial ground contact must be toe');
assert.equal(middle.pivot,'sole','backward middle contact must roll onto sole');
assert.equal(last.pivot,'heel','backward last contact must roll onto heel');
assert.equal(first.planted,true);assert.equal(last.planted,true);
const forward=new SourceFootContact({samples,gait,sourceGround:0,readWitness,rootAt:()=>0});
forward.step({phase:.12,totalPhase:.12,worldZ:0});
const fp=forward.step({phase:.60,totalPhase:.60,worldZ:0});
assert.equal(fp.pivot,'toe','protected forward default must retain monotonic heel-to-toe restriction');
console.log('V024_REVERSE_ROCKER_TOE_SOLE_HEEL_PASS');
V024_CONTACT_TEST
cat > "$DEST_REL/patch.py" <<'V024_PATCH'
#!/usr/bin/env python3
"""Strict v0.1.23 to v0.1.24 backward-slot patch, forward baseline immutable."""
import pathlib,sys
root=pathlib.Path(sys.argv[1]);dest=pathlib.Path(sys.argv[2]);p=dest/'viewer.mjs';s=p.read_text()
def once(old,new):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError(f'V024_VIEWER_PINNED_ANCHOR_{n}_'+old[:120])
 s=s.replace(old,new,1)
assert 'OrbitControls' in s and 'sourceKnee' not in s[:0] and 'GLTFLoader' in s
assert 'new THREE.AnimationMixer(actor)' not in s
once('/* v0.1.23. ONE moving Walking_Woman.','/* v0.1.24. ONE moving Walking_Woman.')
once("import {distalHeading} from './foot-heading.mjs';", "import {distalHeading} from './foot-heading.mjs';\nimport {sourcePhase,reversedSamples,reversedWindows,backwardRootDelta,signedTravelPass,signForDirection} from './reverse-gait.mjs';")
once('const terrainArgs=new URLSearchParams(location.search);',
"""const terrainArgs=new URLSearchParams(location.search);
// Direction changes must restart the physical world contact run. No instant
// sign flip of a planted anchor; the forward branch uses its original math.
const directionMode=terrainArgs.get('move')==='forward'?'forward':'backward';
const backward=()=>directionMode==='backward';
const bodyPhase=p=>sourcePhase(directionMode,p);""")
# Fallback must be visually moving backwards but must NEVER assert real contact.
once("let terrainMode=TERRAIN_MODES.includes(terrainArgs.get('terrain'))?terrainArgs.get('terrain'):'profile-ridges';",
     "let terrainMode=TERRAIN_MODES.includes(terrainArgs.get('terrain'))?terrainArgs.get('terrain'):(backward()?'flat':'profile-ridges');")
once('worldZ+=(nextCycle-previewCycle)*dynamicMotion.stride;',
     'worldZ+=signForDirection(directionMode)*(nextCycle-previewCycle)*dynamicMotion.stride;')
once('previewCycle=nextCycle;phase=mod1(previewCycle);\n frameBody(phase);\n const q=phase*clipDuration,yaw=independentPose(pelvisProfile,q).pelvisYaw;',
"""previewCycle=nextCycle;phase=mod1(previewCycle);
 frameBody(bodyPhase(previewCycle));
 const q=bodyPhase(previewCycle)*clipDuration,yaw=independentPose(pelvisProfile,q).pelvisYaw;""")
# Pose source remains the calibrated originals, sampled in reverse chronology.
once('const yaw=independentPose(pelvisProfile,phase*clipDuration).pelvisYaw;',
    'const yaw=independentPose(pelvisProfile,bodyPhase(totalPhase)*clipDuration).pelvisYaw;')
once('const footFit=independentPose(pelvisProfile,phase*clipDuration).feet[side];',
    'const footFit=independentPose(pelvisProfile,bodyPhase(totalPhase)*clipDuration).feet[side];')
once('worldZ+=rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);',
    'worldZ+=backward()?backwardRootDelta(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion):rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);')
once('totalPhase=newPhase;phase=mod1(totalPhase);frameBody(phase);',
    'totalPhase=newPhase;phase=mod1(totalPhase);frameBody(bodyPhase(totalPhase));')
once('if(lastHipSolve.feasible){groundLift+=lastHipSolve.delta;frameBody(phase)}',
    'if(lastHipSolve.feasible){groundLift+=lastHipSolve.delta;frameBody(bodyPhase(totalPhase))}')
once("  terrainAt:terrainMode==='flat'?null:terrainAt,", "  terrainAt:terrainMode==='flat'?null:terrainAt,reverseRocker:backward(),")
# Physical derivation: rootCurve must be built from ORIGINAL forward source
# before deriving backward samples and reversed contact windows.
once('rootCurve=buildRootCurve(baseline,sourceGaits);stride=rootCurve.stride;',
"""rootCurve=buildRootCurve(baseline,sourceGaits);stride=rootCurve.stride;
// Keep exact forward source intact in previous version. Backward samples are
// reverse-indexed source measurements, with mirrored stance chronology.
if(backward()){
 sourceSamples=reversedSamples(sourceSamples);
 sourceGaits=reversedWindows(sourceGaits);
}
const forwardSourceCommit='ed4bae4ffbe713fc3170f4028708ff8a9992bbab';""")
# Honest negative displacement instead of failing positive-only forward gate.
once("if(!Number.isFinite(travelled)||travelled<.04)throw Error('NO_OBSERVABLE_WORLD_TRAVEL_AT_STARTUP '+travelled);",
"if(!Number.isFinite(travelled)||signForDirection(directionMode)*travelled<.04)throw Error('NO_OBSERVABLE_DIRECTIONAL_WORLD_TRAVEL_AT_STARTUP '+travelled);")
once("if(terrainMode!=='flat'&&worldZ-terrainCenterZ>14)rebuildTerrain(Math.floor(worldZ/14)*14);",
"if(terrainMode!=='flat'&&Math.abs(worldZ-terrainCenterZ)>14)rebuildTerrain(Math.round(worldZ/14)*14);")
# Shared review/gates accept signed travel. A negative root is correct backward.
once('maxTrailingExtensionDeficit=Math.max(maxTrailingExtensionDeficit,Math.max(0,actualRelative-sourceRelative));',
     'maxTrailingExtensionDeficit=Math.max(maxTrailingExtensionDeficit,Math.max(0,signForDirection(directionMode)*(actualRelative-sourceRelative)));')
once('worldZ>speedGait(speed,stride).stride*2.70',
     'signForDirection(directionMode)*worldZ>speedGait(speed,stride).stride*2.70')
once('Math.abs(worldZ/realTime-requested)<.17',
     'signedTravelPass(directionMode,worldZ/realTime,requested,.17)')
once('nominalForwardAdvance:worldZ,generatedAnimationMixerCount:0',
     'directionSlot:directionMode,expectedTravelSign:signForDirection(directionMode),signedWorldAdvance:worldZ,generatedAnimationMixerCount:0')
once("schema:'hareworks-woman-accepted-v019-world-pin-v0.1.23'",
     "schema:'hareworks-v0.1.24-directional-two-of-eight'")
once("a.download='hareworks-woman-accepted-v019-world-pin-v0.1.23.json'",
     "a.download='hareworks-v0.1.24-'+directionMode+'-world-pin.json'")
once("status('PHYSICAL IK ON '+terrainMode.toUpperCase()+' AT '",
     "status('PHYSICAL '+directionMode.toUpperCase()+' WALK IK ON '+terrainMode.toUpperCase()+' AT '")
once("$('identity').textContent=`v0.1.23 ACCEPTED V019 SOURCE ROOT + HONEST RUNNING PREVIEW",
     "$('identity').textContent=`v0.1.24 ${directionMode.toUpperCase()} DIRECTIONAL IK · TWO OF EIGHT CARDINAL SLOTS · PHYSICAL STATUS SEPARATE · SOURCE WALKING_WOMAN PHASE CALIBRATION · V019 SOURCE ROOT + HONEST RUNNING PREVIEW")
once('function updateMotionStatus(){',
"""$('directionMode').value=directionMode;
$('directionMode').onchange=()=>{
 const u=new URL(location.href);u.searchParams.set('move',$('directionMode').value);
 location.assign(u.toString()); // new world run, no planted-anchor teleport
};
function updateMotionStatus(){""")
once("$('motionStatus').textContent='PHYSICAL TERRAIN IK UNAVAILABLE · UNPINNED PREVIEW ONLY · '",
     "$('motionStatus').textContent=directionMode.toUpperCase()+' PHYSICAL TERRAIN IK UNAVAILABLE · UNPINNED PREVIEW ONLY · '")
once('}else $(\'motionStatus\').textContent=`DYNAMIC SOURCE-ANCHORED FOOT PATH',
     '}else $(\'motionStatus\').textContent=`${directionMode.toUpperCase()} DYNAMIC SOURCE-ANCHORED FOOT PATH')
# Source diagnostics and explicit two-slot scope; never claim diagonal locomotion.
once('terrainMode,terrainStrength,terrainHipReachSolver:true,',
     'directionSlot:directionMode,directionStatus:"FORWARD_AND_BACKWARD_IMPLEMENTED; SIX_OTHER_DIRECTIONS_UNIMPLEMENTED",terrainMode,terrainStrength,terrainHipReachSolver:true,')
once('terrainMode,terrainStrength,bodyTerrainLift:groundLift,hipReachLimitCount,',
     'directionMode,terrainMode,terrainStrength,bodyTerrainLift:groundLift,hipReachLimitCount,')
once('3 measured cycles, 120 Hz, traveling root ${worldZ.toFixed(3)} u',
     '3 measured cycles, 120 Hz, ${directionMode} traveling root ${worldZ.toFixed(3)} u')
# Avoid silently v23 legacy phrases asserting a new (backward) walk is already accepted.
s=s.replace('v0.1.23','v0.1.24').replace('V0.1.23','V0.1.24')
# Revert pinned original source SHA literal (used in documentation marker) after global version substitution.
assert "directionMode" in s and "reversedSamples(sourceSamples)" in s
assert 'backwardRootDelta(' in s and 'sourceGaits=reversedWindows(sourceGaits);' in s
assert s.count('new THREE.AnimationMixer(actor)')==0
p.write_text(s.rstrip()+'\n')
# The v23 foot-gait is byte-identical for FORWARD. Only reverse rocker transfer
# gains an optional mode and never touches ankle target or source pose.
p=dest/'foot-gait.mjs';t=p.read_text()
needle='constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0,transformSource=null,terrainAt=null}){'
assert t.count(needle)==1
t=t.replace(needle,'constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0,transformSource=null,terrainAt=null,reverseRocker=false}){')
needle='this.readWitness=readWitness;this.rootAt=rootAt;this.transformSource=transformSource;this.terrainAt=terrainAt;this.activeDuty=gait.duty;'
assert t.count(needle)==1
t=t.replace(needle,'this.readWitness=readWitness;this.rootAt=rootAt;this.transformSource=transformSource;this.terrainAt=terrainAt;this.reverseRocker=reverseRocker;this.activeDuty=gait.duty;')
needle='if(order[pivot]<order[this.pivot])pivot=this.pivot;'
assert t.count(needle)==1
t=t.replace(needle,'if(this.reverseRocker?order[pivot]>order[this.pivot]:order[pivot]<order[this.pivot])pivot=this.pivot;')
p.write_text(t.rstrip()+'\n')
# Distinct, cache-busted HTML with accessible backward/forward selection.
p=dest/'index.html';t=p.read_text()
t=t.replace('v0.1.23','v0.1.24').replace('V0.1.23','V0.1.24')
needle='<div id="motionStatus" class="bar" role="status" aria-live="polite">'
assert t.count(needle)==1
t=t.replace(needle,"""<div class="bar" role="group" aria-label="Locomotion direction: two of eight slots">
<label for="directionMode">Direction</label><select id="directionMode"><option value="backward">Backward (−Z)</option><option value="forward">Forward (+Z, baseline)</option></select>
<strong>2/8 directional slots</strong><span class="small">Facing stays +Z. Switching directions starts a fresh world run to protect planted anchors. Lateral and diagonal slots are not implemented.</span></div>
"""+needle)
t=t.replace('<title>Hareworks v0.1.24 | Accepted Walk + World Pin</title>',
            '<title>Hareworks v0.1.24 | Forward + Backward Procedural IK</title>')
t=t.replace('Walking_Woman · Dynamic World-Space IK','Walking_Woman · Forward / Backward Procedural IK')
t=t.replace('Original Walking_Woman trajectories supply the reference.',
            'Original Walking_Woman trajectories supply startup calibration. Backward uses reversed procedural phase, reversed world root travel and toe-first heel-last rocker. No baked clip playback drives the visible character.')
t=t.replace('v0.1.24-startup-and-preview','v0.1.24-backward-direction-physical-ik')
p.write_text(t.rstrip()+'\n')
p=dest/'review-server.py';t=p.read_text().replace('v0.1.23','v0.1.24');p.write_text(t.rstrip()+'\n')
# Produce new README, contract and source-obligation tests; copy other files unchanged.
print('V024_PATCH_PASS: copied v23 forward baseline, distinct backward slot, signed world travel, no model edit')
V024_PATCH
cat > "$DEST_REL/README.md" <<'V024_README'
# Hareworks v0.1.24: backwards walking, directional slot 2 of 8

The owner accepts the current **forward walk** as good enough for now. Preserve v0.1.23 without modification. This new version adds a **BACKWARD (-Z)** procedural world-IK locomotion slot, with a selectable **FORWARD (+Z)** unchanged reference, and still only one visible actor. These are the second and first cardinal slots in a prospective eight-direction blend tree, not a finished blend tree or eight-way continuous blend.

**Not an animated clip played in reverse.** The visible GLB still has no AnimationMixer on the actor. At startup, capture real Walking_Woman source joint and skinned-shoe measurements, fit the existing upper-body and gait equations, then reuse the samples in reversed phase chronology to generate a physically solved backward walker. A reverse root integral moves the actor -Z while the face, foot heading, anterior knee poles and shoes continue to face +Z. Stance windows are reversed and the contact rocker moves toe -> sole -> heel for backward motion. Planted world anchors remain fixed within one run; changing direction reloads into a fresh world run rather than teleporting an existing stance foot.

**Protected:** canonical GLB unchanged, existing v0.1.9/v0.1.18/v0.1.23 source versions untouched, right-foot yaw improvement, stable knee pole, terrain hip/reach diagnostics, OrbitControls and mobile interface. No root rotation, no backward facing, no sideways strafing, no diagonal behavior. Root travel and audit must be *signed*. Flat and terrain tests remain available. Backward defaults to FLAT so the new gait can be assessed without extreme-terrain startup failure.

**r3 test-harness recovery:** the copied historical `foot-gait-test.mjs` from v23 erroneously imported `inferContacts` and `swingResidual`, which the current `foot-gait.mjs` no longer exports. r3 replaces only the NEW v24 staging copy of that test with coverage of the actual public API (`sourceAt`, `supportMode`, `SourceFootContact` and `phase01` from `root-motion.mjs`). It additionally verifies world anchor locking, terrain contact placement, reverse rocker option, stance-to-swing continuity and expected failure handling. Older source files and forward gait remain untouched. r2 failed before publishing anything.

**Honest gates:** exact startup GLB binary must be SHA verified in Termux; programmatic contact tests, full 120-Hz real browser audits, signed root travel and skinned heel/sole/toe drift must be independently inspected. The viewer visibly labels the fallback PREVIEW_UNPINNED. Script syntax and synthetic geometry tests alone cannot establish physical IK or owner visual acceptance.

**Repo authority:** single SHA-checked Android Termux Git script, persistent Documents/GodotProjects/parametric-parambulator checkout, new version directory only, commit/push/exact remote readback, browser cache identity and durable evidence receipts.
V024_README
cat > "$DEST_REL/contract.json" <<'V024_CONTRACT'
{
  "schema": "hareworks-v0.1.24-directional-backward-second-slot",
  "repo": "Valar05/parametric-parambulator",
  "parent": "ed4bae4ffbe713fc3170f4028708ff8a9992bbab",
  "modelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "modelSize": 6784896,
  "sourceViewerBlob": "55d4073a74ad7d26a8ded6d68288f1f8555f9e58",
  "sourceWalk": "Walking_Woman",
  "implementedSlots": [
    "forward",
    "backward"
  ],
  "unimplementedSlots": [
    "left",
    "right",
    "forward-left",
    "forward-right",
    "back-left",
    "back-right"
  ],
  "executionLane": "Android Termux Git only",
  "mutablePaths": [
    "tools/hareworks-forward-woman/v0.1.24/"
  ],
  "originalSourceModified": false,
  "ownerVisualAcceptance": false,
  "physicalContactVerified": false,
  "explicitExclusions": [
    "model mutation",
    "new animation clip",
    "root reorientation",
    "forward gait rewrite",
    "silent blend tree generalization"
  ],
  "rulesAGENTSBlob": "547c2af52303f4efb718bbf8f82a698110c7bfca",
  "rulesCampaignEtiquetteDoc": "1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI"
}
V024_CONTRACT
# All source modules require exact remote Git blob identity before authoring.
[ "$(git -C "$CHECKOUT" hash-object "$CHECKOUT/$SOURCE_REL/viewer.mjs")" = 55d4073a74ad7d26a8ded6d68288f1f8555f9e58 ] || { echo 'BLOCKED_BACKWARD_BASE_VIEWER_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object "$CHECKOUT/$SOURCE_REL/foot-gait.mjs")" = ecc036c99f92dfa02b17a9457e76b0998a127c04 ] || { echo 'BLOCKED_BACKWARD_BASE_CONTACT_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object "$CHECKOUT/$SOURCE_REL/terrain-hip.mjs")" = 9dd0b9fd1d843b41c958aa2ee2dd0997c6559d2a ] || { echo 'BLOCKED_BACKWARD_BASE_PELVIS_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object "$CHECKOUT/$SOURCE_REL/source-knee-governor.mjs")" = eefc2b0b867778bb384eafe95af4e63d7caa2f6b ] || { echo 'BLOCKED_BACKWARD_BASE_KNEE_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object "$CHECKOUT/$SOURCE_REL/foot-heading.mjs")" = 39108d51fcd6f1d0133e8ebdb79c665350bc1a4b ] || { echo 'BLOCKED_BACKWARD_BASE_FOOT_HEADING_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json")" = f6e8940b5eaeaf154a126eaa5221dcfcab0d94d1 ] || { echo 'BLOCKED_BACKWARD_ARCHIVED_SOURCE_CHANGED' >&2;exit 77; }
python3 "$DEST_REL/patch.py" "$CHECKOUT" "$DEST_REL"
# Old v23 foot-gait-test.mjs imported inferContacts and swingResidual, which
# do not exist in the current source module. This test is VERSIONED into the
# new isolated v24 BUILDROOT only. The unchanged v23 test/source stay intact.
STAGE='repair-stale-foot-contact-test-current-module-api'
cat > "$DEST_REL/foot-gait-test.mjs" <<'V024_REAL_API_CONTACT_TEST'
import assert from 'node:assert/strict';
import {phase01} from './root-motion.mjs';
import {sourceAt,supportMode,SourceFootContact} from './foot-gait.mjs';
const n=360;
const samples=Array.from({length:n},(_,i)=>{
 const q=i/n,theta=q*2*Math.PI,z=.28*Math.cos(theta);
 return {phase:q,hip:[.10,.91,0],knee:[.10,.55,.06],ankle:[.10,.21+.03*Math.max(0,Math.sin(theta)),z],
  heel:[.10,.015,z-.12],sole:[.10,.025,z],toe:[.10,.04,z+.12],q:[0,0,0,1]};
});
assert.equal(phase01(-.2),.8);
assert.equal(supportMode({heel:[0,-.03,0],toe:[0,.03,0]},0),'heel');
for(const q of [0,.1,.24,.50,.75,.999]){
 const sample=sourceAt(samples,q);
 for(const key of ['hip','knee','ankle','heel','sole','toe'])
  assert.equal(sample[key].length,3,key+' length');
 for(const key of ['hip','knee','ankle','heel','sole','toe'])
  assert(sample[key].every(Number.isFinite),key+' finite');
}
const gait={start:.10,duty:.58};
const fixed={heel:[.1,0,.15],sole:[.1,0,.25],toe:[.1,0,.35],ankle:[.1,.2,.25]};
const readWitness=kind=>fixed[kind].slice();
const c=new SourceFootContact({samples,gait,sourceGround:0,readWitness,rootAt:q=>q*1.2});
const a=c.step({phase:.12,totalPhase:.12,worldZ:.11});
assert(a.planted&&a.pivot==='heel');
const pin=a.anchor.slice();
for(const q of [.13,.18,.23,.3,.38,.45,.55,.62]){
 const b=c.step({phase:q,totalPhase:q,worldZ:q*1.2});
 assert(b.planted);
 assert.deepEqual(b.anchor,pin,'stance world anchor moved while rocker was constant');
 assert(b.ankleTarget.every(Number.isFinite));
}
const lift=c.step({phase:.70,totalPhase:.70,worldZ:.84});
assert(!lift.planted&&lift.pivot==='air');
assert(lift.ankleTarget.every(Number.isFinite));
assert(c.transitions>=2);
const terrain=(x,z)=>.10+.02*z;
const onHill=new SourceFootContact({samples,gait,sourceGround:0,readWitness,rootAt:q=>q*1.2,terrainAt:terrain});
const h=onHill.step({phase:.12,totalPhase:.12,worldZ:.11});
assert(Math.abs(h.anchor[1]-terrain(h.anchor[0],h.anchor[2]))<1e-12);
const reverse=new SourceFootContact({samples,gait,sourceGround:0,readWitness,rootAt:q=>q*1.2,reverseRocker:true});
const reverseStart=reverse.step({phase:.12,totalPhase:.12,worldZ:.11});
assert(reverseStart.planted&&reverseStart.anchor,'reverse rocker option is accepted');
assert.throws(()=>new SourceFootContact({samples,gait:{start:.1,duty:.30},sourceGround:0,readWitness}),/INVALID_SOURCE_STANCE_WINDOW/);
assert.throws(()=>sourceAt(samples.slice(0,5),.2),/SOURCE_SAMPLES_INSUFFICIENT/);
console.log('V024_CURRENT_FOOT_GAIT_API_CONTACT_TEST_PASS: sourceAt, phase01, heel stance lock, release, terrain anchor, reverse option, failures');
V024_REAL_API_CONTACT_TEST
# No silent disabling: execute this replacement and every other source test.
# Forward segment unchanged in new copy except opt-in reverse rocker constructor;
# original v23 and preceding versions cannot be touched by this campaign.
# SHA checks are resolved inside BUILDROOT. `git -C CHECKOUT` would wrongly
# inspect absent target files in the live repo. Do not regress this scope.
[ "$(pwd -P)" = "$(readlink -f "$BUILDROOT")" ] || { echo 'BLOCKED_STAGING_SCOPE_LOST' >&2;exit 77; }
[ -f "$BUILDROOT/$DEST_REL/foot-heading.mjs" ] &&
[ "$(git hash-object "$BUILDROOT/$DEST_REL/foot-heading.mjs")" = 39108d51fcd6f1d0133e8ebdb79c665350bc1a4b ] || { echo 'BLOCKED_BACKWARD_FOOT_HEADING_REGRESSION' >&2;exit 77; }
[ -f "$BUILDROOT/$DEST_REL/source-knee-governor.mjs" ] &&
[ "$(git hash-object "$BUILDROOT/$DEST_REL/source-knee-governor.mjs")" = eefc2b0b867778bb384eafe95af4e63d7caa2f6b ] || { echo 'BLOCKED_BACKWARD_KNEE_REGRESSION' >&2;exit 77; }
python3 - "$BUILDROOT/$DEST_REL" "$CHECKOUT/$DEST_REL" <<'V024_R3_GATE'
import pathlib,sys
build,live=[pathlib.Path(x) for x in sys.argv[1:]]
expected=('viewer.mjs','foot-heading.mjs','source-knee-governor.mjs','reverse-gait.mjs',
 'reverse-gait-test.mjs','backward-contact-test.mjs','foot-gait.mjs','foot-gait-test.mjs','terrain-hip.mjs',
 'terrain-core.mjs','patch.py','index.html','review-server.py','contract.json',
 'campaign-v0.1.24-r3-current-api-test-recovery.sh')
missing=[x for x in expected if not (build/x).is_file()]
if missing:raise SystemExit('BLOCKED_V024_R3_STAGING_REQUIRED_MISSING='+repr(missing))
if live.exists():raise SystemExit('BLOCKED_V024_R3_LIVE_DESTINATION_COLLISION')
print('V024_R3_BUILDROOT_MANIFEST_PASS required='+str(len(expected))+' liveDestinationAbsent=1')
V024_R3_GATE
STAGE='test-backward-source-phase-and-world-contact'
python3 - "$DEST_REL/patch.py" "$DEST_REL/review-server.py" "$DEST_REL/startup-regression.py" <<'V024_PY_PARSE'
import pathlib,sys
for p in sys.argv[1:]:compile(pathlib.Path(p).read_text(),p,'exec')
print('V024_PYTHON_SYNTAX_PASS')
V024_PY_PARSE
for f in "$DEST_REL"/*.mjs;do node --check "$f" || { echo "BLOCKED_JS_SYNTAX=$f" >&2;exit 77; };done
node "$DEST_REL/reverse-gait-test.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json"
node "$DEST_REL/backward-contact-test.mjs"
node "$DEST_REL/terrain-core-test.mjs"
node "$DEST_REL/terrain-hip-test.mjs"
node "$DEST_REL/foot-heading-test.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2/motion-profile.json"
node "$DEST_REL/source-knee-governor-test.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/foot-profile.json"
node "$DEST_REL/contact-core-test.mjs"
# Regression: obsolete test imports may not escape the staging gate.
if grep -Eq 'inferContacts|swingResidual' "$DEST_REL/foot-gait-test.mjs";then
 echo 'BLOCKED_STALE_GAIT_TEST_IMPORTS_REMAIN' >&2;exit 77
fi
node "$DEST_REL/foot-gait-test.mjs"
node "$DEST_REL/dynamic-gait-test.mjs"
node "$DEST_REL/shoe-witness-test.mjs"
node "$DEST_REL/contact-test.mjs"
node "$DEST_REL/root-model-test.mjs"
node "$DEST_REL/geometry-test.mjs"
node "$DEST_REL/source-speed-contact-test.mjs"
node "$DEST_REL/knee-source-invariant-test.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/foot-profile.json"
# At this point all author checks are synthetic or archival; real GLB browser
# step and planted-sole audit remains pending after Termux publication.
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
git commit -m 'Hareworks v0.1.24 add backward procedural directional gait slot'
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
for terrain_file in reverse-gait.mjs reverse-gait-test.mjs backward-contact-test.mjs foot-gait-test.mjs terrain-core.mjs terrain-core-test.mjs terrain-hip.mjs terrain-hip-test.mjs flat-parity-test.mjs foot-heading.mjs patch.py index.html review-server.py;do
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
 for f in viewer.mjs foot-gait.mjs foot-gait-test.mjs root-motion.mjs source-knee-governor.mjs terrain-core.mjs terrain-core-test.mjs terrain-hip.mjs terrain-hip-test.mjs flat-parity-test.mjs index.html;do
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
HTTP_DIRECTION_SHA="$(curl -fsS "http://127.0.0.1:$PORT/$DEST_REL/reverse-gait.mjs" | sha256sum | awk '{print $1}')"
[ "$HTTP_DIRECTION_SHA" = "$(sha256sum "$DEST_REL/reverse-gait.mjs" | awk '{print $1}')" ] || { echo 'BLOCKED_VIEWER_SERVES_WRONG_DIRECTION_MODULE' >&2;exit 80; }
[ "$(sha256sum "$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || { echo 'BLOCKED_HAREWORKS_GLB_CHANGED' >&2;exit 80; }
python3 - "$STATE" "$CAMPAIGN_ID" "$BASE_SHA" "$NEW_SHA" "$ENTRY_SHA" "$MODEL_SHA" "$URL" "$PORT" "$SERVER_PID" "$CHECKOUT" "$AGENTS_BLOB" "$ETIQUETTE_DOC" "$TOPDOWN_DOC" "$HTTP_SHA" "$PUBLISHED_REUSE" "$RECOVERED_R2_PARTIAL_INIT" <<'PYRECEIPT'
import datetime,json,pathlib,sys
(state,campaign,base,commit,entry,model,url,port,pid,checkout,agents,etiquette,topdown,viewer_hash,reused,recovered)=sys.argv[1:]
receipt={
 'campaign':campaign,'status':'PERSISTENT_CHECKOUT_AND_V024_BACKWARD_DIRECTION_PUBLISHED_BROWSER_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sparseCheckout':False,
 'androidSharedStorageGitTrust':'exact-canonical-project-only, global safe.directory',
 'lfsStatusGuard':'Git LFS filters configured locally; only exactly SHA-verified tracked Hareworks binary is admissible as unstaged model materialization',
 'lfsStatusGuardDoesNotHideChanges':True,
 'previousIncompleteGitInitRecovered':recovered=='1',
 'protectedGait':'v0.1.23 forward controller and model untouched; backward -Z implemented in new v0.1.24 slot; no diagonal motion',
 'shoeWitnesses':'v0.1.14 whole skinned foot low-surface longitudinal PCA bands, preserved unchanged',
 'calibrationFailureBehavior':'source procedural preview moving but explicitly UNPINNED and unapproved',
 'camera':'orbit and zoom with world-target follow','directionSlotsImplemented':['forward','backward'],'directionSlotsPending':6,
 'unrelatedReplLfsFetched':False,'hareworksCopyPolicy':'exactly one verified worktree model, reusable private LFS cache',
 'rulesReadInAuthoringTurn':{'AGENTSBlob':agents,'CampaignEtiquetteDocument':etiquette,'TopDownEtiquetteDocument':topdown},
 'viewerUrl':url,'viewerPid':int(pid),'viewerPort':int(port),'viewerGaitSha256':viewer_hash,
 'alreadyPublishedRerun':reused=='1','browserRealSkinnedFootAudit':'PENDING; explicit backward signed-world-root and skinned-foot audit required',
 'actualSkinned3dPhysicsTestedInTermux':False,
 'contactGate':'PENDING_BACKWARD_WORLD_SKINNED_AUDIT; reverse-time source phase and signed root tests alone are not physical acceptance','gaitResemblanceGate':'PENDING_OWNER_VISUAL_ACCEPTANCE; backward must actually walk -Z facing +Z; fallback preview is UNPINNED',
 'ownerVisualAcceptance':False,'canonicalModelUnchanged':True}
p=pathlib.Path(state)/'latest-receipt.json'
p.write_text(json.dumps(receipt,indent=2)+'\n')
print('RECEIPT='+str(p))
PYRECEIPT
STAGE='review-ready-owner-verdict-pending'
echo "CHECKOUT_READY=$CHECKOUT"
echo 'NORMAL_GIT_CHECKOUT=YES'
echo "BACKWARD_DIRECTION_REVIEW_ROOT=$CHECKOUT/$DEST_REL"
echo "MODEL_SHA256=$MODEL_SHA"
echo "PUBLISHED_COMMIT=$NEW_SHA"
echo "SCRIPT_SHA256=$ENTRY_SHA"
echo "VIEWER_PID=$SERVER_PID"
echo "VIEWER_URL=$URL"
echo "PHYSICAL_TERRAIN_JS_SHA256=$HTTP_TERRAIN_SHA"
echo "LIVE_VIEWER_JS_SHA256=$HTTP_VIEWER_SHA"
echo "DIRECTION_MATH_SHA256=$HTTP_DIRECTION_SHA"
echo 'CAMERA_ORBIT=RESTORED_SOURCE_CODE__PHONE_INTERACTION_PENDING'
echo 'DIRECTIONAL_SLOTS=FORWARD_PLUS_BACKWARD__OTHER_SIX_PENDING'
echo 'CONTACT_GATE=PENDING_REAL_BROWSER_STRESS_AUDIT__PREVIEW_IS_UNPINNED_IF_PHYSICS_FAILS'
echo 'GAIT_RESEMBLANCE_GATE=PENDING_OWNER_VISUAL_ACCEPTANCE'
if command -v termux-open-url >/dev/null 2>&1;then
 termux-open-url "$URL" || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
elif command -v am >/dev/null 2>&1;then
 am start -a android.intent.action.VIEW -d "$URL" >/dev/null 2>&1 || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
fi
