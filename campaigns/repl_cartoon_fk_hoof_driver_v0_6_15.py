#!/usr/bin/env python3
"""Single-GLB Termux Git integration of cartoon four-beat FK-hoof walk v0.6.15.

Input/output: one canonical assets/repl/Repl.glb (same path).
Human visual verdict remains separate from full skinned-model numeric pass.
One downloaded ZIP includes all payloads; Git mutation is ONLY via Termux.
"""
from __future__ import annotations
import argparse,base64,datetime as dt,hashlib,importlib.util,json,os
from pathlib import Path
import shutil,subprocess,sys,tempfile,traceback

sys.dont_write_bytecode=True
VER='0.6.15'
PROJECT='REPL_CARTOON_FK_HOOF_WALK'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BRANCH='main'
KNOWN_PARENT_HEAD='f0927b29e3525018999a223f219c38866dc9b9c0'
CANON='assets/repl/Repl.glb'
MANIFEST='assets/repl/CANONICAL_MODEL.json'
README='README.md'
SOURCE_SHA='976d8f2b3da32a01bb99c5dfbce00bc28df2db702836a0ec8337eda1573137ab'
SOURCE_BLOB='e839cdab19e82f3c68471c80bfee9d730f1948a4'
PREVIOUS_MODEL='campaigns/repl_cartoon_fk_hoof_model_v0_6_8.py'
FRONT_MODEL='campaigns/repl_cartoon_fk_hoof_model_v0_6_10.py'
FRONT_MODEL_BLOB='1c52ffd39596d4baab93adb317c031f3ae3f4252'
REFERENCE_COMMIT='859a74c72cf0d8c35e54b4128119603976f8daa9'
REFERENCE_GLB_SHA='eff0c604ca56ba58543c7a477bffc0e22e3c23f1d5da00bdbf1ea62369f27509'
REFERENCE_GLB_BLOB='ee68428d9edf305c22e1bd4aa1fca7ad61e993e1'
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
 'campaigns/repl_cartoon_fk_hoof_model_v0_6_15.py':'model.py',
 'campaigns/repl_cartoon_fk_hoof_trajectory_v0_6_15.json':'trajectory.json',
 'campaigns/repl_cartoon_fk_hoof_regression_v0_6_15.py':'regression.py',
  'campaigns/repl_cartoon_fk_hoof_git_transport_regression_v0_6_15.py':'git_transport_regression.py',
 'campaigns/repl_cartoon_fk_hoof_driver_v0_6_15.py':'driver.py',
 'campaigns/repl_cartoon_fk_hoof_viewer_v0_6_15.html.in':'viewer.html.in',
 'campaigns/repl_cartoon_fk_hoof_blender_review_v0_6_15.py':'blender_review.py',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.15.sh':'run-termux.sh',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.15_CONTRACT.json':'contract.json',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.15_SELFTEST.py':'selftest.py',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.15_PACKET_MANIFEST.json':'../manifest.json',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.15_README.md':'../README.md',
}
OUT_HTML='REPL_CARTOON_FK_HOOF_WALK_v0.6.15_TEXTURED_POSE_LAB.html'
OUT_REPORT='REPL_CARTOON_FK_HOOF_WALK_v0.6.15_report.json'
OUT_RECEIPT='REPL_CARTOON_FK_HOOF_WALK_v0.6.15_RECEIPT.txt'
LAST_BLOCKED_DIAGNOSTIC=None

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
 try:
  p=subprocess.run(command,cwd=str(cwd) if cwd else None,env=env,
     stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
     timeout=timeout,check=False)
 except subprocess.TimeoutExpired as exc:
  raise Blocked('COMMAND_TIMEOUT:'+command[0]+':'+str(timeout)+'s') from exc
 except OSError as exc:
  raise Blocked('COMMAND_EXECUTION_ERROR:'+command[0]+':'+type(exc).__name__) from exc
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
 global LAST_BLOCKED_DIAGNOSTIC
 payload=(json.dumps(diagnostic,indent=2,sort_keys=True,allow_nan=False)+'\n').encode('utf8')
 path=downloads/('REPL_CARTOON_FK_HOOF_WALK_v0.6.15_BLOCKED_'+sha(payload)[:12]+'.json')
 publish(path,payload)
 emit('CAMPAIGN_DIAGNOSTIC_PATH',str(path))
 LAST_BLOCKED_DIAGNOSTIC=str(path)
 return path

