#!/usr/bin/env python3
"""One-shot authorized Termux Git: Blender FK editable rig -> new GLB -> viewer."""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time,traceback,urllib.request,uuid
V='OBSIDIANTI_FK_FEET_EXPORT_REVIEW_v1.0.0'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
BASE='9069e4928009ebc2403bb5dd9bcbd10563c2feb9'
SOURCE='assets/obsidianti/source/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_UNAPPROVED.blend'
SOURCE_SHA='30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27'
OUT='diagnostics/obsidianti/fk-feet-export-review-v1.0.0/OBSIDIANTI_FK_FEET_41_CLIP_EXPORT_UNAPPROVED.glb'
MEMBERS={
'campaigns/'+V+'_driver.py':'driver.py',
'campaigns/'+V+'_export.py':'export.py',
'campaigns/'+V+'_inspect.py':'inspect.py',
'campaigns/'+V+'_server.py':'server.py',
'campaigns/'+V+'_viewer.html':'viewer.html',
'docs/obsidianti/'+V+'.md':'README.md'}
PACKET=pathlib.Path(__file__).resolve().parent
DOWNLOADS=pathlib.Path.home()/'storage'/'downloads';RUN=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid())
WORK=pathlib.Path.home()/'.local'/'state'/V/RUN;WORK.mkdir(parents=True,exist_ok=False)
RECEIPT=WORK/'RECEIPT.json';r={'campaign':V,'run':RUN,'stage':'BOOT','status':'STARTED',
'authority':'ISOLATED_TERMUX_GIT_ONLY','ownerVisualAcceptance':'PENDING','source':SOURCE,'sourceSHA256':SOURCE_SHA,
'AGENTSblob':AGENTS_BLOB,'CampaignEtiquette':'Home Center doc 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI read at commissioning'}
def save():RECEIPT.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
def stage(s):r['stage']=s;save();print('STAGE='+s,flush=True)
def require(ok,msg):
 if not ok:raise RuntimeError(msg)
def sha(path):
 h=hashlib.sha256()
 with pathlib.Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def run(argv,timeout=300,env=None,ok=True):
 p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,errors='replace',timeout=timeout,stdin=subprocess.DEVNULL,env=env)
 if ok and p.returncode:raise RuntimeError('COMMAND_FAILED '+repr([str(x) for x in argv][:8])+' '+p.stderr[-900:]+' '+p.stdout[-550:])
 return p
def git(root,*args,timeout=300,ok=True):return run(['git','-C',root,*args],timeout=timeout,ok=ok)
def push(root):
 head=git(root,'rev-parse','HEAD').stdout.strip()
 for n in range(3):
  p=git(root,'push','origin','HEAD:refs/heads/main',timeout=900,ok=False)
  if p.returncode==0:break
  if n==2:raise RuntimeError('GIT_PUSH_FAILED_'+p.stderr[-1000:])
  time.sleep(2+n)
 remote=run(['git','ls-remote',REMOTE,'refs/heads/main']).stdout.split()[0]
 require(remote==head,'REMOTE_GIT_READBACK_MISMATCH');r['lastVerifiedHEAD']=head;save();return head
def blender(root,script,items):
 native=shutil.which('blender')
 if native:return [native,'--background','--factory-startup','--disable-autoexec','--python',str(root/script),'--',*map(str,items)]
 pd=shutil.which('proot-distro');require(pd,'BLENDER_NOT_INSTALLED')
 distro=None
 for candidate in ('obs-arp-blender50','debian'):
  try:
   if run([pd,'login',candidate,'--','blender','--version'],timeout=55,ok=False).returncode==0:distro=candidate;break
  except subprocess.TimeoutExpired:pass
 require(distro,'BLENDER_NOT_INSTALLED_IN_KNOWN_PROOT')
 def mp(value):
  path=pathlib.Path(value).resolve()
  if path.is_relative_to(root.resolve()):return '/mnt/obs-repo/'+str(path.relative_to(root.resolve()))
  if path.is_relative_to(WORK.resolve()):return '/mnt/obs-work/'+str(path.relative_to(WORK.resolve()))
  raise RuntimeError('UNMAPPED_BLENDER_PATH_'+str(path))
 return [pd,'login',distro,'--bind',str(root.resolve())+':/mnt/obs-repo','--bind',str(WORK.resolve())+':/mnt/obs-work','--','blender','--background','--factory-startup','--disable-autoexec','--python',mp(root/script),'--',*[mp(x) for x in items]]
