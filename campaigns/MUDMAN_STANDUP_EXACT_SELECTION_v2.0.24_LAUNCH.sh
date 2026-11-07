#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
V=MUDMAN_STANDUP_EXACT_SELECTION_v2.0.24
ENTRY="$(sha256sum "$0" | awk '{print $1}')"
printf 'CAMPAIGN=%s\nAUTHORITY=TERMUX_GIT_ONLY\nENTRY_SHA256=%s\n' "$V" "$ENTRY"
export PYTHONDONTWRITEBYTECODE=1
python3 - "$0" "$ENTRY" "${1:-run}" <<'PY'
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,re,shutil,struct,subprocess,sys,time,uuid,traceback

V='MUDMAN_STANDUP_EXACT_SELECTION_v2.0.24'
PREV='MUDMAN_GODOT_CURATED_v2.0.23'
ROOT='campaigns/'+V
REPO='Valar05/parametric-parambulator'
PREV_VIEW='campaigns/'+PREV+'_viewer.html'
PREV_SERVER='campaigns/'+PREV+'_server.py'
PREV_CONTRACT='campaigns/'+PREV+'.contract.json'
PREV_RESULT='diagnostics/mudman/godot-curated-v2.0.23/runs/20261107T143456Z-5a637cc3/MUDMAN_GODOT_CURATED_REVIEW_UNAPPROVED.glb'
PREV_EVIDENCE='diagnostics/mudman/godot-curated-v2.0.23/runs/20261107T143456Z-5a637cc3/EVIDENCE.json'
PREV_GLBSHA='19304bf8007670e36a38b354b5f8d2ea0c39982c97e2a247acdac1190fe2b7ef'
PREV_VIEW_BLOB='36c3d670db8fa87f60adb7237bc59bc4399b80b5'
PREV_CONTRACT_BLOB='a4b3fc5cb429dde507b5d186ec571fbc73a60e9a'
PREV_EVIDENCE_BLOB='3f831e27df993d7f774e7aaa0783ebfa3b8575e3'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
BASE_COMMIT='5ca1ec466ce53871122cc74dc056dd1f3252082f'
ORIGINAL_ERROR='CANNOT_UNAMBIGUOUSLY_SELECT_StandUp'
NEW_PICKER='''function chooseAnimation(gltf,movement){
 const matches=gltf.animations.filter(a=>a.name===movement);
 if(matches.length!==1)throw Error('EXACT_ANIMATION_SELECTION_FAILED_'+movement+' count='+matches.length+'; GLB clips='+JSON.stringify(gltf.animations.map(a=>a.name)));
 return matches[0];
}'''
ORIGINAL_PICKER='''function chooseAnimation(gltf,movement){
 const names=gltf.animations.map(a=>a.name);
 const matching=gltf.animations.filter(a=>new RegExp('(^|[^a-z0-9])'+movement+'($|[^a-z0-9])','i').test(a.name)||a.name.toLowerCase().endsWith(movement.toLowerCase()));
 if(matching.length===1)return matching[0];
 if(gltf.animations.length===1)return gltf.animations[0];
 throw Error('CANNOT_UNAMBIGUOUSLY_SELECT_'+movement+'; GLB clips='+JSON.stringify(names));
}'''

script=pathlib.Path(sys.argv[1]).resolve();claimed_sha=sys.argv[2];mode=sys.argv[3]
root=pathlib.Path.home()/'.local/state'/V/'working';receipt=root/'RECEIPT.json'
state={'schema':V,'authority':'TERMUX_GIT_ONLY','status':'BOOT','launcherSHA256':claimed_sha,
       'rulesBlob':AGENTS_BLOB,'canonicalObsidiantiSHA256':CANON_SHA,'sourceGitBase':BASE_COMMIT,
       'originalGodotCurationSHA256':PREV_GLBSHA,'canonicalModelModified':False,
       'retargetExecuted':False,'animationKeyframesModified':False,'ownerVisualAcceptance':'PENDING'}

def require(x,message):
 if not x:raise RuntimeError(message)
def digest(f):
 h=hashlib.sha256()
 with open(f,'rb') as fh:
  for buf in iter(lambda:fh.read(1024*1024),b''):h.update(buf)
 return h.hexdigest()
def save(p,obj):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_name('.'+p.name+'.'+uuid.uuid4().hex[:6]+'.tmp')
 tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
 os.replace(tmp,p)
