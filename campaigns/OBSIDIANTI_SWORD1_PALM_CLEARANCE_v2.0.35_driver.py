#!/usr/bin/env python3
"""One-shot Termux Git publication: v2.0.33 SwordAttack1 palm contact and right-arm clearance.

PUBLISHES ONLY NEW VERSIONED SOURCE AND REVIEW EVIDENCE. All 42 input animations,
canonical Obsidianti, and existing donor GLBs are unchanged. No direct GitHub writes.
"""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,subprocess,sys,time,traceback,uuid
sys.dont_write_bytecode=True
V='OBSIDIANTI_SWORD1_PALM_CLEARANCE_v2.0.35'
BASE='898051da60092002cb39137d0683fbff45118085'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
SOURCE='899aa3f7f24fb3b36e80a1c96cff7d032dcacf27f990231203ba5c08f2ee066b'
SOURCE_PATH='diagnostics/obsidianti/sword1-sustained-ik-v2.0.33/runs/20261107T213143Z-f1187b82/OBSIDIANTI_SWORD1_SUSTAINED_IK_42_CLIP_REVIEW_UNAPPROVED.glb'
CANON_PATH='assets/obsidianti/Obsidianti.glb'
OLDHELPER='campaigns/MUDMAN_ARES_FULL_RETARGET_v2.0.22_driver.py'
CORE='campaigns/OBSIDIANTI_ANIMATION_REUNION_v2.0.31_compose.py'
OLDVIEW='campaigns/OBSIDIANTI_SWORD1_SUSTAINED_IK_v2.0.33_viewer.html'
OLDSERVER='campaigns/OBSIDIANTI_SWORD1_SUSTAINED_IK_v2.0.33_server.py'
HELPER_BLOB='610970b4acc11033b1345a508aa2c6c38f0e2adc'
CORE_BLOB='3203b3b0b18bdbcb247541cdac3e9d7167a50558'
VIEW_BLOB='d7e1e1bc4cc8f9ceab1e84d23b54e3208a073dbf'
SERVER_BLOB='4ab8be3a4db0ba7c8cb48c0b13c640c8a33904dc'
SC='campaigns/'+V
FILES={SC+'_LAUNCH.sh':'LAUNCHER',SC+'_driver.py':'driver.py',SC+'_fix.py':'fix.py',
       SC+'_viewer.html':'GENERATED_VIEWER',SC+'_server.py':'GENERATED_SERVER',
       SC+'.contract.json':'contract.json','tests/'+V+'_TEST.py':'test.py'}
REL='diagnostics/obsidianti/sword1-palm-clearance-v2.0.34/runs/'
PROTECTED=(CANON_PATH,SOURCE_PATH,'assets/repl/Repl.glb',
 'diagnostics/obsidianti/animation-reunion-v2.0.32/runs/20261107T203838Z-d49615bb/OBSIDIANTI_41_CLIP_SHIELD_LANCE_LIONHEART_ARP_REVIEW_UNAPPROVED.glb',
 'diagnostics/obsidianti/vanguard-rigify-arp-v2.0.17/runs/20261107T044021Z-81e43a05/OBSIDIANTI_VANGUARD_ARP_EXPERIMENT_UNAPPROVED.glb')

def require(x,msg):
 if not x:raise RuntimeError(msg)
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 require(spec and spec.loader,'VERIFIED_MODULE_MISSING_'+name)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def save(path,value):
 path=pathlib.Path(path);path.parent.mkdir(exist_ok=True,parents=True)
 temp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex[:8]+'.tmp')
 temp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');os.replace(temp,path)
