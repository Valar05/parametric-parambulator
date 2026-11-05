#!/usr/bin/env python3
"""One-invocation Android Termux Git existing FK GLB motion IK editor campaign."""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time,uuid,zipfile,traceback,gzip
V='OBSIDIANTI_IK_AUTHORING_v1.9.5'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
SOURCES={'assets/obsidianti/Obsidianti.glb':'8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'}
V156_ZIP_SHA='fc3ca580b82de074f6a2f040e8335baf1351b74a102df389bbaa5dfc85a68c3a'
V156_GLB_SHA='261f10786dd0eb0e80667173e4a893f6822356da628a5907efd6d0bbc2a74ff5'
FILES={'campaigns/OBSIDIANTI_IK_AUTHORING_RUN_v1.9.5.py':'driver.py','campaigns/OBSIDIANTI_IK_AUTHORING_BUILD_v1.9.5.py':'blender_author.py','campaigns/OBSIDIANTI_IK_AUTHORING_VERIFY_v1.9.5.py':'blender_verify.py','docs/obsidianti/IK_AUTHORING_v1.9.5.md':'doc.md'}
DEST='assets/obsidianti/source/Obsidianti_IK_AUTHOR_v1.9.5.blend'
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def cmd(argv,timeout=300,check=True,env=None):
 p=subprocess.run([str(x) for x in argv],text=True,capture_output=True,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+repr([str(x) for x in argv][:5])+' '+p.stderr[-1300:]+' '+p.stdout[-500:])
 return p
def git(repo,*args,**kw):return cmd(['git','-C',str(repo),*args],**kw)
def blender_command(repo,work,script,args):
 b=shutil.which('blender')
 if b:return [b,'--background','--disable-autoexec','--python',str(repo/script),'--',*map(str,args)]
 proot=shutil.which('proot-distro')
 if not proot:raise RuntimeError('BLENDER_UNAVAILABLE_NATIVE_AND_PROOT_DEBIAN')
 rr=repo.resolve();ww=work.resolve()
 def map_path(s):
  s=str(pathlib.Path(s).resolve())
  if s.startswith(str(rr)+'/'):return '/mnt/obs-repo/'+s[len(str(rr))+1:]
  if s.startswith(str(ww)+'/'):return '/mnt/obs-work/'+s[len(str(ww))+1:]
  raise RuntimeError('BLENDER_UNMAPPED_PATH '+s)
 newargs=[map_path(a) if str(a).startswith('/') else str(a) for a in args]
 return [proot,'login','debian','--bind',str(rr)+':/mnt/obs-repo','--bind',str(ww)+':/mnt/obs-work','--','blender','--background','--disable-autoexec','--python',map_path(repo/script),'--',*newargs]
def recover_v156(downloads,work):
 matches=[p for p in downloads.glob('OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.6*_HANDOFF.zip') if sha(p)==V156_ZIP_SHA]
 if len(matches)!=1:raise RuntimeError('EXACT_V156_BASE_HANDOFF_MISSING_OR_AMBIGUOUS')
 with zipfile.ZipFile(matches[0]) as z:
  b=z.read('visual/Candidate_UNAPPROVED.glb')
 if hashlib.sha256(b).hexdigest()!=V156_GLB_SHA:raise RuntimeError('V156_EXACT_CANDIDATE_SHA_MISMATCH')
 p=work/'Obsidianti_v156_verified.glb';p.write_bytes(b)
 return p,matches[0]
def git_pointer(repo,path):
 t=git(repo,'show','HEAD:'+path).stdout
 if not t.startswith('version https://git-lfs.github.com/spec/v1\n'):raise RuntimeError('EXPECTED_GIT_LFS_POINTER '+path)
 return t

def inspect_blend_container(path):
 """Identify modern Blender native/zstd or legacy gzip containers.
 A header is not evidence of semantic validity: only Blender reopen can verify it.
 """
 with open(path,'rb') as f:sig=f.read(12)
 if sig.startswith(b'BLENDER'):return 'UNCOMPRESSED_NATIVE_BLEND'
 if sig.startswith(bytes((0x28,0xb5,0x2f,0xfd))):return 'ZSTANDARD_COMPRESSED_NATIVE_BLEND_REOPEN_REQUIRED'
 if sig.startswith(bytes((0x1f,0x8b))):
  try:
   with gzip.open(path,'rb') as f:
    if f.read(7)==b'BLENDER':return 'LEGACY_GZIP_COMPRESSED_NATIVE_BLEND'
  except (OSError,EOFError) as e:raise RuntimeError('LEGACY_GZIP_BLEND_CORRUPT '+str(e))
 raise RuntimeError('OUTPUT_BLEND_UNRECOGNIZED_MAGIC hex='+sig[:12].hex())

