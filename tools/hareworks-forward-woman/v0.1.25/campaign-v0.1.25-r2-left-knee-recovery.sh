#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_LEFT_PROCEDURAL_v0.1.25_R2_DOCUMENTS
# r2 correction: the phone's real archived 60-frame knee test discovered
# 11 anatomical-side failures in the NEW lateral solver. The assertion remains
# hard and the separate left pole is recalibrated against actual source witnesses.
# r3 recovery: keep verified r2 BUILDROOT fixes and replace the stale copied
# v0.1.13 foot-gait test with a v0.1.23/24 API-correct unit regression.
# Previous r2 run stopped before installation/push on a missing named export.
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_LEFT_PROCEDURAL_v0.1.25_R2_DOCUMENTS'
VERSION='v0.1.25'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='1d2281ab5f7d69b7abb19f27c33c550c66d4e30d'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-left-procedural-v0.1.25-r2-documents"
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
  grep -q 'hareworks-v0.1.25-directional-left-third-slot' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
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
[ -f tools/hareworks-forward-woman/v0.1.24/viewer.mjs ] || { echo 'BLOCKED_MISSING_SOURCE_GAIT_BASELINE' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.24/viewer.mjs)" = 015b3e7ce44bfd36d0d411620785a7d9550030d4 ] || { echo 'BLOCKED_PUBLISHED_V023_SOURCE_CHANGED' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.24/terrain-core.mjs)" = 47a476db52f2bede12bf73309aeedb2c579adb3c ] || { echo 'BLOCKED_PUBLISHED_V023_TERRAIN_CHANGED' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.24/foot-gait.mjs)" = db047eae53cdbef04ce59dcff3db9d705000aa79 ] || { echo 'BLOCKED_PUBLISHED_V021_FOOT_TARGET_CHANGED' >&2;exit 74; }
[ -f tools/hareworks-forward-woman/v0.1.9/viewer.mjs ] || { echo 'BLOCKED_MISSING_ACCEPTED_V025_REFERENCE' >&2;exit 74; }
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
 TEMP_MODEL="$MODEL.r25-verified-${ENTRY_SHA:0:12}.tmp"
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
STAGE='generate-v025-left-procedural-controller'
SOURCE_REL='tools/hareworks-forward-woman/v0.1.24'
[ -d "$CHECKOUT/$SOURCE_REL" ] || { echo 'BLOCKED_SOURCE_V023_MISSING' >&2;exit 77; }
cp -R "$CHECKOUT/$SOURCE_REL" "$DEST_REL"
for old_launcher in "$DEST_REL"/campaign-*.sh;do [ -f "$old_launcher" ] && rm -- "$old_launcher" || :;done
cp "$ENTRY" "$DEST_REL/campaign-v0.1.25-r2-left-knee-recovery.sh"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.2" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3"
# Path authority: before installation, DEST_REL exists ONLY inside BUILDROOT.
# The first phone run failed because the regression check mistakenly used
# git -C "$CHECKOUT" to locate a newly generated, as-yet-unpublished file.
STAGE='verify-v025-r3-staging-copy-before-patch'
[ "$(pwd -P)" = "$(readlink -f "$BUILDROOT")" ] || { echo 'BLOCKED_STAGING_CWD_MISMATCH' >&2;exit 77; }
[ ! -e "$CHECKOUT/$DEST_REL" ] || { echo 'BLOCKED_STAGING_ALREADY_IN_LIVE_CHECKOUT' >&2;exit 77; }
python3 - "$CHECKOUT/$SOURCE_REL" "$BUILDROOT/$DEST_REL" <<'V025_STAGING'
import hashlib,pathlib,sys
src,dst=[pathlib.Path(q) for q in sys.argv[1:]]
source={p.relative_to(src).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in src.rglob('*') if p.is_file() and not p.name.startswith('campaign-')}
staged={p.relative_to(dst).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dst.rglob('*') if p.is_file() and not p.name.startswith('campaign-')}
if source!=staged:
 missing=sorted(set(source)-set(staged));extra=sorted(set(staged)-set(source));changed=sorted(p for p in set(source)&set(staged) if source[p]!=staged[p])
 raise SystemExit('BLOCKED_STAGING_SOURCE_COPY_INCOMPLETE missing='+str(missing)+' extra='+str(extra)+' changed='+str(changed))
for mandatory in ('viewer.mjs','foot-heading.mjs','source-knee-governor.mjs','foot-gait.mjs','terrain-core.mjs','terrain-hip.mjs','review-server.py','index.html'):
 if mandatory not in staged:raise SystemExit('BLOCKED_STAGING_MANDATORY_MISSING_'+mandatory)
print('V025_R3_STAGING_COPY_BYTE_PARITY_PASS modules='+str(len(staged)))
V025_STAGING
STAGE='generate-v025-left-procedural-controller'
cat > "$DEST_REL/lateral-gait.mjs" <<'V025_LATERAL'
/* Hareworks v0.1.25, third directional slot: genuine left strafe (-world X).
 * Body, shoes and eyes stay facing +Z. The original Walking_Woman phase supplies
 * alternating support timing and anatomical landmarks; transformed ankle paths,
 * independent planted world-X anchors and a distinct stateless anterior IK solve
 * produce lateral travel, NOT a translated forward playback clip.
 * Forward and backward implementations are byte-for-byte preserved in v0.1.24.
 */
