#!/usr/bin/env python3
"""One-invocation Termux Git campaign: purchased ARP full source library to one review GLB."""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,time,uuid,traceback,zipfile,re
V='MUDMAN_ARES_FULL_RETARGET_v2.0.22'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE='09165dc8a47b032e5ef84d93220301e64674efad' # toe-roll evidence source pinned
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
ARES='63b6e7a7250cfb03e49cf0d335101d808126ae926894d74c1b2a6a49936b8b2a'
MUDZIP='fbcb592ac941dbc34ecade66b044b551f5bd55bf5855be50d8af5caba0514f79'
MUDFBX='4d4f3c503e33a4eb4ca6039b9dc1b7b83e5c1ce25b371625aee53ba2e1c89ff7'
MUDPNG='f1a6089742844a6a3b0a4b7c93ce6ca80faf126adf92ec135bb7aa26a478e886'

ARPZIP='2b377bbc5d81dfcef4209971e332a8bcb402ed44605e5ed0cddc2e90fafebf28'
TARGET='assets/obsidianti/Obsidianti.glb'
LOCKED=[TARGET,'assets/repl/Repl.glb',
        'diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/20261107T021037Z-2edec0d5/AxeKick/ARP_AxeKick_REVIEW.glb']
OLDTRIAL='campaigns/OBSIDIANTI_ARP_BLENDER5_ISOLATED_v2.0.12_blender_trial.py'
OLDEXPORT='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_export.py'
OLDVIEW='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_viewer.html'
OLDSERVER='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_server.py'
OLDHELPER='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py'
REL='diagnostics/mudman/ares-full-retarget-v2.0.22/runs/'
SOURCES={
 'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER',
 'campaigns/'+V+'_driver.py':'driver.py',
 'campaigns/'+V+'_derive.py':'derive.py',
 'campaigns/'+V+'_audit.py':'audit.py',
 'campaigns/'+V+'_fbx_native.py':'fbx_native.py',
 'campaigns/'+V+'_merge.py':'merge.py',
 'campaigns/'+V+'_blender_trial.py':'blender_trial.py',
 'campaigns/'+V+'_export.py':'export.py',
 'campaigns/'+V+'_viewer.html':'viewer.html',
 'campaigns/'+V+'_server.py':'server.py',
 'campaigns/'+V+'.contract.json':'contract.json',
 'tests/'+V+'_TEST.py':'test_driver.py'}

sys.dont_write_bytecode=True  # NEVER generate __pycache__ inside a verified checkout

def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for buf in iter(lambda:f.read(1048576),b''):h.update(buf)
 return h.hexdigest()

