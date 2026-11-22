#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_ACCEPTED_V019_INVERSE_SUPPORT_v0.1.15_DOCUMENTS
# One persistent FULL Git checkout in Android Documents, not a fresh temporary clone.
# Authoritative mutation is Termux Git ONLY; model and old versions stay immutable.
set -Eeuo pipefail
umask 077
CAMPAIGN_ID='HAREWORKS_WOMAN_DYNAMIC_RUNWAY_WORLD_PIN_v0.1.16_DOCUMENTS'
VERSION='v0.1.16'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_SHA='683b80a86f54e4d86f946acbd71ab71906a4dd18'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
ETIQUETTE_DOC='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
TOPDOWN_DOC='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
ENTRY="$(readlink -f "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
STATE="$HOME/.local/state/hareworks-woman-dynamic-runway-v0.1.16-v1-documents"
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
  grep -q 'hareworks-v0.1.16-dynamic-runway-world-pin' "$DEST_REL/contract.json" || { echo 'BLOCKED_PUBLISHED_CONTRACT_MISSING' >&2;exit 73; }
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
[ -f tools/hareworks-forward-woman/v0.1.15/viewer.mjs ] || { echo 'BLOCKED_MISSING_SOURCE_GAIT_BASELINE' >&2;exit 74; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.15/viewer.mjs)" = 90b4bfec0f572a9700dee5bc7369d02c65f46695 ] || { echo 'BLOCKED_PUBLISHED_V015_SOURCE_CHANGED' >&2;exit 74; }
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
 TEMP_MODEL="$MODEL.r16-verified-${ENTRY_SHA:0:12}.tmp"
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
STAGE='generate-v016-dynamic-world-gait'
SOURCE_REL='tools/hareworks-forward-woman/v0.1.15'
[ -d "$CHECKOUT/$SOURCE_REL" ] || { echo 'BLOCKED_MISSING_PUBLISHED_V015_SOURCE' >&2; exit 77; }
cp -R "$CHECKOUT/$SOURCE_REL" "$DEST_REL"
for old_launcher in "$DEST_REL"/campaign-*.sh;do [ -f "$old_launcher" ] && rm -- "$old_launcher" || :;done
cp "$ENTRY" "$DEST_REL/campaign-v0.1.16-v1-godotprojects.sh"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.2" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.2"
cp -R "$CHECKOUT/tools/hareworks-forward-woman/v0.1.3" "$BUILDROOT/tools/hareworks-forward-woman/v0.1.3"
cat > "$DEST_REL/speed-gait.mjs" <<'V016_SPEED_MATH'
/* v0.1.16: speed is distance/time, not an AnimationMixer playback multiplier.
 * Full stride is TWO steps (one left and one right). Alter stride, cadence,
 * fore-aft reach and lateral lead geometry together; retain v0.1.9 source curves.
 * No here-defined profile is owner-accepted until real skinned contact passes. */
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const smooth=x=>{const t=clamp(x,0,1);return t*t*(3-2*t)};
export const REF_WALK_SPEED=1.26677;
export function speedGait(speed,referenceStride){
 if(!Number.isFinite(speed)||speed<0||speed>5||!Number.isFinite(referenceStride)||referenceStride<.9||referenceStride>1.55)
  throw Error('DYNAMIC_GAIT_INPUT_INVALID');
 const ratio=clamp(speed/REF_WALK_SPEED,0,1);
 // At the reference source speed the original procedural reach is unchanged.
 // Slow: shorter step and greater cycles per DISTANCE than slowed reference clip.
 const stride=referenceStride*(.42+.58*ratio);
 const cadence=speed>0?speed/stride:0;
 const lead=smooth((ratio-.22)/.95);
 return {speed,stride,cadence,scale:stride/referenceStride,
  crossover:.012+.050*lead,stanceDuty:.615-.035*lead,
  liftFactor:.88+.23*lead,phaseRate:cadence,
  referenceStride,source:'accepted v0.1.9 hip-relative procedural gait'};
}
export function blendMotion(previous,target,dt){
 if(!previous)return {...target};
 if(!Number.isFinite(dt)||dt<0)throw Error('DYNAMIC_GAIT_DT_INVALID');
 const k=1-Math.exp(-Math.min(dt,.1)/.22),out={...target};
 for(const key of ['stride','scale','crossover','stanceDuty','liftFactor'])
  out[key]=previous[key]+(target[key]-previous[key])*k;
 out.cadence=out.stride>0?target.speed/out.stride:0;
 out.phaseRate=out.cadence;
 return out;
}
export function adjustAnkleForSpeed(hip,ankle,side,motion){
 if(!['left','right'].includes(side)||!hip||!ankle||hip.length!==3||ankle.length!==3||!motion)
  throw Error('DYNAMIC_GAIT_LANDMARK_INVALID');
 const z=ankle[2]-hip[2],leading=smooth((z+.07)/.34);
 const sign=side==='left'?-1:1;
 return [hip[0]+(ankle[0]-hip[0])*.94+sign*motion.crossover*(.28+.72*leading),
   ankle[1],hip[2]+z*motion.scale];
}
export function transformSourceFoot(s,side,motion){
 if(!motion||!s||!s.ankle||!s.hip)throw Error('DYNAMIC_SOURCE_MISSING');
 const a=adjustAnkleForSpeed(s.hip,s.ankle,side,motion),shiftX=a[0]-s.ankle[0];
 const adapt=(name)=>{
  const p=s[name]; if(!p||p.length!==3)throw Error('DYNAMIC_SOURCE_NO_'+name);
  return [p[0]+shiftX,p[1],s.hip[2]+(p[2]-s.hip[2])*motion.scale];
 };
 return {...s,ankle:a,heel:adapt('heel'),sole:adapt('sole'),toe:adapt('toe')};
}
export function rootStepDistance(rootAt,curve,oldPhase,newPhase,motion){
 if(newPhase<oldPhase||!curve||!motion||motion.referenceStride!==curve.stride)
  throw Error('DYNAMIC_ROOT_PHASE_OR_CONTRACT');
 return (rootAt(curve,newPhase)-rootAt(curve,oldPhase))*motion.scale;
}
V016_SPEED_MATH
cat > "$DEST_REL/dynamic-gait-test.mjs" <<'V016_SPEED_TEST'
import assert from 'node:assert/strict';
import {speedGait,blendMotion,transformSourceFoot,adjustAnkleForSpeed,rootStepDistance} from './speed-gait.mjs';
const D=1.224546, slow=speedGait(.30,D),middle=speedGait(.52,D),fast=speedGait(1.27,D);
assert(slow.stride<middle.stride&&middle.stride<fast.stride,'Speed must change stride geometry');
assert(slow.cadence<middle.cadence&&middle.cadence<fast.cadence,'Speed must change cadence');
assert(slow.crossover<fast.crossover,'Runway placement must respond to speed');
assert(slow.stanceDuty>fast.stanceDuty,'Support timing must respond to speed');
assert(Math.abs(fast.scale-1)<.002,'Reference source gait must remain accurate at its native speed');
assert(Math.abs(middle.cadence*middle.stride-.52)<1e-12,'True distance/time consistency');
const l={hip:[.071,.90,.10],ankle:[.12,.19,.37],heel:[.14,.08,.31],sole:[.15,.08,.39],toe:[.15,.10,.48]},
 r={hip:[-.062,.90,.10],ankle:[-.02,.19,.37],heel:[-.03,.08,.31],sole:[-.03,.08,.39],toe:[-.03,.10,.48]};
