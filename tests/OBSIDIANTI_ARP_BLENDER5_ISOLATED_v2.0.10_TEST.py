#!/usr/bin/env python3
"""Self-tests: deterministic patches, real disposable Git publication and blocked-trial gating.
NEVER contacts owner's repository or launches Blender.
"""
from __future__ import annotations
import hashlib,importlib.util,json,pathlib,subprocess,sys,tempfile,types,os,contextlib,io
from PIL import Image
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import driver as d

def sh(*a):
 p=subprocess.run(a,capture_output=True,text=True)
 if p.returncode:raise AssertionError((a,p.stderr,p.stdout))
 return p.stdout.strip()

def old_snippets():
 return "\n".join([
  "if bpy.app.version[:2]!=(4,3):raise RuntimeError('BLENDER_4_3_REQUIRED_ACTUAL_'+bpy.app.version_string)",
  "  allowed={p.identifier for p in bpy.ops.arp.retarget.get_rna_type().properties}",
  "  with bpy.context.temp_override(**context()):\n   if not bpy.ops.arp.retarget.poll():raise RuntimeError('ARP_RETARGET_POLL_FALSE_AFTER_MAPPING')",
  "  result['retargetOperator']=list(operator(bpy.ops.arp.retarget,'EXEC_DEFAULT',**retarget_options))",
  "  result['targetMotion']=motion_stats(witnesses(tgt,start,end))",
  "  result['render']=render_frames(tgt,meshes,out,start,end,args.clip)",
  "  result['mapping']={'boneCount':len(active),'mapped':active,'excludedCount':len(dropped)}",
  "  result['status']='VISUAL_REVIEW_PENDING_MOTION_GATE_PASS' if result['motionGate'] else 'REJECTED_BUT_RENDERED_ANATOMY_OR_ARTICULATION'",
  "'obsidianti-arp-3.79.17-first-live-v2.0.5'",
 ])

def test_patch(tmp):
 repo=tmp/'repo';old=repo/'campaigns';old.mkdir(parents=True)
 (repo/(d.PREVIOUS+'blender_trial.py')).write_text('def run():\n  '+old_snippets())
 (repo/(d.PREVIOUS+'blender_probe.py')).write_text("if bpy.app.version[:2] != (4,3):raise RuntimeError('REQUIRES_BLENDER_4_3_ACTUAL_'+bpy.app.version_string)\n'obsidianti-private-arp-operator-probe-v2.0.5'")
 (repo/(d.PREVIOUS+'gif_writer.py')).write_text('def assemble(a,b,c): pass\n')
 pkt=tmp/'packet';pkt.mkdir()
 outs=d.patch_scripts(repo,pkt)
 s=(pkt/'blender_trial.py').read_text();p=(pkt/'blender_probe.py').read_text()
 assert "BLENDER_5_0_REQUIRED" in s and "REQUIRES_BLENDER_5_0" in p
 assert 'BEFORE_RETARGET_RNA' in s and 'BEFORE_RETARGET_POLL' in s and 'BEFORE_RETARGET_EXEC' in s
 assert 'RETARGET_EXEC_RETURNED' in s and 'TARGET_MOTION_CAPTURED' in s
 assert 'RENDERING' in s and 'RENDER_COMPLETE' in s and 'BONE_MAP_CREATED' in s
 assert all(len(h)==64 for h in outs.values())
 (repo/(d.PREVIOUS+'blender_trial.py')).write_text('unexpected incompatible source')
 try:d.patch_scripts(repo,pkt)
 except RuntimeError as e:assert 'PATCH_PRECONDITION_FAILED' in str(e)
 else:raise AssertionError('changed upstream contract should block')
 return pkt

def git_fixture(tmp):
 bare=tmp/'bare.git';repo=tmp/'working'
 sh('git','init','--bare','--initial-branch=main',str(bare))
 sh('git','init','--initial-branch=main',str(repo))
 sh('git','-C',str(repo),'config','user.name','Fixture')
 sh('git','-C',str(repo),'config','user.email','fixture@invalid.test')
 (repo/'AGENTS.md').write_text('fixture rules')
 (repo/'README.md').write_text('source baseline')
 sh('git','-C',str(repo),'add','-A')
 sh('git','-C',str(repo),'commit','-m','fixture source')
 sh('git','-C',str(repo),'remote','add','origin',str(bare))
 sh('git','-C',str(repo),'push','origin','HEAD:main')
 return repo,bare

