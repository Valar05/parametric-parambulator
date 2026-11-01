#!/usr/bin/env python3
"""One-invocation, phone-first Pose Lab inspector for Repl v0.6.6.

Only Termux Git may update the canonical parametric-parambulator repository.
This release does not modify the canonical GLB, animations, skin or materials.
"""
from __future__ import annotations
import argparse,base64,datetime,hashlib,importlib.util,json,os,shutil,struct,subprocess,sys,tempfile,traceback
from pathlib import Path

sys.dont_write_bytecode=True
VERSION='0.6.6'
PROJECT='REPL_POSE_LAB_BONE_CONTROLS'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
HEAD_LOCK='4e5c15de287d38292e0dd7364031ef084fa55639'
CANON='assets/repl/Repl.glb'
CANON_SHA='c3209b404b5c50842591cfa654142d2f0d84d27eb1acf7779b8d4d504d4508af'
CANON_BLOB='d5b57ffc1a491f96faa5b6ed4e16dd1a3a3477c1'
VIEWER_PATH='campaigns/repl_leg_silhouette_viewer_v0_6_5.html.in'
VIEWER_BLOB='78ba1538992fa77df07138f08e72d67ffed61e2f'
GIZMO_PATH='campaigns/repl_tail_gizmo_v0_4_0.js'
GIZMO_BLOB='1b4396ed0027a0a75baed840d7ed741e57c58a92'
PACKET_FILES={
 'campaigns/repl_pose_lab_bones_v0_6_6.js':'pose_lab_bones.js',
 'campaigns/repl_pose_lab_bones_patch_v0_6_6.py':'patch_viewer.py',
 'campaigns/repl_pose_lab_bones_driver_v0_6_6.py':'driver.py',
 'campaigns/REPL_POSE_LAB_BONE_CONTROLS_v0.6.6.sh':'run-termux.sh',
 'campaigns/REPL_POSE_LAB_BONE_CONTROLS_v0.6.6_SELFTEST.py':'selftest.py',
 'campaigns/REPL_POSE_LAB_BONE_CONTROLS_v0.6.6_CONTRACT.json':'contract.json',
 'campaigns/REPL_POSE_LAB_BONE_CONTROLS_v0.6.6_README.md':'README.md',
 'campaigns/REPL_POSE_LAB_BONE_CONTROLS_v0.6.6_PACKET_MANIFEST.json':'../manifest.json',
}
HTML_NAME='REPL_POSE_LAB_BONE_CONTROLS_v0.6.6.html'
REPORT_NAME='REPL_POSE_LAB_BONE_CONTROLS_v0.6.6_report.json'
RECEIPT_NAME='REPL_POSE_LAB_BONE_CONTROLS_v0.6.6_RECEIPT.txt'
LOG_NAME='REPL_POSE_LAB_BONE_CONTROLS_v0.6.6_OPERATOR.log'

class Blocked(RuntimeError): pass

def need(condition,reason):
 if not condition:raise Blocked(reason)
def emit(key,value):print(f'{key}={value}',flush=True)
def sha(data):return hashlib.sha256(data).hexdigest()
def gitblob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def file_sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def run(cmd,cwd=None,timeout=180,check=True):
 env=os.environ.copy();env['GIT_TERMINAL_PROMPT']='0';env['GIT_LFS_SKIP_SMUDGE']='1'
 env['PYTHONDONTWRITEBYTECODE']='1'
 try:r=subprocess.run(cmd,cwd=str(cwd) if cwd else None,env=env,
     capture_output=True,timeout=timeout,text=True,check=False)
 except subprocess.TimeoutExpired as e:raise Blocked('COMMAND_TIMEOUT:'+str(cmd[0])+':'+str(timeout)) from e
 if check and r.returncode:raise Blocked('COMMAND_FAILED:'+str(cmd[0])+':'+str(r.returncode)+':'+(r.stderr or r.stdout)[-420:].replace('\n',' '))
 return r

def git(repo,*args,check=True,timeout=180):return run(['git',*args],cwd=repo,check=check,timeout=timeout)
def gout(repo,*args):return git(repo,*args).stdout.strip()

