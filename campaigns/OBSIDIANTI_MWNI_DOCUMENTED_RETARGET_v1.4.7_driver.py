#!/usr/bin/env python3
"""Termux-authorized documented Mwni retarget with physical validation, reimport, viewer."""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,struct,subprocess,sys,time,traceback,urllib.request,uuid

V='OBSIDIANTI_MWNI_DOCUMENTED_RETARGET_v1.4.7'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_COMMIT='00d75d2ea608e1f5c3b01aa37a3f905ed0ca10f0'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANONICAL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
REVIEW_RECEIPT='diagnostics/obsidianti/mwni-recovery-v1.4.3/RECOVERY_RECEIPT.json'
RECOVERY_COMMIT='45ee7b2fc7b06a66bfce17ebf7687e300666eabc'
RESULTS_SHA='a04700e59b86a617c7fa66fc0921bae79ee07c282f7ff3418642c270ca51e981'
MODEL='assets/obsidianti/Obsidianti.glb'
LOCKED=(MODEL,'assets/repl/Repl.glb')
SRC={'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER',
     'campaigns/'+V+'_driver.py':'driver.py',
     'campaigns/'+V+'_server.py':'server.py',
     'campaigns/'+V+'_blender_trial.py':'blender_trial.py',
     'campaigns/'+V+'_glb_verify.py':'glb_verify.py',
     'campaigns/'+V+'_viewer.html':'viewer.html',
     'campaigns/'+V+'.contract.json':'contract.json',
     'tests/'+V+'_TEST.py':'test_driver.py'}
DIR='diagnostics/obsidianti/mwni-documented-v1.4.7/runs'

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def cmd(args,timeout=180,env=None,check=True):
    a=[str(x) for x in args]
    p=subprocess.run(a,capture_output=True,text=True,timeout=timeout,env=env)
    if check and p.returncode:raise RuntimeError('COMMAND_FAILURE '+repr(a[:7])+' '+p.stderr[-1200:]+' '+p.stdout[-300:])
    return p

def git(repo,*args,timeout=180,check=True):return cmd(['git','-C',repo,*args],timeout=timeout,check=check)
def g(repo,*args):return git(repo,*args).stdout.strip()

def packet_guard(packet):
    manifest=json.loads((packet/'manifest.json').read_text())
    expected={'driver.py','server.py','viewer.html','contract.json','test_driver.py','blender_trial.py','glb_verify.py'}
    if set(manifest)!=expected:raise RuntimeError('INVALID_PAYLOAD_MEMBERS '+repr(set(manifest)))
    for name,expected_sha in manifest.items():
        source=packet/name
        if not source.is_file() or sha(source)!=expected_sha:raise RuntimeError('PAYLOAD_SHA256_MISMATCH '+name)
    return sha(packet/'manifest.json')

def safe_copy(source,dest):
    source=pathlib.Path(source);dest=pathlib.Path(dest)
    if dest.exists():
        if not dest.is_file() or sha(dest)!=sha(source):raise RuntimeError('DESTINATION_COLLISION '+str(dest))
        return
    dest.parent.mkdir(parents=True,exist_ok=True)
    tmp=dest.with_name('.'+dest.name+'.tmp-'+uuid.uuid4().hex[:8]);shutil.copyfile(source,tmp)
    try:
        if sha(tmp)!=sha(source):raise RuntimeError('COPY_SHA_CHANGED '+str(dest))
        os.replace(tmp,dest)
    finally:
        if tmp.exists():tmp.unlink()

def repo_preflight(root):
    dst=root/'checkout';env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
    # Isolated git only. Never use the operator's dirty checkout.
    cmd(['git','clone','--quiet','--depth=1','--single-branch','--branch','main',REMOTE,dst],timeout=450,env=env)
    if g(dst,'remote','get-url','origin').removesuffix('.git')!=REMOTE.removesuffix('.git'):raise RuntimeError('WRONG_GIT_ORIGIN')
    head=g(dst,'rev-parse','HEAD')
    if head!=BASE_COMMIT:
        if git(dst,'merge-base','--is-ancestor',BASE_COMMIT,'HEAD',check=False).returncode:
            x=git(dst,'fetch','--no-tags','--depth=90','origin',BASE_COMMIT,timeout=180,check=False)
            if x.returncode or git(dst,'merge-base','--is-ancestor',BASE_COMMIT,'HEAD',check=False).returncode:
                raise RuntimeError('CANONICAL_SOURCE_NOT_DESCENDED_FROM_RECOVERY '+head)
    if g(dst,'rev-parse','HEAD:AGENTS.md')!=AGENTS_BLOB:raise RuntimeError('AGENTS_POLICY_SOURCE_CHANGED')
    if g(dst,'status','--porcelain'):raise RuntimeError('ISOLATED_GIT_CHECKOUT_NOT_CLEAN')
    pointer=g(dst,'show','HEAD:'+MODEL)
    if 'oid sha256:'+CANONICAL_SHA not in pointer:raise RuntimeError('CANONICAL_GLB_POINTER_NOT_APPROVED')
    if not (dst/REVIEW_RECEIPT).is_file():raise RuntimeError('GIT_RECOVERY_RECEIPT_MISSING')
    receipt=json.loads((dst/REVIEW_RECEIPT).read_text())
    if receipt.get('canonGLBSHA256')!=CANONICAL_SHA or receipt.get('resultsSHA256')!=RESULTS_SHA:
        raise RuntimeError('RECOVERY_EVIDENCE_NOT_SHA_LOCKED')
    if {item['clip'] for item in receipt.get('files',[]) if item['kind']=='candidateGLB'}!={'Heavy1','Light2'}:
        raise RuntimeError('EXACT_2_CANDIDATE_SET_MISSING')
    if git(dst,'lfs','version',check=False).returncode:raise RuntimeError('GIT_LFS_NOT_INSTALLED')
    return dst,head,receipt

