#!/usr/bin/env python3
"""Single-GLB Termux Git integration of Repl owner-corrected foreleg hierarchy v0.6.3.

Input/output: one canonical assets/repl/Repl.glb (same path).
Human visual verdict remains separate from full skinned-model numeric pass.
One downloaded ZIP includes all payloads; Git mutation is ONLY via Termux.
"""
from __future__ import annotations
import argparse,base64,datetime as dt,hashlib,importlib.util,json,os
from pathlib import Path
import shutil,subprocess,sys,tempfile,traceback

sys.dont_write_bytecode=True
VER='0.6.3'
PROJECT='REPL_FORELEG_BEND_REVERSAL'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BRANCH='main'
KNOWN_PARENT_HEAD='dac0d5ed854562096d8c8da919bc85bc431601bc'
CANON='assets/repl/Repl.glb'
MANIFEST='assets/repl/CANONICAL_MODEL.json'
README='README.md'
SOURCE_SHA='6a519d49d21dae6048553edc0aa09b340b8ca13979750a4abc1631a48e5c019f'
SOURCE_BLOB='6078f4f74069891bf4140e7925fe3e53e66569fa'
COMPATIBILITY_HOST_SAMPLE_SHA='0f33b3258fde571ee50aa42469f698a3048208a69fa16e8ac09d8906cb701c80'  # v0.6.2 structural-equivalent local candidate, NOT production-byte identity
BASE_ENGINE='campaigns/repl_hair_bind_v0_1_0.py'
BASE_ENGINE_BLOB='33ca93660f3d5858d4496027902b9b7a7e44d800'
GIZMO_JS='campaigns/repl_tail_gizmo_v0_4_0.js'
GIZMO_JS_BLOB='1b4396ed0027a0a75baed840d7ed741e57c58a92'
CAMPAIGN_FILES={
 'campaigns/repl_foreleg_chain_shift_v0_6_3.py':'model.py',
 'campaigns/repl_foreleg_lower_chain_constraints_v0_6_3.py':'fore_constraints.py',
 'campaigns/repl_foreleg_chain_driver_v0_6_3.py':'driver.py',
 'campaigns/repl_foreleg_chain_viewer_v0_6_3.html.in':'viewer.html.in',
 'campaigns/repl_foreleg_chain_blender_review_v0_6_3.py':'blender_review.py',
 'campaigns/REPL_FORELEG_BEND_REVERSAL_v0.6.3.sh':'run-termux.sh',
 'campaigns/REPL_FORELEG_BEND_REVERSAL_v0.6.3_CONTRACT.json':'contract.json',
 'campaigns/REPL_FORELEG_BEND_REVERSAL_v0.6.3_SELFTEST.py':'selftest.py',
}
OUT_HTML='REPL_FORELEG_BEND_REVERSAL_v0.6.3_TEXTURERENDER.html'
OUT_REPORT='REPL_FORELEG_BEND_REVERSAL_v0.6.3_report.json'
OUT_RECEIPT='REPL_FORELEG_BEND_REVERSAL_v0.6.3_RECEIPT.txt'

class Blocked(RuntimeError):pass

def need(ok,reason):
 if not ok:raise Blocked(reason)
