#!/usr/bin/env python3
"""One-shot Termux Git-only ARP 3.79.17 installation, real Remap and visible GIF campaign.
Vendor ZIP never touches public Git or public diagnostics. Canonical GLB is read-only.
"""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,re,shutil,stat,subprocess,sys,time,uuid,zipfile,traceback
from gif_writer import assemble
V='OBSIDIANTI_ARP_FIRST_LIVE_v2.0.4'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE='c9ee48bdcf59f2cc9870ec00a0b96a7314cd7059'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
LION='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
ARES='63b6e7a7250cfb03e49cf0d335101d808126ae926894d74c1b2a6a49936b8b2a'
ARP_ZIP='2b377bbc5d81dfcef4209971e332a8bcb402ed44605e5ed0cddc2e90fafebf28'
TARGET='assets/obsidianti/Obsidianti.glb'
DONOR='assets/obsidianti/source/LionheartLancer.blend'
LOCKED=(TARGET,'assets/repl/Repl.glb')
SOURCE={'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER','campaigns/'+V+'_driver.py':'driver.py',
 'campaigns/'+V+'_blender_trial.py':'blender_trial.py','campaigns/'+V+'_blender_probe.py':'blender_probe.py','campaigns/'+V+'_gif_writer.py':'gif_writer.py',
 'campaigns/'+V+'.contract.json':'contract.json','tests/'+V+'_TEST.py':'test_driver.py'}
DIAG='diagnostics/obsidianti/arp-first-live-v2.0.4/runs/'

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def call(args,timeout=240,check=True,env=None):
 z=subprocess.run([str(v) for v in args],capture_output=True,text=True,timeout=timeout,env=env)
 if check and z.returncode:raise RuntimeError('COMMAND_FAILED '+repr([str(v) for v in args[:6]])+' STDOUT='+z.stdout[-550:]+' STDERR='+z.stderr[-1100:])
 return z

def git(root,*args,timeout=240,check=True):return call(['git','-C',root,*args],timeout=timeout,check=check)
def g(root,*args):return git(root,*args).stdout.strip()

def safe_copy(src,dst):
 src=pathlib.Path(src);dst=pathlib.Path(dst)
 if dst.exists():
  if dst.is_file() and sha(src)==sha(dst):return
  raise RuntimeError('DESTINATION_COLLISION_NO_OVERWRITE '+str(dst))
 dst.parent.mkdir(parents=True,exist_ok=True)
 temp=dst.with_name('.'+dst.name+'.'+uuid.uuid4().hex+'.tmp')
 try:
  shutil.copyfile(src,temp)
  if sha(src)!=sha(temp):raise RuntimeError('COPY_CHECKSUM_FAILURE')
  os.replace(temp,dst)
 finally:
  if temp.exists():temp.unlink()

def run_git_clone(root):
 repo=root/'repo'
 e=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
 call(['git','clone','--quiet','--depth=1','--single-branch','--branch','main',REMOTE,repo],timeout=480,env=e)
 if g(repo,'remote','get-url','origin').removesuffix('.git')!=REMOTE.removesuffix('.git'):raise RuntimeError('WRONG_REMOTE_ORIGIN')
 head=g(repo,'rev-parse','HEAD')
 if head!=BASE:
  q=git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False)
  if q.returncode:
   git(repo,'fetch','--no-tags','--depth=120','origin',BASE,timeout=190)
   if git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False).returncode:raise RuntimeError('MAIN_NOT_DESCENDED_FROM_PINNED_REVISION')
 if g(repo,'rev-parse','HEAD:AGENTS.md')!=AGENTS:raise RuntimeError('CURRENT_GIT_RULES_MISMATCH')
 if 'oid sha256:'+CANON not in git(repo,'show','HEAD:'+TARGET).stdout:raise RuntimeError('CANONICAL_GLB_LFS_SHA_MISMATCH')
 if 'oid sha256:'+LION not in git(repo,'show','HEAD:'+DONOR).stdout:raise RuntimeError('DONOR_NATIVE_BLEND_LFS_SHA_MISMATCH')
 if g(repo,'status','--porcelain'):raise RuntimeError('ISOLATED_GIT_REPO_NOT_CLEAN')
 return repo,head