import {rootStepDistance} from './speed-gait.mjs';
import {kneeFromTarget} from './ik-core.mjs';
export const LATERAL_FACTOR=.75;
export const LATERAL_Z_RETAIN=.18;
// The v1 left pole at +.70 yielded 11 real archived knee-side violations.
// Calibrate this ONE left-strafe pole to +1.40, keeping its character-local
// position absolutely fixed and its anterior +.95 reach intact. This is a
// DIFFERENT controller from the protected v24 forward/backward pole pair.
export const LATERAL_FIXED_POLES=Object.freeze({left:Object.freeze([1.40,-.02,.95]),right:Object.freeze([-.70,-.02,.95])});
const finite=v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite);
const norm=v=>Math.hypot(...v);
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const add=(a,b)=>a.map((v,i)=>v+b[i]);
const mul=(a,k)=>a.map(v=>v*k);
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export function lateralCadence(speed,motion){
 if(!Number.isFinite(speed)||speed<0||!motion||!(motion.stride>.01))throw Error('LATERAL_BAD_CADENCE');
 return speed/(LATERAL_FACTOR*motion.stride);
}
export function leftRootDelta(rootAt,curve,previous,next,motion){
 const d=rootStepDistance(rootAt,curve,previous,next,motion);
 if(!Number.isFinite(d)||d<-.000001)throw Error('LEFT_NONPHYSICAL_ROOT');
 return -LATERAL_FACTOR*d;
}
export function lateralSource(s,side){
 if(!['left','right'].includes(side)||!s||!['ankle','hip','knee','heel','sole','toe'].every(k=>finite(s[k])))throw Error('LATERAL_BAD_SOURCE');
 // Lateral placement is derived from source forward/back ankle excursion.
 // Anatomical center and original skinned shoe patch distances remain intact.
 const sign=side==='left'?1:-1,relativeZ=s.ankle[2]-s.hip[2];
 const ankle=[s.hip[0]-LATERAL_FACTOR*relativeZ+sign*.025,s.ankle[1],s.hip[2]+LATERAL_Z_RETAIN*relativeZ];
 const shift=sub(ankle,s.ankle);
 return {...s,ankle,
  heel:add(s.heel,shift),sole:add(s.sole,shift),toe:add(s.toe,shift)};
}
export function lateralPreviewTarget(hip,ankle,side){
 if(!finite(hip)||!finite(ankle)||!['left','right'].includes(side))throw Error('LATERAL_BAD_PREVIEW');
 const dz=ankle[2]-hip[2],sign=side==='left'?1:-1;
 return [hip[0]-LATERAL_FACTOR*dz+sign*.025,ankle[1],hip[2]+LATERAL_Z_RETAIN*dz];
}
export function lateralPole(side,yaw){
 const p=LATERAL_FIXED_POLES[side];if(!p||!Number.isFinite(yaw))throw Error('LATERAL_POLE_BAD_INPUT');
 const c=Math.cos(yaw),s=Math.sin(yaw);
 return [p[0]*c+p[2]*s,p[1],-p[0]*s+p[2]*c];
}
export function lateralKnee({hip,contactAnkle,sourceHip,sourceKnee,upperLength,lowerLength,side,pelvisYaw,centerX}){
 if(![hip,contactAnkle,sourceHip,sourceKnee].every(finite)||!Number.isFinite(centerX)||
 !Number.isFinite(upperLength)||!Number.isFinite(lowerLength)||upperLength<=0||lowerLength<=0)
  throw Error('LATERAL_BAD_KNEE_INPUT');
 const v=sub(contactAnkle,hip),d=norm(v);
 if(!(d>1e-6))throw Error('LATERAL_ZERO_TARGET');
 const min=Math.abs(upperLength-lowerLength)+.00045;
 const max=upperLength+lowerLength-.00045;
 const actual=add(hip,mul(v,clamp(d,min,max)/d));
 // Pole is a CONSTANT CHARACTER-LOCAL OFFSET, translated by the moving hip.
 // It must not remain at the world origin while the actor strafes many units.
 const knee=kneeFromTarget(hip,actual,upperLength,lowerLength,add(hip,lateralPole(side,pelvisYaw)));
 const deviation=norm(sub(knee,add(hip,sub(sourceKnee,sourceHip))));
 const clearance=(side==='left'?1:-1)*(knee[0]-centerX);
 return {ankle:actual,knee,kneeSourceError:deviation,unfulfilledContactDelta:norm(sub(actual,contactAnkle)),
  signedKneeClearance:clearance,baselineMismatch:false,acceptedFraction:1,
  proceduralLateralIK:true,staticPole:true};
}
export function leftTravelPass(worldX,worldZ,expected,margin=.17){
 return [worldX,worldZ,expected,margin].every(Number.isFinite)&&expected>=0&&
  Math.abs(worldX+expected)<=margin&&Math.abs(worldZ)<=.03;
}
V025_LATERAL
cat > "$DEST_REL/lateral-gait-test.mjs" <<'V025_TEST'
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {LATERAL_FACTOR,LATERAL_FIXED_POLES,lateralCadence,leftRootDelta,lateralSource,lateralPreviewTarget,lateralPole,lateralKnee,leftTravelPass} from './lateral-gait.mjs';
import {rootAt} from './root-motion.mjs';
import {speedGait} from './speed-gait.mjs';
import {sourceAt} from './foot-gait.mjs';
import {independentPose} from '../v0.1.2/pose-kernel.mjs';
import {kneeFromTarget} from './ik-core.mjs';
const D=1.224546,curve={stride:D},linear=(_c,q)=>D*q;
const motion=speedGait(.52,D);
assert(LATERAL_FACTOR>=.65&&LATERAL_FACTOR<=.9);
assert(lateralCadence(.52,motion)>motion.cadence);
let t=0,x=0;
for(let i=0;i<1800;i++){
 const dt=1/120,prev=t;t+=lateralCadence(.52,motion)*dt;
 const step=leftRootDelta(linear,curve,prev,t,motion);
 assert(step<=0&&step>-.012,'physical -X increments');x+=step;
}
assert(leftTravelPass(x,0,.52*15,.00001),'exact lateral travel speed');
assert(!leftTravelPass(x,.4,.52*15,.02),'reject fake diagonally-drifting X travel');
assert.throws(()=>lateralCadence(-1,motion));
const start={hip:[.11,.91,.13],knee:[.11,.55,.2],ankle:[.12,.21,.39],heel:[.12,.02,.30],sole:[.12,.01,.39],toe:[.12,.02,.51],q:[0,0,0,1]};
let left=lateralSource(start,'left'),right=lateralSource(start,'right');
assert(left.ankle[0]<start.ankle[0]-.1,'left swing must stride laterally');
assert(Math.abs(left.ankle[2]-start.hip[2])<Math.abs(start.ankle[2]-start.hip[2])*.20);
assert.equal(left.ankle[1],start.ankle[1]);
assert(Math.max(...left.toe.map((v,i)=>Math.abs((v-left.ankle[i])-(start.toe[i]-start.ankle[i]))))<1e-12,'shoe shape rigid');
assert(Math.abs((right.ankle[0]-left.ankle[0])+.05)<1e-12);
assert.deepEqual(lateralPreviewTarget(start.hip,start.ankle,'left'),left.ankle);
assert.throws(()=>lateralSource(start,'north'),/BAD_SOURCE/);
for(let side of ['left','right']){
 let pole=lateralPole(side,0);assert.deepEqual(pole,LATERAL_FIXED_POLES[side]);
 assert(pole[2]>.90,'static pole stays well ahead of body');
 const sg=side==='left'?1:-1;
 const H=[sg*.12,.92,.12],A=[sg*.13,.22,.18],K=lateralKnee({hip:H,contactAnkle:A,
  sourceHip:H,sourceKnee:[sg*.17,.59,.21],upperLength:.357,lowerLength:.38,side,pelvisYaw:0,centerX:0});
 assert(Math.hypot(...K.ankle.map((v,i)=>v-H[i]))<.737);
 assert(sg*K.knee[0]>=.012,'knee on anatomical side');
 assert(K.unfulfilledContactDelta<.005);
}
const archivePath=process.argv[2],profilePath=process.argv[3];
if(archivePath&&profilePath){
 const S=JSON.parse(fs.readFileSync(archivePath,'utf8')).samples;
 const p=JSON.parse(fs.readFileSync(profilePath,'utf8'));
 assert.equal(S.length,60);let crossings=0,maxReq=0;
 for(const src of S)for(const side of ['left','right']){
  const raw={...src.legs[side],heel:src.legs[side].ankle,sole:src.legs[side].ankle,toe:src.legs[side].ankle};
  const q=lateralSource(raw,side),g=src.legs[side],center=(src.legs.left.hip[0]+src.legs.right.hip[0])*.5;
  const k=lateralKnee({hip:g.hip,contactAnkle:q.ankle,sourceHip:g.hip,sourceKnee:g.knee,
  upperLength:p[side].upperLength,lowerLength:p[side].lowerLength,side,pelvisYaw:0,centerX:center});
  if(k.signedKneeClearance<.012)crossings++;
  maxReq=Math.max(maxReq,k.unfulfilledContactDelta);
 }
 assert.equal(crossings,0,'source archive knee must stay on its side');
 assert(maxReq<.009,'archived lateral step must be anatomically reachable');
 // Second gate: 360 source-interpolated midframes, with the ACTUAL fitted
 // pelvis yaw, not a convenient yaw=0 assumption. Keep the previously hard
 // centerline guard, with a stronger 0.015u protected margin.
 const motionPath=process.argv[4];
 assert(motionPath,'actual fitted pelvis motion profile is mandatory');
 const motionFit=JSON.parse(fs.readFileSync(motionPath,'utf8'));
 const bySide=Object.fromEntries(['left','right'].map(side=>[side,S.map((item,i)=>{
  const d=item.legs[side];
  return {phase:i/S.length,hip:d.hip,knee:d.knee,ankle:d.ankle,
   heel:d.ankle,sole:d.ankle,toe:d.toe,q:[0,0,0,1]};
 })]));
 let minMid=Infinity,maxKneeStep=0,maxInterpReach=0,oldPoleFails=0;
 for(const side of ['left','right']){
  const sg=side==='left'?1:-1;let priorKnee=null;
  for(let i=0;i<360;i++){
   const q=i/360,raw=sourceAt(bySide[side],q),other=sourceAt(bySide[side==='left'?'right':'left'],q);
   const transformed=lateralSource(raw,side);
   const yaw=independentPose(motionFit,q*motionFit.duration).pelvisYaw;
   const hipCenter=(raw.hip[0]+other.hip[0])*.5;
   const k=lateralKnee({hip:raw.hip,contactAnkle:transformed.ankle,
    sourceHip:raw.hip,sourceKnee:raw.knee,
    upperLength:p[side].upperLength,lowerLength:p[side].lowerLength,
    side,pelvisYaw:yaw,centerX:hipCenter});
   minMid=Math.min(minMid,k.signedKneeClearance);
   maxInterpReach=Math.max(maxInterpReach,k.unfulfilledContactDelta);
   if(priorKnee){const d=Math.hypot(...k.knee.map((v,j)=>v-priorKnee[j]));maxKneeStep=Math.max(maxKneeStep,d);}
   priorKnee=k.knee;
   if(side==='left'){
    const pole=[raw.hip[0]+.70,raw.hip[1]-.02,raw.hip[2]+.95];
    const legacy=kneeFromTarget(raw.hip,k.ankle,p[side].upperLength,p[side].lowerLength,pole);
    if(legacy[0]-hipCenter<.012)oldPoleFails++;
   }
  }
 }
 assert(minMid>=.015,'ARCHIVED_MIDFRAME_KNEE_CROSSES_CENTER_OR_CLEARANCE_TOO_SMALL '+minMid);
 assert(maxKneeStep<.020,'LATERAL_POLE_MIDFRAME_KNEE_DISCONTINUITY '+maxKneeStep);
 assert(maxInterpReach<.009,'ARCHIVED_MIDFRAME_LATERAL_ANKLE_UNREACHABLE '+maxInterpReach);
 assert(oldPoleFails>=8,'INJECTED_OLD_PLUS_070_POLE_NOT_REJECTED '+oldPoleFails);
 console.log('LEFT_LATERAL_ARCHIVED_KNEE_ENVELOPE_PASS 120 source poses; 720 yaw-aware midframe leg solves; minSide='+minMid.toFixed(5)+' maxKneeFrameStep='+maxKneeStep.toFixed(5)+' oldPoleRejectedFrames='+oldPoleFails+' maxReachClamp='+maxReq);
}
console.log('LEFT_WORLD_X_PROCEDURAL_ROOT_SOURCE_PRESERVATION_PASS displacement='+x.toFixed(5));
V025_TEST
cat > "$DEST_REL/lateral-anchor-test.mjs" <<'V025_ANCHOR_TEST'
import assert from 'node:assert/strict';
import {SourceFootContact} from './foot-gait.mjs';
import {lateralSource} from './lateral-gait.mjs';
const n=120,samples=Array.from({length:n},(_,i)=>{
 const q=i/n,z=.35*Math.cos(2*Math.PI*q),h=q>.62? .13*Math.sin(Math.PI*(q-.62)/.38):0;
 return {phase:q,hip:[.10,.9,.10],knee:[.14,.58,.22],ankle:[.12,.18+h,z],heel:[.12,.03+h,z-.1],sole:[.12,.02+h,z],toe:[.12,.03+h,z+.13],q:[0,0,0,1]};
});
const witness={ankle:[.1,.18,0],heel:[.1,0,0],sole:[.1,0,0],toe:[.1,0,0]};
const gait={start:.03,duty:.58};
const calc=new SourceFootContact({samples,gait,sourceGround:0,readWitness:k=>witness[k],transformSource:s=>lateralSource(s,'left')});
let anchor=null,planted=0,swing=0;
for(let i=0;i<480;i++){
 const p=(i/120)%1,x=-.004*i;
 const t=calc.step({phase:p,worldX:x,worldZ:0,totalPhase:i/120});
 if(t.planted){planted++;if(anchor&&t.pivot==='sole')assert.deepEqual(t.anchor,anchor,'world-X anchor must not drift under root travel');anchor=t.anchor;}
 else{anchor=null;swing++;assert(t.ankleTarget.every(Number.isFinite));}
}
assert(planted>200&&swing>80);
console.log('V025_LEFT_WORLD_X_CONTACT_ANCHOR_PASS planted='+planted+' swing='+swing);
V025_ANCHOR_TEST
cat > "$DEST_REL/patch.py" <<'V025_PATCH'
#!/usr/bin/env python3
"""Strict published v24 -> isolated v25 procedural left-stride patch. No old writes."""
import pathlib,sys
root=pathlib.Path(sys.argv[1]);dest=pathlib.Path(sys.argv[2]);p=dest/'viewer.mjs';s=p.read_text()
def once(old,new):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError('V025_PINNED_VIEWER_ANCHOR_'+str(n)+'_'+old[:125])
 s=s.replace(old,new,1)