def recover_previous_verified_build(home,work):
 """Recover last valid build output; Blender must still independently reopen it."""
 required={'Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp'}
 for version in ():
  prev=home/'.local/state'/('OBSIDIANTI_IK_AUTHORING_'+version)
  if not prev.is_dir():continue
  matches=[]
  for p in sorted(prev.glob('*/work/Obsidianti_IK_AUTHOR_'+version+'.blend')):
   br=p.parent/'build_report.json'
   if not br.is_file() or not p.is_file() or p.stat().st_size<1024:continue
   try:
    report=json.loads(br.read_text())
    if report.get('status')!='IK_EDIT_AUTHORING_COPY_CREATED_REVIEW_PENDING':continue
    if set(report.get('editableActions',{}))!=required:continue
    typ=inspect_blend_container(p)
    matches.append((p,br,typ))
   except (ValueError,OSError,RuntimeError,KeyError):continue
  if len(matches)>1:raise RuntimeError('AMBIGUOUS_PREVIOUS_NATIVE_BUILD '+version)
  if len(matches)==1:
   p,br,typ=matches[0]
   return {'file':p,'report':br,'container':typ,'sha256':sha(p),'version':version}
 return None

def main(packet,launcher_sha):
 home=pathlib.Path.home();downloads=home/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('TERMUX_DOWNLOADS_NOT_CONFIGURED')
 run=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:7]
 root=home/'.local/state'/V/run;root.mkdir(parents=True,exist_ok=False)
 work=root/'work';work.mkdir();repo=root/'repo'
 receipt=downloads/(V+'_'+run+'_RECEIPT.json')
 state={'version':V,'run':run,'authority':'TERMUX_GIT_ONLY','stage':'BOOT','status':'STARTED','launcherSHA256':launcher_sha,
        'rules':{'agentsExpectedBlob':AGENTS_BLOB,'etiquetteReadByAuthor':'2026-11-05 via Home Center'},'originalBlendChanged':False,'lionheartMotionImported':False,
        'originalGLBChanged':False,'ownerVisualAcceptance':'PENDING'}
 def save():receipt.write_text(json.dumps(state,indent=2,sort_keys=True)+'\n')
 save()
 try:
  state['stage']='VERIFY_INPUT_HANDOFF';save()
  model,handoff=recover_v156(downloads,work)
  state['previewGLB_SHA256']=sha(model);state['previewHandoff']=str(handoff)
  state['stage']='ISOLATED_GIT_CHECKOUT';save()
  env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
  cmd(['git','clone','--depth=25','--single-branch','--branch','main','--config','filter.lfs.smudge=','--config','filter.lfs.required=false',REMOTE,repo],timeout=900,env=env)
  original_head=git(repo,'rev-parse','HEAD').stdout.strip();state['initialRemoteHead']=original_head
  if git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()!=AGENTS_BLOB:raise RuntimeError('AGENTS_LIVE_BLOB_CHANGED_FROM_AUTHOR_READ')
  ag=(repo/'AGENTS.md').read_text()
  if 'Campaign Etiquette' not in ag or 'Termux Git' not in ag:raise RuntimeError('AGENTS_CONTENT_GATE_FAILED')
  if cmd(['git','lfs','version'],check=False).returncode:raise RuntimeError('GIT_LFS_REQUIRED')
  state['stage']='FETCH_AND_VERIFY_UNCHANGED_CANONICAL_GLB';save()
  cmd(['git','-C',repo,'lfs','pull','--include='+','.join(SOURCES),'--exclude='],timeout=1500,env=dict(env,GIT_LFS_SKIP_SMUDGE='0'))
  for p,expected in SOURCES.items():
   if sha(repo/p)!=expected:raise RuntimeError('PINNED_SOURCE_SHA_MISMATCH '+p+' actual='+sha(repo/p))
  state['sourceSHA256']=dict(SOURCES);save()
  state['stage']='PREPUBLICATION_DESTINATION_COLLISION_GATE';save()
  for path in [*FILES,DEST]:
   if (repo/path).exists() or git(repo,'ls-tree','HEAD','--',path).stdout.strip():raise RuntimeError('VERSIONED_DESTINATION_COLLISION '+path)
  state['stage']='PUBLISH_SOURCE_THROUGH_TERMUX_GIT';save()
  for target,src in FILES.items():
   dst=repo/target;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(packet/src,dst)
  git(repo,'add','--',*FILES)
  staged=set(git(repo,'diff','--cached','--name-only').stdout.splitlines())
  if staged!=set(FILES):raise RuntimeError('SOURCE_STAGED_SCOPE_INVALID '+str(staged))
  if not git(repo,'config','--get','user.name',check=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Campaign')
  if not git(repo,'config','--get','user.email',check=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')
  git(repo,'commit','-m','Obsidianti: Obsidianti-only FK-to-IK editor campaign v1.9.5')
  source_commit=git(repo,'rev-parse','HEAD').stdout.strip();state['sourceCommit']=source_commit;save()
  cmd(['git','-C',repo,'push','origin','HEAD:refs/heads/main'],timeout=450,env=env)
  remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]
  if remote!=source_commit:raise RuntimeError('SOURCE_REMOTE_READBACK_MISMATCH')
  state['sourceCommitRemoteReadback']=remote
  state['stage']='BUILD_EXISTING_GLB_FK_TO_NATIVE_IK_EDITOR';save()
  out=work/'Obsidianti_IK_AUTHOR_v1.9.5.blend';br=work/'build_report.json'
  prior=None # NEVER inherit the visually rejected v1.9.5 controller reconstruction
  if prior is not None:
   shutil.copyfile(prior['file'],out)
   shutil.copyfile(prior['report'],br)
   (work/'blender-build.log').write_text('RECOVERED_PRIOR_'+prior['version']+'='+str(prior['file'])+'\nSHA256='+prior['sha256']+'\n')
   state['recoveredPriorBuild']=prior['version'];state['recoveredPriorBuildSHA256']=prior['sha256'];save()
  else:
   call=blender_command(repo,work,'campaigns/OBSIDIANTI_IK_AUTHORING_BUILD_v1.9.5.py',[
    model,out,br])
   p=cmd(call,timeout=2400,check=False);(work/'blender-build.log').write_text(p.stdout+'\n'+p.stderr)
   if p.returncode or not out.is_file():raise RuntimeError('BLENDER_AUTHORING_BUILD_FAILED '+str(p.returncode)+' '+p.stderr[-1600:]+' '+p.stdout[-1600:])
  state['blendFileContainer']=inspect_blend_container(out);save()
  if json.loads(br.read_text()).get('status') not in ('IK_EDITABLE_POSE_PARITY_PASSED','IK_EDITABLE_POSE_PARITY_FAILED_UNAPPROVED'):raise RuntimeError('BUILD_REPORT_NOT_COMPLETE')
  state['buildReport']=json.loads(br.read_text());state['buildSHA256']=sha(out);save()
  state['stage']='INDEPENDENT_NATIVE_BLEND_REOPEN_AND_VERIFY';save()
  vr=work/'native_verify.json'
  call=blender_command(repo,work,'campaigns/OBSIDIANTI_IK_AUTHORING_VERIFY_v1.9.5.py',[out,br,vr])
  p=cmd(call,timeout=1500,check=False);(work/'blender-verify.log').write_text(p.stdout+'\n'+p.stderr)
  if p.returncode or not vr.is_file():raise RuntimeError('NATIVE_BLEND_READBACK_FAILED '+p.stderr[-1200:]+' '+p.stdout[-1200:])
  check=json.loads(vr.read_text())
  if check['readbackStatus'] not in ('REOPENED_AND_PHYSICALLY_VALIDATED','REOPENED_QUARANTINED_PHYSICAL_PARITY_FAILED'):raise RuntimeError('INVALID_REOPEN_VERDICT')
  if not state['buildReport']['physicalParity']['passed']:
   pp=state['buildReport']['physicalParity']
   offenders=[]
   for clip,by_side in pp['actions'].items():
    for side,metric in by_side.items():
     bad={k:round(metric[k],5) for k,limit in pp['limits'].items() if metric[k]>limit}
     if bad:offenders.append({'clip':clip,'side':side,'exceeded':bad,'worstFrame':metric.get('worstFrame')})
   state['physicalParityFailures']=offenders
   if out.is_file():
    quarantine=downloads/(V+'_'+run+'_FAILED_PARITY_UNAPPROVED.blend')
    if quarantine.exists():raise RuntimeError('QUARANTINE_DOWNLOAD_COLLISION')
    shutil.copyfile(out,quarantine)
    if sha(quarantine)!=sha(out):raise RuntimeError('QUARANTINE_COPY_SHA_MISMATCH')
    state['quarantinedBlendPath']=str(quarantine);state['quarantinedBlendSHA256']=sha(quarantine)
   save()
   print('IK_POSE_PARITY=FAILED; UNAPPROVED_PREVIEW_ONLY; NO_GIT_BLEND_PUBLICATION',flush=True)
   for row in offenders[:14]:print('BAD_POSE='+json.dumps(row,sort_keys=True),flush=True)
   raise RuntimeError('FK_TO_IK_EVALUATED_POSE_PARITY_FAILED_'+str(len(offenders))+'_SIDE_ACTIONS')
  state['verification']=check;save()
  for path,expected in SOURCES.items():
   if sha(repo/path)!=expected:raise RuntimeError('SOURCE_CHANGED_DURING_BLENDER_RUN '+path)
  if sha(model)!=V156_GLB_SHA:raise RuntimeError('VISUAL_BASE_CHANGED_DURING_RUN')
  state['stage']='PUBLISH_EDITABLE_BLEND_TERMUX_GIT_LFS';save()
  dst=repo/DEST;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(out,dst)
  if sha(dst)!=sha(out):raise RuntimeError('LFS_PUBLICATION_SOURCE_BYTES_MISMATCH')
  git(repo,'add','--',DEST)
  if git(repo,'diff','--cached','--name-only').stdout.splitlines()!=[DEST]:raise RuntimeError('UNEXPECTED_STAGED_CONTENT')
  git(repo,'commit','-m','Obsidianti: native Blender FK-to-IK pose-parity editor v1.9.5, review pending')
  finalcommit=git(repo,'rev-parse','HEAD').stdout.strip()
  pointer=git_pointer(repo,DEST)
  if 'oid sha256:'+sha(out) not in pointer:raise RuntimeError('LFS_POINTER_SHA_MISMATCH')
  cmd(['git','-C',repo,'push','origin','HEAD:refs/heads/main'],timeout=1200,env=env)
  remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]
  if remote!=finalcommit:raise RuntimeError('AUTHORING_BLEND_REMOTE_READBACK_MISMATCH')
  remote_pointer=git(repo,'show',finalcommit+':'+DEST).stdout
  if remote_pointer!=pointer:raise RuntimeError('AUTHORING_BLEND_POINTER_REMOTE_MISMATCH')
  state['publishedBlendGitPath']=DEST;state['publishedBlendSHA256']=sha(out);state['publishedBlendCommit']=finalcommit;state['remoteReadback']=remote
  state['stage']='COPY_TO_DOWNLOADS_AND_VERIFY';save()
  public=downloads/(V+'_'+run+'_EDITABLE.blend')
  if public.exists():raise RuntimeError('DOWNLOAD_OUTPUT_COLLISION')
  shutil.copyfile(out,public)
  if sha(public)!=sha(out):raise RuntimeError('DOWNLOAD_READBACK_MISMATCH')
  if shutil.which('termux-media-scan'):cmd(['termux-media-scan',public],check=False,timeout=20)
  state['sharedDownload']=str(public);state['status']='EDITABLE_FK_TO_IK_POSE_PARITY_VERIFIED_VISUAL_REVIEW_PENDING';state['stage']='COMPLETE';save()
  print('EDITABLE_BLEND='+str(public)+'\nEDITABLE_SHA256='+sha(public)+'\nPUBLISHED_GIT='+DEST+'\nREMOTE_COMMIT='+remote,flush=True)
  print('IK_RIG=PRESENT\nSOURCE_MOTION=OBSIDIANTI_GLB_ONLY\nANIMATION_CURVES=ORIGINAL_FK_PRESERVED\nIK_POSE_PARITY=NUMERIC_PASS\nVISUAL_ACCEPTANCE=PENDING',flush=True)
 except Exception as e:
  state['error']=type(e).__name__+': '+str(e);state['status']='BLOCKED';state['stage']='BLOCKED_'+state['stage'];save()
  print('BLOCKED='+state['error'],flush=True);traceback.print_exc()
  raise
 finally:
  save()
  handoff=downloads/(V+'_'+run+'_HANDOFF.zip')
  with zipfile.ZipFile(handoff,'x',compression=zipfile.ZIP_DEFLATED) as z:
   z.write(receipt,'receipt.json')
   for n in ('build_report.json','native_verify.json','blender-build.log','blender-verify.log'):
    p=work/n
    if p.is_file():z.write(p,'evidence/'+n)
  print('RECEIPT='+str(receipt)+'\nHANDOFF='+str(handoff)+'\nHANDOFF_SHA256='+sha(handoff),flush=True)
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('USAGE: driver.py PACKET_DIRECTORY LAUNCHER_SHA')
 main(pathlib.Path(sys.argv[1]),sys.argv[2])
