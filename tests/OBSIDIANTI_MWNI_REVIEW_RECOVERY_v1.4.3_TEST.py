#!/usr/bin/env python3
import gzip,hashlib,importlib.util,pathlib,struct,tempfile
p=pathlib.Path(__file__).with_name('driver.py');spec=importlib.util.spec_from_file_location('mwni_recovery_under_test',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as t:
 root=pathlib.Path(t);old=root/'old';downloads=root/'downloads';downloads.mkdir();p=(old/'work/Heavy1/MWNI_Heavy1_UNAPPROVED.glb');p.parent.mkdir(parents=True)
 dat=b'glTF'+struct.pack('<II',2,12);p.write_bytes(dat)
 item={'path':'/mnt/obs-output/Heavy1/MWNI_Heavy1_UNAPPROVED.glb','sha256':hashlib.sha256(dat).hexdigest(),'bytes':len(dat)}
 assert m.resolve_candidate(old,downloads,'Heavy1','candidateGLB',item)==p
 output=downloads/'recovered.glb';assert m.durable_copy(p,output,item['sha256'])=='COPIED_SHA_VERIFIED'
 assert m.durable_copy(p,output,item['sha256'])=='EXISTS_VERIFIED'
 try:
  m.resolve_candidate(old,downloads,'Heavy1','candidateGLB',{**item,'path':'/mnt/obs-output/../secret'},False)
 except RuntimeError:pass
 else:raise AssertionError('traversal allowed')
 try:
  m.resolve_candidate(old,downloads,'Heavy1','candidateGLB',{**item,'sha256':'0'*64},False)
 except RuntimeError:pass
 else:raise AssertionError('SHA mismatch allowed')
 try:
  m.durable_copy(p,output,'0'*64)
 except RuntimeError:pass
 else:raise AssertionError('source SHA mismatch allowed')
 bad=root/'bad.blend';bad.write_bytes(b'NOTBLENDER')
 try:m.file_structure(bad,'.blend')
 except RuntimeError:pass
 else:raise AssertionError('bad BLEND allowed')
 blend=root/'ok.blend';blend.write_bytes(b'BLENDER-v430');assert m.file_structure(blend,'.blend')['encoding']=='BLEND_RAW'
 zipped=root/'compressed.blend';zipped.write_bytes(gzip.compress(b'BLENDER-v430'+b'correct review content'*3000,mtime=0))
 assert m.file_structure(zipped,'.blend')['encoding']=='BLEND_GZIP'

 # Genuine Zstandard frame created from the same BLENDER-v430 sample with zstd 1.5.
 # Fixture embedded so Termux does NOT need zstd installed merely to run tests.
 zs=bytes.fromhex('28b52ffd04586501002402424c454e4445522d76343330636f72726563742072657669657720636f6e74656e740100ba0dc87c3e01888cac6b')
 zstdfile=root/'compressed-zstd.blend';zstdfile.write_bytes(zs)
 assert m.file_structure(zstdfile,'.blend')['encoding']=='BLEND_ZSTD'
 assert m.file_structure(zstdfile,'.blend')['zstdFrameMagic']=='28b52ffd'
 zbad=root/'corrupt-zstd.blend';zbad.write_bytes(zs[:-1]+bytes([zs[-1]^0xFF]))
 if m.shutil.which('zstd'):
  try:m.file_structure(zbad,'.blend')
  except RuntimeError:pass
  else:raise AssertionError('corrupted Zstd stream accepted despite available verifier')
 assert m.sha(zbad)!=m.sha(zstdfile), 'digest must distinguish corruption even without zstd installed'

 corrupt=root/'bad-compressed.blend';corrupt.write_bytes(zipped.read_bytes()[:-8]+b'\x00'*8)
 try:m.file_structure(corrupt,'.blend')
 except RuntimeError:pass
 else:raise AssertionError('corrupt gzip trailer allowed')
 wrong=root/'wrong-gzip.blend';wrong.write_bytes(gzip.compress(b'NOTBLENDER'+b'x'*1000,mtime=0))
 try:m.file_structure(wrong,'.blend')
 except RuntimeError:pass
 else:raise AssertionError('gzip non-BLEND content allowed')
 for clip in ('Heavy1','Light2'):
  for kind,ext,data in [('candidateGLB','.glb',b'glTF'+struct.pack('<II',2,12)),('editableBlend','.blend',zstdfile.read_bytes())]:
   name=f'MWNI_{clip}_UNAPPROVED{ext}'
   testfile=old/'work'/clip/name;testfile.parent.mkdir(parents=True,exist_ok=True);testfile.write_bytes(data)
   expected={'path':f'/mnt/obs-output/{clip}/{name}','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
   assert m.resolve_candidate(old,downloads,clip,kind,expected)==testfile, (clip,kind)
   dst=downloads/f'v143_{clip}_{name}'
   assert m.durable_copy(testfile,dst,expected['sha256'])=='COPIED_SHA_VERIFIED'
   assert m.file_structure(dst,ext)['encoding'] in ('GLB2','BLEND_ZSTD')
   assert m.durable_copy(testfile,dst,expected['sha256'])=='EXISTS_VERIFIED'
 print('TEST_4_ARTIFACT_RECOVERY=PASS')
 print('TEST_BLENDER_GZIP_INTEGRITY=PASS')
 print('TEST_BLENDER_ZSTD_MAGIC_AND_HASH=PASS')
 output.write_bytes(b'WRONG')
 try:m.durable_copy(p,output,item['sha256'])
 except RuntimeError:pass
 else:raise AssertionError('collision allowed')
 print('TEST_PATH_TRANSLATION=PASS')
 print('TEST_VIRTUAL_TRAVERSAL_REJECTED=PASS')
 print('TEST_SHA_AND_STRUCTURE_GATES=PASS')
 print('TEST_IDEMPOTENT_VERIFIED_COPY_AND_COLLISION=PASS')
