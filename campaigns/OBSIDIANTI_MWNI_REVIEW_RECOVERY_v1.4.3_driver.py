#!/usr/bin/env python3
"""Termux-only recovery: publish SHA-locked prior Mwni candidate exports. No animation edits."""
from __future__ import annotations
import datetime,gzip,hashlib,json,os,pathlib,shutil,struct,subprocess,sys,time,traceback,uuid
V='OBSIDIANTI_MWNI_REVIEW_RECOVERY_v1.4.3'
PREV='OBSIDIANTI_MWNI_RETARGET_PLUGIN_v1.4.0'
PREV_RUN='20261106T172615Z-6d53cfaf'
PRIOR_EVIDENCE_COMMIT='8f3485133c8ce5f616e396aab2fbf83636412334'
PRIOR_SOURCE_COMMIT='57887917861935874ec5e7dd1fda8b7617aa6941'
PRIOR_RESULTS_SHA='a04700e59b86a617c7fa66fc0921bae79ee07c282f7ff3418642c270ca51e981'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANONICAL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
REPO_URL='https://github.com/Valar05/parametric-parambulator.git'
PRIOR_RESULTS='diagnostics/obsidianti/mwni-plugin-v1.4.0/RESULTS.json'
PRIOR_REPORT='diagnostics/obsidianti/mwni-plugin-v1.4.0/REPORT.md'
PRIOR_RECEIPT='diagnostics/obsidianti/mwni-plugin-v1.4.0/EVIDENCE_RECEIPT.json'
MODEL='assets/obsidianti/Obsidianti.glb';LOCKED=(MODEL,'assets/repl/Repl.glb')
SOURCES={'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER','campaigns/'+V+'_driver.py':'driver.py','tests/'+V+'_TEST.py':'test_driver.py','campaigns/'+V+'.contract.json':'contract.json'}
DIR='diagnostics/obsidianti/mwni-recovery-v1.4.3'
EVIDENCE={DIR+'/RECOVERY_REPORT.md':'RECOVERY_REPORT.md',DIR+'/RECOVERY_RECEIPT.json':'RECOVERY_RECEIPT.json'}


def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()

def invoke(args,timeout=150,check=True,env=None):
 r=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=timeout,env=env)
 if check and r.returncode:raise RuntimeError('COMMAND_FAILED '+repr([str(x) for x in args[:8]])+' EXIT='+str(r.returncode)+' '+r.stderr[-900:])
 return r

def git(repo,*args,timeout=150,check=True):return invoke(['git','-C',repo,*args],timeout=timeout,check=check)
def gtext(repo,*args):return git(repo,*args).stdout.strip()

def safe_path_name(dest):
 p=pathlib.PurePosixPath(dest)
 if p.is_absolute() or any(part in ('..','.') for part in p.parts):raise RuntimeError('UNSAFE_RELATIVE_PATH '+dest)
 return p

def validate_manifest(packet):
 m=json.loads((packet/'manifest.json').read_text())
 if set(m)!={'driver.py','test_driver.py','contract.json'}:raise RuntimeError('WRONG_PACKET_MEMBERS')
 for name,digest in m.items():
  p=packet/name
  if not p.is_file() or sha(p)!=digest:raise RuntimeError('PACKET_HASH_MISMATCH '+name)
 return sha(packet/'manifest.json')