def publish(repo,phase):
 local=g(repo,'rev-parse','HEAD')
 for retry in range(3):
  res=git(repo,'push','origin','HEAD:refs/heads/main',timeout=320,check=False)
  if not res.returncode:break
  if retry==2:raise RuntimeError('GIT_PUSH_FAILED_'+phase+' '+res.stderr[-1200:])
  time.sleep(1+retry)
 remote=git(repo,'ls-remote','origin','refs/heads/main',timeout=120).stdout.split()
 if not remote or remote[0]!=local:raise RuntimeError('GIT_REMOTE_COMMIT_SHA_READBACK_FAILED_'+phase)
 git(repo,'fetch','--quiet','origin','main',timeout=180)
 if g(repo,'rev-parse','refs/remotes/origin/main')!=local:raise RuntimeError('GIT_REMOTE_FETCH_READBACK_FAILED_'+phase)
 return local

def source_pub(repo,packet,launcher):
 # Arguments are keyword-only at the call site to keep the bundle directory
 # distinct from the single-file launcher. Both are Path-like.
 if not pathlib.Path(packet).is_dir() or not pathlib.Path(launcher).is_file():
  raise RuntimeError('SOURCE_PUBLICATION_EXPECTS_PACKET_DIRECTORY_AND_LAUNCHER_FILE')
 pending={dst:launcher if key=='LAUNCHER' else packet/key for dst,key in SOURCE.items()}
 coll=[name for name in pending if (repo/name).exists()]
 if coll:
  # Safe retry after a previously published source commit: exact same source bytes
  # and every expected path. No overwrite, stash, reset, or force push.
  if (len(coll)==len(pending) and
      all((repo/name).is_file() and sha(repo/name)==sha(path) for name,path in pending.items()) and
      not g(repo,'status','--porcelain')):
   commit=g(repo,'log','-1','--format=%H','--',next(iter(pending)))
   if not commit:raise RuntimeError('VERSIONED_SOURCE_ALREADY_PRESENT_BUT_NO_COMMIT')
   return commit
  raise RuntimeError('NEW_CAMPAIGN_SOURCE_PATH_COLLISION '+repr(coll))
 for name,path in pending.items():safe_copy(path,repo/name)
 git(repo,'add','--',*sorted(pending))
 if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(pending):raise RuntimeError('GIT_SOURCE_STAGING_NOT_EXACT')
 if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Termux ARP Campaign')
 if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','termux-arp@users.noreply.github.com')
 git(repo,'commit','-m','Obsidianti: create private Auto-Rig Pro 3.79.17 headless Remap campaign')
 return publish(repo,'SOURCE')

def private_zip(downloads):
 candidates=[x for x in downloads.glob('*.zip') if x.name.lower()=='auto_rig_pro_3.79.17.zip' and x.is_file() and not x.is_symlink()]
 if len(candidates)!=1:raise RuntimeError('EXPECTED_PRIVATE_ARP_ZIP_NOT_FOUND_OR_AMBIGUOUS auto_rig_pro_3.79.17.zip')
 path=candidates[0]
 if not (1_000_000<path.stat().st_size<70_000_000):raise RuntimeError('ARP_PRIVATE_ZIP_SIZE_OUT_OF_BOUNDS')
 with zipfile.ZipFile(path) as z:
  if z.testzip() is not None:raise RuntimeError('ARP_VENDOR_ZIP_INTEGRITY_FAILED')
 digest=sha(path)
 if digest!=ARP_ZIP:raise RuntimeError('PURCHASED_ARP_ZIP_SHA_MISMATCH_EXPECTED_3_79_17')
 return path,digest