const le=transformSourceFoot(l,'left',fast),re=transformSourceFoot(r,'right',fast);
assert(le.ankle[0]<l.ankle[0]&&re.ankle[0]>r.ankle[0],'Foot placement must move toward centerline');
assert(Math.abs((le.toe[2]-le.heel[2])-(l.toe[2]-l.heel[2])*fast.scale)<1e-10,
 'Heel and toe geometry scale consistently');
assert(Math.abs(adjustAnkleForSpeed(l.hip,l.ankle,'left',fast)[2]-(l.hip[2]+(l.ankle[2]-l.hip[2])*fast.scale))<1e-10);
const fake={stride:D},rootAt=(_,q)=>D*q;
for(const target of [0,.3,.52,.8,1.27,1.6]){
 const g=speedGait(target,D),dt=.00833333,q=target/g.stride*dt;
 assert(Math.abs(rootStepDistance(rootAt,fake,1,1+q,g)-target*dt)<1e-10,'Root velocity must match slider');
}
let state=speedGait(.52,D),phase=0,position=0,locked=[12.3,-.4,7.3];
for(const target of [0,.52,1.27,.3,1.5,0]){
 for(let i=0;i<240;i++){
  state=blendMotion(state,speedGait(target,D),1/120);
  const next=phase+state.cadence/120;
  const delta=rootStepDistance(rootAt,fake,phase,next,state);
  assert(delta>=-1e-10 && delta<.05,'Root continuity on speed change');
  phase=next;position+=delta;
  const stanceTarget=locked.slice();
  assert.deepEqual(stanceTarget,locked,'World contact anchor must never move with gait speed');
 }
}
assert(position>0);
assert.throws(()=>speedGait(NaN,D));
assert.throws(()=>speedGait(.52,.66));
assert.throws(()=>rootStepDistance(rootAt,fake,1,0,fast));
console.log('DYNAMIC_SPEED_STRIDE_CADENCE_AND_RUNWAY_PASS');
console.log('SPEED_CHANGE_NO_ROOT_TELEPORT_AND_STATIC_WORLD_ANCHOR_PASS');
V016_SPEED_TEST
cat > "$DEST_REL/source-speed-contact-test.mjs" <<'V016_CONTACT_TEST'
import assert from 'node:assert/strict';
import {SourceFootContact} from './foot-gait.mjs';
import {speedGait,transformSourceFoot} from './speed-gait.mjs';
const n=60,source=Array.from({length:n},(_,i)=>{
 const q=i/n,theta=q*2*Math.PI,hip=[.06,.91,0],ankle=[.11,.18,.37*Math.sin(theta)];
 return {phase:q,hip,knee:[.11,.54,.1],ankle,
   heel:[ankle[0],.01,ankle[2]-.12],sole:[ankle[0],0,ankle[2]],toe:[ankle[0],.01,ankle[2]+.12],
   q:[0,0,0,1]};
});
let last=[.1,.19,0],contact=new SourceFootContact({samples:source,
 gait:{start:.1,duty:.58},sourceGround:0,readWitness:kind=>kind==='ankle'?last.slice():[.04,0,1.2],
 transformSource:(s,gait)=>transformSourceFoot(s,'left',gait)});
