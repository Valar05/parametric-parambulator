#!/usr/bin/env python3
"""Source-only synthetic tests. This repository does NOT contain Repl.glb.
A green CI run is NOT proof of actual weighted GLB execution or visual review.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name, ROOT/path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

engine=load("campaigns/repl_tail_four_controls_v0_3_0.py","repl_v030")
prev=load("campaigns/repl_hair_five_controls_v0_2_0.py","repl_v020")
base=load("campaigns/repl_hair_bind_v0_1_0.py","repl_v010")

assert engine.VERSION=="0.3.0"
assert engine.PREDECESSOR_BLOB_SHA == prev.git_blob_sha(
    (ROOT/"campaigns/repl_hair_five_controls_v0_2_0.py").read_bytes()
)
assert engine.SOURCE_SHA256 == prev.SOURCE_SHA256 == base.SOURCE_SHA256
assert engine.TAIL_NAMES[:2] == ("REPL_TAIL_BASE","REPL_TAIL_TIP")
assert len(engine.TAIL_NAMES)==4
assert len(engine.MANE_NAMES)==3
lengths=engine.check_progressive_lengths()
assert len(lengths)==3 and lengths[0]>lengths[1]>lengths[2]>0
for u in [0,.01,.20,.50,.51,.70,.79,.80,.91,1]:
    w=engine.axial_weights(u)
    assert len(w)==4 and all(x>=0 for x in w)
    assert abs(sum(w)-1)<1e-12
    assert sum(x>0 for x in w)<=2
assert engine.axial_weights(0)==(1,0,0,0)
assert engine.axial_weights(1)==(0,0,0,1)
assert all(abs(engine.loop_wave(t,lag))<1e-12
           for t in (0,4) for lag in (.0,.2,.4,.6))

# A synthetic hierarchical bone system with old 48 joint slots.
# Verify that adding the two controls preserves all mane node identities,
# preserves original inverse bind matrices, and creates rest-canceling
# child matrices for the new tail joints.
identity=(1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.)
doc={
    "buffers":[{"byteLength":0}],
    "bufferViews":[],
    "accessors":[],
    "nodes":[{"name":"Bone_" + str(i)} for i in range(51)],
    "skins":[{"joints":list(range(48))}]
}
for i,name in enumerate(engine.MANE_NAMES+engine.TAIL_NAMES[:2]):
    doc["nodes"][43+i]={"name":name,"translation":[0,0,0]}
# The first two tail nodes already form a chain in v0.2.
doc["nodes"][46]["children"]=[47]
raw=bytearray()
idx=base.emit_accessor(doc,raw,[identity]*48,5126,"MAT4")
doc["skins"][0]["inverseBindMatrices"]=idx
original_mane=json.dumps(doc["nodes"][43:46],sort_keys=True)
ibms,idxmap,manifest=engine.add_descendants(doc,bytes(raw),prev,base)
assert len(doc["nodes"])==53 and len(doc["skins"][0]["joints"])==50
assert json.dumps(doc["nodes"][43:46],sort_keys=True)==original_mane
assert [r["name"] for r in manifest]==list(engine.TAIL_NAMES[2:])
assert 51 in doc["nodes"][47]["children"] and 52 in doc["nodes"][51]["children"]
assert all(ibms[i] == prev.matrix_from_glb_mat4(identity) for i in range(48))
for name,pivot in zip(engine.TAIL_NAMES[2:],engine.TAIL_PIVOTS[2:]):
    i,n=idxmap[name]
    assert all(abs(a-b)<1e-6 for a,b in zip(doc["nodes"][n]["translation"],pivot))

# The generated second clip touches only the four declared tail controls.
doc["animations"]=[{"name":"locked-neck-clip","samplers":[],"channels":[]}]
sampled=engine.add_tail_clip(doc,raw,base,idxmap)
assert len(doc["animations"])==2
assert doc["animations"][0]["name"]=="locked-neck-clip"
assert len(doc["animations"][1]["channels"])==4
assert len(sampled)==4
assert all(c["target"]["path"]=="rotation" for c in doc["animations"][1]["channels"])
assert {c["target"]["node"] for c in doc["animations"][1]["channels"]} == {
    idxmap[name][1] for name in engine.TAIL_NAMES
}
assert "__GLB_BASE64__" in engine.HTML_TEMPLATE
assert "GLTFLoader" in engine.HTML_TEMPLATE
assert "Save full-resolution PNG frame" in engine.HTML_TEMPLATE
print("SYNTHETIC_TAIL_CHAIN=PASS")
print("PROGRESSIVE_LENGTHS=" + json.dumps([round(v,6) for v in lengths]))
print("FOUR_TAIL_ONLY_ROTATION_CHANNELS=PASS")
print("LOCKED_THREE_MANE_NODE_NAMES=PASS")
print("ACTUAL_OWNER_GLB_TEST=NOT_RUN_NO_ASSET_IN_PUBLIC_GITHUB")
print("FULL_TEXTURED_RUNTIME_REVIEW=HUMAN_PENDING")
