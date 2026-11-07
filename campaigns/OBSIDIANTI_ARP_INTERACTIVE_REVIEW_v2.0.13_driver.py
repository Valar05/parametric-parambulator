#!/usr/bin/env python3
"""One-shot Termux Git-only v2.0.13: reuse existing v1.4.4 interactive viewer
with exact saved Auto-Rig Pro Heavy1 and AxeKick actions, no new render/retarget.
"""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,struct,subprocess,sys,time,urllib.request,uuid

V='OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE='ebd49a4eafd0b518614033ae7fc9b823e6642f85'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
RUN='20261107T015728Z-dfe90dc2'
PREV='OBSIDIANTI_ARP_BLENDER5_ISOLATED_v2.0.12'
V12E='diagnostics/obsidianti/arp-blender5-isolated-v2.0.12/runs/'+RUN+'/EVIDENCE.json'
DEST='diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/'
OLDVIEW='campaigns/OBSIDIANTI_MWNI_VIEWER_v1.4.4_'
LOCKED=('assets/obsidianti/Obsidianti.glb','assets/repl/Repl.glb')
PD='5.10.3'
PD_SHA='88f1a45f13dc2ae9bfc805693ca0908f16444dd696006a90a12a0faabdb8f1c1'
PD_HOME=pathlib.Path.home()/'.local/share/obsidianti-arp-purchased/proot-distro-5.10.3'
CLIPS=('Heavy1','AxeKick')
SOURCE={'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER','campaigns/'+V+'_driver.py':'driver.py',
 'campaigns/'+V+'_export.py':'export.py','campaigns/'+V+'_viewer.html':'viewer.html',
 'campaigns/'+V+'_server.py':'server.py','campaigns/'+V+'.contract.json':'contract.json',
 'tests/'+V+'_TEST.py':'test_driver.py'}

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()

def call(args,timeout=220,check=True,env=None):
 argv=list(map(str,args));p=subprocess.run(argv,capture_output=True,text=True,errors='replace',timeout=timeout,env=env,stdin=subprocess.DEVNULL)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED rc='+str(p.returncode)+' '+repr(argv[:4])+' '+p.stderr[-400:]+' '+p.stdout[-200:])
 return p

def git(root,*args,timeout=280,check=True):return call(['git','-C',root,*args],timeout=timeout,check=check)
def g(root,*args):return git(root,*args).stdout.strip()

def copy_no_clobber(src,dst):
 src=pathlib.Path(src);dst=pathlib.Path(dst)
 if not src.is_file() or src.is_symlink():raise RuntimeError('COPY_SOURCE_NOT_REGULAR_'+str(src))
 if dst.exists():
  if not dst.is_file() or dst.is_symlink() or sha(dst)!=sha(src):raise RuntimeError('COPY_DESTINATION_COLLISION_'+str(dst))
  return
 dst.parent.mkdir(parents=True,exist_ok=True)
 tmp=dst.with_name('.'+dst.name+'.tmp-'+uuid.uuid4().hex[:8]);shutil.copyfile(src,tmp)
 try:
  if sha(tmp)!=sha(src):raise RuntimeError('COPY_SHA_MISMATCH')
  os.replace(tmp,dst)
 finally:
  if tmp.exists():tmp.unlink()

def save(path,obj):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name('.'+path.name+'.tmp-'+uuid.uuid4().hex[:8]);tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');os.replace(tmp,path)

