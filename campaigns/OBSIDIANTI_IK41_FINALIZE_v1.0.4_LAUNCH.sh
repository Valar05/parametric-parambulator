#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
CAMPAIGN_LAUNCHER="$(realpath "$0")"
CAMPAIGN_LAUNCHER_SHA256="$(sha256sum "$CAMPAIGN_LAUNCHER" | awk '{print $1}')"
export CAMPAIGN_LAUNCHER CAMPAIGN_LAUNCHER_SHA256
printf 'CAMPAIGN=OBSIDIANTI_IK41_FINALIZE_v1.0.4\nAUTHORITY=ISOLATED_TERMUX_GIT_ONLY\nENTRY=%s\nENTRY_SHA256=%s\n' "$CAMPAIGN_LAUNCHER" "$CAMPAIGN_LAUNCHER_SHA256"
python3 - <<'PY_CAMPAIGN'
from __future__ import annotations
import os,sys,pathlib,hashlib,json,shutil,subprocess,datetime,traceback,zipfile,math
VERSION='OBSIDIANTI_IK41_FINALIZE_v1.0.4'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
OLD_VERIFY_BLOB='cf398104ef5d24104adf35404ec7e94282d86052'
PREVIOUS_HEAD='7a8f020835b32f71c98dd5adaf7394712dee66c4'
SOURCE='assets/obsidianti/source/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_UNAPPROVED.blend'
SOURCE_SHA='30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27'
OUTPUT='assets/obsidianti/source/OBSIDIANTI_IK41_EDITABLE_v1.0.3_UNAPPROVED.blend'
OUTPUT_SHA='30ad2518a820e6b1770dcced6a46f1f2f91db28af799c60dfa21ab3488cda75e'
PREVIOUS_VERSION='OBSIDIANTI_IK41_FK_ACTION_RESTORE_v1.0.3'
PREVIOUS_RUN='20261109T112207Z-22830'
AUTHOR_VERSION='OBSIDIANTI_FK_TO_IK_41_v1.0.1'
AUTHOR_RUN='20261109T031136Z-9060'
OLD_VERIFY='campaigns/'+PREVIOUS_VERSION+'_verify.py'
NEW_VERIFY='campaigns/'+VERSION+'_verify.py'
DOC='docs/obsidianti/'+VERSION+'.md'
CONTRACT='campaigns/'+VERSION+'.contract.json'
NEW_LAUNCH='campaigns/'+VERSION+'_LAUNCH.sh'
ENTRY=pathlib.Path(os.environ['CAMPAIGN_LAUNCHER']).resolve()
HOME=pathlib.Path.home(); DOWNLOADS=HOME/'storage/downloads';DOWNLOADS.mkdir(parents=True,exist_ok=True)
RUN=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid())
STATE=HOME/'.local/state'/VERSION/RUN;STATE.mkdir(parents=True,exist_ok=False)
RECEIPT=STATE/'RECEIPT.json'; VERIFY_REPORT=STATE/'BLENDER_REOPEN.json'
receipt={'campaign':VERSION,'status':'STARTED','stage':'BOOT','run':RUN,'authority':'ISOLATED_TERMUX_GIT_ONLY','launcherSHA256':os.environ['CAMPAIGN_LAUNCHER_SHA256'], 'rulesAGENTSblob':AGENTS_BLOB,'rulesCampaignEtiquette':'Home Center document 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI read in this campaign authoring turn','candidateSHA256':OUTPUT_SHA,'fkSourceSHA256':SOURCE_SHA,'ownerVisualAcceptance':'PENDING'}
def save():RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
def stage(s):receipt['stage']=s;save();print('STAGE='+s,flush=True)
def need(test,error):
 if not test:raise RuntimeError(error)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for part in iter(lambda:f.read(1<<20),b''):h.update(part)
 return h.hexdigest()
def call(args,timeout=900,env=None,check=True):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,errors='replace',stdin=subprocess.DEVNULL,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED_'+repr(list(map(str,args[:6])))+'_'+p.stderr[-1200:]+'_'+p.stdout[-500:])
 return p
