#!/usr/bin/env python3
"""Obsidianti v2.0.39 one-invocation Termux Git and SHA-identified 44-clip viewer."""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,subprocess,sys,traceback,uuid
sys.dont_write_bytecode=True
V='OBSIDIANTI_SWORD1_PALM_CLEARANCE_v2.0.39'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
BASE='898051da60092002cb39137d0683fbff45118085'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
SOURCE='ed1f4f34f2f3a261e0c5096a39599980f20868223245455e2be554299d55a5a2'
SOURCE_PATH='diagnostics/obsidianti/sword1-palm-clearance-v2.0.36/runs/20261108T174847Z-8fc3d90a/OBSIDIANTI_SWORD1_PALM_CLEARANCE_43_CLIP_UNAPPROVED.glb'
CANON_PATH='assets/obsidianti/Obsidianti.glb'
OLDHELPER='campaigns/MUDMAN_ARES_FULL_RETARGET_v2.0.22_driver.py'
CORE='campaigns/OBSIDIANTI_ANIMATION_REUNION_v2.0.31_compose.py'
V236='campaigns/OBSIDIANTI_SWORD1_PALM_CLEARANCE_v2.0.36_driver.py'
OLDVIEW='campaigns/OBSIDIANTI_SWORD1_PALM_CLEARANCE_v2.0.36_viewer.html'
OLDSERVER='campaigns/OBSIDIANTI_SWORD1_PALM_CLEARANCE_v2.0.36_server.py'
SC='campaigns/'+V
FILES={SC+'_LAUNCH.sh':'LAUNCHER',SC+'_driver.py':'driver.py',SC+'_fix.py':'fix.py',
       SC+'_viewer.html':'GENERATED_VIEWER',SC+'_server.py':'GENERATED_SERVER',
       SC+'.contract.json':'contract.json','tests/'+V+'_TEST.py':'test.py'}
REL='diagnostics/obsidianti/sword1-palm-clearance-v2.0.39/runs/'
PROTECTED=(CANON_PATH,SOURCE_PATH,'assets/repl/Repl.glb',
 'diagnostics/obsidianti/sword1-sustained-ik-v2.0.33/runs/20261107T213143Z-f1187b82/OBSIDIANTI_SWORD1_SUSTAINED_IK_42_CLIP_REVIEW_UNAPPROVED.glb')

def require(x,msg):
 if not x:raise RuntimeError(msg)
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 require(spec and spec.loader,'MISSING_MODULE_'+name)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def save(path,value):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex[:8]+'.tmp')
 temp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');os.replace(temp,path)

def patch_viewer(original):
 require('Vanguard_SwordAttack1_TwoHand_PalmIK_Clearance' in original,'VIEWER_SOURCE_CLIP_MISSING')
 out=original.replace('43-clip palm grip and arm clearance v2.0.36','44-clip wrist polish and smooth shield v2.0.39')
 out=out.replace('43-clip palm grip and right-arm clearance','44-clip wrist polish and smooth shield')
 out=out.replace('43 clips · refined palm + right arm','44 clips · refined wrist + shield')
 out=out.replace('Original 42 clips · before refinement','Original 43 clips · before wrist polish')
 out=out.replace("mode==='candidate'?['Vanguard_SwordAttack1_TwoHand_PalmIK_Clearance'",
                 "mode==='candidate'?['Vanguard_SwordAttack1_TwoHand_PalmIK_WristShield_v239','Vanguard_SwordAttack1_TwoHand_PalmIK_Clearance'")
 out=out.replace("mode==='before'?['Vanguard_SwordAttack1_TwoHand_GripIK'",
                 "mode==='before'?['Vanguard_SwordAttack1_TwoHand_PalmIK_Clearance','Vanguard_SwordAttack1_TwoHand_GripIK'")
 start=out.index('<p id="note">');end=out.index('</p>',start)+4
 out=out[:start]+('<p id="note">44 clips. Original 43 clips are unchanged. New SwordAttack1 wrist orientation is anatomically guided by the finger-knuckle axis relative to the lance, with the left palm re-solved to the original shaft contact point; right-arm animation channels and pose-event times are carried forward unchanged. The shield shrink is a slower, monotonic smooth scale transition. The previous 43-clip version remains selectable. This is an unapproved physical review, not a claim of perfect wrist anatomy or collision-free skin.</p>')+out[end:]
 require('WristShield_v239' in out and '44 clips' in out,'VIEWER_CANDIDATE_PATCH_FAILED')
 return out