def file_structure(p,extension):
 """Identify SHA-locked Blender/GLB artifacts without assuming Blender's compression.

 Important: Blender 4.3.2 with compress=True emits Zstandard frames (28 b5 2f fd),
 not necessarily gzip. The *authoritative* integrity test is the prior Blender
 output's exact SHA-256 AND size from the committed v1.4.0 results. Structure
 checks are additional sanity checks and must not demand unavailable decoders.
 """
 p=pathlib.Path(p)
 size=p.stat().st_size
 if extension=='.glb':
  with open(p,'rb') as f:header=f.read(12)
  if len(header)!=12 or header[:4]!=b'glTF':raise RuntimeError('BAD_GLB_MAGIC '+str(p))
  magic,version,length=struct.unpack('<4sII',header)
  if version!=2 or length!=size:raise RuntimeError('BAD_GLB_SIZE_OR_VERSION '+str(p))
  return {'encoding':'GLB2','bytes':size,'structureCheck':'GLTF2_HEADER_AND_LENGTH'}
 if extension!='.blend':raise RuntimeError('UNKNOWN_CANDIDATE_FORMAT '+str(p))
 with open(p,'rb') as f:prefix=f.read(12)
 def valid_header(header):
  return (len(header)==12 and header[:7]==b'BLENDER' and
          header[7:8] in (b'-',b'_') and header[8:9] in (b'v',b'V') and
          all(48<=c<=57 for c in header[9:12]))
 if valid_header(prefix):
  return {'encoding':'BLEND_RAW','bytes':size,'blenderHeader':prefix.decode('ascii')}
 if prefix[:4]==b'\x28\xb5\x2f\xfd':
  # zstd is an OPTIONAL extra check, not a new required package installation.
  # Prior SHA+length are enforced BEFORE this function is called on device.
  binary=shutil.which('zstd')
  if binary:
   r=invoke([binary,'-t','-q',p],timeout=180,check=False)
   if r.returncode:raise RuntimeError('CORRUPT_ZSTD_BLEND '+str(p)+' '+r.stderr[-350:])
   validation='ZSTD_FULL_STREAM_OK_AND_AUTHORITATIVE_SHA'
  else:
   validation='ZSTD_MAGIC_PLUS_AUTHORITATIVE_SHA_NO_DECODER_AVAILABLE'
  return {'encoding':'BLEND_ZSTD','bytes':size,'zstdFrameMagic':prefix[:4].hex(),'structureCheck':validation}
 if prefix[:2]==b'\x1f\x8b':
  try:
   with gzip.open(p,'rb') as stream:
    header=stream.read(12)
    if not valid_header(header):raise RuntimeError('BAD_GZIP_BLEND_CONTENT '+str(p)+' HEADER='+header.hex())
    count=len(header)
    while True:
     block=stream.read(1024*1024)
     if not block:break
     count+=len(block)
     if count>1024*1024*1024:raise RuntimeError('BLEND_DECOMPRESSED_LIMIT_EXCEEDED '+str(p))
  except (OSError,EOFError) as e:
   raise RuntimeError('CORRUPT_GZIP_BLEND '+str(p)+' '+repr(e)) from e
  return {'encoding':'BLEND_GZIP','bytes':size,'decompressedBytes':count,'blenderHeader':header.decode('ascii')}
 raise RuntimeError('BAD_BLEND_MAGIC '+str(p)+' HEADER='+prefix[:12].hex())

def resolve_candidate(previous_root,downloads,clip,key,record,allow_fallback=True):
 """Translate Blender's proot bind prefix into Termux actual work dir, with hash guard."""
 path=record['path'];prefix='/mnt/obs-output/'
 if not path.startswith(prefix):raise RuntimeError('UNRECOGNIZED_BLENDER_VIRTUAL_PATH '+repr(path))
 rel=safe_path_name(path[len(prefix):])
 expected=pathlib.PurePosixPath(clip)/('MWNI_'+clip+'_UNAPPROVED'+('.glb' if key=='candidateGLB' else '.blend'))
 if rel!=expected:raise RuntimeError('UNEXPECTED_BLENDER_ARTIFACT_RELATIVE_PATH '+str(rel)+' expected '+str(expected))
 candidates=[previous_root/'work'/pathlib.Path(*rel.parts)]
 if allow_fallback:
  # Only other previously produced exact filenames in the user's Downloads, not arbitrary device crawling.
  candidates.extend(sorted(downloads.glob(PREV+'_*_'+expected.name)))
  # Other bounded, immutable run folders if the recorded run was moved between app sessions.
  parent=previous_root.parent
  if parent.is_dir():
   candidates.extend(sorted(parent.glob('*/work/'+str(rel))))
 inspected=[]
 for p in dict.fromkeys(candidates):
  if not p.is_file():continue
  actual=sha(p);inspected.append((str(p),actual))
  if actual!=record['sha256']:continue
  if p.stat().st_size!=record['bytes']:raise RuntimeError('CANDIDATE_SIZE_MISMATCH '+str(p))
  file_structure(p,p.suffix)
  return p
 raise RuntimeError('VERIFIED_CANDIDATE_NOT_FOUND '+clip+' '+key+' expectedSha='+record['sha256']+' inspected='+repr(inspected[:10]))

