#!/usr/bin/env python3
"""Termux Git only. Git-owned Blender 41-action live IK campaign, single invocation."""
import pathlib,hashlib,os,sys,subprocess,json,shutil,datetime,time,traceback,zipfile
V='OBSIDIANTI_FK_TO_IK_41_v1.0.0'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
RULES='547c2af52303f4efb718bbf8f82a698110c7bfca'
SOURCE='assets/obsidianti/source/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_UNAPPROVED.blend'
SOURCE_SHA='30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27'
DEST='assets/obsidianti/source/OBSIDIANTI_IK41_EDITABLE_v1.0.0_UNAPPROVED.blend'
NAMES={'author.py':'campaigns/'+V+'_author.py','verify.py':'campaigns/'+V+'_verify.py',
 'driver.py':'campaigns/'+V+'_driver.py','README.md':'docs/obsidianti/'+V+'.md',
 'contract.json':'campaigns/'+V+'.contract.json'}
PK=pathlib.Path(__file__).resolve().parent;HOME=pathlib.Path.home()
RUN=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid())
STATE=HOME/'.local'/'state'/V/RUN;STATE.mkdir(parents=True,exist_ok=False)
DOWNLOAD=HOME/'storage'/'downloads';DOWNLOAD.mkdir(parents=True,exist_ok=True)
REC=STATE/'RECEIPT.json'
r={'campaign':V,'runId':RUN,'status':'STARTED','stage':'BOOT','authority':'ISOLATED_TERMUX_GIT_ONLY',
 'input':SOURCE,'inputSHA256':SOURCE_SHA,'output':DEST,'rulesAGENTSblob':RULES,
 'rulesCampaignEtiquette':'HomeCenter doc 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI read live in authoring turn',
 'ownerVisualAcceptance':'PENDING'}
def save():REC.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
def stage(x):r['stage']=x;save();print('STAGE='+x,flush=True)
def need(v,s):
 if not v:raise RuntimeError(s)
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def cmd(argv,timeout=600,check=True,env=None):
 p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,errors='replace',stdin=subprocess.DEVNULL,timeout=timeout,env=env)
 if p.returncode and check:raise RuntimeError('COMMAND_FAILED_'+repr(argv[:7])+'\n'+p.stderr[-2000:]+'\n'+p.stdout[-700:])
 return p
def git(root,*args,check=True,timeout=600):return cmd(['git','-C',str(root),*args],check=check,timeout=timeout)
def clean(root):need(not git(root,'status','--porcelain').stdout.strip(),'ISOLATED_CHECKOUT_DIRTY')
def remotereadback(root):
 head=git(root,'rev-parse','HEAD').stdout.strip()
 p=git(root,'push','origin','HEAD:refs/heads/main',check=False,timeout=900)
 need(p.returncode==0,'TERMUX_GIT_PUSH_BLOCKED_'+p.stderr[-1600:])
 actual=cmd(['git','ls-remote',REMOTE,'refs/heads/main']).stdout.split()[0]
 need(actual==head,'REMOTE_READBACK_HEAD_MISMATCH_'+head+'_'+actual)
 r['verifiedRemoteHEAD']=head;save();print('REMOTE_HEAD_VERIFIED='+head,flush=True)
 return head
def blender_command(root,script,params):
 native=shutil.which('blender')
 if native:return [native,'--background','--factory-startup','--disable-autoexec','--python',str(root/script),'--',*map(str,params)]
 pd=shutil.which('proot-distro');need(pd,'BLENDER_OR_PROOT_NOT_FOUND')
 for distro in ('obs-arp-blender50','debian'):
  p=cmd([pd,'login',distro,'--','blender','--version'],timeout=70,check=False)
  if p.returncode:continue
  def inside(value):
   v=pathlib.Path(value).resolve()
   for start,prefix in ((root,'/mnt/obs-repo'),(STATE,'/mnt/obs-state')):
    try:return prefix+'/'+str(v.relative_to(start.resolve()))
    except ValueError:pass
   raise RuntimeError('BLENDER_PATH_OUTSIDE_AUTHORIZED_RUN_'+str(v))
  return [pd,'login',distro,'--bind',str(root.resolve())+':/mnt/obs-repo',
    '--bind',str(STATE.resolve())+':/mnt/obs-state','--',
    'blender','--background','--factory-startup','--disable-autoexec','--python',inside(root/script),'--',*[inside(x) for x in params]]
 raise RuntimeError('BLENDER_NOT_AVAILABLE_IN_ALLOWED_PROOT')