def checkout(root):
 repo=root/'repo';env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
 call(['git','clone','--quiet','--depth=1','--single-branch','--branch=main',REMOTE,repo],timeout=650,env=env)
 if g(repo,'remote','get-url','origin').removesuffix('.git')!=REMOTE.removesuffix('.git'):raise RuntimeError('WRONG_REMOTE')
 head=g(repo,'rev-parse','HEAD')
 if head!=BASE and git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False).returncode:
  git(repo,'fetch','--no-tags','--depth=180','origin',BASE,timeout=300)
  if git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False).returncode:raise RuntimeError('HEAD_NOT_DESCENDED_FROM_ACTUAL_V212_EVIDENCE')
 if g(repo,'rev-parse','HEAD:AGENTS.md')!=AGENTS:raise RuntimeError('LIVE_AGENTS_BLOB_CHANGED')
 if 'oid sha256:'+CANON not in git(repo,'show','HEAD:'+LOCKED[0]).stdout:raise RuntimeError('CANONICAL_LFS_POINTER_CHANGED')
 if g(repo,'status','--porcelain'):raise RuntimeError('CLEAN_ISOLATED_CHECKOUT_REQUIRED')
 evidence=json.loads((repo/V12E).read_text())
 if evidence.get('runId')!=RUN or evidence.get('canonicalModelSHA256')!=CANON:raise RuntimeError('V212_REAL_TERUMX_RUN_NOT_PINNED')
 for clip in CLIPS:
  trial=evidence['trials'][clip]
  if trial.get('stage')!='SAVED_BLEND' or trial.get('targetAction')!=clip+'_remap' or not trial.get('blendSHA256'):
   raise RuntimeError('NO_VERIFIED_SAVED_ARP_ACTION_'+clip)
  if trial.get('blenderExit')!=0 or trial.get('motionGate') is not True:raise RuntimeError('ARP_MOTION_EVIDENCE_INCOMPLETE_'+clip)
 return repo,head,evidence

def patch_once(data,old,new):
 if data.count(old)!=1:raise RuntimeError('VIEWER_TEMPLATE_CONTRACT_CHANGED_'+old[:65]+' count='+str(data.count(old)))
 return data.replace(old,new,1)

def create_viewer(repo,packet):
 html=(repo/(OLDVIEW+'viewer.html')).read_text()
 server=(repo/(OLDVIEW+'server.py')).read_text()
 patches=[
 ('<title>Obsidianti | Mwni Retarget Review</title>','<title>Obsidianti | Auto-Rig Pro Interactive Review</title>'),
 ('<h1>Obsidianti | Mwni foot-IK retarget review</h1>','<h1>Obsidianti | ARP live 3D review</h1>'),
 ('<option value="Light2">Light2</option>','<option value="AxeKick">AxeKick</option>'),
 ('<option value="candidate">Mwni IK candidate</option>','<option value="candidate">Purchased ARP retarget</option>'),
 ('<option value="original">Original (if available)</option>','<option value="original" disabled>Original not available for these actions</option>'),
 ('Select Mwni IK candidate.','Select purchased ARP retarget.'),
 ('Mwni candidate UNAPPROVED','ARP preview | Heavy1 REVIEW | AxeKick OWNER ACCEPTED'),
 ('These are UNAPPROVED experimental exports, not the canonical model. Floor guide is visual, not a physical contact test.',
  'Review exported ARP Actions in the existing interactive viewer. AxeKick accepted; Heavy1 hip/foot IK under review. Floor guide is visual, not a contact solver.'),
 ]
 for a,b in patches:html=patch_once(html,a,b)
 # Distinct source identity while preserving exact proven v1.4.4 viewer behavior.
 html=patch_once(html,'<label for="version">Rig</label>','<label for="version">Source</label>')
 server=patch_once(server,"server_version='ObsidiantiMwniViewer/1.4.4'","server_version='ObsidiantiARPViewer/2.0.13'")
 (packet/'viewer.html').write_text(html)
 (packet/'server.py').write_text(server)
 return {'viewerSHA256':sha(packet/'viewer.html'),'serverSHA256':sha(packet/'server.py')}

