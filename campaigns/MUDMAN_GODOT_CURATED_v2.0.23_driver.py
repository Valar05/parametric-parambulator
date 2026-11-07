#!/usr/bin/env python3
"""Single-invocation Termux Git campaign. Existing v2.0.22 real GLB -> exact texture, grounded origin, Godot-only clips.
No Blender, no action resampling, no canonical character mutations. Git is sole publication authority.
"""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,time,uuid,urllib.request,traceback
sys.dont_write_bytecode=True
V='MUDMAN_GODOT_CURATED_v2.0.23'
BASE='95aa8562e2036cd11e3d1063b5b569f92afef53b'
V22_DRIVER='campaigns/MUDMAN_ARES_FULL_RETARGET_v2.0.22_driver.py'
V22_DRIVER_BLOB='610970b4acc11033b1345a508aa2c6c38f0e2adc'
V22_VIEWER='campaigns/MUDMAN_ARES_FULL_RETARGET_v2.0.22_viewer.html'
V22_VIEWER_BLOB='2b1ee3ca9150a28cbe3457e9797ba29df9526a79'
V22_SERVER='campaigns/MUDMAN_ARES_FULL_RETARGET_v2.0.22_server.py'
V22_SERVER_BLOB='3ff094299d095cd9f358eba8e890b78b28869361'
V22_GLB='diagnostics/mudman/ares-full-retarget-v2.0.22/runs/20261107T133703Z-00546afd/MUDMAN_ARES_FULL_LIBRARY_UNAPPROVED.glb'
V22_GLB_SHA='396e9cf024846ba9e8c5159a9b8660b21a296a73a6e656d4c347dc86780079d6'
V22_RESULTS='diagnostics/mudman/ares-full-retarget-v2.0.22/runs/20261107T133703Z-00546afd/ACTION_RESULTS.json'
V22_RESULTS_BLOB='d504ee3fe108b552fcd74648a2be8fcd1f1fe9ae'
ZIP_SHA='fbcb592ac941dbc34ecade66b044b551f5bd55bf5855be50d8af5caba0514f79'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
LOCKED=['assets/obsidianti/Obsidianti.glb','assets/repl/Repl.glb','diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/20261107T021037Z-2edec0d5/AxeKick/ARP_AxeKick_REVIEW.glb']
SRCROOT='campaigns/'+V
SOURCE_FILES={SRCROOT+'_LAUNCH.sh':'LAUNCHER',SRCROOT+'_driver.py':'driver.py',SRCROOT+'_patch_glb.py':'patch_glb.py',SRCROOT+'_viewer.html':'viewer.html',SRCROOT+'_server.py':'server.py',SRCROOT+'.contract.json':'contract.json','tests/'+V+'_TEST.py':'test_patch.py'}
REL='diagnostics/mudman/godot-curated-v2.0.23/runs/'

def require(c,msg):
 if not c:raise RuntimeError(msg)
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,doc):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 temp=p.with_name('.'+p.name+'.'+uuid.uuid4().hex[:6]+'.tmp')
 temp.write_text(json.dumps(doc,sort_keys=True,indent=2)+'\n');os.replace(temp,p)
def patch_exact(s,old,new):
 n=s.count(old);require(n>0,'VIEWER_EXPECTED_SOURCE_FRAGMENT_MISSING_'+repr(old[:65]));return s.replace(old,new)