def validate_glb(p,expected,expected_bytes):
    if not p.is_file() or p.is_symlink():raise RuntimeError('REVIEW_GLB_MISSING_OR_SYMLINK '+str(p))
    if p.stat().st_size!=expected_bytes or sha(p)!=expected:raise RuntimeError('REVIEW_GLB_HASH_OR_SIZE_MISMATCH '+str(p))
    with open(p,'rb') as f:
        header=f.read(12)
        if len(header)!=12 or header[:4]!=b'glTF':raise RuntimeError('NOT_GLTF_BINARY '+str(p))
        _,version,total=struct.unpack('<4sII',header)
        if version!=2 or total!=expected_bytes:raise RuntimeError('GLB_HEADER_BYTES_INVALID '+str(p))
        chunk=f.read(8)
        if len(chunk)!=8:raise RuntimeError('GLB_JSON_CHUNK_MISSING')
        size,tag=struct.unpack('<I4s',chunk)
        if tag!=b'JSON' or size>16*1024*1024:raise RuntimeError('GLB_JSON_CHUNK_INVALID')
        info=json.loads(f.read(size))
    clips=[x.get('name') or '<unnamed>' for x in info.get('animations',[])]
    if not clips:raise RuntimeError('NO_REAL_GLB_ANIMATION '+str(p))
    if not info.get('meshes') or not info.get('skins'):raise RuntimeError('GLB_MESH_OR_SKIN_MISSING '+str(p))
    return {'sha256':expected,'bytes':expected_bytes,'animations':clips,'meshes':len(info['meshes']),'skins':len(info['skins'])}

def publish(repo,stage):
    shahead=g(repo,'rev-parse','HEAD')
    for i in range(3):
        x=git(repo,'push','origin','HEAD:refs/heads/main',timeout=350,check=False)
        if not x.returncode:break
        if i==2:raise RuntimeError(stage+'_PUSH_REJECTED '+x.stderr[-1200:])
        time.sleep(2+i)
    remote=git(repo,'ls-remote','origin','refs/heads/main',timeout=100).stdout.split()
    if not remote or remote[0]!=shahead:raise RuntimeError(stage+'_REMOTE_HEAD_NOT_SAME')
    git(repo,'fetch','--quiet','origin','main',timeout=180)
    if g(repo,'rev-parse','refs/remotes/origin/main')!=shahead:raise RuntimeError(stage+'_REMOTE_READBACK_FAILED')
    return shahead

def source_commit(repo,launcher,packet):
    source_files={dst:launcher if name=='LAUNCHER' else packet/name for dst,name in SRC.items()}
    existing=[dst for dst in SRC if (repo/dst).exists()]
    if existing:
        if len(existing)!=len(SRC) or any(sha(repo/dst)!=sha(src) for dst,src in source_files.items()):
            raise RuntimeError('VERSIONED_SOURCE_COLLISION_IN_GIT '+repr(existing))
        return g(repo,'log','-1','--format=%H','--',next(iter(SRC)))
    for dst,src in source_files.items():safe_copy(src,repo/dst)
    git(repo,'add','--',*sorted(SRC))
    names=set(g(repo,'diff','--cached','--name-only').splitlines())
    if names!=set(SRC):raise RuntimeError('SOURCE_STAGING_OUTSIDE_ALLOWLIST '+repr(names))
    if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Campaign')
    if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')
    git(repo,'commit','-m','Obsidianti: documented Mwni alignment, motion gates and live review')
    return publish(repo,'SOURCE')


