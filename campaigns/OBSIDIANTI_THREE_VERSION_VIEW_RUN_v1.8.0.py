#!/usr/bin/env python3
"""Termux Git-only, read-only model comparison for canonical, v1.5.6 and v1.7.0.

Does not modify canonical GLB. Requires actual verified v1.7.0 previous-run
artifacts, not a synthetic or regenerated replacement.
"""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,socket,subprocess,sys,time,uuid,zipfile,struct,traceback,urllib.request
V='OBSIDIANTI_THREE_VERSION_VIEW_v1.8.0'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
MODEL='assets/obsidianti/Obsidianti.glb'
CANON_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
V156_SHA='261f10786dd0eb0e80667173e4a893f6822356da628a5907efd6d0bbc2a74ff5'
HANDOFF_SHA='fc3ca580b82de074f6a2f040e8335baf1351b74a102df389bbaa5dfc85a68c3a'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
R_V170='OBSIDIANTI_MULTI_ACTION_NATIVE_IK_v1.7.0'
FILES={'campaigns/OBSIDIANTI_THREE_VERSION_VIEW_RUN_v1.8.0.py':'driver.py',
       'review/obsidianti-three-version-view-v1.8.0.html':'viewer.html',
       'docs/obsidianti/THREE_VERSION_VIEW_v1.8.0.md':'doc.md'}

def hashfile(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for x in iter(lambda:f.read(1<<20),b''):h.update(x)
 return h.hexdigest()
def command(argv,timeout=240,check=True,env=None):
 p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+repr(argv[:6])+' '+p.stderr[-1500:])
 return p
def git(repo,*args,**kw):return command(['git','-C',repo,*args],**kw)
def json_glb(path):
 with open(path,'rb') as f:
  h=f.read(20)
  if len(h)!=20 or h[:4]!=b'glTF':raise RuntimeError('INVALID_GLB '+str(path))
  n,t=struct.unpack_from('<II',h,12)
  if t!=0x4e4f534a:raise RuntimeError('MISSING_JSON_GLB_CHUNK')
  g=json.loads(f.read(n))
 return g

def recover_version170(downloads,home):
 """Read actual v1.7.0 completed Termux receipts and validate exact run and file."""
 matches=[]
 for receipt in downloads.glob(R_V170+'_*_RECEIPT.json'):
  try:
   r=json.loads(receipt.read_text());run=r.get('run')
   if r.get('campaign')!=R_V170 or r.get('status')!='UNAPPROVED_MULTIACTION_VISUAL_REVIEW_AVAILABLE' or not run:continue
   base=home/'.local/state'/R_V170/run/'review'
   manifest=json.loads((base/'manifest.json').read_text())
   if manifest.get('run')!=run or manifest.get('campaign')!=R_V170:continue
   target=base/'Obsidianti.glb'
   donor=base/manifest['source']['file']
   h=hashfile(target);sourcehash=hashfile(donor)
   if h!=manifest['obsidiantiSha256'] or sourcehash!=manifest['source']['sha256']:continue
   if r.get('merged',{}).get('outputSHA256')!=h:continue
   if r.get('canonicalModelChanged') is not False:continue
   matches.append((receipt,r,manifest,target,donor))
  except (KeyError,OSError,ValueError,TypeError,json.JSONDecodeError):continue
 if not matches:raise RuntimeError('V170_VERIFIED_RUN_NOT_FOUND: Need existing completed v1.7.0 viewer artifacts and receipt on this phone; no substitution')
 # Use newest successful receipt by name. A different stored candidate is never guessed.
 matches.sort(key=lambda x:x[0].name)
 return matches[-1]

def recover_v156(downloads,work):
 options=[]
 for p in downloads.glob('OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.6*_HANDOFF.zip'):
  if hashfile(p)==HANDOFF_SHA:options.append(p)
 if len(options)!=1:raise RuntimeError('VERIFIED_V156_HANDOFF_MISSING_OR_AMBIGUOUS')
 with zipfile.ZipFile(options[0]) as z:raw=z.read('visual/Candidate_UNAPPROVED.glb')
 if hashlib.sha256(raw).hexdigest()!=V156_SHA:raise RuntimeError('V156_CANDIDATE_HASH_MISMATCH')
 dst=work/'Obsidianti_v156.glb';dst.write_bytes(raw)
 return dst,options[0]

