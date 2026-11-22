#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_SOURCE_KNEE_RESTORATION_v0.1.20_DOCUMENTS
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_SOURCE_KNEE_RESTORATION_v0.1.20_DOCUMENTS'
VERSION='v0.1.20'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='af2aed9e58c9679d841c7b954e3ebe368e52a183'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-source-knee-restoration-v0.1.20-v1-documents"
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
  grep -q 'hareworks-v0.1.20-original-knee-pole-restoration' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
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
[ -f tools/hareworks-forward-woman/v0.1.19/viewer.mjs ] || { echo 'BLOCKED_MISSING_SOURCE_GAIT_BASELINE' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.19/viewer.mjs)" = 0b3a884c2799059f04fd95bef1c11a089f2d1321 ] || { echo 'BLOCKED_PUBLISHED_V019_SOURCE_CHANGED' >&2;exit 74; }
[ -f tools/hareworks-forward-woman/v0.1.9/viewer.mjs ] || { echo 'BLOCKED_MISSING_ACCEPTED_V020_REFERENCE' >&2;exit 74; }
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
SOURCE_REL='tools/hareworks-forward-woman/v0.1.19'
[ -d "$CHECKOUT/$SOURCE_REL" ] || { echo 'BLOCKED_MISSING_PUBLISHED_V019_SOURCE' >&2;exit 77; }
cp -R "$CHECKOUT/$SOURCE_REL" "$DEST_REL"
for old_launcher in "$DEST_REL"/campaign-*.sh;do [ -f "$old_launcher" ] && rm -- "$old_launcher" || :;done
cp "$ENTRY" "$DEST_REL/campaign-v0.1.20-v1-godotprojects.sh"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.2" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3"
# v0.1.19 whole source copied; approved foot heading and original model are unchanged.
cat > "$DEST_REL/source-knee-governor.mjs" <<'V020_KNEE_SOURCE'
/* v0.1.20: Stable forward-facing local knee poles and source ankle trajectory have
 * authority. Contact physics may adjust an ankle only inside the anatomical
 * source-knee envelope. NO previous-frame knee, radial smoothing, post-solve
 * centerline projection, or skinned witness error feedback into thigh/shin IK.
 * A conflict is evidence, not permission to silently contort a leg. */
import {kneeFromTarget} from './ik-core.mjs';
// Per the owner: the poles remain stationary in character-local space, well
// ANTERIOR (+Z), and never follow an animated foot, knee, or prior frame.
// Asymmetry is fitted to the original 60-frame Walking_Woman knee witnesses.
export const STABLE_LOCAL_POLES=Object.freeze({left:Object.freeze([-.20,-.05,.90]),right:Object.freeze([.10,.15,.90])});
export function stableForwardPole(side,pelvisYaw){
 const p=STABLE_LOCAL_POLES[side];if(!p||!Number.isFinite(pelvisYaw))throw Error('STABLE_FORWARD_POLE_INVALID');
 const c=Math.cos(pelvisYaw),s=Math.sin(pelvisYaw);
 return [p[0]*c+p[2]*s,p[1],-p[0]*s+p[2]*c];
}
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const add=(a,b)=>a.map((v,i)=>v+b[i]);
const scale=(a,n)=>a.map(v=>v*n);
const norm=a=>Math.hypot(...a);
const lerp=(a,b,t)=>a.map((v,i)=>v+(b[i]-v)*t);
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function fitReach(H,A,l1,l2){
 const v=sub(A,H),d=norm(v),lo=Math.abs(l1-l2)+.0003,hi=l1+l2-.0003;
 if(!Number.isFinite(d)||d<1e-9)throw Error('SOURCE_KNEE_ZERO_REACH');
 return add(H,scale(v,clamp(d,lo,hi)/d));
}
export function chooseSourceKnee({hip,sourceHip,sourceKnee,sourceAnkle,contactAnkle,pole,
 upperLength,lowerLength,side,centerX,maxKneeDeviation=.025,minSideClearance=.012}){
 const positions=[hip,sourceHip,sourceKnee,sourceAnkle,contactAnkle,pole];
 if(!positions.every(a=>Array.isArray(a)&&a.length===3&&a.every(Number.isFinite))||
   ![upperLength,lowerLength,centerX,maxKneeDeviation,minSideClearance].every(Number.isFinite)||
   upperLength<=0||lowerLength<=0||maxKneeDeviation<=0|| !['left','right'].includes(side))
   throw Error('SOURCE_KNEE_GOVERNOR_BAD_INPUT');
 const sign=side==='left'?1:-1;
 const expectedAnkle=fitReach(hip,add(hip,sub(sourceAnkle,sourceHip)),upperLength,lowerLength);
 const expectedKnee=add(hip,sub(sourceKnee,sourceHip));
 const requestedDelta=norm(sub(contactAnkle,expectedAnkle));
 const calc=t=>{
  const A=fitReach(hip,lerp(expectedAnkle,contactAnkle,t),upperLength,lowerLength);
  const K=kneeFromTarget(hip,A,upperLength,lowerLength,pole);
  const error=norm(sub(K,expectedKnee)),signed=sign*(K[0]-centerX);
  return {ankle:A,knee:K,kneeSourceError:error,signedKneeClearance:signed,
   valid:error<=maxKneeDeviation&&signed>=minSideClearance};
 };
 let best=calc(0);
 // Baseline reconstruction itself should not fail just because a foot is planted.
 // Report the source/rig discrepancy, but do not make a visually catastrophic
 // discontinuous decision using the previous physical frame.
 const baselineMismatch=!best.valid;
 if(!baselineMismatch){
  const full=calc(1);
  if(full.valid){best=full;best.acceptedFraction=1;}
  else{
   let lo=0,hi=1;
   for(let i=0;i<18;i++){
    const mid=(lo+hi)*.5,next=calc(mid);
    if(next.valid){lo=mid;best=next;}else hi=mid;
   }
   best.acceptedFraction=lo;
  }
 }else best.acceptedFraction=0;
 return {...best,baselineMismatch,requestedContactDelta:requestedDelta,
  unfulfilledContactDelta:norm(sub(contactAnkle,best.ankle)),
  sourceKnee:expectedKnee};
}
V020_KNEE_SOURCE