def public_write(path,data):
 path=Path(path);need(path.parent.is_dir(),'DOWNLOADS_NOT_MOUNTED')
 if path.exists():
  need(path.is_file() and file_sha(path)==sha(data),
       'VERSIONED_PUBLIC_COLLISION:'+path.name)
  return 'ALREADY_VERIFIED'
 fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name+'.')
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 need(file_sha(path)==sha(data),'PUBLIC_READBACK_FAILED:'+path.name)
 return 'NEW_SHA_VERIFIED'

def verify_glb(data):
 need(sha(data)==CANON_SHA,'CANONICAL_MODEL_SHA_MISMATCH__NO_ASSET_MUTATION')
 need(gitblob(data)==CANON_BLOB,'CANONICAL_GIT_BLOB_MISMATCH')
 need(len(data)>=30 and data[:4]==b'glTF','GLB_INVALID_MAGIC')
 _,version,length=struct.unpack_from('<4sII',data,0)
 need(version==2 and length==len(data),'GLB_LENGTH_INVALID')
 n,chunk=struct.unpack_from('<I4s',data,12);need(chunk==b'JSON','GLB_JSON_CHUNK_MISSING')
 doc=json.loads(data[20:20+n]);need(len(doc.get('nodes',[]))==53,'GLB_NODES_NOT_53')
 need(len(doc.get('skins',[{}])[0].get('joints',[]))==50,'GLB_JOINTS_NOT_50')
 need(len(doc.get('animations',[]))==6,'GLB_ANIMATION_COUNT_CHANGED')
 names={x.get('name') for x in doc['nodes']}
 need(all(x in names for x in ('Bone_012','Bone_018','Bone_023','Bone_028')),'GLB_FOUR_TIP_NAMES_MISSING')
 return doc

def one_model(repo,ref='HEAD'):
 models=[s for s in gout(repo,'ls-tree','-r','--name-only',ref).splitlines() if s.lower().endswith('.glb')]
 need(models==[CANON],'SINGLE_CANONICAL_GLB_VIOLATION:'+repr(models))

def checkout(work):
 repo=work/'repo'
 if repo.exists():
  need((repo/'.git').is_dir(),'CAMPAIGN_STATE_REPO_NOT_GIT')
  need(gout(repo,'remote','get-url','origin')==REMOTE,'CAMPAIGN_REMOTE_UNEXPECTED')
  git(repo,'fetch','--quiet','origin','main',timeout=180)
  return repo
 tmp=Path(tempfile.mkdtemp(dir=work,prefix='.repo-clone-'))
 try:
  shutil.rmtree(tmp)
  run(['git','clone','--quiet','--single-branch','--branch','main',REMOTE,str(tmp)],timeout=200)
  need(gout(tmp,'remote','get-url','origin')==REMOTE,'GIT_CLONE_REMOTE_WRONG')
  os.replace(tmp,repo)
 finally:
  if tmp.exists():shutil.rmtree(tmp)
 return repo

def verify_repo(repo,allow_done=False):
 one_model(repo)
 need(not git(repo,'status','--porcelain','--untracked-files=all').stdout.strip(),
      'PRIVATE_CAMPAIGN_CHECKOUT_DIRTY__SAFE_STOP')
 model=(repo/CANON).read_bytes();verify_glb(model)
 need(gout(repo,'rev-parse','HEAD:'+CANON)==CANON_BLOB,'CANONICAL_GIT_MODEL_BLOB_CHANGED')
 for path,blob in ((VIEWER_PATH,VIEWER_BLOB),(GIZMO_PATH,GIZMO_BLOB)):
  need((repo/path).is_file() and gout(repo,'hash-object','--',path)==blob,
       'REQUIRED_VIEWER_SOURCE_CHANGED:'+path)
 manifest=json.loads((repo/'assets/repl/CANONICAL_MODEL.json').read_text('utf8'))
 need(manifest['active_model']['version']=='0.6.5' and manifest['active_model']['sha256']==CANON_SHA,
      'ACTIVE_PRODUCTION_NOT_PINNED_v0.6.5')
 return model

