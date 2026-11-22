#!/data/data/com.termux/files/usr/bin/bash
# HAREWORKS_WOMAN_v0.1.15_r2_WHITESPACE_PUBLICATION_RECOVERY
# Resume ONLY the verified 20-file, already-staged v0.1.15 campaign in
# the owner's ordinary Android Documents Git checkout. No gait regeneration.
set -Eeuo pipefail
umask 077
CAMPAIGN='HAREWORKS_WOMAN_v0.1.15_r2_STAGED_PUBLICATION_RECOVERY'
BASE='7a3690fa99c52f70636fa49be851e521a793838c'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_SIZE=6784896
AGENTS_SHA='547c2af52303f4efb718bbf8f82a698110c7bfca'
RULES_CAMPAIGN='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
RULES_TOPDOWN='1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU'
DEST='tools/hareworks-forward-woman/v0.1.15'
ORIGINAL='campaign-v0.1.15-v1-godotprojects.sh'
ORIGINAL_SHA='e7d425be3b6c8ad67f31b95b165dabb304955c8d8000642fd1628cc028f2c374'
OWN='campaign-v0.1.15-r2-whitespace-publication-recovery.sh'
ENTRY="$(readlink -f -- "${BASH_SOURCE[0]}")"
ENTRY_SHA="$(sha256sum "$ENTRY" | awk '{print $1}')"
CHECKOUT="$HOME/storage/documents/GodotProjects/parametric-parambulator"
STATE="$HOME/.local/state/hareworks-woman-v0.1.15-r2-publication-recovery"
mkdir -p "$STATE"
STAGE=preflight
NEW_SHA=''
EXIT_STATE=BLOCKED
on_exit(){
  local rc=$?
  if [ "$rc" -ne 0 ]; then
    python3 - "$STATE" "$CAMPAIGN" "$STAGE" "$rc" "$ENTRY_SHA" "$BASE" "$MODEL_SHA" "$NEW_SHA" <<'PYFAIL' || true
import json,pathlib,sys,datetime
state,campaign,stage,rc,entry,base,model,commit=sys.argv[1:]
p=pathlib.Path(state)/'last-failure.json'
p.write_text(json.dumps({'campaign':campaign,'status':'BLOCKED','stage':stage,'exitCode':int(rc),
 'scriptSha256':entry,'baseCommit':base,'modelSha256':model,'localCommit':commit,
 'ownerVisualAcceptance':False,'realBrowserGaitAudit':'PENDING'},indent=2)+'\n')
PYFAIL
    printf 'BLOCKED stage=%s exit=%s receipt=%s/last-failure.json\n' "$STAGE" "$rc" "$STATE" >&2
  fi
}
trap on_exit EXIT
printf 'CAMPAIGN=%s\nSCRIPT_SHA256=%s\nBASE_SHA=%s\nMODEL_SHA=%s\nCHECKOUT=%s\n' "$CAMPAIGN" "$ENTRY_SHA" "$BASE" "$MODEL_SHA" "$CHECKOUT"
if [ "${PREFIX:-}" != '/data/data/com.termux/files/usr' ] || [ -z "${ANDROID_ROOT:-}" ];then
  echo 'BLOCKED_NOT_ANDROID_TERMUX' >&2;exit 70
fi
for cmd in git python3 node curl timeout sha256sum stat;do
  command -v "$cmd" >/dev/null || { echo "BLOCKED_MISSING_COMMAND=$cmd" >&2;exit 71; }
done
export GIT_LFS_SKIP_SMUDGE=1 GIT_TERMINAL_PROMPT=0
STAGE=verify-exact-normal-checkout
[ -d "$HOME/storage/documents" ] && [ -d "$CHECKOUT/.git" ] && [ ! -L "$CHECKOUT" ] && [ ! -L "$CHECKOUT/.git" ] || {
  echo 'BLOCKED_EXPECTED_PERSISTENT_CHECKOUT_MISSING_OR_SYMLINK' >&2;exit 72; }
