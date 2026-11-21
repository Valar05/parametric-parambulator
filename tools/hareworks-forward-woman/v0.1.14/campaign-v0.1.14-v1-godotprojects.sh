#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_ACCEPTED_V019_INVERSE_SUPPORT_v0.1.14_DOCUMENTS
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_SHOE_WITNESS_RECOVERY_v0.1.14_DOCUMENTS'
VERSION='v0.1.14'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='480780cf2c6c78227d8c27e227a31204e303666d'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-shoe-witness-v0.1.14-v1-documents"
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
  grep -q 'hareworks-woman-accepted-v019-shoe-recovery-v0.1.14' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
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
[ -f tools/hareworks-forward-woman/v0.1.13/viewer.mjs ] || { echo 'BLOCKED_MISSING_SOURCE_GAIT_BASELINE' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.13/viewer.mjs)" = d170d71c630b486daf5c5a94629a9c7674430fbb ] || { echo 'BLOCKED_REJECTED_V013_SOURCE_CHANGED' >&2;exit 74; }
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
 TEMP_MODEL="$MODEL.r14-verified-${ENTRY_SHA:0:12}.tmp"
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
STAGE='generate-v014-shoe-witness-recovery'
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.13" "$DEST_REL"
# Only remove the previous campaign entrypoint in the fresh, unpublished COPY.
for old_launcher in "$DEST_REL"/campaign-*.sh;do [ -f "$old_launcher" ] && rm -- "$old_launcher" || :;done
cp "$ENTRY" "$DEST_REL/campaign-v0.1.14-v1-godotprojects.sh"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.2" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3"
cat > "$DEST_REL/shoe-witness.mjs" <<'V014_SHOE_MODULE'
/* v0.1.14: true skinned footwear witness selection.
 * Partition the ACTUAL whole foot surface, not an already-reduced 20-vertex sole patch.
 * Geometry and provenance reports remain owner-review evidence, never automatic acceptance.
 */
