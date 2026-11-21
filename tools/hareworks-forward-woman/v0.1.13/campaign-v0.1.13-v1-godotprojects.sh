#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_ACCEPTED_V019_INVERSE_SUPPORT_v0.1.13_DOCUMENTS
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_ACCEPTED_V019_INVERSE_SUPPORT_v0.1.13_DOCUMENTS'
VERSION='v0.1.13'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='fa927379890b111220b368595c6e2f27725a9d1a'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-source-v0.1.13-v1-documents"
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
  grep -q 'hareworks-woman-accepted-v019-world-pinning-v0.1.13' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
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
[ -f tools/hareworks-forward-woman/v0.1.11/viewer.mjs ] || { echo 'BLOCKED_MISSING_SOURCE_GAIT_BASELINE' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.12/viewer.mjs)" = b7e3f63128bf4672c4aaf610408dbdc48f7be096 ] || { echo 'BLOCKED_REJECTED_V012_SOURCE_CHANGED' >&2;exit 74; }
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
 TEMP_MODEL="$MODEL.r4-verified-${ENTRY_SHA:0:12}.tmp"
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
STAGE='generate-v019-inverse-support-gait'
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.12" "$DEST_REL"
# Discard stale v0.1.12 launcher from the TEMPORARY new-version copy only.
for old_launcher in "$DEST_REL"/campaign-*.sh;do [ -f "$old_launcher" ] && rm -- "$old_launcher" || :;done
cp "$ENTRY" "$DEST_REL/campaign-v0.1.13-v1-godotprojects.sh"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.2" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3"
cat > "$DEST_REL/root-motion.mjs" <<'__HAREWORKS_V013_FILE_0__'
/* Hareworks 0.1.13: reconstruct world-root travel by inverting the accepted ankle trajectory.
   Phase is a complete LEFT+RIGHT gait cycle, not the movement of one ankle.
   No source animation tracks run on the visible actor. */
export const phase01=q=>((q%1)+1)%1;
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export const smooth01=x=>{const t=clamp(x,0,1);return t*t*(3-2*t)};
export const gap=(q,start)=>phase01(q-start);
export const inside=(q,g)=>gap(q,g.start)<g.duty;
const v3=v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite);
const st=(a,i)=>a[(i%a.length+a.length)%a.length];
export function derivative(samples,i,kind='ankle',component=2){
 const n=samples.length;
 return (st(samples,i+1)[kind][component]-st(samples,i-1)[kind][component])*n/2;
}
function contiguous(mask){
 const n=mask.length,out=[];
 for(let i=0;i<n;i++){
  if(!mask[i]||mask[(i-1+n)%n])continue;
  let length=0;while(length<n&&mask[(i+length)%n])length++;
  out.push({start:i/n,duty:length/n,count:length});
 }
 return out;
}
export function inferVelocityContact(samples){
 if(!Array.isArray(samples)||samples.length<60||samples.some(s=>!v3(s.ankle)||!v3(s.heel)||!v3(s.sole)||!v3(s.toe)))throw Error('SOURCE_WITNESS_SCHEMA_INVALID');
 const n=samples.length,v=samples.map((_,i)=>derivative(samples,i));
 const low=Math.min(...v),cut=Math.min(-.25,low*.22),runs=contiguous(v.map(z=>z<cut));
 const ranges=runs.filter(g=>g.duty>=.47&&g.duty<=.70);
 if(!ranges.length)throw Error('SOURCE_CONTACT_VELOCITY_AMBIGUOUS '+JSON.stringify({minVelocity:low,threshold:cut,runs}));
 ranges.sort((a,b)=>b.duty-a.duty);
 const g=ranges[0];
 const floor=Math.min(...samples.flatMap(s=>[s.heel[1],s.toe[1]]));
 const supportHeights=[];const swingHeights=[];
 for(let i=0;i<n;i++){
  const h=Math.min(samples[i].heel[1],samples[i].toe[1])-floor;
  (inside(i/n,g)?supportHeights:swingHeights).push(h);
 }
 const mean=x=>x.reduce((a,b)=>a+b,0)/x.length;
 return {...g,method:'circular backward-ankle velocity, with independent heel/toe height diagnostics',
  thresholdVelocity:cut,sourceMinDerivative:low,meanContactHeight:mean(supportHeights),meanSwingHeight:mean(swingHeights),
  groundCandidate:floor,confidence:'kinematic window only; physical skinned witness audit required'};
}
export function buildRootCurve(feet,gaits){
 const n=feet.left.length;
 if(n<60||feet.right.length!==n)throw Error('ROOT_SAMPLE_COUNT_MISMATCH');
 const speeds=[];
 for(let i=0;i<=n;i++){
  const q=i/n,vs=['left','right'].map(side=>derivative(feet[side],i)),weights=['left','right'].map((side,j)=>{
   const g=gaits[side],u=gap(q,g.start),edge=Math.min(u,g.duty-u),window=inside(q,g)?(.12+.88*smooth01(edge/.035)):0;
   return window*smooth01((-vs[j]-.22)/.75);
  });
  if(weights[0]+weights[1]<1e-10){
   const candidate=vs[0]<vs[1]?0:1;
   weights[candidate]=1;
  }
  speeds.push(-(vs[0]*weights[0]+vs[1]*weights[1])/(weights[0]+weights[1]));
 }
 // Periodicity is required for a seamless cycle; the terminal derivative equals the first.
 speeds[n]=speeds[0];
 if(speeds.some(v=>!Number.isFinite(v)||v<-.1||v>5))throw Error('ROOT_VELOCITY_NONPHYSICAL');
 const positions=[0];for(let i=1;i<=n;i++)positions.push(positions[i-1]+(speeds[i-1]+speeds[i])/(2*n));
 const stride=positions[n];
 if(!(stride>.9&&stride<1.55))throw Error('ROOT_STRIDE_OUTSIDE_MEASURED_BIPED_RANGE '+stride);
 return {schema:'hareworks-accepted-v019-inverted-support-root-v0.1.13',n,speeds,positions,stride,
  method:'integral of negative fitted stance-ankle phase velocity; double support weighted by measured backward velocity',
  sourceFootSampleCount:n,ownerVisualAcceptance:false};
}
export function rootAt(curve,totalPhase){
 const cycles=Math.floor(totalPhase),q=phase01(totalPhase),x=q*curve.n,i=Math.floor(x),t=x-i;
 return cycles*curve.stride+curve.positions[i]*(1-t)+curve.positions[i+1]*t;
}
export function kneeFlexion(l1,l2,hip,ankle){
 if(!v3(hip)||!v3(ankle)||!(l1>0&&l2>0))throw Error('INVALID_LEG_GEOMETRY');
 const d=Math.hypot(...hip.map((x,i)=>x-ankle[i]));
 const c=clamp((l1*l1+l2*l2-d*d)/(2*l1*l2),-1,1);
 return (Math.PI-Math.acos(c))*180/Math.PI;
}
__HAREWORKS_V013_FILE_0__
cat > "$DEST_REL/foot-gait.mjs" <<'__HAREWORKS_V013_FILE_1__'
/* Hareworks 0.1.13: phase-independent, continuous contact target projection.
   Swing is the already-accepted source-fitted path with boundary corrections,
   not a new generic sine/smoothstep gait. */
