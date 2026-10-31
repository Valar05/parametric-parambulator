"""Synthetic logic tests only; actual owner GLB is not stored in Git."""
import importlib.util
import json
from pathlib import Path

repo=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

base=load(repo/"campaigns/repl_hair_bind_v0_1_0.py","repl_base")
new=load(repo/"campaigns/repl_hair_five_controls_v0_2_0.py","repl_new")

contract=json.loads((repo/"campaigns/REPL_HAIR_FIVE_CONTROLS_V0_2_0_CONTRACT.json").read_text())
assert contract["version"]==new.VERSION=="0.2.0"
assert contract["source"]["sha256"]==new.SOURCE_SHA256
assert new.git_blob_sha((repo/"campaigns/repl_hair_bind_v0_1_0.py").read_bytes())==new.PREDECESSOR_BLOB_SHA
assert len(new.CONTROLS)==5
assert len(set(i[0] for i in new.CONTROLS))==5
assert not set(("Bone_011","Bone_017","Bone_033","Bone_038")) & set(c[1] for c in new.CONTROLS)

j,w=new.normalize4({43:0.25,44:0.5,45:0.25})
assert j==(44,43,45,0) and abs(sum(w)-1)<1e-7

# Synthetic 43-joint identity bind, 46 nodes. This tests the appended
# child-node/IBM indexing and that every hair-only transform starts neutral.
names=tuple(f"Bone_{k:03d}" for k in range(43))
nodes=[{"name":n} for n in names]+[{"name":"geometry_0"},{"name":"SmartRigArmature"},{"name":"geometry_0.001"}]
doc={"nodes":nodes,"skins":[{"joints":list(range(43)),"inverseBindMatrices":77}]}
I=(1.,0.,0.,0., 0.,1.,0.,0., 0.,0.,1.,0., 0.,0.,0.,1.)
class Fake:
  accessor=staticmethod(lambda document,binary,index:[I for _ in range(43)])
  apply_matrix=staticmethod(base.apply_matrix)
  matrix_mult=staticmethod(base.matrix_mult)
indices,mats,manifest,old=new.new_joint_definitions(doc,b"",Fake)
assert len(doc["nodes"])==51 and len(doc["skins"][0]["joints"])==48
assert sorted(indices.values())==list(range(43,48))
for k,mat in enumerate(mats[43:]):
    node=doc["nodes"][46+k]
    assert node["rotation"]==[0,0,0,1]
    assert node["scale"]==[1,1,1]
    assert "hair_only_control"==node["extras"]["role"]
    # At rest, child world is translation(local); multiplication by its
    # inverse bind must yield identity.
    parent_name=new.CONTROLS[k][1]
    parent=next(i for i,n in enumerate(doc["nodes"]) if n["name"]==parent_name)
    assert 46+k in doc["nodes"][parent]["children"]
    world=new.translation_matrix(node["translation"])
    result=base.matrix_mult(world,mat)
    assert max(abs(result[i]-I[i]) for i in range(16))<1e-6

assert all(x>0 for x in contract["limits"].values() if isinstance(x,(int,float)))
print("GIT_SOURCE_COMPILE_AND_SYNTHETIC_BIND=PASS")
print("OWNER_REPL_GLB_PRESENT_IN_CI=NO")
print("REAL_GLB_FIVE_BONE_BIND=NOT_RUN")
print("PHONE_AND_VISUAL_ACCEPTANCE=PENDING")
