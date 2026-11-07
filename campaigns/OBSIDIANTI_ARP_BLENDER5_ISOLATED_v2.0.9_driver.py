#!/usr/bin/env python3
"""Isolated Blender 5.0 ARM64 Auto-Rig Pro retarget campaign. Mutation: Termux Git only.
Existing Debian proot and canonical models are untouched. Vendor source never published.
"""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time,uuid,traceback
from PIL import Image
V='OBSIDIANTI_ARP_BLENDER5_ISOLATED_v2.0.9'
OLD='OBSIDIANTI_ARP_FIRST_LIVE_v2.0.5'
DISTRO='obs-arp-blender50'
IMAGE='ubuntu:26.04'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE='d73c742ca9d3dcb7caf8d18826cd51650422fa7a'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
LION='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
ARES='63b6e7a7250cfb03e49cf0d335101d808126ae926894d74c1b2a6a49936b8b2a'
ARPZIP='2b377bbc5d81dfcef4209971e332a8bcb402ed44605e5ed0cddc2e90fafebf28'
TARGET='assets/obsidianti/Obsidianti.glb'; DONOR='assets/obsidianti/source/LionheartLancer.blend'
PROTECTED=(TARGET,'assets/repl/Repl.glb')
PREVIOUS='campaigns/'+OLD+'_'
SOURCE={
 'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER',
 'campaigns/'+V+'_driver.py':'driver.py',
 'campaigns/'+V+'_blender_trial.py':'blender_trial.py',
 'campaigns/'+V+'_blender_probe.py':'blender_probe.py',
 'campaigns/'+V+'_gif_writer.py':'gif_writer.py',
 'campaigns/'+V+'.contract.json':'contract.json',
 'tests/'+V+'_TEST.py':'test_driver.py',
}
EVID='diagnostics/obsidianti/arp-blender5-isolated-v2.0.9/runs/'


def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def cmd(argv,timeout=600,check=True,env=None,stream=False):
 argv=list(map(str,argv))
 if stream:
  print('COMMAND_BEGIN='+repr(argv[:3]),flush=True)
  with subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
      text=True,errors='replace',env=env,bufsize=1) as p:
   start=time.monotonic();last=[]
   for line in p.stdout:
    line=line.rstrip('\n');last.append(line);last=last[-25:]
    if any(x in line.lower() for x in ('blender','error','fail','fetch','install','unpack','setting up','warning','download')):
     print('PACKAGE: '+line[:300],flush=True)
    if time.monotonic()-start>timeout:
     p.kill();p.wait();raise RuntimeError('COMMAND_TIMED_OUT_'+repr(argv[:3]))
   rc=p.wait()
   print('COMMAND_EXIT='+str(rc)+' '+repr(argv[:3]),flush=True)
   if rc and check:raise RuntimeError('COMMAND_FAILED_'+str(rc)+' '+repr(argv[:3])+' '+repr(last[-9:]))
   return {'returncode':rc,'stdout':'\n'.join(last)}
 p=subprocess.run(argv,capture_output=True,text=True,errors='replace',timeout=timeout,env=env,stdin=subprocess.DEVNULL)
 if p.returncode and check:raise RuntimeError('COMMAND_FAILED_'+str(p.returncode)+' '+repr(argv[:5])+' '+p.stderr[-600:]+' '+p.stdout[-350:])
 return p

def git(repo,*args,timeout=300,check=True):return cmd(['git','-C',repo,*args],timeout=timeout,check=check)
def g(repo,*a):return git(repo,*a).stdout.strip()

def save_atomic(p,data):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_name('.'+p.name+'.'+uuid.uuid4().hex[:8]+'.tmp')
 tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n');os.replace(tmp,p)

