#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_SOURCE_DERIVED_WORLD_IK_v0.1.12_r4_DOCUMENTS
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_SOURCE_DERIVED_WORLD_IK_v0.1.12_r4_DOCUMENTS'
VERSION='v0.1.12'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='350d0c9a696233bfc76e409a07e3431ea91892fd'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-source-v0.1.12-r4-documents"
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
  grep -q 'hareworks-woman-source-measured-ik-campaign-v0.1.12' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
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
STAGE='generate-source-measured-gait'
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.11" "$DEST_REL"
cp "$ENTRY" "$DEST_REL/campaign-v0.1.12-r4-godotprojects.sh"
cat > "$DEST_REL/foot-gait.mjs" <<'__V012_FOOT_GAIT_MJS__'
/* Hareworks v0.1.12: source-measured task-space trajectory and hybrid contact scheduler.
   No source joint rotations drive the generated character. No generic swing sine. */
export const phase01 = q => ((q % 1) + 1) % 1;
const clamp = (v,a,b) => Math.max(a,Math.min(b,v));
const interp = (a,b,t) => a.map((x,i) => x + (b[i]-x)*t);
const add = (a,b) => a.map((x,i) => x+b[i]);
const sub = (a,b) => a.map((x,i) => x-b[i]);
const mul = (a,t) => a.map(x => x*t);
const finite3 = a => Array.isArray(a)&&a.length===3&&a.every(Number.isFinite);
export function sourceAt(samples,phase){
  const n=samples.length;if(n<60)throw Error('GAIT_SOURCE_TOO_SHORT');
  const x=phase01(phase)*n,i=Math.floor(x),t=x-i;
  const at=j=>samples[(j+n)%n],p0=at(i-1),p1=at(i),p2=at(i+1),p3=at(i+2);
  const spline=(name)=>p1[name].map((_,k)=>{
    const a=p0[name][k],b=p1[name][k],c=p2[name][k],d=p3[name][k];
    return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t);
  });
  return {phase:phase01(phase),ankle:spline('ankle'),heel:spline('heel'),sole:spline('sole'),toe:spline('toe'),
    q0:p1.q,q1:p2.q,qt:t};
}
const wrapDelta=(v,start)=>phase01(v-start);
export function inferContacts(samples){
  if(!Array.isArray(samples)||samples.length<180||samples.some(s=>!['ankle','heel','sole','toe'].every(k=>finite3(s[k]))||!Array.isArray(s.q)||s.q.length!==4||!s.q.every(Number.isFinite)))throw Error('INVALID_MEASURED_RIG_SAMPLES');
  const n=samples.length,low=samples.map(s=>Math.min(s.heel[1],s.toe[1])),mn=Math.min(...low),mx=Math.max(...low),span=mx-mn;
  if(span<.008)throw Error('INSUFFICIENT_SOURCE_FOOT_CLEARANCE');
  let best=null;
  // Evaluate real height contours. The duty emerges from source samples, never fixed at 55/60%.
  for(const fraction of [.10,.14,.18,.22,.28,.34,.40]){
    const threshold=mn+Math.max(.006,span*fraction),under=low.map(h=>h<=threshold);
    let runs=[];
    for(let i=0;i<n;i++){
      if(!under[i]||under[(i-1+n)%n])continue;
      let len=0;while(len<n&&under[(i+len)%n])len++;
      runs.push({startIndex:i,count:len,duty:len/n,threshold,fraction});
    }
    for(const run of runs){
      if(run.duty<.30||run.duty>.79)continue;
      const avg=Array.from({length:run.count},(_,k)=>low[(run.startIndex+k)%n]).reduce((a,b)=>a+b,0)/run.count;
      const score=avg-mn + Math.abs(run.duty-.53)*span*.05+fraction*span*.04;
      if(!best||score<best.score)best={...run,score};
    }
  }
  if(!best)throw Error('CONTACT_INFERENCE_AMBIGUOUS__CHECK_SOURCE_AND_GROUND');
  return {start:best.startIndex/n,duty:best.duty,threshold:best.threshold,sourceHeightRange:span,
    lowHeight:mn,method:'continuous skinned heel/toe low-height episode, adaptive threshold',confidence:'kinematic inference, not force sensing'};
}
export function supportMode(sample,ground){
  const heel=sample.heel[1]-ground,toe=sample.toe[1]-ground,delta=heel-toe;
  const threshold=Math.max(.008,Math.min(.024,Math.abs(heel)+Math.abs(toe))*.20);
  return delta < -threshold?'heel': delta > threshold?'toe':'sole';
}
export function swingResidual(samples,gait,phase){
  const u=clamp((wrapDelta(phase,gait.start)-gait.duty)/(1-gait.duty),0,1);
  const liftoff=sourceAt(samples,gait.start+gait.duty),touchdown=sourceAt(samples,gait.start),now=sourceAt(samples,phase);
  return sub(now.ankle,interp(liftoff.ankle,touchdown.ankle,u));
}
export class SourceFootContact{
  constructor({samples,gait,sourceGround,groundY=0,readWitness}){
    this.samples=samples;this.gait=gait;this.sourceGround=sourceGround;this.groundY=groundY;
    this.readWitness=readWitness;this.state='initial';this.pivot='sole';this.anchor=null;
    this.swingFrom=null;this.swingTo=null;this.transitions=0;this.pivotTransitions=0;
  }
  step({phase,worldZ,stride}){
    const s=sourceAt(this.samples,phase),p=wrapDelta(phase,this.gait.start),planted=p<this.gait.duty;
    const nextState=planted?'stance':'swing';let pivot=planted?supportMode(s,this.sourceGround):'air';
    // A contact rolls heel -> sole -> toe, never backwards within one plant.
    if(planted&&this.state==='stance'){
      const order={heel:0,sole:1,toe:2};
      if(order[pivot]<order[this.pivot])pivot=this.pivot;
    }
    if(nextState!==this.state){
      if(planted){this.pivot=pivot;this.anchor=this.readWitness(pivot).slice();this.anchor[1]=this.groundY;}
      else{
        const currentAnkle=this.readWitness('ankle').slice();
        this.swingFrom=currentAnkle;
        const landing=sourceAt(this.samples,this.gait.start).ankle;
        const phaseLeft=1-p;
        this.swingTo=[landing[0],landing[1]-this.sourceGround+this.groundY,landing[2]+worldZ+stride*phaseLeft];
        if(this.state==='initial'){
          // Starting mid-swing must not teleport to the interpolated late-swing pose.
          const u=clamp((p-this.gait.duty)/(1-this.gait.duty),0,.995),r=swingResidual(this.samples,this.gait,phase);
          this.swingFrom=mul(sub(sub(currentAnkle,r),mul(this.swingTo,u)),1/(1-u));
        }
      }
      this.state=nextState;this.transitions++;
    }else if(planted&&pivot!==this.pivot){
      // Heel -> full sole -> toe: transfer the physical pivot at the existing skinned witness.
      this.pivot=pivot;this.anchor=this.readWitness(pivot).slice();this.anchor[1]=this.groundY;this.pivotTransitions++;
    }
    let ankleTarget;
    if(planted){
      const sourcePivot=s[this.pivot];
      ankleTarget=sub(this.anchor,sub(sourcePivot,s.ankle));
    }else{
      const u=clamp((p-this.gait.duty)/(1-this.gait.duty),0,1);
      if(!this.swingFrom||!this.swingTo)throw Error('MISSING_SWING_ENDPOINT');
      ankleTarget=add(interp(this.swingFrom,this.swingTo,u),swingResidual(this.samples,this.gait,phase));
    }
    if(!finite3(ankleTarget))throw Error('NONFINITE_SOURCE_IK_TARGET');
    return {ankleTarget,planted,pivot,anchor:this.anchor?.slice()||null,source:s,
      witnessTarget:planted?this.anchor.slice():ankleTarget.slice(),transitions:this.transitions,pivotTransitions:this.pivotTransitions};
  }
}
__V012_FOOT_GAIT_MJS__
cat > "$DEST_REL/foot-gait-test.mjs" <<'__V012_FOOT_GAIT_TEST_MJS__'
import assert from 'node:assert/strict';
import {phase01,sourceAt,inferContacts,swingResidual,SourceFootContact,supportMode} from './foot-gait.mjs';
const n=360,samples=Array.from({length:n},(_,i)=>{
 const p=i/n,stance=p>=.08&&p<.62,h=stance?0:.16*Math.sin(Math.PI*((p-.62+1)%1)/.46)**2;
 const z=.35*Math.cos(2*Math.PI*p),ankle=[.1,.2+h,z];
 return {phase:p,ankle,heel:[.1,h,z-.10],toe:[.1,h,z+.12],sole:[.1,h,z],q:[0,0,0,1]};
});
assert.equal(phase01(-.2),.8);
const g=inferContacts(samples);
assert(g.duty>.3&&g.duty<.8,JSON.stringify(g));
assert(sourceAt(samples,.333).ankle.every(Number.isFinite));
assert(swingResidual(samples,g,g.start+g.duty+.1).every(Number.isFinite));
assert.equal(supportMode({heel:[0,-.03,0],toe:[0,.03,0]},0),'heel');
let witness={heel:[0,0,0],toe:[0,0,.2],sole:[0,0,.1],ankle:[0,.2,0]};
const c=new SourceFootContact({samples,gait:g,sourceGround:0,readWitness:x=>witness[x]});
let first=c.step({phase:g.start+.01,worldZ:0,stride:.65});
assert(first.planted&&first.anchor&&first.pivot);
const anchor=first.anchor.slice();
for(let k=0;k<Math.floor(g.duty*n)-3;k++){let f=c.step({phase:g.start+.01+(k/n),worldZ:k*.002,stride:.65});assert(f.planted);if(f.pivot===first.pivot)assert.deepEqual(f.anchor,anchor)}
let air=c.step({phase:g.start+g.duty+.005,worldZ:.4,stride:.65});assert(!air.planted&&air.ankleTarget.every(Number.isFinite));
assert.throws(()=>inferContacts([{heel:[0,0,0]}]),/INVALID/);
assert.throws(()=>inferContacts(Array.from({length:n},()=>({ankle:[0,0,0],heel:[0,0,0],toe:[0,0,0],sole:[0,0,0],q:[0,0,0,1]}))),/CLEARANCE/);
console.log('SOURCE_GAIT_UNIT_PASS',JSON.stringify(g));
__V012_FOOT_GAIT_TEST_MJS__
cat > "$DEST_REL/patch.py" <<'__V012_PATCH_PY__'
#!/usr/bin/env python3
"""Hareworks v0.1.12 deterministic immutable-version patcher.
Requires pristine v0.1.11 copied to a brand-new v0.1.12 path by Termux.
"""
import json
import pathlib
import re
import sys

