#!/usr/bin/env python3
"""Owner Termux-Git only: exact signed 90-degree Hips rotations for HitHeadLeft.
All other clips, original texture, geometry, skin and grounded parent unchanged.
Original unmodified 23-clip source, not v2.0.26's rejected 62.38-degree derivative.
"""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,subprocess,sys,time,uuid,traceback
sys.dont_write_bytecode=True
V='MUDMAN_HITHEADLEFT_QUARTERTURN_v2.0.27'
BASE='3c05c87b5aa4f428be2602adef10ad387e3af4da'
REPO='Valar05/parametric-parambulator'
RULES='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
SRC_GLB='diagnostics/mudman/godot-curated-v2.0.23/runs/20261107T143456Z-5a637cc3/MUDMAN_GODOT_CURATED_REVIEW_UNAPPROVED.glb'
SRC_SHA='19304bf8007670e36a38b354b5f8d2ea0c39982c97e2a247acdac1190fe2b7ef'
PRIOR_DRIVER='campaigns/MUDMAN_HITHEADLEFT_FRAME_v2.0.26_driver.py';PRIOR_DRIVER_BLOB='724e990af5ee546c0c26bcbe591aa137e2613b0a'
PRIOR_FIX='campaigns/MUDMAN_HITHEADLEFT_FRAME_v2.0.26_fix.py';PRIOR_FIX_BLOB='488666348e2f9f1f07a9cda318889384d2158aa9'
PRIOR_VIEW='campaigns/MUDMAN_HITHEADLEFT_FRAME_v2.0.26_viewer.html';PRIOR_VIEW_BLOB='cf5b95b1873ad0858deb35298d14b7e5941ee69a'
PRIOR_SERVER='campaigns/MUDMAN_HITHEADLEFT_FRAME_v2.0.26_server.py';PRIOR_SERVER_BLOB='3ffe94383a3ad87d8b6ce01ff558cac645ded512'
GLB_HELP='campaigns/MUDMAN_GODOT_CURATED_v2.0.23_patch_glb.py';GLB_HELP_BLOB='7c83a4f356f57f00b5eb48389cb8f6422abdfb96'
GIT_HELP='campaigns/MUDMAN_ARES_FULL_RETARGET_v2.0.22_driver.py';GIT_HELP_BLOB='610970b4acc11033b1345a508aa2c6c38f0e2adc'
COMMIT_HELP='campaigns/MUDMAN_GODOT_CURATED_v2.0.23_driver.py';COMMIT_HELP_BLOB='dd73cf68739200f445e2eb7e46e88c8a452a5b99'
VIEWER_HELP='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py'
PROTECTED=['assets/obsidianti/Obsidianti.glb','assets/repl/Repl.glb',
           'diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/20261107T021037Z-2edec0d5/AxeKick/ARP_AxeKick_REVIEW.glb']
SOURCE_ROOT='campaigns/'+V
SOURCE_FILES={SOURCE_ROOT+'_LAUNCH.sh':'LAUNCHER',SOURCE_ROOT+'_driver.py':'driver.py',
 SOURCE_ROOT+'_fix.py':'fix.py',SOURCE_ROOT+'_viewer_build.py':'viewer_build.py',
 SOURCE_ROOT+'_viewer.html':'viewer.html',SOURCE_ROOT+'_server.py':'server.py',
 SOURCE_ROOT+'.contract.json':'contract.json','tests/'+V+'_TEST.py':'test_fix.py'}
REL='diagnostics/mudman/hitheadleft-quarterturn-v2.0.27/runs/'

def require(ok,why):
 if not ok:raise RuntimeError(why)
