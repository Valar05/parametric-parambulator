#!/usr/bin/env python3
"""Source-level sanity preflight, not a replacement for real GLB testing."""
from __future__ import annotations
import importlib.util,json,math,sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root));sys.dont_write_bytecode=True
import fore_constraints as s
import model as m
assert m.VERSION=='0.6.1'
assert m.CANON=='assets/repl/Repl.glb'
assert m.SOURCE_SHA=='edbe9c647839b3c37b627519e8a7477d7fa8720138913ed3b6524d4613212518'
assert len(m.LEGS)==2
assert all(len(z['bones'])==4 for z in m.LEGS.values())
assert s.HIGH[1]>0 and s.LOW[2]<0
assert m.ROOT_TRAVEL>.95
assert len(m.WALK_NAMES)==3
assert m.event(.25,0.,(0.,.04,.243))[1] is False
links=[(0,1,0),(0,-.21,-.115),(0,-.28,-.008),(0,-.25,.008),(0,-.18,-.008)]
q=[-5,45,-60,-12]
assert len(s.fk(links,q))==5
assert len(s.poles(s.fk(links,q)))==2
assert len(s.optimize(links,(0,.18,.25),.5,[27,-15,-25,-8])[0])==4
print('SOURCE_PREFLIGHT=PASS')
print('ACTUAL_OWNER_GLB_TEST=DEFER_TO_REAL_MODEL_DRIVER')