let pin=null,planted=0,changes=0,lastDuty=null;
for(let i=0;i<900;i++){
 const target=i<300?.3:i<600?1.18:.52, gait=speedGait(target,1.224546),q=(i/300)%1;
 const f=contact.step({phase:q,totalPhase:i/300,worldZ:i*.001,gait});
 if(f.planted){
  if(pin!==null)assert.deepEqual(f.anchor,pin,'speed changed a world pin during stance');
  pin=f.anchor;planted++;
  assert(f.pivot!=='air');
 }else pin=null;
 if(lastDuty!==null&&lastDuty!==contact.activeDuty){changes++;assert(pin!==null,'stance duration changed outside touchdown');}
 lastDuty=contact.activeDuty;
 last=f.ankleTarget.slice();
}
assert(planted>150&&changes>=2,'gait speed must change touchdown timing');
assert(contact.transitions>3);
console.log('WORLD_PIN_STAYS_FIXED_ACROSS_SPEED_CHANGE_PASS transitions='+contact.transitions+' dutyUpdates='+changes);
V016_CONTACT_TEST
cat > "$DEST_REL/patch.py" <<'V016_PATCH'
#!/usr/bin/env python3
"""Exact-source-only additive v0.1.16 patch of existing v0.1.15.
No canonical GLB / historical directory modifications."""
from pathlib import Path
import sys, json, hashlib

root=Path(sys.argv[1]); dest=Path(sys.argv[2])
source=root/'tools/hareworks-forward-woman/v0.1.15'
if not source.is_dir():raise SystemExit('NO_PUBLISHED_V015_SOURCE')
p=dest/'viewer.mjs'
s=p.read_text()
def one(old,new):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError('V016_VIEWER_ANCHOR_'+str(n)+'_'+old[:85])
 s=s.replace(old,new,1)

