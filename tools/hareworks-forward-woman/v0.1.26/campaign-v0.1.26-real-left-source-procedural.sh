#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_REAL_LEFT_CLIP_v0.1.26_DOCUMENTS
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
CAMPAIGN_ID='HAREWORKS_WOMAN_REAL_LEFT_CLIP_v0.1.26_DOCUMENTS'
VERSION='v0.1.26'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='6342bb2a9b40c3d6911a1d58d6e384a7ddc24916'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-real-left-clip-v0.1.26-documents"
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
 elif [ "$HEAD_SHA" = "$LIVE" ] && [ -f "$DEST_REL/sidestep-core.mjs" ] && [ -f "$DEST_REL/contract.json" ];then
  # A second run after a verified publication is read-only and relaunches review.
  grep -q 'Cautious_Crouch_Walk_Left' "$DEST_REL/sidestep-core.mjs" || { echo 'BLOCKED_PUBLISHED_GAIT_MISSING' >&2;exit 73; }
  grep -q 'hareworks-v0.1.26-procedural-real-left-clip' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
  PUBLISHED_REUSE=1
  NEW_SHA="$HEAD_SHA"
 elif [ "$LIVE" = "$BASE_SHA" ] &&
      [ "$(git rev-list --parents -n 1 "$HEAD_SHA" | awk '{print $2}')" = "$BASE_SHA" ] &&
      [ -f "$DEST_REL/sidestep-core.mjs" ] && [ -f "$DEST_REL/contract.json" ];then
  # Previous push failed or its outcome was ambiguous. Reuse the SAME commit.
  [ "$(git diff-tree --no-commit-id --name-only -r "$HEAD_SHA" | awk -v p="$DEST_REL/" 'index($0,p)!=1 {bad=1} END{print bad+0}')" = 0 ] || { echo 'BLOCKED_PENDING_COMMIT_MUTATED_OTHER_PATHS' >&2;exit 73; }
  grep -q 'Cautious_Crouch_Walk_Left' "$DEST_REL/sidestep-core.mjs" || { echo 'BLOCKED_PENDING_GAIT_MISSING' >&2;exit 73; }
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
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.25/viewer.mjs)" = c1b5c06c0b0138cf56126c853b8d9f1e056c98ec ] || { echo 'BLOCKED_REJECTED_V025_HISTORY_CHANGED' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.24/viewer.mjs)" = 015b3e7ce44bfd36d0d411620785a7d9550030d4 ] || { echo 'BLOCKED_OWNER_BACKWARD_HISTORY_CHANGED' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.2.7/sidestep-core.mjs)" = 5e413a0d736d8e040c9d0da64e84a36409ce86de ] || { echo 'BLOCKED_REAL_LEFT_SOURCE_CORE_CHANGED' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.2.7/source-witness.json)" = b33ca21e92e41d26d3653490f8f1783f7d3810d7 ] || { echo 'BLOCKED_LEFT_SOURCE_WITNESS_CHANGED' >&2;exit 74; }
[ -f tools/hareworks-forward-woman/v0.1.9/viewer.mjs ] || { echo 'BLOCKED_MISSING_ACCEPTED_FORWARD_REFERENCE' >&2;exit 74; }
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
 RUN="$(mktemp -d "$STATE/build.XXXXXXXX")"
 BUILDROOT="$RUN"
 mkdir -p "$BUILDROOT/tools/hareworks-forward-woman"
 cd "$BUILDROOT"
 STAGE='stage-real-left-source-v027'
 SOURCE_REL='tools/hareworks-forward-woman/v0.2.7'
 [ -d "$CHECKOUT/$SOURCE_REL" ] || { echo 'BLOCKED_VERIFIED_REAL_LEFT_SOURCE_FOLDER_MISSING' >&2;exit 77; }
 [ ! -e "$CHECKOUT/$DEST_REL" ] || { echo 'BLOCKED_DEST_ALREADY_EXISTS' >&2;exit 77; }
 cp -R "$CHECKOUT/$SOURCE_REL" "$DEST_REL"
 cp "$ENTRY" "$DEST_REL/campaign-v0.1.26-real-left-source-procedural.sh"
 python3 - "$CHECKOUT/$SOURCE_REL" "$BUILDROOT/$DEST_REL" <<'V026_STAGE'
import hashlib,pathlib,sys
s,d=[pathlib.Path(x) for x in sys.argv[1:]]
a={p.relative_to(s).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in s.rglob('*') if p.is_file()}
b={p.relative_to(d).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in d.rglob('*') if p.is_file() and not p.name.startswith('campaign-v0.1.26')}
if a!=b:raise SystemExit('BLOCKED_VERIFIED_LEFT_SOURCE_COPY_NOT_BYTE_EQUAL')
for f in ('sidestep-core.mjs','sidestep-core-test.mjs','source-witness.json','source-witness-test.mjs'):
 if f not in b:raise SystemExit('BLOCKED_SOURCE_LEFT_MISSING_'+f)
print('V026_VERIFIED_REAL_LEFT_SOURCE_COPY_PASS files='+str(len(b)))
V026_STAGE
 [ "$(git -C "$CHECKOUT" hash-object "$BUILDROOT/$DEST_REL/sidestep-core.mjs")" = 5e413a0d736d8e040c9d0da64e84a36409ce86de ] || { echo 'BLOCKED_STAGED_LEFT_MATH_CORE_MISMATCH' >&2;exit 77; }
 cat > "$DEST_REL/viewer.mjs" <<'V026_VIEWER'
