#!/usr/bin/env python3
"""Fast invariant checks. Actual source-skinned three-stage run is mandatory next."""
from pathlib import Path
import sys,math
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import fore_constraints as s,model as m
assert m.VERSION=='0.6.2'
assert m.CANON=='assets/repl/Repl.glb'
assert m.SOURCE_SHA=='af261c92bbfeca49a1fc064df4fa31d355f8df16c13b79ec056951822a4be78d'
assert m.LEGS['LF']['upper']=='Bone_014' and m.LEGS['LF']['lower']=='Bone_013'
assert m.LEGS['RF']['upper']=='Bone_020' and m.LEGS['RF']['lower']=='Bone_019'
for leg in m.LEGS.values():
 assert len(leg['bones'])==4 and leg['upper']==leg['bones'][1] and leg['lower']==leg['bones'][2]
assert m.ROOT_TRAVEL==.96 and len(m.WALK_NAMES)==3
assert m.phase_at(.25,0)[1] is False
links=[(0,1,0),(0,-.21,-.115),(0,-.28,-.008),(0,-.25,.008),(0,-.18,-.008)]
assert len(s.fk(links,[-5,45,-60,-12]))==5
assert len(s.poles(s.fk(links,[-5,45,-60,-12])))==2
print('PACKET_STATIC_PREFLIGHT=PASS')
print('REAL_CANONICAL_MODEL_FULL_TEST=REQUIRED_NEXT')