import {phase01,clamp,gap,inside} from './root-motion.mjs';
const add=(a,b)=>a.map((x,i)=>x+b[i]),sub=(a,b)=>a.map((x,i)=>x-b[i]),scale=(a,n)=>a.map(x=>x*n);
const mix=(a,b,t)=>a.map((x,i)=>x+(b[i]-x)*t);
const finite=a=>Array.isArray(a)&&a.length===3&&a.every(Number.isFinite);
export function sourceAt(samples,q){
 const n=samples.length;if(n<60)throw Error('SOURCE_SAMPLES_INSUFFICIENT');
 const x=phase01(q)*n,i=Math.floor(x),t=x-i;
 const at=j=>samples[(j+n)%n],p0=at(i-1),p1=at(i),p2=at(i+1),p3=at(i+2);
 const sample=name=>p1[name].map((_,k)=>{
  const a=p0[name][k],b=p1[name][k],c=p2[name][k],d=p3[name][k];
  return .5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t);
 });
 return {phase:phase01(q),ankle:sample('ankle'),hip:sample('hip'),knee:sample('knee'),
  heel:sample('heel'),sole:sample('sole'),toe:sample('toe'),q0:p1.q,q1:p2.q,qt:t};
}
export function supportMode(s,ground){
 const heel=s.heel[1]-ground,toe=s.toe[1]-ground;
 const th=Math.max(.007,Math.min(.020,(Math.abs(heel)+Math.abs(toe))*.16));
 return heel-toe < -th?'heel':heel-toe>th?'toe':'sole';
}
export class SourceFootContact{
 constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0}){
  if(!gait||!Number.isFinite(gait.start)||!(gait.duty>.45&&gait.duty<.73))throw Error('INVALID_SOURCE_STANCE_WINDOW');
  this.samples=samples;this.gait=gait;this.sourceGround=sourceGround;this.groundY=groundY;
  this.readWitness=readWitness;this.rootAt=rootAt;
  this.state='initial';this.pivot='sole';this.anchor=null;this.transitions=0;this.pivotTransitions=0;
  this.swingCorrection=[0,0,0];this.badAnchorHeight=0;this.contactJump=0;
 }
 step({phase,worldZ,totalPhase}){
  const s=sourceAt(this.samples,phase),p=gap(phase,this.gait.start),planted=p<this.gait.duty;
  const next=planted?'stance':'swing';let pivot=planted?supportMode(s,this.sourceGround):'air';
  if(planted&&this.state==='stance'){
   const order={heel:0,sole:1,toe:2};
   if(order[pivot]<order[this.pivot])pivot=this.pivot;
  }
  const baseline=add(s.ankle,[0,-this.sourceGround,worldZ]);
  if(next!==this.state){
   if(planted){
    this.pivot=pivot;this.anchor=this.readWitness(pivot).slice();
    this.badAnchorHeight=Math.max(this.badAnchorHeight,Math.abs(this.anchor[1]-this.groundY));
   }else{
    // Preserve the exact final solved ankle on the first swing step.
    this.swingCorrection=sub(this.readWitness('ankle'),baseline);
   }
   this.state=next;this.transitions++;
  }else if(planted&&pivot!==this.pivot){
   // Physically transfer support without teleporting the ankle or projecting an anchor to Y=0.
   this.pivot=pivot;this.anchor=this.readWitness(pivot).slice();
   this.badAnchorHeight=Math.max(this.badAnchorHeight,Math.abs(this.anchor[1]-this.groundY));
   this.pivotTransitions++;
  }
  let target;
  if(planted){
   target=sub(this.anchor,sub(s[this.pivot],s.ankle));
  }else{
   const u=clamp((p-this.gait.duty)/(1-this.gait.duty),0,1),blend=(1-u)*(1-u)*(1+2*u);
   target=add(baseline,scale(this.swingCorrection,blend));
  }
  if(!finite(target))throw Error('NONFINITE_SOURCE_FOOT_TARGET');
  return {ankleTarget:target,planted,pivot,anchor:this.anchor?.slice()||null,source:s,
   witnessTarget:planted?this.anchor.slice():target.slice(),transitions:this.transitions,
   pivotTransitions:this.pivotTransitions,badAnchorHeight:this.badAnchorHeight};
 }
}
__HAREWORKS_V013_FILE_1__
cat > "$DEST_REL/root-model-test.mjs" <<'__HAREWORKS_V013_FILE_2__'
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {legAt,rotateY} from '../v0.1.3/foot-kernel.mjs';
import {independentPose} from '../v0.1.2/pose-kernel.mjs';
import {inferVelocityContact,buildRootCurve,rootAt,kneeFlexion} from './root-motion.mjs';