def copy_no_clobber(src,dst):
 src=pathlib.Path(src);dst=pathlib.Path(dst)
 if not src.is_file() or src.is_symlink():raise RuntimeError('COPY_SOURCE_INVALID_'+str(src))
 if dst.exists():
  if dst.is_file() and not dst.is_symlink() and sha(src)==sha(dst):return
  raise RuntimeError('DESTINATION_COLLISION_'+str(dst))
 dst.parent.mkdir(parents=True,exist_ok=True)
 temp=dst.with_name('.'+dst.name+'.'+uuid.uuid4().hex[:8]+'.tmp')
 try:
  shutil.copyfile(src,temp)
  if sha(temp)!=sha(src):raise RuntimeError('COPY_SHA_MISMATCH')
  os.replace(temp,dst)
 finally:
  if temp.exists():temp.unlink()

def check_contract(packet,launcher,launchsha):
 if not launcher.is_file() or launcher.is_symlink() or sha(launcher)!=launchsha:raise RuntimeError('LAUNCHER_SHA_MISMATCH')
 if set(x.name for x in packet.iterdir() if x.is_file())!={'driver.py','test_driver.py','contract.json','manifest.json'}:
  raise RuntimeError('PAYLOAD_FILES_NOT_EXACT')
 mf=json.loads((packet/'manifest.json').read_text())
 if set(mf)!={'driver.py','test_driver.py','contract.json'} or any(sha(packet/n)!=val for n,val in mf.items()):
  raise RuntimeError('PAYLOAD_INTEGRITY_FAILED')
 contract=json.loads((packet/'contract.json').read_text())
 if contract.get('sourceMutablePaths')!=sorted(SOURCE) or contract.get('authority')!='TERMUX_GIT_ONLY':
  raise RuntimeError('CONTRACT_AUTHORITY_OR_PATHS_INVALID')
 if contract.get('pinnedInputHead')!=BASE or contract.get('purchasedZipSha256')!=ARPZIP:raise RuntimeError('CONTRACT_PIN_MISMATCH')

def checkout(root):
 repo=root/'repo'
 env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
 cmd(['git','clone','--quiet','--single-branch','--branch','main','--depth=1',REMOTE,repo],timeout=600,env=env)
 if g(repo,'remote','get-url','origin').removesuffix('.git')!=REMOTE.removesuffix('.git'):raise RuntimeError('WRONG_GIT_REMOTE')
 head=g(repo,'rev-parse','HEAD')
 if head!=BASE:
  if git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False).returncode:
   git(repo,'fetch','--no-tags','--depth=180','origin',BASE)
   if git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False).returncode:
    raise RuntimeError('REMOTE_HEAD_NOT_DESCENDED_FROM_VERIFIED_CRASH_REPORT')
 if g(repo,'rev-parse','HEAD:AGENTS.md')!=AGENTS:raise RuntimeError('AGENTS_BLOB_CHANGED')
 for name,h in ((TARGET,CANON),(DONOR,LION)):
  if 'oid sha256:'+h not in git(repo,'show','HEAD:'+name).stdout:
   raise RuntimeError('PINNED_GIT_LFS_POINTER_CHANGED_'+name)
 if g(repo,'status','--porcelain'):raise RuntimeError('ISOLATED_CLONE_DIRTY')
 return repo,head

def replace_once(src,a,b):
 count=src.count(a)
 if count!=1:raise RuntimeError('PATCH_PRECONDITION_FAILED '+repr(a[:70])+' occurrences='+str(count))
 return src.replace(a,b,1)