def git(root,*args,**kw):return call(['git','-C',str(root),*args],**kw)
def remote_readback(root):
 git(root,'config','lfs.concurrenttransfers','1')
 env=os.environ.copy();env.update(GOMEMLIMIT='200MiB',GOGC='25')
 result=call(['git','-C',str(root),'push','origin','HEAD:refs/heads/main'],timeout=1900,check=False,env=env)
 need(result.returncode==0,'TERMUX_GIT_PUSH_FAILED_'+result.stderr[-1400:])
 local=git(root,'rev-parse','HEAD').stdout.strip()
 remote=call(['git','ls-remote',REMOTE,'refs/heads/main']).stdout.split()[0]
 need(remote==local,'REMOTE_GIT_HEAD_MISMATCH_'+local+'_'+remote)
 receipt['remoteHEAD']=remote;save();print('REMOTE_HEAD_VERIFIED='+remote,flush=True)
 return remote
def blender(root,script,args):
 native=shutil.which('blender')
 if native:return [native,'--background','--factory-startup','--disable-autoexec','--python',str(root/script),'--',*map(str,args)]
 pd=shutil.which('proot-distro');need(pd,'NO_BLENDER_RUNTIME')
 for distro in ('obs-arp-blender50','debian'):
  if call([pd,'login',distro,'--','blender','--version'],timeout=90,check=False).returncode==0:
   def remap(path):
    path=pathlib.Path(path).resolve()
    for rootpath,prefix in ((root.resolve(),'/mnt/obs-repo'),(STATE.resolve(),'/mnt/obs-work')):
     if path.is_relative_to(rootpath):return prefix+'/'+str(path.relative_to(rootpath))
    raise RuntimeError('BLENDER_UNMAPPED_PATH_'+str(path))
   return [pd,'login',distro,'--bind',str(root.resolve())+':/mnt/obs-repo','--bind',str(STATE.resolve())+':/mnt/obs-work','--','blender','--background','--factory-startup','--disable-autoexec','--python',remap(root/script),'--',*[remap(a) for a in args]]
 raise RuntimeError('BLENDER_5_NOT_AVAILABLE')
def copyverify(src,dst,expected):
 need(src.is_file() and sha(src)==expected,'SOURCE_HASH_MISMATCH_'+str(src))
 need(not dst.exists(),'OUTPUT_COLLISION_'+str(dst))
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 need(sha(dst)==expected,'COPIED_BYTES_MISMATCH')
def publish_logs():
 for p in (RECEIPT,VERIFY_REPORT,STATE/'BLENDER_REOPEN.log'):
  if p.exists():shutil.copyfile(p,DOWNLOADS/(VERSION+'_'+RUN+'_'+p.name))
 def pack():
  filename=DOWNLOADS/(VERSION+'_'+RUN+'_DIAGNOSTICS.zip')
  with zipfile.ZipFile(filename,'w',zipfile.ZIP_DEFLATED) as z:
   for p in (RECEIPT,VERIFY_REPORT,STATE/'BLENDER_REOPEN.log'):
    if p.exists():z.write(p,p.name)
  print('DIAGNOSTICS='+str(filename),flush=True)
 pack()
