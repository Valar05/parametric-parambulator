#!/usr/bin/env python3
"""Single-GLB Termux Git integration of cartoon four-beat FK-hoof walk v0.6.17.

Input/output: one canonical assets/repl/Repl.glb (same path).
Human visual verdict remains separate from full skinned-model numeric pass.
One downloaded ZIP includes all payloads; Git mutation is ONLY via Termux.
"""
from __future__ import annotations
import argparse,base64,datetime as dt,hashlib,importlib.util,json,os
from pathlib import Path
import shutil,subprocess,sys,tempfile,traceback

sys.dont_write_bytecode=True
VER='0.6.17'
PROJECT='REPL_CARTOON_FK_HOOF_WALK'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BRANCH='main'
KNOWN_PARENT_HEAD='6156c8cd21e7c3f5aca82de0dba7082c211eeb5a'
CANON='assets/repl/Repl.glb'
MANIFEST='assets/repl/CANONICAL_MODEL.json'
README='README.md'
SOURCE_SHA='713a172ef697e04511ef1df625a67436a127e2e7dc8b5c98983a7ccb67f24a85'
EXPECTED_VALIDATED_V0616_OUTPUT_SHA='c6dc250356248e5860e5919568e4103d6c1d2cb6e071e7bb9a0f7ce1f42ee4c1'
MODEL_SOLVER_VERSION='0.6.16'
SOURCE_BLOB='79ac66bf4e0801fbbba5047d0b31969a78ccc0e9'
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
 'campaigns/repl_cartoon_fk_hoof_model_v0_6_17.py':'model.py',
 'campaigns/repl_cartoon_fk_hoof_trajectory_v0_6_17.json':'trajectory.json',
 'campaigns/repl_cartoon_fk_hoof_regression_v0_6_17.py':'regression.py',
 'campaigns/repl_cartoon_fk_hoof_git_transport_regression_v0_6_17.py':'git_transport_regression.py',
 'campaigns/repl_cartoon_fk_hoof_driver_v0_6_17.py':'driver.py',
 'campaigns/repl_cartoon_fk_hoof_viewer_v0_6_17.html.in':'viewer.html.in',
 'campaigns/repl_cartoon_fk_hoof_blender_review_v0_6_17.py':'blender_review.py',
 'campaigns/repl_cartoon_fk_hoof_agents_gate_v0_6_17.py':'agents_gate.py',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.17.sh':'run-termux.sh',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.17_CONTRACT.json':'contract.json',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.17_SELFTEST.py':'selftest.py',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.17_PACKET_MANIFEST.json':'../manifest.json',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.17_README.md':'../README.md',
 'AGENTS.md':'../AGENTS.md',
}
OUT_HTML='REPL_CARTOON_FK_HOOF_WALK_v0.6.17_TEXTURED_POSE_LAB.html'
OUT_REPORT='REPL_CARTOON_FK_HOOF_WALK_v0.6.17_report.json'
OUT_RECEIPT='REPL_CARTOON_FK_HOOF_WALK_v0.6.17_RECEIPT.txt'
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
 path=downloads/('REPL_CARTOON_FK_HOOF_WALK_v0.6.17_BLOCKED_'+sha(payload)[:12]+'.json')
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
      'SOURCE_NOT_EXACT_v0.6.15_CANONICAL_GLB')
 need(gout(repo,'rev-parse','HEAD:'+CANON)==SOURCE_BLOB,'GIT_SOURCE_BLOB_CHANGED')
 for name,blob in ((BASE_ENGINE,BASE_ENGINE_BLOB),(GIZMO_JS,GIZMO_JS_BLOB),(POSE_PATCH,POSE_PATCH_BLOB),(POSE_JS,POSE_JS_BLOB),(PREVIOUS_MODEL,PREVIOUS_MODEL_BLOB),(FRONT_MODEL,FRONT_MODEL_BLOB)):
  need((repo/name).is_file(),'GIT_OWNED_ENGINE_MISSING:'+name)
  need(gout(repo,'hash-object','--',name)==blob,'ENGINE_OR_GIZMO_UNEXPECTED_EDIT:'+name)
 data=json.loads((repo/MANIFEST).read_text('utf8'))
 need(data.get('canonical_glb_path')==CANON,'MANIFEST_PATH_INVALID')
 need(data.get('active_model',{}).get('sha256')==SOURCE_SHA and
      data['active_model'].get('version')=='0.6.15',
      'MANIFEST_ACTIVE_MODEL_NOT_v0.6.15')
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
   'Repl · Cartoon FK-Hoof Walk v0.6.17 + Pose Lab')
 template=template.replace('Repl · Pose Lab bone controls v0.6.6',
   'Repl · Cartoon FK-Hoof Walk v0.6.17')
 template=template.replace('This is a reversible pose reference, not a new walk animation.',
   'Inspect the new v0.6.17 walk; pose edits are temporary and do not change the model.')
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
  'owner_visual_acceptance':'REJECTED_V0615_FRONT_HOOF_KICKING',
  'owner_next_correction':'Bring peak front contact and continuous hoof trajectory with no kicking'}
 active=dict(old)
 for obsolete in ('measured_front_hoof_clearance','measured_front_swing_angles',
  'front_swing_profile','minimum_mid_swing_clearance','minimum_early_swing_clearance',
  'owner_visual_goal','max_keyframe_rotation_step_deg'):
  active.pop(obsolete,None)
 active.update({'version':VER,'campaign':PROJECT,'path':CANON,
  'sha256':sha(model),'git_blob_sha1':gitblob(model),
  'joint_count':50,'node_count':53,'animations':6,
  'mode':'FULL_GROUND_RELATIVE_FOUR_BEAT_FRONT_HOOF',
  'controlled_front_bones':['Bone_014','Bone_015','Bone_020','Bone_021'],
  'controlled_body_bones':[],
  'forehoof_clearance_absolute_goal_units':[.056,.101],
  'measured_hoof_clearance':report['front_hoof_clearance'],
  'measured_rig_audit':report['rig_audit'],
  'preserved_support_side_sag':report['loaded_shoulder_drop'],
  'max_stance_hoof_movement':report['max_stance_vertex_delta'],
  'body_profile':report['profile'],
  'precomputed_measured_trajectory_sha256':report['trajectory_sha256'],
  'preserved_hind_leg_tracks':'IDENTICAL_TO_v0.6.15',
  'preserved_front_distal_tracks':'IDENTICAL_TO_v0.6.15',
  'mane_tail_and_nonwalk_clips':'UNCHANGED',
  'root_forward_travel':.96,
  'tested_real_mesh_frame_pairs':report['tested_physical_frames'],
  'gait_phasing':'UNCHANGED',
  'review_html_sha256':sha(html),
  'human_visual_acceptance':'PENDING'})
 data['active_model']=active
 data['status']='MEASURED_GLTF_LOW_FOREHOOF_v0.6.17__HUMAN_VISUAL_PENDING'
 data['single_canonical_glb_count']=1
 data['owner_rules']=list(dict.fromkeys(list(data.get('owner_rules',[]))+[
   'Rejected v0.6.15: forehoof darts ahead and performs visible kick unrelated to ground contact',
   'Full front-stance world-Z contact lock and no significant reverse or instantaneous forward kick',
   'Front swing arc remains low but moves monotonically forward in world space',
   'Only four front shoulder/middle rotation channels are mutable; distal/hoof/toe and rear locked',
   'Preserve existing v0.6.15 body sag and roll without re-editing any root channel',
   'One canonical GLB, no alternate rig, human visual acceptance is independent of numeric checks']))
 return json.dumps(data,indent=2,sort_keys=True)+'\n'

