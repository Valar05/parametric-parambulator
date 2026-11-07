#!/usr/bin/env python3
"""One-invocation Termux Git campaign: purchased ARP full source library to one review GLB."""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,time,uuid,traceback
V='OBSIDIANTI_ARP_FULL_LIBRARY_v2.0.14'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE='3501004150ac2db37a2609872004827427d2b126'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
LION='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
ARES='63b6e7a7250cfb03e49cf0d335101d808126ae926894d74c1b2a6a49936b8b2a'
ARPZIP='2b377bbc5d81dfcef4209971e332a8bcb402ed44605e5ed0cddc2e90fafebf28'
AXE='c6f1d74b2de97e12f2eefc9c44a0404c26ad19e29d481af08e585130ee9103da'
HEAVY='1738d067cdc3f0f47ceab3cb31320f0f8700f471db74011c2dd0db08d84b2c75'
OLD_RUN='20261107T021037Z-2edec0d5'
DONOR='assets/obsidianti/source/LionheartLancer.blend'
TARGET='assets/obsidianti/Obsidianti.glb'
LOCKED=[TARGET,'assets/repl/Repl.glb']
OLDTRIAL='campaigns/OBSIDIANTI_ARP_BLENDER5_ISOLATED_v2.0.12_blender_trial.py'
OLDEXPORT='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_export.py'
OLDVIEW='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_viewer.html'
OLDSERVER='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_server.py'
OLDHELPER='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py'
LION_CLIPS=['Idle','Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp']
ARES_CLIPS=['Idle-Cross','StepForward','StepBack','StepLeft','StepRight','StepForwardLeft','StepForwardRight','StepBackLeft','StepBackRight','AxeKick']
CONTROL_RELS={
 'AxeKick_remap':f'diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/{OLD_RUN}/AxeKick/ARP_AxeKick_REVIEW.glb',
 'Heavy1_old_ARP':f'diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/{OLD_RUN}/Heavy1/ARP_Heavy1_REVIEW.glb'}
REL='diagnostics/obsidianti/arp-full-library-v2.0.14/runs/'
SOURCES={
 'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER',
 'campaigns/'+V+'_driver.py':'driver.py',
 'campaigns/'+V+'_merge.py':'merge.py',
 'campaigns/'+V+'_blender_trial.py':'blender_trial.py',
 'campaigns/'+V+'_viewer.html':'viewer.html',
 'campaigns/'+V+'_server.py':'server.py',
 'campaigns/'+V+'.contract.json':'contract.json',
 'tests/'+V+'_TEST.py':'test_driver.py'}

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

def checkout(root):
 repo=root/'repo'
 env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
 command(['git','clone','--quiet','--depth=1','--branch=main','--single-branch',REMOTE,repo],timeout=1200,env=env)
 require(g(repo,'remote','get-url','origin').removesuffix('.git')==REMOTE.removesuffix('.git'),'WRONG_REMOTE')
 head=g(repo,'rev-parse','HEAD')
 if head!=BASE:
  a=git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False)
  if a.returncode:
   git(repo,'fetch','--no-tags','--depth=400','origin',BASE,timeout=950)
   require(git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False).returncode==0,'GIT_HEAD_NOT_DESCENDED_FROM_PINNED_BASE')
 require(g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'AGENTS_CHANGED_RULES_READ_BLOCKED')
 for p,sha in ((TARGET,CANON),(DONOR,LION)):
  require('oid sha256:'+sha in git(repo,'show','HEAD:'+p).stdout,'PINNED_LFS_POINTER_CHANGED_'+p)
 require(not g(repo,'status','--porcelain'),'ISOLATED_CHECKOUT_NOT_CLEAN')
 return repo,head

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
 paths=list(downloads.glob('Ares*.blend'))+list(downloads.glob('Ares*.blend*'))
 paths=list(dict.fromkeys(paths))
 for p in sorted(paths):
  if p.is_file() and not p.is_symlink() and digest(p)==ARES:return p
 raise RuntimeError('EXACT_ARES_SOURCE_NOT_IN_ANDROID_DOWNLOADS_SHA_'+ARES)

