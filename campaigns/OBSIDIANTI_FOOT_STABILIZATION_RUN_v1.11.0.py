#!/usr/bin/env python3
"""Termux Git-only export and identifiable phone viewer for verified sparse FK."""
import os,sys,json,hashlib,pathlib,shutil,tempfile,datetime,subprocess,traceback,zipfile,struct,socket,time,urllib.request
V='OBSIDIANTI_FOOT_STABILIZATION_v1.11.0'
REPO='https://github.com/Valar05/parametric-parambulator.git'
DEST='diagnostics/obsidianti/foot-stabilization-v1.11.0'
BASE_SHA='e740668656c20bd8ea375d5bdeeec49e5719585f7670667e7c232fb2cc34fad4'
BASE_NAME='SPARSE_FK_EDITABLE_UNAPPROVED.blend'
RULES_SHA='547c2af52303f4efb718bbf8f82a698110c7bfca'
CLIPS=['BEFORE_EDITED_'+s for s in ('Heavy1','Heavy2','Heavy3')]
SOURCE={f'campaigns/OBSIDIANTI_FOOT_STABILIZATION_RUN_v1.11.0.py':'driver.py',f'campaigns/OBSIDIANTI_FOOT_STABILIZATION_SOLVER_v1.11.0.py':'stabilize.py',f'campaigns/OBSIDIANTI_FOOT_STABILIZATION_SERVER_v1.11.0.py':'server.py',f'docs/obsidianti/FOOT_STABILIZATION_v1.11.0.md':'readme.md',f'docs/obsidianti/FOOT_STABILIZATION_VIEWER_v1.11.0.html':'viewer.html'}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def run(argv,check=True,timeout=300,env=None):
 p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,timeout=timeout,env=env)
 if p.returncode and check:raise RuntimeError('COMMAND_FAILED '+repr(argv[:6])+'\n'+p.stdout[-700:]+'\n'+p.stderr[-1400:])
 return p
def git(repo,*a,**kw):return run(['git','-C',repo,*a],**kw)
def published(repo,rel):return bool(git(repo,'ls-tree','-r','--name-only','HEAD','--',rel).stdout.strip())
def validate_glb(path):
 with open(path,'rb') as f:
  header=f.read(20)
  if len(header)!=20:raise RuntimeError('GLB_HEADER_TRUNCATED')
  magic,version,total,jsonlen,chunktype=struct.unpack('<4sIIII',header)
  if magic!=b'glTF' or version!=2 or total!=path.stat().st_size or chunktype!=0x4e4f534a:raise RuntimeError('GLB_STRUCTURE_INVALID')
  data=json.loads(f.read(jsonlen))
 animations=data.get('animations',[])
 if len(animations)!=6:raise RuntimeError('EXPORT_WRONG_CLIP_COUNT_'+str([(x.get('name'),len(x.get('channels',[]))) for x in animations]))
 names=[x.get('name','') for x in animations]
 missing=[c for c in CLIPS if not any(c==n or c in n for n in names)]
 if missing:raise RuntimeError('EXPORT_WRONG_ANIMATION_NAMES_'+repr({'missing':missing,'exported':names}))
 if len({n for n in names})!=6:raise RuntimeError('EXPORT_DUPLICATE_CLIP_NAMES')
 if not data.get('meshes') or not data.get('skins'):raise RuntimeError('EXPORT_NO_MESH_OR_SKIN')
 if not data.get('nodes'):raise RuntimeError('EXPORT_NO_NODES')
 if any(len(x.get('channels',[]))<5 for x in animations):raise RuntimeError('EXPORT_ANIMATION_CHANNELS_MISSING')
 paths=[c['target'].get('path') for a in animations for c in a['channels']]
 if 'rotation' not in paths:raise RuntimeError('EXPORT_NO_ROTATION_TRACKS')
 # Reject any other rig's animation as a source of apparent success.
 if any('Lionheart_' in n for n in names):raise RuntimeError('EXPORT_ORIGINAL_ACTIONS_INCLUDED')
 return {'animationNames':names,'animationChannelCounts':{a.get('name'):len(a['channels']) for a in animations},'meshes':len(data['meshes']),'skins':len(data['skins']),'nodes':len(data['nodes']),'fileSHA256':sha(path),'fileBytes':path.stat().st_size}