def render(repo,packet,model):
 modname='pose_lab_066_viewer_patch'
 spec=importlib.util.spec_from_file_location(modname,packet/'patch_viewer.py')
 p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
 template=(repo/VIEWER_PATH).read_text('utf8')
 js=(packet/'pose_lab_bones.js').read_text('utf8')
 rendered=p.patch(template,js,sha(model))
 gizmo=(repo/GIZMO_PATH).read_text('utf8')
 need('const chosen = new THREE.Vector3(0,1.05,-0.93);' in gizmo,'GIZMO_UPSTREAM_ANCHOR_CHANGED')
 gizmo=gizmo.replace('const chosen = new THREE.Vector3(0,1.05,-0.93);',
                     'const chosen = new THREE.Vector3(0,1.204,-0.889);')
 gizmo=gizmo.replace('existing.position.copy(chosen);','existing.position.set(0,1.05,-0.93);')
 gizmo=gizmo.replace('d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f',sha(model))
 need('__GIZMO_JS__' in rendered and '__EMBEDDED_GLB_BASE64__' in rendered,
      'RENDER_PLACEHOLDER_MISSING')
 rendered=rendered.replace('__GIZMO_JS__',gizmo).replace('__EMBEDDED_GLB_BASE64__',base64.b64encode(model).decode('ascii'))
 need('__EMBEDDED_GLB_BASE64__' not in rendered and '__GIZMO_JS__' not in rendered,
      'RENDER_PLACEHOLDER_NOT_REPLACED')
 need(rendered.count('id="pl-edit"')==1 and rendered.count('id="pl-lockX"')==1,
      'RENDER_POSE_CONTROL_INTEGRATION_MISSING')
 return rendered.encode('utf8')

def stage_commit(repo,packet,html_hash):
 allowed=list(PACKET_FILES)
 for dest,part in PACKET_FILES.items():
  dst=repo/dest
  need(not dst.exists(),'CAMPAIGN_VERSION_FILE_EXISTS:'+dest)
  source=(packet/part).resolve()
  need(source.is_file(),'PACKET_FILE_MISSING:'+part)
  dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_bytes(source.read_bytes())
 git(repo,'add','--',*allowed)
 staged=gout(repo,'diff','--cached','--name-only').splitlines()
 need(set(staged)==set(allowed) and len(staged)==len(allowed),'STAGED_NONALLOWLIST_PATHS:'+repr(staged))
 git(repo,'-c','user.name=Repl Termux Campaign','-c','user.email=repl-termux-campaign@users.noreply.github.com',
     'commit','-m','Add non-destructive phone Pose Lab bone manipulation v0.6.6')
 one_model(repo)
 need(gout(repo,'rev-parse','HEAD:'+CANON)==CANON_BLOB,'GLB_CHANGED_DURING_VIEWER_COMMIT')
 return gout(repo,'rev-parse','HEAD')

def remote_ref(repo):
 r=gout(repo,'ls-remote','origin','refs/heads/main').split()
 need(len(r)==2,'REMOTE_BRANCH_UNREACHABLE')
 return r[0]

def push_with_reconcile(repo,parent,commit):
 if remote_ref(repo)==commit:
  emit('GIT_PUSH','ALREADY_LIVE_VERIFIED');return
 need(remote_ref(repo)==parent,'REMOTE_MAIN_ADVANCED__NO_FORCE_PUSH')
 options=[('origin',['git','push','--quiet','origin','HEAD:refs/heads/main'])]
 if shutil.which('gh'):
  if run(['gh','auth','status','-h','github.com'],check=False,timeout=12).returncode==0:
   options.append(('gh',['git','-c','credential.helper=!gh auth git-credential','push','--quiet',
     'origin','HEAD:refs/heads/main']))
 if shutil.which('ssh'):
  options.append(('ssh',['git','push','--quiet',
    'git@github.com:Valar05/parametric-parambulator.git','HEAD:refs/heads/main']))
 failed=[]
 for route,cmd in options:
  try:
   r=run(cmd,cwd=repo,check=False,timeout=110)
   if r.returncode==0 or remote_ref(repo)==commit:
    emit('GIT_PUSH','READBACK_VERIFIED_VIA_'+route);return
   failed.append(route+':exit='+str(r.returncode)+':'+r.stderr[-140:].replace('\n',' '))
  except Blocked as e:
   if remote_ref(repo)==commit:
    emit('GIT_PUSH','ACK_LOST_BUT_REMOTE_READBACK_MATCHED');return
   failed.append(route+':'+str(e))
 need(False,'GIT_PUSH_FAILED__LOCAL_COMMIT_PRESERVED__'+str(failed))

