#!/usr/bin/env python3
"""One-click Termux Git campaign: enrich the SAME Obsidianti canonical GLB with full motions.

No direct GitHub mutation, no Pose Lab workspace, no Windows/cauldron substitution.
Source scripts MUST be committed to the authorized repo, then canonical model updated there.
"""
from __future__ import annotations
import datetime, hashlib, json, os, pathlib, shutil, struct, subprocess, sys, time, uuid

CAMPAIGN='OBSIDIANTI_FULL_LIBRARY_v1.1.0'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
REPO='Valar05/parametric-parambulator'
CANONICAL='assets/obsidianti/Obsidianti.glb'
BASE_SHA='27f943ddf1ba1f72169026a2cb4750662f00b053f78e4346f43b3888c744e95b'
GFT='https://github.com/Valar05/gravity-fist-threejs.git'
SCRIPTS={
 'campaigns/OBSIDIANTI_FULL_LIBRARY_v1.1.0.sh':'campaigns/OBSIDIANTI_FULL_LIBRARY_v1.1.0.sh',
 'campaigns/OBSIDIANTI_FULL_LIBRARY_RUN_v1.1.0.py':'campaigns/OBSIDIANTI_FULL_LIBRARY_RUN_v1.1.0.py',
 'campaigns/OBSIDIANTI_GLTF_LIBRARY_v1.1.0.py':'campaigns/OBSIDIANTI_GLTF_LIBRARY_v1.1.0.py',
 'campaigns/OBSIDIANTI_SOURCE_SAMPLER_v1.1.0.py':'campaigns/OBSIDIANTI_SOURCE_SAMPLER_v1.1.0.py',
 'campaigns/OBSIDIANTI_FULL_LIBRARY_v1.1.0.contract.json':'campaigns/OBSIDIANTI_FULL_LIBRARY_v1.1.0.contract.json',
 'docs/obsidianti/FULL_LIBRARY_v1.1.0.md':'docs/obsidianti/FULL_LIBRARY_v1.1.0.md',
 'review/obsidianti-library-v1.1.0.html':'review/obsidianti-library-v1.1.0.html',
}
FILES={
 'payload/LionheartLancer.blend':'81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4',
 'payload/Obsidianti.blend':'68f7b29cfa76e0cc300d72fc37062ba786c1d6c75841f0b3a9c1ae78dbd33ce1',
 'payload/Obsidianti.idle-candidate.glb':BASE_SHA,
}

def h(path):
 result=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):result.update(b)
 return result.hexdigest()

def atomic_json(path,p):
 path.parent.mkdir(parents=True,exist_ok=True)
 t=path.with_suffix('.tmp');t.write_text(json.dumps(p,sort_keys=True,indent=2)+'\n');os.replace(t,path)

def command(args,cwd=None,env=None,timeout=150,check=True):
 p=subprocess.run(args,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+repr(args[:7])+' '+p.stderr[-1600:])
 return p

def git(path,args,**opts):return command(['git','-C',str(path),*args],**opts)

def ensure_tool(name,required=True):
 path=shutil.which(name)
 if not path and required:raise RuntimeError('TOOL_NOT_AVAILABLE '+name)
 return path

def git_file_sha(repo,path):
 p=git(repo,['show','HEAD:'+path],check=False)
 if p.returncode:return None
 raw=p.stdout
 if raw.startswith('version https://git-lfs.github.com/spec/v1'):
  for row in raw.splitlines():
   if row.startswith('oid sha256:'):return row.split(':',1)[1].strip()
  raise RuntimeError('LFS_POINTER_INVALID '+path)
 return hashlib.sha256(raw.encode()).hexdigest()

def lfs_oid(repo,path):
 p=git(repo,['show','HEAD:'+path]);text=p.stdout
 if not text.startswith('version https://git-lfs.github.com/spec/v1'):raise RuntimeError('CANONICAL_NOT_LFS '+path)
 return next(x[11:].strip() for x in text.splitlines() if x.startswith('oid sha256:'))

def validate_packet(packet):
 manifest=json.loads((packet/'manifest.json').read_text());assert manifest['campaign']==CAMPAIGN
 for rel,digest in manifest['files'].items():
  path=packet/rel
  if not path.is_file() or h(path)!=digest:raise RuntimeError('PACKET_FILE_SHA_MISMATCH '+rel)
 for name,expected in FILES.items():
  if manifest['files'].get(name)!=expected:raise RuntimeError('PACKET_SOURCE_PROVENANCE_ERROR '+name)
 for path in SCRIPTS:
  if path not in manifest['files']:raise RuntimeError('PACKET_SCRIPT_MISSING '+path)
 return manifest