def addon_fetch(root):
 vendor=root/'vendor-checkout';cmd(['git','init','--quiet',str(vendor)],timeout=90)
 git(vendor,'remote','add','origin',VENDOR_URL)
 env=dict(os.environ,GIT_TERMINAL_PROMPT='0')
 for i in range(3):
  r=cmd(['git','-C',vendor,'fetch','--no-tags','--depth=1','origin',VENDOR_SHA],timeout=380,check=False,env=env)
  if r.returncode==0:break
  if i==2:
   # Some Git hosts decline direct old-SHA shallow fetch. Fetch the short stable branch history instead.
   alt=cmd(['git','-C',vendor,'fetch','--no-tags','--depth=120','origin','refs/heads/stable'],timeout=380,check=False,env=env)
   if alt.returncode:raise RuntimeError('MWNI_PINNED_COMMIT_FETCH_FAILED '+r.stderr[-650:]+' FALLBACK '+alt.stderr[-650:])
   else:break
  time.sleep(i+2)
 git(vendor,'checkout','--detach',VENDOR_SHA)
 if g(vendor,'rev-parse','HEAD')!=VENDOR_SHA:raise RuntimeError('MWNI_VENDOR_COMMIT_MISMATCH')
 if g(vendor,'status','--porcelain'):raise RuntimeError('MWNI_VENDOR_TREE_DIRTY')
 # Prevent name collision with another plugin installation. This is an isolated, permanent module store.
 installed=pathlib.Path.home()/'.local/share/obsidianti-blender-addons'/('mwni-2.1.1-'+VENDOR_SHA[:12])
 module=installed/'animation_retargeting'
 if installed.exists():
  if not (module/'__init__.py').is_file():raise RuntimeError('MWNI_PREVIOUS_PARTIAL_INSTALL_COLLISION')
  for p in vendor.glob('*.py'):
   if not (module/p.name).is_file() or sha(module/p.name)!=sha(p):raise RuntimeError('MWNI_INSTALLED_PLUGIN_BYTES_DIFFER '+p.name)
 else:
  stage=installed.with_name('.'+installed.name+'.tmp-'+uuid.uuid4().hex[:8]);module_tmp=stage/'animation_retargeting'
  module_tmp.mkdir(parents=True)
  for p in vendor.glob('*.py'):safe_copy(p,module_tmp/p.name)
  # Carry upstream license/docs in the permanent pinned mirror without edits.
  for p in vendor.iterdir():
   if p.is_file() and p.suffix.lower() in ('.md','.txt'):
    safe_copy(p,module_tmp/p.name)
  stage.rename(installed)
 for fn in ['__init__.py','context.py','drivers.py','ik.py','baking.py','alignment.py','mapping.py']:
  if not (module/fn).is_file():raise RuntimeError('MWNI_INSTALL_INCOMPLETE '+fn)
 return installed,{p.name:sha(p) for p in sorted(module.glob('*.py'))}


def optional_original(repo,models,paths):
    """Use previously cached, exact canonical bytes; NEVER delay Mwni viewing for a network fetch."""
    previous=(pathlib.Path.home()/'.local/state'/'OBSIDIANTI_MWNI_RETARGET_PLUGIN_v1.4.0'/
              '20261106T172615Z-6d53cfaf'/'repo'/MODEL)
    possible=[previous,repo/MODEL]
    for candidate in possible:
        if candidate.is_file() and candidate.stat().st_size>1000000 and sha(candidate)==CANONICAL_SHA:
            info=validate_glb(candidate,CANONICAL_SHA,candidate.stat().st_size)
            info.update({'url':'/models/canonical.glb','role':'Canonical original (read-only)'})
            paths['canonical']=str(candidate);models['canonical']=info
            return 'ORIGINAL_COMPARE_AVAILABLE_CACHED_SHA_VERIFIED'
    # Local Git LFS checkout may work from a previously cached object, without downloading.
    x=git(repo,'lfs','checkout','--',MODEL,timeout=30,check=False)
    candidate=repo/MODEL
    if x.returncode==0 and candidate.is_file() and candidate.stat().st_size>1000000 and sha(candidate)==CANONICAL_SHA:
        info=validate_glb(candidate,CANONICAL_SHA,candidate.stat().st_size)
        info.update({'url':'/models/canonical.glb','role':'Canonical original (read-only)'})
        paths['canonical']=str(candidate);models['canonical']=info
        return 'ORIGINAL_COMPARE_AVAILABLE_CACHED_LFS'
    return 'ORIGINAL_COMPARE_UNAVAILABLE_NO_NETWORK_FETCH__CANDIDATE_VIEWER_STILL_WORKS'

