#!/usr/bin/env python3
"""Repl v0.6.0. One canonical Git GLB, forward-traveling IK stages.

All pushes use Git from Termux, never direct ChatGPT GitHub mutations.
One downloaded ZIP includes all sources. Does not create a second .glb in repo.
Stages run and self-validate automatically before publishing the canonical file.
A diagnostic candidate may exist privately outside Git but is not delivered.
"""
from __future__ import annotations
import argparse
import base64
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback

sys.dont_write_bytecode=True
VER='0.6.0'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BRANCH='main'
PARENT_HEAD='85551cb00466e7075a539b288d8e6fcbf9ea18cd'
CANON='assets/repl/Repl.glb'
MANIFEST='assets/repl/CANONICAL_MODEL.json'
README='README.md'
GIT_SOURCE_SHA='55bca4c3406f46bd5c6475127158554a823f8aa36bfd7a6c969d9fb2806ccc7b'
GIT_SOURCE_BLOB='5fe7b6bdf6ffe4201e331d1db52ea0d24cad9002'
BASE_ENGINE='campaigns/repl_hair_bind_v0_1_0.py'
BASE_ENGINE_BLOB='33ca93660f3d5858d4496027902b9b7a7e44d800'
GIZMO_JS='campaigns/repl_tail_gizmo_v0_4_0.js'
GIZMO_JS_BLOB='1b4396ed0027a0a75baed840d7ed741e57c58a92'
FILES={
 'campaigns/REPL_FORWARD_IK_WALK_v0.6.0.sh':'run-termux.sh',
 'campaigns/repl_forward_ik_walk_v0_6_0.py':'gait.py',
 'campaigns/repl_forward_ik_walk_driver_v0_6_0.py':'driver.py',
 'campaigns/repl_forward_ik_walk_viewer_v0_6_0.html.in':'viewer.html.in',
 'campaigns/repl_forward_ik_walk_blender_v0_6_0.py':'blender_review.py',
 'campaigns/REPL_FORWARD_IK_WALK_v0.6.0_CONTRACT.json':'contract.json'
}
REVIEW='REPL_FORWARD_IK_WALK_v0.6.0_TEXTURERENDER.html'
REPORT='REPL_FORWARD_IK_WALK_v0.6.0_report.json'
RECEIPT='REPL_FORWARD_IK_WALK_v0.6.0_RECEIPT.txt'
class Blocked(RuntimeError):pass

def need(x,why):
 if not x:raise Blocked(why)

def emit(k,v):print(f'{k}={v}',flush=True)

def sha(b):return hashlib.sha256(b).hexdigest()

def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def git_blob(raw):
 return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()

def run(args,cwd=None,check=True,timeout=210):
 env=os.environ.copy()
 env['GIT_TERMINAL_PROMPT']='0';env['PYTHONDONTWRITEBYTECODE']='1';env['GIT_LFS_SKIP_SMUDGE']='1'
 p=subprocess.run(args,cwd=str(cwd) if cwd else None,env=env,
                  capture_output=True,text=True,timeout=timeout,check=False)
 if check and p.returncode:
  raise Blocked('COMMAND_FAILED:'+args[0]+':'+str(p.returncode)+':'+p.stderr[-280:].replace('\n',' '))
 return p

def git(repo,*args,check=True):return run(['git',*args],cwd=repo,check=check)

def gout(repo,*args):return git(repo,*args).stdout.strip()

def atomic(path,data):
 path=Path(path)
 need(path.parent.is_dir(),'OUTPUT_PARENT_MISSING:'+str(path.parent))
 if path.is_file():
  need(file_sha(path)==sha(data),'SAME_VERSION_PUBLIC_FILE_COLLISION:'+path.name)
  return
 fd,temp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(temp,path)
 finally:
  if os.path.exists(temp):os.unlink(temp)
 need(file_sha(path)==sha(data),'OUTPUT_READBACK_MISMATCH:'+path.name)

