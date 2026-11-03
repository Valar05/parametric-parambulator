#!/usr/bin/env python3
"""Packet integrity plus contract/trajectory regression before loading Git models."""
from __future__ import annotations
import ast,hashlib,importlib.util,json,pathlib,sys,math
sys.dont_write_bytecode=True
root=pathlib.Path(__file__).resolve().parent
manifest=json.loads((root.parent/'manifest.json').read_text('utf8'))
assert manifest['campaign']=='REPL_CARTOON_FK_HOOF_WALK' and manifest['version']=='0.6.15'
required={'README.md','campaign/model.py','campaign/trajectory.json',
  'campaign/driver.py','campaign/regression.py','campaign/viewer.html.in','campaign/blender_review.py',
  'campaign/run-termux.sh','campaign/contract.json','campaign/selftest.py',
  'campaign/git_transport_regression.py'}
assert set(manifest['sha256'])==required
for rel,h in manifest['sha256'].items():
 p=root.parent/rel;assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h,rel
for name in ('model.py','regression.py','driver.py','selftest.py','git_transport_regression.py'):
 ast.parse((root/name).read_text('utf8'))
spec=importlib.util.spec_from_file_location('repl_measured_low_forehooves',root/'model.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.VERSION=='0.6.15' and m.CANON=='assets/repl/Repl.glb'
assert m.EDITED=={'Bone_014','Bone_015','Bone_020','Bone_021'}
assert m.MIN_SWING_Y>=.003 and m.MAX_PEAK_Y<=.102
assert m.TARGET_MIN>=.24 and m.TARGET_MAX<=.34
p=json.loads((root/'trajectory.json').read_text('utf8'))
assert p['source_sha256']==m.SOURCE_SHA and p['version']==m.VERSION
assert p['ground_y']==m.GROUND_Y
assert p['body_settle']==.0016 and p['body_roll_degrees']==.30
assert set(p['angle_offsets_degrees'])=={'1_LF','1_RF','2_LF','2_RF'}
for stage in (1,2):
 for label in m.FRONT:
  key=f'{stage}_{label}';angles=p['angle_offsets_degrees'][key]
  expected={str(f) for f in range(m.PERIOD) if not m.phase(label,f)[1]}
  assert set(angles)==expected
  assert p['development_measurements'][key]['peak']>0.07
  assert p['development_measurements'][key]['min']>=.004
  for f,v in angles.items():
   assert len(v)==2 and all(math.isfinite(t) for t in v)
   assert -55<=v[0]<=55 and -32<=v[1]<=40
assert len(p['angle_offsets_degrees']['1_LF'])==12
assert len(p['angle_offsets_degrees']['1_RF'])==12
contract=json.loads((root/'contract.json').read_text('utf8'))
assert contract['version']==m.VERSION
assert contract['source_sha256']==m.SOURCE_SHA
assert contract['execution_lane']=='TERMUX_GIT_ONLY'
assert contract['source_head']=='f0927b29e3525018999a223f219c38866dc9b9c0'
# The real-GLB reference test, run before shipping, is frozen in the contract.
ref=contract['host_measured_candidate_verification']
assert ref['physical_frame_hoof_pairs']==1164
assert ref['real_source_sha256']==m.SOURCE_SHA
assert ref['swing_min_world_y']>.0035
assert ref['maximum_stance_vertex_delta']<.014
assert all(.245<=v<=.335 for v in ref['peak_lift_ratios'].values())
# The independent numeric guard also needs to compile.
assert 'verify_measurements' in (root/'regression.py').read_text('utf8')
# Avoid historical bugs: no unresolved global_alpha, no synthetic-only proof claim.
assert 'global_alpha' not in (root/'model.py').read_text('utf8')
assert 'def verify(' in (root/'model.py').read_text('utf8')
# Our Git checkout infrastructure is tested separately with a disposable fake Git repo.
sys.path.insert(0,str(root))
from git_transport_regression import run_tests
checks=run_tests(root/'driver.py')
assert all(v=='PASS' for v in checks.values()),checks
print('PACKET_HASHES=PASS')
print('PINNED_MEASURED_TRAJECTORY=PASS')
print('GIT_CACHE_AND_TIMEOUT_RECOVERY=PASS')
print('REGRESSION_NO_STALE_GLOBAL_ALPHA=PASS')
print('PRODUCTION_GLTF_LOCAL_PREFLIGHT=PASS__DEVICE_RECHECK_PENDING')