def main(folder,launcher_sha):
 home=pathlib.Path.home();downloads=home/'storage/downloads';base=downloads/BASE_NAME
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 state=home/'.local/state'/V;state.mkdir(parents=True,exist_ok=True)
 receipt=state/(stamp+'_RECEIPT.json')
 work=pathlib.Path(tempfile.mkdtemp(prefix='obs_sparse_review_'));repo=work/'repo';logs=work/'logs';logs.mkdir()
 doc={'campaign':V,'run':stamp,'authority':'TERMUX_GIT_ONLY','status':'STARTED','sourceBlendSHA256':BASE_SHA,'launcherSHA256':launcher_sha,'rulesAGENTSBlobSHA':RULES_SHA,'rulesEtiquetteSource':'Home Center Drive 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI','authorRulesRead':'2026-11-06','canonicalGLBModified':False,'originalBlendModified':False,'ownerVisualApproval':False,'downloads':{}}
 def save():receipt.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
 save()
 try:
  if not downloads.is_dir():raise RuntimeError('TERMUX_DOWNLOADS_MISSING')
  if not base.is_file() or sha(base)!=BASE_SHA:
   raise RuntimeError('VERIFIED_SPARSE_BLEND_MISSING_OR_HASH_MISMATCH '+str(base))
  print('EDITED_BLEND_VERIFIED='+str(base)+' SHA256='+BASE_SHA,flush=True)
  env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1'
  run(['git','clone','--quiet','--no-checkout',REPO,repo],env=env,timeout=500)
  git(repo,'checkout','-q','main',env=env)
  git(repo,'lfs','install','--local')
  head=git(repo,'rev-parse','HEAD').stdout.strip()
  ag=git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()
  if ag!=RULES_SHA:raise RuntimeError('RULES_AGENTS_CHANGED_'+ag)
  doc.update(startingHEAD=head,executionDir=str(repo));save()
  print('RESOLVED_REPO='+str(repo)+'\nHEAD='+head+'\nBRANCH=main',flush=True)
  targets=[*SOURCE,DEST+'/REPORT.json',DEST+'/REPORT.md',DEST+'/FOOT_STABILIZATION_REVIEW_UNAPPROVED.glb','assets/obsidianti/FOOT_STABILIZATION_v1.11.0_EDITABLE_UNAPPROVED.blend']
  for rel in targets:
   if published(repo,rel) or (repo/rel).exists():raise RuntimeError('VERSION_DESTINATION_COLLISION '+rel)
  for rel,name in SOURCE.items():
   dest=repo/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(folder/name,dest)
  for rel,name in SOURCE.items():
   if sha(repo/rel)!=sha(folder/name):raise RuntimeError('STAGED_FILE_HASH_MISMATCH_'+rel)
  for rel in SOURCE:
   if rel.endswith('.py'):
    import py_compile
    py_compile.compile(str(repo/rel),doraise=True)
  # A unique path-specific LFS rule; never alter the Repl or canonical asset rules.
  git(repo,'lfs','track',DEST+'/*.glb')
  git(repo,'lfs','track','assets/obsidianti/FOOT_STABILIZATION_v1.11.0_EDITABLE_UNAPPROVED.blend')
  targets.append('.gitattributes')
  git(repo,'add','--',*SOURCE,'.gitattributes')
  git(repo,'commit','-m','Obsidianti: foot stabilization campaign source v1.11.0')
  sourcehead=git(repo,'rev-parse','HEAD').stdout.strip()
  git(repo,'push','origin','HEAD:main',timeout=400)
  if git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]!=sourcehead:raise RuntimeError('SOURCE_REMOTE_READBACK_FAILED')
  for rel,name in SOURCE.items():
   if git(repo,'show','HEAD:'+rel).stdout!=(folder/name).read_text():raise RuntimeError('SOURCE_REMOTE_BYTES_MISMATCH_'+rel)
  doc.update(sourceCommit=sourcehead,sourceRemoteReadback=True);save()
  output=work/'FOOT_STABILIZATION_REVIEW_UNAPPROVED.glb';export_report=work/'EXPORT.json'
  blender=shutil.which('blender');proot=shutil.which('proot-distro')
  if blender:
   cmd=[blender,'--background','--disable-autoexec','--python',repo/'campaigns/OBSIDIANTI_FOOT_STABILIZATION_SOLVER_v1.11.0.py','--',base,output,export_report]
  elif proot:
   cmd=[proot,'login','debian','--bind',str(repo)+':/mnt/obs-repo','--bind',str(work)+':/mnt/obs-work','--bind',str(downloads)+':/mnt/obs-downloads','--','blender','--background','--disable-autoexec','--python','/mnt/obs-repo/campaigns/OBSIDIANTI_FOOT_STABILIZATION_SOLVER_v1.11.0.py','--','/mnt/obs-downloads/'+BASE_NAME,'/mnt/obs-work/'+output.name,'/mnt/obs-work/'+export_report.name]
  else:raise RuntimeError('BLENDER_AND_PROOT_DISTRO_MISSING')
  export=run(cmd,check=False,timeout=2300)
  (logs/'blender.log').write_text(export.stdout+'\n'+export.stderr)
  print('BLENDER_EXIT_CODE='+str(export.returncode),flush=True)
  if export.returncode:raise RuntimeError('BLENDER_EXPORT_FAILED '+export.stderr[-600:])
  finding=validate_glb(output)
  blender_meta=json.loads(export_report.read_text())
  if len(blender_meta.get('reviewClips',[]))!=6:raise RuntimeError('BLENDER_REVIEW_CLIP_CONTRACT_FAILED')
  if any(not any(n==c or c in n for n in finding['animationNames']) for c in blender_meta['reviewClips']):raise RuntimeError('EXPORTED_ACTION_IDENTITY_MISMATCH')
  print('STABILIZATION_CANDIDATE_COUNT='+str(blender_meta.get('candidateCount',0)),flush=True)
  if blender_meta.get('candidateCount',0)==0:print('NO_CANDIDATES_ACCEPTED=YES; VIEWER_WILL_SHOW_FALLBACKS',flush=True)
  doc['GLB']=finding;doc['stabilization']=blender_meta;save()
  print('GLB_STRUCTURE_PASS=YES\nANIMATION_COUNT='+str(len(finding['animationNames']))+'\nGLB_SHA256='+finding['fileSHA256'],flush=True)
  report=work/'REPORT.json';report.write_text(json.dumps({'status':'REVIEW_EXPORTED_UNAPPROVED','sourceBlendSHA256':BASE_SHA,'gitSourceCommit':sourcehead,'launcherSHA256':launcher_sha,'validation':finding,'blenderReport':json.loads(export_report.read_text()),'originalFKPreserved':True,'canonicalGLBModified':False},indent=2,sort_keys=True)+'\n')
  markdown=work/'REPORT.md';markdown.write_text('# Obsidianti foot stabilization v1.11.0\n\nStatus: **REVIEW_UNAPPROVED**\n\nThree BEFORE and three candidate/fallback clips from the user-edited source `.blend`. Original edit actions and canonical GLB unchanged. Human visual review pending.\n\nGLB SHA256: '+finding['fileSHA256']+'`\n')
  candidate_blend=output.with_suffix('.blend')
  if not candidate_blend.is_file():raise RuntimeError('BLENDER_CANDIDATE_FILE_MISSING')
  publish=[(DEST+'/REPORT.json',report),(DEST+'/REPORT.md',markdown),(DEST+'/FOOT_STABILIZATION_REVIEW_UNAPPROVED.glb',output),('assets/obsidianti/FOOT_STABILIZATION_v1.11.0_EDITABLE_UNAPPROVED.blend',candidate_blend)]
  for rel,p in publish:
   path=repo/rel;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,path)
  git(repo,'add','--',*[x for x,_ in publish]);git(repo,'commit','-m','Obsidianti: foot stabilization review export v1.11.0')
  evidence=git(repo,'rev-parse','HEAD').stdout.strip()
  git(repo,'lfs','push','origin','HEAD',timeout=850)
  git(repo,'push','origin','HEAD:main',timeout=400)
  if git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]!=evidence:raise RuntimeError('EVIDENCE_REMOTE_READBACK_FAILED')
  ptr=git(repo,'show','HEAD:'+DEST+'/FOOT_STABILIZATION_REVIEW_UNAPPROVED.glb').stdout
  if 'oid sha256:'+sha(output) not in ptr:raise RuntimeError('REMOTE_GLTF_LFS_POINTER_MISMATCH')
  ptrblend=git(repo,'show','HEAD:assets/obsidianti/FOOT_STABILIZATION_v1.11.0_EDITABLE_UNAPPROVED.blend').stdout
  if 'oid sha256:'+sha(candidate_blend) not in ptrblend:raise RuntimeError('REMOTE_BLEND_LFS_POINTER_MISMATCH')
  for rel,p in publish[:2]:
   if hashlib.sha256(git(repo,'show','HEAD:'+rel).stdout.encode()).hexdigest()!=sha(p):raise RuntimeError('REMOTE_REPORT_HASH_MISMATCH '+rel)
  doc.update(evidenceCommit=evidence,remoteReadbackVerified=True);save()
  print('REMOTE_READBACK_VERIFIED=YES EVIDENCE_COMMIT='+evidence,flush=True)
  # Stable phone Download and persistent served copy; never point the viewer to tmp.
  dglb=downloads/(V+'_'+stamp+'.glb')
  if dglb.exists():raise RuntimeError('DOWNLOAD_PATH_COLLISION_'+str(dglb))
  shutil.copyfile(output,dglb)
  if sha(dglb)!=sha(output):raise RuntimeError('DOWNLOAD_GLB_HASH_MISMATCH')
  doc['downloads']['GLB']={'path':str(dglb),'sha256':sha(dglb)}
  dbl=downloads/(V+'_'+stamp+'_EDITABLE_UNAPPROVED.blend')
  if dbl.exists():raise RuntimeError('DOWNLOAD_BLEND_COLLISION')
  shutil.copyfile(candidate_blend,dbl)
  if sha(dbl)!=sha(candidate_blend):raise RuntimeError('DOWNLOAD_BLEND_HASH_MISMATCH')
  doc['downloads']['Blend']={'path':str(dbl),'sha256':sha(dbl)}
  print('DOWNLOADS_EDITABLE_BLEND='+str(dbl)+' SHA256='+sha(dbl),flush=True)
  print('DOWNLOADS_REVIEW_GLB='+str(dglb)+' SHA256='+sha(dglb),flush=True)
  if shutil.which('termux-media-scan'):run(['termux-media-scan',dglb],check=False,timeout=20)
  run_id=stamp+'-'+finding['fileSHA256'][:12]+'-'+launcher_sha[:8]
  site=home/'.local/share'/V/run_id;site.mkdir(parents=True,exist_ok=False)
  shutil.copyfile(output,site/'Obsidianti_Foot_Stabilization.glb');shutil.copyfile(folder/'viewer.html',site/'index.html')
  manifest={'run':run_id,'asset':'Obsidianti_Foot_Stabilization.glb','glbSHA256':finding['fileSHA256'],'blendSHA256':BASE_SHA,'gitCommit':evidence,'launcherSHA256':launcher_sha,'clips':finding['animationNames'],'animationNames':finding['animationNames'],'source':'EDITED_FK_USER_UPLOAD_EXACT_SHA'}
  (site/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
  # Persist server script as its own immutable copy. Server lifespan is independent of checkout.
  shutil.copyfile(folder/'server.py',site/'server.py')
  with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
  log=site/'server.log'
  fd=open(log,'a')
  server=subprocess.Popen([sys.executable,'-B',site/'server.py',site,str(port),run_id],stdin=subprocess.DEVNULL,stdout=fd,stderr=subprocess.STDOUT,cwd=site,start_new_session=True)
  fd.close()
  url=f'http://127.0.0.1:{port}/index.html?run={run_id}'
  print('REVIEW_URL='+url,flush=True)
  for i in range(30):
   if server.poll() is not None:raise RuntimeError('VIEWER_SERVER_EXITED_'+str(server.returncode))
   try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/manifest.json?run={run_id}',timeout=2) as response:
     if response.headers.get('X-Obsidianti-Run')!=run_id:raise RuntimeError('VIEWER_IDENTITY_HEADER_MISMATCH')
     if 'no-store' not in response.headers.get('Cache-Control',''):raise RuntimeError('VIEWER_CACHE_HEADER_MISSING')
     if json.loads(response.read())['glbSHA256']!=finding['fileSHA256']:raise RuntimeError('VIEWER_MANIFEST_SHA_MISMATCH')
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/Obsidianti_Foot_Stabilization.glb',timeout=10) as response:
     if hashlib.sha256(response.read()).hexdigest()!=finding['fileSHA256']:raise RuntimeError('SERVED_GLB_MISMATCH')
    with urllib.request.urlopen(url,timeout=4) as response:
     html=response.read().decode('utf8')
     if 'Foot Stabilization v1.11.0' not in html:raise RuntimeError('SERVED_VIEWER_VERSION_MISMATCH')
    break
   except (OSError,TimeoutError):time.sleep(.2)
  else:raise RuntimeError('VIEWER_HTTP_NOT_READY')
  doc.update(status='VIEWER_READY_UNAPPROVED',viewer={'url':url,'port':port,'pid':server.pid,'run':run_id,'site':str(site),'serverLog':str(log),'glbSHA256':sha(site/'Obsidianti_Foot_Stabilization.glb'),'headers':'no-store; X-Obsidianti-Run='+run_id});save()
  print('VIEWER_HTTP_IDENTITY_VERIFIED=YES\nVIEWER_SERVER_PID='+str(server.pid),flush=True)
  # Best effort only. PRINTED URL remains mandatory if phone does not open.
  opener=shutil.which('termux-open-url')
  if opener:
   res=run([opener,url],check=False,timeout=20)
   print('ANDROID_OPEN_REQUEST='+('SENT' if res.returncode==0 else 'FAILED')+'; REVIEW_URL='+url,flush=True)
  else:print('ANDROID_OPEN_REQUEST=UNAVAILABLE; REVIEW_URL='+url,flush=True)
  print('STATUS=VIEWER_READY_UNAPPROVED\nCANONICAL_GLB_UNCHANGED=YES',flush=True)
 except Exception as e:
  doc['status']='BLOCKED';doc['error']=type(e).__name__+': '+str(e);save()
  traceback.print_exc();print('BLOCKED='+doc['error'],flush=True)
 finally:
  handoff=downloads/(V+'_'+stamp+'_HANDOFF.zip')
  with zipfile.ZipFile(handoff,'w',compression=zipfile.ZIP_DEFLATED) as z:
   z.write(receipt,'receipt.json')
   for p in logs.glob('*'):z.write(p,'logs/'+p.name)
   for name in ('EXPORT.json','REPORT.json','REPORT.md'):
    p=work/name
    if p.exists():z.write(p,'results/'+name)
  print('RECEIPT='+str(receipt)+'\nHANDOFF='+str(handoff)+'\nHANDOFF_SHA256='+sha(handoff),flush=True)
if __name__=='__main__':main(pathlib.Path(sys.argv[1]),sys.argv[2])