def glb_anim_names(path):
 data=pathlib.Path(path).read_bytes()
 if len(data)<40 or data[:4]!=b'glTF' or struct.unpack_from('<I',data,8)[0]!=len(data):return []
 n,typ=struct.unpack_from('<I4s',data,12)
 if typ!=b'JSON':return []
 try:g=json.loads(data[20:20+n]);return [x['name'] for x in g.get('animations',[])]
 except Exception:return []

def find_ares(work):
 home=pathlib.Path.home()
 paths=[
  home/'storage/documents/GodotProjects/gravity-fist-threejs/assets/models/Ares.glb',
  home/'storage/documents/GodotProjects/pose-lab-v2/public/assets/ares/ares_rigged_diffuse.glb',
  home/'storage/documents/GodotProjects/gravity-fist/models/Ares.glb',
  pathlib.Path('/storage/emulated/0/Documents/GodotProjects/gravity-fist-threejs/assets/models/Ares.glb'),
  pathlib.Path('/storage/emulated/0/Documents/GodotProjects/pose-lab-v2/public/assets/ares/ares_rigged_diffuse.glb')
 ]
 required=['StepForward','StepBack','StepLeft','StepRight','StepForwardLeft','StepForwardRight','StepBackLeft','StepBackRight','AxeKick']
 for path in paths:
  if path.is_file():
   names=glb_anim_names(path)
   if all(any(n==x or n.startswith(x+'_') or n.startswith(x+'-') or n.startswith(x+'|') for n in names) for x in required):
    return path,{'method':'VERIFIED_EXISTING_PHONE_ASSET','sha256':h(path),'clips':names}
 donor=work/'gravity-fist-source';env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1';env['GIT_TERMINAL_PROMPT']='0'
 command(['git','clone','--depth=1','--branch','main','--single-branch',GFT,str(donor)],env=env,timeout=220)
 source=donor/'assets/models/Ares.glb'
 if not source.exists():raise RuntimeError('ARES_DONOR_PATH_MISSING_IN_SOURCE_REPOSITORY')
 # The repo uses LFS for imported GLBs; retrieve only Ares, not the whole asset library.
 get=git(donor,['lfs','pull','--include=assets/models/Ares.glb','--exclude='],timeout=240,check=False)
 if get.returncode or source.read_bytes()[:4]!=b'glTF':
  raise RuntimeError('ARES_LFS_FETCH_FAILED '+get.stderr[-1000:])
 names=glb_anim_names(source)
 if not all(any(n==x or n.startswith(x+'_') or n.startswith(x+'-') or n.startswith(x+'|') for n in names) for x in required):
  raise RuntimeError('ARES_DONOR_MISSING_REQUIRED_CLIPS '+repr(names))
 return source,{'method':'PINNED_TERMINAL_GIT_LFS_DONOR_FETCH','sha256':h(source),'clips':names,'gitHead':git(donor,['rev-parse','HEAD']).stdout.strip()}