def verify_repo_source(repo):
 glbs=[p for p in gout(repo,'ls-tree','-r','--name-only','HEAD').splitlines()
       if p.lower().endswith('.glb')]
 need(glbs==[CANON],'EXPECTED_ONE_CANONICAL_MODEL:'+str(glbs))
 raw=(repo/CANON).read_bytes()
 need(sha(raw)==GIT_SOURCE_SHA,'SOURCE_CANONICAL_HASH_NOT_APPROVED')
 need(gout(repo,'rev-parse','HEAD:'+CANON)==GIT_SOURCE_BLOB,
      'SOURCE_GIT_BLOB_NOT_V052')
 for relative,blob in [(BASE_ENGINE,BASE_ENGINE_BLOB),(GIZMO_JS,GIZMO_JS_BLOB)]:
  need((repo/relative).is_file(),'REQUIRED_REPO_ENGINE_MISSING:'+relative)
  need(gout(repo,'hash-object','--',relative)==blob,'REQUIRED_ENGINE_CHANGED:'+relative)
 manifest=json.loads((repo/MANIFEST).read_text('utf8'))
 need(manifest['active_model']['sha256']==GIT_SOURCE_SHA,
      'OWNER_MANIFEST_AND_CANONICAL_ASSET_DIVERGED')
 need(manifest['canonical_glb_path']==CANON,'CANONICAL_PATH_CHANGED')
 emit('LIVE_CANONICAL_SOURCE',GIT_SOURCE_SHA)
 emit('REPO_MODEL_COUNT',1)
 return raw,manifest

def checkout(state):
 repo=state/'repo'
 if repo.exists():
  need((repo/'.git').is_dir(),'CAMPAIGN_CHECKOUT_IS_NOT_A_REPOSITORY')
  need(gout(repo,'remote','get-url','origin')==REMOTE,'CAMPAIGN_CHECKOUT_WRONG_REMOTE')
  git(repo,'fetch','--quiet','origin','main')
  remote=gout(repo,'rev-parse','refs/remotes/origin/main')
  local=gout(repo,'rev-parse','HEAD')
  changes=git(repo,'status','--porcelain','--untracked-files=all').stdout.strip()
  need(not changes,'CAMPAIGN_CHECKOUT_DIRTY__PRESERVED:'+changes[:100])
  if local!=remote:
   need(git(repo,'merge-base','--is-ancestor',remote,local,check=False).returncode==0,
        'LOCAL_AND_REMOTE_DIVERGED__PRESERVED')
   emit('RESUME_EXISTING_LOCAL_COMMIT',local)
  return repo
 work=Path(tempfile.mkdtemp(prefix='.repl-walk-clone-',dir=state))
 try:
  shutil.rmtree(work)
  run(['git','clone','--quiet','--branch','main','--single-branch',REMOTE,str(work)],timeout=220)
  need(gout(work,'remote','get-url','origin')==REMOTE,'CLONE_REMOTE_MISMATCH')
  os.replace(work,repo)
 finally:
  if work.exists():shutil.rmtree(work)
 return repo

def load_engine(repo):
 path=repo/BASE_ENGINE
 spec=importlib.util.spec_from_file_location('repl_immutable_v010_for_walk',path)
 base=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(base)
 base.EXPECTED_JOINTS=50
 return base

def load_gait(path):
 spec=importlib.util.spec_from_file_location('repl_forward_gait_v060',path)
 gait=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(gait)
 need(gait.SOURCE_SHA==GIT_SOURCE_SHA,'PACKET_GAIT_ASSET_IDENTITY_CHANGED')
 need(gait.CANONICAL_REL==CANON,'PACKET_CANONICAL_PATH_CHANGED')
 return gait

def update_manifest(manifest,report,output):
 prev=dict(manifest.get('active_model') or {})
 manifest['previous_model']={'version':prev.get('version'),'sha256':prev.get('sha256'),
  'git_blob_sha1':prev.get('git_blob_sha1'),
  'owner_visual_acceptance':'TAIL_PIVOT_APPROVED_IN_CHAT',
  'source_regression':'NONE'}
 manifest['active_model']={
  'path':CANON,'version':VER,'campaign':'REPL_FORWARD_IK_WALK',
  'sha256':sha(output),'git_blob_sha1':git_blob(output),
  'joint_count':50,'node_count':53,'animations':6,
  'walk_review_clips':[a['clip'] for a in report['stages'].values()],
  'walk_clip_names':[a['clip'] for a in report['stages'].values()],
  'stride_duration':report['kinematics']['stride_duration'],
  'world_root_travel_z':report['kinematics']['travel_units'],
  'walk_direction_world':'+Z','mode':'FORWARD_TRAVEL_ONLY_NO_IN_PLACE',
  'hoof_plant_test':report['skinned_hoof_witness_test'],
  'tail_pivot':'UNCHANGED_FROM_APPROVED_V052',
  'all_previous_animations':'PRESERVED',
  'accepted_mane_weights':'UNCHANGED',
  'human_visual_acceptance':'PENDING'
 }
 manifest['status']='FORWARD_FOUR_BEAT_IK_WALK_v0.6.0__HUMAN_VISUAL_PENDING'
 manifest['single_canonical_glb_count']=1
 manifest['later_hair_motion_results_in_repo']=True
 manifest['owner_rules']=list(dict.fromkeys(list(manifest.get('owner_rules',[]))+[
   'Forward travel walk ONLY; never bake or ship an in-place/treadmill walk',
   'Four real skinned-leg IK and hoof-mesh stance slip required',
   'No separate GLB for a review stage; three clips in the same canonical asset']))
 return json.dumps(manifest,indent=2,sort_keys=True)+'\n'