assert 'OrbitControls' in s and 'GLTFLoader' in s and 'SourceFootContact' in s
assert 'new THREE.AnimationMixer(actor)' not in s
once('/* v0.1.24. ONE moving Walking_Woman.','/* v0.1.25. ONE moving Walking_Woman.')
once("import {distalHeading} from './foot-heading.mjs';",
"import {distalHeading} from './foot-heading.mjs';\nimport {LATERAL_FACTOR,lateralCadence,leftRootDelta,lateralSource,lateralPreviewTarget,lateralPole,lateralKnee,leftTravelPass} from './lateral-gait.mjs';")
once("const directionMode=terrainArgs.get('move')==='forward'?'forward':'backward';\nconst backward=()=>directionMode==='backward';\nconst bodyPhase=p=>sourcePhase(directionMode,p);",
"""const requestedMove=terrainArgs.get('move');
const directionMode=['forward','backward','left'].includes(requestedMove)?requestedMove:'left';
const backward=()=>directionMode==='backward';
const lateral=()=>directionMode==='left';
const bodyPhase=p=>lateral()?mod1(p):sourcePhase(directionMode,p);
const travelUnits=()=>lateral()?-worldX:signForDirection(directionMode)*worldZ;
""")
once("(backward()?'flat':'profile-ridges')","((backward()||lateral())?'flat':'profile-ridges')")
once('rootCurve=null,worldZ=0,frameTimer=','rootCurve=null,worldZ=0,worldX=0,frameTimer=')
once('worldZ+=signForDirection(directionMode)*(nextCycle-previewCycle)*dynamicMotion.stride;',
"""if(lateral())worldX-=LATERAL_FACTOR*(nextCycle-previewCycle)*dynamicMotion.stride;
 else worldZ+=signForDirection(directionMode)*(nextCycle-previewCycle)*dynamicMotion.stride;""")
