"""Read-only host checks for campaign packet, atomic-copy collision, hard locks, and sourceless behavior."""
import importlib.util,json,hashlib,pathlib,tempfile,ast,sys
p=pathlib.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('campaign_under_test',p/'driver.py')
d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
assert d.VENDOR_SHA=='8c91ff4f4d898bab835b3587f17585487056b60b'
assert d.DONOR_SHA!='' and d.TARGET_SHA!=''
assert d.MODEL in d.LOCKED and 'assets/repl/Repl.glb' in d.LOCKED
assert all('/' in k for k in d.SOURCE)
assert len(set(d.SOURCE)|set(d.OUTPUT))==len(d.SOURCE)+len(d.OUTPUT)
assert d.packet_guard(p)
with tempfile.TemporaryDirectory() as tmp:
 t=pathlib.Path(tmp);s=t/'src';s.write_bytes(b'verified');dst=t/'dst';d.safe_copy(s,dst);assert dst.read_bytes()==b'verified'
 try:d.safe_copy(s,dst);raise AssertionError('collision not detected')
 except RuntimeError as exc:assert 'DESTINATION_COLLISION' in str(exc)
 assert dst.read_bytes()==b'verified'
 # Fail closed on one corrupted member, preserve original packet and model.
 copies=t/'packet';copies.mkdir()
 for name in ('driver.py','blender_trial.py','contract.json','manifest.json'):(copies/name).write_bytes((p/name).read_bytes())
 (copies/'blender_trial.py').write_bytes(b'corrupted')
 try:d.packet_guard(copies);raise AssertionError('bad packet accepted')
 except RuntimeError as exc:assert 'PACKET_MEMBER_SHA_FAIL' in str(exc)
 assert not (t/'assets').exists()
for name in ('driver.py','blender_trial.py'):
 tree=ast.parse((p/name).read_text());assert tree
 print('AST_OK='+name)
print('TESTS_PASS: pin, contract, packet, tamper rejection, no overwrite, source invariants')
