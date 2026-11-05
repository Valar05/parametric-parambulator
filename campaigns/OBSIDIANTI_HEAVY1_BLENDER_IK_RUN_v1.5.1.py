#!/usr/bin/env python3
"""One single Termux Git campaign; actual Blender two-bone IK only for Heavy1.

READ true source archive, CONSTRUCT temporary Blender rig from exact target bind,
DRIVE IK and pole controls, BAKE six rotations, independently validate skinned
geometry, publish same original canonical GLB ONLY on full physical pass.
"""
from __future__ import annotations
import argparse, datetime, hashlib, importlib.util, json, os, pathlib, shutil, subprocess, sys, time, uuid, zipfile, stat

VERSION='OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.1'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
MODEL='assets/obsidianti/Obsidianti.glb'
MODEL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
DONOR='diagnostics/obsidianti/lionheart-ik-all-v1.4.0/actions/Heavy1.json'
DONOR_SHA='a14304e455f978fcdbb0607f187a175310e034fdfed7f83176402fd7eb9f1fd4'
CALIB='diagnostics/obsidianti/lionheart-ik-all-v1.4.0/calibration.json'
CALIB_SHA='b6d23f49c67df7816124362f4b1ee540db5c16a672fbc8c435a7f503ca123336'
MATH='campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py'
MATH_SHA='dc19a766ce41950c8040a81339d488573f70151910aa3ebf479ab8296484851f'
AUDIT='9c7d3774d945cc00bac1e4bfc621e50e3df7ba71'
BLENDER='campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_EVAL_v1.5.1.py'
APPLY='campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_APPLY_v1.5.1.py'
RUNNER='campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_v1.5.1.py'
TEST='tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_v1.5.1.py'
DOC='docs/obsidianti/HEAVY1_BLENDER_IK_v1.5.1.md'
VIEW='review/obsidianti-heavy1-blender-ik-v1.5.1.html'
FILES=(BLENDER,APPLY,RUNNER,TEST,DOC,VIEW)
REPORT='diagnostics/obsidianti/heavy1-blender-ik-v1.5.1'


