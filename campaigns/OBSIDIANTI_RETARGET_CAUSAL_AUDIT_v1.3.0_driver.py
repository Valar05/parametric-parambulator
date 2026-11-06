#!/usr/bin/env python3
"""One Termux invocation, repo-source first, actual historical read-only source evaluation."""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,time,traceback,uuid
V='OBSIDIANTI_RETARGET_CAUSAL_AUDIT_v1.3.0'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_HEAD='9c2529c309f79e8f6342a0850be3b61127b8b999'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
LIONHEART_SHA='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
TARGET_SHA='955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32'
CANONICAL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
DIR='diagnostics/obsidianti/retarget-causal-audit-v1.3.0'
SOURCES={'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER',
         'campaigns/'+V+'_driver.py':'driver.py',
         'campaigns/'+V+'_analyze.py':'analyze.py',
         'campaigns/'+V+'_summarize.py':'summarize.py',
         'tests/'+V+'_TEST.py':'test.py',
         'docs/obsidianti/RETARGET_CAUSAL_AUDIT_v1.3.0.md':'README.md',
         'campaigns/'+V+'.contract.json':'contract.json'}
EVIDENCE={DIR+'/'+x:x for x in ('CAUSAL_AUDIT.json','CAUSAL_AUDIT_CANONICAL.json','CAUSE_REPORT.md','EVIDENCE_RECEIPT.json')}
LOCKED=('assets/obsidianti/Obsidianti.glb','assets/repl/Repl.glb')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def cmd(args,timeout=240,env=None,check=True):
 r=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=timeout,env=env)
 if check and r.returncode:raise RuntimeError('COMMAND_FAILED='+repr([str(x) for x in args][:8])+'; STDOUT='+r.stdout[-900:]+'; STDERR='+r.stderr[-1400:])
 return r
def git(repo,*args,**kw):return cmd(['git','-C',str(repo),*args],**kw)
def safe_push(repo,expected,stage):
 """Reconcile ambiguous network push results before retry, never force push."""
 for attempt in range(3):
  pushed=git(repo,'push','origin','HEAD:refs/heads/main',timeout=420,check=False)
  read=git(repo,'ls-remote','origin','refs/heads/main',timeout=100,check=False)
  remote=read.stdout.strip().split()[0] if read.returncode==0 and read.stdout.strip() else None
  if remote==expected:return remote
  message=(pushed.stdout+'\n'+pushed.stderr)[-700:]
  if 'non-fast-forward' in message or '[rejected]' in message:
   raise RuntimeError(stage+'_CONCURRENT_REMOTE_UPDATE_NO_FORCE '+message)
  if attempt<2:time.sleep(2*(attempt+1))
 raise RuntimeError(stage+'_PUSH_OR_REMOTE_READBACK_FAILED local='+expected+' remote='+str(remote))

def atomic_copy(src,dst):
 src=pathlib.Path(src);dst=pathlib.Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():
  if sha(src)==sha(dst):return False
  raise RuntimeError('PATH_COLLISION_DIFFERENT_BYTES '+str(dst))
 tmp=dst.with_name('.'+dst.name+'.tmp-'+uuid.uuid4().hex)
 try:
  shutil.copyfile(src,tmp)
  if sha(src)!=sha(tmp):raise RuntimeError('FILE_COPY_SHA_MISMATCH '+str(src))
  os.replace(tmp,dst)
 finally:
  if tmp.exists():tmp.unlink()
 return True

def latest_donor():
 roots=[pathlib.Path.home()/'storage/downloads',pathlib.Path.home()/'storage/documents',pathlib.Path('/storage/emulated/0/Download')]
 seen=set()
 for root in roots:
  if not root.is_dir():continue
  for gl in ('LionheartLancer*.blend','Lionheart*.blend'):
   for p in root.glob(gl):
    if str(p) in seen:continue
    seen.add(str(p))
    if p.is_file() and sha(p)==LIONHEART_SHA:return p
 raise RuntimeError('ORIGINAL_LIONHEART_BLEND_NOT_FOUND_BY_VERIFIED_SHA')

