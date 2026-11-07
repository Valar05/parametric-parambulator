#!/usr/bin/env python3
"""Termux-only recovery of genuine prior ARP trial, no vendor/model mutation."""
from __future__ import annotations
import datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys, time, traceback, uuid
from PIL import Image
from gif_writer import assemble

V='OBSIDIANTI_ARP_RENDER_RECOVERY_v2.0.6'
PREV='OBSIDIANTI_ARP_FIRST_LIVE_v2.0.5'
PREVRUN='20261106T235842Z-73d0582a'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE='ab13be07fea9d8e289401fde04b7da2f534b9f0d'
PREVEV='diagnostics/obsidianti/arp-first-live-v2.0.5/runs/'+PREVRUN+'/EVIDENCE.json'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
LION='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
ARES='63b6e7a7250cfb03e49cf0d335101d808126ae926894d74c1b2a6a49936b8b2a'
ARPZIP='2b377bbc5d81dfcef4209971e332a8bcb402ed44605e5ed0cddc2e90fafebf28'
LOCKED=('assets/obsidianti/Obsidianti.glb','assets/repl/Repl.glb')
SRC={'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER','campaigns/'+V+'_driver.py':'driver.py',
     'campaigns/'+V+'_saved_render.py':'saved_render.py','campaigns/'+V+'_gif_writer.py':'gif_writer.py',
     'campaigns/'+V+'.contract.json':'contract.json', 'tests/'+V+'_TEST.py':'test_driver.py'}
OUTDIR='diagnostics/obsidianti/arp-render-recovery-v2.0.6/runs/'
CLIPS=('AxeKick','Heavy1')

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(1<<20),b''):h.update(x)
 return h.hexdigest()

def command(argv,timeout=240,check=True,env=None):
 p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+repr(list(map(str,argv))[:6])+' '+p.stderr[-900:]+' '+p.stdout[-450:])
 return p

def git(repo,*a,timeout=240,check=True):return command(['git','-C',repo,*a],timeout=timeout,check=check)
def g(repo,*a):return git(repo,*a).stdout.strip()

def copy_noclobber(src,dst):
 src=pathlib.Path(src);dst=pathlib.Path(dst)
 if not src.is_file() or src.is_symlink():raise RuntimeError('SOURCE_NOT_REGULAR_FILE '+str(src))
 if dst.exists():
  if dst.is_file() and not dst.is_symlink() and sha(dst)==sha(src):return
  raise RuntimeError('NO_OVERWRITE_COLLISION '+str(dst))
 dst.parent.mkdir(parents=True,exist_ok=True)
 temp=dst.with_name('.'+dst.name+'.'+uuid.uuid4().hex[:8]+'.tmp')
 try:
  shutil.copyfile(src,temp)
  if sha(src)!=sha(temp):raise RuntimeError('COPY_SHA_MISMATCH')
  os.replace(temp,dst)
 finally:
  if temp.exists():temp.unlink()

def clone(root):
 repo=root/'repo'
 env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
 p=command(['git','clone','--quiet','--depth=1','--single-branch','--branch=main',REMOTE,repo],timeout=480,env=env)
 if g(repo,'remote','get-url','origin').removesuffix('.git')!=REMOTE.removesuffix('.git'):
  raise RuntimeError('WRONG_GIT_REMOTE')
 head=g(repo,'rev-parse','HEAD')
 if head!=BASE:
  if git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False).returncode:
   git(repo,'fetch','--no-tags','--depth=120','origin',BASE,timeout=240)
   if git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False).returncode:
    raise RuntimeError('GIT_MAIN_NOT_DESCENDED_FROM_V205_VERIFIED_OUTPUT')
 if g(repo,'rev-parse','HEAD:AGENTS.md')!=AGENTS:raise RuntimeError('AGENTS_BLOB_CHANGED')
 if 'oid sha256:'+CANON not in git(repo,'show','HEAD:'+LOCKED[0]).stdout:
  raise RuntimeError('CANONICAL_GLB_LFS_POINTER_CHANGED')
 ev=json.loads(git(repo,'show','HEAD:'+PREVEV).stdout)
 assert ev['runId']==PREVRUN and ev['privateAddonHeadlessProbe']['status']=='REAL_PURCHASED_ARP_REMAP_HEADLESS_OPERATOR_REGISTRATION_PASS'
 assert ev['canonicalGLBSHA256']==CANON and ev['nativeLionheartBlendSHA256']==LION
 assert ev['privateAddonZIPSHA256']==ARPZIP and ev['canonicalModified'] is False
 assert all(ev['trials'][k]['error']=='BLENDER_RENDER_FRAME_COUNT_INVALID_0' for k in ('Ares','Lionheart'))
 if g(repo,'status','--porcelain'):raise RuntimeError('ISOLATED_CLONE_DIRTY')
 return repo,head,ev

