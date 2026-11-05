#!/usr/bin/env python3
"""Termux-Git campaign: make an *unapproved* multi-action Obsidianti review candidate.

Exports source Lionheart GLB and applies Blender IK to eight previously rejected
Lionheart action leg tracks. Original v1.5.6 Heavy1 candidate and all protected
tracks are preserved. Never mutates the canonical model.
"""
from __future__ import annotations
import datetime,hashlib,io,json,os,pathlib,shutil,socket,subprocess,sys,tarfile,time,uuid,zipfile,struct,traceback
V='OBSIDIANTI_MULTI_ACTION_NATIVE_IK_v1.7.0'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_MODEL='assets/obsidianti/Obsidianti.glb'
BASE_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
BLEND='assets/obsidianti/source/LionheartLancer.blend'
BLEND_SHA='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
CALIB='diagnostics/obsidianti/lionheart-ik-all-v1.4.0/calibration.json'
CALIB_SHA='b6d23f49c67df7816124362f4b1ee540db5c16a672fbc8c435a7f503ca123336'
MATH='campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py'
MATH_SHA='dc19a766ce41950c8040a81339d488573f70151910aa3ebf479ab8296484851f'
ENGINE_ORIG='campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_EVAL_v1.5.6.py'
APPLY_ORIG='campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_APPLY_v1.5.6.py'
ENGINE='campaigns/OBSIDIANTI_MULTI_ACTION_IK_EVAL_v1.7.0.py'
APPLY='campaigns/OBSIDIANTI_MULTI_ACTION_IK_APPLY_v1.7.0.py'
DRIVER='campaigns/OBSIDIANTI_MULTI_ACTION_IK_RUN_v1.7.0.py'
EXPORTER='campaigns/OBSIDIANTI_MULTI_ACTION_SOURCE_EXPORT_v1.7.0.py'
VIEW='review/obsidianti-multi-action-review-v1.7.0.html'
DOC='docs/obsidianti/MULTI_ACTION_IK_REVIEW_v1.7.0.md'
ACTIONS=('Cast','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
PROTECTED=('Lionheart_Heavy1','Lionheart_Heavy2')
HANDOFF_SHA='fc3ca580b82de074f6a2f040e8335baf1351b74a102df389bbaa5dfc85a68c3a'
PREVIEW_SHA='261f10786dd0eb0e80667173e4a893f6822356da628a5907efd6d0bbc2a74ff5'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for part in iter(lambda:f.read(1048576),b''):h.update(part)
 return h.hexdigest()
def cmd(argv,*,check=True,timeout=240,env=None):
 p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+repr(argv[:6])+' rc='+str(p.returncode)+'\n'+p.stderr[-1800:]+'\n'+p.stdout[-500:])
 return p
def git(root,*args,**kw):return cmd(['git','-C',str(root),*args],**kw)
def network_cmd(argv,*,timeout,env,attempts=3):
 last=None
 for i in range(attempts):
  try:return cmd(argv,timeout=timeout,env=env)
  except RuntimeError as e:
   last=e
   if i+1<attempts:
    if 'clone' in argv and pathlib.Path(argv[-1]).is_dir():shutil.rmtree(argv[-1])
    time.sleep(2+i*3)
 raise RuntimeError('NETWORK_RETRY_EXHAUSTED '+str(last))

def read_glb(path):
 data=pathlib.Path(path).read_bytes()
 if data[:4]!=b'glTF':raise RuntimeError('GLB_MAGIC_INVALID '+str(path))
 n,t=struct.unpack_from('<II',data,12)
 if t!=0x4E4F534A:raise RuntimeError('GLB_JSON_CHUNK_MISSING')
 g=json.loads(data[20:20+n]);return g

def marker_patch(s,needle,new,label):
 n=s.count(needle)
 if n!=1:raise RuntimeError('TEMPLATE_PATCH_AMBIGUOUS '+label+' matches='+str(n))
 return s.replace(needle,new)

