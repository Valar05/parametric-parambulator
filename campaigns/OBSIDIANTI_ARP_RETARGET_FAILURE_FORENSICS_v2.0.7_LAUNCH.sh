#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
V=OBSIDIANTI_ARP_RETARGET_FAILURE_FORENSICS_v2.0.7
SELF="$(realpath "$0")"
SELF_SHA="$(sha256sum "$SELF" | cut -d' ' -f1)"
echo "CAMPAIGN=$V"
echo 'AUTHORITY=TERMUX_GIT_ONLY'
echo "LAUNCHER_SHA256=$SELF_SHA"
if [ -z "${PREFIX:-}" ] || [ ! -x "$PREFIX/bin/bash" ]; then echo 'BLOCKED: Termux required'; exit 2; fi
"$PREFIX/bin/python3" - "$SELF" "$SELF_SHA" <<'END_PYTHON'
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,re,shutil,subprocess,sys,time,uuid,traceback
V='OBSIDIANTI_ARP_RETARGET_FAILURE_FORENSICS_v2.0.7'
PREV='OBSIDIANTI_ARP_FIRST_LIVE_v2.0.5'
PREVID='20261106T235842Z-73d0582a'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE='ccec23b752bd677bbc26e4bb3df73ffd25386944'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
LION='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
ARES='63b6e7a7250cfb03e49cf0d335101d808126ae926894d74c1b2a6a49936b8b2a'
ARP='2b377bbc5d81dfcef4209971e332a8bcb402ed44605e5ed0cddc2e90fafebf28'
LOCKED=('assets/obsidianti/Obsidianti.glb','assets/repl/Repl.glb')
SRC='campaigns/'+V+'_LAUNCH.sh'
DIAG='diagnostics/obsidianti/arp-retarget-failure-forensics-v2.0.7/runs/'
SELF=pathlib.Path(sys.argv[1]);SELF_SHA=sys.argv[2]

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for part in iter(lambda:f.read(1048576),b''):h.update(part)
 return h.hexdigest()

def command(argv,timeout=240,check=True,env=None):
 p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED rc='+str(p.returncode)+' '+repr(argv[:5])+' '+p.stderr[-700:])
 return p

def git(repo,*args,check=True,timeout=240):return command(['git','-C',repo,*args],check=check,timeout=timeout)
def g(repo,*args):return git(repo,*args).stdout.strip()

def copy_new(src,dst):
 src=pathlib.Path(src);dst=pathlib.Path(dst)
 if not src.is_file() or src.is_symlink():raise RuntimeError('NONREGULAR_SOURCE '+str(src))
 if dst.exists():raise RuntimeError('NO_OVERWRITE_DESTINATION_COLLISION '+str(dst))
 dst.parent.mkdir(parents=True,exist_ok=True)
 tmp=dst.with_name('.'+dst.name+'.'+uuid.uuid4().hex[:8]+'.tmp')
 try:
  shutil.copyfile(src,tmp)
  if sha(tmp)!=sha(src):raise RuntimeError('FILE_COPY_SHA_MISMATCH '+str(dst))
  os.replace(tmp,dst)
 finally:
  if tmp.exists():tmp.unlink()

def classify(lines):
 lower='\n'.join(lines).lower()
 return {'segfaultOrFatal':any(x in lower for x in ('segmentation fault','core dumped','fatal python error','blender crashed')),
  'tracebackPresent':'traceback (most recent call last)' in lower,
  'retargetMentioned':'retarget' in lower,
  'missingSourceAction':'source action' in lower and any(x in lower for x in ('missing','not found')),
  'warningOrError':any(x in lower for x in ('warning','error','exception')),
  'silentExitSuspected':not any(x in lower for x in ('traceback (most recent call last)','fatal python error','segmentation fault','core dumped','blender crashed'))}