def test_commit_and_receipts(tmp):
 repo,bare=git_fixture(tmp)
 pkt=tmp/'packet';pkt.mkdir(exist_ok=True)
 for path,key in d.SOURCE.items():
  if key!='LAUNCHER':(pkt/key).write_text('fixture '+key)
 launcher=tmp/'launcher.sh';launcher.write_text('#!/bin/sh\ntrue\n')
 got=d.commit_source(repo,pkt,launcher)
 assert got==sh('git','--git-dir',str(bare),'rev-parse','main')
 for path in d.SOURCE:
  assert sh('git','--git-dir',str(bare),'show','main:'+path)
 try:d.commit_source(repo,pkt,launcher)
 except RuntimeError as e:assert 'COLLISION' in str(e)
 else:raise AssertionError('collision not blocked')
 work=tmp/'testwork';work.mkdir()
 root=work/'run';root.mkdir()
 (root/'evidence').mkdir(exist_ok=True)
 # add_evidence creates evidence/ itself; remove prepared directory
 (root/'evidence').rmdir()
 image=work/'frame.png';Image.new('RGB',(64,64),(45,55,65)).save(image)
 gif=work/'anim.gif';Image.new('P',(64,64)).save(gif,format='GIF')
 state={'sourceCommit':got,'inputGitHead':'fixture','blenderVersion':'Blender 5.0.1',
        'arpProbe':{'status':'pass'}, 'trials':{'Heavy1':{'status':'MOTION_GATE_REJECTED_WITH_VISUAL','stage':'COMPLETE','targetAction':'X'}}}
 oldhome=os.environ.get('HOME')
 os.environ['HOME']=str(tmp)
 try:final=d.add_evidence(repo,root,'fixture-run',state,{'Heavy1':{'gif':gif,'contact':image}},lambda:None)
 finally:
  if oldhome is None:os.environ.pop('HOME',None)
  else:os.environ['HOME']=oldhome
 assert final==sh('git','--git-dir',str(bare),'rev-parse','main')
 assert sh('git','--git-dir',str(bare),'show','main:'+d.EVID+'fixture-run/EVIDENCE.json')
 # User's Android Downloads isn't available in fixture: passed copy will need diversion below

def test_frames_failfast(tmp):
 root=tmp/'run';root.mkdir()
 private=tmp/'private';private.mkdir();repo=tmp/'repo';repo.mkdir()
 src=tmp/'source.blend';src.write_bytes(b'source')
 target=tmp/'target.glb';target.write_bytes(b'glb')
 oldcmd=d.cmd;oldpd=d.pd_command
 try:
  d.pd_command=lambda:["private-python","-c","VERIFIED_MODULE",]
  def native_crash(argv,timeout=240,check=True,env=None,stream=False):
   trial=root/'out'/'Heavy1'/'trial';trial.mkdir(parents=True,exist_ok=True)
   (trial/'TRIAL.json').write_text(json.dumps({'status':'BOOT','stage':'BEFORE_RETARGET_EXEC','mapping':{'boneCount':22}}))
   return types.SimpleNamespace(returncode=139,stdout='Writing: /tmp/source.crash.txt',stderr='proot terminated with signal 11')
  d.cmd=native_crash
  out,files=d.execute_clip(root,private,repo,src,'x'*64,target,'Heavy1')
  assert out['status']=='BLOCKED_NATIVE_OR_PYTHON_RUNTIME' and out['stage']=='BEFORE_RETARGET_EXEC'
  assert not files
 finally:d.cmd=oldcmd;d.pd_command=oldpd