def vendor(downloads):
 archive=downloads/'auto_rig_pro_3.79.17.zip'
 require(archive.is_file() and digest(archive)==ARPZIP,'PURCHASED_ARP_ZIP_MISSING_OR_CHANGED')
 private=pathlib.Path.home()/'.local/share/obsidianti-arp-purchased/3.79.17'/ARPZIP[:16]/'modules'
 require(private.is_dir() and len([p for p in private.iterdir() if p.is_dir() and (p/'__init__.py').is_file()])==1,
         'PURCHASED_ARP_PRIVATE_MODULE_MISSING')
 return private

def create_sources(repo,packet):
 # The source is the exact prior successful ARP plugin runner; only the Hips mapping option changes.
 src=(repo/OLDTRIAL).read_text()
 src=patch_one(src,"if hasattr(item,'location') and source_name=='mixamorig:Hips':item.location=True",
                    "if hasattr(item,'location') and source_name=='mixamorig:Hips':item.location=False")
 src=patch_one(src,"  result['sourceMotion']=motion_stats(witnesses(src,start,end))",
     "  result['sourceWitness17']=witnesses(src,start,end)\n  result['sourceMotion']=motion_stats(result['sourceWitness17'])")
 src=patch_one(src,"  result['targetMotion']=motion_stats(witnesses(tgt,start,end))",
     "  result['targetWitness17']=witnesses(tgt,start,end)\n  result['targetMotion']=motion_stats(result['targetWitness17'])")
 scale_fn="""def scale_snapshot(src,tgt):
 def one(o):
  def leg(side):
   a=o.data.bones.get('mixamorig:'+side+'UpLeg');b=o.data.bones.get('mixamorig:'+side+'Leg')
   return round(float((a.tail_local-a.head_local).length+(b.tail_local-b.head_local).length),6) if a and b else None
  return {'scale':[round(float(v),8) for v in o.scale],
   'worldMatrix':[[round(float(v),8) for v in row] for row in o.matrix_world],
   'objectDimensions':[round(float(v),8) for v in o.dimensions],
   'legLengthsArmatureSpace':{'Left':leg('Left'),'Right':leg('Right')}}
 return {'source':one(src),'target':one(tgt)}

"""
 src=patch_one(src,'def run(args):',scale_fn+'def run(args):')
 src=patch_one(src,"  result['autoScaleOperator']=list(operator(bpy.ops.arp.auto_scale))",
   "  result['scaleBeforeAutoScale']=scale_snapshot(src,tgt)\n  result['autoScaleOperator']=list(operator(bpy.ops.arp.auto_scale))\n  result['scaleAfterAutoScale']=scale_snapshot(src,tgt)\n  result['sourceWitnessPostAutoScale17']=witnesses(src,start,end)")
 src=patch_one(src,"  result['mapping']={'boneCount':len(active),'mapped':active,'excludedCount':len(dropped)}",
  "  result['mapping']={'boneCount':len(active),'mapped':active,'excludedCount':len(dropped),\n   'hipsRoot':True,'hipsLocation':False,'profile':'ROOT_ONLY_AUTOSCALE'}")
 (packet/'blender_trial.py').write_text(src)
 compile(src,str(packet/'blender_trial.py'),'exec')
 # Existing interactive viewer, same controls and renderer, dynamic full-library selector.
 html=(repo/OLDVIEW).read_text()
 a='<option value="Heavy1">Heavy1</option><option value="AxeKick">AxeKick</option>'
 controls=[('AxeKick','AxeKick | APPROVED preserved'),('Heavy1_old_ARP','Heavy1 | previous ARP baseline')]
 for clip in LION_CLIPS:
  if clip!='Heavy1':controls.append(('Lionheart_'+clip,'Lionheart '+clip))
  else:controls.append(('Lionheart_Heavy1','Lionheart Heavy1 | NEW root-only'))
 for clip in ARES_CLIPS:
  if clip!='AxeKick':controls.append(('Ares_'+clip,'Ares '+clip))
 options=''.join('<option value="'+n+'">'+label+'</option>' for n,label in controls)
 html=patch_one(html,a,options)
 html=patch_one(html,"mode==='candidate'?'candidate'+clip:'canonical'","mode==='candidate'?'candidate':'canonical'")
 html=html.replace('ARP live 3D review','ARP full-library 3D review').replace('Heavy1 REVIEW | AxeKick OWNER ACCEPTED','Full library PREVIEW | AxeKick preserved')
 html=html.replace('Heavy1 hip/foot IK under review','all clips unapproved except preserved AxeKick')
 (packet/'viewer.html').write_text(html)
 server=(repo/OLDSERVER).read_text().replace('ObsidiantiARPViewer/2.0.13','ObsidiantiARPViewer/2.0.14')
 (packet/'server.py').write_text(server)
 return {'trial':digest(packet/'blender_trial.py'),'viewer':digest(packet/'viewer.html'),'server':digest(packet/'server.py')}