root=pathlib.Path(sys.argv[1]); target=root/'tools/hareworks-forward-woman/v0.1.12'
v=target/'viewer.mjs'; s=v.read_text()
def once(old,new):
    global s
    count=s.count(old)
    if count!=1:raise RuntimeError(f'PATCH_ANCHOR_COUNT expected=1 got={count} anchor={old[:80]!r}')
    s=s.replace(old,new)
def region(begin,end,replacement):
    global s
    if s.count(begin)!=1 or s.count(end)!=1:raise RuntimeError(f'PATCH_REGION_MISSING {begin!r}/{end!r}')
    a=s.index(begin);b=s.index(end,a+len(begin));s=s[:a]+replacement+s[b:]

once("import {WorldContact,mod1,clamp,swingProgress,nextStartDelta,followCamera,cadenceFor,travelToNextContact} from './contact-core.mjs';",
     "import {mod1,clamp,followCamera,cadenceFor} from './contact-core.mjs';\nimport {inferContacts,sourceAt,SourceFootContact} from './foot-gait.mjs';")
once('stride=.66,clearance=.055,phase=0','stride=.66,phase=0')
once('let maxDrift=0,maxIK=0,maxPenetration=0,unreachable=0,contactCount=0,swingCount=0,transitions=0,lastAnchorLocations={},failedFrames=0;',
     'let maxDrift=0,maxIK=0,maxPenetration=0,unreachable=0,contactCount=0,swingCount=0,transitions=0,failedFrames=0;\nlet sourceSamples=null,sourceGaits=null,sourceGround=0,witnessCache=null,sourceSeamRepair={},shapeSum=0,shapeCount=0;')
