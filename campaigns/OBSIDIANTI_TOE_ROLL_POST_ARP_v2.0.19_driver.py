#!/usr/bin/env python3
"""One-command Termux Git campaign: measured post-ARP toe rolls and AxeKick shoe contact."""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,time,uuid,traceback
V='OBSIDIANTI_TOE_ROLL_POST_ARP_v2.0.19'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE='40d6f8e4465dec37191623d5a1b083227612c2cc'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
LION='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
LIBSHA='3e9a5b4d0ff2847a05d56a81292881d4a3b6b75a7ebdc90e362f6384b31a9021'
AXE='c6f1d74b2de97e12f2eefc9c44a0404c26ad19e29d481af08e585130ee9103da'
TARGET='assets/obsidianti/Obsidianti.glb'
DONOR='assets/obsidianti/source/LionheartLancer.blend'
LIB='diagnostics/obsidianti/arp-full-library-v2.0.14/runs/20261107T031757Z-c7c5e4e4/Obsidianti_ARP_FULL_LIBRARY_UNAPPROVED.glb'
AXEPATH='diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/20261107T021037Z-2edec0d5/AxeKick/ARP_AxeKick_REVIEW.glb'
OLDVIEW='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_viewer.html'
OLDSERVER='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_server.py'
OLDHELPER='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py'
OLDGIT='campaigns/OBSIDIANTI_VANGUARD_RIGIFY_ARP_v2.0.17_driver.py'
LOCKED=[TARGET,'assets/repl/Repl.glb',AXEPATH,LIB]
REL='diagnostics/obsidianti/toe-roll-post-arp-v2.0.19/runs/'
SOURCES={'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER','campaigns/'+V+'_driver.py':'driver.py',
 'campaigns/'+V+'_patch.py':'patch.py','campaigns/'+V+'_source_contacts.py':'source_contacts.py',
 'campaigns/'+V+'_viewer.html':'viewer.html','campaigns/'+V+'_server.py':'server.py',
 'campaigns/'+V+'.contract.json':'contract.json','tests/'+V+'_TEST.py':'test_driver.py'}

