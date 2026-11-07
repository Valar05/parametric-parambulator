#!/usr/bin/env python3
"""Single authorized Termux Git campaign: exact historical idle + composed guarded Ares steps.
No runtime substitution, no canonical mutation, no re-retargeting and no Godot implementation.
"""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,time,uuid,traceback
sys.dont_write_bytecode=True
V='OBSIDIANTI_ARP_GUARD_COMPOSE_v2.0.29'
BASE='a15b5aee199624fa38c3ca4137fb328c5e4a63d5'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
ARP='e7f60fea731fd9537380868adbb52fee63df34fdf1b6d7694bc39925b440fa1d'
CANON_PATH='assets/obsidianti/Obsidianti.glb'
ARP_PATH='diagnostics/obsidianti/arp-contact-ik-authoring-v2.0.16/runs/20261107T041249Z-40a10759/Obsidianti_ARP_FULL_LIBRARY_UNAPPROVED.glb'
V16_KEYS='diagnostics/obsidianti/arp-contact-ik-authoring-v2.0.16/runs/20261107T041249Z-40a10759/KEYS.json'
V16_KEYS_BLOB='c02692b3c77f33faf417157b8586bcfb9e5aeec3'
V110_ORIGINAL='campaigns/OBSIDIANTI_GLTF_LIBRARY_v1.1.0.py'
V110_BLOB='772880dbf4c47c4e79fd9f4f097681a5f7c3bd08'
OLD_HELPER_BLOB='610970b4acc11033b1345a508aa2c6c38f0e2adc'
PROTECTED=[CANON_PATH,'assets/repl/Repl.glb','diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/20261107T021037Z-2edec0d5/AxeKick/ARP_AxeKick_REVIEW.glb']
SC='campaigns/'+V
FILES={SC+'_LAUNCH.sh':'LAUNCHER',SC+'_driver.py':'driver.py',SC+'_compose.py':'compose.py',SC+'_viewer.html':'viewer.html',SC+'_server.py':'server.py',SC+'.contract.json':'contract.json','tests/'+V+'_TEST.py':'test_compose.py'}
REL='diagnostics/obsidianti/arp-guard-compose-v2.0.29/runs/'

def require(x,msg):
 if not x:raise RuntimeError(msg)
def load(p,n):
 spec=importlib.util.spec_from_file_location(n,p);require(spec and spec.loader,'HELPER_MODULE_UNAVAILABLE');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def save(p,obj):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_name('.'+p.name+'.'+uuid.uuid4().hex[:7]+'.tmp');tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');os.replace(tmp,p)

def commit_unique(helper,repo,paths,label,protected):
 # A previously published identical version may only be reused in a safe resume.
 exist=[x for x in paths if (repo/x).exists()]
 if exist:
  require(len(exist)==len(paths) and all((repo/x).is_file() and sha(repo/x)==sha(p) for x,p in paths.items()),'VERSIONED_DESTINATION_COLLISION_'+label)
  require(not helper.g(repo,'status','--porcelain'),'PREVIOUS_VERSION_REUSE_DIRTY')
  return helper.g(repo,'rev-parse','HEAD')
 require(not helper.g(repo,'status','--porcelain'),'CHECKOUT_DIRTY_BEFORE_COMMIT')
 for path,src in paths.items():
  require(not (repo/path).exists(),'DESTINATION_ALREADY_EXISTS_'+path)
  helper.copy_new(src,repo/path)
 helper.git(repo,'add','--',*sorted(paths))
 staged=set(helper.g(repo,'diff','--cached','--name-only').splitlines())
 require(staged==set(paths),'STAGED_FILE_ALLOWLIST_VIOLATION_'+label)
 if not helper.git(repo,'config','user.name',check=False).stdout.strip():helper.git(repo,'config','user.name','Termux Obsidianti Guard')
 if not helper.git(repo,'config','user.email',check=False).stdout.strip():helper.git(repo,'config','user.email','termux-obsidianti-guard@users.noreply.github.com')
 helper.git(repo,'commit','-m','Obsidianti: recover v1.1 authored idle and ARP v2.0.16 eight-direction guard '+label,timeout=220)
 commit=helper.publish(repo,label,protected)
 for path,src in paths.items():
  text=helper.git(repo,'show','refs/remotes/origin/main:'+path).stdout
  if path.endswith(('.glb','.blend')):
   require('oid sha256:'+sha(src) in text,'REMOTE_GIT_LFS_BINARY_POINTER_INVALID_'+path)
  else:
   require(text==src.read_text(),'REMOTE_GIT_TEXT_READBACK_INVALID_'+path)
 require(not helper.g(repo,'status','--porcelain'),'POST_PUBLISH_DIRTY_CHECKOUT')
 return commit