def publish(repo,stage,required_protected):
 # No force pushes. On a genuinely unrelated advance, rebase additive path-only commits.
 for attempt in range(4):
  want=g(repo,'rev-parse','HEAD')
  result=git(repo,'push','origin','HEAD:refs/heads/main',timeout=800,check=False)
  if result.returncode==0:
   remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()
   require(remote and remote[0]==want,'PUSH_REMOTE_HEAD_READBACK_MISMATCH')
   git(repo,'fetch','--quiet','origin','main',timeout=400)
   require(g(repo,'rev-parse','refs/remotes/origin/main')==want,'REMOTE_FETCH_MISMATCH')
   for p,blob in required_protected.items():require(g(repo,'rev-parse','HEAD:'+p)==blob,'PROTECTED_BLOB_CHANGED')
   return want
  if attempt==3:raise RuntimeError('GIT_PUSH_BLOCKED_'+stage+'_'+result.stderr[-650:])
  git(repo,'fetch','--quiet','origin','main',timeout=450)
  for p,blob in required_protected.items():require(g(repo,'rev-parse','refs/remotes/origin/main:'+p)==blob,'REMOTE_PROTECTED_ASSET_ADVANCED_STOP')
  # Rebase only isolated additive campaign commits. Git must resolve cleanly or stop.
  git(repo,'rebase','refs/remotes/origin/main',timeout=500)
 raise RuntimeError('PUBLICATION_EXHAUSTED')

def commit(repo,files,stage,protected):
 if any((repo/p).exists() for p in files):raise RuntimeError('VERSIONED_DESTINATION_COLLISION_'+stage)
 for p,f in files.items():copy_new(f,repo/p)
 git(repo,'add','--',*sorted(files))
 staged=set(g(repo,'diff','--cached','--name-only').splitlines())
 require(staged==set(files),'STAGED_PATH_ALLOWLIST_MISMATCH_'+stage)
 if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Termux Obsidianti ARP')
 if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','termux-obsidianti-arp@users.noreply.github.com')
 git(repo,'commit','-m','Obsidianti: full-library purchased ARP '+stage)
 published=publish(repo,stage,protected)
 for p,original in files.items():
  text=git(repo,'show','refs/remotes/origin/main:'+p).stdout
  if p.endswith('.glb'):
   require('oid sha256:'+digest(original) in text,'PUBLISHED_GLB_LFS_POINTER_WRONG_'+p)
  else:
   require(text==original.read_text(),'PUBLISHED_TEXT_READBACK_WRONG_'+p)
 return published

