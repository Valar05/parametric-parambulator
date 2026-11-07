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

# Regression: detect all populated Ares slots, not one Action name per motion.
# This is the precise defect that lost Cross-Enemy and eight Step actions.
def test_all_source_slots():
 import types,importlib.util
 fake=types.ModuleType('bpy')
 class Slot:
  def __init__(self,s):self.identifier=s;self.target_id_type='OBJECT'
 class Curve:
  def __init__(self,i):
   self.data_path='pose.bones["mixamorig:LeftArm"].rotation_euler'
   self.keyframe_points=[types.SimpleNamespace(co=types.SimpleNamespace(y=0.)),types.SimpleNamespace(co=types.SimpleNamespace(y=float(i+1)))]
 class Strip:
  def channelbag(self,slot,ensure=False):return types.SimpleNamespace(fcurves=[Curve(i) for i in range(25)])
 def action(n,slots):
  return types.SimpleNamespace(name=n,slots=[Slot(s) for s in slots],layers=[types.SimpleNamespace(strips=[Strip()])],frame_range=(1.,30.))
 core=('Hips','Spine','Spine1','Spine2','Neck','Head','LeftShoulder','LeftArm','LeftForeArm','LeftHand','RightShoulder','RightArm','RightForeArm','RightHand','LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase','RightUpLeg','RightLeg','RightFoot','RightToeBase')
 arm=types.SimpleNamespace(type='ARMATURE',name='Armature',pose=types.SimpleNamespace(bones={('mixamorig:'+x):True for x in core}))
 fake.data=types.SimpleNamespace(objects=[arm],actions=[action('Jab-Enemy',['OBCross']),action('Cross',['OBCross-Player','OBCross-Enemy'])]+[action('A'+str(i),['OBCross']) for i in range(28)])
 path=pathlib.Path(sys.argv[1]).with_name('audit.py')
 prev=sys.modules.get('bpy');sys.modules['bpy']=fake
 try:
  spec=importlib.util.spec_from_file_location('mudman_source_audit_test',path)
  mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  _,rows,excluded=mod.scan()
  assert len(rows)==31 and not excluded
  names={x['name'] for x in rows}
  assert {'Jab-Enemy','Cross-Enemy','Cross-Player'}.issubset(names)
  assert rows[0]['name']=='Jab-Enemy' and rows[1]['name']=='Cross-Enemy'
  assert [x for x in rows if x['name']=='Cross-Enemy'][0]['slot']=='OBCross-Enemy'
  print('ACTION_SLOT_REGRESSION=PASS JAB_ENEMY CROSS_ENEMY CROSS_PLAYER ALL_POPULATED_SLOTS')
 finally:
  if prev is None:sys.modules.pop('bpy',None)
  else:sys.modules['bpy']=prev

test_all_source_slots()

# Regression: original ZIP inputs require exact members, hashes and no path traversal.
def test_target_zip():
 import zipfile,importlib.util,hashlib
 path=pathlib.Path(sys.argv[1]).with_name('driver.py')
 spec=importlib.util.spec_from_file_location('mudman_zip_test',path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 prefix='Meshy_AI_Mudstone_Golem_20261107_animated_mixamo_Running'
 with tempfile.TemporaryDirectory() as d:
  root=pathlib.Path(d);downloads=root/'downloads';downloads.mkdir()
  z=downloads/(prefix+'.zip');inputs={prefix+'/'+prefix+'.fbx':b'FBX test bytes',prefix+'/'+prefix+'.png':b'PNG test bytes'}
  with zipfile.ZipFile(z,'w') as out:
   for n,b in inputs.items():out.writestr(n,b)
  m.MUDZIP=hashlib.sha256(z.read_bytes()).hexdigest();m.MUDFBX=hashlib.sha256(b'FBX test bytes').hexdigest();m.MUDPNG=hashlib.sha256(b'PNG test bytes').hexdigest()
  _,fbx,png=m.target_zip(downloads,root)
  assert fbx.read_bytes()==b'FBX test bytes' and png.read_bytes()==b'PNG test bytes'
  _,fbx2,png2=m.target_zip(downloads,root)
  assert fbx2==fbx and png2==png
  bad=downloads/(prefix+'.zip');bad.unlink()
  with zipfile.ZipFile(bad,'w') as out:
   out.writestr('../evil.fbx',b'evil');out.writestr(prefix+'/'+prefix+'.png',b'PNG test bytes')
  m.MUDZIP=hashlib.sha256(bad.read_bytes()).hexdigest()
  try:
   m.target_zip(downloads,root/'clean')
   raise AssertionError('malicious ZIP accepted')
  except RuntimeError as e:assert 'UNTRUSTED_MUDMAN_ZIP_MEMBER_PATH' in str(e) or 'MUDMAN_ZIP_MEMBER_INVENTORY' in str(e)
  print('ZIP_EXTRACTION_REGRESSION=PASS VERIFIED_MEMBERS HASH_GUARD RESUME_NO_OVERWRITE TRAVERSAL_BLOCKED')

test_target_zip()

# v2.0.20 contract typo regression: malformed 71-character Ares SHA passed
# the package integrity test and failed on the operator's phone.
def test_contract_identity():
 import copy
 path=pathlib.Path(sys.argv[1]).with_name('driver.py')
 spec=importlib.util.spec_from_file_location('mudman_contract_test',path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 contract=json.loads(path.with_name('contract.json').read_text())
 assert m.validate_contract(contract)
 assert len(contract['aresSHA256'])==64
 for field in ('aresSHA256','targetZipSHA256','targetFBXSHA256','targetTextureSHA256', 'pinnedGitBase'):
  broken=copy.deepcopy(contract)
  broken[field]+=('abcdef0' if field=='aresSHA256' else 'f')
  try:m.validate_contract(broken)
  except RuntimeError as exc:assert 'CONTRACT_FIELD_MISMATCH_'+field in str(exc)
  else:raise AssertionError('Bad contract field accepted: '+field)
 broken=copy.deepcopy(contract);broken['sourceMutablePaths'].pop()
 try:m.validate_contract(broken)
 except RuntimeError as exc:assert 'MUTABLE_PATH_CONTRACT_MISMATCH' in str(exc)
 else:raise AssertionError('Missing source path accepted')
 print('CONTRACT_REGRESSION=PASS EXACT_REAL_ARES_SHA ALL_INPUT_HASHES MALFORMED_HASH_BLOCKED FILE_ALLOWLIST')

test_contract_identity()