def _seed_is_pinned(repo):
 """Use only committed and hash-locked git objects from previous campaigns.

 Does not touch a prior checkout, even when its worktree is dirty. Never
 mistake a local path with an unrelated remote for the authorized repository.
 """
 try:
  repo=Path(repo)
  if not (repo/'.git').is_dir():return False
  if gout(repo,'remote','get-url','origin')!=REMOTE:return False
  if gout(repo,'rev-parse','HEAD')!=KNOWN_PARENT_HEAD:return False
  if gout(repo,'rev-parse','HEAD:'+CANON)!=SOURCE_BLOB:return False
  if not (repo/CANON).is_file():return False
  if file_sha(repo/CANON)!=SOURCE_SHA:return False
  return True
 except (Blocked,ValueError,RuntimeError,OSError):return False


def _assert_pinned_checkout(repo):
 need((repo/'.git').is_dir(),'BOOTSTRAP_NOT_GIT')
 need(gout(repo,'remote','get-url','origin')==REMOTE,'BOOTSTRAP_WRONG_REMOTE')
 need(gout(repo,'rev-parse','HEAD')==KNOWN_PARENT_HEAD,'BOOTSTRAP_HEAD_CHANGED_NO_OVERWRITE')
 need(gout(repo,'rev-parse','HEAD:'+CANON)==SOURCE_BLOB,'BOOTSTRAP_CANONICAL_BLOB_MISMATCH')
 need(file_sha(repo/CANON)==SOURCE_SHA,'BOOTSTRAP_CANONICAL_SOURCE_BYTES_MISMATCH')
 need(not git(repo,'status','--porcelain','--untracked-files=all').stdout.strip(),
      'BOOTSTRAP_DIRTY_NOT_SAFE')


def _local_cache_candidates(work):
 parent=work.parent
 def order(path):
  import re
  v=re.search(r'v(\d+)\.(\d+)\.(\d+)',path.parent.name)
  return tuple(int(x) for x in v.groups()) if v else (0,0,0)
 return sorted((x for x in parent.glob('cartoon-fk-hoof-v*/repo')
                if x.resolve()!=work.joinpath('repo').resolve()),key=order,reverse=True)


def _offline_seed_copy(source,stage):
 """Copy committed Git history only. No mutation to the source checkout."""
 if stage.exists():
  need(not (stage/'.git').exists(),'STAGING_ALREADY_INITIALIZED')
  need(not any(stage.iterdir()),'STAGING_DIRECTORY_NOT_EMPTY')
  stage.rmdir()
 run(['git','clone','--quiet','--local','--no-hardlinks','--single-branch',
      '--branch',BRANCH,'--no-tags',str(source),str(stage)],timeout=160)
 git(stage,'remote','set-url','origin',REMOTE)
 _assert_pinned_checkout(stage)