/* Hareworks v0.1.26: source-authored Cautious_Crouch_Walk_Left, procedural generated rig.
 * NO Walking_Woman lateral guess. NO backward-only direction-dispatcher.
 * A/B shows only ONE rig at a time. Original source rig has an AnimationMixer
 * for comparison; generated rig has ZERO source animation actions. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {ROOT,CLIPS,calibrate,pose,angleDeg} from './sidestep-core.mjs';
import {sourceContactWindow,isSourcePlanted,projectedSourceKnee,travelPhaseRate,distance} from './left-contact.mjs';
const $=x=>document.getElementById(x),V=()=>new THREE.Vector3(),Q=()=>new THREE.Quaternion();
const MODEL='../../../assets/hareworks/Hareworks-nine-clips.glb';
const SOURCE_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const SIZE=6784896,N=720,CONTACT_MAX_CORRECTION=.085,KNEE_MAX_CORRECTION=.035;
const limbs={left:['mixamorigLeftUpLeg','mixamorigLeftLeg','mixamorigLeftFoot'],right:['mixamorigRightUpLeg','mixamorigRightLeg','mixamorigRightFoot']};
const scene=new THREE.Scene();scene.background=new THREE.Color('#142231');scene.add(new THREE.HemisphereLight(0xeaf6ff,0x42576b,2.5));
const sunlight=new THREE.DirectionalLight(0xffffff,3.3);sunlight.position.set(-4,8,6);scene.add(sunlight);
const grid=new THREE.GridHelper(240,240,0x608ba7,0x2d4357);scene.add(grid);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-3,3,2,-2,.01,300),orbit=new OrbitControls(camera,renderer.domElement);orbit.enablePan=false;orbit.enableDamping=true;orbit.dampingFactor=.1;orbit.minZoom=.55;orbit.maxZoom=4;
const views={oblique:[-3.8,2.8,5.0],front:[0,2.6,6.5],side:[-6.5,2.5,0],top:[-.01,8,.01]};
let currentView='front',cameraTracked=V(0,.9,0);
function cameraAt(name){currentView=name;let at=actor?actor.position.clone().add(V(0,.9,0)):V(0,.9,0);cameraTracked.copy(at);orbit.target.copy(at);camera.position.copy(at).add(V(...views[name]));camera.up.set(0,1,0);orbit.update();}
function follow(){if(!actor)return;const to=actor.position.clone().add(V(0,.9,0)),step=to.sub(cameraTracked);orbit.target.add(step);camera.position.add(step);cameraTracked.add(step);}
function resize(){let w=Math.max(300,$('stage').clientWidth),h=Math.max(320,Math.min(720,Math.round(w*.78)));renderer.setSize(w,h,false);camera.top=2.4;camera.bottom=-2.4;camera.left=-2.4*w/h;camera.right=-camera.left;camera.updateProjectionMatrix();}
window.addEventListener('resize',resize);resize();
let source=null,actor=null,sourceRig=null,actorRig=null,sourceMixer=null,sourceClips={},snapshots={},plans={},sourceContacts={},ground=0;
let phase=0,cycles=0,worldX=0,playing=true,speed=1.23,lastTime=performance.now(),ready=false,frameCount=0;
let mode='procedural',contactLock={left:null,right:null},contactFlags={left:false,right:false},maxAnchorDrift=0,maxKneeShift=0,maxContactError=0,skippedCorrections=0,lastFailure='',lastStats=null,lastAudit=null;
let worldStride=0,duration=0,referenceClip=CLIPS[1];
const status=x=>$('status').textContent=x;
cameraAt(currentView);
const wpos=b=>b.getWorldPosition(V()),wq=b=>b.getWorldQuaternion(Q());
function rig(root){let out={};root.traverse(o=>{if(o.isBone){if(out[o.name])throw Error('DUPLICATE_BONE_'+o.name);out[o.name]=o;}});if(Object.keys(out).length!==74||!out[ROOT])throw Error('LEFT_SOURCE_NOT_74_BONES');return out;}
function setWorldQ(b,q){b.quaternion.copy(wq(b.parent).invert().multiply(q)).normalize();}
function aimJoint(b,from,to){let org=wpos(b),u=from.clone().sub(org),v=to.clone().sub(org);if(u.lengthSq()<1e-12||v.lengthSq()<1e-12)throw Error('LEFT_IK_ZERO_VECTOR');let q=Q().setFromUnitVectors(u.normalize(),v.normalize());setWorldQ(b,q.multiply(wq(b)));}
function snapshot(name){const clip=sourceClips[name],clone=cloneSkeleton(source),bones=rig(clone),mixer=new THREE.AnimationMixer(clone);mixer.clipAction(clip).reset().play();const result={name,sampleCount:N,duration:clip.duration,bones:{}};
 for(const key of Object.keys(bones))result.bones[key]={pos:[],quat:[],scale:[]};
 for(let i=0;i<N;i++){mixer.setTime(clip.duration*i/N);clone.updateMatrixWorld(true);for(const [key,b] of Object.entries(bones)){let o=result.bones[key];o.pos.push(b.position.toArray());o.quat.push(b.quaternion.toArray());o.scale.push(b.scale.toArray());}}
 const tr=clip.tracks.find(t=>t.name===ROOT+'.position');if(tr){let n=tr.times.length,size=tr.getValueSize();result.terminalRootTrack={lastTime:tr.times[n-1],lastPosition:Array.from(tr.values.slice((n-1)*size,n*size))};}
 return result;}
function sampleFootTravel(gltf){const clip=sourceClips[CLIPS[0]],model=cloneSkeleton(gltf.scene),bones=rig(model),m=new THREE.AnimationMixer(model);m.clipAction(clip).reset().play();let out={left:[],right:[]};
 for(let i=0;i<N;i++){m.setTime(clip.duration*i/N);model.updateMatrixWorld(true);for(let side of ['left','right'])out[side].push({ankle:wpos(bones[limbs[side][2]]).toArray()});}
 return out;}
function setPose(targetBones,snapshot,plan,p){const result=pose(snapshot,plan,p);for(const [name,part] of Object.entries(result.bones)){let b=targetBones[name];b.position.fromArray(part.position);b.quaternion.fromArray(part.quaternion).normalize();b.scale.fromArray(part.scale);}return result;}
function sourceAt(q){sourceMixer.stopAllAction();sourceMixer.clipAction(sourceClips[referenceClip]).reset().play();sourceMixer.setTime(((q%1)+1)%1*sourceClips[referenceClip].duration);source.updateMatrixWorld(true);}
function resetContact(){contactLock={left:null,right:null};contactFlags={left:false,right:false};maxAnchorDrift=0;maxKneeShift=0;maxContactError=0;skippedCorrections=0;lastFailure='';}
function applyIK(side,target){const [un,kn,fn]=limbs[side],up=actorRig[un],knee=actorRig[kn],foot=actorRig[fn];const H=wpos(up),K=wpos(knee),A=wpos(foot),d=A.distanceTo(target);maxContactError=Math.max(maxContactError,d);
 if(d>CONTACT_MAX_CORRECTION){skippedCorrections++;lastFailure='SOURCE_CONTACT_X_ERROR_'+side+'_'+d.toFixed(4);return false;}
 // Correct the source-authored leg without importing last frame's pole or a
 // changing left/right knee steering signal. The reference curve is rebuilt
 // from SOURCE every step, and any excessive correction is rejected visibly.
 const ik=projectedSourceKnee(H.toArray(),K.toArray(),A.toArray(),target.toArray());
 if(!ik.valid||ik.sourceKneeDisplacement>KNEE_MAX_CORRECTION){skippedCorrections++;lastFailure='SOURCE_KNEE_ENVELOPE_'+side+'_'+(ik.sourceKneeDisplacement??ik.reason);return false;}
 const footQ=wq(foot).clone();aimJoint(up,K,V(...ik.knee));actor.updateMatrixWorld(true);aimJoint(knee,wpos(foot),target);actor.updateMatrixWorld(true);setWorldQ(foot,footQ);actor.updateMatrixWorld(true);
 maxKneeShift=Math.max(maxKneeShift,ik.sourceKneeDisplacement);return true;
}
function poseProcedural(p,rootX,{correct=true}={}){setPose(actorRig,snapshots[CLIPS[1]],plans[CLIPS[1]],p);actor.position.set(rootX,0,0);actor.updateMatrixWorld(true);
 const ret={};for(const side of ['left','right']){
  let confidence=sourceContacts[side].method==='ANALYTIC_SOURCE_GROUND_VELOCITY';
  let pin=isSourcePlanted(p,sourceContacts[side]),foot=actorRig[limbs[side][2]],actual=wpos(foot),entry=contactLock[side];
  if(correct){if(pin&&!contactFlags[side]){entry={world:actual.clone(),phase:cycles};contactLock[side]=entry;}if(!pin)contactLock[side]=null;
   contactFlags[side]=pin;if(pin&&entry){let settled=confidence?applyIK(side,entry.world):false;if(!confidence)lastFailure='SOURCE_LEFT_CONTACT_UNVERIFIED_'+side;actual=wpos(foot);maxAnchorDrift=Math.max(maxAnchorDrift,actual.distanceTo(entry.world));ret[side]={planted:true,drift:actual.distanceTo(entry.world),solverApplied:settled,foot:actual.toArray(),anchor:entry.world.toArray()};}
   else ret[side]={planted:false,drift:null,solverApplied:false,foot:actual.toArray()};}
  else ret[side]={planted:pin,drift:null,solverApplied:false,foot:actual.toArray()};
 }
 return ret;}
function redraw({physics=true}={}){if(!ready)return;
 const p=((cycles%1)+1)%1;phase=p;worldX=cycles*worldStride;lastStats=poseProcedural(p,worldX,{correct:physics&&mode==='procedural'});
 if(mode==='source'){sourceAt(p);source.position.set(referenceClip===CLIPS[0]?Math.floor(cycles)*worldStride:worldX,0,0);source.visible=true;actor.visible=false;}else{source.visible=false;actor.visible=true;}
 source.updateMatrixWorld(true);actor.updateMatrixWorld(true);follow();$('phaseOut').textContent=(p*100).toFixed(1)+'%';$('phase').value=Math.round(p*1000);
 if(frameCount++%30===0)metrics();}
function metrics(){if(!ready)return;const state=mode==='source'?'SOURCE_ANIMATION_REFERENCE__NOT_GENERATED':skippedCorrections?'PROCEDURAL_LEFT_SOURCE_CORRECTION_WARN':'PROCEDURAL_LEFT_SOURCE_DERIVED';
 $('metrics').textContent=`${state}\nOriginal source: Cautious_Crouch_Walk_Left_inplace · generated rig source mixer=0\nMeasured authored lateral travel ${worldStride.toFixed(4)} u/cycle; actual X ${worldX.toFixed(4)} u; speed ${speed.toFixed(2)} u/s\nGenerated cadence ${(speed/worldStride).toFixed(3)} cycles/s · source period ${duration.toFixed(4)} s\nLeft contact ${JSON.stringify(sourceContacts.left)}\nRight contact ${JSON.stringify(sourceContacts.right)}\nWorld-ankle anchor max residual ${maxAnchorDrift.toFixed(4)} u; max permitted correction ${CONTACT_MAX_CORRECTION.toFixed(3)} u\nRejected IK corrections ${skippedCorrections}; source knee max adjustment ${maxKneeShift.toFixed(4)} u\n${lastFailure||'No source-contact conflict yet'}\nOriginal v0.1.24 forward/backward and v0.2.7 source comparison untouched.\nWhole-body source parity is independent of foot-contact success. Owner acceptance PENDING.`;}
function reset(){cycles=0;worldX=0;resetContact();if(ready){redraw();cameraAt('front');}}
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';};
$('reset').onclick=()=>reset();
$('speed').oninput=()=>{speed=Number($('speed').value);$('speedOut').textContent=speed.toFixed(2)+' u/s';};
$('direction').onchange=()=>{
 const selected=$('direction').value;if(selected==='left')return;
 if(!['forward','backward'].includes(selected))throw Error('UNKNOWN_DIRECTION_'+selected);
 const u=new URL('../v0.1.24/index.html',location.href);u.searchParams.set('move',selected);u.searchParams.set('terrain','flat');
 location.assign(u.toString()); // Navigation to immutable old slot, not a live blend or a new pose.
};
$('mode').onchange=()=>{mode=$('mode').value;resetContact();redraw();status(mode==='source'?'ORIGINAL IN-PLACE LEFT CLIP: SOURCE ANIMATION REFERENCE':'PROCEDURAL LEFT: MATHEMATICAL 74-BONE GAIT + WORLD-X CONTACT IK');};
$('reference').onchange=()=>{referenceClip=$('reference').value;redraw();};
$('phase').oninput=()=>{playing=false;$('play').textContent='Play';cycles=Math.floor(cycles)+Number($('phase').value)/1000;resetContact();redraw({physics:false});};
for(const key of Object.keys(views))$(key).onclick=()=>cameraAt(key);
$('audit').onclick=async()=>{if(!ready)return;let old={cycles,playing,mode,speed,referenceClip};playing=false;mode='procedural';referenceClip=CLIPS[1];cycles=0;resetContact();let frames=0,maxJointAngle=0,maxJointPosition=0,firstFrameFootGap=0,contactPhases={left:0,right:0};
 status('Auditing 3 traveling source-derived left cycles at 120 Hz; independent source parity and actual world contact...');
 try{const steps=Math.ceil(3*duration*120),startDate=performance.now();for(let i=0;i<steps;i++){
    cycles=(i/steps)*3;redraw();const p=phase;
    // Math reconstruction is audited BEFORE IK at reference snapshot phase.
    let computed=pose(snapshots[CLIPS[1]],plans[CLIPS[1]],p).bones;
    sourceAt(p);
    if(p<plans[CLIPS[1]].seamStart){for(const name of Object.keys(actorRig)){
     const b=sourceRig[name],a=computed[name];maxJointAngle=Math.max(maxJointAngle,angleDeg(b.quaternion.toArray(),a.quaternion));
     maxJointPosition=Math.max(maxJointPosition,b.position.distanceTo(V(...a.position)));
    }}
    for(const side of ['left','right'])if(lastStats?.[side]?.planted)contactPhases[side]++;
    frames++;if(i%40===0)await new Promise(requestAnimationFrame);
   }
   let maxDrift=maxAnchorDrift,skips=skippedCorrections,verifiedContactWindows=['left','right'].every(s=>sourceContacts[s].method==='ANALYTIC_SOURCE_GROUND_VELOCITY');
   lastAudit={schema:'hareworks-v0.1.26-real-left-source-procedural-audit',sourceSha256:SOURCE_SHA,
    sourceClips:CLIPS,controller:'source-calibrated 74-bone mathematical procedural pose plus world-X ankle IK, no generated animation mixer',
    renderedReferenceForAudit:'source AnimationMixer on hidden reference rig only',actualSourceBytes:SIZE,rigBones:74,sourceFramesPerClip:N,
    travelPerCycle:worldStride,worldTravelX:cycles*worldStride,sourcePeriod:duration,sourceGroundContacts:sourceContacts,
    actualFrames:frames,physicsHz:120,contactSampleFrames:contactPhases,worldAnkleAnchorMaxDrift:maxDrift,skippedContactIK:skips,
    sourceJointMaxQuaternionDeg:maxJointAngle,sourceJointMaxPosition:maxJointPosition,strictSourceParityExcludedSeam:1-plans[CLIPS[1]].seamStart,
    contactGate:(verifiedContactWindows&&maxDrift<=.025&&skips===0)?'ANKLE_PIN_PASS__NOT_SKINNED_SOLE_CERTIFICATION':'ANKLE_PIN_WARN',
    sourceParityGate:maxJointAngle<1&&maxJointPosition<.006?'SOURCE_MATH_PARITY_PASS':'SOURCE_MATH_PARITY_WARN',
    ownerAccepted:false};
   $('auditOut').textContent=JSON.stringify(lastAudit,null,2);
   try{await fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(lastAudit)});}catch(e){}
   status('LEFT SOURCE/PROCEDURAL AUDIT COMPLETE · contact '+lastAudit.contactGate+' · source '+lastAudit.sourceParityGate+' · owner review pending');
  }catch(e){status('AUDIT_ERROR '+e.message);console.error(e)}finally{cycles=old.cycles;playing=old.playing;mode=old.mode;speed=old.speed;referenceClip=old.referenceClip;redraw();}
};
$('export').onclick=()=>{if(!lastAudit){status('Run audit first');return;}let u=URL.createObjectURL(new Blob([JSON.stringify(lastAudit,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=u;a.download='hareworks-v0.1.26-left-procedural-audit.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),5000);};
function animate(t){requestAnimationFrame(animate);let dt=Math.max(0,Math.min((t-lastTime)/1000,.05));lastTime=t;
 if(ready&&playing){cycles+=dt*travelPhaseRate(speed,worldStride);redraw();}orbit.update();renderer.render(scene,camera);}
requestAnimationFrame(animate);
try{
 const res=await fetch(MODEL,{cache:'no-store'});if(!res.ok)throw Error('LEFT_MODEL_HTTP_'+res.status);
 const bytes=await res.arrayBuffer();if(bytes.byteLength!==SIZE)throw Error('LEFT_SOURCE_GLB_SIZE_'+bytes.byteLength);
 const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');if(hash!==SOURCE_SHA)throw Error('LEFT_SOURCE_GLB_HASH_'+hash);
 const gltf=await new GLTFLoader().parseAsync(bytes,new URL('../../../assets/hareworks/',import.meta.url).href);
 if(gltf.animations.length!==9)throw Error('LEFT_SOURCE_REQUIRES_NINE_CLIPS_'+gltf.animations.length);
 for(let clip of CLIPS){let found=gltf.animations.find(o=>o.name===clip);if(!found)throw Error('LEFT_SOURCE_CLIP_MISSING_'+clip);sourceClips[clip]=found;}
 source=cloneSkeleton(gltf.scene);actor=cloneSkeleton(gltf.scene);sourceRig=rig(source);actorRig=rig(actor);scene.add(source,actor);source.visible=false;
 sourceMixer=new THREE.AnimationMixer(source);for(let clip of CLIPS)sourceMixer.clipAction(sourceClips[clip]).reset().play();
 for(let clip of CLIPS){snapshots[clip]=snapshot(clip);plans[clip]=calibrate(snapshots[clip],.93);}
 duration=snapshots[CLIPS[1]].duration;worldStride=plans[CLIPS[0]].trend[0]-plans[CLIPS[1]].trend[0];
 if(!(worldStride>1&&worldStride<2))throw Error('LEFT_TRUE_WALK_SOURCE_TRAVEL_NOT_SEPARATED_'+worldStride);
 let original=sampleFootTravel(gltf);for(let side of ['left','right']){
  try{sourceContacts[side]=sourceContactWindow(original[side],sourceClips[CLIPS[0]].duration)}
  catch(e){throw Error('LEFT_ACTUAL_CLIP_CONTACT_DISCOVERY_FAILED_'+side+'_'+e.message)}
 }
 // This is left in the real clip's GLB +X convention; the old guessed -X
 // control was based on forward Walking_Woman and was NEVER an accepted slot.
 speed=Number((worldStride/duration).toFixed(2));$('speed').value=String(speed);$('speedOut').textContent=speed.toFixed(2)+' u/s';
 grid.position.y=new THREE.Box3().setFromObject(actor).min.y;
 ready=true;reset();sourceAt(0);source.visible=false;actor.visible=true;
 $('identity').textContent=`v0.1.26 · REAL Cautious_Crouch_Walk_Left_inplace · source ${SOURCE_SHA} · 74 joints · 720 source-calibrated phases per clip · 0 generated mixer · source left world +X=${worldStride.toFixed(3)}u/cycle · commit ${new URLSearchParams(location.search).get('commit')||'unknown'} · entry ${new URLSearchParams(location.search).get('scriptSha')||'unknown'}`;
 status('TRUE LEFT CLIP DERIVED · GENERATED 74-BONE PROCEDURAL GAIT ACTIVE · IK ankle pin audit PENDING');
}catch(e){status('LEFT_SOURCE_OR_STARTUP_BLOCKED '+String(e.message||e));$('auditOut').textContent='BLOCKED_REAL_GLTF_SOURCE '+String(e.message||e);console.error(e);}
V026_VIEWER
 cat > "$DEST_REL/left-contact.mjs" <<'V026_CONTACT'
/* Hareworks v0.1.26: source-derived LEFT contact, never a generic forward-walk strafe.
 * The real Cautious_Crouch_Walk_Left clip supplies actual traveling foot trajectories.
 * Source is calibration only; generated rig is solved procedurally each frame. */