def publish(repo,phase):
 local=g(repo,'rev-parse','HEAD')
 for n in range(3):
  p=git(repo,'push','origin','HEAD:refs/heads/main',timeout=320,check=False)
  if p.returncode==0:break
  if n==2:raise RuntimeError('REMOTE_PUSH_FAILED_'+phase+' '+p.stderr[-1100:])
  time.sleep(n+1)
 remote=git(repo,'ls-remote','origin','refs/heads/main',timeout=120).stdout.split()
 if not remote or remote[0]!=local:raise RuntimeError('REMOTE_HEAD_READBACK_MISMATCH_'+phase)
 git(repo,'fetch','--quiet','origin','main',timeout=240)
 if g(repo,'rev-parse','refs/remotes/origin/main')!=local:raise RuntimeError('REMOTE_FETCH_SHA_MISMATCH_'+phase)
 return local

def source_publish(repo,packet,launcher):
 pending={path:launcher if src=='LAUNCHER' else packet/src for path,src in SRC.items()}
 exist=[name for name in pending if (repo/name).exists()]
 if exist:
  if len(exist)==len(pending) and all(sha(repo/p)==sha(f) for p,f in pending.items()):
   return g(repo,'log','-1','--format=%H','--',next(iter(pending)))
  raise RuntimeError('CAMPAIGN_VERSION_PATH_COLLISION '+repr(exist))
 for name,f in pending.items():copy_noclobber(f,repo/name)
 git(repo,'add','--',*sorted(pending))
 if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(pending):raise RuntimeError('SOURCE_GIT_STAGING_ALLOWLIST_FAILED')
 if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Termux ARP Recovery')
 if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','termux-arp-recovery@users.noreply.github.com')
 git(repo,'commit','-m','Obsidianti: recover real ARP Blender frames without repeating retarget')
 return publish(repo,'SOURCE')

def prior_inventory(trialroot):
 files=[]
 if trialroot.is_dir():
  for p in trialroot.rglob('*'):
   if p.is_file() and not p.is_symlink():
    rel=str(p.relative_to(trialroot))
    files.append({'path':rel,'bytes':p.stat().st_size})
 return sorted(files,key=lambda x:x['path'])[:120]

def find_frames(prior_work,clip):
 """Find and validate 16 real PNGs, accepting Blender-generated extra suffixes.
 No source image creation, metadata-only frames, or filename-only validation.
 """
 candidates=[]
 if prior_work.is_dir():
  for p in prior_work.rglob('frame_*'):
   if p.is_symlink() or not p.is_file() or p.stat().st_size<1000 or p.stat().st_size>15_000_000:continue
   m=re.search(r'frame_(\d{3})(?:\D|$)',p.name)
   if not m:continue
   idx=int(m.group(1))
   if not 0<=idx<16:continue
   try:
    with Image.open(p) as im:
     if im.format!='PNG' or im.size!=(512,512):continue
     im.verify()
   except (OSError,ValueError):continue
   candidates.append((idx,p))
 groups={}
 for idx,p in candidates:groups.setdefault(p.parent,{})[idx]=p
 valid=[(parent,d) for parent,d in groups.items() if len(d)==16]
 if not valid:return [],{'candidates':len(candidates),'parentGroups':{str(k):len(v) for k,v in groups.items()}}
 valid.sort(key=lambda x:(len(x[0].parts),str(x[0])))
 parent,d=valid[0]
 return [d[i] for i in range(16)],{'candidates':len(candidates),'selectedParent':str(parent),'sourceFilenames':[d[i].name for i in range(16)]}