def start_viewer(repo,runroot,manifest):
    server=repo/('campaigns/'+V+'_server.py')
    config=runroot/'viewer_manifest.json';config.write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    ready=runroot/'viewer_ready.json';log=runroot/'VIEWER_SERVER.log'
    with open(log,'a') as out:
        proc=subprocess.Popen([sys.executable,str(server),'--config',str(config),'--ready',str(ready)],
            stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,close_fds=True)
    for i in range(60):
        if proc.poll() is not None:raise RuntimeError('VIEWER_SERVER_DIED '+log.read_text()[-1700:])
        if ready.is_file():break
        time.sleep(.15)
    if not ready.is_file():raise RuntimeError('VIEWER_SERVER_NEVER_BOUND_PORT '+log.read_text()[-1000:])
    ticket=json.loads(ready.read_text());base='http://127.0.0.1:'+str(ticket['port'])
    def get(path,method='GET'):
        request=urllib.request.Request(base+path,method=method,headers={'Cache-Control':'no-cache'})
        with urllib.request.urlopen(request,timeout=16) as r:
            if r.headers.get('X-Obsidianti-Run')!=manifest['runId'] or r.headers.get('X-Obsidianti-Build')!=manifest['buildToken']:
                raise RuntimeError('STALE_HTTP_SERVER_IDENTITY_MISMATCH '+path)
            return r.read(),dict(r.headers)
    health,_=get('/health');actual=json.loads(health)
    if actual.get('runId')!=manifest['runId'] or actual.get('buildToken')!=manifest['buildToken'] or actual.get('pid')!=ticket['pid']:
        raise RuntimeError('SERVER_PROCESS_AND_MANIFEST_IDENTITY_MISMATCH')
    page,heads=get('/index.html?run='+manifest['runId']+'&build='+manifest['buildToken'])
    if hashlib.sha256(page).hexdigest()!=sha(repo/('campaigns/'+V+'_viewer.html')):
        raise RuntimeError('WRONG_VIEWER_HTML_BYTES')
    if 'no-store' not in heads.get('Cache-Control',''):raise RuntimeError('HTML_CACHE_POLICY_MISSING')
    raw,_=get('/manifest.json');observed=json.loads(raw)
    if observed.get('buildToken')!=manifest['buildToken'] or set(observed['models'])!=set(manifest['models']):raise RuntimeError('VIEWER_MANIFEST_MISMATCH')
    for key,item in manifest['models'].items():
        _,headers=get(item['url'],method='HEAD')
        if headers.get('X-Model-SHA256')!=item['sha256'] or int(headers.get('Content-Length','-1'))!=item['bytes']:
            raise RuntimeError('REAL_HTTP_MODEL_HEADER_MISMATCH '+key)
        if 'no-store' not in headers.get('Cache-Control',''):raise RuntimeError('MODEL_CACHE_POLICY_MISSING')
    return ticket,log

def auto_open(url):
    methods=[]
    if shutil.which('termux-open-url'):methods.append(['termux-open-url',url])
    if shutil.which('am'):methods.append(['am','start','-a','android.intent.action.VIEW','-d',url])
    for args in methods:
        try:
            r=cmd(args,timeout=12,check=False)
            if r.returncode==0:return {'intentSent':True,'command':args[0],'message':r.stdout[-250:]}
        except Exception:pass
    return {'intentSent':False,'reason':'Browser launch unavailable; copy VIEWER_URL into phone browser'}



DONOR_SHA='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
VENDOR_URL='https://github.com/Mwni/blender-animation-retargeting.git'
VENDOR_SHA='8c91ff4f4d898bab835b3587f17585487056b60b'
VENDOR_PIN_RECEIPT='diagnostics/obsidianti/mwni-plugin-v1.4.0/EVIDENCE_RECEIPT.json'
CLIPS=('Kick','Light1')

def original_donor(downloads):
    matches=[]
    for folder in (downloads,pathlib.Path.home()/'storage/documents'):
        if not folder.is_dir():continue
        for file in folder.glob('Lionheart*.blend'):
            if file.is_file() and sha(file)==DONOR_SHA:matches.append(file)
    if not matches:raise RuntimeError('LOCKED_NATIVE_DONOR_BLEND_MISSING_SHA_'+DONOR_SHA)
    return matches[0]

def model_materialize(repo):
    for attempt in range(3):
        r=git(repo,'lfs','fetch','origin','HEAD','--include='+MODEL,'--exclude=',timeout=800,check=False)
        if r.returncode==0:break
        if attempt==2:raise RuntimeError('CANONICAL_LFS_FETCH_FAILED_'+r.stderr[-900:])
        time.sleep(2+attempt)
    git(repo,'lfs','checkout','--',MODEL,timeout=260)
    if sha(repo/MODEL)!=CANONICAL_SHA:raise RuntimeError('CANONICAL_GLB_EXACT_SHA_FAILED')
    return repo/MODEL