const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
const avg=(p,k)=>p.reduce((s,v)=>s+v.xyz[k],0)/p.length;
function eigenAxis(points){
 const mx=avg(points,0),mz=avg(points,2);
 let xx=0,zz=0,xz=0;
 for(const p of points){const x=p.xyz[0]-mx,z=p.xyz[2]-mz;xx+=x*x;zz+=z*z;xz+=x*z;}
 const theta=.5*Math.atan2(2*xz,xx-zz);
 return [Math.cos(theta),Math.sin(theta)];
}
function chooseBin(points,k){
 // A contact witness must represent low, physically skinned surface geometry.
 const low=points.map(p=>p.xyz[1]).sort((a,b)=>a-b);
 const cutoff=low[Math.max(0,Math.min(low.length-1,Math.floor(low.length*.45)))];
 const subset=points.filter(p=>p.xyz[1]<=cutoff+0.012);
 subset.sort((a,b)=>a.xyz[1]-b.xyz[1]||a.mi-b.mi||a.j-b.j);
 return subset.slice(0,Math.min(k,subset.length));
}
export function selectShoeWitnesses(input,rawToeDirection){
 if(!Array.isArray(input)||input.length<24)throw Error('INSUFFICIENT_SKINNED_FOOT_VERTICES_'+input?.length);
 const ids=new Set(),valid=[];
 for(const p of input){
  if(!p||!Array.isArray(p.xyz)||p.xyz.length!==3||!p.xyz.every(Number.isFinite)||!Number.isInteger(p.mi)||!Number.isInteger(p.j))continue;
  const key=p.mi+':'+p.j;if(ids.has(key))continue;ids.add(key);valid.push(p);
 }
 if(valid.length<24)throw Error('INSUFFICIENT_UNIQUE_FOOT_VERTICES_'+valid.length);
 // Restrict the PCA to the lower visible shoe surface; tall shin polygons must not drive direction.
 const bottom=Math.min(...valid.map(p=>p.xyz[1]));
 let low=valid.filter(p=>p.xyz[1]<=bottom+.13);
 if(low.length<24)low=valid.slice();
 let axis=eigenAxis(low);
 const toe=[rawToeDirection?.[0]||0,rawToeDirection?.[2]||0],td=Math.hypot(...toe);
 if(td>.012&&axis[0]*toe[0]+axis[1]*toe[1]<0)axis=axis.map(x=>-x);
 else if(td<=.012&&axis[1]<0)axis=axis.map(x=>-x);
 const points=low.map(p=>({...p,projection:p.xyz[0]*axis[0]+p.xyz[2]*axis[1]}));
 points.sort((a,b)=>a.projection-b.projection);
 const length=points.at(-1).projection-points[0].projection;
 if(length<.065)throw Error('SKINNED_SHOE_LONGITUDINAL_EXTENT_INSUFFICIENT_'+length.toFixed(5));
 // Use non-overlapping spatial bands, THEN choose lower skinned vertices WITHIN each band.
 const n=points.length;
 const lo=points.slice(0,Math.floor(n*.32)),mid=points.slice(Math.floor(n*.38),Math.ceil(n*.62)),hi=points.slice(Math.ceil(n*.68));
 const picked=[chooseBin(lo,14),chooseBin(mid,14),chooseBin(hi,14)];
 if(picked.some(p=>p.length<4))throw Error('SKINNED_SHOE_SURFACE_BAND_MISSING');
 const means=picked.map(group=>group.reduce((s,v)=>s+v.projection,0)/group.length);
 if(means[1]-means[0]<.018||means[2]-means[1]<.018)throw Error('SKINNED_SHOE_PATCH_CENTROIDS_NOT_DISTINCT_'+means.join(','));
 const patch=ps=>({indexes:ps.map(p=>({mi:p.mi,j:p.j})),count:ps.length});
 return {heel:patch(picked[0]),sole:patch(picked[1]),toe:patch(picked[2]),
   evidence:{wholeFootCandidates:valid.length,lowSurfaceCandidates:low.length,shoeLongitudinalExtent:length,
     heelSoleToeLongitudinalCentroids:means,axisXZ:axis,method:'PCA of real skinned shoe vertices in XZ; lowest vertices of independent longitudinal thirds'}};
}
V014_SHOE_MODULE
cat > "$DEST_REL/shoe-witness-test.mjs" <<'V014_SHOE_TEST'
import assert from 'node:assert/strict';
import {selectShoeWitnesses} from './shoe-witness.mjs';
const pts=[];let index=0;
// Synthetic shoe is long in Z, wide in X, vertical range taller than its sole;
// the ankle->toe direction is mostly DOWN, reproducing the previous axis failure.
for(let i=0;i<24;i++)for(let j=0;j<12;j++){
 const x=.07+(j-5.5)*.005,z=-.12+i*.011;
 const y=(j<6?.004:.012)+(.002*i%3);
 pts.push({mi:0,j:index++,xyz:[x,y,z]});
}
const result=selectShoeWitnesses(pts,[.018,-.10,.034]);
assert.ok(result.evidence.shoeLongitudinalExtent>.20);
assert.ok(result.heel.count>=4&&result.sole.count>=4&&result.toe.count>=4);
assert.ok(result.evidence.heelSoleToeLongitudinalCentroids[0]<result.evidence.heelSoleToeLongitudinalCentroids[1]);
assert.ok(result.evidence.heelSoleToeLongitudinalCentroids[1]<result.evidence.heelSoleToeLongitudinalCentroids[2]);
const groups=[result.heel,result.sole,result.toe].map(g=>new Set(g.indexes.map(x=>x.mi+':'+x.j)));
assert.equal(groups[0].size,result.heel.count);
for(let a=0;a<3;a++)for(let b=a+1;b<3;b++)assert.ok([...groups[a]].every(x=>!groups[b].has(x)));
// Too narrow is a real failure, not a guessed witness.
assert.throws(()=>selectShoeWitnesses(pts.map(p=>({...p,xyz:[p.xyz[0],p.xyz[1],p.xyz[2]*.09]})),[0,-.1,.03]),/INSUFFICIENT/);
// A 20-vertex nearest low-point set must NEVER qualify as a whole shoe.
assert.throws(()=>selectShoeWitnesses(pts.slice(0,20),[0,-.1,.03]),/INSUFFICIENT/);
// Vertices can be permuted and the three bands remain distinct.
let reversed=selectShoeWitnesses(pts.slice().reverse(),[.018,-.10,.034]);
assert.equal(reversed.heel.count>0,true);
console.log('SKINNED_SHOE_WITNESS_GEOMETRY_TEST_PASS length='+result.evidence.shoeLongitudinalExtent.toFixed(4));
V014_SHOE_TEST
cat > "$DEST_REL/patch.py" <<'V014_PATCH_SCRIPT'
#!/usr/bin/env python3
"""Strict source-blob-pinned recovery of v0.1.13, into immutable v0.1.14 only."""
from pathlib import Path
import json,sys
root=Path(sys.argv[1]).resolve()
target=root/'tools/hareworks-forward-woman/v0.1.14'
p=target/'viewer.mjs'
s=p.read_text()
def once(old,new):
 global s
 if s.count(old)!=1:raise RuntimeError('PATCH_ANCHOR_COUNT_'+str(s.count(old))+' '+old[:90])
 s=s.replace(old,new,1)
