#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_TERRAIN_IK_STRESS_v0.1.21_DOCUMENTS
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_TERRAIN_IK_STRESS_v0.1.21_DOCUMENTS'
VERSION='v0.1.21'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='f19caf72ded2226889a50f2824c9895b7b914a2f'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-terrain-ik-stress-v0.1.21-v1-documents"
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
  grep -q 'hareworks-v0.1.21-true-terrain-surface-ik-test' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
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
[ -f tools/hareworks-forward-woman/v0.1.20/viewer.mjs ] || { echo 'BLOCKED_MISSING_SOURCE_GAIT_BASELINE' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.20/viewer.mjs)" = 978577d4b4d219af2c40e235a91a90586f3604b4 ] || { echo 'BLOCKED_PUBLISHED_V020_SOURCE_CHANGED' >&2;exit 74; }
[ -f tools/hareworks-forward-woman/v0.1.9/viewer.mjs ] || { echo 'BLOCKED_MISSING_ACCEPTED_V021_REFERENCE' >&2;exit 74; }
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
SOURCE_REL='tools/hareworks-forward-woman/v0.1.20'
[ -d "$CHECKOUT/$SOURCE_REL" ] || { echo 'BLOCKED_MISSING_PUBLISHED_V020_SOURCE' >&2;exit 77; }
cp -R "$CHECKOUT/$SOURCE_REL" "$DEST_REL"
for old_launcher in "$DEST_REL"/campaign-*.sh;do [ -f "$old_launcher" ] && rm -- "$old_launcher" || :;done
cp "$ENTRY" "$DEST_REL/campaign-v0.1.21-v1-godotprojects.sh"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.2" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3"
# Published v0.1.20 copied unchanged first. Protected knee and gait source stay unchanged.
cat > "$DEST_REL/terrain-core.mjs" <<'V021_TERRAIN_CORE'
/* Hareworks v0.1.21. The SAME deterministic height function drives visible
 * terrain triangles, world-space touchdown anchors, pelvis elevation and the
 * heel/sole/toe terrain clearance audit. No randomized scene-only bumps. */
export const TERRAIN_MODES=Object.freeze(['flat','uphill','downhill','cross-slope','rough']);
export const validTerrain=(mode,intensity)=>TERRAIN_MODES.includes(mode)&&Number.isFinite(intensity)&&intensity>=0&&intensity<=1.25;
export function terrainHeight(x,z,mode='flat',intensity=.65){
 if(!validTerrain(mode,intensity)||![x,z].every(Number.isFinite))throw Error('TERRAIN_INPUT_INVALID');
 const s=intensity;
 switch(mode){
  case 'flat':return 0;
  case 'uphill':return .085*s*z;
  case 'downhill':return -.085*s*z;
  case 'cross-slope':return .105*s*x;
  case 'rough':return s*(.026*Math.sin(2.0*z+.43*x)+.013*Math.sin(3.7*z-.81*x)+.009*(Math.cos(2.3*x+1.4*z)-1));
 }
 throw Error('TERRAIN_UNREACHABLE');
}
export function terrainNormal(x,z,mode='flat',intensity=.65){
 const e=.002;
 const dx=(terrainHeight(x+e,z,mode,intensity)-terrainHeight(x-e,z,mode,intensity))/(2*e),
       dz=(terrainHeight(x,z+e,mode,intensity)-terrainHeight(x,z-e,mode,intensity))/(2*e);
 const d=Math.hypot(dx,1,dz);
 return [-dx/d,1/d,-dz/d];
}
export function terrainBodyLift(previous,desired,dt){
 if(![previous,desired,dt].every(Number.isFinite)||dt<0||dt>.25)throw Error('TERRAIN_LIFT_INPUT_INVALID');
 const maxChange=.40*dt;
 return previous+Math.max(-maxChange,Math.min(maxChange,desired-previous));
}
export function terrainGrid(mode='rough',intensity=.65,centerZ=0,nx=24,nz=176){
 if(!validTerrain(mode,intensity)||!Number.isFinite(centerZ)||!Number.isInteger(nx)||!Number.isInteger(nz)||nx<2||nx>96||nz<2||nz>400)
  throw Error('TERRAIN_GRID_CONFIG_INVALID');
 const positions=[],colors=[],indices=[];
 for(let iz=0;iz<=nz;iz++){
  const z=centerZ-10+iz*54/nz;
  for(let ix=0;ix<=nx;ix++){
   const x=-2.65+ix*5.30/nx, y=terrainHeight(x,z,mode,intensity);
   positions.push(x,y,z);
   const contour=.5+.5*Math.sin(9.0*y+2.1*x),light=.86+.12*contour;
   colors.push(.23*light,.33*light,.30*light);
  }
 }
 for(let iz=0;iz<nz;iz++)for(let ix=0;ix<nx;ix++){
  const a=iz*(nx+1)+ix,b=a+1,c=a+(nx+1),d=c+1;
  indices.push(a,c,b,b,c,d);
 }
 return {positions,colors,indices,centerZ,triangles:indices.length/3};
}
V021_TERRAIN_CORE