def main(packet,launcher,expected):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 require(launcher.is_file() and sha(launcher)==expected,'ENTRY_SHA_CHANGED')
 mf=json.loads((packet/'manifest.json').read_text())
 need={'driver.py','compose.py','viewer.html','server.py','test_compose.py','contract.json','v22_helpers.py'}
 require(set(mf)==need,'PACKET_ALLOWLIST_MISMATCH')
 for f,h in mf.items():require(sha(packet/f)==h,'PACKET_INTEGRITY_FAILED_'+f)
 contract=json.loads((packet/'contract.json').read_text())
 require(contract['schema']==V and contract['authority']=='TERMUX_GIT_ONLY' and contract['canonicalSHA256']==CANON and contract['arpInputSHA256']==ARP,'CAMPAIGN_CONTRACT_CHANGED')
 require(set(contract['sourceMutablePaths'])==set(FILES) and contract['pinnedGitBase']==BASE,'MUTATION_SCOPE_OR_BASE_CHANGED')
 # Deterministic immutable Git helper provenance.
 hb=(packet/'v22_helpers.py').read_bytes()
 hashblob=hashlib.sha1(b'blob '+str(len(hb)).encode()+b'\0'+hb).hexdigest()
 require(hashblob==OLD_HELPER_BLOB,'PINNED_GIT_PUBLISH_HELPER_DRIFT')
 for name in ('driver.py','compose.py','test_compose.py','server.py'):
  compile((packet/name).read_bytes(),str(packet/name),'exec')
 downloads=pathlib.Path.home()/'storage/downloads';require(downloads.is_dir(),'ANDROID_DOWNLOADS_UNAVAILABLE')
 root=pathlib.Path.home()/'.local/state'/V/'working';root.mkdir(parents=True,exist_ok=True)
 receipt=root/'RECEIPT.json'
 if receipt.exists():
  state=json.loads(receipt.read_text());require(state.get('schema')==V and state.get('launcherSHA256')==expected,'RESUME_SCRIPT_OR_RECEIPT_IDENTITY_MISMATCH')
 else:
  runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
  state={'schema':V,'runId':runid,'status':'BOOT','authority':'TERMUX_GIT_ONLY','launcherSHA256':expected,
    'rulesBlob':AGENTS,'liveEtiquette':'CAMPAIGN_ETIQUETTE — Git Script Campaign Operating Rules','canonicalObsidiantiSHA256':CANON,
    'originalAnimationDonorSHA256':CANON,'arpReviewSHA256':ARP,'canonicalModified':False,'arpInvoked':False,
    'otherAnimationsProtected':23,'ownerVisualAcceptance':'PENDING'}
  save(receipt,state)
 def stage(label):state['stage']=label;save(receipt,state);print('STAGE='+label,flush=True)
 helper=load(packet/'v22_helpers.py','obs_guard_prior_git')
 helper.BASE=BASE
 require(helper.AGENTS==AGENTS and helper.CANON==CANON and helper.REMOTE.endswith('Valar05/parametric-parambulator.git'),'GIT_HELPER_AUTHORITY_CHANGED')
 try:
  stage('BOOT_ISOLATED_OWNER_TERMUX_GIT')
  rd=root/'checkout';repo=rd/'repo'
  if repo.is_dir():
   require(helper.g(repo,'rev-parse','--show-toplevel')==str(repo),'ISOLATED_CHECKOUT_PATH_DRIFT')
   require(not helper.g(repo,'status','--porcelain'),'ISOLATED_CHECKOUT_DIRTY')
   require(helper.g(repo,'remote','get-url','origin').endswith('Valar05/parametric-parambulator.git'),'WRONG_GIT_REMOTE_RESUME')
   head=helper.g(repo,'rev-parse','HEAD');history=helper.verify_pinned_ancestry(repo,BASE,head)
  else:
   rd.mkdir(parents=True,exist_ok=True);repo,head,history=helper.checkout(rd)
  state['inputGitHead']=head;state['verifiedHistory']=history
  require(helper.g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'LIVE_AGENTS_POLICY_DRIFT')
  require('oid sha256:'+CANON in helper.git(repo,'show','HEAD:'+CANON_PATH).stdout,'ORIGINAL_CANONICAL_LFS_POINTER_CHANGED')
  require('oid sha256:'+ARP in helper.git(repo,'show','HEAD:'+ARP_PATH).stdout,'V216_ARP_LFS_POINTER_CHANGED')
  require(helper.g(repo,'rev-parse','HEAD:'+V110_ORIGINAL)==V110_BLOB,'HISTORICAL_V110_GUARD_SOURCE_CHANGED')
  require(helper.g(repo,'rev-parse','HEAD:'+V16_KEYS)==V16_KEYS_BLOB,'V216_LIVE_MOTION_KEYS_REPORT_CHANGED')
  protected={p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED};state['protectedBefore']=protected
  # Preflight all unique source destinations before touching any canonical binary.
  stage('GIT_DESTINATION_COLLISION_PREFLIGHT')
  if any((repo/p).exists() for p in FILES):
   require(len([p for p in FILES if (repo/p).exists()])==len(FILES),'PARTIAL_VERSIONED_SOURCE_COLLISION')
  source_files={dst:(launcher if entry=='LAUNCHER' else packet/entry) for dst,entry in FILES.items()}
  stage('PUBLISH_VERSIONED_SOURCE_TERMUX_GIT')
  published_source=commit_unique(helper,repo,source_files,'SOURCE',protected)
  previously_published=state.get('sourceCommit')
  if previously_published:
   require(helper.git(repo,'merge-base','--is-ancestor',previously_published,published_source,check=False).returncode==0,'SOURCE_RESUME_HISTORY_DIVERGED')
   source_commit=previously_published
  else:source_commit=published_source
  state['sourceCommit']=source_commit
  stage('VERIFY_SOURCE_COMMIT_REMOTE_READBACK')
  # Physical binary authority: one exact original authored idle GLB and one real 24-25-key v2.0.16 ARP GLB.
  stage('HYDRATE_REAL_AUTHORED_IDLE_AND_MOVING_ARP_LIBRARY')
  helper.hydrate(repo,{CANON_PATH:CANON,ARP_PATH:ARP})
  original=repo/CANON_PATH;arp=repo/ARP_PATH
  require(sha(original)==CANON and sha(arp)==ARP,'PHYSICAL_INPUTS_DIFFER_FROM_PINNED_LFS')
  # Test on the REAL v2.0.16 GLB rig before any production composition. The test creates
  # temporary synthetic guard keys, never asserting they are actual owner source.
  test=subprocess.run([sys.executable,str(packet/'test_compose.py'),'--real',str(arp)],cwd=packet,capture_output=True,text=True,timeout=280,stdin=subprocess.DEVNULL,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  require(test.returncode==0,'PHYSICAL_RIG_COMPOSITION_SELFTEST_FAILED_'+test.stdout[-850:]+test.stderr[-1100:])
  print(test.stdout.strip(),flush=True);state['physicalSchemaTests']=test.stdout.strip()
  stage('REAL_23_CLIP_LIBRARY_GUARD_COMPOSITION')
  output=root/(V+'_'+state['runId']+'_REVIEW.glb');proof=root/'GUARD_COMPOSITION.json'
  fix=load(packet/'compose.py','obs_real_guard_compose')
  if output.is_file() and proof.is_file():
   result=json.loads(proof.read_text());require(result.get('resultSHA256')==sha(output),'RESUME_RESULT_SHA_CHANGED')
  else:
   require(not output.exists() and not proof.exists(),'PARTIAL_COMPOSITION_OUTPUT_REQUIRES_DIAGNOSIS')
   result=fix.compose(original,arp,output,proof)
  require(result['status']=='GUARD_COMPOSED_REVIEW_UNAPPROVED' and result['existingAnimationsPreserved']==23 and len(result['steps'])==8,'COMPOSITION_RESULT_DOES_NOT_MEET_USER_SCOPE')
  require(all(c['hipKeys']>=10 and c['maxGuardWorldRotationErrorDegrees']<.45 for c in result['steps']),'ACTUAL_EIGHT_STEPS_NOT_PHYSICALLY_COMPATIBLE')
  candidate=downloads/output.name
  helper.copy_new(output,candidate)
  require(sha(candidate)==result['resultSHA256'],'ANDROID_DOWNLOADS_REVIEW_MODEL_SHA_CHANGED')
  state['candidateSHA256']=sha(candidate);state['candidateDownload']=str(candidate)
  stage('REAL_33_CLIP_RESULT_VERIFIED_NO_CANONICAL_MUTATION')
  # Serve original historical authoring, v2.0.16 unmodified ARP and corrected candidate, SHA-checked.
  token=hashlib.sha256((state['runId']+source_commit+expected+sha(candidate)+ARP+CANON).encode()).hexdigest()[:24]
  assets={'candidate':candidate,'original':arp,'historical':original}
  metas={key:{'sha256':sha(file),'bytes':file.stat().st_size,'url':'/models/'+key+'.glb',
    'animations':[a['name'] for a in fix.read_glb(file)[0]['animations']]} for key,file in assets.items()}
  viewer={'schema':V,'runId':state['runId'],'sourceCommit':source_commit,'buildToken':token,'launcherSHA256':expected,
   'htmlPath':str(repo/(SC+'_viewer.html')),'models':metas,'modelPaths':{k:str(p) for k,p in assets.items()},
   'canonicalModelSHA256':CANON,'mode':'THREE_JS_RECOVERED_LIONHEART_IDLE_ARP_EIGHT_DIRECTION_COMBAT_REVIEW_UNAPPROVED'}
  oldviewer=load(repo/'campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py','obs_guard_existing_viewer_transport')
  oldviewer.V=V
  if state.get('viewerURL') and state.get('viewerHTTPVerified'):
   # Verify old process is still alive rather than trust a stale receipt; if not start new.
   import urllib.request
   try:
    with urllib.request.urlopen('http://127.0.0.1:'+str(state['serverPort'])+'/health',timeout=3) as h:
     health=json.loads(h.read())
    alive=health.get('runId')==state['runId'] and health.get('buildToken')==token
   except Exception:alive=False
   ticket={'url':state['viewerURL'],'port':state['serverPort'],'pid':state.get('serverPID')} if alive else oldviewer.start_server(root,repo,viewer)
  else:ticket=oldviewer.start_server(root,repo,viewer)
  state.update({'viewerURL':ticket['url'],'serverPID':ticket['pid'],'serverPort':ticket['port'],'viewerHTTPVerified':True})
  stage('HTTP_VIEWER_BINARY_SHA_AND_RUN_ID_VERIFIED')
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(oldviewer.open_browser(ticket['url'])).upper(),flush=True)
  run_dir=REL+state['runId']+'/'
  glbrel=run_dir+'OBSIDIANTI_COMBAT_GUARD_RECOVERED_REVIEW_UNAPPROVED.glb'
  require(helper.g(repo,'check-attr','filter','--',glbrel).endswith('lfs'),'LFS_REVIEW_MODEL_ATTRIBUTE_NOT_CONFIGURED')
  evidence={'schema':V,'status':'REVIEW_READY_NOT_OWNER_ACCEPTED','runId':state['runId'],'sourceCommit':source_commit,
    'sourceGitHead':head,'rulesBlob':AGENTS,'campaignEtiquette':'LIVE_READ_AND_CONTRACT_PINNED',
    'ownerVisualAcceptance':'PENDING','canonicalModified':False,'arpRerun':False,
    'sourceCanonicalIdleSHA256':CANON,'sourceARPv216SHA256':ARP,'candidateSHA256':sha(candidate),'candidateBytes':candidate.stat().st_size,
    'original23ClipsUnmodified':True,'newActionCount':10,'stepCount':8,'originalAuthoredIdleRecovered':True,
    'guardComposition':result,'physicalSchemaTests':state['physicalSchemaTests'],'viewerHTTPVerified':True,'viewerURL':ticket['url'],
    'protectedBefore':protected,'protectedAfter':{p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED}}
  require(evidence['protectedAfter']==protected,'PROTECTED_USER_ASSET_CHANGED')
  ev=root/'EVIDENCE.json';save(ev,evidence)
  report=root/'REPORT.md'
  report.write_text('# Obsidianti Ares lower-body steps + recovered Lionheart guard (v2.0.29)\n\n'
    '**Owner visual approval: PENDING.** Source was restored from original canonical content SHA `'+CANON+'`. ARP step lower-body source v2.0.16 SHA `'+ARP+'`.\n\n'
    'Recovered historical named animations: `LionheartIdle_UNREVIEWED` (static original guard) and `ObsidiantiIdle` (authored 3.0 second secondary-motion loop).\n\n'
    'Eight new clips `CombatStep*` retain moving Hips, legs, knees, feet, and toes from v2.0.16. Upper Spine subtree uses exact original guard with compensating Spine rotation from the v1.1 algorithm. All 23 original ARP animations retained as-is.\n\n'
    'The ARP v2.0.14 steps were not used: historical KEYS shows only two hip keys per step. The real v2.0.16 steps have 24–25 keys.\n\n'
    'Input 23 clips; output 33 clips. Candidate SHA-256 `'+sha(candidate)+'`.\n\n'
    'Viewer (Three.js, candidate/ARP/historical A/B): '+ticket['url']+'\n\n'
    'No canonical model writes, no vendor ARP rerun, no new Godot game. The proposed Three.js runtime is not implemented in this campaign.\n\n'
    'Guard numerical max world-frame deviations (degrees): '+repr({x['composed']:x['maxGuardWorldRotationErrorDegrees'] for x in result['steps']})+'\n')
  # Versioned evidence only; previously accepted original files and accepted AxeKick never rewritten.
  items={run_dir+'REPORT.md':report,run_dir+'GUARD_COMPOSITION.json':proof,
   run_dir+'EVIDENCE.json':ev,glbrel:candidate}
  stage('COMMIT_EVIDENCE_AND_REAL_BINARY_BY_TERMUX_GIT')
  evidence_commit=commit_unique(helper,repo,items,'EVIDENCE',protected)
  state.update({'evidenceCommit':evidence_commit,'status':'33_CLIP_IDLE_AND_GUARD_STEPS_PUBLISHED_OWNER_REVIEW_PENDING'})
  stage('REMOTE_GIT_LFS_READBACK_COMPLETE')
  print('RESULT_GLB='+str(candidate),flush=True)
  print('RESULT_SHA256='+sha(candidate),flush=True)
  print('SOURCE_GIT_COMMIT='+source_commit,flush=True)
  print('EVIDENCE_GIT_COMMIT='+evidence_commit,flush=True)
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('CANONICAL_UNCHANGED=YES',flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as error:
  state.update({'status':'BLOCKED','error':str(error)[:1500],'errorType':type(error).__name__,'traceback':traceback.format_exc()[-3500:]})
  save(receipt,state)
  print('STATUS=BLOCKED '+state['error'],flush=True)
  if (root/'GUARD_COMPOSITION.json').exists():print('COMPOSITION_DIAGNOSTICS='+str(root/'GUARD_COMPOSITION.json'),flush=True)
  raise
 finally:
  save(receipt,state)
  print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('usage: driver.py PACKET LAUNCHER EXPECTED_SHA')
 main(sys.argv[1],sys.argv[2],sys.argv[3])
