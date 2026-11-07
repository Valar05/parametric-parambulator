#!/usr/bin/env python3
"""Owner-authorized single Termux Git campaign for a SwordAttack1 sustained two-hand IK variant.
Only new versioned campaign+review artifacts; canonical and all 41 original animation clips immutable.
"""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,time,traceback,uuid
sys.dont_write_bytecode=True
V='OBSIDIANTI_SWORD1_SUSTAINED_IK_v2.0.33'
BASE='dbaf788e7ec30e659920c9a02a5ab6a49d5e388a'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
B41='9ff2b5423b4bf5fea1bf67295b52d848803381699fede56164aca9ce65bea9b7'
B41_PATH='diagnostics/obsidianti/animation-reunion-v2.0.32/runs/20261107T203838Z-d49615bb/OBSIDIANTI_41_CLIP_SHIELD_LANCE_LIONHEART_ARP_REVIEW_UNAPPROVED.glb'
CANON_PATH='assets/obsidianti/Obsidianti.glb'
PRIOR='campaigns/OBSIDIANTI_ANIMATION_REUNION_v2.0.31_compose.py'
PRIOR_BLOB='3203b3b0b18bdbcb247541cdac3e9d7167a50558'
OLDHELPER_BLOB='610970b4acc11033b1345a508aa2c6c38f0e2adc'
PROTECTED=(CANON_PATH,B41_PATH,'assets/repl/Repl.glb',
 'diagnostics/obsidianti/vanguard-rigify-arp-v2.0.17/runs/20261107T044021Z-81e43a05/OBSIDIANTI_VANGUARD_ARP_EXPERIMENT_UNAPPROVED.glb',
 'diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/20261107T021037Z-2edec0d5/AxeKick/ARP_AxeKick_REVIEW.glb')
SC='campaigns/'+V
FILES={SC+'_LAUNCH.sh':'LAUNCHER',SC+'_driver.py':'driver.py',SC+'_bake.py':'bake.py',
       SC+'_viewer.html':'viewer.html',SC+'_server.py':'server.py',SC+'.contract.json':'contract.json',
       'tests/'+V+'_TEST.py':'test_bake.py'}
REL='diagnostics/obsidianti/sword1-sustained-ik-v2.0.33/runs/'

def require(x,msg):
 if not x:raise RuntimeError(msg)
def sha(f):
 d=hashlib.sha256()
 with open(f,'rb') as b:
  for x in iter(lambda:b.read(1<<20),b''):d.update(x)
 return d.hexdigest()
def save(p,obj):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_name('.'+p.name+'.'+uuid.uuid4().hex[:8]+'.tmp');t.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');os.replace(t,p)
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 require(spec and spec.loader,'PINNED_PYTHON_DEPENDENCY_UNAVAILABLE_'+name)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def commit_unique(h,repo,paths,label,protected):
 exists=[p for p in paths if (repo/p).exists()]
 if exists:
  require(len(exists)==len(paths) and all((repo/p).is_file() and sha(repo/p)==sha(src) for p,src in paths.items()),'VERSIONED_PATH_COLLISION_'+label)
  require(not h.g(repo,'status','--porcelain'),'REUSED_VERSIONED_PATHS_DIRTY')
  return h.g(repo,'rev-parse','HEAD')
 require(not h.g(repo,'status','--porcelain'),'DIRTY_ISOLATED_CHECKOUT_BEFORE_'+label)
 for p,s in paths.items():h.copy_new(s,repo/p)
 h.git(repo,'add','--',*sorted(paths))
 staged=set(h.g(repo,'diff','--cached','--name-only').splitlines())
 require(staged==set(paths),'SOURCE_OR_OUTPUT_STAGE_ALLOWLIST_FAILURE')
 if not h.git(repo,'config','user.name',check=False).stdout.strip():h.git(repo,'config','user.name','Termux Obsidianti Sword1 IK')
 if not h.git(repo,'config','user.email',check=False).stdout.strip():h.git(repo,'config','user.email','termux-obsidianti-ik@users.noreply.github.com')
 h.git(repo,'commit','-m','Obsidianti SwordAttack1 sustained offhand lance IK '+label)
 committed=h.publish(repo,label,protected)
 for path,original in paths.items():
  shown=h.git(repo,'show','refs/remotes/origin/main:'+path).stdout
  if path.endswith('.glb'):
   require('oid sha256:'+sha(original) in shown,'GLB_LFS_REMOTE_READBACK_FAILED_'+path)
  else:require(shown==original.read_text(),'TEXT_REMOTE_READBACK_FAILED_'+path)
 require(not h.g(repo,'status','--porcelain'),'POST_COMMIT_DIRTY_CHECKOUT')
 return committed