def verify_addon(repo,root):
    pinned=json.loads((repo/VENDOR_PIN_RECEIPT).read_text())['vendorScriptHashes']
    installed=pathlib.Path.home()/'.local/share/obsidianti-blender-addons'/('mwni-2.1.1-'+VENDOR_SHA[:12])
    if installed.is_dir():
        module=installed/'animation_retargeting'
        if {f.name:sha(f) for f in module.glob('*.py')}==pinned:return installed
        raise RuntimeError('PINNED_ADDON_MODULE_HASHES_CHANGED')
    addon,checks=addon_fetch(root)
    if checks!=pinned:raise RuntimeError('FETCHED_PINNED_ADDON_HASHES_DIFFER')
    return addon

def blender_run(repo,donor,addon,work):
    if not shutil.which('proot-distro') and not shutil.which('blender'):
        raise RuntimeError('BLENDER_4_3_DEVICE_RUNTIME_NOT_AVAILABLE')
    for script in ('blender_trial.py','glb_verify.py'):safe_copy(repo/('campaigns/'+V+'_'+script),work/script)
    if shutil.which('proot-distro'):
        base=['proot-distro','login','debian','--bind',str(donor.parent.resolve())+':/mnt/obs-input',
              '--bind',str(repo.resolve())+':/mnt/obs-repo','--bind',str(addon.resolve())+':/mnt/obs-addon',
              '--bind',str(work.resolve())+':/mnt/obs-work','--']
        version=cmd(base+['blender','--version'],timeout=90)
        if 'Blender 4.3.' not in version.stdout:raise RuntimeError('PINNED_ADDON_REQUIRES_BLENDER_4_3_'+version.stdout[:140])
        args=base+['blender','--background','--factory-startup','--enable-autoexec','--python',
                   '/mnt/obs-work/blender_trial.py','--','--source','/mnt/obs-input/'+donor.name,
                   '--target','/mnt/obs-repo/'+MODEL,'--addon','/mnt/obs-addon',
                   '--vendor-sha',VENDOR_SHA,'--output','/mnt/obs-work']
    else:
        base=[]
        version=cmd(['blender','--version'],timeout=90)
        if 'Blender 4.3.' not in version.stdout:raise RuntimeError('PINNED_ADDON_REQUIRES_BLENDER_4_3')
        args=['blender','--background','--factory-startup','--enable-autoexec','--python',str(work/'blender_trial.py'),
            '--','--source',str(donor),'--target',str(repo/MODEL),'--addon',str(addon),
            '--vendor-sha',VENDOR_SHA,'--output',str(work)]
    actual=cmd(args,timeout=3400,check=False)
    (work/'BLENDER.log').write_text(actual.stdout+'\n'+actual.stderr)
    if not (work/'BLENDER_EVIDENCE.json').is_file():raise RuntimeError('BLENDER_NO_DIAGNOSTIC_RECEIPT '+actual.stderr[-1300:])
    return base,actual.returncode,json.loads((work/'BLENDER_EVIDENCE.json').read_text())

def verify_one(base,repo,work,clip,row):
    candidate=pathlib.Path(row['outputGLB']['path'])
    if not candidate.is_file():
        candidate=work/clip/candidate.name
    if not candidate.is_file() or sha(candidate)!=row['outputGLB']['sha256']:
        raise RuntimeError('BAKED_CANDIDATE_GLB_SHA_MISSING_'+clip)
    prior=work/clip/'BAKED_METRICS.json';prior.write_text(json.dumps(row['baked'],indent=2)+'\n')
    report=work/clip/'REIMPORTED.json'
    if base:
        args=base+['blender','--background','--factory-startup','--python','/mnt/obs-work/glb_verify.py','--',
              '--glb','/mnt/obs-work/'+clip+'/'+candidate.name,'--clip',clip,
              '--prior','/mnt/obs-work/'+clip+'/BAKED_METRICS.json','--out','/mnt/obs-work/'+clip+'/REIMPORTED.json']
    else:
        args=['blender','--background','--factory-startup','--python',str(work/'glb_verify.py'),'--',
              '--glb',str(candidate),'--clip',clip,'--prior',str(prior),'--out',str(report)]
    r=cmd(args,timeout=720,check=False)
    (work/clip/'REIMPORT.log').write_text(r.stdout+'\n'+r.stderr)
    if not report.exists():raise RuntimeError('REIMPORT_NO_EVIDENCE_'+clip+' '+r.stderr[-600:])
    data=json.loads(report.read_text())
    if r.returncode or data.get('status')!='FRESH_BLENDER_GLTF_REIMPORT_ARTICULATION_PASSED_OWNER_REVIEW_PENDING':
        raise RuntimeError('REIMPORT_PHYSICAL_GATE_FAIL_'+clip+' '+data.get('error',r.stderr[-600:]))
    return candidate,data