def patch_scripts(repo,packet):
 source=(repo/(PREVIOUS+'blender_trial.py')).read_text()
 probe=(repo/(PREVIOUS+'blender_probe.py')).read_text()
 gif=(repo/(PREVIOUS+'gif_writer.py')).read_text()
 source=replace_once(source,"if bpy.app.version[:2]!=(4,3):raise RuntimeError('BLENDER_4_3_REQUIRED_ACTUAL_'+bpy.app.version_string)",
    "if bpy.app.version[:2]!=(5,0):raise RuntimeError('BLENDER_5_0_REQUIRED_ACTUAL_'+bpy.app.version_string)")
 probe=replace_once(probe,"if bpy.app.version[:2] != (4,3):raise RuntimeError('REQUIRES_BLENDER_4_3_ACTUAL_'+bpy.app.version_string)",
    "if bpy.app.version[:2] != (5,0):raise RuntimeError('REQUIRES_BLENDER_5_0_ACTUAL_'+bpy.app.version_string)")
 source=replace_once(source,"  allowed={p.identifier for p in bpy.ops.arp.retarget.get_rna_type().properties}",
    "  result['stage']='BEFORE_RETARGET_RNA';save()\n  allowed={p.identifier for p in bpy.ops.arp.retarget.get_rna_type().properties}")
 source=replace_once(source,"  with bpy.context.temp_override(**context()):\n   if not bpy.ops.arp.retarget.poll():raise RuntimeError('ARP_RETARGET_POLL_FALSE_AFTER_MAPPING')",
    "  result['stage']='BEFORE_RETARGET_POLL';save()\n  with bpy.context.temp_override(**context()):\n   if not bpy.ops.arp.retarget.poll():raise RuntimeError('ARP_RETARGET_POLL_FALSE_AFTER_MAPPING')")
 source=replace_once(source,"  result['retargetOperator']=list(operator(bpy.ops.arp.retarget,'EXEC_DEFAULT',**retarget_options))",
    "  result['stage']='BEFORE_RETARGET_EXEC';save()\n  result['retargetOperator']=list(operator(bpy.ops.arp.retarget,'EXEC_DEFAULT',**retarget_options))\n  result['stage']='RETARGET_EXEC_RETURNED';save()")
 source=replace_once(source,"  result['targetMotion']=motion_stats(witnesses(tgt,start,end))",
    "  result['targetMotion']=motion_stats(witnesses(tgt,start,end))\n  result['stage']='TARGET_MOTION_CAPTURED';save()")
 source=replace_once(source,"  result['render']=render_frames(tgt,meshes,out,start,end,args.clip)",
    "  result['stage']='RENDERING';save()\n  result['render']=render_frames(tgt,meshes,out,start,end,args.clip)\n  result['stage']='RENDER_COMPLETE';save()")
 source=replace_once(source,"  result['mapping']={'boneCount':len(active),'mapped':active,'excludedCount':len(dropped)}",
    "  result['mapping']={'boneCount':len(active),'mapped':active,'excludedCount':len(dropped)}\n  result['stage']='BONE_MAP_CREATED';save()")
 source=replace_once(source,"  result['status']='VISUAL_REVIEW_PENDING_MOTION_GATE_PASS' if result['motionGate'] else 'REJECTED_BUT_RENDERED_ANATOMY_OR_ARTICULATION'",
    "  result['status']='VISUAL_REVIEW_PENDING_MOTION_GATE_PASS' if result['motionGate'] else 'REJECTED_BUT_RENDERED_ANATOMY_OR_ARTICULATION'\n  result['stage']='COMPLETE'")
 source=source.replace('obsidianti-arp-3.79.17-first-live-v2.0.5','obsidianti-arp-3.79.17-blender5-v2.0.9')
 probe=probe.replace('obsidianti-private-arp-operator-probe-v2.0.5','obsidianti-private-arp-operator-probe-v2.0.9')
 for name,content in [('blender_trial.py',source),('blender_probe.py',probe),('gif_writer.py',gif)]:
  (packet/name).write_text(content)
  compile(content,str(packet/name),'exec')
 return {'trial':sha(packet/'blender_trial.py'),'probe':sha(packet/'blender_probe.py'),'gif':sha(packet/'gif_writer.py')}