def patched_verifier(old):
 anchor='  for t in sorted(set((times[0],times[len(times)//2],times[-1]))):'
 need(old.count(anchor)==1,'VERIFIER_SAMPLING_ANCHOR_NOT_UNIQUE')
 old=old.replace(anchor,"  sample_times=sorted(set((times[0],times[len(times)//2],times[-1])))\n  expected_samples+=len(sample_times)\n  for t in sample_times:")
 start=" worst={'ankleM':0.,'kneeM':0.,'footDeg':0.};tested=0"
 need(old.count(start)==1,'COUNTER_ANCHOR_INVALID')
 old=old.replace(start,start+';expected_samples=0')
 gate=" need(tested>=123,'REOPEN_POSES_NOT_123_'+str(tested))"
 need(old.count(gate)==1,'OLD_BAD_123_GATE_NOT_FOUND')
 old=old.replace(gate," result['expectedIKPoseSamples']=expected_samples;save()\n need(expected_samples==121,'PINNED_41_CLIP_SAMPLE_CENSUS_CHANGED_'+str(expected_samples))\n need(tested==expected_samples,'REOPEN_POSE_SAMPLE_COUNT_MISMATCH_'+str(tested)+'_'+str(expected_samples))")
 need('need(not problems,' in old and "need(worst[k]<=limits[k]" in old,'REQUIRED_STRICT_EVIDENCE_GATES_MISSING')
 compile(old,NEW_VERIFY,'exec')
 return old
