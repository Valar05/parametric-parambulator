#!/usr/bin/env python3
"""Fail-closed AGENTS.md read/install gate for Repl v0.6.17.

Invoked by the ONE Termux campaign entrypoint, not a second operator command.
Only creates root AGENTS.md if it was absent at the exact pinned source
revision. Does not replace a different pre-existing policy file.
"""
from __future__ import annotations
import hashlib,json,os
from pathlib import Path

RULES_URL='https://docs.google.com/document/d/1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI/edit'
MANDATORY=('EVERY agent turn','Termux Git only','BEFORE','owner visual acceptance','v0.6.16','AGENTS.md')
class RulesBlocked(RuntimeError):pass

def require(ok,message):
 if not ok:raise RulesBlocked(message)
def sha(b):return hashlib.sha256(b).hexdigest()

def read_gate(template, contract):
 """Called before checkout or ANY repository mutation."""
 template,contract=Path(template),Path(contract)
 require(template.is_file() and contract.is_file(),'RULES_FILE_MISSING')
 policy=template.read_bytes();data=json.loads(contract.read_text('utf8'))
 text=policy.decode('utf8')
 require(text.startswith('# AGENTS.md') and all(x in text for x in MANDATORY) and RULES_URL in text,
         'AGENTS_TEMPLATE_REQUIRED_RULES_MISSING')
 require(data.get('campaign_etiquette')==RULES_URL and data.get('execution_lane')=='TERMUX_GIT_ONLY',
         'CONTRACT_RULES_POINTER_MISMATCH')
 require(data.get('version')=='0.6.17' and data.get('solver_version')=='0.6.16',
         'CONTRACT_VERSION_OR_SOLVER_MISMATCH')
 print('AGENTS_READ_BEFORE_WORK=PASS',flush=True)
 print('CAMPAIGN_ETIQUETTE_POINTER='+RULES_URL,flush=True)
 print('AGENTS_SOURCE_SHA256='+sha(policy),flush=True)
 return sha(policy)

def destination_preflight(repo,packet,dest_map):
 """Checks every destination BEFORE any canonical model write."""
 repo=Path(repo).resolve();packet=Path(packet).resolve()
 expected=set(dest_map)
 require('AGENTS.md' in expected,'AGENTS_DESTINATION_REQUIRED')
 require(len(expected)==len(dest_map),'DUPLICATE_PUBLICATION_DESTINATION')
 for dest,rel in dest_map.items():
  relative=Path(dest)
  require(not relative.is_absolute() and '..' not in relative.parts,
          'BAD_REPO_DESTINATION:'+dest)
  require(dest=='AGENTS.md' or 'v0.6.17' in dest or 'v0_6_17' in dest,
          'OLD_CAMPAIGN_FILENAME_PRESENT:'+dest)
  target=repo/relative
  require(target.resolve().is_relative_to(repo), 'DESTINATION_OUTSIDE_REPO:'+dest)
  require(not target.exists() and not target.is_symlink(),
          'DESTINATION_COLLISION_BEFORE_GLB_WRITE:'+dest)
  src=(packet/rel).resolve()
  require(src.is_relative_to(packet.parent) and src.is_file(),
          'PACKET_SOURCE_NOT_PRESENT:'+rel)
  require(target.parent==repo or not target.parent.is_symlink(),
          'DESTINATION_PARENT_SYMLINK:'+dest)
 print('PREPUBLICATION_DESTINATION_COLLISION_GATE=PASS_'+str(len(dest_map)),flush=True)
 return True

def install(repo,policy_file):
 """Atomic exclusive creation; refuses to modify any other file."""
 repo=Path(repo);source=Path(policy_file).read_bytes()
 target=repo/'AGENTS.md'
 require(not target.is_symlink(),'AGENTS_SYMLINK_DENIED')
 try:
  fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
 except FileExistsError as e:
  raise RulesBlocked('AGENTS_POLICY_ALREADY_EXISTS_NO_OVERWRITE') from e
 try:
  with os.fdopen(fd,'wb') as f:f.write(source);f.flush();os.fsync(f.fileno())
 except BaseException:
  try:target.unlink()
  except OSError:pass
  raise
 require(target.read_bytes()==source,'AGENTS_READBACK_MISMATCH')
 print('AGENTS_INSTALLED_SHA256='+sha(source),flush=True)
 return sha(source)