def publish(helper,repo,items,stage,protected):
 exists=[p for p in items if (repo/p).exists()]
 if exists:
  require(len(exists)==len(items),'PARTIALLY_COLLIDING_OUTPUT_PATHS_'+stage)
  require(all(sha(repo/p)==sha(f) for p,f in items.items()),'NONIDENTICAL_VERSIONED_OUTPUT_COLLISION_'+stage)
  require(not helper.g(repo,'status','--porcelain'),'DIRTY_VERSIONED_REUSE_'+stage)
  return helper.g(repo,'rev-parse','HEAD')
 require(not helper.g(repo,'status','--porcelain'),'DIRTY_CHECKOUT_BEFORE_'+stage)
 for p,f in items.items():
  require(not (repo/p).exists(),'EXISTING_DESTINATION_'+p)
  helper.copy_new(f,repo/p)
 helper.git(repo,'add','--',*sorted(items))
 require(set(helper.g(repo,'diff','--cached','--name-only').splitlines())==set(items),'MUTATION_ALLOWLIST_VIOLATED')
 if not helper.git(repo,'config','user.name',check=False).stdout.strip():helper.git(repo,'config','user.name','Termux Obsidianti IK Review')
 if not helper.git(repo,'config','user.email',check=False).stdout.strip():helper.git(repo,'config','user.email','termux-obsidianti-ik@users.noreply.github.com')
 helper.git(repo,'commit','-m','Obsidianti SwordAttack1 palm IK and right-arm torso clearance '+stage)
 commit=helper.publish(repo,stage,protected)
 for p,f in items.items():
  blob=helper.git(repo,'show','refs/remotes/origin/main:'+p).stdout
  if p.endswith('.glb'):
   require('oid sha256:'+sha(f) in blob,'REMOTE_GIT_LFS_SHA_MISMATCH_'+p)
  else:require(blob==f.read_text(),'REMOTE_TEXT_READBACK_MISMATCH_'+p)
 require(not helper.g(repo,'status','--porcelain'),'PUBLISHED_WORKTREE_DIRTY')
 return commit

def patch_viewer(original):
 out=original
 patches=(
 ('42-clip full-attack grip IK v2.0.33','43-clip palm grip and arm clearance v2.0.35'),
 ('42-clip sustained lance grip IK','43-clip palm grip and right-arm clearance'),
 ('42 clips · sustained IK variant','43 clips · refined palm + right arm'),
 ('Original 41 clips · before grip variant','Original 42 clips · before refinement'),
 ("mode==='candidate'?['Vanguard_SwordAttack1_TwoHand_GripIK','Vanguard_SwordAttack1'",
  "mode==='candidate'?['Vanguard_SwordAttack1_TwoHand_PalmIK_Clearance','Vanguard_SwordAttack1_TwoHand_GripIK','Vanguard_SwordAttack1'"),
 ("mode==='before'?['Vanguard_SwordAttack1','Lionheart_Light1'",
  "mode==='before'?['Vanguard_SwordAttack1_TwoHand_GripIK','Vanguard_SwordAttack1','Lionheart_Light1'"),
 )
 for old,new in patches:
  require(out.count(old)==1,'VIEWER_PATCH_ANCHOR_'+str(out.count(old))+'_'+old[:45])
  out=out.replace(old,new,1)
 start=out.index('<p id="note">');end=out.index('</p>',start)+4
 out=out[:start]+('<p id="note">43 clips, all previous 42 animations byte-preserved. Refined SwordAttack1 keeps the original 0.23-second opening and shield charm, uses finger-base-measured palm contact IK for the full attack, and redirects the right elbow away from a torso proxy. Right-hand counter-rotation preserves the original lance world-space angle, but the lance may shift in position. The full original variant remains selectable. Contact and lance-angle measurements are shown as advisory evidence, not a claim of exact physical contact or collision-free mesh. Original 42-clip baseline remains available. Owner acceptance pending.</p>')+out[end:]
 require('43-clip' in out and 'Vanguard_SwordAttack1_TwoHand_PalmIK_Clearance' in out,'VIEWER_PATCH_POSTCONDITION')
 return out

def patch_server(original):
 old='ObsidiantiSustainedGripIK/2.0.33'
 require(original.count(old)==1,'SERVER_PATCH_ANCHOR_INVALID')
 return original.replace(old,'ObsidiantiPalmGripIK/2.0.35')