const witnesses=JSON.parse(fs.readFileSync(new URL('../v0.1.3/reference-leg-witnesses.json',import.meta.url),'utf8'));
const legs=JSON.parse(fs.readFileSync(new URL('../v0.1.3/foot-profile.json',import.meta.url),'utf8'));
const pelvis=JSON.parse(fs.readFileSync(new URL('../v0.1.2/motion-profile.json',import.meta.url),'utf8'));
const N=witnesses.samples.length;assert.equal(N,60);
const data={left:[],right:[]};const errors={left:[],right:[]};
for(let i=0;i<N;i++){
 const source=witnesses.samples[i],q=i/N,t=q*legs.duration;
 const yaw=independentPose(pelvis,t).pelvisYaw;
 for(const side of ['left','right']){
  const s=source.legs[side],local=legAt(legs,side,t).ankleLocal;
  const r=rotateY(local,yaw),ankle=s.hip.map((v,j)=>v+r[j]);
  const err=Math.hypot(...ankle.map((x,j)=>x-s.ankle[j]));errors[side].push(err);
  // A heel proxy is used ONLY in this source-witness math test. The actual
  // physical heel/sole/toe patches MUST be validated on the real skinned GLB.
  const heel=[ankle[0],s.toe[1]+.014,ankle[2]-.10];
  const toe=s.toe,sole=[(heel[0]+toe[0])/2,Math.min(heel[1],toe[1]),(heel[2]+toe[2])/2];
  data[side].push({phase:q,ankle,hip:s.hip,knee:s.knee,heel,sole,toe,q:[0,0,0,1]});
 }
}
const rms=x=>Math.sqrt(x.reduce((a,b)=>a+b*b,0)/x.length);
const errL=rms(errors.left),errR=rms(errors.right);
assert(errL<.003&&errR<.003,`v0.1.9 source-fit regression ${errL} ${errR}`);
const gaits=Object.fromEntries(['left','right'].map(side=>[side,inferVelocityContact(data[side])]));
for(const side of ['left','right'])assert(gaits[side].duty>.48&&gaits[side].duty<.70,JSON.stringify(gaits[side]));
const root=buildRootCurve(data,gaits);
assert(root.stride>1.06&&root.stride<1.46,'FULL_GAIT_CYCLE_DISTANCE_COUNTED_AS_HALF_CYCLE '+root.stride);
const values={};
for(const side of ['left','right']){
 const s=gaits[side],i0=s.start*N,steps=240;
 const at=q=>{const x=((q%1)+1)%1*N,i=Math.floor(x),t=x-i;const a=data[side][i].ankle,b=data[side][(i+1)%N].ankle;return a.map((v,j)=>v+(b[j]-v)*t)};
 const base=at(s.start)[2]+rootAt(root,s.start);
 let maxDrift=0,maxWrongDrift=0;
 for(let i=0;i<=steps;i++){
  const q=s.start+s.duty*i/steps;
  const exact=at(q)[2]+rootAt(root,q)-base;
  const wrong=at(q)[2]+.68*(q-s.start)-at(s.start)[2];
  maxDrift=Math.max(maxDrift,Math.abs(exact));maxWrongDrift=Math.max(maxWrongDrift,Math.abs(wrong));
 }
 assert(maxDrift<.11,`${side} FULL_CYCLE_WORLD_SUPPORT_DRIFT_TOO_LARGE ${maxDrift}`);
 assert(maxWrongDrift>maxDrift+.09,`${side} WRONG_HALF_STRIDE_NO_LONGER_REJECTED`);
 values[side]={originalFitRMSError:rms(errors[side]),stanceStart:s.start,duty:s.duty,
  maxWorldAnkleDriftBeforePin:maxDrift,rejectedHalfCycleMaxDrift:maxWrongDrift};
}
assert(Math.abs(rootAt(root,2)-2*root.stride)<1e-9,'ROOT_MULTI_CYCLE_SEAM');
assert(Math.abs(rootAt(root,1)-root.stride)<1e-9,'ROOT_FIRST_CYCLE_SEAM');
assert(kneeFlexion(.35,.39,[0,0,0],[0,-.7,0])<50);
const failing={left:data.left.map(x=>({...x,ankle:[1,2,3]})),right:data.right};
assert.throws(()=>inferVelocityContact(failing.left),/AMBIGUOUS/,'FAIL_INJECTED_CONTACT_FLAT');
assert.throws(()=>buildRootCurve({left:data.left,right:data.right.slice(1)},gaits),/ROOT_SAMPLE_COUNT_MISMATCH/,'FAIL_INJECTED_ROOT_SAMPLE_MISMATCH');
console.log('ACCEPTED_V019_MATH_GATE_PASS',JSON.stringify({modelSource:witnesses.sourceSha256,referenceFrames:N,rootFullCycle:root.stride,...values}));
console.log('REAL_SKINNED_GL_B_AND_BROWSER_AUDIT_NOT_YET_RUN');
__HAREWORKS_V013_FILE_2__
cat > "$DEST_REL/contact-test.mjs" <<'__HAREWORKS_V013_FILE_3__'
import assert from 'node:assert/strict';
import {sourceAt,supportMode,SourceFootContact} from './foot-gait.mjs';
import {phase01} from './root-motion.mjs';
const n=360;
const samples=Array.from({length:n},(_,i)=>{
 const q=i/n,angle=q*2*Math.PI,ankle=[.1,.23+.05*Math.max(0,Math.sin(angle)),.35*Math.cos(angle)];
 return {phase:q,hip:[.1,1,0],knee:[.1,.55,.05],ankle,
  heel:[.1,.04,ankle[2]-.12],sole:[.1,.02,ankle[2]],toe:[.1,.04,ankle[2]+.12],q:[0,0,0,1]};
});
assert(sourceAt(samples,.2).ankle.every(Number.isFinite));
assert.equal(phase01(-.1),.9);
assert.equal(supportMode({heel:[0,-.03,0],toe:[0,.03,0]},0),'heel');
let current={heel:[.1,0,.0],sole:[.1,0,.10],toe:[.1,0,.21],ankle:[.1,.23,.11]};
const c=new SourceFootContact({samples,gait:{start:0,duty:.60},sourceGround:.02,readWitness:k=>current[k],rootAt:q=>q*1.2});
let p=c.step({phase:.01,worldZ:.01,totalPhase:.01});assert(p.planted&&p.anchor);
const prev=p.anchor.slice();
p=c.step({phase:.03,worldZ:.04,totalPhase:.03});if(p.pivot==='heel')assert.deepEqual(p.anchor,prev);
const before=current.ankle.slice();
p=c.step({phase:.601,worldZ:.68,totalPhase:.601});assert(!p.planted&&p.ankleTarget.every(Number.isFinite));
// At liftoff, source swing inherits the previously solved foot without a reset.
assert(Math.hypot(...p.ankleTarget.map((v,i)=>v-before[i]))<.1);
assert.throws(()=>new SourceFootContact({samples,gait:{start:0,duty:.31},sourceGround:0,readWitness:k=>current[k]}),/INVALID_SOURCE_STANCE/);
console.log('CONTACT_TRANSITION_UNIT_PASS');
__HAREWORKS_V013_FILE_3__
cat > "$DEST_REL/patch.py" <<'__HAREWORKS_V013_FILE_4__'
#!/usr/bin/env python3
"""Patch immutable published v0.1.12 into a NEW v0.1.13 directory only.
All anchors are single-occurrence and version/hashes are externally pinned by Termux.
The original asset and approved v0.1.9 remain untouched.
"""
from pathlib import Path
import json
import sys