def command(argv,timeout=500,check=True,env=None):
 argv=[str(x) for x in argv]
 p=subprocess.run(argv,capture_output=True,text=True,errors='replace',stdin=subprocess.DEVNULL,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED_'+str(p.returncode)+' '+repr(argv[:5])+' '+p.stderr[-600:]+' '+p.stdout[-250:])
 return p

def git(repo,*a,timeout=400,check=True):return command(['git','-C',repo,*a],timeout=timeout,check=check)
def g(repo,*a):return git(repo,*a).stdout.strip()
def write_json(p,value):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_name('.'+p.name+'.'+uuid.uuid4().hex[:8]+'.tmp')
 tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');os.replace(tmp,p)
def copy_new(a,b):
 a=pathlib.Path(a);b=pathlib.Path(b)
 if not a.is_file() or a.is_symlink():raise RuntimeError('SOURCE_NOT_REGULAR_'+str(a))
 if b.exists():
  if b.is_file() and not b.is_symlink() and digest(b)==digest(a):return
  raise RuntimeError('DESTINATION_COLLISION_'+str(b))
 b.parent.mkdir(parents=True,exist_ok=True)
 temp=b.with_name('.'+b.name+'.'+uuid.uuid4().hex[:8])
 shutil.copy2(a,temp)
 if digest(a)!=digest(temp):raise RuntimeError('COPY_HASH_MISMATCH')
 os.replace(temp,b)
def require(expr,label):
 if not expr:raise RuntimeError(label)
def patch_one(s,old,new):
 n=s.count(old)
 if n!=1:raise RuntimeError('SOURCE_PATCH_PRECONDITION_'+str(n)+'_'+old[:70])
 return s.replace(old,new,1)
def import_path(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 return mod

def verify_pinned_ancestry(repo,base,head):
 """Prove the pinned base is truly in the history of the checked-out main.

 A depth-one clone has no parent for HEAD. Fetching only the BASE object does
 not restore HEAD's parent links; the old campaign falsely rejected valid Git.
 Deepen the TRACKED main history, not just the pinned commit object. The full
 history fallback is bounded and never changes the checked-out revision.
 """
 if git(repo,'merge-base','--is-ancestor',base,head,check=False).returncode==0:
  return {'base':base,'head':head,'method':'ALREADY_COMPLETE','isAncestor':True}
 observed=[]
 for stage,flags in [('DEEPEN_16',['--deepen=16']),('DEEPEN_128',['--deepen=128']),
                     ('DEEPEN_512',['--deepen=512']),('UNSHALLOW',['--unshallow'])]:
  if g(repo,'rev-parse','--is-shallow-repository')!='true':break
  last=None
  for attempt in range(2):
   p=git(repo,'fetch','--no-tags',*flags,'origin','main',timeout=1000,check=False)
   observed.append({'stage':stage,'attempt':attempt+1,'returnCode':p.returncode})
   last=p
   if p.returncode==0:break
   time.sleep(attempt+1)
  if last is None or last.returncode!=0:
   raise RuntimeError('GIT_MAIN_HISTORY_FETCH_FAILED_'+stage+'_rc='+str(last.returncode if last else 'NONE')+
                      '_'+str(last.stderr[-450:] if last else ''))
  require(g(repo,'rev-parse','HEAD')==head,'GIT_HISTORY_FETCH_CHANGED_CHECKED_OUT_HEAD')
  if git(repo,'merge-base','--is-ancestor',base,head,check=False).returncode==0:
   print('GIT_SHALLOW_ANCESTRY_RECOVERED='+stage+' BASE='+base+' HEAD='+head,flush=True)
   return {'base':base,'head':head,'method':stage,'attempts':observed,'isAncestor':True}
 # Do not silently accept an unrelated, rewritten branch. An unshallowed Git
 # graph with no ancestor relationship is a real divergence and is a hard stop.
 raise RuntimeError('PINNED_GIT_BASE_NOT_ANCESTOR_AFTER_VERIFIED_MAIN_HISTORY_FETCH '+
                    'base='+base+' head='+head+' shallow='+g(repo,'rev-parse','--is-shallow-repository'))

def checkout(root):
 repo=root/'repo'
 env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
 command(['git','clone','--quiet','--depth=1','--branch=main','--single-branch',REMOTE,repo],timeout=1200,env=env)
 require(g(repo,'remote','get-url','origin').removesuffix('.git')==REMOTE.removesuffix('.git'),'WRONG_REMOTE')
 head=g(repo,'rev-parse','HEAD')
 ancestry=verify_pinned_ancestry(repo,BASE,head)
 require(g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'AGENTS_CHANGED_RULES_READ_BLOCKED')
 for p,sha in ((TARGET,CANON),):
  require('oid sha256:'+sha in git(repo,'show','HEAD:'+p).stdout,'PINNED_LFS_POINTER_CHANGED_'+p)
 require(not g(repo,'status','--porcelain'),'ISOLATED_CHECKOUT_NOT_CLEAN')
 return repo,head,ancestry

def hydrate(repo,paths):
 git(repo,'lfs','install','--local',timeout=100)
 for path,expected in paths.items():
  if (repo/path).is_file() and digest(repo/path)==expected:continue
  git(repo,'lfs','pull','--include='+path,'--exclude=','origin',timeout=2000,check=False)
  git(repo,'lfs','fetch','--include='+path,'--exclude=','origin','HEAD',timeout=2000,check=False)
  git(repo,'lfs','checkout',path,timeout=450,check=False)
  require((repo/path).is_file() and digest(repo/path)==expected,'VERIFIED_LFS_OBJECT_UNAVAILABLE_'+path)
  print('INPUT_VERIFIED='+path+' SHA256='+expected,flush=True)

def source_ares(downloads):
 roots=[downloads,downloads.parent/'Documents',downloads.parent/'Models',downloads.parent]
 seen=set()
 for folder in roots:
  if not folder.is_dir():continue
  for p in sorted(folder.glob('Ares*.blend')):
   if p in seen:continue
   seen.add(p)
   if p.is_file() and not p.is_symlink() and digest(p)==ARES:return p
 raise RuntimeError('EXACT_OWNER_ARES_BLEND_MISSING_FROM_ANDROID_DOWNLOADS_SHA_'+ARES)

def target_zip(downloads,root):
 files=sorted(downloads.glob('Meshy_AI_Mudstone_Golem*.zip'))
 actual=next((p for p in files if p.is_file() and not p.is_symlink() and digest(p)==MUDZIP),None)
 require(actual is not None,'OWNER_MUDMAN_MESHY_ZIP_MISSING_OR_CHANGED_SHA_'+MUDZIP)
 target=root/'input';target.mkdir(parents=True,exist_ok=True)
 fbx=target/'Meshy_AI_Mudstone_Golem_20261107_animated_mixamo_Running.fbx'
 png=fbx.with_suffix('.png')
 if fbx.is_file() and png.is_file() and digest(fbx)==MUDFBX and digest(png)==MUDPNG:
  return actual,fbx,png
 with zipfile.ZipFile(actual) as z:
  members=[x for x in z.infolist() if not x.is_dir()]
  require(len(members)==2 and {pathlib.PurePosixPath(x.filename).suffix for x in members}=={'.fbx','.png'},'MUDMAN_ZIP_MEMBER_INVENTORY_UNEXPECTED')
  for x in members:
   name=pathlib.PurePosixPath(x.filename).name
   require(len(pathlib.PurePosixPath(x.filename).parts)==2 and name in (fbx.name,png.name),'UNTRUSTED_MUDMAN_ZIP_MEMBER_PATH')
   dest=target/name
   data=z.read(x)
   expected=MUDFBX if name.endswith('.fbx') else MUDPNG
   require(hashlib.sha256(data).hexdigest()==expected,'MUDMAN_ZIP_UNCOMPRESSED_BYTES_CHANGED_'+name)
   if dest.is_file():require(digest(dest)==expected,'MUDMAN_PRIVATE_INPUT_COLLISION_'+name)
   else:
    tmp=dest.with_name('.'+dest.name+'.tmp');tmp.write_bytes(data)
    os.replace(tmp,dest)
 require(digest(fbx)==MUDFBX and digest(png)==MUDPNG,'MUDMAN_EXTRACT_HASH_MISMATCH')
 return actual,fbx,png

def vendor(downloads):
 archive=downloads/'auto_rig_pro_3.79.17.zip'
 require(archive.is_file() and digest(archive)==ARPZIP,'PURCHASED_ARP_ZIP_MISSING_OR_CHANGED')
 private=pathlib.Path.home()/'.local/share/obsidianti-arp-purchased/3.79.17'/ARPZIP[:16]/'modules'
 require(private.is_dir() and len([p for p in private.iterdir() if p.is_dir() and (p/'__init__.py').is_file()])==1,'PURCHASED_ARP_PRIVATE_MODULE_MISSING')
 return private

def publish(repo,stage,required_protected):
 # Use the existing proved bounded rebase/readback policy, additive-only source files.
 for attempt in range(4):
  want=g(repo,'rev-parse','HEAD')
  result=git(repo,'push','origin','HEAD:refs/heads/main',timeout=800,check=False)
  if result.returncode==0:
   remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()
   require(remote and remote[0]==want,'PUSH_REMOTE_HEAD_READBACK_MISMATCH')
   git(repo,'fetch','--quiet','origin','main',timeout=400)
   require(g(repo,'rev-parse','refs/remotes/origin/main')==want,'REMOTE_FETCH_MISMATCH')
   for p,blob in required_protected.items():
    require(g(repo,'rev-parse','HEAD:'+p)==blob,'PROTECTED_BLOB_CHANGED_'+p)
   return want
  if attempt==3:raise RuntimeError('GIT_PUSH_BLOCKED_'+stage+'_'+result.stderr[-650:])
  git(repo,'fetch','--quiet','origin','main',timeout=450)
  for p,blob in required_protected.items():
   require(g(repo,'rev-parse','refs/remotes/origin/main:'+p)==blob,'REMOTE_PROTECTED_ASSET_ADVANCED_STOP')
  git(repo,'rebase','refs/remotes/origin/main',timeout=500)
 raise RuntimeError('PUBLICATION_EXHAUSTED')

def commit(repo,files,stage,protected):
 if any((repo/p).exists() for p in files):raise RuntimeError('VERSIONED_DESTINATION_COLLISION_'+stage)
 for p,f in files.items():copy_new(f,repo/p)
 git(repo,'add','--',*sorted(files))
 staged=set(g(repo,'diff','--cached','--name-only').splitlines())
 require(staged==set(files),'STAGED_PATH_ALLOWLIST_MISMATCH_'+stage)
 if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Termux Mudman ARP')
 if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','termux-mudman-ares@users.noreply.github.com')
 git(repo,'commit','-m','Mudman: full Ares action-slot purchased ARP '+stage)
 published=publish(repo,stage,protected)
 for path,original in files.items():
  content=git(repo,'show','refs/remotes/origin/main:'+path).stdout
  if path.endswith(('.glb','.blend')):
   require('oid sha256:'+digest(original) in content,'PUBLISHED_BINARY_LFS_POINTER_WRONG_'+path)
  else:require(content==original.read_text(),'PUBLISHED_TEXT_READBACK_WRONG_'+path)
 return published


def safe_token(value):
 value=re.sub(r'[^A-Za-z0-9_.-]','_',value)[:72]
 return value+'-'+hashlib.sha256(value.encode()).hexdigest()[:8]

def blender_argv(pd,root,private,source,fbx,script,args):
 binds=['--bind',str(private.resolve())+':/mnt/arp-private',
        '--bind',str(root.resolve())+':/mnt/arp-work',
        '--bind',str(source.parent.resolve())+':/mnt/arp-source',
        '--bind',str(fbx.parent.resolve())+':/mnt/arp-target']
 return pd+['login','obs-arp-blender50',*binds,'--','blender','--background','--factory-startup','--enable-autoexec',
             '--python','/mnt/arp-work/'+script,'--',*args]

def inventory(pd,root,private,source,fbx):
 output=root/'SOURCE_AND_TARGET_AUDIT.json'
 args=['--source','/mnt/arp-source/'+source.name,'--source-sha',ARES,
  '--target','/mnt/arp-target/'+fbx.name,'--target-sha',MUDFBX,
  '--output','/mnt/arp-work/SOURCE_AND_TARGET_AUDIT.json']
 p=command(blender_argv(pd,root,private,source,fbx,'audit.py',args),timeout=2200,check=False)
 (root/'BLENDER_AUDIT.log').write_text(p.stdout+'\n'+p.stderr)
 audit=json.loads(output.read_text()) if output.is_file() else {}
 require(p.returncode==0 and audit.get('status')=='SOURCE_AND_MUDMAN_RIG_AUDITED',
         'BLENDER_SOURCE_OR_FBX_PREFLIGHT_FAILED_'+str(audit.get('error',p.stderr[-400:]))[:650])
 require(len(audit['actions'])>=25,'BLENDER_AUDIT_FOUND_TOO_FEW_ACTION_SLOTS')
 return audit

def retarget_one(pd,root,private,source,fbx,item):
 label=item['name'];slug=safe_token(label)
 parent=root/'trials';parent.mkdir(exist_ok=True)
 folder=parent/slug
 # Never delete or overwrite failed diagnostic attempts. Isolated retries use
 # distinct directories; a previously verified GLB is reused instead.
 if folder.exists():
  for attempt in range(1,20):
   p=parent/(slug+'-retry-'+str(attempt))
   if not p.exists():folder=p;break
  else:raise RuntimeError('PER_ACTION_RETRY_LIMIT_REACHED_'+label)
 args=['--private','/mnt/arp-private','--source','/mnt/arp-source/'+source.name,
       '--source-sha',ARES,'--target','/mnt/arp-target/'+fbx.name,
       '--target-sha',MUDFBX,'--clip',label,'--action',item['action'],
       '--slot',item['slot'],'--output','/mnt/arp-work/trials/'+folder.name]
 p=command(blender_argv(pd,root,private,source,fbx,'blender_trial.py',args),timeout=4200,check=False)
 (parent/(folder.name+'_BLENDER.log')).write_text(p.stdout+'\n'+p.stderr)
 receipt=folder/'TRIAL.json';r=json.loads(receipt.read_text()) if receipt.is_file() else {}
 blend=folder/('ARP_'+label+'_UNAPPROVED.blend')
 require(p.returncode==0 and r.get('stage')=='SAVED_BLEND' and blend.is_file() and r.get('blendSHA256')==digest(blend),
  'ARES_TO_MUDMAN_ARP_FAILED_'+label+'_rc='+str(p.returncode)+' stage='+str(r.get('stage'))+' '+str(r.get('error',p.stderr[-270:]))[:360])
 require(r.get('targetAction')==label+'_remap','MUDMAN_RETARGETED_ACTION_WRONG_'+label)
 require(r.get('sourceSlot',{}).get('identifier')==item['slot'],'SOURCE_SLOT_DRIFT_'+label)
 require(r.get('mapping',{}).get('boneCount',0)>=18,'MUDMAN_MIXAMO_CORE_MAPPING_INCOMPLETE_'+label)
 return blend,r

def export_one(pd,root,blend,item):
 label=item['name'];slug=safe_token(label)
 folder=root/'exports';folder.mkdir(exist_ok=True)
 glb=folder/(slug+'.glb');receipt=folder/(slug+'.json')
 args=pd+['login','obs-arp-blender50',
    '--bind',str(blend.parent.resolve())+':/mnt/arp-source',
    '--bind',str(root.resolve())+':/mnt/arp-work','--',
    'blender','--background','--factory-startup','--disable-autoexec','--python','/mnt/arp-work/export.py','--',
    '--source','/mnt/arp-source/'+blend.name,'--sha',digest(blend),
    '--action',label+'_remap','--output','/mnt/arp-work/exports/'+glb.name,
    '--receipt','/mnt/arp-work/exports/'+receipt.name]
 p=command(args,timeout=2400,check=False)
 (folder/(slug+'_EXPORT.log')).write_text(p.stdout+'\n'+p.stderr)
 r=json.loads(receipt.read_text()) if receipt.is_file() else {}
 require(p.returncode==0 and r.get('status')=='BLENDER5_SAVED_ARP_ACTION_EXPORTED_GLB' and glb.is_file() and digest(glb)==r.get('glbSHA256'),
  'MUDMAN_GLTF_EXPORT_FAILED_'+label+'_rc='+str(p.returncode)+' '+str(r.get('error',p.stderr[-270:]))[:330])
 return glb,r

def validate_contract(contract):
 """Verifies all immutable identity hashes before any Git or Blender work.

 Regression: v2.0.20 embedded a 71-character wrong Ares SHA in its
 contract. This function is also tested with an intentionally malformed SHA.
 """
 expected={'schema':V,'authority':'TERMUX_GIT_ONLY','aresSHA256':ARES,
           'targetZipSHA256':MUDZIP,'targetFBXSHA256':MUDFBX,
           'targetTextureSHA256':MUDPNG,
           'canonicalObsidiantiSHA256':CANON,
           'purchasedARPZipSHA256':ARPZIP,'agentsBlob':AGENTS,
           'pinnedGitBase':BASE,
           'repository':'Valar05/parametric-parambulator'}
 for field,want in expected.items():
  got=contract.get(field)
  if got!=want:
   raise RuntimeError('CONTRACT_FIELD_MISMATCH_'+field+'_expected_'+want[:22]+'_got_'+str(got)[:45])
 for field in ('aresSHA256','targetZipSHA256','targetFBXSHA256','targetTextureSHA256',
               'canonicalObsidiantiSHA256','purchasedARPZipSHA256','agentsBlob','pinnedGitBase'):
  if len(contract[field]) not in (40,64) or not all(c in '0123456789abcdef' for c in contract[field]):
   raise RuntimeError('CONTRACT_HASH_MALFORMED_'+field)
 require(sorted(contract.get('sourceMutablePaths',[]))==sorted(SOURCES),'MUTABLE_PATH_CONTRACT_MISMATCH')
 require(contract.get('canonicalMutationAllowed') is False,'CONTRACT_CANONICAL_MUTATION_FORBIDDEN')
 require(contract.get('securityTitanUsed') is False,'CONTRACT_DONOR_BOUNDARY')
 return True

def main(packet,launcher,expected):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 require(launcher.is_file() and digest(launcher)==expected,'LAUNCHER_SHA_MISMATCH')
 manifest=json.loads((packet/'manifest.json').read_text())
 wanted={'driver.py','derive.py','audit.py','fbx_native.py','merge.py','test_driver.py','contract.json'}
 require(set(manifest)==wanted and all(digest(packet/n)==sha for n,sha in manifest.items()),'PAYLOAD_MEMBER_SHA_MISMATCH')
 contract=json.loads((packet/'contract.json').read_text())
 validate_contract(contract)
 for n in ('driver.py','derive.py','audit.py','fbx_native.py','merge.py','test_driver.py'):
  command(['python3','-m','py_compile',str(packet/n)])
 command(['python3',str(packet/'test_driver.py'),str(packet/'merge.py')],timeout=220)
 downloads=pathlib.Path.home()/'storage/downloads';require(downloads.is_dir(),'ANDROID_DOWNLOADS_MOUNT_MISSING')
 state_home=pathlib.Path.home()/'.local/state'/V;state_home.mkdir(parents=True,exist_ok=True)
 root=state_home/'working';root.mkdir(exist_ok=True)
 receipt=root/'RECEIPT.json'
 if receipt.is_file():
  state=json.loads(receipt.read_text())
  require(state.get('launcherSHA256')==expected and state.get('schema')==V,'CAMPAIGN_RESUME_IDENTITY_MISMATCH')
  require(state.get('authority')=='TERMUX_GIT_ONLY','RESUME_AUTHORITY_MISMATCH')
 else:
  runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
  state={'schema':V,'runId':runid,'status':'BOOT','stage':'BOOT','launcherSHA256':expected,
    'authority':'TERMUX_GIT_ONLY','rulesBlob':AGENTS,'pinnedGitBase':BASE,
    'canonicalSHA256':CANON,'canonicalModified':False,'previousObsidiantiAnimationsModified':False,
    'securityTitanNotUsed':True,'purchasedARPSourcePublished':False,'ownerVisualAcceptance':'PENDING'}
 def mark(stage):
  state['stage']=stage;write_json(receipt,state);print('STAGE='+stage,flush=True)
 runid=state['runId'];mark('BOOT_OR_RESUME')
 try:
  source=source_ares(downloads)
  zip_file,fbx,png=target_zip(downloads,root)
  private=vendor(downloads)
  state['inputAresSHA256']=digest(source);state['inputMudmanZipSHA256']=digest(zip_file)
  state['inputFBXSHA256']=digest(fbx);state['inputTextureSHA256']=digest(png)
  mark('OWNER_ARES_AND_MUDMAN_ZIP_VERIFIED')
  repo=root/'repo';deriver=import_path(packet/'derive.py','mudman_derived_sources')
  if not repo.is_dir():
   repo,head,ancestry=checkout(root);state['inputHead']=head;state['gitAncestryProof']=ancestry
  else:
   head=g(repo,'rev-parse','HEAD');state['resumeGitHead']=head
   require(g(repo,'remote','get-url','origin').removesuffix('.git')==REMOTE.removesuffix('.git'),'RESUME_WRONG_REMOTE')
   require(g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'RESUME_AGENTS_CHANGED')
  protected={p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}
  if 'protectedBefore' in state:require(state['protectedBefore']==protected,'RESUME_PROTECTED_PATH_CHANGED')
  state['protectedBefore']=protected
  require(g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'RULES_READ_BLOCKED')
  # The source-only phase is guaranteed to be non-mutating with respect to
  # canonical character assets and all prior review binaries.
  for name in (OLDTRIAL,OLDEXPORT,OLDVIEW,OLDSERVER,OLDHELPER):require((repo/name).is_file(),'BASELINE_SOURCE_MISSING_'+name)
  built=deriver.make(repo,packet,V)
  state['derivedSources']=built
  for name,file in (('audit.py',packet/'audit.py'),('fbx_native.py',packet/'fbx_native.py'),('blender_trial.py',packet/'blender_trial.py'),
     ('export.py',packet/'export.py')):copy_new(file,root/name)
  if state.get('sourceCommit') is None:
   require(not g(repo,'status','--porcelain'),'ISOLATED_REPO_DIRTY_BEFORE_SOURCE_PUBLICATION')
   source_files={k:(launcher if v=='LAUNCHER' else packet/v) for k,v in SOURCES.items()}
   if all((repo/p).is_file() and digest(repo/p)==digest(f) for p,f in source_files.items()):
    # Recover a crash immediately after Git push, not duplicate the publish.
    sc=g(repo,'rev-parse','HEAD');remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()
    require(remote and remote[0]==sc,'SOURCE_COMMIT_REMOTE_UNCONFIRMED')
    state['sourceCommit']=sc
   else:state['sourceCommit']=commit(repo,source_files,'SOURCE',protected)
  mark('SOURCE_COMMITTED_AND_REMOTE_READBACK')
  # Keep python import from creating __pycache__ in the isolated Git checkout.
  old=import_path(repo/OLDHELPER,'mudman_v213_private_blender_runtime')
  require(not g(repo,'status','--porcelain'),'HELPER_IMPORT_DIRTIED_VERIFIED_CHECKOUT')
  pd=old.private_pd();state['blenderRuntime']=old.ensure_container(pd)
  mark('PURCHASED_ARP_BLENDER_CONTAINER_VERIFIED')
  if state.get('sourceAudit'):
   audit=state['sourceAudit']
  else:
   audit=inventory(pd,root,private,source,fbx)
   state['sourceAudit']=audit
  write_json(root/'SOURCE_AND_TARGET_AUDIT.json',audit)
  actions=audit['actions'];require(len({a['name'] for a in actions})==len(actions),'DUPLICATE_ARES_ACTION_LABELS')
  state['expectedActionSlots']=len(actions)
  state['sourceActionInventory']=[{'name':a['name'],'sourceAction':a['action'],'slot':a['slot'],'curves':a['fcurves']} for a in actions]
  mark('REAL_ARES_SLOTS_AND_MUDMAN_SKIN_AUDITED')
  # Retarget every real populated slot, including enemy and player variations.
  # Do not cherry-pick, skip on a visual heuristic, or silently replace with
  # Security Titan. Per-action errors stay visible and resumable.
  errors=dict(state.get('errors',{}));progress=dict(state.get('progress',{}));outputs={}
  for i,item in enumerate(actions,1):
   label=item['name'];slug=safe_token(label)
   glb=root/'exports'/(slug+'.glb');gr=root/'exports'/(slug+'.json')
   if glb.is_file() and gr.is_file():
    exp=json.loads(gr.read_text())
    if exp.get('glbSHA256')==digest(glb) and exp.get('status')=='BLENDER5_SAVED_ARP_ACTION_EXPORTED_GLB':
     outputs[label]=glb;progress[label]={'status':'EXPORTED','sha256':digest(glb),'resumed':True}
     print('REUSED_VERIFIED_ACTION='+label+' ('+str(i)+'/'+str(len(actions))+')',flush=True)
     continue
    raise RuntimeError('PREEXISTING_EXPORT_IDENTITY_CONFLICT_'+label)
   state['currentAction']={'index':i,'total':len(actions),'name':label,'slot':item['slot']};mark('RETARGET_'+str(i)+'_OF_'+str(len(actions))+'_'+slug)
   try:
    blend,r=retarget_one(pd,root,private,source,fbx,item)
    glb,exp=export_one(pd,root,blend,item)
    outputs[label]=glb
    # This Blend was generated exclusively inside the private campaign run,
    # and is no longer needed after a SHA-verified GLB export. Keep logs.
    blend.unlink()
    progress[label]={'status':'EXPORTED','sha256':digest(glb),'sourceMotion':r.get('sourceMotion'),
      'targetMotion':r.get('targetMotion'),'sourceSlot':r.get('sourceSlot'),
      'mappedBones':r.get('mapping',{}).get('boneCount'),
      'sourceStatic':item.get('static',False),'exportBytes':glb.stat().st_size}
    errors.pop(label,None)
    print('MUDMAN_ARES_CLIP='+label+' SHA256='+digest(glb),flush=True)
   except BaseException as exc:
    errors[label]=str(exc)[:850]
    progress[label]={'status':'FAILED','error':str(exc)[:850]}
    print('MUDMAN_ARES_ACTION_FAILED='+label+' '+str(exc)[:330],flush=True)
   state['errors']=errors;state['progress']=progress;mark('ACTION_CHECKPOINT_'+str(i))
  state['errors']=errors;state['progress']=progress;state['exportedCount']=len(outputs)
  if not outputs:raise RuntimeError('NO_REAL_ARES_ACTION_EXPORTED_TO_MUDMAN; inspect individual Blender logs')
  mark('MERGE_ALL_EXPORTED_ACTIONS')
  merged_inputs=[{'name':'Mudman_'+a['name'],'path':str(outputs[a['name']])} for a in actions if a['name'] in outputs]
  merger=import_path(packet/'merge.py','mudman_gltf_merger')
  library=root/(V+'_'+runid+'_REVIEW_LIBRARY.glb');keys=root/'KEYS.json'
  if library.is_file():
   require(keys.is_file(),'EXISTING_MERGED_GLB_MISSING_KEYS')
   doc,_=merger.load(library)
   require([x['name'] for x in doc['animations']]==[x['name'] for x in merged_inputs],'RESUMED_MERGE_ANIMATION_NAMES_CHANGED')
   mr={'merged':{'clips':len(merged_inputs),'names':[x['name'] for x in merged_inputs],'sha256':digest(library)}}
  else:
   mr=merger.merge(merged_inputs,library,keys)
  require(mr['merged']['clips']==len(outputs),'GLB_MERGED_ACTION_COUNT_WRONG')
  doc,_=merger.load(library)
  require(len(doc['animations'])==len(outputs) and len(doc.get('skins',[]))>0 and len(doc.get('meshes',[]))>0,'MUDMAN_REVIEW_NOT_ANIMATED_SKINNED_MODEL')
  out=downloads/library.name;copy_new(library,out)
  require(digest(out)==digest(library),'PHONE_DOWNLOADS_MUDMAN_LIBRARY_HASH_MISMATCH')
  state['outputSHA256']=digest(out);state['outputPath']=str(out)
  write_json(root/'ACTION_RESULTS.json',{'schema':V,'inputs':audit,'results':progress,'errors':errors,
    'expected':len(actions),'exported':len(outputs),'combinedGLBSHA256':digest(library)})
  for item in ('ACTION_RESULTS.json','SOURCE_AND_TARGET_AUDIT.json','KEYS.json'):
   dest=downloads/(V+'_'+runid+'_'+item)
   copy_new(root/item,dest)
   print('DOWNLOAD_DIAGNOSTIC='+str(dest)+' SHA256='+digest(dest),flush=True)
  mark('COMBINED_REAL_MUDMAN_GLB_AND_DIAGNOSTICS_COPIED_DOWNLOADS')
  token=hashlib.sha256((runid+state['sourceCommit']+expected+digest(out)).encode()).hexdigest()[:24]
  viewer={'schema':V,'runId':runid,'buildToken':token,'launcherSHA256':expected,
   'sourceCommit':state['sourceCommit'],'htmlPath':str(repo/('campaigns/'+V+'_viewer.html')),
   'models':{'candidate':{'sha256':digest(out),'bytes':out.stat().st_size,
     'url':'/models/candidate.glb','animations':mr['merged']['names']}},
   'modelPaths':{'candidate':str(out)},'mode':'ARES_ALL_POPULATED_SLOTS_MUDMAN_MIXAMO_PURCHASED_ARP_UNAPPROVED'}
  old.V=V
  if state.get('viewerURL') and state.get('viewerHTTPVerified'):
   ticket={'url':state['viewerURL'],'pid':state.get('serverPID'),'port':state.get('serverPort')}
  else:
   ticket=old.start_server(root,repo,viewer)
   state['viewerURL']=ticket['url'];state['serverPID']=ticket['pid'];state['serverPort']=ticket['port']
  state['viewerHTTPVerified']=True
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(old.open_browser(ticket['url'])).upper(),flush=True)
  mark('REAL_GLB_SHA_VERIFIED_HTTP_VIEWER')
  evidence={'schema':V,'runId':runid,'authority':'TERMUX_GIT_ONLY','rulesBlob':AGENTS,
   'baseGitHead':state.get('inputHead'),'sourceCommit':state['sourceCommit'],
   'sourceAresSHA256':ARES,'targetZipSHA256':MUDZIP,'targetFBXSHA256':MUDFBX,'targetTextureSHA256':MUDPNG,
   'purchasedARPZipSHA256':ARPZIP,'canonicalObsidiantiSHA256':CANON,
   'canonicalModified':False,'securityTitanUsed':False,'previousAcceptedAnimationsModified':False,
   'sourceActionDatablocks':audit['sourceActionDatablocks'],'populatedActionSlots':len(actions),
   'exportedAnimations':len(outputs),'failures':errors,
   'outputSHA256':digest(out),'outputBytes':out.stat().st_size,'outputPath':str(out),
   'viewerURL':ticket['url'],'viewerHTTPVerified':True,'ownerVisualAcceptance':'PENDING',
   'protectedBefore':protected,'protectedAfter':{p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED},
   'gitAncestryProof':state.get('gitAncestryProof'),'texture':'EXACT_OWNER_MESHY_PNG',
   'ARPProfile':'AUTO_SCALE_HIPS_ROOT_AND_LOCATION_ALL_NATIVE_MIXAMO_MAPPING'}
  require(evidence['protectedAfter']==protected,'PROTECTED_ORIGINAL_GIT_OBJECT_CHANGED')
  write_json(root/'EVIDENCE.json',evidence)
  report=root/'REPORT.md'
  report.write_text('# Mudman / All Ares animations | purchased ARP v2.0.21\n\n'
   +'**Status:** '+('ALL_REAL_ARES_ACTION_SLOTS_EXPORTED' if not errors else 'PARTIAL_EXPERIMENT_WITH_RECORDED_ERRORS')
   +'; OWNER VISUAL REVIEW PENDING.\n\n'
   +'## Exact source\n\nAres (2).blend SHA256 `'+ARES+'`. Meshy Running FBX ZIP SHA256 `'+MUDZIP+'`. Original FBX and texture remain unchanged. No Security Titan donor.\n\n'
   +'## Full inventory\n\n'+str(len(actions))+' populated Mixamo armature action slots from '
   +str(audit['sourceActionDatablocks'])+' source Action datablocks. Includes independently identified enemy-vs-player Cross slots. Exported: '
   +str(len(outputs))+'. Failed: '+str(len(errors))+'.\n\n'
   +'## Per-slot result\n\n'+''.join('- '+a['name']+' (action='+a['action']+', slot='+a['slot']+'): '+progress[a['name']]['status']
      +((' | '+errors[a['name']]) if a['name'] in errors else '')+'\n' for a in actions)
   +'\n## Outputs\n\n'+out.name+' SHA256 `'+digest(out)+'`.\n\nViewer: '+ticket['url']
   +'\n\nAres all-slot retarget only, no animation cleanup, no target sculpt, original Running FBX preserved separately, no canonical Obsidianti/Repl/Git library mutation.\n')
  dest=REL+runid+'/'
  files={dest+'REPORT.md':report,dest+'KEYS.json':keys,
   dest+'SOURCE_AND_TARGET_AUDIT.json':root/'SOURCE_AND_TARGET_AUDIT.json',
   dest+'ACTION_RESULTS.json':root/'ACTION_RESULTS.json',dest+'EVIDENCE.json':root/'EVIDENCE.json',
   dest+'MUDMAN_ARES_FULL_LIBRARY_UNAPPROVED.glb':out}
  glb_rel=dest+'MUDMAN_ARES_FULL_LIBRARY_UNAPPROVED.glb'
  require('lfs' in git(repo,'check-attr','filter','--',glb_rel).stdout,'MUDMAN_EXPERIMENT_GLB_NOT_GIT_LFS_TRACKED')
  if state.get('evidenceCommit'):
   ev=state['evidenceCommit']
   require(g(repo,'rev-parse','HEAD')==ev,'EVIDENCE_RESUME_GIT_HEAD_CHANGED')
  else:
   ev=commit(repo,files,'EVIDENCE',protected)
   state['evidenceCommit']=ev
  state['status']='MUDMAN_ARES_FULL_LIBRARY_REVIEW_READY_UNAPPROVED' if not errors else 'MUDMAN_ARES_PARTIAL_LIBRARY_REVIEW_READY_UNAPPROVED'
  mark('REMOTE_GIT_EVIDENCE_PUBLISHED')
  print('MUDMAN_REVIEW_GLB='+str(out),flush=True)
  print('MUDMAN_REVIEW_SHA256='+digest(out),flush=True)
  print('EVIDENCE_URL=https://github.com/Valar05/parametric-parambulator/blob/'+ev+'/'+dest+'REPORT.md',flush=True)
  print('OBSIDIANTI_AND_PREVIOUS_ANIMATIONS_UNCHANGED=YES',flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as exc:
  state.update({'status':'BLOCKED','errorType':type(exc).__name__,'error':str(exc)[:1600],
    'traceback':traceback.format_exc()[-3500:]})
  write_json(receipt,state)
  print('STATUS=BLOCKED '+str(exc)[:900],flush=True)
  raise
 finally:
  write_json(receipt,state)
  print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('usage: driver.py PACKET LAUNCHER SHA256')
 main(sys.argv[1],sys.argv[2],sys.argv[3])