def copy_campaign_sources(repo,packet):
 for dst,name in FILES.items():
  src=packet/name
  need(src.is_file(),'MISSING_PACKET_SOURCE:'+name)
  target=repo/dst
  need(not target.exists(),'RELEASE_SOURCE_VERSION_COLLISION:'+dst)
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(src.read_bytes())

def make_viewer(packet,repo,model,report):
 template=(packet/'viewer.html.in').read_text('utf8')
 gizmo=(repo/GIZMO_JS).read_text('utf8')
 # Display corrected socket as the CURRENT default; retain orange obsolete
 # pivot for comparison, without updating the model's accepted bind matrix.
 need('const chosen = new THREE.Vector3(0,1.05,-0.93);' in gizmo,
      'EXPECTED_GIZMO_DEFAULT_NOT_RECOGNIZED')
 gizmo=gizmo.replace('const chosen = new THREE.Vector3(0,1.05,-0.93);',
                     'const chosen = new THREE.Vector3(0,1.204,-0.889);')
 gizmo=gizmo.replace('existing.position.copy(chosen);',
                     'existing.position.set(0,1.05,-0.93);')
 gizmo=gizmo.replace('d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f',GIT_SOURCE_SHA)
 need('__GIZMO_JS__' in template and '__EMBEDDED_GLB_BASE64__' in template,
      'VIEWER_PLACEHOLDER_MISSING')
 html=template.replace('__GIZMO_JS__',gizmo).replace('__EMBEDDED_GLB_BASE64__',base64.b64encode(model).decode('ascii'))
 need('REPL_WALK_03_FORWARD_SECONDARY_INTEGRATED' in report['stages']['3']['clip'],
      'VIEWER_NOT_ACTUAL_INTEGRATED_GAIT')
 return html.encode('utf8')

def append_readme(current):
 s=current
 tag='## Repl: moving four-beat IK walk v0.6.0'
 need(tag not in s,'README_SAME_RELEASE_DUPLICATE')
 s+='\n'+tag+'\n\n'
 s+='The one canonical `assets/repl/Repl.glb` now contains three additional '
 s+='forward-traveling four-beat horse walk review clips (legs, body, integration). '
 s+='Each advances the original skeletal root in world +Z. There is no in-place '
 s+='walk variant. Four distinct stance/swing sequences are solved using the actual '
 s+='foreleg/hindleg chains, with mesh-hoof groundedness tests. The earlier mane, '
 s+='corrected tail pivot, tail straightening and previous clips are unchanged. '
 s+='The owner\'s visual verdict is pending; Git numerical checks alone are not acceptance.\n'
 return s