def private_pd():
 folder=PD_HOME/'python';mark=PD_HOME/'WHEEL_SHA256.json'
 if not mark.is_file() or mark.is_symlink():raise RuntimeError('EXISTING_PRIVATE_PROOT_CLI_MISSING')
 info=json.loads(mark.read_text())
 if info.get('packageVersion')!=PD or info.get('wheelSha256')!=PD_SHA:raise RuntimeError('PROOT_CLI_IDENTITY_CHANGED')
 members=info.get('packageFileHashes',{})
 if len(members)<12:raise RuntimeError('PROOT_CLI_FILE_SET_INCOMPLETE')
 for name,checksum in members.items():
  item=folder.joinpath(*pathlib.PurePosixPath(name).parts)
  if not item.is_file() or item.is_symlink() or sha(item)!=checksum:raise RuntimeError('PROOT_CLI_MEMBER_CHANGED_'+name)
 expr='import sys;sys.path.insert(0,'+repr(str(folder))+');from proot_distro.cli import main;main()'
 return [sys.executable,'-c',expr]

def ensure_container(pd):
 ident=call(pd+['login','obs-arp-blender50','--','/bin/cat','/etc/os-release'],timeout=110)
 if 'Ubuntu' not in ident.stdout or '26.04' not in ident.stdout:raise RuntimeError('NOT_PINNED_UBUNTU26_CONTAINER')
 version=call(pd+['login','obs-arp-blender50','--','/usr/bin/blender','--version'],timeout=110)
 if not version.stdout.startswith('Blender 5.0.'):raise RuntimeError('NOT_BLENDER_5_0')
 arch=call(pd+['login','obs-arp-blender50','--','/usr/bin/dpkg','--print-architecture'],timeout=110)
 if arch.stdout.strip()!='arm64':raise RuntimeError('NOT_ARM64_CONTAINER')
 return version.stdout.splitlines()[0]

def locate_saved_blends(repo,evidence):
 rel={clip:DEST.replace('/runs/','/no/unused') for clip in []}
 old=pathlib.Path.home()/'.local/state'/PREV/RUN/'out'
 local={}
 for clip in CLIPS:
  expected=evidence['trials'][clip]['blendSHA256']
  candidate=old/clip/'trial'/('ARP_'+clip+'_UNAPPROVED.blend')
  if candidate.is_file() and not candidate.is_symlink() and sha(candidate)==expected:
   local[clip]=candidate;continue
  relpath='diagnostics/obsidianti/arp-blender5-isolated-v2.0.12/runs/'+RUN+'/'+clip+'/ARP_'+clip+'_UNAPPROVED.blend'
  ptr=git(repo,'show','HEAD:'+relpath).stdout
  if 'oid sha256:'+expected not in ptr:raise RuntimeError('V212_GIT_BLEND_LFS_POINTER_MISMATCH_'+clip)
  git(repo,'lfs','install','--local',timeout=80)
  git(repo,'lfs','pull','--include='+relpath,'--exclude=','origin',timeout=1500)
  if not (repo/relpath).is_file() or sha(repo/relpath)!=expected:raise RuntimeError('BLENDER_DERIVATIVE_LFS_BYTES_UNAVAILABLE_'+clip)
  local[clip]=repo/relpath
 return local

def validate_glb(path,clip):
 path=pathlib.Path(path)
 if not path.is_file() or path.stat().st_size<200000:raise RuntimeError('GLB_NOT_PRODUCED_'+clip)
 with open(path,'rb') as f:
  header=f.read(12)
  if len(header)!=12 or header[:4]!=b'glTF':raise RuntimeError('GLB_MAGIC_INVALID_'+clip)
  magic,version,length=struct.unpack('<4sII',header)
  if version!=2 or length!=path.stat().st_size:raise RuntimeError('GLB_HEADER_INVALID_'+clip)
  size,typ=struct.unpack('<I4s',f.read(8))
  if typ!=b'JSON' or size<=0 or size>12*1024*1024:raise RuntimeError('GLB_JSON_BLOCK_INVALID')
  data=json.loads(f.read(size))
 animations=data.get('animations') or []
 if len(animations)!=1:raise RuntimeError('EXACT_ONE_REVIEW_ANIMATION_REQUIRED_'+clip+'_FOUND_'+str(len(animations)))
 name=animations[0].get('name','')
 if clip.lower() not in name.lower() and name not in ('Animation','Action'):
  raise RuntimeError('PREVIEW_CLIP_NAME_MISMATCH_'+clip+'_'+name)
 channels=animations[0].get('channels',[])
 if len(channels)<8:raise RuntimeError('UNEXPECTED_TOO_FEW_GLTF_ANIMATION_CHANNELS_'+clip)
 if not data.get('meshes') or not data.get('skins'):raise RuntimeError('PREVIEW_MODEL_MESH_OR_SKIN_MISSING_'+clip)
 return {'sha256':sha(path),'bytes':path.stat().st_size,'animations':[name], 'channels':len(channels), 'meshes':len(data['meshes']),'skins':len(data['skins']),
         'url':'/models/candidate'+clip+'.glb','role':'Purchased ARP '+clip+' unmodified saved action'}