region('function setWorldQ(', 'function turnToward(', '''function witnessWorld(c,kind){
 if(kind==='ankle')return wpos(c.foot);
 const patch=kind==='heel'?c.heelPatch:kind==='toe'?c.toePatch:c.patch;
 return soleWorld(c.meshes,patch);
}
function measuredFootQ(s){return Q().fromArray(s.q0).slerp(Q().fromArray(s.q1),s.qt).normalize()}
function setWorldQ(b,desired){b.quaternion.copy(wq(b.parent).invert().multiply(desired)).normalize()}
''')
region('function nominalLanding(', 'const cameraTarget=', '''function measuredWitnesses(){const out={};for(const side of ['left','right']){
 const c=legs[side];out[side]=Object.fromEntries(['ankle','heel','sole','toe'].map(k=>[k,witnessWorld(c,k).toArray()]));
 }return out;}
function contactTargets(){const out={};for(const side of ['left','right']){
 out[side]=worldContacts[side].step({phase,worldZ,stride});
 }return out;}
function adjustReach(targets){let correction=0;
 for(const side of ['left','right']){
  const leg=legs[side],ankle=V(...targets[side].ankleTarget),hip=wpos(leg.up),r=leg.upperLength+leg.lowerLength-.014;
  correction=Math.max(correction,Math.max(0,hip.distanceTo(ankle)-r));}
 if(correction>0){const moved=Math.min(.14,correction+.002);rig.mixamorigHips.position.y-=moved;actor.updateMatrixWorld(true);if(correction>.14)unreachable++;}
}
function solveLeg(side,t){const c=legs[side],desiredQ=measuredFootQ(t.source),target=V(...t.ankleTarget);
 let desiredAnkle=target.clone(),best=Infinity;
 for(let iter=0;iter<5;iter++){
  for(const b of c.chain)copyLocal(b,rest[b.name]);actor.updateMatrixWorld(true);
  const H=wpos(c.up),K0=wpos(c.knee),max=c.upperLength+c.lowerLength-.005,min=Math.abs(c.upperLength-c.lowerLength)+.005;
  let direction=desiredAnkle.clone().sub(H);
  if(direction.length()>max||direction.length()<min){direction.setLength(clamp(direction.length(),min,max));desiredAnkle.copy(H).add(direction);unreachable++;}
  const pole=legAt(footProfile,side,phase*clipDuration).poleLocal;
  const yaw=independentPose(pelvisProfile,phase*clipDuration).pelvisYaw;
  const K=V(...kneeFromTarget(H.toArray(),desiredAnkle.toArray(),c.upperLength,c.lowerLength,rotateY(pole,yaw)));
  turnToward(c.up,K0,K);actor.updateMatrixWorld(true);
  turnToward(c.knee,wpos(c.foot),desiredAnkle);actor.updateMatrixWorld(true);
  setWorldQ(c.foot,desiredQ);actor.updateMatrixWorld(true);
  const actual=witnessWorld(c,t.planted?t.pivot:'ankle');
  const wanted=V(...t.witnessTarget),error=wanted.sub(actual);best=error.length();
  if(best<.0018)break;desiredAnkle.add(error.multiplyScalar(.92));
 }
 const actual=witnessWorld(c,t.planted?t.pivot:'ankle'),drift=actual.distanceTo(V(...t.witnessTarget));
 const ankle=wpos(c.foot),reference=V(...t.source.ankle).add(actor.position);
 const shapeError=ankle.distanceTo(reference);shapeSum+=shapeError*shapeError;shapeCount++;
 if(t.planted){maxDrift=Math.max(maxDrift,drift);contactCount++}else swingCount++;
 const h=['heel','sole','toe'].map(k=>witnessWorld(c,k).y);maxPenetration=Math.max(maxPenetration,Math.max(0,...h.map(y=>-y)));
 maxIK=Math.max(maxIK,drift);
 drawPins[side].position.copy(V(...t.witnessTarget));drawPins[side].visible=$('showContacts').checked;
 drawPins[side].material.color.setHex(t.planted?0x65f2b7:0xffb65f);
 return {planted:t.planted,pivot:t.pivot,drift,sole:witnessWorld(c,'sole').toArray(),
  ankle:ankle.toArray(),target:t.ankleTarget,anchor:t.anchor,shapeError,reach:c.upperLength+c.lowerLength};
}
function physicsStep(dt){
 // Capture last physically solved geometry BEFORE frameBody restores the source-calibration skeleton.
 witnessCache=measuredWitnesses();
 const cadence=cadenceFor(speed,stride);phase=mod1(phase+cadence*dt);worldZ+=speed*dt;frameBody(phase);
 const targets=contactTargets();adjustReach(targets);const feet={};
 for(const side of ['left','right'])feet[side]=solveLeg(side,targets[side]);
 transitions=worldContacts.left.transitions+worldContacts.right.transitions;runFrames++;
 lastStats={phase,worldTravelZ:worldZ,speed,cadence,worldRootZ:actor.position.z,feet,transitions,
 maxSkinnedStanceDrift:maxDrift,maxSkinnedTargetError:maxIK,maxNewFloorPenetration:maxPenetration,
 sourceAnkleRms:Math.sqrt(shapeSum/Math.max(1,shapeCount)),reachAdjustments:unreachable,
 contactFrames:contactCount,swingFrames:swingCount,solvedIKPerFrame:true,generatedAnimationMixerCount:0};
 return lastStats;
}
''')
region('function renderMetrics(', "$('play').onclick=", '''function renderMetrics(prefix='LIVE'){if(!lastStats)return;const feet=lastStats.feet;
 $('metrics').textContent=`${prefix} · SOURCE-MEASURED WALKING_WOMAN · WORLD IK\\nTravel Z ${worldZ.toFixed(3)} u, phase ${(phase*100).toFixed(1)}%, cadence ${cadenceFor(speed,stride).toFixed(3)} cycles/s\\nLEFT ${feet.left.pivot} ${feet.left.planted?'PLANTED':'SWING'}, drift ${feet.left.drift.toFixed(4)} u\\nRIGHT ${feet.right.pivot} ${feet.right.planted?'PLANTED':'SWING'}, drift ${feet.right.drift.toFixed(4)} u\\nSkinned support error ${maxDrift.toFixed(5)} u, floor penetration ${maxPenetration.toFixed(5)} u\\nSource ankle RMS ${lastStats.sourceAnkleRms.toFixed(5)} u; knee reach warnings ${unreachable}\\nContact transitions ${transitions}; source stance L ${(sourceGaits.left.duty*100).toFixed(1)}%, R ${(sourceGaits.right.duty*100).toFixed(1)}%\\nANIMATION MIXER ON VISIBLE ACTOR: ZERO · source joints NOT replayed`;
}
function clearStats(){maxDrift=0;maxIK=0;maxPenetration=0;unreachable=0;contactCount=0;swingCount=0;transitions=0;runFrames=0;lastStats=null;shapeSum=0;shapeCount=0;}
function initRun(){if(!ready)return;
 phase=0;worldZ=0;clearStats();frameBody(0);witnessCache=measuredWitnesses();const next={};
 for(const side of ['left','right'])next[side]=new SourceFootContact({samples:sourceSamples[side],gait:sourceGaits[side],
  sourceGround,readWitness:k=>witnessCache[side][k]});
 worldContacts=next;physicsStep(0);pinCamera();renderMetrics('RESET');
}
''')
region("$('speed').oninput=", "$('showContacts').onchange=", '''$('speed').oninput=()=>{speed=Number($('speed').value);$('speedOut').textContent=speed.toFixed(2)+' u/s';updateMotionStatus()};
function updateMotionStatus(){
 $('motionStatus').textContent=`SOURCE-DERIVED FOOT PATH · ${stride.toFixed(3)} u travel/cycle · ${cadenceFor(speed,stride).toFixed(3)} cycles/s · no synthetic foot lift`;
}
updateMotionStatus();
''')
region("$('audit').onclick=",'function frame(now)', '''$('audit').onclick=async()=>{if(!ready)return;const was=playing;playing=false;
 status('Auditing measured contacts across 3 cycles, 120 Hz; source resemblance is a separate gate…');const oldSpeed=speed;speed=.52;
 try{initRun();const n=Math.ceil((3/cadenceFor(speed,stride))*120);
  const worst={left:0,right:0},previous={left:null,right:null},pivotCounts={},samples=[];
  let anchorMaxStep=0;
  for(let i=0;i<n;i++){
   const m=physicsStep(1/120);
   for(const side of ['left','right']){
    const f=m.feet[side];pivotCounts[side+':'+f.pivot]=(pivotCounts[side+':'+f.pivot]||0)+1;
    if(f.planted){worst[side]=Math.max(worst[side],f.drift);
      if(previous[side]&&previous[side].pivot===f.pivot)
       anchorMaxStep=Math.max(anchorMaxStep,Math.hypot(...f.anchor.map((x,j)=>x-previous[side].anchor[j])));
      previous[side]={pivot:f.pivot,anchor:f.anchor?.slice()};}
    else previous[side]=null;
   }
   if(i%15===0)samples.push({time:i/120,phase:m.phase,worldZ:m.worldTravelZ,
    left:m.feet.left,right:m.feet.right,cameraTrackingOffset:cameraOffsets[view]});
   if(i%35===0)await new Promise(requestAnimationFrame);
  }
  pinCamera();const cameraError=Math.abs((camera.position.z-actor.position.z)-cameraOffsets[view][2]);
  const physicalPass=worst.left<=.025&&worst.right<=.025&&maxPenetration<=.020&&anchorMaxStep<=1e-8&&worldZ>.9&&cameraError<1e-8&&unreachable===0;
  report={schema:'hareworks-woman-source-measured-world-ik-v0.1.12',sourceSha256:SOURCE_SHA,
    sourceClip:CLIP,rigBones:74,sourceContactMethod:sourceGaits,sourceSeamRepair,
    strideCycle:stride,actualCyclesTested:n/120*cadenceFor(speed,stride),
    nominalForwardAdvance:worldZ,generatedAnimationMixerCount:0,calibrationOnlySourceMixer:true,
    oneVisibleCharacter:true,rootMovementIsWorldTravel:true,cameraFixedFollow:true,
    stanceAnchorCoordinateSystem:'WORLD',contactPatch:'skinned heel/sole/toe witnesses',physicsRateHz:120,
    sampledFrames:n,worldTravelZ:worldZ,referenceRigWasNotDisplayed:true,
    solver:'measured phase + hybrid heel/sole/toe contact + true world-space two-bone IK',
    maxSkinnedSoleDriftPerSide:worst,maximumContactAnchorTranslation:anchorMaxStep,
    maxFootPenetration:maxPenetration,maxIKResidual:maxIK,reachAdjustments:unreachable,
    cameraWorldFollowError:cameraError,touchdownTransitions:transitions,contactPivotCounts:pivotCounts,
    sourceAnkleRms:Math.sqrt(shapeSum/Math.max(shapeCount,1)),sourcePoseSamples:360,
    contactGate:physicalPass?'PASS':'WARN',resemblanceGate:'OWNER_VISUAL_REVIEW_PENDING',
    status:physicalPass?'PHYSICAL_CONTACT_PASS_STYLE_OWNER_PENDING':'PHYSICAL_CONTACT_WARN_OWNER_REVIEW_REQUIRED',
    ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,observations:samples};
  $('metrics').textContent=`${report.status}\\nCONTACT: heel/sole/toe anchors L ${worst.left.toFixed(5)}, R ${worst.right.toFixed(5)} u (limit .025)\\nSource ankle RMS ${report.sourceAnkleRms.toFixed(5)} u (advisory, NOT gait approval)\\nFloor intrusion ${maxPenetration.toFixed(5)} u; IK warnings ${unreachable}\\n3 measured cycles, 120 Hz, traveling root ${worldZ.toFixed(3)} u\\nSTYLE GATE: must resemble v0.1.9 Walking_Woman in owner's inspection`;
  try{const response=await fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(report)});
   if(!response.ok)throw Error('HTTP_'+response.status);const receipt=await response.json();status(report.status+' · evidence saved '+receipt.sha256.slice(0,12));}
  catch(e){status(report.status+' · autosave unavailable '+e.message+' · Export still works')}
 }catch(e){status('SOURCE_GAIT_AUDIT_ERROR '+e.message);console.error(e)}
 finally{const summary=$('metrics').textContent;speed=oldSpeed;initRun();$('metrics').textContent=summary;playing=was;$('play').textContent=playing?'Pause':'Play';}
};
''')
region(' // Calibrate source contact LOW phases', ' groundOffset=absoluteGround;', ''' // Measure actual heel/toe/sole/ankle positions and orientation from the immutable source clip.
 const N=360;sourceSamples={left:[],right:[]};let absoluteGround=Infinity;
 for(let i=0;i<N;i++){
  mixer.setTime(clipDuration*i/N);source.updateMatrixWorld(true);
  for(const side of ['left','right']){
   const c=legs[side],foot=srcRig[c.foot.name],q=wq(foot).toArray();
   const obs={phase:i/N,ankle:wpos(foot).toArray(),heel:soleWorld(refMeshes,c.heelPatch).toArray(),
    sole:soleWorld(refMeshes,c.patch).toArray(),toe:soleWorld(refMeshes,c.toePatch).toArray(),q};
   sourceSamples[side].push(obs);absoluteGround=Math.min(absoluteGround,obs.heel[1],obs.toe[1]);
  }
 }
 // The authored clip has a documented final <7% phase reset: smooth ONLY a verified seam.
 sourceSeamRepair={};
 for(const side of ['left','right']){
  const arr=sourceSamples[side],start=Math.floor(.93*N),a=arr[start],b=arr[0],last=arr[N-1];
  const jump=V(...last.ankle).distanceTo(V(...b.ankle));
  sourceSeamRepair[side]={terminalResetAnkleJump:jump,repaired:false};
  if(jump>.045){for(let i=start+1;i<N;i++){
   const t=(i-start)/(N-start),w=t*t*(3-2*t);
   for(const k of ['ankle','heel','sole','toe'])arr[i][k]=a[k].map((v,j)=>v*(1-w)+b[k][j]*w);
   arr[i].q=Q().fromArray(a.q).slerp(Q().fromArray(b.q),w).toArray();
  }sourceSeamRepair[side].repaired=true;}
 }
 sourceGround=absoluteGround;sourceGaits={left:inferContacts(sourceSamples.left),right:inferContacts(sourceSamples.right)};
 // Source-derived spatial travel per cycle; no artist-tuned stride/clearance parameters.
 const measuredTravel=['left','right'].map(side=>{
  const z=sourceSamples[side].map(s=>s.ankle[2]);return Math.max(...z)-Math.min(...z);
 });
 stride=(measuredTravel[0]+measuredTravel[1])*.5;
 if(!(stride>=.3&&stride<=1))throw Error('SOURCE_DERIVED_TRAVEL_OUT_OF_RANGE '+stride);
 updateMotionStatus();
 const phaseSeparation=mod1(sourceGaits.left.start-sourceGaits.right.start);
 if(phaseSeparation<.30||phaseSeparation>.70)throw Error('LEFT_RIGHT_CONTACT_TIMING_AMBIGUOUS '+phaseSeparation);
''')
# Original low-phase identifiers removed; preserve reference source and dispose source Mixer.
region(' const footPhases=Object.fromEntries(', ' ready=true;', ''' const footPhases=Object.fromEntries(Object.entries(sourceGaits).map(([side,g])=>
  [side,{contactStart:g.start,sourceStanceDuty:g.duty,threshold:g.threshold,seam:sourceSeamRepair[side]}]));
''')
once('legs[side]={side,chain:b,up,knee,bridge,foot,toe,patch,meshes:actorMeshes,soleLocal,upperLength,lowerLength,stanceQ:wq(foot),contactStart:0};',
     "const heelPatch=pickSolePatch(actorMeshes,foot),toePatch=pickSolePatch(actorMeshes,toe);\n  legs[side]={side,chain:b,up,knee,bridge,foot,toe,patch,heelPatch,toePatch,meshes:actorMeshes,soleLocal,upperLength,lowerLength};")
