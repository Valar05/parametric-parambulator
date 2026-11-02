#!/usr/bin/env python3
"""Structural, destination, identity, bad-source and full-response regressions."""
from pathlib import Path
import hashlib,sys,json,importlib.util,ast,re,symtable
sys.dont_write_bytecode=True
packet=Path(__file__).resolve().parent
root=packet.parent

def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=json.loads((packet/'contract.json').read_text())
m=load(packet/'model.py','repl18_selftest_solver')
d=load(packet/'driver.py','repl18_selftest_driver')
assert c['source_git_commit']==d.PARENT
assert c['source_model_sha256']==d.SRC_SHA==m.SOURCE_SHA
assert c['authorized_lane']=='TERMUX_GIT_ONLY'
assert c['expected_source_version']=='0.6.17'
assert c['new_version']==m.VERSION=='0.6.19'
assert d.POLICY_MARK in (root/'AGENTS_ADDENDUM.md').read_text()
assert len(d.FILES)==len(set(d.FILES))
assert all('v0.6.19' in x or 'v0_6_19' in x for x in d.FILES)
assert 'AGENTS.md' not in d.FILES
for script in packet.glob('*.py'):
 ast.parse(script.read_text(),filename=str(script))
# Regression for v0.6.18: `import os,tempfile` within `main()` shadowed `os`
# before `os.chdir(repo)` and was invisible to syntax-only checks.
main_scope=next(ch for ch in symtable.symtable((packet/'driver.py').read_text(),str(packet/'driver.py'),'exec').get_children() if ch.get_name()=='main')
assert main_scope.lookup('os').is_global(), 'REGRESSION_OS_SHADOWED_WITHIN_MAIN'
assert main_scope.lookup('tempfile').is_global(), 'REGRESSION_TEMPFILE_SHADOWED_WITHIN_MAIN'
main_ast=next(n for n in ast.parse((packet/'driver.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='main')
assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) for n in ast.walk(main_ast)), 'NESTED_IMPORT_IN_MAIN'
assert all(len(profile[1])==20 for profile in m.reference_profiles())
ref=json.loads((packet/'stance_reference.json').read_text())
assert ref['version']=='0.6.19'
assert set(ref['degree_offsets'])=={'1_LF','1_RF','2_LF','2_RF'}
assert all(set(rows)==set(str(x) for x in range(32)) for rows in ref['degree_offsets'].values())
for leg in ('LF','RF'):
 assert sum(m.phase(leg,i)[1] for i in range(32))==20
try:m.apply(b'wrong',ref,m.reference_profiles()[0],None,None)
except m.Blocked as e:assert 'CANONICAL_SOURCE_CHANGED' in str(e)
else:raise AssertionError('BAD_SOURCE_NOT_REJECTED')
for s in ['model.py','driver.py','git_core.py']:
 assert 'git push --force' not in (packet/s).read_text()
print('PACKET_STATIC_SYNTAX_AND_SOURCE_GUARDS=PASS')
print('UNIQUE_V0619_GIT_DESTINATIONS=PASS')
print('SCOPE_AND_VISUAL_ACCEPTANCE_LOCKS=PASS')
print('SYNTHETIC_UNAUTHORIZED_SOURCE_REJECTION=PASS')
print('REAL_PRODUCTION_GLB_PHYSICS=TERMUX_REQUIRED')

print('ENTRYPOINT_GLOBAL_BINDING_AND_NESTED_IMPORT_REGRESSION=PASS')
# Exercise function execution all the way through the blocked and successful
# publication branches with synthetic Git and GLB fixtures, with NO real push.
reg=load(packet/'driver_regression.py','repl0619_driver_runtime_regression')
reg.case(True)
reg.case(False)
print('MOCK_FULL_DRIVER_BLOCKED_AND_SUCCESS_EXECUTION_PATHS=PASS')
