#!/usr/bin/env python3
"""Single-GLB Termux Git integration of cartoon four-beat FK-hoof walk v0.6.8.

Input/output: one canonical assets/repl/Repl.glb (same path).
Human visual verdict remains separate from full skinned-model numeric pass.
One downloaded ZIP includes all payloads; Git mutation is ONLY via Termux.
"""
from __future__ import annotations
import argparse,base64,datetime as dt,hashlib,importlib.util,json,os
from pathlib import Path
import shutil,subprocess,sys,tempfile,traceback

sys.dont_write_bytecode=True
VER='0.6.8'
PROJECT='REPL_CARTOON_FK_HOOF_WALK'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BRANCH='main'
KNOWN_PARENT_HEAD='aa447cc39b3a4664b2d05d71fdbb41d150c43131'
CANON='assets/repl/Repl.glb'
MANIFEST='assets/repl/CANONICAL_MODEL.json'
README='README.md'
SOURCE_SHA='c3209b404b5c50842591cfa654142d2f0d84d27eb1acf7779b8d4d504d4508af'
SOURCE_BLOB='d5b57ffc1a491f96faa5b6ed4e16dd1a3a3477c1'
COMPATIBILITY_HOST_SAMPLE_SHA='2ca4879d215321b246b89ccb7b534a85cbca2d413588a45e5ad80497c9190d61' # reconstructed v0.6.5 track structure; NOT production source bytes
BASE_ENGINE='campaigns/repl_hair_bind_v0_1_0.py'
BASE_ENGINE_BLOB='33ca93660f3d5858d4496027902b9b7a7e44d800'
GIZMO_JS='campaigns/repl_tail_gizmo_v0_4_0.js'
GIZMO_JS_BLOB='1b4396ed0027a0a75baed840d7ed741e57c58a92'
POSE_PATCH='campaigns/repl_pose_lab_bones_patch_v0_6_6.py'
POSE_PATCH_BLOB='73e36078a7be40c4482a6c35c408afe67ed64d77'
POSE_JS='campaigns/repl_pose_lab_bones_v0_6_6.js'
POSE_JS_BLOB='d4d41cd9dc68bf8f640a436fef9ce6c303f1e239'
CAMPAIGN_FILES={
 'campaigns/repl_cartoon_fk_hoof_model_v0_6_8.py':'model.py',
 'campaigns/repl_cartoon_fk_hoof_driver_v0_6_8.py':'driver.py',
 'campaigns/repl_cartoon_fk_hoof_viewer_v0_6_8.html.in':'viewer.html.in',
 'campaigns/repl_cartoon_fk_hoof_blender_review_v0_6_8.py':'blender_review.py',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.8.sh':'run-termux.sh',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.8_CONTRACT.json':'contract.json',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.8_SELFTEST.py':'selftest.py',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.8_PACKET_MANIFEST.json':'../manifest.json',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.8_README.md':'../README.md',
}
OUT_HTML='REPL_CARTOON_FK_HOOF_WALK_v0.6.8_TEXTURED_POSE_LAB.html'
OUT_REPORT='REPL_CARTOON_FK_HOOF_WALK_v0.6.8_report.json'
OUT_RECEIPT='REPL_CARTOON_FK_HOOF_WALK_v0.6.8_RECEIPT.txt'

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
      'SOURCE_NOT_EXACT_v0.6.5_CANONICAL_GLB')
 need(gout(repo,'rev-parse','HEAD:'+CANON)==SOURCE_BLOB,'GIT_SOURCE_BLOB_CHANGED')
 for name,blob in ((BASE_ENGINE,BASE_ENGINE_BLOB),(GIZMO_JS,GIZMO_JS_BLOB),(POSE_PATCH,POSE_PATCH_BLOB),(POSE_JS,POSE_JS_BLOB)):
  need((repo/name).is_file(),'GIT_OWNED_ENGINE_MISSING:'+name)
  need(gout(repo,'hash-object','--',name)==blob,'ENGINE_OR_GIZMO_UNEXPECTED_EDIT:'+name)
 data=json.loads((repo/MANIFEST).read_text('utf8'))
 need(data.get('canonical_glb_path')==CANON,'MANIFEST_PATH_INVALID')
 need(data.get('active_model',{}).get('sha256')==SOURCE_SHA and
      data['active_model'].get('version')=='0.6.5',
      'MANIFEST_ACTIVE_MODEL_NOT_v0.6.5')
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
   'Repl · Cartoon FK-Hoof Walk v0.6.8 + Pose Lab')
 template=template.replace('Repl · Pose Lab bone controls v0.6.6',
   'Repl · Cartoon FK-Hoof Walk v0.6.8')
 template=template.replace('This is a reversible pose reference, not a new walk animation.',
   'Inspect the new v0.6.8 walk; pose edits are temporary and do not change the model.')
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
  'owner_visual_acceptance':'REJECTED_v0.6.5_HOOF_MASS_COLLAPSE_WRONG_TOE_ROTATION',
  'owner_diagnostic':'Pose Lab v0.6.6 user manual demonstration; NOT pose keyframes'}
 active=dict(old)
 for obsolete in ('observed_mid_swing_joint_angles','peak_swing_distal_displacement',
       'max_adjacent_joint_rotation_change','visible_sagittal_arc_in_world_space',
       'swing_surface_min_y','min_swing_hoof_surface_y','foreleg_ik_target_error'):
  active.pop(obsolete,None)
 active.update({'version':VER,'campaign':PROJECT,'path':CANON,
  'sha256':sha(model),'git_blob_sha1':gitblob(model),
  'joint_count':50,'node_count':53,'animations':6,
  'mode':'CARTOON_FOUR_BEAT_FORWARD_TRAVEL_FK_HOOF',
  'toe_masses':'LOCAL_FK_REST__NO_WORLD_PIN__NO_ANIMATED_TIP_DEFORMERS',
  'stance_contact_verification':'TRAJECTORY_OF_STABLE_MESH_PATCH__NOT_OLD_TO_NEW_POSE_DELTA',
  'protected_hoof_bones':sorted(['Bone_012','Bone_018','Bone_023','Bone_028']),
  'protected_front_middle_joints':['Bone_014','Bone_020'],
  'cartoon_swing_driver_degrees':{
    'LF':{'Bone_013':52},'RF':{'Bone_019':52},
    'LH':{'Bone_026':12,'Bone_025':-14,'Bone_024':38},
    'RH':{'Bone_031':12,'Bone_030':-14,'Bone_029':38}},
  'measured_swing_driver_angles':report['driver_mid_swing_delta_deg'],
  'measured_swing_segment_angles':report['world_segment_mid_swing_angles'],
  'max_keyframe_rotation_step_deg':report['max_keyframe_rotation_step_deg'],
  'swing_surface_min_y':report['min_swing_hoof_mesh_y'],
  'root_forward_travel':.96,'gait_phasing':'PRESERVED',
  'accepted_mane_weights':'UNCHANGED','tail_pivot':'APPROVED_v0.5.2_PRESERVED',
  'all_previous_animations':'PRESERVED',
  'review_html_sha256':sha(html),'human_visual_acceptance':'PENDING'})
 data['active_model']=active;data['status']='CARTOON_FK_HOOF_v0.6.8__HUMAN_VISUAL_PENDING'
 data['single_canonical_glb_count']=1;data['later_hair_motion_results_in_repo']=True
 data['owner_rules']=list(dict.fromkeys(list(data.get('owner_rules',[]))+[
   'Owner observed v0.6.5 hoof-tip bones squash/rotate incorrectly despite middle forejoint working',
   'v0.6.6 Pose Lab diagnostic demonstrates usable ankle and leg signs, NOT intended keyframe values',
   'Do not rotate hoof-mass/toe deformation bones as swing IK targets. Keep local FK rest orientation',
   'Protect approved front middle-joint channels and existing four-beat root travel/mane/tail',
   'Make visibly exaggerated cartoon hoof swing with independently checked four-leg skinned result',
   'Only one canonical assets/repl/Repl.glb; owner visual acceptance still required']))
 return json.dumps(data,indent=2,sort_keys=True)+'\n'