once('v0.1.11 · SHA ${SOURCE_SHA}', 'v0.1.12 SOURCE TASK-SPACE · SHA ${SOURCE_SHA}')
once('· low-foot phases ${JSON.stringify(footPhases)}', '· inferred heel/toe contact ${JSON.stringify(footPhases)}')
once("a.download='hareworks-woman-world-foot-ik-v0.1.11.json'", "a.download='hareworks-woman-source-world-ik-v0.1.12.json'")
once("status('REAL RIG ACTIVE · one moving actor · fixed-follow camera · world-locked skinned soles');", "status('MEASURED SOURCE GAIT ACTIVE · world support · two-bone IK · owner gait review pending');")
# There must not be a generated AnimationMixer driving the actor.
if 'new THREE.AnimationMixer(actor)' in s:raise RuntimeError('GENERATED_ACTOR_HAS_ANIMATION_MIXER')
if 'Math.sin(Math.PI*' in s:raise RuntimeError('GENERIC_SWING_SINE_RETAINED')
v.write_text(s)

html=target/'index.html';h=html.read_text()
h=h.replace('v0.1.11','v0.1.12').replace('Real World Foot IK','Measured Source Foot IK')
h=h.replace('One independently posed skinned Hareworks character walking','One source-measured, independently IK-solved skinned Hareworks character walking')
h=h.replace('Longer, lower swing by default; tune stride and clearance independently. Foot anchors and IK stay active.','Swing and heel-to-toe motion are reconstructed from the original Walking_Woman source, not parameter sliders. Physical contact and style resemblance are distinct gates.')
# Delete old synthetic-shape controls but retain world speed input.
a=h.index('<div class="bar" role="group" aria-label="Stride and foot clearance tuning">')
b=h.index('<div id="motionStatus"',a)
h=h[:a]+h[b:]
h=h.replace('Checking stride, clearance and cadence agreement...', 'Deriving measured gait and ground support...')
h=h.replace('Run 3-cycle skinned foot-pin audit','Audit source gait + skinned contacts')
h=h.replace('src="./viewer.mjs"','src="./viewer.mjs?build=v0.1.12"')
h=h.replace('The model moves in world Z;', 'The model moves in world Z;')
html.write_text(h)