def local_log_evidence():
 prev=pathlib.Path.home()/'.local/state'/PREV/PREVID
 receipt=prev/'RECEIPT.json'
 if not receipt.is_file():raise RuntimeError('EXACT_PRIOR_RECEIPT_MISSING '+str(receipt))
 state=json.loads(receipt.read_text())
 if state.get('runId')!=PREVID or state.get('canonicalGLBSHA256')!=CANON or state.get('vendorZIPsha256')!=ARP:
  raise RuntimeError('PRIOR_RECEIPT_IDENTITY_INVALID')
 rows=[]
 for clip,expected in (('AxeKick',ARES),('Heavy1',LION)):
  root=prev/'work'/clip
  trial=root/'trial/TRIAL.json';log=root/'BLENDER.log'
  if not trial.is_file() or not log.is_file():raise RuntimeError('ORIGINAL_TRIAL_OR_BLENDER_LOG_MISSING '+clip)
  t=json.loads(trial.read_text())
  if t.get('inputSHA256')!={'source':expected,'target':CANON}:raise RuntimeError('PRIOR_TRIAL_INPUT_SHA_MISMATCH '+clip)
  if t.get('status')!='BOOT':raise RuntimeError('PRIOR_TRIAL_STATUS_CHANGED '+clip+' '+str(t.get('status')))
  lines=log.read_text(errors='replace').splitlines()
  markers=classify(lines)
  # Only derive log metadata for public Git; original full log is private, stays in Termux.
  row={'clip':clip,'sourceSHA256':expected,'trialSHA256':sha(trial),'trialStatus':t['status'],
       'mappedBones':t.get('mapping',{}).get('boneCount'),'targetAction':t.get('targetAction'),
       'sourceAnimatedLimbGroups':t.get('sourceMotion',{}).get('animatedLimbGroups',{}),
       'logSHA256':sha(log),'logByteCount':log.stat().st_size,'logLineCount':len(lines),
       'logFlags':markers,'frameCount':len(list((root/'trial').rglob('frame_*.png'))),
       'editableBlenderExists':any((root/'trial').rglob('ARP_*_UNAPPROVED.blend')),
       'retargetOutcome':'UNVERIFIED'}
  rows.append(row)
  print('CLIP='+clip+' STATUS=BOOT MAPPED_BONES='+str(row['mappedBones'])+' LOG_SHA256='+row['logSHA256'],flush=True)
  print('LOG_FLAGS='+json.dumps(markers,sort_keys=True),flush=True)
  print('PRIVATE_LOG_LAST_45_LINES_'+clip+'=BEGIN',flush=True)
  print('\n'.join(lines[-45:]),flush=True)
  print('PRIVATE_LOG_LAST_45_LINES_'+clip+'=END',flush=True)
 return rows