def emit(k,v):print(f'{k}={v}',flush=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def gitblob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def file_sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()

def run(command,cwd=None,check=True,timeout=180):
 env=os.environ.copy()
 env['PYTHONDONTWRITEBYTECODE']='1'
 env['GIT_TERMINAL_PROMPT']='0'
 env['GIT_LFS_SKIP_SMUDGE']='1'
 p=subprocess.run(command,cwd=str(cwd) if cwd else None,env=env,
   stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
   timeout=timeout,check=False)
 if check and p.returncode:
  raise Blocked('COMMAND_FAILED:'+command[0]+':'+str(p.returncode)+':'+p.stderr[-480:].replace('\n',' '))
 return p

def git(repo,*args,check=True):return run(['git',*args],cwd=repo,check=check)
def gout(repo,*args):return git(repo,*args).stdout.strip()

def publish(path,data):
 path=Path(path)
 need(path.parent.is_dir(),'PUBLIC_DOWNLOADS_MISSING')
 if path.exists():
  need(path.is_file() and file_sha(path)==sha(data),
       'VERSIONED_PUBLIC_FILE_CONTENT_COLLISION:'+path.name)
  return
 fd,temp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(temp,path)
 finally:
  if os.path.exists(temp):os.unlink(temp)
 need(file_sha(path)==sha(data),'PUBLIC_FILE_READBACK_FAILED:'+path.name)

def checkout(work):
 repo=work/'repo'
 if repo.exists():
  need((repo/'.git').is_dir(),'STATE_CHECKOUT_NOT_GIT')
  need(gout(repo,'remote','get-url','origin')==REMOTE,'CAMPAIGN_GIT_REMOTE_MISMATCH')
  need(not git(repo,'status','--porcelain','--untracked-files=all').stdout.strip(),
       'CAMPAIGN_REPO_DIRTY_NO_AUTO_RESET')
  git(repo,'fetch','--quiet','origin',BRANCH)
  head=gout(repo,'rev-parse','HEAD');remote=gout(repo,'rev-parse','refs/remotes/origin/main')
  if head!=remote:
   need(git(repo,'merge-base','--is-ancestor',remote,head,check=False).returncode==0,
        'LOCAL_AHEAD_BRANCH_NOT_DESCENDED_FROM_REMOTE')
  return repo
 stage=Path(tempfile.mkdtemp(prefix='.repl-fore-ik-clone-',dir=work))
 try:
  shutil.rmtree(stage)
  run(['git','clone','--quiet','--branch','main','--single-branch',REMOTE,str(stage)],timeout=200)
  need(gout(stage,'remote','get-url','origin')==REMOTE,'CLONE_REMOTE_NOT_EXPECTED')
  os.replace(stage,repo)
 finally:
  if stage.exists():shutil.rmtree(stage)
 return repo

def one_model(repo,ref='HEAD'):
 models=[x for x in gout(repo,'ls-tree','-r','--name-only',ref).splitlines()
   if x.lower().endswith('.glb')]
 need(models==[CANON],'REPO_GLB_MULTIPLICATION_OR_PATH_MISMATCH:'+repr(models))

def verify_source(repo):
 one_model(repo)
 model=(repo/CANON).read_bytes()
 need(sha(model)==SOURCE_SHA and gitblob(model)==SOURCE_BLOB,
      'SOURCE_NOT_EXACT_v0.6.2_CANONICAL_GLB')
 need(gout(repo,'rev-parse','HEAD:'+CANON)==SOURCE_BLOB,'GIT_SOURCE_BLOB_CHANGED')
 for name,blob in ((BASE_ENGINE,BASE_ENGINE_BLOB),(GIZMO_JS,GIZMO_JS_BLOB)):
  need((repo/name).is_file(),'GIT_OWNED_ENGINE_MISSING:'+name)
  need(gout(repo,'hash-object','--',name)==blob,'ENGINE_OR_GIZMO_UNEXPECTED_EDIT:'+name)
 data=json.loads((repo/MANIFEST).read_text('utf8'))
 need(data.get('canonical_glb_path')==CANON,'MANIFEST_PATH_INVALID')
 need(data.get('active_model',{}).get('sha256')==SOURCE_SHA and
      data['active_model'].get('version')=='0.6.2',
      'MANIFEST_ACTIVE_MODEL_NOT_v0.6.2')
 emit('CANONICAL_SOURCE_SHA',sha(model));emit('SINGLE_GLB',1)
 return model,data

def import_module(path,name):
 sys.path.insert(0,str(Path(path).parent))
 spec=importlib.util.spec_from_file_location(name,path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return m

def make_viewer(packet,repo,model):
 template=(packet/'viewer.html.in').read_text('utf8')
 gizmo=(repo/GIZMO_JS).read_text('utf8')
 need('const chosen = new THREE.Vector3(0,1.05,-0.93);' in gizmo,
      'GIZMO_UPSTREAM_SOURCE_CHANGED')
 gizmo=gizmo.replace('const chosen = new THREE.Vector3(0,1.05,-0.93);',
      'const chosen = new THREE.Vector3(0,1.204,-0.889);')
 gizmo=gizmo.replace('existing.position.copy(chosen);',
      'existing.position.set(0,1.05,-0.93);')
 gizmo=gizmo.replace('d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f',sha(model))
 need('__GIZMO_JS__' in template and '__EMBEDDED_GLB_BASE64__' in template,
      'MISSING_ACTUAL_TEXTURED_VIEWER_PLACEHOLDERS')
 html=template.replace('__GIZMO_JS__',gizmo).replace('__EMBEDDED_GLB_BASE64__',base64.b64encode(model).decode('ascii'))
 need('show-hinges' in html,'FORELEG_HINGE_DIAGNOSTICS_NOT_IN_VIEWER')
 return html.encode('utf8')

def manifest_update(previous,model,report,html):
 data=dict(previous)
 old=dict(data.get('active_model') or {})
 data['previous_model']={
  'version':old.get('version'),'sha256':old.get('sha256'),
  'git_blob_sha1':old.get('git_blob_sha1'),
  'owner_visual_acceptance':'REJECTED__v0.6.2_FORELEG_BEND_DIRECTIONS_REVERSED',
  'hindleg_notes':'BETTER_BUT_NOT_YET_HUMAN_APPROVED',
  'source_regression':'NONE'}
 active=dict(old)
 for obsolete in ('foreleg_upper_forward_joints','foreleg_lower_backward_joints','foreleg_carpus_hinge','foreleg_elbow_hinge','shifted_hinge_pole_metrics'):
  active.pop(obsolete,None)
 active.update({
   'path':CANON,'version':VER,'campaign':PROJECT,
   'sha256':sha(model),'git_blob_sha1':gitblob(model),
   'joint_count':50,'node_count':53,'animations':6,
   'mode':'FORWARD_TRAVEL_ONLY_NO_IN_PLACE',
   'foreleg_upper_backward_joints':report['foreleg_upper_backward'],
   'foreleg_lower_forward_joints':report['foreleg_lower_forward'],
   'max_swing_toe_marker_deviation':report['max_swing_toe_marker_deviation'],
   'max_stance_toe_marker_deviation':report['max_stance_toe_marker_deviation'],
   'max_skinned_stance_hoof_delta':report['max_real_skinned_stance_hoof_vertex_delta'],
   'min_swing_hoof_surface_y':report['min_swing_skin_hoof_y'],
   'swing_hoof_surface_visual_review':'REQUIRED',
   'shifted_hinge_pole_metrics':{
    'upper_backward_max':report['max_upper_backward_pole_mid_swing'],
    'lower_forward_min':report['min_lower_forward_pole_mid_swing']},
   'hindleg_tracks':'UNCHANGED_FROM_v0.6.2',
   'root_travel':'UNCHANGED_0.96_MODEL_UNITS',
   'accepted_mane_weights':'UNCHANGED',
   'tail_pivot':'UNCHANGED_FROM_APPROVED_v0.5.2',
   'all_previous_animations':'PRESERVED',
   'foreleg_review_html_sha256':sha(html),
   'human_visual_acceptance':'PENDING'})
 data['active_model']=active
 data['status']='FORELEG_CHAIN_SHIFT_v0.6.3__HUMAN_VISUAL_PENDING'
 data['single_canonical_glb_count']=1
 data['later_hair_motion_results_in_repo']=True
 data['owner_rules']=list(dict.fromkeys(list(data.get('owner_rules',[]))+[
  'Correct foreleg upper Bone_014/020 bends backward, lower Bone_013/019 bends forward',
  'Do not revert v0.6.3 directions and do not move the correct v0.6.2 bone levels',
  'All hindleg, foreleg stance, mane/tail, root/world travel tracks must stay exact',
  'No in-place walk and exactly one GLB in repository']))
 return json.dumps(data,indent=2,sort_keys=True)+'\n'

def append_readme(old):
 heading='## Owner-corrected foreleg bend polarity v0.6.3'
 need(heading not in old,'README_v063_DUPLICATE_HEADING')
 return (old.rstrip()+'\n\n'+heading+'\n\n'
  'The owner rejected v0.6.2 because the forehoof bends FORWARD, not backward. '
  'The upper mapped foreleg joints LF Bone_014/RF Bone_020 now bend BACKWARD, '
  'and the lower mapped joints LF Bone_013/RF Bone_019 bend FORWARD. '
  'Joint-chain levels remain unchanged from v0.6.2; no additional bones are added. '
  'Only swing foreleg rotations in the same three forward-travel walk animations '
  'are corrected. Stance legs, hind legs, root translation, body, mane, tail, '
  'approved socket, skin weights and earlier three animation clips remain intact. '
  'The canonical assets/repl/Repl.glb is the only model file in the repository. '
  'A textured viewer highlights both bend positions and displays forward travel. '
  'Visual acceptance remains pending until the owner reviews v0.6.3.\n')

def commit(repo,packet,model,report,html):
 need(sha(model)!=SOURCE_SHA,'CORRECTED_MODEL_EQUALS_UNCHANGED_INPUT')
 p=repo/CANON
 fd,tmp=tempfile.mkstemp(prefix='.Repl.fore063.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(model);f.flush();os.fsync(f.fileno())
  need(file_sha(tmp)==sha(model),'CANONICAL_STAGING_FILE_WRONG_SHA')
  os.replace(tmp,p)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 need(file_sha(p)==sha(model),'CANONICAL_GLTF_WRITE_READBACK_FAILED')
 data=json.loads((repo/MANIFEST).read_text('utf8'))
 (repo/MANIFEST).write_text(manifest_update(data,model,report,html),encoding='utf8')
 (repo/README).write_text(append_readme((repo/README).read_text('utf8')),encoding='utf8')
 for dest,packet_name in CAMPAIGN_FILES.items():
  target=repo/dest
  need(not target.exists(),'SOURCE_CAMPAIGN_VERSION_FILENAME_EXISTS:'+dest)
  source=packet/packet_name
  need(source.is_file(),'PACKET_SOURCE_MISSING:'+packet_name)
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(source.read_bytes())
 allowed=[CANON,MANIFEST,README]+list(CAMPAIGN_FILES)
 git(repo,'add','--',*allowed)
 staged=git(repo,'diff','--cached','--name-only').stdout.strip().splitlines()
 need(set(staged)==set(allowed) and len(staged)==len(allowed),
      'GIT_STAGED_FILE_SET_NOT_EXPECTED:'+repr(staged))
 need(not any(x.startswith('??') for x in git(repo,'status','--porcelain','--untracked-files=all').stdout.splitlines()),
      'UNEXPECTED_UNTRACKED_CAMPAIGN_FILE')
 git(repo,'-c','user.name=Repl Termux Campaign',
     '-c','user.email=repl-termux-campaign@users.noreply.github.com',
     'commit','-m','Reverse both Repl foreleg IK bend directions without moving joints v0.6.3')
 return gout(repo,'rev-parse','HEAD')

def push(repo,parent):
 need(gout(repo,'ls-remote','origin','refs/heads/main').split()[0]==parent,
      'REMOTE_HEAD_ADVANCED_NO_FORCE_PUSH')
 cmds=[['git','push','--quiet','origin','HEAD:refs/heads/main']]
 if shutil.which('gh'):
  if run(['gh','auth','status','-h','github.com'],check=False,timeout=12).returncode==0:
   cmds.append(['git','-c','credential.helper=!gh auth git-credential','push','--quiet',
                'origin','HEAD:refs/heads/main'])
 if shutil.which('ssh'):
  cmds.append(['git','push','--quiet',
               'git@github.com:Valar05/parametric-parambulator.git',
               'HEAD:refs/heads/main'])
 for i,cmd in enumerate(cmds):
  result=run(cmd,cwd=repo,check=False,timeout=160)
  if result.returncode==0:
   emit('GIT_PUSH_ROUTE',('origin','gh','ssh')[i]);return
 need(False,'ALL_EXISTING_TERMUX_GIT_PUSH_AUTH_ROUTES_FAILED__LOCAL_COMMIT_PRESERVED')

def verify_remote(repo,model,commit):
 git(repo,'fetch','--quiet','origin',BRANCH)
 ref=gout(repo,'rev-parse','refs/remotes/origin/main')
 need(ref==commit,'REMOTE_COMMIT_DIFFERS_FROM_LOCAL')
 one_model(repo,ref)
 need(gout(repo,'rev-parse',f'{ref}:{CANON}')==gitblob(model),
      'REMOTE_CANONICAL_BLOB_NOT_UPDATED')
 raw=subprocess.run(['git','show',f'{ref}:{CANON}'],cwd=repo,
   stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
 need(raw.returncode==0 and sha(raw.stdout)==sha(model),
      'REMOTE_BINARY_READBACK_SHA_MISMATCH')
 manifest=json.loads(git(repo,'show',f'{ref}:{MANIFEST}').stdout)
 need(manifest.get('active_model',{}).get('version')==VER and
      manifest['active_model']['sha256']==sha(model),
      'REMOTE_MANIFEST_VERSION_NOT_UPDATED')
 return ref

def receipt(downloads,remote,model,report):
 fields={
  'CAMPAIGN':PROJECT,'VERSION':VER,'LANE':'TERMUX_GIT',
  'REMOTE_HEAD':remote,'CANONICAL_GLB':CANON,'REMOTE_GLB_COUNT':1,
  'REMOTE_GLB_SHA256':sha(model),'REMOTE_GIT_BLOB':gitblob(model),
  'UPPER_BACKWARD_LF':'Bone_014','UPPER_BACKWARD_RF':'Bone_020',
  'LOWER_FORWARD_LF':'Bone_013','LOWER_FORWARD_RF':'Bone_019',
  'MAX_SWING_TOE_MARKER_ERROR':report['max_swing_toe_marker_deviation'],
  'MAX_UPPER_BACKWARD_POLE':report['max_upper_backward_pole_mid_swing'],
  'MIN_LOWER_FORWARD_POLE':report['min_lower_forward_pole_mid_swing'],
  'STANCE_TOE_MARKER_CHANGE':report['max_stance_toe_marker_deviation'],
  'REAL_SKINNED_STANCE_HOOF_CHANGE':report['max_real_skinned_stance_hoof_vertex_delta'],
  'MIN_SWING_SURFACE_Y_LF':report['min_swing_skin_hoof_y']['LF'],
  'MIN_SWING_SURFACE_Y_RF':report['min_swing_skin_hoof_y']['RF'],
  'SWING_GROUND_INTERSECTION':'REVIEW_REQUIRED',
  'HIND_LEGS':'EXACT_UNCHANGED','MANE_TAIL':'EXACT_UNCHANGED',
  'ROOT_FORWARD_TRAVEL':'0.96','IN_PLACE_WALK':'NONE',
  'HUMAN_VISUAL_VERDICT':'PENDING',
  'STATUS':'REMOTE_SINGLE_CANONICAL_FORELEG_BEND_REVERSAL_READBACK_VERIFIED'}
 data=('\n'.join(k+'='+str(v) for k,v in fields.items())+'\n').encode('utf8')
 publish(downloads/OUT_RECEIPT,data)
 emit('RECEIPT_PATH',str(downloads/OUT_RECEIPT))
 for k,v in fields.items():emit(k,v)

def optional_blender(repo,packet,downloads):
 exe=shutil.which('blender')
 if not exe:emit('BLENDER_RENDER','NOT_ON_TERMUX_PATH__FULL_TEXTURED_HTML_READY');return
 folder=downloads/'REPL_FORELEG_BEND_REVERSAL_v0.6.3_blender'
 folder.mkdir(parents=True,exist_ok=True)
 command=[exe,'--background','--factory-startup','--python',
   str(packet/'blender_review.py'),'--','--glb',str(repo/CANON),
   '--output',str(folder)]
 try:
  result=run(command,check=False,timeout=420)
  publish(folder/'blender_run_v0.6.3.log',(result.stdout+'\n'+result.stderr)[-15000:].encode('utf8'))
  emit('BLENDER_RENDER','GENERATED' if result.returncode==0 else 'FAILED__HTML_REVIEW_AVAILABLE')
 except (OSError,subprocess.TimeoutExpired):
  emit('BLENDER_RENDER','FAILED_OR_TIMEOUT__HTML_REVIEW_AVAILABLE')

def maybe_open(downloads):
 file=downloads/OUT_HTML
 exe=shutil.which('termux-media-scan')
 if exe:
  try:
   r=run([exe,str(file)],check=False,timeout=15)
   emit('MEDIA_SCAN','REQUESTED_NOT_VERIFIED' if r.returncode==0 else 'FAILED')
  except Exception:emit('MEDIA_SCAN','FAILED')
 exe=shutil.which('termux-open')
 if exe:
  try:
   r=run([exe,str(file)],check=False,timeout=12)
   emit('BROWSER_OPEN','REQUESTED_NOT_CONFIRMED' if r.returncode==0 else 'FAILED')
  except Exception:emit('BROWSER_OPEN','FAILED')
 else:emit('BROWSER_OPEN','UNAVAILABLE')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--packet',required=True)
 args=p.parse_args()
 packet=Path(args.packet).resolve()
 need(packet.is_dir(),'EXTRACTED_PACKET_NOT_FOUND')
 downloads=Path.home()/'storage'/'downloads'
 need(downloads.is_dir(),'TERMUX_DOWNLOADS_NOT_MOUNTED')
 work=Path.home()/'.local'/'share'/'repl-campaigns'/'foreleg-bend-v0.6.3'
 work.mkdir(parents=True,exist_ok=True)
 emit('CAMPAIGN',PROJECT);emit('VERSION',VER)
 emit('LANE','TERMUX_GIT_ONLY');emit('MODEL_PATH',CANON)
 repo=checkout(work)
 head=gout(repo,'rev-parse','HEAD')
 remote=gout(repo,'rev-parse','refs/remotes/origin/main')
 one_model(repo)
 existing=json.loads((repo/MANIFEST).read_text('utf8'))
 active=existing.get('active_model',{})
 if head==remote and active.get('version')==VER:
  model=(repo/CANON).read_bytes()
  need(sha(model)==active.get('sha256'),
       'PRIOR_SUCCESS_MODEL_UNEXPECTED_SHA')
  need((downloads/OUT_HTML).is_file() and (downloads/OUT_REPORT).is_file(),
       'PRIOR_SUCCESS_VISUAL_EVIDENCE_NOT_FOUND')
  report=json.loads((downloads/OUT_REPORT).read_text('utf8'))
  need(report.get('new_sha256')==sha(model),'PRIOR_SUCCESS_REPORT_WRONG_MODEL')
  emit('RUN_MODE','EXISTING_COMPLETED_RELEASE')
  verified=verify_remote(repo,model,head)
  receipt(downloads,verified,model,report);maybe_open(downloads);return
 if head!=remote:
  need(active.get('version')==VER,'UNEXPECTED_LOCAL_AHEAD_REVISION')
  model=(repo/CANON).read_bytes()
  need(sha(model)==active.get('sha256'),
       'PENDING_LOCAL_COMMIT_MODEL_UNEXPECTED')
  need((downloads/OUT_HTML).is_file() and (downloads/OUT_REPORT).is_file(),
       'PENDING_COMMIT_EVIDENCE_FILES_MISSING')
  report=json.loads((downloads/OUT_REPORT).read_text('utf8'))
  need(report['new_sha256']==sha(model),'PENDING_COMMIT_REPORT_INVALID')
  emit('RUN_MODE','RESUME_PREVIOUS_LOCAL_COMMIT_AND_PUSH')
  push(repo,remote)
  verified=verify_remote(repo,model,head)
  receipt(downloads,verified,model,report);optional_blender(repo,packet,downloads)
  maybe_open(downloads);return
 source,manifest=verify_source(repo)
 base=import_module(repo/BASE_ENGINE,'repl_locked_base_for_ik062')
 base.EXPECTED_JOINTS=50
 repair=import_module(packet/'model.py','repl_fore_constraint_model_062')
 need(repair.SOURCE_SHA==SOURCE_SHA and repair.CANON==CANON,
      'PACKET_MODEL_DECLARED_WRONG_SOURCE')
 emit('FORELEG_BEND_REVERSAL','STARTING_ON_ACTUAL_REPO_GLB')
 model,report=repair.make_correction(source,base,progress=lambda v:emit('PROGRESS',v))
 emit('COMPATIBILITY_HOST_SAMPLE_SHA',COMPATIBILITY_HOST_SAMPLE_SHA)
 emit('HOST_SAMPLE_SAME_SOURCE_BYTES','NO__REAL_PRODUCTION_SOURCE_IS_SHA_PINNED')
 emit('ACTUAL_TERMUX_MODEL_SHA256',sha(model))
 emit('FORELEG_BEND_REVERSAL','ACTUAL_SOURCE_REVERSED_BEND_VALIDATION_PASS')
 html=make_viewer(packet,repo,model)
 report['review_html_sha256']=sha(html)
 report['source_git_commit']=head
 report['source_git_blob']=SOURCE_BLOB
 publish(downloads/OUT_HTML,html)
 publish(downloads/OUT_REPORT,(json.dumps(report,sort_keys=True,indent=2)+'\n').encode('utf8'))
 emit('TEXTURED_VIEWER',str(downloads/OUT_HTML))
 emit('ACTUAL_MODEL_TEST_REPORT',str(downloads/OUT_REPORT))
 need(gout(repo,'ls-remote','origin','refs/heads/main').split()[0]==head,
      'REMOTE_MOVED_BEFORE_CANONICAL_UPDATE__PRESERVED')
 commit_sha=commit(repo,packet,model,report,html)
 emit('LOCAL_MODEL_COMMIT',commit_sha)
 push(repo,head)
 verified=verify_remote(repo,model,commit_sha)
 receipt(downloads,verified,model,report)
 optional_blender(repo,packet,downloads)
 maybe_open(downloads)

if __name__=='__main__':
 try:main()
 except Blocked as exc:
  emit('CAMPAIGN_STATUS','BLOCKED')
  emit('CAUSE',exc)
  emit('LIVE_CANONICAL_MODEL_STATUS','UNCHANGED_OR_LOCAL_COMMIT_UNPUSHED')
  sys.exit(2)
 except Exception as exc:
  traceback.print_exc()
  emit('CAMPAIGN_STATUS','FAILED')
  emit('CAUSE',type(exc).__name__+':'+str(exc))
  emit('LIVE_CANONICAL_MODEL_STATUS','UNVERIFIED')
  sys.exit(3)
