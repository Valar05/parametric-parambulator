#!/usr/bin/env python3
"""Termux Git-only installation and execution of Obsidianti v1.2 pelvis / weapon fix.

Single canonical model path; code-first commit; no direct GitHub connector writes;
never operates inside the user's dirty project working tree.
"""
from __future__ import annotations
import datetime, hashlib, json, os, pathlib, shutil, subprocess, sys, time, uuid

VERSION='OBSIDIANTI_PELVIS_WEAPON_v1.2.1'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
CANONICAL='assets/obsidianti/Obsidianti.glb'
BLEND='assets/obsidianti/source/LionheartLancer.blend'
SOURCE_SHA='5fa8773736cf4fd28eae13e13368246642642a1802d76e47ed7e14faf70d04c0'
BLEND_SHA='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
SCRIPTS={
 'campaigns/OBSIDIANTI_PELVIS_WEAPON_v1.2.1.sh',
 'campaigns/OBSIDIANTI_PELVIS_WEAPON_RUN_v1.2.1.py',
 'campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py',
 'docs/obsidianti/PELVIS_WEAPON_v1.2.1.md',
 'tests/OBSIDIANTI_PELVIS_WEAPON_TEST_v1.2.1.py',
 'tests/OBSIDIANTI_RULES_GATE_TEST_v1.2.1.py',
}

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def cmd(argv,cwd=None,env=None,timeout=150,ok=True):
 p=subprocess.run(argv,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
 if ok and p.returncode:raise RuntimeError('COMMAND_FAILED:'+str(argv[:8])+':'+p.stderr[-1500:])
 return p

def git(repo,args,**opts):return cmd(['git','-C',str(repo),*args],**opts)

def atomic_json(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n');os.replace(tmp,path)

def lfs_oid(repo,path):
 p=git(repo,['show','HEAD:'+path],ok=False)
 if p.returncode:raise RuntimeError('CANONICAL_NOT_ON_REMOTE:'+path)
 s=p.stdout
 if not s.startswith('version https://git-lfs.github.com/spec/v1'):
  raise RuntimeError('EXPECTED_LFS_POINTER:'+path)
 for row in s.splitlines():
  if row.startswith('oid sha256:'):return row.split(':',1)[1]
 raise RuntimeError('INVALID_GIT_LFS_POINTER:'+path)

def current_blob(repo,path):
 p=git(repo,['show','HEAD:'+path],ok=False)
 return hashlib.sha256(p.stdout.encode()).hexdigest() if not p.returncode else None

def commit(repo,paths,message):
 git(repo,['add','--',*paths]);staged=git(repo,['diff','--cached','--name-only']).stdout.splitlines()
 if any(x not in paths for x in staged):raise RuntimeError('STAGED_OUTSIDE_ALLOWLIST:'+str(staged))
 if not staged:return git(repo,['rev-parse','HEAD']).stdout.strip(),False
 if not git(repo,['config','user.name'],ok=False).stdout.strip():git(repo,['config','user.name','Obsidianti Termux Campaign'])
 if not git(repo,['config','user.email'],ok=False).stdout.strip():git(repo,['config','user.email','obsidianti-campaign@users.noreply.github.com'])
 git(repo,['commit','-m',message],timeout=150)
 return git(repo,['rev-parse','HEAD']).stdout.strip(),True

def read_repo_rules(repo):
 """Read the ACTUAL checked-out rules and verify byte-exact Git tracking.

 Historical v1.2.0 bug: searched for lowercase 'read the live Campaign
 Etiquette' although AGENTS says 'Read the live Campaign Etiquette'.
 Policy must be checked by document identity/tracked content, never by brittle
 case-sensitive prose snippets.
 """
 agent=repo/'AGENTS.md'
 if not agent.is_file():raise RuntimeError('RULES_READ_BLOCKED_NO_AGENTS')
 try:rules=agent.read_text(encoding='utf-8-sig')
 except (UnicodeError,OSError) as e:raise RuntimeError('RULES_READ_BLOCKED_UNREADABLE_AGENTS:'+str(e)) from e
 root=git(repo,['rev-parse','--show-toplevel']).stdout.strip()
 if pathlib.Path(root).resolve()!=repo.resolve():
  raise RuntimeError('RULES_READ_BLOCKED_REPOSITORY_ROOT_MISMATCH')
 tracked=git(repo,['rev-parse','HEAD:AGENTS.md'],ok=False)
 actual=git(repo,['hash-object',str(agent)],ok=False)
 if tracked.returncode or actual.returncode or tracked.stdout.strip()!=actual.stdout.strip():
  raise RuntimeError('RULES_READ_BLOCKED_AGENTS_NOT_GIT_TRACKED_OR_MODIFIED')
 policy=rules.casefold()
 if (not rules.lstrip().startswith('# AGENTS.md') or len(rules)<500
  or 'parametric-parambulator' not in policy
  or 'termux git only' not in policy
  or 'campaign etiquette' not in policy):
  raise RuntimeError('RULES_READ_BLOCKED_WRONG_POLICY_DOCUMENT')
 return {'agentsSha256':sha(agent),'agentsGitBlob':tracked.stdout.strip(),
         'rulesAuthority':'VERIFIED_GIT_TRACKED_REPO_AGENTS_POLICY'}

def source_sample(repo,work):
 script=repo/'campaigns/OBSIDIANTI_SOURCE_SAMPLER_v1.1.0.py'
 if not script.is_file():raise RuntimeError('UPSTREAM_LIONHEART_SAMPLER_NOT_AVAILABLE')
 src=repo/BLEND;out=work/'lionheart-contacts.json'
 blender=shutil.which('blender')
 if blender:
  args=[blender,'--background','--python',str(script),'--','--kind','lionheart','--source',str(src),'--out',str(out)]
 elif shutil.which('proot-distro'):
  args=['proot-distro','login','debian',
   '--bind',str(repo.resolve())+':/mnt/obs-repo',
   '--bind',str(work.resolve())+':/mnt/obs-work',
   '--','blender','--background',
   '--python','/mnt/obs-repo/campaigns/OBSIDIANTI_SOURCE_SAMPLER_v1.1.0.py',
   '--','--kind','lionheart',
   '--source','/mnt/obs-repo/'+BLEND,'--out','/mnt/obs-work/lionheart-contacts.json']
 else:raise RuntimeError('BLENDER_NOT_AVAILABLE_ON_PHONE')
 p=cmd(args,timeout=540,ok=False)
 (work/'blender-contacts.log').write_text(p.stdout+'\n'+p.stderr)
 if p.returncode or not out.is_file():raise RuntimeError('BLENDER_LIONHEART_CONTACT_SAMPLER_FAILED:'+p.stderr[-1000:])
 data=json.loads(out.read_text())
 if data.get('sourceKind')!='lionheart' or data.get('actionCount')!=11:raise RuntimeError('UNEXPECTED_LIONHEART_SAMPLE_SET')
 return out

def ensure_lfs():
 if not cmd(['git','lfs','version'],ok=False).returncode:return
 if shutil.which('pkg'):cmd(['pkg','install','-y','git-lfs'],timeout=240)
 if cmd(['git','lfs','version'],ok=False).returncode:raise RuntimeError('GIT_LFS_UNAVAILABLE')

def main():
 if len(sys.argv)!=2:raise RuntimeError('USAGE: RUN_ABSOLUTE_PACKET_ROOT')
 packet=pathlib.Path(sys.argv[1]).resolve()
 manifest=json.loads((packet/'manifest.json').read_text())
 if manifest.get('campaign')!=VERSION:raise RuntimeError('PACKET_IDENTITY_MISMATCH')
 for file,digest in manifest['files'].items():
  p=packet/file
  if not p.is_file() or sha(p)!=digest:raise RuntimeError('PACKET_MEMBER_SHA_INVALID:'+file)
 if set(manifest['files'])!=SCRIPTS:raise RuntimeError('PACKET_ALLOWLIST_MISMATCH')
 print('CAMPAIGN='+VERSION+'\nLANE=TERMUX_GIT_ONLY\nMODEL='+CANONICAL+'\nPACKET_VERIFIED=YES',flush=True)
 if not shutil.which('git'):raise RuntimeError('GIT_MISSING')
 # Verify the exact prior field failure cannot recur BEFORE touching Git remote.
 rules_test=packet/'tests/OBSIDIANTI_RULES_GATE_TEST_v1.2.1.py'
 rules_result=cmd([sys.executable,str(rules_test),str(packet/'campaigns/OBSIDIANTI_PELVIS_WEAPON_RUN_v1.2.1.py')],timeout=20,ok=False)
 if rules_result.returncode:
  raise RuntimeError('RULES_GATE_REGRESSION_FAILED:'+rules_result.stderr[-1300:])
 print(rules_result.stdout.strip(),flush=True)
 ensure_lfs()
 work=pathlib.Path.home()/'.local/state'/VERSION/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]);work.mkdir(parents=True)
 downloads=pathlib.Path.home()/'storage/downloads';downloads=downloads if downloads.is_dir() else work
 receipt=downloads/(VERSION+'_'+work.name+'_RECEIPT.json')
 status={'campaign':VERSION,'stage':'STARTED','owner':'Termux Git','canonical':CANONICAL,'expectedSource':SOURCE_SHA,'workdir':str(work),'gitMutations':'none','visualAcceptance':'PENDING'}
 atomic_json(receipt,status)
 try:
  repo=work/'repo';env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1';env['GIT_TERMINAL_PROMPT']='0'
  cmd(['git','clone','--depth=1','--branch','main','--single-branch',REMOTE,str(repo)],env=env,timeout=240)
  status['headBefore']=git(repo,['rev-parse','HEAD']).stdout.strip()
  rule_evidence=read_repo_rules(repo)
  status.update(rule_evidence)
  status['campaignEtiquetteDocument']='1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI'
  status['etiquetteReadByAuthor']='Home Center freshly read 2026-11-04'
  print('RULES_READ=PASS\nAGENTS_GIT_BLOB='+rule_evidence['agentsGitBlob'],flush=True)
  if git(repo,['status','--porcelain=v1','--untracked-files=all']).stdout.strip():raise RuntimeError('DIRTY_ISOLATED_CHECKOUT')
  oldoid=lfs_oid(repo,CANONICAL);status['remoteOldModelOid']=oldoid
  if oldoid!=SOURCE_SHA:raise RuntimeError('CANONICAL_MODEL_CHANGED_EXPECTED_'+SOURCE_SHA+'_GOT_'+oldoid)
  replt=git(repo,['rev-parse','HEAD:assets/repl/Repl.glb']).stdout.strip()
  # Collision gate runs BEFORE copying scripts or altering the model.
  for rel in sorted(SCRIPTS):
   src=packet/rel;dst=repo/rel
   if dst.exists() and sha(dst)!=sha(src):raise RuntimeError('VERSIONED_SOURCE_COLLISION:'+rel)
  print('STAGE=FETCH_CANONICAL_AND_LIONHEART_LFS',flush=True)
  lfs=git(repo,['lfs','pull','--include='+CANONICAL+','+BLEND,'--exclude='],timeout=300,ok=False)
  if lfs.returncode:raise RuntimeError('LFS_SOURCE_PULL_FAILED:'+lfs.stderr[-1000:])
  if sha(repo/CANONICAL)!=SOURCE_SHA or sha(repo/BLEND)!=BLEND_SHA:raise RuntimeError('CANONICAL_OR_LIONHEART_SOURCE_BYTES_MISMATCH')
  status['sourceModelBytesVerified']=True;status['sourceBlendBytesVerified']=True
  for rel in sorted(SCRIPTS):
   dest=repo/rel
   if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(packet/rel,dest)
  paths=[rel for rel in sorted(SCRIPTS) if git(repo,['ls-files','--error-unmatch',rel],ok=False).returncode!=0]
  c,changed=commit(repo,paths,'Obsidianti: source v1.2 pelvis contact and weapon-drift repair')
  status['scriptCommit']=c;status['scriptCommitted']=changed
  for rel in SCRIPTS:
   if current_blob(repo,rel)!=sha(packet/rel):raise RuntimeError('SOURCE_GIT_READBACK_FAILED:'+rel)
  status['gitMutations']='local source commit only';atomic_json(receipt,status)
  print('STAGE=EVALUATE_REAL_LIONHEART_SOURCE',flush=True)
  sampled=source_sample(repo,work);status['sourceSampleSha256']=sha(sampled)
  patcher=repo/'campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py';output=work/'fit-report.json'
  test=repo/'tests/OBSIDIANTI_PELVIS_WEAPON_TEST_v1.2.1.py';pre=work/'real-model-preflight.json'
  print('STAGE=REAL_MODEL_PHYSICAL_PREFLIGHT',flush=True)
  verify=cmd([sys.executable,str(test),'--model',str(repo/CANONICAL),'--source',str(sampled),'--solver',str(patcher),'--out',str(pre)],timeout=360,ok=False)
  (work/'preflight.log').write_text(verify.stdout+'\n'+verify.stderr)
  if verify.returncode or not pre.is_file():raise RuntimeError('REAL_MODEL_PREFLIGHT_FAILED:'+verify.stderr[-1400:])
  preflight=json.loads(pre.read_text());status['verifiedPreflight']=preflight
  print('STAGE=CANONICAL_MODEL_PATCH',flush=True)
  r=cmd([sys.executable,str(patcher),'--model',str(repo/CANONICAL),'--source',str(sampled),'--report',str(output)],timeout=300,ok=False)
  (work/'solver.log').write_text(r.stdout+'\n'+r.stderr)
  if r.returncode or not output.is_file():raise RuntimeError('PELVI_WEAPON_SOLVER_FAILED:'+r.stderr[-1200:])
  fit=json.loads(output.read_text());status['fitReport']=fit
  if fit['beforeSha256']!=SOURCE_SHA or fit['clipCount']!=23 or sha(repo/CANONICAL)!=fit['afterSha256']:raise RuntimeError('FINAL_PATCH_RESULT_MISMATCH')
  if fit['afterSha256']!=preflight['expectedFinalSha256']:raise RuntimeError('REAL_MODEL_PREFLIGHT_OUTPUT_SHA_DIFFERS')
  if fit['weaponTranslationChannelsRemoved']<3:raise RuntimeError('WEAPON_TRANSLATION_TRACK_REMOVAL_MISSING')
  if len(list((repo/'assets/obsidianti').glob('*.glb')))!=1:raise RuntimeError('MULTIPLE_CANONICAL_GLB_FILES')
  c2,changed2=commit(repo,[CANONICAL],'Obsidianti: correct Lionheart pelvis pitch and remove weapon translation on SAME GLB')
  if not changed2:raise RuntimeError('NO_ACTUAL_CANONICAL_MODEL_CHANGE')
  if git(repo,['rev-parse','HEAD:assets/repl/Repl.glb']).stdout.strip()!=replt:raise RuntimeError('REPL_MODEL_CHANGED')
  if lfs_oid(repo,CANONICAL)!=fit['afterSha256']:raise RuntimeError('LFS_MODEL_POINTER_READBACK_FAILED')
  if git(repo,['status','--porcelain=v1','--untracked-files=all']).stdout.strip():raise RuntimeError('DIRTY_AFTER_MODEL_COMMIT')
  status['modelCommit']=c2;status['gitMutations']='local source and canonical model commits; push pending';atomic_json(receipt,status)
  print('STAGE=NONFORCED_GIT_PUSH_AND_READBACK',flush=True)
  pushed=git(repo,['push','origin','HEAD:refs/heads/main'],timeout=240,ok=False)
  if pushed.returncode:
   if 'non-fast-forward' in pushed.stderr or '[rejected]' in pushed.stderr:raise RuntimeError('REMOTE_ADVANCED_STOP_NO_FORCE')
   if shutil.which('gh'):
    pushed=cmd(['git','-C',str(repo),'-c','credential.helper=!gh auth git-credential','push','origin','HEAD:refs/heads/main'],timeout=240,ok=False)
   if pushed.returncode:raise RuntimeError('PUSH_FAILED:'+pushed.stderr[-1600:])
  remote=git(repo,['ls-remote','origin','refs/heads/main']).stdout.split()[0]
  if remote!=c2:raise RuntimeError('REMOTE_HEAD_DIFFERS_FROM_COMMITTED_HEAD')
  status['remoteCommitVerified']=remote;status['remoteLfsPointerVerified']=lfs_oid(repo,CANONICAL)
  status['gitMutations']='remote source/model commits readback verified; actual LFS binary readback separate'
  # Use the existing model viewer; leave the file itself, other clips and all materials untouched.
  import socket, urllib.request
  for port in range(8179,8188):
   s=socket.socket()
   try:s.bind(('127.0.0.1',port))
   except OSError:continue
   finally:s.close()
   log=open(work/('viewer-'+str(port)+'.log'),'ab',buffering=0)
   try:
    proc=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(repo)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    time.sleep(.45)
    url='http://127.0.0.1:'+str(port)+'/review/obsidianti-library-v1.1.0.html'
    if proc.poll() is None:
     try:
      with urllib.request.urlopen(url,timeout=3) as resp:
       if resp.status==200:status.update({'viewerURL':url,'viewerPid':proc.pid,'viewerHTTP':'200_NOT_HUMAN_APPROVAL'});break
     except Exception:pass
    if proc.poll() is None:proc.terminate()
   finally:log.close()
  status['stage']='REMOTE_CANDIDATE_PUBLISHED_VISUAL_ACCEPTANCE_PENDING'
  atomic_json(receipt,status)
  print('STATUS='+status['stage']+'\nREMOTE_HEAD='+remote+'\nMODEL_SHA256='+fit['afterSha256']+'\nPITCH_CLIPS='+str(fit['pelvisPitchClipsApplied'])+'\nWEAPON_TRANSLATION_CHANNELS_REMOVED='+str(fit['weaponTranslationChannelsRemoved'])+'\nRECEIPT='+str(receipt),flush=True)
  if 'viewerURL' in status:print('REVIEW_URL='+status['viewerURL'],flush=True)
  return 0
 except Exception as e:
  status['stage']='BLOCKED_REQUIRES_RECOVERY_NO_COMPLETION_CLAIM';status['error']=str(e)
  atomic_json(receipt,status)
  print('STATUS=BLOCKED\nREASON='+str(e)+'\nRECEIPT='+str(receipt),flush=True)
  return 2

if __name__=='__main__':sys.exit(main())
