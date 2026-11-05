#!/usr/bin/env python3
"""One-invocation Android Termux Git source and native Blender IK authoring campaign."""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time,uuid,zipfile,traceback
V='OBSIDIANTI_IK_AUTHORING_v1.9.0'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
SOURCES={'assets/obsidianti/source/Obsidianti.blend':'68f7b29cfa76e0cc300d72fc37062ba786c1d6c75841f0b3a9c1ae78dbd33ce1',
 'assets/obsidianti/source/LionheartLancer.blend':'81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4',
 'assets/obsidianti/Obsidianti.glb':'8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'}
V156_ZIP_SHA='fc3ca580b82de074f6a2f040e8335baf1351b74a102df389bbaa5dfc85a68c3a'
V156_GLB_SHA='261f10786dd0eb0e80667173e4a893f6822356da628a5907efd6d0bbc2a74ff5'
FILES={'campaigns/OBSIDIANTI_IK_AUTHORING_RUN_v1.9.0.py':'driver.py','campaigns/OBSIDIANTI_IK_AUTHORING_BUILD_v1.9.0.py':'blender_author.py','campaigns/OBSIDIANTI_IK_AUTHORING_VERIFY_v1.9.0.py':'blender_verify.py','docs/obsidianti/IK_AUTHORING_v1.9.0.md':'doc.md'}
DEST='assets/obsidianti/source/Obsidianti_IK_AUTHOR_v1.9.0.blend'
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

def main(packet,launcher_sha):
 home=pathlib.Path.home();downloads=home/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('TERMUX_DOWNLOADS_NOT_CONFIGURED')
 run=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:7]
 root=home/'.local/state'/V/run;root.mkdir(parents=True,exist_ok=False)
 work=root/'work';work.mkdir();repo=root/'repo'
 receipt=downloads/(V+'_'+run+'_RECEIPT.json')
 state={'version':V,'run':run,'authority':'TERMUX_GIT_ONLY','stage':'BOOT','status':'STARTED','launcherSHA256':launcher_sha,
        'rules':{'agentsExpectedBlob':AGENTS_BLOB,'etiquetteReadByAuthor':'2026-11-05 via Home Center'},'originalBlendChanged':False,
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
  state['stage']='FETCH_AND_VERIFY_REAL_SOURCE_BLENDS';save()
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
  git(repo,'commit','-m','Obsidianti: isolated sparse-key native IK authoring campaign v1.9.0')
  source_commit=git(repo,'rev-parse','HEAD').stdout.strip();state['sourceCommit']=source_commit;save()
  cmd(['git','-C',repo,'push','origin','HEAD:refs/heads/main'],timeout=450,env=env)
  remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]
  if remote!=source_commit:raise RuntimeError('SOURCE_REMOTE_READBACK_MISMATCH')
  state['sourceCommitRemoteReadback']=remote
  state['stage']='BUILD_SPARSE_NATIVE_IK_AUTHORING_BLEND';save()
  out=work/'Obsidianti_IK_AUTHOR_v1.9.0.blend';br=work/'build_report.json'
  call=blender_command(repo,work,'campaigns/OBSIDIANTI_IK_AUTHORING_BUILD_v1.9.0.py',[
   repo/'assets/obsidianti/source/LionheartLancer.blend',repo/'assets/obsidianti/source/Obsidianti.blend',model,out,br])
  # Map the verified preview GLB into the Blender work bind; it is under work already.
  p=cmd(call,timeout=2400,check=False);(work/'blender-build.log').write_text(p.stdout+'\n'+p.stderr)
  if p.returncode or not out.is_file():raise RuntimeError('BLENDER_AUTHORING_BUILD_FAILED '+str(p.returncode)+' '+p.stderr[-700:])
  if out.open('rb').read(7)!=b'BLENDER':raise RuntimeError('OUTPUT_IS_NOT_NATIVE_BLEND')
  if json.loads(br.read_text()).get('status')!='IK_EDIT_AUTHORING_COPY_CREATED_REVIEW_PENDING':raise RuntimeError('BUILD_REPORT_NOT_SUCCESS')
  state['buildReport']=json.loads(br.read_text());state['buildSHA256']=sha(out);save()
  state['stage']='INDEPENDENT_NATIVE_BLEND_REOPEN_AND_VERIFY';save()
  vr=work/'native_verify.json'
  call=blender_command(repo,work,'campaigns/OBSIDIANTI_IK_AUTHORING_VERIFY_v1.9.0.py',[out,br,vr])
  p=cmd(call,timeout=1500,check=False);(work/'blender-verify.log').write_text(p.stdout+'\n'+p.stderr)
  if p.returncode or not vr.is_file():raise RuntimeError('NATIVE_BLEND_READBACK_FAILED '+p.stderr[-800:])
  check=json.loads(vr.read_text())
  if check['readbackStatus']!='PERSISTED_AUTHORING_BLEND_STRUCTURALLY_VERIFIED_NOT_VISUALLY_APPROVED':raise RuntimeError('INVALID_REOPEN_VERDICT')
  state['verification']=check;save()
  for path,expected in SOURCES.items():
   if sha(repo/path)!=expected:raise RuntimeError('SOURCE_CHANGED_DURING_BLENDER_RUN '+path)
  if sha(model)!=V156_GLB_SHA:raise RuntimeError('VISUAL_BASE_CHANGED_DURING_RUN')
  state['stage']='PUBLISH_EDITABLE_BLEND_TERMUX_GIT_LFS';save()
  dst=repo/DEST;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(out,dst)
  if sha(dst)!=sha(out):raise RuntimeError('LFS_PUBLICATION_SOURCE_BYTES_MISMATCH')
  git(repo,'add','--',DEST)
  if git(repo,'diff','--cached','--name-only').stdout.splitlines()!=[DEST]:raise RuntimeError('UNEXPECTED_STAGED_CONTENT')
  git(repo,'commit','-m','Obsidianti: native Blender sparse-key IK editable reference v1.9.0, review pending')
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
  state['sharedDownload']=str(public);state['status']='EDITABLE_NATIVE_IK_BLEND_PUBLISHED_UNAPPROVED';state['stage']='COMPLETE';save()
  print('EDITABLE_BLEND='+str(public)+'\nEDITABLE_SHA256='+sha(public)+'\nPUBLISHED_GIT='+DEST+'\nREMOTE_COMMIT='+remote,flush=True)
  print('IK_RIG=PRESENT\nSOURCE_TIMINGS=ACTUAL_NATIVE_ACTION_KEYS\nVISUAL_ACCEPTANCE=PENDING',flush=True)
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
