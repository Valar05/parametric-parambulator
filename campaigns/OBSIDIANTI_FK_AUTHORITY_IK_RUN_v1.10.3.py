#!/usr/bin/env python3
"""Termux Git-only, isolated source/IK authoring gate, durable evidence and resumability."""
import os,sys,pathlib,hashlib,json,subprocess,shutil,tempfile,zipfile,traceback,datetime,time
V='OBSIDIANTI_FK_AUTHORITY_IK_AUTHORING_v1.10.3'
REPO='https://github.com/Valar05/parametric-parambulator.git'
ARCHIVE='diagnostics/obsidianti/ares-fk-rebase-v1.0.1/UNAPPROVED_CANDIDATE.zip'
RESULT='diagnostics/obsidianti/ares-fk-rebase-v1.0.1/RESULT.json'
CAN_SHA='955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32'
ZIP_SHA='4a039eb3d73ae1d3430c7eb9c90c55aba5d4c00fda7a86e6704c8eaab2c45b10'
SRC_COMMIT='7b94590d4fe9a3a1a0481cd3d75426a58eb05517'
AGENT_SHA='547c2af52303f4efb718bbf8f82a698110c7bfca'
DEST='diagnostics/obsidianti/fk-authority-ik-v1.10.3'
FILES={'campaigns/OBSIDIANTI_FK_AUTHORITY_IK_RUN_v1.10.3.py':'driver.py','campaigns/OBSIDIANTI_FK_AUTHORITY_IK_BUILD_v1.10.3.py':'build.py','docs/obsidianti/FK_AUTHORITY_IK_v1.10.3.md':'readme.md'}
def hashfile(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def run(argv,*,check=True,timeout=240,env=None):
 p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+repr(argv[:8])+'\n'+p.stdout[-900:]+'\n'+p.stderr[-1600:])
 return p
def git(repo,*args,**kw):return run(['git','-C',repo,*args],**kw)
def download_lfs(repo,path,expected,output):
 # Fetch ONLY the required Obsidianti evidence object; never request Repl's missing LFS object.
 git(repo,'lfs','fetch','origin','--include='+path,'--exclude=',timeout=500)
 git(repo,'lfs','checkout',path,timeout=120)
 inp=repo/path
 if hashfile(inp)!=expected:raise RuntimeError('LFS_EVIDENCE_SHA_MISMATCH_'+path)
 shutil.copyfile(inp,output)
def pub_sha(repo,path):
 return git(repo,'rev-parse','HEAD:'+path).stdout.strip()
def verify_hashes(repo,receipt):
 a=git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()
 if a!=AGENT_SHA:raise RuntimeError('AGENTS_BLOB_CHANGED '+a)
 receipt['agentsGitBlobSHA']=a