def durable_copy(source,dest,expected):
 source=pathlib.Path(source);dest=pathlib.Path(dest)
 if sha(source)!=expected:raise RuntimeError('SOURCE_BYTES_CHANGED '+str(source))
 if dest.exists():
  if not dest.is_file() or sha(dest)!=expected:raise RuntimeError('OUTPUT_FILENAME_COLLISION '+str(dest))
  return 'EXISTS_VERIFIED'
 dest.parent.mkdir(parents=True,exist_ok=True)
 tmp=dest.with_name('.'+dest.name+'.tmp-'+uuid.uuid4().hex[:10])
 try:
  shutil.copyfile(source,tmp)
  if sha(tmp)!=expected:raise RuntimeError('DESTINATION_COPY_HASH_CHANGED '+str(dest))
  os.replace(tmp,dest)
 finally:
  if tmp.exists():tmp.unlink()
 return 'COPIED_SHA_VERIFIED'

def publish(repo,stage):
 head=gtext(repo,'rev-parse','HEAD')
 for attempt in range(3):
  out=git(repo,'push','origin','HEAD:refs/heads/main',timeout=300,check=False)
  if not out.returncode:break
  if attempt==2:raise RuntimeError(stage+'_GIT_PUSH_FAILED '+out.stderr[-1200:])
  time.sleep(2+attempt)
 raw=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()
 if not raw or raw[0]!=head:raise RuntimeError(stage+'_REMOTE_SHA_MISMATCH expected='+head+' actual='+repr(raw))
 git(repo,'fetch','origin','main',timeout=200)
 if gtext(repo,'rev-parse','refs/remotes/origin/main')!=head:raise RuntimeError(stage+'_REMOTE_FETCH_MISMATCH')
 return head

def clone_checkout(root):
 repo=root/'repo';env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
 invoke(['git','clone','--quiet','--depth=1','--single-branch','--branch','main',REPO_URL,repo],timeout=450,env=env)
 origin=gtext(repo,'remote','get-url','origin')
 if origin.rstrip('/').removesuffix('.git')!=REPO_URL.removesuffix('.git'):raise RuntimeError('WRONG_REPOSITORY_REMOTE '+origin)
 head=gtext(repo,'rev-parse','HEAD')
 # Do not assume the old evidence is in HEAD; verify ancestry. Fetch only when needed.
 r=git(repo,'cat-file','-e',PRIOR_EVIDENCE_COMMIT+'^{commit}',check=False)
 if r.returncode or git(repo,'merge-base','--is-ancestor',PRIOR_EVIDENCE_COMMIT,'HEAD',check=False).returncode:
  got=git(repo,'fetch','--no-tags','--depth=60','origin',PRIOR_EVIDENCE_COMMIT,timeout=180,check=False)
  if got.returncode or git(repo,'merge-base','--is-ancestor',PRIOR_EVIDENCE_COMMIT,'HEAD',check=False).returncode:
   raise RuntimeError('PREVIOUS_EVIDENCE_NOT_IN_CURRENT_MAIN_ANCESTRY '+head)
 if gtext(repo,'rev-parse','HEAD:AGENTS.md')!=AGENTS_BLOB:raise RuntimeError('POLICY_BLOB_CHANGED')
 if gtext(repo,'status','--porcelain'):raise RuntimeError('CLEAN_ISOLATED_CHECKOUT_REQUIRED')
 lfs=gtext(repo,'show','HEAD:'+MODEL)
 if 'oid sha256:'+CANONICAL_SHA not in lfs:raise RuntimeError('CANONICAL_MODEL_LFS_SHA_CHANGED')
 return repo,head