once('groundLift=terrainBodyLift(groundLift,terrainAt(0,worldZ),Math.min(.25,Math.max(0,dt)));',
     'groundLift=terrainBodyLift(groundLift,terrainAt(worldX,worldZ),Math.min(.25,Math.max(0,dt)));')
once('target.fromArray(adjustAnkleForSpeed(H.toArray(),target.toArray(),side,dynamicMotion));',
     'target.fromArray(lateral()?lateralPreviewTarget(H.toArray(),target.toArray(),side):adjustAnkleForSpeed(H.toArray(),target.toArray(),side,dynamicMotion));')
once('kneeFromTarget(H.toArray(),target.toArray(),c.upperLength,c.lowerLength,rotateY(v.poleLocal,yaw))',
     'kneeFromTarget(H.toArray(),target.toArray(),c.upperLength,c.lowerLength,lateral()?lateralPole(side,yaw):rotateY(v.poleLocal,yaw))')
once(' actor.position.z=worldZ;actor.position.y=-groundOffset+groundLift;actor.updateMatrixWorld(true);}',
     ' actor.position.x=worldX;actor.position.z=worldZ;actor.position.y=-groundOffset+groundLift;actor.updateMatrixWorld(true);}')
once('out[side]=worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion});',
     'out[side]=worldContacts[side].step({phase,worldX,worldZ,totalPhase,gait:dynamicMotion});')
once(" const chosen=chooseSourceKnee({hip:H.toArray(),sourceHip:t.source.hip,",
""" const chosen=lateral()?lateralKnee({hip:H.toArray(),sourceHip:t.source.hip,
   sourceKnee:t.source.knee,contactAnkle:requested.toArray(),
   upperLength:c.upperLength,lowerLength:c.lowerLength,side,pelvisYaw:yaw,
   centerX:hipCenterX}):chooseSourceKnee({hip:H.toArray(),sourceHip:t.source.hip,""")
once(' const cadence=cadenceFor(speed,dynamicMotion.stride),newPhase=totalPhase+cadence*dt;',
     ' const cadence=lateral()?lateralCadence(speed,dynamicMotion):cadenceFor(speed,dynamicMotion.stride),newPhase=totalPhase+cadence*dt;')
once('worldZ+=backward()?backwardRootDelta(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion):rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);',
"""if(lateral())worldX+=leftRootDelta(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);
 else worldZ+=backward()?backwardRootDelta(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion):rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);""")
once('groundLift=terrainBodyLift(groundLift,terrainAt(0,worldZ),dt);',
     'groundLift=terrainBodyLift(groundLift,terrainAt(worldX,worldZ),dt);')
once('const touchdown={side,z:t.anchor[2],phase:totalPhase};',
     'const touchdown={side,z:lateral()?t.anchor[0]:t.anchor[2],phase:totalPhase};')