def source_eval(repo,source,work):
 """Fresh half-frame Blender evaluation. Never save original BLEND."""
 sample=repo/'campaigns/OBSIDIANTI_SOURCE_SAMPLER_v1.1.0.py'
 raw=sample.read_text()
 if raw.count('current+=1')!=1:raise RuntimeError('HISTORIC_SAMPLER_HALF_FRAME_PATCH_NOT_UNIQUE')
 # Source is exact Git-owned sampler, transformed deterministically in isolated workdir.
 half=work/'SOURCE_SAMPLER_HALF_FRAMES_v1.3.0.py';half.write_text(raw.replace('current+=1','current+=0.5'))
 dst=work/'ORIGINAL_LIONHEART_EVALUATED_HALF_FRAMES.json'
 blender=shutil.which('blender')
 if blender:
  args=[blender,'--background','--python',half,'--','--source',source,'--out',dst,'--kind','lionheart']
 else:
  if not shutil.which('proot-distro'):raise RuntimeError('BLENDER_OR_EXISTING_PROOT_DEBIAN_REQUIRED')
  args=['proot-distro','login','debian','--bind',str(source.parent.resolve())+':/mnt/obs-input','--bind',str(work.resolve())+':/mnt/obs-output',
       '--','blender','--background','--python','/mnt/obs-output/'+half.name,'--','--source','/mnt/obs-input/'+source.name,'--out','/mnt/obs-output/'+dst.name,'--kind','lionheart']
 r=cmd(args,timeout=1500,check=False)
 (work/'BLENDER_EVALUATION.log').write_text(r.stdout+'\n'+r.stderr)
 if r.returncode:raise RuntimeError('SOURCE_BLENDER_EVALUATION_FAILED '+(r.stdout+'\n'+r.stderr)[-1800:])
 j=json.loads(dst.read_text())
 if j.get('sourceKind')!='lionheart' or len(j.get('actions',{}))<11:raise RuntimeError('EVALUATED_SOURCE_INCOMPLETE')
 if len(j['actions']['Heavy1']['frames'])<45:raise RuntimeError('HALF_FRAME_EVALUATION_NOT_EXECUTED')
 return dst,{'samplerSHA256':sha(half),'actualEvaluatedSourceSHA256':sha(dst),'actionCount':len(j['actions']),'blenderVersion':j.get('blenderVersion')}