root=Path(sys.argv[1]).resolve()
target=root/'tools/hareworks-forward-woman/v0.1.13'
v=target/'viewer.mjs'
s=v.read_text()

def once(old,new):
    global s
    n=s.count(old)
    if n!=1:raise RuntimeError(f'PATCH_ANCHOR_MISMATCH count={n}, anchor={old[:110]!r}')
    s=s.replace(old,new,1)

def region(first,end,replacement):
    global s
    if s.count(first)!=1 or s.count(end)!=1:raise RuntimeError('PATCH_REGION_ANCHOR_MISMATCH '+first[:60])
    a=s.index(first);b=s.index(end,a)
    s=s[:a]+replacement+s[b:]

once('/* v0.1.11. ONE moving Walking_Woman.', '/* v0.1.13. ONE moving Walking_Woman.')
once("import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';", "import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';\nimport {OrbitControls} from 'three/addons/controls/OrbitControls.js';")
once("import {inferContacts,sourceAt,SourceFootContact} from './foot-gait.mjs';", "import {sourceAt,SourceFootContact} from './foot-gait.mjs';\nimport {inferVelocityContact,buildRootCurve,rootAt,kneeFlexion} from './root-motion.mjs';")
once("const camera=new THREE.OrthographicCamera(-3,3,2,-2,.01,300);const cameraOffsets={oblique:[-4.8,3.15,5.7],side:[-6.4,2.75,0],front:[0,2.9,7.0],top:[-.01,8,.01]};let view='oblique';", "const camera=new THREE.OrthographicCamera(-3,3,2,-2,.01,300);const cameraOffsets={oblique:[-4.8,3.15,5.7],side:[-6.4,2.75,0],front:[0,2.9,7.0],top:[-.01,8,.01]};let view='oblique';\nconst orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.dampingFactor=.10;orbit.enablePan=false;orbit.enableRotate=true;orbit.minZoom=.55;orbit.maxZoom=3.5;orbit.target.set(0,.90,0);camera.position.fromArray(cameraOffsets[view]);orbit.update();")
once("let ready=false,playing=true,speed=.52,stride=.66,phase=0,worldZ=0,frameTimer=performance.now(),accumulator=0,groundOffset=0,runFrames=0,report=null,lastStats=null;", "let ready=false,playing=true,speed=.52,stride=.66,phase=0,totalPhase=0,rootCurve=null,worldZ=0,frameTimer=performance.now(),accumulator=0,groundOffset=0,runFrames=0,report=null,lastStats=null;")
once("let maxDrift=0,maxIK=0,maxPenetration=0,unreachable=0,contactCount=0,swingCount=0,transitions=0,failedFrames=0;", "let maxDrift=0,maxIK=0,maxPenetration=0,unreachable=0,contactCount=0,swingCount=0,transitions=0,failedFrames=0,maxTrailingExtensionDeficit=0,maxAnchorHeight=0;")
once("return soleWorld(c.meshes,patch);\n}", "return soleWorld(c.meshes,patch);\n}\nfunction splitFootPatches(meshes,foot,toe,all){\n const axis=wpos(toe).sub(wpos(foot));if(axis.length()<.035)throw Error('FOOT_TOE_AXIS_DEGENERATE_'+foot.name);axis.normalize();\n const points=all.indexes.map(idx=>{const m=meshes[idx.mi],p=m.getVertexPosition(idx.j,V());m.localToWorld(p);return {idx,forward:p.dot(axis)};}).sort((a,b)=>a.forward-b.forward);\n if(points.length<12||points.at(-1).forward-points[0].forward<.025)throw Error('SKINNED_HEEL_TOE_SEPARATION_INSUFFICIENT_'+foot.name);\n const k=Math.max(4,Math.floor(points.length/4));const mid=points.slice(k,points.length-k);\n const patch=part=>({indexes:part.map(p=>p.idx),count:part.length});\n const groups={heel:patch(points.slice(0,k)),sole:patch(mid),toe:patch(points.slice(-k))};\n const identity=g=>g.indexes.map(x=>x.mi+':'+x.j).join('|');\n if(new Set(Object.values(groups).map(identity)).size!==3)throw Error('HEEL_SOLE_TOE_WITNESSES_IDENTICAL');\n return groups;\n}")
region('function adjustReach(targets){','function solveLeg(side,t){', '''function adjustReach(targets){
 // The source-v0.1.9 hip curve is a protected style constraint. Do NOT push pelvis
 // down by an arbitrary 0.14 units. The real IK gate records any genuine overreach.
 for(const side of ['left','right']){
  const c=legs[side],reach=wpos(c.up).distanceTo(V(...targets[side].ankleTarget))-(c.upperLength+c.lowerLength);
  if(reach>.003)unreachable++;
 }
}
''')
once("const ankle=wpos(c.foot),reference=V(...t.source.ankle).add(actor.position);", "const ankle=wpos(c.foot),reference=V(...t.source.ankle).add(actor.position);\n  if(t.planted){const g=sourceGaits[side],u=mod1(phase-g.start)/g.duty;\n   if(u>.70){const actualRelative=ankle.z-wpos(c.up).z,sourceRelative=t.source.ankle[2]-t.source.hip[2];\n    maxTrailingExtensionDeficit=Math.max(maxTrailingExtensionDeficit,Math.max(0,actualRelative-sourceRelative));}\n   maxAnchorHeight=Math.max(maxAnchorHeight,t.badAnchorHeight||0);}")
once("out[side]=worldContacts[side].step({phase,worldZ,stride});", "out[side]=worldContacts[side].step({phase,worldZ,totalPhase});")
once("phase=mod1(phase+cadence*dt);worldZ+=speed*dt;frameBody(phase);", "totalPhase+=cadence*dt;phase=mod1(totalPhase);worldZ=rootAt(rootCurve,totalPhase);frameBody(phase);")
region('const cameraTarget=V();','function renderMetrics(', '''const trackedFollow=V(0,.90,0);
function pinCamera(){
 if(!actor)return;
 const desired=actor.position.clone().add(V(0,.90,0)),delta=desired.sub(trackedFollow);
 orbit.target.add(delta);camera.position.add(delta);trackedFollow.add(delta);orbit.update();
}
function setCameraPreset(k){
 view=k;const world=actor?actor.position:V();trackedFollow.copy(world).add(V(0,.90,0));
 orbit.target.copy(trackedFollow);camera.position.fromArray(cameraOffsets[k]).add(world);
 camera.up.set(0,1,0);orbit.update();camera.updateProjectionMatrix();
}
''')
once("function clearStats(){maxDrift=0;maxIK=0;maxPenetration=0;unreachable=0;contactCount=0;swingCount=0;transitions=0;runFrames=0;lastStats=null;shapeSum=0;shapeCount=0;}", "function clearStats(){maxDrift=0;maxIK=0;maxPenetration=0;unreachable=0;contactCount=0;swingCount=0;transitions=0;runFrames=0;lastStats=null;shapeSum=0;shapeCount=0;maxTrailingExtensionDeficit=0;maxAnchorHeight=0;}")
once("phase=0;worldZ=0;clearStats();frameBody(0);", "phase=0;totalPhase=0;worldZ=0;clearStats();frameBody(0);")
once("sourceGround,readWitness:k=>witnessCache[side][k]});", "sourceGround,readWitness:k=>witnessCache[side][k],rootAt:q=>rootAt(rootCurve,q)});")
once("for(const k of Object.keys(cameraOffsets))$(k).onclick=()=>{view=k;pinCamera()};", "for(const k of Object.keys(cameraOffsets))$(k).onclick=()=>setCameraPreset(k);\n$('resetCamera').onclick=()=>setCameraPreset('oblique');")
once("a.download='hareworks-woman-source-world-ik-v0.1.12.json'", "a.download='hareworks-woman-accepted-v019-world-pin-v0.1.13.json'")
once("try{initRun();const n=Math.ceil((3/cadenceFor(speed,stride))*120);", "try{initRun();const cameraOffsetBefore=camera.position.clone().sub(actor.position);const n=Math.ceil((3/cadenceFor(speed,stride))*120);")
once("pinCamera();const cameraError=Math.abs((camera.position.z-actor.position.z)-cameraOffsets[view][2]);", "pinCamera();const cameraError=camera.position.clone().sub(actor.position).distanceTo(cameraOffsetBefore);")
once("&&worldZ>.9&&cameraError<1e-8&&unreachable===0;", "&&worldZ>2.5&&cameraError<1e-6&&unreachable===0&&maxTrailingExtensionDeficit<.055&&maxAnchorHeight<.026;")
once("schema:'hareworks-woman-source-measured-world-ik-v0.1.12'", "schema:'hareworks-woman-accepted-v019-world-pin-v0.1.13'")
once("solver:'measured phase + hybrid heel/sole/toe contact + true world-space two-bone IK'", "solver:'accepted v0.1.9 ankle/pelvis curves + inverse phase-dependent support-root + world-space contact IK'")
once("sourceAnkleRms:Math.sqrt(shapeSum/Math.max(shapeCount,1)),sourcePoseSamples:360,", "sourceAnkleRms:Math.sqrt(shapeSum/Math.max(shapeCount,1)),sourcePoseSamples:360,\n    rootMethod:rootCurve.method,rootStridePerFullCycle:rootCurve.stride,\n    cameraOrbitEnabled:orbit.enableRotate&&orbit.enableZoom,\n    maxTrailingExtensionDeficit,maxAnchorHeight,")
once("if(ready&&playing){accumulator", "if(ready&&playing){accumulator")
once("renderer.render(scene,camera);}", "orbit.update();renderer.render(scene,camera);}")
once("const heelPatch=pickSolePatch(actorMeshes,foot),toePatch=pickSolePatch(actorMeshes,toe);\n  legs[side]={side,chain:b,up,knee,bridge,foot,toe,patch,heelPatch,toePatch,meshes:actorMeshes,soleLocal,upperLength,lowerLength};patches[side]=patch;", "const split=splitFootPatches(actorMeshes,foot,toe,patch),heelPatch=split.heel,toePatch=split.toe,solePatch=split.sole;\n  legs[side]={side,chain:b,up,knee,bridge,foot,toe,patch:solePatch,heelPatch,toePatch,meshes:actorMeshes,soleLocal,upperLength,lowerLength};patches[side]=solePatch;")
region(' // The authored clip has a documented final <7% phase reset:', ' groundOffset=absoluteGround;', ''' // Preserve original sub-duration source samples unchanged; do not invent a seam morph.
 sourceSeamRepair={left:{repaired:false},right:{repaired:false}};
 sourceGround=absoluteGround;
 sourceGaits={left:inferVelocityContact(sourceSamples.left),right:inferVelocityContact(sourceSamples.right)};
 const phaseSeparation=mod1(sourceGaits.left.start-sourceGaits.right.start);
 if(phaseSeparation<.30||phaseSeparation>.70)throw Error('LEFT_RIGHT_CONTACT_TIMING_AMBIGUOUS '+phaseSeparation);
 rootCurve=buildRootCurve(sourceSamples,sourceGaits);stride=rootCurve.stride;
 updateMotionStatus();
''')
once("const c=legs[side],foot=srcRig[c.foot.name],q=wq(foot).toArray();\n   const obs={phase:i/N,ankle:wpos(foot).toArray(),heel:soleWorld(refMeshes,c.heelPatch).toArray(),", "const c=legs[side],foot=srcRig[c.foot.name],q=wq(foot).toArray();\n   const sourceHip=wpos(srcRig[c.up.name]),accepted=legAt(footProfile,side,clipDuration*i/N),\n     acceptedYaw=independentPose(pelvisProfile,clipDuration*i/N).pelvisYaw;\n   const acceptedAnkle=sourceHip.clone().add(V(...rotateY(accepted.ankleLocal,acceptedYaw)));\n   const obs={phase:i/N,ankle:acceptedAnkle.toArray(),hip:sourceHip.toArray(),knee:wpos(srcRig[c.knee.name]).toArray(),\n    heel:soleWorld(refMeshes,c.heelPatch).toArray(),")
once("v0.1.12 SOURCE TASK-SPACE", "v0.1.13 ACCEPTED V019 INVERSE SUPPORT ROOT")
once("status('MEASURED SOURCE GAIT ACTIVE · world support · two-bone IK · owner gait review pending');", "status('ACCEPTED V0.1.9 WALK + INVERTED WORLD SUPPORT · orbit restored · owner review pending');")
# No auto pass: a quantitative gate is independent of human inspection.
if 'new THREE.AnimationMixer(actor)' in s or 'Math.sin(Math.PI*' in s:
    raise RuntimeError('SOURCE_LEG_PLAYBACK_OR_SYNTHETIC_SINE_DETECTED')