def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as file:
  for chunk in iter(lambda:file.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def run(argv,timeout=250,required=True,env=None):
 p=None
 for attempt in range(3):
  try:p=subprocess.run([str(a) for a in argv],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout,env=env)
  except subprocess.TimeoutExpired:
   if attempt<2:continue
   raise RuntimeError('SUBPROCESS_TIMEOUT '+repr(argv[:4]))
  if p.returncode and required:
   if attempt<2 and any(x in p.stderr.lower() for x in ('could not resolve host','connection timed out','tls','temporarily unavailable')):continue
   raise RuntimeError('SUBPROCESS_FAILED '+repr(argv[:4])+' '+p.stderr[-850:])
  return p
 raise RuntimeError('SUBPROCESS_NO_RESULT')
def git(repo,*args,timeout=250,required=True):return run(['git','-C',str(repo),*args],timeout=timeout,required=required)
def js(p):return json.loads(pathlib.Path(p).read_text())
def atomic_json(path,data):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n');os.replace(tmp,path)
def pointer(repo,path,rev='HEAD'):
 blob=git(repo,'show',rev+':'+path).stdout
 if not blob.startswith('version https://git-lfs.github.com/spec/v1\n'):raise RuntimeError('EXPECTED_GIT_LFS_POINTER '+path)
 oid=next((x.split(':',1)[1].strip() for x in blob.splitlines() if x.startswith('oid sha256:')),None)
 if not oid or len(oid)!=64:raise RuntimeError('INVALID_GIT_LFS_OID '+path)
 return oid

def commit(repo,paths,message):
 git(repo,'add','--',*paths)
 staged=git(repo,'diff','--cached','--name-only').stdout.splitlines()
 if any(x not in paths for x in staged):raise RuntimeError('STAGED_WRONG_PATH')
 if not staged:return None
 if not git(repo,'config','--get','user.name',required=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Campaign')
 if not git(repo,'config','--get','user.email',required=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')
 git(repo,'commit','-m',message)
 return git(repo,'rev-parse','HEAD').stdout.strip()
def push(repo,head):
 p=git(repo,'push','origin','HEAD:refs/heads/main',timeout=360,required=False)
 if p.returncode:
  if 'non-fast-forward' in p.stderr or '[rejected]' in p.stderr:raise RuntimeError('PUSH_REFUSED_REMOTE_ADVANCED')
  if shutil.which('gh'):
   p=run(['git','-C',str(repo),'-c','credential.helper=!gh auth git-credential','push','origin','HEAD:refs/heads/main'],timeout=360,required=False)
  if p.returncode:raise RuntimeError('PUSH_AUTH_OR_NETWORK_FAILED '+p.stderr[-900:])
 line=git(repo,'ls-remote','origin','refs/heads/main',timeout=100).stdout.strip()
 if not line or line.split()[0]!=head:raise RuntimeError('REMOTE_HEAD_READBACK_MISMATCH')
 git(repo,'fetch','--no-tags','origin','main',timeout=210)
 if git(repo,'rev-parse','refs/remotes/origin/main').stdout.strip()!=head:raise RuntimeError('FETCHED_HEAD_READBACK_MISMATCH')
 return head

def verify_rules(repo):
 p=repo/'AGENTS.md'
 if not p.is_file():raise RuntimeError('RULES_READ_BLOCKED')
 blob=git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()
 if git(repo,'hash-object','--',str(p)).stdout.strip()!=blob:raise RuntimeError('AGENTS_WORKTREE_NOT_PINNED')
 txt=p.read_text()
 for tok in ('# AGENTS.md','Termux Git','Campaign Etiquette'):
  if tok not in txt:raise RuntimeError('RULES_IDENTITY_BAD '+tok)
 return {'gitBlob':blob,'sha256':sha(p),'etiquetteHomeCenterId':'1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI',
         'etiquetteReadByCampaignAuthor':'2026-11-04 via Home Center','termuxDirectHomeCenterRead':False}

def verify_packet(p):
 m=js(p/'manifest.json')
 if m.get('campaign')!=VERSION or set(m.get('files',{}))!=set(FILES):raise RuntimeError('PACKET_MEMBER_LIST_INVALID')
 for name,expected in m['files'].items():
  f=p/name
  if not f.is_file() or sha(f)!=expected:raise RuntimeError('PACKET_MEMBER_TAMPERED '+name)
 return m

def ensure_lfs():
 if run(['git','lfs','version'],required=False).returncode==0:return
 if not shutil.which('pkg'):raise RuntimeError('TERMUX_GIT_LFS_MISSING')
 run(['pkg','install','-y','git-lfs'],timeout=240)
 if run(['git','lfs','version'],required=False).returncode:raise RuntimeError('GIT_LFS_INSTALL_FAILED')

def verify_source(repo):
 if sha(repo/DONOR)!=DONOR_SHA or sha(repo/CALIB)!=CALIB_SHA or sha(repo/MATH)!=MATH_SHA:
  raise RuntimeError('ARCHIVED_LIONHEART_OR_MATH_SOURCE_MODIFIED')
 if git(repo,'merge-base','--is-ancestor',AUDIT,'HEAD',required=False).returncode:
  git(repo,'fetch','--deepen=50','origin','main',timeout=210)
  if git(repo,'merge-base','--is-ancestor',AUDIT,'HEAD',required=False).returncode:raise RuntimeError('AUDIT_COMMIT_NOT_IN_MAIN_HISTORY')
 m=js(repo/'diagnostics/obsidianti/lionheart-ik-all-v1.4.0/manifest.json')
 if m.get('artifactHashes',{}).get('actions/Heavy1.json')!=DONOR_SHA:raise RuntimeError('ARCHIVE_MANIFEST_TAMPERED')
 if m.get('sourceModelSha256')!=MODEL_SHA:raise RuntimeError('ARCHIVE_TARGET_PROVENANCE_INVALID')

def blender_cmd(repo,work,amp,out,report):
 args=['--model',str(repo/MODEL),'--source',str(repo/DONOR),'--calibration',str(repo/CALIB),
   '--math-helper',str(repo/MATH),'--output',str(out),'--report',str(report),'--amplitude',str(amp)]
 if shutil.which('blender'):
  return ['blender','--background','--factory-startup','--python',str(repo/BLENDER),'--',*args]
 if not shutil.which('proot-distro'):raise RuntimeError('BLENDER_UNAVAILABLE_NATIVE_AND_PROOT_DEBIAN')
 replacements={str(repo):'/mnt/obs-repo',str(work):'/mnt/obs-work'}
 def translate(path):
  s=str(path)
  for source,translated in replacements.items():
   if s==source or s.startswith(source+'/'):return translated+s[len(source):]
  return s
 return ['proot-distro','login','debian','--bind',str(repo)+':/mnt/obs-repo','--bind',str(work)+':/mnt/obs-work',
  '--','blender','--background','--factory-startup','--python',translate(repo/BLENDER),'--',
  *[translate(x) if x.startswith('/') else x for x in args]]

def test_candidate_guard(repo,origin,candidate):
 p=repo/MATH
 spec=importlib.util.spec_from_file_location('guarded_blender_ik_math',p);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
 g,b=M.load_glb(origin);h,c=M.load_glb(candidate)
 if not bytes(c).startswith(bytes(b)):raise RuntimeError('ORIGINAL_SKINNED_BIN_CHANGED')
 for item in ('nodes','skins','meshes','materials','textures','images','scenes'):
  if g.get(item)!=h.get(item):raise RuntimeError('PROTECTED_STRUCTURAL_GLB_DIFFERENCE '+item)
 if len(g['animations'])!=len(h['animations']):raise RuntimeError('CLIP_COUNT_DIFFERENT')
 for a,z in zip(g['animations'],h['animations']):
  if a['name']!=z['name']:raise RuntimeError('ANIMATION_ORDER_CHANGED')
  if a['name']!='Lionheart_Heavy1':
   if a!=z:raise RuntimeError('OTHER_ANIMATION_MUTATED '+a['name'])
  elif a['channels']!=z['channels']:raise RuntimeError('HEAVY1_CHANNELS_CHANGED')
 ids={n.get('name'):i for i,n in enumerate(g['nodes'])}
 allowed={(ids['mixamorig:'+side+part],'rotation') for side in ('Left','Right') for part in ('UpLeg','Leg','Foot')}
 a=next(x for x in g['animations'] if x['name']=='Lionheart_Heavy1')
 z=next(x for x in h['animations'] if x['name']=='Lionheart_Heavy1')
 edits=[]
 for key,ch in enumerate(a['channels']):
  k=(ch['target']['node'],ch['target']['path']);sa=a['samplers'][ch['sampler']];sb=z['samplers'][ch['sampler']]
  if sa!=sb:edits.append(k)
 if set(edits)!=allowed or len(edits)!=6:raise RuntimeError('NOT_EXACTLY_SIX_ALLOWED_ROTATION_TRACKS')
 return [g['nodes'][x[0]]['name']+'/'+x[1] for x in edits]

def write_evidence_zip(dst,paths):
 if dst.exists():raise RuntimeError('HANDOFF_ARCHIVE_ALREADY_EXISTS')
 with zipfile.ZipFile(dst,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
  for name,path in sorted(paths.items()):
   if pathlib.Path(path).is_file():z.write(path,name)
 return sha(dst)

def start_viewer(repo,work):
 import urllib.request, socket
 for port in range(8179,8188):
  sock=socket.socket();free=False
  try:sock.bind(('127.0.0.1',port));free=True
  except OSError:pass
  finally:sock.close()
  if not free:continue
  log=open(work/'viewer.log','ab',buffering=0)
  proc=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(repo)],
             stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
  time.sleep(.5)
  uri=f'http://127.0.0.1:{port}/review/obsidianti-heavy1-blender-ik-v1.5.1.html'
  try:
   with urllib.request.urlopen(uri,timeout=3) as resp:
    if resp.status==200:return {'url':uri,'status':'HTTP_200_ONLY_NOT_HUMAN_VISUAL_ACCEPTANCE','pid':proc.pid}
  except Exception:pass
  if proc.poll() is None:proc.terminate()
 return {'status':'NO_LOCAL_VIEWER'}

def execute(packet):
 packet=pathlib.Path(packet).resolve();verify_packet(packet)
 print('CAMPAIGN='+VERSION+'\nAUTHORITY=TERMUX_GIT_ONLY\nPACKET_SHA_VERIFIED=YES',flush=True)
 ensure_lfs()
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:7]
 work=pathlib.Path.home()/'.local/state'/VERSION/runid;work.mkdir(parents=True)
 downloads=pathlib.Path.home()/'storage/downloads'
 if not downloads.is_dir():downloads=work
 receipt=downloads/(VERSION+'_'+runid+'_RECEIPT.json')
 status={'campaign':VERSION,'status':'STARTED','stage':'SOURCES','authority':'TERMUX_GIT_ONLY',
   'modelChanged':False,'ownerVisualApproval':False,'expectedModelLfsSha256':MODEL_SHA,
   'nativeLionheartAuditSHA256':DONOR_SHA,'sourceAuditCommit':AUDIT,
   'method':'ACTUAL_BLENDER_NATIVE_IK_CHAIN_WITH_POLE_AND_COPY_ROTATION',
   'badHeavy1FKUsedToInitializeIK':False}
 atomic_json(receipt,status)
 repo=work/'repo';best=None;selected=None
 reports=[];report_paths={};preflight=None
 try:
  env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1';env['GIT_TERMINAL_PROMPT']='0'
  run(['git','clone','--depth=50','--single-branch','--branch','main',REMOTE,str(repo)],timeout=400,env=env)
  originalHead=git(repo,'rev-parse','HEAD').stdout.strip();status['remoteHeadAtStart']=originalHead
  status['rules']=verify_rules(repo)
  if git(repo,'status','--porcelain=v1','--untracked-files=all').stdout.strip():raise RuntimeError('DIRTY_ISOLATED_CHECKOUT')
  if pointer(repo,MODEL)!=MODEL_SHA:raise RuntimeError('PROTECTED_MODEL_SHA_CHANGED')
  replOriginal=git(repo,'rev-parse','HEAD:assets/repl/Repl.glb').stdout.strip();status['protectedReplBlob']=replOriginal
  verify_source(repo)
  existing=[name for name in FILES if (repo/name).exists()]
  if existing and (len(existing)!=len(FILES) or any(sha(repo/name)!=sha(packet/name) for name in FILES)):
   raise RuntimeError('VERSIONED_SOURCE_PATH_COLLISION '+repr(existing))
  if not existing and (repo/REPORT).exists():raise RuntimeError('NEW_DIAGNOSTIC_PREFIX_COLLISION')
  if existing and (repo/REPORT).exists():raise RuntimeError('VERSIONED_REPORT_ALREADY_USED_DO_NOT_OVERWRITE')
  status['stage']='FETCH_ACTUAL_CANONICAL_BINARY';atomic_json(receipt,status)
  git(repo,'lfs','pull','--include='+MODEL,'--exclude=',timeout=600)
  if sha(repo/MODEL)!=MODEL_SHA:raise RuntimeError('EXACT_PUBLISHED_CANONICAL_BINARY_NOT_PRESENT')
  if len(list((repo/'assets/obsidianti').glob('*.glb')))!=1:raise RuntimeError('MULTIPLE_CANONICAL_OBSIDIANTI_MODELS')
  for name in FILES:
   if not (repo/name).exists():
    p=repo/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(packet/name,p)
  status['stage']='REAL_SOURCE_TESTS';atomic_json(receipt,status)
  passed=run([sys.executable,str(repo/TEST),'--repo',str(repo)],timeout=150)
  if 'ALL_TESTS_PASSED' not in passed.stdout:raise RuntimeError('REAL_SOURCE_REGRESSION_FAILED')
  status['tests']=passed.stdout.strip()
  if not existing:
   status['stage']='COMMIT_SOURCE_AND_TESTS_FIRST';atomic_json(receipt,status)
   commitHead=commit(repo,FILES,'Obsidianti: actual Blender IK/pole Heavy1 campaign v1.5.1')
   if not commitHead:raise RuntimeError('SOURCE_COMMIT_NOT_CREATED')
   push(repo,commitHead)
   status['sourceCommitReadback']=commitHead
  else:status['sourceCommitReadback']=originalHead
  if git(repo,'status','--porcelain=v1','--untracked-files=all').stdout.strip():raise RuntimeError('STAGE_AFTER_SOURCE_NOT_CLEAN')
  # Always try actual Blues native IK. Falling back to old FK would be violating the user's request.
  status['stage']='BLENDER_NATIVE_CONSTRAINT_IK_AND_REAL_SKIN_PREFLIGHT';atomic_json(receipt,status)
  # First run uses source amplitude 1 exactly. Only bounded proportional fallback
  # is considered if the real Blender full-skinned solution is unreachable.
  for amp in (1.0,.95,1.05,.9,.85,.8):
   tag=str(amp).replace('.','_');out=work/('blender-ik-'+tag+'.json')
   engineReport=work/('blender-eval-'+tag+'.json');physical=work/('physical-'+tag+'.json')
   candidate=work/('quarantined-heavy1-'+tag+'.glb')
   row={'amplitude':amp,'blenderStatus':'NOT_STARTED','physicalStatus':'NOT_STARTED'}
   blender=run(blender_cmd(repo,work,amp,out,engineReport),timeout=1800,required=False)
   (work/('blender-engine-'+tag+'.log')).write_text(blender.stdout+'\n'+blender.stderr)
   if blender.returncode or not out.exists():
    row['blenderStatus']='FAILED';row['error']=blender.stderr[-1600:]
    reports.append(row);atomic_json(receipt,{**status,'searchProfiles':reports});continue
   row['blenderStatus']='NATIVE_BLENDER_CONSTRAINTS_EVALUATED';row['evaluatedSamplesSHA256']=sha(out)
   test=run([sys.executable,str(repo/APPLY),'--model',str(repo/MODEL),'--math-helper',str(repo/MATH),
         '--native-ik-samples',str(out),'--source',str(repo/DONOR),'--report',str(physical),'--out',str(candidate)],timeout=1200,required=False)
   (work/('skinning-'+tag+'.log')).write_text(test.stdout+'\n'+test.stderr)
   if physical.exists():
    r=js(physical);row['physicalStatus']=r.get('status');row['metrics']=r.get('metrics');row['failures']=r.get('failures');row['physicalProbeCount']=r.get('physicalProbeCount')
   else:row['physicalStatus']='APPLY_FAILED_BEFORE_REPORT';row['error']=test.stderr[-1600:]
   reports.append(row);report_paths[tag]={'blender':out,'physical':physical,'engine':engineReport}
   atomic_json(receipt,{**status,'searchProfiles':reports})
   if test.returncode==0 and candidate.exists() and physical.exists() and js(physical).get('status')=='PHYSICAL_PREFLIGHT_PASSED_CANDIDATE_ONLY':
    selected=row;best=candidate;preflight=physical;break
  status['searchProfiles']=reports
  if not best:
   status['status']='BLOCKED_TRUE_BLENDER_IK_OR_SKIN_PREFLIGHT_MODEL_UNCHANGED'
   raise RuntimeError('NO_FULLY_VALID_HEAVY1_BLENDER_IK_SOLVE')
  status['selectedAmplitude']=selected['amplitude']
  status['candidateSha256']=sha(best)
  status['changedTracks']=test_candidate_guard(repo,repo/MODEL,best)
  if sha(repo/MODEL)!=MODEL_SHA:raise RuntimeError('MODEL_CHANGED_DURING_QUARANTINED_PREFLIGHT')
  if git(repo,'rev-parse','HEAD:assets/repl/Repl.glb').stdout.strip()!=replOriginal:raise RuntimeError('PROTECTED_REPL_CHANGED')
  evidence=repo/REPORT
  if evidence.exists():raise RuntimeError('REPORT_ALREADY_EXISTS_AT_PUBLICATION')
  evidence.mkdir(parents=True)
  shutil.copyfile(preflight,evidence/'physical-preflight.json')
  shutil.copyfile(report_paths[str(selected['amplitude']).replace('.','_')]['blender'],evidence/'blender-native-evaluated.json')
  atomic_json(evidence/'candidate-provenance.json',{'inputModel':MODEL_SHA,'candidate':sha(best),
    'selectedAmplitude':selected['amplitude'],'sourceHead':originalHead,'allProfiles':reports})
  status['stage']='INSTALL_ONLY_AFTER_SUCCESSFUL_REAL_SKINNED_PREFLIGHT';atomic_json(receipt,status)
  tmp=(repo/MODEL).with_name('.obsidianti-blender-ik-'+runid+'.tmp')
  shutil.copyfile(best,tmp)
  if sha(tmp)!=status['candidateSha256']:raise RuntimeError('CANDIDATE_TO_CANONICAL_TEMP_SHA_MISMATCH')
  os.replace(tmp,repo/MODEL)
  if sha(repo/MODEL)!=status['candidateSha256']:raise RuntimeError('MODEL_AFTER_INSTALL_SHA_MISMATCH')
  if git(repo,'check-attr','filter','--',MODEL).stdout.strip().split()[-1]!='lfs':raise RuntimeError('GIT_LFS_MODEL_NOT_ENFORCED')
  changed=[MODEL,*[str(x.relative_to(repo)) for x in evidence.iterdir()]]
  status['stage']='TERMUX_GIT_PUBLISH_SAME_CANONICAL';atomic_json(receipt,status)
  modelCommit=commit(repo,changed,'Obsidianti: Heavy1 Blender evaluated native IK, visual candidate only')
  if not modelCommit or pointer(repo,MODEL)!=status['candidateSha256']:raise RuntimeError('POSTCOMMIT_MODEL_POINTER_WRONG')
  if git(repo,'status','--porcelain=v1').stdout.strip():raise RuntimeError('WORKTREE_NOT_CLEAN_POSTCOMMIT')
  git(repo,'lfs','push','origin','HEAD',timeout=600)
  status['remoteHeadVerified']=push(repo,modelCommit)
  if pointer(repo,MODEL,'refs/remotes/origin/main')!=status['candidateSha256']:raise RuntimeError('REMOTE_MODEL_LFS_OID_NOT_MATCH')
  if git(repo,'rev-parse','refs/remotes/origin/main:assets/repl/Repl.glb').stdout.strip()!=replOriginal:raise RuntimeError('REMOTE_REPL_MODIFIED')
  status['modelChanged']=True;status['status']='HEAVY1_BLENDER_NATIVE_IK_PUBLISHED_CANDIDATE_VISUAL_PENDING'
  status['viewer']=start_viewer(repo,work)
  atomic_json(receipt,status)
  print('STATUS='+status['status']+'\nREMOTE_HEAD='+modelCommit+'\nCANONICAL_SHA256='+status['candidateSha256'],flush=True)
  if status['viewer'].get('url'):print('VIEWER='+status['viewer']['url'],flush=True)
  return 0
 except Exception as exception:
  status['error']=str(exception)
  if not status.get('modelChanged'):
   status['status']=status['status'] if status['status'].startswith('BLOCKED') else 'BLOCKED_NO_MODEL_PUBLICATION'
  # The existing authoring source is durable, but the failure ALSO receives
  # real Git evidence through the same authorized Termux lane when safe.
  try:
   if repo.is_dir() and (repo/MODEL).exists() and sha(repo/MODEL)==MODEL_SHA and not (repo/REPORT).exists() and reports:
    evidence=repo/REPORT;evidence.mkdir(parents=True)
    atomic_json(evidence/'preflight-failed.json',{'status':status['status'],'profiles':reports,'modelUnchanged':True,'reason':str(exception)})
    attempted=commit(repo,[str((evidence/'preflight-failed.json').relative_to(repo))],
        'Obsidianti: preserve failed true Blender IK Heavy1 diagnostic; no model change')
    if attempted:
     status['failureDiagnosticRemoteCommit']=push(repo,attempted)
     if pointer(repo,MODEL,'refs/remotes/origin/main')!=MODEL_SHA:raise RuntimeError('FAILURE_REPORT_MODEL_OID_CHANGED')
     status['failedModelRemoteConfirmedUnchanged']=True
  except Exception as persist:
   status['failureDiagnosticSaveError']=str(persist)
  atomic_json(receipt,status)
  print('STATUS='+status['status']+'\nSTAGE='+status['stage']+'\nERROR='+str(exception)+'\nRECEIPT='+str(receipt),flush=True)
  return 2
 finally:
  try:
   files={'receipt.json':receipt}
   for x in sorted(work.glob('blender-engine-*.log')):files[x.name]=x
   for x in sorted(work.glob('skinning-*.log')):files[x.name]=x
   for x in sorted(work.glob('blender-eval-*.json')):files[x.name]=x
   for x in sorted(work.glob('physical-*.json')):files[x.name]=x
   archive=downloads/(VERSION+'_'+runid+'_HANDOFF.zip')
   digest=write_evidence_zip(archive,files)
   status['handoffZip']=str(archive);status['handoffSha256']=digest
   atomic_json(receipt,status)
   print('HANDOFF_ZIP='+str(archive)+'\nHANDOFF_SHA256='+digest+'\nRECEIPT='+str(receipt),flush=True)
  except Exception as err:print('HANDOFF_FAILED='+str(err),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--packet',required=True);a=p.parse_args()
 sys.exit(execute(pathlib.Path(a.packet)))