def region(first,end,replacement):
 global s
 if s.count(first)!=1 or s.count(end)!=1:raise RuntimeError('PATCH_REGION_NOT_UNIQUE '+first[:40])
 a=s.index(first);b=s.index(end,a)
 s=s[:a]+replacement+s[b:]
# Preserve every accepted gait curve, the phase-integrated inverse root, original camera orbit and contact core.
once("import {OrbitControls} from 'three/addons/controls/OrbitControls.js';", "import {OrbitControls} from 'three/addons/controls/OrbitControls.js';\nimport {selectShoeWitnesses} from './shoe-witness.mjs';")
region('function splitFootPatches(meshes,foot,toe,all){','function measuredFootQ(s){', """function splitFootPatches(meshes,foot,toe,all){
 // The v0.1.13 bug partitioned only 20 points from the ALREADY-selected sole.
 // Select the actual whole shoe through the skinned vertex weights and spatial bounds.
 const ankle=wpos(foot),toePos=wpos(toe),boneNames=new Set([foot.name,toe.name]);
 const profiles=[];
 for(let mi=0;mi<meshes.length;mi++){
  const m=meshes[mi],position=m.geometry.getAttribute('position'),skinIdx=m.geometry.getAttribute('skinIndex'),skinW=m.geometry.getAttribute('skinWeight');
  if(!position)continue;
  const bones=m.skeleton?.bones||[],footBones=new Set(bones.map((b,i)=>boneNames.has(b.name)?i:-1).filter(i=>i>=0));
  const step=Math.max(1,Math.floor(position.count/40000));
  for(let j=0;j<position.count;j+=step){
   const p=m.getVertexPosition(j,V());m.localToWorld(p);
   const r=Math.min(p.distanceTo(ankle),p.distanceTo(toePos));
   if(r>.42||p.y>ankle.y+.14||Math.abs(p.x-ankle.x)>.24)continue;
   let influence=0;
   if(skinIdx&&skinW&&footBones.size){
    for(let k=0;k<4;k++)if(footBones.has(skinIdx.getComponent(j,k)))influence+=skinW.getComponent(j,k);
   }
   profiles.push({mi,j,xyz:p.toArray(),influence,radialDistance:r});
  }
 }
 let last='',chosen=null;
 // Prefer genuine foot/toe SKIN influence; adapt the selection without inventing geometry.
 for(const gate of [.20,.10,.04,0]){
  const a=profiles.filter(p=>p.influence>=gate&&(gate>0||p.radialDistance<.33));
  if(a.length<24){last='INSUFFICIENT_FOOT_INFLUENCE gate='+gate+' count='+a.length;continue;}
  try{chosen=selectShoeWitnesses(a,toePos.clone().sub(ankle).toArray());
   chosen.evidence.weightThreshold=gate;
   chosen.evidence.sampledCandidateVertices=profiles.length;
   break;
  }catch(e){last=e.message;}
 }
 if(!chosen)throw Error('REAL_SHOE_GEOMETRY_CANNOT_SPLIT_'+foot.name+' '+last);
 console.info('REAL_SHOE_WITNESSES '+foot.name,chosen.evidence);
 return chosen;
}
""")
# Do not leave users with a blank screen if an unrelated calibration gate trips.
once("actor.updateMatrixWorld(true);rest=captureSeed();", "actor.updateMatrixWorld(true);rest=captureSeed();\n scene.add(actor);actor.updateMatrixWorld(true); // verified 3D model remains visible even if calibration later fails\n $('identity').textContent='v0.1.14 · ORIGINAL SKINNED 3D MODEL HASH '+SOURCE_SHA+' · SOURCE MATH AND CONTACT AUDIT PENDING';")
once("}catch(e){status('REAL_MODEL_CALIBRATION_BLOCKED '+e.message);console.error(e)}", "}catch(e){playing=false;ready=false;if(actor&&!actor.parent){scene.add(actor);actor.updateMatrixWorld(true);}\n status('REAL_MODEL_CALIBRATION_BLOCKED '+e.message+' · ORIGINAL RIG VISIBLE (STATIC DIAGNOSTIC; NOT A WALK)');console.error(e)}")
once("/* v0.1.13. ONE moving Walking_Woman.","/* v0.1.14. ONE moving Walking_Woman.")
once("v0.1.13 ACCEPTED V019 INVERSE SUPPORT ROOT","v0.1.14 ACCEPTED V019 INVERSE SUPPORT ROOT + REAL SHOE WITNESSES")
once("a.download='hareworks-woman-accepted-v019-world-pin-v0.1.13.json'", "a.download='hareworks-woman-accepted-v019-world-pin-v0.1.14.json'")
once("schema:'hareworks-woman-accepted-v019-world-pin-v0.1.13'", "schema:'hareworks-woman-accepted-v019-world-pin-v0.1.14'")
p.write_text(s)
# Retain original viewer interface, add identity and calibration semantics, distinct cache key.
html=target/'index.html';h=html.read_text().replace('v0.1.13','v0.1.14')
h=h.replace('src="./viewer.mjs?build=v0.1.14-inverse-root"','src="./viewer.mjs?build=v0.1.14-geometry-fix"')
h=h.replace('src="./viewer.mjs?build=v0.1.14"','src="./viewer.mjs?build=v0.1.14-geometry-fix"')
h=h.replace('One source-measured','One source-measured')
html.write_text(h)
# Audits are explicitly versioned; browser evidence never impersonates user visual acceptance.
rp=target/'review-server.py';r=rp.read_text().replace('v0.1.13','v0.1.14');rp.write_text(r)
# Reuse v0.1.13's original mathematical modules and tests unchanged (only local schema version).
rm=target/'root-motion.mjs';rm.write_text(rm.read_text().replace("root-v0.1.13","root-v0.1.14"))
# Update the immutable top-level contract for the new scoped publication.
contract=target/'contract.json';j=json.loads(contract.read_text());j['schema']='hareworks-woman-accepted-v019-shoe-recovery-v0.1.14';j['parent']='480780cf2c6c78227d8c27e227a31204e303666d';j['mutablePaths']=['tools/hareworks-forward-woman/v0.1.14/'];j['witnessMethod']='whole skinned shoe vertices, skin-weight preference, horizontal PCA, three distinct low-surface longitudinal bands';j['calibrationErrorBehavior']='source model remains visible but static, audit not passed';j['ownerVisualAcceptance']=False
contract.write_text(json.dumps(j,indent=2)+'\n')
readme=target/'README.md';readme.write_text("""# Hareworks v0.1.14: restore visible model and fix shoe witnesses

Published v0.1.13 fails early with `SKINNED_HEEL_TOE_SEPARATION_INSUFFICIENT_mixamorigLeftFoot` because it tries to divide twenty already-selected lowest sole points. This is a classification defect, not evidence that the model GLB is missing. The v0.1.13 viewer deferred adding the actor to the scene until all calibration gates passed, creating a blank view.

v0.1.14 preserves the source-derived accepted v0.1.9 gait, inverse stance-driven world-root, true IK solver, phase-varying advance, actor travel, and touch/mouse camera orbit from v0.1.13. Only the shoe witness selection and empty-screen behavior change. It classifies full skinned shoe vertices by horizontal principal axis and low-surface longitudinal bands, preferring actual foot/toe skin weights. All three patches must have unique indices and spatially separated centroids. A calibration failure now leaves the correct hash-verified 3D model visible in a STATIC, explicitly failed diagnostic state; it does not claim the gait works.

Model SHA: `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`. Target only: `Valar05/parametric-parambulator`, persistent checkout in Android `Documents/GodotProjects/parametric-parambulator`. Immutable parent: `480780cf2c6c78227d8c27e227a31204e303666d`. No GLB duplication, no unrelated LFS fetch, no temporary clones, no old-version mutations. Numeric witness tests are synthetic. Actual skinned moving contact physics, compatibility of the vertex groups and visual likeness remain browser/owner acceptance gates; they are not proven by static tests.
""")
print('PATCH_V014_GEOMETRY_VISIBILITY_COMPLETE')
V014_PATCH_SCRIPT
STAGE='patch-and-test-v014-witness-fix'
python3 "$DEST_REL/patch.py" "$BUILDROOT"
python3 - "$DEST_REL/patch.py" "$DEST_REL/review-server.py" <<'V014_PARSE'
import pathlib,sys
for path in sys.argv[1:]:compile(pathlib.Path(path).read_text(),path,'exec')
print('PYTHON_PARSE_PASS')
V014_PARSE
for f in root-motion.mjs foot-gait.mjs root-model-test.mjs contact-test.mjs viewer.mjs shoe-witness.mjs shoe-witness-test.mjs;do
 node --check "$DEST_REL/$f" || { echo "BLOCKED_JS_PARSE=$f" >&2;exit 77; }
