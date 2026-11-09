#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
VERSION=OBSIDIANTI_FK_TO_IK_41_v1.0.1
SCRIPT_PATH="$(realpath "$0")"
HOME_DIR="$HOME"
export HOME_DIR SCRIPT_PATH VERSION
printf 'CAMPAIGN=%s\nAUTHORITY=ISOLATED_TERMUX_GIT_ONLY\nENTRY=%s\n' "$VERSION" "$SCRIPT_PATH"
sha256sum "$SCRIPT_PATH" | awk '{print "ENTRY_SHA256=" $1}'
command -v python3 >/dev/null || { echo 'BLOCKED=PYTHON3_MISSING'; exit 1; }
command -v git >/dev/null || { echo 'BLOCKED=GIT_MISSING'; exit 1; }
python3 - <<'PY_ENGINE'
from __future__ import annotations
import os,sys,pathlib,hashlib,subprocess,shutil,datetime,time,json,traceback,zipfile,math
V=os.environ['VERSION']; HOME=pathlib.Path(os.environ['HOME_DIR']); ENTRY=pathlib.Path(os.environ['SCRIPT_PATH'])
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
OLD='OBSIDIANTI_FK_TO_IK_41_v1.0.0'; OLD_AUTHOR='campaigns/'+OLD+'_author.py'; OLD_VERIFY='campaigns/'+OLD+'_verify.py'
SOURCE='assets/obsidianti/source/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_UNAPPROVED.blend'
SOURCE_SHA='30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27'
OUT='assets/obsidianti/source/OBSIDIANTI_IK41_EDITABLE_v1.0.1_UNAPPROVED.blend'
A='campaigns/'+V+'_author.py'; VER='campaigns/'+V+'_verify.py'; DOC='docs/obsidianti/'+V+'.md'; CONTRACT='campaigns/'+V+'.contract.json'
LAUNCH='campaigns/'+V+'_LAUNCH.sh'
RUN=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid())
STATE=HOME/'.local'/'state'/V/RUN;STATE.mkdir(parents=True,exist_ok=False)
D=HOME/'storage'/'downloads';D.mkdir(parents=True,exist_ok=True)
R=STATE/'RECEIPT.json';rec={'campaign':V,'run':RUN,'status':'STARTED','stage':'BOOT','authority':'ISOLATED_TERMUX_GIT_ONLY','entrySHA256':'','source':SOURCE,'sourceSHA256':SOURCE_SHA,'output':OUT,'agentsGitBlob':AGENTS,'campaignEtiquetteRead':'LIVE_READ_BY_CHATGPT_2026-11-08','ownerVisualAcceptance':'PENDING','v100Failure':'IK41_ACTUAL_POSE_PARITY_FAILED_80_KNEE_ONLY'}
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for x in iter(lambda:f.read(1<<20),b''):h.update(x)
 return h.hexdigest()
rec['entrySHA256']=sha(ENTRY)
def save():R.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n')
def stage(s):rec['stage']=s;save();print('STAGE='+s,flush=True)
def need(v,s):
 if not v:raise RuntimeError(s)
def run(argv,timeout=600,check=True,env=None):
 p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,errors='replace',stdin=subprocess.DEVNULL,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED_'+repr(argv[:8])+' '+p.stderr[-1600:]+' '+p.stdout[-500:])
 return p
def git(repo,*args,**kw):return run(['git','-C',str(repo),*args],**kw)
def read(repo,path):return git(repo,'show','HEAD:'+path).stdout
def clean(repo):need(not git(repo,'status','--porcelain').stdout.strip(),'DIRTY_ISOLATED_GIT_CHECKOUT')
def remote_readback(repo):
 head=git(repo,'rev-parse','HEAD').stdout.strip()
 for t in range(3):
  p=git(repo,'push','origin','HEAD:refs/heads/main',timeout=1200,check=False)
  if p.returncode==0:break
  if t==2:raise RuntimeError('GIT_PUSH_FAILED_'+p.stderr[-1400:])
  time.sleep(3+t*3)
 remote=run(['git','ls-remote',REMOTE,'refs/heads/main']).stdout.split()[0]
 need(remote==head,'REMOTE_GIT_READBACK_MISMATCH_'+head+'_'+remote)
 rec['remoteHEAD']=head;save();print('REMOTE_HEAD_VERIFIED='+head,flush=True)
 return head
