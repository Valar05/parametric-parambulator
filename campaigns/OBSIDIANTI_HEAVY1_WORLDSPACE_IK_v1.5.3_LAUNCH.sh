#!/data/data/com.termux/files/usr/bin/bash
# Obsidianti Heavy1 source-world-space Blender IK repair, v1.5.3.
# Authorized body: Termux Git, one invocation, versioned immutable sources.
set -Eeuo pipefail
VERSION='OBSIDIANTI_HEAVY1_WORLDSPACE_IK_v1.5.3'
MODEL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
SOURCE_COMMIT='e5ff174d734fcfdfa9ed6a297e9f5ba56c3587e3'
FAILURE_COMMIT='a3381d7c57f7f3fe1b9999412f9a2244a2c8421f'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
SELF_REL='campaigns/OBSIDIANTI_HEAVY1_WORLDSPACE_IK_v1.5.3_LAUNCH.sh'
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 GIT_LFS_SKIP_SMUDGE=1 GIT_TERMINAL_PROMPT=0
umask 077
[[ -n "${PREFIX:-}" && -x "$PREFIX/bin/bash" ]] || { echo 'BLOCKED_NOT_TERMUX'; exit 2; }
for bin in git python3 sha256sum; do command -v "$bin" >/dev/null || { echo "BLOCKED_DEPENDENCY=$bin"; exit 2; }; done
SELF="$(readlink -f "${BASH_SOURCE[0]}")"
SELF_SHA="$(sha256sum "$SELF"|cut -d' ' -f1)"
RUNID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
STATE="$HOME/.local/state/$VERSION/$RUNID"; mkdir -p "$STATE"
OUT="$HOME/storage/downloads"; [[ -d "$OUT" ]] || OUT="$STATE"
LOG="$OUT/${VERSION}_${RUNID}_OPERATOR.log"
RECEIPT="$OUT/${VERSION}_${RUNID}_RECEIPT.json"
REPO="$STATE/repo"; PACKET="$STATE/packet"
STAGE='BOOT'; ERR=''; RUN_RC=2; REPO_COMMIT=''; MODEL_PUBLISHED='NOT_ESTABLISHED'
exec > >(tee -a "$LOG") 2>&1
receipt(){
 export HC_STAGE="$STAGE" HC_ERROR="$ERR" HC_RC="$RUN_RC" HC_SHA="$SELF_SHA" HC_COMMIT="$REPO_COMMIT" HC_RECEIPT="$RECEIPT" HC_MODEL="$MODEL_SHA" HC_PUBLISHED="$MODEL_PUBLISHED" HC_LOG="$LOG"
 python3 -B - <<'PY'
import os,json,pathlib,datetime
p=pathlib.Path(os.environ['HC_RECEIPT']);r={'campaign':'OBSIDIANTI_HEAVY1_WORLDSPACE_IK_v1.5.3','authority':'TERMUX_GIT_ONLY','stage':os.environ['HC_STAGE'],'error':os.environ['HC_ERROR'],'exitCode':int(os.environ['HC_RC']),'launcherSha256':os.environ['HC_SHA'],'sourceCommit':os.environ['HC_COMMIT'],'sourceModelSha256':os.environ['HC_MODEL'],'modelPublication':os.environ['HC_PUBLISHED'],'ownerVisualApproval':False,'operatorLog':os.environ['HC_LOG'],'generatedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
t=p.with_suffix('.tmp');t.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');t.replace(p)
PY
}
on_exit(){
 local rc="$?"
 if ((rc!=0));then RUN_RC="$rc"; [[ -n "$ERR" ]] || ERR="FAILED_AT_${STAGE}";fi
 receipt || true
 echo "STAGE=$STAGE"; echo "ERROR=${ERR:-NONE}"; echo "OPERATOR_LOG=$LOG"; echo "RECEIPT=$RECEIPT"; echo "EXIT=$RUN_RC"
}
trap on_exit EXIT
trap 'ERR="INTERRUPTED";exit 130' INT TERM
printf 'CAMPAIGN=%s\nAUTHORITY=TERMUX_GIT_ONLY\nSELF_SHA256=%s\n' "$VERSION" "$SELF_SHA"
STAGE='PINNED_ISOLATED_GIT_CLONE'
git clone --depth=100 --single-branch --branch main --config filter.lfs.smudge= --config filter.lfs.required=false "$REMOTE" "$REPO"
HEAD="$(git -C "$REPO" rev-parse HEAD)"
echo "RESOLVED_REPO=$REPO";echo "EXECUTION_DIR=$REPO";echo 'BRANCH=main';echo "HEAD=$HEAD"
[[ "$(git -C "$REPO" rev-parse HEAD:AGENTS.md)" == "$AGENTS_BLOB" ]] || { ERR='AGENTS_REVISION_CHANGED';exit 2; }
[[ -z "$(git -C "$REPO" status --porcelain=v1 --untracked-files=all)" ]] || { ERR='DIRTY_ISOLATED_SOURCE';exit 2; }
for commit in "$SOURCE_COMMIT" "$FAILURE_COMMIT"; do
 if ! git -C "$REPO" merge-base --is-ancestor "$commit" HEAD 2>/dev/null; then
  git -C "$REPO" fetch --deepen=150 origin main
  git -C "$REPO" merge-base --is-ancestor "$commit" HEAD || { ERR="MISSING_HISTORICAL_SOURCE:$commit";exit 2; }
 fi
done
[[ "$(git -C "$REPO" show HEAD:assets/obsidianti/Obsidianti.glb)" == *"oid sha256:$MODEL_SHA"* ]] || { ERR='CANONICAL_MODEL_CHANGED_NO_PERMISSION_TO_OVERWRITE';exit 2; }
[[ "$(git -C "$REPO" rev-parse HEAD:assets/repl/Repl.glb)" != '' ]] || { ERR='REPL_LOCK_MISSING';exit 2; }
STAGE='PREPUBLICATION_VERSIONED_PATH_GUARD'
# The code generator inspects all six destination names before writing any source.
# This launcher is itself committed and read back before the physical run.
[[ ! -e "$REPO/$SELF_REL" ]] || { ERR='VERSIONED_LAUNCHER_DESTINATION_COLLISION';exit 2; }
mkdir -p "$(dirname "$REPO/$SELF_REL")"
python3 -B - "$REPO" <<'PY_GEN'
#!/usr/bin/env python3
"""Make immutable Heavy1 v1.5.3 from verified 1.5.1 source in isolated repo."""
import pathlib,sys,hashlib,ast
root=pathlib.Path(sys.argv[1]); V='v1.5.3'; OLD='v1.5.1'
files=[('campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_EVAL_'+OLD+'.py','campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_EVAL_'+V+'.py'),('campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_APPLY_'+OLD+'.py','campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_APPLY_'+V+'.py'),('campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_'+OLD+'.py','campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_'+V+'.py'),('tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_'+OLD+'.py','tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_'+V+'.py'),('docs/obsidianti/HEAVY1_BLENDER_IK_'+OLD+'.md','docs/obsidianti/HEAVY1_BLENDER_IK_'+V+'.md'),('review/obsidianti-heavy1-blender-ik-'+OLD+'.html','review/obsidianti-heavy1-blender-ik-'+V+'.html')]
# Preflight every new destination before writing even one file.
for _,new in files:
 if (root/new).exists():raise RuntimeError('VERSIONED_SOURCE_PATH_COLLISION '+new)
oldsrc={}
for old,new in files:
 p=root/old
 if not p.is_file():raise RuntimeError('MISSING_VERIFIED_SOURCE '+old)
 oldsrc[new]=p.read_text()

E='campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_EVAL_'+V+'.py';A='campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_APPLY_'+V+'.py';R='campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_'+V+'.py';T='tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_'+V+'.py';D='docs/obsidianti/HEAVY1_BLENDER_IK_'+V+'.md'
def replace_once(src,old,new,label):
 n=src.count(old)
 if n!=1:raise RuntimeError('PATCH_ANCHOR_DRIFT '+label+' count='+str(n))
 return src.replace(old,new,1)

def between(src,start,end,new,label):
 if src.count(start)!=1 or src.count(end)!=1:raise RuntimeError('PATCH_ANCHOR_DRIFT '+label)
 i=src.index(start);j=src.index(end,i)
 return src[:i]+new+src[j:]

# Fix the source-to-target trajectory domain: source world-space controller deltas,
# NEVER hip-relative changes from a donor pelvis that travels rapidly mid-attack.
s=oldsrc[E]
s=between(s,' def source_rel(b,hip):',' # These empties genuinely drive Blender', ''' def goals(row,hip_pose):
  output={}
  for side in SIDES:
   controller=row['bones'][side+'Foot.IK']; controller0=frame0[side+'Foot.IK']
   ankle=row['bones'][f'mixamorig:{side}Foot']; ankle0=frame0[f'mixamorig:{side}Foot']
   pole=row['bones'][side+'Knee.IK']
   # WORLD delta is authoritative. The source pelvis's large world translation
   # is excluded from this six-track transfer, because target pelvis is LOCKED.
   worldDelta=v3(controller['worldPosition'])-v3(controller0['worldPosition'])
   # Native evaluated ankle offset, independent of source hip and any pole error.
   residual=(v3(ankle['worldPosition'])-v3(controller['worldPosition']))-(v3(ankle0['worldPosition'])-v3(controller0['worldPosition']))
   scale=float(calibration['legRatios'][side]['combinedRatio'])*a.amplitude
   target_local=hipLocal[side]['ankle']+align@(worldDelta+residual)*scale
   poleLever=v3(pole['worldPosition'])-v3(controller['worldPosition'])
   pole_local=target_local+align@poleLever*scale
   # Map the source foot's WORLD rotation delta into the target anatomical basis.
   source_delta=(q_bl(ankle['worldQuaternion'])@q_bl(ankle0['worldQuaternion']).inverted()).normalized()
   mapped_delta=(align@source_delta.to_matrix()@align.transposed()).to_quaternion()
   idle_target_world=(hip_pose.to_quaternion()@hipLocal[side]['foot'].to_quaternion()).normalized()
   qworld=(mapped_delta@idle_target_world).normalized()
   output[side]={'ankleWorld':hip_pose@target_local,'poleWorld':hip_pose@pole_local,
       'footWorldRot':qworld, 'sourceDelta':worldDelta.length,
       'poleSeparation':(pole_local-target_local).length}
  return output

''','replace-goals')
s=s.replace('from approved combat Idle','from approved combat Idle')
s=replace_once(s,"'targetInitialization':'ACTUAL_ACCEPTED_LIONHEART_IDLE',","'targetInitialization':'ACTUAL_ACCEPTED_LIONHEART_IDLE',\n    'trajectoryBasis':'SOURCE_WORLD_FOOT_CONTROLLER_DELTA_NO_DONOR_PELVIS_COMPENSATION',",'trajectory-provenance')
oldsrc[E]=s

s=oldsrc[A]
s=between(s,' # Detect whether the original native controller trajectory is preserved with',' errors=[]', ''' # The source returns to its starting pose, so endpoint travel is ZERO by
 # construction. Record actual cumulative travel; endpoint displacement separately.
 scores['sourceControllerNetDisplacement_m']={}
 scores['sourceControllerPeakStep_m']={}
 for side in SIDES:
  series=[x['legsRelativePelvis'][side]['footControllerRelativePelvisMetres'] for x in source['frames']]
  world=[x['bones'][side+'Foot.IK']['worldPosition'] for x in source['frames']]
  scores['sourceControllerTotalTravel_m'][side]=sum(length(vec(y,x)) for x,y in zip(world,world[1:]))
  scores['sourceControllerNetDisplacement_m'][side]=length(vec(world[-1],world[0]))
  scores['sourceControllerPeakStep_m'][side]=max(length(vec(y,x)) for x,y in zip(world,world[1:]))
''','source-travel-metrics')
s=replace_once(s," if sample.get('engine','').find('Blender 4.x actual IK')<0 or sample.get('originalBadFKUsedForLegBasis') is not False:"," if (sample.get('engine','').find('Blender 4.x actual IK')<0 or sample.get('originalBadFKUsedForLegBasis') is not False\n   or sample.get('trajectoryBasis')!='SOURCE_WORLD_FOOT_CONTROLLER_DELTA_NO_DONOR_PELVIS_COMPENSATION'):",'sample-provenance')
oldsrc[A]=s

s=oldsrc[R]
# On v153 the original v151 REPORT prefix and source filenames get version bumped.
# Fixed preset amplitude exploration is NOT evidence of physical validity; respect gates.
s=replace_once(s,"  for amp in (1.0,.95,1.05,.9,.85,.8):","  for amp in (1.0,.97,1.03,.94,.91,.88,.85,.82,.8,1.05,1.08):",'bounded-amp-search')
s=replace_once(s,"  status['searchProfiles']=reports\n  if not best:","  status['searchProfiles']=reports\n  if not best:",'preserve-search-status')
# Ensure an already validated source commit need not repeat source publication.
# Viewer: identified server and no-cache responses, never accept stale model silently.
s=between(s,'def start_viewer(repo,work):','def execute(packet):', '''def start_viewer(repo,work):
 import urllib.request, socket
 runner_hash=sha(repo/RUNNER); model_hash=sha(repo/MODEL)
 source_head=git(repo,'rev-parse','HEAD').stdout.strip()
 server_code="import http.server,sys\\nclass H(http.server.SimpleHTTPRequestHandler):\\n def end_headers(self):\\n  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')\\n  self.send_header('Pragma','no-cache')\\n  self.send_header('X-Heavy1-Build',sys.argv[3])\\n  super().end_headers()\\nhttp.server.ThreadingHTTPServer(('127.0.0.1',int(sys.argv[1])),lambda *a,**kw:H(*a,directory=sys.argv[2],**kw)).serve_forever()\\n"
 for port in range(8179,8200):
  sock=socket.socket()
  try:sock.bind(('127.0.0.1',port))
  except OSError:continue
  finally:sock.close()
  log=open(work/'viewer.log','ab',buffering=0)
  proc=subprocess.Popen([sys.executable,'-B','-c',server_code,str(port),str(repo),source_head],
     stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
  time.sleep(.6)
  uri=f'http://127.0.0.1:{port}/review/obsidianti-heavy1-blender-ik-v1.5.3.html?build={source_head}&model={model_hash}&runner={runner_hash}'
  try:
   with urllib.request.urlopen(uri,timeout=5) as resp:
    if resp.status==200 and resp.headers.get('X-Heavy1-Build')==source_head and 'no-store' in resp.headers.get('Cache-Control',''):
     return {'url':uri,'status':'HTTP_IDENTIFIED_NOT_HUMAN_ACCEPTANCE','pid':proc.pid,
       'sourceHead':source_head,'modelSha256':model_hash,'runnerSha256':runner_hash,
       'port':port,'cacheControl':resp.headers.get('Cache-Control'),'identityHeader':resp.headers.get('X-Heavy1-Build')}
  except Exception:pass
  if proc.poll() is None:proc.terminate()
 return {'status':'NO_IDENTIFIED_LOCAL_VIEWER'}

''','viewer-cache-identity')
oldsrc[R]=s

s=oldsrc[T]
s=replace_once(s," must('target_local+align@nativePoleToFoot' in s,'pole lever arm not preserved')"," must('pole_local=target_local+align@poleLever*scale' in s,'pole lever arm not preserved')",'pole-test')
s=replace_once(s," must('set(edits)!=allowed' in r,'six-track allowlist missing')"," must('set(edits)!=allowed' in r,'six-track allowlist missing')\n must('worldDelta=v3(controller' in s and \"worldDelta+residual\" in s,'source controller not driven by world displacement')\n must('sourceControllerNetDisplacement_m' in a and 'sum(length(vec(y,x))' in a,'cyclic motion measured as zero')\n must('SOURCE_WORLD_FOOT_CONTROLLER_DELTA_NO_DONOR_PELVIS_COMPENSATION' in s,'trajectory provenance missing')",'world-delta-tests')
oldsrc[T]=s

# All versioned files are new. Never silently modify old v151 files.
for old,new in files:
 s=oldsrc[new].replace('v1.5.1',V)
 # v151 runner/test have capitalized constant too.
 s=s.replace('OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.1','OBSIDIANTI_HEAVY1_BLENDER_IK_'+V)
 if new.endswith('.html'):
  s=s.replace('<main id="stage">','<div id="buildid" role="note" style="padding:7px 12px;font-size:11px;overflow-wrap:anywhere">Validating build identity…</div><main id="stage">')
  s=s.replace("const holder=document.getElementById('stage')", "const query=new URLSearchParams(location.search);document.getElementById('buildid').textContent='BUILD '+(query.get('build')||'UNKNOWN')+' | MODEL SHA256 '+(query.get('model')||'UNKNOWN')+' | RUNNER SHA256 '+(query.get('runner')||'UNKNOWN')+' | CLIP Lionheart_Heavy1';const holder=document.getElementById('stage')")
  s=s.replace("new GLTFLoader().load('../assets/obsidianti/Obsidianti.glb?review='+Date.now(),result=>{", "const modelurl='../assets/obsidianti/Obsidianti.glb?sha='+encodeURIComponent(query.get('model')||'missing');fetch(modelurl,{cache:'no-store'}).then(r=>r.arrayBuffer()).then(async b=>{const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('');if(digest!==query.get('model'))throw Error('Loaded model digest mismatch: '+digest);document.getElementById('buildid').textContent+=' | LOADED GLB SHA VERIFIED';}).catch(e=>status.textContent='BLOCKED ASSET IDENTITY: '+e);new GLTFLoader().load(modelurl,result=>{")
 if new==D:
  s+='''\n\n## v1.5.3 source-world trajectory correction\nThe donor Heavy1 pelvis moves sharply in the middle of the action. Its foot IK\ncontrollers move more smoothly in WORLD space. The previous evaluator imported\npelvis-relative displacement onto the target's locked pelvis, causing excessive\nfoot displacement, knee branch flips, and discontinuity. This version maps the\ndonor's SOURCE WORLD controller displacement and evaluated ankle residual to the\ntarget idle foot, retaining the target's original Heavy1 pelvis tracks untouched.\nPole positions use the actual source pole-to-controller lever arm. Foot rotation\nuses the donor's world rotation delta in the anatomical aligned frame.\nCyclic source travel is integrated along the controller path, not inferred\nfrom identical first and last positions. All failures remain fail-closed.\n\nOnly Heavy1 six leg rotation channels are mutable. The evaluated Blender rig\nremains real IK, with actual full-skinned wedge validation required before any\ncanonical GLB commit. Human visual acceptance remains pending until supplied.\n'''
 if new.endswith('.py'):ast.parse(s,filename=new)
 p=root/new
 if p.exists():
  if p.read_text()!=s:raise RuntimeError('VERSIONED_DESTINATION_COLLISION '+new)
 else:
  p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 print('GENERATED',new,hashlib.sha256(s.encode()).hexdigest())
print('PATCH_COMPLETED=ALL_SIX_VERSIONED_FILES')
PY_GEN
STAGE='TEST_VERSIONED_SOURCE'
python3 -B "$REPO/tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_v1.5.3.py"
# Test the actual generator twice: a rerun must be byte-idempotent.
python3 -B - "$REPO" <<'PY'
import pathlib,sys,hashlib,ast
r=pathlib.Path(sys.argv[1]); v='v1.5.3'
names=[f'campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_{p}_{v}.py' for p in ('EVAL','APPLY','RUN')]+[f'tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_{v}.py']
for n in names:
 t=(r/n).read_text();ast.parse(t,filename=n)
 assert 'v1.5.1' not in t,n
print('NEW_VERSION_PYTHON_AST=PASS')
PY
cp "$SELF" "$REPO/$SELF_REL"
[[ "$(sha256sum "$REPO/$SELF_REL" |cut -d' ' -f1)" == "$SELF_SHA" ]] || { ERR='LAUNCHER_COPY_MISMATCH';exit 2; }
STAGE='COMMIT_AND_READBACK_TERMUX_GIT'
git -C "$REPO" config user.name 'Obsidianti Termux Campaign'
git -C "$REPO" config user.email 'obsidianti-campaign@users.noreply.github.com'
# Allowlist only the six new v1.5.3 sources and the self-contained launcher.
PATHS=(
 campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_EVAL_v1.5.3.py
 campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_APPLY_v1.5.3.py
 campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_v1.5.3.py
 tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_v1.5.3.py
 docs/obsidianti/HEAVY1_BLENDER_IK_v1.5.3.md
 review/obsidianti-heavy1-blender-ik-v1.5.3.html
 "$SELF_REL"
)
git -C "$REPO" add -- "${PATHS[@]}"
mapfile -t STAGED < <(git -C "$REPO" diff --cached --name-only)
[[ "${#STAGED[@]}" == 7 ]] || { ERR="STAGED_FILE_COUNT_NOT_SEVEN:${#STAGED[@]}";exit 2; }
for n in "${STAGED[@]}";do
 allowed=0;for a in "${PATHS[@]}";do [[ "$n" == "$a" ]] && allowed=1;done
 ((allowed==1)) || { ERR="UNAUTHORIZED_STAGED_FILE:$n";exit 2; }
done
git -C "$REPO" commit -m 'Obsidianti Heavy1: world-space native IK trajectory v1.5.3 source and recovery'
REPO_COMMIT="$(git -C "$REPO" rev-parse HEAD)"
[[ -z "$(git -C "$REPO" status --porcelain=v1 --untracked-files=all)" ]] || { ERR='NEW_SOURCE_COMMIT_DIRTY';exit 2; }
git -C "$REPO" push origin HEAD:refs/heads/main || { ERR='REMOTE_ADVANCED_OR_PUSH_REJECTED_NO_FORCE';exit 2; }
[[ "$(git -C "$REPO" ls-remote origin refs/heads/main|cut -f1)" == "$REPO_COMMIT" ]] || { ERR='REMOTE_SOURCE_READBACK_FAILED';exit 2; }
echo "SOURCE_COMMIT_READBACK=$REPO_COMMIT"
STAGE='ASSEMBLE_EXACT_COMMITTED_PACKET'
mkdir -p "$PACKET"
for rel in "${PATHS[@]:0:6}";do
 mkdir -p "$(dirname "$PACKET/$rel")"
 git -C "$REPO" show "$REPO_COMMIT:$rel" > "$PACKET/$rel"
 cmp "$REPO/$rel" "$PACKET/$rel" || { ERR="PACKET_MISMATCH:$rel";exit 2; }
done
python3 -B - "$PACKET" <<'PY'
import hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1]);d={}
for f in p.rglob('*'):
 if f.is_file():d[f.relative_to(p).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
assert len(d)==6
(p/'manifest.json').write_text(json.dumps({'campaign':'OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.3','files':d},sort_keys=True,indent=2)+'\n')
PY
STAGE='RUN_NATIVE_BLENDER_AND_SKINNED_PHYSICAL_GATES'
# v1.5.3 owns validation, quarantined search, publication, failure evidence and review.
set +e
python3 -B "$REPO/campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_v1.5.3.py" --packet "$PACKET"
RUN_RC=$?
set -e
if ((RUN_RC!=0));then ERR='NATIVE_BLENDER_OR_SKINNED_GATE_FAILED_SEE_VERSIONED_V153_HANDOFF';exit "$RUN_RC";fi
MODEL_PUBLISHED='RUNNER_REPORTS_SUCCESS_VERIFY_V153_RECEIPT'
STAGE='RUNNER_REPORTED_SUCCESS_VISUAL_VERDICT_PENDING'
echo 'STATUS=REAL_BLENDER_IK_PHYSICAL_GATE_PASSED_RUNNER_RETURNED_SUCCESS'
echo 'OWNER_VISUAL_ACCEPTANCE=PENDING'
RUN_RC=0
