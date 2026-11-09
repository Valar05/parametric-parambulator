#!/usr/bin/env python3
"""Termux Git only: recover saved IK41, restore missing FK action datablocks, verify, publish."""
import os,sys,pathlib,hashlib,datetime,shutil,subprocess,json,traceback,zipfile
V='OBSIDIANTI_IK41_FK_ACTION_RESTORE_v1.0.3'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
SOURCE='assets/obsidianti/source/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_UNAPPROVED.blend'
SOURCE_SHA='30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27'
OLD_SHA='f594543e098f553d02f09d7dcbdcd3019bc15181a8d513e64a5d98a0f3ad429a'
OLD='OBSIDIANTI_FK_TO_IK_41_v1.0.1';PRIOR_RUN='20261109T031136Z-9060'
DEST='assets/obsidianti/source/OBSIDIANTI_IK41_EDITABLE_v1.0.3_UNAPPROVED.blend'
ROOT=pathlib.Path(__file__).resolve().parent;HOME=pathlib.Path.home();D=HOME/'storage'/'downloads';D.mkdir(parents=True,exist_ok=True)
RUN=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid())
STATE=HOME/'.local'/'state'/V/RUN;STATE.mkdir(parents=True,exist_ok=False)
REC=STATE/'RECEIPT.json';BUILD=STATE/'RESTORE_REPORT.json';VERIFY=STATE/'BLENDER_REOPEN.json'
FILES={
 'driver.py':'campaigns/'+V+'_driver.py',
 'repair.py':'campaigns/'+V+'_repair.py',
 'verify.py':'campaigns/'+V+'_verify.py',
 'README.md':'docs/obsidianti/'+V+'.md',
 'contract.json':'campaigns/'+V+'.contract.json',
 'LAUNCH.sh':'campaigns/'+V+'_LAUNCH.sh',
}
r={'campaign':V,'run':RUN,'status':'STARTED','stage':'BOOT','authority':'ISOLATED_TERMUX_GIT_ONLY','sourceSHA256':SOURCE_SHA,'priorCandidateSHA256':OLD_SHA,'output':DEST,'rulesAGENTSblob':AGENTS,'rulesCampaignEtiquette':'Home Center doc 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI read in authoring turn','ownerVisualAcceptance':'PENDING'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def save():REC.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
def stage(s):r['stage']=s;save();print('STAGE='+s,flush=True)
def need(x,msg):
 if not x:raise RuntimeError(msg)
def call(args,timeout=900,check=True,env=None):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True,errors='replace',stdin=subprocess.DEVNULL,timeout=timeout,env=env)
 if p.returncode and check:raise RuntimeError('COMMAND_FAILED '+repr([str(a) for a in args[:6]])+'\n'+p.stderr[-1400:]+'\n'+p.stdout[-900:])
 return p
def git(root,*args,**kw):return call(['git','-C',str(root),*args],**kw)
def remotehead(root):
 git(root,'config','lfs.concurrenttransfers','1')
 env=os.environ.copy();env.update(GOMEMLIMIT='200MiB',GOGC='25')
 p=call(['git','-C',str(root),'push','origin','HEAD:refs/heads/main'],timeout=1800,env=env,check=False)
 need(p.returncode==0,'GIT_PUSH_FAILED_'+p.stderr[-1500:])
 local=git(root,'rev-parse','HEAD').stdout.strip()
 remote=call(['git','ls-remote',REMOTE,'refs/heads/main']).stdout.split()[0]
 need(local==remote,'REMOTE_HEAD_READBACK_MISMATCH_'+local+'_'+remote)
 r['verifiedRemoteHEAD']=remote;save();print('REMOTE_HEAD_VERIFIED='+remote,flush=True);return remote
def blender(root,script,args):
 native=shutil.which('blender')
 if native:return [native,'--background','--factory-startup','--disable-autoexec','--python',str(root/script),'--',*map(str,args)]
 pd=shutil.which('proot-distro');need(pd,'NO_BLENDER_OR_PROOT')
 for distro in ('obs-arp-blender50','debian'):
  p=call([pd,'login',distro,'--','blender','--version'],timeout=80,check=False)
  if p.returncode==0:
   def mapped(path):
    x=pathlib.Path(path).resolve()
    if x.is_relative_to(root.resolve()):return '/mnt/obs-repo/'+str(x.relative_to(root.resolve()))
    if x.is_relative_to(STATE.resolve()):return '/mnt/obs-work/'+str(x.relative_to(STATE.resolve()))
    raise RuntimeError('PROOT_PATH_NOT_BOUND_'+str(x))
   return [pd,'login',distro,'--bind',str(root.resolve())+':/mnt/obs-repo',
    '--bind',str(STATE.resolve())+':/mnt/obs-work','--','blender','--background','--factory-startup','--disable-autoexec',
    '--python',mapped(root/script),'--',*[mapped(a) for a in args]]
 raise RuntimeError('ALLOWED_BLENDER_RUNTIME_NOT_FOUND')
