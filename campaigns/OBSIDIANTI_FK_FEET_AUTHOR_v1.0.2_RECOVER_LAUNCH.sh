#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
V=OBSIDIANTI_FK_FEET_AUTHOR_v1.0.2
SELF="$(realpath "$0")"
ENTRY_SHA256="$(sha256sum "$SELF" | cut -d' ' -f1)"
printf 'CAMPAIGN=%s\nAUTHORITY=TERMUX_GIT_ONLY\nENTRY=%s\nENTRY_SHA256=%s\nRECOVERY=EXACT_V100_LOCAL_COMMIT_OR_STAGED_POINTER\n' "$V" "$SELF" "$ENTRY_SHA256"
export PYTHONDONTWRITEBYTECODE=1
python3 - "$SELF" "$ENTRY_SHA256" <<'PY'
import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time,traceback
ENTRY=pathlib.Path(sys.argv[1]);ENTRY_SHA=sys.argv[2]
V='OBSIDIANTI_FK_FEET_AUTHOR_v1.0.2'
OLD='OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
SRC='diagnostics/obsidianti/animation-reunion-v2.0.32/runs/20261107T203838Z-d49615bb/OBSIDIANTI_41_CLIP_SHIELD_LANCE_LIONHEART_ARP_REVIEW_UNAPPROVED.glb'
SRC_SHA='9ff2b5423b4bf5fea1bf67295b52d848803381699fede56164aca9ce65bea9b7'
OUT='assets/obsidianti/source/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_UNAPPROVED.blend'
SCRIPT='campaigns/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.2_RECOVER_LAUNCH.sh'
DOC='docs/obsidianti/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.2_RECOVERY.md'
D=pathlib.Path.home()/'storage'/'downloads'
ST=pathlib.Path.home()/'.local'/'state'/OLD
RECEIPT=D/(V+'_RECOVERY_RECEIPT.json')
V100_MESSAGE=OLD+': independent FK-foot Blender authoring copy, unapproved'
V102_MESSAGE=V+': recover verified FK-foot authoring blend without Blender rebuild'
EXPECTED_REMOTE_SOURCE='7ffaf183bfd9e5902bd1b90fec3b5fc0871a795c'
r={'campaign':V,'authority':'TERMUX_GIT_ONLY','status':'STARTED','stage':'BOOT','source':SRC,'sourceSHA256':SRC_SHA,'entrySHA256':ENTRY_SHA,'AGENTSblob':AGENTS,'visualAcceptance':'PENDING','timestampUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def save():
 D.mkdir(parents=True,exist_ok=True)
 temp=RECEIPT.with_suffix('.json.part');temp.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');temp.replace(RECEIPT)
def stage(s):r['stage']=s;save();print('STAGE='+s,flush=True)
def require(x,msg):
 if not x:raise RuntimeError(msg)
def sha(f):
 h=hashlib.sha256()
 with open(f,'rb') as inp:
  for buf in iter(lambda:inp.read(1024*1024),b''):h.update(buf)
 return h.hexdigest()
def run(args,timeout=180,check=True,env=None):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,errors='replace',stdin=subprocess.DEVNULL,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED_'+repr(args)+'_EXIT_'+str(p.returncode)+'_'+p.stderr[-700:])
 return p
def git(repo,*args,timeout=180,check=True,env=None):return run(['git','-C',str(repo),*args],timeout,check,env)
def out(repo,*args):return git(repo,*args).stdout.strip()
def remote_head():
 x=run(['git','ls-remote',REMOTE,'refs/heads/main'],timeout=90).stdout.split()
 require(len(x)==2 and len(x[0])==40,'REMOTE_MAIN_NOT_VERIFIED');return x[0]
def status_lines(repo):return git(repo,'status','--porcelain=v1','--untracked-files=all').stdout.splitlines()
def pointer(repo,ref):
 p=git(repo,'show',ref,check=False)
 require(p.returncode==0 and 'oid sha256:'+digest in p.stdout,'EXPECTED_BINARY_LFS_POINTER_ABSENT_'+ref)
 return p.stdout
def exact_old_commit(repo,local,upstream):
 require(out(repo,'log','-1','--format=%s')==V100_MESSAGE,'LOCAL_HEAD_NOT_IDENTIFIED_V100_BINARY_COMMIT')
 require(out(repo,'rev-parse','HEAD^')==upstream,'LOCAL_BINARY_COMMIT_PARENT_NOT_CURRENT_REMOTE')
 changed=git(repo,'diff-tree','--no-commit-id','--name-only','-r','HEAD').stdout.strip().splitlines()
 require(changed==[OUT],'LOCAL_BINARY_COMMIT_SCOPE_MISMATCH_'+repr(changed))
 pointer(repo,'HEAD:'+OUT)
 return True
def ensure_download(blend):
 stage('DELIVER_VERIFIED_NATIVE_BLEND_TO_ANDROID_DOWNLOADS')
 dst=D/blend.name
 if dst.exists():require(sha(dst)==digest,'ANDROID_DOWNLOAD_VERSION_COLLISION')
 else:shutil.copyfile(blend,dst)
 require(sha(dst)==digest,'ANDROID_DOWNLOAD_SHA_READBACK_FAILED')
 r['downloadPath']=str(dst);r['downloadSHA256']=digest;save()
 print('DOWNLOAD='+str(dst)+'\nSHA256='+digest,flush=True)
try:
 save()
 require(sha(ENTRY)==ENTRY_SHA,'LAUNCHER_CHANGED')
 require(shutil.which('git') and run(['git','lfs','version'],check=False).returncode==0,'TERMUX_GIT_LFS_REQUIRED')
 stage('RECOVER_INDEPENDENTLY_VERIFIED_V100_BLEND')
 valid=[]
 for rec in sorted(ST.glob('*/RECEIPT.json')):
  try:
   base=rec.parent;bfile=base/'BLENDER_BUILD.json';vfile=base/'BLENDER_VERIFY.json';blend=base/pathlib.Path(OUT).name;repo=base/'repo'
   if not all(p.is_file() for p in (rec,bfile,vfile,blend)) or not (repo/'.git').exists():continue
   old=json.loads(rec.read_text());b=json.loads(bfile.read_text());v=json.loads(vfile.read_text())
   digest0=sha(blend)
   if b.get('status')!='BLENDER_SAVED_UNAPPROVED' or v.get('status')!='REOPENED_FK_FEET_VERIFIED':continue
   if b.get('outputSHA256')!=digest0 or old.get('source')!=SRC or old.get('sourceSHA256')!=SRC_SHA:continue
   valid.append((rec,blend,repo,digest0,old,b,v))
  except (OSError,ValueError,KeyError):continue
 require(valid,'NO_VERIFIED_V100_NATIVE_BLENDER_OUTPUT')
 require(len({x[3] for x in valid})==1,'MULTIPLE_DISTINCT_VERIFIED_BLENDS')
 rec,blend,repo,digest,old,b,v=max(valid,key=lambda x:x[0].stat().st_mtime)
 r.update(priorReceipt=str(rec),priorRun=old.get('run'),blendSHA256=digest,blendBytes=blend.stat().st_size,buildVerified=b['status'],independentReopen=v['status'])
 print('RECOVERED='+str(blend)+'\nSHA256='+digest,flush=True)
 stage('CLASSIFY_EXACT_LOCAL_COMMIT_AND_REMOTE_ANCESTRY')
 require(out(repo,'rev-parse','--is-inside-work-tree')=='true','BAD_ISOLATED_CHECKOUT')
 require(out(repo,'remote','get-url','origin')==REMOTE,'REMOTE_URL_MISMATCH')
 require(out(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'AGENTS_PIN_CHANGED')
 require((repo/'AGENTS.md').is_file(),'MISSING_RULES_IN_CHECKOUT')
 local=out(repo,'rev-parse','HEAD');upstream=remote_head()
 r.update(localBefore=local,remoteBefore=upstream);save()
 # The recovered v1.0.0 source publication SHA is immutable; nonmatching remote heads block.
 if local==upstream:
  require(upstream==EXPECTED_REMOTE_SOURCE or (git(repo,'cat-file','-e','HEAD:'+OUT,check=False).returncode==0 and 'oid sha256:'+digest in git(repo,'show','HEAD:'+OUT).stdout),'UNKNOWN_REMOTE_HEAD')
  mode='SOURCE_COMMIT_WITH_STAGED_BINARY'
 elif out(repo,'log','-1','--format=%s')==V102_MESSAGE:
  # Rerun after a previously committed v1.0.2 recovery: parent must be either source HEAD or verified v1.0.0 binary commit.
  parent=out(repo,'rev-parse','HEAD^')
  require(upstream==parent or upstream==local,'V102_COMMIT_NOT_DIRECTLY_PUBLISHABLE')
  pointer(repo,'HEAD:'+OUT)
  require(sha(repo/SCRIPT)==ENTRY_SHA,'COMMITTED_V102_LAUNCHER_MISMATCH')
  mode='V102_COMMIT_ALREADY_PREPARED'
 else:
  exact_old_commit(repo,local,upstream)
  mode='V100_BINARY_COMMIT_LOCAL_AHEAD_ONE'
 r['recoveryMode']=mode;save();print('RECOVERY_MODE='+mode+'\nLOCAL_HEAD='+local+'\nREMOTE_HEAD='+upstream,flush=True)
 stage('PROVE_REPO_DIRTY_SCOPE_AND_BINARY_IDENTITY')
 tracked=git(repo,'ls-files','--stage','--',OUT).stdout.strip()
 if mode=='SOURCE_COMMIT_WITH_STAGED_BINARY':
  require(git(repo,'cat-file','-e','HEAD:'+OUT,check=False).returncode!=0,'OUTPUT_ALREADY_IN_REMOTE_SOURCE_COMMIT')
  if tracked:pointer(repo,':'+OUT)
 else:pointer(repo,'HEAD:'+OUT)
 target=repo/OUT
 if target.exists():require(sha(target)==digest,'WORKTREE_BINARY_HASH_COLLISION')
 allowed={OUT}
 dirty=status_lines(repo)
 unexpected=[line for line in dirty if line[3:] not in allowed]
 require(not unexpected,'FOREIGN_DIRTY_WORKTREE_'+repr(unexpected[:10]))
 # If old local commit exists, it is not discarded, reset, rebased or amended.
 if mode!='V102_COMMIT_ALREADY_PREPARED':
  require(not (repo/SCRIPT).exists() and not (repo/DOC).exists(),'V102_PATH_ALREADY_EXISTS')
  stage('WRITE_NEW_VERSIONED_RECOVERY_SOURCE')
  dest=repo/SCRIPT;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ENTRY,dest)
  require(sha(dest)==ENTRY_SHA,'LAUNCHER_REPO_READBACK_MISMATCH')
  note=('# Obsidianti FK-foot v1.0.2 verified binary publication recovery\n\n'
        'Only authorized execution lane: isolated Termux Git. The v1.0.0 Blender output and independent native reopen are reused without rebuild.\n\n'
        'v1.0.1 falsely blocked because it did not recognize the legitimate unpushed v1.0.0 binary commit, generated before its Git LFS push was killed.\n'
        'This release requires local v1.0.0 commit to be exactly one commit ahead of the matching verified remote source commit, with exactly the one LFS output path changed, an exact message, parent and SHA.\n'
        'Alternatively the intact verified staged pointer is accepted. Unexpected commits, dirty files and remote changes block; no reset/rebase/stash/force pushes.\n'
        'LFS is configured for one transfer with bounded Go memory; existing verified Blender output is delivered to Android Downloads before network publication.\n'
        'This is a publication recovery only. No canonical GLB or historic 41 clips are modified. Human visual acceptance pending.\n')
  d=repo/DOC;d.parent.mkdir(parents=True,exist_ok=True);d.write_text(note)
  if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(blend,target)
  require(sha(target)==digest,'RESTORED_BINARY_WRONG_HASH')
  require(git(repo,'check-attr','filter','--',OUT).stdout.strip().endswith(': lfs'),'OUTPUT_NOT_LFS_FILTERED')
  env=os.environ.copy();env.update(GOMEMLIMIT='256MiB',GOGC='50',GIT_LFS_CONCURRENT_TRANSFERS='1')
  git(repo,'config','--local','lfs.concurrenttransfers','1')
  stage('STAGE_EXACT_BINARY_AND_RECOVERY_SOURCE')
  git(repo,'add','--',OUT,SCRIPT,DOC,timeout=300,env=env)
  pointer(repo,':'+OUT)
  expected=sorted([SCRIPT,DOC]+([OUT] if mode=='SOURCE_COMMIT_WITH_STAGED_BINARY' else []))
  staged=sorted(git(repo,'diff','--cached','--name-only').stdout.strip().splitlines())
  require(staged==expected,'STAGED_PATHS_OUT_OF_SCOPE_'+repr(staged))
  stage('COMMIT_RECOVERY_WITHOUT_REWRITING_PREVIOUS_COMMIT')
  git(repo,'commit','-m',V102_MESSAGE)
 else:
  env=os.environ.copy();env.update(GOMEMLIMIT='256MiB',GOGC='50',GIT_LFS_CONCURRENT_TRANSFERS='1')
  require(not dirty,'V102_COMMITTED_RETRY_HAS_DIRTY_FILES')
 newhead=out(repo,'rev-parse','HEAD');r['newLocalCommit']=newhead;save()
 pointer(repo,'HEAD:'+OUT)
 # Preserve a user-visible Blender artifact even when Git upload is interrupted.
 ensure_download(blend)
 stage('UPLOAD_EXACT_LFS_OBJECT_WITH_BOUNDED_MEMORY')
 env.update(GIT_LFS_SKIP_SMUDGE='1')
 git(repo,'config','--local','lfs.concurrenttransfers','1')
 lfs_ok=False
 for n in range(3):
  p=git(repo,'lfs','push','origin',newhead,timeout=1200,check=False,env=env)
  if p.returncode==0:lfs_ok=True;break
  r['lastLFSError']=p.stderr[-500:];save();time.sleep(2*(n+1))
 require(lfs_ok,'LFS_UPLOAD_FAILED__BLEND_ALREADY_IN_DOWNLOADS')
 stage('PUSH_AND_REMOTE_EXACT_READBACK')
 now=remote_head()
 if now!=newhead:
  require(now==upstream,'REMOTE_MAIN_MOVED__NO_FORCE_PUSH')
  pushed=False
  for n in range(3):
   p=git(repo,'push','origin','HEAD:refs/heads/main',timeout=600,check=False,env=env)
   if p.returncode==0:pushed=True;break
   if remote_head()==newhead:pushed=True;break
   r['lastPushError']=p.stderr[-600:];save();time.sleep(2*(n+1))
  require(pushed,'GIT_PUSH_FAILED__BLEND_ALREADY_IN_DOWNLOADS')
 require(remote_head()==newhead,'REMOTE_READBACK_HEAD_NOT_OURS')
 # Check the actually published pointer from remote Git API, not merely local HEAD.
 git(repo,'fetch','--no-tags','origin','main',timeout=300,env=env)
 require(out(repo,'rev-parse','FETCH_HEAD')==newhead,'FETCHED_REMOTE_COMMIT_MISMATCH')
 pointer(repo,'FETCH_HEAD:'+OUT)
 r.update(status='BLEND_VERIFIED_GIT_LFS_PUBLISHED_DOWNLOAD_VERIFIED_VISUAL_PENDING',stage='COMPLETE',verifiedRemoteHEAD=newhead)
 save()
 print('STATUS='+r['status']+'\nREMOTE_HEAD='+newhead+'\nDOWNLOAD='+str(D/blend.name)+'\nSHA256='+digest+'\nRECEIPT='+str(RECEIPT),flush=True)
except BaseException as exc:
 r.update(status='BLOCKED',error=str(exc),traceback=traceback.format_exc());save()
 print('STATUS=BLOCKED '+str(exc)+'\nRECEIPT='+str(RECEIPT),flush=True)
 sys.exit(1)
PY
