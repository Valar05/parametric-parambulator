#!/usr/bin/env python3
"""One-shot isolated Termux Git campaign; inspect published IK via baked GLB; copy native blend to Downloads."""
import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time,traceback,urllib.request,zipfile
V='OBSIDIANTI_IK41_PREVIEW_v1.0.5'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
RULES='547c2af52303f4efb718bbf8f82a698110c7bfca'
SOURCE='assets/obsidianti/source/OBSIDIANTI_IK41_EDITABLE_v1.0.3_UNAPPROVED.blend'
SOURCE_SHA='30ad2518a820e6b1770dcced6a46f1f2f91db28af799c60dfa21ab3488cda75e'
OUT='diagnostics/obsidianti/ik41-preview-v1.0.5/OBSIDIANTI_IK41_BAKED_VISUAL_REVIEW_UNAPPROVED.glb'
FILES={'driver.py':'campaigns/'+V+'_driver.py','export.py':'campaigns/'+V+'_export.py','inspect.py':'campaigns/'+V+'_inspect.py',
       'server.py':'campaigns/'+V+'_server.py','viewer.html':'campaigns/'+V+'_viewer.html',
       'README.md':'docs/obsidianti/'+V+'.md','LAUNCH.sh':'campaigns/'+V+'_LAUNCH.sh'}
P=pathlib.Path(__file__).resolve().parent;H=pathlib.Path.home();D=H/'storage'/'downloads';D.mkdir(parents=True,exist_ok=True)
RUN=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid())
W=H/'.local'/'state'/V/RUN;W.mkdir(parents=True,exist_ok=False)
R=W/'RECEIPT.json';rec={'campaign':V,'run':RUN,'status':'STARTED','stage':'BOOT','authority':'ISOLATED_TERMUX_GIT_ONLY',
     'sourceSHA256':SOURCE_SHA,'rulesAGENTSblob':RULES,'ownerVisualAcceptance':'PENDING',
     'representation':'BAKED_GLTF_MOTION_NOT_BLENDER_IK_CONTROLS'}
def save():R.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n')
def stage(name):rec['stage']=name;save();print('STAGE='+name,flush=True)
def need(condition,message):
 if not condition:raise RuntimeError(message)