cat > "$DEST_REL/source-knee-governor-test.mjs" <<'V020_KNEE_TEST'
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chooseSourceKnee,stableForwardPole,STABLE_LOCAL_POLES} from './source-knee-governor.mjs';
const source=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const profile=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
assert.equal(source.samples.length,60);
let maxBaseline=0,minSide=Infinity,maxAccepted=0,suppressed=0,baselineMismatch=0,cases=0;
const norm=a=>Math.hypot(...a);
for(const side of ['left','right']){
 const sign=side==='left'?1:-1,{upperLength,lowerLength}=profile[side];
 for(let i=0;i<60;i++){
  const entry=source.samples[i],s=entry.legs[side],cent=(entry.legs.left.hip[0]+entry.legs.right.hip[0])*.5;
  // Validate original archived knee-plane, as opposed to guessing an angle.
  // A static, forward (+Z) character-local bend pole. Not one retargeted
  // from an animated knee, and not an oscillating X/Y offset.
  assert(STABLE_LOCAL_POLES[side][2]>.88);
  const pole=stableForwardPole(side,entry.pelvisYaw);
  const base={hip:s.hip,sourceHip:s.hip,sourceKnee:s.knee,sourceAnkle:s.ankle,
    pole,upperLength,lowerLength,side,centerX:cent};
  const fit=chooseSourceKnee({...base,contactAnkle:s.ankle});
  assert.equal(fit.baselineMismatch,false);
  assert.equal(fit.acceptedFraction,1);
  maxBaseline=Math.max(maxBaseline,fit.kneeSourceError);minSide=Math.min(minSide,fit.signedKneeClearance);
  assert(fit.signedKneeClearance>.012);
  for(const x of [-.3,-.1,0,.08,.22])for(const z of [-.13,0,.13]){
   const contact=[s.ankle[0]-sign*x,s.ankle[1],s.ankle[2]+z];
   const k=chooseSourceKnee({...base,contactAnkle:contact});
   const repeat=chooseSourceKnee({...base,contactAnkle:contact});
   assert.deepEqual(k,repeat,'no hidden knee history / frame rate coupling');
   assert(k.signedKneeClearance>=.012-1e-8,'cannot cross pelvis center');
   assert(k.kneeSourceError<=.025+1e-8,'do not sacrifice knee silhouette for contact');
   assert(Math.abs(norm(k.ankle.map((v,j)=>v-s.hip[j]))-upperLength-lowerLength)<1.0);
   if(k.unfulfilledContactDelta>.025)suppressed++;
   maxAccepted=Math.max(maxAccepted,k.kneeSourceError);
   if(k.baselineMismatch)baselineMismatch++;
   cases++;
  }
 }
}
assert(maxBaseline<.020&&minSide>.018,'stable forward pole must resemble real archived knees');
assert(suppressed>30,'synthetic contact disturbance must challenge the knee guard');
for(const side of ['left','right'])for(const yaw of [-.4,0,.2,.6]){
 const p=stableForwardPole(side,yaw),q=stableForwardPole(side,yaw);
 assert.deepEqual(p,q);assert(Math.hypot(...p)>.85);
 const c=Math.cos(yaw),s=Math.sin(yaw),localX=p[0]*c-p[2]*s,localZ=p[0]*s+p[2]*c;
 assert(Math.abs(localX-STABLE_LOCAL_POLES[side][0])<1e-12,'lateral pole movement forbidden');
 assert(Math.abs(localZ-STABLE_LOCAL_POLES[side][2])<1e-12,'forward pole must stay out front');
}
assert.throws(()=>stableForwardPole('bad',0));
assert.equal(baselineMismatch,0);
assert.throws(()=>chooseSourceKnee({}));
console.log(`STATIC_FORWARD_KNEE_POLE_SOURCE_RESEMBLANCE_PASS samples=120 max=${maxBaseline} minSide=${minSide}`);
console.log(`STATELESS_KNEE_CONTACT_GOVERNOR_PASS cases=${cases} kneeMax=${maxAccepted} protectedConflicts=${suppressed}`);
V020_KNEE_TEST