def _network_bootstrap(work):
 """Resume a private fetch cache. Never issue a full-history clone."""
 stage=work/'network-bootstrap'
 if not stage.exists():
  stage.mkdir(parents=True)
  run(['git','init','-q','-b',BRANCH,str(stage)],timeout=20)
  git(stage,'remote','add','origin',REMOTE)
 else:
  need((stage/'.git').is_dir(),'NETWORK_CACHE_NOT_GIT__PRESERVED')
  need(gout(stage,'remote','get-url','origin')==REMOTE,
       'NETWORK_CACHE_WRONG_REMOTE__PRESERVED')
  status=git(stage,'status','--porcelain','--untracked-files=all').stdout.strip()
  need(not status,'NETWORK_CACHE_DIRTY__PRESERVED')
  # A previously verified bootstrap is reusable without another network call.
  try:
   _assert_pinned_checkout(stage)
   emit('GIT_FETCH_CACHE','COMPLETE_PINNED_SOURCE_REUSED')
   return stage
  except Blocked:
   pass
 # Try partial/shallow fetch first; retry network failures with a second,
 # compatible shallow fetch into the SAME private object store.
 attempts=[
  (['git','-c','protocol.version=2','fetch','--quiet','--no-tags',
     '--filter=blob:none','--depth=8','origin',
     '+refs/heads/main:refs/remotes/origin/main'],150),
  (['git','-c','protocol.version=2','fetch','--quiet','--no-tags',
     '--depth=8','origin',
     '+refs/heads/main:refs/remotes/origin/main'],195),
 ]
 errors=[]
 for i,(cmd,timeout) in enumerate(attempts,1):
  emit('GIT_FETCH_ATTEMPT',str(i)+'_OF_'+str(len(attempts)))
  try:
   result=run(cmd,cwd=stage,check=False,timeout=timeout)
   if result.returncode==0:
    emit('GIT_FETCH_ATTEMPT_RESULT','PASS_'+str(i));break
   errors.append('attempt_'+str(i)+'_exit_'+str(result.returncode)+':'+result.stderr[-180:].replace('\n',' '))
  except Blocked as exc:errors.append('attempt_'+str(i)+':'+str(exc))
 else:
  raise Blocked('GIT_NETWORK_SHALLOW_FETCH_EXHAUSTED__PRIVATE_CACHE_RETAINED:'+ ';'.join(errors))
 fetched=gout(stage,'rev-parse','refs/remotes/origin/main')
 need(fetched==KNOWN_PARENT_HEAD,'REMOTE_MOVED_AFTER_PIN__NO_OVERWRITE:'+fetched)
 # Do not reset, stash, or overwrite the previous locally committed tree.
 head=git(stage,'rev-parse','--verify','HEAD',check=False)
 if head.returncode==0:
  need(head.stdout.strip()==KNOWN_PARENT_HEAD,'NETWORK_CACHE_HEAD_UNEXPECTED__PRESERVED')
 else:
  git(stage,'checkout','-q','-B',BRANCH,'refs/remotes/origin/main')
 _assert_pinned_checkout(stage)
 return stage


def checkout(work):
 repo=work/'repo'
 if repo.exists():
  need((repo/'.git').is_dir(),'STATE_CHECKOUT_NOT_GIT')
  need(gout(repo,'remote','get-url','origin')==REMOTE,'CAMPAIGN_GIT_REMOTE_MISMATCH')
  need(not git(repo,'status','--porcelain','--untracked-files=all').stdout.strip(),
       'CAMPAIGN_REPO_DIRTY_NO_AUTO_RESET')
  head=gout(repo,'rev-parse','HEAD')
  remote=git(repo,'rev-parse','--verify','refs/remotes/origin/main',check=False)
  need(remote.returncode==0,'LOCAL_GIT_REMOTE_TRACKING_REF_MISSING')
  if head!=remote.stdout.strip():
   need(git(repo,'merge-base','--is-ancestor',remote.stdout.strip(),head,check=False).returncode==0,
        'LOCAL_AHEAD_BRANCH_NOT_DESCENDED_FROM_REMOTE')
  emit('GIT_CHECKOUT_MODE','RESUME_EXISTING_PRIVATE_REPO_NO_NETWORK_CLONE')
  return repo
 # If a prior version already fetched the original and historical bytes,
 # reuse them without network access, modifying only this version's checkout.
 for seed in _local_cache_candidates(work):
  if not _seed_is_pinned(seed):continue
  stage=Path(tempfile.mkdtemp(prefix='.repl0615-local-',dir=work))
  try:
   _offline_seed_copy(seed,stage)
   os.replace(stage,repo)
   emit('GIT_CHECKOUT_MODE','VERIFIED_PREVIOUS_CAMPAIGN_CACHE')
   emit('GIT_CACHE_SOURCE',str(seed))
   return repo
  except (Blocked,OSError) as exc:
   emit('GIT_CACHE_SOURCE_REJECTED',seed.parent.name+':'+str(exc).split(':')[0])
  finally:
   if stage.exists():shutil.rmtree(stage)
 # The network path is shallow, resumable and bounded; full clone forbidden.
 emit('GIT_CHECKOUT_MODE','SHALLOW_BOUNDED_GIT_FETCH')
 stage=_network_bootstrap(work)
 os.replace(stage,repo)
 _assert_pinned_checkout(repo)
 return repo

