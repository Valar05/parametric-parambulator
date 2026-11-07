#!/usr/bin/env python3
"""Termux Git-only campaign: forensics-guided repair of a single mudman GLB clip.
Source/asset checkout, world-frame analysis, modification, evidence and model all
executed within the authorized owner phone Git lane. User review is separate.
"""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,time,uuid,traceback
sys.dont_write_bytecode=True
V='MUDMAN_HITHEADLEFT_FRAME_v2.0.26'
BASE='837180b94b8405e35c0a5c6e8438cc9a474b3870'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
SRC_GLB='diagnostics/mudman/godot-curated-v2.0.23/runs/20261107T143456Z-5a637cc3/MUDMAN_GODOT_CURATED_REVIEW_UNAPPROVED.glb'
SRC_SHA='19304bf8007670e36a38b354b5f8d2ea0c39982c97e2a247acdac1190fe2b7ef'
V24_VIEW='campaigns/MUDMAN_STANDUP_EXACT_SELECTION_v2.0.24_viewer.html';V24_VIEW_BLOB='dacaa916cfba2a3e2e0764083ab629714db28d7b'
V24_SERVER='campaigns/MUDMAN_STANDUP_EXACT_SELECTION_v2.0.24_server.py';V24_SERVER_BLOB='b5fc306e7652fb1cfe12f35b991c06d00800e11f'
V23_BASE='campaigns/MUDMAN_GODOT_CURATED_v2.0.23_patch_glb.py';V23_BASE_BLOB='7c83a4f356f57f00b5eb48389cb8f6422abdfb96'
V23_DRIVER='campaigns/MUDMAN_GODOT_CURATED_v2.0.23_driver.py';V23_DRIVER_BLOB='dd73cf68739200f445e2eb7e46e88c8a452a5b99'
V22_HELPER='campaigns/MUDMAN_ARES_FULL_RETARGET_v2.0.22_driver.py';V22_HELPER_BLOB='610970b4acc11033b1345a508aa2c6c38f0e2adc'
PROTECTED=['assets/obsidianti/Obsidianti.glb','assets/repl/Repl.glb',
           'diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/20261107T021037Z-2edec0d5/AxeKick/ARP_AxeKick_REVIEW.glb']
SRC='campaigns/'+V
REL='diagnostics/mudman/hitheadleft-frame-v2.0.26/runs/'
SOURCES={SRC+'_LAUNCH.sh':'LAUNCHER',SRC+'_driver.py':'driver.py',SRC+'_fix.py':'fix.py',
         SRC+'_viewer_build.py':'viewer_build.py',SRC+'_viewer.html':'viewer.html',
         SRC+'_server.py':'server.py',SRC+'.contract.json':'contract.json',
         'tests/'+V+'_TEST.py':'test_fix.py'}