cat > "$DEST_REL/terrain-core-test.mjs" <<'V021_TERRAIN_TEST'
import assert from 'node:assert/strict';
import {TERRAIN_MODES,terrainHeight,terrainNormal,terrainGrid,terrainBodyLift} from './terrain-core.mjs';
import {SourceFootContact} from './foot-gait.mjs';
const H=terrainHeight;
assert.equal(TERRAIN_MODES.length,5);
for(const x of [-2.1,0,1.4])for(const z of [-7,0,2,15])assert.equal(H(x,z,'flat',.65),0);
assert(Math.abs(H(0,0,'rough',.65))<1e-12);
assert(H(0,10,'uphill',1)>H(0,2,'uphill',1));
assert(H(0,10,'downhill',1)<H(0,2,'downhill',1));
assert(H(1,0,'cross-slope',1)>H(-1,0,'cross-slope',1));
for(const mode of TERRAIN_MODES){
 const mesh=terrainGrid(mode,.7,10,15,35),count=(15+1)*(35+1);
 assert.equal(mesh.positions.length,count*3);
 assert.equal(mesh.colors.length,count*3);
 assert.equal(mesh.indices.length,15*35*6);
 for(let i=0;i<count;i++){
  const [x,y,z]=mesh.positions.slice(i*3,i*3+3);
  assert(Math.abs(y-H(x,z,mode,.7))<1e-12,'visible mesh must be collision surface');
 }
 for(const i of mesh.indices)assert(i>=0&&i<count);
 for(const z of [0,.5,3,12]){
  const n=terrainNormal(.09,z,mode,.7);
  assert(n.every(Number.isFinite)&&Math.abs(Math.hypot(...n)-1)<1e-10);
  assert(n[1]>.95,'terrain too steep for this conservative IK test');
 }
}
assert.throws(()=>H(0,0,'random',1));
assert.throws(()=>H(NaN,0,'rough',1));
assert.throws(()=>terrainGrid('rough',1,0,0,10));
const samples=Array.from({length:60},(_,i)=>{
 const q=i/60,z=.18*Math.sin(2*Math.PI*q),x=.09;
 return {ankle:[x,.18,z],hip:[x,.9,0],knee:[x,.53,.1],heel:[x,.03,z-.07],sole:[x,0,z],toe:[x,.03,z+.08]};
});
let seen=0,stance=0,swing=0,anchorAtStance=null,held=0;
const witness=(kind)=>kind==='ankle'?[.09,.18,seen*.003]:[.09,0,seen*.003];
const contact=new SourceFootContact({samples,gait:{start:.10,duty:.58},sourceGround:0,
 readWitness:witness,rootAt:q=>q,terrainAt:(x,z)=>H(x,z,'rough',.7)});
for(let i=0;i<380;i++){
 seen=i;
 const phase=(i/130)%1;const result=contact.step({phase,worldZ:i*.003,totalPhase:i/130});
 assert(result.ankleTarget.every(Number.isFinite));
 if(result.planted){
  stance++;
  assert(Math.abs(result.anchor[1]-H(result.anchor[0],result.anchor[2],'rough',.7))<1e-12,'touchdown must land on real surface');
  if(anchorAtStance&&contact.pivot===anchorAtStance.pivot&&contact.transitions===anchorAtStance.transitions)
   {assert.deepEqual(result.anchor,anchorAtStance.anchor,'stance anchor slid while root walked');held++}
  anchorAtStance={anchor:result.anchor,pivot:contact.pivot,transitions:contact.transitions};
 }else{anchorAtStance=null;swing++;}
}
assert(stance>140&&swing>65&&held>60);
let y=0,prev=0;
for(let i=0;i<500;i++){
 const z=i*.004; y=terrainBodyLift(y,H(0,z,'rough',.7),1/120);
 assert(Math.abs(y-prev)<=.4/120+1e-11);prev=y;
}
assert.throws(()=>terrainBodyLift(0,1,NaN));
console.log('TERRAIN_MESH_EQUALS_PHYSICAL_HEIGHT_PASS modes='+TERRAIN_MODES.join(','));
console.log('TERRAIN_WORLD_TOUCHDOWN_LOCK_PASS stance='+stance+' swing='+swing+' held='+held);
console.log('TERRAIN_BODY_LIFT_CONTINUITY_PASS');
V021_TERRAIN_TEST