def test_private_oci_cli_guards(tmp):
 import zipfile
 import types
 # Signed-wheel verification and safe extraction from a structurally realistic
 # synthetic fixture; DO NOT use a real online wheel in local acceptance tests.
 wheel=tmp/'synthetic.whl'
 with zipfile.ZipFile(wheel,'w') as z:
  z.writestr('proot_distro/cli.py', 'def main():pass\n')
  z.writestr('proot_distro/__init__.py', '__version__="test"\n')
  for n in range(14):z.writestr(f'proot_distro/fixture_{n}.py',f'# fixture {n}\n')
 oldsha=d.PD_WHEEL_SHA
 d.PD_WHEEL_SHA=d.sha(wheel)
 try:
  dest=tmp/'extracted';hashes=d.safe_extract_private_cli(wheel,dest)
  assert 'proot_distro/cli.py' in hashes
  with zipfile.ZipFile(tmp/'evil.whl','w') as z:z.writestr('../escape','BAD')
  # The digest check must precede any unsafe member reads.
  try:d.safe_extract_private_cli(tmp/'evil.whl',tmp/'invalid')
  except RuntimeError as err:assert 'SHA256_MISMATCH' in str(err)
  else:raise AssertionError('unsafe unverified wheel was extracted')
 finally:d.PD_WHEEL_SHA=oldsha

 # Full mocked install path, keeping the owner Debian entry untouched.
 oldcmd=d.cmd;oldinstall=d.install_private_pd;oldpd=d.pd_command
 try:
  d.install_private_pd=lambda:None
  d.pd_command=lambda:['private-python','-c','TEST_MODULE']
  calls=[];installed={'value':False}
  def fake_cmd(argv,timeout=600,check=True,env=None,stream=False):
   a=list(map(str,argv));calls.append(a)
   if a[3]=='login' and a[4]==d.DISTRO:
    if not installed['value']:
     return types.SimpleNamespace(returncode=1,stdout='',stderr='not installed')
    if '/etc/os-release' in a:return types.SimpleNamespace(returncode=0,stdout='PRETTY_NAME="Ubuntu 26.04 LTS"\n',stderr='')
    if '--print-architecture' in a:return types.SimpleNamespace(returncode=0,stdout='arm64\n',stderr='')
    if '/usr/bin/env' in a:return types.SimpleNamespace(returncode=0,stdout='PD_IMAGE=ubuntu:26.04\n',stderr='')
    if '--version' in a:return types.SimpleNamespace(returncode=0,stdout='Blender 5.0.1\n',stderr='')
   if a[3]=='list':return types.SimpleNamespace(returncode=0,stdout='',stderr='')
   if a[3]=='install':
    assert a[4:]==['--name',d.DISTRO,d.IMAGE]
    installed['value']=True
    return types.SimpleNamespace(returncode=0,stdout='installed',stderr='')
   raise AssertionError('unexpected command '+repr(a))
  d.cmd=fake_cmd
  state={};saves=[]
  result=d.ensure_distro(state,lambda:saves.append(state.get('stage')))
  assert result=='Blender 5.0.1'
  assert state['globalProotDistroUntouched'] is True and state['imageAndArchitectureVerified'] is True
  assert not any('debian' in x for argv in calls for x in argv)
  assert any(argv[3]=='install' and argv[-1]==d.IMAGE for argv in calls)
  calls.clear();result=d.ensure_distro(state,lambda:None)
  assert result=='Blender 5.0.1' and not any(argv[3]=='install' for argv in calls)
  # Fails closed for an existing wrong or broken named container.
  calls.clear();installed['value']=False
  def invalid_alias(argv,timeout=600,check=True,env=None,stream=False):
   a=list(map(str,argv));calls.append(a)
   if a[3]=='login':return types.SimpleNamespace(returncode=1,stdout='',stderr='bad container')
   if a[3]=='list':return types.SimpleNamespace(returncode=0,stdout=d.DISTRO+'\n',stderr='')
   raise AssertionError('must never install over an existing alias')
  d.cmd=invalid_alias
  try:d.ensure_distro({},lambda:None)
  except RuntimeError as err:assert 'REFUSE_OVERWRITE' in str(err)
  else:raise AssertionError('existing corrupted alias was overwritten')
 finally:d.cmd=oldcmd;d.install_private_pd=oldinstall;d.pd_command=oldpd

def test_output_collision(tmp):
 src=tmp/'a';src.write_text('A');dst=tmp/'b';dst.write_text('B')
 try:d.copy_no_clobber(src,dst)
 except RuntimeError as e:assert 'COLLISION' in str(e)
 else:raise AssertionError('overwrite allowed')

def main():
 with tempfile.TemporaryDirectory(prefix='obs-v209-regression-') as td:
  p=pathlib.Path(td)
  test_patch(p/'patch');(p/'copy').mkdir();test_output_collision(p/'copy')
 with tempfile.TemporaryDirectory(prefix='obs-v209-git-') as td:
  p=pathlib.Path(td)
  with contextlib.redirect_stdout(io.StringIO()):test_commit_and_receipts(p)
 with tempfile.TemporaryDirectory(prefix='obs-v209-native-') as td:
  p=pathlib.Path(td)
  with contextlib.redirect_stdout(io.StringIO()):test_frames_failfast(p)
 with tempfile.TemporaryDirectory(prefix='obs-v210-cli-') as td:
  p=pathlib.Path(td)
  with contextlib.redirect_stdout(io.StringIO()):test_private_oci_cli_guards(p)
 print('TEST_DRIVER=PASS patched_blender5_context Git_source_commit_push_readback evidence_binary_readback crash_stage_gating private_official_OCI_CLI_sha_and_alias_gates',flush=True)

if __name__=='__main__':main()