def verify_remote(repo,commit):
 git(repo,'fetch','--quiet','origin','main',timeout=180)
 ref=gout(repo,'rev-parse','refs/remotes/origin/main')
 need(ref==commit,'REMOTE_REF_NOT_COMMIT')
 one_model(repo,ref)
 need(gout(repo,'rev-parse',ref+':'+CANON)==CANON_BLOB,
      'REMOTE_CANONICAL_MODEL_CHANGED_UNEXPECTEDLY')
 for dest in PACKET_FILES:
  need(bool(gout(repo,'rev-parse',ref+':'+dest)),'REMOTE_PACKET_FILE_MISSING:'+dest)
 return ref

def media_scan(downloads):
 exe=shutil.which('termux-media-scan')
 if not exe:return 'UNAVAILABLE'
 try:
  p=run([exe,str(downloads/HTML_NAME)],check=False,timeout=20)
  return 'REQUESTED_NOT_VERIFIED' if p.returncode==0 else 'FAILED_EXIT_'+str(p.returncode)
 except Exception:return 'FAILED'

def receipt(downloads,data):
 lines=['CAMPAIGN='+PROJECT,'VERSION='+VERSION,'LANE=TERMUX_GIT_ONLY']
 lines.extend(f'{key}={value}' for key,value in data.items())
 data_bytes=('\n'.join(lines)+'\n').encode('utf8')
 try:public_write(downloads/RECEIPT_NAME,data_bytes)
 except Blocked:
  # A previous versioned receipt is an evidence artifact, never overwrite it.
  # Current definitive result stays visible in console / versioned operator log.
  emit('RECEIPT_FILE','PRIOR_VERSIONED_COLLISION__SEE_CONSOLE')
 else:emit('RECEIPT_FILE',str(downloads/RECEIPT_NAME))
 for line in lines:print(line,flush=True)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--packet',required=True);args=ap.parse_args()
 packet=Path(args.packet).resolve()
 need(packet.is_dir(),'PACKET_MISSING')
 downloads=Path.home()/'storage'/'downloads';need(downloads.is_dir(),'TERMUX_DOWNLOADS_UNAVAILABLE')
 work=Path.home()/'.local/share/repl-campaigns/pose-lab-bones-v0.6.6'
 work.mkdir(parents=True,exist_ok=True)
 emit('CAMPAIGN',PROJECT);emit('VERSION',VERSION)
 emit('SOURCE_MODEL_SHA256_PIN',CANON_SHA)
 emit('CANONICAL_GLB_POLICY','ONE_REPO_FILE_UNMODIFIED')
 repo=checkout(work)
 head=gout(repo,'rev-parse','HEAD');remote=gout(repo,'rev-parse','refs/remotes/origin/main')
 model=verify_repo(repo)
 html=render(repo,packet,model)
 report={
  'campaign':PROJECT,'version':VERSION,'source_commit':HEAD_LOCK,
  'canonical_model_path':CANON,'canonical_model_sha256':CANON_SHA,
  'canonical_model_git_blob_sha1':CANON_BLOB,'pose_editor_html_sha256':sha(html),
  'canonical_glb_mutated':False,'gait_animations_mutated':False,
  'skeleton_bones':50,'tip_protected_bones':['Bone_012','Bone_018','Bone_023','Bone_028'],
  'capabilities':['overlay_toggle','tap_bone','additive_selection','double_tap_empty_deselect',
   'two_finger_twist_local_axis','X_Y_Z_locks','accessible_selector','undo_redo',
   'reset_pose','export_quaternions_json','camera_mode','frozen_tip_preview'],
  'human_visual_acceptance':'PENDING'}
 # Verify deliverable is truly published and hashed before touching Git.
 emit('HTML_DELIVERY',public_write(downloads/HTML_NAME,html))
 report_data=(json.dumps(report,indent=2,sort_keys=True)+'\n').encode('utf8')
 emit('REPORT_DELIVERY',public_write(downloads/REPORT_NAME,report_data))
 emit('PUBLISHED_VIEWER_SHA256',sha(html))
 emit('CANONICAL_GLB_SHA256',sha((repo/CANON).read_bytes()))
 if head==HEAD_LOCK and remote==HEAD_LOCK:
  need(remote_ref(repo)==HEAD_LOCK,'REMOTE_MOVED__REFUSE_SOURCE_COMMIT')
  commit=stage_commit(repo,packet,sha(html));emit('LOCAL_COMMIT',commit)
 elif head!=remote:
  need(remote==HEAD_LOCK,'REMOTE_MAIN_ADVANCED_WHILE_LOCAL_AHEAD')
  need(all((repo/dest).is_file() for dest in PACKET_FILES),
       'LOCAL_AHEAD_NOT_OUR_CAMPAIGN__NO_PUSH')
  for dest,part in PACKET_FILES.items():
   need((repo/dest).read_bytes()==(packet/part).resolve().read_bytes(),
        'LOCAL_AHEAD_SOURCE_DIFFERS:'+dest)
  commit=head;emit('RUN_MODE','RESUME_EXISTING_LOCAL_COMMIT')
 else:
  need(all((repo/dest).is_file() for dest in PACKET_FILES),
      'REMOTE_ADVANCED_NOT_OUR_CAMPAIGN')
  for dest,part in PACKET_FILES.items():
   need((repo/dest).read_bytes()==(packet/part).resolve().read_bytes(),
        'REMOTE_ADVANCED_HAS_DIFFERENT_PACKET:'+dest)
  commit=head;emit('RUN_MODE','PREVIOUSLY_COMMITTED_AND_VERIFIED')
 if head!=remote or head==HEAD_LOCK:
  push_with_reconcile(repo,HEAD_LOCK,commit)
 remote_done=verify_remote(repo,commit)
 emit('TARGET_ARTIFACT','VIEWER_ONLY__NO_GLB_EDIT')
 emit('MEDIA_SCAN',media_scan(downloads))
 receipt(downloads,{
  'CAMPAIGN_STATUS':'DELIVERED_VIEWER__HUMAN_VISUAL_ACCEPTANCE_PENDING',
  'GITHUB_MAIN_READBACK':remote_done,'GITHUB_SINGLE_CANONICAL_GLB':1,
  'CANONICAL_GLB_SHA256':sha(model),'CANONICAL_GLB_MUTATION':'NONE',
  'FULL_INTERACTIVE_VIEWER':str(downloads/HTML_NAME),
  'VIEWER_SHA256':sha(html),'DIAGNOSTIC_REPORT':str(downloads/REPORT_NAME),
  'POSE_EXPORT':'FROM_VIEWER_SAVE_POSE_JSON',
  'HUMAN_VISUAL_ACCEPTANCE':'PENDING',
  'OPERATOR_ACTION':'Open viewer in Android browser; tap Pose Mode, select bones, twist two fingers, export pose JSON and a PNG'})

if __name__=='__main__':
 try:main()
 except Exception as e:
  if isinstance(e,Blocked):emit('CAMPAIGN_STATUS','BLOCKED')
  else:emit('CAMPAIGN_STATUS','FAILED');traceback.print_exc()
  emit('CAUSE',type(e).__name__+':'+str(e))
  emit('CANONICAL_GLB_MUTATION','NONE_BY_THIS_CAMPAIGN')
  emit('NEXT_ACTION','If a local Git commit was created but push failed, rerun SAME campaign; do not run diagnostic micro-scripts.')
  sys.exit(2)