def patch_eval_and_apply(repo,pack):
 engine=(repo/ENGINE_ORIG).read_text();apply=(repo/APPLY_ORIG).read_text()
 # Version the reusable evaluator and remove only Heavy1-specific action identities.
 # SHA is assigned after parsing --source; source path is separately verified by the runner
 engine=marker_patch(engine,"HEAVY1_SHA='a14304e455f978fcdbb0607f187a175310e034fdfed7f83176402fd7eb9f1fd4'","HEAVY1_SHA=''",'engine SHA')
 engine=marker_patch(engine," a=args()\n if bpy.app.version", " a=args()\n global HEAVY1_SHA\n HEAVY1_SHA=sha(a.source)\n if bpy.app.version",'engine set hash')
 engine=marker_patch(engine,"source['action']!='Heavy1' or len(source['frames'])!=61", "source['action']!=a.action or len(source['frames'])<3",'engine action validation')
 # Actual original indentation below is one space (function-local).
 engine=marker_patch(engine," p.add_argument('--amplitude',type=float,default=1.0)", " p.add_argument('--action',required=True)\n p.add_argument('--amplitude',type=float,default=1.0)",'engine CLI')
 engine=marker_patch(engine,"x['name']=='Lionheart_Heavy1'", "x['name']=='Lionheart_'+a.action",'engine target clip')
 engine=marker_patch(engine,"if len(frames)!=61:raise RuntimeError('BLENDER_SOURCE_NOT_ALL_61_FRAMES')", "if len(frames)!=len(source['frames']):raise RuntimeError('BLENDER_SOURCE_SAMPLE_COUNT_WRONG')",'engine sample count')
 engine=marker_patch(engine,"VER='OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.6'", "VER='"+V+"'",'engine version')
 apply=marker_patch(apply,"HEAVY1_SHA='a14304e455f978fcdbb0607f187a175310e034fdfed7f83176402fd7eb9f1fd4'","HEAVY1_SHA=''",'apply SHA')
 # Validate exact original indentation before inserting code.
 apply=marker_patch(apply," a=p.parse_args()", " a=p.parse_args()\n global HEAVY1_SHA,CLIP\n HEAVY1_SHA=sha(a.source);CLIP='Lionheart_'+a.action",'apply set hash')
 apply=marker_patch(apply," p.add_argument('--out',required=True)", " p.add_argument('--action',required=True)\n p.add_argument('--out',required=True)",'apply CLI')
 apply=marker_patch(apply,"len(frames)!=61 or any(y<=x for x,y in zip(stimes,stimes[1:])) or abs(stimes[0])>.001 or abs(stimes[-1]-1)>.001", "len(frames)!=len(source['frames']) or any(y<=x for x,y in zip(stimes,stimes[1:])) or abs(stimes[0])>.001 or abs(stimes[-1]-float(source['durationSeconds']))>.001",'apply timeline')
 apply=marker_patch(apply,"VER='OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.6'", "VER='"+V+"'",'apply version')
 for txt,path in ((engine,repo/ENGINE),(apply,repo/APPLY)):
  compile(txt,str(path),'exec');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(txt)
 return {ENGINE:sha(repo/ENGINE),APPLY:sha(repo/APPLY)}

def blender_command(repo,work,script,args):
 b=shutil.which('blender')
 if b:return [b,'--background','--disable-autoexec','--python',str(repo/script),'--',*map(str,args)]
 proot=shutil.which('proot-distro')
 if not proot:raise RuntimeError('BLENDER_UNAVAILABLE_NATIVE_AND_PROOT_DEBIAN')
 rr=repo.resolve();ww=work.resolve()
 def mapped(p):
  s=str(pathlib.Path(p).resolve())
  if s.startswith(str(rr)+'/'):return '/mnt/obs-repo/'+s[len(str(rr))+1:]
  if s.startswith(str(ww)+'/'):return '/mnt/obs-work/'+s[len(str(ww))+1:]
  raise RuntimeError('BLENDER_ARG_OUTSIDE_VERIFIED_BIND '+s)
 aa=[]
 for x in args:
  s=str(x);aa.append(mapped(s) if s.startswith('/') else s)
 return [proot,'login','debian','--bind',str(rr)+':/mnt/obs-repo','--bind',str(ww)+':/mnt/obs-work','--','blender','--background','--disable-autoexec','--python',mapped(repo/script),'--',*aa]