export const mod1=v=>((v%1)+1)%1;
export const distance=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const add=(a,b)=>a.map((v,i)=>v+b[i]);
const scale=(a,s)=>a.map(v=>v*s);
export function sourceContactWindow(points,duration){
 const n=points?.length;
 if(!Number.isInteger(n)||n<120||!(duration>.1)||points.some(p=>!p||!Array.isArray(p.ankle)||p.ankle.length!==3||!p.ankle.every(Number.isFinite)))throw Error('LEFT_SOURCE_CONTACT_INVALID');
 const Y=points.map(p=>p.ankle[1]),X=points.map(p=>p.ankle[0]),bottom=Math.min(...Y),dt=duration/n;
 const vx=points.map((p,i)=>{let a=X[(i-1+n)%n],b=X[(i+1)%n];return (b-a)/(2*dt)});
 // Avoid the source clip's documented terminal root teleport in differentiation.
 for(let i=Math.floor(n*.93);i<n;i++)vx[i]=NaN;
 const runs=(mask)=>{let result=[];for(let i=0;i<n;i++){if(!mask[i]||mask[(i-1+n)%n])continue;let k=0;while(k<n&&mask[(i+k)%n])k++;result.push({start:i/n,duty:k/n,frames:k});}return result;};
 let best=null,method='ANALYTIC_SOURCE_GROUND_VELOCITY';
 for(let height of [.035,.06,.09,.13]){for(let threshold of [.25,.45,.7,1.05]){
   let candidates=runs(points.map((_,i)=>Y[i]-bottom<=height&&Math.abs(vx[i])<=threshold));
   let eligible=candidates.filter(x=>x.duty>=.25&&x.duty<=.75).sort((a,b)=>b.frames-a.frames);
   if(eligible.length){let candidate=eligible[0];if(!best||candidate.frames>best.frames)best={...candidate,height,velocityThreshold:threshold};}
 }}
 if(!best){
   // Still derive timing from the actual left clip, NEVER infer it from Walking_Woman.
   method='SOURCE_HEIGHT_FALLBACK__CONTACT_UNVERIFIED';let lo=Y.map(y=>y-bottom<=.055),candidates=runs(lo).sort((a,b)=>b.frames-a.frames);
   best=candidates[0]||null;
   if(!best||best.duty<.15){
     const k=Y.indexOf(bottom);best={start:mod1(k/n-.25),duty:.50,frames:Math.round(n*.5)};
     method='SOURCE_HEIGHT_MINIMUM_TIMING__NO_CONTACT_PROOF';
   }
   best={...best,height:.055,velocityThreshold:null};
 }
 return {start:best.start,duty:best.duty,frames:best.frames,method,minAnkleY:bottom,sourceClip:'Cautious_Crouch_Walk_Left',velocityThreshold:best.velocityThreshold,heightThreshold:best.height};
}
export function isSourcePlanted(q,window){return mod1(q-window.start)<window.duty;}
export function projectedSourceKnee(hip,knee,ankle,desired){
 for(let p of [hip,knee,ankle,desired])if(!Array.isArray(p)||p.length!==3||p.some(v=>!Number.isFinite(v)))throw Error('LEFT_IK_BAD_VECTOR');
 const l1=distance(hip,knee),l2=distance(knee,ankle),v=sub(desired,hip),d=Math.hypot(...v);
 if(!(l1>.12&&l2>.12&&d>Math.abs(l1-l2)+.0001&&d<l1+l2-.0001))return {valid:false,reason:'REACH',reach:d,maxReach:l1+l2};
 const u=scale(v,1/d),a=(l1*l1-l2*l2+d*d)/(2*d),radius=Math.sqrt(Math.max(0,l1*l1-a*a));
 const known=sub(knee,hip),normal=sub(known,scale(u,dot(known,u))),length=Math.hypot(...normal);
 if(length<.0001)return {valid:false,reason:'POLE_SINGULAR'};
 const K=add(add(hip,scale(u,a)),scale(normal,radius/length));
 return {valid:true,knee:K,upperLength:l1,lowerLength:l2,sourceKneeDisplacement:distance(K,knee)};
}
export function targetTravelX({totalPhase,travelPerCycle,speed}){
 if(!Number.isFinite(totalPhase)||!Number.isFinite(travelPerCycle)||!Number.isFinite(speed)||travelPerCycle<.5||speed<0)throw Error('LEFT_WORLD_TRAVEL_INVALID');
 return totalPhase*travelPerCycle;
}
export function travelPhaseRate(speed,sourceTravelPerCycle){
 if(!Number.isFinite(speed)||!Number.isFinite(sourceTravelPerCycle)||speed<0||sourceTravelPerCycle<.5)throw Error('LEFT_RATE_INVALID');
 return speed/sourceTravelPerCycle;
}
V026_CONTACT
 cat > "$DEST_REL/left-contact-test.mjs" <<'V026_TEST'