def commit_output(repo,packet,model,report):
 output_path=repo/CANON
 # Exactly one git-tracked GLB, no untracked version-named models.
 tempdir=output_path.parent
 fd,temp=tempfile.mkstemp(prefix='.Repl.v060-',suffix='.tmp',dir=tempdir)
 try:
  with os.fdopen(fd,'wb') as f:f.write(model);f.flush();os.fsync(f.fileno())
  need(file_sha(temp)==sha(model),'MODEL_TEMP_WRITE_SHA_MISMATCH')
  os.replace(temp,output_path)
 finally:
  if os.path.exists(temp):os.unlink(temp)
 need(file_sha(output_path)==sha(model),'CANONICAL_WRITE_READBACK_MISMATCH')
 original=json.loads((repo/MANIFEST).read_text('utf8'))
 (repo/MANIFEST).write_text(update_manifest(original,report,model),encoding='utf8')
 (repo/README).write_text(append_readme((repo/README).read_text('utf8')),encoding='utf8')
 copy_campaign_sources(repo,packet)
 allowed=[CANON,MANIFEST,README]+list(FILES)
 git(repo,'add','--',*allowed)
 staged=set(git(repo,'diff','--cached','--name-only').stdout.strip().splitlines())
 need(staged==set(allowed),'STAGED_FILE_SET_DIFFERENT_FROM_CONTRACT:'+repr(staged))
 need(not git(repo,'status','--porcelain','--untracked-files=all').stdout.count('??'),
      'REPO_HAS_UNEXPECTED_UNTRACKED_ARTIFACT')
 git(repo,'-c','user.name=Repl Termux Campaign',
     '-c','user.email=repl-termux-campaign@users.noreply.github.com',
     'commit','-m','Bake Repl forward four-beat IK walk into canonical GLB v0.6.0')
 return gout(repo,'rev-parse','HEAD')

def push(repo,base_head):
 remote_now=gout(repo,'ls-remote','origin','refs/heads/main').split()[0]
 need(remote_now==base_head,'REMOTE_BRANCH_ADVANCED_DURING_CAMPAIGN__PRESERVED')
 commands=[['git','push','--quiet','origin','HEAD:refs/heads/main']]
 if shutil.which('gh'):
  if run(['gh','auth','status','-h','github.com'],check=False,timeout=12).returncode==0:
   commands.append(['git','-c','credential.helper=!gh auth git-credential','push','--quiet',
                    'origin','HEAD:refs/heads/main'])
 # Respect the owner's already installed Termux SSH identity if present.
 if shutil.which('ssh'):
  commands.append(['git','push','--quiet','git@github.com:Valar05/parametric-parambulator.git',
                   'HEAD:refs/heads/main'])
 for index,cmd in enumerate(commands):
  result=run(cmd,cwd=repo,check=False,timeout=160)
  if result.returncode==0:
   emit('TERMUX_GIT_PUSH_ROUTE',('origin','gh','ssh')[index]);return
 need(False,'GIT_PUSH_AUTH_OR_NETWORK_FAILED__LOCAL_COMMIT_PRESERVED')