def export_one(pd,root,src,clip,expected):
 out=root/'exports';out.mkdir(exist_ok=True)
 final=out/('ARP_'+clip+'_REVIEW.glb');rec=out/('EXPORT_'+clip+'.json')
 # Re-execution requires SHA and actual receipt consistency; never use a stale GLB.
 cmd=pd+['login','obs-arp-blender50',
   '--bind',str(src.parent.resolve())+':/mnt/arp-source',
   '--bind',str(root.resolve())+':/mnt/arp-review','--',
   'blender','--background','--factory-startup','--disable-autoexec',
   '--python','/mnt/arp-review/export.py','--',
   '--source','/mnt/arp-source/'+src.name,'--sha',expected,'--action',clip+'_remap',
   '--output','/mnt/arp-review/exports/'+final.name,'--receipt','/mnt/arp-review/exports/'+rec.name]
 p=call(cmd,timeout=1800,check=False)
 (out/('BLENDER_'+clip+'.log')).write_text(p.stdout+'\n'+p.stderr)
 note=json.loads(rec.read_text()) if rec.is_file() else {}
 if p.returncode or note.get('status')!='BLENDER5_SAVED_ARP_ACTION_EXPORTED_GLB':
  raise RuntimeError('BLENDER5_PREVIEW_EXPORT_FAILED_'+clip+'_rc='+str(p.returncode)+'_'+str(note.get('error',p.stderr[-500:]))[:400])
 info=validate_glb(final,clip)
 if info['sha256']!=note.get('glbSHA256') or info['bytes']!=note.get('glbBytes'):
  raise RuntimeError('GLB_EXPORT_RECEIPT_AND_REAL_BYTES_DISAGREE_'+clip)
 return final,info

def publish(repo,phase):
 commit=g(repo,'rev-parse','HEAD')
 for i in range(3):
  proc=git(repo,'push','origin','HEAD:refs/heads/main',timeout=550,check=False)
  if not proc.returncode:break
  if i==2:raise RuntimeError('GIT_PUSH_FAILED_'+phase+'_'+proc.stderr[-700:])
  time.sleep(i+1)
 remote=git(repo,'ls-remote','origin','refs/heads/main',timeout=110).stdout.split()
 if not remote or remote[0]!=commit:raise RuntimeError('GIT_REMOTE_READBACK_FAILED_'+phase)
 git(repo,'fetch','--quiet','origin','main',timeout=260)
 if g(repo,'rev-parse','refs/remotes/origin/main')!=commit:raise RuntimeError('GIT_REMOTE_FETCH_NOT_MATCHED_'+phase)
 return commit