if 'new OrbitControls(camera,renderer.domElement)' not in s or 'rootAt(rootCurve,totalPhase)' not in s:
    raise RuntimeError('CAMERA_OR_ROOT_FEATURE_MISSING')
v.write_text(s)

html=target/'index.html';h=html.read_text()
if h.count('v0.1.12')<1:raise RuntimeError('UNEXPECTED_HTML_VERSION')
h=h.replace('v0.1.12','v0.1.13').replace('Measured Source Foot IK','Accepted Walk + World Pin')
h=h.replace('Fixed-follow camera presets','Orbit camera presets (drag to rotate, pinch to zoom)')
h=h.replace('<strong>Camera pinned:</strong>','<strong>Camera follows and orbits:</strong>')
h=h.replace('<button id="top">Top</button>','<button id="top">Top</button><button id="resetCamera">Reset orbit</button><span>Drag to rotate · pinch to zoom</span>')
h=h.replace('The camera follows a fixed offset while the ground moves past.', 'The camera follows the traveling actor while preserving your orbit and zoom.')
h=h.replace('src="./viewer.mjs?build=v0.1.13"','src="./viewer.mjs?build=v0.1.13-inverse-root"')
if 'resetCamera' not in h:raise RuntimeError('HTML_CAMERA_RESET_MISSING')
html.write_text(h)
print(json.dumps({'status':'PATCHED_NEW_DIRECTORY_ONLY','viewerBytes':len(s),'orbitRestored':True,'inverseRoot':True,'noLegacyEdits':True}))
__HAREWORKS_V013_FILE_4__
cat > "$DEST_REL/review-server.py" <<'__HAREWORKS_V013_FILE_5__'
"""Read-only local Hareworks viewer, explicit owner-unapproved browser audits."""
import hashlib
import http.server
import json
import math
import os
import pathlib
import sys

