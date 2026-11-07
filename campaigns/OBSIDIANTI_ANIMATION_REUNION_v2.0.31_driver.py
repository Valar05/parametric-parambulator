#!/usr/bin/env python3
"""Single authorized Termux Git repair: finish the 30-clip shield/lance review publication.
Recover SHA-checked completed v2.0.30 output where available; no retargeting or canonical mutation.
"""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,time,uuid,traceback
sys.dont_write_bytecode=True
V='OBSIDIANTI_ANIMATION_REUNION_v2.0.31'
BASE='a72db9e0791fb71574d301864cf8d1926c937c14'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
KICK='c6f1d74b2de97e12f2eefc9c44a0404c26ad19e29d481af08e585130ee9103da'
VANG='3f27fce824c74fbd0a38c1d4f589ef21818a37afc1926459f9abb5739a23f2ce'
CANON_PATH='assets/obsidianti/Obsidianti.glb'
KICK_PATH='diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/20261107T021037Z-2edec0d5/AxeKick/ARP_AxeKick_REVIEW.glb'
VANG_PATH='diagnostics/obsidianti/vanguard-rigify-arp-v2.0.17/runs/20261107T044021Z-81e43a05/OBSIDIANTI_VANGUARD_ARP_EXPERIMENT_UNAPPROVED.glb'
V16_KEYS='diagnostics/obsidianti/arp-contact-ik-authoring-v2.0.16/runs/20261107T041249Z-40a10759/KEYS.json'
V16_KEYS_BLOB='c02692b3c77f33faf417157b8586bcfb9e5aeec3'
V110_ORIGINAL='campaigns/OBSIDIANTI_GLTF_LIBRARY_v1.1.0.py'
V110_BLOB='772880dbf4c47c4e79fd9f4f097681a5f7c3bd08'
OLD_HELPER_BLOB='610970b4acc11033b1345a508aa2c6c38f0e2adc'
PROTECTED=[CANON_PATH,'assets/repl/Repl.glb','diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/20261107T021037Z-2edec0d5/AxeKick/ARP_AxeKick_REVIEW.glb']
SC='campaigns/'+V
FILES={SC+'_LAUNCH.sh':'LAUNCHER',SC+'_driver.py':'driver.py',SC+'_compose.py':'compose.py',SC+'_viewer.html':'viewer.html',SC+'_server.py':'server.py',SC+'.contract.json':'contract.json','tests/'+V+'_TEST.py':'test_compose.py'}
REL='diagnostics/obsidianti/animation-reunion-v2.0.31/runs/'

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
 helper.git(repo,'commit','-m','Obsidianti: unite original Ares guard, shield and Vanguard 2H with accepted AxeKick '+label,timeout=220)
 commit=helper.publish(repo,label,protected)
 for path,src in paths.items():
  text=helper.git(repo,'show','refs/remotes/origin/main:'+path).stdout
  if path.endswith(('.glb','.blend')):
   require('oid sha256:'+sha(src) in text,'REMOTE_GIT_LFS_BINARY_POINTER_INVALID_'+path)
  else:
   require(text==src.read_text(),'REMOTE_GIT_TEXT_READBACK_INVALID_'+path)
 require(not helper.g(repo,'status','--porcelain'),'POST_PUBLISH_DIRTY_CHECKOUT')
 return commit