def retarget(pd,root,repo,private,source,source_sha,target,clip):
 slot=root/'trials'/('Ares_' if source_sha==ARES else 'Lionheart_')/clip
 if slot.exists():
  receipt=slot/'TRIAL.json';blend=slot/('ARP_'+clip+'_UNAPPROVED.blend')
  if receipt.is_file():
   r=json.loads(receipt.read_text())
   if blend.is_file() and r.get('blendSHA256')==digest(blend) and r.get('stage')=='SAVED_BLEND':
    return r,blend
  raise RuntimeError('EXISTING_INCOMPLETE_TRIAL_REQUIRES_EXPLICIT_DIAGNOSTICS_'+str(slot))
 slot.parent.mkdir(parents=True,exist_ok=True)
 cmd=pd+['login','obs-arp-blender50','--bind',str(private.resolve())+':/mnt/arp-private',
  '--bind',str(root.resolve())+':/mnt/arp-work',
  '--bind',str(source.parent.resolve())+':/mnt/arp-source',
  '--bind',str(target.parent.resolve())+':/mnt/arp-target','--',
  'blender','--background','--factory-startup','--enable-autoexec','--python',
  '/mnt/arp-work/blender_trial.py','--',
  '--private','/mnt/arp-private','--source','/mnt/arp-source/'+source.name,
  '--source-sha',source_sha,'--target','/mnt/arp-target/'+target.name,'--target-sha',CANON,
  '--clip',clip,'--output','/mnt/arp-work/trials/'+('Ares_' if source_sha==ARES else 'Lionheart_')+'/'+clip]
 p=command(cmd,timeout=3600,check=False)
 (slot.parent/(clip+'_BLENDER.log')).write_text(p.stdout+'\n'+p.stderr)
 receipt=slot/'TRIAL.json'
 r=json.loads(receipt.read_text()) if receipt.is_file() else {}
 blend=slot/('ARP_'+clip+'_UNAPPROVED.blend')
 require(p.returncode==0 and r.get('stage')=='SAVED_BLEND' and r.get('blendSHA256') and blend.is_file() and digest(blend)==r['blendSHA256'],
   'PURCHASED_ARP_RETARGET_FAILED_'+clip+'_exit='+str(p.returncode)+' stage='+str(r.get('stage'))+' error='+str(r.get('error',''))[:260])
 require(r.get('targetAction')==clip+'_remap','ARP_TARGET_ACTION_UNEXPECTED_'+clip)
 return r,blend

def export(pd,root,src,clip,sha):
 out=root/'exports';out.mkdir(exist_ok=True)
 key='Ares_'+clip if 'Ares_' in str(src) else 'Lionheart_'+clip
 glb=out/(key+'.glb');rec=out/(key+'.json')
 if glb.is_file() and rec.is_file():
  r=json.loads(rec.read_text())
  if r.get('glbSHA256')==digest(glb) and r.get('sourceBlendSHA256')==sha:return glb,r
 cmd=pd+['login','obs-arp-blender50',
   '--bind',str(src.parent.resolve())+':/mnt/arp-source',
   '--bind',str(root.resolve())+':/mnt/arp-work','--','blender','--background',
   '--factory-startup','--disable-autoexec','--python','/mnt/arp-work/export.py','--',
   '--source','/mnt/arp-source/'+src.name,'--sha',sha,'--action',clip+'_remap',
   '--output','/mnt/arp-work/exports/'+glb.name,'--receipt','/mnt/arp-work/exports/'+rec.name]
 p=command(cmd,timeout=2400,check=False)
 (out/(key+'_EXPORT.log')).write_text(p.stdout+'\n'+p.stderr)
 r=json.loads(rec.read_text()) if rec.is_file() else {}
 require(p.returncode==0 and r.get('status')=='BLENDER5_SAVED_ARP_ACTION_EXPORTED_GLB' and glb.is_file() and digest(glb)==r.get('glbSHA256'),
   'SAVED_ACTION_EXPORT_FAILED_'+key+'_rc='+str(p.returncode)+' '+str(r.get('error',''))[:280])
 return glb,r