def verify_prior(previous):
 if not previous.is_dir():raise RuntimeError('PERSISTENT_V205_RUN_MISSING '+str(previous))
 receipt=previous/'RECEIPT.json'
 if not receipt.is_file():raise RuntimeError('PERSISTENT_V205_RECEIPT_MISSING')
 data=json.loads(receipt.read_text())
 if data.get('runId')!=PREVRUN or data.get('schema')!=PREV:raise RuntimeError('PERSISTENT_RUN_IDENTITY_MISMATCH')
 if data.get('gitEvidenceCommit')!=BASE or data.get('canonicalGLBSHA256')!=CANON:
  raise RuntimeError('V205_GIT_EVIDENCE_OR_CANONICAL_SHA_MISMATCH')
 if data.get('vendorZIPsha256')!=ARPZIP or data.get('sourceBlenderSHA256')!=LION:
  raise RuntimeError('V205_VENDOR_OR_DONOR_SHA_MISMATCH')
 if data.get('arpProbe',{}).get('status')!='REAL_PURCHASED_ARP_REMAP_HEADLESS_OPERATOR_REGISTRATION_PASS':
  raise RuntimeError('V205_REAL_ARP_HEADLESS_PROBE_NOT_VERIFIED')
 if data.get('originalCanonicalModelUnchanged') is not True:
  raise RuntimeError('V205_REPORTED_CANONICAL_MODIFICATION')
 return data

def render_saved(root,project,out,metadata,clip):
 script=root/'saved_render.py'
 out.mkdir(parents=True,exist_ok=False)
 inputs=out/'input.json';inputs.write_text(json.dumps(metadata,sort_keys=True)+'\n')
 if shutil.which('proot-distro'):
  cmd=['proot-distro','login','debian',
       '--bind',str(project.parent.resolve())+':/mnt/arp-saved',
       '--bind',str(root.resolve())+':/mnt/arp-recovery','--',
       'blender','--background','--factory-startup','--disable-autoexec',
       '--python','/mnt/arp-recovery/saved_render.py','--',
       '--blend','/mnt/arp-saved/'+project.name,
       '--input','/mnt/arp-recovery/'+str(inputs.relative_to(root)),
       '--output','/mnt/arp-recovery/'+str(out.relative_to(root))+'/render']
 elif shutil.which('blender'):
  cmd=['blender','--background','--factory-startup','--disable-autoexec','--python',str(script),'--',
       '--blend',str(project),'--input',str(inputs),'--output',str(out/'render')]
 else:raise RuntimeError('BLENDER_UNAVAILABLE_FOR_SAVED_PROJECT_RECOVERY')
 p=command(cmd,timeout=1200,check=False)
 (out/'BLENDER_RECOVERY.log').write_text(p.stdout+'\n'+p.stderr)
 status=out/'render/RENDER.json'
 if not status.is_file():raise RuntimeError('SAVED_PROJECT_RENDER_NO_RECEIPT '+p.stderr[-550:])
 rec=json.loads(status.read_text())
 if p.returncode or rec.get('status')!='RENDERED_SAVED_ARP_ACTION':
  raise RuntimeError('SAVED_PROJECT_BLENDER_RENDER_FAILED '+str(rec.get('error',p.stderr[-400:]))[:450])
 return rec