def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def command(argv,timeout=500,check=True,env=None):
 argv=[str(x) for x in argv]
 p=subprocess.run(argv,capture_output=True,text=True,errors='replace',stdin=subprocess.DEVNULL,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED_'+str(p.returncode)+' '+repr(argv[:6])+' '+p.stderr[-500:]+' '+p.stdout[-260:])
 return p
def git(repo,*a,timeout=400,check=True):return command(['git','-C',repo,*a],timeout=timeout,check=check)
def g(repo,*a):return git(repo,*a).stdout.strip()
def require(x,msg):
 if not x:raise RuntimeError(msg)
def write_json(path,value):
 p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_name('.'+p.name+'.'+uuid.uuid4().hex[:6]);tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');os.replace(tmp,p)
def copy_new(src,dest):
 src=pathlib.Path(src);dest=pathlib.Path(dest)
 require(src.is_file() and not src.is_symlink(),'SOURCE_MISSING_'+str(src))
 if dest.exists():
  if dest.is_file() and not dest.is_symlink() and digest(dest)==digest(src):return
  raise RuntimeError('DESTINATION_COLLISION_'+str(dest))
 dest.parent.mkdir(parents=True,exist_ok=True)
 temp=dest.with_name('.'+dest.name+'.'+uuid.uuid4().hex[:6]);shutil.copy2(src,temp)
 require(digest(temp)==digest(src),'COPY_SHA_MISMATCH')
 os.replace(temp,dest)
def import_path(path,name):
 """Read checked-out Python code without creating untracked __pycache__.

 The v2.0.18 operator run proved that an ordinary import of the v2.0.17
 Git helper dirties the disposable checkout before its clean-tree gate.
 Do NOT conceal dirt or reset a checkout: suppress the import side effect.
 """
 was=sys.dont_write_bytecode
 try:
  sys.dont_write_bytecode=True
  spec=importlib.util.spec_from_file_location(name,path)
  require(spec is not None and spec.loader is not None,'IMPORT_HELPER_SPEC_MISSING_'+str(path))
  module=importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module
 finally:
  sys.dont_write_bytecode=was
def patch_once(text,old,new):
 require(text.count(old)==1,'VIEWER_PATCH_PRECONDITION_'+old[:90])
 return text.replace(old,new,1)

def make_viewer(repo,packet):
 html=(repo/OLDVIEW).read_text()
 names=['AxeKick_Floor','AxeKick']+[f'Lionheart_{n}_ToeRoll' for n in ('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')]
 names += [f'Lionheart_{n}' for n in ('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')]
 names += ['Heavy1_old_ARP']+[f'Ares_{n}' for n in ('StepForward','StepBack','StepLeft','StepRight','StepForwardLeft','StepForwardRight','StepBackLeft','StepBackRight')]
 options=''.join('<option value="'+n+'">'+n+(' [candidate]' if n.endswith('_ToeRoll') or n=='AxeKick_Floor' else ' [original]')+'</option>' for n in names)
 html=patch_once(html,'<option value="Heavy1">Heavy1</option><option value="AxeKick">AxeKick</option>',options)
 html=patch_once(html,"mode==='candidate'?'candidate'+clip:'canonical'","mode==='candidate'?'candidate':'canonical'")
 html=patch_once(html,'const names=gltf.animations.map(a=>a.name);','const names=gltf.animations.map(a=>a.name);\n const exact=gltf.animations.find(a=>a.name===movement);if(exact)return exact;')
 html=patch_once(html,'if(modelBounds)floor.position.y=modelBounds.min.y+Number(el(\'ground\').value)','if(modelBounds)floor.position.y=Number(el(\'ground\').value)')
 html=patch_once(html,'floor.position.y=modelBounds.min.y+Number(el(\'ground\').value)','floor.position.y=Number(el(\'ground\').value)')
 html=html.replace('Obsidianti | ARP live 3D review','Obsidianti | measured toe-roll A/B review')
 html=html.replace('Heavy1 REVIEW | AxeKick OWNER ACCEPTED','Lionheart toe-roll trial | AxeKick first-frame grounded')
 html=html.replace('AxeKick accepted; Heavy1 hip/foot IK under review. Floor guide is visual, not a contact solver.',
 'Compare original clips with ToeRoll variants. AxeKick_Floor has first-frame skinned sole at Y=0; AxeKick original preserved. Viewer floor grid Y=0. No canonical change. Unapproved.')
 (packet/'viewer.html').write_text(html)
 server=(repo/OLDSERVER).read_text().replace('ObsidiantiARPViewer/2.0.13','ObsidiantiARPViewer/ToeRoll-v2.0.19')
 (packet/'server.py').write_text(server)
 return {'viewer':digest(packet/'viewer.html'),'server':digest(packet/'server.py')}

def publish(repo,stage,protected):
 for attempt in range(4):
  head=g(repo,'rev-parse','HEAD')
  p=git(repo,'push','origin','HEAD:refs/heads/main',timeout=800,check=False)
  if p.returncode==0:
   remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()
   require(remote and remote[0]==head,'GIT_REMOTE_HEAD_READBACK_MISMATCH')
   git(repo,'fetch','--quiet','origin','main',timeout=450)
   require(g(repo,'rev-parse','refs/remotes/origin/main')==head,'GIT_FETCHED_REMOTE_HEAD_MISMATCH')
   for path,blob in protected.items():require(g(repo,'rev-parse','HEAD:'+path)==blob,'PROTECTED_BLOB_CHANGED_'+path)
   return head
  if attempt==3:raise RuntimeError('TERMUX_GIT_PUSH_FAILED_'+stage+'_'+p.stderr[-700:])
  git(repo,'fetch','--quiet','origin','main',timeout=450)
  for path,blob in protected.items():require(g(repo,'rev-parse','refs/remotes/origin/main:'+path)==blob,'REMOTE_PROTECTED_ASSET_CHANGED_'+path)
  git(repo,'rebase','refs/remotes/origin/main',timeout=600)
 raise RuntimeError('TERMUX_GIT_REMOTE_PUBLICATION_EXHAUSTED')

def commit(repo,files,stage,protected):
 for path in files:
  require(not (repo/path).exists(),'VERSIONED_DESTINATION_COLLISION_'+path)
 for path,src in files.items():copy_new(src,repo/path)
 git(repo,'add','--',*sorted(files))
 require(set(g(repo,'diff','--cached','--name-only').splitlines())==set(files),'STAGED_FILE_ALLOWLIST_MISMATCH')
 if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Termux Obsidianti ToeRoll')
 if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','termux-obsidianti-toeroll@users.noreply.github.com')
 git(repo,'commit','-m','Obsidianti: measured toe-roll + AxeKick floor '+stage,timeout=400)
 result=publish(repo,stage,protected)
 for path,src in files.items():
  actual=git(repo,'show','refs/remotes/origin/main:'+path).stdout
  if path.endswith(('.glb','.blend')):
   require('oid sha256:'+digest(src) in actual,'LFS_REMOTE_POINTER_WRONG_'+path)
  else:require(actual==pathlib.Path(src).read_text(),'TEXT_REMOTE_READBACK_MISMATCH_'+path)
 return result

def main(packet,launcher,expected):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 require(launcher.is_file() and digest(launcher)==expected,'LAUNCHER_SHA_MISMATCH')
 manifest=json.loads((packet/'manifest.json').read_text())
 wanted={'driver.py','patch.py','source_contacts.py','test_driver.py','contract.json'}
 require(set(manifest)==wanted and all(digest(packet/n)==v for n,v in manifest.items()),'PACKET_HASH_MANIFEST_MISMATCH')
 contract=json.loads((packet/'contract.json').read_text())
 require(contract['schema']==V and contract['authority']=='TERMUX_GIT_ONLY' and sorted(contract['sourceMutablePaths'])==sorted(SOURCES),'CONTRACT_SCOPE_MISMATCH')
 for n in ('driver.py','patch.py','source_contacts.py','test_driver.py'):command(['python3','-m','py_compile',str(packet/n)])
 command(['python3',str(packet/'test_driver.py'),str(packet/'patch.py')],timeout=450)
 downloads=pathlib.Path.home()/'storage/downloads';require(downloads.is_dir(),'ANDROID_DOWNLOADS_MOUNT_MISSING')
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
 receipt=root/'RECEIPT.json'
 state={'campaign':V,'runId':runid,'status':'BOOT','authority':'TERMUX_GIT_ONLY','stage':'BOOT',
    'launcherSHA256':expected,'rulesBlob':AGENTS,'campaignEtiquetteLiveRead':'CHATGPT_2026_11_07',
    'pinnedGitBase':BASE,'modelCanonicalModified':False,'baselineAnimationsPreserved':True,
    'purchasedARPRerun':False,'ownerVisualAcceptance':'PENDING'}
 def mark(stage):state['stage']=stage;write_json(receipt,state);print('STAGE='+stage,flush=True)
 mark('BOOT')
 try:
  # Fresh isolated Git-only authority. Do not use the model-side container for publication.
  shared=import_path(packet/'driver.py','selfdriver') if False else None
  # Reuse the already reviewed v2.0.17 Git clone/ancestry guard via pinned source.
  env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
  repo=root/'repo'
  command(['git','clone','--quiet','--depth=1','--single-branch','--branch','main',REMOTE,repo],timeout=1200,env=env)
  head=g(repo,'rev-parse','HEAD')
  require(g(repo,'remote','get-url','origin').removesuffix('.git')==REMOTE.removesuffix('.git'),'REPO_REMOTE_MISMATCH')
  before_import=g(repo,'status','--porcelain')
  state['freshCloneGitStatus']=before_import
  require(not before_import,'FRESH_ISOLATED_CLONE_DIRTY_BEFORE_HELPER_IMPORT_'+repr(before_import[:400]))
  helper=import_path(repo/OLDGIT,'verified_v217_git_guard')
  ancestry=helper.verify_pinned_ancestry(repo,BASE,head)
  require(g(repo,'rev-parse','HEAD')==head,'GIT_ANCESTRY_PROBE_CHANGED_HEAD')
  require(g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'AGENTS_RULES_CHANGED_STOP')
  state['gitAncestryProof']=ancestry;state['inputGitHead']=head
  for path,expected_hash in ((TARGET,CANON),(DONOR,LION),(LIB,LIBSHA),(AXEPATH,AXE)):
   content=git(repo,'show','HEAD:'+path).stdout
   require('oid sha256:'+expected_hash in content,'PINNED_LFS_POINTER_MISMATCH_'+path)
  protected={x:g(repo,'rev-parse','HEAD:'+x) for x in LOCKED};state['protectedBefore']=protected
  after_import=g(repo,'status','--porcelain')
  state['postHelperImportGitStatus']=after_import
  state['helperImportProducedPycache']=bool(list((repo/'campaigns').glob('__pycache__/*')))
  require(not after_import,'REPO_CHECKOUT_DIRTY_AFTER_READONLY_HELPER_IMPORT_'+repr(after_import[:500]))
  mark('GIT_PINNED_ANCESTRY_RULES_AND_FOUR_BINARY_ASSETS_VERIFIED')
  for p in (OLDVIEW,OLDSERVER,OLDHELPER,OLDGIT):require((repo/p).is_file(),'BASELINE_SOURCE_MISSING_'+p)
  state['viewerSourceSHA']=make_viewer(repo,packet)
  source_files={k:(launcher if v=='LAUNCHER' else packet/v) for k,v in SOURCES.items()}
  state['sourceCommit']=commit(repo,source_files,'SOURCE',protected)
  mark('TERMUX_GIT_SOURCE_COMMITTED_PUSHED_READBACK')
  runtime=import_path(repo/OLDHELPER,'verified_v213_blender_runtime')
  require(not g(repo,'status','--porcelain'),'REPO_DIRTY_AFTER_RUNTIME_HELPER_IMPORT_'+repr(g(repo,'status','--porcelain')[:400]))
  pd=runtime.private_pd();state['blenderRuntime']=runtime.ensure_container(pd)
  helper.hydrate(repo,{DONOR:LION,LIB:LIBSHA})
  require(digest(repo/LIB)==LIBSHA and digest(repo/DONOR)==LION,'INPUT_LFS_CONTENT_CHANGED')
  mark('EXACT_LIONHEART_AND_V214_REVIEW_LIBRARY_INPUTS_HYDRATED')
  copy_new(packet/'source_contacts.py',root/'source_contacts.py')
  contact=root/'DONOR_CONTACTS.json'
  argv=pd+['login','obs-arp-blender50','--bind',str(root.resolve())+':/mnt/arp-work','--',
     'blender','--background','--factory-startup','--disable-autoexec','--python','/mnt/arp-work/source_contacts.py','--',
     '--source','/mnt/arp-work/repo/'+DONOR,'--sha',LION,'--output','/mnt/arp-work/DONOR_CONTACTS.json']
  r=command(argv,timeout=3600,check=False)
  (root/'BLENDER_DONOR_CONTACTS.log').write_text(r.stdout+'\n'+r.stderr)
  source_report=json.loads(contact.read_text()) if contact.is_file() else {}
  require(r.returncode==0 and source_report.get('status')=='DONOR_NATIVE_BLENDER_TOE_WITNESSES_VERIFIED' and len(source_report.get('actions',{}))==10,
    'ACTUAL_SOURCE_CONTACT_BLENDER_MEASUREMENT_FAILED_rc='+str(r.returncode)+'_'+str(source_report.get('error',r.stderr[-600:]))[:700])
  mark('NATIVE_DONOR_CONTACTS_MEASURED_FOR_ALL_TEN_CLIPS')
  result=root/(V+'_'+runid+'_A_B_REVIEW.glb')
  report=root/'MEASUREMENTS_AND_CORRECTIONS.json'
  trial=command(['python3',str(packet/'patch.py'),'--source',str(repo/LIB),'--contacts',str(contact),
   '--output',str(result),'--report',str(report)],timeout=900,check=False)
  (root/'PATCH.log').write_text(trial.stdout+'\n'+trial.stderr)
  patched=json.loads(report.read_text()) if report.is_file() else {}
  require(trial.returncode==0 and patched.get('status')=='UNAPPROVED_EXPERIMENT' and result.is_file() and
   digest(result)==patched.get('outputSHA256') and patched.get('newAnimations')==11,
   'TOE_ROLL_PATCH_OR_AXEKICK_GROUND_FAILED_'+str(trial.stderr[-850:]))
  require(patched.get('originalSampleBufferPreserved') and patched['axeKick']['originalPreserved'] and
   abs(patched['axeKick']['after']['minY'])<=.002,'AXEKICK_OR_SOURCE_ANIMATION_PRESERVATION_MISMATCH')
  output_download=downloads/result.name;copy_new(result,output_download)
  require(digest(output_download)==digest(result),'DOWNLOADS_CANDIDATE_SHA_MISMATCH')
  state['combinedReviewGLB']=str(output_download);state['combinedSHA256']=digest(result)
  mark('ORIGINALS_PLUS_ALL_ELEVEN_VARIANTS_COPIED_TO_ANDROID_DOWNLOADS')
  for fn in ('DONOR_CONTACTS.json','MEASUREMENTS_AND_CORRECTIONS.json'):
   copy_new(root/fn,downloads/(V+'_'+runid+'_'+fn))
  build=hashlib.sha256((runid+state['sourceCommit']+expected+digest(output_download)).encode()).hexdigest()[:24]
  viewer={'schema':V,'runId':runid,'buildToken':build,'launcherSHA256':expected,'sourceCommit':state['sourceCommit'],
    'htmlPath':str(repo/('campaigns/'+V+'_viewer.html')),
    'models':{'candidate':{'sha256':digest(output_download),'bytes':output_download.stat().st_size,
      'url':'/models/candidate.glb','animations':patched['clipNames']}},
    'modelPaths':{'candidate':str(output_download)},'canonicalModelSHA256':CANON,
    'mode':'ORIGINALS_PRESERVED_AND_10_TOEROLL_PLUS_AXEKICK_FLOOR_CANDIDATES'}
  runtime.V=V;ticket=runtime.start_server(root,repo,viewer)
  state['viewerURL']=ticket['url'];state['viewerPID']=ticket['pid'];state['viewerPort']=ticket['port']
  mark('NO_CACHE_REAL_GLB_HTTP_VIEWER_SHA_VERIFIED')
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(runtime.open_browser(ticket['url'])).upper(),flush=True)
  evidence={'schema':V,'runId':runid,'sourceCommit':state['sourceCommit'],'inputCommit':head,'rulesBlob':AGENTS,
   'ownerIntent':'10 LIONHEART TOE ROLL PATCHES AND AXEKICK FLOOR AFTER RETARGET','authority':'TERMUX_GIT_ONLY',
   'sourceDonorSHA256':LION,'sourceReviewGLBSHA256':LIBSHA,'originalAcceptedAxeKickSHA256':AXE,
   'canonicalSHA256':CANON,'canonicalModified':False,'originalAnimationsPreserved':True,'retargetingRerun':False,
   'inputClips':patched['inputAnimations'],'createdVariantClips':patched['newAnimations'],
   'outGLBSHA256':digest(output_download),'outGLBBytes':output_download.stat().st_size,
   'toeRollCorrections':{x:{'correctedSamples':y['correctedSamples'],'maxOffsetM':y['maxOffsetM'],
     'rejectedFrames':len(y['rejected'])} for x,y in patched['lionheart'].items()},
   'axeKickGroundOffsetM':patched['axeKick']['shiftM'],'axeKickMeasuredFirstFrame':patched['axeKick']['before'],
   'axeKickGroundVerified':patched['axeKick']['after']['minY'],
   'viewerURL':ticket['url'],'viewerHTTPVerified':True,'viewerRendered':'OWNER_UNVERIFIED',
   'ownerVisualAcceptance':'PENDING','protectedBefore':protected,
   'protectedAfter':{x:g(repo,'rev-parse','HEAD:'+x) for x in LOCKED}}
  require(evidence['protectedBefore']==evidence['protectedAfter'],'PROTECTED_REPO_ASSETS_CHANGED')
  write_json(root/'EVIDENCE.json',evidence)
  rep=root/'REPORT.md'
  rep.write_text('# Obsidianti post-ARP donor foot length / toe-roll experiment v2.0.19\n\n'
   'Owner: all ten Lionheart attack clips plus AxeKick grounded. No new ARP retarget; canonical unchanged.\n\n'
   '**Status:** A/B REVIEW ONLY, NO VISUAL APPROVAL.\n\n'
   'Source: LionheartLancer.blend SHA256 '+LION+'; baseline review GLB SHA256 '+LIBSHA+'; branch base '+BASE+'\n\n'
   'First-frame AxeKick weighted shoe surface: '+str(round(patched['axeKick']['before']['minY'],6))+
   ' m; constant hips Y correction '+str(round(patched['axeKick']['shiftM'],6))+' m; new first-frame min '+
   str(round(patched['axeKick']['after']['minY'],8))+' m.\n\n'
   'Original AxeKick is untouched in combined GLB; revised variant named AxeKick_Floor.\n\n'
   '## Toe-roll results\n\n'+''.join('- '+name+': '+str(value['correctedSamples'])+' foot-frame samples, maximum '+
   str(value['maxOffsetM'])+' m, '+str(len(value['rejected']))+' guarded-out samples\n'
   for name,value in patched['lionheart'].items())+'\nA/B viewer: '+ticket['url']+'\n\n'
   'All original 20 GLB animations retained, same original animation samplers and source BIN prefix.\n'
   'Donor foot contacts measured from native Blender source; see DONOR_CONTACTS.json.\n'
   'No tweaks to Vanguard or original AxeKick, and no preservation claims beyond recorded structural tests.\n')
  dest=REL+runid+'/'
  files={dest+'REPORT.md':rep,dest+'EVIDENCE.json':root/'EVIDENCE.json',
    dest+'DONOR_CONTACTS.json':contact,dest+'MEASUREMENTS_AND_CORRECTIONS.json':report,
    dest+'Obsidianti_ToeRoll_A_B_UNAPPROVED.glb':output_download}
  check=git(repo,'check-attr','filter','--',dest+'Obsidianti_ToeRoll_A_B_UNAPPROVED.glb').stdout
  require('lfs' in check,'OUTPUT_GLB_GIT_LFS_ATTRIBUTE_MISSING')
  state['evidenceCommit']=commit(repo,files,'EVIDENCE',protected)
  state['status']='A_B_REVIEW_READY_AND_REMOTE_READBACK_VERIFIED'
  state['ownerVisualAcceptance']='PENDING';mark('DONE_A_B_REVIEW_UNAPPROVED')
  print('RESULT_GLB='+str(output_download),flush=True)
  print('OUTPUT_SHA256='+digest(output_download),flush=True)
  print('TERMUX_EVIDENCE_COMMIT='+state['evidenceCommit'],flush=True)
  print('AXEKICK_FIRST_FRAME_FOOT_Y='+str(patched['axeKick']['after']['minY']),flush=True)
 except BaseException as exc:
  state.update({'status':'BLOCKED','errorType':type(exc).__name__,'error':str(exc)[:1500],
    'traceback':traceback.format_exc()[-3800:]})
  mark('BLOCKED_'+state.get('stage','UNKNOWN'))
  print('BLOCKED='+str(exc)[:1500],flush=True)
  raise

if __name__=='__main__':main(sys.argv[1],sys.argv[2],sys.argv[3])