def copy_to_downloads(file):
 DOWNLOADS.mkdir(parents=True,exist_ok=True)
 target=DOWNLOADS/pathlib.Path(file).name
 if target.exists():
  require(sha(target)==sha(file),'DOWNLOAD_DEST_COLLISION_'+target.name)
 else:
  shutil.copyfile(file,target)
 require(sha(target)==sha(file),'DOWNLOAD_SHA_MISMATCH');r['downloadPath']=str(target);save();return target
def serve(root,output):
 stage('START_VERSIONED_THREE_JS_VIEWER')
 spec={'run':RUN,'root':str(WORK),'modelSHA256':sha(output)}
 (WORK/'server_config.json').write_text(json.dumps(spec)+'\n')
 server_file=root/('campaigns/'+V+'_server.py')
 log=(WORK/'viewer_server.log').open('ab')
 p=subprocess.Popen([sys.executable,str(server_file),'--config',str(WORK/'server_config.json'),'--ready',str(WORK/'VIEWER_READY.json'),'--port','9380'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=str(WORK),close_fds=True);log.close()
 for _ in range(75):
  file=WORK/'VIEWER_READY.json'
  if file.is_file():break
  if p.poll() is not None:raise RuntimeError('VIEWER_SERVER_EXITED_'+str(p.returncode))
  time.sleep(.2)
 require(file.is_file(),'VIEWER_SERVER_NOT_READY')
 ready=json.loads(file.read_text());health=urllib.request.urlopen('http://127.0.0.1:'+str(ready['port'])+'/health',timeout=10)
 require(json.loads(health.read())['sha256']==sha(output),'VIEWER_HEALTH_SHA_MISMATCH')
 r.update(viewer=ready);save();print('VIEWER_URL='+ready['url'],flush=True)
try:
 save();stage('VALIDATE_PACKET_AND_GIT')
 require(shutil.which('git') and shutil.which('python3'),'GIT_AND_PYTHON_REQUIRED')
 require(run(['git','lfs','version'],ok=False).returncode==0,'GIT_LFS_REQUIRED')
 for dst,src in MEMBERS.items():
  f=PACKET/src;require(f.is_file() and f.stat().st_size>100,'MISSING_PACKET_FILE_'+src)
 for f in ('driver.py','export.py','inspect.py','server.py'):compile((PACKET/f).read_text(),f,'exec')
 env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1'
 root=WORK/'repo';stage('ISOLATED_VERIFIED_GIT_CHECKOUT')
 p=run(['git','clone','--depth','1','--single-branch','--branch','main','--filter=blob:none',REMOTE,str(root)],env=env,timeout=650,ok=False)
 if p.returncode:
  if root.exists():shutil.rmtree(root)
  run(['git','clone','--depth','1','--single-branch','--branch','main',REMOTE,str(root)],env=env,timeout=650)
 require(not git(root,'status','--porcelain').stdout.strip(),'ISOLATED_REPO_DIRTY')
 head=git(root,'rev-parse','HEAD').stdout.strip();r['bootHEAD']=head;save()
 require(head==BASE,'REPOSITORY_HEAD_MOVED_REFUSE_UNREVIEWED_SOURCE_'+head)
 require(git(root,'rev-parse','HEAD:AGENTS.md').stdout.strip()==AGENTS_BLOB,'AGENTS_CHANGED_RULES_REREAD_REQUIRED')
 stage('DESTINATION_COLLISION_GATE')
 for dest in [*MEMBERS,OUT]:
  require(not (root/dest).exists(),'TARGET_EXISTS_'+dest)
  require(git(root,'cat-file','-e','HEAD:'+dest,ok=False).returncode!=0,'GIT_TARGET_ALREADY_TRACKED_'+dest)
 stage('PUBLISH_VERSIONED_CAMPAIGN_SOURCE_TERMUX_GIT')
 for dst,src in MEMBERS.items():
  target=root/dst;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PACKET/src,target)
 git(root,'add','--',*MEMBERS);git(root,'commit','-m',V+': isolated FK authoring rig GLB export viewer')
 r['sourceHEAD']=push(root)
 stage('HYDRATE_SHA_LOCKED_FK_BLEND')
 run(['git','-C',str(root),'-c','lfs.concurrenttransfers=1','lfs','pull','--include='+SOURCE,'--exclude='],timeout=1400)
 blend=root/SOURCE;require(blend.is_file() and sha(blend)==SOURCE_SHA,'PUBLISHED_BLEND_HYDRATION_OR_SHA_FAILED')
 stage('BLENDER_EXPORT_EXISTING_41_CLIP_EDITABLE_RIG')
 output=WORK/pathlib.Path(OUT).name;build=WORK/'BLENDER_EXPORT.json'
 p=run(blender(root,'campaigns/'+V+'_export.py',[blend,output,build]),timeout=2400,ok=False)
 (WORK/'BLENDER_EXPORT.log').write_text(p.stdout+'\n'+p.stderr)
 require(p.returncode==0 and output.is_file(),'BLENDER_GLTF_EXPORT_FAILED_'+p.stdout[-750:]+p.stderr[-1150:])
 proof=json.loads(build.read_text());require(proof['status']=='EXPORTED_FK_EDITABLE_GLTF_REVIEW_PENDING' and proof['outputSHA256']==sha(output),'BLENDER_EXPORT_RECEIPT_INVALID')
 stage('STRUCTURAL_41_CLIP_EXPORT_GATE')
 p=run([sys.executable,str(root/('campaigns/'+V+'_inspect.py')),output,WORK/'GLB_STRUCTURE.json',sha(output)],timeout=120,ok=False)
 require(p.returncode==0,'GLB_EXPORT_INSPECTION_FAILED_'+p.stderr[-1400:]);print(p.stdout.strip(),flush=True)
 # Make the actual GLB user-accessible before performing expensive LFS network upload.
 stage('PUBLISH_GLTF_TO_ANDROID_DOWNLOADS')
 download=copy_to_downloads(output);r.update(modelSHA256=sha(output),modelBytes=output.stat().st_size);save()
 shutil.copyfile(root/('campaigns/'+V+'_viewer.html'),WORK/'viewer.html');shutil.copyfile(output,WORK/'model.glb')
 (WORK/'manifest.json').write_text(json.dumps({'run':RUN,'clipCount':41,'modelSHA256':sha(output),'publishedSourceCommit':r['sourceHEAD']})+'\n')
 serve(root,output)
 stage('PUBLISH_MODEL_TO_GIT_LFS_AND_REMOTE_READBACK')
 target=root/OUT;target.parent.mkdir(parents=True,exist_ok=True)
 require(not target.exists(),'BINARY_DESTINATION_COLLISION')
 shutil.copyfile(output,target)
 require(git(root,'check-attr','filter','--',OUT).stdout.strip().endswith(': lfs'),'GLB_GIT_LFS_ATTRIBUTE_MISSING')
 git(root,'add','--',OUT)
 pointer=git(root,'show',':'+OUT).stdout
 require('oid sha256:'+sha(output) in pointer,'STAGED_LFS_SHA_MISMATCH')
 git(root,'commit','-m',V+': published 41-clip FK editable GLB, visual review pending')
 r['modelHEAD']=push(root)
 pointer=git(root,'show','origin/main:'+OUT).stdout
 require('oid sha256:'+sha(output) in pointer,'REMOTE_LFS_POINTER_NOT_VERIFIED')
 r.update(stage='COMPLETE',status='EXPORTED_41_CLIP_GLB_PUBLISHED_VIEWER_RUNNING_VISUAL_PENDING',visualAcceptance='PENDING')
 save();print('STATUS='+r['status']+'\nMODEL_DOWNLOAD='+str(download)+'\nMODEL_SHA256='+sha(output)+'\nVIEWER_URL='+r['viewer']['url'],flush=True)
except BaseException as err:
 r.update(stage=r.get('stage'),status='BLOCKED',error=str(err),traceback=traceback.format_exc());save()
 print('STATUS=BLOCKED '+str(err)+'\nRECEIPT='+str(RECEIPT),flush=True)
 sys.exit(1)
finally:
 DOWNLOADS.mkdir(parents=True,exist_ok=True)
 destination=DOWNLOADS/(V+'_'+RUN+'_RECEIPT.json')
 if RECEIPT.exists():shutil.copyfile(RECEIPT,destination);print('RECEIPT='+str(destination),flush=True)
