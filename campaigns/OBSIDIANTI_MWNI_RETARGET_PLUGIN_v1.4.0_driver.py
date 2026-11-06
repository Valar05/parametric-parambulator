#!/usr/bin/env python3
"""Termux Git-only Mwni install and real-geometry test. No canonical model writes."""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time,traceback,uuid
V='OBSIDIANTI_MWNI_RETARGET_PLUGIN_v1.4.0'
REPO_URL='https://github.com/Valar05/parametric-parambulator.git'
VENDOR_URL='https://github.com/Mwni/blender-animation-retargeting.git'
VENDOR_SHA='8c91ff4f4d898bab835b3587f17585487056b60b'
RESEARCH_PARENT='d07e2adc17186df87a1689e8e2f82f37f4dc972a'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
DONOR_SHA='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
TARGET_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
MODEL='assets/obsidianti/Obsidianti.glb'; LOCKED=(MODEL,'assets/repl/Repl.glb')
SOURCE={
 'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER',
 'campaigns/'+V+'_driver.py':'driver.py',
 'tests/'+V+'_TEST.py':'test_driver.py',
 'campaigns/'+V+'_blender_trial.py':'blender_trial.py',
 'campaigns/'+V+'.contract.json':'contract.json',
}
DIR='diagnostics/obsidianti/mwni-plugin-v1.4.0'
OUTPUT={DIR+'/REPORT.md':'REPORT.md',DIR+'/RESULTS.json':'RESULTS.json',DIR+'/EVIDENCE_RECEIPT.json':'EVIDENCE_RECEIPT.json'}

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def run(args,timeout=120,env=None,check=True,cwd=None):
 x=subprocess.run([str(v) for v in args],text=True,capture_output=True,timeout=timeout,env=env,cwd=cwd)
 if check and x.returncode:raise RuntimeError('COMMAND_FAILED '+repr(list(map(str,args))[:12])+' RC='+str(x.returncode)+' STDERR='+x.stderr[-1200:]+' STDOUT='+x.stdout[-1200:])
 return x

def git(root,*args,timeout=120,check=True):return run(['git','-C',root,*args],timeout=timeout,check=check)
def gstr(root,*args):return git(root,*args).stdout.strip()
def safe_copy(s,d):
 s=pathlib.Path(s);d=pathlib.Path(d)
 if d.exists():raise RuntimeError('DESTINATION_COLLISION '+str(d))
 d.parent.mkdir(parents=True,exist_ok=True)
 tmp=d.with_name('.'+d.name+'.'+uuid.uuid4().hex[:8]+'.tmp')
 try:
  shutil.copyfile(s,tmp)
  if sha(s)!=sha(tmp):raise RuntimeError('COPY_SHA_MISMATCH '+str(d))
  os.replace(tmp,d)
 finally:
  if tmp.exists():tmp.unlink()
def identity(repo):
 if not gstr(repo,'config','user.name'):git(repo,'config','user.name','Obsidianti Termux Campaign')
 if not gstr(repo,'config','user.email'):git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')

def push_readback(repo,stage):
 head=gstr(repo,'rev-parse','HEAD')
 for i in range(3):
  p=git(repo,'push','origin','HEAD:refs/heads/main',timeout=320,check=False)
  if p.returncode==0:break
  if i==2:raise RuntimeError(stage+'_GIT_PUSH_REJECTED '+p.stderr[-1200:])
  time.sleep(2*(i+1))
 remote=git(repo,'ls-remote','origin','refs/heads/main',timeout=90).stdout.split()[0]
 if remote!=head:raise RuntimeError(stage+'_REMOTE_SHA_MISMATCH '+remote+' expected '+head)
 git(repo,'fetch','origin','main',timeout=180)
 if gstr(repo,'rev-parse','refs/remotes/origin/main')!=head:raise RuntimeError(stage+'_REMOTE_FETCH_MISMATCH')
 return head