def viewer(repo,packet):
 original=(repo/V22_VIEWER).read_text()
 s=original
 s=patch_exact(s,'Mudman | All Ares animations','Mudman | Godot-curated clay boxer')
 s=patch_exact(s,'<option value="Mudman_Jab-Enemy">Mudman Jab-Enemy</option>','<option value="Jab-Enemy">Jab-Enemy</option>')
 s=patch_exact(s,"const featured=['Mudman_Jab-Enemy','Mudman_Cross-Enemy','Mudman_Idle','Mudman_Run'];", "const featured=['Jab-Enemy','Cross-Enemy','Idle-Cross','Run'];")
 s=patch_exact(s,"floor.position.y=modelBounds.min.y+Number(el('ground').value)", "floor.position.y=Number(el('ground').value)")
 s=patch_exact(s,'Review every exported Ares action slot on the Mudman.','Review 23 Godot-mapped enemy clips on the textured, floor-grounded Mudman.')
 s=patch_exact(s,'Every populated Ares action slot transferred to the original Mudman Mixamo FBX. Includes enemy Jab/Cross. No manual cleanup. Floor guide is visual, not a physical ground solver.',
 'Original Mes​hy clay texture verified and embedded; 77 Ares candidates curated to 23 Godot enemy states. Poses and keyframes unchanged. Floor guide y=0; root translated using actual skinned idle mesh minimum. Owner review pending.'.replace('Mes\u200bhy','Meshy'))
 # Detect white / missing material at run time instead of showing a misleading successful status.
 needle='disposeScene(loadedScene);loadedScene=gltf.scene;scene.add(loadedScene);'
 replacement='''disposeScene(loadedScene);loadedScene=gltf.scene;scene.add(loadedScene);
 let physicalMeshes=0, texturedMeshes=0;
 loadedScene.traverse(obj=>{if(obj.isMesh){physicalMeshes++;
  const mats=Array.isArray(obj.material)?obj.material:[obj.material];
  if(mats.length>0&&mats.every(m=>m&&m.map&&m.map.image))texturedMeshes++}});
 if(physicalMeshes<1||texturedMeshes!==physicalMeshes)throw Error('MUDMAN_TEXTURE_NOT_MAPPED: '+texturedMeshes+'/'+physicalMeshes);
 el('identity').textContent+=' | TEXTURED '+texturedMeshes+'/'+physicalMeshes;'''
 s=patch_exact(s,needle,replacement)
 s=patch_exact(s,'Mudman | Ares ARP Review','Mudman | Godot curation 2.0.23')
 (packet/'viewer.html').write_text(s)
 srv=(repo/V22_SERVER).read_text().replace('MudmanAresARPViewer/2.0.20','MudmanGodotCuratedViewer/2.0.23')
 (packet/'server.py').write_text(srv)
 require('floor.position.y=modelBounds.min.y' not in s,'VIEWER_BAD_LEGACY_FLOOR_GUESS')
 require('MUDMAN_TEXTURE_NOT_MAPPED' in s and 'Floor guide y=0' in s or 'Floor guide y=0'.lower() in s.lower(),'VIEWER_REPAIR_MISSING')
 return {n:sha(packet/n) for n in ('viewer.html','server.py')}

def commit_stage(old,repo,paths,message,protected):
 # No direct GitHub writes. Unique destinations, staged allowlist, Git readback.
 existing=[p for p in paths if (repo/p).exists()]
 if existing:
  require(len(existing)==len(paths) and all((repo/p).is_file() and sha(repo/p)==sha(f) for p,f in paths.items()),'PARTIAL_OR_DIFFERENT_VERSIONED_SOURCE_EXISTS')
  require(not old.g(repo,'status','--porcelain'),'REUSED_SOURCE_CHECKOUT_DIRTY')
  return old.g(repo,'rev-parse','HEAD')
 for p in paths:require(not (repo/p).exists(),'SOURCE_VERSION_COLLISION_'+p)
 for p,f in paths.items():old.copy_new(f,repo/p)
 old.git(repo,'add','--',*sorted(paths))
 staged=set(old.g(repo,'diff','--cached','--name-only').splitlines())
 require(staged==set(paths),'GIT_STAGED_FILES_OUTSIDE_ALLOWLIST')
 if not old.git(repo,'config','user.name',check=False).stdout.strip():old.git(repo,'config','user.name','Termux Mudman Curation')
 if not old.git(repo,'config','user.email',check=False).stdout.strip():old.git(repo,'config','user.email','termux-mudman-curation@users.noreply.github.com')
 old.git(repo,'commit','-m',message,timeout=200)
 head=old.publish(repo,message,protected)
 for p,f in paths.items():
  content=old.git(repo,'show','refs/remotes/origin/main:'+p).stdout
  if p.endswith('.glb'):
   require('oid sha256:'+sha(f) in content,'GIT_LFS_REMOTE_POINTER_NOT_MATCHING_'+p)
  else:require(content==f.read_text(),'REMOTE_TEXT_READBACK_CHANGED_'+p)
 require(not old.g(repo,'status','--porcelain'),'POSTCOMMIT_CHECKOUT_DIRTY')
 return head