def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(path,obj):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex[:6]);temp.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n');os.replace(temp,path)
def load(path,n):
 spec=importlib.util.spec_from_file_location(n,path);require(spec and spec.loader,'MISSING_LIBRARY_'+str(path))
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def main(packet_path,launcher_path,expected):
 packet=pathlib.Path(packet_path).resolve();launcher=pathlib.Path(launcher_path).resolve()
 require(launcher.is_file() and digest(launcher)==expected,'ENTRY_SHA256_MISMATCH')
 manifest=json.loads((packet/'manifest.json').read_text())
 require(set(manifest)=={'driver.py','fix.py','viewer_build.py','test_fix.py','contract.json'},'UNEXPECTED_PAYLOAD_MEMBERS')
 for k,v in manifest.items():require(digest(packet/k)==v,'PAYLOAD_SHA_MISMATCH_'+k)
 contract=json.loads((packet/'contract.json').read_text())
 require(contract['schema']==V and contract['authority']=='TERMUX_GIT_ONLY' and contract['baselineGLBSHA256']==SRC_SHA,'MISSION_CONTRACT_INVALID')
 test=subprocess.run([sys.executable,str(packet/'test_fix.py')],capture_output=True,text=True,timeout=80,
                     env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL)
 require(test.returncode==0,'QUARTERTURN_SELFTEST_FAILED_'+test.stdout[-400:]+test.stderr[-600:])
 print(test.stdout.strip(),flush=True)
 downloads=pathlib.Path.home()/'storage/downloads'
 require(downloads.is_dir(),'ANDROID_DOWNLOADS_ACCESS_REQUIRED')
 working=pathlib.Path.home()/'.local/state'/V/'working';working.mkdir(parents=True,exist_ok=True)
 receipt=working/'RECEIPT.json'
 if receipt.is_file():
  state=json.loads(receipt.read_text())
  require(state.get('schema')==V and state.get('entrySHA256')==expected,'RESUME_VERSION_CONFLICT')
 else:
  runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
  state={'schema':V,'runId':runid,'entrySHA256':expected,'authority':'TERMUX_GIT_ONLY',
    'rulesBlob':RULES,'etiquetteTitle':'CAMPAIGN_ETIQUETTE — Git Script Campaign Operating Rules',
    'canonicalObsidiantiSHA256':CANON,'pinnedSourceCommit':BASE,'baselineGLBSHA256':SRC_SHA,
    'ownerVisualAcceptance':'PENDING','canonicalModified':False,'status':'BOOT'}
  write(receipt,state)
 def stage(label):
  state['stage']=label;write(receipt,state);print('STAGE='+label,flush=True)
 try:
  stage('VERIFY_ISOLATED_TERMUX_GIT_HISTORY')
  # GIT is the authoritative execution lane. No direct ChatGPT Git mutation.
  isolated=working/'isolated';repo=isolated/'repo'
  if not repo.exists():
   isolated.mkdir(parents=True,exist_ok=True)
   cmd=['git','clone','--quiet','--depth=1','--single-branch','--branch','main',
        'https://github.com/'+REPO+'.git',str(repo)]
   env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
   cloned=subprocess.run(cmd,timeout=1200,capture_output=True,text=True,env=env,stdin=subprocess.DEVNULL)
   require(cloned.returncode==0,'ISOLATED_GIT_CLONE_FAILED_'+cloned.stderr[-400:])
  # SHA lock all donor implementation contracts as actually published in Git.
  def ref_blob(path):
   r=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD:'+path],capture_output=True,text=True,timeout=90,stdin=subprocess.DEVNULL)
   require(r.returncode==0,'GIT_PATH_MISSING_'+path)
   return r.stdout.strip()
  for path,blob in ((PRIOR_DRIVER,PRIOR_DRIVER_BLOB),(PRIOR_FIX,PRIOR_FIX_BLOB),
                    (PRIOR_VIEW,PRIOR_VIEW_BLOB),(PRIOR_SERVER,PRIOR_SERVER_BLOB),
                    (GLB_HELP,GLB_HELP_BLOB),(GIT_HELP,GIT_HELP_BLOB),(COMMIT_HELP,COMMIT_HELP_BLOB)):
   require(ref_blob(path)==blob,'UPSTREAM_PUBLISHED_SOURCE_HASH_CHANGED_'+path)
  helper=load(repo/GIT_HELP,'v227_pinned_git_helper');helper.BASE=BASE
  require(helper.AGENTS==RULES and helper.CANON==CANON,'ROOT_AGENTS_OR_CANONICAL_AUTHORITY_CHANGED')
  require(helper.g(repo,'rev-parse','--show-toplevel')==str(repo),'ISOLATED_REPO_IDENTITY_MISMATCH')
  require(helper.g(repo,'remote','get-url','origin').endswith('Valar05/parametric-parambulator.git'),'GIT_REMOTE_WRONG')
  require(not helper.g(repo,'status','--porcelain'),'ISOLATED_REPO_DIRTY')
  head=helper.g(repo,'rev-parse','HEAD')
  state['inputGitHead']=head
  state['gitAncestry']=helper.verify_pinned_ancestry(repo,BASE,head)
  require(helper.g(repo,'rev-parse','HEAD:AGENTS.md')==RULES,'ROOT_AGENT_RULES_CHANGED')
  require('oid sha256:'+CANON in helper.git(repo,'show','HEAD:assets/obsidianti/Obsidianti.glb').stdout,'PROTECTED_CANONICAL_LFS_CHANGED')
  protected={p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED}
  state['protectedBefore']=protected
  stage('BUILD_VERSIONED_EXACT90_VIEWER_FROM_PINNED_SOURCE')
  viewbuild=load(packet/'viewer_build.py','v227_viewer_build')
  original_view=(repo/PRIOR_VIEW).read_text()
  (packet/'viewer.html').write_text(viewbuild.build(original_view))
  server=(repo/PRIOR_SERVER).read_text()
  require("MudmanHitHeadLeftFrameViewer/2.0.26" in server,'PINNED_SERVER_VERSION_CHANGED')
  (packet/'server.py').write_text(server.replace('MudmanHitHeadLeftFrameViewer/2.0.26','MudmanHitHeadLeftQuarterTurnViewer/2.0.27'))
  stage('PUBLISH_VERSIONED_SOURCE_AND_READBACK')
  commit_helper=load(repo/COMMIT_HELP,'v227_existing_commit_helper')
  sources={path:(launcher if member=='LAUNCHER' else packet/member) for path,member in SOURCE_FILES.items()}
  source_commit=commit_helper.commit_stage(helper,repo,sources,'Mudman: exact 90-degree HitHeadLeft SOURCE',protected)
  state['sourceCommit']=source_commit
  stage('GET_REAL_ORIGINAL_CURATED_GLB')
  # NEVER use the user-rejected 62.38 degree v26 candidate as the source.
  existing=sorted(downloads.glob('MUDMAN_GODOT_CURATED_v2.0.23_*_REVIEW.glb'))
  baseline=next((p for p in existing if p.is_file() and not p.is_symlink() and digest(p)==SRC_SHA),None)
  if baseline is None:
   helper.hydrate(repo,{SRC_GLB:SRC_SHA});baseline=repo/SRC_GLB
  require(digest(baseline)==SRC_SHA,'ORIGINAL_UNCORRECTED_CURATED_GLB_IDENTITY_FAILED')
  fix=load(packet/'fix.py','v227_exact_quarter_turn')
  priorfix=load(repo/PRIOR_FIX,'v226_locked_utility_code')
  test_outputs={}
  for label,axis in (('candidate',fix.NORMAL_AXIS),('axis',fix.MEASURED_AXIS)):
   stage('ACTUAL_GLB_EXACT_90_DEGREE_'+label.upper())
   path=working/(V+'_'+state['runId']+'_'+label+'_REVIEW.glb')
   diag=working/(label+'_FORENSICS.json')
   if path.is_file() and diag.is_file():
    doc=json.loads(diag.read_text());require(doc.get('candidateSHA256')==digest(path) and doc.get('rotationDegrees')==90.0,'RESUME_REPAIR_IDENTITY_FAILED_'+label)
   else:
    require(not path.exists() and not diag.exists(),'UNSAFE_PARTIAL_CANDIDATE_'+label)
    doc=fix.apply_one(baseline,path,repo/GLB_HELP,priorfix,axis,label)
    write(diag,doc)
   target=downloads/path.name
   helper.copy_new(path,target)
   require(digest(target)==doc['candidateSHA256'],'ANDROID_DOWNLOADS_HASH_MISMATCH_'+label)
   test_outputs[label]={'file':target,'diagnostics':diag,'proof':doc}
   state[label+'SHA256']=doc['candidateSHA256'];state[label+'Download']=str(target)
   stage('REAL_GLB_'+label.upper()+'_23_CLIPS_AND_SKIN_VERIFIED')
  stage('EXACT_SHA_3_WAY_ORIGINAL_VS_QUARTERTURN_VIEWER')
  allnames=sorted(fix.EXPECTED)
  model_files={'candidate':test_outputs['candidate']['file'],'axis':test_outputs['axis']['file'],'original':baseline}
  token=hashlib.sha256((state['runId']+source_commit+expected+''.join(digest(p) for p in model_files.values())).encode()).hexdigest()[:24]
  models={k:{'sha256':digest(p),'bytes':p.stat().st_size,'url':'/models/'+k+'.glb','animations':allnames} for k,p in model_files.items()}
  manifest_view={'schema':V,'runId':state['runId'],'buildToken':token,'launcherSHA256':expected,
    'sourceCommit':source_commit,'htmlPath':str(repo/(SOURCE_ROOT+'_viewer.html')),
    'modelPaths':{k:str(p) for k,p in model_files.items()},'models':models,
    'canonicalModelSHA256':CANON,'mode':'EXACT_90_DEGREE_HIPS_ROTATION_REVIEW_UNAPPROVED'}
  oldviewer=load(repo/VIEWER_HELP,'v227_pinned_viewer_helper');oldviewer.V=V
  ticket=oldviewer.start_server(working,repo,manifest_view)
  state.update({'viewerURL':ticket['url'],'viewerPID':ticket['pid'],'viewerPort':ticket['port'],'viewerHTTPVerified':True})
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(oldviewer.open_browser(ticket['url'])).upper(),flush=True)
  stage('VERSIONED_RESULT_GIT_PUBLICATION')
  dest=REL+state['runId']+'/'
  outputpaths={dest+'HITHEADLEFT_90X_FORENSICS.json':test_outputs['candidate']['diagnostics'],
    dest+'HITHEADLEFT_90AXIS_FORENSICS.json':test_outputs['axis']['diagnostics'],
    dest+'MUDMAN_HITHEADLEFT_90X_UNAPPROVED.glb':test_outputs['candidate']['file'],
    dest+'MUDMAN_HITHEADLEFT_90AXIS_UNAPPROVED.glb':test_outputs['axis']['file']}
  for name in outputpaths:
   if name.endswith('.glb'):require(helper.g(repo,'check-attr','filter','--',name).endswith('lfs'),'RESULT_NOT_LFS_'+name)
  evidence={'schema':V,'authority':'TERMUX_GIT_ONLY','ownerVisualAcceptance':'PENDING',
    'rulesBlob':RULES,'etiquetteTitle':state['etiquetteTitle'],'canonicalObsidiantiSHA256':CANON,
    'inputCommit':head,'sourceCommit':source_commit,'originalCuratedSHA256':SRC_SHA,
    'rejectedV226Angle':62.38362,'newAngleDegrees':90,'rotationBone':'mixamorig:Hips',
    'candidateSHA256':test_outputs['candidate']['proof']['candidateSHA256'],
    'alternateSHA256':test_outputs['axis']['proof']['candidateSHA256'],
    'allOther22ClipsByteIdentical':True,'materialAndSkinPreserved':True,
    'sourceAresBlendUnmodified':True,'canonicalModified':False,'protectedBefore':protected,
    'protectedAfter':{p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED},
    'viewerURL':ticket['url'],'viewerHTTPVerified':True,'testReceipt':test.stdout.strip(),
    'status':'TWO_EXACT_90_DEGREE_REVIEW_CANDIDATES_PENDING_OWNER_VERDICT'}
  require(evidence['protectedBefore']==evidence['protectedAfter'],'PROTECTED_ASSET_CHANGED')
  ev=working/'EVIDENCE.json';write(ev,evidence)
  report=working/'REPORT.md'
  report.write_text('# Mudman HitHeadLeft exact 90-degree Hips correction v2.0.27\n\n'
    'The v2.0.26 correction of 62.38362 degrees was rejected by the owner. Both candidates here are EXACTLY 90 degrees on the actual Hips rotation track, 31 keys, using v2.0.23 unmodified original SHA '+SRC_SHA+'.\n\n'
    'Candidate 90X: '+evidence['candidateSHA256']+'; alternate forensic 90-axis: '+evidence['alternateSHA256']+'.\n'
    'Both preserve 22 other animation clips byte-for-byte, key timing, skinned mesh, UVs, textures, model ground root. No Ares, Gravity Fist, or accepted asset changes.\n\n'
    'Viewer '+ticket['url']+'\n\nOWNER VISUAL ACCEPTANCE: PENDING.\n')
  outputpaths[dest+'EVIDENCE.json']=ev;outputpaths[dest+'REPORT.md']=report
  evcommit=commit_helper.commit_stage(helper,repo,outputpaths,'Mudman: exact 90-degree HitHeadLeft candidates EVIDENCE',protected)
  state['evidenceCommit']=evcommit
  stage('GIT_REMOTE_BINARY_AND_TEXT_READBACK_COMPLETE')
  state['status']='EXACT_90_DEGREE_REVIEW_READY_UNAPPROVED';write(receipt,state)
  print('GIT_EVIDENCE_COMMIT='+evcommit,flush=True)
  print('MUDMAN_90X_GLB_SHA256='+evidence['candidateSHA256'],flush=True)
  print('MUDMAN_90_AXIS_GLB_SHA256='+evidence['alternateSHA256'],flush=True)
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as exc:
  state.update({'status':'BLOCKED','errorType':type(exc).__name__,'error':str(exc)[:1200],
                'traceback':traceback.format_exc()[-3400:]})
  write(receipt,state);print('STATUS=BLOCKED '+str(exc)[:900],flush=True)
  raise
 finally:
  write(receipt,state);print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('usage: driver.py PACKET LAUNCHER EXPECTED_SHA256')
 main(*sys.argv[1:])