def start_blender_sampler(packet,work,source,output,kind,repo):
 script=repo/'campaigns/OBSIDIANTI_SOURCE_SAMPLER_v1.1.0.py'
 native=shutil.which('blender')
 if native:
  args=[native,'--background','--python',str(script),'--','--kind',kind,'--source',str(source),'--out',str(output)]
 else:
  if not shutil.which('proot-distro'):raise RuntimeError('BLENDER_NOT_FOUND: native blender and proot-distro unavailable')
  source=pathlib.Path(source).resolve();packet=pathlib.Path(packet).resolve();work=pathlib.Path(work).resolve()
  # Read-only operations inside an isolated workdir. Bind the optional external Ares source folder explicitly.
  binder=['--bind',str(packet)+':/mnt/obs-packet','--bind',str(work)+':/mnt/obs-run','--bind',str(repo.resolve())+':/mnt/obs-repo']
  if source.is_relative_to(packet):sub='/mnt/obs-packet/'+str(source.relative_to(packet))
  elif source.is_relative_to(work):sub='/mnt/obs-run/'+str(source.relative_to(work))
  else:
   binder+=['--bind',str(source.parent)+':/mnt/obs-input'];sub='/mnt/obs-input/'+source.name
  args=['proot-distro','login','debian',*binder,'--','blender','--background','--python','/mnt/obs-repo/campaigns/OBSIDIANTI_SOURCE_SAMPLER_v1.1.0.py','--','--kind',kind,'--source',sub,'--out','/mnt/obs-run/'+output.name]
 p=command(args,timeout=420,check=False)
 (work/(kind+'-blender.log')).write_text(p.stdout+'\n'+p.stderr)
 if p.returncode:raise RuntimeError('BLENDER_SOURCE_EVALUATION_FAILED_'+kind+' '+p.stderr[-1100:])
 if not output.exists():raise RuntimeError('BLENDER_DID_NOT_CREATE_SOURCE_SAMPLES_'+kind)
 d=json.loads(output.read_text())
 if d['sourceKind']!=kind or d['actionCount']<10:raise RuntimeError('SOURCE_SAMPLE_INCOMPLETE_'+kind)
 return {'kind':kind,'sha256':h(output),'source':str(source),'clipCount':d['actionCount'],'blenderVersion':d.get('blenderVersion')}

def require_lfs():
 if command(['git','lfs','version'],check=False).returncode:
  pkg=shutil.which('pkg')
  if not pkg:raise RuntimeError('GIT_LFS_MISSING_AND_NO_TERMUX_PKG')
  command([pkg,'install','-y','git-lfs'],timeout=240)
 if command(['git','lfs','version'],check=False).returncode:raise RuntimeError('GIT_LFS_NOT_AVAILABLE')

def commit(repo,paths,message):
 if not paths:return None
 git(repo,['add','--',*paths])
 staged=git(repo,['diff','--cached','--name-only']).stdout.splitlines()
 if any(x not in paths for x in staged):raise RuntimeError('UNAUTHORIZED_STAGED_PATH')
 if not staged:return None
 if CANONICAL in staged:
  assert git(repo,['check-attr','filter','--',CANONICAL]).stdout.strip().endswith(': lfs')
  pointer=git(repo,['show',':'+CANONICAL]).stdout
  if not pointer.startswith('version https://git-lfs.github.com/spec/v1'):raise RuntimeError('CANONICAL_LFS_POINTER_MISSING')
 if not git(repo,['config','user.name'],check=False).stdout.strip():git(repo,['config','user.name','Obsidianti Termux Campaign'])
 if not git(repo,['config','user.email'],check=False).stdout.strip():git(repo,['config','user.email','obsidianti-campaign@users.noreply.github.com'])
 git(repo,['commit','-m',message],timeout=180)
 return git(repo,['rev-parse','HEAD']).stdout.strip()

def validate_clean_checkout(repo):
 if git(repo,['status','--porcelain=v1','--untracked-files=all']).stdout.strip():raise RuntimeError('WORKTREE_NOT_CLEAN')

def read_repo_rules(repo):
 p=repo/'AGENTS.md';text=p.read_text()
 if 'Termux Git only' not in text or 'Every campaign uses one uniquely versioned Android Termux' not in text:raise RuntimeError('REPO_AGENTS_READ_BLOCKED')
 return h(p)