def import_path(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 require(spec is not None and spec.loader is not None,'IMPORT_SPEC_FAILED')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 return mod
def stage(s):
 state['stage']=s;save(receipt,state);print('STAGE='+s,flush=True)
def patch_viewer(src):
 require(src.count(ORIGINAL_PICKER)==1,'ORIGINAL_SELECTOR_NOT_EXACTLY_ONE')
 require(src.count('Mudman | Godot curation 2.0.23')==1,'VIEWER_TITLE_SOURCE_CHANGED')
 result=src.replace(ORIGINAL_PICKER,NEW_PICKER,1).replace('Mudman | Godot curation 2.0.23','Mudman | Godot curation 2.0.24',1)
 require(ORIGINAL_ERROR not in result and result.count('function chooseAnimation(gltf,movement)')==1,'SELECTOR_REPAIR_INVALID')
 require('MUDMAN_TEXTURE_NOT_MAPPED' in result and 'floor.position.y=Number(el(\'ground\').value)' in result,'PREVIOUS_MATERIAL_OR_FLOOR_REPAIR_LOST')
 return result

def glb_names(path):
 with open(path,'rb') as f:
  header=f.read(20)
  require(len(header)==20 and header[:4]==b'glTF','GLB_HEADER_INVALID')
  version,total,json_len,chunk=struct.unpack_from('<IIII',header,4)
  require(version==2 and total==path.stat().st_size and chunk==0x4e4f534a,'GLB_HEADER_OR_JSON_CHUNK_INVALID')
  require(0<json_len<15_000_000,'GLB_JSON_CHUNK_SIZE_INVALID')
  data=json.loads(f.read(json_len))
 names=[x.get('name') for x in data.get('animations',[])]
 require(all(isinstance(x,str) and x for x in names),'GLB_ANIMATION_NAME_MISSING')
 return names

def test_picker(viewer,names):
 require(len(names)==23 and len(set(names))==23,'CURATED_GLB_NOT_23_UNIQUE_ANIMATIONS')
 require({'StandUp','ProneBackStandUp','Jab-Enemy','Cross-Enemy','Idle-Cross'}.issubset(names),'EXPECTED_GODOT_ANIMATIONS_MISSING')
 require(viewer.count(NEW_PICKER)==1,'NEW_SELECTOR_NOT_EXACTLY_ONE')
 require(ORIGINAL_PICKER not in viewer,'LEGACY_FUZZY_SELECTOR_RETAINED')
 # Test EXACT source function in JavaScript, not a hand-written approximation.
 code='''const assert=require('node:assert/strict');
const fs=require('node:fs');
const data=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const picker=fs.readFileSync(process.argv[3],'utf8');
const fn=(new Function('return ('+picker+')'))();
const gltf={animations:data.map(name=>({name,signature:'clip-'+name}))};
for(const name of data){assert.equal(fn(gltf,name).name,name)}
assert.equal(fn(gltf,'StandUp').name,'StandUp');
assert.equal(fn(gltf,'ProneBackStandUp').name,'ProneBackStandUp');
assert.throws(()=>fn(gltf,'Stand'),/EXACT_ANIMATION_SELECTION_FAILED/);
assert.throws(()=>fn({animations:[{name:'StandUp'},{name:'StandUp'}]},'StandUp'),/count=2/);
assert.throws(()=>fn({animations:[{name:'Other'}]},'StandUp'),/count=0/);
console.log('EXACT_SELECTION_NODE_TESTS_OK 23_CLIPS + STANDUP_COLLISION + UNKNOWN + DUPLICATE');
'''
 node=shutil.which('node')
 require(node is not None,'NODE_JS_REQUIRED_FOR_BROWSER_SELECTOR_VALIDATION')
 testdir=root/'tests';testdir.mkdir(parents=True,exist_ok=True)
 (testdir/'names.json').write_text(json.dumps(names))
 (testdir/'picker.js').write_text(NEW_PICKER+'\n')
 (testdir/'test.js').write_text(code)
 p=subprocess.run([node,str(testdir/'test.js'),str(testdir/'names.json'),str(testdir/'picker.js')],capture_output=True,text=True,timeout=25)
 require(p.returncode==0,'NODE_EXACT_PICKER_TEST_FAILED_'+p.stderr[-900:])
 print(p.stdout.strip(),flush=True)
 # Also assert the delivered HTML embeds the exact tested function.
 require(NEW_PICKER in viewer,'TESTED_PICKER_NOT_IN_VIEWER')
 return code

try:
 require(script.is_file() and digest(script)==claimed_sha,'ENTRY_SCRIPT_CHANGED')
 if mode=='selftest':
  text='x'+ORIGINAL_PICKER+'\n<title>Mudman | Godot curation 2.0.23</title>\nMUDMAN_TEXTURE_NOT_MAPPED\nfloor.position.y=Number(el(\'ground\').value)'
  new=patch_viewer(text)
  names=['StandUp','ProneBackStandUp','Jab-Enemy','Cross-Enemy','Idle-Cross']+[f'Other{i}' for i in range(18)]
  root.mkdir(parents=True,exist_ok=True)
  test_picker(new,names)
  print('SELFTEST_OK: EXACT_SELECTOR_AND_VIEWER_PATCH',flush=True)
  raise SystemExit(0)
 require(mode=='run','UNKNOWN_MODE')
 root.mkdir(parents=True,exist_ok=True)
 resume_published=False
 if receipt.exists():
  prior=json.loads(receipt.read_text())
  require(prior.get('launcherSHA256')==claimed_sha and prior.get('schema')==V,'PRIOR_RUN_IDENTITY_CONFLICT')
  if prior.get('status')=='PUBLISHED_AND_VIEWER_VERIFIED':
   import urllib.request
   url=prior.get('viewerURL');require(url,'PRIOR_COMPLETE_MISSING_URL')
   try:
    with urllib.request.urlopen(url.replace('index.html?','health?'),timeout=3) as response:
     active=json.loads(response.read());require(active['buildToken']==prior['buildToken'],'STALE_VIEWER_IN_REUSABLE_RECEIPT')
    print('REUSED_VERIFIED_VIEWER_URL='+url,flush=True)
    print('STATUS=PUBLISHED_AND_VIEWER_VERIFIED',flush=True)
    raise SystemExit(0)
   except (OSError,KeyError,ValueError,RuntimeError):pass
   resume_published=True
   print('RECOVERING_VIEWER_SERVER_WITHOUT_REPUBLISHING_IMMUTABLE_EVIDENCE',flush=True)
 state['runId']=prior.get('runId') if receipt.exists() else datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 stage('CHECKOUT_PINNED_GIT_MAIN')
 # Reuse vetted Git functions from the repo's immutable existing source, not a new Git architecture.
 boot=pathlib.Path(root/'checkout')
 repo=boot/'repo'
 if not repo.is_dir():
  boot.mkdir(parents=True,exist_ok=True)
  env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
  clone=subprocess.run(['git','clone','--quiet','--depth=1','--branch=main','--single-branch','https://github.com/'+REPO+'.git',str(repo)],env=env,capture_output=True,text=True,timeout=1200)
  require(clone.returncode==0,'VERIFIED_GIT_CLONE_FAILED_'+clone.stderr[-800:])
 old=import_path(repo/'campaigns/MUDMAN_ARES_FULL_RETARGET_v2.0.22_driver.py','mudman_prior_git_v224')
 prior_driver=import_path(repo/('campaigns/'+PREV+'_driver.py'),'mudman_v23_driver_v224')
 v13=import_path(repo/'campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py','mudman_v13_viewer_v224')
 require(old.REMOTE=='https://github.com/'+REPO+'.git' and old.AGENTS==AGENTS_BLOB and old.CANON==CANON_SHA,'REPO_HELPER_AUTHORITY_CHANGED')
 require(old.g(repo,'remote','get-url','origin')=='https://github.com/'+REPO+'.git','WRONG_GIT_REMOTE')
 require(not old.g(repo,'status','--porcelain'),'ISOLATED_CHECKOUT_DIRTY')
 head=old.g(repo,'rev-parse','HEAD')
 proof=old.verify_pinned_ancestry(repo,BASE_COMMIT,head)
 for path,blob in [(PREV_VIEW,PREV_VIEW_BLOB),(PREV_CONTRACT,PREV_CONTRACT_BLOB),(PREV_EVIDENCE,PREV_EVIDENCE_BLOB),('AGENTS.md',AGENTS_BLOB)]:
  require(old.g(repo,'rev-parse','HEAD:'+path)==blob,'VERIFIED_SOURCE_BLOB_CHANGED_'+path)
 require('oid sha256:'+CANON_SHA in old.git(repo,'show','HEAD:assets/obsidianti/Obsidianti.glb').stdout,'CANONICAL_OBSIDIANTI_CHANGED')
 require('oid sha256:'+PREV_GLBSHA in old.git(repo,'show','HEAD:'+PREV_RESULT).stdout,'PREVIOUS_APPROVED_REVIEW_GLB_POINTER_CHANGED')
 state['sourceBaseGitHead']=head;state['gitAncestryProof']=proof
 locked=prior_driver.LOCKED
 protected={p:old.g(repo,'rev-parse','HEAD:'+p) for p in locked}
 stage('LOCATE_OR_RESTORE_IDENTICAL_CURATED_GLB')
 downloads=pathlib.Path.home()/'storage/downloads';require(downloads.is_dir(),'ANDROID_DOWNLOADS_MISSING')
 expected_name=PREV+'_'+'20261107T143456Z-5a637cc3'+'_REVIEW.glb'
 candidates=[downloads/expected_name,root/expected_name]
 model=next((p for p in candidates if p.is_file() and not p.is_symlink() and digest(p)==PREV_GLBSHA),None)
 if model is None:
  old.hydrate(repo,{PREV_RESULT:PREV_GLBSHA})
  model=repo/PREV_RESULT
 require(digest(model)==PREV_GLBSHA,'REAL_GLTF_SHA_NOT_ORIGINAL_23_CLIP_MODEL')
 contract=json.loads((repo/PREV_CONTRACT).read_text())
 expected=contract['gravityFistGodotSource']['expectedStates']
 names=glb_names(model)
 require(len(names)==len(expected)==23 and set(names)==set(expected),'ACTUAL_GLTF_CLIP_NAMES_DEVIATE_FROM_GODOT_CONTRACT')
 state.update({'inputGLBSHA256':PREV_GLBSHA,'inputGLBPath':str(model),'clipCount':23,'protectedBefore':protected})
 stage('GENERATE_EXACT_NAME_VIEWER_AND_EXECUTE_JS_TESTS')
 viewer=patch_viewer((repo/PREV_VIEW).read_text())
 picker_test=test_picker(viewer,names)
 server_src=(repo/PREV_SERVER).read_text()
 require(server_src.count('MudmanGodotCuratedViewer/2.0.23')==1,'PRIOR_SERVER_VERSION_UNEXPECTED')
 server_new=server_src.replace('MudmanGodotCuratedViewer/2.0.23','MudmanGodotCuratedViewer/2.0.24')
 doc={'schema':V,'authority':'TERMUX_GIT_ONLY','mission':'Repair StandUp vs ProneBackStandUp ambiguous viewer selection with exact names; preserve the published v2.0.23 curated GLB unchanged',
  'sourceGitBaseCommit':BASE_COMMIT,'sourceGitHead':head,'rulesBlob':AGENTS_BLOB,'previousViewerGitBlob':PREV_VIEW_BLOB,
  'sourceGLBSHA256':PREV_GLBSHA,'canonicalObsidiantiSHA256':CANON_SHA,'viewerSelection':'STRICT_EXACT_NAME_UNIQUE',
  'noBlender':True,'noAnimationReexport':True,'modelMutationAllowed':False,'ownerVisualAcceptanceRequired':True}
 artifacts=root/'source';artifacts.mkdir(exist_ok=True)
 (artifacts/'viewer.html').write_text(viewer)
 (artifacts/'server.py').write_text(server_new)
 (artifacts/'contract.json').write_text(json.dumps(doc,indent=2)+'\n')
 (artifacts/'test.js').write_text(picker_test)
 sources={ROOT+'_LAUNCH.sh':script,ROOT+'_viewer.html':artifacts/'viewer.html',ROOT+'_server.py':artifacts/'server.py',
          ROOT+'.contract.json':artifacts/'contract.json','tests/'+V+'_TEST.js':artifacts/'test.js'}
 stage('TERMUX_GIT_SOURCE_COMMIT_AND_REMOTE_READBACK')
 if resume_published:
  for path,file in sources.items():require((repo/path).is_file() and digest(repo/path)==digest(file),'RESUME_SOURCE_DIFFERS_FROM_PUBLISHED_'+path)
  source_commit=prior['sourceGitCommit']
 else:
  source_commit=prior_driver.commit_stage(old,repo,sources,'Mudman: StandUp exact viewer selection SOURCE',protected)
 state['sourceGitCommit']=source_commit
 # New immutable viewer build, same exact GLB, fresh server identity and URL.
 v13.V=V
 token=hashlib.sha256((V+state['runId']+claimed_sha+source_commit+PREV_GLBSHA+digest(repo/(ROOT+'_viewer.html'))).encode()).hexdigest()[:24]
 viewer_meta={'schema':V,'runId':state['runId'],'buildToken':token,'launcherSHA256':claimed_sha,'sourceCommit':source_commit,
              'htmlPath':str(repo/(ROOT+'_viewer.html')),'modelPaths':{'candidate':str(model)},
              'models':{'candidate':{'sha256':PREV_GLBSHA,'bytes':model.stat().st_size,'url':'/models/candidate.glb','animations':names}},
              'canonicalModelSHA256':CANON_SHA,'mode':'EXACT_SELECTION_23_CLIP_GODOT_CURATED_UNMODIFIED_MODEL'}
 stage('FRESH_NO_CACHE_MODEL_VIEWER')
 viewerroot=root/'viewer';viewerroot.mkdir(exist_ok=True)
 ticket=v13.start_server(viewerroot,repo,viewer_meta)
 state['viewerURL']=ticket['url'];state['buildToken']=token;state['viewerPID']=ticket['pid'];state['viewerPort']=ticket['port']
 stage('HTTP_AND_SHA_VERIFIED')
 print('VIEWER_URL='+ticket['url'],flush=True)
 print('BROWSER_OPEN_INTENT_SENT='+str(v13.open_browser(ticket['url'])).upper(),flush=True)
 evidence={'schema':V,'authority':'TERMUX_GIT_ONLY','runId':state['runId'],'sourceCommit':source_commit,'rulesBlob':AGENTS_BLOB,
  'gitSourceBase':head,'inputGLBSHA256':PREV_GLBSHA,'outputGLBSHA256':PREV_GLBSHA,'modelBytes':model.stat().st_size,
  'modelModified':False,'animationKeyframesModified':False,'meshAndTextureModified':False,'viewerSelection':'EXACT_UNIQUE',
  'testedAnimations':names,'bugRegression':['StandUp vs ProneBackStandUp','all 23 exact names','missing name','duplicate name'],
  'viewerURL':ticket['url'],'viewerHTTPVerified':True,'serverPID':ticket['pid'],'buildToken':token,
  'protectedBefore':protected,'protectedAfter':{p:old.g(repo,'rev-parse','HEAD:'+p) for p in locked},
  'ownerVisualAcceptance':'PENDING'}
 require(evidence['protectedBefore']==evidence['protectedAfter'],'PROTECTED_MODEL_OR_ANIMATION_CHANGED')
 evidence_dir='diagnostics/mudman/godot-curated-viewer-v2.0.24/runs/'+state['runId']+'/'
 report=(root/'REPORT.md');report.write_text('# Mudman StandUp viewer fix v2.0.24\n\nOriginal curated GLB SHA-256 `'+PREV_GLBSHA+'` was served unchanged.\n\n'
        'Original viewer incorrectly matched StandUp and ProneBackStandUp using suffix search. New viewer requires exactly one full-name match, tested on actual GLB list of 23 actions.\n\n'
        'Texture, grounded origin, meshes, skeleton, and animation keyframes have not been changed.\n\n'
        'Viewer: '+ticket['url']+'\n\n**Owner visual acceptance PENDING**.\n')
 save(root/'EVIDENCE.json',evidence)
 if resume_published:
  state['evidenceGitCommit']=prior['evidenceGitCommit']
  state['status']='PUBLISHED_AND_VIEWER_VERIFIED'
  stage('PUBLISHED_AND_VIEWER_VERIFIED')
  print('VIEWER_RESTARTED=YES; PRIOR_GIT_EVIDENCE_UNCHANGED='+state['evidenceGitCommit'],flush=True)
  print('VIEWER_URL='+ticket['url'],flush=True)
  raise SystemExit(0)
 stage('TERMUX_GIT_EVIDENCE_COMMIT_AND_REMOTE_READBACK')
 evidence_commit=prior_driver.commit_stage(old,repo,{evidence_dir+'REPORT.md':report,evidence_dir+'EVIDENCE.json':root/'EVIDENCE.json'},'Mudman: StandUp exact viewer selection EVIDENCE',protected)
 state['evidenceGitCommit']=evidence_commit
 state['status']='PUBLISHED_AND_VIEWER_VERIFIED'
 stage('PUBLISHED_AND_VIEWER_VERIFIED')
 print('MODEL_UNCHANGED=YES SHA256='+PREV_GLBSHA,flush=True)
 print('GIT_EVIDENCE_COMMIT='+evidence_commit,flush=True)
 print('VIEWER_URL='+ticket['url'],flush=True)
 print('STATUS='+state['status'],flush=True)
except SystemExit:
 raise
except BaseException as ex:
 state['status']='BLOCKED';state['error']=str(ex)[:1100];state['traceback']=traceback.format_exc()[-2400:]
 save(receipt,state)
 print('STATUS=BLOCKED '+str(ex)[:1100],flush=True)
 raise
finally:
 print('RECEIPT='+str(receipt),flush=True)
PY