def patch_server(original):
 old='ObsidiantiPalmGripIK/2.0.36'
 require(old in original,'SERVER_VERSION_ANCHOR_NOT_FOUND')
 return original.replace(old,'ObsidiantiWristShield/2.0.39')

def main(packet,launcher,expected):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 require(launcher.is_file() and sha(launcher)==expected,'LAUNCHER_SHA_INVALID')
 manifest=json.loads((packet/'manifest.json').read_text())
 require(set(manifest)=={'driver.py','fix.py','test.py','contract.json'},'PAYLOAD_ALLOWLIST_DRIFT')
 require(all(sha(packet/p)==d for p,d in manifest.items()),'PAYLOAD_MEMBER_SHA_INVALID')
 contract=json.loads((packet/'contract.json').read_text())
 require(contract['schema']==V and contract['authority']=='TERMUX_GIT_ONLY' and contract['input43SHA256']==SOURCE
         and contract['canonicalSHA256']==CANON and set(contract['sourceMutablePaths'])==set(FILES),'CONTRACT_IDENTITY_DRIFT')
 for name in ('driver.py','fix.py','test.py'):compile((packet/name).read_bytes(),name,'exec')
 downloads=pathlib.Path.home()/'storage/downloads';require(downloads.is_dir(),'ANDROID_DOWNLOADS_MISSING')
 root=pathlib.Path.home()/'.local/state'/V/'working';root.mkdir(parents=True,exist_ok=True)
 receipt=root/'RECEIPT.json'
 if receipt.exists():
  state=json.loads(receipt.read_text())
  require(state.get('schema')==V and state.get('launcherSHA256')==expected,'RESUME_IDENTITY_CHANGED')
 else:
  state={'schema':V,'runId':datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8],
         'authority':'TERMUX_GIT_ONLY','launcherSHA256':expected,'canonicalSHA256':CANON,
         'input43SHA256':SOURCE,'agentsGitBlob':AGENTS,'ownerVisualAcceptance':'PENDING',
         'canonicalModified':False,'original43Modified':False,'status':'BOOT'};save(receipt,state)
 def stage(name):state['stage']=name;save(receipt,state);print('STAGE='+name,flush=True)
 try:
  stage('ISOLATED_TERMUX_GIT_SOURCE_POLICY_AND_43_GLTF_PIN')
  repo=root/'checkout/repo'
  if not repo.is_dir():
   repo.parent.mkdir(parents=True,exist_ok=True)
   p=subprocess.run(['git','clone','--quiet','--depth=1','--single-branch','--branch','main',REMOTE,str(repo)],
      env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0'),stdin=subprocess.DEVNULL,
      capture_output=True,text=True,timeout=1200)
   require(p.returncode==0,'GIT_CLONE_FAILED_'+p.stderr[-500:])
  helper=module(repo/OLDHELPER,'v239_git_helper');helper.BASE=BASE
  old=module(repo/V236,'v236_publish_helper')
  require(helper.AGENTS==AGENTS and helper.CANON==CANON,'PINNED_HELPER_POLICY_DRIFT')
  require(helper.g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'LIVE_AGENTS_BLOB_CHANGED')
  head=helper.g(repo,'rev-parse','HEAD');helper.verify_pinned_ancestry(repo,BASE,head)
  for path,digest in ((SOURCE_PATH,SOURCE),(CANON_PATH,CANON)):
   require('oid sha256:'+digest in helper.git(repo,'show','HEAD:'+path).stdout,'LOCKED_SOURCE_SHA_MISMATCH_'+path)
  protected={p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED}
  require(not helper.g(repo,'status','--porcelain'),'DIRTY_ISOLATED_CHECKOUT')
  state['sourceGitHead']=head;state['protectedBefore']=protected
  stage('BUILD_VERSIONED_VIEWER_AND_SOURCE_WITH_UNIQUE_PATHS')
  vpath=root/'viewer.html';spath=root/'server.py'
  viewer=patch_viewer((repo/OLDVIEW).read_text());server=patch_server((repo/OLDSERVER).read_text())
  for path,data in ((vpath,viewer),(spath,server)):
   if path.exists():require(path.read_text()==data,'RESUMED_GENERATION_DRIFT_'+str(path))
   else:path.write_text(data)
  files={dest:launcher if name=='LAUNCHER' else vpath if name=='GENERATED_VIEWER' else spath if name=='GENERATED_SERVER' else packet/name
         for dest,name in FILES.items()}
  stage('PUBLISH_COMPLETE_V239_SOURCE_TERMUX_GIT_REMOTE_READBACK')
  sourcecommit=old.publish(helper,repo,files,'SOURCE',protected);state['sourceCommit']=sourcecommit
  stage('GIT_LFS_HYDRATE_EXACT_V236_PUBLISHED_43_CLIPS')
  helper.hydrate(repo,{SOURCE_PATH:SOURCE});source=repo/SOURCE_PATH
  require(sha(source)==SOURCE,'REAL_43_SOURCE_SHA_MISMATCH')
  core=module(repo/CORE,'v239_glb_core');fix=module(packet/'fix.py','v239_fix')
  stage('ACTUAL_43_CLIP_WRIST_AND_SHIELD_PRETEST_NEGATIVE_TESTS')
  proc=subprocess.run([sys.executable,str(packet/'test.py'),str(source),str(repo/CORE)],cwd=packet,
       stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=500,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  require(proc.returncode==0,'REAL_MODEL_PREFLIGHT_FAILED_'+proc.stdout[-900:]+proc.stderr[-1400:]);print(proc.stdout.strip(),flush=True)
  stage('BAKE_AND_REOPEN_44_CLIP_REVIEW_WITH_LOCKED_RIGHT_ARM')
  final=root/(V+'_'+state['runId']+'_44_CLIP_REVIEW.glb');proof=root/'WRIST_SHIELD_PROOF.json'
  if final.exists() and proof.exists():
   report=json.loads(proof.read_text());require(sha(final)==report['outputSHA256'],'RESUMED_BINARY_SHA_DRIFT')
  else:
   require(not final.exists() and not proof.exists(),'PARTIAL_BAKE_COLLISION')
   report=fix.run(source,final,proof,core)
  j,b=core.read_glb(final);original,origbin=core.read_glb(source)
  require(len(j['animations'])==44 and j['animations'][:43]==original['animations'] and b.startswith(origbin),'43_CLIP_PRESERVATION_FAILED')
  previous=original['animations'][-1];nextone=j['animations'][-1]
  right_ids={core.name_ids(j)[n] for n in fix.RIGHT}
  signature=lambda a:[(c['target'],a['samplers'][c['sampler']]) for c in a['channels'] if c['target']['node'] in right_ids]
  require(signature(previous)==signature(nextone),'RIGHT_ARM_CHANNEL_IDENTITY_CHANGED')
  userfile=downloads/final.name;helper.copy_new(final,userfile)
  require(sha(userfile)==report['outputSHA256'],'ANDROID_REVIEW_FILE_SHA_DRIFT')
  state.update({'reviewDownload':str(userfile),'outputSHA256':sha(userfile),'clipCount':44})
  stage('START_IDENTIFIED_44_CLIP_AND_PREVIOUS_43_CLIP_REVIEW_VIEWER')
  models={'candidate':userfile,'before':source}
  meta={key:{'sha256':sha(path),'bytes':path.stat().st_size,'url':'/models/'+key+'.glb',
             'animations':[a['name'] for a in (j if key=='candidate' else original)['animations']]}
        for key,path in models.items()}
  token=hashlib.sha256((state['runId']+sourcecommit+expected+sha(userfile)).encode()).hexdigest()[:24]
  identity={'schema':V,'runId':state['runId'],'sourceCommit':sourcecommit,'buildToken':token,
    'launcherSHA256':expected,'htmlPath':str(repo/(SC+'_viewer.html')),'models':meta,
    'modelPaths':{k:str(path) for k,path in models.items()},'canonicalModelSHA256':CANON,
    'mode':'THREEJS_WRIST_ORIENTATION_SMOOTH_SHIELD_44_CLIP_REVIEW'}
  transport=module(repo/'campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py','v239_viewer_transport');transport.V=V
  ticket=transport.start_server(root,repo,identity)
  state.update({'viewerURL':ticket['url'],'viewerPort':ticket['port'],'viewerPID':ticket['pid']})
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(transport.open_browser(ticket['url'])).upper(),flush=True)
  stage('PUBLISH_44_CLIP_REVIEW_AND_EVIDENCE_GIT_LFS')
  prefix=REL+state['runId']+'/'
  glbpath=prefix+'OBSIDIANTI_SWORD1_WRIST_SHIELD_44_CLIP_UNAPPROVED.glb'
  require(helper.g(repo,'check-attr','filter','--',glbpath).endswith('lfs'),'REVIEW_GLB_NOT_LFS')
  require({p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED}==protected,'PROTECTED_HASH_DRIFT')
  evidence={'schema':V,'authority':'TERMUX_GIT_ONLY','status':'UNAPPROVED_44_CLIP_REVIEW',
    'original43SHA256':SOURCE,'resultSHA256':sha(userfile),'rulesBlob':AGENTS,'sourceGitHead':head,
    'sourceCommit':sourcecommit,'viewerURL':ticket['url'],'ownerVisualAcceptance':'PENDING',
    'original43Preserved':True,'canonicalModified':False,'rightArmSourceSamplersPreserved':True,
    'poseTimingUnchanged':True,'shield':report['shield'],'leftWrist':report['leftWrist']}
  ev=root/'EVIDENCE.json';save(ev,evidence)
  md=root/'REPORT.md';md.write_text('# Obsidianti v2.0.39 wrist and shield review\n\n'
    'Original 43 clips, right arm, and pose timing preserved. Left wrist correction and slower continuous shield shrinking are in appended 44th clip.\n\n'
    'Owner visual approval PENDING. Actual physical wrist grip quality is not proved by numerical IK alone.\n\n'
    'Source SHA: '+SOURCE+'\nResult SHA: '+sha(userfile)+'\nViewer: '+ticket['url']+'\n')
  commit=old.publish(helper,repo,{prefix+'REPORT.md':md,prefix+'WRIST_SHIELD_PROOF.json':proof,
      prefix+'EVIDENCE.json':ev,glbpath:userfile},'EVIDENCE',protected)
  state.update({'status':'44_CLIP_REVIEW_PUBLISHED_OWNER_ACCEPTANCE_PENDING','evidenceCommit':commit})
  stage('REMOTE_GIT_LFS_READBACK_COMPLETE')
  print('RESULT_GLB='+str(userfile),flush=True)
  print('RESULT_SHA256='+sha(userfile),flush=True)
  print('SOURCE_GIT_COMMIT='+sourcecommit,flush=True)
  print('EVIDENCE_GIT_COMMIT='+commit,flush=True)
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('CANONICAL_AND_PREVIOUS_43_CLIPS_UNCHANGED=YES',flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as err:
  state.update({'status':'BLOCKED','error':str(err)[:1800],'traceback':traceback.format_exc()[-2800:]})
  print('STATUS=BLOCKED '+state['error'],flush=True);raise
 finally:save(receipt,state);print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('usage driver.py PACKET LAUNCHER EXPECTED_SHA')
 main(sys.argv[1],sys.argv[2],sys.argv[3])