def measure(models):
 """Read all 23 GLB animation structures before modifying anything."""
 js={n:json_glb(p) for n,p in models.items()}
 clips={n:[a.get('name') for a in g['animations']] for n,g in js.items()}
 names=clips['canonical']
 if len(names)!=23 or len(set(names))!=23:raise RuntimeError('CANONICAL_CLIP_LIBRARY_UNEXPECTED')
 for name in models:
  if clips[name]!=names:raise RuntimeError('THREE_VERSION_CLIP_NAMES_OR_ORDER_DIFFER '+name)
 for key in ('nodes','skins','meshes','scenes','materials','textures','images'):
  if any(js[n].get(key)!=js['canonical'].get(key) for n in models if n!='canonical'):
   raise RuntimeError('RIG_STRUCTURE_MISMATCH '+key)
 differences={n:[z for z in names if js[n]['animations'][names.index(z)]!=js['canonical']['animations'][names.index(z)]] for n in models if n!='canonical'}
 if differences['v156']!=['Lionheart_Heavy1']:raise RuntimeError('V156_IS_NOT_SINGLE_ACTION_REPAIR '+repr(differences['v156']))
 allowed={'Lionheart_'+x for x in ('Heavy1','Cast','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')}
 if not set(differences['v170']).issubset(allowed):raise RuntimeError('V170_PROTECTED_CLIP_MUTATION '+repr(differences['v170']))
 if 'Lionheart_Heavy1' not in differences['v170']:raise RuntimeError('V170_MISSING_HEAVY1_IMPROVEMENT')
 if len(differences['v170'])<2:raise RuntimeError('V170_NO_NEW_ACTION_DIFFERENCE')
 if js['v170']['animations'][names.index('Lionheart_Heavy1')]!=js['v156']['animations'][names.index('Lionheart_Heavy1')]:raise RuntimeError('V170_DOES_NOT_PRESERVE_HEAVY1')
 # All version-level animation differences must be exactly from their respective intended clips.
 sizes={n:{'bytes':pathlib.Path(p).stat().st_size,'sha256':hashfile(p)} for n,p in models.items()}
 return {'measuredModels':sizes,'animationCount':len(names),'animationNames':names,'animationsDifferentFromCanonical':differences,
         'rigTopologyIdentical':True,'v156Heavy1PreservedInV170':True,
         'measurementNote':'Clip structure comparisons; source-motion visual quality remains owner review'}

def serve(public,run,receipt):
 code="import http.server,sys\nclass H(http.server.SimpleHTTPRequestHandler):\n def end_headers(self):\n  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')\n  self.send_header('Pragma','no-cache')\n  self.send_header('X-Comparison-Run',sys.argv[3])\n  super().end_headers()\nhttp.server.ThreadingHTTPServer(('127.0.0.1',int(sys.argv[1])),lambda *args,**kw:H(*args,directory=sys.argv[2],**kw)).serve_forever()\n"
 for _ in range(10):
  sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
  with open(public/'server.log','ab',buffering=0) as log:
   proc=subprocess.Popen([sys.executable,'-B','-c',code,str(port),str(public),run],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True)
  for _ in range(30):
   if proc.poll() is not None:break
   try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/manifest.json',timeout=1) as resp:
     data=json.loads(resp.read());ok=resp.status==200 and data.get('run')==run and resp.headers.get('X-Comparison-Run')==run and 'no-store' in resp.headers.get('Cache-Control','')
     if ok:return {'url':f'http://127.0.0.1:{port}/viewer.html?run={run}','port':port,'pid':proc.pid,'run':run,'cacheHeader':resp.headers['Cache-Control']}
   except Exception:time.sleep(.2)
  proc.terminate();proc.wait(timeout=4)
 raise RuntimeError('NO_VERIFIED_FRESH_VIEWER_SERVICE')