def main():
 if len(sys.argv)!=2:raise RuntimeError('USAGE: campaign.py ABSOLUTE_PACKET_ROOT')
 packet=pathlib.Path(sys.argv[1]).resolve()
 if not packet.exists():raise RuntimeError('PACKET_MISSING')
 print('CAMPAIGN='+CAMPAIGN,flush=True)
 print('LANE=TERMUX_GIT_ONLY; NO_NEW_GLB_NAMES',flush=True)
 manifest=validate_packet(packet)
 print('PACKET_SOURCE_SHA_GUARDS=PASS',flush=True)
 for tool in ('git','python3'):ensure_tool(tool)
 require_lfs()
 timestamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 work=pathlib.Path.home()/'.local/state'/'obsidianti-full-library-v1.1.0'/(timestamp+'-'+uuid.uuid4().hex[:6]);work.mkdir(parents=True)
 downloads=pathlib.Path.home()/'storage/downloads';downloads=downloads if downloads.is_dir() else work
 receipt=downloads/(CAMPAIGN+'_'+timestamp+'_RECEIPT.json')
 state={'campaign':CAMPAIGN,'status':'STARTED','targetRepo':REPO,'canonicalModel':CANONICAL,'initialCanonicalSha256':BASE_SHA,'workdir':str(work),'packetManifestSha256':h(packet/'manifest.json'),'authorizedLane':'Termux Git only','etiquetteReadByAuthor':'Home Center current 2026-11-04','runtimeHumanVisualVerdict':'PENDING','ReplChanged':False,'reportPath':str(receipt)}
 atomic_json(receipt,state)
 try:
  env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1';env['GIT_TERMINAL_PROMPT']='0'
  repo=work/'target-repo'
  command(['git','clone','--depth=1','--branch','main','--single-branch',REMOTE,str(repo)],env=env,timeout=220)
  state['sourceHead']=git(repo,['rev-parse','HEAD']).stdout.strip();state['agentsSha256']=read_repo_rules(repo)
  validate_clean_checkout(repo)
  expected=git(repo,['show','HEAD:'+CANONICAL],check=False)
  if expected.returncode:raise RuntimeError('CANONICAL_ABSENT_RUN_v1.0.0_FIRST')
  current=lfs_oid(repo,CANONICAL)
  if current!=BASE_SHA:raise RuntimeError('BASELINE_MISMATCH_SOURCE_CHANGED; CURRENT='+current)
  orig_repl=git(repo,['rev-parse','HEAD:assets/repl/Repl.glb']).stdout.strip()
  got=git(repo,['lfs','pull','--include='+CANONICAL,'--exclude='],timeout=250,check=False)
  model=repo/CANONICAL
  if h(model)!=BASE_SHA:
   # If LFS transiently unavailable, the exact already-verified baseline is in the packet.
   fb=packet/'payload/Obsidianti.idle-candidate.glb'
   if not fb.is_file() or h(fb)!=BASE_SHA:raise RuntimeError('MODEL_BASELINE_FALLBACK_MISSING')
   model.write_bytes(fb.read_bytes())
  if h(model)!=BASE_SHA:raise RuntimeError('CANONICAL_SOURCE_BYTES_NOT_VERIFIED')
  state['canonicalReadbackSha256']=h(model)
  state['repoRead']={'head':state['sourceHead'],'agentsSha256':state['agentsSha256'],'canonicalSha256':state['canonicalReadbackSha256']}
  # Git-FIRST: add unique campaign script, source sampler, patcher, docs and viewer
  # before running any of them. This is an isolated verified checkout, not the
  # owner's existing phone workspace. Commit source first; model is a separate
  # subsequent commit, with no new GLB filename.
  for dest,src in SCRIPTS.items():
   pd=repo/dest;ps=packet/src
   if pd.exists():
    if h(pd)!=h(ps):raise RuntimeError('VERSIONED_CAMPAIGN_DESTINATION_COLLISION '+dest)
   else:
    pd.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ps,pd)
  staged=[x for x in SCRIPTS if git(repo,['ls-files','--error-unmatch',x],check=False).returncode!=0]
  state['scriptCommit']=commit(repo,staged,'Obsidianti: save v1.1.0 complete animation library campaign')
  for dst,src in SCRIPTS.items():
   if git_file_sha(repo,dst)!=h(packet/src):raise RuntimeError('COMMITTED_SCRIPT_READBACK_MISMATCH '+dst)
  state['scriptRepoCommitVerified']=git(repo,['rev-parse','HEAD']).stdout.strip()
  print('SOURCE_SCRIPTS_GIT_COMMITTED='+state['scriptRepoCommitVerified'],flush=True)
  ares,meta=find_ares(work);state['aresDonor']=meta
  lion=work/'lionheart-evaluated.json';ar=work/'ares-evaluated.json'
  state['samples']=[start_blender_sampler(packet,work,packet/'payload/LionheartLancer.blend',lion,'lionheart',repo),start_blender_sampler(packet,work,ares,ar,'ares',repo)]
  patch=repo/'campaigns/OBSIDIANTI_GLTF_LIBRARY_v1.1.0.py';report=work/'bake_report.json'
  command([sys.executable,str(patch),'--model',str(model),'--lionheart',str(lion),'--ares',str(ar),'--report',str(report)],timeout=160)
  baked=json.loads(report.read_text());state['bake']=baked
  names=glb_anim_names(model)
  if h(model)!=baked['newSha256'] or len(names)!=23:raise RuntimeError('RESULT_GLB_VALIDATION_FAILED')
  if names[:3]!=['Running','Walking','LionheartIdle_UNREVIEWED']:raise RuntimeError('ORIGINAL_CLIP_SEQUENCE_MUTATED')
  if len(list((repo/'assets/obsidianti').glob('*.glb')))!=1:raise RuntimeError('MULTIPLE_OBSIDIANTI_GLBS_NOT_ALLOWED')
  # Versioned code was already committed in the isolated repo BEFORE sampling.
  state['modelCommit']=commit(repo,[CANONICAL],'Obsidianti: update SAME canonical GLB with full Lionheart/Ares animation library')
  validate_clean_checkout(repo)
  head=git(repo,['rev-parse','HEAD']).stdout.strip()
  if git(repo,['rev-parse','HEAD:assets/repl/Repl.glb']).stdout.strip()!=orig_repl:raise RuntimeError('REPL_CANONICAL_MODEL_MUTATED')
  if lfs_oid(repo,CANONICAL)!=baked['newSha256']:raise RuntimeError('MODEL_COMMIT_LFS_POINTER_DIFFERS_FROM_FINAL_BYTES')
  # Standard non-forced push. Recover auth transient with existing gh credentials, never force.
  p=git(repo,['push','origin','HEAD:refs/heads/main'],timeout=210,check=False)
  if p.returncode:
   if '[rejected]' in p.stderr or 'non-fast-forward' in p.stderr:raise RuntimeError('REMOTE_MOVED_RETRY_AFTER_RECONCILE')
   if shutil.which('gh'):
    p=command(['git','-C',str(repo),'-c','credential.helper=!gh auth git-credential','push','origin','HEAD:refs/heads/main'],timeout=210,check=False)
   if p.returncode:raise RuntimeError('GIT_PUSH_FAILED '+p.stderr[-1200:])
  readback=git(repo,['ls-remote','origin','refs/heads/main']).stdout.split()[0]
  if readback!=head:raise RuntimeError('REMOTE_HEAD_NOT_EQUAL_PUSHED_HEAD')
  state['remoteHeadVerified']=readback;state['remoteModelLfsPointerOidVerified']=lfs_oid(repo,CANONICAL)
  state['remoteLfsObjectByteReadback']='NOT_INDEPENDENTLY_VERIFIED_BY_GITHUB_POINTER'
  state['ReplChanged']=False
  # Start read-only phone viewer on a genuinely free port. The previous v1.0.0
  # phone server may still own 8179; do not confuse a port collision with success.
  import socket, urllib.request
  for port in range(8179,8188):
   sock=socket.socket()
   try:
    sock.bind(('127.0.0.1',port))
   except OSError:
    continue
   finally:
    sock.close()
   log=open(work/('viewer-'+str(port)+'.log'),'ab',buffering=0)
   try:
    proc=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(repo)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    time.sleep(.45)
    url='http://127.0.0.1:'+str(port)+'/review/obsidianti-library-v1.1.0.html'
    if proc.poll() is None:
     try:
      with urllib.request.urlopen(url,timeout=3) as response:
       if response.status==200:
        state['viewerPid']=proc.pid;state['viewerUrl']=url;state['viewerStatus']='HTTP_200_NOT_VISUAL_ACCEPTANCE';break
     except Exception:pass
    if proc.poll() is None:proc.terminate()
   finally:log.close()
  if not state.get('viewerUrl'):state['viewerStatus']='NO_REACHABLE_FREE_LOCAL_PORT_8179_TO_8187'
  state['status']='REMOTE_GIT_COMMITTED_ANIMATION_CANDIDATES__HUMAN_VISUAL_PENDING'
  atomic_json(receipt,state)
  print('STATUS='+state['status']+'\nREMOTE_HEAD='+readback+'\nMODEL_SHA256='+baked['newSha256']+'\nCLIPS='+','.join(names)+'\nRECEIPT='+str(receipt),flush=True)
  if state.get('viewerUrl'):print('REVIEW_URL='+state['viewerUrl'],flush=True)
  return 0
 except Exception as e:
  state['status']='BLOCKED_NO_REMOTE_MODEL_SUCCESS';state['error']=str(e);atomic_json(receipt,state)
  print('STATUS=BLOCKED\nREASON='+str(e)+'\nRECEIPT='+str(receipt),flush=True)
  return 2

if __name__=='__main__':sys.exit(main())