def one_model(repo,ref='HEAD'):
 models=[x for x in gout(repo,'ls-tree','-r','--name-only',ref).splitlines()
   if x.lower().endswith('.glb')]
 need(models==[CANON],'REPO_GLB_MULTIPLICATION_OR_PATH_MISMATCH:'+repr(models))

def verify_source(repo):
 one_model(repo)
 model=(repo/CANON).read_bytes()
 need(sha(model)==SOURCE_SHA and gitblob(model)==SOURCE_BLOB,
      'SOURCE_NOT_EXACT_v0.6.10_CANONICAL_GLB')
 need(gout(repo,'rev-parse','HEAD:'+CANON)==SOURCE_BLOB,'GIT_SOURCE_BLOB_CHANGED')
 for name,blob in ((BASE_ENGINE,BASE_ENGINE_BLOB),(GIZMO_JS,GIZMO_JS_BLOB),(POSE_PATCH,POSE_PATCH_BLOB),(POSE_JS,POSE_JS_BLOB),(PREVIOUS_MODEL,PREVIOUS_MODEL_BLOB),(FRONT_MODEL,FRONT_MODEL_BLOB)):
  need((repo/name).is_file(),'GIT_OWNED_ENGINE_MISSING:'+name)
  need(gout(repo,'hash-object','--',name)==blob,'ENGINE_OR_GIZMO_UNEXPECTED_EDIT:'+name)
 data=json.loads((repo/MANIFEST).read_text('utf8'))
 need(data.get('canonical_glb_path')==CANON,'MANIFEST_PATH_INVALID')
 need(data.get('active_model',{}).get('sha256')==SOURCE_SHA and
      data['active_model'].get('version')=='0.6.10',
      'MANIFEST_ACTIVE_MODEL_NOT_v0.6.10')
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
   'Repl · Cartoon FK-Hoof Walk v0.6.15 + Pose Lab')
 template=template.replace('Repl · Pose Lab bone controls v0.6.6',
   'Repl · Cartoon FK-Hoof Walk v0.6.15')
 template=template.replace('This is a reversible pose reference, not a new walk animation.',
   'Inspect the new v0.6.15 walk; pose edits are temporary and do not change the model.')
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
  'owner_visual_acceptance':'PARTIAL_v0.6.10_CORRECT_JOINTS_BUT_PRANCING',
  'owner_next_correction':'Bring peak front clearance to 25-33 percent and include subtle loaded-corner settle'}
 active=dict(old)
 for obsolete in ('measured_front_hoof_clearance','measured_front_swing_angles',
  'front_swing_profile','minimum_mid_swing_clearance','minimum_early_swing_clearance',
  'owner_visual_goal','max_keyframe_rotation_step_deg'):
  active.pop(obsolete,None)
 active.update({'version':VER,'campaign':PROJECT,'path':CANON,
  'sha256':sha(model),'git_blob_sha1':gitblob(model),
  'joint_count':50,'node_count':53,'animations':6,
  'mode':'LOW_FOREHOOF_ARC_AND_SUBTLE_CORNER_SAG',
  'controlled_front_bones':['Bone_014','Bone_015','Bone_020','Bone_021'],
  'controlled_body_bones':['Bone_000'],
  'forehoof_clearance_ratio_goal':[.25,.33],
  'measured_hoof_clearance':report['front_hoof_clearance'],
  'measured_rig_audit':report['rig_audit'],
  'measured_support_side_sag':report['loaded_shoulder_drop'],
  'max_stance_hoof_movement':report['max_stance_vertex_delta'],
  'body_profile':report['profile'],
  'precomputed_measured_trajectory_sha256':report['trajectory_sha256'],
  'preserved_hind_leg_tracks':'IDENTICAL_TO_v0.6.10',
  'preserved_front_distal_tracks':'IDENTICAL_TO_v0.6.10',
  'mane_tail_and_nonwalk_clips':'UNCHANGED',
  'root_forward_travel':.96,
  'tested_real_mesh_frame_pairs':report['tested_physical_frames'],
  'gait_phasing':'UNCHANGED',
  'review_html_sha256':sha(html),
  'human_visual_acceptance':'PENDING'})
 data['active_model']=active
 data['status']='MEASURED_GLTF_LOW_FOREHOOF_v0.6.15__HUMAN_VISUAL_PENDING'
 data['single_canonical_glb_count']=1
 data['owner_rules']=list(dict.fromkeys(list(data.get('owner_rules',[]))+[
   'Owner sees v0.6.10 front-hoof prance; target one quarter to one third current clearance',
   'Actual reference horse barely clears ground despite significant front joint arc',
   'Keep real rig unusual toe bones, upper and middle leg curvature, rear local bone animations',
   'Add small support-side roll/vertical settle in stage 2 and 3 while guarding contact',
   'No cosmetic threshold bypass; actual skinned vertices, not screenshot pixels, govern clearance',
   'One canonical GLB, forward travel and existing mane/tail unchanged; human verdict pending']))
 return json.dumps(data,indent=2,sort_keys=True)+'\n'

