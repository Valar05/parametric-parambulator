#!/usr/bin/env python3
"""One-command Android Termux Git campaign to recover source-grounded Lionheart stance IK.

Writes only Valar05/parametric-parambulator via Termux Git. Never edits a dirty owner
checkout, never creates another canonical GLB, never modifies Ares or Repl.
"""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,struct,subprocess,sys,time,uuid

VERSION='OBSIDIANTI_CONTACT_IK_v1.3.1'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
REPO='Valar05/parametric-parambulator'
EXPECTED_MAIN='24a4696390f012eb8e4c35173fab802cd6eb6be9'
HISTORICAL='806cf70cdd957312d290d3cdd3d5e0c239f1f5a6'
CURRENT_SHA='f9fc5cef4d2f0b08f2a74e350d3251bc993a861ecbb6a22eda5267a09e4629e6'
HISTORICAL_SHA='5fa8773736cf4fd28eae13e13368246642642a1802d76e47ed7e14faf70d04c0'
SOURCE_BLEND='assets/obsidianti/source/LionheartLancer.blend'
SOURCE_BLEND_SHA='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
CANONICAL='assets/obsidianti/Obsidianti.glb'
FILES=(
 'campaigns/OBSIDIANTI_CONTACT_IK_v1.3.1.sh',
 'campaigns/OBSIDIANTI_CONTACT_IK_RUN_v1.3.1.py',
 'campaigns/OBSIDIANTI_CONTACT_IK_SOLVE_v1.3.1.py',
 'tests/OBSIDIANTI_CONTACT_IK_TEST_v1.3.1.py',
 'docs/obsidianti/CONTACT_IK_v1.3.1.md',
 'review/obsidianti-contact-ik-v1.3.1.html',
)

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def run(args,cwd=None,env=None,timeout=240,required=True):
 p=subprocess.run([str(x) for x in args],cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
 if required and p.returncode:raise RuntimeError('COMMAND_FAILED '+str(args[:5])+' exit='+str(p.returncode)+' '+p.stderr[-1400:])
 return p

def git(repo,args,**kw):return run(['git','-C',str(repo),*args],**kw)

def lfs_oid(repo,revision= 'HEAD'):
 txt=git(repo,['show',revision+':'+CANONICAL]).stdout
 if not txt.startswith('version https://git-lfs.github.com/spec/v1\n'):raise RuntimeError('CANONICAL_LFS_POINTER_MISSING')
 return next(x.split(':',1)[1].strip() for x in txt.splitlines() if x.startswith('oid sha256:'))

def state_write(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');os.replace(tmp,path)

def require_clean(repo,stage):
 s=git(repo,['status','--porcelain=v1','--untracked-files=all']).stdout
 if s.strip():raise RuntimeError('DIRTY_ISOLATED_REPO_'+stage+':'+repr(s[:500]))

def validate_rules(repo):
 path=repo/'AGENTS.md'
 if not path.is_file():raise RuntimeError('RULES_READ_BLOCKED_NO_ACTUAL_AGENTS')
 tracked=git(repo,['ls-files','--error-unmatch','AGENTS.md'],required=False)
 if tracked.returncode:raise RuntimeError('RULES_READ_BLOCKED_UNTRACKED_AGENTS')
 raw=path.read_bytes()
 if run(['git','hash-object','--',str(path)]).stdout.strip()!=git(repo,['rev-parse','HEAD:AGENTS.md']).stdout.strip():
  raise RuntimeError('RULES_READ_BLOCKED_AGENTS_CHANGED')
 text=raw.decode('utf-8');low=text.casefold()
 if '# agents.md' not in low or 'campaign etiquette' not in low or 'termux git' not in low:
  raise RuntimeError('RULES_READ_BLOCKED_INVALID_CONTENT')
 return {'rulesGitBlob':git(repo,['rev-parse','HEAD:AGENTS.md']).stdout.strip(),'rulesSha256':sha(path), 'etiquetteSource':'Home Center CAMPAIGN_ETIQUETTE 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI, author verified 2026-11-04'}

def ensure_lfs():
 if run(['git','lfs','version'],required=False).returncode==0:return
 pkg=shutil.which('pkg')
 if pkg:run([pkg,'install','-y','git-lfs'],timeout=250)
 if run(['git','lfs','version'],required=False).returncode:raise RuntimeError('GIT_LFS_NOT_INSTALLED')

def commit(repo,files,message):
 git(repo,['add','--',*files])
 staged=git(repo,['diff','--cached','--name-only']).stdout.splitlines()
 if any(x not in files for x in staged):raise RuntimeError('UNAPPROVED_STAGED_FILE')
 if not staged:raise RuntimeError('SOURCE_COLLISION_NO_NEW_COMMIT')
 if not git(repo,['config','user.name'],required=False).stdout.strip():git(repo,['config','user.name','Obsidianti Termux Campaign'])
 if not git(repo,['config','user.email'],required=False).stdout.strip():git(repo,['config','user.email','obsidianti-campaign@users.noreply.github.com'])
 git(repo,['commit','-m',message],timeout=180)
 return git(repo,['rev-parse','HEAD']).stdout.strip()

def push(repo,commit_sha):
 # Never force-push, ever. The repo history is the model rollback mechanism.
 p=git(repo,['push','origin','HEAD:refs/heads/main'],required=False,timeout=260)
 if p.returncode:
  if '[rejected]' in p.stderr or 'non-fast-forward' in p.stderr:raise RuntimeError('REMOTE_MOVED_STOP_NO_FORCE')
  if shutil.which('gh'):
   p=run(['git','-C',str(repo),'-c','credential.helper=!gh auth git-credential','push','origin','HEAD:refs/heads/main'],required=False,timeout=260)
  if p.returncode:raise RuntimeError('PUSH_AUTH_OR_NETWORK_FAILED:'+p.stderr[-1100:])
 current=git(repo,['ls-remote','origin','refs/heads/main']).stdout.split()[0]
 if current!=commit_sha:raise RuntimeError('REMOTE_COMMIT_READBACK_DIFFERS')
 return current

def source_sample(repo,work):
 source=repo/SOURCE_BLEND;sampler=repo/'campaigns/OBSIDIANTI_SOURCE_SAMPLER_v1.1.0.py'
 if not sampler.is_file():raise RuntimeError('PINNED_BLENDER_SOURCE_SAMPLER_NOT_AVAILABLE')
 out=work/'native-lionheart-evaluated-world-feet.json'
 native=shutil.which('blender')
 if native:
  args=[native,'--background','--python',str(sampler),'--','--kind','lionheart','--source',str(source),'--out',str(out)]
 else:
  if not shutil.which('proot-distro'):raise RuntimeError('BLENDER_UNAVAILABLE_NATIVE_AND_PROOT')
  args=['proot-distro','login','debian','--bind',str(repo.resolve())+':/mnt/obs-repo','--bind',str(work.resolve())+':/mnt/obs-work',
   '--','blender','--background','--python','/mnt/obs-repo/campaigns/OBSIDIANTI_SOURCE_SAMPLER_v1.1.0.py',
   '--','--kind','lionheart','--source','/mnt/obs-repo/'+SOURCE_BLEND,'--out','/mnt/obs-work/'+out.name]
 p=run(args,required=False,timeout=600)
 (work/'native-blender-source.log').write_text(p.stdout+'\n'+p.stderr)
 if p.returncode or not out.is_file():raise RuntimeError('BLENDER_SOURCE_EVALUATION_FAILED:'+p.stderr[-850:])
 d=json.loads(out.read_text())
 if d.get('sourceKind')!='lionheart' or d.get('actionCount')!=11:
  raise RuntimeError('BLENDER_SOURCE_ACTION_SET_INVALID')
 return out

def start_viewer(repo,work,report):
 import socket,urllib.request
 for port in range(8179,8188):
  s=socket.socket();free=False
  try:s.bind(('127.0.0.1',port));free=True
  except OSError:pass
  finally:s.close()
  if not free:continue
  logfile=open(work/('viewer-'+str(port)+'.log'),'ab',buffering=0)
  try:
   process=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(repo)],stdin=subprocess.DEVNULL,stdout=logfile,stderr=subprocess.STDOUT,start_new_session=True)
   time.sleep(.4)
   url='http://127.0.0.1:'+str(port)+'/review/obsidianti-contact-ik-v1.3.1.html'
   if process.poll() is None:
    try:
     with urllib.request.urlopen(url,timeout=3) as x:
      if x.status==200:return {'url':url,'pid':process.pid,'status':'HTTP_200_NOT_OWNER_VISUAL_VERDICT'}
    except Exception:pass
   if process.poll() is None:process.terminate()
  finally:logfile.close()
 return {'status':'VIEWER_NOT_AVAILABLE','url':None}

