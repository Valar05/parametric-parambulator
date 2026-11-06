#!/usr/bin/env python3
"""No ARP runtime locally; exercise real packet/ZIP/publication guards and failure injection."""
import hashlib,importlib.util,json,os,pathlib,subprocess,sys,tempfile,zipfile,types
from PIL import Image
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('d',HERE/'driver.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
contract=json.loads((HERE/'contract.json').read_text())
assert contract['authority']=='TERMUX_GIT_ONLY' and contract['vendorCodeMustStayPrivate']
assert sorted(d.SOURCE)==contract['sourceMutablePaths']
assert d.AGENTS==contract['agentsBlob'] and d.CANON==contract['canonicalGLBSHA256']
assert set(d.LOCKED)==set(contract['lockedModelPaths'])
assert {'blender_probe.py','blender_trial.py','driver.py','gif_writer.py','test_driver.py','contract.json'} <= {x.name for x in HERE.glob('*') if x.is_file()}
assert 'blender_probe.py' in (HERE/'driver.py').read_text().split('def main(packet,launcher,launchsha)',1)[1].split('for p,h',1)[0], 'blender probe omitted from packet guard'
assert len(contract['sourceMutablePaths'])==7 and all('v2.0.3' in p for p in contract['sourceMutablePaths'])
with tempfile.TemporaryDirectory() as td:
 root=pathlib.Path(td)
 valid=root/'purchased.zip'
 with zipfile.ZipFile(valid,'w') as z:
  z.writestr('auto_rig_pro-master/__init__.py','def register():pass\n')
  z.writestr('auto_rig_pro-master/remap.py','# fake test only\n')
 # Exercise the original failing *complete* private installer path with a real ZIP.
 installed=d.private_install(valid,d.sha(valid),install_base=root/'private-addon-fixture')
 assert (installed/'auto_rig_pro'/'__init__.py').is_file()
 assert d.private_install(valid,d.sha(valid),install_base=root/'private-addon-fixture') == installed
 assert list(installed.iterdir())[0].name == 'auto_rig_pro'
 direct=root/'direct.zip'
 with zipfile.ZipFile(direct,'w') as z:
  z.writestr('__init__.py','def register():pass\n')
  z.writestr('src/auto_rig_remap.py','# test only\n')
 direct_inst=d.private_install(direct,d.sha(direct),install_base=root/'private-direct-fixture')
 assert (direct_inst/'auto_rig_pro'/'__init__.py').exists()
 folder=root/'unpacked';d.unpack_checked(valid,folder)
 assert (folder/'auto_rig_pro-master/__init__.py').is_file()
 evil=root/'traversal.zip'
 with zipfile.ZipFile(evil,'w') as z:z.writestr('../bad.txt','X')
 try:d.unpack_checked(evil,root/'reject');raise AssertionError('unsafe zip accepted')
 except RuntimeError as ex:assert 'UNSAFE_ZIP_MEMBER' in str(ex)
 src=root/'from.txt';src.write_text('A')
 dst=root/'to.txt';d.safe_copy(src,dst);d.safe_copy(src,dst)
 src.write_text('B')
 try:d.safe_copy(src,dst);raise AssertionError('overwrite not blocked')
 except RuntimeError as ex:assert 'COLLISION' in str(ex)
 # Exercise the actual asset() call with a Git LFS pointer-only checkout.
 # Test the EXACT prior failure: include + exclude=* returns no binary. Require
 # --exclude= (empty) and ensure it really produces independently SHA-matched files.
 def fake_assets_case(mode):
  sim=root/('lfs-'+mode);sim.mkdir()
  canon=b'GLB2 fixture bytes\x00'*1000
  donor=b'BLENDER file fixture\x01'*950
  want={d.TARGET:canon,d.DONOR:donor}
  for path,payload in want.items():
   file=sim/path;file.parent.mkdir(parents=True,exist_ok=True)
   file.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:'+hashlib.sha256(payload).hexdigest()+'\nsize '+str(len(payload))+'\n')
  old_git=d.git;old_canon=d.CANON;old_lion=d.LION
  d.CANON=hashlib.sha256(canon).hexdigest();d.LION=hashlib.sha256(donor).hexdigest()
  calls=[]
  def fake_git(repo,*args,**kw):
   calls.append(args)
   if args[:2]==('lfs','pull') or args[:2]==('lfs','fetch'):
    assert any(a.startswith('--include=') for a in args),args
    assert '--exclude=' in args, 'LFS exclude is not cleared: '+repr(args)
    assert '--exclude=*' not in args
    if mode=='pull_hydrates' and args[1]=='pull':
     for path,payload in want.items():(sim/path).write_bytes(payload)
    if mode=='fetch_fallback' and args[1]=='fetch':
     for path,payload in want.items():(sim/path).write_bytes(payload)
    if mode=='tampered':
     for path in want:(sim/path).write_bytes(b'WRONG MODEL BINARY')
   return types.SimpleNamespace(returncode=0,stdout='',stderr='')
  d.git=fake_git
  try:
   if mode=='tampered':
    try:d.assets(sim);raise AssertionError('WRONG LFS BYTES ACCEPTED')
    except RuntimeError as ex:assert 'GIT_LFS_EXACT_MODEL_RETRIEVAL_BLOCKED' in str(ex),str(ex)
   else:
    target,donor=d.assets(sim)
    assert target.read_bytes()==canon and donor.read_bytes()==want[d.DONOR]
    assert all(a not in ('--exclude=*',) for args in calls for a in args)
   assert any(args[:2]==('lfs','pull') for args in calls),calls
   if mode=='fetch_fallback':assert any(args[:2]==('lfs','fetch') for args in calls),calls
  finally:d.git=old_git;d.CANON=old_canon;d.LION=old_lion
 for mode in ('pull_hydrates','fetch_fallback','tampered'):
  fake_assets_case(mode)
 # Isolate a verified Git LFS cache object as another supported fallback.
 cached=root/'cached_lfs';cached.mkdir()
 content=b'cached LFS object verified'*920
 targetfile=cached/d.TARGET;targetfile.parent.mkdir(parents=True)
 targetfile.write_text('version https://git-lfs.github.com/spec/v1\n')
 digest=hashlib.sha256(content).hexdigest()
 object_path=cached/'.git/lfs/objects'/digest[:2]/digest[2:4]/digest
 object_path.parent.mkdir(parents=True)
 object_path.write_bytes(content)
 assert d._cache_restore(cached,d.TARGET,digest)
 assert d.sha(targetfile)==digest
 # tampered native cache content MUST NEVER be used, even if path matches SHA.
 targetfile.write_text('version https://git-lfs.github.com/spec/v1\n')
 object_path.write_bytes(b'corrupt')
 assert not d._cache_restore(cached,d.TARGET,digest)
 assert targetfile.read_text().startswith('version https://git-lfs.github.com/')
 # Disposable real Git source/evidence publication, including SHA readback and conflict cases.
 remote=root/'remote.git';workspace=root/'work'
 subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
 subprocess.run(['git','clone',str(remote),str(workspace)],check=True,capture_output=True)
 def G(*args):return subprocess.run(['git','-C',str(workspace),*args],check=True,capture_output=True,text=True).stdout.strip()
 G('config','user.name','test');G('config','user.email','test@example.invalid')
 (workspace/'README.md').write_text('test\n');G('add','README.md');G('commit','-m','initial')
 G('branch','-M','main');G('push','origin','main')
 head=d.publish(workspace,'FAKE_FIXTURE')
 assert head==G('rev-parse','HEAD')
 # exact proof of remote origin branch
 assert subprocess.run(['git','ls-remote',str(remote),'refs/heads/main'],capture_output=True,text=True,check=True).stdout.split()[0]==head
 # Exercise real source publication with all seven versioned paths, the real
 # allowlist, Git commit/push/readback, and collision refusal.
 source_head=d.source_pub(workspace,HERE,HERE/'driver.py')
 assert source_head==G('rev-parse','HEAD')
 assert subprocess.run(['git','ls-remote',str(remote),'refs/heads/main'],capture_output=True,text=True,check=True).stdout.split()[0]==source_head
 assert all((workspace/path).is_file() for path in d.SOURCE)
 assert all(subprocess.run(['git','-C',str(workspace),'cat-file','-e','HEAD:'+path],check=False,capture_output=True).returncode==0 for path in d.SOURCE)
 # Exact-byte reuse is allowed, but edited/existing paths remain protected.
 assert d.source_pub(workspace,HERE,HERE/'driver.py')==source_head
 collision=(workspace/next(iter(d.SOURCE)));collision.write_text('different')
 try:d.source_pub(workspace,HERE,HERE/'driver.py');raise AssertionError('changed source paths were overwritten')
 except RuntimeError as ex:assert 'COLLISION' in str(ex)
 # Regression: v2.0.2 swapped launcher and packet arguments, attempting to
 # shutil.copyfile(the packet directory) and raising IsADirectoryError.
 # Validate the function signature AND invoke the real main() through source
 # publication, evidence publication and remote SHA readback with isolated Git.
 try:d.source_pub(workspace,HERE/'driver.py',HERE);raise AssertionError('reversed source args accepted')
 except RuntimeError as ex:assert 'SOURCE_PUBLICATION_EXPECTS_PACKET_DIRECTORY' in str(ex)
 full_remote=root/'main-remote.git';full_repo=root/'main-working'
 subprocess.run(['git','init','--bare',str(full_remote)],check=True,capture_output=True)
 subprocess.run(['git','clone',str(full_remote),str(full_repo)],check=True,capture_output=True)
 def GF(*a):return subprocess.run(['git','-C',str(full_repo),*a],capture_output=True,text=True,check=True).stdout.strip()
 GF('config','user.name','fixture');GF('config','user.email','test@example.invalid')
 for path in d.LOCKED:
  f=full_repo/path;f.parent.mkdir(parents=True,exist_ok=True)
  f.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:'+d.CANON+'\nsize 123456\n')
 GF('add','.');GF('commit','-m','synthetic model pointers');GF('branch','-M','main');GF('push','origin','main')
 fake_home=root/'fake-home';(fake_home/'storage/downloads').mkdir(parents=True)
 fake_models=root/'fake-models';fake_models.mkdir()
 fake_target=fake_models/'target.glb';fake_target.write_bytes(b'NOT REAL GLB - FULL DRIVER FIXTURE')
 fake_source=fake_models/'source.blend';fake_source.write_bytes(b'NOT REAL BLEND - FULL DRIVER FIXTURE')
 fake_private=root/'private-fixture/modules';fake_private.mkdir(parents=True)
 fake_vendor=root/'private_vendor.zip';fake_vendor.write_bytes(b'FAKE-PRIVATE-ZIP-NO-PUBLICATION')
 old_home=pathlib.Path.home;old_clone=d.run_git_clone;old_zip=d.private_zip
 old_install=d.private_install;old_probe=d.headless_probe;old_assets=d.assets
 old_ares=d.optional_ares;old_runner=d.blender_runner;old_call=d.call
 def guarded_call(args,*aa,**kk):
  if args and str(args[0])=='python3' and any('test_driver.py' in str(x) for x in args):
   return types.SimpleNamespace(returncode=0,stdout='RECURSION_GUARD',stderr='')
  return old_call(args,*aa,**kk)
 try:
  pathlib.Path.home=classmethod(lambda cls:fake_home)
  d.run_git_clone=lambda _root:(full_repo,GF('rev-parse','HEAD'))
  d.private_zip=lambda _dl:(fake_vendor,'synthetic-digest')
  d.private_install=lambda src,hashval:fake_private
  d.headless_probe=lambda rr,p:{'status':'REAL_PURCHASED_ARP_REMAP_HEADLESS_OPERATOR_REGISTRATION_PASS', 'activation':{'moduleName':'TEST_FIXTURE'},'sceneProperties':{'source_rig':True,'target_rig':True,'bones_map_v2':True}}
  d.assets=lambda _repo:(fake_target,fake_source)
  d.optional_ares=lambda _dl:None
  d.blender_runner=lambda *a:({'status':'BLOCKED','error':'EXPECTED_SYNTHETIC_TEST_NO_REAL_BLENDER'},None)
  d.call=guarded_call
  d.main(HERE,HERE/'driver.py','synthetic-launcher-sha')
  receipts=list((fake_home/'.local/state'/d.V).glob('*/RECEIPT.json'))
  assert len(receipts)==1,receipts
  final_receipt=json.loads(receipts[0].read_text())
  assert final_receipt['status']=='ARP_EXECUTED_NO_VALIDATED_ANIMATION__EVIDENCE_GIT_PUBLISHED',final_receipt
  assert final_receipt['gitEvidenceCommit']==GF('rev-parse','HEAD')
  assert final_receipt['originalCanonicalModelUnchanged'] is True
  assert final_receipt['trialStatuses']['Lionheart']=='BLOCKED'
  assert GF('rev-parse','HEAD:'+d.TARGET)
  assert GF('rev-parse','HEAD:'+'campaigns/'+d.V+'_driver.py')
  assert d.V in GF('show','HEAD:'+'campaigns/'+d.V+'_driver.py')
  remote_head=subprocess.run(['git','ls-remote',str(full_remote),'refs/heads/main'],capture_output=True,text=True,check=True).stdout.split()[0]
  assert remote_head==GF('rev-parse','HEAD')
  assert not any('auto_rig_pro' in x or 'private_vendor' in x for x in GF('ls-tree','-r','--name-only','HEAD').splitlines())
  # Second entire main() run: synthetic SUCCESS branch with actual PIL frames,
  # GIF + contact binary publication, and exact remote byte readback.
  success_remote=root/'success-remote.git';success_repo=root/'success-working'
  subprocess.run(['git','init','--bare',str(success_remote)],check=True,capture_output=True)
  subprocess.run(['git','clone',str(success_remote),str(success_repo)],check=True,capture_output=True)
  full_repo=success_repo
  GF('config','user.name','fixture');GF('config','user.email','test@example.invalid')
  for path in d.LOCKED:
   f=success_repo/path;f.parent.mkdir(parents=True,exist_ok=True)
   f.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:'+d.CANON+'\nsize 123456\n')
  GF('add','.');GF('commit','-m','synthetic model pointers')
  GF('branch','-M','main');GF('push','origin','main')
  fake_home=root/'success-home';(fake_home/'storage/downloads').mkdir(parents=True)
  def synthetic_success(rootarg,priv,repo,out,source,srcsha,target,clip):
   from gif_writer import assemble
   trial=out/clip/'trial';trial.mkdir(parents=True)
   frames=trial/'frames';frames.mkdir()
   for idx in range(16):
    im=Image.new('RGB',(512,512),(30+idx*5,40+idx*4,65+idx*3))
    im.save(frames/('frame_%03d.png'%idx))
   data={'status':'VISUAL_REVIEW_PENDING_MOTION_GATE_PASS','clip':clip,
      'motionGate':True,'targetAction':'SYNTHETIC_ONLY','graphic':None}
   graphic=assemble(frames,trial,clip);data['graphic']=graphic
   return data,graphic
  d.blender_runner=synthetic_success
  d.main(HERE,HERE/'driver.py','synthetic-launcher-success-sha')
  evidence=list((fake_home/'.local/state'/d.V).glob('*/RECEIPT.json'))
  assert len(evidence)==1,evidence
  succ=json.loads(evidence[0].read_text())
  assert succ['status']=='ARP_TRIAL_EVIDENCE_GIT_PUBLISHED_OWNER_REVIEW_PENDING',succ
  assert succ['trialStatuses']['Lionheart']=='VISUAL_REVIEW_PENDING_MOTION_GATE_PASS'
  assert succ['gitEvidenceCommit']==GF('rev-parse','HEAD')
  tree=GF('ls-tree','-r','--name-only','HEAD').splitlines()
  gifpaths=[x for x in tree if x.endswith('.gif')]
  assert len(gifpaths)==1,gifpaths
  pngpaths=[x for x in tree if x.endswith('.png')]
  assert len(pngpaths)==1,pngpaths
  assert subprocess.run(['git','-C',str(success_repo),'cat-file','blob','HEAD:'+gifpaths[0]],capture_output=True,check=True).stdout[:6]==b'GIF89a'
  assert subprocess.run(['git','ls-remote',str(success_remote),'refs/heads/main'],capture_output=True,text=True,check=True).stdout.split()[0]==GF('rev-parse','HEAD')
 finally:
  pathlib.Path.home=old_home;d.run_git_clone=old_clone;d.private_zip=old_zip
  d.private_install=old_install;d.headless_probe=old_probe;d.assets=old_assets
  d.optional_ares=old_ares;d.blender_runner=old_runner;d.call=old_call
 # GIF and contact sheet from real PNG decoding
 from gif_writer import assemble
 frames=root/'frames';frames.mkdir()
 for i in range(16):
  image=Image.new('RGB',(512,512),(i*12,70,i*8))
  image.save(frames/('frame_%03d.png'%i))
 result=assemble(frames,root,'Test')
 assert result['distinctFrames']==16 and result['gifBytes']>1000
 print('TEST_OK_TERMUX_GIT_PRIVATE_VENDOR_KEPT_OUT_OF_SOURCE_ALLOWLIST')
 print('TEST_OK_COMPLETE_PRIVATE_ADDON_INSTALL_REUSE_AND_DIRECT_ZIP_LAYOUT')
 print('TEST_OK_ARCHIVE_PATH_TRAVERSAL_AND_COLLISION_REJECTED')
 print('TEST_OK_LFS_POINTER_HYDRATION_EMPTY_EXCLUDE_FETCH_FALLBACK_AND_TAMPER_REJECTION')
 print('TEST_OK_LFS_NATIVE_OBJECT_CACHE_VERIFIED_AND_CORRUPTION_REJECTED')
 print('TEST_OK_COMPLETE_VERSIONED_GIT_SOURCE_PUBLICATION_PUSH_READBACK_AND_COLLISION_REJECTION')
 print('TEST_OK_REAL_GIT_REMOTE_COMMIT_PUSH_AND_SHA_READBACK')
 print('TEST_OK_REAL_16_FRAME_GIF_ASSEMBLY')
 print('TEST_OK_FULL_MAIN_TESTS_EXACT_SOURCE_PUBLISH_INVOCATION_AND_REMOTE_EVIDENCE')
 print('TEST_OK_FULL_MAIN_SYNTHETIC_SUCCESS_PUBLICATION_GIF_CONTACT_REMOTE_HASHES')
 print('TEST_LIMIT_ACTUAL_ARP_VENDOR_ZIP_AND_BLENDER_REQUIRED_ON_OWNER_TERMUX')