# Only new-version paths may be written. Treat successful patch publication as pending human approval.
for p in ['viewer.mjs','index.html','foot-gait.mjs','foot-gait-test.mjs']:
    assert (target/p).is_file(),p
print(json.dumps({'patch':'SOURCE_MEASURED_GAIT_PATCHED','modelUnchanged':True,'viewerBytes':v.stat().st_size,'htmlBytes':html.stat().st_size}))
__V012_PATCH_PY__
cat > "$DEST_REL/review-server.py" <<'__V012_REVIEW_SERVER_PY__'
"""Hareworks v0.1.12: no-store viewer with strict browser evidence readback."""
import hashlib
import http.server
import json
import os
import pathlib
import sys

root,ready,state=sys.argv[1:]
SOURCE_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
SCHEMA='hareworks-woman-source-measured-world-ik-v0.1.12'
class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,
        '.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=root,**kwargs)
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
        self.send_header('Pragma','no-cache')
        super().end_headers()
    def do_POST(self):
        if self.path.split('?')[0].split('/')[-1]!='evidence':
            self.send_error(404);return
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<350 or n>4000000:raise ValueError('invalid evidence size')
            raw=self.rfile.read(n);d=json.loads(raw)
            if d.get('schema')!=SCHEMA or d.get('sourceSha256')!=SOURCE_SHA:raise ValueError('wrong campaign source')
            if d.get('sourceClip')!='Walking_Woman' or d.get('rigBones')!=74:raise ValueError('wrong rig or clip')
            if d.get('generatedAnimationMixerCount')!=0 or d.get('oneVisibleCharacter') is not True:raise ValueError('runtime source animation forbidden')
            if d.get('cameraFixedFollow') is not True or d.get('stanceAnchorCoordinateSystem')!='WORLD':raise ValueError('contact/camera requirement')
            if d.get('physicsRateHz')!=120 or d.get('sampledFrames',0)<300:raise ValueError('incomplete measured audit')
            if d.get('contactGate') not in ('PASS','WARN') or d.get('resemblanceGate')!='OWNER_VISUAL_REVIEW_PENDING':raise ValueError('must keep style gate pending')
            if d.get('ownerVisualAcceptance') is not False:raise ValueError('owner acceptance cannot be self-reported')
            if not isinstance(d.get('sourceContactMethod'),dict) or set(d['sourceContactMethod'])!={'left','right'}:raise ValueError('missing source gait events')
            for s in ('left','right'):
                g=d['sourceContactMethod'][s]
                if not (isinstance(g.get('duty'),(int,float)) and .30<=g['duty']<=.79):raise ValueError('invalid gait events')
            for f in ('worldTravelZ','maximumContactAnchorTranslation','maxFootPenetration','maxIKResidual','cameraWorldFollowError','sourceAnkleRms'):
                val=d.get(f)
                if not isinstance(val,(int,float)) or not (-1e7<val<1e7):raise ValueError('invalid metric '+f)
            out=pathlib.Path(state);out.mkdir(parents=True,exist_ok=True)
            p=out/'woman-measured-source-browser-evidence-v0.1.12.json';p.write_bytes(raw)
            receipt={'status':'BROWSER_MEASURED_AUDIT_SAVED_NOT_OWNER_ACCEPTED',
                'sha256':hashlib.sha256(raw).hexdigest(),'path':str(p),
                'modelSha256':SOURCE_SHA,'contactGate':d['contactGate'],
                'resemblanceGate':'OWNER_VISUAL_REVIEW_PENDING'}
            (out/'browser-receipt-v0.1.12.json').write_text(json.dumps(receipt,indent=2)+'\n')
            raw_out=json.dumps(receipt).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(raw_out)));self.end_headers();self.wfile.write(raw_out)
        except Exception as exc:
            self.send_error(422,'evidence rejected: '+str(exc)[:100])
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
pathlib.Path(ready).write_text(json.dumps({'pid':os.getpid(),'port':server.server_address[1],
 'root':root,'state':state,'sourceSha256':SOURCE_SHA}))