def publish(repo,phase):
 commit=g(repo,'rev-parse','HEAD')
 for n in range(3):
  p=git(repo,'push','origin','HEAD:refs/heads/main',timeout=500,check=False)
  if p.returncode==0:break
  if n==2:raise RuntimeError('GIT_PUSH_BLOCKED_'+phase+' '+p.stderr[-700:])
  time.sleep(n+1)
 remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()
 if not remote or remote[0]!=commit:raise RuntimeError('GIT_REMOTE_HEAD_READBACK_MISMATCH_'+phase)
 git(repo,'fetch','--quiet','origin','main')
 if g(repo,'rev-parse','refs/remotes/origin/main')!=commit:raise RuntimeError('GIT_FETCH_READBACK_MISMATCH_'+phase)
 return commit

def commit_source(repo,packet,launcher):
 pending={path:launcher if n=='LAUNCHER' else packet/n for path,n in SOURCE.items()}
 if any((repo/path).exists() for path in pending):raise RuntimeError('SOURCE_PATH_COLLISION_NO_OVERWRITE')
 for path,src in pending.items():copy_no_clobber(src,repo/path)
 git(repo,'add','--',*sorted(pending))
 if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(pending):raise RuntimeError('SOURCE_STAGING_ALLOWLIST_MISMATCH')
 if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Termux ARP Blender5')
 if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','termux-arp-blender5@users.noreply.github.com')
 git(repo,'commit','-m','Obsidianti: pilot purchased ARP Remap in isolated Blender 5.0 arm64')
 commit=publish(repo,'SOURCE')
 for path,src in pending.items():
  if git(repo,'show','refs/remotes/origin/main:'+path).stdout!=src.read_text():
   raise RuntimeError('PUBLISHED_SOURCE_READBACK_FAILED_'+path)
 return commit

def verify_vendor():
 zipfile=pathlib.Path.home()/'storage/downloads/auto_rig_pro_3.79.17.zip'
 if not zipfile.is_file() or zipfile.is_symlink() or sha(zipfile)!=ARPZIP:
  raise RuntimeError('PURCHASED_ARP_ZIP_MISSING_OR_SHA_CHANGED')
 private=pathlib.Path.home()/'.local/share/obsidianti-arp-purchased/3.79.17'/ARPZIP[:16]/'modules'
 if not private.is_dir() or len([p for p in private.iterdir() if p.is_dir() and (p/'__init__.py').is_file()])!=1:
  raise RuntimeError('VERIFIED_PRIOR_ARP_PRIVATE_MODULE_INSTALL_MISSING')
 return private

def ensure_distro(state,save):
 if not shutil.which('proot-distro'):raise RuntimeError('PROOT_DISTRO_UNAVAILABLE')
 probe=cmd(['proot-distro','login',DISTRO,'--','/bin/cat','/etc/os-release'],timeout=110,check=False)
 if probe.returncode:
  helpstr=cmd(['proot-distro','install','--help']).stdout
  if '--name' not in helpstr and '--override-alias' not in helpstr:
   raise RuntimeError('PROOT_DISTRO_CUSTOM_NAME_NOT_SUPPORTED_REFUSE_SYSTEM_OVERWRITE')
  state['stage']='INSTALL_ISOLATED_UBUNTU_CONTAINER';save()
  # --name creates an independent distro; Debian remains installed as before.
  cmd(['proot-distro','install','--name',DISTRO,IMAGE],timeout=1800,stream=True)
 probe=cmd(['proot-distro','login',DISTRO,'--','/bin/cat','/etc/os-release'],timeout=110)
 if 'Ubuntu' not in probe.stdout or '26.04' not in probe.stdout:
  raise RuntimeError('ISOLATED_CONTAINER_NOT_UBUNTU_26_04 '+probe.stdout[:210])
 present=cmd(['proot-distro','login',DISTRO,'--','/usr/bin/blender','--version'],timeout=100,check=False)
 if present.returncode or not present.stdout.startswith('Blender 5.0.'):
  state['stage']='INSTALL_ISOLATED_ARM64_BLENDER';save()
  # Mutates only the newly named Ubuntu container, never the existing Debian one.
  command='set -eu; export DEBIAN_FRONTEND=noninteractive; apt-get update; if ! apt-cache show blender >/dev/null 2>&1; then if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then sed -i "/^Components:/ { / universe /! s/$/ universe/; }" /etc/apt/sources.list.d/ubuntu.sources; fi; apt-get update; fi; apt-get install -y --no-install-recommends blender python3 ca-certificates'
  cmd(['proot-distro','login',DISTRO,'--','/bin/sh','-lc',command],timeout=2200,stream=True)
 present=cmd(['proot-distro','login',DISTRO,'--','/usr/bin/blender','--version'],timeout=120)
 if not present.stdout.startswith('Blender 5.0.'):
  raise RuntimeError('ARM64_BLENDER_5_0_NOT_VERIFIED '+present.stdout[:250])
 state['blenderVersion']=present.stdout.splitlines()[0];state['isolatedContainerName']=DISTRO
 state['stage']='BLENDER5_ISOLATED_RUNTIME_VERIFIED';save()
 print('ISOLATED_UBUNTU_BLENDER='+state['blenderVersion']+' CONTAINER='+DISTRO,flush=True)
 return present.stdout.splitlines()[0]