once('lastStats={phase,worldTravelZ:worldZ,speed,cadence,worldRootZ:actor.position.z,feet,transitions,',
     'lastStats={phase,worldTravelX:worldX,worldTravelZ:worldZ,directionAxisSignedTravel:travelUnits(),speed,cadence,worldRootX:actor.position.x,worldRootZ:actor.position.z,feet,transitions,')
once('Travel Z ${worldZ.toFixed(3)} u, phase ',
     'Travel X ${worldX.toFixed(3)} u, Z ${worldZ.toFixed(3)} u, signed axis ${travelUnits().toFixed(3)} u, phase ')
once('phase=0;totalPhase=0;worldZ=0;groundLift=terrainAt(0,0);',
     'phase=0;totalPhase=0;worldX=0;worldZ=0;groundLift=terrainAt(0,0);')
once('  transformSource:(s,gait)=>transformSourceFoot(s,side,gait||dynamicMotion)});',
     '  transformSource:(s,gait)=>lateral()?lateralSource(s,side):transformSourceFoot(s,side,gait||dynamicMotion)});')
once('  terrainAt:terrainMode===\'flat\'?null:terrainAt,reverseRocker:backward(),',
     '  terrainAt:terrainMode===\'flat\'?null:terrainAt,reverseRocker:backward(),') if False else None
once('  previewCycle=0;worldZ=0;dynamicMotion=speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE);frameBody(0);',
     '  previewCycle=0;worldX=0;worldZ=0;dynamicMotion=speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE);frameBody(0);')
once(' const startZ=worldZ;for(let i=0;i<32;i++)physicsStep(1/120);',
     '  const startTravel=travelUnits();for(let i=0;i<32;i++)physicsStep(1/120);')
once(' const travelled=worldZ-startZ;\n if(!Number.isFinite(travelled)||signForDirection(directionMode)*travelled<.04)',
     '  const travelled=travelUnits()-startTravel;\n if(!Number.isFinite(travelled)||travelled<.04)')
once(' directionMode,terrainMode,terrainStrength,bodyTerrainLift:groundLift,hipReachLimitCount,maxShinTerrainCollision,hipSolve:lastHipSolve};',
     '  lateralProceduralFootTargets:lateral(),directionRootX:worldX,terrainMode,terrainStrength,bodyTerrainLift:groundLift,hipReachLimitCount,maxShinTerrainCollision,hipSolve:lastHipSolve};')
once('if(terrainMode!==\'flat\'&&Math.abs(worldZ-terrainCenterZ)>14)',
     'if(terrainMode!==\'flat\'&&Math.abs(worldZ-terrainCenterZ)>14)') if False else None
# Live audit: X is the travel axis for left. Preserve all original negative-Z gates.
once('signForDirection(directionMode)*worldZ>speedGait(speed,stride).stride*2.70',
     'travelUnits()>(lateral()?LATERAL_FACTOR:1)*speedGait(speed,stride).stride*2.70')
once('maxTrailingExtensionDeficit<.055&&maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&maxKneeFlexDelta<6',
     '(lateral()||maxTrailingExtensionDeficit<.055)&&maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&(lateral()||maxKneeFlexDelta<6)')
once('minSignedKneeCenterline>=.012&&maxKneeSourcePositionDelta<=.025',
     'minSignedKneeCenterline>=.012&&(lateral()||maxKneeSourcePositionDelta<=.025)')
once('directionStatus:"FORWARD_AND_BACKWARD_IMPLEMENTED; SIX_OTHER_DIRECTIONS_UNIMPLEMENTED"',
     'directionStatus:"FORWARD_BACKWARD_LEFT_IMPLEMENTED; FIVE_OTHER_DIRECTIONS_UNIMPLEMENTED"')
once('surfaceAtRoot:terrainAt(0,worldZ)', 'surfaceAtRoot:terrainAt(worldX,worldZ)')
once('directionSlot:directionMode,expectedTravelSign:signForDirection(directionMode),signedWorldAdvance:worldZ',
     'directionSlot:directionMode,expectedTravelSign:backward()||lateral()?-1:1,signedWorldAdvance:lateral()?worldX:worldZ,rootWorldX:worldX,rootWorldZ:worldZ')
once('sampledFrames:n,worldTravelZ:worldZ,referenceRigWasNotDisplayed:true,',
     'sampledFrames:n,worldTravelX:worldX,worldTravelZ:worldZ,referenceRigWasNotDisplayed:true,')
once('if(i%15===0)samples.push({time:i/120,phase:m.phase,worldZ:m.worldTravelZ,',
     'if(i%15===0)samples.push({time:i/120,phase:m.phase,worldX:m.worldTravelX,worldZ:m.worldTravelZ,')
once('const expected=speedGait(requested,stride),steps=Math.ceil((1.20/expected.cadence)*120);',
     'const expected=speedGait(requested,stride),steps=Math.ceil((1.20/(lateral()?lateralCadence(requested,expected):expected.cadence))*120);')
once('speedMatrix.push({requested,realTime,travel:worldZ,measuredLastFootfall:latestStepSpacing,',
     'speedMatrix.push({requested,realTime,travelX:worldX,travelZ:worldZ,measuredLastFootfall:latestStepSpacing,')
once('rootMeanSpeed:worldZ/realTime,',
     'rootMeanSpeed:travelUnits()/realTime,')
once('signedTravelPass(directionMode,worldZ/realTime,requested,.17)',
     '(lateral()?leftTravelPass(worldX/realTime,worldZ/realTime,requested,.17):signedTravelPass(directionMode,worldZ/realTime,requested,.17))')
once('Math.abs(worldZ/realTime-requested)<.17',
     'Math.abs(travelUnits()/realTime-requested)<.17') if False else None
once('const n=Math.ceil((3/cadenceFor(speed,speedGait(speed,stride).stride))*120);',
     'const n=Math.ceil((3/(lateral()?lateralCadence(speed,speedGait(speed,stride)):cadenceFor(speed,speedGait(speed,stride).stride)))*120);')
once('nominalForwardAdvance:worldZ,generatedAnimationMixerCount:0',
     'nominalAxisTravel:travelUnits(),generatedAnimationMixerCount:0') if False else None