def sha(path):
 h=hashlib.sha256()
 with pathlib.Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def cmd(args,timeout=600,env=None,check=True):
 p=subprocess.run([str(x) for x in args],stdin=subprocess.DEVNULL,capture_output=True,text=True,errors='replace',timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED_'+repr(args[:5])+' '+p.stderr[-1300:]+' '+p.stdout[-650:])
 return p
def git(root,*args,**kw):return cmd(['git','-C',str(root),*args],**kw)
def push(root):
 git(root,'config','lfs.concurrenttransfers','1');env=os.environ.copy();env.update(GOMEMLIMIT='200MiB',GOGC='25')
 p=cmd(['git','-C',str(root),'push','origin','HEAD:refs/heads/main'],timeout=1800,env=env,check=False)
 need(p.returncode==0,'TERMUX_GIT_PUSH_FAILED_'+p.stderr[-1500:])
 head=git(root,'rev-parse','HEAD').stdout.strip();remote=cmd(['git','ls-remote',REMOTE,'refs/heads/main']).stdout.split()[0]
 need(head==remote,'REMOTE_HEAD_READBACK_MISMATCH')
 rec['verifiedRemoteHEAD']=head;save();print('REMOTE_HEAD_VERIFIED='+head,flush=True);return head
def blender(root,script,args):
 native=shutil.which('blender')
 if native:return [native,'--background','--factory-startup','--disable-autoexec','--python',str(root/script),'--',*map(str,args)]
 pd=shutil.which('proot-distro');need(pd,'BLENDER_AND_PROOT_NOT_FOUND')
 for distro in ('obs-arp-blender50','debian'):
  p=cmd([pd,'login',distro,'--','blender','--version'],check=False,timeout=65)
  if p.returncode==0:
   def mapped(path):
    f=pathlib.Path(path).resolve()
    if f.is_relative_to(root.resolve()):return '/mnt/obs-repo/'+str(f.relative_to(root.resolve()))
    if f.is_relative_to(W.resolve()):return '/mnt/obs-work/'+str(f.relative_to(W.resolve()))
    raise RuntimeError('UNBOUND_PROOT_PATH_'+str(f))
   return [pd,'login',distro,'--bind',str(root.resolve())+':/mnt/obs-repo',
           '--bind',str(W.resolve())+':/mnt/obs-work','--','blender','--background',
           '--factory-startup','--disable-autoexec','--python',mapped(root/script),'--',*[mapped(a) for a in args]]
 raise RuntimeError('NO_ALLOWED_BLENDER_RUNTIME')
def downloads(src,filename=None):
 dst=D/(filename or src.name)
 if dst.exists():need(sha(dst)==sha(src),'DOWNLOAD_EXISTING_FILE_SHA_DIFFERS_'+dst.name)
 else:shutil.copyfile(src,dst)
 need(sha(dst)==sha(src),'DOWNLOAD_COPY_HASH_FAILED_'+dst.name)
 return dst
def startserver(root,out):
 stage('SERVE_PREVIEW_LOCALHOST')
 shutil.copyfile(root/FILES['viewer.html'],W/'viewer.html')
 shutil.copyfile(out,W/'model.glb')
 (W/'manifest.json').write_text(json.dumps({'run':RUN,'clipCount':41,'modelSHA256':sha(out)})+'\n')
 (W/'server_config.json').write_text(json.dumps({'root':str(W),'run':RUN,'modelSHA256':sha(out)})+'\n')
 with (W/'VIEWER_SERVER.log').open('ab') as log:
  proc=subprocess.Popen([sys.executable,str(root/FILES['server.py']),'--config',str(W/'server_config.json'),
                         '--ready',str(W/'VIEWER_READY.json'),'--port','9440'],stdin=subprocess.DEVNULL,
                         stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=str(W),close_fds=True)
 for i in range(90):
  if (W/'VIEWER_READY.json').exists():break
  need(proc.poll() is None,'VIEWER_SERVER_EXITED')
  time.sleep(.2)
 need((W/'VIEWER_READY.json').exists(),'VIEWER_NOT_READY')
 ready=json.loads((W/'VIEWER_READY.json').read_text())
 with urllib.request.urlopen('http://127.0.0.1:'+str(ready['port'])+'/health',timeout=15) as resp:health=json.loads(resp.read())
 need(health.get('sha256')==sha(out),'VIEWER_HEALTH_MODEL_WRONG')
 rec['viewerURL']=ready['url'];save();print('VIEWER_URL='+ready['url'],flush=True)
def diagnostics():
 for p in [R,W/'BLENDER_EXPORT.json',W/'GLB_INSPECT.json',W/'BLENDER_EXPORT.log']:
  if p.exists():shutil.copyfile(p,D/(V+'_'+RUN+'_'+p.name))
 out=D/(V+'_'+RUN+'_DIAGNOSTICS.zip')
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for p in [R,W/'BLENDER_EXPORT.json',W/'GLB_INSPECT.json',W/'BLENDER_EXPORT.log']:
   if p.exists():z.write(p,p.name)
 print('DIAGNOSTICS='+str(out),flush=True)
try:
 save();stage('VERIFY_TERMUX_PACKET')
 need(shutil.which('git') and shutil.which('python3') and cmd(['git','lfs','version'],check=False).returncode==0,'TERMUX_GIT_LFS_REQUIRED')
 for f in FILES:need((P/f).is_file(),'PACKET_MISSING_'+f)
 for f in ('driver.py','export.py','inspect.py','server.py'):compile((P/f).read_text(),f,'exec')
 stage('CLONE_ISOLATED_SOURCE_AND_RULES_GATE')
 root=W/'repo';env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1'
 p=cmd(['git','clone','--depth','1','--single-branch','--branch','main','--filter=blob:none',REMOTE,str(root)],env=env,timeout=900,check=False)
 if p.returncode:
  if root.exists():shutil.rmtree(root)
  cmd(['git','clone','--depth','1','--single-branch','--branch','main',REMOTE,str(root)],env=env,timeout=900)
 need(not git(root,'status','--porcelain').stdout.strip(),'GIT_CHECKOUT_DIRTY')
 rec['sourceHEAD']=git(root,'rev-parse','HEAD').stdout.strip();save()
 need(git(root,'rev-parse','HEAD:AGENTS.md').stdout.strip()==RULES,'AGENTS_RULES_CHANGED')
 need('oid sha256:'+SOURCE_SHA in git(root,'show','HEAD:'+SOURCE).stdout,'IK_NATIVE_BLEND_LFS_IDENTITY_CHANGED')
 for p in [*FILES.values(),OUT]:
  need(git(root,'cat-file','-e','HEAD:'+p,check=False).returncode!=0,'VERSIONED_DEST_COLLISION_'+p)
  need(not (root/p).exists(),'WORKTREE_DEST_COLLISION_'+p)
 stage('PUBLISH_VERSIONED_PREVIEW_SOURCES_TERMUX_GIT')
 for local,remote in FILES.items():
  dest=root/remote;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/local,dest)
 git(root,'add','--',*FILES.values());git(root,'commit','-m',V+': inspect exact published IK41 as baked 41-clip viewer')
 rec['sourcePublicationHEAD']=push(root)
 stage('HYDRATE_PUBLISHED_IK41_NATIVE_BLEND_LFS')
 p=git(root,'lfs','pull','--include='+SOURCE,'--exclude=',timeout=1800,check=False)
 need(p.returncode==0,'SOURCE_BLEND_LFS_PULL_FAILED_'+p.stderr[-900:])
 src=root/SOURCE;need(src.is_file() and sha(src)==SOURCE_SHA,'VERIFIED_PUBLISHED_NATIVE_IK_BLEND_MISSING')
 stage('COPY_VERIFIED_NATIVE_BLEND_TO_ANDROID_DOWNLOADS')
 blend=downloads(src)
 rec['nativeBlendDownloads']=str(blend);save()
 print('BLEND_DOWNLOAD='+str(blend)+' SHA256='+sha(blend),flush=True)
 stage('EXPORT_IK_EVALUATED_MOTION_USING_NATIVE_BLENDER')
 out=W/pathlib.Path(OUT).name;report=W/'BLENDER_EXPORT.json'
 p=cmd(blender(root,FILES['export.py'],[src,out,report]),timeout=2700,check=False)
 (W/'BLENDER_EXPORT.log').write_text(p.stdout+'\n'+p.stderr)
 need(p.returncode==0 and out.exists(),'IK_GLTF_EXPORT_FAILED_'+p.stderr[-1500:]+p.stdout[-800:])
 result=json.loads(report.read_text());need(result.get('status')=='IK41_BAKED_41_CLIP_PREVIEW_EXPORTED_UNAPPROVED' and result.get('outputSHA256')==sha(out),'IK_GLTF_EXPORT_AUDIT_INVALID')
 stage('VERIFY_41_CLIP_GLB_STRUCTURE')
 p=cmd([sys.executable,str(root/FILES['inspect.py']),out,W/'GLB_INSPECT.json',sha(out)],timeout=120,check=False)
 need(p.returncode==0,'IK_GLTF_INSPECTION_FAILED_'+p.stderr[-1300:]);print(p.stdout.strip(),flush=True)
 stage('COPY_PREVIEW_GLB_TO_ANDROID_DOWNLOADS')
 model=downloads(out);rec['modelDownloads']=str(model);rec['modelSHA256']=sha(out);save()
 print('MODEL_DOWNLOAD='+str(model)+' SHA256='+sha(out),flush=True)
 startserver(root,out)
 stage('PUBLISH_NEW_REVIEW_GLB_THROUGH_TERMUX_GIT_LFS')
 target=root/OUT;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(out,target)
 need(git(root,'check-attr','filter','--',OUT).stdout.strip().endswith(': lfs'),'PREVIEW_GLB_LFS_ATTRIBUTE_MISSING')
 git(root,'add','--',OUT)
 need('oid sha256:'+sha(out) in git(root,'show',':'+OUT).stdout,'PREVIEW_STAGED_POINTER_WRONG')
 git(root,'commit','-m',V+': evaluated IK41 41-clip GLB for owner visual review')
 rec['modelPublicationHEAD']=push(root)
 need('oid sha256:'+sha(out) in git(root,'show','HEAD:'+OUT).stdout,'PUBLISHED_PREVIEW_POINTER_WRONG')
 rec.update(stage='COMPLETE',status='IK41_BAKED_41_CLIP_VIEWER_RUNNING_AND_GLB_PUBLISHED_VISUAL_PENDING')
 save();print('STATUS='+rec['status']+'\nVIEWER_URL='+rec['viewerURL']+'\nBLEND_DOWNLOAD='+str(blend)+'\nMODEL_DOWNLOAD='+str(model),flush=True)
except BaseException as e:
 rec.update(status='BLOCKED',error=str(e),traceback=traceback.format_exc()[-3500:]);save()
 print('STATUS=BLOCKED '+str(e)+'\nRECEIPT='+str(R),flush=True)
 sys.exit(1)
finally:
 try:diagnostics()
 except Exception as e:print('DIAGNOSTIC_WARNING='+repr(e),flush=True)