def append_readme(old):
 heading='## Cartoon horse walk with FK-protected hoof mass v0.6.8'
 need(heading not in old,'README_V067_HEADING_COLLISION')
 return old.rstrip()+'\n\n'+heading+'\n\n'+(
   'Owner rejected the v0.6.5 ankle/toe animation as stiff, wrongly rotated, '
   'and squashing the hoof mass. A v0.6.6 Pose Lab demonstration identified '
   'the functioning lower hinges and confirmed the hind hoof mass contains '
   'two independent toe-deformation branches per hoof. v0.6.8 leaves those '
   'deformation branches as FK followers, fixes all four hoof-mass parent '
   'rotations at local rest, preserves approved front middle joint motion, and '
   'adds 52-degree cartoon front lower swing plus 38-degree rear lower swing '
   'through the owner-demonstrated local X axes. It preserves existing contact '
   'rhythm, all prior clips, root travel 0.96, mane/approved tail, single GLB. '
   'The textured HTML includes the existing Pose Lab tools; visual acceptance '
   'remains PENDING until owner review.\n')

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
     'commit','-m','Animate Repl cartoon four-beat with FK-locked hoof masses v0.6.8')
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
  'CARTOON_JOINT_PEAK_DELTA_DEG':json.dumps(report['driver_mid_swing_delta_deg'],sort_keys=True),
  'MAX_FK_TIP_LOCAL_CHANGE_DEG':report['protected_tip_max_local_delta_deg'],
  'MAX_ADDED_STANCE_CONTACT_DRIFT':report['max_stance_hoof_mesh_change'],
  'CONTACT_REPAIR_PROFILE_DEG':report.get('stance_repair_limit_deg',0),
  'PEAK_FRAME_TO_FRAME_ROTATION_DEG':report['max_keyframe_rotation_step_deg'],
  'MIN_SWING_SKIN_HEIGHT':min(report['min_swing_hoof_mesh_y'].values()),
  'PROTECTED_FRONT_MIDDLE_JOINTS':'Bone_014,Bone_020',
  'HOOF_MASS':'LOCAL_FK_FROZEN_PARENT_FOLLOWING',
  'ALL_STAGES':'VALIDATED','MANE_TAIL':'UNCHANGED',
  'ROOT_FORWARD_TRAVEL':'0.96','IN_PLACE_WALK':'NONE',
  'HUMAN_VISUAL_VERDICT':'PENDING',
  'STATUS':'REMOTE_SINGLE_CANONICAL_CARTOON_FK_HOOF_WALK_READBACK_VERIFIED'}
 data=('\n'.join(k+'='+str(v) for k,v in fields.items())+'\n').encode('utf8')
 publish(downloads/OUT_RECEIPT,data)
 emit('RECEIPT_PATH',str(downloads/OUT_RECEIPT))
 for k,v in fields.items():emit(k,v)