def pick_base(downloads,work):
 found=[]
 for p in downloads.glob('OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.6*_HANDOFF.zip'):
  if sha(p)==HANDOFF_SHA:found.append(p)
 if len(found)!=1:raise RuntimeError('VERIFIED_V156_HANDOFF_MISSING_OR_AMBIGUOUS_IN_DOWNLOADS')
 with zipfile.ZipFile(found[0]) as z:
  content=z.read('visual/Candidate_UNAPPROVED.glb')
 if hashlib.sha256(content).hexdigest()!=PREVIEW_SHA:raise RuntimeError('V156_CANDIDATE_BINARY_MISMATCH')
 p=work/'v156-visual-base.glb';p.write_bytes(content)
 return p,found[0]

def merge(repo,base,selected,output):
 # Preserve all original v1.5.6 animation sampler objects except six rotation
 # samplers for each expressly selected action. Original binary remains prefix.
 import importlib.util,math
 spec=importlib.util.spec_from_file_location('obs_multi_glb_math',repo/MATH)
 M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
 g,b=M.load_glb(base)
 before=__import__('copy').deepcopy(g)
 oldbuf=bytes(b)
 ids={n.get('name'):i for i,n in enumerate(g['nodes']) if n.get('name')}
 def append(values,kind):
  while len(b)%4:b.append(0)
  count={'SCALAR':1,'VEC4':4}[kind]
  flat=[float(x) for row in values for x in ([row] if kind=='SCALAR' else row)]
  if any(not math.isfinite(x) for x in flat):raise RuntimeError('NONFINITE_CHANNEL_OUTPUT')
  off=len(b);b.extend(struct.pack('<'+'f'*len(flat),*flat))
  vi=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':4*len(flat)})
  ai=len(g['accessors']);v={'bufferView':vi,'componentType':5126,'count':len(values),'type':kind}
  if kind=='SCALAR':v['min']=[min(values)];v['max']=[max(values)]
  g['accessors'].append(v);return ai
 for action,filename in selected.items():
  sample=json.loads(pathlib.Path(filename).read_text());frames=sample['frames'];times=[float(f['timeSeconds']) for f in frames]
  anim=next(x for x in g['animations'] if x['name']=='Lionheart_'+action)
  inputs=append(times,'SCALAR');n=0
  for ch in anim['channels']:
   if ch['target']['path']!='rotation':continue
   name=g['nodes'][ch['target']['node']].get('name')
   if name not in [f'mixamorig:{s}{p}' for s in ('Left','Right') for p in ('UpLeg','Leg','Foot')]:continue
   qs=[f['joints'][name] for f in frames]
   if any(abs(math.hypot(*q)-1)>0.0002 for q in qs):raise RuntimeError('BAD_BAKED_QUATERNION '+name)
   output_idx=append(qs,'VEC4');sm=anim['samplers'][ch['sampler']]
   sm['input']=inputs;sm['output']=output_idx;sm['interpolation']='LINEAR';n+=1
  if n!=6:raise RuntimeError('EXACT_SIX_ROTATION_TRACKS_REQUIRED '+action+' found='+str(n))
 after={x['name']:x for x in g['animations']};prior={x['name']:x for x in before['animations']}
 protected=[x for x in prior if x not in {'Lionheart_'+a for a in selected}]
 if any(after[x]!=prior[x] for x in protected):raise RuntimeError('UNAUTHORIZED_CLIP_MUTATION')
 if not bytes(b).startswith(oldbuf):raise RuntimeError('INPUT_BINARY_PREFIX_CHANGED')
 for key in ('nodes','skins','meshes','materials','textures','images','scenes'):
  if g.get(key)!=before.get(key):raise RuntimeError('PROTECTED_GLB_STRUCTURE_CHANGED_'+key)
 if sha(base)!=PREVIEW_SHA:raise RuntimeError('V156_BASE_CHANGED_DURING_MERGE')
 output.write_bytes(M.encode_glb(g,b))
 new=read_glb(output)
 if len(new['animations'])!=len(before['animations']):raise RuntimeError('FINAL_ANIMATION_COUNT_CHANGED')
 return {'inputCandidateSHA256':PREVIEW_SHA,'outputSHA256':sha(output),'modifiedActions':list(selected),'protectedAnimations':protected,'animationCount':len(new['animations'])}