cat > "$DEST_REL/patch.py" <<'V020_PATCH_FILE_END'
#!/usr/bin/env python3
"""v0.1.20 restore the pure v0.1.9 knee pole and source shape. NEVER edit older versions.
Start from a COPY of pinned, published v0.1.19. No binary/model writes.
"""
import pathlib,sys
source,dest=map(pathlib.Path,sys.argv[1:]);p=dest/'viewer.mjs';s=p.read_text()
def once(old,new):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError('V020_PATCH_ANCHOR_COUNT_'+str(n)+'_'+old[:100])
 s=s.replace(old,new,1)
def region(start,end,new):
 global s
 if s.count(start)!=1 or s.count(end)!=1:raise RuntimeError('V020_REGION_NOT_UNIQUE')
 i=s.index(start);j=s.index(end,i)
 s=s[:i]+new+s[j:]
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
assert 'function runwayFootQ(' in s and 'OrbitControls' in s
once('/* v0.1.19. ONE moving Walking_Woman.', '/* v0.1.20. ONE moving Walking_Woman.')
once("import {sourceKneePlane} from './source-knee-plane.mjs';",
    "import {chooseSourceKnee,stableForwardPole} from './source-knee-governor.mjs';")
once('let priorWorldKnee={left:null,right:null},minSignedKneeCenterline=Infinity,',
'''let priorWorldKnee={left:null,right:null},minSignedKneeCenterline=Infinity,''') if False else None
once('    maxKneeSourcePositionDelta=0,maxKneeWorldStep=0,kneeCenterlineCorrections=0;',
    '''    maxKneeSourcePositionDelta=0,maxKneeWorldStep=0,kneeCenterlineCorrections=0;
let maxAnkleContactConflict=0,sourceKneeBaselineMismatches=0;''')
# The 0.1.19 stateful bend-plane, its arbitrary angular speed limit and side
# clamp are rejected. This new solver is an ORIGINAL source-pole solve plus
# one bounded contact target choice. No skinned-witness iterative backreaction.
region('function solveLeg(side,t){','function physicsStep(dt){', '''function solveLeg(side,t){
 const c=legs[side],desiredQ=measuredFootQ(t.source),requested=V(...t.ankleTarget);
 // Start every step from the original v0.1.9 source phase, not the previous
 // frame's knee quaternion, contact error, or a history-dependent pole.
 for(const b of c.chain)copyLocal(b,rest[b.name]);actor.updateMatrixWorld(true);
 const H=wpos(c.up),K0=wpos(c.knee);
 const yaw=independentPose(pelvisProfile,phase*clipDuration).pelvisYaw;
 // Stable source-calibrated pole, fixed relative to model heading. No X sway.
 const pole=stableForwardPole(side,yaw);
 const hipCenterX=(wpos(legs.left.up).x+wpos(legs.right.up).x)*.5;
 const chosen=chooseSourceKnee({hip:H.toArray(),sourceHip:t.source.hip,
   sourceKnee:t.source.knee,sourceAnkle:t.source.ankle,
   contactAnkle:requested.toArray(),pole,upperLength:c.upperLength,
   lowerLength:c.lowerLength,side,centerX:hipCenterX,
   maxKneeDeviation:.025,minSideClearance:.012});
 // Keep the same ORIGINAL v0.1.9 two-link solve. Shoe style remains distal.
 const A=V(...chosen.ankle),K=V(...chosen.knee);
 turnToward(c.up,K0,K);actor.updateMatrixWorld(true);
 turnToward(c.knee,wpos(c.foot),A);actor.updateMatrixWorld(true);
 setWorldQ(c.foot,desiredQ);actor.updateMatrixWorld(true);
 const kneeBefore=wpos(c.knee),hipBefore=wpos(c.up),ankleBefore=wpos(c.foot);
 const upperQ=c.up.quaternion.clone(),shinQ=c.knee.quaternion.clone();
 // Keep witness caching unstyled; foot-yaw and knee pose are independent.
 if(!unstyledWitnessCache)unstyledWitnessCache={};
 unstyledWitnessCache[side]=Object.fromEntries(['ankle','heel','sole','toe'].map(k=>[k,witnessWorld(c,k).toArray()]));
 // Exact approved v0.1.18 foot heading logic, unchanged.
 const footFit=independentPose(pelvisProfile,phase*clipDuration).feet[side];
 const kneeToFoot=clamp(kneeBefore.x-ankleBefore.x,-.16,.16);
 const stylizedToe=[footFit.toeVector[0]+.20*kneeToFoot,footFit.toeVector[1],footFit.toeVector[2]];
 try{
  const original=wq(c.foot),fitted=runwayFootQ(c,stylizedToe,distalHeading(side,footFit,pelvisProfile));
  const styleBlend=t.planted?(chosen.unfulfilledContactDelta<.008?.35:.08):.52;
  setWorldQ(c.foot,original.slerp(fitted,styleBlend));actor.updateMatrixWorld(true);
 }catch(footError){
  setWorldQ(c.foot,desiredQ);previewFaults++;lastPreviewError=String(footError.message||footError);
 }
 const kneeChanged=kneeBefore.distanceTo(wpos(c.knee));
 const hipChanged=hipBefore.distanceTo(wpos(c.up));
 const ankleChanged=ankleBefore.distanceTo(wpos(c.foot));
 const kneeQuatChanged=Math.max(upperQ.angleTo(c.up.quaternion),shinQ.angleTo(c.knee.quaternion));
 if(Math.max(kneeChanged,hipChanged,ankleChanged,kneeQuatChanged)>1e-6)
  throw Error('DISTAL_FOOT_STYLE_MUTATED_KNEE_IK_'+side+'_'+kneeChanged.toExponential(2));
 maxDistalKneeDelta=Math.max(maxDistalKneeDelta,kneeChanged);
 const currentKnee=wpos(c.knee);
 const signedKnee=(side==='left'?1:-1)*(currentKnee.x-hipCenterX);
 minSignedKneeCenterline=Math.min(minSignedKneeCenterline,signedKnee);
 maxKneeSourcePositionDelta=Math.max(maxKneeSourcePositionDelta,chosen.kneeSourceError);
 maxAnkleContactConflict=Math.max(maxAnkleContactConflict,chosen.unfulfilledContactDelta);
 if(chosen.baselineMismatch)sourceKneeBaselineMismatches++;
 if(priorWorldKnee[side])maxKneeWorldStep=Math.max(maxKneeWorldStep,currentKnee.distanceTo(V(...priorWorldKnee[side])));
 priorWorldKnee[side]=currentKnee.toArray(); // evidence only, never used by solver
 const actual=witnessWorld(c,t.planted?t.pivot:'ankle'),drift=actual.distanceTo(V(...t.witnessTarget));
 const ankle=wpos(c.foot),reference=V(...t.source.ankle).add(actor.position);
 if(t.planted){const g=sourceGaits[side],u=mod1(phase-g.start)/g.duty;
  if(u>.70){const actualRelative=ankle.z-wpos(c.up).z,sourceRelative=t.source.ankle[2]-t.source.hip[2];
   maxTrailingExtensionDeficit=Math.max(maxTrailingExtensionDeficit,Math.max(0,actualRelative-sourceRelative));}
  maxAnchorHeight=Math.max(maxAnchorHeight,t.badAnchorHeight||0);
 }
 const flex=kneeFlexion(c.upperLength,c.lowerLength,wpos(c.up).toArray(),ankle.toArray());
 const referenceFlex=kneeFlexion(c.upperLength,c.lowerLength,t.source.hip,t.source.ankle);
 if(Number.isFinite(flex)&&Number.isFinite(referenceFlex))
  maxKneeFlexDelta=Math.max(maxKneeFlexDelta,Math.abs(flex-referenceFlex));
 const shapeError=ankle.distanceTo(reference);shapeSum+=shapeError*shapeError;shapeCount++;
 if(t.planted){maxDrift=Math.max(maxDrift,drift);contactCount++}else swingCount++;
 const h=['heel','sole','toe'].map(k=>witnessWorld(c,k).y);
 maxPenetration=Math.max(maxPenetration,Math.max(0,...h.map(y=>-y)));
 maxIK=Math.max(maxIK,drift);
 drawPins[side].position.copy(V(...t.witnessTarget));drawPins[side].visible=$('showContacts').checked;
 drawPins[side].material.color.setHex(t.planted?0x65f2b7:0xffb65f);
 return {planted:t.planted,pivot:t.pivot,drift,sole:witnessWorld(c,'sole').toArray(),
  ankle:ankle.toArray(),target:t.ankleTarget,anchor:t.anchor,shapeError,reach:c.upperLength+c.lowerLength,
  kneeFlexionDeg:flex,sourceKneeFlexionDeg:referenceFlex,distalKneePositionChange:kneeChanged,
  sourceKneeError:chosen.kneeSourceError,contactConflict:chosen.unfulfilledContactDelta,
  kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch};
}
''')
once('maxKneeSourcePositionDelta=0;maxKneeWorldStep=0;kneeCenterlineCorrections=0;',
     'maxKneeSourcePositionDelta=0;maxKneeWorldStep=0;kneeCenterlineCorrections=0;maxAnkleContactConflict=0;sourceKneeBaselineMismatches=0;')