def copy_checked(a,b,expected):
 need(a.is_file() and sha(a)==expected,'COPY_INPUT_SHA_MISMATCH_'+str(a))
 need(not b.exists(),'OUTPUT_COLLISION_'+str(b))
 b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
 need(sha(b)==expected,'COPY_OUTPUT_SHA_MISMATCH')
def publish_receipts():
 for p in (REC,BUILD,VERIFY,STATE/'RESTORE_BLENDER.log',STATE/'VERIFY_BLENDER.log'):
  if p.is_file():shutil.copyfile(p,D/(V+'_'+RUN+'_'+p.name))
def diagnostics():
 path=D/(V+'_'+RUN+'_DIAGNOSTICS.zip')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for p in (REC,BUILD,VERIFY,STATE/'RESTORE_BLENDER.log',STATE/'VERIFY_BLENDER.log'):
   if p.is_file():z.write(p,p.name)
 print('DIAGNOSTICS='+str(path),flush=True)
try:
 save();need(shutil.which('git') and shutil.which('git-lfs') and shutil.which('python3'),'TERMUX_GIT_LFS_PYTHON_REQUIRED')
 stage('VERIFY_EMBEDDED_PACKET_AND_PRIOR_IK_CANDIDATE')
 for filename in FILES:
  need((ROOT/filename).is_file(),'PACKET_FILE_MISSING_'+filename)
 for f in ('driver.py','repair.py','verify.py'):compile((ROOT/f).read_text(),f,'exec')
 old=HOME/'.local'/'state'/OLD/PRIOR_RUN
 old_candidate=old/'OBSIDIANTI_IK41_EDITABLE_v1.0.1_UNAPPROVED.blend'
 old_author=old/'BLENDER_AUTHOR.json'
 need(old_candidate.is_file() and sha(old_candidate)==OLD_SHA,'PREVIOUS_IK_BINARY_NOT_FOUND_OR_HASH_CHANGED')
 need(old_author.is_file(),'PREVIOUS_IK_BUILD_REPORT_MISSING')
 auth=json.loads(old_author.read_text())
 need(auth.get('status')=='IK41_NATIVE_BLEND_VERIFIED_POSE_PARITY_OWNER_VISUAL_PENDING' and auth.get('outputSHA256')==OLD_SHA and auth.get('ikActionCount')==41 and auth.get('poseParity',{}).get('passed') is True,'PREVIOUS_AUTHOR_REPORT_NOT_VALID')
 candidate=STATE/old_candidate.name;audit=STATE/'BLENDER_AUTHOR.json'
 copy_checked(old_candidate,candidate,OLD_SHA);shutil.copyfile(old_author,audit)
 stage('FRESH_TERMUX_GIT_CLONE_AND_RULES_GATE')
 root=STATE/'repo';env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1'
 p=call(['git','clone','--depth','1','--single-branch','--branch','main','--filter=blob:none',REMOTE,str(root)],timeout=1200,check=False,env=env)
 if p.returncode:
  if root.exists():shutil.rmtree(root)
  call(['git','clone','--depth','1','--single-branch','--branch','main',REMOTE,str(root)],timeout=1200,env=env)
 need(not git(root,'status','--porcelain').stdout.strip(),'GIT_CLONE_DIRTY')
 head=git(root,'rev-parse','HEAD').stdout.strip();r['initialRemoteHEAD']=head;save()
 need(git(root,'rev-parse','HEAD:AGENTS.md').stdout.strip()==AGENTS,'AGENTS_RULES_CHANGED')
 need('oid sha256:'+SOURCE_SHA in git(root,'show','HEAD:'+SOURCE).stdout,'REFERENCE_GIT_LFS_POINTER_CHANGED')
 need(git(root,'cat-file','-e','HEAD:campaigns/OBSIDIANTI_IK41_REOPEN_RECOVERY_v1.0.2_verify.py',check=False).returncode==0,'PRIOR_RECOVERY_SOURCE_NOT_PRESENT')
 for dest in [*FILES.values(),DEST]:
  need(git(root,'cat-file','-e','HEAD:'+dest,check=False).returncode!=0,'GIT_DESTINATION_ALREADY_EXISTS_'+dest)
  need(not (root/dest).exists(),'DISK_DESTINATION_ALREADY_EXISTS_'+dest)
 stage('PUBLISH_VERSIONED_RECOVERY_SOURCES_BY_TERMUX_GIT')
 for source,dest in FILES.items():
  f=root/dest;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source,f)
 git(root,'add','--',*FILES.values())
 git(root,'commit','-m',V+': restore orphaned FK actions without rebuilding IK')
 r['sourcePublicationHEAD']=remotehead(root)
 stage('HYDRATE_EXACT_FK_REFERENCE_BLEND')
 p=git(root,'lfs','pull','--include='+SOURCE,'--exclude=',timeout=1800,check=False)
 need(p.returncode==0,'REFERENCE_LFS_FETCH_FAILED_'+p.stderr[-1200:])
 reference=root/SOURCE;need(reference.is_file() and sha(reference)==SOURCE_SHA,'REFERENCE_FK_SOURCE_SHA_INVALID')
 stage('RESTORE_MISSING_FK_ACTIONS_IN_NEW_BLEND')
 out=STATE/pathlib.Path(DEST).name
 p=call(blender(root,FILES['repair.py'],[reference,candidate,out,BUILD]),timeout=2100,check=False)
 (STATE/'RESTORE_BLENDER.log').write_text(p.stdout+'\n'+p.stderr)
 need(p.returncode==0 and BUILD.exists(),'RESTORE_BLENDER_FAILED_'+p.stderr[-1400:]+p.stdout[-950:])
 q=json.loads(BUILD.read_text());need(q.get('status')=='RESTORED_ACTIONS_SAVED_UNAPPROVED' and out.is_file() and sha(out)==q.get('outputSHA256'),'RESTORE_SAVED_BINARY_INVALID')
 r['newCandidateSHA256']=sha(out);r['actionsRestored']=q['missingCount'];save()
 stage('INDEPENDENT_NATIVE_BLENDER_REOPEN_FK_CURVES_AND_IK_POSES')
 p=call(blender(root,FILES['verify.py'],[reference,out,audit,BUILD,VERIFY]),timeout=2100,check=False)
 (STATE/'VERIFY_BLENDER.log').write_text(p.stdout+'\n'+p.stderr)
 need(p.returncode==0 and VERIFY.is_file(),'INDEPENDENT_REOPEN_PROCESS_FAILED_'+p.stderr[-1400:]+p.stdout[-950:])
 proof=json.loads(VERIFY.read_text())
 need(proof.get('status')=='VERIFIED_41_IK_NATIVE_REOPEN_OWNER_VISUAL_PENDING' and proof.get('fkCurveComparison',{}).get('passed') is True and proof.get('IKClipCount')==41 and proof.get('actualIKPoseSamples',0)>=123,'INDEPENDENT_REOPEN_REPORTED_FAILURE_'+str(proof.get('error')))
 stage('COPY_VERIFIED_NATIVE_BLEND_TO_ANDROID_DOWNLOADS')
 download=D/out.name
 if download.exists():need(sha(download)==sha(out),'ANDROID_DOWNLOAD_COLLISION_WRONG_HASH')
 else:copy_checked(out,download,sha(out))
 r['downloadPath']=str(download);r['newCandidateSHA256']=sha(out);save()
 print('BLEND_DOWNLOAD='+str(download)+' SHA256='+sha(out),flush=True)
 stage('GIT_LFS_PUBLISH_NEW_BLEND_AND_REMOTE_READBACK')
 path=root/DEST;copy_checked(out,path,sha(out))
 need(git(root,'check-attr','filter','--',DEST).stdout.strip().endswith(': lfs'),'BLEND_GIT_LFS_ATTRIBUTE_MISSING')
 git(root,'add','--',DEST)
 need('oid sha256:'+sha(out) in git(root,'show',':'+DEST).stdout,'STAGED_GIT_LFS_POINTER_WRONG')
 git(root,'commit','-m',V+': native 41 IK authoring plus 82 preserved FK action datablocks, visual pending')
 r['binaryPublicationHEAD']=remotehead(root)
 need('oid sha256:'+sha(out) in git(root,'show','HEAD:'+DEST).stdout,'FINAL_GIT_LFS_POINTER_WRONG')
 r.update(status='IK41_FK_ACTIONS_VERIFIED_PUBLISHED_VISUAL_PENDING',stage='COMPLETE',verifiedOriginalFKActions=82,verifiedIKActions=41,originalFKCurvesPreserved=True,ownerVisualAcceptance='PENDING');save()
 print('STATUS='+r['status']+'\nREMOTE_HEAD='+r['binaryPublicationHEAD']+'\nRECEIPT='+str(REC),flush=True)
except BaseException as e:
 r.update(status='BLOCKED',error=str(e),traceback=traceback.format_exc()[-3200:]);save()
 print('STATUS=BLOCKED '+str(e)+'\nRECEIPT='+str(REC),flush=True)
 sys.exit(1)
finally:
 try:publish_receipts();diagnostics()
 except Exception as e:print('DIAGNOSTICS_WARNING='+repr(e),flush=True)