def safe_copy(input,target):
 target.parent.mkdir(parents=True,exist_ok=True)
 need(not target.exists(),'OUTPUT_PATH_ALREADY_EXISTS_'+str(target))
 shutil.copyfile(input,target)
 need(sha(target)==sha(input),'COPY_SHA_MISMATCH_'+str(target))
def snapshot():
 try:
  destination=DOWNLOAD/(V+'_'+RUN+'_RECEIPT.json');shutil.copyfile(REC,destination);r['downloadsReceipt']=str(destination)
 except Exception:pass
try:
 save();stage('VERIFY_PACKET_AND_RULES')
 spec=json.loads((PK/'contract.json').read_text());need(spec['campaign']==V and spec['inputSHA256']==SOURCE_SHA,'CONTRACT_MISMATCH')
 for src,target in NAMES.items():
  need((PK/src).is_file() and (PK/src).stat().st_size>100,'MISSING_SOURCE_MEMBER_'+src)
  if src.endswith('.py'):compile((PK/src).read_text(),src,'exec')
 stage('CLONE_DISPOSABLE_TERMUX_GIT_CHECKOUT')
 root=STATE/'repo';env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1'
 p=cmd(['git','clone','--depth','1','--branch','main','--single-branch','--filter=blob:none',REMOTE,str(root)],timeout=700,env=env,check=False)
 if p.returncode:
  if root.exists():shutil.rmtree(root)
  cmd(['git','clone','--depth','1','--branch','main','--single-branch',REMOTE,str(root)],timeout=700,env=env)
 clean(root)
 base=git(root,'rev-parse','HEAD').stdout.strip();r['sourceHEAD']=base;save()
 need(git(root,'rev-parse','HEAD:AGENTS.md').stdout.strip()==RULES,'AGENTS_RULES_CHANGED_REAUTHOR_CAMPAIGN')
 need(git(root,'show','HEAD:'+SOURCE).stdout.find('oid sha256:'+SOURCE_SHA)>=0,'PINNED_SOURCE_LFS_POINTER_CHANGED')
 stage('NO_COLLISION_AND_SOURCE_PUBLISH')
 for target in list(NAMES.values())+[DEST]:
  need(git(root,'cat-file','-e','HEAD:'+target,check=False).returncode!=0,'SOURCE_PATH_COLLISION_'+target)
  need(not (root/target).exists(),'WORKTREE_DEST_COLLISION_'+target)
 for src,target in NAMES.items():
  p=root/target;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PK/src,p)
 git(root,'add','--',*NAMES.values());git(root,'commit','-m',V+': independently keyed IK controls for all 41 preserved FK animations')
 source_commit=remotereadback(root);r['sourcePublicationHEAD']=source_commit
 stage('HYDRATE_PINNED_FK_BLENDER_SOURCE')
 p=git(root,'lfs','pull','--include='+SOURCE,'--exclude=',timeout=1600,check=False)
 need(p.returncode==0,'INPUT_LFS_PULL_FAILED_'+p.stderr[-1200:])
 infile=root/SOURCE;need(sha(infile)==SOURCE_SHA,'SOURCE_BLEND_REAL_SHA_MISMATCH')
 print('INPUT_VERIFIED='+SOURCE+' SHA256='+SOURCE_SHA,flush=True)
 stage('BUILD_41_CLIP_NATIVE_BLENDER_IK')
 target=STATE/'OBSIDIANTI_IK41_EDITABLE_v1.0.0_UNAPPROVED.blend'
 audit=STATE/'BLENDER_AUTHOR.json';verify=STATE/'BLENDER_REOPEN.json'
 job=blender_command(root,'campaigns/'+V+'_author.py',[infile,target,audit])
 p=cmd(job,timeout=3600,check=False);(STATE/'BLENDER_AUTHOR.log').write_text(p.stdout+'\n'+p.stderr)
 need(p.returncode==0 and target.is_file(),'NATIVE_BLENDER_AUTHOR_FAILED_'+p.stderr[-1600:]+p.stdout[-1200:])
 a=json.loads(audit.read_text());need(a['status']=='IK41_NATIVE_BLEND_VERIFIED_POSE_PARITY_OWNER_VISUAL_PENDING' and a['ikActionCount']==41 and a['outputSHA256']==sha(target),'IK41_AUTHOR_AUDIT_FAILED')
 stage('INDEPENDENT_NATIVE_BLENDER_REOPEN_AND_POSE_CHECK')
 job=blender_command(root,'campaigns/'+V+'_verify.py',[target,audit,verify])
 p=cmd(job,timeout=2100,check=False);(STATE/'BLENDER_REOPEN.log').write_text(p.stdout+'\n'+p.stderr)
 need(p.returncode==0 and verify.is_file(),'BLENDER_REOPEN_FAILED_'+p.stderr[-1400:]+p.stdout[-1200:])
 q=json.loads(verify.read_text());need(q['status']=='REOPEN_41_ACTIONS_IK_VERIFIED_VISUAL_PENDING' and q['sha256']==sha(target),'REOPEN_RESULT_NOT_VERIFIED')
 stage('DELIVER_LOCAL_NATIVE_BLEND_BEFORE_NETWORK')
 delivered=DOWNLOAD/target.name
 if delivered.exists():need(sha(delivered)==sha(target),'DOWNLOAD_COLLISION_WRONG_SHA')
 else:safe_copy(target,delivered)
 r['downloadBlend']=str(delivered);r['outputSHA256']=sha(target);save()
 stage('PUBLISH_NEW_VERSIONED_BLEND_TERMUX_GIT_LFS')
 dst=root/DEST;safe_copy(target,dst)
 need(git(root,'check-attr','filter','--',DEST).stdout.strip().endswith(': lfs'),'GIT_LFS_NOT_CONFIGURED_FOR_BLEND')
 git(root,'add','--',DEST)
 pointer=git(root,'show',':'+DEST).stdout
 need('oid sha256:'+sha(target) in pointer,'STAGED_LFS_POINTER_WRONG')
 git(root,'commit','-m',V+': IK41 editable native Blend, full pose parity verified, visual pending')
 # Bound Git LFS memory after a previous Termux SIGKILL during LFS push.
 git(root,'config','lfs.concurrenttransfers','1')
 envflags=os.environ.copy();envflags.update({'GOMEMLIMIT':'200MiB','GOGC':'25'})
 p=cmd(['git','-C',str(root),'push','origin','HEAD:refs/heads/main'],timeout=1800,check=False,env=envflags)
 need(p.returncode==0,'LFS_GIT_PUSH_FAILED_'+p.stderr[-1700:])
 head=git(root,'rev-parse','HEAD').stdout.strip();remote=cmd(['git','ls-remote',REMOTE,'refs/heads/main']).stdout.split()[0]
 need(head==remote,'BINARY_REMOTE_HEAD_MISMATCH')
 need('oid sha256:'+sha(target) in git(root,'show','HEAD:'+DEST).stdout,'BINARY_LFS_REMOTE_POINTER_MISMATCH')
 stage('COMPLETE');r.update(status='IK41_PUBLISHED_41_ACTION_POSE_PARITY_VERIFIED_OWNER_VISUAL_PENDING',blendPublicationHEAD=head,blendSHA256=sha(target),
  referenceOriginalSHA256=SOURCE_SHA,fullPoseParity=a['poseParity'],ownerVisualAcceptance='PENDING');save();snapshot()
 print('STATUS='+r['status']+'\nDOWNLOAD='+str(delivered)+'\nSHA256='+sha(target)+'\nREMOTE_HEAD='+head+'\nRECEIPT='+str(REC),flush=True)
except BaseException as exc:
 r.update(status='BLOCKED',error=str(exc),traceback=traceback.format_exc()[-3200:]);save();snapshot()
 print('STATUS=BLOCKED '+str(exc)+'\nRECEIPT='+str(REC),flush=True);sys.exit(1)
finally:
 # Persist a diagnostic ZIP, but never package the huge native binary twice.
 try:
  zpath=DOWNLOAD/(V+'_'+RUN+'_DIAGNOSTICS.zip')
  with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
   for p in (REC,STATE/'BLENDER_AUTHOR.json',STATE/'BLENDER_REOPEN.json',STATE/'BLENDER_AUTHOR.log',STATE/'BLENDER_REOPEN.log'):
    if p.exists():z.write(p,p.name)
  print('DIAGNOSTICS='+str(zpath),flush=True)
 except Exception as e:print('DIAGNOSTICS_WRITE_WARNING='+repr(e),flush=True)
