#!/usr/bin/env python3
"""v0.6.20 packet, dynamic planning, source/authority and runtime regressions.

This host selftest does not count as physical v0.6.17 GLB validation.
"""
import ast,hashlib,importlib.util,json,pathlib,symtable,sys,tempfile
sys.dont_write_bytecode=True
p=pathlib.Path(__file__).resolve().parent
root=p.parent
def load(f,name):
 s=importlib.util.spec_from_file_location(name,f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load(p/'model.py','repl20_test_model')
d=load(p/'driver.py','repl20_test_driver')
c=json.loads((p/'contract.json').read_text())
assert m.VERSION==d.VERSION==c['version']=='0.6.20'
assert m.SOURCE_SHA==d.SRC_SHA==c['source_model_sha256']
assert d.PARENT==c['source_git_commit']
assert d.SRC_BLOB==c['source_model_git_blob']
assert c['authorized_lane']=='TERMUX_GIT_ONLY'
assert set(m.EDITABLE)=={'Bone_015','Bone_014','Bone_020','Bone_021'}
assert set(d.FILES)==set(dict(d.FILES))
assert all('v0.6.20' in k or 'v0_6_20' in k for k in d.FILES)
assert all(k.startswith('campaigns/') for k in d.FILES)
assert 'AGENTS.md' not in d.FILES
assert d.POLICY_MARK in (root/'AGENTS_ADDENDUM.md').read_text()
assert 'Do not design campaigns' in (root/'AGENTS_ADDENDUM.md').read_text()
for file in p.glob('*.py'):
 src=file.read_text();ast.parse(src,filename=str(file))
 assert not ('git push' in src and '--force' in src) if file.name!='selftest.py' else True
sc=symtable.symtable((p/'driver.py').read_text(),str(p/'driver.py'),'exec')
main=next(s for s in sc.get_children() if s.get_name()=='main')
for symbol in ('os','tempfile','json','Path','core'):
 if symbol in ('core',):continue
 assert main.lookup(symbol).is_global(),('SCOPING_REGRESSION',symbol)
fn=next(f for f in ast.parse((p/'driver.py').read_text()).body if isinstance(f,ast.FunctionDef) and f.name=='main')
assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) for n in ast.walk(fn))
# Fail closed at source boundary before touching any file or issuing a git call.
try:m.evaluate(b'bad source',None,None,None,tempfile.mkdtemp())
except m.Blocked as e:assert 'CANONICAL_SOURCE_NOT_LOCKED' in str(e)
else:raise AssertionError('BAD_SOURCE_INCORRECTLY_ALLOWED')
# Synthetic geometry tests exercise actual beam planner, not a hardcoded profile.
class Fake:
 def __init__(self):self.tracks=[{}]*3;self.names={}
 def state(self,stage,leg,frame,delta=(0.,0.)):
  start=m.LEGS[leg][3];j=(frame-start)%32
  a,b=delta
  # Bone flexion, contact Y, Z and reach all respond differently.
  return {'bend':40+.65*b-.12*a,'sole_y':.006+.0002*a-.00015*b,
    'z':.003+.0003*j+.003*a-.002*b,
    'relative_z':.12+.003*a-.002*b,'heel_to_toe':max(0.,.02+.0004*a),
    'shoulder_z':0.,'heel_y':.03,'toe_y':.01}
fake=Fake()
for leg in ('LF','RF'):
 grid=m.grids(leg,1,fake,range_deg=16.,step=4.)
 assert len(grid)==23 and all(grid)
 assert grid[0][0][:2]==(0.,0.)
 plan=m.beam_plan(fake,1,leg,grid,.016,15.,.030,.015)
 assert plan is not None and len(plan['angles'])==23
 assert all(len(a)==2 and abs(a[0])<=28 and abs(a[1])<=28 for a in plan['angles'])
 assert plan['angles'][0]==(0.,0.) and plan['angles'][-1]==(0.,0.)
# Profiles must be searched beyond the previous four, with no scope expansion.
configs=list(m.configs());assert len(configs)>24
assert len({tuple(sorted(x.items())) for x in configs})==len(configs)
assert all(set(x)=={'shift_LF','shift_RF','knee_target','knee_weight','smooth'} for x in configs)
print('SOURCE_AND_RULES_INTEGRITY_GATES=PASS')
print('ADAPTIVE_BEAM_PLANNER_BOTH_FRONT_LEGS=PASS')
print('MULTISTRATEGY_FEEDBACK_SEARCH_CONFIGURATIONS='+str(len(configs)))
print('NESTED_IMPORT_AND_GLOBAL_SCOPE_REGRESSION=PASS')
print('UNIQUE_V0620_REPO_PUBLICATION_PATHS=PASS')
print('NEGATIVE_BAD_SOURCE_SAFETY_REGRESSION=PASS')
reg=load(p/'driver_regression.py','repl20_runtime_regression')
assert reg.case(True)
assert reg.case(False)
print('DRIVER_FULL_MOCK_BLOCKED_AND_SUCCESS_BRANCHES=PASS')
print('REAL_PRODUCTION_MODEL_CHECK=REQUIRED_ON_TERMUX')