def find_source():
 roots=[pathlib.Path.home()/'storage/downloads',pathlib.Path('/storage/emulated/0/Download'),pathlib.Path.home()/'storage/documents']
 for root in roots:
  if not root.exists():continue
  for p in sorted(root.glob('Lionheart*.blend')):
   if p.is_file() and sha(p)==DONOR_SHA:return p
 raise RuntimeError('ORIGINAL_LIONHEART_SHA_LOCKED_BLEND_NOT_FOUND')

def packet_guard(packet):
 m=json.loads((packet/'manifest.json').read_text())
 expected={'driver.py','blender_trial.py','contract.json','test_driver.py'}
 if set(m)!=expected:raise RuntimeError('EMBEDDED_PACKET_MEMBERS_INVALID '+str(set(m)))
 for name,h in m.items():
  if not (packet/name).is_file() or sha(packet/name)!=h:raise RuntimeError('PACKET_MEMBER_SHA_FAIL '+name)
 return sha(packet/'manifest.json')

def clone_repo(root):
 repo=root/'repo';env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
 # Clone only canonical main, no stale user working directory, no forced reset or stash.
 run(['git','clone','--quiet','--depth=1','--branch','main','--single-branch',REPO_URL,str(repo)],timeout=480,env=env)
 if gstr(repo,'remote','get-url','origin').rstrip('.git')!=REPO_URL.rstrip('.git'):raise RuntimeError('WRONG_GIT_ORIGIN')
 head=gstr(repo,'rev-parse','HEAD')
 # Need the exact already proven evidence revision in the clone ancestry.
 if head!=RESEARCH_PARENT:
  x=git(repo,'fetch','--no-tags','--depth=40','origin',RESEARCH_PARENT,timeout=180,check=False)
  if x.returncode or git(repo,'merge-base','--is-ancestor',RESEARCH_PARENT,'HEAD',check=False).returncode:
   raise RuntimeError('SOURCE_HISTORY_NO_LONGER_CONTAINS_PINNED_RESEARCH '+head)
 if gstr(repo,'rev-parse','HEAD:AGENTS.md')!=AGENTS_BLOB:raise RuntimeError('AGENTS_BLOB_NOT_APPROVED')
 if gstr(repo,'status','--porcelain'):raise RuntimeError('ISOLATED_GIT_WORKTREE_DIRTY')
 return repo,head

def lfs_source(repo):
 pointer=gstr(repo,'show','HEAD:'+MODEL)
 if ('oid sha256:'+TARGET_SHA) not in pointer:raise RuntimeError('CANONICAL_LFS_SOURCE_SHA_CHANGED')
 for attempt in range(3):
  x=git(repo,'lfs','fetch','origin','HEAD','--include='+MODEL,'--exclude=',timeout=780,check=False)
  if x.returncode==0:break
  if attempt==2:raise RuntimeError('CANONICAL_LFS_FETCH_FAILED '+x.stderr[-1400:])
  time.sleep(2+attempt)
 git(repo,'lfs','checkout','--',MODEL,timeout=300)
 if sha(repo/MODEL)!=TARGET_SHA:raise RuntimeError('CANONICAL_GLB_BINARY_SHA_WRONG')
 return repo/MODEL

