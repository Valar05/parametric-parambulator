#!/usr/bin/env python3
"""Obsidianti sparse FK, v1.10.4. Termux Git owned mutation and immutable source baseline."""
import os,sys,pathlib,hashlib,json,subprocess,shutil,tempfile,zipfile,traceback,datetime
V='OBSIDIANTI_SPARSE_FK_AUTHORING_v1.10.4'
REPO='https://github.com/Valar05/parametric-parambulator.git'
BASE_NAME='OBSIDIANTI_FK_AUTHORITY_IK_AUTHORING_v1.10.1_20261106T041103Z_FK_BASELINE.blend'
BASE_SHA='96e13a407a3d1746636509ddf26dbc6d15aec78458beb333cbc99dfecf320034'
CAN_SHA='955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32'
AGENT_SHA='547c2af52303f4efb718bbf8f82a698110c7bfca'
DEST='diagnostics/obsidianti/sparse-fk-v1.10.4'
FILES={'campaigns/OBSIDIANTI_SPARSE_FK_RUN_v1.10.4.py':'driver.py',
       'campaigns/OBSIDIANTI_SPARSE_FK_BUILD_v1.10.4.py':'build.py',
       'docs/obsidianti/SPARSE_FK_AUTHORING_v1.10.4.md':'readme.md'}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def run(argv,check=True,timeout=270,env=None):
 argv=[str(x) for x in argv]
 p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+repr(argv[:7])+'\n'+p.stdout[-700:]+'\n'+p.stderr[-1400:])
 return p
