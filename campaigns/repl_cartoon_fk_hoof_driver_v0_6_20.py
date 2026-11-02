#!/usr/bin/env python3
"""Repl v0.6.20: recover, replan, independently verify, publish via Termux Git only."""
from __future__ import annotations
import argparse,datetime,hashlib,importlib.util,json,os,sys,tempfile,traceback
from pathlib import Path
sys.dont_write_bytecode=True
VERSION='0.6.20'
PREFIX='REPL_CARTOON_FK_HOOF_WALK_v0.6.20'
PARENT='af576184ab956cc3b07de2e49f9db9eebeb4049b'
SRC_SHA='c6dc250356248e5860e5919568e4103d6c1d2cb6e071e7bb9a0f7ce1f42ee4c1'
SRC_BLOB='532ee6b18bf4a412fe0a674311ddef3c9ae46001'
CANON='assets/repl/Repl.glb'
MODEL_META='assets/repl/CANONICAL_MODEL.json'
POLICY_MARK='## 2026-11-02 — Mandatory predictive, resilient campaign engineering (owner directive)'
FILES={
 'campaigns/repl_cartoon_fk_hoof_model_v0_6_20.py':'model.py',
 'campaigns/repl_cartoon_fk_hoof_driver_v0_6_20.py':'driver.py',
 'campaigns/repl_cartoon_fk_hoof_git_core_v0_6_20.py':'git_core.py',
 'campaigns/repl_cartoon_fk_hoof_selftest_v0_6_20.py':'selftest.py',
 'campaigns/repl_cartoon_fk_hoof_driver_regression_v0_6_20.py':'driver_regression.py',
 'campaigns/repl_cartoon_fk_hoof_viewer_v0_6_20.html.in':'viewer.html.in',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.20.sh':'run-termux.sh',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.20_CONTRACT.json':'contract.json',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.20_README.md':'../README.md',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.20_AGENTS_ADDENDUM.md':'../AGENTS_ADDENDUM.md',
 'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.20_PACKET_MANIFEST.json':'../manifest.json',
}
def need(ok,reason):
 if not ok:raise RuntimeError(reason)
def sha(b):return hashlib.sha256(b).hexdigest()
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

def write_diagnostic(core,downloads,tag,detail):
 content=(json.dumps(detail,indent=2,sort_keys=True,default=str)+'\n').encode()
 path=downloads/(PREFIX+'_'+tag+'_'+sha(content)[:12]+'.json')
 core.publish(path,content)
 print('DIAGNOSTIC='+str(path),flush=True)
 return path

def remote_model_verify(core,repo,expected_commit,expected_model_sha):
 core.git(repo,'fetch','--quiet','origin','main')
 # Remote Git tree inspection, not merely local commit hash.
 head=core.gout(repo,'rev-parse','refs/remotes/origin/main')
 need(head==expected_commit,'REMOTE_COMMIT_READBACK_MISMATCH')
 blob=core.gout(repo,'rev-parse','refs/remotes/origin/main:'+CANON)
 content=(repo/CANON).read_bytes()
 need(blob==core.gitblob(content) and sha(content)==expected_model_sha,
      'REMOTE_MODEL_BLOB_OR_LOCAL_BYTES_CHANGED')
 print('REMOTE_READBACK_SHA='+head,flush=True)
 print('REMOTE_MODEL_BLOB='+blob,flush=True)