# The original certified author source is used as a version-locked base. This entire
# corrective algorithm is added before its strict parity gate, not by weakening it.
PATCH=r'''
 # Per-frame knee-pole refinement. v1.0.0 set one pole angle per side for all
 # poses. That solves ankles but allows knees to drift 35–65mm at representative
 # frames. Rotate each *animated pole control* around that frame's original hip
 # to ankle axis, seeking the original knee plane; never touch source FK curves.
 audit['stage']='REFINE_INDEPENDENT_KNEE_POLES';record()
 def evaluated_knee(side):
  obj=arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
  return obj.pose.bones['mixamorig:'+side+'Leg'].head.copy()
 def set_pole_world(side,point):
  pb=arm.pose.bones['CTRL_'+side+'_KNEE_POLE']
  mat=pb.matrix.copy();mat.translation=point;pb.matrix=mat
  bpy.context.view_layer.update()
 from mathutils import Quaternion
 corrections={};unsolved=[]
 for name,frames in sampled.items():
  action,slot=new_actions[name];play(arm,action,slot)
  perclip={'corrected':0,'maxBeforeM':0.,'maxAfterM':0.,'worstFrame':None}
  for row in frames:
   t=row['t'];setframe(t)
   for side in ('Left','Right'):
    desired=row['legs'][side];ankle=desired['foot'].translation;hip=desired['hip'];knee=desired['knee']
    start=error(arm,side,desired)['kneeM']
    perclip['maxBeforeM']=max(perclip['maxBeforeM'],start)
    if start<=.004:continue
    axis=ankle-hip
    if axis.length<.05:continue
    axis.normalize()
    target=knee-hip;target-=axis*target.dot(axis)
    current=evaluated_knee(side)-hip;current-=axis*current.dot(axis)
    if target.length<.001 or current.length<.001:continue
    signed=math.atan2(axis.dot(current.cross(target)),current.dot(target))
    pb=arm.pose.bones['CTRL_'+side+'_KNEE_POLE']
    original=pb.matrix.translation.copy()
    best=(start,original.copy())
    # Both signs are tested rather than assuming Blender's IK pole-angle sign.
    for angle in (signed,-signed,signed*.5,-signed*.5,signed*1.5,-signed*1.5):
     candidate=hip+Quaternion(axis,angle)@(original-hip)
     set_pole_world(side,candidate)
     err=error(arm,side,desired)['kneeM']
     if err<best[0]:best=(err,candidate.copy())
    set_pole_world(side,best[1])
    # Iterative signed correction on the best candidate; bounded and deterministic.
    for _ in range(3):
     if best[0]<=.003:break
     cur=evaluated_knee(side)-hip;cur-=axis*cur.dot(axis)
     if cur.length<.001:break
     theta=math.atan2(axis.dot(cur.cross(target)),cur.dot(target))
     base=best[1].copy()
     for a in (theta,-theta,theta*.5,-theta*.5):
      candidate=hip+Quaternion(axis,a)@(base-hip)
      set_pole_world(side,candidate)
      err=error(arm,side,desired)['kneeM']
      if err<best[0]:best=(err,candidate.copy())
     set_pole_world(side,best[1])
    if best[0]<start:
     need(pb.keyframe_insert(data_path='location',frame=t,group='IK41 '+side),'POLE_KEY_WRITE_FAILED_'+name)
     perclip['corrected']+=1
    perclip['maxAfterM']=max(perclip['maxAfterM'],best[0])
    if best[0]>.025 and len(unsolved)<160:
     unsolved.append({'clip':name,'frame':t,'side':side,'kneeBeforeM':start,'kneeAfterM':best[0]})
  corrections[name]=perclip
 audit['kneePoleRefinement']={'perClip':corrections,'firstUnsolved':unsolved,'method':'ANIMATED_KNEE_POLE_GEOMETRIC_BOUNDED_SEARCH'}
 record()
 # Strict original full-pose check follows unchanged. Unsolved frames block.
'''
DOC_TEXT='''# Obsidianti 41 Action FK-to-IK knee pole refinement v1.0.1

Authority: Termux Git only, isolated verified checkout, all original FK Actions preserved. Recovery from 2026-11-09 v1.0.0 real model failure with 80 retained bad samples: ankles ~2 micrometers, feet 0 degrees; right knee 35–65 mm errors. The fixed pole-angle-per-side was insufficient. This version retains one stable pole angle and solves per-frame knee pole positions by bounded geometric rotation around original hip-to-ankle axis. Every resulting controller is keyed into that clip's own copied IK Action. No FK bone keys are changed and no two-handed Sword1 work resumes.

Validate *all 41 Actions* at original, integer, and half-frame poses against the source FK (.012m ankle/.025m knee/3deg foot orientation); after keying, independently reopen native Blender and verify bone constraints, original action signatures and action count. If tolerances fail, publish diagnostics but NOT a successful IK authoring blend. The source binary is pinned to SHA256 30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27. The original 41-clip animations and FK authoring baseline are never overwritten. Genuine Blender runtime, Git LFS readback, and owner visual acceptance are separate gates.
'''
def patched_source(old):
 mark=" audit['stage']='FULL_POSE_PARITY_ON_ACTUAL_IK';record()"
 need(old.count(mark)==1,'V100_AUTHOR_PATCH_ANCHOR_CHANGED')
 need(old.count(" limits={'ankleM':.012,'kneeM':.025,'footDeg':3.0}")==1,'STRICT_LIMIT_ANCHOR_CHANGED')
 need(old.count(" need(not bad,'IK41_ACTUAL_POSE_PARITY_FAILED_")==1,'STRICT_PARITY_GATE_MISSING')
 # PATCH first-line indentation remains within the enclosing try block.
 body=old.replace(mark,PATCH+'\n'+mark)
 return body.replace("V='OBSIDIANTI_FK_TO_IK_41_v1.0.0'","V='OBSIDIANTI_FK_TO_IK_41_v1.0.1'")