cat > "$DEST_REL/flat-parity-test.mjs" <<'V021_FLAT_PARITY_TEST'
import assert from 'node:assert/strict';
import {SourceFootContact as OriginalContact} from '../v0.1.20/foot-gait.mjs';
import {SourceFootContact as TerrainContact} from './foot-gait.mjs';
const samples=Array.from({length:360},(_,i)=>{
 const q=i/360,phi=2*Math.PI*q,z=.22*Math.cos(phi),x=.10;
 return {q,ankle:[x,.2+.03*Math.max(0,Math.sin(phi)),z],hip:[x,.9,0],knee:[x,.56,.1],
  heel:[x,.015,z-.09],sole:[x,.0,z],toe:[x,.015,z+.10]};
});
let current=0;
const readWitness=kind=>kind==='ankle'?[.10,.20,current*.003]:[.10,.007,current*.003];
const options={samples,gait:{start:.14,duty:.59},sourceGround:0,groundY:0,readWitness,rootAt:q=>q};
const old=new OriginalContact(options),next=new TerrainContact({...options,terrainAt:null});
let comparisons=0;
for(let i=0;i<1200;i++){
 current=i;const phase=(i/193.2)%1,worldZ=i*.003;
 const a=old.step({phase,worldZ,totalPhase:i/193.2}),b=next.step({phase,worldZ,totalPhase:i/193.2});
 assert.deepEqual(b,a,'flat-ground source gait must be byte-equivalent numerically at frame '+i);
 assert.equal(next.activeDuty,old.activeDuty);
 assert.equal(next.transitions,old.transitions);
 comparisons++;
}
const bad=new TerrainContact({...options,terrainAt:()=>NaN});
assert.throws(()=>bad.step({phase:.2,worldZ:0,totalPhase:.2}),/TERRAIN_CONTACT_ANCHOR_INVALID/);
console.log('FLAT_GROUND_V020_CONTACT_NUMERIC_PARITY_PASS frames='+comparisons);
console.log('TERRAIN_CONTACT_INVALID_SURFACE_FAIL_CLOSED_PASS');
V021_FLAT_PARITY_TEST

cat > "$DEST_REL/patch.py" <<'V021_PATCH_SOURCE'
#!/usr/bin/env python3
"""Hareworks v0.1.21 terrain stress harness. Copies v0.1.20; no historical edit."""
from pathlib import Path
import sys
root,dest=map(Path,sys.argv[1:])
v=dest/'viewer.mjs';s=v.read_text()
def one(a,b):
 global s
 n=s.count(a)
 if n!=1:raise RuntimeError('V021_PINNED_VIEWER_ANCHOR_'+str(n)+'_'+a[:100])
 s=s.replace(a,b,1)
