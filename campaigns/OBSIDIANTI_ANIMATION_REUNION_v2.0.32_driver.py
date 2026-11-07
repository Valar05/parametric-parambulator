#!/usr/bin/env python3
"""Termux Git only: preserve the published 30 clips, append v2.0.16 Lionheart, repair viewer aliases."""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,subprocess,sys,time,uuid,traceback
sys.dont_write_bytecode=True
V='OBSIDIANTI_ANIMATION_REUNION_v2.0.32'
BASE='386ed52d83828d8f0611860dd66a41ba6ba90d56'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
THIRTY='53339b746023c096c1df7196f3adeb29702f63345d45f8fcec75dde49d500b66'
V16='e7f60fea731fd9537380868adbb52fee63df34fdf1b6d7694bc39925b440fa1d'
CANON_PATH='assets/obsidianti/Obsidianti.glb'
THIRTY_PATH='diagnostics/obsidianti/animation-reunion-v2.0.31/runs/20261107T181326Z-8a265a9b/OBSIDIANTI_30_CLIP_SHIELD_AND_LANCE_LIBRARY_UNAPPROVED.glb'
V16_PATH='diagnostics/obsidianti/arp-contact-ik-authoring-v2.0.16/runs/20261107T041249Z-40a10759/Obsidianti_ARP_FULL_LIBRARY_UNAPPROVED.glb'
V31_SOURCE='campaigns/OBSIDIANTI_ANIMATION_REUNION_v2.0.31_compose.py'
V31_BLOB='3203b3b0b18bdbcb247541cdac3e9d7167a50558'
V16_KEYS='diagnostics/obsidianti/arp-contact-ik-authoring-v2.0.16/runs/20261107T041249Z-40a10759/KEYS.json'
V16_KEYS_BLOB='c02692b3c77f33faf417157b8586bcfb9e5aeec3'
OLD_HELPER_BLOB='610970b4acc11033b1345a508aa2c6c38f0e2adc'
SC='campaigns/'+V
FILES={SC+'_LAUNCH.sh':'LAUNCHER',SC+'_driver.py':'driver.py',SC+'_compose.py':'compose.py',SC+'_viewer.html':'viewer.html',SC+'_server.py':'server.py',SC+'.contract.json':'contract.json','tests/'+V+'_TEST.py':'test_compose.py'}
REL='diagnostics/obsidianti/animation-reunion-v2.0.32/runs/'
PROTECTED=[CANON_PATH,'assets/repl/Repl.glb',
  THIRTY_PATH,V16_PATH,
  'diagnostics/obsidianti/vanguard-rigify-arp-v2.0.17/runs/20261107T044021Z-81e43a05/OBSIDIANTI_VANGUARD_ARP_EXPERIMENT_UNAPPROVED.glb',
  'diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/20261107T021037Z-2edec0d5/AxeKick/ARP_AxeKick_REVIEW.glb']

def require(test,message):
 if not test:raise RuntimeError(message)
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 require(spec and spec.loader,'PYTHON_HELPER_IMPORT_UNAVAILABLE_'+name)
 x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x);return x
def save(path,obj):
 p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_name('.'+p.name+'.'+uuid.uuid4().hex[:8]+'.tmp')
 tmp.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n');os.replace(tmp,p)

def commit_unique(helper,repo,paths,label,protected):
 existing=[p for p in paths if (repo/p).exists()]
 if existing:
  require(len(existing)==len(paths) and all((repo/p).is_file() and sha(repo/p)==sha(source) for p,source in paths.items()),'VERSIONED_DESTINATION_COLLISION_'+label)
  require(not helper.g(repo,'status','--porcelain'),'REUSED_COMMIT_CHECKOUT_DIRTY')
  return helper.g(repo,'rev-parse','HEAD')
 require(not helper.g(repo,'status','--porcelain'),'DIRTY_ISOLATED_CHECKOUT_'+label)
 for dest,src in paths.items():
  require(not (repo/dest).exists(),'VERSIONED_PATH_ALREADY_PRESENT_'+dest)
  helper.copy_new(src,repo/dest)
 helper.git(repo,'add','--',*sorted(paths))
 staged=set(helper.g(repo,'diff','--cached','--name-only').splitlines())
 require(staged==set(paths),'STAGED_MUTATION_OUTSIDE_ALLOWLIST_'+label)
 if not helper.git(repo,'config','user.name',check=False).stdout.strip():helper.git(repo,'config','user.name','Termux Obsidianti ARP')
 if not helper.git(repo,'config','user.email',check=False).stdout.strip():helper.git(repo,'config','user.email','termux-obsidianti-arp@users.noreply.github.com')
 helper.git(repo,'commit','-m','Obsidianti: restore latest Lionheart ARP and fix Three.js bone lookup '+label,timeout=220)
 commit=helper.publish(repo,label,protected)
 for dest,src in paths.items():
  remote=helper.git(repo,'show','refs/remotes/origin/main:'+dest).stdout
  if dest.endswith('.glb'):require('oid sha256:'+sha(src) in remote,'REMOTE_LFS_POINTER_NOT_MATCHING_'+dest)
  else:require(remote==src.read_text(),'REMOTE_SOURCE_READBACK_NOT_MATCHING_'+dest)
 require(not helper.g(repo,'status','--porcelain'),'POST_PUBLISH_DIRTY_CHECKOUT')
 return commit

