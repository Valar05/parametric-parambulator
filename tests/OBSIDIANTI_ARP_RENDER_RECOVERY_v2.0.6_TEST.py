#!/usr/bin/env python3
"""Regression tests for actual file recovery, no vendor pretend execution."""
from __future__ import annotations
import ast,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,tempfile,types
from PIL import Image
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('recovery_driver',HERE/'driver.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
contract=json.loads((HERE/'contract.json').read_text())
assert contract['authority']=='TERMUX_GIT_ONLY'
assert contract['sourceMutablePaths']==sorted(d.SRC)
assert contract['priorRunId']==d.PREVRUN
assert contract['lockedModelPaths']==list(d.LOCKED)
assert contract['canonicalGLBSHA256']==d.CANON
assert 'recover_one(previous,root,clip,downloads)' in (HERE/'driver.py').read_text()
for py in ('driver.py','gif_writer.py','saved_render.py','test_driver.py'):
 ast.parse((HERE/py).read_text())

def frame(dest,n,suffix='.png'):
 dest.mkdir(parents=True,exist_ok=True)
 p=dest/('frame_%03d'%n+suffix)
 Image.new('RGB',(512,512),((n*16)%256,80,n*12)).save(p,format='PNG')
 return p

def sha(s):return hashlib.sha256(s).hexdigest()

def make_trial(root,clip,render_status='VISUAL_REVIEW_PENDING_MOTION_GATE_PASS',frames=True):
 p=root/'work'/clip/'trial';p.mkdir(parents=True)
 data={'status':render_status,'inputSHA256':{'source':d.ARES if clip=='AxeKick' else d.LION,'target':d.CANON},
       'targetAction':clip+'_Retarget','sourceRig':'Donor','targetRig':'Target','targetMeshes':['Mesh'],
       'sourceMotion':{'sampledFrames':17},'targetMotion':{'sampledFrames':17},
       'motionGate':True,'mapping':{'boneCount':22},'actionRange':[1,20]}
 (p/('ARP_'+clip+'_UNAPPROVED.blend')).write_bytes(b'BLENDER FAKE TEST FIXTURE NOT ARP')
 data['blendSHA256']=d.sha(p/('ARP_'+clip+'_UNAPPROVED.blend'))
 (p/'TRIAL.json').write_text(json.dumps(data))
 if frames:
  for i in range(16):frame(p/'frames',i,'.png.png')
 return p

def run(cmd,cwd=None):
 p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True)
 if p.returncode:raise AssertionError(f'FAILED {cmd} {p.stderr[-700:]}')
 return p.stdout.strip()