def verify_lfs(repo):
 git(repo,'lfs','version',timeout=60)
 git(repo,'lfs','install','--local',timeout=90)
 paths=(TARGET,DONOR)
 names=','.join(paths)
 pull=git(repo,'lfs','pull','--include='+names,'--exclude=','origin',timeout=1000,check=False)
 checkout=git(repo,'lfs','checkout',*paths,timeout=240,check=False)
 if any(not (repo/p).is_file() or sha(repo/p)!=h for p,h in ((TARGET,CANON),(DONOR,LION))):
  fetch=git(repo,'lfs','fetch','--include='+names,'--exclude=','origin','HEAD',timeout=1000,check=False)
  second=git(repo,'lfs','checkout',*paths,timeout=240,check=False)
 for p,h in ((TARGET,CANON),(DONOR,LION)):
  if not (repo/p).is_file() or sha(repo/p)!=h:
   raise RuntimeError('EXACT_MODEL_BINARY_NOT_HYDRATED_'+p+' pull='+str(pull.returncode))
  print('LFS_REAL_BINARY_VERIFIED='+p+' SHA256='+h,flush=True)
 return repo/DONOR,repo/TARGET

def execute_blender(argv,root,clip):
 proc=cmd(argv,timeout=2600,check=False)
 folder=root/'out'/clip
 folder.mkdir(parents=True,exist_ok=True)
 (folder/'BLENDER.log').write_text(proc.stdout+'\n'+proc.stderr)
 return proc

def probe_blender(root,private):
 folder=root/'probe';folder.mkdir(exist_ok=False)
 command=['proot-distro','login',DISTRO,
  '--bind',str(private.resolve())+':/mnt/arp-private',
  '--bind',str(root.resolve())+':/mnt/arp-work','--',
  'blender','--background','--factory-startup','--enable-autoexec',
  '--python','/mnt/arp-work/blender_probe.py','--',
  '--private','/mnt/arp-private','--output','/mnt/arp-work/probe/PROBE.json']
 p=cmd(command,timeout=500,check=False)
 (folder/'BLENDER.log').write_text(p.stdout+'\n'+p.stderr)
 recfile=folder/'PROBE.json'
 data=json.loads(recfile.read_text()) if recfile.is_file() else {}
 if p.returncode or data.get('status')!='REAL_PURCHASED_ARP_REMAP_HEADLESS_OPERATOR_REGISTRATION_PASS':
  raise RuntimeError('BLENDER5_ARP_REGISTRATION_BLOCKED_'+str(data.get('error',p.stderr[-330:]))[:420])
 print('BLENDER5_PURCHASED_ARP_REGISTRATION=PASS',flush=True)
 return {'blenderVersion':data['blenderVersion'],'status':data['status'],'activation':data.get('activation')}