def unpack_checked(blob,root):
 """Never write path-traversal or symlink entries; this is a private vendor install only."""
 root.mkdir(parents=True,exist_ok=False)
 with zipfile.ZipFile(blob) as z:
  entries=z.infolist()
  if len(entries)>3000 or sum(i.file_size for i in entries)>250_000_000:raise RuntimeError('VENDOR_ZIP_SIZE_OR_ENTRY_BUDGET_EXCEEDED')
  for i in entries:
   p=pathlib.PurePosixPath(i.filename)
   if p.is_absolute() or any(x in ('.','..') for x in p.parts) or '\\' in i.filename or '\x00' in i.filename:raise RuntimeError('UNSAFE_ZIP_MEMBER')
   if (i.external_attr>>16)&0o170000==0o120000:raise RuntimeError('ZIP_SYMLINK_MEMBER_FORBIDDEN')
   dest=root.joinpath(*p.parts)
   if i.is_dir():dest.mkdir(parents=True,exist_ok=True);continue
   dest.parent.mkdir(parents=True,exist_ok=True)
   with z.open(i) as src, open(dest,'xb') as dst:shutil.copyfileobj(src,dst)

def private_install(src,ziphash,install_base=None):
 base=pathlib.Path(install_base) if install_base is not None else pathlib.Path.home()/'.local/share/obsidianti-arp-purchased/3.79.17'/ziphash[:16]
 final=base/'modules'
 if final.is_dir() and len([p for p in final.iterdir() if p.is_dir() and (p/'__init__.py').exists()])==1:
  return final
 scratch=base/('unpack-'+uuid.uuid4().hex[:8])
 unpack_checked(src,scratch)
 # An ARP purchased ZIP sometimes has a wrapper holding the installable ZIP.
 roots=[p.parent for p in scratch.rglob('__init__.py') if p.parent.name.lower().startswith(('auto_rig_pro','auto-rig-pro'))]
 if not roots:
  wrappers=[p for p in scratch.rglob('*.zip') if 'auto' in p.name.lower() and p.stat().st_size>500_000]
  if len(wrappers)==1:
   inner=base/('inner-'+uuid.uuid4().hex[:8]);unpack_checked(wrappers[0],inner)
   roots=[p.parent for p in inner.rglob('__init__.py') if p.parent.name.lower().startswith(('auto_rig_pro','auto-rig-pro'))]
 if not roots:
  fallback=[p.parent for p in scratch.rglob('__init__.py') if (p.parent/'src'/'auto_rig_remap.py').is_file()]
  if not fallback and (scratch/'__init__.py').is_file():fallback=[scratch]
  roots=fallback
 if len(roots)!=1:raise RuntimeError('PRIVATE_ADDON_PACKAGE_ROOT_NOT_UNIQUE '+str(len(roots)))
 picked=roots[0]
 parent=base/('modules-'+uuid.uuid4().hex[:8]);parent.mkdir(parents=True)
 name='auto_rig_pro' if picked==scratch or picked.name in ('auto_rig_pro-master','auto-rig-pro-master') else picked.name
 if name=='__init__' or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',name):name='auto_rig_pro'
 shutil.copytree(picked,parent/name)
 if final.exists():
  if len([p for p in final.iterdir() if p.is_dir() and (p/'__init__.py').exists()])!=1:
   raise RuntimeError('PRIVATE_ARP_ADDON_INSTALL_COLLISION')
 else:os.replace(parent,final)
 return final

def _verified_model_file(path,expected):
 """A Git LFS pointer is not the model. Verify the full bytes, not filename or git blob."""
 try:
  return path.is_file() and not path.is_symlink() and sha(path)==expected
 except OSError:return False

def _cache_restore(repo,relative,expected):
 """Recover only verified Git LFS object bytes from the isolated repo's native cache."""
 object_path=repo/'.git/lfs/objects'/expected[:2]/expected[2:4]/expected
 if not _verified_model_file(object_path,expected):return False
 dest=repo/relative
 tmp=dest.with_name('.'+dest.name+'.lfsrestore-'+uuid.uuid4().hex[:8])
 try:
  shutil.copyfile(object_path,tmp)
  if not _verified_model_file(tmp,expected):raise RuntimeError('GIT_LFS_CACHED_BLOB_SHA_CHANGED')
  os.replace(tmp,dest)
 finally:
  if tmp.exists():tmp.unlink()
 return True