def recover_previous_v230(previous_dir,fix,original,vanguard,axekick,output,proof):
    """Recover the already-composed GLB from the owner-run v2.0.30 crash.
    Verify its bytes and every commissioned clip against the three real, SHA-pinned
    donor models before copying. Never modify the old receipt or old candidate.
    A missing/invalid recovery returns False so ordinary composition can proceed.
    """
    prior_receipt=previous_dir/'RECEIPT.json'
    if not prior_receipt.is_file():return False
    try:
        old=json.loads(prior_receipt.read_text())
        require(old.get('schema')=='OBSIDIANTI_ANIMATION_REUNION_v2.0.30','PREVIOUS_SCHEMA_WRONG')
        run=old.get('runId','')
        require(len(run)>15 and all(c.isalnum() or c in '-_' for c in run),'PREVIOUS_RUN_ID_INVALID')
        previous_candidate=previous_dir/('OBSIDIANTI_ANIMATION_REUNION_v2.0.30_'+run+'_REVIEW.glb')
        previous_proof=previous_dir/'GUARD_COMPOSITION.json'
        if not previous_candidate.is_file() or not previous_proof.is_file():return False
        audit=json.loads(previous_proof.read_text())
        shaold=sha(previous_candidate)
        require(audit.get('outSHA256')==shaold,'V230_COMPOSED_BINARY_HASH_MISMATCH')
        require(audit.get('canonicalSourceSHA256')==CANON and audit.get('vanguardSourceSHA256')==VANG and audit.get('acceptedAxeKickSourceSHA256')==KICK,'V230_SOURCE_IDENTITY_MISMATCH')
        require(audit.get('status')=='30_CLIP_COMBINED_REVIEW_UNAPPROVED' and audit.get('count')==30 and audit.get('shieldRetained') and audit.get('lanceRetained'),'V230_INVALID_RESULT')
        gj,gb=fix.read_glb(previous_candidate)
        cj,cb=fix.read_glb(original)
        vj,vb=fix.read_glb(vanguard)
        kj,kb=fix.read_glb(axekick)
        expected=list(fix.SELECT_CANON)+[a['name'] for a in vj['animations']]+['AxeKick']
        require(len(expected)==30 and [a['name'] for a in gj['animations']]==expected,'V230_GLTF_INVENTORY_CHANGED')
        require(gb.startswith(cb),'V230_GEOMETRY_BUFFER_NOT_CANONICAL')
        for attr in ('nodes','meshes','skins','materials','textures','images','scenes'):
            require(gj.get(attr)==cj.get(attr),'V230_CANONICAL_GEOMETRY_OR_RIG_CHANGED_'+attr)
        for idx,name in enumerate(fix.SELECT_CANON):
            src=next(a for a in cj['animations'] if a['name']==name)
            require(gj['animations'][idx]==src,'V230_ORIGINAL_GUARDED_ACTION_CHANGED_'+name)
        require(len(audit.get('vanguardVerified',[]))==19,'V230_VANGUARD_TRANSFER_MISSING')
        require(len(audit.get('originalGuardedStepWitnesses',{}))==8,'V230_ARES_STEPS_MISSING')
        require(len(audit.get('idleBreathingMotion',[]))>=2,'V230_FULL_IDLE_MOTION_MISSING')
        require(not output.exists() and not proof.exists(),'V231_RECOVERY_OUTPUT_COLLISION')
        # Atomic copy into the new versioned review path. A failed copy never
        # leaves a partial output that would block the bounded compose fallback.
        partial=output.with_name('.'+output.name+'.recovery-partial')
        require(not partial.exists(),'STALE_PARTIAL_RECOVERY_REQUIRES_INSPECTION')
        try:
            shutil.copy2(previous_candidate,partial)
            require(sha(partial)==shaold,'V231_RECOVERED_COPY_SHA_MISMATCH')
            os.replace(partial,output)
        finally:
            if partial.exists():partial.unlink()
        audit['schema']=V
        audit['recovery']={'method':'SHA_VERIFIED_EXACT_V230_COMPLETED_COMPOSITION','v230RunId':run,
                           'unchangedGLBSHA256':shaold,'v230ReceiptStatus':old.get('status'),'retargetingRerun':False}
        save(proof,audit)
        print('RECOVERED_V230_COMPLETED_GLTF=YES SHA256='+shaold+' CLIPS=30',flush=True)
        return True
    except Exception as error:
        print('PREVIOUS_BINARY_RECOVERY_REJECTED='+str(error)[:400]+'; NORMAL_VERIFIED_COMPOSE_FALLBACK=YES',flush=True)
        # No unauthorized edits to the old candidate; fallback to deterministic compose.
        return False