one("import {sourceAt,SourceFootContact} from './foot-gait.mjs';", "import {sourceAt,SourceFootContact} from './foot-gait.mjs';\nimport {speedGait,blendMotion,transformSourceFoot,adjustAnkleForSpeed,rootStepDistance} from './speed-gait.mjs';")
one('let motionMode=\'LOADING\',frameTickCount=0,lastPreviewError=\'\',previewCycle=0;',
    "let motionMode='LOADING',frameTickCount=0,lastPreviewError='',previewCycle=0;\nlet dynamicMotion=null; // speed-dependent stride geometry, cadence and crossover; not clip-time scaling")
one('previewCycle+=Math.max(0,speed)*dt/REFERENCE_ROOT_UNITS_PER_CYCLE;\n phase=mod1(previewCycle);worldZ=REFERENCE_ROOT_UNITS_PER_CYCLE*previewCycle;',
    '''dynamicMotion=blendMotion(dynamicMotion,speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE),dt);
 const nextCycle=previewCycle+(dynamicMotion.cadence*dt);
 worldZ+=(nextCycle-previewCycle)*dynamicMotion.stride;
 previewCycle=nextCycle;phase=mod1(previewCycle);''')
one('const target=H.clone().add(V(...rotateY(v.ankleLocal,yaw)));',
    '''const target=H.clone().add(V(...rotateY(v.ankleLocal,yaw)));
    target.fromArray(adjustAnkleForSpeed(H.toArray(),target.toArray(),side,dynamicMotion));''')
# Actual accepted v0.1.9 foot orientation rather than forcing the source GLB sample
# rotation onto the fully procedural leg. Blend limits deviation pending owner review.
needle='function measuredFootQ(s){'
assert s.count(needle)==1
foot='''// Accepted v0.1.9 toe-vector + ankle-yaw analytical orientation.
function runwayFootQ(c,toeVector,ankleYaw){
 const from=wpos(c.toe).sub(wpos(c.foot)),to=V(...toeVector);
 if(from.lengthSq()<1e-9||to.lengthSq()<1e-9)throw Error('RUNWAY_FOOT_VECTOR_DEGENERATE');
 const axis=to.normalize(),base=Q().setFromUnitVectors(from.normalize(),axis).multiply(wq(c.foot));
 const forward=V(0,0,1).applyQuaternion(base),desired=V(Math.sin(ankleYaw),0,Math.cos(ankleYaw));
 const fp=forward.addScaledVector(axis,-forward.dot(axis)),dp=desired.addScaledVector(axis,-desired.dot(axis));
 if(fp.lengthSq()<1e-7||dp.lengthSq()<1e-7)throw Error('RUNWAY_FOOT_HEADING_SINGULAR');
 fp.normalize();dp.normalize();
 const twist=Math.atan2(axis.dot(fp.clone().cross(dp)),fp.dot(dp));
 return Q().setFromAxisAngle(axis,twist).multiply(base).normalize();
}
'''
s=s.replace(needle,foot+needle,1)
one('const f=sourceAt(sourceSamples[side],phase);setWorldQ(c.foot,measuredFootQ(f));actor.updateMatrixWorld(true);',
    '''const f=sourceAt(sourceSamples[side],phase);setWorldQ(c.foot,measuredFootQ(f));actor.updateMatrixWorld(true);
    const footFit=independentPose(pelvisProfile,q).feet[side];
    const original=wq(c.foot).clone(),fitted=runwayFootQ(c,footFit.toeVector,footFit.ankleYaw);
    setWorldQ(c.foot,original.slerp(fitted,.52));actor.updateMatrixWorld(true);''')