done
node "$DEST_REL/shoe-witness-test.mjs"
node "$DEST_REL/contact-test.mjs"
node "$DEST_REL/root-model-test.mjs"
node "$DEST_REL/contact-core-test.mjs"
node "$DEST_REL/geometry-test.mjs"
# Source binary is SHA-verified at checkout preflight. Require a real glTF JSON chunk, not a pointer.
python3 - "$CHECKOUT/$MODEL" "$MODEL_SHA" <<'V014_GLB_PREFLIGHT'
import hashlib,json,pathlib,struct,sys
b=pathlib.Path(sys.argv[1]).read_bytes()
if hashlib.sha256(b).hexdigest()!=sys.argv[2]:raise SystemExit('BLOCKED_GLB_SHA')
magic,version,length=struct.unpack_from('<4sII',b,0)
if magic!=b'glTF' or version!=2 or length!=len(b):raise SystemExit('BLOCKED_GLB_HEADER')
length,typ=struct.unpack_from('<II',b,12)
if typ!=0x4e4f534a:raise SystemExit('BLOCKED_GLB_JSON')
j=json.loads(b[20:20+length]);clips=[a.get('name') for a in j.get('animations',[])]
if len(clips)!=9 or 'Walking_Woman' not in clips or not j.get('meshes') or not j.get('skins'):raise SystemExit('BLOCKED_GLB_CONTENT')
print('ORIGINAL_HASH_VERIFIED_SKINNED_MODEL=PASS, BROWSER_SKINNING_NOT_YET_AUDITED')
V014_GLB_PREFLIGHT
python3 - "$DEST_REL/viewer.mjs" "$DEST_REL/index.html" "$DEST_REL/shoe-witness.mjs" <<'V014_PRESERVE'
import pathlib,sys
viewer,html,shoe=[pathlib.Path(s).read_text() for s in sys.argv[1:]]
need=['new OrbitControls(camera,renderer.domElement)','orbit.target.add(delta)','orbit.update()',
 'rootAt(rootCurve,totalPhase)','acceptedAnkle=sourceHip.clone()','new SourceFootContact',
 'sourceHip','scene.add(actor);actor.updateMatrixWorld(true); // verified 3D model remains visible',
 'REAL_MODEL_CALIBRATION_BLOCKED', 'selectShoeWitnesses(a,toePos.clone()', 'maxTrailingExtensionDeficit']