once('KNEE_CENTERLINE_CLEARANCE ${Number.isFinite(minSignedKneeCenterline)?minSignedKneeCenterline.toFixed(4):"pending"} u · centerline corrections ${kneeCenterlineCorrections} · max knee step ${maxKneeWorldStep.toFixed(4)} u · knee source delta ${maxKneeSourcePositionDelta.toFixed(4)} u',
    'SOURCE_KNEE_RESTORED clearance ${Number.isFinite(minSignedKneeCenterline)?minSignedKneeCenterline.toFixed(4):"pending"} u · source knee Δ ${maxKneeSourcePositionDelta.toFixed(4)} u · maximum contact conflict ${maxAnkleContactConflict.toFixed(4)} u · max step ${maxKneeWorldStep.toFixed(4)} u')
once('maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&maxKneeFlexDelta<6&&minSignedKneeCenterline>=.0179;',
    'maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&maxKneeFlexDelta<6&&minSignedKneeCenterline>=.012&&maxKneeSourcePositionDelta<=.025&&maxAnkleContactConflict<=.025&&sourceKneeBaselineMismatches===0;')
once("kneeCenterlineCorrections,kneeSourceAuthority:'60-frame Walking_Woman real knee witnesses',observations:samples};",
    "kneeCenterlineCorrections:0,kneeSourceAuthority:'stationary character-local anterior knee poles; stateless 60-frame source shape envelope',maxAnkleContactConflict,sourceKneeBaselineMismatches,observations:samples};")