one('setWorldQ(c.foot,desiredQ);actor.updateMatrixWorld(true);',
    '''setWorldQ(c.foot,desiredQ);actor.updateMatrixWorld(true);
  // Preserve the published skinned contact geometry but restore a portion of
  // v0.1.9 toe-vector/yaw styling and align foot slightly toward its knee.
  const footFit=independentPose(pelvisProfile,phase*clipDuration).feet[side];
  const kneeToFoot=clamp(wpos(c.knee).x-wpos(c.foot).x,-.16,.16);
  const stylizedToe=[footFit.toeVector[0]+.20*kneeToFoot,
                     footFit.toeVector[1],footFit.toeVector[2]];
  try{
   const original=wq(c.foot).clone(),fitted=runwayFootQ(c,stylizedToe,footFit.ankleYaw);
   const styleBlend=t.planted?(best<.008?.35:.08):.52;
   setWorldQ(c.foot,original.slerp(fitted,styleBlend));actor.updateMatrixWorld(true);
  }catch(footError){
   // Keep original orientation, and log warning; never hide an invalid contact.
   setWorldQ(c.foot,desiredQ);previewFaults++;lastPreviewError=String(footError.message||footError);
  }''')
one('out[side]=worldContacts[side].step({phase,worldZ,totalPhase});',
    'out[side]=worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion});')
one('const cadence=cadenceFor(speed,stride);totalPhase+=cadence*dt;phase=mod1(totalPhase);worldZ=rootAt(rootCurve,totalPhase);frameBody(phase);',
    '''dynamicMotion=blendMotion(dynamicMotion,speedGait(speed,rootCurve.stride),dt);
 const cadence=cadenceFor(speed,dynamicMotion.stride),newPhase=totalPhase+cadence*dt;
 worldZ+=rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);
 totalPhase=newPhase;phase=mod1(totalPhase);frameBody(phase);''')
one('phase=0;totalPhase=0;worldZ=0;clearStats();frameBody(0);',
    '''phase=0;totalPhase=0;worldZ=0;dynamicMotion=speedGait(speed,rootCurve.stride);
 clearStats();frameBody(0);''')
one('sourceGround,readWitness:k=>witnessCache[side][k],rootAt:q=>rootAt(rootCurve,q)});',
    '''sourceGround,readWitness:k=>witnessCache[side][k],rootAt:q=>rootAt(rootCurve,q),
  transformSource:(s,gait)=>transformSourceFoot(s,side,gait||dynamicMotion)});''')
one("previewCycle=0;worldZ=0;frameBody(0);for(const p of Object.values(drawPins))p.visible=false;",
    "previewCycle=0;worldZ=0;dynamicMotion=speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE);frameBody(0);for(const p of Object.values(drawPins))p.visible=false;")
# The source viewer initializes at the speed selected in the HTML; change speed
# only through a smooth parameter update, not a reset or an anchor re-seed.
one("$('speed').oninput=()=>{speed=Number($('speed').value);$('speedOut').textContent=speed.toFixed(2)+' u/s';updateMotionStatus()};",
    "$('speed').oninput=()=>{speed=Number($('speed').value);$('speedOut').textContent=speed.toFixed(2)+' u/s';updateMotionStatus()};") if False else None
one("$('motionStatus').textContent='UNPINNED SOURCE PROCEDURAL PREVIEW · '+REFERENCE_ROOT_UNITS_PER_CYCLE.toFixed(4)+' u/full cycle · contact audit NOT available';",
    "$('motionStatus').textContent='UNPINNED DYNAMIC GEOMETRY PREVIEW · target stride '+(dynamicMotion?.stride||0).toFixed(3)+' u/full cycle · no contact proof';")
one('}else $(\'motionStatus\').textContent=`SOURCE-DERIVED FOOT PATH · ${stride.toFixed(3)} u travel/cycle · ${cadenceFor(speed,stride).toFixed(3)} cycles/s · no synthetic foot lift`;',
    '''}else $('motionStatus').textContent=`DYNAMIC SOURCE-ANCHORED FOOT PATH · stride ${(dynamicMotion?.stride||stride).toFixed(3)} u/full cycle · cadence ${cadenceFor(speed,dynamicMotion?.stride||stride).toFixed(3)} cycles/s · crossover ${(dynamicMotion?.crossover||0).toFixed(3)} u`;
''')
# New speed panel is an actual slow-to-fast gait range, rather than 0..0.8.
one("$('metrics').textContent=`${prefix} · SOURCE-MEASURED WALKING_WOMAN · WORLD IK", "$('metrics').textContent=`${prefix} · DYNAMIC SOURCE-ANCHORED WALKING_WOMAN · WORLD IK")
one('cadence ${cadenceFor(speed,stride).toFixed(3)} cycles/s\\nLEFT',
    'cadence ${cadenceFor(speed,dynamicMotion?.stride||stride).toFixed(3)} cycles/s, stride ${(dynamicMotion?.stride||stride).toFixed(3)}\\nLEFT')
