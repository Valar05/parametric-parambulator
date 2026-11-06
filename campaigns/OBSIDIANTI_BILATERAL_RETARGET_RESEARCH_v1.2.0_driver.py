#!/usr/bin/env python3
"""One invocation forensic-only Termux Git campaign. Strict no model mutation."""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,traceback,uuid,zipfile
V='OBSIDIANTI_BILATERAL_RETARGET_RESEARCH_v1.2.0'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
BLEND_SHA='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
BASE_ARCHIVE='diagnostics/obsidianti/ares-fk-rebase-v1.0.1/UNAPPROVED_CANDIDATE.zip'
BASE_MEMBER='AresScaled_PreContactFK_UNAPPROVED.glb'
BASE_ARCHIVE_SHA='4a039eb3d73ae1d3430c7eb9c90c55aba5d4c00fda7a86e6704c8eaab2c45b10'
BASE_GLB_SHA='955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32'
TARGET='diagnostics/obsidianti/bilateral-retarget-research-v1.2.0'
CAMPAIGN='campaigns/'+V+'_LAUNCH.sh'
SOURCE={('campaigns/'+V+'_'+name+'.py'):name+'.py' for name in ('driver','archaeology','analyze','summarize')}
EVIDENCE={TARGET+'/'+f:f for f in ('ARCHAEOLOGY_INDEX.json','MOTION_METRICS.json','RESEARCH_REPORT.md','EVIDENCE_RECEIPT.json')}
LOCKED=['assets/obsidianti/Obsidianti.glb','assets/repl/Repl.glb']
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def run(args,timeout=240,env=None,check=True):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=timeout,env=env)
 if p.returncode and check:raise RuntimeError('COMMAND_FAILED '+repr(list(map(str,args))[:6])+'\n'+p.stderr[-1000:]+'\n'+p.stdout[-500:])
 return p
def git(repo,*args,**kw):return run(['git','-C',repo,*args],**kw)
def validate_packet(packet):
 manifest=json.loads((packet/'manifest.json').read_text())
 required={'driver.py','archaeology.py','analyze.py','summarize.py'}
 if set(manifest)!=required:raise RuntimeError('PACKET_INVENTORY_FAILED')
 for name,expected in manifest.items():
  if sha(packet/name)!=expected:raise RuntimeError('PACKET_SHA_INVALID '+name)
 return hashlib.sha256((packet/'manifest.json').read_bytes()).hexdigest()
def donor_blend():
 roots=[pathlib.Path.home()/'storage/downloads',pathlib.Path('/storage/emulated/0/Download'),pathlib.Path.home()/'storage/documents']
 seen=set()
 for root in roots:
  if not root.is_dir():continue
  for pattern in ('LionheartLancer*.blend','Lionheart*.blend'):
   for candidate in root.glob(pattern):
    if str(candidate) in seen:continue
    seen.add(str(candidate))
    if candidate.is_file() and sha(candidate)==BLEND_SHA:return candidate
 raise RuntimeError('VERIFIED_LIONHEART_ORIGINAL_NOT_IN_ANDROID_DOWNLOADS_OR_DOCUMENTS')
def extract_baseline(repo,work):
 p=repo/BASE_ARCHIVE
 if not p.is_file():raise RuntimeError('HISTORICAL_PRECONTACT_REVIEW_ARCHIVE_ABSENT')
 git(repo,'lfs','fetch','origin','HEAD','--include='+BASE_ARCHIVE,'--exclude=',timeout=600)
 git(repo,'lfs','checkout','--',BASE_ARCHIVE,timeout=180)
 if sha(p)!=BASE_ARCHIVE_SHA:raise RuntimeError('PRECONTACT_ARCHIVE_SHA_MISMATCH')
 out=work/'HISTORICAL_PRECONTACT_ARES_SCALED_UNAPPROVED.glb'
 with zipfile.ZipFile(p) as z:
  if BASE_MEMBER not in z.namelist():raise RuntimeError('EXPECTED_HISTORICAL_GLB_MISSING')
  if any(x.startswith('/') or '..' in pathlib.PurePosixPath(x).parts for x in z.namelist()):raise RuntimeError('HISTORICAL_ARCHIVE_UNSAFE')
  with z.open(BASE_MEMBER) as f,open(out,'wb') as g:shutil.copyfileobj(f,g)
 if sha(out)!=BASE_GLB_SHA:raise RuntimeError('PRECONTACT_MODEL_SHA_MISMATCH')
 return out