def recover_one(previous,root,clip,downloads):
 name='Ares' if clip=='AxeKick' else 'Lionheart'
 work=previous/'work'/clip
 trial=work/'trial'
 rec={'clip':clip,'donorName':name,'ownerVisualVerdict':'PENDING',
      'canonicalModelModified':False,'stage':'READ_PREVIOUS',
      'priorInventory':prior_inventory(trial)}
 metadata=trial/'TRIAL.json'
 if not metadata.is_file():rec.update({'status':'NO_ORIGINAL_BLENDER_TRIAL_RECEIPT'});return rec,{}
 original=json.loads(metadata.read_text())
 rec['sourceTrialStatus']=original.get('status')
 rec['originalClipSHA']=original.get('inputSHA256',{})
 rec['targetAction']=original.get('targetAction')
 rec['sourceMotion']=original.get('sourceMotion',{})
 rec['targetMotion']=original.get('targetMotion',{})
 rec['motionGate']=original.get('motionGate')
 rec['sourceRig']=original.get('sourceRig');rec['targetRig']=original.get('targetRig')
 rec['mapping']=original.get('mapping',{})
 rec['blenderExitCode']=0 # prior driver only assembled when this was zero and trial wasn't BLOCKED
 if original.get('inputSHA256',{}).get('target')!=CANON:
  rec.update({'status':'PRIOR_TARGET_SHA_NOT_PINNED'});return rec,{}
 want=ARES if clip=='AxeKick' else LION
 if original.get('inputSHA256',{}).get('source')!=want:
  rec.update({'status':'PRIOR_SOURCE_SHA_NOT_PINNED'});return rec,{}
 if original.get('status') not in ('VISUAL_REVIEW_PENDING_MOTION_GATE_PASS','REJECTED_BUT_RENDERED_ANATOMY_OR_ARTICULATION'):
  rec.update({'status':'PRIOR_TRIAL_NOT_COMPLETED','originalError':str(original.get('error',''))[:600]});return rec,{}
 found,details=find_frames(work,clip)
 rec['frameDiscovery']=details
 project=trial/('ARP_'+clip+'_UNAPPROVED.blend')
 if project.is_file() and not project.is_symlink():
  rec['savedBlenderSHA256']=sha(project)
  if rec['savedBlenderSHA256']!=original.get('blendSHA256'):
   rec.update({'status':'SAVED_BLEND_SHA_MISMATCH'});return rec,{}
 else:rec['savedBlenderSHA256']='MISSING'
 if len(found)!=16:
  if not project.is_file() or project.is_symlink():
   rec.update({'status':'FRAMES_AND_SAVED_BLEND_MISSING','priorInventoryAfter':prior_inventory(trial)});return rec,{}
  rerenderdir=root/clip/'rerender'
  rerenderdir.parent.mkdir(parents=True,exist_ok=True)
  try:
   info=render_saved(root,project,rerenderdir,original,clip)
   rec['rerender']={k:v for k,v in info.items() if k in ('status','targetAction','targetArmature','frameCount','framing')}
  except Exception as ex:
   rec.update({'status':'SAVED_BLEND_RERENDER_FAILED','rerenderFailure':type(ex).__name__+' '+str(ex)[:500]});return rec,{}
  found,more=find_frames(rerenderdir,clip)
  rec['frameDiscoveryAfterRerender']=more
  if len(found)!=16:
   rec.update({'status':'RENDER_DONE_BUT_16_FRAMES_UNAVAILABLE','frameDiscoveryAfterRerender':more});return rec,{}
 else:rec['reusedOriginalFrames']=True
 output=root/clip/'artifacts';output.mkdir(parents=True,exist_ok=False)
 staged=output/'frames';staged.mkdir()
 for i,src in enumerate(found):
  copy_noclobber(src,staged/('frame_%03d.png'%i))
 graphic=assemble(staged,output,clip)
 if graphic['frames']!=16:raise RuntimeError('REBUILT_GIF_FRAME_COUNT_WRONG')
 rec.update({'status':'BLENDER_VISUAL_EVIDENCE_RECOVERED_OWNER_REVIEW_PENDING',
             'graphic':{k:v for k,v in graphic.items() if k not in ('gif','contact')},
             'distinctFrames':graphic['distinctFrames']})
 return rec,{'gif':pathlib.Path(graphic['gif']),'contact':pathlib.Path(graphic['contact']),
             'blend':project if project.is_file() else None}

