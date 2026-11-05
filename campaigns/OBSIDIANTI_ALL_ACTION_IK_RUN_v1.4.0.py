#!/usr/bin/env python3
"""One-invocation, no-model-mutation Termux Git campaign for all Lionheart IK action data."""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, pathlib, shutil, subprocess, sys, time, uuid, zipfile

VERSION='OBSIDIANTI_ALL_ACTION_IK_v1.4.0'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
SOURCE='assets/obsidianti/source/LionheartLancer.blend'
MODEL='assets/obsidianti/Obsidianti.glb'
SOURCE_SHA='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
MODEL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
ACTIONS=('Idle','Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
BASE='diagnostics/obsidianti/lionheart-ik-all-v1.4.0'
FILES=(
 'campaigns/OBSIDIANTI_ALL_ACTION_IK_BLENDER_v1.4.0.py',
 'campaigns/OBSIDIANTI_ALL_ACTION_IK_ANALYZE_v1.4.0.py',
 'campaigns/OBSIDIANTI_ALL_ACTION_IK_RUN_v1.4.0.py',
 'docs/obsidianti/ALL_ACTION_IK_AUDIT_v1.4.0.md',
 'tests/OBSIDIANTI_ALL_ACTION_IK_TEST_v1.4.0.py',
)

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def exec_cmd(args,timeout=240,env=None,required=True):
 p=subprocess.run([str(x) for x in args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,timeout=timeout)
 if required and p.returncode:raise RuntimeError('COMMAND_FAILED '+str(args[:6])+' code='+str(p.returncode)+' '+p.stderr[-1800:])
 return p

def git(root,*args,timeout=180,required=True):return exec_cmd(['git','-C',str(root),*args],timeout=timeout,required=required)

def save_json(path,obj):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');os.replace(tmp,path)

def ensure_lfs():
 if exec_cmd(['git','lfs','version'],required=False).returncode:
  pkg=shutil.which('pkg')
  if not pkg:raise RuntimeError('GIT_LFS_UNAVAILABLE_IN_TERMUX')
  exec_cmd([pkg,'install','-y','git-lfs'],timeout=320)
 if exec_cmd(['git','lfs','version'],required=False).returncode:raise RuntimeError('GIT_LFS_INSTALL_FAILED')

def pointer(root,file):
 text=git(root,'show','HEAD:'+file).stdout
 if not text.startswith('version https://git-lfs.github.com/spec/v1\n'):raise RuntimeError('EXPECTED_LFS_POINTER:'+file)
 for line in text.splitlines():
  if line.startswith('oid sha256:'):return line[len('oid sha256:'):]
 raise RuntimeError('INVALID_LFS_POINTER:'+file)

def push(repo,head):
 p=git(repo,'push','origin','HEAD:refs/heads/main',timeout=300,required=False)
 if p.returncode:
  if 'non-fast-forward' in p.stderr or '[rejected]' in p.stderr:raise RuntimeError('REMOTE_MAIN_MOVED_NO_FORCE_PUSH')
  if shutil.which('gh'):
   p=exec_cmd(['git','-C',str(repo),'-c','credential.helper=!gh auth git-credential','push','origin','HEAD:refs/heads/main'],timeout=300,required=False)
  if p.returncode:raise RuntimeError('GIT_PUSH_FAILED:'+p.stderr[-1200:])
 remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]
 if remote!=head:raise RuntimeError('REMOTE_READBACK_HEAD_MISMATCH')
 git(repo,'fetch','--no-tags','origin','main',timeout=180)
 if git(repo,'rev-parse','refs/remotes/origin/main').stdout.strip()!=head:raise RuntimeError('FETCHED_MAIN_HEAD_MISMATCH')
 return remote

def run_blender(repo,work,data):
 native=shutil.which('blender')
 blender=repo/'campaigns/OBSIDIANTI_ALL_ACTION_IK_BLENDER_v1.4.0.py'
 if native:
  argv=[native,'--background','--disable-autoexec','--python',str(blender),'--','--source',str(repo/SOURCE),'--output',str(data),'--expected-sha256',SOURCE_SHA]
 else:
  proot=shutil.which('proot-distro')
  if not proot:raise RuntimeError('BLENDER_NOT_AVAILABLE_NATIVE_OR_DEBIAN_PROOT')
  argv=[proot,'login','debian','--bind',str(repo.resolve())+':/mnt/obs-ik-repo',
     '--bind',str(work.resolve())+':/mnt/obs-ik-work','--','blender','--background','--disable-autoexec',
     '--python','/mnt/obs-ik-repo/'+str(blender.relative_to(repo)),'--',
     '--source','/mnt/obs-ik-repo/'+SOURCE,'--output','/mnt/obs-ik-work/diagnostics','--expected-sha256',SOURCE_SHA]
 p=exec_cmd(argv,timeout=900,required=False)
 (work/'source-blender.log').write_text(p.stdout+'\n'+p.stderr)
 if p.returncode:raise RuntimeError('NATIVE_BLENDER_EVALUATION_FAILED:'+p.stderr[-1600:])
 if 'ALL_LIONHEART_ACTIONS_EVALUATED=11' not in p.stdout:raise RuntimeError('BLENDER_ALL_ACTION_GATE_MISSING')


def test_diagnostics(data):
 rig=json.loads((data/'source-rig.json').read_text())
 if rig.get('actionNames')!=list(ACTIONS):raise RuntimeError('SOURCE_ACTION_COUNT_OR_NAMES_WRONG')
 if rig.get('sourceSha256')!=SOURCE_SHA:raise RuntimeError('SOURCE_ACTION_PROVENANCE_WRONG')
 samples={}
 for name in ACTIONS:
  d=json.loads((data/'actions'/f'{name}.json').read_text())
  f=d['frames'];times=[row['timeSeconds'] for row in f]
  if name!='Idle' and (len(f)<3 or any(b<=a for a,b in zip(times,times[1:]))):raise RuntimeError('INVALID_FRAME_TIMING:'+name)
  for frame in f:
   if not all(x in frame['bones'] for x in ('LeftFoot.IK','RightFoot.IK','LeftKnee.IK','RightKnee.IK','mixamorig:LeftFoot','mixamorig:RightFoot','mixamorig:Hips')):raise RuntimeError('ACTION_IK_BONES_MISSING:'+name)
   if not all(side in frame['legsRelativePelvis'] for side in ('Left','Right')):raise RuntimeError('ACTION_LEG_RELATIVE_MISSING:'+name)
  samples[name]={'frameCount':len(f),'durationSeconds':d['durationSeconds'],'sha256':sha(data/'actions'/f'{name}.json')}
 return samples


def export_downloads(path,diagnostics,receipt,report):
 target=path
 if target.exists():raise RuntimeError('EXISTING_OUTPUT_ZIP_COLLISION:'+str(target))
 with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
  for p in sorted(diagnostics.rglob('*.json')):
   z.write(p,p.relative_to(diagnostics.parent))
  z.writestr('RUN_RECEIPT.json',json.dumps(receipt,indent=2,sort_keys=True))
  z.writestr('README.txt',report)
 return sha(target)


def main(packet):
 os.environ['PYTHONDONTWRITEBYTECODE']='1'
 packet=pathlib.Path(packet).resolve();manifest=json.loads((packet/'manifest.json').read_text())
 if manifest['version']!=VERSION or set(manifest['files'])!=set(FILES):raise RuntimeError('CAMPAIGN_PACKET_WRONG_MANIFEST')
 for p,expected in manifest['files'].items():
  if not (packet/p).is_file() or sha(packet/p)!=expected:raise RuntimeError('CAMPAIGN_PACKET_SHA_MISMATCH:'+p)
 print('PACKET_SOURCE_SHA_VERIFIED=YES',flush=True)
 ensure_lfs()
 now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 work=pathlib.Path.home()/'.local/state'/VERSION/(now+'-'+uuid.uuid4().hex[:7]);work.mkdir(parents=True)
 downloads=pathlib.Path.home()/'storage/downloads'
 downloads=downloads if downloads.is_dir() else work
 receipt_file=downloads/(VERSION+'_'+work.name+'_RECEIPT.json')
 receipt={'campaign':VERSION,'authority':'TERMUX_GIT_ONLY','modelChanged':False,'modelApproved':False,
   'requestedActions':list(ACTIONS),'sourceSha256Expected':SOURCE_SHA,'modelSha256Expected':MODEL_SHA,
   'status':'RUNNING','stage':'CLONE','sourceFiles':list(FILES),
   'ruleAuthority':{'liveAgentsRepository':'Valar05/parametric-parambulator',
     'etiquetteHomeCenterId':'1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI',
     'authorReadTime':'2026-11-04'},'workdir':str(work)}
 save_json(receipt_file,receipt)
 try:
  env=os.environ.copy();env.update(GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
  repo=work/'repo'
  exec_cmd(['git','clone','--depth=1','--single-branch','--branch','main',REMOTE,str(repo)],env=env,timeout=360)
  source_head=git(repo,'rev-parse','HEAD').stdout.strip()
  receipt['sourceMainHead']=source_head
  agents=repo/'AGENTS.md'
  if not agents.exists() or not agents.read_text().startswith('# AGENTS.md'):raise RuntimeError('RULES_READ_BLOCKED')
  rules_sha=git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()
  if git(repo,'hash-object','--',str(agents)).stdout.strip()!=rules_sha:raise RuntimeError('RULES_READ_CHANGED')
  receipt['rulesGitBlob']=rules_sha;receipt['rulesSha256']=sha(agents)
  if git(repo,'status','--porcelain=v1').stdout.strip():raise RuntimeError('UNEXPECTED_DIRTY_CLONE')
  if pointer(repo,SOURCE)!=SOURCE_SHA or pointer(repo,MODEL)!=MODEL_SHA:raise RuntimeError('REMOTE_LFS_SOURCE_OR_MODEL_CHANGED')
  original_repl=git(repo,'rev-parse','HEAD:assets/repl/Repl.glb').stdout.strip()
  # Fail closed on ANY existing destination; no reset/stash/silent reuse.
  for p in FILES:
   if (repo/p).exists():raise RuntimeError('VERSIONED_DESTINATION_COLLISION:'+p)
  if (repo/BASE).exists():raise RuntimeError('DIAGNOSTIC_DATASET_PATH_ALREADY_EXISTS')
  receipt['stage']='DOWNLOAD_PROVENANCE_BINARIES';save_json(receipt_file,receipt)
  print('STAGE=DOWNLOAD_PROVENANCE_BINARIES SOURCE_HEAD='+source_head,flush=True)
  git(repo,'lfs','pull','--include='+SOURCE+','+MODEL,'--exclude=',timeout=780)
  if sha(repo/SOURCE)!=SOURCE_SHA or sha(repo/MODEL)!=MODEL_SHA:raise RuntimeError('SOURCE_OR_TARGET_LFS_BINARY_CORRUPTED')
  receipt['verifiedRealBinaryHashes']={SOURCE:SOURCE_SHA,MODEL:MODEL_SHA}
  # Only write all new versioned scripts after ensuring file version collision gate.
  for path in FILES:
   dest=repo/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(packet/path,dest)
  test=repo/'tests/OBSIDIANTI_ALL_ACTION_IK_TEST_v1.4.0.py'
  test_output=exec_cmd([sys.executable,str(test)],timeout=40)
  if 'TESTS_PASSED=' not in test_output.stdout:raise RuntimeError('REGRESSION_TEST_RECEIPT_MISSING')
  receipt['staticRegressionTests']=test_output.stdout.strip()
  data=work/'diagnostics';data.mkdir()
  receipt['stage']='BLENDER_NATIVE_EVALUATED_ALL_ACTIONS';save_json(receipt_file,receipt)
  print('STAGE=BLENDER_NATIVE_EVALUATED_ALL_ACTIONS',flush=True)
  run_blender(repo,work,data)
  samples=test_diagnostics(data)
  receipt['actionSamples']=samples
  receipt['stage']='CALIBRATE_APPROVED_TARGET_IDLE';save_json(receipt_file,receipt)
  analyzer=repo/'campaigns/OBSIDIANTI_ALL_ACTION_IK_ANALYZE_v1.4.0.py'
  p=exec_cmd([sys.executable,str(analyzer),'--target',str(repo/MODEL),'--diagnostics',str(data)],timeout=240)
  (work/'calibrate.log').write_text(p.stdout+'\n'+p.stderr)
  calibration=json.loads((data/'calibration.json').read_text())
  if len(calibration['actions'])!=11 or calibration['modelSha256']!=MODEL_SHA:raise RuntimeError('INCOMPLETE_CALIBRATION')
  if sha(repo/MODEL)!=MODEL_SHA or sha(repo/SOURCE)!=SOURCE_SHA:raise RuntimeError('READ_ONLY_AUDIT_MUTATED_ASSETS')
  receipt['stage']='PERSIST_EVALUATED_DATA';save_json(receipt_file,receipt)
  dest=repo/BASE;shutil.copytree(data,dest)
  dataset_files=sorted(str(x.relative_to(repo)) for x in dest.rglob('*.json'))
  manifest={'schema':'obsidianti-all-action-ik-audit-publication','version':VERSION,
     'repoSourceMainHead':source_head,'sourceModelSha256':MODEL_SHA,'donorBlendSha256':SOURCE_SHA,
     'sourceGitAgentsBlob':rules_sha,'actionNames':list(ACTIONS),
     'artifactHashes':{str(x.relative_to(dest)):sha(x) for x in sorted(dest.rglob('*.json'))},
     'groundContactPhysics':'NOT_PROVEN_BY_CONTROLLER_POSITION','noModelWrite':True,
     'executionLane':'Android Termux Git','ownerVisualVerdict':'NOT_REQUESTED_FOR_READ_ONLY_AUDIT'}
  save_json(dest/'manifest.json',manifest)
  # Copy a review-friendly archive to phone Downloads even if later push fails.
  report='Native Blender constraints evaluated across 11 Lionheart actions at full+half frames. Original model unchanged. See calibration.json and per-action files. Offsets are provisional and not ground contact proof.\n'
  archive=downloads/(VERSION+'_'+work.name+'_ALL_ACTIONS.zip')
  receipt['archivePath']=str(archive)
  receipt['stage']='COPY_PHONE_DOWNLOADS';save_json(receipt_file,receipt)
  receipt['archiveSha256']=export_downloads(archive,dest,receipt,report)
  print('LOCAL_ARCHIVE='+str(archive)+' SHA256='+receipt['archiveSha256'],flush=True)
  receipt['stage']='COMMIT_AND_PUSH_PERSISTENT_REPORT';save_json(receipt_file,receipt)
  if git(repo,'rev-parse','HEAD:assets/repl/Repl.glb').stdout.strip()!=original_repl:raise RuntimeError('REPL_CHANGED')
  if git(repo,'status','--porcelain=v1').stdout.count('??')==0:raise RuntimeError('EXPECTED_NEW_SOURCE_AND_DATA_FILES_NOT_DETECTED')
  if not git(repo,'config','user.name',required=False).stdout.strip():git(repo,'config','user.name','Obsidianti Diagnostic Campaign')
  if not git(repo,'config','user.email',required=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')
  allpaths=[*FILES,*[str(x.relative_to(repo)) for x in dest.rglob('*.json')]]
  git(repo,'add','--',*allpaths)
  staged=git(repo,'diff','--cached','--name-only').stdout.splitlines()
  if not staged or sorted(staged)!=sorted(allpaths):raise RuntimeError('STAGED_SCOPE_OR_DATASET_INCOMPLETE')
  git(repo,'commit','-m','Obsidianti: save native Lionheart all-action IK controller and Idle calibration audit',timeout=200)
  result_head=git(repo,'rev-parse','HEAD').stdout.strip();receipt['localCommit']=result_head
  if pointer(repo,MODEL)!=MODEL_SHA:raise RuntimeError('MODEL_POINTER_CHANGED_BY_READ_ONLY_AUDIT')
  if git(repo,'rev-parse','HEAD:assets/repl/Repl.glb').stdout.strip()!=original_repl:raise RuntimeError('REPL_AFTER_COMMIT_CHANGED')
  if git(repo,'status','--porcelain=v1').stdout.strip():raise RuntimeError('ISOLATED_REPO_DIRTY_AFTER_COMMIT')
  print('STAGE=REMOTE_PUSH_REPORT_ONLY',flush=True)
  receipt['remoteHeadVerified']=push(repo,result_head)
  if pointer(repo,MODEL)!=MODEL_SHA:raise RuntimeError('MODEL_CHANGED_AFTER_PUSH')
  remote_manifest=git(repo,'show','refs/remotes/origin/main:'+BASE+'/manifest.json').stdout
  if json.loads(remote_manifest)['artifactHashes']!=manifest['artifactHashes']:raise RuntimeError('REMOTE_REPORT_CONTENT_MISMATCH')
  receipt['remoteReportVerified']=True;receipt['remoteReportPrefix']=BASE
  receipt['modelChanged']=False;receipt['status']='ALL_11_NATIVE_IK_ACTIONS_SAVED_TO_REMOTE_GIT'
  save_json(receipt_file,receipt)
  print('STATUS='+receipt['status']+'\nREMOTE_HEAD='+result_head+'\nREPORT_DIR='+BASE+'\nMODEL_UNCHANGED_SHA256='+MODEL_SHA+'\nRECEIPT='+str(receipt_file),flush=True)
  return 0
 except Exception as e:
  receipt['status']='BLOCKED_NO_CLAIM_OF_REMOTE_SAVE';receipt['failureStage']=receipt.get('stage');receipt['error']=str(e)
  save_json(receipt_file,receipt)
  print('STATUS='+receipt['status']+'\nERROR='+str(e)+'\nRECEIPT='+str(receipt_file),flush=True)
  return 2

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--packet',required=True)
 args=parser.parse_args();sys.exit(main(args.packet))