def append_readme(old):
 heading='## Repl ground-relative forehoof walk v0.6.17'
 need(heading not in old,'README_GROUND_WALK_ALREADY_EXISTS')
 return old.rstrip()+'\n\n'+heading+'\n\n'+(
  'The owner rejected v0.6.15 for a forward hoof kick unrelated to ground contact. '
  'This campaign repairs all 32 frames of both front legs in each walk clip, '
  'including planted stance. Precomputed offsets use physical skinned hoof '
  'measurements from canonical v0.6.10 and the exact authored v0.6.15 motion '
  'formula. An independent runtime validator on the actual pinned v0.6.15 '
  'binary checks all hooves across 97 frames, root movement, support drift, '
  'foot-ground clearance, forward world displacement, and abrupt joint '
  'rotation BEFORE Git mutation. Only Bone_014, Bone_015, Bone_020, Bone_021 '
  'animation channels change. The rear legs, front hoof/toe/distal channels, '
  'root trajectory and loaded-corner sag, all accepted mane/tail assets, '
  'and prior clips remain unchanged. Human visual acceptance remains pending. '
  'The standalone v0.6.17 AGENTS gate installs and reads root AGENTS.md; '
  'prepublication checks forbid historical source filename collisions.\n')

def commit(repo,packet,model,report,html,policy_gate):
 policy_gate.destination_preflight(repo,packet,CAMPAIGN_FILES)
 need(sha(model)!=SOURCE_SHA,'CORRECTED_MODEL_EQUALS_UNCHANGED_INPUT')
 need(sha(model)==EXPECTED_VALIDATED_V0616_OUTPUT_SHA,'VALIDATED_MODEL_BINARY_CHANGED_NO_PUBLICATION')
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
  if dest=='AGENTS.md':
   policy_gate.install(repo,source)
  else:
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
     'commit','-m','Publish validated Repl ground-relative gait and AGENTS boot laws v0.6.17')
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
 agent_remote=git(repo,'show',f'{ref}:AGENTS.md').stdout.encode('utf8')
 need(sha(agent_remote)==sha((repo/'AGENTS.md').read_bytes()),'REMOTE_AGENTS_MD_READBACK_SHA_MISMATCH')
 emit('AGENTS_REMOTE_READBACK','PASS')
 need(gout(repo,'rev-parse',f'{ref}:campaigns/repl_cartoon_fk_hoof_agents_gate_v0_6_17.py')==gitblob((repo/'campaigns/repl_cartoon_fk_hoof_agents_gate_v0_6_17.py').read_bytes()),'REMOTE_AGENTS_HELPER_MISSING')
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
  'FOREHOOF_PHYSICAL_CLEARANCE_BY_STAGE':json.dumps(report['front_hoof_clearance'],sort_keys=True),
  'WEIGHT_TRANSFER_PROFILE':json.dumps(report['profile'],sort_keys=True),
  'PHYSICAL_STANCE_MAX_WORLD_Z_DRIFT':report['max_stance_vertex_delta'],
  'PRESERVED_SUPPORT_SAG':json.dumps(report['loaded_shoulder_drop'],sort_keys=True),
  'REAR_LEG_KEYFRAMES':'IDENTICAL_V0615',
  'FRONT_DISTAL_KEYFRAMES':'IDENTICAL_V0615',
  'HOOF_MASSES':'UNCHANGED_V0615',
  'ALL_STAGES':'VALIDATED','MANE_TAIL':'UNCHANGED',
  'ROOT_FORWARD_TRAVEL':'0.96','IN_PLACE_WALK':'NONE',
  'HUMAN_VISUAL_VERDICT':'PENDING',
  'AGENTS_RULES_GATE':'READ_BEFORE_WORK',
  'AGENTS_REMOTE_GIT_READBACK':'PASS',
  'GAIT_SOLVER_VERSION':'0.6.16_UNCHANGED',
  'VALIDATED_V0616_CANDIDATE_SHA256':EXPECTED_VALIDATED_V0616_OUTPUT_SHA,
  'STATUS':'REMOTE_GROUND_RELATIVE_FRONT_HOOF_READBACK_VERIFIED_HUMAN_PENDING'}
 data=('\n'.join(k+'='+str(v) for k,v in fields.items())+'\n').encode('utf8')
 publish(downloads/OUT_RECEIPT,data)
 emit('RECEIPT_PATH',str(downloads/OUT_RECEIPT))
 for k,v in fields.items():emit(k,v)