def main(packet,launcher,launcher_sha):
 packet=pathlib.Path(packet);launcher=pathlib.Path(launcher)
 members=json.loads((packet/'manifest.json').read_text())
 wanted={'driver.py','saved_render.py','gif_writer.py','test_driver.py','contract.json'}
 if set(members)!=wanted:raise RuntimeError('PAYLOAD_MEMBERS_INVALID')
 for p,dig in members.items():
  if sha(packet/p)!=dig:raise RuntimeError('PAYLOAD_MEMBER_SHA_FAILED_'+p)
 contract=json.loads((packet/'contract.json').read_text())
 if contract['sourceMutablePaths']!=sorted(SRC) or contract['authority']!='TERMUX_GIT_ONLY':
  raise RuntimeError('CONTRACT_AUTHORITY_OR_SOURCE_SCOPE_MISMATCH')
 command(['python3','-m','py_compile',*[packet/x for x in ('driver.py','saved_render.py','gif_writer.py','test_driver.py')]])
 command(['python3',packet/'test_driver.py'],timeout=120)
 if not launcher.is_file() or launcher.is_symlink():raise RuntimeError('LAUNCHER_NOT_REAL_FILE')
 if sha(launcher)!=launcher_sha:raise RuntimeError('LAUNCHER_SHA_CHANGED')
 downloads=pathlib.Path.home()/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('ANDROID_DOWNLOADS_MISSING')
 previous=pathlib.Path.home()/'.local/state'/PREV/PREVRUN
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
 receipt=root/'RECEIPT.json'
 state={'campaign':V,'runId':runid,'status':'BOOT','authority':'TERMUX_GIT_ONLY',
        'priorRunId':PREVRUN,'priorGitEvidenceCommit':BASE,
        'launcherSHA256':launcher_sha,'modelSHA256':CANON,'sourceSHA256':LION,
        'vendorZIPsha256':ARPZIP,'gitRulesBlob':AGENTS,'canonicalModified':False,
        'vendorCodePublished':False,'ownerVisualAcceptance':'PENDING'}
 def save():
  tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2,sort_keys=True)+'\n');os.replace(tmp,receipt)
 save()
 try:
  original=verify_prior(previous)
  state['priorRunVerified']=True;save()
  repo,head,prev_evidence=clone(root)
  state['gitInputHead']=head;state['protectedBefore']={p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED};save()
  source=source_publish(repo,packet,launcher)
  state['sourceCommit']=source;state['status']='SOURCE_REMOTE_VERIFIED';save()
  copy_noclobber(packet/'saved_render.py',root/'saved_render.py')
  clips={};outputs={}
  for clip in CLIPS:
   result,graphics=recover_one(previous,root,clip,downloads)
   clips[clip]=result;outputs[clip]=graphics
   state['clipStatuses']={k:v.get('status') for k,v in clips.items()};save()
   print('RECOVERY_'+clip.upper()+'='+result.get('status'),flush=True)
  evidence=root/'evidence';evidence.mkdir()
  report=evidence/'REPORT.md';jsonfile=evidence/'EVIDENCE.json'
  public={'schema':V,'runId':runid,'sourceCommit':source,'priorRunId':PREVRUN,'priorEvidenceCommit':BASE,
          'originalBlenderRegistration':'VERIFIED_PURCHASED_AUTO_RIG_PRO_3.79.17',
          'canonicalSHA256':CANON,'donorSHA256':LION,'aresSHA256':ARES,'privateAddonZIPSHA256':ARPZIP,
          'gitRulesBlob':AGENTS,'campaignEtiquette':'READ_LIVE_2026_11_06',
          'authority':'TERMUX_GIT_ONLY','canonicalModified':False,'vendorSourcePublished':False,
          'ownerVisualAcceptance':'PENDING','clips':clips}
  jsonfile.write_text(json.dumps(public,indent=2,sort_keys=True)+'\n')
  report.write_text('# Auto-Rig Pro first-trial visual recovery\n\nRecovered from exact persisted v2.0.5 Termux Blender trials, '
    'not a new solver or retarget. The installed proprietary ARP add-on and original GLB were untouched.\n\n'
    +'\n'.join('- '+clip+': '+clips[clip]['status']+'; original Blender status: '+str(clips[clip].get('sourceTrialStatus'))
               +'; distinct frames: '+str(clips[clip].get('distinctFrames','unavailable')) for clip in CLIPS)
    +'\n\nAll images are UNAPPROVED. Motion, anatomy and contact require owner review.\n')
  destinations={OUTDIR+runid+'/REPORT.md':report,OUTDIR+runid+'/EVIDENCE.json':jsonfile}
  for clip,outs in outputs.items():
   for kind in ('gif','contact'):
    p=outs.get(kind)
    if p:destinations[OUTDIR+runid+'/'+clip+'/'+p.name]=p
  if any((repo/p).exists() for p in destinations):raise RuntimeError('NEW_GIT_EVIDENCE_PATH_COLLISION')
  for p,f in destinations.items():copy_noclobber(f,repo/p)
  git(repo,'add','--',*sorted(destinations))
  if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(destinations):
   raise RuntimeError('EVIDENCE_GIT_STAGING_ALLOWLIST_FAILED')
  git(repo,'commit','-m','Obsidianti: publish recovered ARP Blender-rendered Ares and Lionheart evidence')
  published=publish(repo,'EVIDENCE')
  if {p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}!=state['protectedBefore']:
   raise RuntimeError('CANONICAL_GIT_MODEL_BLOB_CHANGED')
  for dest,f in destinations.items():
   blob=subprocess.run(['git','-C',str(repo),'cat-file','blob','refs/remotes/origin/main:'+dest],
                       capture_output=True,timeout=180,check=True).stdout
   if hashlib.sha256(blob).hexdigest()!=sha(f):raise RuntimeError('REMOTE_OUTPUT_BLOB_SHA_READBACK_FAILED '+dest)
  for clip,outs in outputs.items():
   for kind in ('gif','contact','blend'):
    p=outs.get(kind)
    if p:
     d=downloads/(V+'_'+runid+'_'+clip+'_'+p.name)
     copy_noclobber(p,d)
     print('DOWNLOAD_'+clip.upper()+'_'+kind.upper()+'='+str(d)+' SHA256='+sha(d),flush=True)
   if outs.get('gif'):
    url='https://github.com/Valar05/parametric-parambulator/blob/'+published+'/'+OUTDIR+runid+'/'+clip+'/'+outs['gif'].name
    print('GIF_URL_'+clip.upper()+'='+url,flush=True)
  state['gitEvidenceCommit']=published
  state['status']='VISUAL_EVIDENCE_GIT_PUBLISHED_OWNER_REVIEW_PENDING' if any(outputs.values()) else 'RECOVERY_NO_RENDER_ARTIFACT__DIAGNOSTIC_GIT_PUBLISHED'
  save()
  print('REPORT_URL=https://github.com/Valar05/parametric-parambulator/blob/'+published+'/'+OUTDIR+runid+'/REPORT.md',flush=True)
  print('CANONICAL_MODEL_UNCHANGED=YES',flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as ex:
  state.update({'status':'BLOCKED','error':type(ex).__name__+' '+str(ex)[:950],'tracebackLocal':traceback.format_exc()[-3800:]});save()
  print('STATUS=BLOCKED '+state['error'],flush=True)
  raise
 finally:
  save();print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('USAGE driver.py packet launcher launcher_sha')
 main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve(),sys.argv[3])