s=s.replace('v0.1.19','v0.1.20').replace('V0.1.19','V0.1.20')
assert 'sourceKneePlane(' not in s
assert 'chooseSourceKnee(' in s and 'stableForwardPole(' in s and 'kneeFromTarget(' in s
assert 'distalHeading(side,footFit,pelvisProfile)' in s
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
p.write_text(s.rstrip()+'\n')
for name in ('index.html','review-server.py'):
 p=dest/name;t=p.read_text().replace('v0.1.19','v0.1.20').replace('V0.1.19','V0.1.20').replace('v0.1.19-source-knee-plane','v0.1.20-source-knee-recovery')
 p.write_text(t.rstrip()+'\n')
# Retire obsolete stateful solver from this NEW version only (old sources immutable).
for old in ('source-knee-plane.mjs','source-knee-plane-test.mjs'):
 f=dest/old
 if f.exists():f.unlink()
for f in dest.rglob('*'):
 if f.is_file() and f.suffix in ('.mjs','.py','.json','.md','.html','.sh'):
  f.write_bytes(f.read_bytes().rstrip(b'\r\n')+b'\n')
print('V020_FIXED_FORWARD_KNEE_POLES_PATCH_PASS approvedFootHeading=UNCHANGED kneePoleLateralSway=REMOVED')
V020_PATCH_FILE_END