def main(packet,launcher_sha):
 home=pathlib.Path.home();downloads=home/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('TERMUX_DOWNLOADS_REQUIRED')
 run=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:7]
 state=home/'.local/state'/V/run;state.mkdir(parents=True,exist_ok=False)
 work=state/'work';work.mkdir();repo=state/'repo';public=state/'review';public.mkdir()
 receipt=downloads/(V+'_'+run+'_RECEIPT.json')
 result={'campaign':V,'run':run,'authority':'TERMUX_GIT_ONLY','stage':'BOOT','status':'STARTED','launcherSHA256':launcher_sha,'canonicalChanged':False,
         'agentsReadExpectedBlob':AGENTS_BLOB,'authorReadEtq':'2026-11-05 Home Center','ownerVisualAcceptance':'PENDING'}
 def save():receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 save()
 try:
  result['stage']='MEASURE_EXISTING_THREE_MODELS';save()
  v156,handoff=recover_v156(downloads,work)
  old,oldreceipt,oldmanifest,v170,donor=recover_version170(downloads,home)
  if hashfile(v156)!=V156_SHA:raise RuntimeError('V156_CHANGED')
  result['v170RecoveredReceipt']=str(oldreceipt);result['v170RecoveredRun']=oldmanifest['run'];result['v156Handoff']=str(handoff)
  # Read first two identities and source inventory before repository publication.
  preread={'v156':{'sha256':hashfile(v156),'bytes':v156.stat().st_size},'v170':{'sha256':hashfile(v170),'bytes':v170.stat().st_size},
           'lionheart':{'sha256':hashfile(donor),'bytes':donor.stat().st_size,'clipNames':[a['name'] for a in json_glb(donor)['animations']]}}
  result['preread']=preread;save()
  result['stage']='ISOLATED_TERMUX_GIT_CHECKOUT';save()
  env=os.environ.copy();env.update(GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
  command(['git','clone','--depth=25','--single-branch','--branch','main','--config','filter.lfs.smudge=','--config','filter.lfs.required=false',REMOTE,repo],timeout=600,env=env)
  head=git(repo,'rev-parse','HEAD').stdout.strip();result['inputRemoteHead']=head
  blob=git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()
  if blob!=AGENTS_BLOB:raise RuntimeError('AGENTS_REVISION_MISMATCH: '+blob)
  read=(repo/'AGENTS.md').read_text()
  if 'Campaign Etiquette' not in read or 'Termux Git' not in read:raise RuntimeError('RULES_NOT_VALID')
  result['rulesRead']='AGENTS_HEAD_BLOB_VERIFIED_AND_LIVE_ETIQUETTE_READ_BY_AUTHOR';save()
  # Get the actual canonical model and independently confirm known SHA.
  result['stage']='VERIFY_CANONICAL_SOURCE_BINARY';save()
  if command(['git','lfs','version'],check=False).returncode:raise RuntimeError('TERMUX_GIT_LFS_REQUIRED')
  command(['git','-C',repo,'lfs','pull','--include='+MODEL,'--exclude='],timeout=1200,env={**env,'GIT_LFS_SKIP_SMUDGE':'0'})
  canonical=repo/MODEL
  if hashfile(canonical)!=CANON_SHA:raise RuntimeError('CANONICAL_GLB_HASH_UNEXPECTED '+hashfile(canonical))
  measures=measure({'canonical':canonical,'v156':v156,'v170':v170});result['measurements']=measures;save()
  (work/'measurements.json').write_text(json.dumps(measures,indent=2,sort_keys=True)+'\n')
  result['stage']='PREFLIGHT_NEW_SOURCE_DESTINATIONS';save()
  for dest in FILES:
   if (repo/dest).exists() or git(repo,'ls-tree','HEAD','--',dest).stdout.strip():raise RuntimeError('VERSIONED_SOURCE_COLLISION '+dest)
  for dest,name in FILES.items():
   dst=repo/dest;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(packet/name,dst)
  result['stage']='PUBLISH_SCRIPT_SOURCE_TERMUX_GIT';save()
  git(repo,'add','--',*FILES)
  if set(git(repo,'diff','--cached','--name-only').stdout.splitlines())!=set(FILES):raise RuntimeError('STAGED_SCOPE_WRONG')
  if not git(repo,'config','--get','user.name',check=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Campaign')
  if not git(repo,'config','--get','user.email',check=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')
  git(repo,'commit','-m','Obsidianti: verifiable three-version read-only viewer v1.8.0')
  commit=git(repo,'rev-parse','HEAD').stdout.strip();result['sourceCommit']=commit;save()
  command(['git','-C',repo,'push','origin','HEAD:refs/heads/main'],timeout=300,env=env)
  remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]
  if remote!=commit:raise RuntimeError('REMOTE_COMMIT_READBACK_FAILED')
  result['sourceRemoteReadback']=remote;save()
  result['stage']='STAGE_THREE_VERIFIED_VERSIONS';save()
  versions={'canonical':(canonical,'Obsidianti_Canonical.glb'), 'v156':(v156,'Obsidianti_v156.glb'), 'v170':(v170,'Obsidianti_v170.glb')}
  declared={}
  for name,(src,filename) in versions.items():
   dst=public/filename;shutil.copyfile(src,dst)
   if hashfile(dst)!=hashfile(src):raise RuntimeError('PUBLIC_BINARY_COPY_MISMATCH '+name)
   declared[name]={'file':filename,'sha256':hashfile(dst),'bytes':dst.stat().st_size}
  lionfile='Lionheart_ALL_SOURCE.glb';shutil.copyfile(donor,public/lionfile)
  if hashfile(public/lionfile)!=hashfile(donor):raise RuntimeError('LIONHEART_PUBLIC_HASH_MISMATCH')
  shutil.copyfile(repo/'review/obsidianti-three-version-view-v1.8.0.html',public/'viewer.html')
  manifest={'run':run,'sourceCommit':commit,'versions':declared,'lionheart':{'file':lionfile,'sha256':hashfile(donor),'bytes':donor.stat().st_size},'measurements':measures,
            'sourceOriginalV170Run':oldmanifest['run'],'modelPublication':'NONE','ownerVisualAcceptance':'PENDING'}
  (public/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
  result['stage']='START_VERIFIED_PHONE_VIEWER';save()
  result['viewer']=serve(public,run,result);result['status']='THREE_VERSION_VIEWER_READY_OWNER_REVIEW_PENDING';result['stage']='COMPLETE';save()
  print('VIEWER_URL='+result['viewer']['url'],flush=True)
  print('LIONHEART_SHA256='+hashfile(donor),flush=True)
  for key,rec in declared.items():print('OBSIDIANTI_'+key.upper()+'_SHA256='+rec['sha256'],flush=True)
  print('CANONICAL_MODEL_CHANGED=NO\nOWNER_VISUAL_ACCEPTANCE=PENDING',flush=True)
 except Exception as e:
  result['status']='BLOCKED';result['error']=type(e).__name__+': '+str(e);result['stage']='BLOCKED_'+result['stage'];save()
  print('BLOCKED='+result['error'],flush=True);traceback.print_exc();raise
 finally:
  save();bundle=downloads/(V+'_'+run+'_HANDOFF.zip')
  with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED) as z:
   z.write(receipt,'receipt.json')
   if (work/'measurements.json').is_file():z.write(work/'measurements.json','measurements.json')
   if (public/'manifest.json').is_file():z.write(public/'manifest.json','visual/manifest.json')
  print('RECEIPT='+str(receipt)+'\nHANDOFF='+str(bundle)+'\nHANDOFF_SHA256='+hashfile(bundle),flush=True)
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('USAGE: driver.py PACKET_FOLDER LAUNCHER_SHA256')
 main(pathlib.Path(sys.argv[1]),sys.argv[2])