CANON="$(readlink -f -- "$CHECKOUT")"
DOCS="$(readlink -f -- "$HOME/storage/documents")"
[ "$CANON" = "$DOCS/GodotProjects/parametric-parambulator" ] || { echo "BLOCKED_WRONG_CHECKOUT=$CANON" >&2;exit 72; }
if ! git config --global --get-all safe.directory 2>/dev/null | grep -Fxq -- "$CANON";then
 git config --global --add safe.directory "$CANON"
fi
cd "$CHECKOUT"
[ "$(git rev-parse --show-toplevel)" = "$CANON" ] || { echo 'BLOCKED_NOT_EXACT_GIT_REPO' >&2;exit 72; }
[ "$(git symbolic-ref --short HEAD)" = main ] || { echo 'BLOCKED_WRONG_BRANCH' >&2;exit 72; }
case "$(git remote get-url origin)" in "$REMOTE"|'git@github.com:Valar05/parametric-parambulator.git') :;; *) echo 'BLOCKED_WRONG_ORIGIN' >&2;exit 72;; esac
[ "$(git hash-object AGENTS.md)" = "$AGENTS_SHA" ] || { echo 'BLOCKED_AGENTS_REVISION_CHANGED' >&2;exit 72; }
[ "$(git rev-parse HEAD:AGENTS.md)" = "$AGENTS_SHA" ] || { echo 'BLOCKED_GIT_AGENTS_REVISION_CHANGED' >&2;exit 72; }
[ "$(git hash-object tools/hareworks-forward-woman/v0.1.14/viewer.mjs)" = 'eb8c4b652a8e335d7b27eebcc3901848666b022f' ] || { echo 'BLOCKED_SOURCE_VIEWER_CHANGED' >&2;exit 72; }
[ -f "$MODEL" ] && [ ! -L "$MODEL" ] && [ "$(stat -c '%s' "$MODEL")" = "$MODEL_SIZE" ] &&
  [ "$(sha256sum "$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || { echo 'BLOCKED_REAL_HAREWORKS_GLB_NOT_VERIFIED' >&2;exit 73; }
POINTER="$(printf 'version https://git-lfs.github.com/spec/v1\noid sha256:%s\nsize %s' "$MODEL_SHA" "$MODEL_SIZE")"
[ "$(git show HEAD:"$MODEL")" = "$POINTER" ] || { echo 'BLOCKED_MODEL_GIT_POINTER_CHANGED' >&2;exit 73; }
# All mutations stay in this one unpublished v0.1.15 directory.
remote_main(){ timeout 40 git ls-remote "$REMOTE" refs/heads/main | awk '{print $1}'; }
STAGE=verify-remote-main
LIVE=''
for attempt in 1 2 3;do
  LIVE="$(remote_main)" && [ -n "$LIVE" ] && break || true
  sleep "$attempt"
done
[ -n "$LIVE" ] || { echo 'BLOCKED_REMOTE_UNAVAILABLE' >&2;exit 74; }
HEAD_SHA="$(git rev-parse HEAD)"
MODE='STAGED_RECOVERY'
if [ "$HEAD_SHA" = "$BASE" ] && [ "$LIVE" = "$BASE" ];then
  [ -z "$(git ls-tree -r --name-only HEAD -- "$DEST")" ] || { echo 'BLOCKED_DEST_ALREADY_TRACKED_AT_BASE' >&2;exit 74; }
elif [ "$HEAD_SHA" != "$BASE" ] && [ "$(git rev-list --parents -n 1 HEAD | awk '{print $2}')" = "$BASE" ] &&
     [ "$(git diff-tree --no-commit-id --name-only -r HEAD | awk -v p="$DEST/" 'index($0,p)!=1{print $0;bad=1} END{if(bad)exit 1}')" = '' ];then
  [ -f "$DEST/$OWN" ] && [ "$(sha256sum "$DEST/$OWN" | awk '{print $1}')" = "$ENTRY_SHA" ] || {
    echo 'BLOCKED_UNRECOGNIZED_LOCAL_COMMIT_OR_RECOVERY_SCRIPT' >&2;exit 74; }
  [ "$(git rev-parse "HEAD:$DEST/$OWN")" = "$(git hash-object "$ENTRY")" ] || {
    echo 'BLOCKED_RECOVERY_SCRIPT_NOT_IN_COMMIT' >&2;exit 74; }
  if [ "$LIVE" = "$HEAD_SHA" ];then MODE='PUBLISHED_REUSE'
  elif [ "$LIVE" = "$BASE" ];then MODE='PENDING_PUSH'
  else echo "BLOCKED_REMOTE_DIVERGED=$LIVE" >&2;exit 74;fi
  NEW_SHA="$HEAD_SHA"
else
  echo "BLOCKED_UNEXPECTED_HEAD_OR_REMOTE head=$HEAD_SHA remote=$LIVE base=$BASE" >&2;exit 74
fi
# A rerun after a commit must never bypass the dirty-check just because a
# matching version was published. Android's sole approved exception is the
# SHA-verified materialized model, which we already checked above.
if [ "$MODE" != STAGED_RECOVERY ];then
  STAGE=verify-existing-commit-worktree
  python3 - "$MODEL" <<'PYCLEAN'
import subprocess,sys
model=sys.argv[1]
r=subprocess.run(['git','status','--porcelain=v1','--untracked-files=all','-z'],capture_output=True,check=True)
for item in [x.decode('utf-8','surrogateescape') for x in r.stdout.split(b'\0') if x]:
 if item != ' M '+model:
  raise SystemExit('BLOCKED_COMMITTED_GAIT_CHECKOUT_DIRTY_'+repr(item))
print('PUBLISHED_OR_UNPUSHED_CHECKOUT_SCOPE_PASS')
PYCLEAN
  [ -z "$(git diff --cached --name-only)" ] || { echo 'BLOCKED_PENDING_INDEX_NOT_CLEAN' >&2;exit 75; }
  [ "$(git rev-parse "HEAD:$DEST/$ORIGINAL")" = "$(git hash-object "$DEST/$ORIGINAL")" ] || {
    echo 'BLOCKED_COMMITTED_GENERATOR_CHANGED' >&2;exit 75; }
  [ "$(sha256sum "$DEST/$ORIGINAL" | awk '{print $1}')" = "$ORIGINAL_SHA" ] || {
    echo 'BLOCKED_GENERATOR_IDENTITY_CHANGED' >&2;exit 75; }
fi
STAGE=verify-already-staged-payload
if [ "$MODE" = STAGED_RECOVERY ];then
  [ -f "$DEST/$ORIGINAL" ] && [ ! -L "$DEST/$ORIGINAL" ] &&
   [ "$(sha256sum "$DEST/$ORIGINAL" | awk '{print $1}')" = "$ORIGINAL_SHA" ] || {
     echo 'BLOCKED_V015_GENERATOR_NOT_EXACT_ORIGINAL' >&2;exit 75; }
  [ -f "$DEST/contract.json" ] && grep -Fq 'hareworks-woman-accepted-v019-startup-recovery-v0.1.15' "$DEST/contract.json" || {
    echo 'BLOCKED_WRONG_SOURCE_PAYLOAD_CONTRACT' >&2;exit 75; }
  # PYCHECKER's 'validate' only accepts 20 exact new staged paths (+ optional
  # matching pre-staged r2 recovery source), the known LFS materialization, and
  # EXACTLY the three known EOF whitespace errors. Any other change blocks.
  python3 - "$DEST" "$OWN" "$ENTRY_SHA" "$MODEL" <<'PYCHECKER'
import hashlib,pathlib,re,subprocess,sys
base,own,entrysha,model=sys.argv[1:]
root=pathlib.Path(base)
fixes={'archived-root-regression.mjs','patch.py','startup-regression.py'}
original=root/'campaign-v0.1.15-v1-godotprojects.sh'
run=lambda *xs:subprocess.run(xs,capture_output=True,check=False)
def reject(msg):raise SystemExit('BLOCKED_STAGED_PAYLOAD_VALIDATION_'+msg)
changes=run('git','status','--porcelain=v1','--untracked-files=all','-z')
if changes.returncode:reject('GIT_STATUS')
items=[x.decode('utf-8','surrogateescape') for x in changes.stdout.split(b'\0') if x]
paths=set();staged=set();extra=False
for item in items:
 if len(item)<4 or item[2]!=' ':reject('BAD_STATUS_'+repr(item))
 xy,path=item[:2],item[3:]
 if path==model and xy==' M':continue
 if not path.startswith(base+'/') or '..' in pathlib.PurePosixPath(path).parts:reject('OUT_OF_SCOPE_'+repr(item))
 name=path[len(base)+1:]
 if '/' in name or pathlib.Path(path).is_symlink():reject('NESTED_OR_SYMLINK_'+repr(item))
 if name==own and xy in ('??','A '):
  if hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()!=entrysha:reject('R2_COLLISION')
  extra=True
  if xy=='A ':staged.add(name)
  paths.add(name);continue
 if xy not in ('A ','AM'):reject('UNEXPECTED_DIRTY_STATUS_'+repr(item))
 if xy=='AM':
  if name not in fixes:reject('UNRELATED_UNSTAGED_MODIFICATION_'+name)
  idx=run('git','show',':'+path)
  if idx.returncode:reject('INDEX_MISSING_'+name)
  expected=idx.stdout.rstrip(b'\n')+b'\n'
  if pathlib.Path(path).read_bytes()!=expected:reject('UNEXPECTED_WORKTREE_MODIFICATION_'+name)
 staged.add(name);paths.add(name)
if len(staged - {own})!=20:reject('EXPECTED_20_STAGED_FILES_GOT_'+str(len(staged-{own})))
if len(paths)!=(21 if extra else 20):reject('UNEXPECTED_PAYLOAD_COUNT_'+str(len(paths)))
required={'viewer.mjs','index.html','foot-gait.mjs','root-motion.mjs','shoe-witness.mjs',
          'contract.json','archived-root-regression.mjs','patch.py','startup-regression.py'}
if not required<=staged:reject('MISSING_REQUIRED_PAYLOAD')
res=run('git','diff','--cached','--check')
if res.returncode not in (0,2):reject('WHITESPACE_CHECK_UNEXPECTED_EXIT_'+str(res.returncode))
errors=res.stdout.decode('utf-8','replace').strip().splitlines()
if res.returncode==0 and errors:reject('WHITESPACE_OUTPUT_WITH_ZERO_EXIT')
found=[]
for err in errors:
 m=re.fullmatch(re.escape(base)+r'/([^/:]+):\d+: new blank line at EOF\.',err.strip())
 if not m:reject('OTHER_WHITESPACE_ERROR_'+repr(err))
 found.append(m.group(1))
if set(found) not in (fixes,set()):reject('INCOMPLETE_OR_WRONG_EOF_ERRORS_'+str(found))
if len(found) not in (0,3):reject('WRONG_WHITESPACE_ERROR_COUNT')
for name in fixes:
 path=root/name
 if not path.is_file() or path.is_symlink():reject('MISSING_FIX_FILE_'+name)
 if run('git','ls-files','--error-unmatch',str(path)).returncode:reject('MISSING_INDEX_ENTRY_'+name)
 blob=run('git','show',':'+str(path))
 if blob.returncode:reject('STAGED_BLOB_NOT_FOUND_'+name)
 expected=blob.stdout.rstrip(b'\n')+b'\n'
 if expected==blob.stdout and errors:reject('EXPECTED_TRAILING_BLANK_MISSING_'+name)
 if not blob.stdout.endswith(b'\n\n') and errors:reject('NOT_EXACT_EOF_BLANK_'+name)
 actual=path.read_bytes()
 if actual not in (blob.stdout,expected):reject('WORKTREE_BYTES_DRIFT_'+name)
 if actual!=expected:
  path.write_bytes(expected)
  if path.read_bytes()!=expected:reject('FIX_WRITE_READBACK_FAILED_'+name)
 print('REPAIRED_EXACT_THREE_TRAILING_BLANK_LINES='+name)
print('STAGED_RECOVERY_SCOPE_VERIFIED=1 sourceFiles=20 selectedEOFErrors='+str(sorted(found)))
PYCHECKER
  STAGE=stage-repaired-source-only
  if [ ! -e "$DEST/$OWN" ];then
    cp -- "$ENTRY" "$DEST/$OWN"
  fi
  [ "$(sha256sum "$DEST/$OWN" | awk '{print $1}')" = "$ENTRY_SHA" ] || {
    echo 'BLOCKED_NEW_RECOVERY_SOURCE_COLLISION' >&2;exit 75; }
  git add -- "$DEST/archived-root-regression.mjs" "$DEST/patch.py" "$DEST/startup-regression.py" "$DEST/$OWN"
  git diff --cached --check || { echo 'BLOCKED_WHITESPACE_RECHECK' >&2;exit 75; }
  # Never accept unrelated staged/untracked files after repair.
  python3 - "$DEST" "$MODEL" <<'PYSTAGE'
import pathlib,subprocess,sys
base,model=sys.argv[1:]
lines=subprocess.run(['git','status','--porcelain=v1','--untracked-files=all','-z'],capture_output=True,check=True).stdout
entries=[p.decode('utf-8','surrogateescape') for p in lines.split(b'\0') if p]
expected=21;seen=0
for item in entries:
 if item.startswith(' M '+model):continue
 if not item.startswith('A  '+base+'/') or item.count('/')!=base.count('/')+1:
  raise SystemExit('BLOCKED_STAGED_FINAL_SCOPE_'+repr(item))
 seen+=1
if seen!=expected:raise SystemExit('BLOCKED_STAGE_COUNT expected=21 actual='+str(seen))
print('RECOVERY_STAGE_PASS addedFiles='+str(seen)+' modelUnchanged=1')
PYSTAGE
  # These are the same physics/math tests the original campaign already passed.
  STAGE=recheck-gait-source-and-tests
  for f in "$DEST"/*.mjs;do node --check "$f";done
  python3 - "$DEST" <<'PYPARSE'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
for name in ('patch.py','startup-regression.py','review-server.py'):
 compile((p/name).read_text(),str(p/name),'exec')
print('PYTHON_PARSE_RECOVERY_PASS')
PYPARSE
  node "$DEST/shoe-witness-test.mjs"
  node "$DEST/contact-test.mjs"
  node "$DEST/root-model-test.mjs"
  node "$DEST/contact-core-test.mjs"
  node "$DEST/geometry-test.mjs"
  node "$DEST/archived-root-regression.mjs" tools/hareworks-forward-woman/v0.1.3/reference-leg-witnesses.json
  python3 "$DEST/startup-regression.py" "$DEST"
  STAGE=git-commit
  [ "$(remote_main)" = "$BASE" ] || { echo 'BLOCKED_REMOTE_ADVANCED_BEFORE_COMMIT' >&2;exit 76; }
  git var GIT_AUTHOR_IDENT >/dev/null || { echo 'BLOCKED_MISSING_GIT_IDENTITY' >&2;exit 76; }
  git commit -m 'Hareworks v0.1.15 recover staged startup motion after Git EOF check'
  NEW_SHA="$(git rev-parse HEAD)"
  [ "$(git rev-list --parents -n 1 HEAD | awk '{print $2}')" = "$BASE" ] || { echo 'BLOCKED_COMMIT_PARENT_CHANGED' >&2;exit 76; }
fi
# If a previous launch committed successfully but push failed, publish the
# existing identical commit. NEVER amend, reset, stash, rebase or force push.
if [ "$MODE" = STAGED_RECOVERY ] || [ "$MODE" = PENDING_PUSH ];then
  STAGE=publish-existing-commit
  LATEST="$(remote_main)" || true
  if [ "$LATEST" = "$BASE" ];then
    if ! GIT_LFS_SKIP_PUSH=1 timeout 90 git push origin HEAD:refs/heads/main;then
      GIT_LFS_SKIP_PUSH=1 timeout 90 git push 'git@github.com:Valar05/parametric-parambulator.git' HEAD:refs/heads/main || {
        echo "BLOCKED_GIT_PUSH_FAILED_COMMIT_PRESERVED=$NEW_SHA" >&2;exit 77; }
    fi
  elif [ "$LATEST" != "$NEW_SHA" ];then
    echo "BLOCKED_REMOTE_CHANGED_DURING_PUBLISH expected=$NEW_SHA actual=$LATEST" >&2;exit 77
  fi
fi
STAGE=verify-exact-remote-publication
[ "$(remote_main)" = "$NEW_SHA" ] || { echo 'BLOCKED_REMOTE_COMMIT_NOT_READ_BACK' >&2;exit 78; }
GIT_LFS_SKIP_SMUDGE=1 timeout 95 git fetch --depth 1 --filter=blob:none origin refs/heads/main
[ "$(git rev-parse FETCH_HEAD)" = "$NEW_SHA" ] || { echo 'BLOCKED_FETCH_READBACK_MISMATCH' >&2;exit 78; }
for f in $(git diff-tree --no-commit-id --name-only -r "$NEW_SHA");do
  case "$f" in "$DEST"/*) :;; *) echo "BLOCKED_REMOTE_UNEXPECTED_MEMBER=$f" >&2;exit 78;; esac
  [ "$(git rev-parse "FETCH_HEAD:$f")" = "$(git rev-parse "HEAD:$f")" ] || {
    echo "BLOCKED_REMOTE_BLOB_MISMATCH=$f" >&2;exit 78; }
done
[ "$(git diff --cached --name-only | wc -l)" = 0 ] || { echo 'BLOCKED_INDEX_NOT_CLEAN_AFTER_PUBLICATION' >&2;exit 78; }
[ "$(sha256sum "$MODEL" | awk '{print $1}')" = "$MODEL_SHA" ] || { echo 'BLOCKED_MODEL_CHANGED_AFTER_PUBLICATION' >&2;exit 78; }
[ "$(git hash-object "$DEST/$OWN")" = "$(git rev-parse "HEAD:$DEST/$OWN")" ] || { echo 'BLOCKED_DELIVERED_SCRIPT_NOT_IN_COMMIT' >&2;exit 78; }
STAGE=launch-physical-walk-review
RUN="$(mktemp -d "$STATE/viewer.XXXXXXXX")"
READY="$RUN/ready.json"
SERVER_LOG="$STATE/review-server.log"
nohup python3 "$DEST/review-server.py" "$CHECKOUT" "$READY" "$STATE" </dev/null >> "$SERVER_LOG" 2>&1 &
SERVER_PID=$!
for k in $(seq 1 40);do [ -s "$READY" ] && break;sleep .25;done
[ -s "$READY" ] && kill -0 "$SERVER_PID" 2>/dev/null || { echo 'BLOCKED_VIEWER_SERVER_NOT_READY' >&2;exit 79; }
PORT="$(python3 - "$READY" <<'PYPORT'
import json,sys
print(json.load(open(sys.argv[1]))['port'])
PYPORT
)"
URL="http://127.0.0.1:$PORT/$DEST/index.html?commit=$NEW_SHA&scriptSha=$ENTRY_SHA"
curl -fsSI --max-time 20 "$URL" > "$RUN/headers.txt"
grep -iq 'Cache-Control: no-store' "$RUN/headers.txt" || { echo 'BLOCKED_CACHE_HEADERS' >&2;exit 79; }
for f in viewer.mjs root-motion.mjs foot-gait.mjs;do
  actual="$(curl -fsS --max-time 25 "http://127.0.0.1:$PORT/$DEST/$f" | sha256sum | awk '{print $1}')"
  expected="$(sha256sum "$DEST/$f" | awk '{print $1}')"
  [ "$actual" = "$expected" ] || { echo "BLOCKED_HTTP_FILE_IDENTITY=$f" >&2;exit 79; }
done
python3 - "$STATE" "$CAMPAIGN" "$BASE" "$NEW_SHA" "$ENTRY_SHA" "$MODEL_SHA" "$URL" "$PORT" "$SERVER_PID" "$CANON" "$AGENTS_SHA" "$RULES_CAMPAIGN" "$RULES_TOPDOWN" <<'PYRECEIPT'
import datetime,json,pathlib,sys
(state,campaign,base,published,entry,model,url,port,pid,checkout,agents,etiquette,topdown)=sys.argv[1:]
r={'campaign':campaign,'status':'STAGED_EOF_RECOVERED_PUBLISHED_VIEWER_LAUNCHED_AUDIT_PENDING',
 'timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'originalUnpublishedCampaignReused':True,'whitespaceOnlyRepair':[ 'archived-root-regression.mjs','patch.py','startup-regression.py'],
 'sourceCommit':base,'publishedCommit':published,'remoteReadbackVerified':True,'entrySha256':entry,
 'originalSourceModelSha256':model,'modelUnchanged':True,'checkout':checkout,'persistentCheckout':True,
 'rulesReadInAuthoringTurn':{'AGENTSBlob':agents,'CampaignEtiquette':etiquette,'TopDownEtiquette':topdown},
 'viewerUrl':url,'viewerPort':int(port),'viewerPid':int(pid),
 'contactGate':'REAL_SKINNED_BROWSER_AUDIT_PENDING',
 'ownerVisualAcceptance':False,'viewerOpening':'REQUESTED_NOT_CONFIRMED'}
p=pathlib.Path(state)/'latest-receipt.json';p.write_text(json.dumps(r,indent=2)+'\n')
print('RECEIPT='+str(p))
PYRECEIPT
STAGE=review-ready
printf 'CHECKOUT_READY=%s\nPUBLISHED_COMMIT=%s\nSCRIPT_SHA256=%s\nMODEL_SHA256=%s\n' "$CHECKOUT" "$NEW_SHA" "$ENTRY_SHA" "$MODEL_SHA"
printf 'V015_GAIT_FILES_REUSED=YES\nWHITESPACE_REPAIRED_ONLY=YES\n'
printf 'VIEWER_URL=%s\nVIEWER_PID=%s\n' "$URL" "$SERVER_PID"
echo 'CONTACT_GATE=PENDING_REAL_BROWSER_SKINNED_120HZ_AUDIT'
echo 'GAIT_RESEMBLANCE_GATE=PENDING_OWNER_VISUAL_ACCEPTANCE'
if command -v termux-open-url >/dev/null 2>&1;then
  termux-open-url "$URL" || echo 'VIEWER_OPEN_REQUEST_FAILED__URL_ABOVE_IS_AVAILABLE'
elif command -v am >/dev/null 2>&1;then
  am start -a android.intent.action.VIEW -d "$URL" >/dev/null 2>&1 || echo 'VIEWER_OPEN_REQUEST_FAILED__URL_ABOVE_IS_AVAILABLE'
fi