def execute_clip(root,private,repo,source,source_sha,target,clip):
 folder=root/'out'/clip;folder.mkdir(parents=True,exist_ok=False)
 trial=folder/'trial'
 base=['proot-distro','login',DISTRO,
   '--bind',str(private.resolve())+':/mnt/arp-private',
   '--bind',str(root.resolve())+':/mnt/arp-work',
   '--bind',str(source.parent.resolve())+':/mnt/arp-source',
   '--bind',str(target.parent.resolve())+':/mnt/arp-target','--']
 command=base+['blender','--background','--factory-startup','--enable-autoexec',
  '--python','/mnt/arp-work/blender_trial.py','--',
  '--private','/mnt/arp-private',
  '--source','/mnt/arp-source/'+source.name,'--source-sha',source_sha,
  '--target','/mnt/arp-target/'+target.name,'--target-sha',CANON,
  '--clip',clip,'--output','/mnt/arp-work/out/'+clip+'/trial']
 process=cmd(command,timeout=2600,check=False)
 (folder/'BLENDER.log').write_text(process.stdout+'\n'+process.stderr)
 receipt=trial/'TRIAL.json'
 raw=json.loads(receipt.read_text()) if receipt.is_file() else {}
 status=raw.get('status','NO_TRIAL_RECEIPT')
 outcome={'clip':clip,'blenderExit':process.returncode,'trialStatus':status,
   'stage':raw.get('stage','UNKNOWN'),'targetAction':raw.get('targetAction'),
   'mappingBoneCount':raw.get('mapping',{}).get('boneCount'),
   'motionGate':raw.get('motionGate'), 'sourceMotion':raw.get('sourceMotion',{}),
   'targetMotion':raw.get('targetMotion',{}),
   'errorType':raw.get('errorType'), 'error':str(raw.get('error',''))[:400]}
 complete=status in ('VISUAL_REVIEW_PENDING_MOTION_GATE_PASS','REJECTED_BUT_RENDERED_ANATOMY_OR_ARTICULATION')
 if process.returncode or not complete:
  outcome['status']='BLOCKED_NATIVE_OR_PYTHON_RUNTIME'
  outcome['rawLogSHA256']=sha(folder/'BLENDER.log')
  print('TRIAL_'+clip.upper()+'=BLOCKED stage='+outcome['stage']+' rc='+str(process.returncode),flush=True)
  return outcome,{}
 # Hard gate: only complete retargets with 16 verified original Blender renders
 frames=sorted((trial/'frames').glob('frame_*.png'))
 if len(frames)!=16:
  outcome['status']='RENDER_FRAMES_MISSING_AFTER_SUCCESS_STATUS';return outcome,{}
 for file in frames:
  with Image.open(file) as im:
   if im.format!='PNG' or im.size!=(512,512):raise RuntimeError('INVALID_REAL_BLENDER_PNG_'+file.name)
   im.verify()
 sys.path.insert(0,str(root))
 from gif_writer import assemble
 arts=assemble(trial/'frames',trial,clip)
 outcome['graphic']={k:v for k,v in arts.items() if k not in ('gif','contact')}
 outcome['status']='VISUAL_OWNER_REVIEW_PENDING' if raw.get('motionGate') else 'MOTION_GATE_REJECTED_WITH_VISUAL'
 result={'gif':pathlib.Path(arts['gif']),'contact':pathlib.Path(arts['contact'])}
 blend=trial/('ARP_'+clip+'_UNAPPROVED.blend')
 if blend.is_file() and sha(blend)==raw.get('blendSHA256'):result['blend']=blend
 print('TRIAL_'+clip.upper()+'='+outcome['status']+' DISTINCT='+str(arts['distinctFrames']),flush=True)
 return outcome,result