def optional_blender(repo,packet,downloads):
 exe=shutil.which('blender')
 if not exe:emit('BLENDER_RENDER','NOT_ON_TERMUX_PATH__FULL_TEXTURED_HTML_READY');return
 folder=downloads/'REPL_CARTOON_FK_HOOF_WALK_v0.6.8_blender'
 folder.mkdir(parents=True,exist_ok=True)
 command=[exe,'--background','--factory-startup','--python',
   str(packet/'blender_review.py'),'--','--glb',str(repo/CANON),
   '--output',str(folder)]
 try:
  result=run(command,check=False,timeout=420)
  publish(folder/'blender_run_v0.6.8.log',(result.stdout+'\n'+result.stderr)[-15000:].encode('utf8'))
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
 work=Path.home()/'.local'/'share'/'repl-campaigns'/'cartoon-fk-hoof-v0.6.8'
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
 base=import_module(repo/BASE_ENGINE,'repl_locked_base_for_cartoon067')
 base.EXPECTED_JOINTS=50
 repair=import_module(packet/'model.py','repl_cartoon_fk_hoof_model_067')
 need(repair.SOURCE_SHA==SOURCE_SHA and repair.CANON==CANON,
      'PACKET_MODEL_DECLARED_WRONG_SOURCE')
 emit('CARTOON_FK_HOOF_WALK','STARTING_ON_PINNED_CANONICAL_GLB')
# Recover expected contact failures automatically, preserving contract locks.
 # The first profile is untouched FK; subsequent profiles permit bounded
 # corrections ONLY on the same lower-leg driver, never on the hoof itself.
 failures=[]
 model=report=None
 for limit in (0,12,24,36):
  emit('RECOVERY_STANCE_PROFILE_DEGREES',limit)
  try:
   model,report=repair.make_candidate(source,base,progress=lambda v:emit('PROGRESS',v),
                                       stance_repair_limit=limit)
   emit('RECOVERY_PROFILE_PASS',limit)
   break
  except repair.Blocked as exc:
   reason=str(exc)
   failures.append({'profile':limit,'reason':reason})
   emit('RECOVERY_PROFILE_DIAGNOSIS',str(limit)+':'+reason)
   # Only physical-contact problems are eligible for repair. Anatomy, source,
   # mesh penetration and direction failures are not license to guess.
   if not reason.startswith(('PLANTED_HOOF_ADDED_DRIFT:',
                             'PLANTED_HOOF_ABSOLUTE_DRIFT:')):
    raise Blocked('ANATOMICAL_OR_OTHER_NONRECOVERABLE_GATE:'+reason)
 if model is None:
  diagnostics={'campaign':PROJECT,'version':VER,'source_sha256':SOURCE_SHA,
               'status':'BLOCKED_PRESERVED_CANONICAL',
               'recovery_profiles':failures,'note':'No threshold relaxed; no Git mutation'}
  publish(downloads/('REPL_CARTOON_FK_HOOF_WALK_v0.6.8_BLOCKED.json'),
          (json.dumps(diagnostics,indent=2,sort_keys=True)+'\n').encode('utf8'))
  raise Blocked('ALL_BOUNDED_CONTACT_RECOVERY_PROFILES_FAILED__CANONICAL_UNCHANGED')
 report['recovery_profiles_attempted']=failures

 emit('COMPATIBILITY_HOST_SAMPLE_SHA',COMPATIBILITY_HOST_SAMPLE_SHA)
 emit('HOST_SAMPLE_SAME_SOURCE_BYTES','NO__REAL_PRODUCTION_SOURCE_IS_SHA_PINNED')
 emit('ACTUAL_TERMUX_MODEL_SHA256',sha(model))
 emit('CARTOON_FK_HOOF_WALK','NUMERIC_VALIDATION_ON_ACTUAL_SOURCE_PASS')
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