def append_readme(old):
 heading='## Repl measured low front walk v0.6.15'
 need(heading not in old,'README_MEASURED_WALK_ALREADY_EXISTS')
 return old.rstrip()+'\n\n'+heading+'\n\n'+(
  'The v0.6.10 canonical model was decoded and its skinned hoof vertices measured '
  'directly. The signed, source-locked trajectory in campaigns/ was optimized '
  'against those physical geometry measurements before the packet was built. '
  'Termux re-measures every hoof through all 97 frames in the three forward '
  'walk clips before allowing Git mutation. Front peak swing lift is targeted '
  'at 25-33% of v0.6.10, with toe-off clearance greater than 0.0035 model '
  'units in the actual deformed mesh and restrained load-side body settle. '
  'Only four front shoulder/middle rotation channels and stage 2/3 root Y/roll '
  'can change. Rear joints, distal hoof and toe joints, skin, geometry, hair, '
  'earlier clips, root X/Z and forward travel remain unchanged. One canonical '
  'GLB path. Human visual acceptance required.\n')

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
     'commit','-m','Lower Repl forehoof arc and add measured loaded-corner sag v0.6.15')
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
  'FOREHOOF_RATIO_BY_STAGE':json.dumps(report['front_hoof_clearance'],sort_keys=True),
  'WEIGHT_TRANSFER_PROFILE':json.dumps(report['profile'],sort_keys=True),
  'PHYSICAL_STANCE_MAX_DELTA':report['max_stance_vertex_delta'],
  'SUPPORT_SIDE_SAG':json.dumps(report['loaded_shoulder_drop'],sort_keys=True),
  'REAR_LEG_KEYFRAMES':'IDENTICAL_V0610',
  'FRONT_DISTAL_KEYFRAMES':'IDENTICAL_V0610',
  'HOOF_MASSES':'UNCHANGED_V0610',
  'ALL_STAGES':'VALIDATED','MANE_TAIL':'UNCHANGED',
  'ROOT_FORWARD_TRAVEL':'0.96','IN_PLACE_WALK':'NONE',
  'HUMAN_VISUAL_VERDICT':'PENDING',
  'STATUS':'REMOTE_SINGLE_CANONICAL_LOW_FOREHOOF_READBACK_VERIFIED'}
 data=('\n'.join(k+'='+str(v) for k,v in fields.items())+'\n').encode('utf8')
 publish(downloads/OUT_RECEIPT,data)
 emit('RECEIPT_PATH',str(downloads/OUT_RECEIPT))
 for k,v in fields.items():emit(k,v)