def require(x,msg):
 if not x:raise RuntimeError(msg)
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write_json(path,obj):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex[:6]+'.tmp');tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');os.replace(tmp,path)
def load_module(p,n):
 spec=importlib.util.spec_from_file_location(n,p);require(spec and spec.loader,'PYTHON_IMPORT_NOT_FOUND_'+str(p));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def main(packet_path,launcher_path,expected):
 packet=pathlib.Path(packet_path).resolve();launcher=pathlib.Path(launcher_path).resolve()
 require(launcher.is_file() and digest(launcher)==expected,'ENTRY_SCRIPT_SHA_CHANGED')
 mf=json.loads((packet/'manifest.json').read_text());required={'driver.py','fix.py','viewer_build.py','test_fix.py','contract.json','base_glb.py','v22_helpers.py'}
 require(set(mf)==required,'PACKET_MEMBERS_CHANGED')
 for fn,d in mf.items():require(digest(packet/fn)==d,'SHA_CHANGED_IN_PACKET_'+fn)
 contract=json.loads((packet/'contract.json').read_text())
 require(contract.get('schema')==V and contract.get('authority')=='TERMUX_GIT_ONLY' and contract.get('sourceReviewGLBSHA256')==SRC_SHA,'INVALID_USER_MISSION_CONTRACT')
 require(contract.get('sourceAction')=='HitHeadLeft' and set(contract.get('comparisonClips',[]))=={'Idle-Cross','HitHeadRightBig'},'MOTION_SCOPE_CHANGED')
 # Independent provenance gates for both vendored, immutable, prior published helpers.
 import hashlib as _hashlib
 for fn,blob in (('v22_helpers.py',V22_HELPER_BLOB),('base_glb.py',V23_BASE_BLOB)):
  b=(packet/fn).read_bytes();git_blob=_hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
  require(git_blob==blob,'IMMUTABLE_HELPER_SOURCE_BLOB_CHANGED_'+fn)
 # Deterministic tests before touching Git or persistent assets.
 p=subprocess.run([sys.executable,str(packet/'test_fix.py')],capture_output=True,text=True,
                  timeout=200,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL)
 require(p.returncode==0,'REPAIR_TEST_FAILURE_'+p.stdout[-600:]+p.stderr[-800:])
 print(p.stdout.strip(),flush=True)
 downloads=pathlib.Path.home()/'storage/downloads';require(downloads.is_dir(),'ANDROID_DOWNLOADS_NOT_AVAILABLE')
 root=pathlib.Path.home()/'.local/state'/V/'working';root.mkdir(parents=True,exist_ok=True)
 receipt=root/'RECEIPT.json'
 if receipt.exists():
  state=json.loads(receipt.read_text());require(state.get('schema')==V and state.get('launcherSHA256')==expected,'RESUME_VERSION_OR_IDENTITY_MISMATCH')
 else:
  runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
  state={'schema':V,'runId':runid,'authority':'TERMUX_GIT_ONLY','launcherSHA256':expected,
         'status':'BOOT','rulesBlob':AGENTS,'canonicalObsidiantiSHA256':CANON,
         'sourceReviewSHA256':SRC_SHA,'otherAnimationsLocked':22,'userApprovedPosesPreserved':True,
         'ownerVisualAcceptance':'PENDING','canonicalModified':False,'arpRerun':False}
  write_json(receipt,state)
 def stage(name):
  state['stage']=name;write_json(receipt,state);print('STAGE='+name,flush=True)
 helper=load_module(packet/'v22_helpers.py','mudman_v226_prior_git_helpers')
 helper.BASE=BASE
 require(helper.AGENTS==AGENTS and helper.CANON==CANON,'OWNER_RULES_OR_CANON_MISMATCH')
 try:
  stage('ISOLATED_TERMUX_GIT_BOOT')
  rd=root/'checkout';repo=rd/'repo'
  if repo.is_dir():
   require(helper.g(repo,'rev-parse','--show-toplevel')==str(repo),'WORKING_REPO_PATH_MISMATCH')
   require(not helper.g(repo,'status','--porcelain'),'ISOLATED_RESUME_REPO_DIRTY')
   require(helper.g(repo,'remote','get-url','origin').endswith('Valar05/parametric-parambulator.git'),'WRONG_REMOTE_ON_RESUME')
   head=helper.g(repo,'rev-parse','HEAD')
   proof=helper.verify_pinned_ancestry(repo,BASE,head)
  else:
   rd.mkdir(parents=True,exist_ok=True)
   repo,head,proof=helper.checkout(rd)
  require(helper.g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'RULES_READ_BLOCKED_AGENT_POLICY_ADVANCED')
  require('oid sha256:'+CANON in helper.git(repo,'show','HEAD:assets/obsidianti/Obsidianti.glb').stdout,'CANONICAL_HASH_OR_LFS_POINTER_CHANGED')
  for path,expected_blob in ((V24_VIEW,V24_VIEW_BLOB),(V24_SERVER,V24_SERVER_BLOB),(V23_BASE,V23_BASE_BLOB),(V23_DRIVER,V23_DRIVER_BLOB),(V22_HELPER,V22_HELPER_BLOB)):
   require(helper.g(repo,'rev-parse','HEAD:'+path)==expected_blob,'PREVIOUS_SOURCE_DRIFT_'+path)
  state['baseGitHead']=head;state['historyProof']=proof
  protected={n:helper.g(repo,'rev-parse','HEAD:'+n) for n in PROTECTED};state['protectedGitBlobsBefore']=protected
  stage('PREPARE_EXISTING_VIEWER_WITH_WORLD_FRAME_AB_COMPARISON')
  viewer_builder=load_module(packet/'viewer_build.py','mudman_viewer_builder_v226')
  text=viewer_builder.build((repo/V24_VIEW).read_text())
  (packet/'viewer.html').write_text(text)
  server=(repo/V24_SERVER).read_text()
  # Version-specific server identity, no server route or cache policy changes.
  old_version='MudmanStandUpExactViewer/2.0.24'
  if old_version not in server:
   # Probe exact server_version from pinned source in a bounded way.
   import re
   m=re.search("server_version='([^']+)'",server)
   require(m is not None and m.group(1).endswith('/2.0.24'),'SERVER_TEMPLATE_IDENTITY_DRIFT')
   old_version=m.group(1)
  server=server.replace(old_version,'MudmanHitHeadLeftFrameViewer/2.0.26')
  (packet/'server.py').write_text(server)
  # Preserve existing source policy, no incidental change in old code.
  v23driver=load_module(repo/V23_DRIVER,'mudman_v223_publish_helper')
  sources={path:(launcher if member=='LAUNCHER' else packet/member) for path,member in SOURCES.items()}
  stage('VERSIONED_GIT_SOURCE_COMMIT')
  if state.get('sourceCommit'):
   require(helper.g(repo,'rev-parse','HEAD')==state['sourceCommit'] or helper.g(repo,'cat-file','-t',state['sourceCommit'])=='commit','SOURCE_COMMIT_RESUME_MISSING')
   source_commit=state['sourceCommit']
  else:
   source_commit=v23driver.commit_stage(helper,repo,sources,'Mudman: measured HitHeadLeft torso-frame root repair SOURCE',protected)
   state['sourceCommit']=source_commit
  stage('SOURCE_GIT_REMOTE_READBACK')
  # Resolve the actual previous accepted 23-clip experimental asset, byte-for-byte.
  inputs=sorted(downloads.glob('MUDMAN_GODOT_CURATED_v2.0.23_*_REVIEW.glb'))
  prior=next((p for p in inputs if p.is_file() and not p.is_symlink() and digest(p)==SRC_SHA),None)
  if prior is None:
   helper.hydrate(repo,{SRC_GLB:SRC_SHA});prior=repo/SRC_GLB
  require(digest(prior)==SRC_SHA,'EXACT_CURRENT_MUDMAN_REVIEW_GLB_HASH_CHANGED')
  stage('ACTUAL_23_CLIP_GLB_WORLD_FRAME_FORENSICS')
  patch=load_module(packet/'fix.py','mudman_v226_glb_repair')
  output=root/(V+'_'+state['runId']+'_REVIEW.glb')
  diagfile=root/'HITHEADLEFT_FRAME_FORENSICS.json'
  if output.is_file() and diagfile.is_file():
   diagnostic=json.loads(diagfile.read_text())
   require(diagnostic.get('outputSHA256')==digest(output),'INTERRUPTED_CANDIDATE_BYTES_DISAGREE')
  else:
   if diagfile.exists() and not output.exists():
    previous=json.loads(diagfile.read_text())
    require(previous.get('sourceSHA256')==SRC_SHA,'RESUMED_FORENSIC_SOURCE_MISMATCH')
    require(previous.get('status')!='BLOCKED_NO_GUESS','PRIOR_ROOT_AXIS_DIAGNOSTIC_FOUND_NO_SAFE_FIX: '+str(previous.get('blocker','unqualified root axis')))
   require(not output.exists() and not diagfile.exists(),'PARTIAL_OUTPUT_REQUIRES_FORENSIC_RECOVERY')
   diagnostic=patch.repair(prior,output,diagfile,repo/V23_BASE)
  prior_forensic=pathlib.Path.home()/'.local/state'/'MUDMAN_HITHEADLEFT_AXIS_v2.0.25'/'working'/'HITHEADLEFT_AXIS_FORENSICS.json'
  if prior_forensic.is_file():
   try:
    olddiag=json.loads(prior_forensic.read_text())
    if olddiag.get('sourceSHA256')==SRC_SHA:
     diagnostic['v225PriorForensic']={'blocker':olddiag.get('blocker'),'referenceBodyDirectionDot':olddiag.get('referenceBodyDirectionDot'),
       'oldCandidateAngles':[{k:c.get(k) for k in ('node','offAxisDegrees','referenceRotationsAgreeDegrees','qualifies')} for c in olddiag.get('candidates',[])]}
     write_json(diagfile,diagnostic)
   except (OSError,ValueError):pass
  require(diagnostic['status']=='WORLD_FRAME_REPAIR_CANDIDATE_UNAPPROVED','UNVERIFIED_AXIS_REPAIR_STATUS')
  require(diagnostic['otherClipsByteEquivalent']==22 and diagnostic['otherClipsUnchanged'],'NON_TARGET_CLIP_CHANGED')
  candidate=downloads/output.name
  helper.copy_new(output,candidate)
  require(digest(candidate)==digest(output),'ANDROID_DOWNLOADS_CANDIDATE_HASH_CHANGED')
  state.update({'candidateDownload':str(candidate),'candidateSHA256':digest(candidate),'actualCorrection':diagnostic['chosen']})
  stage('ACTUAL_MUDMAN_GLB_VERIFIED_SINGLE_CLIP_WORLD_FRAME_CHANGED')
  # Two separately verified assets, original vs corrected, for human acceptance.
  token=hashlib.sha256((state['runId']+source_commit+expected+digest(candidate)+SRC_SHA).encode()).hexdigest()[:24]
  animations=sorted(patch.EXPECTED)
  models={key:{'sha256':digest(path),'bytes':path.stat().st_size,'url':'/models/'+key+'.glb','animations':animations}
          for key,path in (('candidate',candidate),('original',prior))}
  viewer_spec={'schema':V,'runId':state['runId'],'buildToken':token,'launcherSHA256':expected,'sourceCommit':source_commit,
    'htmlPath':str(repo/(SRC+'_viewer.html')),'models':models,'modelPaths':{'candidate':str(candidate),'original':str(prior)},
    'canonicalModelSHA256':CANON,'mode':'HITHEADLEFT_MEASURED_WORLD_FRAME_CORRECTION_BEFORE_AFTER_REVIEW'}
  old_viewer=load_module(repo/'campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py','mudman_v213_existing_viewer_helper');old_viewer.V=V
  # A valid prior receipt isn't evidence that a server process is still alive;
  # retry on a fresh unique port and check model hashes with HTTP HEAD.
  ticket=old_viewer.start_server(root,repo,viewer_spec)
  state.update({'viewerURL':ticket['url'],'serverPID':ticket['pid'],'serverPort':ticket['port'],'viewerHTTPVerified':True})
  stage('BOTH_MODELS_HTTP_SHA_READBACK_VERIFIED')
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(old_viewer.open_browser(ticket['url'])).upper(),flush=True)
  dirrel=REL+state['runId']+'/'
  glbrel=dirrel+'MUDMAN_HITHEADLEFT_FRAME_REVIEW_UNAPPROVED.glb'
  require(helper.g(repo,'check-attr','filter','--',glbrel).endswith('lfs'),'GLB_REVIEW_RESULT_LFS_ATTRIBUTE_MISSING')
  report=root/'REPORT.md'
  report.write_text('# Mudman HitHeadLeft: measured axis correction v2.0.26\n\n'
    '**Owner visual approval: PENDING.** Exactly one GLB HitHeadLeft local rotation channel changed. All other 22 animations and model textures preserved.\n\n'
    'Original SHA256 `'+SRC_SHA+'`, candidate SHA256 `'+digest(candidate)+'`.\n\n'
    'Affected node: `'+diagnostic['chosen']['node']+'`, observed initial angle: '
       +str(diagnostic['chosen']['angleDegrees'])+' degrees. Derived correction axis: '
       +repr(diagnostic['chosen']['axis'])+'.\n\n'
    'The correction is measured against original Ares-derived Idle-Cross and HitHeadRightBig; no ARP/blender rerun or source Gravity Fist modifications.\n\n'
    'Full quaternion values, skinning comparisons and five sampled times are in HITHEADLEFT_FRAME_FORENSICS.json.\n\n'
    'A/B no-cache viewer: '+ticket['url']+'\n')
  evidence={'schema':V,'authority':'TERMUX_GIT_ONLY','runId':state['runId'],'sourceCommit':source_commit,
    'originalSHA256':SRC_SHA,'candidateSHA256':digest(candidate),'status':'REVIEW_READY_NOT_OWNER_ACCEPTED',
    'rotationNode':diagnostic['chosen']['node'],'angleMeasuredDegrees':diagnostic['chosen']['angleDegrees'],
    'allOther22ClipsUnchanged':True,'canonicalAndOthersProtectedBefore':protected,
    'canonicalAndOthersProtectedAfter':{p:helper.g(repo,'rev-parse','HEAD:'+p) for p in PROTECTED},
    'viewerURL':ticket['url'],'viewerHTTPVerified':True,'rulesBlob':AGENTS,'canonicalObsidiantiSHA256':CANON,
    'ownerVisualAcceptance':'PENDING','noOriginalGravityFistSourceMutation':True,'noARPRerun':True,
    'testResults':p.stdout.strip()}
  require(evidence['canonicalAndOthersProtectedBefore']==evidence['canonicalAndOthersProtectedAfter'],'CANONICAL_OR_ACCEPTED_ASSET_ADVANCED')
  evfile=root/'EVIDENCE.json';write_json(evfile,evidence)
  stage('COMMIT_GIT_EVIDENCE_AND_BINARY_WITH_HASH_READBACK')
  evidence_commit=v23driver.commit_stage(helper,repo,{dirrel+'REPORT.md':report,dirrel+'HITHEADLEFT_FRAME_FORENSICS.json':diagfile,
    dirrel+'EVIDENCE.json':evfile,glbrel:candidate},'Mudman: measured HitHeadLeft torso-frame root EVIDENCE',protected)
  state['evidenceCommit']=evidence_commit
  state['status']='WORLD_FRAME_CORRECTED_CANDIDATE_PUBLISHED_OWNER_VISUAL_PENDING'
  stage('EXACT_REMOTE_EVIDENCE_READBACK_COMPLETE')
  print('MUDMAN_REPAIRED_GLB='+str(candidate),flush=True)
  print('MUDMAN_REPAIRED_GLB_SHA256='+digest(candidate),flush=True)
  print('GIT_EVIDENCE_COMMIT='+evidence_commit,flush=True)
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as err:
  state.update({'status':'BLOCKED','error':str(err)[:1400],'errorType':type(err).__name__,'traceback':traceback.format_exc()[-4000:]})
  write_json(receipt,state)
  print('STATUS=BLOCKED '+str(err)[:1000],flush=True)
  if (root/'HITHEADLEFT_FRAME_FORENSICS.json').exists():
   print('FORENSIC_DIAGNOSTICS='+str(root/'HITHEADLEFT_FRAME_FORENSICS.json'),flush=True)
  raise
 finally:
  write_json(receipt,state);print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('usage: driver.py PACKET LAUNCHER EXPECTED_SHA256')
 main(sys.argv[1],sys.argv[2],sys.argv[3])
