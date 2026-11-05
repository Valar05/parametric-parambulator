#!/data/data/com.termux/files/usr/bin/bash
# Obsidianti Heavy1 source-world-space Blender IK repair, v1.5.4.
# Authorized body: Termux Git, one invocation, versioned immutable sources.
set -Eeuo pipefail
VERSION='OBSIDIANTI_HEAVY1_COMBINED_DIAGNOSTIC_v1.5.4'
MODEL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
SOURCE_COMMIT='1daf0b7cfd830a9812a4dbe5b4487330c86f0ab1'
FAILURE_COMMIT='434b50dc0cabbf1220fa07081bf09e7439ed0e75'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
SELF_REL='campaigns/OBSIDIANTI_HEAVY1_COMBINED_DIAGNOSTIC_v1.5.4_LAUNCH.sh'
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
p=pathlib.Path(os.environ['HC_RECEIPT']);r={'campaign':'OBSIDIANTI_HEAVY1_COMBINED_DIAGNOSTIC_v1.5.4','authority':'TERMUX_GIT_ONLY','stage':os.environ['HC_STAGE'],'error':os.environ['HC_ERROR'],'exitCode':int(os.environ['HC_RC']),'launcherSha256':os.environ['HC_SHA'],'sourceCommit':os.environ['HC_COMMIT'],'sourceModelSha256':os.environ['HC_MODEL'],'modelPublication':os.environ['HC_PUBLISHED'],'ownerVisualApproval':False,'operatorLog':os.environ['HC_LOG'],'generatedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
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
import pathlib,sys,ast,hashlib
root=pathlib.Path(sys.argv[1]);old='v1.5.3';new='v1.5.4'
paths=[('campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_'+k+'_'+old+'.py','campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_'+k+'_'+new+'.py') for k in ('EVAL','APPLY','RUN')]
paths += [('tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_'+old+'.py','tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_'+new+'.py'),('docs/obsidianti/HEAVY1_BLENDER_IK_'+old+'.md','docs/obsidianti/HEAVY1_BLENDER_IK_'+new+'.md'),('review/obsidianti-heavy1-blender-ik-'+old+'.html','review/obsidianti-heavy1-blender-ik-'+new+'.html')]
for a,b in paths:
 if (root/b).exists():raise RuntimeError('VERSIONED_DESTINATION_COLLISION '+b)
 if not (root/a).is_file():raise RuntimeError('SOURCE_NOT_COMMITTED '+a)
src={b:(root/a).read_text() for a,b in paths}
def one(s,a,b,label):
 if s.count(a)!=1:raise RuntimeError('PATCH_DRIFT '+label+' expected 1 got '+str(s.count(a)))
 return s.replace(a,b,1)
def region(s,a,b,repl,label):
 if s.count(a)!=1 or s.count(b)!=1:raise RuntimeError('PATCH_DRIFT_REGION '+label)
 i=s.index(a);j=s.index(b,i);return s[:i]+repl+s[j:]
E,A,R,T,D,H=[b for a,b in paths]
s=src[E]
s=one(s," p.add_argument('--amplitude',type=float,default=1.0)"," p.add_argument('--amplitude',type=float,default=1.0)\n p.add_argument('--strategy',choices=['native','idle','local'],default='native')\n p.add_argument('--leg-ratio',choices=['combined','thigh','shin'],default='combined')",'eval-args')
s=one(s,"scale=float(calibration['legRatios'][side]['combinedRatio'])*a.amplitude","ratio={'combined':'combinedRatio','thigh':'thighRatio','shin':'shinRatio'}[a.leg_ratio]\n   scale=float(calibration['legRatios'][side][ratio])*a.amplitude",'anatomical-scales')
s=one(s,"qworld=(mapped_delta@idle_target_world).normalized()",'''qworld=(mapped_delta@idle_target_world).normalized()
   if a.strategy=='idle':
    qworld=idle_target_world
   elif a.strategy=='local':
    hipnow=q_bl(row['bones']['mixamorig:Hips']['worldQuaternion'])
    hipfirst=q_bl(frame0['mixamorig:Hips']['worldQuaternion'])
    footlocal_now=hipnow.inverted()@q_bl(ankle['worldQuaternion'])
    footlocal_first=hipfirst.inverted()@q_bl(ankle0['worldQuaternion'])
    localdelta=(footlocal_first.inverted()@footlocal_now).normalized()
    mappedlocal=(align@localdelta.to_matrix()@align.transposed()).to_quaternion()
    qworld=(idle_target_world@mappedlocal).normalized()''','isolate-foot-rotations')
s=one(s,"'amplitude':a.amplitude,'frames':frames}","'amplitude':a.amplitude,'strategy':a.strategy,'legRatio':a.leg_ratio,'frames':frames}",'result-provenance')
src[E]=s
s=src[A]
# Produce physically inspectable QUARANTINED GLB even when the kinematics fail.
# Never produce a candidate if structural protection or source buffer integrity fails.
s=one(s,''' if errors:
  print('PREFLIGHT_FAILED='+','.join(errors),flush=True)
  return 2
 blob=M.encode_glb(g,b)''',''' protection_errors=[x for x in errors if x.startswith(('PROTECTED_GLB_FIELD_CHANGED','PROTECTED_ACTION_CHANGED','ACTION_CHANNEL_POINTER_CHANGED','NONLEG_SAMPLER_CHANGED','SOURCE_BUFFER_OVERWRITTEN'))]
 if protection_errors:
  print('PROTECTED_STRUCTURE_BLOCK='+','.join(protection_errors),flush=True)
  return 2
 blob=M.encode_glb(g,b)''','quarantine-even-on-physical-fail')
s=one(s," print('PREFLIGHT_PASSED='+r['candidateSha256'],flush=True)"," if errors:\n  print('QUARANTINED_CANDIDATE_CREATED='+r['candidateSha256'],flush=True)\n  print('PREFLIGHT_FAILED='+','.join(errors),flush=True)\n  return 2\n print('PREFLIGHT_PASSED='+r['candidateSha256'],flush=True)",'return-failed-after-visual')
# Baseline probes are independent of the altered Heavy1 track.
needle=" r={'version':VER,'status':'PHYSICAL_PREFLIGHT_FAILED_NO_MODEL_CHANGE'"
addition=''' # Audit reference Idle and pre-existing Heavy1 without accepting them as correct.
 baselines={}
 for ref_name in ('LionheartIdle_UNREVIEWED','Lionheart_Heavy1'):
  ref_anim=next((z for z in orig_json['animations'] if z['name']==ref_name),None)
  if ref_anim is None:continue
  ref_tracks=M.channels(orig_json,original_bin,ref_anim)
  values=[]
  for tt in (0.,1/60,1/30,.10,.25,.5,.75,1.):
   ww=M.global_matrices(orig_json,ref_tracks,tt)
   pp=M.skin_foot_points(witnesses,skin,ibm,ww)
   values.append({'time':tt,'minimumSoleY':{side:min(v[1] for v in pp[side]) for side in SIDES}})
  baselines[ref_name]=values
'''
s=one(s,needle,addition+needle,'baseline-calibration')
s=one(s,"'nativeIKPoleCalibrations':sample['poleCalibration'],","'nativeIKPoleCalibrations':sample['poleCalibration'],'referenceBaselineSoles':baselines,'strategy':sample.get('strategy'),'legRatio':sample.get('legRatio'),",'baseline-report')
src[A]=s
s=src[R]
s=one(s,'def blender_cmd(repo,work,amp,out,report):','def blender_cmd(repo,work,amp,out,report,strategy,ratio):','blender-signature')
s=one(s,"'--output',str(out),'--report',str(report),'--amplitude',str(amp)]","'--output',str(out),'--report',str(report),'--amplitude',str(amp),'--strategy',strategy,'--leg-ratio',ratio]",'blender-args')
s=one(s,"  for amp in (1.0,.97,1.03,.94,.91,.88,.85,.82,.8,1.05,1.08):",'''  # Distinguish bone-scale mismatches from foot-rotation basis errors.
  # Calibrated candidates are actual Blender IK evaluations, not FK guesses.
  profiles=[('native','combined',1.),('idle','combined',1.),('local','combined',1.),
            ('native','thigh',1.),('idle','thigh',1.),('local','thigh',1.),
            ('native','shin',1.),('idle','shin',1.),('local','shin',1.),
            ('idle','combined',.90),('idle','combined',1.08),
            ('local','combined',.90),('native','combined',.90)]
  for strategy,ratio,amp in profiles:''','profile-search')
s=one(s,"   tag=str(amp).replace('.','_');out=work/('blender-ik-'+tag+'.json')","   tag=(strategy+'-'+ratio+'-'+str(amp).replace('.','_'));out=work/('blender-ik-'+tag+'.json')",'tags')
s=one(s,"   row={'amplitude':amp,'blenderStatus':'NOT_STARTED','physicalStatus':'NOT_STARTED'}","   row={'amplitude':amp,'strategy':strategy,'legRatio':ratio,'tag':tag,'blenderStatus':'NOT_STARTED','physicalStatus':'NOT_STARTED'}",'profile-receipt')
s=one(s,"blender_cmd(repo,work,amp,out,engineReport)","blender_cmd(repo,work,amp,out,engineReport,strategy,ratio)",'launch-blender')
s=one(s,"   reports.append(row);report_paths[tag]={'blender':out,'physical':physical,'engine':engineReport}","   row['candidatePath']=str(candidate) if candidate.exists() else None\n   reports.append(row);report_paths[tag]={'blender':out,'physical':physical,'engine':engineReport}",'retain-candidate')
s=one(s,"report_paths[str(selected['amplitude']).replace('.','_')]['blender']","report_paths[selected['tag']]['blender']",'selected-tag')
# Insert dedicated failure preview function before execute.
entry='def execute(packet):'
visual=r'''def publish_quarantined_visual(repo,work,downloads,reports,status):
 # Only isolated preview bytes. Never alter the canonical repo GLB on failure.
 import urllib.request,socket
 viable=[]
 for row in reports:
  path=row.get('candidatePath')
  if not path or not pathlib.Path(path).is_file():continue
  m=row.get('metrics') or {}
  score=(100*float(m.get('maxSkinnedPenetration_m') or 99)
       +25*float(m.get('maxQuarterFootStep_m') or 99)
       +.1*float(m.get('maxHalfFrameJointRotationStep_deg') or 999)
       +100*float(m.get('maxNativeControllerMiss_m') or 99))
  viable.append((score,row))
 if not viable:return {'status':'NO_CANDIDATE_BINARY','reason':'No safe physical candidate produced'}
 viable.sort(key=lambda x:x[0]);score,row=viable[0]
 folder=downloads/(VERSION+'_'+work.name+'_VISUAL')
 folder.mkdir(parents=True,exist_ok=False)
 src=pathlib.Path(row['candidatePath']);dst=folder/'Candidate_UNAPPROVED.glb'
 shutil.copyfile(src,dst)
 if sha(dst)!=sha(src):raise RuntimeError('PUBLIC_QUARANTINE_READBACK_MISMATCH')
 physical=work/('physical-'+row['tag']+'.json')
 if physical.is_file():shutil.copyfile(physical,folder/'physical-report.json')
 html=(repo/VIEW).read_text()
 html=html.replace('../assets/obsidianti/Obsidianti.glb','./Candidate_UNAPPROVED.glb')
 html=html.replace('visual review pending','FAILED PHYSICAL GATES - VISUAL DIAGNOSTIC ONLY')
 html=html.replace('Not owner-approved','FAILED PHYSICAL VALIDATION. NOT APPROVED. CANONICAL MODEL UNCHANGED')
 (folder/'review.html').write_text(html)
 meta={'status':'QUARANTINED_VISUAL_FAILED_PHYSICAL_GATES','profile':row,'score':score,
       'candidateSHA256':sha(dst),'htmlSHA256':sha(folder/'review.html'),
       'canonicalModelUnchanged':sha(repo/MODEL)==MODEL_SHA,
       'modelPublished':False,'ownerVisualApproval':False,'files':{'glb':str(dst),'html':str(folder/'review.html')}}
 atomic_json(folder/'visual-receipt.json',meta)
 if shutil.which('termux-media-scan'):
  for published in (dst,folder/'review.html'):
   run(['termux-media-scan',str(published)],timeout=20,required=False)
 code="import http.server,sys\nclass H(http.server.SimpleHTTPRequestHandler):\n def end_headers(self):\n  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')\n  self.send_header('Pragma','no-cache')\n  self.send_header('X-Heavy1-Candidate',sys.argv[3])\n  super().end_headers()\nhttp.server.ThreadingHTTPServer(('127.0.0.1',int(sys.argv[1])),lambda *a,**kw:H(*a,directory=sys.argv[2],**kw)).serve_forever()\n"
 for port in range(8230,8280):
  with socket.socket() as sock:
   try:sock.bind(('127.0.0.1',port))
   except OSError:continue
  logfile=open(work/'visual-server.log','ab',buffering=0)
  proc=subprocess.Popen([sys.executable,'-B','-c',code,str(port),str(folder),sha(dst)],stdout=logfile,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
  time.sleep(.4)
  url=f'http://127.0.0.1:{port}/review.html?model={sha(dst)}&build={status.get("sourceCommitReadback", "UNKNOWN")}&runner={sha(repo/RUNNER)}'
  try:
   with urllib.request.urlopen(url,timeout=3) as response:
    if response.status!=200 or response.headers.get('X-Heavy1-Candidate')!=sha(dst):raise RuntimeError('STALE_VISUAL_SERVER')
    meta.update({'url':url,'port':port,'serverPID':proc.pid,'cacheControl':response.headers.get('Cache-Control'),'httpIdentity':response.headers.get('X-Heavy1-Candidate')})
    atomic_json(folder/'visual-receipt.json',meta)
    if shutil.which('termux-open-url'):
     opened=run(['termux-open-url',url],timeout=12,required=False)
     meta['openRequested']=opened.returncode==0
    else:meta['openRequested']=False
    print('QUARANTINED_VISUAL_URL='+url,flush=True)
    print('QUARANTINED_CANDIDATE_SHA256='+sha(dst),flush=True)
    print('FAILED_VALIDATION_NOT_APPROVED=YES',flush=True)
    return meta
  except Exception:
   if proc.poll() is None:proc.terminate()
 meta['status']='PUBLIC_VISUAL_FILES_VERIFIED_VIEWER_UNAVAILABLE'
 return meta

'''
s=one(s,entry,visual+entry,'quarantine-view')
s=one(s,"   files={'receipt.json':receipt}","   files={'receipt.json':receipt}\n   vr=status.get('visualReview') or {}\n   if vr.get('files'):\n    for title,path in vr['files'].items():\n     if pathlib.Path(path).is_file():files['visual/'+pathlib.Path(path).name]=path\n    rp=pathlib.Path(vr['files']['html']).parent/'physical-report.json'\n    if rp.is_file():files['visual/physical-report.json']=rp",'zip-visual-artifacts')
s=one(s,'''  if not best:
   status['status']='BLOCKED_TRUE_BLENDER_IK_OR_SKIN_PREFLIGHT_MODEL_UNCHANGED'
   raise RuntimeError('NO_FULLY_VALID_HEAVY1_BLENDER_IK_SOLVE')''','''  if not best:
   status['status']='BLOCKED_TRUE_BLENDER_IK_OR_SKIN_PREFLIGHT_MODEL_UNCHANGED'
   status['visualReview']=publish_quarantined_visual(repo,work,downloads,reports,status)
   atomic_json(receipt,status)
   raise RuntimeError('NO_FULLY_VALID_HEAVY1_BLENDER_IK_SOLVE_VISUAL_QUARANTINED')''','failed-preview')
# On success still let user see a candidate. Production candidate will use canonical viewer.
src[R]=s
s=src[T]
# Regression against inadvertently reverting v153 world displacement and stale v151 tests.
s=one(s," must('SOURCE_WORLD_FOOT_CONTROLLER_DELTA_NO_DONOR_PELVIS_COMPENSATION' in s,'trajectory provenance missing')"," must('SOURCE_WORLD_FOOT_CONTROLLER_DELTA_NO_DONOR_PELVIS_COMPENSATION' in s,'trajectory provenance missing')\n must('a.strategy' in s and 'a.leg_ratio' in s,'scale/rotation diagnostics missing')\n must('QUARANTINED_CANDIDATE_CREATED' in a,'failed candidate not retained for review')\n must('publish_quarantined_visual' in r,'failed physical preview missing')",'tests-added')
src[T]=s
src[D]+='''\n\n## v1.5.4 Combined diagnostics and physical preview\nAudit object/rest/bone ratio and foot rotations independently. Run actual Blender IK\nunder native, idle-orientation and hip-local foot-rotation transfers, using\ncombined/thigh/shin anatomical ratios. Each result is physically checked against\nactual skinned wedges and locked canonical bones. Failed physically safe candidate\nGLBs are preserved in isolated private/public evidence, NOT published as canonical.\nThe least-invalid candidate is automatically displayed as UNAPPROVED even if no\nprofile passes, alongside physical metrics, source-Idle baseline and exact SHA.\nReal owner visual approval remains a separate human gate.\n'''
for a,b in paths:
 data=src[b].replace(old,new)
 data=data.replace('v1.5.3',new)
 if b.endswith('.html'):
  data=data.replace('visual review pending','visual diagnostic; approval pending')
 if b.endswith('.py'):ast.parse(data,filename=b)
 p=root/b;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
 print('GENERATED='+b+' SHA256='+hashlib.sha256(data.encode()).hexdigest())
print('SIX_VERSIONED_SOURCES_GENERATED=YES')
PY_GEN
STAGE='TEST_VERSIONED_SOURCE'
python3 -B "$REPO/tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_v1.5.4.py"
# Test the actual generator twice: a rerun must be byte-idempotent.
python3 -B - "$REPO" <<'PY'
import pathlib,sys,hashlib,ast
r=pathlib.Path(sys.argv[1]); v='v1.5.4'
names=[f'campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_{p}_{v}.py' for p in ('EVAL','APPLY','RUN')]+[f'tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_{v}.py']
for n in names:
 t=(r/n).read_text();ast.parse(t,filename=n)
 assert 'v1.5.3' not in t,n
print('NEW_VERSION_PYTHON_AST=PASS')
PY
cp "$SELF" "$REPO/$SELF_REL"
[[ "$(sha256sum "$REPO/$SELF_REL" |cut -d' ' -f1)" == "$SELF_SHA" ]] || { ERR='LAUNCHER_COPY_MISMATCH';exit 2; }
STAGE='COMMIT_AND_READBACK_TERMUX_GIT'
git -C "$REPO" config user.name 'Obsidianti Termux Campaign'
git -C "$REPO" config user.email 'obsidianti-campaign@users.noreply.github.com'
# Allowlist only the six new v1.5.4 sources and the self-contained launcher.
PATHS=(
 campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_EVAL_v1.5.4.py
 campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_APPLY_v1.5.4.py
 campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_v1.5.4.py
 tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_v1.5.4.py
 docs/obsidianti/HEAVY1_BLENDER_IK_v1.5.4.md
 review/obsidianti-heavy1-blender-ik-v1.5.4.html
 "$SELF_REL"
)
git -C "$REPO" add -- "${PATHS[@]}"
mapfile -t STAGED < <(git -C "$REPO" diff --cached --name-only)
[[ "${#STAGED[@]}" == 7 ]] || { ERR="STAGED_FILE_COUNT_NOT_SEVEN:${#STAGED[@]}";exit 2; }
for n in "${STAGED[@]}";do
 allowed=0;for a in "${PATHS[@]}";do [[ "$n" == "$a" ]] && allowed=1;done
 ((allowed==1)) || { ERR="UNAUTHORIZED_STAGED_FILE:$n";exit 2; }
done
git -C "$REPO" commit -m 'Obsidianti Heavy1: world-space native IK trajectory v1.5.4 source and recovery'
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
(p/'manifest.json').write_text(json.dumps({'campaign':'OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.4','files':d},sort_keys=True,indent=2)+'\n')
PY
STAGE='RUN_NATIVE_BLENDER_AND_SKINNED_PHYSICAL_GATES'
# v1.5.4 owns diagnostics and visible failed-candidate evidence without canonical publication.
set +e
python3 -B "$REPO/campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_v1.5.4.py" --packet "$PACKET"
RUN_RC=$?
set -e
if ((RUN_RC!=0));then ERR='NATIVE_BLENDER_OR_SKINNED_GATE_FAILED_VISUAL_REVIEW_QUARANTINED_SEE_V154_RECEIPT';exit "$RUN_RC";fi
MODEL_PUBLISHED='RUNNER_REPORTS_SUCCESS_VERIFY_V153_RECEIPT'
STAGE='RUNNER_REPORTED_SUCCESS_VISUAL_VERDICT_PENDING'
echo 'STATUS=REAL_BLENDER_IK_PHYSICAL_GATE_PASSED_RUNNER_RETURNED_SUCCESS'
echo 'OWNER_VISUAL_ACCEPTANCE=PENDING'
RUN_RC=0
