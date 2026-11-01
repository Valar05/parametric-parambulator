#!/usr/bin/env python3
"""Single-GLB Termux Git integration of cartoon four-beat FK-hoof walk v0.6.10.

Input/output: one canonical assets/repl/Repl.glb (same path).
Human visual verdict remains separate from full skinned-model numeric pass.
One downloaded ZIP includes all payloads; Git mutation is ONLY via Termux.
"""
from __future__ import annotations
import argparse,base64,datetime as dt,hashlib,importlib.util,json,os
from pathlib import Path
import shutil,subprocess,sys,tempfile,traceback

sys.dont_write_bytecode=True
VER='0.6.10'
PROJECT='REPL_CARTOON_FK_HOOF_WALK'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BRANCH='main'
KNOWN_PARENT_HEAD='859a74c72cf0d8c35e54b4128119603976f8daa9'
CANON='assets/repl/Repl.glb'
MANIFEST='assets/repl/CANONICAL_MODEL.json'
README='README.md'
SOURCE_SHA='eff0c604ca56ba58543c7a477bffc0e22e3c23f1d5da00bdbf1ea62369f27509'
SOURCE_BLOB='ee68428d9edf305c22e1bd4aa1fca7ad61e993e1'
PREVIOUS_MODEL='campaigns/repl_cartoon_fk_hoof_model_v0_6_8.py'
PREVIOUS_MODEL_BLOB='70feea06678534fbc438a884b5c712b36bffd2d7'
BASE_ENGINE='campaigns/repl_hair_bind_v0_1_0.py'
BASE_ENGINE_BLOB='33ca93660f3d5858d4496027902b9b7a7e44d800'
GIZMO_JS='campaigns/repl_tail_gizmo_v0_4_0.js'
GIZMO_JS_BLOB='1b4396ed0027a0a75baed840d7ed741e57c58a92'
POSE_PATCH='campaigns/repl_pose_lab_bones_patch_v0_6_6.py'
POSE_PATCH_BLOB='73e36078a7be40c4482a6c35c408afe67ed64d77'
POSE_JS='campaigns/repl_pose_lab_bones_v0_6_6.js'
POSE_JS_BLOB='d4d41cd9dc68bf8f640a436fef9ce6c303f1e239'
CAMPAIGN_FILES={
 'campaigns/repl_cartoon_fk_hoof_model_v0_6_10.py':'model.py',
 'campaigns/repl_cartoon_fk_hoof_regression_v0_6_10.py':'regression.py',
 'campaigns/repl_cartoon_fk_hoof_driver_v0_6_10.py':'driver.py',
 'campaigns/repl_cartoon_fk_hoof_viewer_v0_6_10.html.in':'viewer.html.in',
 'campaigns/repl_cartoon_fk_hoof_blender_review_v0_6_10.py':'blender_review.py',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.10.sh':'run-termux.sh',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.10_CONTRACT.json':'contract.json',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.10_SELFTEST.py':'selftest.py',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.10_PACKET_MANIFEST.json':'../manifest.json',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.10_README.md':'../README.md',
}
OUT_HTML='REPL_CARTOON_FK_HOOF_WALK_v0.6.10_TEXTURED_POSE_LAB.html'
OUT_REPORT='REPL_CARTOON_FK_HOOF_WALK_v0.6.10_report.json'
OUT_RECEIPT='REPL_CARTOON_FK_HOOF_WALK_v0.6.10_RECEIPT.txt'

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

def blocked_report(downloads,diagnostic):
 payload=(json.dumps(diagnostic,indent=2,sort_keys=True,allow_nan=False)+'\n').encode('utf8')
 path=downloads/('REPL_CARTOON_FK_HOOF_WALK_v0.6.10_BLOCKED_'+sha(payload)[:12]+'.json')
 publish(path,payload)
 emit('CAMPAIGN_DIAGNOSTIC_PATH',str(path))
 return path

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
 stage=Path(tempfile.mkdtemp(prefix='.repl-lower-arc-clone-',dir=work))
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
      'SOURCE_NOT_EXACT_v0.6.8_CANONICAL_GLB')
 need(gout(repo,'rev-parse','HEAD:'+CANON)==SOURCE_BLOB,'GIT_SOURCE_BLOB_CHANGED')
 for name,blob in ((BASE_ENGINE,BASE_ENGINE_BLOB),(GIZMO_JS,GIZMO_JS_BLOB),(POSE_PATCH,POSE_PATCH_BLOB),(POSE_JS,POSE_JS_BLOB),(PREVIOUS_MODEL,PREVIOUS_MODEL_BLOB)):
  need((repo/name).is_file(),'GIT_OWNED_ENGINE_MISSING:'+name)
  need(gout(repo,'hash-object','--',name)==blob,'ENGINE_OR_GIZMO_UNEXPECTED_EDIT:'+name)
 data=json.loads((repo/MANIFEST).read_text('utf8'))
 need(data.get('canonical_glb_path')==CANON,'MANIFEST_PATH_INVALID')
 need(data.get('active_model',{}).get('sha256')==SOURCE_SHA and
      data['active_model'].get('version')=='0.6.8',
      'MANIFEST_ACTIVE_MODEL_NOT_v0.6.8')
 emit('CANONICAL_SOURCE_SHA',sha(model));emit('SINGLE_GLB',1)
 return model,data