def main():
 if len(sys.argv)!=2:raise RuntimeError('USAGE: BASH_ENTRYPOINT_PACKET_DIR')
 packet=pathlib.Path(sys.argv[1]).resolve()
 manifest=json.loads((packet/'manifest.json').read_text())
 if manifest['campaign']!=VERSION or set(manifest['files'])!=set(FILES):raise RuntimeError('PACKET_WRONG_VERSION_OR_FILESET')
 for f,h in manifest['files'].items():
  if not (packet/f).is_file() or sha(packet/f)!=h:raise RuntimeError('PACKET_SOURCE_SHA_MISMATCH:'+f)
 print('CAMPAIGN='+VERSION+'\nLANE=TERMUX_GIT_ONLY\nPACKET_VERIFIED=YES',flush=True)
 ensure_lfs()
 ts=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 work=pathlib.Path.home()/'.local/state'/VERSION/(ts+'-'+uuid.uuid4().hex[:6]);work.mkdir(parents=True)
 pub=pathlib.Path.home()/'storage/downloads';pub=pub if pub.is_dir() else work
 receipt=pub/(VERSION+'_'+work.name+'_RECEIPT.json')
 status={'campaign':VERSION,'canonical':CANONICAL,'status':'STARTED','workdir':str(work),'receipt':str(receipt),'currentSourceSha':CURRENT_SHA,'historicSourceSha':HISTORICAL_SHA,'executionLane':'Termux Git only','ownerVisualAcceptance':'PENDING','replModelChanged':False,'modelCommitPushed':False}
 state_write(receipt,status)
 try:
  env=os.environ.copy();env.update(GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
  repo=work/'repo';status['stage']='READ_ISOLATED_SOURCE'
  run(['git','clone','--depth=1','--branch','main','--single-branch',REMOTE,str(repo)],env=env,timeout=300)
  head=git(repo,['rev-parse','HEAD']).stdout.strip()
  status['mainHeadBefore']=head;status['ruleReadback']=validate_rules(repo)
  print('RULES_READ=PASS\nMAIN_HEAD='+head,flush=True)
  # Allow a safe rerun after THIS exact packet's source-only commit reached
  # main but the real physical preflight later failed. Never accept a different
  # successor: the recorded parent must be the pinned last canonical baseline.
  source_already_committed=False
  if head!=EXPECTED_MAIN:
   parents=[r.split(' ',1)[1].strip() for r in git(repo,['cat-file','-p','HEAD']).stdout.splitlines() if r.startswith('parent ')]
   source_already_committed=(EXPECTED_MAIN in parents and all((repo/q).is_file() and sha(repo/q)==sha(packet/q) for q in FILES))
   if not source_already_committed:raise RuntimeError('MAIN_HEAD_CHANGED_OR_SOURCE_VERSION_COLLISION_'+head)
   status['resumingSameVerifiedSourceCommit']=True
  require_clean(repo,'AFTER_CLONE')
  src_lfs=lfs_oid(repo)
  if src_lfs!=CURRENT_SHA:raise RuntimeError('UNEXPECTED_CANONICAL_MODEL_OID_'+src_lfs)
  repl_before=git(repo,['rev-parse','HEAD:assets/repl/Repl.glb']).stdout.strip()
  # Preflight destination collisions BEFORE any script or model mutation.
  for path in FILES:
   p=repo/path
   if p.exists():
    if not source_already_committed or sha(p)!=sha(packet/path):raise RuntimeError('VERSIONED_CAMPAIGN_PATH_ALREADY_EXISTS:'+path)
   elif source_already_committed:raise RuntimeError('RESUMED_SOURCE_MEMBER_MISSING:'+path)
  status['stage']='FETCH_CURRENT_MODEL_AND_ORIGINAL_BLENDER'
  print('STAGE='+status['stage'],flush=True)
  git(repo,['lfs','pull','--include='+CANONICAL+','+SOURCE_BLEND,'--exclude='],timeout=420)
  if sha(repo/CANONICAL)!=CURRENT_SHA or sha(repo/SOURCE_BLEND)!=SOURCE_BLEND_SHA:
   raise RuntimeError('LFS_MODEL_OR_SOURCE_BYTES_MISMATCH')
  status['sourceBinaryVerified']={'model':CURRENT_SHA,'blender':SOURCE_BLEND_SHA}
  # Recover exact v1.1 pre-pitch pelvis rotation data from Git history.
  status['stage']='FETCH_EXACT_PRE_PITCH_HISTORICAL_MODEL'
  print('STAGE='+status['stage'],flush=True)
  git(repo,['fetch','--no-tags','--depth=1','origin',HISTORICAL],timeout=270)
  if git(repo,['rev-parse',HISTORICAL]).stdout.strip()!=HISTORICAL:raise RuntimeError('HISTORY_HEAD_UNVERIFIED')
  hist=work/'history'
  p=git(repo,['worktree','add','--detach',str(hist),HISTORICAL],env=env,timeout=260,required=False)
  if p.returncode:raise RuntimeError('HISTORICAL_WORKTREE_FAILED:'+p.stderr[-1000:])
  if lfs_oid(hist)!=HISTORICAL_SHA:raise RuntimeError('HISTORICAL_LFS_POINTER_WRONG')
  git(hist,['lfs','pull','--include='+CANONICAL,'--exclude='],timeout=420)
  if sha(hist/CANONICAL)!=HISTORICAL_SHA:raise RuntimeError('HISTORICAL_GLB_BYTES_MISMATCH')
  if git(repo,['rev-parse','HEAD']).stdout.strip()!=head:raise RuntimeError('UNEXPECTED_SOURCE_HEAD_CHANGE')
  # Save the unique versioned reusable script in the actual repository FIRST.
  status['stage']='COMMIT_REUSABLE_IK_SOURCE'
  print('STAGE='+status['stage'],flush=True)
  if not source_already_committed:
   for path in FILES:
    p=repo/path;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(packet/path,p)
   status['scriptCommit']=commit(repo,FILES,'Obsidianti: native-source contact speed and leg-scale-aware retarget IK v1.3.1')
  else:
   status['scriptCommit']=head
   print('REUSING_EXACT_EXISTING_SOURCE_COMMIT='+head,flush=True)
  for path in FILES:
   if git(repo,['hash-object','--',path]).stdout.strip()!=git(repo,['rev-parse','HEAD:'+path]).stdout.strip():raise RuntimeError('SOURCE_SCRIPT_COMMIT_NOT_VERIFIED:'+path)
  require_clean(repo,'AFTER_SCRIPT_COMMIT')
  status['stage']='PUSH_SOURCE_SCRIPT_FIRST'
  print('STAGE='+status['stage'],flush=True)
  push(repo,status['scriptCommit']);status['sourceScriptPushed']=True
  state_write(receipt,status)
  status['stage']='BLENDER_EVALUATE_ALL_ORIGINAL_FOOT_CONTACTS'
  print('STAGE='+status['stage'],flush=True)
  # Recover already-evaluated source exactly from the previous real Termux run,
  # avoiding another Blender pass when the SHA matches the owner's receipt.
  prior=pathlib.Path.home()/'.local/state'/'OBSIDIANTI_CONTACT_IK_v1.3.0'/'20261104T214711Z-30c1a4'/'native-lionheart-evaluated-world-feet.json'
  sample=work/'native-lionheart-evaluated-world-feet.json'
  if prior.is_file() and sha(prior)=='7b17dd51aadc208d9b357b8cafcf4c191ae103223842e007a786e91a3556c4f2':
   shutil.copyfile(prior,sample)
   status['nativeSourceReuse']='VERIFIED_SHA_REUSED_FROM_USER_V130_REAL_RUN'
  else:
   sample=source_sample(repo,work)
   status['nativeSourceReuse']='SAMPLED_REAL_BLENDER_NEW'
  status['nativeSampleSha256']=sha(sample)
  # Preflight on EXACT current canonical bytes, no model write. Guard against
  # returning another synthetic-green + physically-broken campaign.
  solver=repo/'campaigns/OBSIDIANTI_CONTACT_IK_SOLVE_v1.3.1.py'
  historical=hist/CANONICAL;model=repo/CANONICAL;diagnostic=work/'ik-preflight-report.json'
  status['stage']='REAL_SKINNED_IK_PREFLIGHT'
  print('STAGE='+status['stage'],flush=True)
  args=[sys.executable,str(solver),'--model',str(model),'--historical',str(historical),'--source',str(sample),'--report',str(diagnostic)]
  p=run([*args,'--check-only'],env=env,timeout=780,required=False)
  (work/'ik-preflight.log').write_text(p.stdout+'\n'+p.stderr)
  if p.returncode or not diagnostic.exists():
   if diagnostic.is_file():
    failure_report=pub/(VERSION+'_'+work.name+'_IK_DIAGNOSTICS.json')
    shutil.copyfile(diagnostic,failure_report)
    status['diagnosticFileInDownloads']=str(failure_report)
    status['diagnosticSha256']=sha(failure_report)
    try:
     failed=json.loads(diagnostic.read_text()).get('physicsFailures',[])
     status['failedClipNames']=[v.get('clip') for v in failed]
     print('FAILED_CONTACT_CLIPS='+','.join(status['failedClipNames']),flush=True)
    except Exception:pass
   raise RuntimeError('REAL_IK_PREFLIGHT_FAILED:'+p.stderr[-1500:])
  dry=json.loads(diagnostic.read_text())
  source_report=pub/(VERSION+'_'+work.name+'_IK_DIAGNOSTICS.json')
  shutil.copyfile(diagnostic,source_report)
  status['diagnosticFileInDownloads']=str(source_report)
  status['diagnosticSha256']=sha(source_report)
  status['preflightSummary']={'passedSourceActionCount':len(dry.get('perClip',[])), 'profileSummaries':[
    {'clip':m['clip'],'rootVerticalScale':m.get('rootVerticalScaleApplied'),'rootHorizontalScale':m.get('rootHorizontalScaleApplied'),'supportedSoleRMS_m':m['supportedSoleRMS_m']} for m in dry.get('perClip',[])]}
  if dry.get('beforeSha256')!=CURRENT_SHA or sha(model)!=CURRENT_SHA:raise RuntimeError('PREFLIGHT_MUTATED_CURRENT_CANONICAL')
  if len(dry.get('perClip',[]))!=10:raise RuntimeError('PREFLIGHT_DID_NOT_COVER_ALL_LIONHEART')
  # Only now alter the SAME canonical GLB path. Never create a model-per-version.
  status['stage']='PATCH_SAME_CANONICAL_GLB'
  print('STAGE='+status['stage'],flush=True)
  actual=work/'ik-postwrite-report.json'
  p=run([*args[:args.index('--report')+1],str(actual)],env=env,timeout=780,required=False)
  (work/'ik-commit.log').write_text(p.stdout+'\n'+p.stderr)
  if p.returncode or not actual.exists():raise RuntimeError('IK_SAME_PATH_PATCH_FAILED:'+p.stderr[-1500:])
  done=json.loads(actual.read_text())
  if done['candidateByteSha256']!=dry['candidateByteSha256'] or sha(model)!=done['candidateByteSha256']:
   raise RuntimeError('ACTUAL_POSTWRITE_SHA_DIFFERS_FROM_PREFLIGHT')
  status['IKReport']=done
  status['stage']='COMMIT_CANONICAL_NO_NEW_GLB'
  if len(list((repo/'assets/obsidianti').glob('*.glb')))!=1:raise RuntimeError('MULTIPLE_OBSIDIANTI_CANONICAL_MODELS')
  if git(repo,['rev-parse','HEAD:assets/repl/Repl.glb']).stdout.strip()!=repl_before:raise RuntimeError('REPL_MODEL_CHANGED')
  if git(repo,['check-attr','filter','--',CANONICAL]).stdout.strip().split()[-1]!='lfs':raise RuntimeError('CANONICAL_IS_NOT_LFS')
  status['modelCommit']=commit(repo,[CANONICAL],'Obsidianti: restore original Lionheart pelvis and apply source-contact two-bone IK to same GLB')
  if lfs_oid(repo)!=done['candidateByteSha256']:raise RuntimeError('LFS_POSTCOMMIT_OID_MISMATCH')
  require_clean(repo,'AFTER_CANONICAL_COMMIT')
  state_write(receipt,status)
  status['stage']='PUSH_CANONICAL_AND_VERIFY_REMOTE'
  print('STAGE='+status['stage'],flush=True)
  git(repo,['lfs','push','origin','HEAD'],timeout=420)
  push(repo,status['modelCommit'])
  # Verify readback of remote HEAD and exact model pointer using the same original path.
  git(repo,['fetch','--no-tags','origin','main'],timeout=180)
  if git(repo,['rev-parse','refs/remotes/origin/main']).stdout.strip()!=status['modelCommit']:
   raise RuntimeError('REMOTE_FETCH_NOT_CURRENT')
  if lfs_oid(repo,'refs/remotes/origin/main')!=done['candidateByteSha256']:
   raise RuntimeError('REMOTE_MODEL_OID_NOT_NEW_CANDIDATE')
  if git(repo,['rev-parse','refs/remotes/origin/main:assets/repl/Repl.glb']).stdout.strip()!=repl_before:
   raise RuntimeError('REMOTE_REPL_MODEL_MUTATED')
  status['remoteHeadVerified']=status['modelCommit'];status['remoteModelOidVerified']=done['candidateByteSha256'];status['modelCommitPushed']=True
  status['remoteModelBinaryIndependentReadback']='LFS_OID_ONLY; full blob byte download unverified'
  status['viewer']=start_viewer(repo,work,done)
  status['status']='PUBLISHED_IK_CANDIDATE_NEEDS_OWNER_VISUAL_VERDICT'
  state_write(receipt,status)
  print('STATUS='+status['status']+'\nREMOTE_HEAD='+status['modelCommit']+'\nMODEL_SHA256='+done['candidateByteSha256']+'\nRECEIPT='+str(receipt),flush=True)
  if status['viewer'].get('url'):print('REVIEW_URL='+status['viewer']['url'],flush=True)
  return 0
 except Exception as exc:
  status['status']='BLOCKED_NO_MODEL_SUCCESS';status['error']=str(exc)
  state_write(receipt,status)
  print('STATUS=BLOCKED\nSTAGE='+status.get('stage','unknown')+'\nREASON='+str(exc)+'\nRECEIPT='+str(receipt),flush=True)
  return 2
if __name__=='__main__':sys.exit(main())
