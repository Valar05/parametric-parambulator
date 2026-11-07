#!/usr/bin/env python3
"""Mock fixtures and production code success/failure gates, no owner remote or vendor."""
from __future__ import annotations
import contextlib,hashlib,importlib,json,os,pathlib,struct,subprocess,sys,tempfile,types,io
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import driver as d

PATCHES=[
'<title>Obsidianti | Mwni Retarget Review</title>',
'<h1>Obsidianti | Mwni foot-IK retarget review</h1>',
'<option value="Light2">Light2</option>',
'<option value="candidate">Mwni IK candidate</option>',
'<option value="original">Original (if available)</option>',
'Select Mwni IK candidate.',
'Mwni candidate UNAPPROVED',
'These are UNAPPROVED experimental exports, not the canonical model. Floor guide is visual, not a physical contact test.',
'<label for="version">Rig</label>'
]

def cmd(*args):
 p=subprocess.run(args,text=True,capture_output=True)
 if p.returncode:raise AssertionError((args,p.stderr))
 return p.stdout.strip()

def git_fixture(t):
 bare=t/'bare.git';work=t/'work';cmd('git','init','--bare','--initial-branch=main',str(bare));cmd('git','init','--initial-branch=main',str(work))
 cmd('git','-C',str(work),'config','user.name','Test');cmd('git','-C',str(work),'config','user.email','test@invalid.example')
 (work/'file.txt').write_text('baseline');cmd('git','-C',str(work),'add','-A');cmd('git','-C',str(work),'commit','-m','init')
 cmd('git','-C',str(work),'remote','add','origin',str(bare));cmd('git','-C',str(work),'push','origin','HEAD:main');return work,bare

def test_source_patching(t):
 repo=t/'repo';repo.mkdir();old=repo/'campaigns';old.mkdir()
 (repo/(d.OLDVIEW+'viewer.html')).write_text('\n'.join(PATCHES))
 (repo/(d.OLDVIEW+'server.py')).write_text("server_version='ObsidiantiMwniViewer/1.4.4'\n")
 packet=t/'packet';packet.mkdir()
 rr=d.create_viewer(repo,packet)
 x=(packet/'viewer.html').read_text();assert '<option value="AxeKick">' in x and 'Mwni candidate UNAPPROVED' not in x
 assert len(rr['viewerSHA256'])==64 and 'ARPViewer' in (packet/'server.py').read_text()
 (repo/(d.OLDVIEW+'viewer.html')).write_text('incompatible')
 try:d.create_viewer(repo,packet)
 except RuntimeError as ex:assert 'VIEWER_TEMPLATE_CONTRACT_CHANGED' in str(ex)
 else:raise AssertionError('missing source contract should block')

def glb(t,name,good=True):
 doc={'asset':{'version':'2.0'},'animations':[{'name':name,'channels':[{'sampler':i,'target':{'node':i,'path':'rotation'}} for i in range(12)]}],
      'meshes':[{}], 'skins':[{}]}
 raw=json.dumps(doc).encode();raw+=b' '*((-len(raw))%4)
 data=b'\0'*210000
 if len(data)%4:data+=b'\0'*(4-len(data)%4)
 size=12+8+len(raw)+8+len(data)
 f=t/'sample.glb'
 f.write_bytes(struct.pack('<4sII',b'glTF',2,size)+struct.pack('<I4s',len(raw),b'JSON')+raw+struct.pack('<I4s',len(data),b'BIN\0')+data)
 return f

def test_real_bytes_glb(t):
 f=glb(t,'Heavy1_remap')
 x=d.validate_glb(f,'Heavy1');assert x['channels']==12 and x['sha256']==d.sha(f)
 glb(t,'Animation');assert d.validate_glb(f,'Heavy1')['animations']==['Animation']
 glb(t,'Heavy1_remap')
 try:d.validate_glb(f,'AxeKick')
 except RuntimeError as e:assert 'CLIP_NAME_MISMATCH' in str(e)
 else:raise AssertionError('wrong clip was accepted')
 glb(t,'Heavy1_remap')
 with open(f,'r+b') as h:h.write(b'FAIL')
 try:d.validate_glb(f,'Heavy1')
 except RuntimeError as e:assert 'GLB_MAGIC_INVALID' in str(e)
 else:raise AssertionError('corrupt GLB passed')

def test_remote_source_publish(t):
 repo,bare=git_fixture(t)
 src=t/'s.txt';src.write_text('authorized')
 d.commit_files(repo,{'campaigns/fixture_thing.py':src},'TEST_SOURCE')
 assert cmd('git','--git-dir',str(bare),'show','main:campaigns/fixture_thing.py')=='authorized'
 try:d.commit_files(repo,{'campaigns/fixture_thing.py':src},'TEST_DUPLICATE')
 except RuntimeError as e:assert 'DESTINATION_COLLISION' in str(e)
 else:raise AssertionError('source overwrite was allowed')
 ev=t/'evidence.json';ev.write_text('{"result":"real evidence"}\n')
 d.commit_files(repo,{'diagnostics/test/evidence.json':ev},'TEST_EVIDENCE')
 assert cmd('git','--git-dir',str(bare),'show','main:diagnostics/test/evidence.json')==ev.read_text().strip()

def test_private_pd_guards(t):
 old=d.PD_HOME
 try:
  d.PD_HOME=t/'private';(d.PD_HOME/'python/proot_distro').mkdir(parents=True)
  (d.PD_HOME/'WHEEL_SHA256.json').write_text(json.dumps({'packageVersion':d.PD,'wheelSha256':'bad','packageFileHashes':{}}))
  try:d.private_pd()
  except RuntimeError as e:assert 'IDENTITY_CHANGED' in str(e)
  else:raise AssertionError('untrusted proot wrapper accepted')
 finally:d.PD_HOME=old

def test_export_fallback_receipt(t):
 # Two independently recorded saved Blender actions. A failed exporter cannot be promoted.
 src=t/'a.blend';src.write_bytes(b'BLENDER content');orig=d.sha(src)
 original=d.call
 try:
  d.call=lambda a,timeout=0,check=False,env=None: types.SimpleNamespace(returncode=127,stdout='',stderr='missing shared object')
  try:d.export_one(['proot'],'/' if False else t,src,'Heavy1',orig)
  except RuntimeError as e:assert 'PREVIEW_EXPORT_FAILED' in str(e)
  else:raise AssertionError('native export failure was accepted')
 finally:d.call=original
 assert d.sha(src)==orig

def main():
 with tempfile.TemporaryDirectory(prefix='obs213-') as td:
  root=pathlib.Path(td)
  for label,fn in [('patch',test_source_patching),('binary',test_real_bytes_glb),('remote',test_remote_source_publish),('private',test_private_pd_guards),('failure',test_export_fallback_receipt)]:
   item=root/label;item.mkdir()
   with contextlib.redirect_stdout(io.StringIO()):fn(item)
 print('TEST_DRIVER=PASS original_viewer_patch_contract exact_real_GLB_shape and corruption remote_Git_commit_push_readback protected_private_CLI export_failure_no_false_success')
if __name__=='__main__':main()