def optional_blender(repo,packet,downloads):
 exe=shutil.which('blender')
 if not exe:emit('BLENDER_RENDER','NOT_ON_TERMUX_PATH__FULL_TEXTURED_HTML_READY');return
 folder=downloads/'REPL_CARTOON_FK_HOOF_WALK_v0.6.17_blender'
 folder.mkdir(parents=True,exist_ok=True)
 command=[exe,'--background','--factory-startup','--python',
   str(packet/'blender_review.py'),'--','--glb',str(repo/CANON),
   '--output',str(folder)]
 try:
  result=run(command,check=False,timeout=420)
  publish(folder/'blender_run_v0.6.17.log',(result.stdout+'\n'+result.stderr)[-15000:].encode('utf8'))
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
 policy_gate=import_module(packet/'agents_gate.py','repl_agents_policy_gate_v0617')
 policy_hash=policy_gate.read_gate(packet.parent/'AGENTS.md',packet/'contract.json')
 downloads=Path.home()/'storage'/'downloads'
 need(downloads.is_dir(),'TERMUX_DOWNLOADS_NOT_MOUNTED')
 work=Path.home()/'.local'/'share'/'repl-campaigns'/'cartoon-fk-hoof-v0.6.17'
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
 policy_gate.destination_preflight(repo,packet,CAMPAIGN_FILES)
 base=import_module(repo/BASE_ENGINE,'repl_locked_base_for_front0610')
 base.EXPECTED_JOINTS=50
 repair=import_module(packet/'model.py','repl_cartoon_fk_hoof_model_0610')
 need(repair.VERSION==MODEL_SOLVER_VERSION,'UNAPPROVED_GAIT_SOLVER_VERSION_DRIFT')
 need(repair.SOURCE_SHA==SOURCE_SHA and repair.CANON==CANON,
      'PACKET_MODEL_DECLARED_WRONG_SOURCE')
 previous=import_module(repo/PREVIOUS_MODEL,'repl_previous_v068_pinned')
 need(gitblob((repo/PREVIOUS_MODEL).read_bytes())==PREVIOUS_MODEL_BLOB,
      'PREVIOUS_V068_SOLVER_SHA_CHANGED')
 plan=json.loads((packet/'trajectory.json').read_text('utf8'))
 need(plan.get('source_sha256')==SOURCE_SHA,'MEASURED_TRAJECTORY_SOURCE_PIN_MISMATCH')
 emit('MEASURED_TRAJECTORY_SHA256',file_sha(packet/'trajectory.json'))
 emit('SOURCE_V0615_FRONT_GROUND_PATH','REAL_GLB_97_FRAME_AND_MIDFRAME_VALIDATION')
 try:
  model,report=repair.build(source,plan,base,previous,
                            progress=lambda v:emit('PROGRESS',v))
  need(sha(model)==EXPECTED_VALIDATED_V0616_OUTPUT_SHA,'VALIDATED_V0616_GLB_CANDIDATE_CHANGED__BLOCKED')
  emit('VALIDATED_V0616_GLB_SHA_REPLAY','PASS')
  report['trajectory_sha256']=file_sha(packet/'trajectory.json')
  check=import_module(packet/'regression.py','repl_0615_measured_production_regression')
  passes=check.verify_measurements(report,plan)
  emit('REAL_SKINNED_TRAJECTORY_VERIFICATION','PASS_1164_FRAME_SAMPLES_AND_576_MIDFRAME_SAMPLES')
  emit('PRODUCTION_MODEL_RECHECKED_MEASUREMENTS',str(passes))
 except Exception as exc:
  blocked_report(downloads,{'campaign':PROJECT,'version':VER,
    'status':'BLOCKED_REAL_GLB_VALIDATION_CANONICAL_PRESERVED',
    'source_sha256':SOURCE_SHA,
    'trajectory_sha256':file_sha(packet/'trajectory.json'),
    'exception_type':type(exc).__name__,'exception':str(exc),
    'traceback':traceback.format_exc()})
  raise Blocked('REAL_GLTF_VALIDATION_FAILED__UNCHANGED:'+type(exc).__name__+':'+str(exc)) from exc
 emit('FRONT_HOOF_CLEARANCE',str({k:v['verified_peak'] for k,v in report['front_hoof_clearance'].items()}))
 emit('PRESERVED_BODY_CORNER_SAG',str(report['loaded_shoulder_drop']))
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
 commit_sha=commit(repo,packet,model,report,html,policy_gate)
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
