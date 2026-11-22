#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_PROFILE_STRESS_v0.1.22_DOCUMENTS
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_PROFILE_STRESS_v0.1.22_DOCUMENTS'
VERSION='v0.1.22'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='6b5843132ed6e896c7dd928b8a43fd5bf7805ad6'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-profile-stress-v0.1.22-v1-documents"
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
  grep -q 'hareworks-v0.1.22-width-invariant-terrain-ik-stress-test' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
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
[ -f tools/hareworks-forward-woman/v0.1.21/viewer.mjs ] || { echo 'BLOCKED_MISSING_SOURCE_GAIT_BASELINE' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.21/viewer.mjs)" = 4b05c9af000e0c30919d4bb7fc47cb183fed425f ] || { echo 'BLOCKED_PUBLISHED_V021_SOURCE_CHANGED' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.21/terrain-core.mjs)" = d6c6c846579787ffc4f24c52047f5a0028b8a97a ] || { echo 'BLOCKED_PUBLISHED_V021_TERRAIN_CHANGED' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.21/foot-gait.mjs)" = ecc036c99f92dfa02b17a9457e76b0998a127c04 ] || { echo 'BLOCKED_PUBLISHED_V021_FOOT_TARGET_CHANGED' >&2;exit 74; }
[ -f tools/hareworks-forward-woman/v0.1.9/viewer.mjs ] || { echo 'BLOCKED_MISSING_ACCEPTED_V022_REFERENCE' >&2;exit 74; }
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
SOURCE_REL='tools/hareworks-forward-woman/v0.1.21'
[ -d "$CHECKOUT/$SOURCE_REL" ] || { echo 'BLOCKED_MISSING_PUBLISHED_V021_SOURCE' >&2;exit 77; }
cp -R "$CHECKOUT/$SOURCE_REL" "$DEST_REL"
for old_launcher in "$DEST_REL"/campaign-*.sh;do [ -f "$old_launcher" ] && rm -- "$old_launcher" || :;done
cp "$ENTRY" "$DEST_REL/campaign-v0.1.22-v1-godotprojects.sh"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.2" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3"
# Published v0.1.20 copied unchanged first. Protected knee and gait source stay unchanged.
cat > "$DEST_REL/terrain-core.mjs" <<'V022_TERRAIN_CORE'
/* Hareworks 0.1.22: true physical, easily readable longitudinal terrain.
 * The three PROFILE_* surfaces are extruded identically across X.
 * One analytic height drives visible geometry and the physical IK/test surface.
 * Older v0.1.21 surfaces and flat controls remain available unchanged. */
