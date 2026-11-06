#!/usr/bin/env python3
"""Termux Git only; restore pre-contact FK, Ares-scale pelvis, publish review ONLY."""
import datetime,hashlib,json,os,pathlib,re,shutil,subprocess,sys,time,traceback,uuid,zipfile
V='OBSIDIANTI_ARES_FK_REBASE_v1.0.1'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
MEASURE_COMMIT='e107240e16a91538948dcbf67176c4e31d00ad5a' # source known at prior measurement run, not necessarily final results commit
MEASURE_RESULT='diagnostics/obsidianti/motion-measurement-v1.0.1/MEASUREMENT_SUMMARY.json'
CANONICAL='assets/obsidianti/Obsidianti.glb'
PREFK_ANCHOR='campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py'
FILES={'campaigns/OBSIDIANTI_ARES_FK_REBASE_RUN_v1.0.1.py':'driver.py',
 'campaigns/OBSIDIANTI_ARES_FK_REBASE_APPLY_v1.0.1.py':'rebase.py',
 'docs/obsidianti/ARES_FK_REBASE_v1.0.1.md':'doc.md'}
DEST='diagnostics/obsidianti/ares-fk-rebase-v1.0.1'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def command(args,timeout=400,check=True,env=None,stdin=None):
 p=subprocess.run([str(x) for x in args],input=stdin,text=True,capture_output=True,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+repr([str(x) for x in args[:6]])+' exit='+str(p.returncode)+' '+p.stderr[-1100:]+' '+p.stdout[-700:])
 return p
def git(repo,*args,**kw):return command(['git','-C',repo,*args],**kw)
def git_lfs_pointer(contents):
 m=re.fullmatch(r'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n?',contents)
 if not m:raise RuntimeError('HISTORIC_LFS_POINTER_UNRECOGNIZED')
 return m.group(1),int(m.group(2))
def history_source(repo,work,env):
 # Anchor is the initial addition of pre-contact pelvis/weapon repair source,
 # predating v1.3 contact IK. No version selected by arbitrary nearby hash.
 commits=git(repo,'log','--diff-filter=A','--format=%H','--',PREFK_ANCHOR).stdout.splitlines()
 if len(commits)!=1:raise RuntimeError('PREIK_ANCHOR_NOT_UNIQUE '+repr(commits))
 anchor=commits[0]
 msg=git(repo,'log','-1','--format=%s',anchor).stdout.strip()
 pointer=git(repo,'show',anchor+':'+CANONICAL).stdout
 oid,size=git_lfs_pointer(pointer)
 # The anchor must predate contact-IK source in the same Git history.
 # This verifies provenance chronologically, not physical validity.
 if not (20_000<size<200_000_000):raise RuntimeError('HISTORIC_FK_SIZE_UNEXPECTED')
 glb=work/'historical-precontact-FK.glb'
 object_path=repo/'.git/lfs/objects'/oid[:2]/oid[2:4]/oid
 if not object_path.is_file():
  # Git LFS fetch does NOT support --object-id. Fetch the exact historical
  # commit ref with an include filter for the canonical model path.
  # The commit has already been recovered from the authenticated Git history.
  p=command(['git','-C',repo,'lfs','fetch','origin',anchor,
             '--include='+CANONICAL,'--exclude='],timeout=1200,check=False,env=env)
  if p.returncode:raise RuntimeError('HISTORIC_FK_LFS_NOT_FETCHABLE anchor='+anchor+' '+(p.stderr+p.stdout)[-1400:])
 if not object_path.is_file():raise RuntimeError('HISTORIC_FK_LFS_OBJECT_ABSENT_AFTER_FETCH')
 if object_path.stat().st_size!=size or sha(object_path)!=oid:raise RuntimeError('HISTORIC_FK_LFS_HASH_BAD')
 shutil.copyfile(object_path,glb)
 import struct
 raw=glb.read_bytes();n=struct.unpack_from('<I',raw,12)[0]
 j=json.loads(raw[20:20+n]);names=[a['name'] for a in j.get('animations',[])]
 expected=['Lionheart_'+x for x in ('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')]
 if len(names)!=23 or any(k not in names for k in expected):raise RuntimeError('HISTORIC_SOURCE_NOT_FULL_FK_LIBRARY '+repr(names))
 return glb,{'anchorCommit':anchor,'anchorMessage':msg,'lfsOID':oid,'size':size,'animationNames':names}