def addon_fetch(root):
 vendor=root/'vendor-checkout';run(['git','init','--quiet',str(vendor)],timeout=90)
 git(vendor,'remote','add','origin',VENDOR_URL)
 env=dict(os.environ,GIT_TERMINAL_PROMPT='0')
 for i in range(3):
  r=run(['git','-C',vendor,'fetch','--no-tags','--depth=1','origin',VENDOR_SHA],timeout=380,check=False,env=env)
  if r.returncode==0:break
  if i==2:
   # Some Git hosts decline direct old-SHA shallow fetch. Fetch the short stable branch history instead.
   alt=run(['git','-C',vendor,'fetch','--no-tags','--depth=120','origin','refs/heads/stable'],timeout=380,check=False,env=env)
   if alt.returncode:raise RuntimeError('MWNI_PINNED_COMMIT_FETCH_FAILED '+r.stderr[-650:]+' FALLBACK '+alt.stderr[-650:])
   else:break
  time.sleep(i+2)
 git(vendor,'checkout','--detach',VENDOR_SHA)
 if gstr(vendor,'rev-parse','HEAD')!=VENDOR_SHA:raise RuntimeError('MWNI_VENDOR_COMMIT_MISMATCH')
 if gstr(vendor,'status','--porcelain'):raise RuntimeError('MWNI_VENDOR_TREE_DIRTY')
 # Prevent name collision with another plugin installation. This is an isolated, permanent module store.
 installed=pathlib.Path.home()/'.local/share/obsidianti-blender-addons'/('mwni-2.1.1-'+VENDOR_SHA[:12])
 module=installed/'animation_retargeting'
 if installed.exists():
  if not (module/'__init__.py').is_file():raise RuntimeError('MWNI_PREVIOUS_PARTIAL_INSTALL_COLLISION')
  for p in vendor.glob('*.py'):
   if not (module/p.name).is_file() or sha(module/p.name)!=sha(p):raise RuntimeError('MWNI_INSTALLED_PLUGIN_BYTES_DIFFER '+p.name)
 else:
  stage=installed.with_name('.'+installed.name+'.tmp-'+uuid.uuid4().hex[:8]);module_tmp=stage/'animation_retargeting'
  module_tmp.mkdir(parents=True)
  for p in vendor.glob('*.py'):safe_copy(p,module_tmp/p.name)
  # Carry upstream license/docs in the permanent pinned mirror without edits.
  for p in vendor.iterdir():
   if p.is_file() and p.suffix.lower() in ('.md','.txt'):
    safe_copy(p,module_tmp/p.name)
  stage.rename(installed)
 for fn in ['__init__.py','context.py','drivers.py','ik.py','baking.py','alignment.py','mapping.py']:
  if not (module/fn).is_file():raise RuntimeError('MWNI_INSTALL_INCOMPLETE '+fn)
 return installed,{p.name:sha(p) for p in sorted(module.glob('*.py'))}

def blender_call(repo,source,addon,work,clip):
 dest=work/clip;dest.mkdir(parents=True,exist_ok=True)
 # The repo evidence proves existing Debian proot Blender 4.3.2; do not install/upgrade Blender.
 if shutil.which('proot-distro'):
  cmd=['proot-distro','login','debian','--bind',str(source.parent.resolve())+':/mnt/obs-input',
       '--bind',str(repo.resolve())+':/mnt/obs-repo','--bind',str(addon.resolve())+':/mnt/obs-addon',
       '--bind',str(work.resolve())+':/mnt/obs-output',
       '--','blender','--background','--factory-startup','--enable-autoexec','--python',
       '/mnt/obs-output/blender_trial.py','--','--source','/mnt/obs-input/'+source.name,
       '--target','/mnt/obs-repo/'+MODEL,'--addon','/mnt/obs-addon','--addon-rev',VENDOR_SHA,
       '--clip',clip,'--out','/mnt/obs-output/'+clip]
 elif shutil.which('blender'):
  cmd=['blender','--background','--factory-startup','--enable-autoexec','--python',str(work/'blender_trial.py'),
       '--','--source',str(source),'--target',str(repo/MODEL),'--addon',str(addon),
       '--addon-rev',VENDOR_SHA,'--clip',clip,'--out',str(dest)]
 else:raise RuntimeError('BLENDER_RUNTIME_UNAVAILABLE_NO_EXISTING_PROOT_OR_NATIVE')
 r=run(cmd,timeout=2500,check=False)
 (dest/'BLENDER.log').write_text(' '.join(map(str,cmd))+'\n'+r.stdout+'\n'+r.stderr)
 verdict=json.loads((dest/'TRIAL.json').read_text()) if (dest/'TRIAL.json').is_file() else {'status':'BLENDER_TRIAL_DID_NOT_WRITE_RECEIPT'}
 return {'returncode':r.returncode,'verdict':verdict,'logTail':(r.stdout+'\n'+r.stderr)[-2800:]}