export const TERRAIN_MODES=Object.freeze([
 'flat','uphill','downhill','cross-slope','rough',
 'profile-ridges','profile-steps','profile-ramp'
]);
export const isProfileTerrain=mode=>mode.startsWith('profile-');
export const validTerrain=(mode,intensity)=>TERRAIN_MODES.includes(mode)&&Number.isFinite(intensity)&&intensity>=0&&intensity<=3;
const clamp=(v,lo,hi)=>Math.min(hi,Math.max(lo,v));
const smooth=t=>{const u=clamp(t,0,1);return u*u*(3-2*u)};
const step=(z,z0,width)=>smooth((z-z0)/width);
// Cyclic step course: climb two blocks, descend two blocks; no unbounded rise.
// The 0.58-unit ramps have a finite slope and are not vertical teleportations.
function stairCourse(z){
 const t=((z-1.10)%12+12)%12;
 const safe=z>=1.10?1:0;
 return safe*(step(t,0,.58)+step(t,2.75,.58)-step(t,6.0,.58)-step(t,8.80,.58));
}
export function terrainHeight(x,z,mode='profile-ridges',intensity=1.1){
 if(!validTerrain(mode,intensity)||![x,z].every(Number.isFinite))throw Error('TERRAIN_INPUT_INVALID');
 const s=intensity;
 switch(mode){
  case 'flat':return 0;
  case 'uphill':return .085*s*z;
  case 'downhill':return -.085*s*z;
  case 'cross-slope':return .105*s*x;
  case 'rough':return s*(.026*Math.sin(2.0*z+.43*x)+.013*Math.sin(3.7*z-.81*x)+.009*(Math.cos(2.3*x+1.4*z)-1));
  case 'profile-ridges':{
   // A real heightfield with pronounced sequential obstacles, identical for both feet.
   const onset=smooth((z-.15)/.90);
   return s*onset*(.135*Math.sin(1.92*(z-.15))+.066*Math.sin(4.10*(z-.15)));
  }
  case 'profile-steps':return .205*s*stairCourse(z);
  case 'profile-ramp':return .16*s*(z>0?z:0);
 }
 throw Error('TERRAIN_MODE_UNREACHABLE');
}
export function terrainNormal(x,z,mode='profile-ridges',intensity=1.1){
 const e=.002;
 const dx=(terrainHeight(x+e,z,mode,intensity)-terrainHeight(x-e,z,mode,intensity))/(2*e);
 const dz=(terrainHeight(x,z+e,mode,intensity)-terrainHeight(x,z-e,mode,intensity))/(2*e);
 const length=Math.hypot(dx,1,dz);
 return [-dx/length,1/length,-dz/length];
}
export function terrainBodyLift(previous,desired,dt){
 if(![previous,desired,dt].every(Number.isFinite)||dt<0||dt>.25)throw Error('TERRAIN_LIFT_INPUT_INVALID');
 // Up to 1.5 surface-units/s on hard steps; finite, bounded and continuous.
 const maxChange=1.50*dt;
 return previous+clamp(desired-previous,-maxChange,maxChange);
}
export function terrainGrid(mode='profile-ridges',intensity=1.1,centerZ=0,nx=12,nz=400){
 if(!validTerrain(mode,intensity)||!Number.isFinite(centerZ)||!Number.isInteger(nx)||!Number.isInteger(nz)||nx<2||nx>96||nz<2||nz>400)
  throw Error('TERRAIN_GRID_CONFIG_INVALID');
 const profile=isProfileTerrain(mode),start=profile?centerZ-6:centerZ-10,extent=profile?24:54;
 const halfWidth=profile?1.35:2.65,positions=[],colors=[],indices=[];
 for(let iz=0;iz<=nz;iz++){
  const z=start+iz*extent/nz;
  for(let ix=0;ix<=nx;ix++){
   const x=-halfWidth+ix*2*halfWidth/nx, y=terrainHeight(x,z,mode,intensity);
   positions.push(x,y,z);
   // No lateral striping in PROFILE modes: the silhouette is the actual height.
   const contour=.5+.5*Math.sin(10*y+1.30*z),light=.80+.16*contour;
   colors.push(.21*light,.30*light,.29*light);
  }
 }
 for(let iz=0;iz<nz;iz++)for(let ix=0;ix<nx;ix++){
  const a=iz*(nx+1)+ix,b=a+1,c=a+(nx+1),d=c+1;
  indices.push(a,c,b,b,c,d);
 }
 return {positions,colors,indices,centerZ,start,extent,halfWidth,triangles:indices.length/3};
}
export function longitudinalProfile(mode,intensity,centerZ=0,count=400){
 if(!validTerrain(mode,intensity)||!Number.isInteger(count)||count<2||count>1000)throw Error('TERRAIN_PROFILE_CONFIG_INVALID');
 const g=terrainGrid(mode,intensity,centerZ,2,Math.min(count,400));
 return Array.from({length:count+1},(_,i)=>{
  const z=g.start+i*g.extent/count;
  return {z,y:terrainHeight(0,z,mode,intensity)};
 });
}
V022_TERRAIN_CORE