one('/* v0.1.20. ONE moving Walking_Woman.', '/* v0.1.21. ONE moving Walking_Woman.')
one("import {inferVelocityContact,buildRootCurve,rootAt,kneeFlexion} from './root-motion.mjs';", "import {inferVelocityContact,buildRootCurve,rootAt,kneeFlexion} from './root-motion.mjs';\nimport {TERRAIN_MODES,terrainHeight,terrainNormal,terrainBodyLift,terrainGrid} from './terrain-core.mjs';")
one('const ground=new THREE.GridHelper(180,180,0x6b8696,0x354858);scene.add(ground);\nfor(let i=0;i<24;i++){const marker=new THREE.Mesh(new THREE.BoxGeometry(.075,.025,.075),new THREE.MeshBasicMaterial({color:i%2?0x42768b:0x6ea9a9}));marker.position.set(-1.3,.015,i*1.5);scene.add(marker)}',
'''const ground=new THREE.GridHelper(180,180,0x6b8696,0x354858);scene.add(ground);
const flatMarkers=new THREE.Group();scene.add(flatMarkers);
for(let i=0;i<24;i++){const marker=new THREE.Mesh(new THREE.BoxGeometry(.075,.025,.075),new THREE.MeshBasicMaterial({color:i%2?0x42768b:0x6ea9a9}));marker.position.set(-1.3,.015,i*1.5);flatMarkers.add(marker)}''')
one('let dynamicMotion=null; // v0.1.20 anatomical pre-IK targets never depend on foot yaw',
'''let dynamicMotion=null; // v0.1.20 original stateless knee solver remains unchanged
// Terrain is a true physical world surface, not a rendered displacement only.
const terrainArgs=new URLSearchParams(location.search);
let terrainMode=TERRAIN_MODES.includes(terrainArgs.get('terrain'))?terrainArgs.get('terrain'):'rough';
const requestedStrength=Number(terrainArgs.get('relief')??'.65');
let terrainStrength=Number.isFinite(requestedStrength)?clamp(requestedStrength,0,1.25):.65;
let groundLift=0,terrainMesh=null,terrainWire=null,terrainCenterZ=0;
const terrainAt=(x,z)=>terrainHeight(x,z,terrainMode,terrainStrength);''')
one('const wpos=b=>b.getWorldPosition(V());', '''// Both visible triangles and foot-contact targets use terrainAt() exactly.
function rebuildTerrain(centerZ=0){
 if(terrainMesh){scene.remove(terrainMesh);scene.remove(terrainWire);
  terrainMesh.geometry.dispose();terrainMesh.material.dispose();terrainWire.material.dispose();
  terrainMesh=null;terrainWire=null;}
 terrainCenterZ=centerZ;
 ground.visible=terrainMode==='flat';flatMarkers.visible=terrainMode==='flat';
 if(terrainMode==='flat')return;
 const grid=terrainGrid(terrainMode,terrainStrength,centerZ,24,176),geo=new THREE.BufferGeometry();
 geo.setAttribute('position',new THREE.Float32BufferAttribute(grid.positions,3));
 geo.setAttribute('color',new THREE.Float32BufferAttribute(grid.colors,3));
 geo.setIndex(grid.indices);geo.computeVertexNormals();
 terrainMesh=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.95,side:THREE.DoubleSide}));
 terrainWire=new THREE.Mesh(geo,new THREE.MeshBasicMaterial({color:0x9ad3d0,wireframe:true,transparent:true,opacity:.10,depthWrite:false}));
 scene.add(terrainMesh);scene.add(terrainWire);
}
rebuildTerrain(0);
function reloadTerrain(mode,strength){
 const url=new URL(location.href);url.searchParams.set('terrain',mode);url.searchParams.set('relief',String(strength));
 location.assign(url.toString()); // New terrain is a NEW run, never teleport a planted anchor.
}
$('terrain').value=terrainMode;$('terrainIntensity').value=String(terrainStrength);
$('terrainIntensityOut').textContent=Math.round(terrainStrength*100)+'%';
$('terrain').onchange=()=>reloadTerrain($('terrain').value,terrainStrength);
$('terrainIntensity').oninput=()=>{$('terrainIntensityOut').textContent=Math.round(Number($('terrainIntensity').value)*100)+'%'};
$('terrainIntensity').onchange=()=>reloadTerrain(terrainMode,Number($('terrainIntensity').value));
const wpos=b=>b.getWorldPosition(V());''')
one('worldZ+=(nextCycle-previewCycle)*dynamicMotion.stride;\n previewCycle=nextCycle;phase=mod1(previewCycle);',
'''worldZ+=(nextCycle-previewCycle)*dynamicMotion.stride;
 groundLift=terrainBodyLift(groundLift,terrainAt(0,worldZ),Math.min(.25,Math.max(0,dt)));
 previewCycle=nextCycle;phase=mod1(previewCycle);''')
one('actor.position.z=worldZ;actor.position.y=-groundOffset;actor.updateMatrixWorld(true);}',
'''actor.position.z=worldZ;actor.position.y=-groundOffset+groundLift;actor.updateMatrixWorld(true);}''')
one('worldZ+=rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);\n totalPhase=newPhase;phase=mod1(totalPhase);frameBody(phase);',
'''worldZ+=rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);
 groundLift=terrainBodyLift(groundLift,terrainAt(0,worldZ),dt);
 totalPhase=newPhase;phase=mod1(totalPhase);frameBody(phase);''')
one('phase=0;totalPhase=0;worldZ=0;dynamicMotion=speedGait(speed,rootCurve.stride);',
'''phase=0;totalPhase=0;worldZ=0;groundLift=terrainAt(0,0);dynamicMotion=speedGait(speed,rootCurve.stride);''')
one('sourceGround,readWitness:k=>witnessCache[side][k],rootAt:q=>rootAt(rootCurve,q),\n  transformSource:(s,gait)=>transformSourceFoot(s,side,gait||dynamicMotion)});',
'''sourceGround,readWitness:k=>witnessCache[side][k],rootAt:q=>rootAt(rootCurve,q),
  terrainAt:terrainMode==='flat'?null:terrainAt,
  transformSource:(s,gait)=>transformSourceFoot(s,side,gait||dynamicMotion)});''')
