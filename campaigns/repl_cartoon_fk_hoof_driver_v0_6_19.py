#!/usr/bin/env python3
"""Repl v0.6.19 Termux-only one-invocation source/doctrine + guarded gait campaign."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,sys,datetime,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
VER='0.6.19'
PREFIX='REPL_CARTOON_FK_HOOF_WALK_v0.6.19'
PARENT='a18fa83d9bc4f4ed2368c497df3f9fd28102080f'
SRC_SHA='c6dc250356248e5860e5919568e4103d6c1d2cb6e071e7bb9a0f7ce1f42ee4c1'
SRC_BLOB='532ee6b18bf4a412fe0a674311ddef3c9ae46001'
AGENTS_OLD_SHA='ee4231dfb5e67d206e53633d8a944eca2082fe27c125f3caa158f0dfe2d4e646'
CANON='assets/repl/Repl.glb'
MODEL_META='assets/repl/CANONICAL_MODEL.json'
POLICY_MARK='## 2026-11-02 — Repl stance and breakover: owner correction and mandatory physical gates'
FILES={
 f'campaigns/repl_cartoon_fk_hoof_model_v0_6_19.py':'model.py',
 f'campaigns/repl_cartoon_fk_hoof_driver_v0_6_19.py':'driver.py',
 f'campaigns/repl_cartoon_fk_hoof_git_core_v0_6_19.py':'git_core.py',
 f'campaigns/repl_cartoon_fk_hoof_selftest_v0_6_19.py':'selftest.py',
 f'campaigns/repl_cartoon_fk_hoof_driver_regression_v0_6_19.py':'driver_regression.py',
 f'campaigns/repl_cartoon_fk_hoof_reference_v0_6_19.json':'stance_reference.json',
 f'campaigns/repl_cartoon_fk_hoof_viewer_v0_6_19.html.in':'viewer.html.in',
 f'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.19.sh':'run-termux.sh',
 f'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.19_CONTRACT.json':'contract.json',
 f'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.19_README.md':'../README.md',
 f'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.19_AGENTS_ADDENDUM.md':'../AGENTS_ADDENDUM.md',
 f'campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.19_PACKET_MANIFEST.json':'../manifest.json',
}

def require(c,w):
 if not c:raise RuntimeError(w)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def main():
 args=argparse.ArgumentParser();args.add_argument('--packet',required=True);o=args.parse_args()
 packet=Path(o.packet).resolve();root=packet.parent
 core=load(packet/'git_core.py','repl18_transport')
 # Reuse the tested v0.6.17 transport engine with exact new version pins.
 core.KNOWN_PARENT_HEAD=PARENT;core.SOURCE_SHA=SRC_SHA;core.SOURCE_BLOB=SRC_BLOB
 core.VER=VER
 down=Path.home()/'storage'/'downloads';require(down.is_dir(),'TERMUX_DOWNLOADS_MISSING')
 work=Path.home()/'.local'/'share'/'repl-campaigns'/'cartoon-fk-hoof-v0.6.19'
 work.mkdir(parents=True,exist_ok=True)
 print('CAMPAIGN_VERSION='+VER,flush=True)
 print('LANE=TERMUX_GIT_ONLY',flush=True)
 print('REQUIRED_RULES_READ=LIVE_ETIQUETTE_AND_REPO_AGENTS_BY_AUTHOR',flush=True)
 repo=core.checkout(work);os.chdir(repo)
 head=core.gout(repo,'rev-parse','HEAD')
 remote=core.gout(repo,'rev-parse','refs/remotes/origin/main')
 require(core.gout(repo,'remote','get-url','origin')==core.REMOTE,'UNAUTHORIZED_GIT_REMOTE')
 require(not core.git(repo,'status','--porcelain','--untracked-files=all').stdout.strip(),'DIRTY_PRIVATE_GIT_TREE')
 require(head==remote,'GIT_HEAD_NOT_EQUAL_REMOTE__RETRY_AFTER_RECONCILIATION')
 require(head==PARENT or (repo/'campaigns/repl_cartoon_fk_hoof_driver_v0_6_19.py').is_file(),
         'CANONICAL_HEAD_CHANGED_AFTER_PACKET_BUILT')
 require(core.gout(repo,'rev-parse','HEAD:'+CANON)==SRC_BLOB,'CANONICAL_GIT_BLOB_CHANGED')
 source=(repo/CANON).read_bytes();require(sha(source)==SRC_SHA,'CANONICAL_SOURCE_SHA_CHANGED')
 meta=json.loads((repo/MODEL_META).read_text('utf8'))
 require(meta['active_model']['sha256']==SRC_SHA and meta['active_model']['version']=='0.6.17',
         'CANONICAL_MODEL_MANIFEST_CHANGED')
 core.one_model(repo)
 print('RESOLVED_REPO='+str(repo.resolve()),flush=True)
 print('EXECUTION_DIR='+str(Path.cwd()),flush=True)
 print('BRANCH='+core.gout(repo,'rev-parse','--abbrev-ref','HEAD'),flush=True)
 print('HEAD='+head,flush=True)
 print('CANONICAL_SOURCE_SHA='+SRC_SHA,flush=True)
 agents=(repo/'AGENTS.md')
 before=agents.read_bytes()
 addition=(root/'AGENTS_ADDENDUM.md').read_bytes()
 if POLICY_MARK.encode() not in before:
  require(sha(before)==AGENTS_OLD_SHA,'AGENTS_MD_CHANGED__DO_NOT_OVERWRITE')
  policy=before.rstrip(b'\n')+b'\n\n'+addition
 else:
  require(before.endswith(addition),'AGENTS_APPEND_MISMATCH')
  policy=before
 # First publish the exact source and requested additive policy. Even when an
 # animation is infeasible, this commissioned Git source and doctrine survive.
 if not (repo/'campaigns/repl_cartoon_fk_hoof_driver_v0_6_19.py').exists():
  require(head==PARENT,'SOURCE_BOOTSTRAP_FROM_UNEXPECTED_HEAD')
  for dest,rel in FILES.items():
   target=repo/dest;src=(packet/rel).resolve()
   require(src.is_relative_to(root) and src.is_file(),'SOURCE_FILE_MISSING:'+rel)
   require(not target.exists() and not target.is_symlink(),'PREPUBLICATION_FILENAME_COLLISION:'+dest)
   require('v0.6.19' in dest or 'v0_6_19' in dest,'STALE_SOURCE_DESTINATION:'+dest)
  agents.write_bytes(policy)
  require(agents.read_bytes()==policy,'AGENTS_WRITE_READBACK_MISMATCH')
  for dest,rel in FILES.items():
   target=repo/dest;target.parent.mkdir(parents=True,exist_ok=True)
   target.write_bytes((packet/rel).resolve().read_bytes())
  files=['AGENTS.md',*FILES]
  core.git(repo,'add','--',*files)
  staged=core.git(repo,'diff','--cached','--name-only').stdout.splitlines()
  require(set(staged)==set(files),'UNEXPECTED_STAGED_FILE_SET')
  core.git(repo,'-c','user.name=Repl Termux Campaign',
   '-c','user.email=repl-termux-campaign@users.noreply.github.com',
   'commit','-m','Document Repl contact limitations and pin stance repair source v0.6.19')
  authored=core.gout(repo,'rev-parse','HEAD')
  core.push(repo,PARENT)
  require(core.gout(repo,'ls-remote','origin','refs/heads/main').split()[0]==authored,
          'SOURCE_GIT_REMOTE_READBACK_FAILED')
  print('SCRIPT_AND_AGENTS_PUBLISHED_SHA='+authored,flush=True)
 else:
  require(agents.read_bytes()==policy,'AGENTS_ALREADY_PUBLISHED_MISMATCH')
  for dest,rel in FILES.items():
   require((repo/dest).read_bytes()==(packet/rel).resolve().read_bytes(),
           'SOURCE_REPLAY_FILE_DIFFERENT:'+dest)
  print('SCRIPT_AND_AGENTS_PUBLISHED_SHA='+head,flush=True)
 print('AGENTS_APPEND_VERIFIED=PASS',flush=True)
 # Canonical source must still be unchanged before candidate construction.
 require(sha((repo/CANON).read_bytes())==SRC_SHA,'SOURCE_CHANGED_AFTER_AGENTS_PUBLICATION')
 reference=json.loads((packet/'stance_reference.json').read_text('utf8'))
 model=load(packet/'model.py','repl18_model')
 base=load(repo/'campaigns/repl_hair_bind_v0_1_0.py','repl18_base')
 base.EXPECTED_JOINTS=50
 previous=load(repo/'campaigns/repl_cartoon_fk_hoof_model_v0_6_8.py','repl18_prev')
 verifier=load(repo/'campaigns/repl_cartoon_fk_hoof_model_v0_6_17.py','repl18_verified_previous')
 try:
  candidate,report,failures=model.evaluate(source,reference,base,previous,verifier)
 except Exception as exc:
  diagnostic={'version':VER,'source_sha256':SRC_SHA,
    'status':'MODEL_UNCHANGED__NO_VALID_TWO_JOINT_CYCLE',
    'failure':str(exc),'owner_visual_status':'V0617_BEST_YET_NOT_ACCEPTED',
    'distal_joint_authorization':'NOT_GRANTED',
    'source_and_agents_committed_to_git':True,
    'validated_output_model_committed':False}
  path=down/(PREFIX+'_BLOCKED.json')
  core.publish(path,(json.dumps(diagnostic,indent=2)+'\n').encode())
  print('DIAGNOSTIC='+str(path),flush=True)
  print('MODEL_UNCHANGED=PASS',flush=True)
  print('CAMPAIGN_STATUS=BLOCKED_TWO_JOINT_PHYSICAL_FEASIBILITY',flush=True)
  return 2
 # If and only if all source, physics, secondary & scope checks pass, mutate GLB.
 report.update({'version':VER,'source_git_commit':head,'source_sha256':SRC_SHA,
   'human_visual_acceptance':'PENDING','rejected_previous':'V0617_NOT_YET_APPROVED'})
 old_model=repo/CANON
 require(sha(old_model.read_bytes())==SRC_SHA,'MODEL_CHANGED_DURING_VALIDATION')
 # os and tempfile are imported at module scope: do not shadow inside main.
 fd,tmp=tempfile.mkstemp(prefix='.Repl_v0618_verified_',dir=old_model.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(candidate);f.flush();os.fsync(f.fileno())
  require(sha(Path(tmp).read_bytes())==sha(candidate),'MODEL_STAGING_HASH_ERROR')
  os.replace(tmp,old_model)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 require(sha(old_model.read_bytes())==sha(candidate),'MODEL_WRITE_READBACK_FAILED')
 meta['previous_model']={'version':'0.6.17','sha256':SRC_SHA,
  'owner_visual_acceptance':'BEST_YET_ALMOST_ACCEPTABLE__NOT_FINAL'}
 new=dict(meta['active_model']);new.update({'version':VER,'sha256':sha(candidate),
  'git_blob_sha1':core.gitblob(candidate),'human_visual_acceptance':'PENDING',
  'mode':'FRONT_STANCE_TWO_JOINT_VERIFIED_FULL_CYCLE',
  'measured_knee_and_reach':report.get('kinematic_details',{}),
  'profile':report['candidate_profile']})
 meta['active_model']=new;meta['status']='REPL_V0618_PHYSICAL_PASS_VISUAL_PENDING'
 (repo/MODEL_META).write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n')
 rd=repo/'README.md';rd.write_text(rd.read_text('utf8').rstrip()+'\n\n## Repl v0.6.19 conditional stance repair\n'+
  'The guarded two-joint physical solver passed 1164 frame and 576 midframe checks; '
  'only the four approved front rotation channels changed. Human visual review pending.\n')
 core.git(repo,'add','--',CANON,MODEL_META,'README.md')
 core.git(repo,'-c','user.name=Repl Termux Campaign',
  '-c','user.email=repl-termux-campaign@users.noreply.github.com',
  'commit','-m','Repl measured foreleg stance extension and trailing breakover v0.6.19')
 outcommit=core.gout(repo,'rev-parse','HEAD')
 parent=core.gout(repo,'rev-parse','HEAD^')
 core.push(repo,parent)
 require(core.gout(repo,'ls-remote','origin','refs/heads/main').split()[0]==outcommit,
         'REMOTE_MODEL_GIT_COMMIT_NOT_READBACK')
 require(core.gout(repo,'rev-parse','HEAD:'+CANON)==core.gitblob(candidate),
         'REMOTE_CANONICAL_MODEL_BLOB_WRONG')
 reportpath=down/(PREFIX+'_report.json')
 core.publish(reportpath,(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
 html=core.make_viewer(packet,repo,candidate).replace(b'v0.6.17',b'v0.6.19')
 core.publish(down/(PREFIX+'_TEXTURED_POSE_LAB.html'),html)
 print('PHYSICAL_GAIT_VALIDATION=PASS',flush=True)
 print('REMOTE_MODEL_SHA='+outcommit,flush=True)
 print('MODEL_SHA256='+sha(candidate),flush=True)
 print('REPORT='+str(reportpath),flush=True)
 print('HUMAN_VISUAL_ACCEPTANCE=PENDING',flush=True)
 return 0

if __name__=='__main__':
 try:sys.exit(main())
 except Exception as exc:
  print('CAMPAIGN_STATUS=BLOCKED',flush=True)
  print('CAUSE='+type(exc).__name__+':'+str(exc)[:1200],flush=True)
  sys.exit(2)