cat > "$DEST_REL/terrain-core-test.mjs" <<'V022_TERRAIN_TEST'
import assert from 'node:assert/strict';
import {TERRAIN_MODES,isProfileTerrain,terrainHeight as H,terrainNormal,terrainGrid,terrainBodyLift,longitudinalProfile,validTerrain} from './terrain-core.mjs';
import {SourceFootContact} from './foot-gait.mjs';
assert.equal(TERRAIN_MODES.length,8);
for(const z of [-4,0,1,3,7,14])for(const x of [-1.35,0,1.35])assert.equal(H(x,z,'flat',2),0);
for(const mode of ['profile-ridges','profile-steps','profile-ramp']){
 assert(isProfileTerrain(mode));
 for(const strength of [.2,1.1,3])for(let z=-2;z<=20;z+=.15){
  const y=H(0,z,mode,strength);
  for(const x of [-1.35,-.8,-.1,.1,.8,1.35])assert.equal(H(x,z,mode,strength),y,'GROUND_HEIGHT_MUST_BE_SAME_ACROSS_WIDTH '+mode);
  const n=terrainNormal(.6,z,mode,strength);
  assert(Math.abs(n[0])<1e-10,'NO_LATERAL_GRADE_IN_PROFILE '+mode);
  assert(Math.abs(Math.hypot(...n)-1)<1e-8);
 }
 const mesh=terrainGrid(mode,1.4,7,12,400);
 assert.equal(mesh.positions.length,13*401*3);
 for(let i=0;i<mesh.positions.length;i+=3){const [x,y,z]=mesh.positions.slice(i,i+3);assert(Math.abs(y-H(x,z,mode,1.4))<1e-12);}
 const edge=longitudinalProfile(mode,1.4,7,400);
 assert.equal(edge.length,401);
 for(const {z,y} of edge)assert(Math.abs(y-H(-1.35,z,mode,1.4))<1e-12);
}
assert(Math.max(...Array.from({length:200},(_,i)=>Math.abs(H(0,i*.085,'profile-ridges',3))))>.30,'MAX_RIDGE_NOT_STRESSFUL');
assert(H(0,4,'profile-steps',3)>.50,'MAX_STEP_NOT_STRESSFUL');
assert(H(0,4,'profile-ramp',3)>1.8,'MAX_RAMP_NOT_STRESSFUL');
assert(Math.abs(H(0,8,'rough',.7)-H(.8,8,'rough',.7))>1e-4,'old surface remains independent selectable option');
assert.throws(()=>H(0,0,'bad',1));assert.throws(()=>H(0,0,'profile-steps',3.01));
assert.throws(()=>terrainGrid('profile-steps',1,0,5,401));
const samples=Array.from({length:60},(_,i)=>{const q=i/60,z=.18*Math.sin(2*Math.PI*q);return {ankle:[.08,.18,z],hip:[.08,.9,0],knee:[.08,.53,.1],heel:[.08,.03,z-.07],sole:[.08,0,z],toe:[.08,.03,z+.08]};});
let tick=0,held=0,previous=null;
const C=new SourceFootContact({samples,gait:{start:.1,duty:.58},sourceGround:0,readWitness:k=>[.08,k==='ankle'?.18:0,tick*.003],rootAt:q=>q,terrainAt:(x,z)=>H(x,z,'profile-steps',2.5)});
for(let i=0;i<450;i++){
 tick=i;const r=C.step({phase:(i/130)%1,worldZ:i*.003,totalPhase:i/130});
 if(!r.planted){previous=null;continue;}
 assert(Math.abs(r.anchor[1]-H(r.anchor[0],r.anchor[2],'profile-steps',2.5))<1e-12,'STRESS_GROUND_CONTACT_Y');
 if(previous&&previous.pivot===r.pivot&&previous.transitions===C.transitions){assert.deepEqual(r.anchor,previous.anchor,'PINNED_CONTACT_SLID');held++;}
 previous={pivot:r.pivot,transitions:C.transitions,anchor:r.anchor};
}
assert(held>80);
let y=0;for(let i=0;i<400;i++){let ny=terrainBodyLift(y,H(0,i*.015,'profile-ramp',3),1/120);assert(Math.abs(ny-y)<=1.5/120+1e-11);y=ny;}
console.log('WIDTH_INVARIANT_LONGITUDINAL_PROFILE_PASS modes=3, strengths=3, width=2.70 units');
console.log('TRUE_STRESS_GEOMETRY_PASS fullMax=300% profileRidges/profileSteps/profileRamp');
console.log('REAL_TOUCHDOWN_ANCHOR_HEIGHT_AND_LOCK_PASS held='+held);
V022_TERRAIN_TEST

cat > "$DEST_REL/patch.py" <<'V022_PATCH_SOURCE'
#!/usr/bin/env python3
"""Hareworks v0.1.22: severe longitudinal terrain and readable ground witnesses.
Build a new immutable version from exact published v0.1.21. Never edit older versions.
"""
from pathlib import Path
import sys
source,dest=map(Path,sys.argv[1:])
v=dest/'viewer.mjs';s=v.read_text()
def one(old,new):
 global s
 count=s.count(old)
 if count!=1:raise RuntimeError(f'V022_PINNED_VIEWER_ANCHOR_{count}_'+old[:125])
 s=s.replace(old,new,1)