def commit_files(repo,files,phase):
 if any((repo/p).exists() for p in files):raise RuntimeError('VERSIONED_GIT_DESTINATION_COLLISION_'+phase)
 for p,f in files.items():copy_no_clobber(f,repo/p)
 git(repo,'add','--',*sorted(files))
 if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(files):raise RuntimeError('GIT_STAGING_SCOPE_CHANGED_'+phase)
 if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Termux ARP Preview')
 if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','termux-arp-preview@users.noreply.github.com')
 git(repo,'commit','-m','Obsidianti: ARP 3D interactive preview '+phase)
 c=publish(repo,phase)
 for p,src in files.items():
  if git(repo,'show','refs/remotes/origin/main:'+p).stdout!=src.read_text():raise RuntimeError('GIT_TEXT_READBACK_FAILED_'+p)
 return c

def start_server(root,repo,manifest):
 config=root/'viewer_manifest.json';ready=root/'viewer_ready.json';log=root/'VIEWER_SERVER.log'
 save(config,manifest)
 with open(log,'w') as f:
  proc=subprocess.Popen([sys.executable,str(repo/('campaigns/'+V+'_server.py')),'--config',str(config),'--ready',str(ready),'--port-base','9200'],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
 for _ in range(100):
  if proc.poll() is not None:raise RuntimeError('VIEWER_SERVER_DIED_'+log.read_text()[-400:])
  if ready.is_file():break
  time.sleep(.12)
 if not ready.is_file():raise RuntimeError('VIEWER_SERVER_NOT_READY')
 ticket=json.loads(ready.read_text());base='http://127.0.0.1:'+str(ticket['port'])
 def fetch(route,method='GET'):
  with urllib.request.urlopen(urllib.request.Request(base+route,method=method,headers={'Cache-Control':'no-cache'}),timeout=25) as r:
   if r.headers.get('X-Obsidianti-Run')!=manifest['runId'] or r.headers.get('X-Obsidianti-Build')!=manifest['buildToken']:raise RuntimeError('STALE_SERVER_IDENTITY')
   return r.read(),r.headers
 data,headers=fetch('/index.html?run='+manifest['runId']+'&build='+manifest['buildToken'])
 if hashlib.sha256(data).hexdigest()!=sha(repo/('campaigns/'+V+'_viewer.html')):raise RuntimeError('VIEWER_HTML_SERVER_MISMATCH')
 if 'no-store' not in headers.get('Cache-Control',''):raise RuntimeError('CACHE_POLICY_MISSING')
 blob,_=fetch('/manifest.json');m=json.loads(blob)
 if m.get('buildToken')!=manifest['buildToken'] or set(m.get('models',{}))!=set(manifest['models']):raise RuntimeError('VIEWER_MANIFEST_STALE')
 for key,info in manifest['models'].items():
  _data,h=fetch(info['url'],method='HEAD')
  if h.get('X-Model-SHA256')!=info['sha256'] or int(h.get('Content-Length','0'))!=info['bytes']:raise RuntimeError('VIEWER_MODEL_HTTP_IDENTITY_WRONG_'+key)
 return ticket

def open_browser(url):
 for cmd in (['termux-open-url',url],['am','start','-a','android.intent.action.VIEW','-d',url]):
  if not shutil.which(cmd[0]):continue
  try:
   p=call(cmd,timeout=12,check=False)
   if p.returncode==0:return True
  except Exception:pass
 return False

def main(packet,launcher,expected_sha):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 if not launcher.is_file() or sha(launcher)!=expected_sha:raise RuntimeError('LAUNCHER_SHA_MISMATCH')
 mf=json.loads((packet/'manifest.json').read_text());want={'driver.py','export.py','test_driver.py','contract.json'}
 if set(mf)!=want or any(sha(packet/f)!=dig for f,dig in mf.items()):raise RuntimeError('PAYLOAD_TAMPERED')
 contract=json.loads((packet/'contract.json').read_text())
 if contract.get('sourceMutablePaths')!=sorted(SOURCE) or contract.get('authority')!='TERMUX_GIT_ONLY' or contract.get('pinnedGitBase')!=BASE:raise RuntimeError('CONTRACT_SOURCE_OR_LANE_CHANGED')
 call(['python3','-m','py_compile',*[str(packet/x) for x in ('driver.py','export.py','test_driver.py')]])
 call(['python3',packet/'test_driver.py'],timeout=100)
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
 receipt=root/'RECEIPT.json';state={'schema':V,'runId':runid,'status':'BOOT','authority':'TERMUX_GIT_ONLY',
   'launcherSHA256':expected_sha,'canonicalSHA256':CANON,'rulesBlob':AGENTS,'sourceV212RunId':RUN,
   'acceptedAxeKickAction':'AxeKick_remap','heavy1Status':'HIP_AND_FOOT_IK_VISUAL_REVIEW',
   'retargetExecuted':False,'rendersExecuted':False,'canonicalModified':False,'ownerVisualReview':'HEAVY1_PENDING'}
 def checkpoint():save(receipt,state)
 checkpoint()
 try:
  repo,head,evidence=checkout(root);state['inputGitHead']=head
  protected={p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED};state['protectedBefore']=protected;checkpoint()
  patches=create_viewer(repo,packet);state['viewerSourceHashes']=patches
  srcfiles={name:launcher if source=='LAUNCHER' else packet/source for name,source in SOURCE.items()}
  sourcecommit=commit_files(repo,srcfiles,'SOURCE');state['sourceGitCommit']=sourcecommit;checkpoint()
  copy_no_clobber(packet/'export.py',root/'export.py')
  pd=private_pd();state['blenderRuntime']=ensure_container(pd);checkpoint()
  originals=locate_saved_blends(repo,evidence);state['priorSavedBlendSHA']={k:sha(v) for k,v in originals.items()};checkpoint()
  exports={};models={}
  (root/'exports').mkdir()
  for clip in CLIPS:
   path,info=export_one(pd,root,originals[clip],clip,evidence['trials'][clip]['blendSHA256'])
   download=pathlib.Path.home()/'storage/downloads'/(V+'_'+runid+'_'+path.name)
   copy_no_clobber(path,download)
   if sha(download)!=info['sha256']:raise RuntimeError('ANDROID_DOWNLOADS_OUTPUT_CORRUPTED')
   models['candidate'+clip]=info;exports['candidate'+clip]=download
   state['exportedModels']={k:{'sha256':v['sha256'],'animation':v['animations'][0],'channels':v['channels']} for k,v in models.items()};checkpoint()
   print('DOWNLOAD_'+clip.upper()+'_GLB='+str(download)+' SHA256='+info['sha256'],flush=True)
  token=hashlib.sha256((runid+sourcecommit+expected_sha+''.join(sorted(x['sha256'] for x in models.values()))).encode()).hexdigest()[:24]
  manifest={'schema':V,'runId':runid,'buildToken':token,'launcherSHA256':expected_sha,'sourceCommit':sourcecommit,
    'htmlPath':str(repo/('campaigns/'+V+'_viewer.html')),
    'modelPaths':{k:str(v) for k,v in exports.items()},'models':models,
    'canonicalModelSHA256':CANON,'mode':'EXACT_SAVED_ARP_ACTIONS_INTERACTIVE_NO_RENDERS'}
  ticket=start_server(root,repo,manifest)
  state['viewerURL']=ticket['url'];state['serverPID']=ticket['pid'];state['serverPort']=ticket['port']
  state['status']='HTTP_3D_VIEWER_VERIFIED__BROWSER_OWNER_REVIEW_PENDING';checkpoint()
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(open_browser(ticket['url'])).upper(),flush=True)
  # Persist exact exported review GLBs to remote Git LFS; no canonical overwrite.
  sub=DEST+runid+'/';rootout=root/'evidence';rootout.mkdir(exist_ok=True)
  summary={'schema':V,'runId':runid,'gitInputHead':head,'gitSourceCommit':sourcecommit,
   'canonicalModelSHA256':CANON,'canonicalModified':False,'rulesBlob':AGENTS,'etiquetteRead':'LIVE_2026_11_06',
   'sourceV212RunId':RUN,'sourceBlends':state['priorSavedBlendSHA'],
   'models':models,'ownerAccepted':{'AxeKick':'ACCEPTED_RENDER_v212','Heavy1':'UNDER_REVIEW_HIP_FOOT_IK'},
   'rendersExecuted':False,'retargetExecuted':False,'viewerURL':ticket['url'],
   'viewerHTTPVerified':True,'viewerBrowserRendered':'UNVERIFIED','vendorSourcePublished':False,
   'protectedBefore':protected,'protectedAfter':{p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}}
  if summary['protectedAfter']!=protected:raise RuntimeError('CANONICAL_ASSET_GIT_POINTER_CHANGED')
  save(rootout/'EVIDENCE.json',summary)
  (rootout/'REPORT.md').write_text('# Obsidianti purchased ARP interactive 3D viewer\n\n'
   +'Live phone URL: `'+ticket['url']+'`\n\nOriginal v1.4.4 interactive viewer controls preserved. '
   +'Blender 5 exported only saved ARP actions to separate review GLBs, without retarget or renders.\n\n'
   +'- AxeKick: owner accepted from v2.0.12 visuals; action unchanged.\n'
   +'- Heavy1: hips and foot IK require owner visual review; no automatic changes.\n'
   +'- Canonical model: SHA-locked and unchanged.\n'
   +'- Browser rendering not claimed by HTTP readback.\n')
  files={sub+'REPORT.md':rootout/'REPORT.md',sub+'EVIDENCE.json':rootout/'EVIDENCE.json'}
  for clip in CLIPS:files[sub+clip+'/ARP_'+clip+'_REVIEW.glb']=exports['candidate'+clip]
  if any((repo/p).exists() for p in files):raise RuntimeError('EVIDENCE_PATH_COLLISION')
  for p,src in files.items():copy_no_clobber(src,repo/p)
  git(repo,'lfs','install','--local',timeout=70)
  git(repo,'add','--',*sorted(files))
  if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(files):raise RuntimeError('EVIDENCE_STAGING_SCOPE_CHANGED')
  git(repo,'commit','-m','Obsidianti: publish exact ARP interactive 3D review GLBs and viewer receipt')
  publishcommit=publish(repo,'EVIDENCE')
  for p,src in files.items():
   blob=git(repo,'show','refs/remotes/origin/main:'+p).stdout
   if p.endswith('.glb'):
    if 'oid sha256:'+sha(src) not in blob:raise RuntimeError('REMOTE_LFS_POINTER_SHA_WRONG_'+p)
   elif blob!=src.read_text():raise RuntimeError('REMOTE_EVIDENCE_TEXT_MISMATCH_'+p)
  if {p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}!=protected:raise RuntimeError('CANONICAL_GIT_ASSETS_CHANGED')
  state['evidenceGitCommit']=publishcommit;state['status']='HTTP_VIEWER_AND_REMOTE_GIT_READBACK__OWNER_HEAVY1_REVIEW_PENDING';checkpoint()
  print('EVIDENCE_URL=https://github.com/Valar05/parametric-parambulator/blob/'+publishcommit+'/'+sub+'REPORT.md',flush=True)
  print('CANONICAL_MODEL_UNCHANGED=YES',flush=True);print('AXEKICK_ACTION_UNCHANGED=YES',flush=True);print('STATUS='+state['status'],flush=True)
 except BaseException as exc:
  state['status']='BLOCKED';state['errorType']=type(exc).__name__;state['error']=str(exc)[:850];checkpoint()
  if state.get('viewerURL'):print('VIEWER_URL='+state['viewerURL']+' (HTTP_VERIFIED_BEFORE_LATE_FAILURE)',flush=True)
  print('STATUS=BLOCKED '+type(exc).__name__+' '+str(exc)[:850],flush=True)
  raise
 finally:
  checkpoint();print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('USAGE driver.py packet launcher sha')
 main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3])
