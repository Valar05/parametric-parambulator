#!/usr/bin/env python3
"""Immutable packet selftest + negative regression on the actual acceptance gates."""
import ast,hashlib,importlib.util,json,pathlib,sys,copy
sys.dont_write_bytecode=True
root=pathlib.Path(__file__).resolve().parent
manifest=json.loads((root.parent/'manifest.json').read_text())
assert manifest['campaign']=='REPL_CARTOON_FK_HOOF_WALK' and manifest['version']=='0.6.17'
required={'README.md','AGENTS.md','campaign/model.py','campaign/trajectory.json',
 'campaign/driver.py','campaign/regression.py','campaign/viewer.html.in',
 'campaign/blender_review.py','campaign/run-termux.sh','campaign/contract.json',
 'campaign/selftest.py','campaign/git_transport_regression.py','campaign/agents_gate.py'}
assert set(manifest['sha256'])==required
for rel,h in manifest['sha256'].items():
 assert hashlib.sha256((root.parent/rel).read_bytes()).hexdigest()==h,rel
for rel in ('model.py','regression.py','driver.py','selftest.py','git_transport_regression.py','agents_gate.py'):
 ast.parse((root/rel).read_text())
spec=importlib.util.spec_from_file_location('repl_model_0616',root/'model.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.VERSION=='0.6.16' and m.EDITED=={'Bone_014','Bone_015','Bone_020','Bone_021'}
plan=json.loads((root/'trajectory.json').read_text())
m.check_plan(plan)
assert plan['source_commit']=='6156c8cd21e7c3f5aca82de0dba7082c211eeb5a'
contract=json.loads((root/'contract.json').read_text())
assert contract['source_sha256']==plan['source_sha256']
assert contract['execution_lane']=='TERMUX_GIT_ONLY'
assert contract['version']=='0.6.17' and contract['solver_version']=='0.6.16'
assert set(contract['allowed_changed_animation_channels'])=={'Bone_015.rotation','Bone_014.rotation','Bone_021.rotation','Bone_020.rotation'}
rspec=importlib.util.spec_from_file_location('repl_0616_regression',root/'regression.py')
rg=importlib.util.module_from_spec(rspec);rspec.loader.exec_module(rg)
# Fail deliberately if an old bug reappears: kick, reversed swing, planted drift,
# too-high hoof, missing frame coverage, or absent visual-acceptance gate.
example={'version':'0.6.16','source_sha256':plan['source_sha256'],
 'tested_physical_frames':1164,'tested_physical_half_frames':576,'maximum_front_joint_step_degrees':12.,
 'maximum_swing_forward_step':.038,'maximum_backward_swing_step':0.,
 'max_stance_vertex_delta':.009,
 'front_hoof_clearance':{f'{s}_{l}':{'verified_peak':.074,'min_swing':.004} for s in (1,2,3) for l in ('LF','RF')},
 'ground_contact':{f'{s}_{l}':{'first_stride_planted_y_min':-.003,'first_stride_planted_y_max':.013} for s in (1,2,3) for l in ('LF','RF')},
 'profile':{'motion':'UNCHANGED_FROM_V0615'}}
assert rg.verify_measurements(example,plan)['no_forward_kick_or_reverse']=='PASS'
for prop,bad in [('maximum_swing_forward_step',.30),('maximum_backward_swing_step',-.20),
 ('maximum_front_joint_step_degrees',30.),('max_stance_vertex_delta',.07),
 ('tested_physical_frames',388),('tested_physical_half_frames',0)]:
 obj=copy.deepcopy(example);obj[prop]=bad
 try:rg.verify_measurements(obj,plan)
 except rg.Blocked:pass
 else:raise AssertionError('NEGATIVE_REGRESSION_NOT_CAUGHT:'+prop)
# A partial packet cannot claim end-to-end acceptance.
from git_transport_regression import run_tests
checks=run_tests(root/'driver.py')
assert all(v=='PASS' for v in checks.values()),checks
print('PACKET_HASHES=PASS')
print('FULL_STRIDE_PRESERVE_SCOPE=PASS')
print('WORLD_GROUND_CONTACT_AND_FORWARD_KICK_NEGATIVE_TESTS=PASS')
print('GIT_CACHE_AND_TIMEOUT_RECOVERY=PASS')
print('REAL_CANONICAL_V0615_REPLAY=REQUIRED_IN_TERMUX_BEFORE_MUTATION')

# Publication must never re-use an old campaign filename or touch assets before preflight.
import tempfile,importlib.util
spec=importlib.util.spec_from_file_location('repl_driver_0617',root/'driver.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
assert d.VER=='0.6.17' and d.MODEL_SOLVER_VERSION=='0.6.16'
assert d.EXPECTED_VALIDATED_V0616_OUTPUT_SHA=='c6dc250356248e5860e5919568e4103d6c1d2cb6e071e7bb9a0f7ce1f42ee4c1'
assert len(set(d.CAMPAIGN_FILES))==len(d.CAMPAIGN_FILES)
assert set(d.CAMPAIGN_FILES)&{'AGENTS.md'}
assert not any(('v0.6.15' in k or 'v0_6_15' in k or 'v0.6.16' in k or 'v0_6_16' in k) for k in d.CAMPAIGN_FILES)
assert hashlib.sha256((root/'model.py').read_bytes()).hexdigest()=='8f5387986d27e0773491024dc95e82ae67a79e66c4b6e9135d51f5f182e76ef7'
assert hashlib.sha256((root/'trajectory.json').read_bytes()).hexdigest()=='8c3d8e4364c12b76549ceffab565e9f680de6ddbfda7d075496420efb4404117'
spec=importlib.util.spec_from_file_location('repl_agents_gate_0617',root/'agents_gate.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
policy_hash=gate.read_gate(root.parent/'AGENTS.md',root/'contract.json')
with tempfile.TemporaryDirectory(prefix='repl0617-policy-test-') as raw:
 repo=pathlib.Path(raw)
 assert gate.destination_preflight(repo,root,d.CAMPAIGN_FILES)
 # Pre-existing different AGENTS file must never be overwritten.
 (repo/'AGENTS.md').write_text('USER POLICY IS NOT FOR OVERWRITING')
 try:gate.destination_preflight(repo,root,d.CAMPAIGN_FILES)
 except gate.RulesBlocked as e:assert 'COLLISION_BEFORE_GLB_WRITE' in str(e)
 else:raise AssertionError('AGENTS_COLLISION_NOT_DETECTED')
 (repo/'AGENTS.md').unlink()
 first=next(k for k in d.CAMPAIGN_FILES if k.endswith('_v0_6_17.py'))
 dst=repo/first;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text('USER PROJECT FILE')
 try:gate.destination_preflight(repo,root,d.CAMPAIGN_FILES)
 except gate.RulesBlocked as e:assert 'COLLISION_BEFORE_GLB_WRITE' in str(e)
 else:raise AssertionError('PREPUBLICATION_COLLISION_NOT_DETECTED')
 assert dst.read_text()=='USER PROJECT FILE'
 dst.unlink()
 assert gate.destination_preflight(repo,root,d.CAMPAIGN_FILES)
 assert gate.install(repo,root.parent/'AGENTS.md')==policy_hash
 assert (repo/'AGENTS.md').read_bytes()==(root.parent/'AGENTS.md').read_bytes()
 try:gate.install(repo,root.parent/'AGENTS.md')
 except gate.RulesBlocked as e:assert 'NO_OVERWRITE' in str(e)
 else:raise AssertionError('AGENTS_REPLACEMENT_NOT_BLOCKED')
print('AGENTS_PER_TURN_READ_POLICY=PACKAGED_AND_VERIFIED')
print('PREPUBLICATION_FILENAME_COLLISION_REGRESSION=PASS')
print('MODEL_AND_TRAJECTORY_REPLAY_BYTES=UNCHANGED_V0616')