one('/* v0.1.21. ONE moving Walking_Woman.', '/* v0.1.22. ONE moving Walking_Woman.')
one("import {TERRAIN_MODES,terrainHeight,terrainNormal,terrainBodyLift,terrainGrid} from './terrain-core.mjs';",
    "import {TERRAIN_MODES,isProfileTerrain,terrainHeight,terrainNormal,terrainBodyLift,terrainGrid,longitudinalProfile} from './terrain-core.mjs';")
one("let terrainMode=TERRAIN_MODES.includes(terrainArgs.get('terrain'))?terrainArgs.get('terrain'):'rough';",
    "let terrainMode=TERRAIN_MODES.includes(terrainArgs.get('terrain'))?terrainArgs.get('terrain'):'profile-ridges';")
one("const requestedStrength=Number(terrainArgs.get('relief')??'.65');",
    "const requestedStrength=Number(terrainArgs.get('relief')??'1.1');")
one('let terrainStrength=Number.isFinite(requestedStrength)?clamp(requestedStrength,0,1.25):.65;',
    'let terrainStrength=Number.isFinite(requestedStrength)?clamp(requestedStrength,0,3):1.1;')
one('let groundLift=0,terrainMesh=null,terrainWire=null,terrainCenterZ=0;',
    '''let groundLift=0,terrainMesh=null,terrainWire=null,terrainSlice=null,terrainCenterZ=0;
const profileMode=()=>isProfileTerrain(terrainMode);
// Ground projection markers show the exact height directly beneath each
// actual skinned heel, sole and toe. They never write IK targets or knee poles.
const projectedWitnesses={left:{},right:{}};
const witnessKinds=['heel','sole','toe'];''')
one("const drawPins={};for(const side of ['left','right']){const m=new THREE.Mesh(new THREE.SphereGeometry(.045,12,10),new THREE.MeshBasicMaterial({color:side==='left'?0x6bf5bf:0xb8fa83,depthTest:false}));m.renderOrder=15;scene.add(m);drawPins[side]=m;}",
'''const drawPins={};for(const side of ['left','right']){const m=new THREE.Mesh(new THREE.SphereGeometry(.045,12,10),new THREE.MeshBasicMaterial({color:side==='left'?0x6bf5bf:0xb8fa83,depthTest:false}));m.renderOrder=15;scene.add(m);drawPins[side]=m;}
for(const side of ['left','right'])for(const kind of witnessKinds){
 const r=kind==='sole'?.030:.019;
 const m=new THREE.Mesh(new THREE.SphereGeometry(r,10,8),new THREE.MeshBasicMaterial({color:side==='left'?0x00e8ff:0xffbd4a,depthTest:false}));
 m.renderOrder=18;scene.add(m);projectedWitnesses[side][kind]=m;
}''')
one('if(terrainMesh){scene.remove(terrainMesh);scene.remove(terrainWire);\n  terrainMesh.geometry.dispose();terrainMesh.material.dispose();terrainWire.material.dispose();\n  terrainMesh=null;terrainWire=null;}',
'''if(terrainMesh){scene.remove(terrainMesh);scene.remove(terrainWire);
  terrainMesh.geometry.dispose();terrainMesh.material.dispose();terrainWire.material.dispose();
  terrainMesh=null;terrainWire=null;}
 if(terrainSlice){scene.remove(terrainSlice);for(const l of terrainSlice.children){l.geometry.dispose();l.material.dispose();}terrainSlice=null;}''')
one('const grid=terrainGrid(terrainMode,terrainStrength,centerZ,24,176),geo=new THREE.BufferGeometry();',
    'const grid=terrainGrid(terrainMode,terrainStrength,centerZ,profileMode()?12:24,profileMode()?400:176),geo=new THREE.BufferGeometry();')
one('scene.add(terrainMesh);scene.add(terrainWire);',
'''scene.add(terrainMesh);scene.add(terrainWire);
 terrainWire.visible=!profileMode(); // Do not obscure the profile with crisscross wireframe.
 if(profileMode()){
  terrainSlice=new THREE.Group();
  const profile=longitudinalProfile(terrainMode,terrainStrength,centerZ,400);
  for(const x of [-.81,.81]){
   const curve=new THREE.BufferGeometry().setFromPoints(profile.map(({z,y})=>V(x,y+.013,z)));
   const line=new THREE.Line(curve,new THREE.LineBasicMaterial({color:x<0?0xf6d383:0x729ca2,depthTest:false,transparent:true,opacity:x<0?.97:.62}));
   line.renderOrder=12;terrainSlice.add(line);
  }
  scene.add(terrainSlice);
 }''')