def blender_command(root,script,args):
 b=shutil.which('blender')
 if b:return [b,'--background','--factory-startup','--disable-autoexec','--python',str(root/script),'--',*map(str,args)]
 pd=shutil.which('proot-distro');need(pd,'BLENDER_NATIVE_OR_PROOT_REQUIRED')
 for distro in ('obs-arp-blender50','debian'):
  p=run([pd,'login',distro,'--','blender','--version'],timeout=65,check=False)
  if p.returncode==0:
   def trans(path):
    path=pathlib.Path(path).resolve()
    if path.is_relative_to(root.resolve()):return '/mnt/obs-repo/'+str(path.relative_to(root.resolve()))
    if path.is_relative_to(STATE.resolve()):return '/mnt/obs-work/'+str(path.relative_to(STATE.resolve()))
    raise RuntimeError('UNMAPPED_BLENDER_PATH_'+str(path))
   return [pd,'login',distro,'--bind',str(root.resolve())+':/mnt/obs-repo',
           '--bind',str(STATE.resolve())+':/mnt/obs-work','--',
           'blender','--background','--factory-startup','--disable-autoexec',
           '--python',trans(root/script),'--',*[trans(x) for x in args]]
 raise RuntimeError('NO_BLENDER_RUNTIME_NATIVE_OR_PROOT')
def copyverify(a,b):
 b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
def results_snapshot():
 for name,source in [('RECEIPT.json',R),('BLENDER_AUTHOR.json',STATE/'BLENDER_AUTHOR.json'),('BLENDER_REOPEN.json',STATE/'BLENDER_REOPEN.json')]:
  if source.exists():shutil.copyfile(source,D/(V+'_'+RUN+'_'+name))