def main(packet,launcher,expected):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 require(launcher.is_file() and sha(launcher)==expected,'ENTRY_LAUNCHER_SHA_CHANGED')
 manifest=json.loads((packet/'manifest.json').read_text())
 expectedfiles={'driver.py','compose.py','test_compose.py','viewer.html','server.py','contract.json','v22_helpers.py'}
 require(set(manifest)==expectedfiles,'PAYLOAD_MEMBER_ALLOWLIST_WRONG')
 for name,expectedSHA in manifest.items():require(sha(packet/name)==expectedSHA,'PAYLOAD_MEMBER_HASH_WRONG_'+name)
 contract=json.loads((packet/'contract.json').read_text())
 require(contract['schema']==V and contract['authority']=='TERMUX_GIT_ONLY' and contract['pinnedGitBase']==BASE,'CONTRACT_WRONG')
 require(set(contract['sourceMutablePaths'])==set(FILES) and contract['canonicalSHA256']==CANON and contract['input30SHA256']==THIRTY and contract['lionheartARPv216SHA256']==V16,'CONTRACT_AUTHORITY_OR_INPUTS_WRONG')
 helperbytes=(packet/'v22_helpers.py').read_bytes()
 blob=hashlib.sha1(b'blob '+str(len(helperbytes)).encode()+b'\0'+helperbytes).hexdigest()
 require(blob==OLD_HELPER_BLOB,'PINNED_GIT_TRANSPORT_MODULE_CHANGED')
 for p in ('driver.py','compose.py','test_compose.py','server.py'):
  compile((packet/p).read_bytes(),str(packet/p),'exec')
 downloads=pathlib.Path.home()/'storage/downloads';require(downloads.is_dir(),'ANDROID_DOWNLOADS_REQUIRED')
 root=pathlib.Path.home()/'.local/state'/V/'working';root.mkdir(parents=True,exist_ok=True)
 receipt=root/'RECEIPT.json'
 if receipt.exists():
  state=json.loads(receipt.read_text());require(state.get('schema')==V and state.get('launcherSHA256')==expected,'RESUME_IDENTITY_MISMATCH')
 else:
  runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
  state={'schema':V,'runId':runid,'launcherSHA256':expected,'authority':'TERMUX_GIT_ONLY',
         'rulesBlob':AGENTS,'rulesTitle':'AGENTS.md and live Campaign Etiquette',
         'canonicalObsidiantiSHA256':CANON,'source30SHA256':THIRTY,'v16LionheartSHA256':V16,
         'canonicalModified':False,'ownerVisualAcceptance':'PENDING','status':'BOOT'}
  save(receipt,state)
 def stage(label):state['stage']=label;save(receipt,state);print('STAGE='+label,flush=True)
 helper=load(packet/'v22_helpers.py','pinned_termux_git_helper_v22')
 helper.BASE=BASE
 require(helper.AGENTS==AGENTS and helper.CANON==CANON and helper.REMOTE.endswith('Valar05/parametric-parambulator.git'),'GIT_REPOSITORY_OR_POLICY_DRIFT')
 try:
  stage('ISOLATED_TERMUX_GIT_BOOT')
  checkout=root/'checkout';repo=checkout/'repo'
  if repo.is_dir():
   require(helper.g(repo,'rev-parse','--show-toplevel')==str(repo),'ISOLATED_REPO_PATH_MISMATCH')
   require(not helper.g(repo,'status','--porcelain'),'ISOLATED_REPO_DIRTY')
   require(helper.g(repo,'remote','get-url','origin').endswith('Valar05/parametric-parambulator.git'),'WRONG_GIT_REMOTE')
   head=helper.g(repo,'rev-parse','HEAD');ancestry=helper.verify_pinned_ancestry(repo,BASE,head)
  else:
   checkout.mkdir(parents=True,exist_ok=True);repo,head,ancestry=helper.checkout(checkout)
  state.update(inputGitHead=head,ancestry=ancestry)
  require(helper.g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'RULES_READ_BLOCKED_POLICY_CHANGED')
  for p,hashvalue in ((CANON_PATH,CANON),(THIRTY_PATH,THIRTY),(V16_PATH,V16)):
   require('oid sha256:'+hashvalue in helper.git(repo,'show','HEAD:'+p).stdout,'GIT_LFS_SOURCE_POINTER_MISMATCH_'+p)
  require(helper.g(repo,'rev-parse','HEAD:'+V31_SOURCE)==V31_BLOB,'PINNED_30_CLIP_COMPOSER_CHANGED')
  require(helper.g(repo,'rev-parse','HEAD:'+V16_KEYS)==V16_KEYS_BLOB,'PINNED_LIONHEART_ACTION_INVENTORY_CHANGED')
  before={p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED};state['protectedBefore']=before
  stage('PREFLIGHT_ALL_NEW_GIT_DESTINATIONS')
  existing=[p for p in FILES if (repo/p).exists()]
  require(not existing or len(existing)==len(FILES),'PARTIAL_VERSIONED_GIT_SOURCE_COLLISION')
  source={dest:(launcher if name=='LAUNCHER' else packet/name) for dest,name in FILES.items()}
  stage('PUBLISH_VERSIONED_V232_SOURCE_THROUGH_TERMUX_GIT')
  source_commit=commit_unique(helper,repo,source,'SOURCE',before)
  state['sourceCommit']=source_commit
  stage('HYDRATE_EXACT_30_CLIP_V216_AND_CANONICAL_GLB')
  helper.hydrate(repo,{CANON_PATH:CANON,THIRTY_PATH:THIRTY,V16_PATH:V16})
  canonical=repo/CANON_PATH;base30=repo/THIRTY_PATH;donor=repo/V16_PATH
  stage('COMPOSE_41_ANIMATIONS_KEEP_PREVIOUS_30_UNMODIFIED')
  fix=load(packet/'compose.py','obs_41_clip_real_composition')
  output=root/(V+'_'+state['runId']+'_REVIEW.glb');proof=root/'COMPOSITION_PROOF.json'
  if output.is_file() and proof.is_file():
   result=json.loads(proof.read_text());require(result.get('outSHA256')==sha(output),'RESUMED_OUTPUT_SHA_WRONG')
  else:
   require(not output.exists() and not proof.exists(),'INCOMPLETE_PREVIOUS_OUTPUT_COLLISION')
   result=fix.compose(base30,donor,canonical,output,proof,repo/V31_SOURCE)
  require(result.get('status')=='41_CLIP_SHIELD_AND_LANCE_REVIEW_UNAPPROVED' and result.get('count')==41 and result.get('outSHA256')==sha(output),'REAL_41_CLIP_COMPOSITION_INVALID')
  require(result['original30AnimationsJSONUnchanged'] and result['original30BinaryPrefixUnchanged'] and len(result['appended'])==11,'ORIGINAL_30_CHANGED_OR_LIONHEART_MISSING')
  test=subprocess.run([sys.executable,str(packet/'test_compose.py'),'--base',str(base30),'--donor',str(donor),
                       '--canonical',str(canonical),'--candidate',str(output),'--proof',str(proof),
                       '--prior-source',str(repo/V31_SOURCE)],cwd=packet,capture_output=True,text=True,timeout=450,stdin=subprocess.DEVNULL,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  require(test.returncode==0,'ACTUAL_41_CLIP_OUTPUT_REGRESSION_TEST_FAILED_'+test.stdout[-750:]+test.stderr[-1400:])
  print(test.stdout.strip(),flush=True);state['outputVerification']=test.stdout.strip()
  candidate=downloads/output.name;helper.copy_new(output,candidate)
  require(sha(candidate)==result['outSHA256'],'ANDROID_DOWNLOADS_41_CLIP_SHA_CHANGED')
  state['candidateSHA256']=sha(candidate);state['candidateDownload']=str(candidate)
  stage('SHA_VERIFIED_REAL_GLTF_WITH_SHIELD_AND_LANCE')
  token=hashlib.sha256((state['runId']+source_commit+expected+sha(candidate)+V16+THIRTY).encode()).hexdigest()[:24]
  assets={'candidate':candidate,'before':base30,'historical':canonical,'v16':donor}
  metas={k:{'sha256':sha(f),'bytes':f.stat().st_size,'url':'/models/'+k+'.glb',
            'animations':[x['name'] for x in fix.load_prior(repo/V31_SOURCE).read_glb(f)[0]['animations']]} for k,f in assets.items()}
  viewer={'schema':V,'runId':state['runId'],'sourceCommit':source_commit,'buildToken':token,'launcherSHA256':expected,
         'htmlPath':str(repo/(SC+'_viewer.html')),'models':metas,'modelPaths':{k:str(f) for k,f in assets.items()},
         'canonicalModelSHA256':CANON,'mode':'THREE_JS_41_CLIP_LIONHEART_ARP_ONE_TWO_HANDED_REVIEW_UNAPPROVED'}
  oldviewer=load(repo/'campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py','verified_existing_threejs_viewer_transport')
  oldviewer.V=V
  stage('SERVE_UNIQUE_SHA_VERIFIED_BROWSER_VIEWER')
  ticket=oldviewer.start_server(root,repo,viewer)
  state.update({'viewerURL':ticket['url'],'serverPID':ticket['pid'],'serverPort':ticket['port'],'viewerHTTPVerified':True})
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(oldviewer.open_browser(ticket['url'])).upper(),flush=True)
  evidencepath=REL+state['runId']+'/'
  binarypath=evidencepath+'OBSIDIANTI_41_CLIP_SHIELD_LANCE_LIONHEART_ARP_REVIEW_UNAPPROVED.glb'
  require(helper.g(repo,'check-attr','filter','--',binarypath).endswith('lfs'),'NEW_OUTPUT_NOT_LFS_TRACKED')
  after={p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED}
  require(after==before,'PROTECTED_PREVIOUS_ASSET_MODIFIED')
  evidence={'schema':V,'status':'REVIEW_PUBLISHED_OWNER_ACCEPTANCE_PENDING',
            'runId':state['runId'],'rulesBlob':AGENTS,'liveEtiquette':'READ_THIS_TURN_AND_PINNED',
            'sourceGitHead':head,'sourceCommit':source_commit,'ownerVisualAcceptance':'PENDING',
            'canonicalModified':False,'base30SHA256':THIRTY,'v16LionheartSHA256':V16,
            'canonicalSHA256':CANON,'reviewSHA256':sha(candidate), 'reviewBytes':candidate.stat().st_size,
            'original30Protected':True,'lionheart11Transferred':True,'totalClips':41,
            'viewerBug':'THREE_JS_GLTFLOADER_COLON_UNDERSCORE_NODE_ALIASES_AND_GRACEFUL_OVERLAY',
            'ThreeJSViewTest':state['outputVerification'],'viewerURL':ticket['url'],
            'viewerHTTPVerified':True,'protectedBefore':before,'protectedAfter':after,
            'composition':result}
  ev=root/'EVIDENCE.json';save(ev,evidence)
  report=root/'REPORT.md'
  report.write_text('# Obsidianti 41-clip ARP Lionheart reunion v2.0.32\n\n'
    '**Owner visual acceptance: PENDING.** Canonical untouched; separate unapproved review GLB.\n\n'
    'Exact previous 30 clips retained; added the 11 v2.0.16 Lionheart ARP actions (including Lionheart_Idle).\n'
    'Vanguard 19, Ares guard steps 8, full authored idle, accepted AxeKick, original Running remain.\n'
    'Original shield/lance geometry, material and skin preserved. No v2.0.19 unapproved toe-roll variants.\n'
    'Viewer now resolves GLTFLoader-sanitized bone names for upper-body overlay and shield and keeps clip playable if overlay unavailable.\n\n'
    'Review SHA-256: '+sha(candidate)+'\nViewer: '+ticket['url']+'\n')
  items={evidencepath+'REPORT.md':report,evidencepath+'COMPOSITION_PROOF.json':proof,evidencepath+'EVIDENCE.json':ev,binarypath:candidate}
  stage('PUBLISH_41_CLIP_REVIEW_EVIDENCE_BY_TERMUX_GIT')
  evidencecommit=commit_unique(helper,repo,items,'EVIDENCE',before)
  state.update({'evidenceCommit':evidencecommit,'status':'41_CLIP_GIT_PUBLISHED_OWNER_VISUAL_REVIEW_PENDING'})
  stage('REMOTE_GIT_LFS_AND_TEXT_READBACK_VERIFIED')
  print('RESULT_GLB='+str(candidate),flush=True)
  print('RESULT_SHA256='+sha(candidate),flush=True)
  print('SOURCE_GIT_COMMIT='+source_commit,flush=True)
  print('EVIDENCE_GIT_COMMIT='+evidencecommit,flush=True)
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('CANONICAL_UNCHANGED=YES',flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as exc:
  state.update({'status':'BLOCKED','errorType':type(exc).__name__,'error':str(exc)[:1800],'traceback':traceback.format_exc()[-4500:]})
  save(receipt,state)
  print('STATUS=BLOCKED '+state['error'],flush=True)
  if (root/'COMPOSITION_PROOF.json').exists():print('COMPOSITION_DIAGNOSTICS='+str(root/'COMPOSITION_PROOF.json'),flush=True)
  raise
 finally:
  save(receipt,state);print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('usage driver.py PACKET LAUNCHER EXPECTED_SHA')
 main(sys.argv[1],sys.argv[2],sys.argv[3])