def optional_blender(repo,packet,downloads):
 exe=shutil.which('blender')
 if not exe:emit('BLENDER_RENDER','NOT_ON_TERMUX_PATH__FULL_TEXTURED_HTML_READY');return
 folder=downloads/'REPL_CARTOON_FK_HOOF_WALK_v0.6.15_blender'
 folder.mkdir(parents=True,exist_ok=True)
 command=[exe,'--background','--factory-startup','--python',
   str(packet/'blender_review.py'),'--','--glb',str(repo/CANON),
   '--output',str(folder)]
 try:
  result=run(command,check=False,timeout=420)
  publish(folder/'blender_run_v0.6.15.log',(result.stdout+'\n'+result.stderr)[-15000:].encode('utf8'))
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
 work=Path.home()/'.local'/'share'/'repl-campaigns'/'cartoon-fk-hoof-v0.6.15'
 work.mkdir(parents=True,exist_ok=True)
 emit('CAMPAIGN',PROJECT);emit('VERSION',VER)
 emit('LANE','TERMUX_GIT_ONLY');emit('MODEL_PATH',CANON)
 repo=checkout(work)
 os.chdir(repo)
 emit('RESOLVED_REPO',str(repo.resolve()))
 emit('EXECUTION_DIR',str(Path.cwd()))
 emit('BRANCH',gout(repo,'rev-parse','--abbrev-ref','HEAD'))
 head=gout(repo,'rev-parse','HEAD')
 emit('HEAD',head)
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
 plan=json.loads((packet/'trajectory.json').read_text('utf8'))
 need(plan.get('source_sha256')==SOURCE_SHA,'MEASURED_TRAJECTORY_SOURCE_PIN_MISMATCH')
 emit('MEASURED_TRAJECTORY_SHA256',file_sha(packet/'trajectory.json'))
 emit('V0610_PHYSICAL_FRONT_CLEARANCE','REAL_GLB_FULL_97_FRAME_VALIDATION')
 try:
  model,report=repair.build(source,plan,base,previous,
                            progress=lambda v:emit('PROGRESS',v))
  report['trajectory_sha256']=file_sha(packet/'trajectory.json')
  check=import_module(packet/'regression.py','repl_0615_measured_production_regression')
  passes=check.verify_measurements(report,plan)
  emit('REAL_SKINNED_TRAJECTORY_VERIFICATION','PASS_1164_SAMPLE_PAIRS')
  emit('PRODUCTION_MODEL_FROZEN_MEASUREMENTS',str(passes))
 except Exception as exc:
  blocked_report(downloads,{'campaign':PROJECT,'version':VER,
    'status':'BLOCKED_REAL_GLB_VALIDATION_CANONICAL_PRESERVED',
    'source_sha256':SOURCE_SHA,
    'trajectory_sha256':file_sha(packet/'trajectory.json'),
    'exception_type':type(exc).__name__,'exception':str(exc),
    'traceback':traceback.format_exc()})
  raise Blocked('REAL_GLTF_VALIDATION_FAILED__UNCHANGED:'+type(exc).__name__+':'+str(exc)) from exc
 emit('FRONT_HOOF_RATIO',str({k:v['verified_ratio'] for k,v in report['front_hoof_clearance'].items()}))
 emit('BODY_CORNER_SAG',str(report['loaded_shoulder_drop']))
 emit('HIND_LEG_CHANNELS','BITWISE_PRESERVED')
 emit('ACTUAL_TERMUX_MODEL_SHA256',sha(model))
 emit('REAL_SKINNED_HOOF_AND_BODY','NUMERIC_VALIDATION_PASS')
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
  try:
   downloads=Path.home()/'storage'/'downloads'
   if downloads.is_dir() and LAST_BLOCKED_DIAGNOSTIC is None:blocked_report(downloads,{
     'campaign':PROJECT,'version':VER,'status':'BLOCKED_CANONICAL_STATE_MUST_BE_INSPECTED',
     'exception_type':type(exc).__name__,'reason':str(exc),
     'traceback':traceback.format_exc()})
  except Exception:pass
  emit('CAMPAIGN_STATUS','BLOCKED')
  emit('CAUSE',str(exc).split(':')[0])
  emit('LIVE_CANONICAL_MODEL_STATUS','UNCHANGED_OR_LOCAL_COMMIT_UNPUSHED')
  sys.exit(2)
 except Exception as exc:
  try:
   downloads=Path.home()/'storage'/'downloads'
   if downloads.is_dir() and LAST_BLOCKED_DIAGNOSTIC is None:blocked_report(downloads,{
     'campaign':PROJECT,'version':VER,'status':'PROGRAMMING_EXCEPTION_CANONICAL_STATE_UNVERIFIED',
     'exception_type':type(exc).__name__,'reason':str(exc),
     'traceback':traceback.format_exc()})
  except Exception:pass
  traceback.print_exc()
  emit('CAMPAIGN_STATUS','FAILED')
  emit('CAUSE',type(exc).__name__+':'+str(exc))
  emit('LIVE_CANONICAL_MODEL_STATUS','UNVERIFIED')
  sys.exit(3)