def add_evidence(repo,root,runid,state,outputs,receipt):
 evidence=root/'evidence';evidence.mkdir(exist_ok=False)
 result=evidence/'EVIDENCE.json';report=evidence/'REPORT.md'
 data={'schema':V,'runId':runid,'authority':'TERMUX_GIT_ONLY',
   'gitSourceCommit':state.get('sourceCommit'),'inputGitHead':state.get('inputGitHead'),
   'agentsBlob':AGENTS,'campaignEtiquette':'READ_LIVE_2026_11_06',
   'canonicalModelSHA256':CANON,'sourceLionheartSHA256':LION,'sourceAresSHA256':ARES,
   'vendorPrivateSHA256':ARPZIP,'vendorCodePublished':False,'canonicalModelModified':False,
   'oldDebianBlender43Preserved':True,'isolatedRuntime':state.get('blenderVersion'),
   'arpProbe':state.get('arpProbe'), 'trials':state.get('trials',{}),
   'ownerVisualAcceptance':'PENDING'}
 save_atomic(result,data)
 report.write_text('# Obsidianti purchased Auto-Rig Pro: isolated Blender 5.0 test\n\n'+
   'Origin: actual Termux Git only, Ubuntu 26.04 isolated proot, unchanged old Debian.\n'+
   'Inputs: SHA-pinned exact Obsidianti and original Lionheart. Vendor source not published.\n\n'+
   '\n'.join('- '+k+': '+x['status']+'; stage '+str(x.get('stage'))+'; target action '+str(x.get('targetAction'))
     for k,x in state.get('trials',{}).items())+'\n\nAll retarget visuals remain UNAPPROVED.\n')
 pending={EVID+runid+'/EVIDENCE.json':result,EVID+runid+'/REPORT.md':report}
 for clip,files in outputs.items():
  for kind,f in files.items():pending[EVID+runid+'/'+clip+'/'+f.name]=f
 if any((repo/p).exists() for p in pending):raise RuntimeError('EVIDENCE_PATH_COLLISION')
 for p,f in pending.items():copy_no_clobber(f,repo/p)
 git(repo,'add','--',*sorted(pending))
 if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(pending):raise RuntimeError('EVIDENCE_STAGING_ALLOWLIST_MISMATCH')
 git(repo,'commit','-m','Obsidianti: actual isolated Blender 5.0 ARP operator results and visual evidence')
 published=publish(repo,'EVIDENCE')
 for p,f in pending.items():
  pfile=p.endswith(('.json','.md'))
  if pfile:
   if git(repo,'show','refs/remotes/origin/main:'+p).stdout!=f.read_text():
    raise RuntimeError('REMOTE_TEXT_READBACK_MISMATCH_'+p)
  elif p.endswith('.blend'):
   pointer=git(repo,'show','refs/remotes/origin/main:'+p).stdout
   if 'oid sha256:'+sha(f) not in pointer:raise RuntimeError('REMOTE_BLEND_LFS_MISMATCH')
  else:
   blob=subprocess.run(['git','-C',str(repo),'cat-file','blob','refs/remotes/origin/main:'+p],capture_output=True,check=True).stdout
   if hashlib.sha256(blob).hexdigest()!=sha(f):raise RuntimeError('REMOTE_VISUAL_BLOB_MISMATCH')
 for clip,files in outputs.items():
  for kind,f in files.items():
   if kind in ('gif','contact'):
    dest=pathlib.Path.home()/'storage/downloads'/(V+'_'+runid+'_'+f.name)
    copy_no_clobber(f,dest)
    print('DOWNLOAD_'+clip.upper()+'_'+kind.upper()+'='+str(dest)+' SHA256='+sha(dest),flush=True)
   if kind=='gif':print('GIF_URL_'+clip.upper()+'=https://github.com/Valar05/parametric-parambulator/blob/'+published+'/'+EVID+runid+'/'+clip+'/'+f.name,flush=True)
 state['evidenceGitCommit']=published;state['status']='OWNER_VISUAL_REVIEW_PENDING' if outputs else 'RETARGET_BLOCKED_DIAGNOSTICS_GIT_PUBLISHED'
 receipt();print('EVIDENCE_URL=https://github.com/Valar05/parametric-parambulator/blob/'+published+'/'+EVID+runid+'/REPORT.md',flush=True)
 return published