def main(packet,launcher,launcher_sha):
 downloads=pathlib.Path.home()/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('ANDROID_DOWNLOADS_MISSING')
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 state=pathlib.Path.home()/'.local/state'/V/runid;state.mkdir(parents=True)
 receipt=state/'RECEIPT.json';rec={'campaign':V,'runid':runid,'authority':'TERMUX_GIT_ONLY',
 'status':'PREFLIGHT','launcherSHA256':launcher_sha,'originalBlenderSourceSHA256':LIONHEART_SHA,
 'historicalTargetSHA256':TARGET_SHA,'agentsBlob':AGENTS_BLOB,'liveCampaignEtiquetteRead':'2026-11-06 via connected Drive',
 'canonicalModelModified':False,'sourceBlendModified':False}
 def save():
  t=receipt.with_suffix('.tmp');t.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n');os.replace(t,receipt)
 save()
 try:
  manifest=json.loads((packet/'manifest.json').read_text())
  required={'analyze.py','driver.py','summarize.py','test.py','README.md','contract.json'}
  if set(manifest)!=required:raise RuntimeError('INVALID_PACKET_INVENTORY')
  for n,h in manifest.items():
   if sha(packet/n)!=h:raise RuntimeError('PACKET_MEMBER_INVALID '+n)
  contract=json.loads((packet/'contract.json').read_text())
  if contract.get('authority')!='ANDROID_TERMUX_GIT_ONLY' or contract.get('lockedPaths')!=list(LOCKED):
   raise RuntimeError('WRONG_MACHINE_READABLE_CONTRACT')
  if set(contract['mutablePaths'])!=set(SOURCES)|set(EVIDENCE):raise RuntimeError('MUTABLE_PATH_CONTRACT_MISMATCH')
  if sha(launcher)!=launcher_sha:raise RuntimeError('LAUNCHER_CHANGED_IN_FLIGHT')
  cmd([sys.executable,'-m','py_compile',*[packet/n for n in ('analyze.py','driver.py','summarize.py','test.py')]])
  cmd([sys.executable,packet/'analyze.py','--selftest'])
  test=cmd([sys.executable,packet/'test.py'])
  if 'HOST_FIXTURE_SUCCESS_AND_FAILURE_PATHS_PASS' not in test.stdout:
   raise RuntimeError('CONTRACT_TEST_MISSING_PASS_MARKER')
  if cmd(['git','lfs','version'],check=False).returncode:raise RuntimeError('GIT_LFS_NOT_FOUND')
  source=latest_donor();rec['actualOriginalSourcePath']=str(source);print('VERIFIED_LIONHEART_BLEND='+str(source),flush=True)
  env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1';env['GIT_TERMINAL_PROMPT']='0'
  repo=state/'checkout'
  cmd(['git','clone','--quiet','--depth=1','--branch','main','--single-branch','--',REMOTE,repo],timeout=600,env=env)
  print('RESOLVED_REPO='+str(repo.resolve()),flush=True)
  print('EXECUTION_DIR='+str(repo.resolve()),flush=True)
  print('BRANCH='+git(repo,'branch','--show-current').stdout.strip(),flush=True)
  print('HEAD='+git(repo,'rev-parse','HEAD').stdout.strip(),flush=True)
  origin=git(repo,'remote','get-url','origin').stdout.strip()
  if origin.removesuffix('.git')!=REMOTE.removesuffix('.git'):raise RuntimeError('INVALID_REPOSITORY_REMOTE '+origin)
  head=git(repo,'rev-parse','HEAD').stdout.strip();rec['sourceMainHead']=head
  if git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()!=AGENTS_BLOB:raise RuntimeError('RULES_READ_BLOCKED_AGENTS_CHANGED')
  if git(repo,'status','--porcelain').stdout.strip():raise RuntimeError('ISOLATED_REPO_DIRTY')
  locked={x:git(repo,'rev-parse','HEAD:'+x).stdout.strip() for x in LOCKED}
  expected_canonical_sha=CANONICAL_SHA
  lfs_pointer=git(repo,'show','HEAD:assets/obsidianti/Obsidianti.glb').stdout
  if ('oid sha256:'+expected_canonical_sha+'\n') not in lfs_pointer:
   raise RuntimeError('CANONICAL_OBSIDIANTI_LFS_SHA_CHANGED')
  rec['canonicalModelLfsSHA256']=expected_canonical_sha
  rec['canonicalGitTreeBlobsBefore']=locked
  # Ensure this source revision is a descendant of the pinned research (or exactly it).
  if head!=BASE_HEAD:
   cmd(['git','-C',repo,'fetch','--depth=80','origin',BASE_HEAD],timeout=300)
   if git(repo,'merge-base','--is-ancestor',BASE_HEAD,head,check=False).returncode:
    raise RuntimeError('HISTORICAL_RESEARCH_NOT_IN_MAIN_ANCESTRY')
  mappings={dst:launcher if src=='LAUNCHER' else packet/src for dst,src in SOURCES.items()}
  # Idempotent reentry allowed only when ALL committed source paths byte-match.
  existing=[x for x in mappings if (repo/x).exists()]
  if existing and (len(existing)!=len(mappings) or any(sha(repo/x)!=sha(mappings[x]) for x in existing)):
   raise RuntimeError('VERSIONED_SOURCE_PATH_COLLISION '+repr(existing))
  result_paths=[x for x in EVIDENCE if (repo/x).exists()]
  if result_paths:
   if len(result_paths)==len(EVIDENCE):
    rec['status']='ALREADY_RESEARCH_COMMITTED_REMOTE';rec['remoteRevision']=head;save()
    print('RESEARCH_ALREADY_PUBLISHED_AT='+head,flush=True);print('STATUS='+rec['status'],flush=True);return
   raise RuntimeError('PARTIAL_EVIDENCE_COLLISION '+repr(result_paths))
  if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Campaign')
  if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')
  if not existing:
   for target,src in mappings.items():atomic_copy(src,repo/target)
   git(repo,'add','--',*sorted(mappings))
   staged=git(repo,'diff','--cached','--name-only').stdout.splitlines()
   if set(staged)!=set(mappings):raise RuntimeError('SOURCE_STAGING_MISMATCH '+repr(staged))
   git(repo,'commit','-m','Obsidianti: commit complete bilateral causal FK diagnostics before runtime')
   newhead=git(repo,'rev-parse','HEAD').stdout.strip()
   remote=safe_push(repo,newhead,'SOURCE')
   rec['sourceCommit']=newhead
  else:rec['sourceCommit']=head
  rec['status']='SOURCE_COMMITTED_REMOTE_VERIFIED';save()
  print('SOURCE_COMMIT='+rec['sourceCommit'],flush=True)
  work=state/'work';work.mkdir()
  # Exact v1.2.0 historical extraction code was already implemented and field-tested.
  spec=importlib.util.spec_from_file_location('previous_archive_recovery',str(repo/'campaigns/OBSIDIANTI_BILATERAL_RETARGET_RESEARCH_v1.2.0_driver.py'))
  prev=importlib.util.module_from_spec(spec);spec.loader.exec_module(prev)
  baseline=prev.extract_baseline(repo,work)
  if sha(baseline)!=TARGET_SHA:raise RuntimeError('HISTORICAL_BASELINE_HASH_CHANGED')
  donor,source_evidence=source_eval(repo,source,work)
  rec['sourceEval']=source_evidence;save()
  analysis=work/'CAUSAL_AUDIT.json'
  r=cmd([sys.executable,packet/'analyze.py','--model',baseline,'--donor',donor,'--blend-sha',LIONHEART_SHA,
         '--expected-model-sha',TARGET_SHA,'--expected-donor-samples-sha',sha(donor),
         '--evaluator',repo/'campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py',
         '--importer',repo/'campaigns/OBSIDIANTI_GLTF_LIBRARY_v1.1.0.py',
         '--output',analysis],timeout=2400)
  (work/'ANALYSIS.log').write_text(r.stdout+'\n'+r.stderr)
  print(r.stdout.strip(),flush=True)
  data=json.loads(analysis.read_text())
  if len(data['clips'])!=10 or not data['invariants']:raise RuntimeError('CAUSAL_ANALYSIS_INCOMPLETE')
  # Independently inspect the REAL current canonical model, without mutating it.
  modelpath=repo/'assets/obsidianti/Obsidianti.glb'
  for attempt in range(3):
   fetched=git(repo,'lfs','fetch','origin','HEAD','--include=assets/obsidianti/Obsidianti.glb','--exclude=',timeout=750,check=False)
   if fetched.returncode==0:break
   if attempt==2:raise RuntimeError('CANONICAL_GLB_LFS_FETCH_FAILED '+fetched.stderr[-1300:])
   time.sleep(2*(attempt+1))
  git(repo,'lfs','checkout','--','assets/obsidianti/Obsidianti.glb',timeout=240)
  if sha(modelpath)!=CANONICAL_SHA:raise RuntimeError('CANONICAL_GLB_BINARY_HASH_MISMATCH '+sha(modelpath))
  canonical_audit=work/'CAUSAL_AUDIT_CANONICAL.json'
  c=cmd([sys.executable,packet/'analyze.py','--target-role','canonical','--model',modelpath,'--donor',donor,'--blend-sha',LIONHEART_SHA,
         '--expected-model-sha',CANONICAL_SHA,'--expected-donor-samples-sha',sha(donor),
         '--evaluator',repo/'campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py',
         '--importer',repo/'campaigns/OBSIDIANTI_GLTF_LIBRARY_v1.1.0.py',
         '--output',canonical_audit],timeout=2400)
  (work/'ANALYSIS_CANONICAL.log').write_text(c.stdout+'\n'+c.stderr)
  print('CANONICAL_READ_ONLY_AUDIT='+str(canonical_audit),flush=True)
  canonical_data=json.loads(canonical_audit.read_text())
  if canonical_data.get('targetRole')!='canonical' or len(canonical_data.get('clips',{}))!=10:
   raise RuntimeError('CANONICAL_CAUSAL_ANALYSIS_INCOMPLETE')
  report=work/'CAUSE_REPORT.md'
  cmd([sys.executable,packet/'summarize.py',analysis,report,canonical_audit])
  e={'schema':'obsidianti-v1.3.0-evidence-receipt','sourceGitRevision':rec['sourceCommit'],
     'originalLionheartSHA256':LIONHEART_SHA,'historicalGLBSHA256':TARGET_SHA,
     'sourceEvaluatedSHA256':sha(donor),'analysisJSONSHA256':sha(analysis),'canonicalAnalysisJSONSHA256':sha(canonical_audit),
     'summaryMarkdownSHA256':sha(report),'agentsBlobSHA':AGENTS_BLOB,
     'authorLiveCampaignEtiquette':'2026-11-06','canonGitTreeBlobs':locked,
     'sourceSampler':source_evidence,'canonicalModified':False,
     'status':'NO_MODEL_REPAIR_PROVEN_DIAGNOSIS_ONLY'}
  (work/'EVIDENCE_RECEIPT.json').write_text(json.dumps(e,indent=2)+'\n')
  for path,rel in EVIDENCE.items():atomic_copy(work/rel,repo/path)
  git(repo,'add','--',*sorted(EVIDENCE))
  staged=git(repo,'diff','--cached','--name-only').stdout.splitlines()
  if set(staged)!=set(EVIDENCE):raise RuntimeError('EVIDENCE_STAGING_MISMATCH '+repr(staged))
  for x in LOCKED:
   if git(repo,'rev-parse','HEAD:'+x).stdout.strip()!=locked[x]:raise RuntimeError('CANONICAL_TREE_CHANGED '+x)
  git(repo,'commit','-m','Obsidianti: publish bilateral retarget causal decomposition and physical witness measurements')
  final_head=git(repo,'rev-parse','HEAD').stdout.strip()
  final_remote=safe_push(repo,final_head,'EVIDENCE')
  git(repo,'fetch','--quiet','origin','main',timeout=180)
  for path in EVIDENCE:
   if git(repo,'show','HEAD:'+path).stdout!=(repo/path).read_text():raise RuntimeError('EVIDENCE_GIT_READBACK_MISMATCH '+path)
  for x in LOCKED:
   if git(repo,'rev-parse','HEAD:'+x).stdout.strip()!=locked[x]:raise RuntimeError('PROTECTED_MODEL_CHANGED '+x)
  rec.update({'status':'RESEARCH_COMMITTED_REMOTE_VERIFIED','remoteCommit':final_head,'sourceEvaluatedSHA256':sha(donor),
     'metricsSHA256':sha(analysis),'canonicalMetricsSHA256':sha(canonical_audit),'reportSHA256':sha(report),'canonicalModelModified':False})
  for x in ('CAUSAL_AUDIT.json','CAUSAL_AUDIT_CANONICAL.json','CAUSE_REPORT.md','EVIDENCE_RECEIPT.json'):
   mirror=downloads/(V+'_'+runid+'_'+x)
   atomic_copy(work/x,mirror)
   print('DOWNLOAD_EVIDENCE='+str(mirror),flush=True)
  save()
  print('REPORT_GIT_URL=https://github.com/Valar05/parametric-parambulator/blob/'+final_head+'/'+DIR+'/CAUSE_REPORT.md',flush=True)
  print('RESEARCH_COMMIT='+final_head,flush=True)
  print('STATUS='+rec['status'],flush=True)
 except Exception as ex:
  rec['status']='BLOCKED';rec['error']=str(ex);rec['traceback']=traceback.format_exc()[-7000:]
  save();print('STATUS=BLOCKED '+str(ex),flush=True)
  raise
 finally:
  save();print('RECEIPT='+str(receipt),flush=True)
if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('USAGE: driver.py PACKET_DIR LAUNCHER_PATH LAUNCHER_SHA')
 main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve(),sys.argv[3])