one('rebuildTerrain(0);', "rebuildTerrain(0);\nif(profileMode()){view='side';camera.position.fromArray(cameraOffsets.side);orbit.update();}")
one("$('terrainIntensityOut').textContent=Math.round(terrainStrength*100)+'%';",
    "$('terrainIntensityOut').textContent=Math.round(terrainStrength*100)+'%';$('terrainReadability').textContent=profileMode()?'PROFILE: identical height under both feet at equal forward Z':'LEGACY: height varies across width; select a Profile course for clear foot evaluation';")
one('const footPatches=[\'heel\',\'sole\',\'toe\'].map(k=>witnessWorld(c,k));',
'''const footPatches=witnessKinds.map(k=>witnessWorld(c,k));
 // Bright dots trace the same analytic contact surface sampled by the IK.
 // Terrain projections are diagnostic only, never anatomy or contact targets.
 for(let i=0;i<witnessKinds.length;i++){
  const p=footPatches[i],marker=projectedWitnesses[side][witnessKinds[i]];
  marker.position.set(p.x,terrainAt(p.x,p.z)+.013,p.z);
  marker.visible=$('showContacts').checked&&ready&&motionMode==='PHYSICAL_GROUND_PINNING';
 }''')
one("for(const p of Object.values(drawPins))p.visible=false;\n $('play').textContent='Pause';",
    "for(const p of Object.values(drawPins))p.visible=false;for(const side of ['left','right'])for(const p of Object.values(projectedWitnesses[side]))p.visible=false;\n $('play').textContent='Pause';")
one("$('showContacts').onchange=()=>{\n for(const side of ['left','right'])drawPins[side].visible=ready&&motionMode==='PHYSICAL_GROUND_PINNING'&&$('showContacts').checked;\n};",
    "$('showContacts').onchange=()=>{\n for(const side of ['left','right']){drawPins[side].visible=ready&&motionMode==='PHYSICAL_GROUND_PINNING'&&$('showContacts').checked;for(const p of Object.values(projectedWitnesses[side]))p.visible=drawPins[side].visible;}\n};")
one('const terrainIntrusion=Math.max(0,...footPatches.map(p=>terrainAt(p.x,p.z)-p.y));',
'''const terrainClearances=Object.fromEntries(witnessKinds.map((k,i)=>[k,footPatches[i].y-terrainAt(footPatches[i].x,footPatches[i].z)]));
 const terrainIntrusion=Math.max(0,...footPatches.map(p=>terrainAt(p.x,p.z)-p.y));''')
one('kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch,',
    'kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch,terrainClearances,')
one('Skinned support error ${maxDrift.toFixed(5)} u, TERRAIN penetration ${maxPenetration.toFixed(5)} u',
'''Skinned support error ${maxDrift.toFixed(5)} u, TERRAIN penetration ${maxPenetration.toFixed(5)} u
WIDTH-PARITY ${profileMode()?'SAME HEIGHT LEFT/RIGHT':'VARIABLE (legacy mode)'} · cyan/orange = terrain level at actual heel,sole,toe
HEEL/SOLE/TOE above ground L ${Object.values(feet.left.terrainClearances).map(x=>x.toFixed(3)).join('/')} · R ${Object.values(feet.right.terrainClearances).map(x=>x.toFixed(3)).join('/')}''')
one("terrainMode,terrainStrength,terrainSourceOfTruth:'terrain-core.mjs height(x,z) shared by mesh, touchdown, swing, body and audit',",
    "terrainMode,terrainStrength,terrainWidthInvariant:profileMode(),terrainProfileHeightSameAcrossWidth:profileMode(),terrainSourceOfTruth:'terrain-core.mjs height(x,z) shared by mesh, touchdown, swing, body and audit',")
one("status('PHYSICAL IK ON '+terrainMode.toUpperCase()+' TERRAIN · 32 real skinned startup steps · run contact audit to verify ground clearance');",
    "status('PHYSICAL IK ON '+terrainMode.toUpperCase()+' AT '+Math.round(terrainStrength*100)+'% · width-invariant profile='+profileMode()+' · run real contact audit');")