cat > "$DEST_REL/contract.json" <<'V020_CONTRACT'
{
  "schema": "hareworks-v0.1.20-original-knee-pole-restoration",
  "repo": "Valar05/parametric-parambulator",
  "parent": "af2aed9e58c9679d841c7b954e3ebe368e52a183",
  "sourceController": "tools/hareworks-forward-woman/v0.1.19/viewer.mjs",
  "sourceControllerBlob": "0b3a884c2799059f04fd95bef1c11a089f2d1321",
  "sourceArchiveBlob": "f6e8940b5eaeaf154a126eaa5221dcfcab0d94d1",
  "sourceFootProfileBlob": "6febeaa8ff461806b590748dfca6461f4d8df1db",
  "canonicalModelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "rulesAGENTSBlob": "547c2af52303f4efb718bbf8f82a698110c7bfca",
  "rulesCampaignEtiquetteDoc": "1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI",
  "rulesTopdownDoc": "1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU",
  "executionLane": "Android Termux Git only",
  "mutablePaths": [
    "tools/hareworks-forward-woman/v0.1.20/"
  ],
  "ownerApproved": "stable pole projection far in front of model, original v0.1.9 knee resemblance, v0.1.18 foot headings, world movement, OrbitControls",
  "ownerRejected": "v0.1.19 severe knee wobble visible at 120 fps, history-dependent knee plane, hard centerline projection",
  "physicalMechanic": "stateless 2-bone fixed forward character-local knee poles; source knee geometry constrains world contact ankle target; no iterative sole-patch error feedback",
  "priorityWhenConflicting": "owner source-knee silhouette first, physical contact gate reports a warning rather than exaggerating the knee",
  "modelModified": false,
  "ownerVisualAcceptance": false
}
V020_CONTRACT

cat > "$DEST_REL/README.md" <<'V020_README'
# Hareworks v0.1.20: stationary forward knee poles, no history-dependent knee corrections

Owner's 120-fps v0.1.19 review is REJECTED: the knees remain unstable and the leg silhouette is noticeably worse. The previous 10-rad/s knee-pole filter and hard side-of-pelvis projection were inventions, not a faithful restoration of the accepted v0.1.9 motion. Remove both.

## Correction

- Use STATIONARY anterior (+Z) poles in character-local space, calibrated against the original 60-frame knee witnesses. No side-to-side pole animation. The solver is a pure function of phase and current hip/ankle, not previous frame, browser FPS or prior knee. The source knee shape is an independently enforced deviation envelope.
- Choose a world-contact ankle target by bounded binary search: accept the most planted-foot correction that keeps the solved knee within 0.025 units of the original source-knee shape and at least 0.012 units on its anatomical side. Do not iterate skin-patch residuals through the knee solver. When the source-style and ideal ground contact cannot both be met, keep the knee and mark the physical contact as a warning; NEVER call that a grounded success.
- Preserve the exact approved left/right `foot-heading.mjs` from v0.1.18, v0.1.19 source speed, OrbitControls and the canonical nine-clip GLB. No new animated source mixer on the visible actor.
- Instrument source-knee error, contact conflict, frame-to-frame knee movement and sole penetration. The actual phone browser 120Hz audit and owner review remain distinct gates. The 120-fps owner video is rejection evidence, not a source of inferred root metrics.