try:
 save()
 need(shutil.which('git') and shutil.which('git-lfs') and shutil.which('python3'),'TERMUX_GIT_LFS_PYTHON_MISSING')
 need(sha(ENTRY)==receipt['launcherSHA256'],'LAUNCHER_ENTRY_CHANGED')
 stage('RECOVER_PINNED_VERIFIED_41_IK_BINARY_NO_REBUILD')
 prior=HOME/'.local/state'/PREVIOUS_VERSION/PREVIOUS_RUN
 candidate=prior/pathlib.Path(OUTPUT).name
 repair=prior/'RESTORE_REPORT.json'
 need(candidate.is_file() and sha(candidate)==OUTPUT_SHA,'V103_REPAIRED_BINARY_MISSING_OR_WRONG_HASH')
 need(repair.is_file(),'V103_REPAIR_RECEIPT_MISSING')
 repair_data=json.loads(repair.read_text())
 need(repair_data.get('status')=='RESTORED_ACTIONS_SAVED_UNAPPROVED' and repair_data.get('outputSHA256')==OUTPUT_SHA and repair_data.get('missingCount')==41 and repair_data.get('referenceActionCount')==82 and repair_data.get('ikActionCount')==41,'V103_REPAIR_NOT_VERIFIED')
 author_source=HOME/'.local/state'/AUTHOR_VERSION/AUTHOR_RUN/'BLENDER_AUTHOR.json'
 need(author_source.is_file(),'PREVIOUS_BLENDER_AUTHOR_AUDIT_MISSING')
 author=json.loads(author_source.read_text())
 need(author.get('status')=='IK41_NATIVE_BLEND_VERIFIED_POSE_PARITY_OWNER_VISUAL_PENDING' and author.get('ikActionCount')==41 and author.get('poseParity',{}).get('passed') is True,'IK41_AUTHOR_REPORT_INVALID')
 local=STATE/candidate.name;localrepair=STATE/'RESTORE_REPORT.json';localauthor=STATE/'BLENDER_AUTHOR.json'
 copyverify(candidate,local,OUTPUT_SHA);shutil.copyfile(repair,localrepair);shutil.copyfile(author_source,localauthor)
 stage('CLONE_FRESH_TERMUX_GIT_AND_PIN_ALL_AUTHORITIES')
 root=STATE/'repo';env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1'
 p=call(['git','clone','--depth','1','--single-branch','--branch','main','--filter=blob:none',REMOTE,str(root)],timeout=1000,env=env,check=False)
 if p.returncode:
  if root.exists():shutil.rmtree(root)
  call(['git','clone','--depth','1','--single-branch','--branch','main',REMOTE,str(root)],timeout=1000,env=env)
 need(not git(root,'status','--porcelain').stdout.strip(),'FRESH_GIT_NOT_CLEAN')
 receipt['sourceHEAD']=git(root,'rev-parse','HEAD').stdout.strip();save()
 need(git(root,'rev-parse','HEAD:AGENTS.md').stdout.strip()==AGENTS_BLOB,'AGENTS_BLOB_CHANGED_RULES_REVIEW_REQUIRED')
 need(git(root,'rev-parse','HEAD:'+OLD_VERIFY).stdout.strip()==OLD_VERIFY_BLOB,'PRIOR_VERIFIER_BLOB_CHANGED')
 need('oid sha256:'+SOURCE_SHA in git(root,'show','HEAD:'+SOURCE).stdout,'ORIGINAL_FK_SOURCE_LFS_POINTER_CHANGED')
 need(git(root,'cat-file','-e','HEAD:'+OUTPUT,check=False).returncode!=0,'OUTPUT_ALREADY_PUBLISHED_REFUSE_OVERWRITE')
 for path in (NEW_VERIFY,DOC,CONTRACT,NEW_LAUNCH,OUTPUT):
  need(git(root,'cat-file','-e','HEAD:'+path,check=False).returncode!=0 and not (root/path).exists(),'VERSIONED_DEST_COLLISION_'+path)
 old=git(root,'show','HEAD:'+OLD_VERIFY).stdout
 new=patched_verifier(old)
 stage('PUBLISH_PATCHED_VERIFICATION_SOURCE_USING_TERMUX_GIT')
 docs="""# Obsidianti IK41 final native reopen and publication v1.0.4

Authority: Termux Git only. No new IK generation, no animation rewrites.

Reuses exact v1.0.3 repaired candidate SHA256 30ad2518a820e6b1770dcced6a46f1f2f91db28af799c60dfa21ab3488cda75e, verified with original source SHA256 30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27. v1.0.3 reopened all 82 preserved original FK actions with 252,130 points and zero differences; all 41 IK actions were present, 121 sampled poses within limits (knee 0.003745m, ankle 0.000008924m). It failed ONLY because the verifier incorrectly required >=123 independent samples for 41 clips, two of which have fewer unique sample times. This patch preserves all substantive checks but computes and compares the expected unique sample count from actual action keyframes, and gates exact pinned 121 count. Neither the original .blend nor the generated IK candidate is modified.

Independent native Blender reopen must reproduce original FK curve metadata, handles, times, values, all 41 active IK chains, and pose tolerances. Then copy to Android Downloads, Git-LFS publish the existing versioned v1.0.3 output with remote HEAD and LFS pointer readback. Owner visual acceptance remains pending. No Sword1/two-handed integration.
"""
 filemap={NEW_VERIFY:new,DOC:docs,CONTRACT:json.dumps({'schema':VERSION,'authorizedExecution':'ISOLATED_TERMUX_GIT_ONLY','source':SOURCE,'sourceSHA256':SOURCE_SHA,'existingIKCandidateSHA256':OUTPUT_SHA,'output':OUTPUT,'originalFKActions':82,'IKClips':41,'expectedReopenPoseSamples':121,'originalAnimationCurveComparisonRequired':True,'noRebuild':True,'ownerVisualAcceptance':'PENDING'},indent=2)+'\n'}
 for dst,content in filemap.items():
  dest=root/dst;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(content)
 shutil.copyfile(ENTRY,root/NEW_LAUNCH)
 need(sha(root/NEW_LAUNCH)==receipt['launcherSHA256'],'LAUNCHER_SOURCE_MISMATCH')
 git(root,'add','--',NEW_VERIFY,DOC,CONTRACT,NEW_LAUNCH)
 git(root,'commit','-m',VERSION+': repair exact IK41 reopen pose sample census without rebuild')
 receipt['sourcePublicationHEAD']=remote_readback(root)
 stage('GIT_LFS_HYDRATE_PINNED_FK_REFERENCE')
 p=git(root,'lfs','pull','--include='+SOURCE,'--exclude=',timeout=1600,check=False)
 need(p.returncode==0,'PINNED_REFERENCE_LFS_FETCH_FAILED_'+p.stderr[-1200:])
 fk=root/SOURCE;need(sha(fk)==SOURCE_SHA,'FK_SOURCE_BINARY_READBACK_FAILED')
 stage('INDEPENDENT_NATIVE_BLENDER_REOPEN_82_FK_41_IK')
 job=blender(root,NEW_VERIFY,[fk,local,localauthor,localrepair,VERIFY_REPORT])
 p=call(job,timeout=2400,check=False)
 (STATE/'BLENDER_REOPEN.log').write_text(p.stdout+'\n'+p.stderr)
 need(p.returncode==0 and VERIFY_REPORT.is_file(),'NATIVE_REOPEN_PROCESS_FAILED_'+p.stderr[-1300:]+p.stdout[-850:])
 proof=json.loads(VERIFY_REPORT.read_text())
 need(proof.get('status')=='VERIFIED_41_IK_NATIVE_REOPEN_OWNER_VISUAL_PENDING' and proof.get('fkCurveComparison',{}).get('passed') is True and proof.get('IKClipCount')==41 and proof.get('actualIKPoseSamples')==121 and proof.get('expectedIKPoseSamples')==121,'NATIVE_VERIFICATION_FAILED_'+str(proof.get('error')))
 need(proof['fkCurveComparison']['referenceActions']==82 and proof['fkCurveComparison']['comparedPoints']>=252130,'ORIGINAL_FK_CURVE_EVIDENCE_INSUFFICIENT')
 receipt['verifiedReopen']=proof;save()
 stage('DELIVER_VERIFIED_IK41_BLEND_TO_ANDROID_DOWNLOADS_BEFORE_NETWORK')
 localcopy=DOWNLOADS/local.name
 if localcopy.exists():need(sha(localcopy)==OUTPUT_SHA,'ANDROID_DOWNLOAD_COLLISION_SHA_MISMATCH')
 else:copyverify(local,localcopy,OUTPUT_SHA)
 receipt['downloadPath']=str(localcopy);save()
 print('BLEND_DOWNLOAD='+str(localcopy)+' SHA256='+OUTPUT_SHA,flush=True)
 stage('PUBLISH_EXISTING_V103_BLEND_NEW_GIT_LFS_PATH')
 copyverify(local,root/OUTPUT,OUTPUT_SHA)
 need(git(root,'check-attr','filter','--',OUTPUT).stdout.strip().endswith(': lfs'),'GIT_LFS_BLEND_ATTRIBUTE_NOT_SET')
 git(root,'add','--',OUTPUT)
 staged=git(root,'show',':'+OUTPUT).stdout
 need('oid sha256:'+OUTPUT_SHA in staged,'STAGED_LFS_OID_NOT_MATCHING_NATIVE_FILE')
 git(root,'commit','-m',VERSION+': publish independently verified 41-action IK authoring native blend, visual pending')
 receipt['binaryPublicationHEAD']=remote_readback(root)
 remote_pointer=git(root,'show','origin/main:'+OUTPUT).stdout
 need('oid sha256:'+OUTPUT_SHA in remote_pointer and 'size 72014396' in remote_pointer,'REMOTE_BINARY_LFS_POINTER_NOT_CONFIRMED')
 receipt.update(status='IK41_REOPEN_FK_CURVES_AND_POSES_VERIFIED_PUBLISHED_VISUAL_PENDING',stage='COMPLETE',ownerVisualAcceptance='PENDING',publishedBlend=OUTPUT,verifiedBinarySHA256=OUTPUT_SHA);save()
 print('STATUS='+receipt['status']+'\nREPO_OUTPUT='+OUTPUT+'\nSHA256='+OUTPUT_SHA+'\nREMOTE_HEAD='+receipt['binaryPublicationHEAD']+'\nRECEIPT='+str(RECEIPT),flush=True)
except BaseException as exc:
 receipt.update(status='BLOCKED',error=str(exc),traceback=traceback.format_exc()[-3400:]);save()
 print('STATUS=BLOCKED '+str(exc)+'\nRECEIPT='+str(RECEIPT),flush=True)
 sys.exit(1)
finally:
 try:publish_logs()
 except Exception as exc:print('DIAGNOSTICS_ERROR='+repr(exc),flush=True)

PY_CAMPAIGN