# The boot-screen build identity must never display a stale v0.1.14 version.
one("$('identity').textContent='v0.1.14 · ORIGINAL SKINNED 3D MODEL HASH '+SOURCE_SHA+' · SOURCE MATH AND CONTACT AUDIT PENDING';",
    "$('identity').textContent='v0.1.22 · ORIGINAL SKINNED 3D MODEL HASH '+SOURCE_SHA+' · STRESS PROFILE SOURCE AND CONTACT AUDIT PENDING';")
# This source code must NOT mutate anatomical step or foot heading definitions.
for protected in ["const pole=stableForwardPole(side,yaw);",'const chosen=chooseSourceKnee(', 'distalHeading(side,footFit,pelvisProfile)',"worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})"]:
 if protected not in s:raise RuntimeError('V022_ACCEPTED_GAIT_MISSING '+protected)
assert 'sourceKneePlane(' not in s
s=s.replace('v0.1.21','v0.1.22').replace('V0.1.21','V0.1.22')
v.write_text(s.rstrip()+'\n')
p=dest/'index.html';h=p.read_text()
h=h.replace('<option value="rough">Rough ground</option>',
'''<option value="rough">Legacy side-varying rough</option><option value="profile-ridges">Profile ridges (clear cross-width)</option><option value="profile-steps">Profile high steps (hard)</option><option value="profile-ramp">Profile steep ramp (hard)</option>''')
h=h.replace('max="1.25" step="0.05" value="0.65"','max="3" step="0.1" value="1.1"')
h=h.replace('<output id="terrainIntensityOut">65%</output>', '<output id="terrainIntensityOut">110%</output>')
h=h.replace('Surface change restarts the run to avoid teleporting planted feet. Green and orange markers show true world contact targets. Default: rough.',
'''Profile courses have identical ground height across the entire walking width. The copper side rails mark the true surface height. Cyan and amber dots mark height directly under each heel/sole/toe. Maximum stress = 300%. Terrain changes reset planted contacts; the original gait is unchanged.<span id="terrainReadability" role="status" aria-live="polite"></span>''')
h=h.replace('Show world contact anchors','Show anchors and heel/sole/toe ground markers')
h=h.replace('one character</span>','one character · stress profiles</span>')
h=h.replace('v0.1.21','v0.1.22').replace('V0.1.21','V0.1.22')
assert h.count('id="terrainReadability"')==1
assert h.count('<option value="profile-ridges">')==1
p.write_text(h.rstrip()+'\n')
p=dest/'review-server.py';t=p.read_text().replace('v0.1.21','v0.1.22').replace('V0.1.21','V0.1.22');p.write_text(t.rstrip()+'\n')
print('V022_PINNED_PROFILE_STRESS_PATCH_PASS: source knee/foot/flat gait untouched; stronger width-invariant contact surface')
V022_PATCH_SOURCE

cat > "$DEST_REL/contract.json" <<'V022_CONTRACT'
{
  "schema": "hareworks-v0.1.22-width-invariant-terrain-ik-stress-test",
  "repo": "Valar05/parametric-parambulator",
  "sourceCommit": "6b5843132ed6e896c7dd928b8a43fd5bf7805ad6",
  "sourceController": "tools/hareworks-forward-woman/v0.1.21/viewer.mjs",
  "sourceControllerBlob": "4b05c9af000e0c30919d4bb7fc47cb183fed425f",
  "sourceTerrainBlob": "d6c6c846579787ffc4f24c52047f5a0028b8a97a",
  "sourceFootGaitBlob": "ecc036c99f92dfa02b17a9457e76b0998a127c04",
  "sourceKneeGovernorBlob": "eefc2b0b867778bb384eafe95af4e63d7caa2f6b",
  "sourceFootHeadingBlob": "39108d51fcd6f1d0133e8ebdb79c665350bc1a4b",
  "canonicalModelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "rulesAGENTSBlob": "547c2af52303f4efb718bbf8f82a698110c7bfca",
  "rulesCampaignEtiquetteDoc": "1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI",
  "executionLane": "Android Termux Git only",
  "mutablePaths": [
    "tools/hareworks-forward-woman/v0.1.22/"
  ],
  "ownerVisualVerdict": "v0.1.21 roughly acceptable, but too little terrain stress and x-varying rough heights obscure profile foot contact",
  "protectedMath": "exact v0.1.21 foot-gait, original source knee-governor, v0.1.18 foot heading, root, camera orbit; terrain-only new version",
  "profileModes": [
    "profile-ridges",
    "profile-steps",
    "profile-ramp"
  ],
  "stressIntensityRange": [
    0,
    3
  ],
  "worldHeightProperty": "for profile modes, terrainHeight(x,z) is EXACTLY independent of x, identical for both feet at same z",
  "diagnostics": [
    "analytic side profile lines",
    "skinned heel/sole/toe terrain projection dots",
    "real 120Hz foot-contact audit"
  ],
  "stressAuditResult": "actual browser audit pending, no synthetic PASS claim",
  "modelModified": false,
  "ownerVisualAcceptance": false
}
V022_CONTRACT