def main(folder,launcher_sha):
 downloads=pathlib.Path.home()/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('TERMUX_DOWNLOADS_MISSING')
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 state=pathlib.Path.home()/'.local/state'/V
 state.mkdir(parents=True,exist_ok=True)
 receipt=state/(stamp+'_RECEIPT.json')
 work=pathlib.Path(tempfile.mkdtemp(prefix='obs_fk_author_'))
 doc={'campaign':V,'authority':'TERMUX_GIT_ONLY','sourceCandidateSHA256':CAN_SHA,'canonicalGLBMutation':False,
      'originalFKProtected':True,'approved':'NO_VISUAL_ACCEPTANCE','status':'STARTED','launcherSHA256':launcher_sha,
      'run':stamp,'paths':{},'rulesRead':'AGENTS and live etiquette inspected by author 2026-11-05'}
 def save():receipt.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
 save();repo=work/'repo';logs=work/'logs';logs.mkdir()
 try:
  os.environ['GIT_LFS_SKIP_SMUDGE']='1'
  env=os.environ.copy()
  # Authoritative repo source, not an arbitrary phone checkout.
  p=run(['git','clone','--quiet','--no-checkout',REPO,repo],timeout=400,env=env)
  git(repo,'checkout','-q','main',env=env);git(repo,'lfs','install','--local')
  head=git(repo,'rev-parse','HEAD').stdout.strip();doc['startingHEAD']=head
  doc['repo']=str(repo);doc['executionDir']=str(repo);doc['branch']='main';verify_hashes(repo,doc);save()
  print('RESOLVED_REPO='+str(repo)+'\nEXECUTION_DIR='+str(repo)+'\nBRANCH=main\nHEAD='+head,flush=True)
  # Need exact original published evidence, verify two independent manifest sources.
  j=json.loads((repo/RESULT).read_text())
  if j['candidateSha256']!=CAN_SHA:raise RuntimeError('RESULT_CANDIDATE_SHA_MISMATCH')
  if j['sourceSha256']!='5fa8773736cf4fd28eae13e13368246642642a1802d76e47ed7e14faf70d04c0':raise RuntimeError('RESULT_PROVENANCE_MISMATCH')
  # Verify expected LFS object before reading any pixels or model.
  archive=work/'candidate.zip';download_lfs(repo,ARCHIVE,ZIP_SHA,archive)
  with zipfile.ZipFile(archive) as z:
   names=z.namelist();expected={'AresScaled_PreContactFK_UNAPPROVED.glb','RESULT.json'}
   if set(names)!=expected or len(names)!=2:raise RuntimeError('ARCHIVE_MEMBER_INVENTORY '+repr(names))
   raw=z.read('AresScaled_PreContactFK_UNAPPROVED.glb')
   if hashlib.sha256(raw).hexdigest()!=CAN_SHA:raise RuntimeError('CANDIDATE_GLB_SHA_MISMATCH')
   if json.loads(z.read('RESULT.json'))['candidateSha256']!=CAN_SHA:raise RuntimeError('ARCHIVE_RESULT_MISMATCH')
  model=work/'source_fk_unapproved.glb';model.write_bytes(raw)
  doc['sourceBinaryVerified']=True;doc['sourceCommit']=SRC_COMMIT;save()
  # Collision gate happens before publishing new source files.
  intended=[*FILES,DEST+'/PARITY.json',DEST+'/REPORT.md',DEST+'/IK_EDITABLE_UNAPPROVED.blend']
  for name in intended:
   if git(repo,'ls-tree','-r','--name-only','HEAD','--',name).stdout.strip() or (repo/name).exists():raise RuntimeError('VERSIONED_PATH_COLLISION '+name)
  for name,local in FILES.items():
   dst=repo/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(folder/local,dst)
  git(repo,'add','--',*FILES)
  git(repo,'commit','-m','Obsidianti: dense FK-sampled IK authoring v1.10.3')
  pre=git(repo,'rev-parse','HEAD').stdout.strip()
  git(repo,'push','origin','HEAD:main',timeout=240)
  remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]
  if remote!=pre:raise RuntimeError('SOURCE_REMOTE_READBACK_FAILED')
  for name,local in FILES.items():
   if git(repo,'show','HEAD:'+name).stdout!= (folder/local).read_text():raise RuntimeError('SOURCE_CONTENT_REMOTE_MISMATCH '+name)
  doc['sourceCommit']=pre;doc['sourceRemoteReadback']=True;doc['status']='SOURCE_PUBLISHED';save()
  # The existing v1.10.1 FK baseline is immutable and is reused, not rebuilt.
  # It must exist even if an experimental IK rig cannot reproduce all poses.
  blender=shutil.which('blender');proot=shutil.which('proot-distro')
  def blender_call(script,output,reportpath):
   if blender:
    return [blender,'--background','--disable-autoexec','--python',repo/script,
            '--',model,output,reportpath]
   if proot:
    return [proot,'login','debian',
            '--bind',str(repo)+':/mnt/obs-repo',
            '--bind',str(work)+':/mnt/obs-work',
            '--','blender','--background','--disable-autoexec',
            '--python','/mnt/obs-repo/'+script,'--',
            '/mnt/obs-work/'+model.name,'/mnt/obs-work/'+output.name,
            '/mnt/obs-work/'+reportpath.name]
   raise RuntimeError('BLENDER_AND_PROOT_DISTRO_ABSENT')
  previous_baseline_name='OBSIDIANTI_FK_AUTHORITY_IK_AUTHORING_v1.10.1_20261106T041103Z_FK_BASELINE.blend'
  previous_baseline_sha='96e13a407a3d1746636509ddf26dbc6d15aec78458beb333cbc99dfecf320034'
  previous_baseline_path=downloads/previous_baseline_name
  if not previous_baseline_path.is_file() or hashfile(previous_baseline_path)!=previous_baseline_sha:
   # Independently recover the exact approved-source FK baseline from prior Git LFS evidence.
   prior='diagnostics/obsidianti/fk-authority-ik-v1.10.1/FK_BASELINE.blend'
   temp=work/'FK_BASELINE_PREVIOUS.blend'
   download_lfs(repo,prior,previous_baseline_sha,temp)
   previous_baseline_path=temp
  doc['previousFKBaselineSHA256']=hashfile(previous_baseline_path)
  doc['fkBaselineStatus']='EXISTING_V1.10.1_FK_BASELINE_REUSED_IMMUTABLE'
  doc['previousFKBaselinePath']=str(previous_baseline_path)
  save()
  print('FK_BASELINE_REUSED='+str(previous_baseline_path)+' SHA256='+previous_baseline_sha,flush=True)
  # Experiment: original FK is immutable; IK can be reported as blocked without
  # discarding the successfully built FK authoring baseline.
  blend=work/'IK_EDITABLE_UNAPPROVED.blend';parity=work/'PARITY.json'
  p=run(blender_call('campaigns/OBSIDIANTI_FK_AUTHORITY_IK_BUILD_v1.10.3.py',blend,parity),timeout=2400,check=False)
  (logs/'ik_blender.log').write_text(p.stdout+'\n'+p.stderr)
  if parity.exists():
   findings=json.loads(parity.read_text())
  else:
   findings={'status':'IK_BUILD_FAILED_NO_PARITY','error':p.stderr[-1100:], 'parity':{'passed':False}}
   parity.write_text(json.dumps(findings,indent=2)+'\n')
  doc['parityStatus']=findings.get('status');doc['blenderReturnCode']=p.returncode
  if blend.exists():doc['ikBlendSHA256']=hashfile(blend)
  ik_pass=(p.returncode==0 and findings.get('status')=='PARITY_PASS_UNAPPROVED_FOR_VISUAL_REVIEW'
           and findings.get('parity',{}).get('passed') is True and blend.exists())
  doc['ikPoseParityPassed']=ik_pass
  save()
  print('KNEE_POLE_PARENTAGE='+str(findings.get('poleParentage','UNAVAILABLE'))+'\nIK_POSE_PARITY='+('PASS' if ik_pass else 'FAILED; FK_BASELINE_PRESERVED'),flush=True)
  report=work/'REPORT.md'
  report.write_text('# Obsidianti FK-authority IK dense FK-sampled IK reconstruction\n\nSource candidate: `'+CAN_SHA+'`\n\nStatus: **'+findings['status']+'**\n\nOriginal FK remains unchanged. Human visual approval is pending.\n\nAn IK authoring artifact is approved for editing ONLY if dense-sample and independent midpoint parity passed.\n')
  # Publish authoritative FK project and diagnostics through the requested Termux Git lane.
  publish=[(DEST+'/PARITY.json',parity),
           (DEST+'/REPORT.md',report)]
  if ik_pass:publish.append((DEST+'/IK_EDITABLE_UNAPPROVED.blend',blend))
  for rel,src in publish:
   target=repo/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
  git(repo,'add','--',*(rel for rel,_ in publish))
  git(repo,'commit','-m','Obsidianti: FK baseline and IK parity evidence v1.10.3')
  pub=git(repo,'rev-parse','HEAD').stdout.strip()
  git(repo,'lfs','push','origin','HEAD',timeout=700)
  git(repo,'push','origin','HEAD:main',timeout=300)
  remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]
  if remote!=pub:raise RuntimeError('EVIDENCE_REMOTE_READBACK_FAILED')
  for rel,src in publish:
   remote_blob=git(repo,'show','HEAD:'+rel).stdout
   if rel.endswith('.blend'):
    if 'oid sha256:'+hashfile(src) not in remote_blob:
     raise RuntimeError('BLEND_LFS_POINTER_READBACK_FAILED '+rel)
   elif hashlib.sha256(remote_blob.encode()).hexdigest()!=hashfile(src):
    raise RuntimeError('TEXT_REMOTE_READBACK_FAILED '+rel)
  doc['evidenceCommit']=pub;doc['evidenceRemoteReadback']=True
  print('REMOTE_READBACK_VERIFIED=YES EVIDENCE_COMMIT='+pub,flush=True)
  # Atomic shared Downloads copy/readback, including the FK baseline even if IK fails.
  for suffix,src in [('PARITY.json',parity),('REPORT.md',report)]:
   if not src.exists():continue
   name=V+'_'+stamp+'_'+suffix;dst=downloads/name
   tmp=downloads/(name+'.partial')
   if dst.exists() or tmp.exists():raise RuntimeError('PUBLIC_DOWNLOAD_COLLISION '+name)
   shutil.copyfile(src,tmp)
   if hashfile(src)!=hashfile(tmp):raise RuntimeError('ANDROID_DOWNLOADS_TEMP_HASH_MISMATCH '+suffix)
   os.replace(tmp,dst)
   if hashfile(src)!=hashfile(dst):raise RuntimeError('ANDROID_DOWNLOADS_SHA_MISMATCH '+suffix)
   doc['paths'][suffix]=str(dst)
  if ik_pass:
   src=blend;suffix='IK_EDITABLE_UNAPPROVED.blend';dst=downloads/(V+'_'+stamp+'_'+suffix)
   tmp=dst.with_name(dst.name+'.partial');shutil.copyfile(src,tmp)
   if hashfile(tmp)!=hashfile(src):raise RuntimeError('IK_DOWNLOAD_TEMP_SHA_MISMATCH')
   os.replace(tmp,dst)
   if hashfile(src)!=hashfile(dst):raise RuntimeError('IK_DOWNLOAD_SHA_MISMATCH')
   doc['paths'][suffix]=str(dst)
  if shutil.which('termux-media-scan'):
   for path in doc['paths'].values():run(['termux-media-scan',path],timeout=30,check=False)
  print('FK_BASELINE_DOWNLOADS='+str(previous_baseline_path),flush=True)
  print('FK_BASELINE_SHA256='+previous_baseline_sha,flush=True)
  doc['status']='IK_PARITY_PASS_UNAPPROVED' if ik_pass else 'FK_BASELINE_PRESERVED_IK_PARITY_FAILED';save()
  print('POSE_PARITY='+str(ik_pass)+'\nSTATUS='+doc['status']+'\nCANONICAL_GLB_UNCHANGED=YES',flush=True)
  for k,v in doc['paths'].items():print(k+'='+v,flush=True)
 except Exception as exc:
  doc['status']='BLOCKED';doc['error']=type(exc).__name__+': '+str(exc);save();traceback.print_exc()
  print('BLOCKED='+doc['error'],flush=True)
 finally:
  handoff=downloads/(V+'_'+stamp+'_HANDOFF.zip')
  with zipfile.ZipFile(handoff,'w',compression=zipfile.ZIP_DEFLATED) as z:
   z.write(receipt,'receipt.json')
   for p in logs.glob('*'):z.write(p,'logs/'+p.name)
   for p in (work/'PARITY.json',work/'REPORT.md'):
    if p.exists():z.write(p,'results/'+p.name)
  print('RECEIPT='+str(receipt)+'\nHANDOFF='+str(handoff)+'\nHANDOFF_SHA256='+hashfile(handoff),flush=True)
if __name__=='__main__':main(pathlib.Path(sys.argv[1]),sys.argv[2])