def check_mids(core,fix,old,new,report):
 jo,bo=core.read_glb(old);jn,bn=core.read_glb(new)
 a0=jo['animations'][-1];a1=jn['animations'][-1]
 ids=core.name_ids(jn);pa=core.parents(jn)
 basepose=fix.snapshot(jo,bo,a0,0.,core)
 palm,_=fix.palm_local_offset(basepose,ids,pa,core)
 # Test actual sampler intervals, not an unrelated uniformly spaced grid.
 ts=[x[0] for x in core.raw_accessor(jn,bn,a1['samplers'][0]['input'])]
 require(len(ts)>=3 and abs(ts[0])<.00001 and all(t2>t1 for t1,t2 in zip(ts,ts[1:])),
         'INVALID_ANIMATION_SAMPLE_TIMES')
 worst_p=(0.,0.);worst_a=(0.,0.);refine=[];checks=0;bad=0
 for t0,t1 in zip(ts,ts[1:]):
  if t1<=fix.LEAD:continue
  at=[]
  for f in (.25,.5,.75):
   t=t0+(t1-t0)*f
   if t<fix.LEAD:continue
   p=fix.snapshot(jn,bn,a1,t,core)
   oldpose=fix.snapshot(jo,bo,a0,t,core)
   r0=fix.world(ids[fix.WEAPON],oldpose,pa,core)[1]
   rp,rq,_=fix.world(ids[fix.WEAPON],p,pa,core)
   wp,wq,_=fix.world(ids[fix.LEFT[2]],p,pa,core)
   palmpos=fix.add(wp,fix.rotate(core,wq,palm))
   target=fix.add(rp,fix.rotate(core,rq,fix.GRIP_LOCAL))
   ep=fix.length(fix.sub(palmpos,target));ea=core.qdeg(r0,rq)
   worst_p=max(worst_p,(ep,t));worst_a=max(worst_a,(ea,t));checks+=1
   # These values are refinement triggers, not falsified pass tolerances.
   if ep>.007 or ea>.65:at.append(t)
  if at:
   bad+=1
   # Refine this interval smoothly, never duplicate an existing timestamp.
   refine.extend((t0+(t1-t0)*f for f in (.25,.5,.75)))
 return {'halfFrameSamples':checks,'maxPalmErrorM':worst_p[0],
         'maxPalmErrorTimeS':worst_p[1],
         'maxLanceAngleErrorDeg':worst_a[0],
         'maxLanceAngleTimeS':worst_a[1],
         'badIntervals':bad,'_refineTimes':sorted(set(refine))}