def verify_remote(repo,expected_sha,commit):
 git(repo,'fetch','--quiet','origin','main')
 head=gout(repo,'rev-parse','refs/remotes/origin/main')
 need(head==commit,'REMOTE_COMMIT_READBACK_NOT_EXPECTED_HEAD')
 glbs=[p for p in gout(repo,'ls-tree','-r','--name-only',head).splitlines()
       if p.lower().endswith('.glb')]
 need(glbs==[CANON],'REMOTE_MULTIPLE_GLBS_OR_WRONG_PATH')
 need(gout(repo,'rev-parse',f'{head}:{CANON}')==expected_sha[1],
      'REMOTE_GIT_BLOB_SHA_WRONG')
 raw=subprocess.run(['git','show',f'{head}:{CANON}'],cwd=repo,
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
 need(raw.returncode==0 and sha(raw.stdout)==expected_sha[0],
      'REMOTE_CANONICAL_BINARY_SHA_READBACK_FAILED')
 manifest=json.loads(git(repo,'show',f'{head}:{MANIFEST}').stdout)
 need(manifest['active_model']['sha256']==expected_sha[0]
      and manifest['active_model']['version']==VER,'REMOTE_MANIFEST_READBACK_FAILED')
 return head

def optional_renderer(repo,packet,downloads):
 executable=shutil.which('blender')
 if not executable:
  emit('BLENDER_RENDER','NOT_ON_TERMUX_PATH__HTML_TEXTURING_AVAILABLE')
  return
 target=downloads/'REPL_FORWARD_IK_WALK_v0.6.0_blender'
 target.mkdir(parents=True,exist_ok=True)
 args=[executable,'--background','--factory-startup','--python',
       str(packet/'blender_review.py'),'--','--glb',str(repo/CANON),
       '--output',str(target)]
 try:
  proc=run(args,check=False,timeout=300)
  (target/'blender_run.log').write_text((proc.stdout+'\n'+proc.stderr)[-9000:],encoding='utf8')
  emit('BLENDER_RENDER','GENERATED' if proc.returncode==0 else 'FAILED__SEE_LOG')
 except (OSError,subprocess.TimeoutExpired) as exc:
  emit('BLENDER_RENDER','FAILED_OR_TIMEOUT__HTML_AVAILABLE')

def publish(downloads,html,report):
 atomic(downloads/REVIEW,html)
 atomic(downloads/REPORT,(json.dumps(report,indent=2,sort_keys=True)+'\n').encode('utf8'))
 emit('TEXTURED_BROWSER_REVIEW',downloads/REVIEW)
 emit('REPORT',downloads/REPORT)
 emit('PREVIEW_SHA256',sha(html))

def maybe_open(downloads):
 path=downloads/REVIEW
 scanner=shutil.which('termux-media-scan')
 if scanner:
  try:
   p=run([scanner,str(path)],check=False,timeout=15)
   emit('MEDIA_SCAN','REQUESTED_NOT_VERIFIED' if p.returncode==0 else 'FAILED')
  except Exception:emit('MEDIA_SCAN','FAILED')
 if shutil.which('termux-open'):
  try:
   p=run(['termux-open',str(path)],check=False,timeout=12)
   emit('BROWSER_OPEN','REQUESTED_NOT_VERIFIED' if p.returncode==0 else 'FAILED')
  except Exception:emit('BROWSER_OPEN','FAILED')
 else:emit('BROWSER_OPEN','NOT_AVAILABLE')

def receipt(downloads,commit,model,report):
 lines={
  'CAMPAIGN':'REPL_FORWARD_FOUR_BEAT_IK_WALK','VERSION':VER,
  'EXECUTION_LANE':'TERMUX_GIT','REPOSITORY':REPO,
  'REMOTE_COMMIT':commit,'CANONICAL_PATH':CANON,'REMOTE_GLB_COUNT':1,
  'CANONICAL_SHA256':sha(model),'CANONICAL_GIT_BLOB':git_blob(model),
  'ROOT_TRAVEL_Z':report['kinematics']['travel_units'],
  'IN_PLACE_VERSION':'NONE',
  'NEW_GAIT_CLIPS':3,'TOTAL_ANIMATIONS':6,
  'HOOF_MESH_MAX_STANCE_SLIDE':max(x['max_physical_hoof_mesh_z_spread']
                                  for x in report['skinned_hoof_witness_test'].values()),
  'BONE_PIVOT':'ACCEPTED_v0.5.2_UNMODIFIED',
  'MANE_AND_TAIL_WEIGHTS':'UNMODIFIED',
  'VISUAL_VERDICT':'PENDING_USER_REVIEW',
  'STATUS':'REMOTE_CANONICAL_FOUR_BEAT_WALK_READBACK_VERIFIED'
 }
 content='\n'.join(f'{k}={v}' for k,v in lines.items())+'\n'
 atomic(downloads/RECEIPT,content.encode('utf8'))
 emit('RECEIPT',downloads/RECEIPT)
 for k,v in lines.items():emit(k,v)

def execute(args):
 packet=Path(args.packet).resolve()
 need(packet.is_dir(),'PACKET_DIRECTORY_MISSING')
 downloads=Path.home()/'storage'/'downloads'
 need(downloads.is_dir(),'TERMUX_SHARED_DOWNLOADS_UNAVAILABLE')
 state=Path.home()/'.local'/'share'/'repl-campaigns'/'forward-ik-v0.6.0'
 state.mkdir(parents=True,exist_ok=True)
 emit('CAMPAIGN','REPL_FORWARD_FOUR_BEAT_IK_WALK')
 emit('VERSION',VER)
 emit('EXECUTION_LANE','TERMUX_GIT')
 emit('REPO',REPO)
 emit('MODEL_PATH',CANON)
 emit('WALK_MODE','WORLD_TRAVEL_ONLY_NO_IN_PLACE')
 repo=checkout(state)
 remote=gout(repo,'rev-parse','refs/remotes/origin/main')
 head=gout(repo,'rev-parse','HEAD')
 # A successful previous invocation is safely idempotent; the source GLB's
 # original SHA no longer matches after the FIRST successful canonical update.
 if head==remote:
  existing=json.loads((repo/MANIFEST).read_text('utf8'))
  active=existing.get('active_model',{})
  if active.get('version')==VER:
   local=(repo/CANON).read_bytes()
   need(sha(local)==active.get('sha256'),
        'EXISTING_COMPLETED_MODEL_DIGEST_MISMATCH')
   need(gout(repo,'rev-parse','HEAD:'+CANON)==active.get('git_blob_sha1'),
        'EXISTING_COMPLETED_GIT_BLOB_MISMATCH')
   need((downloads/REPORT).is_file() and (downloads/REVIEW).is_file(),
        'COMPLETED_RELEASE_MISSING_EVIDENCE__NO_REBUILD_OR_SECOND_GLB')
   report=json.loads((downloads/REPORT).read_text('utf8'))
   need(report.get('output_sha256')==sha(local),
        'COMPLETED_RELEASE_REPORT_MISMATCH')
   emit('REPEAT_RUN','REMOTE_CANONICAL_RELEASE_ALREADY_VERIFIED')
   remote_ver=verify_remote(repo,(sha(local),git_blob(local)),head)
   receipt(downloads,remote_ver,local,report)
   maybe_open(downloads)
   return
 if head!=remote:
  # A previous successful local commit may be pending push. Never regenerate
  # from the already modified canonical asset or destroy the local commit.
  commit=head
  manifest=json.loads((repo/MANIFEST).read_text('utf8'))
  model=(repo/CANON).read_bytes()
  need(manifest.get('active_model',{}).get('version')==VER,
       'UNEXPECTED_AHEAD_COMMIT_NOT_OUR_CAMPAIGN')
  need(manifest['active_model']['sha256']==sha(model),
       'PENDING_LOCAL_COMMIT_HAS_WRONG_MODEL_SHA')
  need(sha((repo/CANON).read_bytes())==manifest['active_model']['sha256'],
       'PENDING_COMMIT_BINARY_READBACK_FAILED')
  report=json.loads((downloads/REPORT).read_text('utf8'))
  html=(downloads/REVIEW).read_bytes()
  emit('AUTO_RESUME','EXISTING_LOCAL_COMMIT_PENDING_PUSH')
  push(repo,remote)
  head=verify_remote(repo,(sha(model),git_blob(model)),commit)
  receipt(downloads,head,model,report)
  maybe_open(downloads)
  return
 need(head==remote,'REMOTE_HEAD_LOCAL_MISMATCH')
 # Other commit changes could be legitimate, but any new source model is a
 # mission boundary. Lock original source SHA even if the commit differs.
 source,manifest=verify_repo_source(repo)
 base=load_engine(repo)
 gait=load_gait(packet/'gait.py')
 emit('REAL_CANONICAL_IK_GENERATION','STARTED')
 model,report=gait.make_gait(source,base,progress=lambda x:emit('PROGRESS',x))
 emit('REAL_CANONICAL_IK_GENERATION','NUMERICALLY_VALIDATED')
 report['skinned_hoof_witness_test']=gait.validate_skinned_hoof_witnesses(model,base)
 emit('SKINNED_HOOF_SURFACE_STANCE_SLIP','PASS')
 emit('ROOT_FORWARD_TRAVEL_UNITS',report['kinematics']['travel_units'])
 html=make_viewer(packet,repo,model,report)
 publish(downloads,html,report)
 # Locked remote HEAD checked again, before any repo mutation.
 remote_now=gout(repo,'ls-remote','origin','refs/heads/main').split()[0]
 need(remote_now==head,'REMOTE_ADVANCED_DURING_GENERATION__NO_OVERWRITE')
 commit=commit_output(repo,packet,model,report)
 emit('LOCAL_CANONICAL_COMMIT',commit)
 push(repo,head)
 remote_verified=verify_remote(repo,(sha(model),git_blob(model)),commit)
 receipt(downloads,remote_verified,model,report)
 optional_renderer(repo,packet,downloads)
 maybe_open(downloads)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--packet',required=True)
 args=parser.parse_args()
 execute(args)

if __name__=='__main__':
 try:main()
 except Blocked as exc:
  emit('STATUS','BLOCKED')
  emit('CAUSE',str(exc))
  emit('CANONICAL_REMOTE_UPDATE','UNVERIFIED')
  sys.exit(2)
 except Exception as exc:
  traceback.print_exc()
  emit('STATUS','FAILED')
  emit('CAUSE',type(exc).__name__+':'+str(exc))
  emit('CANONICAL_REMOTE_UPDATE','UNVERIFIED')
  sys.exit(3)
