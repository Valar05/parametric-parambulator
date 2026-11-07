#!/usr/bin/env python3
"""Offline regression: real GLB2 binary shape, animation preservation, failures."""
import importlib.util,sys,tempfile,pathlib,json,struct
spec=importlib.util.spec_from_file_location('merger',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def mini(path,clip,shift=0.0):
 data=struct.pack('<ffffffff',0,0,0,1,0,0,0,2) # two floating-point time samples plus vec3 values
 js={'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':[0]}],
  'nodes':[{'name':'Root','children':[1],'translation':[0+shift,0,0]},{'name':'mixamorig:Hips','translation':[0,0,0]}],
  'skins':[{'joints':[1],'inverseBindMatrices':0}], 'meshes':[{'primitives':[{'attributes':{'POSITION':0}}]}],
  'buffers':[{'byteLength':len(data)}], 'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':len(data)}],
  'accessors':[{'bufferView':0,'componentType':5126,'count':2,'type':'VEC4'},
   {'bufferView':0,'componentType':5126,'count':2,'type':'SCALAR'}],
  'animations':[{'name':clip,'samplers':[{'input':1,'output':0,'interpolation':'LINEAR'}],
     'channels':[{'sampler':0,'target':{'node':1,'path':'translation'}}]*10}]}
 m.assemble(js,data,path)

with tempfile.TemporaryDirectory() as d:
 d=pathlib.Path(d)
 mini(d/'A.glb','A');mini(d/'B.glb','B')
 args=[{'name':'A','path':str(d/'A.glb')},{'name':'B','path':str(d/'B.glb')}]
 r=m.merge(args,d/'output.glb',d/'REPORT.json')
 assert r['merged']['clips']==2
 base,_=m.load(d/'output.glb')
 assert [x['name'] for x in base['animations']]==['A','B']
 assert base['animations'][1]['samplers'][0]['output']>=2
 try:
  m.merge(args+[args[0]],d/'bad.glb',d/'bad.json')
  raise AssertionError('duplicate clip should fail')
 except ValueError as e:assert 'DUPLICATE_ANIMATION_NAME' in str(e)
 mini(d/'C.glb','C',shift=0.5)
 try:
  m.merge(args+[{'name':'C','path':str(d/'C.glb')}],d/'bad.glb',d/'bad.json')
  raise AssertionError('incompatible skeleton should fail')
 except ValueError as e:assert 'REST_NODE_TRANSFORM_CHANGED' in str(e)
 b=(d/'A.glb').read_bytes();(d/'broken.glb').write_bytes(b[:-4])
 try:
  m.load(d/'broken.glb');raise AssertionError('invalid GLB should fail')
 except ValueError as e:assert 'INVALID_GLB_LENGTH' in str(e)
 print('TESTS=PASS GLB_ROUNDTRIP TWO_CLIPS SAMPLER_REMAP DUPLICATE_GUARD SKELETON_GUARD TRUNCATION_GUARD')