def git(repo,*args,**kw):return run(['git','-C',repo,*args],**kw)
def published(repo,rel):return bool(git(repo,'ls-tree','-r','--name-only','HEAD','--',rel).stdout.strip())
def main(folder,launcher_sha):
 downloads=pathlib.Path.home()/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('TERMUX_DOWNLOADS_MISSING')
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 state=pathlib.Path.home()/'.local/state'/V;state.mkdir(parents=True,exist_ok=True)
 receipt=state/(stamp+'_RECEIPT.json')
 work=pathlib.Path(tempfile.mkdtemp(prefix='obs_sparse_fk_'));logs=work/'logs';logs.mkdir()
 doc={'campaign':V,'authority':'TERMUX_GIT_ONLY','canonicalGLBMutated':False,'originalActionsPreserved':True,
      'fkBaselineSHA256':BASE_SHA,'aresCandidateSHA256':CAN_SHA,'launcherSHA256':launcher_sha,
      'rulesRead':'AGENTS.md and full live Campaign Etiquette read by author 2026-11-06',
      'status':'STARTED','run':stamp,'downloads':{},'ownerVisualApproval':False}
 def save():receipt.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
 save();repo=work/'repo'
 try:
  env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1'
  run(['git','clone','--quiet','--no-checkout',REPO,repo],timeout=450,env=env)
  git(repo,'checkout','-q','main',env=env)
  git(repo,'lfs','install','--local')
  head=git(repo,'rev-parse','HEAD').stdout.strip()
  agentsblob=git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()
  if agentsblob!=AGENT_SHA:raise RuntimeError('AGENT_AUTHORITY_CHANGED_'+agentsblob)
  doc.update({'startingHEAD':head,'agentsGitBlobSHA':agentsblob,'executionDir':str(repo)})
  print('RESOLVED_REPO='+str(repo)+'\nEXECUTION_DIR='+str(repo)+'\nBRANCH=main\nHEAD='+head,flush=True)
  # Already verified original never silently falls back to wrong baseline.
  base=downloads/BASE_NAME
  if not base.is_file() or sha(base)!=BASE_SHA:
   rel='diagnostics/obsidianti/fk-authority-ik-v1.10.1/FK_BASELINE.blend'
   git(repo,'lfs','fetch','origin','--include='+rel,'--exclude=',timeout=700)
   git(repo,'lfs','checkout',rel,timeout=250)
   base=repo/rel
   if not base.is_file() or sha(base)!=BASE_SHA:raise RuntimeError('VERIFIED_FK_BASELINE_UNAVAILABLE')
  doc['fkBaselineLocation']=str(base)
  print('FK_BASELINE_VERIFIED='+str(base)+' SHA256='+BASE_SHA,flush=True)
  # All versioned destinations must be new, including source and evidence.
  expected=[*FILES,DEST+'/REPORT.json',DEST+'/REPORT.md',DEST+'/SPARSE_FK_EDITABLE_UNAPPROVED.blend']
  for rel in expected:
   if published(repo,rel) or (repo/rel).exists():raise RuntimeError('VERSIONED_PATH_ALREADY_EXISTS '+rel)
  for rel,src in FILES.items():
   dst=repo/rel;dst.parent.mkdir(parents=True,exist_ok=True)
   shutil.copyfile(folder/src,dst)
  # Test source existence and its exact checked-in content before execution.
  for rel,src in FILES.items():
   if sha(repo/rel)!=sha(folder/src):raise RuntimeError('REPO_SOURCE_STAGING_HASH_MISMATCH_'+rel)
  for rel in FILES:
   if rel.endswith('.py'):
    import py_compile
    py_compile.compile(str(repo/rel),doraise=True)
  git(repo,'add','--',*FILES)
  git(repo,'commit','-m','Obsidianti: sparse FK-only authoring source v1.10.4')
  sourcehead=git(repo,'rev-parse','HEAD').stdout.strip()
  git(repo,'push','origin','HEAD:main',timeout=300)
  if git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]!=sourcehead:
   raise RuntimeError('SOURCE_REMOTE_READBACK_FAILED')
  for rel,src in FILES.items():
   if git(repo,'show','HEAD:'+rel).stdout!=(folder/src).read_text():raise RuntimeError('SOURCE_REMOTE_CONTENT_MISMATCH_'+rel)
  doc['sourceCommit']=sourcehead;doc['sourceRemoteReadback']=True;save()
  blender=shutil.which('blender');proot=shutil.which('proot-distro')
  out=work/'SPARSE_FK_EDITABLE_UNAPPROVED.blend';rep=work/'REPORT.json'
  if blender:
   argv=[blender,'--background','--disable-autoexec','--python',repo/'campaigns/OBSIDIANTI_SPARSE_FK_BUILD_v1.10.4.py','--',base,out,rep]
  elif proot:
   # Bind original Downloads for existing baseline; do not copy a 25MB binary unnecessarily.
   argv=[proot,'login','debian','--bind',str(repo)+':/mnt/obs-repo','--bind',str(work)+':/mnt/obs-work',
         '--bind',str(downloads)+':/mnt/obs-downloads','--','blender','--background','--disable-autoexec',
         '--python','/mnt/obs-repo/campaigns/OBSIDIANTI_SPARSE_FK_BUILD_v1.10.4.py',
         '--','/mnt/obs-downloads/'+BASE_NAME if base.parent==downloads else '/mnt/obs-repo/diagnostics/obsidianti/fk-authority-ik-v1.10.1/FK_BASELINE.blend',
         '/mnt/obs-work/'+out.name,'/mnt/obs-work/'+rep.name]
  else:raise RuntimeError('BLENDER_AND_PROOT_DISTRO_MISSING')
  b=run(argv,check=False,timeout=2700)
  (logs/'blender.log').write_text(b.stdout+'\n'+b.stderr)
  if rep.exists():findings=json.loads(rep.read_text())
  else:
   findings={'status':'BLENDER_DID_NOT_WRITE_REPORT','returncode':b.returncode,'error':b.stderr[-1000:]}
   rep.write_text(json.dumps(findings,indent=2)+'\n')
  parity=(b.returncode==0 and findings.get('status')=='SPARSE_FK_PARITY_PASS_UNAPPROVED_FOR_VISUAL_REVIEW'
          and findings.get('reductionFraction',0)>=.05 and out.is_file())
  doc['sparseFKParityPassed']=parity;doc['blenderReturnCode']=b.returncode
  doc['reductionFraction']=findings.get('reductionFraction');save()
  print('SPARSE_FK_POSE_PARITY='+('PASS' if parity else 'FAILED'),flush=True)
  if findings.get('error'):print('FAILURE_REASON='+str(findings['error']),flush=True)
  if parity:print('KEY_REDUCTION_FRACTION='+str(findings['reductionFraction']),flush=True)
  markdown=work/'REPORT.md'
  markdown.write_text('# Obsidianti sparse FK authoring v1.10.4\n\n'
   'Input FK baseline: `'+BASE_SHA+'`\n\n'
   'Result: **'+findings.get('status','UNKNOWN')+'**\n\n'
   'Original 23 FK animations preserved. Only copied leg quaternion channels reduced.\n'
   'No IK; no floor-penetration or other artistic correction applied.\n'
   'No canonical model changes. Human visual review required.\n')
  publish=[(DEST+'/REPORT.json',rep),(DEST+'/REPORT.md',markdown)]
  if parity:publish.append((DEST+'/SPARSE_FK_EDITABLE_UNAPPROVED.blend',out))
  for rel,src in publish:
   dest=repo/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
  git(repo,'add','--',*[rel for rel,_ in publish])
  git(repo,'commit','-m','Obsidianti: sparse FK parity evidence v1.10.4')
  evidencehead=git(repo,'rev-parse','HEAD').stdout.strip()
  if parity:git(repo,'lfs','push','origin','HEAD',timeout=800)
  git(repo,'push','origin','HEAD:main',timeout=300)
  if git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]!=evidencehead:
   raise RuntimeError('EVIDENCE_REMOTE_READBACK_FAILED')
  for rel,src in publish:
   observed=git(repo,'show','HEAD:'+rel).stdout
   if rel.endswith('.blend'):
    if 'oid sha256:'+sha(src) not in observed:raise RuntimeError('LFS_REMOTE_POINTER_MISMATCH_'+rel)
   elif hashlib.sha256(observed.encode()).hexdigest()!=sha(src):
    raise RuntimeError('REMOTE_TEXT_READBACK_MISMATCH_'+rel)
  doc['evidenceCommit']=evidencehead;doc['evidenceRemoteReadback']=True
  print('REMOTE_READBACK_VERIFIED=YES EVIDENCE_COMMIT='+evidencehead,flush=True)
  for suffix,src in [('REPORT.json',rep),('REPORT.md',markdown)]+([('SPARSE_FK_EDITABLE_UNAPPROVED.blend',out)] if parity else []):
   name=V+'_'+stamp+'_'+suffix;dest=downloads/name;tmp=downloads/(name+'.partial')
   if dest.exists() or tmp.exists():raise RuntimeError('DOWNLOAD_PATH_COLLISION '+name)
   shutil.copyfile(src,tmp)
   if sha(src)!=sha(tmp):raise RuntimeError('TEMP_DOWNLOAD_SHA_MISMATCH_'+name)
   os.replace(tmp,dest)
   if sha(src)!=sha(dest):raise RuntimeError('FINAL_DOWNLOAD_SHA_MISMATCH_'+name)
   doc['downloads'][suffix]={'path':str(dest),'sha256':sha(dest)}
   if shutil.which('refreshmedia'):
    run(['refreshmedia',dest],check=False,timeout=35)
   elif shutil.which('termux-media-scan'):
    run(['termux-media-scan',dest],check=False,timeout=35)
   print('DOWNLOADS_'+suffix+'='+str(dest)+' SHA256='+sha(dest),flush=True)
  doc['status']='SPARSE_FK_UNAPPROVED_DELIVERED' if parity else 'SPARSE_FK_PARITY_FAILED_SOURCE_FK_PRESERVED'
  print('STATUS='+doc['status']+'\nCANONICAL_GLB_UNCHANGED=YES',flush=True)
  save()
 except Exception as exc:
  doc['status']='BLOCKED';doc['error']=type(exc).__name__+': '+str(exc);save()
  traceback.print_exc();print('BLOCKED='+doc['error'],flush=True)
 finally:
  handoff=downloads/(V+'_'+stamp+'_HANDOFF.zip')
  with zipfile.ZipFile(handoff,'w',compression=zipfile.ZIP_DEFLATED) as z:
   z.write(receipt,'receipt.json')
   for p in logs.glob('*'):z.write(p,'logs/'+p.name)
   for p in (work/'REPORT.json',work/'REPORT.md'):
    if p.exists():z.write(p,'results/'+p.name)
  print('RECEIPT='+str(receipt)+'\nHANDOFF='+str(handoff)+'\nHANDOFF_SHA256='+sha(handoff),flush=True)
if __name__=='__main__':main(pathlib.Path(sys.argv[1]),sys.argv[2])