def main():
 arg=argparse.ArgumentParser();arg.add_argument('--packet',required=True)
 args=arg.parse_args()
 packet=Path(args.packet).resolve();root=packet.parent
 core=module(packet/'git_core.py','repl20_git_core')
 core.KNOWN_PARENT_HEAD=PARENT;core.SOURCE_SHA=SRC_SHA;core.SOURCE_BLOB=SRC_BLOB;core.VER=VERSION
 downloads=Path.home()/'storage'/'downloads'
 need(downloads.is_dir(),'TERMUX_DOWNLOADS_MISSING')
 work=Path.home()/'.local'/'share'/'repl-campaigns'/'cartoon-fk-hoof-v0.6.20'
 work.mkdir(parents=True,exist_ok=True)
 print('CAMPAIGN_VERSION='+VERSION,flush=True)
 print('LANE=TERMUX_GIT_ONLY',flush=True)
 print('REQUIRED_RULES_READ=AUTHOR_FRESH_ETIQUETTE_AND_GITHUB_AGENTS',flush=True)
 repo=core.checkout(work);os.chdir(repo)
 need(core.gout(repo,'remote','get-url','origin')==core.REMOTE,'REMOTE_NOT_CANONICAL')
 need(not core.git(repo,'status','--porcelain','--untracked-files=all').stdout.strip(),
      'PRIVATE_GIT_CHECKOUT_DIRTY__RECONCILE_NOT_RESET')
 head=core.gout(repo,'rev-parse','HEAD')
 remote=core.gout(repo,'rev-parse','refs/remotes/origin/main')
 print('EXECUTION_DIR='+str(repo.resolve()),flush=True)
 print('HEAD='+head,flush=True)
 print('ORIGIN_MAIN='+remote,flush=True)
 # Resume partial publication instead of forcing operator into more scripts.
 meta=json.loads((repo/MODEL_META).read_text())
 active=meta['active_model']
 if active.get('version')==VERSION:
  finished_hash=active['sha256'];need(sha((repo/CANON).read_bytes())==finished_hash,
      'LOCAL_COMMITTED_MODEL_HASH_CHANGED')
  if head!=remote:
   need(core.gout(repo,'merge-base','--is-ancestor',remote,head) is not None,
        'LOCAL_COMMIT_NOT_DESCENDED_FROM_REMOTE')
   need(core.gout(repo,'ls-remote','origin','refs/heads/main').split()[0]==remote,
        'REMOTE_MOVED_DURING_RESUME')
   core.push(repo,remote)
  remote_model_verify(core,repo,head,finished_hash)
  print('CAMPAIGN_STATUS=MODEL_REMOTE_VERIFIED_PREVIOUS_SUCCESS',flush=True)
  print('HUMAN_VISUAL_ACCEPTANCE=PENDING',flush=True)
  return 0
 if head!=remote:
  # Resume source/AGENTS commit with no model change. Never re-commit or reset.
  need((repo/'campaigns/repl_cartoon_fk_hoof_driver_v0_6_20.py').is_file(),
       'UNKNOWN_LOCAL_AHEAD_COMMIT')
  need(core.gout(repo,'rev-parse','HEAD:'+CANON)==SRC_BLOB,
       'SOURCE_MODEL_MUTATED_IN_UNRECONCILED_COMMIT')
  need(core.gout(repo,'ls-remote','origin','refs/heads/main').split()[0]==remote,
       'REMOTE_ADVANCED_WHILE_SOURCE_PUSH_PENDING')
  core.git(repo,'merge-base','--is-ancestor',remote,head)
  core.push(repo,remote)
  remote_model_verify(core,repo,head,SRC_SHA)
  print('RECOVERED_PREVIOUS_SOURCE_POLICY_COMMIT='+head,flush=True)
 need(core.gout(repo,'rev-parse','HEAD:'+CANON)==SRC_BLOB,
      'REMOTE_SOURCE_MODEL_BLOB_CHANGED__NO_SUBSTITUTION')
 source=(repo/CANON).read_bytes();need(sha(source)==SRC_SHA,'CANONICAL_SOURCE_SHA_CHANGED')
 need(active['version']=='0.6.17' and active['sha256']==SRC_SHA,
      'SOURCE_META_VERSION_OR_SHA_MISMATCH')
 core.one_model(repo)
 print('CANONICAL_SOURCE_SHA='+SRC_SHA,flush=True)
 agents_path=repo/'AGENTS.md';before=agents_path.read_bytes()
 addition=(root/'AGENTS_ADDENDUM.md').read_bytes()
 need(b'Mandatory repository boot gate' in before and
      b'Repl stance and breakover' in before and
      b'Python shadow import regression' in before,
      'REQUIRED_PREVIOUS_AGENTS_INSTRUCTIONS_MISSING')
 if POLICY_MARK.encode() in before:
  need(before.endswith(addition),'ALREADY_PUBLISHED_AGENTS_APPEND_CHANGED')
  policy=before
 else:policy=before.rstrip(b'\n')+b'\n\n'+addition
 published_driver=repo/'campaigns/repl_cartoon_fk_hoof_driver_v0_6_20.py'
 if not published_driver.is_file():
  need(head==PARENT,'NO_SAFE_SOURCE_PUBLISH_FROM_UNEXPECTED_HEAD')
  # Complete collision and content preflight before ANY mutation, incl AGENTS.
  for dest,rel in FILES.items():
   dst=repo/dest;src=(packet/rel).resolve()
   need(src.is_relative_to(root) and src.is_file(),'PACKET_FILE_MISSING:'+rel)
   need(not dst.exists() and not dst.is_symlink(),'VERSIONED_DEST_COLLISION:'+dest)
   need('v0.6.20' in dest or 'v0_6_20' in dest,'STALE_SOURCE_FILENAME:'+dest)
  agents_path.write_bytes(policy)
  need(agents_path.read_bytes()==policy,'AGENTS_APPEND_READBACK_FAILED')
  for dest,rel in FILES.items():
   dst=repo/dest;dst.parent.mkdir(parents=True,exist_ok=True)
   dst.write_bytes((packet/rel).resolve().read_bytes())
  core.git(repo,'add','--','AGENTS.md',*FILES)
  listed=core.git(repo,'diff','--cached','--name-only').stdout.splitlines()
  need(set(listed)==set(['AGENTS.md',*FILES]),'UNAUTHORIZED_STAGED_FILES')
  core.git(repo,'-c','user.name=Repl Termux Campaign',
    '-c','user.email=repl-termux-campaign@users.noreply.github.com',
    'commit','-m','Require resilient adaptive campaign recovery and add Repl v0.6.20 source')
  pub=core.gout(repo,'rev-parse','HEAD')
  core.push(repo,PARENT)
  remote_model_verify(core,repo,pub,SRC_SHA)
  print('SCRIPT_AND_AGENTS_PUBLISHED_SHA='+pub,flush=True)
 else:
  need(agents_path.read_bytes()==policy,'AGENTS_ALREADY_PUBLISHED_CONTENT_MISMATCH')
  for dest,rel in FILES.items():
   need((repo/dest).read_bytes()==(packet/rel).resolve().read_bytes(),
        'PUBLISHED_SOURCE_PACKET_MISMATCH:'+dest)
  print('SCRIPT_AND_AGENTS_PUBLISHED_SHA='+head,flush=True)
 need(sha((repo/CANON).read_bytes())==SRC_SHA,'SOURCE_CHANGED_BEFORE_SEARCH')
 base=module(repo/'campaigns/repl_hair_bind_v0_1_0.py','repl20_skinning_engine')
 base.EXPECTED_JOINTS=50
 previous=module(repo/'campaigns/repl_cartoon_fk_hoof_model_v0_6_8.py','repl20_skeleton_engine')
 validator=module(repo/'campaigns/repl_cartoon_fk_hoof_model_v0_6_17.py','repl20_independent_verifier')
 solver=module(packet/'model.py','repl20_adaptive_solver')
 need(solver.SOURCE_SHA==SRC_SHA and solver.VERSION==VERSION,'SOLVER_VERSION_OR_SOURCE_CHANGED')
 try:
  candidate,report,attempts=solver.evaluate(source,base,previous,validator,work/'adaptive',
                                              progress=lambda x:print('PROGRESS='+str(x),flush=True))
 except Exception as exc:
  search_path=work/'adaptive'/'search_checkpoint.json'
  checkpoint=json.loads(search_path.read_text()) if search_path.is_file() else {}
  write_diagnostic(core,downloads,'SEARCH_DIAGNOSTIC',{
   'campaign':PREFIX,'canonical_sha256':SRC_SHA,'status':'MODEL_UNCHANGED__SEARCH_NOT_SUCCESSFUL',
   'exception':str(exc)[:10000],'traceback':traceback.format_exc(limit=5),
   'checkpoint':checkpoint,'authorized_channels':sorted(solver.EDITABLE),
   'remote_source_and_policy_published':True,
   'scope_change_not_approved':'distal and root remain locked',
   'human_visual_approval':'PENDING'})
  print('MODEL_UNCHANGED=PASS',flush=True)
  print('CAMPAIGN_STATUS=ADAPTIVE_SEARCH_NO_PHYSICALLY_VERIFIED_IMPROVEMENT',flush=True)
  return 2
 # Full verifier has passed, but compare actual animation channels yet again.
 need(sha((repo/CANON).read_bytes())==SRC_SHA,'SOURCE_CHANGED_DURING_SEARCH')
 need(sha(candidate)!=SRC_SHA,'CANDIDATE_IDENTICAL_TO_BASELINE')
 # Retain the candidate/receipt independent of transport failures.
 safe=work/'adaptive'/'verified_candidate.glb';safe.parent.mkdir(parents=True,exist_ok=True);safe.write_bytes(candidate)
 need(sha(safe.read_bytes())==sha(candidate),'CANDIDATE_PRIVATE_STAGING_FAILED')
 report.update({'source_sha256':SRC_SHA,'source_git_head':head,'search_attempts':attempts,
    'human_visual_acceptance':'PENDING','review_baseline':'V0617_BEST_YET_NOT_APPROVED'})
 rep=(json.dumps(report,indent=2,sort_keys=True)+'\n').encode()
 report_path=downloads/(PREFIX+'_report.json')
 core.publish(report_path,rep)
 print('REAL_PHYSICS_AND_KINEMATIC_GATES=PASS',flush=True)
 print('VERIFIED_CANDIDATE_SHA256='+sha(candidate),flush=True)
 print('SEARCH_ATTEMPTS='+str(len(attempts)),flush=True)
 viewer=core.make_viewer(packet,repo,candidate).replace(b'v0.6.17',b'v0.6.20')
 viewpath=downloads/(PREFIX+'_TEXTURED_POSE_LAB.html')
 core.publish(viewpath,viewer)
 print('TEXTURED_VIEWER='+str(viewpath),flush=True)
 # No second canonical GLB ever appears in Git; temp file is private outside.
 parent=core.gout(repo,'rev-parse','HEAD')
 need(core.gout(repo,'ls-remote','origin','refs/heads/main').split()[0]==parent,
      'REMOTE_ADVANCED_AFTER_SOURCE_PUBLICATION')
 model_path=repo/CANON
 fd,tmp=tempfile.mkstemp(prefix='.Repl_verified_v0620_',dir=model_path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(candidate);f.flush();os.fsync(f.fileno())
  need(sha(Path(tmp).read_bytes())==sha(candidate),'ATOMIC_MODEL_STAGING_BAD_SHA')
  os.replace(tmp,model_path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 need(sha(model_path.read_bytes())==sha(candidate),'CANONICAL_WRITE_READBACK_FAILED')
 meta['previous_model']={'version':'0.6.17','sha256':SRC_SHA,
   'owner_visual_acceptance':'BEST_YET_ALMOST_ACCEPTABLE__NOT_FINAL'}
 new=dict(meta['active_model'])
 new.update({'version':VERSION,'sha256':sha(candidate),'git_blob_sha1':core.gitblob(candidate),
    'human_visual_acceptance':'PENDING','mode':'ADAPTIVE_FRONT_STANCE_KINEMATIC_REPAIR',
    'measured_knee_and_reach':report['kinematics'],
    'adaptive_solver_summary':report['summary']})
 meta['active_model']=new;meta['status']='REPL_v0.6.20_PHYSICAL_PASS__VISUAL_PENDING'
 (repo/MODEL_META).write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n')
 rd=repo/'README.md'
 rd.write_text(rd.read_text().rstrip()+'\n\n## Repl v0.6.20 adaptive grounded forelegs\n'
    'Bounded adaptive full-cycle search passed exact production skinned geometry '
    'validation; only four front shoulder/middle rotation tracks changed. '
    'Owner visual acceptance pending.\n')
 core.git(repo,'add','--',CANON,MODEL_META,'README.md')
 staged=set(core.git(repo,'diff','--cached','--name-only').stdout.splitlines())
 need(staged=={CANON,MODEL_META,'README.md'},'UNEXPECTED_MODEL_COMMIT_SCOPE')
 core.git(repo,'-c','user.name=Repl Termux Campaign',
    '-c','user.email=repl-termux-campaign@users.noreply.github.com',
    'commit','-m','Repl adaptive grounded front support and trailing breakover v0.6.20')
 commit=core.gout(repo,'rev-parse','HEAD')
 core.push(repo,parent)
 remote_model_verify(core,repo,commit,sha(candidate))
 print('CAMPAIGN_STATUS=REMOTE_MODEL_UPDATED__VISUAL_REVIEW_PENDING',flush=True)
 print('HUMAN_VISUAL_ACCEPTANCE=PENDING',flush=True)
 print('REPORT='+str(report_path),flush=True)
 return 0

if __name__=='__main__':
 try:sys.exit(main())
 except Exception as exc:
  print('CAMPAIGN_STATUS=BLOCKED',flush=True)
  print('CAUSE='+type(exc).__name__+':'+str(exc)[:2000],flush=True)
  sys.exit(2)