def main(packet,launcher,launcher_sha):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 check_contract(packet,launcher,launcher_sha)
 cmd(['python3','-m','py_compile',str(packet/'driver.py'),str(packet/'test_driver.py')])
 cmd(['python3',str(packet/'test_driver.py')],timeout=120)
 downloads=pathlib.Path.home()/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('ANDROID_DOWNLOADS_UNAVAILABLE')
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
 receipt=root/'RECEIPT.json'
 state={'schema':V,'runId':runid,'status':'BOOT','authority':'TERMUX_GIT_ONLY',
  'sourceCommit':None,'entrySHA256':launcher_sha,'purchasedZipSHA256':ARPZIP,
  'canonicalModelSHA256':CANON,'originalCanonicalModelUnchanged':True,'ownerVisualVerdict':'PENDING',
  'stage':'BOOT','agentsBlob':AGENTS,'vendorCodePublished':False,'existingDebianUnmodified':True}
 def save():save_atomic(receipt,state)
 save()
 try:
  private=verify_vendor();state['stage']='VERIFIED_VENDOR_PRIVATE_MODULES';save()
  repo,head=checkout(root);state['inputGitHead']=head
  pre={p:g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED}
  state['protectedBlobsBefore']=pre;state['stage']='GIT_CLONED_AND_RULES_VERIFIED';save()
  scripts=patch_scripts(repo,packet);state['derivedScriptSHA256']=scripts
  state['stage']='SOURCE_PATCHES_VERIFIED';save()
  sourcecommit=commit_source(repo,packet,launcher);state['sourceCommit']=sourcecommit
  state['stage']='GIT_CAMPAIGN_SOURCE_REMOTE_VERIFIED';save()
  for p in ('blender_probe.py','blender_trial.py','gif_writer.py'):copy_no_clobber(packet/p,root/p)
  ensure_distro(state,save)
  state['stage']='HEADLESS_VENDOR_PROBE';save()
  probe=probe_blender(root,private);state['arpProbe']=probe;state['stage']='ARP_REGISTERED_IN_BLENDER5';save()
  lion,target=verify_lfs(repo);state['stage']='ORIGINAL_MODEL_BINARIES_SHA_VERIFIED';save()
  optional=next((f for f in sorted(downloads.glob('Ares*.blend')) if f.is_file() and not f.is_symlink() and sha(f)==ARES),None)
  jobs=[('Heavy1',lion,LION)]+([('AxeKick',optional,ARES)] if optional else [])
  print('ARES_SOURCE_FOUND='+('YES' if optional else 'NO'),flush=True)
  trials={};outputs={};(root/'out').mkdir()
  for clip,src,sh in jobs:
   state['stage']='EXECUTE_'+clip.upper();save()
   res,files=execute_clip(root,private,repo,src,sh,target,clip)
   trials[clip]=res;outputs[clip]=files
   state['trials']=trials;save()
  if sha(repo/TARGET)!=CANON or sha(repo/DONOR)!=LION:
   raise RuntimeError('INPUT_MODEL_OR_DONOR_BINARY_MUTATED_DURING_TRIAL')
  if {p:g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED}!=pre:
   raise RuntimeError('PROTECTED_GIT_BLOBS_CHANGED')
  state['stage']='PUBLISH_REAL_EVIDENCE';save()
  add_evidence(repo,root,runid,state,outputs,save)
  print('CANONICAL_MODEL_UNCHANGED=YES',flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as exc:
  state['status']='BLOCKED';state['errorType']=type(exc).__name__
  state['error']=str(exc)[:850];save()
  print('STATUS=BLOCKED '+type(exc).__name__+' '+str(exc)[:850],flush=True)
  raise
 finally:
  save();print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('USAGE: driver.py PACKET LAUNCHER SHA256')
 main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3])