with tempfile.TemporaryDirectory() as td:
 root=pathlib.Path(td)
 old=root/'prior';new=root/'new';new.mkdir()
 make_trial(old,'AxeKick')
 files,diagnosis=d.find_frames(old/'work'/'AxeKick','AxeKick')
 assert len(files)==16 and files[0].name=='frame_000.png.png'
 out,outputs=d.recover_one(old,new,'AxeKick',root)
 assert out['status']=='BLENDER_VISUAL_EVIDENCE_RECOVERED_OWNER_REVIEW_PENDING'
 assert out['distinctFrames']==16 and outputs['gif'].stat().st_size>1000
 assert outputs['contact'].stat().st_size>1000
 assert Image.open(outputs['gif']).n_frames==16
 assert Image.open(outputs['contact']).size==(1280,1280)
 # Incomplete image set must not masquerade as animation evidence.
 make_trial(old,'Heavy1',frames=False)
 missing,detection=d.find_frames(old/'work'/'Heavy1','Heavy1')
 assert missing==[] and detection['candidates']==0
 # Fallback re-renders ONLY a verified .blend; its real code can be unavailable here,
 # so inject an explicit fake frame-producer and prove the recovery control flow.
 original=d.render_saved
 invocations=[]
 def fixture_render(runroot,project,output,metadata,clip):
  invocations.append(clip)
  for i in range(16):frame(output/'render'/'frames',i)
  return {'status':'RENDERED_SAVED_ARP_ACTION','frameCount':16}
 d.render_saved=fixture_render
 result,outputs=d.recover_one(old,new,'Heavy1',root)
 d.render_saved=original
 assert invocations==['Heavy1'] and result['distinctFrames']==16
 assert result['status']=='BLENDER_VISUAL_EVIDENCE_RECOVERED_OWNER_REVIEW_PENDING'
 assert result['rerender']['status']=='RENDERED_SAVED_ARP_ACTION'
 # A failed original trial is not eligible for fake success.
 source=old/'work'/'Heavy1'/'trial'/'TRIAL.json';j=json.loads(source.read_text());j['status']='BLOCKED';source.write_text(json.dumps(j))
 guard,out=d.recover_one(old,new,'Heavy1',root)
 assert guard['status']=='PRIOR_TRIAL_NOT_COMPLETED' and not out
 # Wrong binary SHA fails even when filenames and frame counts are plausible.
 j['status']='VISUAL_REVIEW_PENDING_MOTION_GATE_PASS';j['inputSHA256']['target']='f'*64;source.write_text(json.dumps(j))
 guard,out=d.recover_one(old,new,'Heavy1',root)
 assert guard['status']=='PRIOR_TARGET_SHA_NOT_PINNED'
 # Test original run receipt identity, including vendor and source hashes.
 p=root/'previous';p.mkdir()
 previous_rec={'schema':d.PREV,'runId':d.PREVRUN,'gitEvidenceCommit':d.BASE,
               'canonicalGLBSHA256':d.CANON,'sourceBlenderSHA256':d.LION,
               'vendorZIPsha256':d.ARPZIP,'arpProbe':{'status':'REAL_PURCHASED_ARP_REMAP_HEADLESS_OPERATOR_REGISTRATION_PASS'},
               'originalCanonicalModelUnchanged':True}
 (p/'RECEIPT.json').write_text(json.dumps(previous_rec))
 assert d.verify_prior(p)['schema']==d.PREV
 previous_rec['vendorZIPsha256']='0'*64
 (p/'RECEIPT.json').write_text(json.dumps(previous_rec))
 try:d.verify_prior(p);raise AssertionError('untrusted vendor zip accepted')
 except RuntimeError as ex:assert 'V205_VENDOR_OR_DONOR_SHA_MISMATCH' in str(ex)
 # Exercise a real disposable Git remote, commits, push, remote fetch readback.
 bare=root/'remote.git';work=root/'setup'
 run(['git','init','--bare','--initial-branch=main',str(bare)])
 run(['git','clone',str(bare),str(work)])
 run(['git','config','user.name','Test'],cwd=work)
 run(['git','config','user.email','test@example.invalid'],cwd=work)
 (work/'AGENTS.md').write_text('Fixture rules v1\n')
 ptr=work/d.LOCKED[0];ptr.parent.mkdir(parents=True,exist_ok=True)
 ptr.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:'+d.CANON+'\nsize 16978732\n')
 prior=work/d.PREVEV;prior.parent.mkdir(parents=True,exist_ok=True)
 prior.write_text(json.dumps({'runId':d.PREVRUN,'privateAddonHeadlessProbe':{'status':'REAL_PURCHASED_ARP_REMAP_HEADLESS_OPERATOR_REGISTRATION_PASS'},
  'canonicalGLBSHA256':d.CANON,'nativeLionheartBlendSHA256':d.LION,
  'privateAddonZIPSHA256':d.ARPZIP,'canonicalModified':False,
  'trials':{k:{'error':'BLENDER_RENDER_FRAME_COUNT_INVALID_0'} for k in ('Ares','Lionheart')}}))
 run(['git','add','.'],cwd=work);run(['git','commit','-m','Fixture baseline'],cwd=work)
 base=run(['git','rev-parse','HEAD'],cwd=work)
 run(['git','push','origin','main'],cwd=work)
 original=(d.REMOTE,d.BASE,d.AGENTS)
 d.REMOTE=str(bare);d.BASE=base;d.AGENTS=run(['git','rev-parse','HEAD:AGENTS.md'],cwd=work)
 isolated=root/'isolated';isolated.mkdir()
 repo,head,ev=d.clone(isolated)
 assert head==base and ev['runId']==d.PREVRUN
 launcher=root/'sample-launcher.sh';launcher.write_text('echo fixture\n')
 result=d.source_publish(repo,HERE,launcher)
 assert len(result)==40 and result==d.g(repo,'rev-parse','HEAD')
 assert result==d.git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]
 assert d.source_publish(repo,HERE,launcher)==result
 # Publish a real binary and verify exact remote bytes.
 report=repo/'diagnostics/test/EVIDENCE.json';report.parent.mkdir(parents=True)
 report.write_text('{"test":true}\n')
 d.git(repo,'add','--','diagnostics/test/EVIDENCE.json')
 d.git(repo,'commit','-m','Publish test report')
 pub=d.publish(repo,'TEST')
 data=subprocess.run(['git','-C',str(repo),'cat-file','blob','refs/remotes/origin/main:diagnostics/test/EVIDENCE.json'],capture_output=True,check=True).stdout
 assert sha(data)==d.sha(report)
 # No overwrite on a changed source file even though the destination name matches.
 launcher.write_text('echo changed\n')
 try:d.source_publish(repo,HERE,launcher);raise AssertionError('collision accepted')
 except RuntimeError as ex:assert 'CAMPAIGN_VERSION_PATH_COLLISION' in str(ex)
 d.REMOTE,d.BASE,d.AGENTS=original
print('RECOVERY_TESTS_PASS: actual gif assembly, double-suffix discovery, saved-project fallback control flow, invalid trial/identity rejection, disposable Git source+evidence remote readback and collisions')