def publish(root,rows):
 repo=root/'repo'
 env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
 command(['git','clone','--quiet','--depth=1','--single-branch','--branch=main',REMOTE,repo],timeout=480,env=env)
 if g(repo,'remote','get-url','origin').removesuffix('.git')!=REMOTE.removesuffix('.git'):raise RuntimeError('WRONG_REMOTE')
 head=g(repo,'rev-parse','HEAD')
 if head!=BASE and git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False).returncode:
  git(repo,'fetch','--no-tags','--depth=150','origin',BASE,timeout=200)
  if git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False).returncode:raise RuntimeError('SOURCE_COMMIT_NOT_ANCESTOR')
 if g(repo,'rev-parse','HEAD:AGENTS.md')!=AGENTS:raise RuntimeError('AGENTS_RULES_SHA_CHANGED')
 if 'oid sha256:'+CANON not in g(repo,'show','HEAD:'+LOCKED[0]):raise RuntimeError('CANONICAL_LFS_POINTER_CHANGED')
 if g(repo,'status','--porcelain'):raise RuntimeError('ISOLATED_CLONE_DIRTY')
 locked={p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}
 out=DIAG+root.name
 paths={SRC:SELF,out+'/EVIDENCE.json':root/'EVIDENCE.json',out+'/REPORT.md':root/'REPORT.md'}
 evidence={'campaign':V,'runId':root.name,'sourceCommit':head,'agentsBlob':AGENTS,
  'sourceTermuxRun':PREVID,'canonicalModelSHA256':CANON,'privateVendorZIPSHA256':ARP,
  'clips':rows,'status':'ACTUAL_PRIOR_BLENDER_LOGS_CLASSIFIED_RETARGET_UNVERIFIED',
  'ownerAcceptance':'PENDING','canonicalModified':False,'vendorSourcePublished':False}
 paths[out+'/EVIDENCE.json'].write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
 paths[out+'/REPORT.md'].write_text('# ARP original Blender retarget failures\n\n'
  +'Evidence from the exact v2.0.5 source Blender logs, not hypothetical replays.\n\n'
  +'\n'.join('- '+r['clip']+': '+str(r['logLineCount'])+' logged lines; mapped '+str(r['mappedBones'])
    +' bones; no completed retarget; flags '+str(r['logFlags']) for r in rows)
  +'\n\nOriginal logs and proprietary addon source remain private on the phone. No model modifications.\n')
 for dest in paths:
  if (repo/dest).exists():raise RuntimeError('VERSIONED_SOURCE_OR_EVIDENCE_COLLISION '+dest)
 for dest,file in paths.items():copy_new(file,repo/dest)
 git(repo,'add','--',*sorted(paths))
 if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(paths):raise RuntimeError('STAGING_ALLOWLIST_FAILED')
 if git(repo,'config','user.name',check=False).returncode:git(repo,'config','user.name','Termux ARP Forensics')
 if git(repo,'config','user.email',check=False).returncode:git(repo,'config','user.email','termux-arp-forensics@users.noreply.github.com')
 git(repo,'commit','-m','Obsidianti: diagnose genuine ARP retarget noncompletion from private Blender logs')
 commit=g(repo,'rev-parse','HEAD')
 for attempt in range(3):
  p=git(repo,'push','origin','HEAD:refs/heads/main',timeout=320,check=False)
  if not p.returncode:break
  if attempt==2:raise RuntimeError('REMOTE_PUSH_FAILED '+p.stderr[-900:])
  time.sleep(attempt+1)
 remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()
 if not remote or remote[0]!=commit:raise RuntimeError('REMOTE_COMMIT_READBACK_DIFFERED')
 git(repo,'fetch','--quiet','origin','main')
 if g(repo,'rev-parse','refs/remotes/origin/main')!=commit:raise RuntimeError('FETCHED_REMOTE_NOT_IDENTICAL')
 for dest,file in paths.items():
  b=subprocess.run(['git','-C',str(repo),'cat-file','blob','refs/remotes/origin/main:'+dest],capture_output=True,check=True).stdout
  if hashlib.sha256(b).hexdigest()!=sha(file):raise RuntimeError('REMOTE_BLOB_SHA_MISMATCH '+dest)
 if {p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}!=locked:raise RuntimeError('CANONICAL_GIT_POINTER_CHANGED')
 return head,commit,'https://github.com/Valar05/parametric-parambulator/blob/'+commit+'/'+out+'/EVIDENCE.json'

def main():
 if sha(SELF)!=SELF_SHA:raise RuntimeError('LAUNCHER_SHA_CHANGED')
 if not (pathlib.Path.home()/'storage/downloads').is_dir():raise RuntimeError('TERMUX_DOWNLOADS_NOT_MOUNTED')
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
 rec=root/'RECEIPT.json';state={'campaign':V,'runId':runid,'status':'BOOT','launcherSHA256':SELF_SHA,
  'authority':'TERMUX_GIT_ONLY','gitRulesBlob':AGENTS,'vendorZIPSHA256':ARP,
  'canonicalModelSHA256':CANON,'canonicalModified':False}
 def save():
  temp=rec.with_suffix('.tmp');temp.write_text(json.dumps(state,indent=2)+'\n');os.replace(temp,rec)
 save()
 try:
  rows=local_log_evidence();state['status']='ACTUAL_LOCAL_LOGS_CLASSIFIED';save()
  head,commit,url=publish(root,rows)
  state.update({'gitInputHEAD':head,'evidenceCommit':commit,'status':'ACTUAL_LOG_DIAGNOSTICS_GIT_REMOTE_VERIFIED'});save()
  print('EVIDENCE_URL='+url,flush=True)
  print('CANONICAL_MODEL_UNCHANGED=YES',flush=True)
  print('STATUS='+state['status'],flush=True)
 except Exception as exc:
  state.update({'status':'BLOCKED','errorType':type(exc).__name__,'error':str(exc)[:650]});save()
  print('STATUS=BLOCKED '+type(exc).__name__+' '+str(exc)[:650],flush=True)
  raise
 finally:
  save();print('RECEIPT='+str(rec),flush=True)
main()
END_PYTHON
