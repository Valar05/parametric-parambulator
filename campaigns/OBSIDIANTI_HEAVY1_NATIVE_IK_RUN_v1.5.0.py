#!/usr/bin/env python3
"""One-invocation Android Termux Git campaign: Heavy1 native controller-driven retarget.

No github direct writes; all repo mutations/commits/pushes happen in the
isolated, SHA-checked Termux Git checkout. Always preserve v1.4 diagnostics.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, pathlib, shutil, subprocess, sys, time, uuid, zipfile, math, html

VERSION='OBSIDIANTI_HEAVY1_NATIVE_IK_v1.5.0'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
MODEL='assets/obsidianti/Obsidianti.glb'
MODEL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
DONOR='diagnostics/obsidianti/lionheart-ik-all-v1.4.0/actions/Heavy1.json'
CALIB='diagnostics/obsidianti/lionheart-ik-all-v1.4.0/calibration.json'
AUDIT_MANIFEST='diagnostics/obsidianti/lionheart-ik-all-v1.4.0/manifest.json'
AUDIT_COMMIT='9c7d3774d945cc00bac1e4bfc621e50e3df7ba71'
DONOR_SHA='a14304e455f978fcdbb0607f187a175310e034fdfed7f83176402fd7eb9f1fd4'
CALIB_SHA='b6d23f49c67df7816124362f4b1ee540db5c16a672fbc8c435a7f503ca123336'
ANALYZER='campaigns/OBSIDIANTI_HEAVY1_NATIVE_IK_SOLVE_v1.5.0.py'
SCRIPT='campaigns/OBSIDIANTI_HEAVY1_NATIVE_IK_RUN_v1.5.0.py'
TEST='tests/OBSIDIANTI_HEAVY1_NATIVE_IK_TEST_v1.5.0.py'
DOC='docs/obsidianti/HEAVY1_NATIVE_IK_v1.5.0.md'
VIEW='review/obsidianti-heavy1-native-ik-v1.5.0.html'
FILES=(ANALYZER,SCRIPT,TEST,DOC,VIEW)
REPORT_DIR='diagnostics/obsidianti/heavy1-native-ik-v1.5.0'


def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()

def run(argv,timeout=300,env=None,required=True):
 last=None
 for attempt in range(2):
  try:
   p=subprocess.run([str(x) for x in argv],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,timeout=timeout)
  except subprocess.TimeoutExpired as e:
   last=RuntimeError('TIMEOUT '+repr(argv[:4]))
   if attempt==0:continue
   raise last
  if p.returncode and required:
   if attempt==0 and ('Could not resolve host' in p.stderr or 'Connection timed out' in p.stderr or 'TLS' in p.stderr):continue
   raise RuntimeError('COMMAND_FAILED exit='+str(p.returncode)+' '+repr(argv[:5])+' '+p.stderr[-1300:]+' '+p.stdout[-300:])
  return p
 raise last if last else RuntimeError('RUN_FAILED')

def git(repo,*args,timeout=300,required=True):
 return run(['git','-C',str(repo),*args],timeout=timeout,required=required)

def read_json(p):return json.loads(pathlib.Path(p).read_text())

def save_json(path,data):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n');os.replace(tmp,path)

def write_text(path,content):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(content)

def pointer(repo,path,rev='HEAD'):
 raw=git(repo,'show',rev+':'+path).stdout
 if not raw.startswith('version https://git-lfs.github.com/spec/v1\n'):raise RuntimeError('LFS_POINTER_MISSING:'+path)
 return next((x.split(':',1)[1].strip() for x in raw.splitlines() if x.startswith('oid sha256:')),None)

def ensure_lfs():
 if run(['git','lfs','version'],required=False).returncode:
  if not shutil.which('pkg'):raise RuntimeError('TERMUX_GIT_LFS_MISSING')
  run(['pkg','install','-y','git-lfs'],timeout=360)
 if run(['git','lfs','version'],required=False).returncode:raise RuntimeError('TERMUX_GIT_LFS_INSTALL_FAILED')

def commit(repo,files,reason):
 if not files:return None
 git(repo,'add','--',*files)
 staged=git(repo,'diff','--cached','--name-only').stdout.splitlines()
 if not staged:return None
 if set(staged)-set(files):raise RuntimeError('STAGED_SCOPE_VIOLATION:'+repr(staged))
 if not git(repo,'config','--get','user.name',required=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Campaign')
 if not git(repo,'config','--get','user.email',required=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')
 git(repo,'commit','-m',reason,timeout=200)
 return git(repo,'rev-parse','HEAD').stdout.strip()

def push(repo,head):
 p=git(repo,'push','origin','HEAD:refs/heads/main',timeout=370,required=False)
 if p.returncode:
  if 'non-fast-forward' in p.stderr or '[rejected]' in p.stderr:raise RuntimeError('REMOTE_MAIN_ADVANCED_NO_FORCE')
  if shutil.which('gh'):
   p=run(['git','-C',str(repo),'-c','credential.helper=!gh auth git-credential','push','origin','HEAD:refs/heads/main'],required=False,timeout=370)
  if p.returncode:raise RuntimeError('PUSH_FAILED:'+p.stderr[-1400:])
 remote=git(repo,'ls-remote','origin','refs/heads/main',timeout=110).stdout.split()[0]
 if remote!=head:raise RuntimeError('REMOTE_HEAD_READBACK_WRONG')
 git(repo,'fetch','--no-tags','origin','main',timeout=200)
 if git(repo,'rev-parse','refs/remotes/origin/main').stdout.strip()!=head:raise RuntimeError('REMOTE_FETCH_READBACK_WRONG')
 return remote

def validate_rules(repo):
 agents=repo/'AGENTS.md'
 if not agents.is_file():raise RuntimeError('RULES_READ_BLOCKED')
 content=agents.read_text()
 if not content.startswith('# AGENTS.md') or 'Campaign Etiquette' not in content or 'Termux Git' not in content:raise RuntimeError('RULES_READ_BLOCKED_INVALID')
 blob=git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()
 if git(repo,'hash-object','--',str(agents)).stdout.strip()!=blob:raise RuntimeError('RULES_READ_CHANGED')
 return {'gitBlob':blob,'sha256':sha(agents),'campaignEtiquetteSource':'Home Center CAMPAIGN_ETIQUETTE:1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI; author read 2026-11-04'}

def verify_packet(packet):
 manifest=read_json(packet/'manifest.json')
 if manifest.get('version')!=VERSION or set(manifest.get('files',{}))!=set(FILES):raise RuntimeError('WRONG_PACKET_MANIFEST')
 for f,h in manifest['files'].items():
  if not (packet/f).is_file() or sha(packet/f)!=h:raise RuntimeError('PACKET_SHA_MISMATCH:'+f)
 return manifest

def verify_remote_audit(repo):
 if git(repo,'merge-base','--is-ancestor',AUDIT_COMMIT,'HEAD',required=False).returncode:
  # shallow clone may need a bounded history extension for the pinned dataset commit
  git(repo,'fetch','--deepen=30','origin','main',timeout=200)
  if git(repo,'merge-base','--is-ancestor',AUDIT_COMMIT,'HEAD',required=False).returncode:raise RuntimeError('VERIFIED_AUDIT_COMMIT_NOT_IN_HISTORY')
 if sha(repo/DONOR)!=DONOR_SHA or sha(repo/CALIB)!=CALIB_SHA:raise RuntimeError('SAVED_NATIVE_IK_DATA_CHANGED')
 d=read_json(repo/AUDIT_MANIFEST)
 if d.get('artifactHashes',{}).get('actions/Heavy1.json')!=DONOR_SHA or d['artifactHashes'].get('calibration.json')!=CALIB_SHA:
  raise RuntimeError('AUDIT_HASH_MANIFEST_CHANGED')
 if d.get('sourceModelSha256')!=MODEL_SHA or d.get('actionNames')!=['Idle','Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp']:
  raise RuntimeError('AUDIT_PROVENANCE_OR_ACTION_SCOPE_CHANGED')

def check_guarded_binary(original,candidate):
 # Verify independent structural and immutable animation records, not only a hash.
 import importlib.util
 mpath=pathlib.Path(__file__).with_name('OBSIDIANTI_HEAVY1_NATIVE_IK_SOLVE_v1.5.0.py')
 spec=importlib.util.spec_from_file_location('h1_native_ik_solve_guard',mpath)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 M=mod.load_math(mpath.parents[1]);ga,ba=M.load_glb(original);gb,bb=M.load_glb(candidate)
 if len(ga['animations'])!=len(gb['animations']):raise RuntimeError('CLIP_COUNT_CHANGED')
 if not bytes(bb).startswith(bytes(ba)):raise RuntimeError('BIN_PREFIX_CHANGED')
 for field in ('nodes','skins','meshes','scenes','materials','textures','images'):
  if ga.get(field)!=gb.get(field):raise RuntimeError('STRUCTURAL_CHANGE:'+field)
 changes=[]
 for a,b in zip(ga['animations'],gb['animations']):
  if a['name']!=b['name']:raise RuntimeError('ACTION_ORDER_CHANGED')
  if a['name']!='Lionheart_Heavy1':
   if a!=b:raise RuntimeError('PROTECTED_ACTION_MODIFIED:'+a['name'])
  else:
   names={i:n.get('name') for i,n in enumerate(ga['nodes'])}
   aa={(c['target']['node'],c['target']['path']):a['samplers'][c['sampler']] for c in a['channels']}
   bb2={(c['target']['node'],c['target']['path']):b['samplers'][c['sampler']] for c in b['channels']}
   if set(aa)!=set(bb2):raise RuntimeError('HEAVY1_CHANNEL_SET_CHANGED')
   for key in aa:
    if aa[key]!=bb2[key]:
     changes.append(names[key[0]]+'/'+key[1])
 allowed={'mixamorig:'+side+part+'/rotation' for side in ('Left','Right') for part in ('UpLeg','Leg','Foot')}
 if set(changes)!=allowed:raise RuntimeError('EDIT_TRACK_WHITELIST_VIOLATION:'+str(changes))
 return sorted(changes)

def svg_evidence(out,trace):
 # Transparent model-independent kinematic evidence; no claim of photographic render.
 data=read_json(trace);frames=data['probes'];lines=[]
 for side in ('Left','Right'):
  for field,col in (('originalAnkleWorld_m','#9ca3af'),('ankleWorld_m','#4db6ac'),('controllerDesiredWorld_m','#ffbb55')):
   points=[]
   for row in frames:
    if side not in row:continue
    t=row['time'];v=row[side][field]
    # x = time; y = actor-space Z (horizontal foot advance)
    X=55+t*670;Y=215+(-v[2])*150+(0 if side=='Left' else 290)
    points.append(f'{X:.1f},{Y:.1f}')
   if points:lines.append('<polyline fill="none" stroke="'+col+'" stroke-width="2" points="'+' '.join(points)+'"/>')
 for yy,side in ((100,'Left'),(390,'Right')):
  lines.append(f'<text x="55" y="{yy}" fill="#e1e8f0" font-size="19">{side} foot: world Z vs time</text>')
  lines.append(f'<path d="M55 {yy+130} H730" stroke="#334155"/>')
 lines.append('<text x="55" y="626" fill="#e1e8f0" font-size="16">Gray: old GLB   Teal: IK-baked ankle   Amber: native-controller target</text>')
 lines.append('<text x="55" y="650" fill="#cbd5e1" font-size="13">Kinematic overlay, not skinned-mesh render or owner approval. Y is inverted target world Z.</text>')
 svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 690"><rect width="800" height="690" fill="#121a27"/>'+''.join(lines)+'</svg>'
 write_text(out,svg)

def create_zip(dst,files):
 if dst.exists():raise RuntimeError('EVIDENCE_ZIP_COLLISION:'+str(dst))
 with zipfile.ZipFile(dst,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
  for name,path in sorted(files.items()):
   if pathlib.Path(path).is_file():z.write(path,name)
 return sha(dst)

def start_viewer(repo,work):
 import socket, urllib.request
 for port in range(8179,8189):
  sock=socket.socket();ok=False
  try:sock.bind(('127.0.0.1',port));ok=True
  except OSError:pass
  finally:sock.close()
  if not ok:continue
  log=open(work/'viewer.log','ab',buffering=0)
  try:
   process=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(repo)],
    stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   time.sleep(.5)
   path='/review/obsidianti-heavy1-native-ik-v1.5.0.html'
   try:
    with urllib.request.urlopen('http://127.0.0.1:'+str(port)+path,timeout=3) as resp:
     if resp.status==200:return {'url':'http://127.0.0.1:'+str(port)+path,'status':'HTTP_200_ONLY_OWNER_VISUAL_PENDING','pid':process.pid}
   except Exception:pass
   if process.poll() is None:process.terminate()
  finally:log.close()
 return {'status':'VIEWER_UNAVAILABLE'}

def main(packet):
 packet=pathlib.Path(packet).resolve();verify_packet(packet)
 print('CAMPAIGN='+VERSION+'\nAUTHORITY=TERMUX_GIT_ONLY\nPACKET_SHA_VERIFIED=YES',flush=True)
 ensure_lfs()
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:7]
 work=pathlib.Path.home()/'.local/state'/VERSION/runid;work.mkdir(parents=True)
 downloads=pathlib.Path.home()/'storage/downloads'
 if not downloads.is_dir():downloads=work
 receipt=downloads/(VERSION+'_'+runid+'_RECEIPT.json')
 data={'campaign':VERSION,'runId':runid,'status':'STARTED','stage':'SOURCE_VERIFY','authority':'TERMUX_GIT_ONLY',
  'modelChanged':False,'ownerVisualAccepted':False,'modelExpectedSha256':MODEL_SHA,
  'donorHeavy1Sha256':DONOR_SHA,'sourceDatasetCommit':AUDIT_COMMIT,'repo':REPO,
  'rules':{'campaignEtiquetteLiveReadByAuthorDate':'2026-11-04','campaignEtiquetteId':'1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'}}
 save_json(receipt,data)
 try:
  env=os.environ.copy();env.update(GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
  repo=work/'repo';run(['git','clone','--depth=25','--single-branch','--branch','main',REMOTE,str(repo)],env=env,timeout=360)
  sourcehead=git(repo,'rev-parse','HEAD').stdout.strip();data['sourceMainHead']=sourcehead
  data['rules']['live']=validate_rules(repo)
  if git(repo,'status','--porcelain=v1','--untracked-files=all').stdout.strip():raise RuntimeError('ISOLATED_CLONE_DIRTY')
  if pointer(repo,MODEL)!=MODEL_SHA:raise RuntimeError('CANONICAL_LFS_CHANGED_FROM_PINNED_REJECTED_INPUT')
  repl=git(repo,'rev-parse','HEAD:assets/repl/Repl.glb').stdout.strip();data['replTreeBefore']=repl
  verify_remote_audit(repo)
  already=[f for f in FILES if (repo/f).exists()]
  if already:
   if len(already)!=len(FILES) or any(sha(repo/f)!=sha(packet/f) for f in FILES):raise RuntimeError('VERSIONED_SOURCE_COLLISION:'+repr(already))
   data['resumedIdenticalSource']=True
  elif (repo/REPORT_DIR).exists():raise RuntimeError('REPORT_PREFIX_COLLISION')
  data['stage']='DOWNLOAD_REAL_LFS_INPUT';save_json(receipt,data)
  git(repo,'lfs','pull','--include='+MODEL,'--exclude=',timeout=600)
  if sha(repo/MODEL)!=MODEL_SHA:raise RuntimeError('CURRENT_MODEL_BINARY_HASH_NOT_MATCH')
  if len(list((repo/'assets/obsidianti').glob('*.glb')))!=1:raise RuntimeError('MULTIPLE_OBSIDIANTI_CANONICAL_GLBS')
  # Test source scripts before any Git mutation.
  for f in FILES:
   if not (repo/f).exists():
    (repo/f).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(packet/f,repo/f)
  testproc=run([sys.executable,str(repo/TEST),'--repo',str(repo)],timeout=150)
  data['testReceipt']=testproc.stdout.strip()
  if 'ALL_TESTS_PASSED' not in testproc.stdout:raise RuntimeError('TESTS_DID_NOT_PROVE_RUNTIME')
  if not already:
   data['stage']='GIT_COMMIT_SOURCE_FIRST';save_json(receipt,data)
   src_commit=commit(repo,list(FILES),'Obsidianti: Heavy1 native IK foot-controller transfer campaign v1.5.0')
   if not src_commit:raise RuntimeError('NEW_SOURCE_COMMIT_MISSING')
   data['sourceCommit']=src_commit
   push(repo,src_commit)
  else:data['sourceCommit']=sourcehead
  if git(repo,'status','--porcelain=v1','--untracked-files=all').stdout.strip():raise RuntimeError('DIRTY_AFTER_SOURCE_PUBLICATION')
  data['stage']='READ_ONLY_REAL_SKINNED_PREFLIGHT';save_json(receipt,data)
  solver=repo/ANALYZER;report=work/'heavy1_native_preflight.json';trace=work/'heavy1_native_probes.json'
  cmd=[sys.executable,str(solver),'--model',str(repo/MODEL),'--repo',str(repo),
   '--source',str(repo/DONOR),'--calibration',str(repo/CALIB),'--report',str(report),'--preview',str(trace)]
  cp=run(cmd,timeout=1200,required=False)
  write_text(work/'solver_preflight.log',cp.stdout+'\n'+cp.stderr)
  if report.exists():
   data['preflight']=read_json(report)
   data['preflightSha256']=sha(report)
  if cp.returncode:
   data['status']='BLOCKED_HEAVY1_PHYSICAL_PREFLIGHT_MODEL_UNCHANGED'
   raise RuntimeError('NATIVE_FOOT_IK_PREFLIGHT_FAILED:'+cp.stderr[-800:])
  if sha(repo/MODEL)!=MODEL_SHA:raise RuntimeError('PREFLIGHT_MUTATED_CANONICAL')
  candidate=work/'candidate.glb';shutil.copyfile(repo/MODEL,candidate)
  checkreport=work/'heavy1_native_apply.json'
  data['stage']='APPLY_TO_QUARANTINED_CANDIDATE';save_json(receipt,data)
  apply_cmd=list(cmd)
  apply_cmd[apply_cmd.index('--model')+1]=str(candidate)
  apply_cmd[apply_cmd.index('--report')+1]=str(checkreport)
  apply_cmd[apply_cmd.index('--preview')+1]=str(work/'heavy1_native_apply_probes.json')
  cp=run(apply_cmd+['--write'],timeout=1200,required=False)
  write_text(work/'solver_apply.log',cp.stdout+'\n'+cp.stderr)
  # Apply ONLY on the isolated candidate copy; never the Git canonical yet.
  if cp.returncode:raise RuntimeError('CANDIDATE_WRITE_FAILED:'+cp.stderr[-1300:])
  if sha(repo/MODEL)!=MODEL_SHA:raise RuntimeError('UNSAFE_APPLY_TOUCHED_CANONICAL_EARLY')
  if not checkreport.exists():raise RuntimeError('APPLY_REPORT_MISSING')
  applied=read_json(checkreport)
  if applied.get('candidateSha256')!=data['preflight'].get('candidateSha256'):
   raise RuntimeError('PREFLIGHT_VS_FINAL_CANDIDATE_SHA_DIFFERS')
  data['changedTracksVerified']=check_guarded_binary(repo/MODEL,candidate)
  data['candidateSha256']=sha(candidate)
  if data['candidateSha256']!=applied['candidateSha256']:raise RuntimeError('CANDIDATE_BINARY_HASH_NOT_MATCH')
  svg=work/'heavy1_foot_path.svg';svg_evidence(svg,trace)
  # Only after full preflight, independent structural guard and actual candidate
  # SHA equality are we allowed to replace the SAME canonical model.
  data['stage']='BUILD_PERSISTENT_REVIEW_EVIDENCE';save_json(receipt,data)
  reportgit=repo/REPORT_DIR;reportgit.mkdir(parents=True,exist_ok=False)
  shutil.copyfile(report,reportgit/'preflight.json')
  shutil.copyfile(trace,reportgit/'ankle_probes.json')
  shutil.copyfile(svg,reportgit/'foot_path.svg')
  data['candidateEvidence']={'preflight':str(reportgit.relative_to(repo))+'/preflight.json',
    'trace':str(reportgit.relative_to(repo))+'/ankle_probes.json',
    'svg':str(reportgit.relative_to(repo))+'/foot_path.svg'}
  if git(repo,'rev-parse','HEAD:assets/repl/Repl.glb').stdout.strip()!=repl:raise RuntimeError('REPL_CHANGED')
  # SAFETY: before model installation, ensure independent full-clip guard passed.
  if sha(repo/MODEL)!=MODEL_SHA:raise RuntimeError('MODEL_SHA_CHANGED_BEFORE_INSTALL')
  install_tmp=(repo/MODEL).with_name('.obsidianti-heavy1-atomic-'+runid+'.tmp')
  shutil.copyfile(candidate,install_tmp)
  if sha(install_tmp)!=data['candidateSha256']:raise RuntimeError('TEMP_INSTALL_SHA_MISMATCH')
  os.replace(install_tmp,repo/MODEL)
  if sha(repo/MODEL)!=data['candidateSha256']:raise RuntimeError('FINAL_INSTALL_SHA_MISMATCH')
  data['stage']='COMMIT_SAME_CANONICAL_AND_EVIDENCE';save_json(receipt,data)
  changed=[MODEL,*[str(p.relative_to(repo)) for p in reportgit.iterdir()]]
  if git(repo,'check-attr','filter','--',MODEL).stdout.strip().split()[-1]!='lfs':raise RuntimeError('GIT_LFS_NOT_ENFORCED')
  data['modelCommit']=commit(repo,changed,'Obsidianti: Heavy1 controller-driven leg bake candidate; full review pending')
  if not data['modelCommit']:raise RuntimeError('MODEL_COMMIT_MISSING')
  if pointer(repo,MODEL)!=data['candidateSha256']:raise RuntimeError('POSTCOMMIT_LFS_POINTER_WRONG')
  if git(repo,'status','--porcelain=v1','--untracked-files=all').stdout.strip():raise RuntimeError('DIRTY_FINAL_CHECKOUT')
  git(repo,'lfs','push','origin','HEAD',timeout=600)
  data['remoteHeadVerified']=push(repo,data['modelCommit'])
  if pointer(repo,MODEL,'refs/remotes/origin/main')!=data['candidateSha256']:raise RuntimeError('REMOTE_MODEL_POINTER_WRONG')
  if git(repo,'rev-parse','refs/remotes/origin/main:assets/repl/Repl.glb').stdout.strip()!=repl:raise RuntimeError('REMOTE_REPL_CHANGED')
  data['status']='PUBLISHED_HEAVY1_NATIVE_IK_CANDIDATE_VISUAL_REVIEW_REQUIRED'
  data['modelChanged']=True;data['ownerVisualAccepted']=False;data['viewer']=start_viewer(repo,work)
  save_json(receipt,data)
  print('STATUS='+data['status']+'\nREMOTE_HEAD='+data['remoteHeadVerified']+'\nMODEL_SHA256='+data['candidateSha256'],flush=True)
  if data['viewer'].get('url'):print('REVIEW_URL='+data['viewer']['url'],flush=True)
  return 0
 except Exception as err:
  # Durable no-model-write record for a physics failure, through the same
  # authorized Termux Git lane. A report doesn't turn a failed repair into success.
  try:
   if data.get('stage')=='READ_ONLY_REAL_SKINNED_PREFLIGHT' and report.exists() and repo.is_dir() and (repo/ANALYZER).exists():
    failure=read_json(report)
    if failure.get('status')=='PHYSICAL_PREFLIGHT_FAILED_MODEL_UNCHANGED' and sha(repo/MODEL)==MODEL_SHA:
     diagnostics=repo/REPORT_DIR
     if not diagnostics.exists():
      diagnostics.mkdir(parents=True,exist_ok=False)
      dst=diagnostics/'preflight-failed.json';shutil.copyfile(report,dst)
      bad=commit(repo,[str(dst.relative_to(repo))],'Obsidianti Heavy1: retain failed native IK physical preflight; no model change')
      if bad:
       push(repo,bad)
       if pointer(repo,MODEL,'refs/remotes/origin/main')!=MODEL_SHA:
        raise RuntimeError('FAILED_PREFLIGHT_MODEL_POINTER_DRIFT')
       data['failureDiagnosticRemoteCommit']=bad
       data['failureDiagnosticSavedGit']=True
  except Exception as persist:
   data['failureDiagnosticSaveError']=str(persist)
  if not data.get('modelChanged'):
   data['status']=data.get('status','BLOCKED_NO_MODEL_SUCCESS') if data.get('status') not in ('STARTED',None) else 'BLOCKED_NO_MODEL_SUCCESS'
  data['error']=str(err)
  save_json(receipt,data)
  print('STATUS='+data['status']+'\nSTAGE='+str(data.get('stage'))+'\nERROR='+str(err)+'\nRECEIPT='+str(receipt),flush=True)
  return 2
 finally:
  # Always hand off an inspectable phone receipt and preflight report.
  try:
   files={'receipt.json':receipt,'solver_preflight.log':work/'solver_preflight.log',
          'preflight.json':work/'heavy1_native_preflight.json','ankle_probes.json':work/'heavy1_native_probes.json',
          'foot_path.svg':work/'heavy1_foot_path.svg','solver_apply.log':work/'solver_apply.log'}
   archive=downloads/(VERSION+'_'+runid+'_HANDOFF.zip')
   digest=create_zip(archive,files)
   data['handoffZip']=str(archive);data['handoffZipSha256']=digest
   save_json(receipt,data)
   print('HANDOFF_ZIP='+str(archive)+'\nHANDOFF_SHA256='+digest+'\nRECEIPT='+str(receipt),flush=True)
  except Exception as ex:print('HANDOFF_ZIP_ERROR='+str(ex),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--packet',required=True);a=p.parse_args()
 sys.exit(main(pathlib.Path(a.packet)))
