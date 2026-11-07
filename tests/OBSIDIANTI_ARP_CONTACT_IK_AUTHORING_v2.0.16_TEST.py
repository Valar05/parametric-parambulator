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


# Regression for the exact v2.0.15 failure: main is a shallow tip two
# commits newer than the pinned base. Local disposable fixtures only.
def test_shallow_main_history():
 import subprocess,os
 from pathlib import Path
 def run(*args, cwd=None, check=True):
  p=subprocess.run([str(x) for x in args],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  if check and p.returncode:raise AssertionError('git fixture '+repr(args)+' '+p.stderr)
  return p.stdout.strip()
 d=Path(tempfile.mkdtemp(prefix='arp-git-ancestry-'))
 try:
  bare=d/'upstream.git';writer=d/'writer';shallow=d/'shallow'
  run('git','init','--bare',bare)
  run('git','clone',bare,writer)
  run('git','config','user.name','Test Runner',cwd=writer)
  run('git','config','user.email','tester@example.invalid',cwd=writer)
  run('git','checkout','-b','main',cwd=writer)
  (writer/'one').write_text('one');run('git','add','one',cwd=writer);run('git','commit','-m','base',cwd=writer)
  base=run('git','rev-parse','HEAD',cwd=writer)
  for i in (2,3):
   (writer/str(i)).write_text(str(i));run('git','add',str(i),cwd=writer);run('git','commit','-m','advance',cwd=writer)
  tip=run('git','rev-parse','HEAD',cwd=writer);run('git','push','-u','origin','main',cwd=writer)
  # file:// is required; a plain path clone ignores --depth.
  run('git','clone','--depth=1','--branch=main','file://'+str(bare),shallow)
  assert run('git','rev-parse','--is-shallow-repository',cwd=shallow)=='true'
  # Verify exact old failure, without changing user repo history.
  assert subprocess.run(['git','merge-base','--is-ancestor',base,tip],cwd=shallow,capture_output=True).returncode!=0
  import importlib.util
  driverpath=Path(sys.argv[1]).with_name('driver.py')
  spec=importlib.util.spec_from_file_location('campaign_boot',driverpath)
  driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
  proof=driver.verify_pinned_ancestry(shallow,base,tip)
  assert proof['isAncestor'] and proof['method'] in ('DEEPEN_16','DEEPEN_128','DEEPEN_512','UNSHALLOW')
  assert run('git','rev-parse','HEAD',cwd=shallow)==tip
  assert subprocess.run(['git','merge-base','--is-ancestor',base,tip],cwd=shallow,capture_output=True).returncode==0
  # A known but unrelated pinned base must still be rejected.
  unrelated=d/'unrelated';run('git','init',unrelated);run('git','config','user.name','Test Runner',cwd=unrelated);run('git','config','user.email','tester@example.invalid',cwd=unrelated)
  (unrelated/'other').write_text('other');run('git','add','other',cwd=unrelated);run('git','commit','-m','unrelated',cwd=unrelated)
  bogus=run('git','rev-parse','HEAD',cwd=unrelated)
  try:driver.verify_pinned_ancestry(shallow,bogus,tip)
  except RuntimeError as e:assert 'PINNED_GIT_BASE_NOT_ANCESTOR' in str(e)
  else:raise AssertionError('unrelated history incorrectly accepted')
  print('GIT_BOOT_REGRESSION=PASS SHALLOW_TWO_COMMITS_DEEPENED FULL_HISTORY_GUARD_UNRELATED_BASE_REJECTED')
 finally:
  shutil.rmtree(d)

import shutil
test_shallow_main_history()
