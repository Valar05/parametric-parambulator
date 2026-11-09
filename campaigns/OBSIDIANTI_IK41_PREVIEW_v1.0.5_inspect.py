"""Enforce exactly 41 nonempty exported baked-motion GLB tracks."""
import pathlib,sys,struct,json,hashlib
src,dst,expected=map(str,sys.argv[1:4]);data=pathlib.Path(src).read_bytes()
assert hashlib.sha256(data).hexdigest()==expected,'REVIEW_GLB_SHA_MISMATCH'
assert data[:4]==b'glTF' and struct.unpack_from('<I',data,4)[0]==2,'NOT_GLB_V2'
assert struct.unpack_from('<I',data,8)[0]==len(data),'GLB_HEADER_SIZE_MISMATCH'
n,tag=struct.unpack_from('<I4s',data,12);assert tag==b'JSON','GLB_JSON_MISSING'
obj=json.loads(data[20:20+n]);an=obj.get('animations',[])
names=[a.get('name','') for a in an]
assert len(names)==41,'IK_PREVIEW_EXPECTED_41_GOT_'+str(len(names))+' '+repr(names)
assert len(set(names))==41 and all(names),'EMPTY_OR_DUPLICATE_CLIP_NAME'
assert obj.get('skins') and obj.get('meshes'),'NO_RIG_OR_MESH'
assert all(a.get('channels') and a.get('samplers') for a in an),'EMPTY_ANIMATION_CLIP'
assert not any('FK_REFERENCE_DO_NOT_EDIT' in x.get('name','') for x in obj.get('nodes',[])),'REFERENCE_RIG_EXPORTED'
doc={'status':'IK41_BAKED_REVIEW_GLB_VALID','sha256':expected,'clipCount':41,'clips':names,'skins':len(obj['skins']),'meshes':len(obj['meshes']),'ownerVisualAcceptance':'PENDING'}
pathlib.Path(dst).write_text(json.dumps(doc,indent=2)+'\n');print('IK41_REVIEW_GLB_41_CLIPS_VERIFIED',flush=True)