def main(packet,launcher,launcher_sha):
 downloads=pathlib.Path.home()/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('TERMUX_SHARED_DOWNLOADS_MISSING')
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
 receipt=root/'RECEIPT.json'
 record={'campaign':V,'runId':runid,'status':'STARTING','authority':'TERMUX_GIT_ONLY',
         'launcherSha256':launcher_sha,'canonicalModified':False,'blendModified':False,
         'agentsSha':AGENTS_BLOB,'liveCampaignEtiquetteRead':'2026-11-06 via connector'}
 def save():
  tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');os.replace(tmp,receipt)
 save();work=root/'work';work.mkdir()
 try:
  record['packetManifestSHA256']=packet_guard(packet)
  run(['python3','-m','py_compile',str(packet/'driver.py'),str(packet/'blender_trial.py'),str(packet/'test_driver.py')])
  run(['python3',str(packet/'test_driver.py')],timeout=90)
  contract=json.loads((packet/'contract.json').read_text())
  if set(contract['mutablePaths'])!=set(SOURCE)|set(OUTPUT):raise RuntimeError('MUTABLE_PATH_CONTRACT_MISMATCH')
  if run(['git','lfs','version'],check=False).returncode:raise RuntimeError('TERMUX_GIT_LFS_REQUIRED')
  donor=find_source();record['sourceBlendSHA256']=sha(donor)
  repo,head=clone_repo(root);record['inputRemoteHead']=head
  tree_before={n:gstr(repo,'rev-parse','HEAD:'+n) for n in LOCKED};record['lockedTreeBefore']=tree_before
  srcfiles={path:launcher if name=='LAUNCHER' else packet/name for path,name in SOURCE.items()}
  if any((repo/n).exists() for n in set(SOURCE)|set(OUTPUT)):
   raise RuntimeError('VERSIONED_DESTINATION_COLLISION_NO_OVERWRITE')
  identity(repo)
  for dst,src in srcfiles.items():safe_copy(src,repo/dst)
  git(repo,'add','--',*sorted(SOURCE))
  staged=set(gstr(repo,'diff','--cached','--name-only').splitlines())
  if staged!=set(SOURCE):raise RuntimeError('SOURCE_PATH_ALLOWLIST_VIOLATION '+repr(staged))
  git(repo,'commit','-m','Obsidianti: install/test pinned free Mwni Blender retargeting add-on',timeout=180)
  record['sourceCommit']=push_readback(repo,'SOURCE');record['status']='SOURCE_COMMITTED_REMOTE_VERIFIED'
  print('SOURCE_COMMIT='+record['sourceCommit'],flush=True);save()
  # Actual 16.9-MB canonical GLB LFS byte locked after read-only source commit.
  model=lfs_source(repo);record['verifiedCanonicalGLBSHA256']=sha(model)
  addon,vendorhash=addon_fetch(root)
  record['pinnedVendorCommit']=VENDOR_SHA;record['installedSourcePath']=str(addon);record['vendorFileHashes']=vendorhash
  safe_copy(packet/'blender_trial.py',work/'blender_trial.py')
  # Probe actual Blender availability and version; do not upgrade system packages.
  if shutil.which('proot-distro'):
   p=run(['proot-distro','login','debian','--','blender','--version'],timeout=90,check=False)
  else:p=run(['blender','--version'],timeout=90,check=False)
  (work/'BLENDER_VERSION.txt').write_text(p.stdout+'\n'+p.stderr)
  if p.returncode:raise RuntimeError('ACTUAL_BLENDER_RUNTIME_VERSION_PROBE_FAILED '+p.stderr[-800:])
  import re
  m=re.search(r'Blender\s+(\d+)\.(\d+)',p.stdout)
  if not m:raise RuntimeError('BLENDER_VERSION_NOT_PARSEABLE '+p.stdout[-300:])
  version=(int(m.group(1)),int(m.group(2)))
  record['blenderVersionProbe']=p.stdout.splitlines()[0]
  if not ((3,0)<=version<(4,4)):
   raise RuntimeError('MWNI_2_1_1_PIN_REQUIRES_BLENDER_3_0_TO_4_3_FOUND_'+repr(version)+'__DO_NOT_AUTO_UPGRADE')
  print('BLENDER_VERSION='+p.stdout.splitlines()[0],flush=True)
  print('MWNI_VENDOR_SHA='+VENDOR_SHA,flush=True)
  trials={}
  for clip in ('Heavy1','Light2'):
   trials[clip]=blender_call(repo,donor,addon,work,clip)
   print('TEST_'+clip+'='+trials[clip]['verdict'].get('status','NO_STATUS')+' RC='+str(trials[clip]['returncode']),flush=True)
   record['lastClip']=clip;save()
  record['trials']={c:{'returncode':t['returncode'],'status':t['verdict'].get('status')} for c,t in trials.items()}
  succeeded=[c for c,t in trials.items() if t['returncode']==0 and t['verdict'].get('status')=='PLUGIN_IK_BAKE_EXPORT_TESTED_UNAPPROVED']
  results={'schema':'obsidianti-mwni-v1.4.0-plugin-evidence','campaign':V,'vendorRepository':VENDOR_URL,'pinnedVendorCommit':VENDOR_SHA,
           'vendorVersion':'2.1.1','blenderVersion':record['blenderVersionProbe'],'targetCanonicalSHA256':TARGET_SHA,
           'originalLionheartSHA256':DONOR_SHA,'testedClips':list(trials),'successfulClipTests':succeeded,
           'trials':trials,'canonicalModelModified':False,'ownerVisualAcceptance':'PENDING',
           'caveat':'Installed add-on in isolated on-device module store and Blender user script directory. Exported GLBs are unapproved diagnostic candidates only.'}
  (work/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n')
  lines=['# Mwni Blender Animation Retargeting: installed and tested', '',
         'Termux-authorized source and evidence campaign; source branch was never written by ChatGPT GitHub connector.',
         '',f'- Pinned upstream revision: `{VENDOR_SHA}` (v2.1.1 compatible with Blender 4.3.x)',
         f'- Blender: `{record["blenderVersionProbe"]}`',f'- Source `.blend` SHA-256: `{DONOR_SHA}`',
         f'- Source canonical GLB SHA-256: `{TARGET_SHA}`',
         f'- Installed addon source: `{addon}`','- Canonical model: unchanged. No owner visual approval.','',
         '| Test | Actual Blender process | Plugin mapped + IK + baked + exported | Left/right foot motion RMS (m), no IK -> IK -> baked |',
         '|---|---:|---|---|']
  for clip,t in trials.items():
   v=t['verdict'];l=[]
   for side in ('Left','Right'):
    z=[]
    for key in ('noIK','withIK','baked'):
     value=v.get(key,{}).get('metrics',{}).get(side,{}).get('footMotionDiscrepancyRms_m')
     z.append('n/a' if value is None else str(value))
    l.append(side+': '+' -> '.join(z))
   lines.append('| '+clip+' | '+str(t['returncode'])+' | '+v.get('status','MISSING')+' | '+'; '.join(l)+' |')
  lines+=['','## Interpretation','',
          'These are third-party Mwni driver/IK retarget tests. Foot bone motion error is not a sole-contact verdict. Actual skinned wedge-sole ranges and on-device output hashes are in `RESULTS.json`.',
          'Any missing candidate, runtime exception, failed bake parity, or foot contact deterioration is identified explicitly; do not label an installed add-on as a successful animation repair.',
          '', '## Explicit protected boundary','',
          'No original Blender source, canonical GLB, model Git LFS pointer, Repl asset, or approved animation was modified. The two exported clip GLBs and experimental `.blend` remain unapproved files in Android Downloads, not new canon.','']
  (work/'REPORT.md').write_text('\n'.join(lines))
  evidence={'schema':V+'-receipt','sourceCommit':record['sourceCommit'],'inputHead':head,'sourceBlendSHA256':DONOR_SHA,
            'canonicalGLBSHA256':TARGET_SHA,'vendorCommit':VENDOR_SHA,'vendorScriptHashes':vendorhash,
            'agentsBlobSHA':AGENTS_BLOB,'liveCampaignEtiquetteReadAtAuthoring':'2026-11-06','resultsSHA256':sha(work/'RESULTS.json'),
            'reportSHA256':sha(work/'REPORT.md'),'testClipsSucceeded':succeeded,
            'canonicalGitTreeBefore':tree_before,'canonicalGitTreeAfter':{n:gstr(repo,'rev-parse','HEAD:'+n) for n in LOCKED},
            'canonicalModified':False,'ownerReviewRequired':True}
  (work/'EVIDENCE_RECEIPT.json').write_text(json.dumps(evidence,indent=2)+'\n')
  if evidence['canonicalGitTreeAfter']!=tree_before:raise RuntimeError('CANONICAL_ASSET_TREE_CHANGED_BEFORE_PUBLICATION')
  for dst,name in OUTPUT.items():safe_copy(work/name,repo/dst)
  git(repo,'add','--',*sorted(OUTPUT))
  staged=set(gstr(repo,'diff','--cached','--name-only').splitlines())
  if staged!=set(OUTPUT):raise RuntimeError('EVIDENCE_PATH_ALLOWLIST_VIOLATION '+repr(staged))
  git(repo,'commit','-m','Obsidianti: archive real Mwni plugin install and foot-IK test findings',timeout=180)
  record['evidenceCommit']=push_readback(repo,'EVIDENCE')
  for dst,name in OUTPUT.items():
   if gstr(repo,'show','HEAD:'+dst)!=(work/name).read_text().strip():raise RuntimeError('EVIDENCE_REMOTE_READBACK_BYTES_DIFFER '+dst)
  if {n:gstr(repo,'rev-parse','HEAD:'+n) for n in LOCKED}!=tree_before:raise RuntimeError('PROTECTED_TREE_MUTATED')
  for name in OUTPUT.values():
   userdest=downloads/(V+'_'+runid+'_'+name);safe_copy(work/name,userdest)
   print('DOWNLOAD_EVIDENCE='+str(userdest),flush=True)
  for clip in succeeded:
   for key in ('candidateGLB','editableBlend'):
    p=pathlib.Path(trials[clip]['verdict']['outputPaths'][key]['path'])
    if sha(p)!=trials[clip]['verdict']['outputPaths'][key]['sha256']:raise RuntimeError('CANDIDATE_SHA_CHANGED '+str(p))
    dest=downloads/(V+'_'+runid+'_'+p.name)
    safe_copy(p,dest)
    print('DOWNLOAD_UNAPPROVED_CANDIDATE='+str(dest)+' SHA256='+sha(dest),flush=True)
  record['status']='PLUGIN_TESTS_EXECUTED_REPORT_COMMITTED_REMOTE_VERIFIED'
  record['testSuccessCount']=len(succeeded)
  record['evidenceCommitReadback']=record['evidenceCommit'];save()
  print('REPORT_URL=https://github.com/Valar05/parametric-parambulator/blob/'+record['evidenceCommit']+'/'+DIR+'/REPORT.md',flush=True)
  print('RESEARCH_COMMIT='+record['evidenceCommit'],flush=True)
  print('PLUGIN_REAL_TESTS_PASSED='+str(len(succeeded))+'/2',flush=True)
  print('CANONICAL_MODEL_UNCHANGED=YES',flush=True)
  print('STATUS='+record['status'],flush=True)
 except Exception as e:
  record['status']='BLOCKED';record['error']=str(e);record['traceback']=traceback.format_exc()[-5000:];save()
  print('STATUS=BLOCKED '+str(e),flush=True)
  raise
 finally:
  save();print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('USAGE driver.py PACKET_DIR LAUNCHER_PATH LAUNCHER_SHA')
 main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve(),sys.argv[3])