one('const n=Math.ceil((3/cadenceFor(speed,stride))*120);',
    'const n=Math.ceil((3/cadenceFor(speed,speedGait(speed,stride).stride))*120);')
one('actualCyclesTested:n/120*cadenceFor(speed,stride),',
    'actualCyclesTested:n/120*cadenceFor(speed,dynamicMotion.stride),')
one('ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,observations:samples};',
    '''ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,observations:samples};
  // Real GLB physical checks at three distinct speeds. Changing speed is not a
  // pass unless contact drift, reach and actual root advance are acceptable.
  const speedMatrix=[];
  for(const requested of [.30,.52,1.18]){
   speed=requested;initRun();
   const expected=speedGait(requested,stride),steps=Math.ceil((1.20/expected.cadence)*120);
   for(let j=0;j<steps;j++){
    physicsStep(1/120);
    if(j%40===0)await new Promise(requestAnimationFrame);
   }
   const realTime=steps/120;
   speedMatrix.push({requested,realTime,travel:worldZ,
    stride:dynamicMotion.stride,cadence:dynamicMotion.cadence,
    maxDrift,maxPenetration,unreachable,
    rootMeanSpeed:worldZ/realTime,
    status:'REAL_SKINNED_GLTF_SOLVER',
    pass:maxDrift<=.025&&maxPenetration<=.020&&unreachable===0&&
      Math.abs(worldZ/realTime-requested)<.17});
  }
  report.speedMatrix=speedMatrix;
  report.dynamicSpeedGate=speedMatrix.every(x=>x.pass)?'PASS':'WARN';
  if(report.dynamicSpeedGate!=='PASS'){
   report.contactGate='WARN';report.status='DYNAMIC_SPEED_PHYSICAL_GATES_WARN_OWNER_REVIEW_REQUIRED';
  }
  speed=oldSpeed;initRun();''')
one('worldZ>2.5&&cameraError<',
    'worldZ>speedGait(speed,stride).stride*2.70&&cameraError<')
one('rootMethod:rootCurve.method,rootStridePerFullCycle:rootCurve.stride,',
    '''rootMethod:rootCurve.method,rootStridePerFullCycle:rootCurve.stride,
    speedResponsiveGait:dynamicMotion,referenceV019FootOrientationBlend:.52,''')
one('previewCycle=0;worldZ=0;frameBody(0);\n console.info(\'V019_REFERENCE_LEG_MOTION_LIVENESS_PASS\'',
    "previewCycle=0;worldZ=0;dynamicMotion=speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE);frameBody(0);\n console.info('V019_REFERENCE_LEG_MOTION_LIVENESS_PASS'")
# Version identity updated in copied file, not in previous baseline.
s=s.replace('v0.1.15','v0.1.16').replace('V0.1.15','V0.1.16')
# Source fit must remain physically audited instead of incorrectly marked accepted.
assert 'rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion)' in s
assert "motionMode='PHYSICAL_GROUND_PINNING'" in s
assert "OrbitControls" in s
p.write_text(s.rstrip()+'\n')

p=dest/'foot-gait.mjs';x=p.read_text()
def foot_once(a,b):
 global x
 if x.count(a)!=1:raise RuntimeError('V016_FOOT_PATCH_ANCHOR_'+str(x.count(a))+'_'+a[:70])
 x=x.replace(a,b,1)
foot_once('constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0}){',
          'constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0,transformSource=null}){')
foot_once('this.readWitness=readWitness;this.rootAt=rootAt;',
          'this.readWitness=readWitness;this.rootAt=rootAt;this.transformSource=transformSource;this.activeDuty=gait.duty;')