def main(packet,launcher,expected):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 require(launcher.is_file() and sha(launcher)==expected,'ENTRY_SHA_CHANGED')
 mf=json.loads((packet/'manifest.json').read_text())
 need={'driver.py','compose.py','viewer.html','server.py','test_compose.py','contract.json','v22_helpers.py'}
 require(set(mf)==need,'PACKET_ALLOWLIST_MISMATCH')
 for f,h in mf.items():require(sha(packet/f)==h,'PACKET_INTEGRITY_FAILED_'+f)
 contract=json.loads((packet/'contract.json').read_text())
 require(contract['schema']==V and contract['authority']=='TERMUX_GIT_ONLY' and contract['canonicalSHA256']==CANON and contract['acceptedAxeKickSHA256']==KICK,'CAMPAIGN_CONTRACT_CHANGED')
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
    'originalAnimationDonorSHA256':CANON,'acceptedAxeKickSHA256':KICK,'vanguardReviewSHA256':VANG,'canonicalModified':False,'arpInvoked':False,
    'otherAnimationsProtected':True,'ownerVisualAcceptance':'PENDING'}
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
  require('oid sha256:'+KICK in helper.git(repo,'show','HEAD:'+KICK_PATH).stdout,'ACCEPTED_AXEKICK_LFS_POINTER_CHANGED')
  require('oid sha256:'+VANG in helper.git(repo,'show','HEAD:'+VANG_PATH).stdout,'V217_VANGUARD_LFS_POINTER_CHANGED')
  require(helper.g(repo,'rev-parse','HEAD:'+V110_ORIGINAL)==V110_BLOB,'HISTORICAL_V110_GUARD_SOURCE_CHANGED')
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
  stage('HYDRATE_CANONICAL_SHIELD_VANGUARD_AND_ACCEPTED_AXEKICK')
  helper.hydrate(repo,{CANON_PATH:CANON,KICK_PATH:KICK,VANG_PATH:VANG})
  original=repo/CANON_PATH;kick=repo/KICK_PATH;vang=repo/VANG_PATH
  require(sha(original)==CANON and sha(kick)==KICK and sha(vang)==VANG,'PHYSICAL_INPUTS_DIFFER_FROM_PINNED_LFS')
  # Test on the REAL v2.0.16 GLB rig before any production composition. The test creates
  # temporary synthetic guard keys, never asserting they are actual owner source.
  test=subprocess.run([sys.executable,str(packet/'test_compose.py'),'--real',str(kick)],cwd=packet,capture_output=True,text=True,timeout=280,stdin=subprocess.DEVNULL,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  require(test.returncode==0,'PHYSICAL_RIG_COMPOSITION_SELFTEST_FAILED_'+test.stdout[-850:]+test.stderr[-1100:])
  print(test.stdout.strip(),flush=True);state['physicalSchemaTests']=test.stdout.strip()
  stage('ACTUAL_30_CLIP_ONE_AND_TWO_HANDED_COMPOSITION')
  output=root/(V+'_'+state['runId']+'_REVIEW.glb');proof=root/'GUARD_COMPOSITION.json'
  fix=load(packet/'compose.py','obs_real_guard_compose')
  if output.is_file() and proof.is_file():
   result=json.loads(proof.read_text());require(result.get('outSHA256')==sha(output),'RESUME_RESULT_SHA_CHANGED')
  else:
   require(not output.exists() and not proof.exists(),'PARTIAL_COMPOSITION_OUTPUT_REQUIRES_DIAGNOSIS')
   previous=pathlib.Path.home()/'.local/state'/'OBSIDIANTI_ANIMATION_REUNION_v2.0.30'/'working'
   recovered=recover_previous_v230(previous,fix,original,vang,kick,output,proof)
   if recovered:result=json.loads(proof.read_text())
   else:result=fix.compose(original,vang,kick,output,proof)
  require(result.get('outSHA256')==sha(output),'FINAL_COMPOSER_DRIVER_SHA_CONTRACT_MISMATCH')
  require(result['status']=='30_CLIP_COMBINED_REVIEW_UNAPPROVED' and result['count']==30 and result['shieldRetained'] and result['lanceRetained'],'COMPOSITION_RESULT_DOES_NOT_MEET_USER_SCOPE')
  require(len(result['vanguardVerified'])==19 and len(result['originalGuardedStepWitnesses'])==8 and len(result['idleBreathingMotion'])>=2,'ANIMATIONS_OR_SHIELD_NOT_PROVED')
  candidate=downloads/output.name
  helper.copy_new(output,candidate)
  require(sha(candidate)==result['outSHA256'],'ANDROID_DOWNLOADS_REVIEW_MODEL_SHA_CHANGED')
  state['candidateSHA256']=sha(candidate);state['candidateDownload']=str(candidate)
  stage('REAL_30_CLIP_RESULT_VERIFIED_SHIELD_AND_LANCE_PRESENT')
  # Serve original historical authoring, v2.0.16 unmodified ARP and corrected candidate, SHA-checked.
  token=hashlib.sha256((state['runId']+source_commit+expected+sha(candidate)+KICK+CANON+VANG).encode()).hexdigest()[:24]
  assets={'candidate':candidate,'historical':original,'vanguard':vang,'axekick':kick}
  metas={key:{'sha256':sha(file),'bytes':file.stat().st_size,'url':'/models/'+key+'.glb',
    'animations':[a['name'] for a in fix.read_glb(file)[0]['animations']]} for key,file in assets.items()}
  viewer={'schema':V,'runId':state['runId'],'sourceCommit':source_commit,'buildToken':token,'launcherSHA256':expected,
   'htmlPath':str(repo/(SC+'_viewer.html')),'models':metas,'modelPaths':{k:str(p) for k,p in assets.items()},
   'canonicalModelSHA256':CANON,'mode':'THREE_JS_30_CLIP_CANONICAL_SHIELD_LANCE_ONE_AND_TWO_HANDED_REVIEW'}
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
  glbrel=run_dir+'OBSIDIANTI_30_CLIP_SHIELD_AND_LANCE_LIBRARY_UNAPPROVED.glb'
  require(helper.g(repo,'check-attr','filter','--',glbrel).endswith('lfs'),'LFS_REVIEW_MODEL_ATTRIBUTE_NOT_CONFIGURED')
  evidence={'schema':V,'status':'REVIEW_READY_NOT_OWNER_ACCEPTED','runId':state['runId'],'sourceCommit':source_commit,
    'sourceGitHead':head,'rulesBlob':AGENTS,'campaignEtiquette':'LIVE_READ_AND_CONTRACT_PINNED',
    'ownerVisualAcceptance':'PENDING','canonicalModified':False,'arpRerun':False,
    'sourceCanonicalIdleSHA256':CANON,'acceptedAxeKickSourceSHA256':KICK,'sourceVanguardv217SHA256':VANG,'candidateSHA256':sha(candidate),'candidateBytes':candidate.stat().st_size,
    'historical8GuardStepsUnmodified':True,'allVanguard19Imported':True,'acceptedAxeKickImported':True,'clipCount':30,'originalAuthoredIdleRecovered':True,'shieldAndLanceRetained':True,
    'guardComposition':result,'physicalSchemaTests':state['physicalSchemaTests'],'viewerHTTPVerified':True,'viewerURL':ticket['url'],
    'protectedBefore':protected,'protectedAfter':{p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED}}
  require(evidence['protectedAfter']==protected,'PROTECTED_USER_ASSET_CHANGED')
  ev=root/'EVIDENCE.json';save(ev,evidence)
  report=root/'REPORT.md'
  report.write_text('# Obsidianti: 30-clip shield-and-lance one/two-handed combat library (v2.0.31)\n\n'
    '**Owner visual approval: PENDING.** Only versioned review GLB, canonical unchanged.\n\n'
    'Sources: original canonical sha256 `'+CANON+'`; all 19 Vanguard ARP v2.0.17 sha256 `'+VANG+'`; accepted AxeKick sha256 `'+KICK+'`.\n\n'
    'Preserved ORIGINAL canonical shield and lance meshes, materials, skin, skeleton and rig. Vanguard shield-removed geometry was NOT copied; only its bone animation tracks were imported.\n\n'
    'Exactly 30 clips: full three-second original ObsidiantiIdle; original Running; eight original v1.1 Ares_Step*_Lower clips with original guard; 19 Vanguard clips including two-handed sword attacks; exact accepted separate AxeKick renamed for display.\n\n'
    'No historical Lionheart attacks, no duplicate ARP iterations, no synthesized static guard, no re-retarget. Original source remains in Git history and other experiment artifacts.\n\n'
    'The shield is retained for one- and two-handed animation modes; viewer visibility toggle is display-only, not GLB geometry removal. Hand grips and shield collisions remain visual-review items.\n\n'
    'Three.js viewer: '+ticket['url']+'\n\n'
    'Review GLB SHA256: `'+sha(candidate)+'`\n')
  # Versioned evidence only; previously accepted original files and accepted AxeKick never rewritten.
  items={run_dir+'REPORT.md':report,run_dir+'GUARD_COMPOSITION.json':proof,
   run_dir+'EVIDENCE.json':ev,glbrel:candidate}
  stage('COMMIT_EVIDENCE_AND_REAL_BINARY_BY_TERMUX_GIT')
  evidence_commit=commit_unique(helper,repo,items,'EVIDENCE',protected)
  state.update({'evidenceCommit':evidence_commit,'status':'30_CLIP_SHIELD_AND_LANCE_LIBRARY_OWNER_REVIEW_PENDING'})
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