cat > "$DEST_REL/README.md" <<'V022_README'
# Hareworks v0.1.22: severe but readable LONGITUDINAL terrain IK stress

The owner judged v0.1.21 insufficiently challenging even at its former maximum and difficult to judge from a profile because its roughness varied across X. This version changes the test ground and diagnostics only, not the current walking choreography.

**Default = profile ridges at 110%; slider extends 0 to 300%.** Profile ridges, high steps and steep ramp have height `Y = h(Z)` exactly independent of X. The two feet see the same terrain height when occupying the same forward Z, making side-on ground clearance unambiguous. Each step rises about 0.615 units at 300%, with a two-step crest of about 1.23 units; ramp grade up to 0.48; ridges visibly exceed the prior 0.06-unit roughness. The physically stressful maximum can exceed reach/ground-clearance feasibility and should produce an honest WARN rather than a fabricated contact PASS.

The visible mesh is a narrower width-invariant extrusion with no confusing transverse grid wireframe, and it displays a copper profile outline derived from exactly the same analytic height function used by ground anchors and pelvis/foot contact. Bright cyan and amber ground markers project the actual skinned heel, sole and toe onto the terrain. The underlying physical IK uses unchanged `terrainAt` for stance anchor Y and target swing height; a bounded vertical-lift rate of 1.5 terrain units/sec allows the pelvis to react to steeper ramps and steps without teleporting. A new mode reloads the viewer to protect planted-anchor identity. The old flat, uphill, downhill, rough and cross-slope modes remain available as legacy comparisons.

**Preserve** v0.1.21 source original knee and ankle trajectories, fixed anterior knee poles, v0.1.18 paired foot headings, non-clip physical IK, root Z travel, 120Hz audit and orbit camera. No controller or canonical GLB edits. The world stress can reveal actual IK failure; visible-only elevation tests cannot establish success. Source simulation checks and Termux real GLB structure checks are separate from actual live browser skinned foot tests and owner acceptance.

Published solely by one immutable v0.1.22 Termux Git script into the existing Documents checkout. Existing version directories and model remain unchanged. Require exact upstream commit/Blob/model hashes, exclusive destination, tightly scoped Git state, SHA-checked script, remote commit and remote readback, cache-busted viewer and persistent receipts.
V022_README
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
cp "$CHECKOUT/tools/hareworks-forward-woman/v0.1.20/foot-gait.mjs" "$CHECKOUT/tools/hareworks-forward-woman/v0.1.20/root-motion.mjs" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.20/"
node "$DEST_REL/flat-parity-test.mjs"
node "$DEST_REL/terrain-core-test.mjs"
# Hold the prior deterministic surface as an immutable reference; stronger profiles must be measurable.
[ "$(git -C "$CHECKOUT" hash-object "$CHECKOUT/$SOURCE_REL/terrain-core.mjs")" = d6c6c846579787ffc4f24c52047f5a0028b8a97a ] || { echo 'BLOCKED_SOURCE_TERRAIN_NOT_VERIFIED' >&2;exit 77; }
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
git commit -m 'Hareworks v0.1.22 strengthen width-invariant terrain and show true foot heights'
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
 'campaign':campaign,'status':'PERSISTENT_CHECKOUT_AND_V022_WIDTH_INVARIANT_STRESS_VIEWER_PUBLISHED_BROWSER_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sparseCheckout':False,
 'androidSharedStorageGitTrust':'exact-canonical-project-only, global safe.directory',
 'lfsStatusGuard':'Git LFS filters configured locally; only exactly SHA-verified tracked Hareworks binary is admissible as unstaged model materialization',
 'lfsStatusGuardDoesNotHideChanges':True,
 'previousIncompleteGitInitRecovered':recovered=='1',
 'protectedGait':'v0.1.21 foot-gait, original knee-governor, foot heading and source actor unchanged; only new terrain profile and diagnostic visuals in v0.1.22',
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