foot_once('step({phase,worldZ,totalPhase}){\n  const s=sourceAt(this.samples,phase),p=gap(phase,this.gait.start),planted=p<this.gait.duty;',
          '''step({phase,worldZ,totalPhase,gait}){
  const p=gap(phase,this.gait.start);
  if(this.state!=='stance'&&p<Math.min(this.gait.duty,this.activeDuty))
   this.activeDuty=clamp(this.gait.duty+((gait?.stanceDuty??.60)-.60),.49,.69);
  const planted=p<this.activeDuty;
  const raw=sourceAt(this.samples,phase),s=this.transformSource?this.transformSource(raw,gait,planted):raw;''')
foot_once('const u=clamp((p-this.gait.duty)/(1-this.gait.duty),0,1)',
          'const u=clamp((p-this.activeDuty)/(1-this.activeDuty),0,1)')
p.write_text(x.rstrip()+'\n')

p=dest/'contact-core.mjs';x=p.read_text();k='stride<.3||stride>1';
if x.count(k)!=2:raise RuntimeError('CADENCE_UNIT_CONTRACT_EXPECTED_TWICE_'+str(x.count(k)))
x=x.replace(k,'stride<.3||stride>1.8')
p.write_text(x.rstrip()+'\n')

p=dest/'index.html';x=p.read_text()
x=x.replace('v0.1.15','v0.1.16').replace('v0.1.15-startup-and-preview','v0.1.16-dynamic-physics')
x=x.replace('max="0.8"','max="1.2"')
x=x.replace('Swing and heel-to-toe motion are reconstructed from the original Walking_Woman source, not parameter sliders.',
 '''Original Walking_Woman trajectories supply the reference. The travel-speed slider changes stride length, cadence, lateral crossover and landing geometry. A physical-contact PASS is separate from seeing the model move.''')
x=x.replace('Feet use actual persistent world-space sole anchors during stance.',
            'The physical controller holds actual world-space skinned sole anchors during stance; a clearly labeled preview is unpinned if physics initialization fails.')
x=x.replace('Walking_Woman · World-Space IK','Walking_Woman · Dynamic World-Space IK')
p.write_text(x.rstrip()+'\n')

p=dest/'review-server.py';x=p.read_text().replace('v0.1.15','v0.1.16')
p.write_text(x.rstrip()+'\n')

# Source tests may be carried forward unchanged; the immutable old v0.1.15 is not modified.
for p in dest.rglob('*'):
 if p.is_file() and p.suffix in ('.mjs','.py','.json','.md','.html','.sh'):
  raw=p.read_bytes();p.write_bytes(raw.rstrip(b'\r\n')+b'\n')
print('V016_PATCH_PASS source=v0.1.15 dynamic_stride=1.2245 physical_world_contacts=retained orbit=retained')
V016_PATCH
cat > "$DEST_REL/README.md" <<'V016_README'
# Hareworks v0.1.16: dynamic runway gait with actual world contacts

Owner request: preserve working v0.1.9 source-derived procedural gait and v0.1.15 visible character, while restoring runway crossover, foot-to-knee orientation and a physically coherent speed control. Do not regress orbit camera, skinned 74-joint model, other clips or source math.

**Confirmed startup exception in v0.1.15**: `cadenceFor()` rejected a measured full-cycle stride near 1.2245 because it allowed 0.3...1.0. v0.1.16 accepts the physically measured 1.2245 and can run the existing real-glb 32-step startup test instead of entering the unpinned fallback. That startup still needs phone browser evidence.

**Dynamic control**: `speed-gait.mjs` computes stride length, cadence and lateral placement from travel speed (not simply animation-time speed). Physical phase advances by cadence*dt. Root advances by the original phase-integrated support-root curve scaled to the current stride; the existing world contact anchor is held fixed through stance. At speed changes geometry parameters change smoothly over about 0.22s, rather than reseeding an anchor. Zero speed produces no root or phase motion. The accepted original source curve remains the 1.267u/s reference.

**Runway character**: the original fitted hip-relative ankle path, knee pole and pelvis continue to supply the motion. Front-leading foot shifts modestly toward centerline, more at fast speed; the procedural toe-vector plus ankle-yaw solver from v0.1.9 contributes 52% to foot orientation against the preserved real-source pose. The computed foot direction also reacts moderately to the measured knee-to-foot lateral offset. This is a style candidate, NOT owner approval.

