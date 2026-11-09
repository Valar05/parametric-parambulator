#!/usr/bin/env python3
"""One-invocation remote Git-owned IK41 verify/publish recovery. No rebuilding or rewriting .blend."""
import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time,traceback,zipfile
VERSION='OBSIDIANTI_IK41_REOPEN_RECOVERY_v1.0.2'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
SOURCE='assets/obsidianti/source/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_UNAPPROVED.blend'
SOURCE_SHA='30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27'
CAND_SHA='f594543e098f553d02f09d7dcbdcd3019bc15181a8d513e64a5d98a0f3ad429a'
CAND='assets/obsidianti/source/OBSIDIANTI_IK41_EDITABLE_v1.0.1_UNAPPROVED.blend'
PRIOR_RUN='20261109T031136Z-9060';OLD_VERSION='OBSIDIANTI_FK_TO_IK_41_v1.0.1'
OLD_SOURCE_COMMIT='fd222204ea43e7efa47516e2aa3647487a7e1925'
FILEMAP={'driver.py':'campaigns/'+VERSION+'_driver.py','verify_reopen.py':'campaigns/'+VERSION+'_verify.py','README.md':'docs/obsidianti/'+VERSION+'.md','LAUNCH.sh':'campaigns/'+VERSION+'_LAUNCH.sh'}
P=pathlib.Path(__file__).resolve().parent;H=pathlib.Path.home();D=H/'storage'/'downloads';D.mkdir(parents=True,exist_ok=True)
RUN=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid())
STATE=H/'.local'/'state'/VERSION/RUN;STATE.mkdir(parents=True,exist_ok=False)
RECEIPT=STATE/'RECEIPT.json';report=STATE/'RECOVERY_VERIFY.json'
r={'launcherSHA256':os.environ.get('OBS_LAUNCHER_SHA256',''), 'campaign':VERSION,'run':RUN,'status':'STARTED','stage':'BOOT','authority':'ISOLATED_TERMUX_GIT_ONLY','rulesAGENTSblob':AGENTS,'rulesCampaignEtiquette':'HomeCenter live read by assistant 2026-11-08','candidateSHA256':CAND_SHA,'sourceSHA256':SOURCE_SHA,'ownerVisualAcceptance':'PENDING'}
def sha(f):
 d=hashlib.sha256()
 with open(f,'rb') as fh:
  for chunk in iter(lambda:fh.read(1024*1024),b''):d.update(chunk)
 return d.hexdigest()
def need(x,msg):
 if not x:raise RuntimeError(msg)