server.serve_forever()
__V012_REVIEW_SERVER_PY__
cat > "$DEST_REL/README.md" <<'__V012_README_MD__'
# Hareworks v0.1.12: source-derived biped IK gait

**Stage:** Termux-publishable candidate for owner visual review. No automatic visual approval.

## Mission

Replace v0.1.11's guessed `0.55` duty, smoothstep foot travel, additive sine lift, and fixed foot pitch with measured `Walking_Woman` skinned heel/sole/toe/ankle trajectories and quaternion foot orientation. Preserve one translating, skinned character, a stationary-world contact frame, fixed-follow camera, real two-bone 120 Hz leg IK, and source-fitted torso. The reference animation is sampled only at initialization; there is no visible-actor `AnimationMixer`, no source leg joint rotation playback, and no changes to the GLB or accepted existing versions.

## Evidence and limitations

- Original GLB expected SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6` (6,784,896 bytes, 74 bones, nine clips).
- The baseline `Walking_Woman` source is sampled at 360 gait phases, with real skinned heel, sole and toe witnesses, ankle position and foot orientation.
- Contact windows are inferred from the observed contiguous low-contact episode at adaptive measured thresholds; not force plate evidence. Ambiguity or implausible left/right separation blocks runtime calibration, not replaced by a fixed duty.
- Heel, sole and toe constitute distinct measured contact-pivot modes, each retaining a world anchor while active. During pivot transfers the anchor is captured from the most recent solved skinned position. During swing, interpolation uses the **measured source displacement residual**, not a generic sine or smoothstep. Root travel per cycle is derived from both source ankles’ measured forward excursions rather than selected with a stride slider.
- Some authored clip source resets may be smoothed only in the last 7% of the phase loop, with exact seam changes disclosed. Source pelvis and upper animation motion remain from the existing fitted system.
- **Physical gate:** skinned active-contact drift per foot <=0.025 model units, world anchor stationary while the same contact pivot is active, ground intrusion <=0.020, no IK reach errors, actual world travel and fixed camera offset. Logs include all-three pivot penetration and source ankle RMS.
- **Independent style gate:** phase-aligned source ankle RMS is an advisory metric, not proof of resemblance. Owner must judge gait character against accepted v0.1.9. No code/test output can set `ownerVisualAcceptance=true`.
- Foot witness selection is based on skinned vertices near the relevant anatomical bone. The 3D source's contact truth is inferred, and no force solver is claimed. If the source's heel/toe shape is unsuitable, report precisely instead of inventing style.

## Runtime

From a verified Android Termux launcher, the SHA-locked campaign checks repository HEAD, `AGENTS.md`, the true model hash and unique version path, then generates/tests the new viewer in the persistent user-owned Git checkout at ~/storage/documents/GodotProjects/parametric-parambulator. The r4 GodotProjects launcher keeps a persistent normal Git checkout in Android Documents. It disables all automatic LFS smudging (including the missing Repl.glb object), selectively fetches ONLY the required Hareworks model if absent, and installs it into the checkout ONCE. The r4 gate repairs the per-repository LFS clean filter and permits only the exact SHA-verified materialized binary's unstaged status; unrelated changes still block. Android shared storage does not reliably support hardlinks. It reuses a private verified LFS cache and never downloads the GLB on every run. It commits solely `tools/hareworks-forward-woman/v0.1.12/`, pushes through Termux Git (no force), readbacks exact remote commit, and starts a cache-proof local review server. The printed complete URL is the actual running server only after an HTTP check; the browser must still load and audit the physical rig. The script retains JSON receipts under `~/.local/state/hareworks-woman-source-v0.1.12-r4-documents/`.

On successful publishing the model remains unchanged, the viewer is a *candidate*, and owner gait approval remains pending. Source bibliography is in Home Center Drive: https://docs.google.com/document/d/1dbxbhHIfaJO731l5g1O7fU91xQ6ztiRkLULOmYnEZpM/edit
__V012_README_MD__
cat > "$DEST_REL/contract.json" <<'__V012_CONTRACT_JSON__'
{
  "schema":"hareworks-woman-source-measured-ik-campaign-v0.1.12",
  "repo":"Valar05/parametric-parambulator",
  "expectedMain":"350d0c9a696233bfc76e409a07e3431ea91892fd",
  "executionLane":"Android Termux Git ONLY",
  "checkoutPath":"~/storage/documents/GodotProjects/parametric-parambulator",
  "checkoutKind":"persistent normal Git checkout, no sparse checkout",
  "lfsPolicy":"all non-Hareworks LFS pointers remain unmaterialized; Repl object unavailable upstream",
  "mutationAllowlist":["tools/hareworks-forward-woman/v0.1.12/"],
  "originalModel":"assets/hareworks/Hareworks-nine-clips.glb",
  "sourceModelSHA256":"a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "sourceModelBytes":6784896,
  "referenceClip":"Walking_Woman",
  "sourceSamplePhases":360,
  "sourceDerivedTravelPerCycle":true,
  "sourceFootJointPlaybackAtRuntime":false,
  "generatedCharacterMixerCount":0,
  "visibleCharacters":1,
  "worldSpacePhysicalAnchors":true,
  "actualSkinnedHeelSoleToeWitnesses":true,
  "legIK":"two-bone 120Hz, physical skinned contact residual correction",
  "camera":"fixed-follow, one traveling character",
  "lockedVersions":["v0.1.9","v0.1.11","v0.2.2","v0.2.6","v0.2.7"],
  "rulesAGENTSBlob":"547c2af52303f4efb718bbf8f82a698110c7bfca",
  "rulesCampaignEtiquetteDoc":"1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI",
  "rulesTopDownEtiquetteDoc":"1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU",
  "modelChangesAuthorized":false,
  "newVersionOnly":true,
  "physicalGate":"browser real skinned witnesses, 3 cycles at 120 Hz",
  "styleGate":"owner visual resemblance to Walking_Woman accepted v0.1.9",
  "ownerVisualAcceptance":false
}
__V012_CONTRACT_JSON__
STAGE='test-source-measured-gait'
python3 "$DEST_REL/patch.py" "$BUILDROOT"
python3 - "$DEST_REL/patch.py" "$DEST_REL/review-server.py" <<'PYCOMPILE'
import pathlib,sys
for name in sys.argv[1:]:compile(pathlib.Path(name).read_text(),name,'exec')
print('PYTHON_SOURCE_COMPILE_PASS')
PYCOMPILE
node --check "$DEST_REL/viewer.mjs"
node --check "$DEST_REL/foot-gait.mjs"
node --check "$DEST_REL/foot-gait-test.mjs"
node "$DEST_REL/foot-gait-test.mjs"
node "$DEST_REL/contact-core-test.mjs"
node "$DEST_REL/geometry-test.mjs"
grep -q 'sourceSamples={left:\[\],right:\[\]}' "$DEST_REL/viewer.mjs" || { echo 'BLOCKED_SOURCE_GAIT_EXTRACTION_MISSING' >&2;exit 77; }
grep -q 'SourceFootContact' "$DEST_REL/viewer.mjs" || { echo 'BLOCKED_WORLD_CONTACT_FIX_MISSING' >&2;exit 77; }
grep -q 'inferContacts' "$DEST_REL/viewer.mjs" || { echo 'BLOCKED_MEASURED_STANCE_GAIT_FIX_MISSING' >&2;exit 77; }
! grep -q 'new THREE.AnimationMixer(actor)' "$DEST_REL/viewer.mjs" || { echo 'BLOCKED_SOURCE_LEG_REPLAY' >&2;exit 77; }
[ "$(sha256sum "$CHECKOUT/$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || { echo 'BLOCKED_SOURCE_MODEL_CHANGED' >&2;exit 77; }
# No overwritten prior campaign, no adjacent cleanup. Only the newly generated directory.
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
git commit -m 'Hareworks v0.1.12 source-derived gait in persistent GodotProjects checkout'
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
 for f in viewer.mjs foot-gait.mjs;do
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
[ "$(sha256sum "$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || { echo 'BLOCKED_HAREWORKS_GLB_CHANGED' >&2;exit 80; }
python3 - "$STATE" "$CAMPAIGN_ID" "$BASE_SHA" "$NEW_SHA" "$ENTRY_SHA" "$MODEL_SHA" "$URL" "$PORT" "$SERVER_PID" "$CHECKOUT" "$AGENTS_BLOB" "$ETIQUETTE_DOC" "$TOPDOWN_DOC" "$HTTP_SHA" "$PUBLISHED_REUSE" "$RECOVERED_R2_PARTIAL_INIT" <<'PYRECEIPT'
import datetime,json,pathlib,sys
(state,campaign,base,commit,entry,model,url,port,pid,checkout,agents,etiquette,topdown,viewer_hash,reused,recovered)=sys.argv[1:]
receipt={
 'campaign':campaign,'status':'PERSISTENT_CHECKOUT_AND_SOURCE_GAIT_PUBLISHED_BROWSER_AUDIT_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sparseCheckout':False,
 'androidSharedStorageGitTrust':'exact-canonical-project-only, global safe.directory',
 'lfsStatusGuard':'Git LFS filters configured locally; only exactly SHA-verified tracked Hareworks binary is admissible as unstaged model materialization',
 'lfsStatusGuardDoesNotHideChanges':True,
 'previousIncompleteGitInitRecovered':recovered=='1',
 'unrelatedReplLfsFetched':False,'hareworksCopyPolicy':'exactly one verified worktree model, reusable private LFS cache',
 'rulesReadInAuthoringTurn':{'AGENTSBlob':agents,'CampaignEtiquetteDocument':etiquette,'TopDownEtiquetteDocument':topdown},
 'viewerUrl':url,'viewerPid':int(pid),'viewerPort':int(port),'viewerGaitSha256':viewer_hash,
 'alreadyPublishedRerun':reused=='1','browserRealSkinnedFootAudit':'PENDING',
 'contactGate':'PENDING_BROWSER_AUDIT','gaitResemblanceGate':'PENDING_OWNER_VISUAL_ACCEPTANCE',
 'ownerVisualAcceptance':False,'canonicalModelUnchanged':True}
p=pathlib.Path(state)/'latest-receipt.json'
p.write_text(json.dumps(receipt,indent=2)+'\n')
print('RECEIPT='+str(p))
PYRECEIPT
STAGE='review-ready-owner-verdict-pending'
echo "CHECKOUT_READY=$CHECKOUT"
echo 'NORMAL_GIT_CHECKOUT=YES'
echo "SOURCE_GAIT_FIXES=$CHECKOUT/$DEST_REL"
echo "MODEL_SHA256=$MODEL_SHA"
echo "PUBLISHED_COMMIT=$NEW_SHA"
echo "SCRIPT_SHA256=$ENTRY_SHA"
echo "VIEWER_PID=$SERVER_PID"
echo "VIEWER_URL=$URL"
echo 'CONTACT_GATE=PENDING_REAL_BROWSER_AUDIT'
echo 'GAIT_RESEMBLANCE_GATE=PENDING_OWNER_VISUAL_ACCEPTANCE'
if command -v termux-open-url >/dev/null 2>&1;then
 termux-open-url "$URL" || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
elif command -v am >/dev/null 2>&1;then
 am start -a android.intent.action.VIEW -d "$URL" >/dev/null 2>&1 || echo 'BROWSER_OPEN_UNVERIFIED: open VIEWER_URL printed above'
fi