one('const kneeChanged=kneeBefore.distanceTo(wpos(c.knee));',
'''// Pitch/roll the already-styled shoe to the measured surface normal.
 // This is distal only: the accepted knee poles, joint positions and foot yaw
 // remain unmodified. Real skinned heel/toe clearance is audited below.
 if(terrainMode!=='flat'){
  const footP=wpos(c.foot),normal=V(...terrainNormal(footP.x,footP.z,terrainMode,terrainStrength));
  const slopeTilt=Q().setFromUnitVectors(V(0,1,0),normal);
  setWorldQ(c.foot,Q().slerp(slopeTilt,.72).multiply(wq(c.foot)).normalize());actor.updateMatrixWorld(true);
 }
 const kneeChanged=kneeBefore.distanceTo(wpos(c.knee));''')
one("const h=['heel','sole','toe'].map(k=>witnessWorld(c,k).y);\n maxPenetration=Math.max(maxPenetration,Math.max(0,...h.map(y=>-y)));",
'''const footPatches=['heel','sole','toe'].map(k=>witnessWorld(c,k));
 const terrainIntrusion=Math.max(0,...footPatches.map(p=>terrainAt(p.x,p.z)-p.y));
 maxPenetration=Math.max(maxPenetration,terrainIntrusion);''')
one('kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch};',
'''kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch,
  terrainHeightAtPivot:terrainAt(actual.x,actual.z),terrainClearance:actual.y-terrainAt(actual.x,actual.z),
  terrainMode};''')
one('contactFrames:contactCount,swingFrames:swingCount,solvedIKPerFrame:true,generatedAnimationMixerCount:0};',
'''contactFrames:contactCount,swingFrames:swingCount,solvedIKPerFrame:true,generatedAnimationMixerCount:0,
 terrainMode,terrainStrength,bodyTerrainLift:groundLift};''')
one('Skinned support error ${maxDrift.toFixed(5)} u, floor penetration ${maxPenetration.toFixed(5)} u',
'''Skinned support error ${maxDrift.toFixed(5)} u, TERRAIN penetration ${maxPenetration.toFixed(5)} u
Surface ${terrainMode} at ${Math.round(terrainStrength*100)}% · root ground Y ${terrainAt(0,worldZ).toFixed(4)} · body lift ${groundLift.toFixed(4)}''')
one('sourceClip:CLIP,rigBones:74,sourceContactMethod:sourceGaits,sourceSeamRepair,',
'''sourceClip:CLIP,rigBones:74,sourceContactMethod:sourceGaits,sourceSeamRepair,
    terrainMode,terrainStrength,terrainSourceOfTruth:'terrain-core.mjs height(x,z) shared by mesh, touchdown, swing, body and audit',
    surfaceAtRoot:terrainAt(0,worldZ),bodyTerrainLift:groundLift,terrainContactsUseWorldSpace:true,''')
one('function frame(now){requestAnimationFrame(frame);',
'''function frame(now){requestAnimationFrame(frame);
 if(terrainMode!=='flat'&&worldZ-terrainCenterZ>14)rebuildTerrain(Math.floor(worldZ/14)*14);''')
one('const startZ=worldZ;for(let i=0;i<32;i++)physicsStep(1/120);',
'''const startZ=worldZ;for(let i=0;i<32;i++)physicsStep(1/120);''') if False else None
one("status('PHYSICAL IK CONTROLLER STARTED · 32 REAL SKINNED STEPS EXECUTED · owner gait approval pending');",
    "status('PHYSICAL IK ON '+terrainMode.toUpperCase()+' TERRAIN · 32 real skinned startup steps · run contact audit to verify ground clearance');")
one("ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,",
'''ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,''') if False else None
# Reuse v0.1.20 original source knees, foot yaw, and protected gait math; version UI only.
s=s.replace('v0.1.20','v0.1.21').replace('V0.1.20','V0.1.21')
assert "terrainAt:terrainMode==='flat'?null:terrainAt" in s
assert "const pole=stableForwardPole(side,yaw);" in s
assert "const chosen=chooseSourceKnee" in s
assert "distalHeading(side,footFit,pelvisProfile)" in s
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
v.write_text(s.rstrip()+'\n')
# Physical ground anchor is the selected surface height, not a screen ornament.
f=dest/'foot-gait.mjs';src=f.read_text()
def replace_foot(old,new,expected=1):
 global src
 n=src.count(old)
 if n!=expected:raise RuntimeError('V021_FOOT_ANCHOR_COUNT_'+str(n)+'_'+old[:70])
 src=src.replace(old,new)