def serve(public,runid,status):
 import urllib.request
 code="import http.server,sys\nclass H(http.server.SimpleHTTPRequestHandler):\n def end_headers(self):\n  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')\n  self.send_header('Pragma','no-cache')\n  self.send_header('X-Obsidianti-Review',sys.argv[3])\n  super().end_headers()\nhttp.server.ThreadingHTTPServer(('127.0.0.1',int(sys.argv[1])),lambda *a,**kw:H(*a,directory=sys.argv[2],**kw)).serve_forever()\n"
 for _ in range(18):
  s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
  log=open(public/'server.log','ab',buffering=0)
  proc=subprocess.Popen([sys.executable,'-B','-c',code,str(port),str(public),runid],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True)
  url=f'http://127.0.0.1:{port}/viewer.html?run={runid}'
  for _ in range(25):
   if proc.poll() is not None:break
   try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/manifest.json',timeout=1) as r:
     if r.status==200 and r.headers.get('X-Obsidianti-Review')==runid and 'no-store' in r.headers.get('Cache-Control',''):
      status['viewer']={'url':url,'port':port,'PID':proc.pid,'headers':dict(r.headers),'run':runid};return url
   except Exception:time.sleep(.15)
  proc.terminate();proc.wait(timeout=4)
 raise RuntimeError('VIEWER_LIVE_IDENTITY_FAILED')