def blender_sample(repo,source,dest,work):
 sampler=repo/'campaigns/OBSIDIANTI_SOURCE_SAMPLER_v1.1.0.py'
 if not sampler.is_file():raise RuntimeError('HISTORICAL_SOURCE_SAMPLER_MISSING')
 native=shutil.which('blender')
 if native:
  args=[native,'--background','--python',sampler,'--','--source',source,'--out',dest,'--kind','lionheart']
 else:
  if not shutil.which('proot-distro'):raise RuntimeError('BLENDER_NATIVE_OR_EXISTING_PROOT_RUNTIME_REQUIRED')
  args=['proot-distro','login','debian','--bind',str(repo.resolve())+':/mnt/obs-repo','--bind',str(source.parent.resolve())+':/mnt/obs-input','--bind',str(work.resolve())+':/mnt/obs-output','--','blender','--background','--python','/mnt/obs-repo/campaigns/OBSIDIANTI_SOURCE_SAMPLER_v1.1.0.py','--','--source','/mnt/obs-input/'+source.name,'--out','/mnt/obs-output/'+dest.name,'--kind','lionheart']
 result=run(args,timeout=1200,check=False)
 (work/'BLENDER_EVALUATION.log').write_text(result.stdout+'\n'+result.stderr)
 if result.returncode:raise RuntimeError('BLENDER_SOURCE_EVALUATION_FAILED '+(result.stdout+'\n'+result.stderr)[-1400:])
 if not dest.is_file():raise RuntimeError('BLENDER_DID_NOT_WRITE_EVALUATED_SOURCE')
 data=json.loads(dest.read_text())
 if len(data.get('actions',{}))<11:raise RuntimeError('BLENDER_ACTIONS_INCOMPLETE '+str(list(data.get('actions',{}))))
 return {'sampleSHA256':sha(dest),'sourceBlenderVersion':data['blenderVersion'],'actionCount':len(data['actions'])}
def identity(repo):
 if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Campaign')
 if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')
def atomic_copy(src,dst):
 src=pathlib.Path(src);dst=pathlib.Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():raise RuntimeError('DESTINATION_COLLISION '+str(dst))
 tmp=dst.with_name('.'+dst.name+'.'+uuid.uuid4().hex+'.tmp')
 try:
  shutil.copyfile(src,tmp)
  if sha(src)!=sha(tmp):raise RuntimeError('COPY_HASH_MISMATCH '+str(dst))
  os.replace(tmp,dst)
 finally:
  if tmp.exists():tmp.unlink()