replace_foot('constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0,transformSource=null}){',
             'constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0,transformSource=null,terrainAt=null}){')
replace_foot('this.readWitness=readWitness;this.rootAt=rootAt;this.transformSource=transformSource;this.activeDuty=gait.duty;',
             'this.readWitness=readWitness;this.rootAt=rootAt;this.transformSource=transformSource;this.terrainAt=terrainAt;this.activeDuty=gait.duty;')
replace_foot(' step({phase,worldZ,totalPhase,gait}){', ''' captureAnchor(kind){
  const anchor=this.readWitness(kind).slice();
  if(this.terrainAt)anchor[1]=this.terrainAt(anchor[0],anchor[2]);
  if(!finite(anchor))throw Error('TERRAIN_CONTACT_ANCHOR_INVALID');
  return anchor;
 }
 step({phase,worldZ,totalPhase,gait}){''')
replace_foot('const baseline=add(s.ankle,[0,-this.sourceGround,worldZ]);',
             '''const baseline=add(s.ankle,[0,-this.sourceGround,worldZ]);
  if(this.terrainAt)baseline[1]+=this.terrainAt(baseline[0],baseline[2]);''')
replace_foot('this.anchor=this.readWitness(pivot).slice();','this.anchor=this.captureAnchor(pivot);',2)
replace_foot('Math.abs(this.anchor[1]-this.groundY)',
             'Math.abs(this.anchor[1]-(this.terrainAt?this.terrainAt(this.anchor[0],this.anchor[2]):this.groundY))',2)
assert src.count('this.anchor=this.captureAnchor(pivot)')==2
f.write_text(src.rstrip()+'\n')
# UI selects separate physical tests, never invisibly changes terrain mid-contact.
p=dest/'index.html';html=p.read_text()
needle='<div class="bar" role="group" aria-label="Orbit camera presets (drag to rotate, pinch to zoom)">'
assert html.count(needle)==1
block='''<div class="bar" role="group" aria-label="Physical terrain test selection">
<label for="terrain">Ground surface</label><select id="terrain"><option value="flat">Flat control</option><option value="uphill">Uphill</option><option value="downhill">Downhill</option><option value="cross-slope">Side slope</option><option value="rough">Rough ground</option></select>
<label for="terrainIntensity">Slope / relief</label><input id="terrainIntensity" type="range" min="0" max="1.25" step="0.05" value="0.65"><output id="terrainIntensityOut">65%</output>
<span class="small">Surface change restarts the run to avoid teleporting planted feet. Green and orange markers show true world contact targets. Default: rough.</span></div>
'''
html=html.replace(needle,block+needle)
html=html.replace('button,input{font:inherit}', 'button,input,select{font:inherit}')
html=html.replace('v0.1.20','v0.1.21').replace('V0.1.20','V0.1.21')
html=html.replace('v0.1.20-source-knees','v0.1.21-terrain-world-contact')
html=html.replace('One source-measured, independently IK-solved skinned Hareworks character',
'''One source-measured, independently IK-solved skinned Hareworks character on physically sampled rough or sloped ground''')
html=html.replace('Audit source gait + skinned contacts','Audit terrain + real skinned contacts')
p.write_text(html.rstrip()+'\n')
p=dest/'review-server.py';txt=p.read_text().replace('v0.1.20','v0.1.21').replace('V0.1.20','V0.1.21');p.write_text(txt.rstrip()+'\n')
print('V021_PINNED_TERRAIN_PATCH_PASS: source knees, foot heading and flat-gait retained')
V021_PATCH_SOURCE