def main(packet,launcher,launcher_sha):
    downloads=pathlib.Path.home()/'storage/downloads'
    if not downloads.is_dir():raise RuntimeError('TERMUX_ANDROID_DOWNLOADS_MISSING')
    runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
    file=root/'RECEIPT.json'
    rec={'campaign':V,'runId':runid,'status':'START','authority':'TERMUX_GIT_ONLY','launcherSHA256':launcher_sha,
      'agentsBlobVerified':AGENTS_BLOB,'campaignEtiquetteReadByAuthor':'2026-11-06','canonicalModified':False,
      'pluginDocumentation':VENDOR_URL+'/blob/'+VENDOR_SHA+'/README.md','priorFailedEvidence':'00d75d2ea608e1f5c3b01aa37a3f905ed0ca10f0','ownerVisualVerdict':'PENDING'}
    def save():
        tmp=file.with_suffix('.tmp');tmp.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n');os.replace(tmp,file)
    save()
    try:
        rec['packetSHA256']=packet_guard(packet)
        cmd(['python3','-m','py_compile']+[str(packet/x) for x in ('driver.py','server.py','test_driver.py','blender_trial.py','glb_verify.py')])
        cmd(['python3',str(packet/'test_driver.py')],timeout=60)
        con=json.loads((packet/'contract.json').read_text())
        if set(con['sourceMutablePaths'])!=set(SRC) or con['diagnosticEvidencePathPrefix']!=DIR+'/':
            raise RuntimeError('SOURCE_OR_EVIDENCE_CONTRACT_OUT_OF_SCOPE')
        repo,head,_=repo_preflight(root);rec['inputRemoteHead']=head
        protected={p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}
        rec['lockedGitBlobsBefore']=protected
        donor=original_donor(downloads);rec['sourceBlendSha256']=sha(donor)
        srccommit=source_commit(repo,launcher,packet)
        rec['sourceCommit']=srccommit;rec['status']='SOURCE_GIT_REMOTE_READBACK_VERIFIED';save()
        model=model_materialize(repo);rec['actualCanonicalGLBSHA256']=sha(model)
        addon=verify_addon(repo,root);rec['addonPath']=str(addon)
        work=root/'work';work.mkdir()
        base,rc,data=blender_run(repo,donor,addon,work)
        rec['blenderExitCode']=rc;rec['blenderStatus']=data.get('status');rec['attempts']=data.get('attempts',{})
        save()
        models={};paths={};approved_candidates={};errors={}
        for clip,row in data.get('clips',{}).items():
            try:
                candidate,recheck=verify_one(base,repo,work,clip,row)
                key='candidate'+clip
                desc=validate_glb(candidate,row['outputGLB']['sha256'],row['outputGLB']['bytes'])
                desc.update({'url':'/models/'+key+'.glb','clip':clip,'role':'Documented Mwni IK (unapproved)'})
                models[key]=desc;paths[key]=str(candidate)
                approved_candidates[clip]={'sha256':sha(candidate),'postExportReimport':recheck,'pluginBaked':row['baked'],
                    'pluginAlignment':row['alignment'],'mode':row['mode']}
                for fileinfo in ('outputGLB','outputBlend'):
                    meta=row[fileinfo];local=work/clip/pathlib.Path(meta['path']).name
                    if not local.is_file() or sha(local)!=meta['sha256']:raise RuntimeError('OUTPUT_BYTES_INVALID_'+fileinfo)
                    dest=downloads/(V+'_'+runid+'_'+local.name)
                    safe_copy(local,dest)
                    print('DOWNLOAD_UNAPPROVED='+str(dest)+' SHA256='+sha(dest),flush=True)
            except Exception as exc:
                errors[clip]=str(exc)
        # Review-only preview assets are a distinctly labeled failed gate, never approval.
        # They serve the user's explicit request to SEE the animation and its defects.
        diagnostic_previews={}
        for clip,row in data.get('diagnostics',{}).items():
            if clip in approved_candidates:continue
            try:
                meta=row['outputGLB'];local=work/clip/'diagnostic'/pathlib.Path(meta['path']).name
                desc=validate_glb(local,meta['sha256'],meta['bytes'])
                key='candidate'+clip
                desc.update({'url':'/models/'+key+'.glb','clip':clip,
                             'role':'REJECTED FLOOR/CONTACT GATE: DIAGNOSTIC ONLY, NOT A FIX',
                             'reviewGate':'FAILED','physicalFailures':row['failures']})
                models[key]=desc;paths[key]=str(local)
                diagnostic_previews[clip]={'sha256':meta['sha256'],'failed':row['failures'],
                                           'actualExportedGLB':str(local)}
                dest=downloads/(V+'_'+runid+'_'+local.name)
                safe_copy(local,dest)
                print('DOWNLOAD_REJECTED_DIAGNOSTIC='+str(dest)+' SHA256='+sha(dest),flush=True)
            except Exception as exc:
                errors[clip+'_diagnostic']=str(exc)
        rec['diagnosticPreviews']=diagnostic_previews
        rec['passingClips']=list(approved_candidates);rec['failedClipReasons']=errors
        # Report is always published, including hard failures, by authorized Termux Git.
        reportdir=root/'evidence';reportdir.mkdir()
        detail={'schema':'mwni-documented-v1.4.7','status':'PHYSICAL_VALIDATION_PASSED_FOR_'+','.join(approved_candidates) if approved_candidates else 'NO_PHYSICALLY_VALID_CANDIDATE',
            'runId':runid,'sourceCommit':srccommit,'originalGLBSHA256':CANONICAL_SHA,'originalBlendSHA256':DONOR_SHA,
            'pluginVendorCommit':VENDOR_SHA,'allBlenderTrials':data,'reimportVerified':approved_candidates,'reimportFailures':errors,'diagnosticPreviews':diagnostic_previews,
            'canonicalModified':False,'ownerVisualVerdict':'PENDING','launcherSHA256':launcher_sha,
            'agentsBlob':AGENTS_BLOB,'documentation':'upstream README target unit scale, one-to-one mapping, rest alignment, driver and IK setup, visual-keyed bake', 'preflightActionInventory':data.get('actionInventory'),'sourceSetup':data.get('sourceSetup'), 'v146ObservedBlocker':'SHOE_ABOUT_0_9_M_ABOVE_REST_FLOOR'}
        report=['# Obsidianti Mwni documented test v1.4.7','',
            'Source-only retarget experiment; canonical GLB and source Blender file are immutable.','',
            'Documented plugin rig scale/rest alignment and real limb articulation are tested BEFORE any GLB is promoted to review.',
            'Prior v1.4.0 IK did not move legs correctly despite numeric claims. This version tests source and target hip-relative foot trajectories, joint angle motion and toe vertex heights.',
            '', 'Real Blender execution exit code: '+str(rc),
            'Physically gated and independently GLB-reimported clips: '+(', '.join(approved_candidates) or 'NONE'),
            'Rejected clip details: '+json.dumps(errors,sort_keys=True),
            'REJECTED DIAGNOSTIC PREVIEW CLIPS (NOT VALIDATED): '+(', '.join(diagnostic_previews) or 'NONE'),'',
            'Any passing clip is still UNAPPROVED pending actual owner visual review.','']
        (reportdir/'REPORT.md').write_text('\n'.join(report))
        (reportdir/'EVIDENCE.json').write_text(json.dumps(detail,indent=2)+'\n')
        diagnostics={DIR+'/'+runid+'/REPORT.md':reportdir/'REPORT.md',DIR+'/'+runid+'/EVIDENCE.json':reportdir/'EVIDENCE.json'}
        for dest,source in diagnostics.items():safe_copy(source,repo/dest)
        git(repo,'add','--',*sorted(diagnostics))
        if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(diagnostics):raise RuntimeError('EVIDENCE_ALLOWLIST_VIOLATION')
        git(repo,'commit','-m','Obsidianti: retain documented Mwni Blender motion and GLB reimport evidence')
        evidencecommit=publish(repo,'EVIDENCE');rec['evidenceCommit']=evidencecommit
        for path,source in diagnostics.items():
            if git(repo,'show','HEAD:'+path).stdout!=source.read_text():raise RuntimeError('EVIDENCE_REMOTE_BYTES_DIFFER')
        if {p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}!=protected:raise RuntimeError('PROTECTED_CANONICAL_GIT_BLOBS_CHANGED')
        for source in diagnostics.values():
            dest=downloads/(V+'_'+runid+'_'+source.name);safe_copy(source,dest)
            print('DOWNLOAD_EVIDENCE='+str(dest),flush=True)
        print('REPORT_URL=https://github.com/Valar05/parametric-parambulator/blob/'+evidencecommit+'/'+DIR+'/'+runid+'/REPORT.md',flush=True)
        if not models:raise RuntimeError('NO_PREVIEW_OR_PASSING_CANDIDATE__DIAGNOSTICS_GIT_PUBLISHED')
        rec['resultClassification']=('SOME_PHYSICALLY_VALID' if approved_candidates else 'ONLY_REJECTED_DIAGNOSTIC')
        original_status=optional_original(repo,models,paths);rec['originalStatus']=original_status
        token=hashlib.sha256((runid+srccommit+launcher_sha+''.join(sorted(x['sha256'] for x in models.values()))).encode()).hexdigest()[:24]
        manifest={'schema':'obsidianti-mwni-documented-v1.4.7','runId':runid,'buildToken':token,'launcherSHA256':launcher_sha,
          'sourceCommit':srccommit,'modelPaths':paths,'models':models,'mode':'DOCUMENTED_MWNI_FULL_BODY_UNAPPROVED' if approved_candidates else 'REJECTED_DIAGNOSTIC_NOT_ACCEPTED',
          'htmlPath':str(repo/('campaigns/'+V+'_viewer.html'))}
        ticket,_=start_viewer(repo,root,manifest)
        rec.update({'viewerURL':ticket['url'],'viewerPid':ticket['pid'],'viewerPort':ticket['port'],
                    'status':('PHYSICAL_GATES_AND_GLB_REIMPORT_PASSED_HTTP_VIEWER_IDENTITY_VERIFIED_OWNER_REVIEW_PENDING' if approved_candidates else 'REJECTED_DIAGNOSTIC_HTTP_VIEWER_IDENTITY_VERIFIED_OWNER_REVIEW_PENDING')})
        save()
        print('VIEWER_URL='+ticket['url'],flush=True)
        print('REVIEW_GATE='+rec['resultClassification'],flush=True)
        print('VIEWER_CANDIDATES='+','.join(approved_candidates),flush=True)
        print('VIEWER_REJECTED_DIAGNOSTICS='+','.join(diagnostic_previews),flush=True)
        browser=auto_open(ticket['url']);rec['browserIntent']=browser;save()
        print('BROWSER_OPEN_INTENT_SENT='+str(browser['intentSent']).upper(),flush=True)
        # Final device viewer receipt must be remotely published, not only printed locally.
        live={'schema':'obsidianti-mwni-documented-viewer-v1.4.7','sourceCommit':srccommit,
              'runId':runid,'url':ticket['url'],'buildToken':token,'serverPid':ticket['pid'],
              'serverPort':ticket['port'],'viewerMode':rec['resultClassification'],
              'motionGatePassedClips':list(approved_candidates),'rejectedDiagnosticClips':list(diagnostic_previews),
              'modelHashes':{k:v['sha256'] for k,v in models.items()},
              'browserIntentSent':browser['intentSent'],'HTTPIdentity':'VERIFIED',
              'browserRender':'UNVERIFIED','ownerVisualAcceptance':'PENDING',
              'canonicalModelUnchanged':True,'launcherSHA256':launcher_sha}
        reviewfile=reportdir/'VIEWER_RECEIPT.json';reviewfile.write_text(json.dumps(live,indent=2)+'\n')
        reviewpath=DIR+'/'+runid+'/VIEWER_RECEIPT.json'
        if (repo/reviewpath).exists():raise RuntimeError('NEW_VIEWER_RECEIPT_COLLISION')
        safe_copy(reviewfile,repo/reviewpath)
        git(repo,'add','--',reviewpath)
        if set(g(repo,'diff','--cached','--name-only').splitlines())!={reviewpath}:
            raise RuntimeError('VIEWER_RECEIPT_STAGING_OUTSIDE_ALLOWLIST')
        git(repo,'commit','-m','Obsidianti: record verified Mwni viewer HTTP identity and review status')
        reviewcommit=publish(repo,'VIEWER_RECEIPT');rec['viewerGitCommit']=reviewcommit
        if git(repo,'show','HEAD:'+reviewpath).stdout!=reviewfile.read_text():
            raise RuntimeError('VIEWER_RECEIPT_REMOTE_READBACK_MISMATCH')
        if {p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}!=protected:
            raise RuntimeError('PROTECTED_MODEL_TREE_CHANGED')
        dest=downloads/(V+'_'+runid+'_VIEWER_RECEIPT.json');safe_copy(reviewfile,dest)
        print('VIEWER_RECEIPT_URL=https://github.com/Valar05/parametric-parambulator/blob/'+reviewcommit+'/'+reviewpath,flush=True)
        print('VIEWER_COMMIT='+reviewcommit,flush=True)
        print('CANONICAL_MODEL_UNCHANGED=YES',flush=True)
        print('STATUS='+rec['status'],flush=True)
    except Exception as exc:
        rec.update({'status':'BLOCKED','error':str(exc),'traceback':traceback.format_exc()[-6500:]});save()
        print('STATUS=BLOCKED '+str(exc),flush=True)
        raise
    finally:
        save();print('RECEIPT='+str(file),flush=True)

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('usage: driver.py PACKET_ROOT LAUNCHER_PATH LAUNCHER_SHA256')
    main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve(),sys.argv[3])