try:
 save();need(shutil.which('git') and shutil.which('git-lfs') and shutil.which('python3'),'TERMUX_GIT_LFS_PYTHON_REQUIRED')
 stage('CLONE_ISOLATED_AND_VERIFY_AGENTS')
 root=STATE/'repo';env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1'
 p=run(['git','clone','--depth','1','--single-branch','--branch','main','--filter=blob:none',REMOTE,str(root)],timeout=800,check=False,env=env)
 if p.returncode:
  if root.exists():shutil.rmtree(root)
  run(['git','clone','--depth','1','--single-branch','--branch','main',REMOTE,str(root)],timeout=800,env=env)
 clean(root);rec['sourceHEAD']=git(root,'rev-parse','HEAD').stdout.strip()
 need(git(root,'rev-parse','HEAD:AGENTS.md').stdout.strip()==AGENTS,'AGENTS_CHANGED_READ_RULES_AGAIN')
 need('oid sha256:'+SOURCE_SHA in read(root,SOURCE),'FK_SOURCE_LFS_POINTER_CHANGED')
 need(git(root,'rev-parse','HEAD:'+OLD_AUTHOR).stdout.strip()=='197758df10b7dfc82db31ba3cf0b265bcc97e0cd','OLD_AUTHOR_BLOB_CHANGED')
 need(git(root,'rev-parse','HEAD:'+OLD_VERIFY).stdout.strip()=='6bf7ebe565b8edbb59f7e6d0e8299d5e04be041c','OLD_VERIFY_BLOB_CHANGED')
 old=read(root,OLD_AUTHOR);ver=read(root,OLD_VERIFY)
 need('IK41_ACTUAL_POSE_PARITY_FAILED_' in old and 'REOPEN_41_ACTIONS_IK_VERIFIED_VISUAL_PENDING' in ver,'V100_SOURCE_CONTRACT_CHANGED')
 stage('PUBLISH_VERSIONED_SOURCE_VIA_TERMUX_GIT')
 targets=[A,VER,DOC,CONTRACT,LAUNCH,OUT]
 for x in targets:
  need(git(root,'cat-file','-e','HEAD:'+x,check=False).returncode!=0,'DESTINATION_EXISTS_'+x)
  need(not (root/x).exists(),'WORKTREE_COLLISION_'+x)
 files={A:patched_source(old),VER:ver,DOC:DOC_TEXT,
 CONTRACT:json.dumps({'schema':V,'lane':'TERMUX_GIT_ONLY','sourceBlend':SOURCE,'sourceSHA256':SOURCE_SHA,'outputBlend':OUT,'originalActions':41,'ikActions':41,'strictPoseParity':{'ankleM':.012,'kneeM':.025,'footDeg':3.0},'mutation':'NEW_VERSIONED_ONLY','ownerVisualAcceptance':'PENDING'},indent=2)+'\n',
 LAUNCH:ENTRY.read_text()}
 for path,body in files.items():
  dst=root/path;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(body)
 for x in (A,VER):compile(files[x],x,'exec')
 # Assert copied source still includes original actionable failure gate.
 need('need(not bad,' in files[A] and 'kneePoleRefinement' in files[A],'FAILED_SOURCE_PATCH_GATE')
 git(root,'add','--',*files);git(root,'commit','-m',V+': correct per-frame IK knee pole directions with 41 FK actions preserved')
 rec['sourcePublicationHEAD']=remote_readback(root)
 stage('HYDRATE_EXACT_FK_SOURCE_LFS')
 p=git(root,'lfs','pull','--include='+SOURCE,'--exclude=',timeout=1700,check=False)
 need(p.returncode==0,'SOURCE_LFS_FETCH_FAILED_'+p.stderr[-1500:])
 infile=root/SOURCE;need(infile.exists() and sha(infile)==SOURCE_SHA,'FK_SOURCE_BINARY_SHA_MISMATCH')
 print('INPUT_VERIFIED='+SOURCE+' SHA256='+SOURCE_SHA,flush=True)
 stage('BLENDER_41_ACTION_KNEE_POLE_REBUILD')
 outfile=STATE/'OBSIDIANTI_IK41_EDITABLE_v1.0.1_UNAPPROVED.blend';audit=STATE/'BLENDER_AUTHOR.json';verify=STATE/'BLENDER_REOPEN.json'
 job=blender_command(root,A,[infile,outfile,audit])
 p=run(job,timeout=3600,check=False);(STATE/'BLENDER_AUTHOR.log').write_text(p.stdout+'\n'+p.stderr)
 need(p.returncode==0 and outfile.exists(),'NATIVE_BLENDER_AUTHOR_FAILED_'+p.stderr[-1800:]+p.stdout[-800:])
 a=json.loads(audit.read_text());need(a['status']=='IK41_NATIVE_BLEND_VERIFIED_POSE_PARITY_OWNER_VISUAL_PENDING' and a['ikActionCount']==41 and a['poseParity']['passed'] and sha(outfile)==a['outputSHA256'],'AUTHOR_VERIFICATION_NOT_PASSED')
 stage('INDEPENDENT_BLENDER_REOPEN')
 job=blender_command(root,VER,[outfile,audit,verify])
 p=run(job,timeout=1700,check=False);(STATE/'BLENDER_REOPEN.log').write_text(p.stdout+'\n'+p.stderr)
 need(p.returncode==0 and verify.exists(),'BLENDER_REOPEN_FAILED_'+p.stderr[-1300:]+p.stdout[-700:])
 q=json.loads(verify.read_text());need(q['status']=='REOPEN_41_ACTIONS_IK_VERIFIED_VISUAL_PENDING' and q['sha256']==sha(outfile),'REOPEN_DID_NOT_VERIFY')
 stage('DELIVER_ANDROID_DOWNLOAD_BEFORE_GIT_NETWORK')
 dest=D/outfile.name
 if dest.exists():need(sha(dest)==sha(outfile),'DOWNLOAD_HASH_COLLISION')
 else:shutil.copyfile(outfile,dest)
 need(sha(dest)==sha(outfile),'DELIVERED_SHA_MISMATCH')
 rec['downloadPath']=str(dest);rec['outputSHA256']=sha(dest);save();results_snapshot()
 stage('TERMUX_GIT_LFS_PUBLISH_AND_REMOTE_READBACK')
 path=root/OUT;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(outfile,path)
 need(git(root,'check-attr','filter','--',OUT).stdout.strip().endswith(': lfs'),'LFS_FILTER_MISSING')
 git(root,'add','--',OUT);need('oid sha256:'+sha(outfile) in git(root,'show',':'+OUT).stdout,'STAGED_POINTER_MISMATCH')
 git(root,'commit','-m',V+': publish pose-parity-verified native IK 41-action authoring blend')
 git(root,'config','lfs.concurrenttransfers','1')
 env=os.environ.copy();env.update({'GOMEMLIMIT':'200MiB','GOGC':'25'})
 p=run(['git','-C',str(root),'push','origin','HEAD:refs/heads/main'],timeout=1800,check=False,env=env)
 need(p.returncode==0,'GIT_LFS_PUSH_FAILED_'+p.stderr[-1400:])
 head=git(root,'rev-parse','HEAD').stdout.strip()
 remote=run(['git','ls-remote',REMOTE,'refs/heads/main']).stdout.split()[0]
 need(remote==head,'GIT_OUTPUT_READBACK_HEAD_MISMATCH')
 need('oid sha256:'+sha(outfile) in read(root,OUT),'OUTPUT_LFS_POINTER_MISMATCH')
 rec.update(status='IK41_POSE_PARITY_VERIFIED_BINARY_PUBLISHED_OWNER_VISUAL_PENDING',stage='COMPLETE',binaryPublicationHEAD=head,poseParity=a['poseParity'],outputSHA256=sha(outfile))
 save();results_snapshot()
 print('STATUS='+rec['status']+'\nDOWNLOAD='+str(dest)+'\nSHA256='+sha(outfile)+'\nREMOTE_HEAD='+head+'\nRECEIPT='+str(R),flush=True)
except BaseException as exc:
 rec.update(status='BLOCKED',error=str(exc),traceback=traceback.format_exc()[-2900:]);save();results_snapshot()
 print('STATUS=BLOCKED '+str(exc)+'\nRECEIPT='+str(R),flush=True)
 sys.exit(1)
finally:
 try:
  z=D/(V+'_'+RUN+'_DIAGNOSTICS.zip')
  with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as archive:
   for x in [R,STATE/'BLENDER_AUTHOR.json',STATE/'BLENDER_REOPEN.json',STATE/'BLENDER_AUTHOR.log',STATE/'BLENDER_REOPEN.log']:
    if x.exists():archive.write(x,x.name)
  print('DIAGNOSTICS='+str(z),flush=True)
 except Exception as exc:print('DIAGNOSTICS_WRITE_WARNING='+str(exc),flush=True)
PY_ENGINE