cat > "$DEST_REL/contract.json" <<'V021_CONTRACT'
{
  "schema": "hareworks-v0.1.21-true-terrain-surface-ik-test",
  "repo": "Valar05/parametric-parambulator",
  "parent": "f19caf72ded2226889a50f2824c9895b7b914a2f",
  "sourceController": "tools/hareworks-forward-woman/v0.1.20/viewer.mjs",
  "sourceControllerBlob": "978577d4b4d219af2c40e235a91a90586f3604b4",
  "sourceFootContactBlob": "d896cf21146873ab968c73e21ab63b8fe50799e9",
  "sourceKneeGovernorBlob": "eefc2b0b867778bb384eafe95af4e63d7caa2f6b",
  "sourceFootHeadingBlob": "39108d51fcd6f1d0133e8ebdb79c665350bc1a4b",
  "canonicalModelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "rulesAGENTSBlob": "547c2af52303f4efb718bbf8f82a698110c7bfca",
  "rulesCampaignEtiquetteDoc": "1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI",
  "rulesTopdownDoc": "1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU",
  "executionLane": "Android Termux Git only",
  "mutablePaths": [
    "tools/hareworks-forward-woman/v0.1.21/"
  ],
  "ownerVisualVerdict": "v0.1.20 good enough for terrain experiment, not final runway/catwalk approval",
  "protectedGait": "v0.1.20 stateless forward knee poles, source ankle/pelvis, speed gait, foot heading, camera and world root are unchanged",
  "terrainModes": [
    "flat",
    "uphill",
    "downhill",
    "cross-slope",
    "rough"
  ],
  "sharedPhysicalSurface": "terrain-core.mjs terrainHeight(x,z) drives rendered ground, stance anchor y, swing targets, body lift and heel/toe intrusion audit",
  "terrainChangePolicy": "explicit full review reload and reset; never mutate the terrain under planted anchors",
  "realGLBAudit": "browser control/button, not author-side synthesized PASS",
  "modelModified": false,
  "ownerVisualAcceptance": false
}
V021_CONTRACT

cat > "$DEST_REL/README.md" <<'V021_README'
# Hareworks v0.1.21: real terrain-contact stress test

The owner accepts v0.1.20 as a sufficient **temporary gait baseline** for testing uneven ground, not the finished catwalk. This version is a terrain harness, not a leg-style revision.

Five selectable surfaces: flat (baseline parity), uphill, downhill, cross-slope and smooth deterministic rough ground. Rough is the initial review preset at 65% intensity, with a 0–125% adjustable strength and a one-tap return to flat. Switching terrain reloads and resets the run, preventing instantaneous mutation under an already planted foot.

The terrain module defines **one physical world-space height function** for visible mesh, heel/sole/toe planted anchor Y, swing targets, pelvis ground-following and penetration metrics. No painted-only bumps and no clip playback. The physical solver still samples the original Walking_Woman nine-clip GLB, 74 bones and original source-derived knee/ankle curves; its stance anchor x/z is held in world space at the actual selected terrain elevation. Hip/root Y follows terrain continuously with bounded rate. The original distal foot heading is preserved, with terrain-normal pitch and roll applied *after* the knee solve, no yaw steering of knees.

The real 120Hz browser audit reports terrain-relative heel/sole/toe intrusion, world-anchor drift, reach conflict, knee source deviation, root speed and contact transitions. It is **not** allowed to report real terrain contact PASS if source knee preservation prevents a plant. The initial 32-step skinned-model startup smoke is distinct from full gait audit and owner visual assessment. A procedural preview remains visibly labeled unpinned on any blocking failure.