def save():RECEIPT.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
def stage(s):r['stage']=s;save();print('STAGE='+s,flush=True)
def call(cmd,timeout=600,env=None,check=True):
 p=subprocess.run([str(x) for x in cmd],capture_output=True,text=True,errors='replace',stdin=subprocess.DEVNULL,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED_'+repr(cmd[:6])+'_'+p.stderr[-950:]+'_'+p.stdout[-500:])
 return p
def git(root,*args,**kw):return call(['git','-C',str(root),*args],**kw)
def push(root):
 git(root,'config','lfs.concurrenttransfers','1');env=os.environ.copy();env.update({'GOMEMLIMIT':'200MiB','GOGC':'25'})
 p=call(['git','-C',str(root),'push','origin','HEAD:refs/heads/main'],timeout=1700,check=False,env=env)
 need(p.returncode==0,'TERMUX_GIT_PUSH_FAILED_'+p.stderr[-1500:])
 local=git(root,'rev-parse','HEAD').stdout.strip()
 remote=call(['git','ls-remote',REMOTE,'refs/heads/main']).stdout.split()[0]
 need(local==remote,'REMOTE_HEAD_READBACK_NOT_EQUAL_'+local+'_'+remote)
 print('REMOTE_HEAD_VERIFIED='+remote,flush=True);r['remoteHEAD']=remote;save();return remote
def blender(root,script,args):
 native=shutil.which('blender')
 if native:return [native,'--background','--factory-startup','--disable-autoexec','--python',str(root/script),'--',*map(str,args)]
 pd=shutil.which('proot-distro');need(pd,'BLENDER_NOT_FOUND_TERMUX_OR_PROOT')
 for distro in ('obs-arp-blender50','debian'):
  if call([pd,'login',distro,'--','blender','--version'],check=False,timeout=60).returncode==0:
   def trans(file):
    file=pathlib.Path(file).resolve()
    if file.is_relative_to(root.resolve()):return '/mnt/obs-repo/'+str(file.relative_to(root.resolve()))
    if file.is_relative_to(STATE.resolve()):return '/mnt/obs-state/'+str(file.relative_to(STATE.resolve()))
    raise RuntimeError('UNMAPPED_BLENDER_PATH_'+str(file))
   return [pd,'login',distro,'--bind',str(root.resolve())+':/mnt/obs-repo',
    '--bind',str(STATE.resolve())+':/mnt/obs-state','--','blender','--background','--factory-startup','--disable-autoexec',
    '--python',trans(root/script),'--',*[trans(x) for x in args]]
 raise RuntimeError('BLENDER_NOT_FOUND_IN_ALLOWED_PROOT')
def snapshots():
 for file in (RECEIPT,report,STATE/'BLENDER_REOPEN.log'):
  if file.is_file():shutil.copyfile(file,D/(VERSION+'_'+RUN+'_'+file.name))
def ziplogs():
 dst=D/(VERSION+'_'+RUN+'_DIAGNOSTICS.zip')
 with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as z:
  for f in (RECEIPT,report,STATE/'BLENDER_REOPEN.log'):
   if f.is_file():z.write(f,f.name)
 print('DIAGNOSTICS='+str(dst),flush=True)
try:
 save();need(r['launcherSHA256'] and sha(P/'LAUNCH.sh')==r['launcherSHA256'],'LAUNCHER_IDENTITY_MISMATCH');need(shutil.which('git') and shutil.which('git-lfs') and shutil.which('python3'),'TERMUX_GIT_LFS_PYTHON_REQUIRED')
 stage('IDENTIFY_EXACT_PREVIOUS_IK41_CANDIDATE_AND_AUTHOR_RECEIPT')
 previous=H/'.local'/'state'/OLD_VERSION/PRIOR_RUN
 candidate=previous/'OBSIDIANTI_IK41_EDITABLE_v1.0.1_UNAPPROVED.blend'
 audit=previous/'BLENDER_AUTHOR.json'
 need(candidate.is_file() and sha(candidate)==CAND_SHA,'PREVIOUS_NATIVE_IK_BLEND_MISSING_OR_SHA_MISMATCH')
 need(audit.is_file(),'PREVIOUS_BLENDER_AUTHOR_REPORT_MISSING')
 doc=json.loads(audit.read_text())
 need(doc.get('status')=='IK41_NATIVE_BLEND_VERIFIED_POSE_PARITY_OWNER_VISUAL_PENDING' and doc.get('outputSHA256')==CAND_SHA and doc.get('poseParity',{}).get('passed') is True and doc.get('ikActionCount')==41,'ORIGINAL_IK41_AUTHOR_REPORT_NOT_VERIFIED')
 # Independent working copies only. Previously produced candidate remains immutable.
 local_candidate=STATE/candidate.name;local_audit=STATE/audit.name
 shutil.copyfile(candidate,local_candidate);shutil.copyfile(audit,local_audit)
 need(sha(local_candidate)==CAND_SHA,'RECOVERED_IK_BINARY_SHA_READBACK_MISMATCH')
 print('RECOVERED_IK_BLEND='+str(candidate)+' SHA256='+CAND_SHA,flush=True)
 stage('CLONE_FRESH_ISOLATED_TERMUX_GIT_AND_VALIDATE_RULES')
 root=STATE/'repo';env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1'
 p=call(['git','clone','--depth','1','--single-branch','--branch','main','--filter=blob:none',REMOTE,str(root)],timeout=900,check=False,env=env)
 if p.returncode:
  if root.exists():shutil.rmtree(root)
  call(['git','clone','--depth','1','--single-branch','--branch','main',REMOTE,str(root)],timeout=900,env=env)
 need(not git(root,'status','--porcelain').stdout.strip(),'NEW_CHECKOUT_NOT_CLEAN')
 r['sourceHEAD']=git(root,'rev-parse','HEAD').stdout.strip();save()
 need(git(root,'rev-parse','HEAD:AGENTS.md').stdout.strip()==AGENTS,'GOVERNING_AGENTS_CHANGED')
 need('oid sha256:'+SOURCE_SHA in git(root,'show','HEAD:'+SOURCE).stdout,'FK_BASELINE_POINTER_CHANGED')
 need(git(root,'merge-base','--is-ancestor',OLD_SOURCE_COMMIT,'HEAD',check=False).returncode==0 or git(root,'cat-file','-e','HEAD:campaigns/OBSIDIANTI_FK_TO_IK_41_v1.0.1_author.py',check=False).returncode==0,'PRIOR_CAMPAIGN_NOT_IN_GIT_HISTORY')
 for path in list(FILEMAP.values())+[CAND]:
  need(git(root,'cat-file','-e','HEAD:'+path,check=False).returncode!=0,'VERSIONED_DEST_ALREADY_EXISTS_'+path)
  need(not (root/path).exists(),'WORKTREE_FILE_COLLISION_'+path)
 stage('PUBLISH_RECOVERY_SOURCE_VIA_TERMUX_GIT')
 for src,dst in FILEMAP.items():
  orig=P/src;need(orig.is_file(),'MISSING_PACKET_FILE_'+src)
  target=root/dst;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(orig,target)
 need(sha(root/FILEMAP['LAUNCH.sh'])==r['launcherSHA256'],'LAUNCHER_SHA_COPY_CHANGED')
 git(root,'add','--',*FILEMAP.values())
 git(root,'commit','-m',VERSION+': independently audit preserved FK curves and recover saved IK41')
 push(root)
 stage('GIT_LFS_HYDRATE_EXACT_PRESERVED_FK_BASELINE')
 p=git(root,'lfs','pull','--include='+SOURCE,'--exclude=',timeout=1600,check=False)
 need(p.returncode==0,'FK_BASELINE_GIT_LFS_FETCH_FAILED_'+p.stderr[-1200:])
 source=root/SOURCE;need(sha(source)==SOURCE_SHA,'FK_BASELINE_REAL_FILE_SHA_MISMATCH')
 stage('INDEPENDENT_NATIVE_BLENDER_REOPEN_AND_STRICT_CURVE_COMPARISON')
 job=blender(root,FILEMAP['verify_reopen.py'],[source,local_candidate,local_audit,report])
 p=call(job,timeout=1800,check=False)
 (STATE/'BLENDER_REOPEN.log').write_text(p.stdout+'\n'+p.stderr)
 need(p.returncode==0 and report.is_file(),'NATIVE_BLENDER_RECOVERY_AUDIT_FAILED_'+p.stderr[-1400:]+p.stdout[-650:])
 v=json.loads(report.read_text());need(v.get('status')=='VERIFIED_41_IK_NATIVE_REOPEN_OWNER_VISUAL_PENDING' and v.get('fkCurveComparison',{}).get('passed') is True and v.get('actualIKPoseSamples',0)>=123,'NATIVE_REOPEN_AUDIT_NOT_PASSED')
 stage('PRESERVE_VERIFIED_NATIVE_BLEND_IN_ANDROID_DOWNLOADS_BEFORE_GIT_LFS')
 dl=D/local_candidate.name
 if dl.is_file():need(sha(dl)==CAND_SHA,'ANDROID_DOWNLOAD_COLLISION_NOT_VERIFIED')
 else:shutil.copyfile(local_candidate,dl)
 need(sha(dl)==CAND_SHA,'ANDROID_DOWNLOAD_BINARY_CHANGED')
 print('MODEL_DOWNLOAD='+str(dl)+' SHA256='+CAND_SHA,flush=True)
 stage('PUBLISH_RECOVERED_BINARY_TO_NEW_GIT_LFS_PATH_AND_REMOTE_READBACK')
 output=root/CAND;output.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(local_candidate,output)
 need(git(root,'check-attr','filter','--',CAND).stdout.strip().endswith(': lfs'),'LFS_REQUIRED_FOR_BLEND')
 git(root,'add','--',CAND)
 need('oid sha256:'+CAND_SHA in git(root,'show',':'+CAND).stdout,'STAGED_BINARY_LFS_POINTER_INCORRECT')
 git(root,'commit','-m',VERSION+': preserve verified 41-action native IK Blender candidate, visual pending')
 push(root)
 need('oid sha256:'+CAND_SHA in git(root,'show','HEAD:'+CAND).stdout,'REMOTE_PUBLISHED_BINARY_POINTER_INVALID')
 r.update(status='PUBLISHED_IK41_NATIVE_BLEND_VERIFIED_OWNER_VISUAL_PENDING',stage='COMPLETE',
  publishedBlend=CAND,downloadPath=str(dl),reopenComparison=v['fkCurveComparison'],reopenIKWorst=v['actualIKWorst'],reopenIKPoseSamples=v['actualIKPoseSamples'])
 save();snapshots()
 print('STATUS='+r['status']+'\nREPO_OUTPUT='+CAND+'\nSHA256='+CAND_SHA+'\nREMOTE_HEAD='+r['remoteHEAD']+'\nRECEIPT='+str(RECEIPT),flush=True)
except BaseException as exc:
 r.update(status='BLOCKED',error=str(exc),traceback=traceback.format_exc()[-3600:]);save()
 try:snapshots()
 except Exception:pass
 print('STATUS=BLOCKED '+str(exc)+'\nRECEIPT='+str(RECEIPT),flush=True)
 sys.exit(1)
finally:
 try:ziplogs()
 except Exception as exc:print('DIAGNOSTICS_WARNING='+repr(exc),flush=True)