def ensure_identity(repo):
 if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Campaign')
 if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')

def main(packet,launcher,launcher_hash):
 downloads=pathlib.Path.home()/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('TERMUX_SHARED_DOWNLOADS_NOT_FOUND')
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
 receipt=root/'RECEIPT.json';record={'campaign':V,'authority':'TERMUX_GIT_ONLY','status':'PREFLIGHT',
    'runId':runid,'launcherSHA256':launcher_hash,'canonicalModified':False,'originalBlendModified':False,
    'originalRunId':PREV_RUN,'agentsBlob':AGENTS_BLOB,'liveCampaignEtiquetteReadAtAuthoring':'2026-11-06',
    'deviceCurrentEtiquetteRead':'RULES_ALREADY_READ_AUTHOR_CHAT__ON_DEVICE_GIT_POLICY_VERIFIED'}
 def save():
  tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n');os.replace(tmp,receipt)
 save()
 try:
  record['manifestSHA256']=validate_manifest(packet)
  invoke(['python3','-m','py_compile',packet/'driver.py',packet/'test_driver.py'])
  invoke(['python3',packet/'test_driver.py'],timeout=50)
  con=json.loads((packet/'contract.json').read_text())
  if set(con['mutablePaths'])!=set(SOURCES)|set(EVIDENCE):raise RuntimeError('WRITE_CONTRACT_MISMATCH')
  if invoke(['git','lfs','version'],check=False).returncode:raise RuntimeError('GIT_LFS_UNAVAILABLE')
  previous=pathlib.Path.home()/'.local/state'/PREV/PREV_RUN
  if not previous.is_dir():raise RuntimeError('PREVIOUS_V140_RUN_DIRECTORY_MISSING '+str(previous))
  prevreceipt=previous/'RECEIPT.json'
  if not prevreceipt.is_file():raise RuntimeError('PREVIOUS_RECEIPT_MISSING')
  old=json.loads(prevreceipt.read_text())
  if old.get('sourceCommit')!=PRIOR_SOURCE_COMMIT or old.get('evidenceCommit')!=PRIOR_EVIDENCE_COMMIT:
   raise RuntimeError('WRONG_OLD_RUN_RECEIPT '+repr({k:old.get(k) for k in ['sourceCommit','evidenceCommit']}))
  repo,prior_head=clone_checkout(root);record['mainHeadAtStart']=prior_head
  locked={n:gtext(repo,'rev-parse','HEAD:'+n) for n in LOCKED};record['lockedTreesBefore']=locked
  original=repo/PRIOR_RESULTS
  if not original.is_file() or sha(original)!=PRIOR_RESULTS_SHA:raise RuntimeError('SOURCE_RESULTS_SHA_NOT_AUTHORITATIVE '+(sha(original) if original.is_file() else 'MISSING'))
  oldresults=json.loads(original.read_text())
  if oldresults['targetCanonicalSHA256']!=CANONICAL_SHA or oldresults['successfulClipTests']!=['Heavy1','Light2']:
   raise RuntimeError('OLD_RESULTS_SEMANTIC_MISMATCH')
  if sha(repo/PRIOR_REPORT)!='63cc95e7c7a44b6d2b8e2102de2b6b8bc2d17e2ac96a912d5844cacc775bc708':raise RuntimeError('PRIOR_REPORT_SHA_CHANGED')
  resolved={}
  for clip in ('Heavy1','Light2'):
   trial=oldresults['trials'][clip]
   if trial['returncode'] or trial['verdict']['status']!='PLUGIN_IK_BAKE_EXPORT_TESTED_UNAPPROVED':raise RuntimeError('ORIGINAL_TRIAL_NOT_SUCCESSFUL '+clip)
   for key in ('candidateGLB','editableBlend'):
    metadata=trial['verdict']['outputPaths'][key]
    p=resolve_candidate(previous,downloads,clip,key,metadata)
    resolved[(clip,key)]={'path':p,'sha':metadata['sha256'],'bytes':metadata['bytes'],'name':p.name,'format':file_structure(p,p.suffix)}
    print('RECOVERED='+clip+'/'+key+' SOURCE='+str(p)+' SHA256='+metadata['sha256'],flush=True)
  # All four original files MUST be found and SHA-checked before any Git publication.
  allpaths=set(SOURCES)|set(EVIDENCE)
  if any((repo/n).exists() for n in allpaths):raise RuntimeError('NEW_VERSION_GIT_PATH_COLLISION')
  ensure_identity(repo)
  for dst,name in SOURCES.items():
   src=launcher if name=='LAUNCHER' else packet/name
   durable_copy(src,repo/dst,sha(src))
  git(repo,'add','--',*sorted(SOURCES));staged=set(gtext(repo,'diff','--cached','--name-only').splitlines())
  if staged!=set(SOURCES):raise RuntimeError('SOURCE_STAGING_ALLOWLIST_FAILURE '+repr(staged))
  git(repo,'commit','-m','Obsidianti: repair Mwni virtual-path artifact handoff in verified Termux recovery')
  record['sourceCommit']=publish(repo,'SOURCE');record['status']='RECOVERY_SOURCE_COMMITTED_REMOTE_VERIFIED';save()
  # No reliance on virtual proot paths beyond mapping to the exact SHA-verified prior workdir.
  copied=[]
  for (clip,key),item in resolved.items():
   dest=downloads/(V+'_'+PREV_RUN+'_'+item['name'])
   outcome=durable_copy(item['path'],dest,item['sha'])
   fmt=file_structure(dest,dest.suffix)
   if fmt['encoding']!=item['format']['encoding']:raise RuntimeError('CANDIDATE_FORMAT_CHANGED_AFTER_COPY '+str(dest))
   copied.append({'format':fmt,'clip':clip,'kind':key,'priorSHA256':item['sha'],'androidSharedPath':str(dest),'sha256Readback':sha(dest),'bytes':dest.stat().st_size,'state':outcome})
   print('DOWNLOAD_UNAPPROVED_CANDIDATE='+str(dest)+' SHA256='+item['sha']+' STATE='+outcome,flush=True)
  report=['# Obsidianti Mwni v1.4.3: recovery of real Blender review files','',
   '**Status:** 4 previous Blender exports recovered and SHA-verified in shared Android Downloads; source and canonical model unchanged.',
   '',f'- Source prior evidence commit: `{PRIOR_EVIDENCE_COMMIT}`',f'- Original run: `{PREV_RUN}`',
   '- Failures repaired: v1.4.0 used proot-only virtual paths; v1.4.1 rejected compressed Blender files; v1.4.2 recognized raw/gzip but not the real Zstd bytes.',
   '- Correction: resolve the pinned proot bind path, verify exact Git-recorded SHA and size, recognize raw/gzip/Zstd Blender signatures and optionally test the entire Zstd frame when the decoder is already installed.',
   '- Retarget tests were completed previously: Heavy1 and Light2, both with plugin IK enabled; they remain UNAPPROVED.',
   '- Heavy1 right-foot discrepancy RMS: 0.419519 m baseline to 0.065851 m with IK.',
   '- Light2 right-foot discrepancy RMS: 0.437381 m baseline to 0.073581 m with IK.',
   '- Light2 left-foot discrepancy RMS WORSENED: 0.078855 m baseline to 0.150371 m with IK.',
   '- This recovery does not rerun the solver, change the plugin, modify source or canonical rig, or assert sole contact/visual approval.',
   '', '## Published candidate files','', '| Clip | Type | SHA-256 | Android Downloads file |','|---|---|---|---|']
  for x in copied:report.append('| '+x['clip']+' | '+x['kind']+' | `'+x['sha256Readback']+'` | `'+pathlib.Path(x['androidSharedPath']).name+'` |')
  report.extend(['','## Publication boundaries','',
   'Source files and evidence committed through Termux Git; exact remote revision verified. No new canonical or alternate deployed GLB. These are diagnostic review artifacts outside the repo, pending owner inspection.',''])
  work=root/'work';work.mkdir()
  (work/'RECOVERY_REPORT.md').write_text('\n'.join(report))
  evidence={'schema':'obsidianti-mwni-review-recovery-v1.4.3','campaign':V,'originalRunId':PREV_RUN,
   'priorSourceCommit':PRIOR_SOURCE_COMMIT,'priorEvidenceCommit':PRIOR_EVIDENCE_COMMIT,
   'resultsSHA256':PRIOR_RESULTS_SHA,'canonGLBSHA256':CANONICAL_SHA,'sourceCommit':record['sourceCommit'],
   'files':copied,'lockedBefore':locked,'lockedAfter':{n:gtext(repo,'rev-parse','HEAD:'+n) for n in LOCKED},
   'canonicalModified':False,'originalBlendModified':False,'ownerVisualAcceptance':'PENDING',
   'reportSHA256':sha(work/'RECOVERY_REPORT.md'),'authorRules':{'agentsBlob':AGENTS_BLOB,'etiquetteRead':'2026-11-06 live'}}
  if evidence['lockedAfter']!=locked:raise RuntimeError('PROTECTED_MODEL_TREE_CHANGED')
  (work/'RECOVERY_RECEIPT.json').write_text(json.dumps(evidence,indent=2)+'\n')
  for dst,name in EVIDENCE.items():durable_copy(work/name,repo/dst,sha(work/name))
  git(repo,'add','--',*sorted(EVIDENCE));staged=set(gtext(repo,'diff','--cached','--name-only').splitlines())
  if staged!=set(EVIDENCE):raise RuntimeError('EVIDENCE_STAGING_ALLOWLIST_FAILURE')
  git(repo,'commit','-m','Obsidianti: publish recovered Mwni candidate hashes and Android delivery receipts')
  record['evidenceCommit']=publish(repo,'EVIDENCE')
  for path,name in EVIDENCE.items():
   if git(repo,'show','HEAD:'+path).stdout!=(work/name).read_text():raise RuntimeError('REMOTE_EVIDENCE_BYTES_MISMATCH '+path)
  if {n:gtext(repo,'rev-parse','HEAD:'+n) for n in LOCKED}!=locked:raise RuntimeError('LOCKED_MODEL_CHANGED')
  for name in EVIDENCE.values():
   dest=downloads/(V+'_'+PREV_RUN+'_'+name)
   state=durable_copy(work/name,dest,sha(work/name))
   print('DOWNLOAD_EVIDENCE='+str(dest)+' STATE='+state,flush=True)
  record.update({'status':'RECOVERED_FOUR_REVIEW_FILES_GIT_REMOTE_VERIFIED','recovered':copied,
     'canonicalModified':False,'evidenceReadback':record['evidenceCommit']});save()
  print('REPORT_URL=https://github.com/Valar05/parametric-parambulator/blob/'+record['evidenceCommit']+'/'+DIR+'/RECOVERY_REPORT.md',flush=True)
  print('SOURCE_COMMIT='+record['sourceCommit'],flush=True)
  print('RESEARCH_COMMIT='+record['evidenceCommit'],flush=True)
  print('CANDIDATE_FILES_SHA_VERIFIED='+str(len(copied)),flush=True)
  print('CANONICAL_MODEL_UNCHANGED=YES',flush=True)
  print('STATUS='+record['status'],flush=True)
 except Exception as exc:
  record['status']='BLOCKED';record['error']=str(exc);record['traceback']=traceback.format_exc()[-4500:];save()
  print('STATUS=BLOCKED '+str(exc),flush=True)
  raise
 finally:
  save();print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('Usage: driver.py PACKET_ROOT LAUNCHER_PATH LAUNCHER_SHA256')
 main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve(),sys.argv[3])