def main(packet,launcher,expected):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 require(sha(launcher)==expected,'ENTRY_SHA_CHANGED')
 manifest=json.loads((packet/'manifest.json').read_text());require(set(manifest)=={'driver.py','patch_glb.py','test_patch.py','contract.json','v22_helpers.py'},'PACKET_FILE_ALLOWLIST_CHANGED')
 for name,expectedsha in manifest.items():require(sha(packet/name)==expectedsha,'PACKET_MEMBER_SHA_MISMATCH_'+name)
 contract=json.loads((packet/'contract.json').read_text())
 require(contract['schema']==V and contract['authority']=='TERMUX_GIT_ONLY' and contract['previousSourceGLBSHA256']==V22_GLB_SHA,'CONTRACT_INVALID')
 downloads=pathlib.Path.home()/'storage/downloads';require(downloads.is_dir(),'ANDROID_DOWNLOADS_ACCESS_REQUIRED')
 zip_candidates=sorted(downloads.glob('Meshy_AI_Mudstone_Golem*.zip'))
 target_zip=next((p for p in zip_candidates if p.is_file() and not p.is_symlink() and sha(p)==ZIP_SHA),None)
 require(target_zip is not None,'OWNER_MESHY_ZIP_MISSING_FROM_ANDROID_DOWNLOADS')
 runroot=pathlib.Path.home()/'.local/state'/V/'working';runroot.mkdir(parents=True,exist_ok=True)
 receipt=runroot/'RECEIPT.json'
 if receipt.exists():
  state=json.loads(receipt.read_text());require(state.get('schema')==V and state.get('launcherSHA256')==expected,'RESUME_IDENTITY_CHANGED')
 else:
  runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
  state={'schema':V,'runId':runid,'stage':'BOOT','status':'BOOT','launcherSHA256':expected,'authority':'TERMUX_GIT_ONLY',
    'sourceReviewGLBSHA256':V22_GLB_SHA,'rulesBlob':AGENTS_BLOB,'canonicalObsidiantiSHA256':CANON_SHA,
    'readGodotRepo':'Valar05/gravity-fist','godotSceneBlobSHA':'4f07c8c2af40038c1f672750b8a155f53f123b6d',
    'godotAttackDataBlobSHA':'f2a1036f75cc7c4b7821e700ffa61a6bed7980fc',
    'approvedPosesUnchanged':True,'ownerVisualAcceptance':'PENDING','canonicalModified':False,
    'blenderOrARPInvoked':False}
 save(receipt,state)
 def checkpoint(stage):state['stage']=stage;save(receipt,state);print('STAGE='+stage,flush=True)
 try:
  checkpoint('VALIDATE_TESTS_AND_OWNER_ATLAS')
  test=subprocess.run([sys.executable,str(packet/'test_patch.py'),'--mesh-zip',str(target_zip)],env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=180)
  require(test.returncode==0,'PATCH_SELFTEST_FAILED_'+test.stdout[-600:]+test.stderr[-600:])
  state['selfTests']=test.stdout.strip()
  checkpoint('GIT_ISOLATED_SOURCE_BASE')
  root=runroot/'checkout'
  # Import the original v2.0.22 proven checkout and publication functions from the immutable published repo.
  # We need a checkout to load those helpers. Do not run them or another workflow directly.
  helper_file=packet/'v22_helpers.py'
  require(helper_file.is_file(),'MISSING_PINNED_V22_GIT_HELPERS')
  _helperbytes=helper_file.read_bytes()
  require(hashlib.sha1(b'blob '+str(len(_helperbytes)).encode()+b'\0'+_helperbytes).hexdigest()==V22_DRIVER_BLOB,'V22_GIT_HELPER_BLOB_CHANGED')
  helper=load(helper_file,'v22_git_helpers_curate')
  helper.BASE=BASE
  require(helper.AGENTS==AGENTS_BLOB and helper.CANON==CANON_SHA and helper.REMOTE.endswith('Valar05/parametric-parambulator.git'),'GIT_AUTHORITY_OR_RULES_MISMATCH')
  if (root/'repo').exists():
   repo=root/'repo';require(helper.g(repo,'rev-parse','--show-toplevel')==str(repo),'CHECKOUT_ORIGIN_CHANGED')
   require(not helper.g(repo,'status','--porcelain'),'CHECKOUT_DIRTY_RESUME')
   head=helper.g(repo,'rev-parse','HEAD');proof=helper.verify_pinned_ancestry(repo,BASE,head)
   require(helper.g(repo,'remote','get-url','origin').endswith('Valar05/parametric-parambulator.git'),'WRONG_REMOTE_RESUME')
  else:
   root.mkdir(parents=True,exist_ok=True)
   repo,head,proof=helper.checkout(root)
  require(helper.g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS_BLOB,'LIVE_AGENTS_CHANGED_STOP')
  for path,sha_bl in ((V22_DRIVER,V22_DRIVER_BLOB),(V22_VIEWER,V22_VIEWER_BLOB),(V22_SERVER,V22_SERVER_BLOB),(V22_RESULTS,V22_RESULTS_BLOB)):
   require(helper.g(repo,'rev-parse','HEAD:'+path)==sha_bl,'BASELINE_GIT_SOURCE_CHANGED_'+path)
  state['gitBaseHead']=head;state['gitAncestryProof']=proof
  protected={p:helper.g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}
  state['protectedBefore']=protected
  checkpoint('PREPARE_AND_PUBLISH_NEW_VERSIONED_SOURCE')
  hashes=viewer(repo,packet)
  state['viewerPatchHashes']=hashes
  # The launcher embeds and verifies the helpers, but they are not published as new source;
  # the already published v2.0.22 driver is their canonical source.
  sources={dst:(launcher if member=='LAUNCHER' else packet/member) for dst,member in SOURCE_FILES.items()}
  source_commit=commit_stage(helper,repo,sources,'Mudman: Godot curation texture grounding SOURCE',protected)
  state['sourceCommit']=source_commit
  checkpoint('SOURCE_COMMITTED_AND_REMOTE_READBACK')
  # Verify exact already published review input from Android Downloads or via authenticated Git LFS.
  inputs=sorted(downloads.glob('MUDMAN_ARES_FULL_RETARGET_v2.0.22_*_REVIEW_LIBRARY.glb'))
  source=next((p for p in inputs if p.is_file() and not p.is_symlink() and sha(p)==V22_GLB_SHA),None)
  if source is None:
   helper.hydrate(repo,{V22_GLB:V22_GLB_SHA});source=repo/V22_GLB
  require(sha(source)==V22_GLB_SHA,'REAL_INPUT_REVIEW_GLB_CHANGED')
  checkpoint('REAL_SOURCE_GLB_VERIFIED_AND_TRANSFORMING')
  patch=load(packet/'patch_glb.py','mudman_curated_glb_v223')
  candidate=runroot/(V+'_'+state['runId']+'_REVIEW.glb')
  proof_file=runroot/'CURATION.json'
  if candidate.is_file() and proof_file.is_file():
   r=json.loads(proof_file.read_text());require(r.get('outputGLBSHA256')==sha(candidate),'CURATION_RESUME_BINARY_INCONSISTENT')
  else:
   require(not candidate.exists() and not proof_file.exists(),'PARTIAL_CURATION_FILES_REQUIRE_SAFE_DIAGNOSIS')
   r=patch.apply(source,target_zip,candidate,proof_file)
  require(r.get('animationsBefore')==77 and r.get('animationsAfter')==23,'ACTUAL_CURATION_COUNTS_INVALID')
  require(r.get('textureEmbeddedSHA256')==patch.OWNER_PNG and abs(r['skinnedGroundAfter']['minY'])<.002,'TEXTURE_OR_GROUND_VERIFICATION_FAILED')
  save(receipt,state)
  candidate_download=downloads/candidate.name
  helper.copy_new(candidate,candidate_download);require(sha(candidate_download)==sha(candidate),'ANDROID_DOWNLOADS_CANDIDATE_BYTES_CHANGED')
  state['candidateSHA256']=sha(candidate_download);state['candidateDownload']=str(candidate_download)
  checkpoint('REAL_TEXTURE_GROUND_AND_23_CLIPS_VERIFIED')
  # Viewer is generated and already published by the Git-source stage; serves a stable y=0 floor.
  token=hashlib.sha256((state['runId']+source_commit+expected+sha(candidate_download)).encode()).hexdigest()[:24]
  viewer_meta={'schema':V,'runId':state['runId'],'buildToken':token,'launcherSHA256':expected,'sourceCommit':source_commit,
   'htmlPath':str(repo/(SRCROOT+'_viewer.html')),
   'models':{'candidate':{'sha256':sha(candidate_download),'bytes':candidate_download.stat().st_size,'url':'/models/candidate.glb',
      'animations':[x['to'] for x in r['animationMap']]}},'modelPaths':{'candidate':str(candidate_download)},
   'canonicalModelSHA256':CANON_SHA,'mode':'TEXTURED_GODOT_CURATED_REAL_SKINNED_GROUND_UNAPPROVED'}
  oldviewer=load(repo/'campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py','mudman_v213_viewer_helper')
  oldviewer.V=V
  if state.get('viewerURL') and state.get('viewerHTTPVerified'):
   ticket={'url':state['viewerURL'],'pid':state.get('serverPID'),'port':state.get('serverPort')}
  else:
   ticket=oldviewer.start_server(runroot,repo,viewer_meta)
   state['viewerURL']=ticket['url'];state['serverPID']=ticket['pid'];state['serverPort']=ticket['port']
  state['viewerHTTPVerified']=True;checkpoint('ACTUAL_GLB_HTTP_VIEWER_VERIFIED')
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(oldviewer.open_browser(ticket['url'])).upper(),flush=True)
  # Evidence: one immutable v2.0.23 review GLB. Never touch canonical or approved animation paths.
  dirrel=REL+state['runId']+'/'
  glb_rel=dirrel+'MUDMAN_GODOT_CURATED_REVIEW_UNAPPROVED.glb'
  require(helper.g(repo,'check-attr','filter','--',glb_rel).endswith('lfs'),'RESULT_GLB_NOT_GIT_LFS_TRACKED')
  evidence={'schema':V,'authority':'TERMUX_GIT_ONLY','sourceCommit':source_commit,'inputGitHead':head,'runId':state['runId'],'rulesBlob':AGENTS_BLOB,
    'sourceReviewGLBSHA256':V22_GLB_SHA,'inputAresSHA256':'63b6e7a7250cfb03e49cf0d335101d808126ae926894d74c1b2a6a49936b8b2a',
    'ownerMudmanZipSHA256':ZIP_SHA,'outputGLBSHA256':sha(candidate_download),'outputBytes':candidate_download.stat().st_size,
    'groundOffsetMeters':r['groundOffsetMeters'],'textureSHA256':r['textureEmbeddedSHA256'],'curatedClips':r['animationsAfter'],
    'animationKeyframesPreserved':True,'originalMeshAndSkinPreserved':True,'previousAcceptedActionsModified':False,
    'canonicalModified':False,'protectedBefore':protected,
    'protectedAfter':{p:helper.g(repo,'rev-parse','HEAD:'+p) for p in LOCKED},
    'viewerURL':ticket['url'],'viewerHTTPVerified':True,'ownerVisualAcceptance':'PENDING','testReceipt':state['selfTests']}
  require(evidence['protectedBefore']==evidence['protectedAfter'],'CANONICAL_OR_APPROVED_FILE_CHANGED')
  evidence_path=runroot/'EVIDENCE.json';save(evidence_path,evidence)
  report=runroot/'REPORT.md'
  report.write_text('# Mudman v2.0.23 | Godot curated / original texture / grounded origin\n\n'
   '**Owner visual acceptance: PENDING.** This is a review derivative, not a canonical asset update.\n\n'
   'Input v2.0.22 77-clip GLB SHA256 `'+V22_GLB_SHA+'`. Output 23-clip GLB SHA256 `'+sha(candidate_download)+'`.\n\n'
   'Actual 2048x2048 Meshy RGB texture embedded as baseColorTexture for every UV-mapped mesh primitive (texture SHA256 `'+r['textureEmbeddedSHA256']+'`).\n\n'
   'Ground calculated from '+str(r['skinnedOriginalGround']['witnessVertices'])+' skinned geometry witnesses: '
   'original min Y '+str(round(r['skinnedOriginalGround']['minY'],6))+' m, constant root correction Y '+str(round(r['groundOffsetMeters'],6))+' m, after correction min Y '+str(round(r['skinnedGroundAfter']['minY'],6))+' m. The floor is y=0 in viewer.\n\n'
   'Original animation samplers, mesh vertex buffer, skins, and per-bone motion are byte-for-byte retained for kept clips. '
   '54 irrelevant/static/duplicate-looking candidates excluded, though prone holds retained. No vendor ARP rerun.\n\n'
   'Godot references: `Valar05/gravity-fist/scenes/SecurityTitan.tscn` and `security_titan.json`, pinned blob SHAs in CURATION.json. '
   'Idle-Cross is an explicit alias for the moving Idle OBCross slot, not an exact action from the Ares source. '
   'Godot HitHeadRight has no exact matching motion from this Ares export, so HitHeadRightBig is retained without falsely renaming it.\n\n'
   '## Kept clips\n\n'+'\n'.join('- `'+x['to']+'` ← `'+x['from']+'`' for x in r['animationMap'])+'\n\n'
   'Viewer: '+ticket['url']+'\n')
  items={dirrel+'REPORT.md':report,dirrel+'CURATION.json':proof_file,dirrel+'EVIDENCE.json':evidence_path,glb_rel:candidate_download}
  commit_evidence=commit_stage(helper,repo,items,'Mudman: Godot curation texture grounding EVIDENCE',protected)
  state['evidenceCommit']=commit_evidence
  state['status']='TEXTURED_GROUNDED_GODOT_CURATED_REVIEW_READY_UNAPPROVED'
  checkpoint('EVIDENCE_GIT_PUBLISHED_AND_READBACK')
  print('CURATED_MUDMAN_GLB='+str(candidate_download),flush=True)
  print('CURATED_MUDMAN_SHA256='+sha(candidate_download),flush=True)
  print('CURATED_MUDMAN_CLIPS=23',flush=True)
  print('REVIEW_URL='+ticket['url'],flush=True)
  print('EVIDENCE_URL=https://github.com/Valar05/parametric-parambulator/blob/'+commit_evidence+'/'+dirrel+'REPORT.md',flush=True)
  print('PREVIOUS_ACCEPTED_MODELS_UNCHANGED=YES',flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as ex:
  state.update({'status':'BLOCKED','errorType':type(ex).__name__,'error':str(ex)[:1000],'traceback':traceback.format_exc()[-2400:]})
  checkpoint('BLOCKED_'+type(ex).__name__)
  print('STATUS=BLOCKED '+str(ex)[:850],flush=True)
  raise
 finally:
  save(receipt,state);print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 require(len(sys.argv)==4,'usage: driver.py PACKET LAUNCHER EXPECTED_SHA')
 main(*sys.argv[1:])