def main(packet,scriptsha):
 home=pathlib.Path.home();downloads=home/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('ANDROID_DOWNLOADS_MISSING')
 run=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 root=home/'.local/state'/V/run;root.mkdir(parents=True)
 repo=root/'repo';work=root/'work';work.mkdir();logs=work/'logs';logs.mkdir()
 receipt=downloads/(V+'_'+run+'_RECEIPT.json');handoff=downloads/(V+'_'+run+'_HANDOFF.zip')
 state={'campaign':V,'run':run,'launcherSHA256':scriptsha,'authority':'TERMUX_GIT_ONLY',
  'rules':{'agentsBlobSHA':AGENTS_BLOB,'liveCampaignEtiquetteReadByAuthor':'2026-11-05'},
  'status':'STARTED','phase':'BOOT','canonicalGLBMutated':False,'otherAnimationsMutated':False,
  'approved':'NO_REVIEW_ONLY','modelSource':'HISTORIC_PRECONTACT_FK'}
 def save():receipt.write_text(json.dumps(state,indent=2,sort_keys=True)+'\n')
 print('CAMPAIGN='+V+' SHA='+scriptsha+' AUTHORITY=TERMUX_GIT_ONLY',flush=True)
 print('MISSION=RESTORE_PRECONTACT_FK_PLUS_ARES_PELVIS_SCALING; CANONICAL_GLB_UNCHANGED',flush=True)
 save()
 try:
  env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
  state['phase']='GIT_HISTORY_AND_RULES';save()
  print('CLONING_AUTHENTICATED_GIT_HISTORY',flush=True)
  command(['git','clone','--depth=160','--single-branch','--branch','main',REMOTE,repo],timeout=900,env=env)
  if not git(repo,'log','--diff-filter=A','--format=%H','--',PREFK_ANCHOR).stdout.strip():
   print('RECOVERING_DEEPER_HISTORY',flush=True)
   command(['git','-C',repo,'fetch','--unshallow','origin','main'],timeout=1100,env=env)
  head=git(repo,'rev-parse','HEAD').stdout.strip();state['startingHEAD']=head
  if git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()!=AGENTS_BLOB:raise RuntimeError('AGENTS_BLOB_CHANGED_REQUIRES_FRESH_RULE_READ')
  if 'Campaign Etiquette' not in (repo/'AGENTS.md').read_text():raise RuntimeError('RULES_REFERENCE_MISSING')
  if command(['git','lfs','version'],check=False).returncode:raise RuntimeError('GIT_LFS_NOT_INSTALLED')
  for path in [*FILES,DEST+'/RESULT.json',DEST+'/RESULT.md',DEST+'/UNAPPROVED_CANDIDATE.zip']:
   if git(repo,'ls-tree','-r','HEAD','--',path).stdout.strip() or (repo/path).exists():raise RuntimeError('VERSIONED_PATH_ALREADY_EXISTS '+path)
  state['phase']='FIND_PRECONTACT_FK';save()
  source,meta=history_source(repo,work,env);state['historicalSource']=meta;save()
  print('HISTORICAL_PRECONTACT_FK='+meta['anchorCommit']+' SHA256='+meta['lfsOID'],flush=True)
  state['phase']='READ_VERIFIED_MEASUREMENTS';save()
  mpath=repo/MEASURE_RESULT
  if not mpath.is_file():raise RuntimeError('PUBLISHED_MEASUREMENT_SUMMARY_NOT_FOUND '+MEASURE_RESULT)
  mj=json.loads(mpath.read_text())
  if mj.get('schema')!='obsidianti-motion-measurement-v1' or mj.get('authority')!='READ_ONLY_BOTH_REAL_ASSETS':raise RuntimeError('MEASUREMENT_PROVENANCE_MISMATCH')
  state['measurementSummarySHA256']=sha(mpath);save()
  state['phase']='GENERATE_REVIEW_CANDIDATE';save()
  candidate=work/'AresScaled_PreContactFK_UNAPPROVED.glb';result=work/'RESULT.json'
  p=command(['python3',packet/'rebase.py',source,candidate,result,mpath],timeout=240,check=False)
  (logs/'rebase.log').write_text(p.stdout+'\n'+p.stderr)
  if p.returncode or not candidate.is_file() or not result.is_file():raise RuntimeError('ARES_REBASE_FAILED '+p.stderr[-1000:])
  data=json.loads(result.read_text())
  if data['sourceSha256']!=meta['lfsOID'] or data['candidateSha256']!=sha(candidate):raise RuntimeError('REBASE_ARTIFACT_PROVENANCE_WRONG')
  state['candidateSHA256']=sha(candidate)
  print('REVIEW_CANDIDATE_SHA256='+sha(candidate)+' SCALE='+str(data['scaleApplied']),flush=True)
  state['phase']='HOST_REVIEW_SAFETY_REPORT';save()
  markdown=work/'RESULT.md'
  markdown.write_text('# Obsidianti pre-contact FK + Ares-style pelvis scale\n\n'
   'Status: **UNAPPROVED candidate; canonical model unchanged.**\n\n'
   'Source historical commit: `'+meta['anchorCommit']+'`\n\n'
   'Source LFS SHA: `'+meta['lfsOID']+'`\n\n'
   'Candidate SHA: `'+sha(candidate)+'`\n\n'
   'Scale = mean(left,right) anatomical leg ratios = '+str(data['scaleApplied'])+'\n\n'
   'All ten Lionheart action pelvis translation tracks scaled around preserved idle. '
   'All rotations, weapon tracks, Ares clips, Walking/Running, geometry and skin unchanged.\n\n'
   'This does NOT solve physical foot contact; it reverts the contact-IK code path and tests the old FK architecture with Ares scaling. '
   'Inspect visual playback and skinned sole floor before considering canonical publication.\n')
  # Preserve the actual candidate in durable Git LFS evidence, not only phone storage.
  archive=work/'UNAPPROVED_CANDIDATE.zip'
  with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_STORED) as z:
   z.write(candidate,'AresScaled_PreContactFK_UNAPPROVED.glb')
   z.write(result,'RESULT.json')
  state['archiveSHA256']=sha(archive)
  state['phase']='PUBLISH_SOURCE_AND_DIAGNOSTICS_TO_GIT';save()
  for dest,src in FILES.items():
   path=repo/dest;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(packet/src,path)
  git(repo,'add','--',*FILES)
  if set(git(repo,'diff','--cached','--name-only').stdout.splitlines())!=set(FILES):raise RuntimeError('GIT_STAGING_SCOPE_BAD')
  if not git(repo,'config','--get','user.name',check=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Campaign')
  if not git(repo,'config','--get','user.email',check=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')
  git(repo,'commit','-m','Obsidianti: precontact FK plus Ares pelvis-scale review v1.0.1')
  report_dest={DEST+'/RESULT.json':result,DEST+'/RESULT.md':markdown,DEST+'/UNAPPROVED_CANDIDATE.zip':archive}
  for name,path in report_dest.items():
   p=repo/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,p)
  git(repo,'add','--',*report_dest)
  if set(git(repo,'diff','--cached','--name-only').stdout.splitlines())!=set(report_dest):raise RuntimeError('GIT_RESULT_SCOPE_BAD')
  git(repo,'commit','-m','Obsidianti: preserved FK Ares-scale review SHA evidence')
  final=git(repo,'rev-parse','HEAD').stdout.strip();state['sourceEvidenceCommit']=final;save()
  command(['git','-C',repo,'push','origin','HEAD:refs/heads/main'],timeout=900,env=env)
  remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]
  if remote!=final:raise RuntimeError('GIT_REMOTE_HEAD_MISMATCH')
  for name,path in report_dest.items():
   rb=git(repo,'show',final+':'+name).stdout
   if name.endswith('.zip'):
    if 'oid sha256:'+sha(path) not in rb:raise RuntimeError('GIT_LFS_POINTER_READBACK_MISMATCH '+name)
   elif hashlib.sha256(rb.encode()).hexdigest()!=sha(path):raise RuntimeError('GIT_RESULT_READBACK_MISMATCH '+name)
  state['remoteReadbackVerified']=True
  state['phase']='PUBLISH_PHONE_DOWNLOADS';save()
  for suffix,path in [('UNAPPROVED.glb',candidate),('REPORT.md',markdown),('RESULT.json',result),('CANDIDATE.zip',archive)]:
   out=downloads/(V+'_'+run+'_'+suffix)
   if out.exists():raise RuntimeError('PUBLIC_PATH_COLLISION '+str(out))
   shutil.copyfile(path,out)
   if sha(out)!=sha(path):raise RuntimeError('PUBLIC_SHA_READBACK_FAILED '+suffix)
   state.setdefault('public',{})[suffix]={'path':str(out),'sha256':sha(out)}
   if shutil.which('termux-media-scan'):command(['termux-media-scan',out],timeout=40,check=False)
  if sha(source)!=meta['lfsOID']:raise RuntimeError('SOURCE_ALTERED')
  state['phase']='COMPLETE';state['status']='UNAPPROVED_ARES_METHOD_FK_CANDIDATE_PUBLISHED_TO_PHONE_AND_SOURCE_READBACK';save()
  print('STATUS='+state['status']+' CANONICAL_GLB_UNCHANGED=YES',flush=True)
  print('GIT_RESULT_COMMIT='+final,flush=True)
  for k,v in state.get('public',{}).items():print(k+'='+v['path']+' SHA256='+v['sha256'],flush=True)
 except Exception as e:
  state['status']='BLOCKED';state['error']=type(e).__name__+': '+str(e);save()
  print('BLOCKED='+state['error'],flush=True);traceback.print_exc();raise
 finally:
  save()
  with zipfile.ZipFile(handoff,'x',compression=zipfile.ZIP_DEFLATED) as z:
   z.write(receipt,'receipt.json')
   for p in logs.glob('*.log'):z.write(p,'logs/'+p.name)
   for name in ('RESULT.json','RESULT.md'):
    p=work/name
    if p.exists():z.write(p,'results/'+name)
  print('RECEIPT='+str(receipt)+'\nHANDOFF='+str(handoff)+'\nHANDOFF_SHA256='+sha(handoff),flush=True)
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('USAGE DRIVER PACKET LAUNCHER_SHA')
 main(pathlib.Path(sys.argv[1]),sys.argv[2])
