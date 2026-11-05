#!/usr/bin/env python3
"""Termux-only, Git-authoritative, read-only character motion measurement campaign."""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time,uuid,zipfile,traceback
V='OBSIDIANTI_MOTION_MEASUREMENT_v1.0.0'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
SOURCES={'assets/obsidianti/Obsidianti.glb':'8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4',
 'assets/obsidianti/source/LionheartLancer.blend':'81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'}
V156_ZIP_SHA='fc3ca580b82de074f6a2f040e8335baf1351b74a102df389bbaa5dfc85a68c3a'
V156_GLB_SHA='261f10786dd0eb0e80667173e4a893f6822356da628a5907efd6d0bbc2a74ff5'
FILES={'campaigns/OBSIDIANTI_MOTION_MEASURE_RUN_v1.0.0.py':'driver.py',
 'campaigns/OBSIDIANTI_MOTION_MEASURE_BLENDER_v1.0.0.py':'blender_measure.py',
 'campaigns/OBSIDIANTI_MOTION_MEASURE_ANALYZE_v1.0.0.py':'analyze.py',
 'docs/obsidianti/MOTION_MEASUREMENT_v1.0.0.md':'doc.md'}
DEST='diagnostics/obsidianti/motion-measurement-v1.0.0'
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def cmd(argv,timeout=300,check=True,env=None):
 p=subprocess.run([str(x) for x in argv],text=True,capture_output=True,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+repr([str(x) for x in argv][:5])+' '+p.stderr[-1200:]+' '+p.stdout[-600:])
 return p
def git(repo,*args,**kw):return cmd(['git','-C',str(repo),*args],**kw)
def blender_command(repo,work,script,args):
 b=shutil.which('blender')
 if b:return [b,'--background','--disable-autoexec','--python',str(repo/script),'--',*map(str,args)]
 proot=shutil.which('proot-distro')
 if not proot:raise RuntimeError('BLENDER_UNAVAILABLE_NATIVE_AND_PROOT_DEBIAN')
 rr=repo.resolve();ww=work.resolve()
 def map_path(x):
  z=str(pathlib.Path(x).resolve())
  if z.startswith(str(rr)+'/'):return '/mnt/obs-repo/'+z[len(str(rr))+1:]
  if z.startswith(str(ww)+'/'):return '/mnt/obs-work/'+z[len(str(ww))+1:]
  raise RuntimeError('UNMAPPED_BLENDER_PATH '+z)
 return [proot,'login','debian','--bind',str(rr)+':/mnt/obs-repo','--bind',str(ww)+':/mnt/obs-work','--','blender','--background','--disable-autoexec','--python',map_path(repo/script),'--',*[map_path(a) for a in args]]
def discover_v156(downloads,work):
 candidates=[]
 for p in downloads.glob('OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.6*_HANDOFF.zip'):
  if sha(p)==V156_ZIP_SHA:candidates.append(p)
 if len(candidates)!=1:raise RuntimeError('EXACT_V156_HANDOFF_MISSING_OR_AMBIGUOUS matched='+str(len(candidates)))
 with zipfile.ZipFile(candidates[0]) as z:
  b=z.read('visual/Candidate_UNAPPROVED.glb')
 if hashlib.sha256(b).hexdigest()!=V156_GLB_SHA:raise RuntimeError('V156_GLB_BYTES_MISMATCH')
 path=work/'Obsidianti_v156_verified.glb';path.write_bytes(b)
 return path,candidates[0]