root,ready,state=sys.argv[1:]
SOURCE='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
SCHEMA='hareworks-woman-accepted-v019-world-pin-v0.1.13'
class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,
        '.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
    def __init__(self,*a,**kw):super().__init__(*a,directory=root,**kw)
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
        self.send_header('Pragma','no-cache')
        super().end_headers()
    def do_POST(self):
        if self.path.split('?')[0].split('/')[-1]!='evidence':
            self.send_error(404);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 450<=size<=4000000:raise ValueError('invalid evidence size')
            raw=self.rfile.read(size);d=json.loads(raw)
            if d.get('schema')!=SCHEMA or d.get('sourceSha256')!=SOURCE:raise ValueError('wrong artifact or source')
            if d.get('sourceClip')!='Walking_Woman' or d.get('rigBones')!=74:raise ValueError('wrong rig')
            if d.get('generatedAnimationMixerCount')!=0 or d.get('oneVisibleCharacter') is not True:
                raise ValueError('source clip playback forbidden on generated actor')
            if d.get('cameraOrbitEnabled') is not True or d.get('cameraFixedFollow') is not True:
                raise ValueError('camera orbit/follow regression')
            if d.get('rootMovementIsWorldTravel') is not True or d.get('stanceAnchorCoordinateSystem')!='WORLD':
                raise ValueError('not physical world locomotion')
            if d.get('physicsRateHz')!=120 or d.get('sampledFrames',0)<300:raise ValueError('incomplete real browser audit')
            if d.get('contactGate') not in ('PASS','WARN') or d.get('resemblanceGate')!='OWNER_VISUAL_REVIEW_PENDING':
                raise ValueError('contact and appearance verdicts conflated')
            if d.get('ownerVisualAcceptance') is not False:raise ValueError('owner verdict cannot be self-reported')
            if set(d.get('sourceContactMethod',{}))!={'left','right'}:raise ValueError('source leg windows absent')
            for side in ('left','right'):
                duty=d['sourceContactMethod'][side].get('duty')
                if not isinstance(duty,(int,float)) or not .45<=duty<=.73:raise ValueError('support window incorrect')
            for key in ('rootStridePerFullCycle','worldTravelZ','maximumContactAnchorTranslation',
                'maxFootPenetration','maxIKResidual','cameraWorldFollowError','sourceAnkleRms',
                'maxTrailingExtensionDeficit','maxAnchorHeight'):
                val=d.get(key)
                if not isinstance(val,(int,float)) or not math.isfinite(val):raise ValueError('nonfinite or missing '+key)
            if not .90<d['rootStridePerFullCycle']<1.55:raise ValueError('full-cycle distance regressed')
            out=pathlib.Path(state);out.mkdir(parents=True,exist_ok=True)
            path=out/'woman-accepted-v019-world-pinning-browser-v0.1.13.json';path.write_bytes(raw)
            receipt={'state':'BROWSER_MEASURED_CONTACT_AUDIT_SAVED_OWNER_GAIT_REVIEW_PENDING',
                'sha256':hashlib.sha256(raw).hexdigest(),'path':str(path),
                'modelSha256':SOURCE,'contactGate':d['contactGate'],
                'cameraOrbitEnabled':True,'ownerVisualAcceptance':False}
            (out/'browser-receipt-v0.1.13.json').write_text(json.dumps(receipt,indent=2)+'\n')
            b=json.dumps(receipt).encode();self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
        except Exception as e:self.send_error(422,'evidence rejected '+str(e)[:90])
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
pathlib.Path(ready).write_text(json.dumps({'pid':os.getpid(),'port':server.server_address[1],
    'root':root,'state':state,'sourceSha256':SOURCE,'ownerVisualAcceptance':False}))