once("schema:'hareworks-v0.1.24-directional-two-of-eight'","schema:'hareworks-v0.1.25-directional-three-of-eight'")
once("a.download='hareworks-v0.1.24-'+directionMode+'-world-pin.json'","a.download='hareworks-v0.1.25-'+directionMode+'-world-pin.json'")
once('3 measured cycles, 120 Hz, ${directionMode} traveling root ${worldZ.toFixed(3)} u',
     '3 measured cycles, 120 Hz, ${directionMode} signed travel ${travelUnits().toFixed(3)} u')
once("$('identity').textContent=`v0.1.24 ${directionMode.toUpperCase()} DIRECTIONAL IK · TWO OF EIGHT CARDINAL SLOTS",
     "$('identity').textContent=`v0.1.25 ${directionMode.toUpperCase()} DIRECTIONAL IK · THREE OF EIGHT SLOTS")
once(" initRun();motionMode='PHYSICAL_GROUND_PINNING';playing=true;pinCamera();",
     " initRun();if(lateral())setCameraPreset('front');motionMode='PHYSICAL_GROUND_PINNING';playing=true;pinCamera();")
once("$('identity').textContent='v0.1.24 · REAL GLB '",
     "$('identity').textContent='v0.1.25 · REAL GLB '")
# Keep old physical controller fallback honest and visibly identify new direction.
once('V0.1.9 PROCEDURAL WALK PREVIEW MOVING · NOT GROUND PINNED',
     '${directionMode.toUpperCase()} PROCEDURAL WALK PREVIEW MOVING · NOT GROUND PINNED') if False else None
s=s.replace('v0.1.24','v0.1.25').replace('V0.1.24','V0.1.25')
assert "lateralSource(s,side)" in s and "lateralKnee(" in s and "leftRootDelta(" in s
assert s.count('new THREE.AnimationMixer(actor)')==0
p.write_text(s.rstrip()+'\n')
# World-X interpolation is an opt-in argument; forward/backward remain zero.
p=dest/'foot-gait.mjs';t=p.read_text()
needle='step({phase,worldZ,totalPhase,gait}){'
if t.count(needle)!=1:raise RuntimeError('V025_SOURCE_FOOT_STEP_ANCHOR')
t=t.replace(needle,'step({phase,worldX=0,worldZ,totalPhase,gait}){',1)
needle='const baseline=add(s.ankle,[0,-this.sourceGround,worldZ]);'
if t.count(needle)!=1:raise RuntimeError('V025_BASELINE_ANKLE_X_ANCHOR')
t=t.replace(needle,'const baseline=add(s.ankle,[worldX,-this.sourceGround,worldZ]);',1)
p.write_text(t.rstrip()+'\n')
# Readable three-slot direction selector with default left and no actor rotation.
p=dest/'index.html';t=p.read_text()
needle='<option value="backward">Backward (−Z)</option><option value="forward">Forward (+Z, baseline)</option>'
if t.count(needle)!=1:raise RuntimeError('V025_DIRECTION_CONTROL_ANCHOR')
t=t.replace(needle,'<option value="left">Left strafe (−X, procedural)</option><option value="backward">Backward (−Z, existing)</option><option value="forward">Forward (+Z, baseline)</option>',1)
t=t.replace('two of eight slots','three of eight slots').replace('<strong>2/8 directional slots</strong>','<strong>3/8 directional slots</strong>')
t=t.replace('Lateral and diagonal slots are not implemented.','Left is independently procedural; right and diagonals are not implemented.')
t=t.replace('Hareworks v0.1.24 | Forward + Backward Procedural IK','Hareworks v0.1.25 | Forward + Backward + Left Procedural IK')
t=t.replace('Walking_Woman · Forward / Backward Procedural IK','Walking_Woman · Three-direction Procedural IK')
t=t.replace('Backward uses reversed procedural phase, reversed world root travel and toe-first heel-last rocker.',
 'Backward uses reversed phase and root travel. Left uses distinct −X planted anchors, sideways foot trajectories, and stationary anterior knee poles while facing forward.')
t=t.replace('The model moves in world Z;','The model moves in world X for left and Z for forward/backward;')
t=t.replace('v0.1.24','v0.1.25').replace('V0.1.24','V0.1.25')
t=t.replace('v0.1.25-backward-direction-physical-ik','v0.1.25-left-procedural-world-x-ik')
p.write_text(t.rstrip()+'\n')
p=dest/'review-server.py';t=p.read_text().replace('v0.1.24','v0.1.25');p.write_text(t.rstrip()+'\n')
print('V025_LEFT_PROCEDURAL_PATCH_PASS immutable v24 sources copied; world-X targets and stateless knee IK only in v25')
V025_PATCH
cat > "$DEST_REL/README.md" <<'V025_README'
# Hareworks v0.1.25: procedural left (-world X), direction 3 of 8

The user reported that v0.1.24 backward WALK WORKS and requested a new procedurally generated LEFT walk. Preserve all v0.1.24 forward/backward sources in their immutable versioned path; this campaign copies that exact published state into NEW v0.1.25 only.

- The actor faces +Z in all modes. Left moves −world X without actor yaw or lateral displacement masquerading as a walk.
- r2 corrective archive gate: v1's separate left lateral knee pole failed 11 out of 120 archived leg checks at yaw 0. The actual stateless left pole is recalibrated from +0.70 to +1.40 character-local X, at unchanged +0.95 anterior Z. The right pole and the v0.1.24 forward/backward pole implementation are unchanged. BOTH the original 120 zero-yaw source checks and a new 720-solve interpolated source check with actual pelvis yaw must pass, with >=.015 unit centerline margin and <=.020 unit knee step. The old pole is deliberately injected and must fail the guard. No numeric gate is relaxed; no contact shift or source clip mutation is introduced.
- The left slot converts source-calibrated ankle excursions into true left/right foot X trajectories with fixed world-space planted anchors, newly calculated 2-bone knee IK with stationary far-forward direction-local poles, source hip bounce, independent swing paths, and a measured root-X integral. The source clip is calibration ONLY: no animation mixer runs on the visible actor.
- Left/X contact baseline is an opt-in extension to SourceFootContact; forward/backward fall back to exactly worldX=0, preserving the existing path. Left and backward/forward are selectable in the same phone viewer, with reload/new anchor initialization when direction changes.
- Left defaults to FLAT for readable visual judgment. Existing terrain/hip diagnostics and camera are retained as provisional; aggressive terrain is not a claimed passed contact audit.
- Root-X travel, world-Z drift, both feet's world stance anchor positions, skinned heel/sole/toe and shin collision evidence are measured by the browser 120Hz audit. Left conditional gates use physical lateral reach rather than incorrectly requiring forward archive knee/stride parity.
- v0.1.24 source model, right-foot heading, source stationary anterior pole solver, gait/archive versions and OrbitControls remain unchanged. Lateral uses a separate, stationary anatomical pole pair and does not alter original source pole positions.
- The four other diagonal/cardinal directions, right strafe and continuous blend tree are UNIMPLEMENTED; only left is commissioned now.