def main(packet,launcher,launcher_hash):
 downloads=pathlib.Path.home()/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('ANDROID_SHARED_DOWNLOADS_NOT_ACCESSIBLE')
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
 receipt=root/'RECEIPT.json'
 record={'campaign':V,'authority':'TERMUX_GIT_ONLY','runId':runid,'launcherSHA256':launcher_hash,'status':'STARTED','canonicalModelsModified':False,'sourceBlendModified':False,'authorRules':{'agentsBlobSHA':AGENTS_BLOB,'campaignEtiquetteReadAtAuthoring':'2026-11-06 HomeCenter live'},'reportStatus':'NOT_YET_COMMITTED'}
 def save():
  tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');os.replace(tmp,receipt)
 save()
 try:
  record['packetManifestSHA256']=validate_packet(packet)
  if run(['git','lfs','version'],check=False).returncode:raise RuntimeError('GIT_LFS_REQUIRED')
  source=donor_blend();record['lionheartSourceSHA256']=sha(source);record['lionheartSourcePath']=str(source)
  print('VERIFIED_LIONHEART_SOURCE='+str(source),flush=True)
  env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1';env['GIT_TERMINAL_PROMPT']='0'
  repo=root/'checkout';run(['git','clone','--quiet','--depth=1','--branch','main','--single-branch','--',REMOTE,repo],timeout=420,env=env)
  origin=git(repo,'remote','get-url','origin').stdout.strip()
  if origin.removesuffix('.git')!=REMOTE.removesuffix('.git'):raise RuntimeError('WRONG_REMOTE '+origin)
  head=git(repo,'rev-parse','HEAD').stdout.strip();record['sourceHead']=head
  agents=git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()
  if agents!=AGENTS_BLOB:raise RuntimeError('AGENTS_BLOB_CHANGED '+agents)
  record['agentsBlobSHA256Verified']=agents
  if git(repo,'status','--porcelain').stdout.strip():raise RuntimeError('ISOLATED_CHECKOUT_DIRTY')
  record['protectedTreesBefore']={p:git(repo,'rev-parse','HEAD:'+p).stdout.strip() for p in LOCKED}
  # Source-first publication: the one authorized Termux Git lane commits and
  # remotely verifies the executable evidence machinery BEFORE running research.
  source_mappings={CAMPAIGN:pathlib.Path(launcher),**{name:packet/src for name,src in SOURCE.items()}}
  evidence_mappings={path:root/'work'/src for path,src in EVIDENCE.items()}
  allpaths=set(source_mappings)|set(evidence_mappings)
  collisions=[name for name in allpaths if (repo/name).exists()]
  if collisions:raise RuntimeError('VERSIONED_GIT_PATH_COLLISION '+repr(collisions))
  identity(repo)
  for target,src in source_mappings.items():atomic_copy(src,repo/target)
  git(repo,'add','--',*sorted(source_mappings))
  staged=git(repo,'diff','--cached','--name-only').stdout.splitlines()
  if set(staged)!=set(source_mappings):raise RuntimeError('UNEXPECTED_SOURCE_STAGED_PATHS '+repr(staged))
  git(repo,'commit','-m','Obsidianti: source-first bilateral retarget archaeology and measurement campaign',timeout=180)
  sourcecommit=git(repo,'rev-parse','HEAD').stdout.strip()
  git(repo,'push','origin','HEAD:refs/heads/main',timeout=360)
  sourcereadback=git(repo,'ls-remote','origin','refs/heads/main',timeout=90).stdout.split()[0]
  if sourcecommit!=sourcereadback:raise RuntimeError('SOURCE_COMMIT_REMOTE_READBACK_MISMATCH')
  record.update({'sourceCampaignCommit':sourcecommit,'sourceCampaignRemoteReadback':sourcereadback,'status':'SOURCE_COMMITTED_REMOTE_VERIFIED__RESEARCH_PENDING'})
  print('SOURCE_CAMPAIGN_REMOTE_COMMIT='+sourcecommit,flush=True)
  save()
  work=root/'work';work.mkdir()
  archive=extract_baseline(repo,work);record['historicalGlbSHA256']=sha(archive)
  archa=run([sys.executable,str(packet/'archaeology.py'),repo,work],timeout=180)
  print(archa.stdout.strip(),flush=True)
  donor=work/'LIONHEART_EVALUATED_SOURCE.json';record['sourceSamples']=blender_sample(repo,source,donor,work)
  print('SOURCE_EVALUATION_SHA256='+record['sourceSamples']['sampleSHA256'],flush=True)
  measurements=work/'MOTION_METRICS.json'
  evaluation=run([sys.executable,str(packet/'analyze.py'),'--evaluator',repo/'campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py','--model',archive,'--donor',donor,'--blend-sha',BLEND_SHA,'--output',measurements],timeout=900)
  (work/'ANALYSIS.log').write_text(evaluation.stdout+'\n'+evaluation.stderr)
  print(evaluation.stdout.strip(),flush=True)
  metrics=json.loads(measurements.read_text())
  if len(metrics.get('clips',{}))!=10 or not all(set(('left','right')).issubset(item) for item in metrics['clips'].values()):raise RuntimeError('BILATERAL_RESEARCH_INCOMPLETE')
  if metrics['historicalTargetGLBSHA256']!=BASE_GLB_SHA:raise RuntimeError('HISTORICAL_RESEARCH_WRONG_MODEL')
  report=work/'RESEARCH_REPORT.md';run([sys.executable,str(packet/'summarize.py'),measurements,work/'ARCHAEOLOGY_INDEX.json',report],timeout=90)
  evidence={'schema':'obsidianti-bilateral-research-commit-evidence-v1.2.0','authority':'Termux Git only','sourceHead':head,'sourceBlenderSHA256':BLEND_SHA,'historicalTargetGLBSHA256':BASE_GLB_SHA,'sourceSampleSHA256':sha(donor),'analysisMetricsSHA256':sha(measurements),'researchMarkdownSHA256':sha(report),'archaeologyIndexSHA256':sha(work/'ARCHAEOLOGY_INDEX.json'),'rulesRead':record['authorRules'],'execution':'ACTUAL_SOURCE_EVALUATED_HISTORICAL_GLB_EVALUATED','immutableCanonicalAssets':record['protectedTreesBefore'],'ownerVisualVerdict':'NOT_APPLICABLE_NO_MODEL_MUTATION','interpretation':'Measured left-right bone movement discrepancy and provenance. No repair proposed as executed.'}
  (work/'EVIDENCE_RECEIPT.json').write_text(json.dumps(evidence,indent=2)+'\n')
  record['evidenceSHA256']={k:sha(v) for k,v in evidence_mappings.items() if pathlib.Path(v).is_file()}
  for target,src in evidence_mappings.items():atomic_copy(src,repo/target)
  git(repo,'add','--',*sorted(evidence_mappings))
  staged=git(repo,'diff','--cached','--name-only').stdout.splitlines()
  if set(staged)!=set(evidence_mappings):raise RuntimeError('UNEXPECTED_EVIDENCE_STAGED_PATHS '+repr(staged))
  for path in LOCKED:
   if git(repo,'rev-parse','HEAD:'+path).stdout.strip()!=record['protectedTreesBefore'][path]:raise RuntimeError('CANONICAL_ASSET_CHANGED '+path)
  git(repo,'commit','-m','Obsidianti: archive prior retarget evidence and measure bilateral FK trajectory deviations',timeout=180)
  newhead=git(repo,'rev-parse','HEAD').stdout.strip()
  git(repo,'push','origin','HEAD:refs/heads/main',timeout=360)
  readback=git(repo,'ls-remote','origin','refs/heads/main',timeout=90).stdout.split()[0]
  if newhead!=readback:raise RuntimeError('REMOTE_MAIN_READBACK_MISMATCH '+newhead+' '+readback)
  git(repo,'fetch','--quiet','origin','main',timeout=150)
  if git(repo,'rev-parse','refs/remotes/origin/main').stdout.strip()!=newhead:raise RuntimeError('REMOTE_FETCH_SHA_MISMATCH')
  for path in EVIDENCE:
   if git(repo,'show','HEAD:'+path).stdout!=(repo/path).read_text():raise RuntimeError('COMMITTED_REPORT_READBACK_MISMATCH '+path)
  for path in LOCKED:
   if git(repo,'rev-parse','HEAD:'+path).stdout.strip()!=record['protectedTreesBefore'][path]:raise RuntimeError('CANONICAL_ASSET_TREE_CHANGED '+path)
  record.update({'status':'RESEARCH_COMMITTED_REMOTE_VERIFIED','reportStatus':'COMMITTED_REMOTE_READBACK_VERIFIED','commit':newhead,'remoteReadbackSHA':readback,'publishedPaths':sorted(allpaths),'metricsSummary':metrics['overall'],'canonicalModelsModified':False})
  # Download mirrors are copies of actual Termux-generated reports; Git commit is authority.
  for artifact in ('RESEARCH_REPORT.md','MOTION_METRICS.json','ARCHAEOLOGY_INDEX.json'):
   mirrored=downloads/(V+'_'+runid+'_'+artifact)
   atomic_copy(work/artifact,mirrored)
   print('DOWNLOAD_EVIDENCE='+str(mirrored),flush=True)
  save()
  print('REPORT_GIT_URL=https://github.com/Valar05/parametric-parambulator/blob/'+newhead+'/'+TARGET+'/RESEARCH_REPORT.md',flush=True)
  print('RESEARCH_COMMIT='+newhead,flush=True)
  print('STATUS='+record['status'],flush=True)
 except Exception as ex:
  record.update({'status':'BLOCKED','error':str(ex),'traceback':traceback.format_exc()[-4000:]});save();print('STATUS=BLOCKED '+str(ex),flush=True)
  raise
 finally:
  save();print('RECEIPT='+str(receipt),flush=True)
if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('USAGE: driver.py PACKET_ROOT LAUNCHER_PATH LAUNCHER_SHA')
 main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve(),sys.argv[3])