def import_module(path,name):
 sys.path.insert(0,str(Path(path).parent))
 spec=importlib.util.spec_from_file_location(name,path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return m

def make_viewer(packet,repo,model):
 template=(packet/'viewer.html.in').read_text('utf8')
 patcher=import_module(repo/POSE_PATCH,'repl_pose_lab_viewer_patch_pinned_v066')
 js=(repo/POSE_JS).read_text('utf8')
 template=patcher.patch(template,js,sha(model))
 template=template.replace('Repl · Pose Lab bone controls (non-destructive)',
   'Repl · Cartoon FK-Hoof Walk v0.6.10 + Pose Lab')
 template=template.replace('Repl · Pose Lab bone controls v0.6.6',
   'Repl · Cartoon FK-Hoof Walk v0.6.10')
 template=template.replace('This is a reversible pose reference, not a new walk animation.',
   'Inspect the new v0.6.10 walk; pose edits are temporary and do not change the model.')
 template=template.replace('The upper front joint', 'The upper front joint')
 gizmo=(repo/GIZMO_JS).read_text('utf8')
 need('const chosen = new THREE.Vector3(0,1.05,-0.93);' in gizmo,
      'GIZMO_UPSTREAM_ANCHOR_CHANGED')
 gizmo=gizmo.replace('const chosen = new THREE.Vector3(0,1.05,-0.93);',
      'const chosen = new THREE.Vector3(0,1.204,-0.889);')
 gizmo=gizmo.replace('existing.position.copy(chosen);',
      'existing.position.set(0,1.05,-0.93);')
 gizmo=gizmo.replace('d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f',sha(model))
 need('__GIZMO_JS__' in template and '__EMBEDDED_GLB_BASE64__' in template,
      'MISSING_TEXTURED_VIEWER_PLACEHOLDERS')
 html=template.replace('__GIZMO_JS__',gizmo).replace('__EMBEDDED_GLB_BASE64__',base64.b64encode(model).decode('ascii'))
 need('id="pl-edit"' in html and 'id="pl-lockX"' in html,
      'POSE_LAB_CONTROLS_MISSING_FROM_CORRECTED_WALK')
 need('show-hinges' in html and 'installReplPoseLab' in html,
      'BONE_VISUALIZATION_LOST')
 return html.encode('utf8')

def manifest_update(previous,model,report,html):
 data=dict(previous);old=dict(data.get('active_model') or {})
 data['previous_model']={'version':old.get('version'),'sha256':old.get('sha256'),
  'git_blob_sha1':old.get('git_blob_sha1'),
  'owner_visual_acceptance':'PARTIAL_v0.6.8_JOINT_DIRECTIONS_CORRECT_REAR_LEGS_REASONABLE',
  'owner_next_correction':'Front hoof drags/rotates through ground; increase shoulder forward lead and middle backward fold'}
 active=dict(old)
 active.update({'version':VER,'campaign':PROJECT,'path':CANON,
  'sha256':sha(model),'git_blob_sha1':gitblob(model),
  'joint_count':50,'node_count':53,'animations':6,
  'mode':'FRONT_SWING_LIFT_ON_CANONICAL_V068',
  'owner_visual_goal':'Front hoof clears ground, shoulder moves 20-30 deg forward, middle folds backward visibly',
  'controlled_bones':sorted(['Bone_015','Bone_014','Bone_021','Bone_020']),
  'preserved_hind_leg_channels':'IDENTICAL_TO_V068',
  'preserved_distal_front_drivers':'Bone_013,Bone_019 identical to v0.6.8',
  'preserved_hoof_masses':'Bone_012,Bone_018,Bone_023,Bone_028 local FK rest unchanged',
  'front_swing_profile':report['profile'],
  'measured_front_swing_angles':report['front_joint_angles'],
  'measured_front_hoof_clearance':report['front_hoof_clearance'],
  'minimum_mid_swing_clearance':report['min_mid_clearance'],
  'minimum_early_swing_clearance':report['min_early_clearance'],
  'max_keyframe_rotation_step_deg':report['max_step_rotation_deg'],
  'root_forward_travel':0.96,'gait_phasing':'UNCHANGED_V068',
  'accepted_mane_weights':'UNCHANGED','tail_pivot':'APPROVED_v0.5.2_PRESERVED',
  'all_previous_animations':'PRESERVED',
  'review_html_sha256':sha(html),'human_visual_acceptance':'PENDING'})
 data['active_model']=active;data['status']='FRONT_SWING_CLEARANCE_v0.6.10__HUMAN_VISUAL_PENDING'
 data['single_canonical_glb_count']=1;data['later_hair_motion_results_in_repo']=True
 data['owner_rules']=list(dict.fromkeys(list(data.get('owner_rules',[]))+[
  'Owner at v0.6.8: current joint directions correct; rear legs reasonable; front hooves drag through ground',
  'Target shoulder directly above foreleg middle joint 20-30 degrees forward during swing',
  'Foreleg middle joint must fold more rearward, producing visibly greater curvature than hindlegs',
  'v0.6.8 front middle lock superseded ONLY by requested front middle folding change',
  'Do not change rear legs, front distal drivers, hoof-mass orientation, stance, timing, root travel, approved mane/tail',
  'Compare skinned hoof underside to planted same-foot surface across swing; human visual verdict remains necessary']))
 return json.dumps(data,indent=2,sort_keys=True)+'\n'

def append_readme(old):
 heading='## Front swing clearance and shoulder-middle articulation v0.6.10'
 need(heading not in old,'README_FRONT_CLEARANCE_HEADING_ALREADY_EXISTS')
 return old.rstrip()+'\n\n'+heading+'\n\n'+(
  'Owner reviewed v0.6.8: joint directions look correct and rear-leg motion is reasonable, '
  'but front hooves drag and rotate through the ground. This front-only campaign '
  'adds 20–30 degrees of world-forward shoulder segment lead at Bone_015/Bone_021 '
  'and stronger world-backward middle segment folding at Bone_014/Bone_020, '
  'with runtime signed axis calibration and bounded physical-clearance profiles. '
  'The whole skinned underside must clear the same hoof planted ground reference. '
  'The 0.6.8 rear legs, front lower drivers, hoof masses and deformation branches, '
  'all stance frames, world forward travel, timing, mane, tail, geometry, weights '
  'and the single canonical GLB path are preserved. Source is strictly pinned '
  'to 0.6.8 and the final textured visual review remains pending.\n')

def commit(repo,packet,model,report,html):
 need(sha(model)!=SOURCE_SHA,'CORRECTED_MODEL_EQUALS_UNCHANGED_INPUT')
 p=repo/CANON
 fd,tmp=tempfile.mkstemp(prefix='.Repl.lower064.',suffix='.tmp',dir=p.parent)
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
     'commit','-m','Increase Repl front shoulder lead and middle fold for hoof clearance v0.6.10')
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
  'FRONT_SHOULDER_MIDDLE_PROFILE':json.dumps(report['profile'],sort_keys=True),
  'MEASURED_MIN_MID_SWING_HOOF_CLEARANCE':report['min_mid_clearance'],
  'MEASURED_MIN_EARLY_SWING_HOOF_CLEARANCE':report['min_early_clearance'],
  'MAX_FRONT_JOINT_STEP_DEG':report['max_step_rotation_deg'],
  'PROTECTED_REAR_LEGS':'IDENTICAL_V068',
  'FRONT_DISTAL_BONES':'IDENTICAL_V068',
  'HOOF_MASSES':'UNCHANGED_V068_LOCAL_FK_REST',
  'ALL_STAGES':'VALIDATED','MANE_TAIL':'UNCHANGED',
  'ROOT_FORWARD_TRAVEL':'0.96','IN_PLACE_WALK':'NONE',
  'HUMAN_VISUAL_VERDICT':'PENDING',
  'STATUS':'REMOTE_SINGLE_CANONICAL_FRONT_LIFT_READBACK_VERIFIED'}
 data=('\n'.join(k+'='+str(v) for k,v in fields.items())+'\n').encode('utf8')
 publish(downloads/OUT_RECEIPT,data)
 emit('RECEIPT_PATH',str(downloads/OUT_RECEIPT))
 for k,v in fields.items():emit(k,v)