Evidence stages are separate: author-script checks; 6,784,896-byte GLB and 9 clips verified by Termux; new v0.1.25 commit and exact remote readback; real 3D IK in phone browser; owner visual acceptance. Numeric code checks do not imply visually acceptable walking.
V025_README
cat > "$DEST_REL/contract.json" <<'V025_CONTRACT'
{
  "schema": "hareworks-v0.1.25-directional-left-third-slot",
  "recoveryRevision": "r2-archived-knee-envelope",
  "newLeftLocalKneePole": [1.4, -0.02, 0.95],
  "rightLocalKneePoleUnchanged": [-0.7, -0.02, 0.95],
  "archivedKneeGate": "120 source poses + 720 source-interpolated yaw-aware leg solves; minSide>=0.015; original v1 pole must fail",
  "mission": "one true procedural left strafe -X while facing +Z; preserve backward and forward",
  "baseCommit": "1d2281ab5f7d69b7abb19f27c33c550c66d4e30d",
  "baseController": "tools/hareworks-forward-woman/v0.1.24",
  "newController": "tools/hareworks-forward-woman/v0.1.25",
  "sourceModelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "sourceModelSize": 6784896,
  "sourceClip": "Walking_Woman",
  "directions": [
    "forward",
    "backward",
    "left"
  ],
  "implementedCount": 3,
  "totalPlanned": 8,
  "realBLENDTREE": false,
  "rightAndDiagonalsImplemented": false,
  "locked": [
    "all files outside v0.1.25",
    "canonical GLB",
    "v0.1.24 forward/backward",
    "approved foot-heading",
    "OrbitControls"
  ],
  "authorizedWriteLane": "single Android Termux Git campaign, no direct connector writes",
  "physicalAudit": "PENDING_REAL_SKINNED_BROWSER",
  "ownerVisualAcceptance": false
}
V025_CONTRACT
python3 "$DEST_REL/patch.py" "$CHECKOUT" "$DEST_REL"
if grep -Eq 'inferContacts|swingResidual' "$DEST_REL/foot-gait-test.mjs";then echo 'BLOCKED_STALE_GAIT_TEST_IN_V24' >&2;exit 77;fi
# No silent disabling: execute this replacement and every other source test.
# Forward segment unchanged in new copy except opt-in reverse rocker constructor;
# original v23 and preceding versions cannot be touched by this campaign.
# SHA checks are resolved inside BUILDROOT. `git -C CHECKOUT` would wrongly
# inspect absent target files in the live repo. Do not regress this scope.
[ "$(pwd -P)" = "$(readlink -f "$BUILDROOT")" ] || { echo 'BLOCKED_STAGING_SCOPE_LOST' >&2;exit 77; }
[ -f "$BUILDROOT/$DEST_REL/foot-heading.mjs" ] &&
[ "$(git hash-object "$BUILDROOT/$DEST_REL/foot-heading.mjs")" = 39108d51fcd6f1d0133e8ebdb79c665350bc1a4b ] || { echo 'BLOCKED_LEFT_FOOT_HEADING_REGRESSION' >&2;exit 77; }
[ -f "$BUILDROOT/$DEST_REL/source-knee-governor.mjs" ] &&
[ "$(git hash-object "$BUILDROOT/$DEST_REL/source-knee-governor.mjs")" = eefc2b0b867778bb384eafe95af4e63d7caa2f6b ] || { echo 'BLOCKED_LEFT_KNEE_REGRESSION' >&2;exit 77; }
python3 - "$BUILDROOT/$DEST_REL" "$CHECKOUT/$DEST_REL" <<'V025_R3_GATE'
import pathlib,sys
build,live=[pathlib.Path(x) for x in sys.argv[1:]]
expected=('viewer.mjs','foot-heading.mjs','source-knee-governor.mjs','lateral-gait.mjs','lateral-gait-test.mjs','lateral-anchor-test.mjs','reverse-gait.mjs',
 'reverse-gait-test.mjs','backward-contact-test.mjs','foot-gait.mjs','foot-gait-test.mjs','terrain-hip.mjs',
 'terrain-core.mjs','patch.py','index.html','review-server.py','contract.json',
 'campaign-v0.1.25-r2-left-knee-recovery.sh')