def main(packet,launcher_sha):
 home=pathlib.Path.home();downloads=home/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('TERMUX_DOWNLOADS_NOT_CONFIGURED')
 run=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:7]
 root=home/'.local/state'/V/run;root.mkdir(parents=True,exist_ok=False)
 work=root/'work';work.mkdir();repo=root/'repo';logs=work/'logs';logs.mkdir()
 receipt=downloads/(V+'_'+run+'_RECEIPT.json');handoff=downloads/(V+'_'+run+'_HANDOFF.zip')
 state={'campaign':V,'run':run,'status':'STARTED','stage':'BOOT','authority':'TERMUX_GIT_ONLY',
  'launcherSHA256':launcher_sha,'rulesRead':{'agentsGithubBlobSHA':AGENTS_BLOB,'campaignEtiquetteReadByAuthor':'2026-11-05 Home Center'},
  'canonicalGLBMutation':False,'nativeBlendMutation':False,'visualAcceptance':'NOT_REQUESTED_READ_ONLY_MEASUREMENT'}
 def save():receipt.write_text(json.dumps(state,indent=2,sort_keys=True)+'\n')
 save();print('AUTHORITY=TERMUX_GIT_ONLY MODEL_MUTATION=FORBIDDEN LIONHEART_IS_MEASUREMENT_REFERENCE_ONLY',flush=True)
 try:
  state['stage']='VERIFY_V156';save();target,handoff_base=discover_v156(downloads,work)
  state['v156GLBSHA256']=sha(target);state['v156HandoffSHA256']=sha(handoff_base)
  print('V156_EXACT_SHA_VERIFIED=YES',flush=True)
  state['stage']='ISOLATED_SOURCE_CHECKOUT';save()
  env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
  # Never operate inside user's working directory or mutate his checkout.
  cmd(['git','clone','--depth=25','--single-branch','--branch','main','--config','filter.lfs.smudge=','--config','filter.lfs.required=false',REMOTE,repo],timeout=900,env=env)
  initial=git(repo,'rev-parse','HEAD').stdout.strip();state['originalGitHEAD']=initial
  if git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()!=AGENTS_BLOB:raise RuntimeError('LIVE_AGENTS_CHANGED_AFTER_AUTHOR_READ')
  if 'Campaign Etiquette' not in (repo/'AGENTS.md').read_text():raise RuntimeError('MANDATORY_RULES_MARKER_MISSING')
  if cmd(['git','lfs','version'],check=False).returncode:raise RuntimeError('GIT_LFS_MISSING')
  state['stage']='VERIFY_NATIVE_SOURCE_AND_CANONICAL';save()
  print('GIT_HEAD='+initial+' FETCHING_VERIFIED_LFS_ASSETS',flush=True)
  cmd(['git','-C',repo,'lfs','pull','--include='+','.join(SOURCES),'--exclude='],timeout=1500,env=dict(env,GIT_LFS_SKIP_SMUDGE='0'))
  for p,expect in SOURCES.items():
   if not (repo/p).is_file() or sha(repo/p)!=expect:raise RuntimeError('SOURCE_HASH_MISMATCH '+p+' observed='+sha(repo/p) if (repo/p).exists() else 'SOURCE_NOT_PRESENT')
  state['inputSHA256']=dict(SOURCES);save()
  for path in [*FILES,DEST+'/MEASUREMENT_REPORT.md',DEST+'/MEASUREMENT_SUMMARY.json',DEST+'/MEASUREMENT_RAW.zip']:
   if (repo/path).exists() or git(repo,'ls-tree','HEAD','--',path).stdout.strip():raise RuntimeError('VERSIONED_PATH_COLLISION '+path)
  state['stage']='PUBLISH_MEASUREMENT_SOURCE';save()
  for dst,src in FILES.items():
   p=repo/dst;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(packet/src,p)
  git(repo,'add','--',*FILES)
  if set(git(repo,'diff','--cached','--name-only').stdout.splitlines())!=set(FILES):raise RuntimeError('STAGED_SOURCE_SCOPE_INVALID')
  if not git(repo,'config','--get','user.name',check=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Campaign')
  if not git(repo,'config','--get','user.email',check=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')
  git(repo,'commit','-m','Obsidianti: read-only native motion measurement campaign v1.0.0')
  sourcecommit=git(repo,'rev-parse','HEAD').stdout.strip();state['sourceCommit']=sourcecommit;save()
  cmd(['git','-C',repo,'push','origin','HEAD:refs/heads/main'],timeout=450,env=env)
  if git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]!=sourcecommit:raise RuntimeError('SOURCE_GIT_REMOTE_READBACK_FAILED')
  state['sourceReadbackVerified']=True
  state['stage']='MEASURE_SOURCE_NATIVE_BLEND';save()
  for kind,source in [('lionheart',repo/'assets/obsidianti/source/LionheartLancer.blend'),('obsidianti',target)]:
   print('MEASURING='+kind,flush=True)
   dest=work/kind;dest.mkdir()
   call=blender_command(repo,work,'campaigns/OBSIDIANTI_MOTION_MEASURE_BLENDER_v1.0.0.py',[source,kind,dest])
   p=cmd(call,timeout=3600,check=False)
   (logs/(kind+'.log')).write_text(p.stdout+'\n'+p.stderr)
   for line in p.stdout.splitlines():
    if line.startswith(('MEASURED=','MEASUREMENT_COMPLETE=')):print(line,flush=True)
   if p.returncode or not (dest/'metadata.json').is_file() or not (dest/'trajectories.csv').is_file():
    raise RuntimeError('BLENDER_MEASUREMENT_FAILED '+kind+' exit='+str(p.returncode)+' '+p.stderr[-1600:])
  state['stage']='ANALYZE_AND_REPORT';save()
  p=cmd(['python3',repo/'campaigns/OBSIDIANTI_MOTION_MEASURE_ANALYZE_v1.0.0.py',work,work/'results'],timeout=300)
  print(p.stdout.strip(),flush=True)
  report=work/'results/REPORT.md';summary=work/'results/summary.json'
  if not report.is_file() or not summary.is_file():raise RuntimeError('RESULTS_MISSING')
  raw=work/'raw.zip'
  with zipfile.ZipFile(raw,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for kind in ('lionheart','obsidianti'):
    for n in ('metadata.json','trajectories.csv'):z.write(work/kind/n,kind+'/'+n)
   z.write(summary,'summary.json');z.write(report,'REPORT.md')
  # Check measured models have not changed, and do not treat generated local zip as publication.
  for path,expected in SOURCES.items():
   if sha(repo/path)!=expected:raise RuntimeError('READ_ONLY_SOURCE_MUTATION_DETECTED '+path)
  if sha(target)!=V156_GLB_SHA:raise RuntimeError('V156_GLB_CHANGED_DURING_MEASUREMENT')
  state['resultSHA256']={'summary':sha(summary),'report':sha(report),'raw':sha(raw)};save()
  state['stage']='PUBLISH_INSPECTABLE_GIT_EVIDENCE';save()
  results={DEST+'/MEASUREMENT_REPORT.md':report,DEST+'/MEASUREMENT_SUMMARY.json':summary,DEST+'/MEASUREMENT_RAW.zip':raw}
  for dst,src in results.items():
   p=repo/dst;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
  git(repo,'add','--',*results)
  if set(git(repo,'diff','--cached','--name-only').stdout.splitlines())!=set(results):raise RuntimeError('STAGED_DIAGNOSTICS_SCOPE_INVALID')
  git(repo,'commit','-m','Obsidianti: native source-to-target half-frame motion measurements v1.0.0')
  final=git(repo,'rev-parse','HEAD').stdout.strip()
  pointer=git(repo,'show','HEAD:'+DEST+'/MEASUREMENT_RAW.zip').stdout
  if 'oid sha256:'+sha(raw) not in pointer:raise RuntimeError('RAW_LFS_POINTER_MISMATCH')
  cmd(['git','-C',repo,'push','origin','HEAD:refs/heads/main'],timeout=900,env=env)
  remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]
  if remote!=final:raise RuntimeError('DIAGNOSTICS_REMOTE_HEAD_READBACK_FAILED')
  for dest,source in results.items():
   blob=git(repo,'show',final+':'+dest).stdout
   if dest.endswith('.zip'):
    if 'oid sha256:'+sha(source) not in blob:raise RuntimeError('RAW_REMOTE_POINTER_MISMATCH')
   else:
    if hashlib.sha256(blob.encode()).hexdigest()!=sha(source):raise RuntimeError('RESULT_REMOTE_READBACK_MISMATCH '+dest)
  state['measurementCommit']=final;state['measurementRemoteReadback']=remote
  state['stage']='PUBLIC_DOWNLOADS';save()
  for suffix,p in [('REPORT.md',report),('SUMMARY.json',summary),('RAW.zip',raw)]:
   dest=downloads/(V+'_'+run+'_'+suffix)
   if dest.exists():raise RuntimeError('PUBLIC_FILE_COLLISION '+str(dest))
   shutil.copyfile(p,dest)
   if sha(dest)!=sha(p):raise RuntimeError('PUBLIC_READBACK_FAILED '+suffix)
   state.setdefault('publicArtifacts',{})[suffix]={'path':str(dest),'sha256':sha(dest)}
   if shutil.which('termux-media-scan'):cmd(['termux-media-scan',dest],timeout=30,check=False)
  state['stage']='COMPLETE';state['status']='READ_ONLY_MEASUREMENTS_REMOTE_VERIFIED';save()
  print('MEASUREMENTS=COMPLETE REMOTE_READBACK=VERIFIED MODEL_UNCHANGED=YES',flush=True)
  print('RESULT_COMMIT='+final,flush=True)
  for suffix,info in state['publicArtifacts'].items():print('RESULT_'+suffix+'='+info['path']+' SHA256='+info['sha256'],flush=True)
 except Exception as e:
  state['status']='BLOCKED';state['error']=type(e).__name__+': '+str(e);state['stage']='BLOCKED_'+state['stage'];save()
  print('BLOCKED='+state['error'],flush=True);traceback.print_exc();raise
 finally:
  save()
  with zipfile.ZipFile(handoff,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   z.write(receipt,'receipt.json')
   for n in logs.glob('*.log'):z.write(n,'logs/'+n.name)
   for kind in ('lionheart','obsidianti'):
    p=work/kind
    for n in ('metadata.json','trajectories.csv','blender_error.txt'):
     if (p/n).is_file():z.write(p/n,kind+'/'+n)
   for n in ('REPORT.md','summary.json'):
    p=work/'results'/n
    if p.is_file():z.write(p,'results/'+n)
  print('RECEIPT='+str(receipt)+'\nHANDOFF='+str(handoff)+'\nHANDOFF_SHA256='+sha(handoff),flush=True)
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('USAGE driver.py PACKET SHA')
 main(pathlib.Path(sys.argv[1]),sys.argv[2])