Safety: new v0.1.21 files only, immutable model SHA-256, v0.1.20 original knee-governor and v0.1.18 accepted foot heading **byte-identical**, camera OrbitControls retained, previous version directories untouched, one checked Android Documents Git worktree, Termux Git commit/push/readback, explicit cache-busted viewer URL and persistent receipt. No direct GitHub mutations.
V021_README
# Model and immutable source file provenance before the test runner.
[ "$(git -C "$CHECKOUT" hash-object tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json)" = f6e8940b5eaeaf154a126eaa5221dcfcab0d94d1 ] || { echo 'BLOCKED_SOURCE_KNEE_REFERENCE_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object tools/hareworks-forward-woman/v0.1.3/foot-profile.json)" = 6febeaa8ff461806b590748dfca6461f4d8df1db ] || { echo 'BLOCKED_SOURCE_LEG_LINKS_CHANGED' >&2;exit 77; }
# Previously accepted foot heading and current knee governor stay byte-identical.
[ "$(git -C "$CHECKOUT" hash-object "$BUILDROOT/$DEST_REL/foot-heading.mjs")" = "$(git -C "$CHECKOUT" hash-object "$CHECKOUT/tools/hareworks-forward-woman/v0.1.18/foot-heading.mjs")" ] || { echo 'BLOCKED_APPROVED_FOOT_HEADING_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object "$BUILDROOT/$DEST_REL/source-knee-governor.mjs")" = eefc2b0b867778bb384eafe95af4e63d7caa2f6b ] || { echo 'BLOCKED_ACCEPTED_V020_KNEE_SOLVER_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object "$BUILDROOT/$DEST_REL/speed-gait.mjs")" = 0a06cf25367bbf945155cfd4756954a54194fec6 ] || { echo 'BLOCKED_ACCEPTED_SPEED_GAIT_CHANGED' >&2;exit 77; }
python3 "$DEST_REL/patch.py" "$CHECKOUT" "$DEST_REL"
STAGE='test-terrain-world-ik'
# v016 already patched using exact published v015 source
:
python3 - "$DEST_REL/patch.py" "$DEST_REL/review-server.py" "$DEST_REL/startup-regression.py" <<'PYPARSE'
import pathlib,sys
for p in sys.argv[1:]:compile(pathlib.Path(p).read_text(),p,'exec')
print('PYTHON_SYNTAX_PASS')
PYPARSE
for f in root-motion.mjs foot-gait.mjs root-model-test.mjs contact-test.mjs viewer.mjs shoe-witness.mjs shoe-witness-test.mjs archived-root-regression.mjs foot-heading.mjs foot-heading-test.mjs source-knee-governor.mjs source-knee-governor-test.mjs knee-source-invariant-test.mjs speed-gait.mjs terrain-core.mjs terrain-core-test.mjs flat-parity-test.mjs;do
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
cp "$CHECKOUT/$SOURCE_REL/foot-gait.mjs" "$CHECKOUT/$SOURCE_REL/root-motion.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.20/"
node "$DEST_REL/flat-parity-test.mjs"
node "$DEST_REL/terrain-core-test.mjs"
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
git commit -m 'Hareworks v0.1.21 physical uphill rough and cross-slope IK stress viewer'
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
for terrain_file in terrain-core.mjs terrain-core-test.mjs flat-parity-test.mjs foot-heading.mjs patch.py index.html review-server.py;do
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
 for f in viewer.mjs foot-gait.mjs root-motion.mjs source-knee-governor.mjs terrain-core.mjs terrain-core-test.mjs flat-parity-test.mjs index.html;do
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
 'campaign':campaign,'status':'PERSISTENT_CHECKOUT_AND_V021_TERRAIN_PHYSICAL_STRESS_VIEWER_PUBLISHED_BROWSER_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sparseCheckout':False,
 'androidSharedStorageGitTrust':'exact-canonical-project-only, global safe.directory',
 'lfsStatusGuard':'Git LFS filters configured locally; only exactly SHA-verified tracked Hareworks binary is admissible as unstaged model materialization',
 'lfsStatusGuardDoesNotHideChanges':True,
 'previousIncompleteGitInitRecovered':recovered=='1',
 'acceptedV021Math':'v0.1.9 original ankle/pelvis plus 60-frame real-source knee plane restored; distal foot yaw unchanged; physical centerline guard runs every frame; real browser audit pending',
 'shoeWitnesses':'v0.1.14 whole skinned foot low-surface longitudinal PCA bands, preserved unchanged',
 'calibrationFailureBehavior':'source procedural preview moving but explicitly UNPINNED and unapproved',
 'camera':'orbit and zoom with world-target follow',
 'unrelatedReplLfsFetched':False,'hareworksCopyPolicy':'exactly one verified worktree model, reusable private LFS cache',
 'rulesReadInAuthoringTurn':{'AGENTSBlob':agents,'CampaignEtiquetteDocument':etiquette,'TopDownEtiquetteDocument':topdown},
 'viewerUrl':url,'viewerPid':int(pid),'viewerPort':int(port),'viewerGaitSha256':viewer_hash,
 'alreadyPublishedRerun':reused=='1','browserRealSkinnedFootAudit':'PENDING; startup preview mode is not a physics audit',
 'actualSkinned3dPhysicsTestedInTermux':False,
 'contactGate':'PENDING_BROWSER_TERRAIN_AUDIT; world-space heel/sole/toe grade verification required; WARN is not PASS','gaitResemblanceGate':'PENDING_OWNER_VISUAL_ACCEPTANCE; diagnostic preview expressly NOT acceptable as physical ground pinning',
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
echo 'TERRAIN_SURFACES=FLAT_UPHILL_DOWNHILL_CROSS_SLOPE_ROUGH__REAL_SKINNED_OWNER_REVIEW_PENDING'
echo 'CONTACT_GATE=PENDING_REAL_BROWSER_TERRAIN_AUDIT__PREVIEW_IS_UNPINNED_IF_PHYSICS_FAILS'
echo 'GAIT_RESEMBLANCE_GATE=PENDING_OWNER_VISUAL_ACCEPTANCE'
if command -v termux-open-url >/dev/null 2>&1;then
 termux-open-url "$URL" || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
elif command -v am >/dev/null 2>&1;then
 am start -a android.intent.action.VIEW -d "$URL" >/dev/null 2>&1 || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
fi
