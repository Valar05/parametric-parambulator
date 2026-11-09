"""Structural GLB review gate. No claim of mathematical motion parity."""
import json,struct,pathlib,sys,hashlib
p=pathlib.Path(sys.argv[1]);dst=pathlib.Path(sys.argv[2]);expected=sys.argv[3]
b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==expected,'GLB_SHA_MISMATCH'
assert len(b)>28 and b[:4]==b'glTF' and struct.unpack_from('<I',b,4)[0]==2,'INVALID_GLTF'
assert struct.unpack_from('<I',b,8)[0]==len(b),'GLB_LENGTH_MISMATCH'
n,tag=struct.unpack_from('<I4s',b,12);assert tag==b'JSON','MISSING_GLB_JSON'
j=json.loads(b[20:20+n]);animations=j.get('animations',[])
names=[a.get('name','') for a in animations]
assert len(animations)==41,'EXPECTED_41_EXPORTED_ANIMATIONS_GOT_'+str(len(animations))+' '+repr(names)
assert len(set(names))==41,'DUPLICATE_EXPORTED_CLIP_NAMES'
assert j.get('skins') and j.get('meshes'),'EXPORTED_RIG_OR_MESH_MISSING'
assert all(a.get('channels') and a.get('samplers') for a in animations),'EMPTY_EXPORTED_ANIMATION'
assert not any('FK_REFERENCE_DO_NOT_EDIT' in x.get('name','') for x in j.get('nodes',[])),'REFERENCE_RIG_LEAKED'
result={'status':'EXPORTED_REVIEW_GLB_STRUCTURALLY_VALID','sha256':expected,'bytes':len(b),'clipCount':len(names),'clips':names,'skinCount':len(j['skins']),'meshCount':len(j['meshes']),'visualAcceptance':'PENDING','poseParity':'NOT_TESTED_BY_REQUEST'}
dst.write_text(json.dumps(result,indent=2)+'\n');print('GLB_REVIEW_GATE_PASS count='+str(len(names)))