def contact_measure(path,core,fix):
 js,dat=core.read_glb(path);act=next(x for x in js['animations'] if x['name']==fix.VARIANT)
 ids=core.name_ids(js);pa=core.parents(js)
 start,end=core.range_times(js,dat,act);errors=[]
 # Sample all keyframes and their midpoints in the attack, including the last frame.
 n=max(40,round((end-fix.LEAD)*fix.FPS*2))
 for k in range(n+1):
  t=fix.LEAD+(end-fix.LEAD)*k/n
  pose=fix.all_trs(js,dat,act,t,core)
  a=fix.world(ids['mixamorig:LeftHand'],pose,pa,core,{})[0]
  b,q,_=fix.world(ids['mixamorig:RightWeapon.R'],pose,pa,core,{})
  target=fix.plus(b,fix.quat_rotate(core,q,fix.GRIP_LOCAL))
  errors.append(fix.norm(fix.minus(a,target)))
 return {'maxContactErrorM':max(errors),'meanContactErrorM':sum(errors)/len(errors),
         'framesAndMidframes':len(errors),'attackFromSeconds':fix.LEAD,'attackUntilSeconds':end}

def main(packet,launcher,expected):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 require(launcher.is_file() and sha(launcher)==expected,'SHA_VERIFIED_LAUNCHER_CHANGED')
 mf=json.loads((packet/'manifest.json').read_text());required={'driver.py','bake.py','viewer.html','server.py','test_bake.py','contract.json','v22_helpers.py'}
 require(set(mf)==required and all(sha(packet/n)==v for n,v in mf.items()),'EMBEDDED_PAYLOAD_TAMPERED')
 c=json.loads((packet/'contract.json').read_text())
 require(c['schema']==V and c['authority']=='TERMUX_GIT_ONLY' and c['pinnedGitBase']==BASE and c['input41SHA256']==B41 and c['canonicalSHA256']==CANON,'CAMPAIGN_IDENTITY_CONTRACT_DRIFT')
 require(set(c['sourceMutablePaths'])==set(FILES),'VERSIONED_WRITE_SCOPE_CHANGED')
 for n in ('driver.py','bake.py','server.py','test_bake.py'):compile((packet/n).read_bytes(),n,'exec')
 hb=(packet/'v22_helpers.py').read_bytes(); blob=hashlib.sha1(b'blob '+str(len(hb)).encode()+b'\0'+hb).hexdigest()
 require(blob==OLDHELPER_BLOB,'PINNED_GIT_HELPER_CHANGED')
 downloads=pathlib.Path.home()/'storage/downloads';require(downloads.is_dir(),'ANDROID_DOWNLOADS_UNAVAILABLE')
 root=pathlib.Path.home()/'.local/state'/V/'working';root.mkdir(parents=True,exist_ok=True)
 receipt=root/'RECEIPT.json'
 if receipt.exists():
  state=json.loads(receipt.read_text());require(state.get('schema')==V and state.get('launcherSHA256')==expected,'SCRIPT_RESUME_IDENTITY_MISMATCH')
 else:
  state={'schema':V,'runId':datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8],
         'status':'BOOT','authority':'TERMUX_GIT_ONLY','launcherSHA256':expected,'rulesBlob':AGENTS,
         'campaignEtiquette':'LIVE_READ_IN_AUTHORING_TURN','canonicalSHA256':CANON,
         'input41SHA256':B41,'ownerVisualAcceptance':'PENDING','canonicalModified':False,'original41Modified':False}
  save(receipt,state)
 def stage(label):state['stage']=label;save(receipt,state);print('STAGE='+label,flush=True)
 h=module(packet/'v22_helpers.py','sword33_pinned_git');h.BASE=BASE
 try:
  stage('BOOT_ISOLATED_TERMUX_GIT_AND_ORIGINAL_ASSET_LOCKS')
  cr=root/'checkout';repo=cr/'repo'
  if repo.is_dir():
   require(h.g(repo,'rev-parse','--show-toplevel')==str(repo),'ISOLATED_CHECKOUT_WRONG_ROOT')
   require(not h.g(repo,'status','--porcelain'),'ISOLATED_CHECKOUT_DIRTY')
   head=h.g(repo,'rev-parse','HEAD');h.verify_pinned_ancestry(repo,BASE,head)
  else:
   cr.mkdir(parents=True,exist_ok=True);repo,head,_=h.checkout(cr)
  require(h.g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'AGENTS_READ_GATE_DRIFT')
  require(h.g(repo,'rev-parse','HEAD:'+PRIOR)==PRIOR_BLOB,'V231_COMPOSER_PIN_CHANGED')
  for path,s in ((CANON_PATH,CANON),(B41_PATH,B41)):
   require('oid sha256:'+s in h.git(repo,'show','HEAD:'+path).stdout,'SOURCE_LFS_POINTER_DRIFT_'+path)
  protected={p:h.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED};state['protectedBefore']=protected;state['inputGitHead']=head
  stage('PRECHECK_SOURCE_DESTINATIONS_AND_COMMIT_VERSIONED_CAMPAIGN')
  sources={p:(launcher if n=='LAUNCHER' else packet/n) for p,n in FILES.items()}
  commit=commit_unique(h,repo,sources,'SOURCE',protected)
  state['sourceCommit']=state.get('sourceCommit',commit)
  stage('HYDRATE_REAL_OWNER_REVIEW_41_CLIP_GLTF')
  h.hydrate(repo,{B41_PATH:B41})
  prev=repo/B41_PATH;require(sha(prev)==B41,'REAL_41_CLIP_SOURCE_SHA_NOT_VERIFIED')
  core=module(repo/PRIOR,'sword33_pinned_glb_accessor')
  fix=module(packet/'bake.py','sword33_bake')
  stage('REAL_RIG_IK_AND_NEGATIVE_CASE_SELFTEST')
  cmd=[sys.executable,str(packet/'test_bake.py'),str(prev),str(repo/PRIOR)]
  test=subprocess.run(cmd,capture_output=True,text=True,timeout=420,stdin=subprocess.DEVNULL,cwd=packet,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  require(test.returncode==0,'REAL_RIG_SYNTHETIC_IK_SELFTEST_FAILED_'+test.stdout[-800:]+test.stderr[-1200:])
  state['realRigSyntheticTest']=test.stdout.strip();print(test.stdout.strip(),flush=True)
  stage('BAKE_FULL_CLIP_LEFT_HAND_LANCE_FOLLOW_AND_SHIELD_CHARM')
  name=V+'_'+state['runId']+'_42_CLIP_REVIEW.glb'
  final=root/name;proof=root/'SUSTAINED_IK_PROOF.json'
  if final.is_file() and proof.is_file():
   data=json.loads(proof.read_text());require(data.get('outputSHA256')==sha(final),'RESUME_42_CLIP_BINARY_HASH_FAILED')
  else:
   require(not final.exists() and not proof.exists(),'PARTIAL_IK_BAKE_REQUIRES_RECOVERY')
   # Bounded adaptive sample-density checks, each trial path uniquely named.
   trials=[];chosen=None
   for fps in (90,180,270):
    fix.FPS=fps
    trial=root/('TRIAL_'+str(fps)+'.glb');pr=root/('TRIAL_'+str(fps)+'.json')
    if trial.is_file() and pr.is_file():
     result=json.loads(pr.read_text());require(result['outputSHA256']==sha(trial),'TRIAL_CHECKPOINT_SHA_DRIFT')
    else:
     require(not trial.exists() and not pr.exists(),'PARTIAL_TRIAL_FILES_COLLISION_'+str(fps))
     result=fix.bake(prev,trial,pr,core)
    measurement=contact_measure(trial,core,fix)
    trials.append({'bakeFPS':fps,'sourceSha':sha(prev),**measurement})
    print('IK_FULL_ATTACK_CONTACT_FPS='+str(fps)+' MAX_ERROR_M='+str(measurement['maxContactErrorM']),flush=True)
    if measurement['maxContactErrorM']<=.012:
     chosen=(trial,result,measurement);break
   require(chosen is not None,'FULL_ATTACK_IK_CONTACT_NOT_SUFFICIENT_'+json.dumps(trials))
   src,result,measurement=chosen
   h.copy_new(src,final)
   data={**result,'bakedFrameAndMidframeAudit':measurement,'allTrialAudits':trials,'outputSHA256':sha(final),'outputBytes':final.stat().st_size}
   save(proof,data)
  require(data['outputSHA256']==sha(final) and data['outputClipCount']==42 and data['maxGripErrorAfterPrepM']<.0001,'OUTPUT_IK_OR_GLTF_INTEGRITY_GATE_FAILED')
  glb,_=core.read_glb(final)
  origin,_=core.read_glb(prev)
  require(len(glb['animations'])==42 and glb['animations'][:41]==origin['animations'],'ALL_41_ORIGINAL_SAMPLERS_NOT_PRESERVED')
  candidate=downloads/name;h.copy_new(final,candidate)
  require(sha(candidate)==data['outputSHA256'],'ANDROID_DOWNLOADS_PREVIEW_HASH_CHANGED')
  state.update({'candidateSHA256':sha(candidate),'candidateDownload':str(candidate),'maxGripErrorM':data['bakedFrameAndMidframeAudit']['maxContactErrorM'],'maxStretchFactor':data['maxStretchFactor']})
  stage('SERVE_SHA_VERIFIED_THREEJS_SIDE_BY_SIDE_REVIEW')
  orig_names=[x['name'] for x in origin['animations']]
  models={'candidate':candidate,'before':prev}
  meta={n:{'sha256':sha(p),'bytes':p.stat().st_size,'url':'/models/'+n+'.glb',
            'animations':[x['name'] for x in (glb if n=='candidate' else origin)['animations']]} for n,p in models.items()}
  token=hashlib.sha256((state['runId']+state['sourceCommit']+expected+sha(candidate)).encode()).hexdigest()[:24]
  manifest={'schema':V,'runId':state['runId'],'sourceCommit':state['sourceCommit'],'buildToken':token,'launcherSHA256':expected,
     'htmlPath':str(repo/(SC+'_viewer.html')),'models':meta,'modelPaths':{n:str(p) for n,p in models.items()},
     'canonicalModelSHA256':CANON,'variantMetrics':{'leadSeconds':fix.LEAD,'maxStretchFactor':data['maxStretchFactor'],
          'maxMidframeGripErrorM':data['bakedFrameAndMidframeAudit']['maxContactErrorM']},
     'mode':'THREE_JS_ONE_AND_TWO_HANDED_VARIANT_REVIEW_BAKED_SUSTAINED_LANCE_IK'}
  oldviewer=module(repo/'campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py','sword33_verified_viewer')
  oldviewer.V=V
  ticket=oldviewer.start_server(root,repo,manifest)
  state.update({'viewerURL':ticket['url'],'serverPID':ticket['pid'],'serverPort':ticket['port'],'viewerHTTPVerified':True})
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(oldviewer.open_browser(ticket['url'])).upper(),flush=True)
  stage('PUBLISH_ONLY_VERSIONED_RESULT_IN_GIT_LFS')
  dest=REL+state['runId']+'/'
  binarypath=dest+'OBSIDIANTI_SWORD1_SUSTAINED_IK_42_CLIP_REVIEW_UNAPPROVED.glb'
  require(h.g(repo,'check-attr','filter','--',binarypath).endswith('lfs'),'NEW_BINARY_NOT_LFS_TRACKED')
  protectedafter={p:h.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED}
  require(protectedafter==protected,'ORIGINAL_RIG_LIBRARY_CHANGED')
  ev={'schema':V,'authority':'TERMUX_GIT_ONLY','status':'REVIEW_UNAPPROVED','rulesBlob':AGENTS,'canonicalSHA256':CANON,
      'base41SHA256':B41,'resultSHA256':sha(candidate),'sourceCommit':state['sourceCommit'],'inputGitHead':head,
      'runId':state['runId'],'animationCount':42,'fullAttackIK':True,'original41PreservedExact':True,
      'shieldOriginalMeshPreserved':True,'maxGripErrorMidframeM':data['bakedFrameAndMidframeAudit']['maxContactErrorM'],
      'maxArmStretchFactor':data['maxStretchFactor'],'newVariant':fix.VARIANT,'viewerURL':ticket['url'],
      'canonicalModified':False,'ownerVisualAcceptance':'PENDING','protectedBefore':protected,'protectedAfter':protectedafter}
  evfile=root/'EVIDENCE.json';save(evfile,ev)
  report=root/'REPORT.md'
  report.write_text('# SwordAttack1 two-handed, sustained offhand IK and wrist charm v2.0.33\n\n'
    'Owner approval: **PENDING**. Canonical and all previous 41 animations preserved untouched.\n\n'
    'Appended only `'+fix.VARIANT+'`. Starts from the **first frame** of `'+fix.SPEAR+'`;'
    ' '+str(fix.LEAD)+' seconds of transitional hand reach and shield shrink/rotation before the unchanged original Vanguard sword attack plays.\n\n'
    'The left hand follows a point down the lance hilt (`RightWeapon.R` local '+str(fix.GRIP_LOCAL)+') with explicit 2-bone IK **for the full attack**.'
    ' Stretch is measured and adjusted across every sample.\n\n'
    'Maximum arm stretch factor: '+str(data['maxStretchFactor'])+'; maximal full-attack keyed grip error '+str(data['maxGripErrorAfterPrepM'])+' m;'
    ' sampled and half-frame error '+str(data['bakedFrameAndMidframeAudit']['maxContactErrorM'])+' m.\n\n'
    'The original left-wrist shield is rotated tip-to-elbow, scaled to 8% and positioned as a charm. Mesh, skin, weapon, and material are not edited.\n\n'
    'The entire first 41 clips and binary payload prefix are byte-for-byte preserved. This is a **new review GLB**, not a canonical model change.\n\n'
    'Viewer: '+ticket['url']+'\n\nOutput SHA-256: '+sha(candidate)+'\n')
  outputs={dest+'REPORT.md':report,dest+'SUSTAINED_IK_PROOF.json':proof,dest+'EVIDENCE.json':evfile,binarypath:candidate}
  evidence_commit=commit_unique(h,repo,outputs,'EVIDENCE',protected)
  state.update({'evidenceCommit':evidence_commit,'status':'REVIEW_PUBLISHED_OWNER_ACCEPTANCE_PENDING'})
  stage('GIT_REMOTE_ASSET_SHA_READBACK_COMPLETE')
  print('RESULT_GLB='+str(candidate),flush=True)
  print('RESULT_SHA256='+sha(candidate),flush=True)
  print('SOURCE_GIT_COMMIT='+state['sourceCommit'],flush=True)
  print('EVIDENCE_GIT_COMMIT='+evidence_commit,flush=True)
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('CANONICAL_AND_41_CLIPS_UNCHANGED=YES',flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as err:
  state.update({'status':'BLOCKED','errorType':type(err).__name__,'error':str(err)[:1800],'traceback':traceback.format_exc()[-2800:]})
  print('STATUS=BLOCKED '+state['error'],flush=True)
  raise
 finally:save(receipt,state);print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('usage: driver.py PACKET LAUNCHER EXPECTED_ENTRY_SHA256')
 main(sys.argv[1],sys.argv[2],sys.argv[3])