import assert from 'node:assert/strict';
import {sourceContactWindow,isSourcePlanted,projectedSourceKnee,targetTravelX,travelPhaseRate} from './left-contact.mjs';
const N=720,D=1.166667,travel=1.43;
for(const start of [.05,.30,.60]){
 const samples=Array.from({length:N},(_,i)=>{
  const q=i/N, p=((q-start+1)%1),stance=p<.58;
  // Physically planted source ankle has approximately zero horizontal speed.
  let x=stance?.4:.4+(.28*(p-.58)/.42),y=stance?.05:.05+.18*Math.sin(Math.PI*(p-.58)/.42)**2;
  return {ankle:[x,y,.1]};
 });
 const found=sourceContactWindow(samples,D);
 assert(found.duty>=.25&&found.duty<=.75,JSON.stringify(found));
 assert(isSourcePlanted(found.start+.02,found));
 assert(!isSourcePlanted(found.start+found.duty+.07,found));
}
assert.equal(targetTravelX({totalPhase:2,travelPerCycle:travel,speed:1.23}),2.86);
assert(Math.abs(travelPhaseRate(1.23,travel)*travel-1.23)<1e-12);
let a=projectedSourceKnee([0,.85,0],[.05,.49,.25],[0,.13,0],[.025,.15,.035]);
assert(a.valid&&Math.abs(Math.hypot(...a.knee.map((v,i)=>v-[0,.85,0][i]))-a.upperLength)<1e-8);
assert(!projectedSourceKnee([0,.85,0],[.05,.49,.25],[0,.13,0],[6,.15,.035]).valid);
assert.throws(()=>sourceContactWindow(Array.from({length:60},()=>({ankle:[0,0,0]})),D),/INVALID/);
assert.throws(()=>travelPhaseRate(.5,0),/INVALID/);
console.log('LEFT_AUTHORED_CLIP_PHASE_CONTACT_IK_TEST_PASS samples='+N+' source=Cautious_Crouch_Walk_Left');
V026_TEST
 cat > "$DEST_REL/index.html" <<'V026_HTML'
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#142231"><title>Hareworks v0.1.26 | Real-Clip Procedural Left Walk</title>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
<style>:root{font:15px system-ui,sans-serif;background:#101923;color:#e9f4ff;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:900px;margin:auto;padding:12px}h1{font-size:21px;margin:6px 0}p{color:#bdcfdd;line-height:1.5}.tag{font-size:12px;color:#b6e7ce;border:1px solid #507b73;padding:4px 8px;border-radius:18px}#identity{font:11px/1.6 ui-monospace,monospace;color:#abc6d2;overflow-wrap:anywhere}#status{padding:8px 0;min-height:42px;color:#b0ecce}#stage{border:1px solid #526f83;border-radius:10px;overflow:hidden}canvas{width:100%;display:block;touch-action:none}.bar{display:flex;gap:9px;align-items:center;flex-wrap:wrap;background:#203244;padding:10px;margin:10px 0;border-radius:9px}button,input,select{font:inherit}button,a.link{color:#f4f9ff;background:#30516d;border:1px solid #779ab4;border-radius:8px;min-height:45px;padding:8px 12px}button:focus-visible,input:focus-visible{outline:3px solid #7ce6d4}label{display:flex;gap:7px;align-items:center}input[type=range]{flex:1;min-width:140px;accent-color:#7ce6d4}#metrics,#auditOut{background:#172c3b;border:1px solid #44657a;border-radius:9px;padding:12px;white-space:pre-wrap;font:12px/1.55 ui-monospace,monospace;overflow-wrap:anywhere;max-height:330px;overflow:auto}.small{font-size:12px}a{color:#a9dffa}</style></head><body><main>
<header><h1>🐇 Hareworks · Procedural Walk LEFT</h1><span class="tag">v0.1.26 · real source clips · one visible rig</span></header>
<p>Source-corrected left stepping. The previous v0.1.25 viewer failed physical initialization and fell back to a forward walking preview. This implementation instead derives its complete 74-bone pose and step timing from <strong>Cautious_Crouch_Walk_Left_inplace</strong>, with traveling gait direction from <strong>Cautious_Crouch_Walk_Left</strong>. The generated character uses mathematical gait curves, world X travel, per-foot source-measured stance windows and bounded two-bone corrective IK. No source AnimationMixer is attached to the generated actor. This remains a source-derived procedural gait prototype, not a complete eight-way blend tree or proven ground-force solver.</p>
<div id="identity">Verifying the original source model…</div><div id="status" role="status" aria-live="polite">Calibrating the actual authored LEFT walk…</div><div id="stage" role="img" aria-label="Single source-derived 3D Hareworks character walking to her left, inspectable camera"></div>
<div class="bar"><button id="play">Pause</button><button id="reset">Reset world walk</button><label for="speed">Travel speed</label><input id="speed" type="range" min="0.3" max="1.6" value="1.23" step="0.01"><output id="speedOut">1.23 u/s</output></div>
<div class="bar" role="group" aria-label="Directional locomotion slots"><label for="direction">Direction (3/8 review slots)</label><select id="direction"><option value="left">Left: authored procedural</option><option value="forward">Forward: protected baseline</option><option value="backward">Backward: owner approved</option></select><span class="small">Selecting another slot navigates to its protected viewer; this is not continuous blending.</span></div>
<div class="bar"><label for="mode">Shown rig</label><select id="mode"><option value="procedural">Generated procedural left (default)</option><option value="source">Original source clip (comparison only)</option></select>
<label for="reference">Source reference</label><select id="reference"><option value="Cautious_Crouch_Walk_Left_inplace">Left walk in place</option><option value="Cautious_Crouch_Walk_Left">Traveling left walk</option></select><span class="small">Only one rig is visible. The source comparison uses a mixer; generated mode does not.</span></div>
<div class="bar" role="group" aria-label="Camera orbit presets"><strong>Orbit:</strong><button id="front">Front</button><button id="side">Side</button><button id="oblique">Three-quarter</button><button id="top">Top</button><span>Drag orbit · pinch zoom · follow actor</span></div>
<div class="bar"><label for="phase">Review gait phase</label><input type="range" id="phase" min="0" max="1000" step="1" value="0"><output id="phaseOut">0%</output><span class="small">Scrubbing stops motion; press Play to resume.</span></div>
<div class="bar"><button id="audit">Audit 120 Hz source gait and world ankle IK</button><button id="export">Export JSON evidence</button><a href="../v0.1.24/index.html">Prior backward/forward</a><a href="../v0.2.7/index.html">Earlier original left-clip study</a></div>
<div id="metrics" role="status">Loading real 74-bone left gait. Contact warnings will remain visible rather than switching to the unrelated forward gait.</div><div id="auditOut" role="status">Browser audit not yet run. No skinned sole-contact certification or owner approval is implied.</div>
<p class="small">Model bytes and SHA-256 are checked at runtime. +X is the travel direction measured in the original GLB's left-walk clip. This is character-relative LEFT despite the previous rejected trial's guessed −X convention. The animation's terminal source reset is repaired analytically, with direct source parity evaluated outside that repaired interval. Existing approved forward and backward versions, original model, and past experiments remain unchanged.</p>
</main><script type="module" src="./viewer.mjs?build=v0.1.26-real-left-source-procedural-ik"></script></body></html>
V026_HTML
 cat > "$DEST_REL/README.md" <<'V026_README'
# Hareworks v0.1.26: REAL authored LEFT walk, procedural reconstruction + ankle IK

**Why v0.1.25 was rejected** (owner's 8019.mp4, 120-Hz recording): the viewer's physical startup was blocked by `BACKWARD_UNKNOWN_DIRECTION_left` in `REAL_GLB_32_STEP_STARTUP_SMOKE`. The model fell back to a clearly labelled v0.1.9 forward procedural preview. The left controller never ran. The underlying v0.1.25 controller also converted the forward `Walking_Woman` foot path into an invented side step. That was not the actual source clip the owner wished to resemble. v0.1.25 is NOT accepted.

## Correct source and scope

The immutable exact source GLB contains nine clips including `Cautious_Crouch_Walk_Left` and `Cautious_Crouch_Walk_Left_inplace`. The older v0.2.7 experiment proved the correct original left gait can be sampled and reconstructed analytically. This version copies its unchanged `sidestep-core.mjs`, `sidestep-core-test.mjs` and `source-witness.json` as an immutable source-provenance base, and creates a new mobile reviewer and source-derived left locomotion prototype. **No `slide_right`, no forward `Walking_Woman` fake strafe, no `signForDirection('left')` backward-only dispatcher.**

- One visible actor at a time, generated by default. A 3/8 direction selector navigates to the protected v0.1.24 forward/backward viewer; navigation is NOT a continuous blend tree. The original source comparison is available as an explicit toggle, never falsely labeled procedural.
- At startup verify model SHA256 and actual GLB clip names/74-joint rig; sample the two authentic LEFT clips at 720 phases each using a source-only mixer. Rebuild every generated joint from a separate mathematical, seam-repaired pose function with **no AnimationMixer on generated actor**.
- The authored traveling source moves +world X (approximately 1.43 units per full cycle), which corresponds to this GLB's named LEFT gait. The rejected trial's guessed −X convention was not owner-accepted. Generate actual world travel at a speed-scaled cadence, preserving the authored in-place side-to-side pelvis sway, crouch, arm position and knee choreography.
- Measure contact phase windows from the actual traveling left clip ankle trajectory rather than original `Walking_Woman`. Apply small, bounded world-ankle pin corrections with a stateless two-link solve preserving the source knee plane, but **refuse large correction** and keep the generated source pose visible with a warning rather than snapping knees. Failed contact discovery must never swap to unrelated forward movement.
- Provide front/side/oblique/top orbit, camera follow and visible real procedural-vs-source toggle. A 120-Hz browser audit measures world-ankle locking and generated-vs-source full 74-joint math parity outside the documented terminal seam repair. Ankle locking does NOT certify a skinned sole or ground forces.

**Protected and immutable:** v0.1.9 forward visual reference, user-approved v0.1.24 backward and v0.1.25 historical reject, v0.2.7 source analysis, original GLB and all nine clips. New files only in `tools/hareworks-forward-woman/v0.1.26/` via one SHA-verified Android Termux Git script. Git remote publication, generated real browser runtime, and owner visual acceptance are distinct evidence gates. No continuous blend tree, right-stride, or diagonal direction is claimed.
V026_README
 cat > "$DEST_REL/contract.json" <<'V026_CONTRACT'
{
  "schema": "hareworks-v0.1.26-procedural-real-left-clip",
  "goal": "Replace visually rejected v0.1.25 forward-source fake left strafe with real Cautious_Crouch_Walk_Left source-derived procedurally generated left gait",
  "ownerVerdict": "v0.1.25 rejected, video 8019.mp4: BACKWARD_UNKNOWN_DIRECTION_left => unrelated unpinned forward preview",
  "repo": "Valar05/parametric-parambulator",
  "baseCommit": "6342bb2a9b40c3d6911a1d58d6e384a7ddc24916",
  "modelPath": "assets/hareworks/Hareworks-nine-clips.glb",
  "modelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "modelBytes": 6784896,
  "requiredSourceClips": ["Cautious_Crouch_Walk_Left", "Cautious_Crouch_Walk_Left_inplace"],
  "forbiddenReferenceAsLateralSource": ["Walking_Woman", "slide_right"],
  "sourceCalibration": "720 phases per clip; 74 joint periodic mathematical reconstruction, original clip source-only; generated has zero animation mixers",
  "worldTravel": "original GLB named left direction, positive world X, measured traveling clip displacement",
  "contact": "source-measured stance, bounded two-link world ankle pin, real browser audit required; no skinned sole contact certification",
  "protected": ["tools/hareworks-forward-woman/v0.1.9/", "tools/hareworks-forward-woman/v0.1.24/", "tools/hareworks-forward-woman/v0.1.25/", "tools/hareworks-forward-woman/v0.2.7/", "assets/hareworks/Hareworks-nine-clips.glb"],
  "mutable": ["tools/hareworks-forward-woman/v0.1.26/"],
  "publication": "Android Termux Git ONLY, no force, exact pinned remote readback",
  "requiredAGENTSBlob": "547c2af52303f4efb718bbf8f82a698110c7bfca",
  "campaignEtiquetteDoc": "1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI",
  "ownerLeftVisualAcceptance": false
}
V026_CONTRACT
 cat > "$DEST_REL/review-server.py" <<'V026_SERVER'
"""Version-pinned local left-walk viewer. Evidence is not owner approval."""
import hashlib, http.server, json, math, os, pathlib, sys
root, ready, state = sys.argv[1:]
SOURCE = 'a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
CLIPS = ['Cautious_Crouch_Walk_Left', 'Cautious_Crouch_Walk_Left_inplace']
SCHEMA = 'hareworks-v0.1.26-real-left-source-procedural-audit'
class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,
      '.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
    def __init__(self,*a,**kw): super().__init__(*a,directory=root,**kw)
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
        self.send_header('Pragma','no-cache')
        super().end_headers()
    def do_POST(self):
        if self.path.split('?')[0].split('/')[-1]!='evidence': self.send_error(404);return
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<300 or n>1000000:raise ValueError('evidence size')
            raw=self.rfile.read(n);d=json.loads(raw)
            if d.get('schema')!=SCHEMA or d.get('sourceSha256')!=SOURCE:raise ValueError('source/schema mismatch')
            if d.get('sourceClips')!=CLIPS or d.get('rigBones')!=74 or d.get('sourceFramesPerClip')!=720:raise ValueError('source clips/rig mismatch')
            if d.get('ownerAccepted') is not False:raise ValueError('false owner-approval state')
            if d.get('actualFrames',0)<250 or d.get('physicsHz')!=120:raise ValueError('incomplete actual browser sample')
            if d.get('contactGate') not in ('ANKLE_PIN_WARN','ANKLE_PIN_PASS__NOT_SKINNED_SOLE_CERTIFICATION'):raise ValueError('unsupported contact gate')
            for x in ('worldTravelX','travelPerCycle','worldAnkleAnchorMaxDrift','sourceJointMaxQuaternionDeg'):
                if not isinstance(d.get(x),(int,float)) or not math.isfinite(d[x]):raise ValueError('bad numeric '+x)
            if d['worldTravelX']<=2 or d['travelPerCycle']<=1:raise ValueError('wrong left root travel')
            path=pathlib.Path(state);path.mkdir(parents=True,exist_ok=True)
            artifact=path/'left-procedural-browser-evidence-v0.1.26.json';artifact.write_bytes(raw)
            result={'status':'REAL_BROWSER_EVIDENCE_SAVED_OWNER_REVIEW_PENDING','sha256':hashlib.sha256(raw).hexdigest(),
                 'sourceSha256':SOURCE,'path':str(artifact),'contactGate':d['contactGate'],'ownerAccepted':False}
            (path/'left-procedural-browser-receipt-v0.1.26.json').write_text(json.dumps(result,indent=2)+'\n')
            b=json.dumps(result).encode();self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
        except Exception as e:self.send_error(422,'evidence rejected '+str(e)[:100])
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
pathlib.Path(ready).write_text(json.dumps({'pid':os.getpid(),'port':server.server_address[1], 'root':root,'state':state,'sourceSha256':SOURCE,'ownerAccepted':False}))
server.serve_forever()
V026_SERVER
 STAGE='validate-v026-source-and-code'
 [ "$(git -C "$CHECKOUT" hash-object "$BUILDROOT/$DEST_REL/sidestep-core.mjs")" = 5e413a0d736d8e040c9d0da64e84a36409ce86de ] || { echo 'BLOCKED_CALIBRATION_MATH_CORE_TOUCHED' >&2;exit 77; }
 python3 - "$DEST_REL" <<'V026_VALIDATION'
import ast,json,pathlib,sys
p=pathlib.Path(sys.argv[1]);c=json.loads((p/'contract.json').read_text());s=(p/'viewer.mjs').read_text();a=(p/'index.html').read_text()
assert c['schema']=='hareworks-v0.1.26-procedural-real-left-clip'
assert c['baseCommit']=='6342bb2a9b40c3d6911a1d58d6e384a7ddc24916'
assert c['ownerLeftVisualAcceptance'] is False
for key in ['Cautious_Crouch_Walk_Left','Cautious_Crouch_Walk_Left_inplace']:
 assert key in s or key in (p/'sidestep-core.mjs').read_text()
for prohibited in ["signForDirection(directionMode)","BACKWARD_UNKNOWN_DIRECTION_left","LATERAL_FACTOR"]:
 assert prohibited not in s, ('BLOCKED_FAKE_OR_BAD_LEFT_CONTROLLER',prohibited)
assert "new THREE.AnimationMixer(actor)" not in s
assert "new THREE.AnimationMixer(source)" in s
assert "pose(snapshots[CLIPS[1]]" in s
assert 'Generated procedural left (default)' in a
ast.parse((p/'review-server.py').read_text())
print('V026_NEW_REAL_LEFT_RUNTIME_SOURCE_GATE_PASS')
V026_VALIDATION
 python3 - "$DEST_REL/review-server.py" <<'V026_PY_PARSE'
import ast,pathlib,sys
ast.parse(pathlib.Path(sys.argv[1]).read_text())
print('V026_BROWSER_SERVER_SYNTAX_PASS')
V026_PY_PARSE
 for f in "$DEST_REL"/*.mjs;do node --check "$f" || { echo "BLOCKED_JS_SYNTAX=$f" >&2;exit 77; };done
 node "$DEST_REL/sidestep-core-test.mjs"
 node "$DEST_REL/source-witness-test.mjs"
 node "$DEST_REL/left-contact-test.mjs"
 python3 - "$CHECKOUT/$MODEL" "$MODEL_SHA" <<'V026_GLB'
import hashlib,json,pathlib,struct,sys
b=pathlib.Path(sys.argv[1]).read_bytes()
if hashlib.sha256(b).hexdigest()!=sys.argv[2]:raise SystemExit('BLOCKED_GLB_HASH_CHANGED')
magic,ver,full=struct.unpack_from('<4sII',b,0)
if magic!=b'glTF' or ver!=2 or full!=len(b):raise SystemExit('BLOCKED_GLB_HEADER')
length,typ=struct.unpack_from('<II',b,12)
if typ!=0x4e4f534a:raise SystemExit('BLOCKED_GLB_JSON')
j=json.loads(b[20:20+length]);clips={a.get('name') for a in j.get('animations',[])}
needed={'Cautious_Crouch_Walk_Left','Cautious_Crouch_Walk_Left_inplace','Walking_Woman'}
if len(clips)!=9 or not needed.issubset(clips) or not j.get('skins') or not j.get('meshes'):raise SystemExit('BLOCKED_REAL_LEFT_CLIP_MISSING_OR_SKELETON_INVALID')
print('V026_NINE_ACTUAL_SOURCE_CLIPS_AND_SKIN_VERIFIED',sorted(clips))
V026_GLB
 [ "$(sha256sum "$CHECKOUT/$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || { echo 'BLOCKED_MODEL_CHANGED_DURING_AUTHOR_STAGE' >&2;exit 77; }
 echo 'V026_AUTHOR_MATH_AND_SOURCE_TESTS_PASS_REAL_SKINNED_BROWSER_PENDING'
STAGE='install-v026-real-left-in-persistent-checkout'
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
git commit -m 'Hareworks v0.1.26 source-corrected procedural left walk and bounded ankle IK'
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
for f in viewer.mjs index.html sidestep-core.mjs sidestep-core-test.mjs source-witness.json source-witness-test.mjs left-contact.mjs left-contact-test.mjs review-server.py README.md contract.json campaign-v0.1.26-real-left-source-procedural.sh;do
 [ "$(git rev-parse "FETCH_HEAD:$DEST_REL/$f")" = "$(git rev-parse "HEAD:$DEST_REL/$f")" ] || { echo "BLOCKED_REMOTE_V026_BLOB_MISMATCH=$f" >&2;exit 79; }
done
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
 for f in viewer.mjs index.html sidestep-core.mjs sidestep-core-test.mjs source-witness.json source-witness-test.mjs left-contact.mjs left-contact-test.mjs review-server.py README.md contract.json campaign-v0.1.26-real-left-source-procedural.sh;do
  [ "$(git rev-parse "FETCH_HEAD:$DEST_REL/$f")" = "$(git rev-parse "HEAD:$DEST_REL/$f")" ] || { echo "BLOCKED_RESUME_V026_BLOB_MISMATCH=$f" >&2;exit 79; }
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
for f in viewer.mjs sidestep-core.mjs left-contact.mjs index.html;do
 LIVE_SHA="$(curl -fsS "http://127.0.0.1:$PORT/$DEST_REL/$f" | sha256sum | awk '{print $1}')"
 DISK_SHA="$(sha256sum "$DEST_REL/$f" | awk '{print $1}')"
 [ "$LIVE_SHA" = "$DISK_SHA" ] || { echo "BLOCKED_V026_WRONG_LIVE_HTTP_ASSET=$f" >&2;exit 80; }
done
HTTP_SHA="$(sha256sum "$DEST_REL/viewer.mjs" | awk '{print $1}')"
HTTP_CORE_SHA="$(sha256sum "$DEST_REL/sidestep-core.mjs" | awk '{print $1}')"
HTTP_IK_SHA="$(sha256sum "$DEST_REL/left-contact.mjs" | awk '{print $1}')"
[ "$(sha256sum "$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || { echo 'BLOCKED_HAREWORKS_GLB_CHANGED' >&2;exit 80; }
python3 - "$STATE" "$CAMPAIGN_ID" "$BASE_SHA" "$NEW_SHA" "$ENTRY_SHA" "$MODEL_SHA" "$URL" "$PORT" "$SERVER_PID" "$CHECKOUT" "$AGENTS_BLOB" "$ETIQUETTE_DOC" "$TOPDOWN_DOC" "$HTTP_SHA" "$PUBLISHED_REUSE" "$RECOVERED_R2_PARTIAL_INIT" <<'V026_RECEIPT'
import datetime,json,pathlib,sys
(state,campaign,base,commit,entry,model,url,port,pid,checkout,agents,etiquette,topdown,viewer_hash,reused,recovered)=sys.argv[1:]
receipt={
 'campaign':campaign,'status':'GIT_PUBLISHED_LEFT_SOURCE_PROCEDURAL_VIEWER_OWNER_REVIEW_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sourceAnalysisVersion':'v0.2.7',
 'protectedForward':'v0.1.9','protectedBackward':'v0.1.24','rejectedLeft':'v0.1.25',
 'generatedRig':'74-bone source-calibrated mathematical pose, world-X stepping, bounded ankle IK, no AnimationMixer on generated',
 'sourceClips':['Cautious_Crouch_Walk_Left','Cautious_Crouch_Walk_Left_inplace'],
 'previousFailure':'v0.1.25 BACKWARD_UNKNOWN_DIRECTION_left: unrelated unpinned forward fallback',
 'newRuntimeNoBackwardOnlyDispatcher':True,'unrelatedReplLfsFetched':False,
 'rulesReadInAuthoringTurn':{'AGENTSBlob':agents,'CampaignEtiquetteDocument':etiquette,'TopDownEtiquetteDocument':topdown},
 'viewerUrl':url,'viewerPid':int(pid),'viewerPort':int(port),'viewerJsSha256':viewer_hash,
 'alreadyPublishedRerun':reused=='1',
 'realGLBHeaderAndRequiredClipsCheckedInTermux':True,
 'realBrowserSkinnedAnimationAudit':'PENDING; browser must load model, calibrate source, compare and measure contact',
 'skinnedSoleContactCertified':False,'leftGaitOwnerVisualAcceptance':False,
 'directionSlots':['forward (protected)','backward (protected)','left (visual review pending)']}
p=pathlib.Path(state)/'latest-receipt.json';p.write_text(json.dumps(receipt,indent=2)+'\n')
print('RECEIPT='+str(p))
V026_RECEIPT
STAGE='review-ready-owner-verdict-pending'
echo "CHECKOUT_READY=$CHECKOUT"
echo 'NORMAL_GIT_CHECKOUT=YES'
echo "REAL_LEFT_PROCEDURAL_REVIEW_ROOT=$CHECKOUT/$DEST_REL"
echo "MODEL_SHA256=$MODEL_SHA"
echo "PUBLISHED_COMMIT=$NEW_SHA"
echo "SCRIPT_SHA256=$ENTRY_SHA"
echo "VIEWER_PID=$SERVER_PID"
echo "VIEWER_URL=$URL"
echo "LEFT_SOURCE_MATH_SHA256=$HTTP_CORE_SHA"
echo "LIVE_VIEWER_JS_SHA256=$HTTP_SHA"
echo "LEFT_WORLD_ANKLE_IK_SHA256=$HTTP_IK_SHA"
echo 'CAMERA_ORBIT=RESTORED_SOURCE_CODE__PHONE_INTERACTION_PENDING'
echo 'DIRECTIONAL_SLOTS=FORWARD_BACKWARD_PROTECTED__LEFT_SOURCE_AUTHORED_REVIEW_PENDING__OTHER_FIVE_UNIMPLEMENTED'
echo 'CONTACT_GATE=PENDING_REAL_BROWSER_ANKLE_PIN_AUDIT__SKINNED_SOLE_NOT_CERTIFIED'
echo 'GAIT_RESEMBLANCE_GATE=REJECTED_V025__REAL_LEFT_V026_OWNER_VISUAL_REVIEW_PENDING'
if command -v termux-open-url >/dev/null 2>&1;then
 termux-open-url "$URL" || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
elif command -v am >/dev/null 2>&1;then
 am start -a android.intent.action.VIEW -d "$URL" >/dev/null 2>&1 || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
fi