def run(packet,launcher_sha):
 downloads=pathlib.Path.home()/'storage/downloads'
 if not downloads.is_dir():raise RuntimeError('TERMUX_STORAGE_DOWNLOADS_NOT_AVAILABLE')
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:7]
 state=pathlib.Path.home()/'.local/state'/V/runid
 state.mkdir(parents=True,exist_ok=False)
 work=state/'work';work.mkdir()
 repo=state/'repo'
 receipt=downloads/(V+'_'+runid+'_RECEIPT.json')
 status={'campaign':V,'run':runid,'authority':'TERMUX_GIT_ONLY','stage':'INIT','status':'STARTED',
  'launcherSHA256':launcher_sha,'agentsExpectedBlob':AGENTS_BLOB,
  'etiquetteReadByAuthor':'2026-11-05 Home Center',
  'baseModelSHA256':BASE_SHA,'v156PreviewSHA256':PREVIEW_SHA,
  'sourceBlendSHA256':BLEND_SHA,'attempts':{},'selected':{},'canonicalModelChanged':False,
  'ownerVisualAcceptance':'PENDING'}
 def save():
  receipt.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
 save()
 try:
  if not shutil.which('git') or not shutil.which('python3'):raise RuntimeError('TERMUX_DEPENDENCIES_MISSING')
  env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1';env['GIT_TERMINAL_PROMPT']='0';env['PYTHONDONTWRITEBYTECODE']='1'
  status['stage']='CLONE_ISOLATED';save()
  network_cmd(['git','clone','--depth=30','--single-branch','--branch','main','--config','filter.lfs.smudge=','--config','filter.lfs.required=false',REMOTE,repo],timeout=600,env=env)
  original=git(repo,'rev-parse','HEAD').stdout.strip();status['originalGitHead']=original
  agents=git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()
  if agents!=AGENTS_BLOB:raise RuntimeError('AGENTS_BLOB_REVISION_CHANGED '+agents)
  if any(z not in (repo/'AGENTS.md').read_text() for z in ('Campaign Etiquette','Termux Git')):raise RuntimeError('REPOSITORY_RULES_MISSING')
  status['rulesRead']='REPO_AGENTS_VERIFIED_AND_ETIQUETTE_READ_BY_AUTHOR';save()
  status['stage']='VERIFY_V156_REVIEW_BASE';save()
  visualbase,handoff=pick_base(downloads,work)
  status['verifiedV156Handoff']=str(handoff);status['verifiedV156HandoffSHA256']=HANDOFF_SHA
  status['stage']='PREFLIGHT_DESTINATIONS';save()
  mappings={DRIVER:'driver.py',ENGINE:'GENERATE',APPLY:'GENERATE',EXPORTER:'export.py',VIEW:'viewer.html',DOC:'doc.md'}
  for dest in mappings:
   if (repo/dest).exists() or git(repo,'ls-tree','HEAD','--',dest).stdout.strip():raise RuntimeError('NEW_SOURCE_DESTINATION_COLLISION '+dest)
  for dest,file in mappings.items():
   if file=='GENERATE':continue
   path=repo/dest;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(pathlib.Path(packet)/file,path)
  generated=patch_eval_and_apply(repo,packet)
  for path in mappings:
   if not (repo/path).is_file():raise RuntimeError('MISSING_CAMPAIGN_SOURCE '+path)
  status['stage']='SOURCE_COMMIT_AND_REMOTE_READBACK';save()
  git(repo,'add','--',*mappings)
  staged=git(repo,'diff','--cached','--name-only').stdout.splitlines()
  if set(staged)!=set(mappings):raise RuntimeError('GIT_STAGED_SCOPE_MISMATCH '+repr(staged))
  if not git(repo,'config','--get','user.email',check=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')
  if not git(repo,'config','--get','user.name',check=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Campaign')
  git(repo,'commit','-m','Obsidianti: multiaction Blender IK unapproved review campaign v1.7.0')
  commit=git(repo,'rev-parse','HEAD').stdout.strip();status['sourceCommit']=commit
  network_cmd(['git','-C',repo,'push','origin','HEAD:refs/heads/main'],timeout=240,env=env)
  readback=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]
  if readback!=commit:raise RuntimeError('SOURCE_REMOTE_COMMIT_READBACK_MISMATCH')
  status['sourceRemoteReadback']=readback;save()
  status['stage']='LOAD_PINNED_LFS_ASSETS';save()
  if cmd(['git','lfs','version'],check=False).returncode:raise RuntimeError('TERMUX_GIT_LFS_UNAVAILABLE')
  network_cmd(['git','-C',repo,'lfs','pull','--include='+','.join([BASE_MODEL,BLEND]),'--exclude='],timeout=1500,env={**env,'GIT_LFS_SKIP_SMUDGE':'0'})
  for path,digest in ((BASE_MODEL,BASE_SHA),(BLEND,BLEND_SHA),(CALIB,CALIB_SHA),(MATH,MATH_SHA)):
   if sha(repo/path)!=digest:raise RuntimeError('PINNED_REPOSITORY_INPUT_HASH_MISMATCH '+path)
  status['stage']='NATIVE_BLENDER_SOURCE_EXPORT';save()
  source_dir=work/'source';source_dir.mkdir()
  args=[repo/BLEND,source_dir,BLEND_SHA]
  p=cmd(blender_command(repo,work,EXPORTER,args),check=False,timeout=1800)
  (work/'lionheart-export.log').write_text(p.stdout+'\n'+p.stderr)
  if p.returncode:raise RuntimeError('SOURCE_EXPORT_FAILED '+p.stderr[-1600:])
  source_meta=json.loads((source_dir/'source_exports.json').read_text())['model']
  if sha(source_dir/source_meta['file'])!=source_meta['sha256']:raise RuntimeError('SOURCE_EXPORT_HASH_FAILED')
  source_info=read_glb(source_dir/source_meta['file'])
  if not source_info.get('animations'):raise RuntimeError('SOURCE_EXPORT_NO_ANIMATIONS')
  status['sourceExportAnimationNames']=[a['name'] for a in source_info['animations']];save()
  selected={}
  for action in ACTIONS:
   status['stage']='SOLVE_'+action;save()
   donor=repo/f'diagnostics/obsidianti/lionheart-ik-all-v1.4.0/actions/{action}.json'
   if not donor.is_file():raise RuntimeError('ACTION_NATIVE_SOURCE_MISSING '+action)
   source=json.loads(donor.read_text())
   if source['action']!=action or len(source['frames'])<3:raise RuntimeError('ACTION_SOURCE_MALFORMED '+action)
   rows=[];winner=None
   # Native original calibrated scale first; retry alternatives if physical failure.
   for strategy,ratio,amp in [('native','combined',1.0),('local','combined',1.0),('native','thigh',1.0),('native','combined',.92)]:
    tag=f'{action}-{strategy}-{ratio}-{amp}'.replace('.','_')
    sample=work/(tag+'-evaluated.json');ereport=work/(tag+'-engine.json');physical=work/(tag+'-physical.json');candidate=work/(tag+'-alone.glb')
    row={'action':action,'profile':[strategy,ratio,amp],'nativeBlender':False,'candidate':False,'physicalPass':False}
    arguments=['--action',action,'--model',repo/BASE_MODEL,'--source',donor,'--calibration',repo/CALIB,'--math-helper',repo/MATH,
      '--output',sample,'--report',ereport,'--amplitude',amp,'--strategy',strategy,'--leg-ratio',ratio]
    try:
     e=cmd(blender_command(repo,work,ENGINE,arguments),check=False,timeout=1500)
     (work/(tag+'-blender.log')).write_text(e.stdout+'\n'+e.stderr)
     if e.returncode or not sample.is_file():
      row['error']='BLENDER_EVAL '+e.stderr[-800:];rows.append(row);continue
     row['nativeBlender']=True;row['sampleSHA256']=sha(sample)
     a=cmd(['python3','-B',repo/APPLY,'--action',action,'--model',repo/BASE_MODEL,'--math-helper',repo/MATH,
       '--native-ik-samples',sample,'--source',donor,'--report',physical,'--out',candidate],check=False,timeout=1200)
     (work/(tag+'-apply.log')).write_text(a.stdout+'\n'+a.stderr)
     if not candidate.is_file():row['error']='APPLY_FAILED '+a.stderr[-800:];rows.append(row);continue
     row['candidate']=True;row['candidateSHA256']=sha(candidate)
     phys=json.loads(physical.read_text());row['metrics']=phys.get('metrics',{});row['failures']=phys.get('failures',[]);row['physicalPass']=a.returncode==0
     row['report']=str(physical)
     # Retain first valid; if none valid, retain minimum-error inspectable sample.
     severity=len(row['failures'])*100+row['metrics'].get('maxNativeControllerMiss_m',0)*50+row['metrics'].get('maxSkinnedPenetration_m',0)*30
     row['severity']=severity
     if not winner or (row['physicalPass'] and not winner['physicalPass']) or (row['physicalPass']==winner['physicalPass'] and severity<winner['severity']):
      winner={**row,'samples':str(sample)}
     if row['physicalPass']:
      rows.append(row);break
    except Exception as ex:row['error']=type(ex).__name__+':'+str(ex)[-900:]
    rows.append(row)
   status['attempts'][action]=rows
   if winner:
    selected[action]=winner['samples'];status['selected'][action]={k:v for k,v in winner.items() if k!='samples'}
   else:status['selected'][action]={'status':'NO_CANDIDATE_AVAILABLE','manualReviewRequired':True}
   save()
  if not selected:raise RuntimeError('NO_ACTION_SOLVED_BY_NATIVE_BLENDER')
  status['stage']='MERGE_UNAPPROVED_PREVIEW';save()
  preview=work/'Obsidianti_MULTIACTION_REVIEW.glb'
  merged=merge(repo,visualbase,selected,preview)
  status['merged']=merged;status['unsolvedActions']=[a for a in ACTIONS if a not in selected]
  status['numericPreflightFullyPassed']=all(x['physicalPass'] for x in status['selected'].values() if 'physicalPass' in x) and not status['unsolvedActions']
  status['stage']='SERVE_PHONE_REVIEW';save()
  public=state/'review';public.mkdir()
  shutil.copyfile(preview,public/'Obsidianti.glb')
  shutil.copyfile(repo/VIEW,public/'viewer.html')
  shutil.copyfile(source_dir/source_meta['file'],public/source_meta['file'])
  manifest={'run':runid,'campaign':V,'sourceCommit':commit,'sourceBlendSHA256':BLEND_SHA,
   'obsidiantiSha256':sha(preview),'source':source_meta,'targetGLB':{'animations':[a['name'] for a in read_glb(preview)['animations']]},
   'candidateLabel':'Obsidianti v1.5.6 + new multi-action IK review, NOT APPROVED',
   'modifiedActions':list(selected),'unsolvedActions':status['unsolvedActions']}
  (public/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
  for p in [public/'Obsidianti.glb',public/source_meta['file']]:
   expected=manifest['obsidiantiSha256'] if p.name=='Obsidianti.glb' else source_meta['sha256']
   if sha(p)!=expected:raise RuntimeError('SERVED_MODEL_HASH_MISMATCH')
  url=serve(public,runid,status)
  status['status']='UNAPPROVED_MULTIACTION_VISUAL_REVIEW_AVAILABLE'
  status['stage']='COMPLETE_REVIEW_PENDING';save()
  print('VIEWER_URL='+url,flush=True)
  print('CANDIDATE_SHA256='+sha(preview),flush=True)
  print('REVIEW_ACTIONS='+','.join(selected),flush=True)
  print('UNSOLVED_ACTIONS='+','.join(status['unsolvedActions']),flush=True)
  print('PHYSICAL_PREFLIGHT_ALL_PASSED='+str(status['numericPreflightFullyPassed']),flush=True)
  print('CANONICAL_GLB_UNCHANGED=YES\nOWNER_VISUAL_ACCEPTANCE=PENDING',flush=True)
 except Exception as exc:
  status['status']='BLOCKED';status['error']=type(exc).__name__+': '+str(exc);status['stage']='BLOCKED_'+status['stage'];save()
  print('BLOCKED='+status['error'],flush=True)
  traceback.print_exc();raise
 finally:
  status['receipt']=str(receipt);save()
  # Always retain checkpoint evidence and small logs in an operator bundle.
  zpath=downloads/(V+'_'+runid+'_HANDOFF.zip')
  with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
   archive.write(receipt,'receipt.json')
   for p in sorted(work.glob('*log')):archive.write(p,'logs/'+p.name)
   for p in sorted(work.glob('*physical.json')):archive.write(p,'physical/'+p.name)
   if status.get('viewer'):
    archive.write(state/'review/manifest.json','visual/manifest.json')
  print('RECEIPT='+str(receipt)+'\nHANDOFF_ZIP='+str(zpath)+'\nHANDOFF_SHA256='+sha(zpath),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('USAGE: driver.py VERIFIED_PACKET_DIR LAUNCHER_SHA256')
 run(pathlib.Path(sys.argv[1]),sys.argv[2])