def main(packet,launcher,expected):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 require(launcher.is_file() and digest(launcher)==expected,'LAUNCHER_OR_SELF_SHA_MISMATCH')
 mf=json.loads((packet/'manifest.json').read_text());want={'driver.py','merge.py','contract.json','test_driver.py'}
 require(set(mf)==want and all(digest(packet/n)==sha for n,sha in mf.items()),'PAYLOAD_MANIFEST_MISMATCH')
 contract=json.loads((packet/'contract.json').read_text())
 require(contract['authority']=='TERMUX_GIT_ONLY' and contract['pinnedGitBase']==BASE and sorted(contract['sourceMutablePaths'])==sorted(SOURCES),'CONTRACT_SCOPE_INVALID')
 for p in ('driver.py','merge.py','test_driver.py'):
  command(['python3','-m','py_compile',str(packet/p)])
 command(['python3',str(packet/'test_driver.py'),str(packet/'merge.py')],timeout=160)
 downloads=pathlib.Path.home()/'storage/downloads'
 require(downloads.is_dir(),'ANDROID_DOWNLOADS_MOUNT_MISSING')
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
 receipt=root/'RECEIPT.json'
 state={'schema':V,'runId':runid,'status':'BOOT','stage':'BOOT','authority':'TERMUX_GIT_ONLY',
  'launcherSHA256':expected,'canonicalSHA256':CANON,'rulesBlob':AGENTS,'etiquetteRead':'CHATGPT_LIVE_2026_11_06',
  'canonicalModified':False,'ownerVisualAcceptance':'PENDING','vendorSourcePublished':False,
  'preset':'AUTO_SCALE=ON; Hips set_as_root=ON; Hips location=OFF; other generated map unchanged',
  'allSourceActions':{'Lionheart':LION_CLIPS,'Ares':ARES_CLIPS}}
 def mark(stage):state['stage']=stage;write_json(receipt,state);print('STAGE='+stage,flush=True)
 mark('BOOT')
 try:
  private=vendor(downloads);ares=source_ares(downloads)
  state['aresSHA256']=digest(ares)
  repo,head=checkout(root);state['inputHead']=head
  protected={p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED};state['protectedBefore']=protected
  require(g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'RULES_READ_BLOCKED')
  mark('SOURCE_AND_RULES_VERIFIED')
  source_hashes=create_sources(repo,packet);state['derivedSourceSHA256']=source_hashes
  # Avoid publishing before source dependencies and legal source files are confirmed.
  for path in (OLDTRIAL,OLDEXPORT,OLDVIEW,OLDSERVER,OLDHELPER):require((repo/path).is_file(),'PREVIOUS_VERIFIED_CODE_MISSING_'+path)
  src={p:(launcher if n=='LAUNCHER' else packet/n) for p,n in SOURCES.items()}
  source_commit=commit(repo,src,'SOURCE',protected);state['sourceCommit']=source_commit;mark('SOURCE_PUBLISHED_AND_REMOTE_READBACK')
  for n,f in [('blender_trial.py',packet/'blender_trial.py'),('export.py',repo/OLDEXPORT)]:copy_new(f,root/n)
  old=import_path(repo/OLDHELPER,'verified_v213_publisher')
  pd=old.private_pd();state['blenderRuntime']=old.ensure_container(pd)
  # Verify actual source and target binaries, not Git LFS pointers alone.
  hydrate(repo,{TARGET:CANON,DONOR:LION,**{rel:AXE if name=='AxeKick_remap' else HEAVY for name,rel in CONTROL_RELS.items()}})
  mark('RUNTIME_AND_REAL_INPUT_BINARIES_VERIFIED')
  trials={};outputs={};errors={}
  jobs=[('Lionheart',clip,repo/DONOR,LION) for clip in LION_CLIPS]
  jobs += [('Ares',clip,ares,ARES) for clip in ARES_CLIPS if clip!='AxeKick']
  for family,clip,source,hashsource in jobs:
   key=family+'_'+clip
   state['currentAction']=key;mark('RETARGET_'+key)
   try:
    r,blend=retarget(pd,root,repo,private,source,hashsource,repo/TARGET,clip)
    glb,exp=export(pd,root,blend,clip,r['blendSHA256'])
    trials[key]={'status':'EXPORTED','action':r.get('targetAction'),'blendSha256':r['blendSHA256'],
     'sourceWitness17':r.get('sourceWitness17'), 'sourceWitnessPostAutoScale17':r.get('sourceWitnessPostAutoScale17'), 'targetWitness17':r.get('targetWitness17'),
     'scaleBefore':r.get('scaleBeforeAutoScale'),'scaleAfter':r.get('scaleAfterAutoScale'),
     'mapping':r.get('mapping'),'motionGate':r.get('motionGate'),'sourceMotion':r.get('sourceMotion'),
     'targetMotion':r.get('targetMotion'),'glbSHA256':exp['glbSHA256']}
    outputs[key]=glb
    print('ACTION_EXPORTED='+key+' SHA256='+digest(glb),flush=True)
   except BaseException as e:
    errors[key]=str(e)[:700];trials[key]={'status':'FAILED','error':errors[key]}
    print('ACTION_FAILED='+key+' '+errors[key],flush=True)
   state['completedActions']={k:v['status'] for k,v in trials.items()};mark('ACTION_CHECKPOINT_'+key)
  # Controls are exact preexisting, not regenerated with a changed preset.
  inputs=[{'name':'AxeKick','path':str(repo/CONTROL_RELS['AxeKick_remap'])},
          {'name':'Heavy1_old_ARP','path':str(repo/CONTROL_RELS['Heavy1_old_ARP'])}]
  inputs.extend({'name':key,'path':str(outputs[key])} for key in [f'Lionheart_{c}' for c in LION_CLIPS]+[f'Ares_{c}' for c in ARES_CLIPS if c!='AxeKick'] if key in outputs)
  write_json(root/'merge_input.json',{'clips':inputs})
  library=root/(V+'_'+runid+'_REVIEW_LIBRARY.glb')
  keyreport=root/'KEYS.json'
  merge=import_path(packet/'merge.py','v214_merge')
  merged=merge.merge(inputs,library,keyreport)
  require(merged['merged']['clips']==len(inputs),'MERGE_NOT_COMPLETE')
  output_download=downloads/library.name
  copy_new(library,output_download)
  require(digest(output_download)==merged['merged']['sha256'],'DOWNLOADS_COPIED_GLB_SHA_MISMATCH')
  state['downloadGLB']=str(output_download);state['downloadSHA256']=digest(output_download)
  state['actionsSucceeded']=len(outputs);state['actionsFailed']=errors
  state['combinedAnimations']=merged['merged']['clips']
  mark('REVIEW_GLB_COPIED_TO_ANDROID_DOWNLOADS')
  # Persistent numeric evidence from actual source/target Blender pose samples.
  trajectory={'schema':V,'preset':state['preset'],'actions':trials,'failures':errors,
   'controlClips':{'AxeKick':AXE,'Heavy1_old_ARP':HEAVY},'sourceActionCount':len(LION_CLIPS)+len(ARES_CLIPS)}
  write_json(root/'TRAJECTORIES.json',trajectory)
  for diagnostic in ('KEYS.json','TRAJECTORIES.json'):
   out=downloads/(V+'_'+runid+'_'+diagnostic)
   copy_new(root/diagnostic,out)
   require(digest(out)==digest(root/diagnostic),'DOWNLOADS_DIAGNOSTIC_CORRUPTED_'+diagnostic)
   print('DOWNLOAD_DIAGNOSTIC='+str(out)+' SHA256='+digest(out),flush=True)
  # Existing interactive viewer with a single multipackage GLB and full animation selector.
  token=hashlib.sha256((runid+source_commit+expected+digest(output_download)).encode()).hexdigest()[:24]
  manifest={'schema':V,'runId':runid,'buildToken':token,'launcherSHA256':expected,
    'sourceCommit':source_commit,'htmlPath':str(repo/('campaigns/'+V+'_viewer.html')),
    'models':{'candidate':{'sha256':digest(output_download),'bytes':output_download.stat().st_size,
      'url':'/models/candidate.glb','animations':merged['merged']['names']}},
    'modelPaths':{'candidate':str(output_download)},'canonicalModelSHA256':CANON,
    'mode':'FULL_LIBRARY_ARP_ROOT_ONLY_PLUS_ACCEPTED_AXEKICK_CONTROL'}
  # Viewer serves immutable, hash-verified Downloads GLB; no canonical replacement.
  old.V=V
  ticket=old.start_server(root,repo,manifest)
  state['viewerURL']=ticket['url'];state['serverPID']=ticket['pid'];state['serverPort']=ticket['port']
  mark('VERIFIED_HTTP_VIEWER')
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(old.open_browser(ticket['url'])).upper(),flush=True)
  evidence={'schema':V,'runId':runid,'sourceCommit':source_commit,'inputGitHead':head,
    'authority':'TERMUX_GIT_ONLY','rulesBlob':AGENTS,'purchasedARPZipSha256':ARPZIP,
    'canonicalModelSHA256':CANON,'canonicalModified':False,'preset':state['preset'],
    'allSourceActions':state['allSourceActions'],'errors':errors,
    'exportedActionCount':len(outputs),'expectedNewRetargetCount':len(jobs),
    'combinedActionCount':merged['merged']['clips'],'outputSHA256':digest(output_download),
    'outputBytes':output_download.stat().st_size,'androidDownloads':str(output_download),
    'viewerURL':ticket['url'],'viewerHTTPVerified':True,'browserRendered':'OWNER_UNVERIFIED',
    'ownerAxeKickVerdict':'ACCEPTED_UNCHANGED_SOURCE_GLB', 'ownerHeavy1Verdict':'PENDING',
    'vendorSourcePublished':False,'protectedBefore':protected,
    'protectedAfter':{p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}}
  require(evidence['protectedAfter']==protected,'PROTECTED_ASSET_CHANGED')
  write_json(root/'EVIDENCE.json',evidence)
  report=root/'REPORT.md';report.write_text(
   '# Obsidianti Auto-Rig Pro full-library review (v2.0.14)\n\n'
   +'Status: '+('ALL_21_SOURCE_ACTIONS_PRESENT' if not errors else 'PARTIAL_ACTION_FAILURES')+'; no canonical GLB mutation.\n\n'
   +'## Configuration\n\nPurchased Auto-Rig Pro 3.79.17; Auto-Scale ON; Hips Set As Root ON; Hips Location OFF. '
   +'Source runner derived from v2.0.12, one Hips location option changed. '\
   +'No manual animation corrections; existing accepted AxeKick preserved as exact earlier GLB sampler data.\n\n'
   +'## Evidence\n\nKeys: KEYS.json. True sampled source and target hip and foot joint paths: TRAJECTORIES.json.\n\n'
   +'Review GLB: '+output_download.name+' (SHA-256 '+digest(output_download)+').\n\n'
   +'Viewer: '+ticket['url']+'\n\n'
   +'Original Heavy1 also included under Heavy1_old_ARP; new Heavy1 is Lionheart_Heavy1.\n\n'
   +'## Results\n\n'+''.join('- '+key+': '+trials[key]['status']+'\n' for key in trials)
   +'\nAxeKick: accepted exact control, not re-retargeted.\n'
   +'No acceptance claim for any newly retargeted animation.\n')
  dest=REL+runid+'/'
  files={dest+'REPORT.md':report,dest+'KEYS.json':keyreport,dest+'TRAJECTORIES.json':root/'TRAJECTORIES.json',dest+'EVIDENCE.json':root/'EVIDENCE.json',
   dest+'Obsidianti_ARP_FULL_LIBRARY_UNAPPROVED.glb':output_download}
  git(repo,'lfs','install','--local',timeout=100)
  filter_attr=git(repo,'check-attr','filter','--',dest+'Obsidianti_ARP_FULL_LIBRARY_UNAPPROVED.glb').stdout.strip()
  require('lfs' in filter_attr,'REVIEW_GLB_LFS_ATTRIBUTE_NOT_CONFIGURED')
  published=commit(repo,files,'EVIDENCE',protected)
  state['evidenceCommit']=published;state['status']='ALL_ACTIONS_EXPORTED_OWNER_REVIEW_PENDING' if not errors else 'PARTIAL_LIBRARY_EXPORTED_ACTION_FAILURES_RECORDED'
  mark('REMOTE_EVIDENCE_PUBLISHED')
  print('REVIEW_GLB='+str(output_download)+' SHA256='+digest(output_download),flush=True)
  print('EVIDENCE_URL=https://github.com/Valar05/parametric-parambulator/blob/'+published+'/'+dest+'REPORT.md',flush=True)
  print('CANONICAL_UNCHANGED=YES',flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as e:
  state['status']='BLOCKED';state['errorType']=type(e).__name__;state['error']=str(e)[:1200]
  state['traceback']=traceback.format_exc()[-2400:];write_json(receipt,state)
  print('STATUS=BLOCKED '+state['error'],flush=True)
  raise
 finally:
  write_json(receipt,state);print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('usage driver.py PACKET LAUNCHER EXPECTED_SHA')
 main(sys.argv[1],sys.argv[2],sys.argv[3])