Only `tools/hareworks-forward-woman/v0.1.20/` is new. Do not edit assets, older iterations or another project. The authorized mutation lane is the checked existing Android Documents repository using Termux Git, with exact remote readback and no force push.
V020_README
# Model and immutable source file provenance before the test runner.
[ "$(git -C "$CHECKOUT" hash-object tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json)" = f6e8940b5eaeaf154a126eaa5221dcfcab0d94d1 ] || { echo 'BLOCKED_SOURCE_KNEE_REFERENCE_CHANGED' >&2;exit 77; }
[ "$(git -C "$CHECKOUT" hash-object tools/hareworks-forward-woman/v0.1.3/foot-profile.json)" = 6febeaa8ff461806b590748dfca6461f4d8df1db ] || { echo 'BLOCKED_SOURCE_LEG_LINKS_CHANGED' >&2;exit 77; }
# Foot heading stays byte-identical to the version the user accepted.
[ "$(git -C "$CHECKOUT" hash-object "$BUILDROOT/$DEST_REL/foot-heading.mjs")" = "$(git -C "$CHECKOUT" hash-object "$CHECKOUT/tools/hareworks-forward-woman/v0.1.18/foot-heading.mjs")" ] || { echo 'BLOCKED_APPROVED_FOOT_HEADING_CHANGED' >&2;exit 77; }
python3 "$DEST_REL/patch.py" "$CHECKOUT" "$DEST_REL"
STAGE='test-source-knee-restoration'
# v016 already patched using exact published v015 source
:
python3 - "$DEST_REL/patch.py" "$DEST_REL/review-server.py" "$DEST_REL/startup-regression.py" <<'PYPARSE'
import pathlib,sys
for p in sys.argv[1:]:compile(pathlib.Path(p).read_text(),p,'exec')
print('PYTHON_SYNTAX_PASS')
PYPARSE
for f in root-motion.mjs foot-gait.mjs root-model-test.mjs contact-test.mjs viewer.mjs shoe-witness.mjs shoe-witness-test.mjs archived-root-regression.mjs foot-heading.mjs foot-heading-test.mjs source-knee-governor.mjs source-knee-governor-test.mjs knee-source-invariant-test.mjs speed-gait.mjs;do
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
git commit -m 'Hareworks v0.1.20 restore original stateless knee movement and bound contact conflict'
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
 for f in viewer.mjs foot-gait.mjs root-motion.mjs source-knee-governor.mjs index.html;do
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
 'campaign':campaign,'status':'PERSISTENT_CHECKOUT_AND_V020_ORIGINAL_KNEE_RESTORATION_PUBLISHED_BROWSER_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sparseCheckout':False,
 'androidSharedStorageGitTrust':'exact-canonical-project-only, global safe.directory',
 'lfsStatusGuard':'Git LFS filters configured locally; only exactly SHA-verified tracked Hareworks binary is admissible as unstaged model materialization',
 'lfsStatusGuardDoesNotHideChanges':True,
 'previousIncompleteGitInitRecovered':recovered=='1',
 'acceptedV020Math':'v0.1.9 original ankle/pelvis plus 60-frame real-source knee plane restored; distal foot yaw unchanged; physical centerline guard runs every frame; real browser audit pending',
 'shoeWitnesses':'v0.1.14 whole skinned foot low-surface longitudinal PCA bands, preserved unchanged',
 'calibrationFailureBehavior':'source procedural preview moving but explicitly UNPINNED and unapproved',
 'camera':'orbit and zoom with world-target follow',
 'unrelatedReplLfsFetched':False,'hareworksCopyPolicy':'exactly one verified worktree model, reusable private LFS cache',
 'rulesReadInAuthoringTurn':{'AGENTSBlob':agents,'CampaignEtiquetteDocument':etiquette,'TopDownEtiquetteDocument':topdown},
 'viewerUrl':url,'viewerPid':int(pid),'viewerPort':int(port),'viewerGaitSha256':viewer_hash,
 'alreadyPublishedRerun':reused=='1','browserRealSkinnedFootAudit':'PENDING; startup preview mode is not a physics audit',
 'actualSkinned3dPhysicsTestedInTermux':False,
 'contactGate':'PENDING_BROWSER_AUDIT; knee preservation may limit stance contact; WARN is not PASS','gaitResemblanceGate':'PENDING_OWNER_VISUAL_ACCEPTANCE; diagnostic preview expressly NOT acceptable as physical ground pinning',
 'ownerVisualAcceptance':False,'canonicalModelUnchanged':True}
p=pathlib.Path(state)/'latest-receipt.json'
p.write_text(json.dumps(receipt,indent=2)+'\n')
print('RECEIPT='+str(p))
PYRECEIPT
STAGE='review-ready-owner-verdict-pending'
echo "CHECKOUT_READY=$CHECKOUT"
echo 'NORMAL_GIT_CHECKOUT=YES'
echo "SOURCE_KNEE_RESTORED_GAIT_ROOT=$CHECKOUT/$DEST_REL"
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