server.serve_forever()
__HAREWORKS_V013_FILE_5__
cat > "$DEST_REL/README.md" <<'__HAREWORKS_V013_FILE_6__'
# Hareworks Walking_Woman v0.1.13: accepted procedural walk + inverse support-root

**State at script authoring:** v0.1.12 published but visually REJECTED. This version is a mathematical integration candidate. Physical GLB browser audit and owner gait approval are separate, pending gates.

## What is retained

- v0.1.9 accepted six-harmonic, hip-relative ankle and knee-pole curves (unchanged), four-harmonic pelvis position/yaw and the existing source-calibrated upper-body motion.
- A single traveling visible character with genuine world-coordinate stance anchors and two-bone leg IK. Original 74-joint Hareworks nine-clip GLB is immutable (SHA256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`). No new GLB added; no other version edited.
- Three.js OrbitControls restored: drag/touch rotate, pinch/scroll zoom, presets and reset; camera target translates with actor but user angle and zoom are not reset each frame.

## Mathematical repair

The original in-place fitted gait is already accurate to the archived `Walking_Woman` witnesses (60 samples): left ankle RMS 0.00154, right RMS 0.00155 units, pelvis RMS 0.00178. v0.1.12's ~0.68 units travel **per entire two-foot cycle** was around half the required travel. Let q be full gait phase and A_s(q) the already-accepted hip-relative fitted ankle. Build the per-phase world-root curve with dR_z/dq ≈ −dA_{support,z}/dq, blending the support ankles in double support; R(q+1)=R(q)+D. The archived-fit proxy yields approximately D=1.22 units/full cycle. Preserve v0.1.9 pelvis and knee pole; avoid arbitrary pelvis vertical reach shifts.

Derive candidate support episodes from negative source ankle forward velocity instead of thresholding height alone. Earlier exact source witness math gave left ~58% duty and right ~60%; these windows are kinematic hypotheses and MUST be validated against actually skinned heel/sole/toe heights and ground velocities. Distinct heel/midsole/toe witness vertex sets are partitioned from the shoe mesh, with a hard guard if they cannot be distinguished. Stance uses immutable world contact targets; swing uses the existing accepted ankle curve plus a decaying correction to preserve the last physically solved ankle at liftoff. No generic swing sine or live source leg clip on the character. A contact pivot transition captures the current skinned witness without forcibly teleporting it to Y=0; the height offset is measured and gated.

A two-support constraint is not guaranteed to be perfectly compatible with source poses. Do not hide conflicts; record actual skinned drift, floor penetration, reach warnings, and late-stance trailing extension deficit. Physical contact PASS requires a real 120 Hz browser three-cycle audit and cannot grant owner gait acceptance.

## Delivery / regression standard

One SHA-guarded Android Termux entrypoint operating on the user's NORMAL persistent checkout `~/storage/documents/GodotProjects/parametric-parambulator`. No new clones or unrelated LFS downloads. No reset, stash, forced checkout or force push. Never overwrite a pre-existing target. Stage only the brand-new `tools/hareworks-forward-woman/v0.1.13/` directory; test and read back the exact Git remote commit and actual served JS bytes. Preserve source `AGENTS.md`, existing v0.1.9, v0.1.11, v0.1.12, Repl and Hareworks model hashes. Explicit owner review remains pending even if local/static tests pass.

Measured source repository basis at `fa927379890b111220b368595c6e2f27725a9d1a`. Mathematical audit and bibliography saved to Home Center: https://docs.google.com/document/d/1dbxbhHIfaJO731l5g1O7fU91xQ6ztiRkLULOmYnEZpM/edit
__HAREWORKS_V013_FILE_6__
cat > "$DEST_REL/contract.json" <<'__HAREWORKS_V013_FILE_7__'
{
  "schema":"hareworks-woman-accepted-v019-world-pinning-v0.1.13",
  "repo":"Valar05/parametric-parambulator",
  "parent":"fa927379890b111220b368595c6e2f27725a9d1a",
  "executionLane":"Android Termux Git only, persistent Documents/GodotProjects normal checkout",
  "authoritativeReference":"v0.1.9 accepted procedural Walking_Woman pelvis/ankle/knee pole",
  "modelSha256":"a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "sourceClip":"Walking_Woman",
  "rigBones":74,
  "worldRootMethod":"negative phase-derivative of v0.1.9 stance ankle path, double-support weighted",
  "contactMethod":"phase velocity hypothesis + independent real skinned heel, sole, toe patches; actual browser contact gate",
  "camera":"orbitable and zoomable fixed-follow tracking, retain yaw/pitch/zoom",
  "visibleActors":1,
  "animatedSourceClipOnGeneratedActor":false,
  "acceptedVersionsUntouched":["v0.1.9","v0.1.11","v0.1.12","v0.2.2","v0.2.6","v0.2.7"],
  "modelModified":false,
  "mutablePaths":["tools/hareworks-forward-woman/v0.1.13/"],
  "rulesAGENTSBlob":"547c2af52303f4efb718bbf8f82a698110c7bfca",
  "rulesCampaignEtiquette":"1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI",
  "rulesTopDownEtiquette":"1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU",
  "ownerRejectedEarlier":"v0.1.12 visually rejected: popping, excessive forward foot, missing trailing extension and camera orbit",
  "physicalGate":"real 74-joint skinned shoe audit at 120 Hz for 3 cycles; contact drift, floor intrusion, reachable IK and trailing extension",
  "styleGate":"owner approval of the actual rendered gait versus accepted v0.1.9",
  "ownerVisualAcceptance":false
}
__HAREWORKS_V013_FILE_7__
STAGE='patch-and-test-v019-inverse-root'
python3 "$DEST_REL/patch.py" "$BUILDROOT"
python3 - "$DEST_REL/patch.py" "$DEST_REL/review-server.py" <<'PY_PARSE'
import pathlib,sys
for f in sys.argv[1:]:compile(pathlib.Path(f).read_text(),f,'exec')
print('PYTHON_PARSE_PASS')
PY_PARSE
for f in root-motion.mjs foot-gait.mjs root-model-test.mjs contact-test.mjs viewer.mjs;do
  node --check "$DEST_REL/$f" || { echo "BLOCKED_JS_PARSE=$f" >&2;exit 77; }
done
node "$DEST_REL/contact-test.mjs"
node "$DEST_REL/root-model-test.mjs"
node "$DEST_REL/contact-core-test.mjs"
node "$DEST_REL/geometry-test.mjs"
# Actual immutable 6.8MB GLB structural preflight. Source mesh-only support physics
# still requires the 120 Hz browser audit; do NOT claim that this is a skinned IK test.
python3 - "$CHECKOUT/$MODEL" "$MODEL_SHA" <<'GLB_PREFLIGHT'
import hashlib,json,pathlib,struct,sys
p=pathlib.Path(sys.argv[1]);data=p.read_bytes()
if hashlib.sha256(data).hexdigest()!=sys.argv[2]:raise SystemExit('BLOCKED_MODEL_SHA_IN_PREFLIGHT')
magic,version,size=struct.unpack_from('<4sII',data,0)
if magic!=b'glTF' or version!=2 or size!=len(data):raise SystemExit('BLOCKED_MODEL_GLB_STRUCTURE')
chunk_size,chunk_type=struct.unpack_from('<II',data,12)
if chunk_type!=0x4E4F534A:raise SystemExit('BLOCKED_MODEL_GLB_JSON_CHUNK')
model=json.loads(data[20:20+chunk_size]);clips=[c.get('name') for c in model.get('animations',[])]
if len(clips)!=9 or 'Walking_Woman' not in clips:raise SystemExit('BLOCKED_SOURCE_WALK_CLIP_IN_MODEL')
if not model.get('skins') or not model.get('meshes'):raise SystemExit('BLOCKED_MODEL_SKIN_OR_MESH')
print('ACTUAL_BINARY_GLB_IDENTITY_AND_STRUCTURE_PASS','clips='+str(len(clips)),'skins='+str(len(model['skins'])))
print('REAL_SKINNED_WORLD_PINNING_PENDING_BROWSER_AUDIT')
GLB_PREFLIGHT
python3 - "$DEST_REL/viewer.mjs" "$DEST_REL/index.html" "$DEST_REL/root-motion.mjs" <<'PYPRESERVE'
import pathlib,sys
viewer=pathlib.Path(sys.argv[1]).read_text();html=pathlib.Path(sys.argv[2]).read_text();root=pathlib.Path(sys.argv[3]).read_text()
required=['new OrbitControls(camera,renderer.domElement)','orbit.target.add(delta)','orbit.update()','rootAt(rootCurve,totalPhase)',
'acceptedAnkle=sourceHip.clone()', 'maxTrailingExtensionDeficit','splitFootPatches','new SourceFootContact','cameraOrbitEnabled']
for marker in required:
 if marker not in viewer:raise SystemExit('BLOCKED_REQUIRED_V019_FEATURE_MISSING:'+marker)
if 'resetCamera' not in html or 'touch-action:none' not in html:raise SystemExit('BLOCKED_TOUCH_ORBIT_USER_INTERFACE_MISSING')
if 'buildRootCurve' not in root or 'inferVelocityContact' not in root:raise SystemExit('BLOCKED_FULL_CYCLE_ROOT_MATH_MISSING')
if 'new THREE.AnimationMixer(actor)' in viewer:raise SystemExit('BLOCKED_SOURCE_LEG_PLAYBACK')
print('PRESERVE_CAMERA_ROOT_AND_CONTACT_STATIC_PASS')
PYPRESERVE
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
git commit -m 'Hareworks v0.1.13 accepted v0.1.9 gait with inverse-root world pinning in persistent GodotProjects checkout'
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
 'acceptedV019Math':'analytical source-ankle root inversion, full two-foot cycle',
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