def main(packet,launcher,expected):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 require(launcher.is_file() and sha(launcher)==expected,'LAUNCHER_SHA_INVALID')
 manifest=json.loads((packet/'manifest.json').read_text())
 require(set(manifest)=={'driver.py','fix.py','test.py','contract.json'},'PAYLOAD_ALLOWLIST_CHANGED')
 require(all(sha(packet/p)==dig for p,dig in manifest.items()),'PAYLOAD_CHECKSUM_INVALID')
 contract=json.loads((packet/'contract.json').read_text())
 require(contract['schema']==V and contract['authority']=='TERMUX_GIT_ONLY' and contract['pinnedGitBase']==BASE
         and contract['input42SHA256']==SOURCE and contract['canonicalSHA256']==CANON,'CONTRACT_IDENTITY_CHANGED')
 require(set(contract['sourceMutablePaths'])==set(FILES),'WRITE_SCOPE_DRIFT')
 for path in ('driver.py','fix.py','test.py'):compile((packet/path).read_bytes(),path,'exec')
 downloads=pathlib.Path.home()/'storage/downloads'
 require(downloads.is_dir(),'ANDROID_DOWNLOADS_UNAVAILABLE')
 root=pathlib.Path.home()/'.local/state'/V/'working';root.mkdir(parents=True,exist_ok=True)
 receipt=root/'RECEIPT.json'
 if receipt.is_file():
  state=json.loads(receipt.read_text())
  require(state.get('schema')==V and state.get('launcherSHA256')==expected,'RESUME_DIFFERENT_LAUNCHER_FORBIDDEN')
 else:
  state={'schema':V,'runId':datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8],
         'authority':'TERMUX_GIT_ONLY','launcherSHA256':expected,'canonicalSHA256':CANON,
         'source42SHA256':SOURCE,'rulesBlob':AGENTS,'campaignEtiquette':'LIVE_CAMPAIGN_ETIQUETTE_READ_AT_AUTHORING',
         'ownerVisualAcceptance':'PENDING','canonicalModified':False,'prior42Modified':False,'status':'BOOT'}
  save(receipt,state)
 def stage(x):state['stage']=x;save(receipt,state);print('STAGE='+x,flush=True)
 try:
  stage('ISOLATED_TERMUX_GIT_AND_LATEST_SOURCE_VERIFY')
  cr=root/'checkout';repo=cr/'repo'
  # Load pinned helper from a harmless TEMP file if no checkout exists yet.
  if not repo.is_dir():
   cr.mkdir(parents=True,exist_ok=True)
   p=subprocess.run(['git','clone','--quiet','--depth=1','--single-branch','--branch','main','https://github.com/Valar05/parametric-parambulator.git',str(repo)],
          env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0'),stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=1200)
   require(p.returncode==0,'ISOLATED_GIT_CLONE_FAILED_'+p.stderr[-450:])
  helper=module(repo/OLDHELPER,'obs_v34_pinned_git');helper.BASE=BASE
  require(helper.AGENTS==AGENTS and helper.CANON==CANON and helper.REMOTE.endswith('Valar05/parametric-parambulator.git'),'PINNED_GIT_HELPER_IDENTITY_CHANGED')
  require(helper.g(repo,'rev-parse','HEAD:'+OLDHELPER)==HELPER_BLOB,'GIT_HELPER_BLOB_CHANGED')
  require(helper.g(repo,'rev-parse','HEAD:'+CORE)==CORE_BLOB,'GLTF_ACCESSOR_BLOB_CHANGED')
  require(helper.g(repo,'rev-parse','HEAD:'+OLDVIEW)==VIEW_BLOB,'VIEWER_DONOR_BLOB_CHANGED')
  require(helper.g(repo,'rev-parse','HEAD:'+OLDSERVER)==SERVER_BLOB,'SERVER_DONOR_BLOB_CHANGED')
  require(helper.g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'AGENTS_POLICY_BLOB_CHANGED')
  head=helper.g(repo,'rev-parse','HEAD');helper.verify_pinned_ancestry(repo,BASE,head)
  for path,dig in ((SOURCE_PATH,SOURCE),(CANON_PATH,CANON)):
   require('oid sha256:'+dig in helper.git(repo,'show','HEAD:'+path).stdout,'LFS_INPUT_POINTER_CHANGED_'+path)
  protected={p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED};state['protectedBefore']=protected;state['inputGitHead']=head
  require(not helper.g(repo,'status','--porcelain'),'DIRTY_ISOLATED_REPO_BEFORE_BOOT')
  stage('BUILD_VERSIONED_VIEWER_AND_SERVER_FROM_PINNED_SOURCES')
  vpath=root/'viewer.html';spath=root/'server.py'
  viewer=patch_viewer((repo/OLDVIEW).read_text());server=patch_server((repo/OLDSERVER).read_text())
  if vpath.exists():require(vpath.read_text()==viewer,'VIEWER_GENERATION_DRIFT')
  else:vpath.write_text(viewer)
  if spath.exists():require(spath.read_text()==server,'SERVER_GENERATION_DRIFT')
  else:spath.write_text(server)
  src={dest:(launcher if name=='LAUNCHER' else vpath if name=='GENERATED_VIEWER' else spath if name=='GENERATED_SERVER' else packet/name)
       for dest,name in FILES.items()}
  stage('PUBLISH_VERSIONED_SOURCE_TERMUX_GIT_REMOTE_READBACK')
  sourcecommit=publish(helper,repo,src,'SOURCE',protected)
  state['sourceCommit']=state.get('sourceCommit',sourcecommit)
  stage('HYDRATE_EXACT_42_CLIP_BINARY_FROM_GIT_LFS')
  helper.hydrate(repo,{SOURCE_PATH:SOURCE});real=repo/SOURCE_PATH
  require(sha(real)==SOURCE,'SOURCE_GLTF_ACTUAL_SHA_DRIFT')
  core=module(repo/CORE,'obs_v34_glb_core');fix=module(packet/'fix.py','obs_v34_fix')
  stage('REAL_RIG_REPAIR_PRETEST_AND_NEGATIVE_TESTS')
  p=subprocess.run([sys.executable,str(packet/'test.py'),str(real),str(repo/CORE)],stdin=subprocess.DEVNULL,
       capture_output=True,text=True,cwd=packet,timeout=450,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  require(p.returncode==0,'ACTUAL_RIG_PRETEST_FAILED_'+p.stdout[-1200:]+p.stderr[-1600:])
  print(p.stdout.strip(),flush=True);state['realRigTests']=p.stdout.strip()
  stage('ADAPTIVE_REBAKE_CONTACT_AND_PUBLISH_REVIEW_WITH_WARNINGS')
  final=root/(V+'_'+state['runId']+'_43_CLIP_REVIEW.glb');proof=root/'PALM_CLEARANCE_PROOF.json'
  if final.is_file() and proof.is_file():
   data=json.loads(proof.read_text());require(sha(final)==data['outputSHA256'],'RESUMED_MODEL_SHA_MISMATCH')
  else:
   require(not final.exists() and not proof.exists(),'PARTIAL_EXISTING_OUTPUT_AMBIGUOUS')
   trials=[];chosen=None;strict_pass=False
   # Start at 120fps with exact prep boundary; refine only intervals with contact/angle drift.
   grid=None
   for attempt in range(4):
    fix.FPS=120;fix.CUSTOM_TIMES=grid
    tag='ADAPT_'+str(attempt)
    path=root/('TRIAL_'+tag+'.glb');report=root/('TRIAL_'+tag+'.json')
    if path.is_file() and report.is_file():
     item=json.loads(report.read_text());require(sha(path)==item['outputSHA256'],'TRIAL_RESUME_SHA_INVALID')
    else:
     require(not path.exists() and not report.exists(),'TRIAL_PARTIAL_COLLISION_'+tag)
     item=fix.run(real,path,report,core,None)
    mid=check_mids(core,fix,real,path,item)
    flagged=mid.pop('_refineTimes');metrics={'attempt':attempt,'fps':120,
      'keyCount':item['frames'],'sha256':sha(path),**mid}
    trials.append(metrics)
    print('PALM_AND_LANCE_AUDIT ATTEMPT='+str(attempt)+' KEYS='+str(item['frames'])+
          ' PALM_MAX_M='+str(mid['maxPalmErrorM'])+' LANCE_ANGLE_MAX_DEG='+str(mid['maxLanceAngleErrorDeg']),flush=True)
    # Preserve the best objectively measured result for advisory visual review.
    score=2.0*mid['maxPalmErrorM']/.012+mid['maxLanceAngleErrorDeg']/1.5
    if chosen is None or score<chosen[3]:chosen=(path,item,mid,score)
    # Original strict v34 thresholds remain unchanged and separately reported.
    if mid['maxPalmErrorM']<=.012 and mid['maxLanceAngleErrorDeg']<=.11:
     strict_pass=True;break
    if not flagged or item['frames']>650:break
    js,dat=core.read_glb(path);clip=js['animations'][-1]
    ts=[x[0] for x in core.raw_accessor(js,dat,clip['samplers'][0]['input'])]
    grid=sorted(set(round(float(t),10) for t in [*ts,*flagged]))
    if len(grid)<=len(ts) or len(grid)>850:break
   require(chosen is not None,'NO_PRODUCED_CANDIDATE_FROM_REAL_SOURCE')
   chosenfile,data,mid,_=chosen;helper.copy_new(chosenfile,final)
   data={**data,'outputSHA256':sha(final),'halfFrameVerification':mid,
         'allTrialVerification':trials,'strictMidframeGatePassed':strict_pass,
         'qualityState':('STRICT_MIDFRAME_PASS' if strict_pass else
          'ADVISORY_FAILED_MIDFRAME_METRICS__REVIEW_ONLY')}
   save(proof,data)
  require(data['outputCount']==43 and data['maxPalmContactErrorM']<=.00015 and data['maxWeaponRotationErrorDeg']<=.03,
          'BAKED_RESULT_DID_NOT_PASS_SOURCE_KINEMATICS')
  new,dat=core.read_glb(final);old,oldbin=core.read_glb(real)
  require(len(new['animations'])==43 and new['animations'][:42]==old['animations'] and dat.startswith(oldbin),'ORIGINAL_42_SAMPLERS_NOT_BYTE_PRESERVED')
  for k in ('nodes','meshes','skins','materials','textures','images','scenes'):
   require(new.get(k)==old.get(k),'ORIGINAL_GEOMETRY_OR_SHIELD_MODIFIED_'+k)
  candidate=downloads/final.name;helper.copy_new(final,candidate)
  require(sha(candidate)==data['outputSHA256'],'ANDROID_DOWNLOADS_PREVIEW_HASH_MISMATCH')
  state.update({'outputSHA256':sha(candidate),'outputDownload':str(candidate),'clipCount':43})
  stage('START_SHA_IDENTIFIED_THREEJS_BEFORE_AFTER_VIEWER')
  models={'candidate':candidate,'before':real}
  meta={k:{'sha256':sha(path),'bytes':path.stat().st_size,'url':'/models/'+k+'.glb',
           'animations':[a['name'] for a in (new if k=='candidate' else old)['animations']]}
        for k,path in models.items()}
  token=hashlib.sha256((state['runId']+state['sourceCommit']+expected+sha(candidate)).encode()).hexdigest()[:24]
  identity={'schema':V,'runId':state['runId'],'sourceCommit':state['sourceCommit'],'buildToken':token,
            'launcherSHA256':expected,'htmlPath':str(repo/(SC+'_viewer.html')),'models':meta,
            'modelPaths':{k:str(p) for k,p in models.items()},'canonicalModelSHA256':CANON,
            'mode':'THREEJS_LANCE_PALM_CONTACT_RIGHT_ARM_CLEARANCE_43_CLIP_REVIEW'}
  oldview=module(repo/'campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py','obs_v34_viewer_transport')
  oldview.V=V
  ticket=oldview.start_server(root,repo,identity)
  state.update({'viewerURL':ticket['url'],'serverPort':ticket['port'],'serverPID':ticket['pid'],'viewerHTTPVerified':True})
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(oldview.open_browser(ticket['url'])).upper(),flush=True)
  stage('PUBLISH_VERSIONED_43_CLIP_REVIEW_GIT_LFS')
  prefix=REL+state['runId']+'/'
  glbpath=prefix+'OBSIDIANTI_SWORD1_PALM_CLEARANCE_43_CLIP_UNAPPROVED.glb'
  require(helper.g(repo,'check-attr','filter','--',glbpath).endswith('lfs'),'REVIEW_BINARY_NOT_GIT_LFS_TRACKED')
  require({p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED}==protected,'PROTECTED_MODEL_MUTATION_DETECTED')
  evidence={'schema':V,'authority':'TERMUX_GIT_ONLY','status':'REVIEW_UNAPPROVED_NOT_PHYSICAL_ACCEPTANCE','input42SHA256':SOURCE,
    'resultSHA256':sha(candidate),'canonicalSHA256':CANON,'rulesBlob':AGENTS,'sourceCommit':state['sourceCommit'],
    'inputGitHead':head,'runId':state['runId'],'clipCount':43,'original42Preserved':True,
    'ownerVisualAcceptance':'PENDING','canonicalModified':False,'viewerURL':ticket['url'],
    'halfFrame':data['halfFrameVerification'],'palmAndCollision':{k:v for k,v in data.items() if k not in ('samples','allTrialVerification')},
    'qualityState':data['qualityState'],'numericMidframeStrictPass':data['strictMidframeGatePassed'],
    'protectedBefore':protected,'protectedAfter':{p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED}}
  ev=root/'EVIDENCE.json';save(ev,evidence)
  report=root/'REPORT.md';report.write_text('# SwordAttack1 palm contact + right-arm clearance v2.0.34\n\n'
    '**OWNER VISUAL APPROVAL PENDING.** Original 42 clips and canonical intact.\n\n'
    'New variant: `'+fix.VARIANT+'`. Preserves 0.23 sec lead and miniature shield.\n'
    'Palm anchor from actual left finger-base bones; right elbow collision proxy optimized against torso, '
    'right hand counter-rotated to preserve lance direction; spear position allowed to move.\n\n'
    'Skinned mesh penetration is **not yet proven absent** by torso proxy checks; owner visual review required.\n\n'
    'Original source v2.0.33 GLB SHA-256 `'+SOURCE+'`. New SHA `'+sha(candidate)+'`.\n\n'
    'Numeric midframe strict pass: '+str(data['strictMidframeGatePassed'])+'; this candidate is REVIEW ONLY.\n'
    'Half frame grip error max '+str(data['halfFrameVerification']['maxPalmErrorM'])+' m. '
    'World lance orientation error max '+str(data['halfFrameVerification']['maxLanceAngleErrorDeg'])+' degrees.\n\n'
    'Torso proxy penetration mean before='+str(data['averagePenetrationBefore'])+
    ' after='+str(data['averagePenetrationAfter'])+'.\n\n'
    'Viewer: '+ticket['url']+'\n')
  items={prefix+'REPORT.md':report,prefix+'PALM_CLEARANCE_PROOF.json':proof,prefix+'EVIDENCE.json':ev,glbpath:candidate}
  commit=publish(helper,repo,items,'EVIDENCE',protected)
  state.update({'evidenceCommit':commit,'numericMidframeStrictPass':data['strictMidframeGatePassed'],'qualityState':data['qualityState'],
                'status':('43_CLIP_NUMERIC_PASS_REVIEW_PENDING' if data['strictMidframeGatePassed']
                 else '43_CLIP_NUMERIC_WARNINGS_VIEWABLE_REVIEW_PENDING')})
  stage('REMOTE_GIT_LFS_AND_VIEWER_SHA_READBACK_COMPLETE')
  print('RESULT_GLB='+str(candidate),flush=True)
  print('RESULT_SHA256='+sha(candidate),flush=True)
  print('SOURCE_GIT_COMMIT='+state['sourceCommit'],flush=True)
  print('EVIDENCE_GIT_COMMIT='+commit,flush=True)
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('CANONICAL_AND_FIRST_42_CLIPS_UNCHANGED=YES',flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as err:
  state.update({'status':'BLOCKED','error':str(err)[:1700],'traceback':traceback.format_exc()[-2800:]})
  print('STATUS=BLOCKED '+state['error'],flush=True)
  raise
 finally:save(receipt,state);print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('usage driver.py PACKET LAUNCHER EXPECTED_ENTRY_SHA256')
 main(sys.argv[1],sys.argv[2],sys.argv[3])
