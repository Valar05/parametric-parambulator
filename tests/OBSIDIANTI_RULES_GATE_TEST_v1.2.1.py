#!/usr/bin/env python3
"""Guard against the exact v1.2.0 capital-R false rejection using real git.

Runs an isolated disposable Git repo and never contacts the owner's remote.
"""
from __future__ import annotations
import importlib.util, pathlib, subprocess, tempfile, sys

def execute(*args,cwd=None):
 p=subprocess.run(args,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 return p.stdout.strip()

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test.py ABSOLUTE_RUNNER_PATH')
 path=pathlib.Path(sys.argv[1]).resolve()
 spec=importlib.util.spec_from_file_location('obsidianti_gate_runner',path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 with tempfile.TemporaryDirectory(prefix='obsidianti-rules-gate-') as tmp:
  repo=pathlib.Path(tmp)/'target-repo';repo.mkdir()
  execute('git','init','-q',str(repo))
  execute('git','config','user.email','test@example.invalid',cwd=repo)
  execute('git','config','user.name','Fixture',cwd=repo)
  agent=repo/'AGENTS.md'
  agent.write_text('# AGENTS.md — Mandatory repository boot gate\n\n'
    'Repository: Valar05/parametric-parambulator.\n'
    'Authorized mutation and execution: Termux Git only.\n'
    '**Read the live Campaign Etiquette document** for every campaign turn.\n'
    + 'The Git object SHA and clean source checkout are verified before any asset modification.\n'*8)
  execute('git','add','AGENTS.md',cwd=repo)
  execute('git','commit','-qm','Add canonical policy',cwd=repo)
  out=mod.read_repo_rules(repo)
  assert out['rulesAuthority']=='VERIFIED_GIT_TRACKED_REPO_AGENTS_POLICY'
  assert len(out['agentsGitBlob'])==40
  print('ACTUAL_CAPITAL_R_PROSE_ACCEPTED=PASS',flush=True)
  agent.write_text(agent.read_text().replace('Termux Git only','Windows only'))
  try:mod.read_repo_rules(repo)
  except RuntimeError as e:
   assert 'AGENTS_NOT_GIT_TRACKED_OR_MODIFIED' in str(e)
  else:raise AssertionError('MUTATED_AGENTS_WAS_ACCEPTED')
  print('UNCOMMITTED_AGENTS_REJECTED=PASS',flush=True)
  execute('git','checkout','--','AGENTS.md',cwd=repo)
  agent.write_text(agent.read_text().replace('Valar05/parametric-parambulator','other/repository'))
  execute('git','add','AGENTS.md',cwd=repo)
  execute('git','commit','-qm','Simulate wrong policy in tracked source',cwd=repo)
  try:mod.read_repo_rules(repo)
  except RuntimeError as e:
   assert 'WRONG_POLICY_DOCUMENT' in str(e)
  else:raise AssertionError('WRONG_REPOSITORY_RULES_ACCEPTED')
  print('WRONG_TRACKED_REPO_POLICY_REJECTED=PASS',flush=True)
 print('RULES_GATE_REGRESSIONS=PASS',flush=True)

if __name__=='__main__':main()