missing=[x for x in expected if not (build/x).is_file()]
if missing:raise SystemExit('BLOCKED_V025_R3_STAGING_REQUIRED_MISSING='+repr(missing))
if live.exists():raise SystemExit('BLOCKED_V025_R3_LIVE_DESTINATION_COLLISION')
print('V025_R2_BUILDROOT_MANIFEST_PASS required='+str(len(expected))+' liveDestinationAbsent=1')
V025_R3_GATE
STAGE='test-left-world-X-source-phase-and-world-contact'
python3 - "$DEST_REL/patch.py" "$DEST_REL/review-server.py" "$DEST_REL/startup-regression.py" <<'V025_PY_PARSE'
import pathlib,sys
for p in sys.argv[1:]:compile(pathlib.Path(p).read_text(),p,'exec')
print('V025_PYTHON_SYNTAX_PASS')
V025_PY_PARSE
for f in "$DEST_REL"/*.mjs;do node --check "$f" || { echo "BLOCKED_JS_SYNTAX=$f" >&2;exit 77; };done
node "$DEST_REL/reverse-gait-test.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json"
node "$DEST_REL/backward-contact-test.mjs"
node "$DEST_REL/lateral-gait-test.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3/foot-profile.json" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2/motion-profile.json"
node "$DEST_REL/lateral-anchor-test.mjs"
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
git commit -m 'Hareworks v0.1.25 add procedural left -X directional locomotion slot'
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
for terrain_file in lateral-gait.mjs lateral-gait-test.mjs lateral-anchor-test.mjs reverse-gait.mjs reverse-gait-test.mjs backward-contact-test.mjs foot-gait-test.mjs terrain-core.mjs terrain-core-test.mjs terrain-hip.mjs terrain-hip-test.mjs flat-parity-test.mjs foot-heading.mjs patch.py index.html review-server.py;do
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
 for f in lateral-gait.mjs lateral-gait-test.mjs lateral-anchor-test.mjs viewer.mjs foot-gait.mjs foot-gait-test.mjs root-motion.mjs source-knee-governor.mjs terrain-core.mjs terrain-core-test.mjs terrain-hip.mjs terrain-hip-test.mjs flat-parity-test.mjs index.html;do
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
HTTP_LATERAL_SHA="$(curl -fsS "http://127.0.0.1:$PORT/$DEST_REL/lateral-gait.mjs" | sha256sum | awk '{print $1}')"
[ "$HTTP_LATERAL_SHA" = "$(sha256sum "$DEST_REL/lateral-gait.mjs" | awk '{print $1}')" ] || { echo 'BLOCKED_WRONG_LIVE_LATERAL_MODULE' >&2;exit 80; }
HTTP_DIRECTION_SHA="$(curl -fsS "http://127.0.0.1:$PORT/$DEST_REL/reverse-gait.mjs" | sha256sum | awk '{print $1}')"
[ "$HTTP_DIRECTION_SHA" = "$(sha256sum "$DEST_REL/reverse-gait.mjs" | awk '{print $1}')" ] || { echo 'BLOCKED_VIEWER_SERVES_WRONG_DIRECTION_MODULE' >&2;exit 80; }
[ "$(sha256sum "$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || { echo 'BLOCKED_HAREWORKS_GLB_CHANGED' >&2;exit 80; }
python3 - "$STATE" "$CAMPAIGN_ID" "$BASE_SHA" "$NEW_SHA" "$ENTRY_SHA" "$MODEL_SHA" "$URL" "$PORT" "$SERVER_PID" "$CHECKOUT" "$AGENTS_BLOB" "$ETIQUETTE_DOC" "$TOPDOWN_DOC" "$HTTP_SHA" "$PUBLISHED_REUSE" "$RECOVERED_R2_PARTIAL_INIT" <<'PYRECEIPT'
import datetime,json,pathlib,sys
(state,campaign,base,commit,entry,model,url,port,pid,checkout,agents,etiquette,topdown,viewer_hash,reused,recovered)=sys.argv[1:]
receipt={
 'campaign':campaign,'status':'PERSISTENT_CHECKOUT_AND_V025_LEFT_PROCEDURAL_DIRECTION_PUBLISHED_BROWSER_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sparseCheckout':False,
 'androidSharedStorageGitTrust':'exact-canonical-project-only, global safe.directory',
 'lfsStatusGuard':'Git LFS filters configured locally; only exactly SHA-verified tracked Hareworks binary is admissible as unstaged model materialization',
 'lfsStatusGuardDoesNotHideChanges':True,
 'previousIncompleteGitInitRecovered':recovered=='1',
 'protectedGait':'v0.1.24 forward and backward source preserved; left -X created in independent v0.1.25 controller; model unchanged',
 'shoeWitnesses':'v0.1.14 whole skinned foot low-surface longitudinal PCA bands, preserved unchanged',
 'calibrationFailureBehavior':'source procedural preview moving but explicitly UNPINNED and unapproved',
 'camera':'orbit and zoom with world-target follow','directionSlotsImplemented':['forward','backward','left'],'directionSlotsPending':5,
 'unrelatedReplLfsFetched':False,'hareworksCopyPolicy':'exactly one verified worktree model, reusable private LFS cache',
 'rulesReadInAuthoringTurn':{'AGENTSBlob':agents,'CampaignEtiquetteDocument':etiquette,'TopDownEtiquetteDocument':topdown},
 'viewerUrl':url,'viewerPid':int(pid),'viewerPort':int(port),'viewerGaitSha256':viewer_hash,
 'alreadyPublishedRerun':reused=='1','browserRealSkinnedFootAudit':'PENDING; explicit left -X signed-world-root and skinned-foot audit required',
 'actualSkinned3dPhysicsTestedInTermux':False,
 'contactGate':'PENDING_LEFT_WORLD_SKINNED_AUDIT; lateral source trajectory and root tests do not prove physics','gaitResemblanceGate':'PENDING_OWNER_VISUAL_ACCEPTANCE; left must actually step -X facing +Z; fallback preview is UNPINNED',
 'ownerVisualAcceptance':False,'canonicalModelUnchanged':True}
p=pathlib.Path(state)/'latest-receipt.json'
p.write_text(json.dumps(receipt,indent=2)+'\n')
print('RECEIPT='+str(p))
PYRECEIPT
STAGE='review-ready-owner-verdict-pending'
echo "CHECKOUT_READY=$CHECKOUT"
echo 'NORMAL_GIT_CHECKOUT=YES'
echo "LEFT_PROCEDURAL_REVIEW_ROOT=$CHECKOUT/$DEST_REL"
echo "MODEL_SHA256=$MODEL_SHA"
echo "PUBLISHED_COMMIT=$NEW_SHA"
echo "SCRIPT_SHA256=$ENTRY_SHA"
echo "VIEWER_PID=$SERVER_PID"
echo "VIEWER_URL=$URL"
echo "PHYSICAL_TERRAIN_JS_SHA256=$HTTP_TERRAIN_SHA"
echo "LIVE_VIEWER_JS_SHA256=$HTTP_VIEWER_SHA"
echo "DIRECTION_MATH_SHA256=$HTTP_LATERAL_SHA"
echo 'CAMERA_ORBIT=RESTORED_SOURCE_CODE__PHONE_INTERACTION_PENDING'
echo 'DIRECTIONAL_SLOTS=FORWARD_BACKWARD_LEFT__OTHER_FIVE_PENDING'
echo 'CONTACT_GATE=PENDING_REAL_BROWSER_STRESS_AUDIT__PREVIEW_IS_UNPINNED_IF_PHYSICS_FAILS'
echo 'GAIT_RESEMBLANCE_GATE=PENDING_OWNER_VISUAL_ACCEPTANCE'
if command -v termux-open-url >/dev/null 2>&1;then
 termux-open-url "$URL" || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
elif command -v am >/dev/null 2>&1;then
 am start -a android.intent.action.VIEW -d "$URL" >/dev/null 2>&1 || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
fi