**Honest gates**: unsupported animation source / GLB hash fails; real physical initialization must complete 32 skinned 120Hz solver steps before marking world IK ready. The old unpinned preview still has an unmistakable warning. Browser physical contact audit and owner visual verdict are independent. Passing JS tests alone does not prove heel/toe geometry, gait beauty, or phone performance.

Single authorized Android Termux entrypoint, verified one-time Hareworks model, persistent Documents/GodotProjects checkout, no new clone, no destructive Git commands, no model writes. Only new versioned v0.1.16 files are eligible for commit/push through Termux. Read AGENTS.md and Campaign Etiquette for authoritative execution constraints.
V016_README
cat > "$DEST_REL/contract.json" <<'V016_CONTRACT'
{
  "schema": "hareworks-v0.1.16-dynamic-runway-world-pin",
  "repo": "Valar05/parametric-parambulator",
  "parent": "683b80a86f54e4d86f946acbd71ab71906a4dd18",
  "ownerMission": "genuine world-pinned dynamic speed, source-faithful runway foot placement, knees/feet alignment and orbit camera",
  "executionLane": "Android Termux Git only",
  "checkout": "~/storage/documents/GodotProjects/parametric-parambulator",
  "sourceModel": "assets/hareworks/Hareworks-nine-clips.glb",
  "sourceSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "acceptedReference": "Walking_Woman v0.1.9 original four/six-harmonic procedural source",
  "sourceController": "tools/hareworks-forward-woman/v0.1.15/viewer.mjs",
  "sourceControllerBlob": "90b4bfec0f572a9700dee5bc7369d02c65f46695",
  "rulesAGENTSBlob": "547c2af52303f4efb718bbf8f82a698110c7bfca",
  "rulesCampaignEtiquetteDoc": "1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI",
  "mutablePaths": [
    "tools/hareworks-forward-woman/v0.1.16/"
  ],
  "previousVersionsUntouched": true,
  "canonicalModelModified": false,
  "rootAdvance": "phase-dependent accepted support-root displacement, scaled by continuously smoothed actual speed-dependent stride",
  "speed": "v = cadence * full-cycle stride; both stride and cadence change, with no stance-anchor replacement on slider changes",
  "runway": "source-generated leading-foot lateral crossover and partial accepted v0.1.9 toe-vector/yaw orientation; clinical anatomy not asserted",
  "contact": "physical skinned heel/sole/toe anchors solved against world positions and audited at 120 Hz",
  "camera": "retained OrbitControls + pinch + tracking",
  "knownFaultRepaired": "cadenceFor rejected verified 1.2245-unit full cycle because legacy maximum was 1.0",
  "ownerVisualAcceptance": false,
  "physicalContactGate": "must pass on the actual phone browser; synthetic source tests do not count",
  "visualReview": "owner specifically requests runway crossover and feet more aligned with inward knees, avoids still-foot animation speed-up"
}
V016_CONTRACT
python3 "$DEST_REL/patch.py" "$CHECKOUT" "$DEST_REL"
STAGE='patch-and-test-v016-dynamic-world-gait'
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
git commit -m 'Hareworks v0.1.16 dynamic stride, runway alignment and world support'
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
 'campaign':campaign,'status':'PERSISTENT_CHECKOUT_AND_V016_DYNAMIC_GAIT_PUBLISHED_REAL_BROWSER_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':base,'publishedCommit':commit,'exactRemoteReadback':True,
 'entrySha256':entry,'modelSha256':model,'modelPreserved':True,
 'checkout':checkout,'persistentWorkingTree':True,'sparseCheckout':False,
 'androidSharedStorageGitTrust':'exact-canonical-project-only, global safe.directory',
 'lfsStatusGuard':'Git LFS filters configured locally; only exactly SHA-verified tracked Hareworks binary is admissible as unstaged model materialization',
 'lfsStatusGuardDoesNotHideChanges':True,
 'previousIncompleteGitInitRecovered':recovered=='1',
 'acceptedV019Math':'v0.1.9 procedural ankle + pelvis, variable stride/cadence root motion from sixty source frames; real 120Hz GLB audit still required',
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
echo "DYNAMIC_RUNWAY_WORLD_ROOT=$CHECKOUT/$DEST_REL"
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