def optional_blender(repo,packet,downloads):
 exe=shutil.which('blender')
 if not exe:emit('BLENDER_RENDER','NOT_ON_TERMUX_PATH__FULL_TEXTURED_HTML_READY');return
 folder=downloads/'REPL_CARTOON_FK_HOOF_WALK_v0.6.10_blender'
 folder.mkdir(parents=True,exist_ok=True)
 command=[exe,'--background','--factory-startup','--python',
   str(packet/'blender_review.py'),'--','--glb',str(repo/CANON),
   '--output',str(folder)]
 try:
  result=run(command,check=False,timeout=420)
  publish(folder/'blender_run_v0.6.10.log',(result.stdout+'\n'+result.stderr)[-15000:].encode('utf8'))
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
 work=Path.home()/'.local'/'share'/'repl-campaigns'/'cartoon-fk-hoof-v0.6.10'
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
  need(report.get('output_sha256')==sha(model),'PRIOR_SUCCESS_REPORT_WRONG_MODEL')
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
  need(report['output_sha256']==sha(model),'PENDING_COMMIT_REPORT_INVALID')
  emit('RUN_MODE','RESUME_PREVIOUS_LOCAL_COMMIT_AND_PUSH')
  push(repo,remote)
  verified=verify_remote(repo,model,head)
  receipt(downloads,verified,model,report);optional_blender(repo,packet,downloads)
  maybe_open(downloads);return
 need(head==KNOWN_PARENT_HEAD,'PRODUCTION_HEAD_ADVANCED_AFTER_CAMPAIGN_BUILT__NO_OVERWRITE')
 source,manifest=verify_source(repo)
 base=import_module(repo/BASE_ENGINE,'repl_locked_base_for_front0610')
 base.EXPECTED_JOINTS=50
 repair=import_module(packet/'model.py','repl_cartoon_fk_hoof_model_0610')
 need(repair.SOURCE_SHA==SOURCE_SHA and repair.CANON==CANON,
      'PACKET_MODEL_DECLARED_WRONG_SOURCE')
 previous=import_module(repo/PREVIOUS_MODEL,'repl_previous_v068_pinned')
 need(gitblob((repo/PREVIOUS_MODEL).read_bytes())==PREVIOUS_MODEL_BLOB,
      'PREVIOUS_V068_SOLVER_SHA_CHANGED')
 emit('FRONT_SWING_CLEARANCE','STARTING_ON_PINNED_V068_CANONICAL_GLB')
 failures=[]
 model=report=None
 for profile in repair.PROFILES:
  emit('BOUNDED_FRONT_SWING_PROFILE',str(profile))
  try:
   model,report=repair.make_candidate(source,base,previous,profile,
                                     progress=lambda v:emit('PROGRESS',v))
   emit('PROFILE_PHYSICAL_HOOF_CLEARANCE_PASS',str(profile))
   break
  except (repair.Blocked, previous.Blocked) as exc:
   reason=str(exc)
   failures.append({'profile':list(profile),'reason':reason})
   emit('PROFILE_DIAGNOSIS',str(profile)+':'+reason[:400])
   # Explore only predictable profile-dependent shape/clearance failures.
   # Source/rigger/channel errors must not be masked by another profile.
   if not reason.startswith(('CLEARANCE_', 'ANATOMICAL_PROFILE_')):
    diagnostic={'campaign':PROJECT,'version':VER,'source_sha256':SOURCE_SHA,
                'status':'BLOCKED_CANONICAL_PRESERVED',
                'attempted_profiles':failures,'reason':reason,
                'note':'No Git mutation, threshold weakening, or alternate bone mapping'}
    blocked_report(downloads,diagnostic)
    raise Blocked('NONRECOVERABLE_RIG_OR_VALIDATION_GATE:'+reason)
  except Exception as exc:
   # Never retry programming defects as though they were anatomical failures.
   # Preserve the exact source and an actionable exception receipt.
   diagnostic={'campaign':PROJECT,'version':VER,'status':'BLOCKED_PROGRAMMING_EXCEPTION_CANONICAL_PRESERVED',
      'source_sha256':SOURCE_SHA,'profile':list(profile),
      'exception_type':type(exc).__name__,'exception':str(exc),
      'traceback':traceback.format_exc(),
      'prior_profile_failures':failures,
      'note':'No candidate committed. Programmer error is not a recoverable anatomy profile.'}
   blocked_report(downloads,diagnostic)
   raise Blocked('PROGRAMMING_EXCEPTION__CANONICAL_UNCHANGED:'+type(exc).__name__+':'+str(exc)) from exc
 if model is None:
  diagnostic={'campaign':PROJECT,'version':VER,'source_sha256':SOURCE_SHA,
              'status':'BLOCKED_PRESERVED_CANONICAL',
              'attempted_profiles':failures,
              'note':'Front clearance unsolved within approved 20-30-degree shoulder range; no Git mutation'}
  blocked_report(downloads,diagnostic)
  raise Blocked('BOUNDED_FRONT_SWING_CLEARANCE_UNSATISFIED__CANONICAL_UNCHANGED')
 report['recovery_profiles_attempted']=failures
 emit('PHYSICAL_FRONT_UNDERSIDE_CLEARANCE_MIN',report['min_mid_clearance'])
 emit('HIND_LEG_CHANNELS','BITWISE_PRESERVED')
 emit('ACTUAL_TERMUX_MODEL_SHA256',sha(model))
 emit('FRONT_SWING_CLEARANCE','NUMERIC_VALIDATION_ON_ACTUAL_SOURCE_PASS')
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