for n in need:
 if n not in viewer:raise SystemExit('BLOCKED_FEATURE_REGRESSION:'+n)
if 'touch-action:none' not in html or 'resetCamera' not in html:raise SystemExit('BLOCKED_TOUCH_CAMERA_REGRESSION')
if 'eigenAxis' not in shoe or 'chooseBin' not in shoe:raise SystemExit('BLOCKED_SHOE_GEOMETRY_REGRESSION')
if 'new THREE.AnimationMixer(actor)' in viewer:raise SystemExit('BLOCKED_VISIBLE_ACTOR_SOURCE_CLIP_PLAYBACK')
print('REGRESSION_LOCKS_V019_GAIT_ORBIT_WORLD_IK_AND_VISIBLE_MODEL_PASS')
V014_PRESERVE
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
git commit -m 'Hareworks v0.1.14 restore skinned model display and separate real shoe contact witnesses'
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
 'campaign':campaign,'status':'PERSISTENT_CHECKOUT_AND_V019_INVERSE_ROOT_PUBLISHED_REAL_BROWSER_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sparseCheckout':False,
 'androidSharedStorageGitTrust':'exact-canonical-project-only, global safe.directory',
 'lfsStatusGuard':'Git LFS filters configured locally; only exactly SHA-verified tracked Hareworks binary is admissible as unstaged model materialization',
 'lfsStatusGuardDoesNotHideChanges':True,
 'previousIncompleteGitInitRecovered':recovered=='1',
 'acceptedV019Math':'unchanged source-ankle root inversion, full two-foot cycle',
 'shoeWitnesses':'whole skinned foot low-surface longitudinal PCA bands, real runtime audit pending',
 'calibrationFailureBehavior':'3d rig remains visible static and explicitly unapproved',
 'camera':'orbit and zoom with world-target follow',
 'unrelatedReplLfsFetched':False,'hareworksCopyPolicy':'exactly one verified worktree model, reusable private LFS cache',
 'rulesReadInAuthoringTurn':{'AGENTSBlob':agents,'CampaignEtiquetteDocument':etiquette,'TopDownEtiquetteDocument':topdown},
 'viewerUrl':url,'viewerPid':int(pid),'viewerPort':int(port),'viewerGaitSha256':viewer_hash,
 'alreadyPublishedRerun':reused=='1','browserRealSkinnedFootAudit':'PENDING',
 'actualSkinned3dPhysicsTestedInTermux':False,
 'contactGate':'PENDING_BROWSER_AUDIT','gaitResemblanceGate':'PENDING_OWNER_VISUAL_ACCEPTANCE',
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
echo 'TRAILING_EXTENSION=NUMERIC_GATE_INCLUDED__OWNER_REVIEW_PENDING'
echo 'CONTACT_GATE=PENDING_REAL_BROWSER_AUDIT'
echo 'GAIT_RESEMBLANCE_GATE=PENDING_OWNER_VISUAL_ACCEPTANCE'
if command -v termux-open-url >/dev/null 2>&1;then
 termux-open-url "$URL" || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
elif command -v am >/dev/null 2>&1;then
 am start -a android.intent.action.VIEW -d "$URL" >/dev/null 2>&1 || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
fi