def assets(repo):
 """Hydrate only the two SHA-locked model sources, despite global LFS skip/exclude settings.

 Our v2.0.1 accidentally passed --exclude=*, which OVERRIDES the include list
 and prevents fetching *both* requested files. Explicit --exclude= clears it.
 """
 paths=[TARGET,DONOR]
 wants={TARGET:CANON,DONOR:LION}
 git(repo,'lfs','version',timeout=60)
 # Set filters only on the disposable checkout. No global LFS changes.
 local_setup=git(repo,'lfs','install','--local',timeout=90,check=False)
 if local_setup.returncode:raise RuntimeError('ISOLATED_GIT_LFS_LOCAL_INSTALL_FAILED '+local_setup.stderr[-350:])
 missing=[path for path in paths if not _verified_model_file(repo/path,wants[path])]
 if missing:
  includes=','.join(missing)
  # Git LFS include and exclude are BOTH enforced. Exclusion must be EMPTY.
  request=['--include='+includes,'--exclude=']
  pull=git(repo,'lfs','pull',*request,'origin',timeout=900,check=False)
  checkout=git(repo,'lfs','checkout',*missing,timeout=280,check=False)
  unresolved=[path for path in missing if not _verified_model_file(repo/path,wants[path])]
  if unresolved:
   # Recover a no-op checkout, transient fetch failure, or a preexisting LFS
   # checkout with smudge globally disabled without downloading entire repo.
   fetch=git(repo,'lfs','fetch','--include='+','.join(unresolved),'--exclude=','origin','HEAD',timeout=900,check=False)
   second=git(repo,'lfs','checkout',*unresolved,timeout=280,check=False)
   still=[path for path in unresolved if not _verified_model_file(repo/path,wants[path])]
   for path in still:
    if _cache_restore(repo,path,wants[path]):
     print('LFS_RECOVERY='+path+' VERIFIED_NATIVE_OBJECT_CACHE',flush=True)
   if any(not _verified_model_file(repo/path,wants[path]) for path in still):
    diagnostics={'pullRC':pull.returncode,'checkoutRC':checkout.returncode,
     'fetchRC':fetch.returncode,'secondCheckoutRC':second.returncode,
     'remaining':[{'path':p,'bytes':(repo/p).stat().st_size if (repo/p).is_file() else None,
      'pointer':bool((repo/p).is_file() and (repo/p).stat().st_size<300 and
       (repo/p).read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'))}
      for p in still if not _verified_model_file(repo/p,wants[p])]}
    raise RuntimeError('GIT_LFS_EXACT_MODEL_RETRIEVAL_BLOCKED '+json.dumps(diagnostics,sort_keys=True))
 for path,want in wants.items():
  file=repo/path
  if not _verified_model_file(file,want):raise RuntimeError('GIT_LFS_REAL_BINARY_NOT_EXACT_'+path)
  print('LFS_REAL_BINARY_VERIFIED='+path+' SHA256='+want+' BYTES='+str(file.stat().st_size),flush=True)
 return repo/TARGET,repo/DONOR

def optional_ares(downloads):
 opts=sorted([p for p in downloads.glob('Ares*.blend') if p.is_file() and not p.is_symlink()])
 for x in opts:
  if sha(x)==ARES:return x
 return None

def headless_probe(root,private):
 """Use real Blender + the purchased add-on BEFORE model hydration or retargeting."""
 output=root/'headless_probe';output.mkdir(exist_ok=False)
 result=output/'PROBE.json'
 if shutil.which('proot-distro'):
  base=['proot-distro','login','debian',
   '--bind',str(private.resolve())+':/mnt/arp-private',
   '--bind',str(root.resolve())+':/mnt/arp-campaign','--']
  cmd=base+['blender','--background','--factory-startup','--enable-autoexec',
   '--python','/mnt/arp-campaign/blender_probe.py','--',
   '--private','/mnt/arp-private','--output','/mnt/arp-campaign/headless_probe/PROBE.json']
 else:
  if not shutil.which('blender'):raise RuntimeError('BLENDER_RUNTIME_UNAVAILABLE_FOR_PURCHASED_ARP_PROBE')
  cmd=['blender','--background','--factory-startup','--enable-autoexec','--python',
   str(root/'blender_probe.py'),'--','--private',str(private),'--output',str(result)]
 trial=call(cmd,timeout=500,check=False)
 (output/'PROBE.log').write_text(trial.stdout+'\n'+trial.stderr)
 if not result.is_file():raise RuntimeError('ARP_REAL_HEADLESS_PROBE_PRODUCED_NO_EVIDENCE '+trial.stderr[-400:])
 rec=json.loads(result.read_text())
 if trial.returncode or rec.get('status')!='REAL_PURCHASED_ARP_REMAP_HEADLESS_OPERATOR_REGISTRATION_PASS':
  summary=rec.get('stackSummary',[])
  raise RuntimeError('ARP_ACTUAL_HEADLESS_REGISTRATION_BLOCKED '+str(rec.get('error',trial.stderr[-500:]))[:280]+ ' STACK='+json.dumps(summary[-5:],sort_keys=True)[:480])
 return rec

def blender_runner(root,private,repo,output,source,source_sha,target,clip):
 folder=output/clip;folder.mkdir(parents=True,exist_ok=False)
 script=root/'blender_trial.py'
 if shutil.which('proot-distro'):
  base=['proot-distro','login','debian',
   '--bind',str(private.resolve())+':/mnt/arp-private',
   '--bind',str(source.parent.resolve())+':/mnt/arp-source',
   '--bind',str(target.parent.resolve())+':/mnt/arp-target',
   '--bind',str(output.resolve())+':/mnt/arp-out',
   '--bind',str(root.resolve())+':/mnt/arp-campaign','--']
  probe=call(base+['blender','--version'],timeout=120)
  if 'Blender 4.3.' not in probe.stdout:raise RuntimeError('ARP_RUNTIME_BLENDER_4_3_REQUIRED '+probe.stdout[:160])
  cmd=base+['blender','--background','--factory-startup','--enable-autoexec',
   '--python','/mnt/arp-campaign/blender_trial.py','--',
   '--private','/mnt/arp-private','--source','/mnt/arp-source/'+source.name,
   '--source-sha',source_sha,'--target','/mnt/arp-target/'+target.name,
   '--target-sha',CANON,'--clip',clip,'--output','/mnt/arp-out/'+clip+'/trial']
 else:
  if not shutil.which('blender'):raise RuntimeError('TERMUX_HAS_NO_PROOT_DEBIAN_OR_NATIVE_BLENDER')
  cmd=['blender','--background','--factory-startup','--enable-autoexec',
   '--python',str(script),'--','--private',str(private),'--source',str(source),
   '--source-sha',source_sha,'--target',str(target),'--target-sha',CANON,
   '--clip',clip,'--output',str(folder/'trial')]
 proc=call(cmd,timeout=2400,check=False)
 (folder/'BLENDER.log').write_text(proc.stdout+'\n'+proc.stderr)
 evidence=folder/'trial/TRIAL.json'
 if not evidence.is_file():return {'status':'BLOCKED','error':'BLENDER_DID_NOT_PRODUCE_TRIAL_JSON','returncode':proc.returncode,'logTail':proc.stderr[-600:]},None
 data=json.loads(evidence.read_text());data['blenderExitCode']=proc.returncode
 if proc.returncode or data['status']=='BLOCKED':return data,None
 graphic=assemble(folder/'trial/frames',folder/'trial',clip)
 data['graphic']=graphic
 return data,graphic

def sanitized(trial):
 # Never upload vendor ZIP, source, installation files, Blender logs or traceback.
 approved=('status','schema','clip','inputSHA256','action','actionRange','sourceRig','targetRig','targetMeshes','sourceBones','targetBones','arp','autoScaleOperator','buildMappingOperator','mapping','sourceMotion','targetMotion','motionGate','targetAction','retargetOperator','render','blendSHA256','graphic','blenderExitCode','errorType','error')
 return {k:v for k,v in trial.items() if k in approved}

def main(packet,launcher,launchsha):
 packet=pathlib.Path(packet);launcher=pathlib.Path(launcher)
 expected={'driver.py','blender_trial.py','blender_probe.py','gif_writer.py','test_driver.py','contract.json'}
 manifest=json.loads((packet/'manifest.json').read_text())
 if set(manifest)!=expected:raise RuntimeError('PAYLOAD_MANIFEST_INVALID')
 for p,h in manifest.items():
  if sha(packet/p)!=h:raise RuntimeError('PAYLOAD_MEMBER_TAMPERED '+p)
 contract=json.loads((packet/'contract.json').read_text())
 if contract['sourceMutablePaths']!=sorted(SOURCE) or contract['authority']!='TERMUX_GIT_ONLY':raise RuntimeError('WRONG_CONTRACT_OR_SOURCE_ALLOWLIST')
 call(['python3','-m','py_compile']+[packet/x for x in ('driver.py','blender_trial.py','blender_probe.py','gif_writer.py','test_driver.py')])
 call(['python3',packet/'test_driver.py'],timeout=90)
 downloads=pathlib.Path.home()/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('ANDROID_SHARED_DOWNLOADS_NOT_CONFIGURED')
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
 receipt=root/'RECEIPT.json'
 rec={'schema':V,'runId':runid,'status':'BOOT','authority':'TERMUX_GIT_ONLY',
  'launcherSHA256':launchsha,'vendorVersionRequested':'3.79.17','vendorZIPsha256':None,
  'addonCodePublished':False,'gitRulesBlob':AGENTS,'canonicalGLBSHA256':CANON,
  'sourceBlenderSHA256':LION,'originalCanonicalModelUnchanged':True,'ownerVisualVerdict':'PENDING'}
 def save():
  tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(rec,sort_keys=True,indent=2)+'\n');os.replace(tmp,receipt)
 save()
 try:
  privzip,ziphash=private_zip(downloads)
  rec['vendorZIPsha256']=ziphash;rec['status']='PRIVATE_VENDOR_ZIP_VERIFIED';save()
  print('ARP_PRIVATE_ZIP_SHA256='+ziphash,flush=True)
  private=private_install(privzip,ziphash)
  rec['status']='PRIVATE_ARP_MODULE_EXTRACTED';save()
  print('PRIVATE_ARP_MODULES_EXTRACTED=YES (Blender registration pending)',flush=True)
  repo,head=run_git_clone(root);rec['gitInputHEAD']=head
  original={p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}
  rec['protectedGitBlobsBefore']=original
  srccommit=source_pub(repo,packet=packet,launcher=launcher)
  rec['gitSourceCommit']=srccommit;rec['status']='CAMPAIGN_SOURCE_GIT_VERIFIED_PENDING_REAL_ARP_PROBE';save()
  for name in ('blender_trial.py','blender_probe.py'):safe_copy(packet/name,root/name)
  try:
   probe=headless_probe(root,private)
  except Exception as probe_exc:
   # Publish ONLY the compact structural facts, never tracebackLocal or vendor code.
   local=root/'headless_probe'/'PROBE.json'
   raw=json.loads(local.read_text()) if local.is_file() else {}
   probe_public={'schema':V+'-headless-registration-failure','runId':runid,
     'gitInputHead':head,'canonicalSha256':CANON,'donorSha256':LION,
     'agentsSha':AGENTS,'vendorZipSha256':ziphash,'blenderVersion':raw.get('blenderVersion'),
     'status':'BLOCKED_REGISTRATION', 'error':raw.get('error'),
     'registrationContext':raw.get('registrationContext'),
     'stackSummary':raw.get('stackSummary',[]),
     'vendorCodeIncluded':False,'canonicalModified':False}
   # Guard against emitting source strings; JSON is a strict allowlist above.
   stage=repo/(DIAG+runid+'/ARP_PROBE_DIAGNOSTIC.json')
   if stage.exists():raise RuntimeError('ARP_DIAG_GIT_PATH_COLLISION') from probe_exc
   stage.parent.mkdir(parents=True,exist_ok=True)
   stage.write_text(json.dumps(probe_public,indent=2,sort_keys=True)+'\n')
   git(repo,'add','--',str(stage.relative_to(repo)))
   git(repo,'commit','-m','Obsidianti: record private ARP headless probe failure metadata only')
   diagcommit=publish(repo,'ARP_PROBE_DIAGNOSTIC')
   if git(repo,'show','HEAD:'+str(stage.relative_to(repo))).stdout!=stage.read_text():
    raise RuntimeError('ARP_PROBE_GIT_REMOTE_READBACK_FAILED') from probe_exc
   if {p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}!=original:
    raise RuntimeError('PROTECTED_MODEL_SHA_CHANGED_ON_PROBE_FAILURE') from probe_exc
   url='https://github.com/Valar05/parametric-parambulator/blob/'+diagcommit+'/'+str(stage.relative_to(repo))
   rec['headlessFailureEvidenceURL']=url;rec['status']='BLOCKED_REGISTRATION_DIAGNOSTIC_GIT_VERIFIED';save()
   print('ARP_PROBE_DIAGNOSTIC_URL='+url,flush=True)
   raise
  rec['arpProbe']={'status':probe['status'],'activation':probe.get('activation'),'sceneProperties':probe.get('sceneProperties')}
  rec['status']='PURCHASED_ARP_HEADLESS_REGISTRATION_VERIFIED';save()
  print('ARP_PRIVATE_ADDON_HEADLESS_REGISTRATION_VERIFIED=YES',flush=True)
  target,lion=assets(repo)
  rec['verifiedInputs']={TARGET:{'sha256':sha(target),'bytes':target.stat().st_size},
   DONOR:{'sha256':sha(lion),'bytes':lion.stat().st_size}};rec['status']='SHA_VERIFIED_GIT_LFS_REAL_BINARIES';save()
  # No user checkout, no original files, and no vendor package are modified.
  rec['status']='ARP_REGISTERED_AND_GIT_LFS_MODELS_VERIFIED';save()
  trials={};out=root/'work';out.mkdir()
  # Blender trial/probe scripts were staged once before the real registration probe.
  optional=optional_ares(downloads)
  jobs=[('Ares','AxeKick',optional,ARES)] if optional else []
  jobs.append(('Lionheart','Heavy1',lion,LION))
  print('ARES_SOURCE_FOUND='+('YES' if optional else 'NO_SKIPPED_SOURCE_NOT_SHA_VERIFIED'),flush=True)
  for tag,clip,source,digest in jobs:
   try:
    result,graphic=blender_runner(root,private,repo,out,source,digest,target,clip)
    trials[tag]=sanitized(result)
    if graphic:
     for key in ('gif','contact'):
      orig=pathlib.Path(graphic[key]);dst=downloads/(V+'_'+runid+'_'+orig.name)
      safe_copy(orig,dst)
      print('DOWNLOAD_'+key.upper()+'='+str(dst)+' SHA256='+sha(dst),flush=True)
     blend=out/clip/'trial'/('ARP_'+clip+'_UNAPPROVED.blend')
     if blend.is_file():
      dst=downloads/(V+'_'+runid+'_'+blend.name);safe_copy(blend,dst)
      print('DOWNLOAD_BLENDER='+str(dst)+' SHA256='+sha(dst),flush=True)
    print('TRIAL_'+tag.upper()+'='+result['status'],flush=True)
   except BaseException as ex:
    trials[tag]={'status':'BLOCKED','errorType':type(ex).__name__,'error':str(ex)[:650]}
    print('TRIAL_'+tag.upper()+'=BLOCKED '+type(ex).__name__+' '+str(ex)[:420],flush=True)
   rec['trialStatuses']={k:v['status'] for k,v in trials.items()};save()
  evidence=root/'evidence';evidence.mkdir()
  public={'schema':V,'runId':runid,'gitSourceCommit':srccommit,'gitInputHEAD':head,
   'gitRulesBlob':AGENTS,'campaignEtiquette':'READ_LIVE_2026_11_06',
   'privateAddonZIPSHA256':ziphash,'addonVersionRequested':'3.79.17','addonCodePublished':False,
   'privateAddonHeadlessProbe':rec.get('arpProbe'),
   'canonicalGLBSHA256':CANON,'nativeLionheartBlendSHA256':LION,'optionalAresSHA256':ARES if optional else None,
   'trials':trials,'canonicalModified':False,'ownerVisualAcceptance':'PENDING'}
  report=evidence/'REPORT.md';js=evidence/'EVIDENCE.json'
  js.write_text(json.dumps(public,indent=2,sort_keys=True)+'\n')
  report.write_text('# Auto-Rig Pro 3.79.17 actual first run\n\n'+
   'Exact private ZIP read in Android Downloads, installed only outside public Git.\n'+
   'Exact canonical Obsidianti model and native donor verified by SHA and Git LFS.\n'+
   'Real purchased ARP bpy.ops.arp operators executed in Blender 4.3 when available.\n\n'+
   '\n'.join('- '+k+': '+v['status'] for k,v in trials.items())+'\n\n'+
   'Failed/diagnostic GIFs are NOT validated animation. Source and canonical model unchanged.\n')
  to_pub={DIAG+runid+'/'+p.name:p for p in (js,report)}
  for tag,clip,source,digest in jobs:
   trial=out/clip/'trial'
   for name in ('ARP_'+clip+'_SIDE_UNAPPROVED.gif','ARP_'+clip+'_SIDE_CONTACT.png','ARP_'+clip+'_UNAPPROVED.blend'):
    candidate=trial/name
    if candidate.is_file():to_pub[DIAG+runid+'/'+tag+'/'+name]=candidate
  if any((repo/p).exists() for p in to_pub):raise RuntimeError('OUTPUT_EVIDENCE_PATH_COLLISION')
  for path,src in to_pub.items():safe_copy(src,repo/path)
  git(repo,'add','--',*sorted(to_pub))
  if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(to_pub):raise RuntimeError('SOURCE_OR_VENDOR_LEAK_IN_GIT_STAGING')
  git(repo,'commit','-m','Obsidianti: verify actual Auto-Rig Pro headless installation and publish first visual evidence')
  published=publish(repo,'EVIDENCE')
  if {p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}!=original:raise RuntimeError('CANONICAL_OR_REPL_GIT_POINTER_CHANGED')
  for path,source in to_pub.items():
   if path.endswith(('.md','.json')):
    if git(repo,'show','refs/remotes/origin/main:'+path).stdout!=source.read_text():raise RuntimeError('REMOTE_TEXT_EVIDENCE_MISMATCH')
   elif path.endswith('.blend'):
    ptr=git(repo,'show','refs/remotes/origin/main:'+path).stdout
    if 'oid sha256:'+sha(source) not in ptr:raise RuntimeError('OUTPUT_BLEND_GIT_LFS_POINTER_SHA_MISMATCH')
   else:
    # Binary readback MUST use raw bytes, never text decoding.
    raw=subprocess.run(['git','-C',str(repo),'cat-file','blob','refs/remotes/origin/main:'+path],capture_output=True,check=True).stdout
    if hashlib.sha256(raw).hexdigest()!=sha(source):raise RuntimeError('REMOTE_GIF_OR_CONTACT_HASH_MISMATCH')
  rec['status']='ARP_TRIAL_EVIDENCE_GIT_PUBLISHED_OWNER_REVIEW_PENDING' if any(v.get('motionGate') for v in trials.values()) else 'ARP_EXECUTED_NO_VALIDATED_ANIMATION__EVIDENCE_GIT_PUBLISHED'
  rec['gitEvidenceCommit']=published;save()
  summary=evidence/'EVIDENCE.json'
  dst=downloads/(V+'_'+runid+'_EVIDENCE.json');safe_copy(summary,dst)
  print('EVIDENCE_URL=https://github.com/Valar05/parametric-parambulator/blob/'+published+'/'+DIAG+runid+'/REPORT.md',flush=True)
  for tag,clip,source,digest in jobs:
   candidate=out/clip/'trial'/('ARP_'+clip+'_SIDE_UNAPPROVED.gif')
   if candidate.is_file():
    print('GIF_URL_'+tag.upper()+'=https://github.com/Valar05/parametric-parambulator/blob/'+published+'/'+DIAG+runid+'/'+tag+'/'+candidate.name,flush=True)
  print('CANONICAL_MODEL_UNCHANGED=YES',flush=True)
  print('STATUS='+rec['status'],flush=True)
 except BaseException as ex:
  if rec.get('status')!='BLOCKED_REGISTRATION_DIAGNOSTIC_GIT_VERIFIED':rec['status']='BLOCKED'
  rec['errorType']=type(ex).__name__;rec['error']=str(ex)[:900];save()
  print('STATUS=BLOCKED '+type(ex).__name__+' '+str(ex)[:900],flush=True)
  raise
 finally:
  save();print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('USAGE driver.py PACKET LAUNCHER SHA')
 main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve(),sys.argv[3])
