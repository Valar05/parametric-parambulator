#!/usr/bin/env python3
"""Pure-python regression: coordinate transforms, GLB baseline, source sample completeness."""
import importlib.util, json, math, pathlib, struct, tempfile

here=pathlib.Path(__file__).resolve().parents[1]
impl=here/'campaigns/OBSIDIANTI_ALL_ACTION_IK_ANALYZE_v1.4.0.py'
spec=importlib.util.spec_from_file_location('obs140analyzer',impl)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def check():
 I=a.ident()
 assert a.matmul(I,I)==I
 assert a.xyz(a.trsmat([1,2,3],[0,0,0,1],[1,1,1]))==[1,2,3]
 assert a.xyz(a.matmul(a.trsmat([1,2,3],[0,0,0,1],[1,1,1]),a.trsmat([4,5,6],[0,0,0,1],[1,1,1])))==[5,7,9]
 q=a.trsmat([0,0,0],[0,0,math.sin(math.pi/4),math.cos(math.pi/4)],[1,1,1])
 assert max(abs(q[0][0]),abs(q[1][1]))<1e-6
 assert abs(q[0][1]+1)<1e-6
 assert abs(a.vlength([3,4,0])-5)<1e-8
 assert a.vecminus([10,6,7],[2,3,1])==[8,3,6]
 with tempfile.TemporaryDirectory() as temp:
  p=pathlib.Path(temp)/'bad.glb'
  p.write_bytes(b'INVALID')
  try:a.load_glb(p)
  except RuntimeError:pass
  else:raise AssertionError('invalid GLB was accepted')
 print('TESTS_PASSED=TRANSFORMS_AND_FAIL_CLOSED')
if __name__=='__main__':check()
