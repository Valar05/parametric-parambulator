#!/usr/bin/env python3
"""Termux Git only: forensic verification and export-parity correction of previously baked Mwni clips.
Never retarget anew or modify original blend, canonical Obsidianti, or Repl.
"""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,struct,subprocess,sys,time,traceback,urllib.request,uuid
import glb_scan

V='OBSIDIANTI_MWNI_EXPORT_PARITY_v1.4.8'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_COMMIT='32d751466f940a0ad3d9caffae5a43db409ea7d0'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANONICAL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
MODEL='assets/obsidianti/Obsidianti.glb'
LOCKED=(MODEL,'assets/repl/Repl.glb')
REVIEW_RECEIPT='diagnostics/obsidianti/mwni-recovery-v1.4.3/RECOVERY_RECEIPT.json'
RESULTS_SHA='a04700e59b86a617c7fa66fc0921bae79ee07c282f7ff3418642c270ca51e981'
PREV_CAMPAIGN='OBSIDIANTI_MWNI_DOCUMENTED_RETARGET_v1.4.7'
PREV_RUN='20261106T205439Z-97230b05'
PREV_EVIDENCE='diagnostics/obsidianti/mwni-documented-v1.4.7/runs/'+PREV_RUN+'/EVIDENCE.json'
VENDOR_PIN='8c91ff4f4d898bab835b3587f17585487056b60b'
SOURCE_BLEND_SHA='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
INPUTS={
 'Kick':{'blend':'1647b546fc3e6f6e907d79ef740200da94b50649834d3fa1dad1df6c19abe81c',
         'glb':'7812f8adc9ea7d957e1bdb1486d5da57fa52b026d0deb80c245d0d51afc48601'},
 'Light1':{'blend':'a871f2bbbe5d401012d847edc2c81d1fa0a224876d3d1c0295189601da7a1b19',
           'glb':'1f7852abd5e51c514d4856b91344c23ba8f1364c4366903f45fbd61eb9d51a99'}
}
VARIANTS=('ACTIONS','NLA_TRACKS','SCENE','ACTIVE_ACTIONS')
SRC={'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER',
     'campaigns/'+V+'_driver.py':'driver.py',
     'campaigns/'+V+'_glb_scan.py':'glb_scan.py',
     'campaigns/'+V+'_glb_verify.py':'glb_verify.py',
     'campaigns/'+V+'_export_variants.py':'export_variants.py',
     'campaigns/'+V+'_server.py':'server.py',
     'campaigns/'+V+'_viewer.html':'viewer.html',
     'campaigns/'+V+'.contract.json':'contract.json',
     'tests/'+V+'_TEST.py':'test_driver.py'}
DIR='diagnostics/obsidianti/mwni-export-parity-v1.4.8/runs'


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
    expected={'driver.py','server.py','viewer.html','contract.json','test_driver.py','glb_scan.py','glb_verify.py','export_variants.py'}
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
    git(repo,'commit','-m','Obsidianti: forensic Mwni baked-action GLB export parity viewer v1.4.8')
    return publish(repo,'SOURCE')

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


def previous_preflight(repo):
    old=json.loads((repo/PREV_EVIDENCE).read_text())
    if old['originalGLBSHA256']!=CANONICAL_SHA or old['originalBlendSHA256']!=SOURCE_BLEND_SHA:
        raise RuntimeError('V147_ORIGINAL_SOURCE_IDENTITY_CHANGED')
    if old['sourceCommit']!='0f6b0cb3ad23d12dff7e49311110b761600ee166':
        raise RuntimeError('V147_ORIGINAL_SOURCE_COMMIT_CHANGED')
    if old['pluginVendorCommit']!=VENDOR_PIN:raise RuntimeError('V147_VENDOR_COMMIT_CHANGED')
    for clip,meta in INPUTS.items():
        row=old['allBlenderTrials']['clips'][clip]
        if row['status']!='BLENDER_IK_BAKE_AND_MOTION_GATES_PASSED_UNAPPROVED':
            raise RuntimeError('V147_BAKED_CLIP_NOT_VALID '+clip)
        for key,fn in (('blend','outputBlend'),('glb','outputGLB')):
            if row[fn]['sha256']!=meta[key]:raise RuntimeError('V147_PRIOR_OUTPUT_SHA_CHANGED '+clip+' '+key)
        if not row.get('baked') or row['physicalFailures']:
            raise RuntimeError('V147_MOTION_GATE_NOT_PASSED '+clip)
    return old

def locate_inputs(root,downloads):
    prev=pathlib.Path.home()/'.local/state'/PREV_CAMPAIGN/PREV_RUN/'work'
    out={}
    for clip,meta in INPUTS.items():
        directory=prev/clip
        entries={}
        for typ,suffix in (('blend','.blend'),('glb','.glb')):
            path=directory/('MWNI147_'+clip+'_UNAPPROVED'+suffix)
            if not path.is_file() or path.is_symlink():
                raise RuntimeError('V147_EXACT_BAKED_SNAPSHOT_MISSING '+str(path))
            if sha(path)!=meta[typ]:raise RuntimeError('V147_EXACT_BAKED_SNAPSHOT_HASH_CHANGED '+str(path))
            entries[typ]=path
        out[clip]=entries
    return out,prev

def runtime(prev,work):
    for script in ('glb_verify.py','glb_scan.py','export_variants.py'):
        safe_copy(work.parent/'checkout'/('campaigns/'+V+'_'+script),work/script)
    if shutil.which('proot-distro'):
        base=['proot-distro','login','debian','--bind',str(prev.resolve())+':/mnt/obs-prev',
              '--bind',str(work.resolve())+':/mnt/obs-work','--']
        check=cmd(base+['blender','--version'],timeout=100)
        if 'Blender 4.3.' not in check.stdout:raise RuntimeError('V147_BLEND_REPLAY_WRONG_BLENDER '+check.stdout[:200])
        return base,True
    check=cmd(['blender','--version'],timeout=100)
    if 'Blender 4.3.' not in check.stdout:raise RuntimeError('BLENDER_4_3_RUNTIME_MISSING')
    return [],False

def run_verification(base,virtual,work,clip,glb,prior,label):
    stage=work/clip/label;stage.mkdir(parents=True,exist_ok=False)
    priorfile=stage/'BAKED_METRICS.json';priorfile.write_text(json.dumps(prior,indent=2)+'\n')
    report=stage/'REIMPORTED.json'
    if virtual:
        # Known v1.4.7 artifact location is mapped separately below.
        if glb.is_relative_to(work):gp='/mnt/obs-work/'+glb.relative_to(work).as_posix()
        else:
            prev=pathlib.Path.home()/'.local/state'/PREV_CAMPAIGN/PREV_RUN/'work'
            gp='/mnt/obs-prev/'+glb.relative_to(prev).as_posix()
        args=base+['blender','--background','--factory-startup','--python','/mnt/obs-work/glb_verify.py','--',
            '--glb',gp,'--clip',clip,'--prior','/mnt/obs-work/'+priorfile.relative_to(work).as_posix(),
            '--out','/mnt/obs-work/'+report.relative_to(work).as_posix()]
    else:
        args=['blender','--background','--factory-startup','--python',str(work/'glb_verify.py'),'--',
            '--glb',str(glb),'--clip',clip,'--prior',str(priorfile),'--out',str(report)]
    result=cmd(args,timeout=750,check=False)
    (stage/'BLENDER_REIMPORT.log').write_text(result.stdout+'\n'+result.stderr)
    if not report.is_file():return {'status':'BLOCKED','error':'GLB_REIMPORT_NO_REPORT '+result.stderr[-500:]}
    data=json.loads(report.read_text());data['blenderExitCode']=result.returncode
    return data

def variant_export(base,virtual,work,clip,blend,mode):
    folder=work/clip/mode;folder.mkdir(parents=True,exist_ok=False)
    outfile=folder/(clip+'_'+mode+'_UNAPPROVED.glb')
    if virtual:
        args=base+['blender','--background','--factory-startup','--enable-autoexec',
            '--python','/mnt/obs-work/export_variants.py','--','--blend','/mnt/obs-prev/'+clip+'/'+blend.name,
            '--expected',INPUTS[clip]['blend'],'--clip',clip,'--mode',mode,
            '--out','/mnt/obs-work/'+outfile.relative_to(work).as_posix()]
    else:
        args=['blender','--background','--factory-startup','--enable-autoexec','--python',str(work/'export_variants.py'),
            '--','--blend',str(blend),'--expected',INPUTS[clip]['blend'],'--clip',clip,
            '--mode',mode,'--out',str(outfile)]
    proc=cmd(args,timeout=950,check=False)
    (folder/'EXPORT.log').write_text(proc.stdout+'\n'+proc.stderr)
    report=outfile.with_suffix('.json');data=json.loads(report.read_text()) if report.exists() else {'status':'BLOCKED','error':'EXPORT_REPORT_MISSING'}
    data['exitCode']=proc.returncode
    return outfile,data

def use_model(models,paths,clip,glb,scan,role,gate):
    key='candidate'+clip
    desc=validate_glb(glb,scan['sha256'],scan['bytes'])
    desc.update({'url':'/models/'+key+'.glb','clip':clip,'role':role,'reviewGate':gate,
      'animatedJointCount':scan['movingJointCount'],'exportVariant':scan.get('exportVariant','original')})
    models[key]=desc;paths[key]=str(glb)

def main(packet,launcher,launcher_sha):
    downloads=pathlib.Path.home()/'storage/downloads'
    if not downloads.is_dir():raise RuntimeError('ANDROID_DOWNLOADS_UNAVAILABLE')
    runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
    receipt=root/'RECEIPT.json'
    rec={'campaign':V,'runId':runid,'status':'BOOT','authority':'TERMUX_GIT_ONLY',
         'launcherSHA256':launcher_sha,'rulesBlob':AGENTS_BLOB,'canonSHA256':CANONICAL_SHA,
         'priorRun':PREV_RUN,'canonicalModified':False,'ownerVisualVerdict':'PENDING'}
    def save():
        tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n');os.replace(tmp,receipt)
    save()
    try:
        rec['payloadManifestSHA256']=packet_guard(packet)
        cmd(['python3','-m','py_compile']+[str(packet/x) for x in ('driver.py','glb_scan.py','glb_verify.py','export_variants.py','server.py','test_driver.py')])
        cmd(['python3',packet/'test_driver.py'],timeout=90)
        contract=json.loads((packet/'contract.json').read_text())
        if set(contract['sourceMutablePaths'])!=set(SRC) or contract['diagnosticEvidencePathPrefix']!=DIR+'/':
            raise RuntimeError('VERSIONED_SOURCE_OR_EVIDENCE_SCOPE_MISMATCH')
        repo,head,_=repo_preflight(root);rec['inputGitHead']=head
        original={p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}
        rec['protectedModelGitBlobsBefore']=original
        old=previous_preflight(repo)
        inputfiles,prev=locate_inputs(root,downloads)
        rec['previousFilesSHA256Verified']={clip:{k:sha(p) for k,p in row.items()} for clip,row in inputfiles.items()}
        commit=source_commit(repo,launcher,packet);rec['sourceCommit']=commit
        rec['status']='SOURCE_PUBLISHED_REMOTE_VERIFIED';save()
        work=root/'work';work.mkdir()
        base,virtual=runtime(prev,work)
        trials={};selected={};errors={};models={};paths={};review_gate={}
        for clip in ('Light1','Kick'):
            prior=old['allBlenderTrials']['clips'][clip]['baked']
            row={'clip':clip,'previousSourceSHA256':INPUTS[clip], 'variants':[],'status':'START'}
            trials[clip]=row
            candidates=[('PRIOR_ACTIVE_ACTIONS',inputfiles[clip]['glb'],None)]
            for idx,(label,glb,meta) in enumerate(candidates):
                scan=glb_scan.scan(glb,clip);scan['exportVariant']=label
                record={'mode':label,'scan':{k:v for k,v in scan.items() if k!='channelDetails'},'status':'SCAN_COMPLETED'}
                row['variants'].append(record)
                if scan['animatedLimbs'] and scan['movingJointCount']>=6:
                    result=run_verification(base,virtual,work,clip,glb,prior,label)
                    record['reimport']=result
                    if result['status']=='FRESH_BLENDER_GLTF_REIMPORT_ARTICULATION_PASSED_OWNER_REVIEW_PENDING':
                        selected[clip]={'glb':glb,'scan':scan,'verify':result,'variant':label};row['status']='PARITY_PASS';break
                else:record['rejection']='GLB_ROTATION_VALUES_STATIC_OR_MISSING'
            if clip not in selected:
                for mode in VARIANTS:
                    outfile,exp=variant_export(base,virtual,work,clip,inputfiles[clip]['blend'],mode)
                    record={'mode':mode,'export':exp};row['variants'].append(record)
                    if exp.get('status')!='EXPORTED_VARIANT_UNREVIEWED' or exp.get('exitCode'):
                        record['rejection']='EXPORT_FAILED';continue
                    if sha(outfile)!=exp['outputSHA256']:raise RuntimeError('EXPORT_VARIANT_SHA_CHANGED '+clip+' '+mode)
                    try:scan=glb_scan.scan(outfile,clip)
                    except Exception as exc:
                        record['rejection']='GLB_SCAN_FAILED '+str(exc);continue
                    scan['exportVariant']=mode;record['scan']={k:v for k,v in scan.items() if k!='channelDetails'}
                    if not scan['animatedLimbs'] or scan['movingJointCount']<6:
                        record['rejection']='GLB_ROTATION_VALUES_STATIC_OR_MISSING';continue
                    result=run_verification(base,virtual,work,clip,outfile,prior,mode)
                    record['reimport']=result
                    if result['status']=='FRESH_BLENDER_GLTF_REIMPORT_ARTICULATION_PASSED_OWNER_REVIEW_PENDING':
                        selected[clip]={'glb':outfile,'scan':scan,'verify':result,'variant':mode};row['status']='PARITY_PASS';break
                    record['rejection']='REIMPORT_PHYSICAL_OR_ACTION_BINDING_FAILURE'
            if clip not in selected:
                row['status']='NO_ANIMATED_AND_GROUNDED_EXPORT_VERIFIED'
                errors[clip]=[{'mode':v['mode'],'reason':v.get('rejection') or v.get('reimport',{}).get('error','UNRESOLVED')} for v in row['variants']]
                # Retain an explicitly rejected preview rather than falsely claiming nothing was generated.
                diag=next((v for v in row['variants'] if v.get('scan',{}).get('animatedLimbs')),None)
                if diag:
                    raw=next((p for name,p,unused in candidates if name==diag['mode']),None)
                    if raw is None:raw=work/clip/diag['mode']/(clip+'_'+diag['mode']+'_UNAPPROVED.glb')
                    scan=glb_scan.scan(raw,clip);scan['exportVariant']=diag['mode']
                    use_model(models,paths,clip,raw,scan,'REJECTED DIAGNOSTIC: motion/skin/reimport gate not accepted','FAILED')
                    review_gate[clip]='REJECTED_DIAGNOSTIC_ONLY'
                else:
                    # Existing v1.4.7 GLB remains available for visual comparison, openly labeled rejected.
                    raw=inputfiles[clip]['glb'];scan=glb_scan.scan(raw,clip);scan['exportVariant']='PRIOR_ACTIVE_ACTIONS'
                    use_model(models,paths,clip,raw,scan,'REJECTED DIAGNOSTIC: zero validated armature animation','FAILED')
                    review_gate[clip]='REJECTED_DIAGNOSTIC_ONLY'
            else:
                picked=selected[clip];use_model(models,paths,clip,picked['glb'],picked['scan'],
                    'GLB ANIMATION AND SKIN REIMPORT VERIFIED; UNAPPROVED OWNER REVIEW','PENDING')
                review_gate[clip]='AWAITING_OWNER_VISUAL_ACCEPTANCE'
            chosen=paths.get('candidate'+clip)
            if chosen:
                p=pathlib.Path(chosen)
                dest=downloads/(V+'_'+runid+'_'+clip+'_'+review_gate[clip]+'.glb')
                safe_copy(p,dest)
                print('DOWNLOAD_REVIEW_GLB='+str(dest)+' SHA256='+sha(dest)+' CLASS='+review_gate[clip],flush=True)
            rec['completedClipTests']=list(trials);save()
        rec['clipStatuses']={k:v['status'] for k,v in trials.items()}
        rec['verifiedModels']={k:v['scan']['sha256'] for k,v in selected.items()}
        rec['reviewClassification']=review_gate;save()
        work_report=root/'evidence';work_report.mkdir()
        summary={'schema':'obsidianti-mwni-export-parity-v1.4.8','runId':runid,
          'sourceCommit':commit,'previousEvidenceCommit':'c7d5137a3014e9cd8c1a847b6f9a8a2f0037e455',
          'canonicalSha256':CANONICAL_SHA,'originalDonorBlendSha256':SOURCE_BLEND_SHA,
          'vendorCommit':VENDOR_PIN,'priorShaVerified':rec['previousFilesSHA256Verified'],
          'results':trials,'passingClips':list(selected),'errors':errors,
          'canonicalModified':False,'ownerVisualAcceptance':'PENDING','authorRules':{'agentsBlob':AGENTS_BLOB,'etiquetteRead':'2026-11-06 live'}}
        (work_report/'EVIDENCE.json').write_text(json.dumps(summary,indent=2)+'\n')
        note=['# Obsidianti Mwni export parity campaign v1.4.8','',
          '**Only v1.4.7 SHA-locked already baked scene files were used. No retarget solver was rerun.**','',
          'Both the raw glTF keyframe values and an explicitly bound fresh Blender reimport are verified.',
          'A rejected diagnostic viewer does not establish physical acceptance.','',
          'Verified GLB/skin clips: '+(', '.join(selected) or 'NONE'),
          'Failed/diagnostic clips: '+(', '.join(k for k in trials if k not in selected) or 'NONE'),
          'Git source revision: '+commit,'Canonical GLB SHA: '+CANONICAL_SHA,'',
          'All pre/post-export attempted variants and reimport failures are in EVIDENCE.json.',
          'No canonical model mutation or owner visual approval was attempted.','']
        (work_report/'REPORT.md').write_text('\n'.join(note))
        evfiles={DIR+'/'+runid+'/'+p.name:p for p in (work_report/'EVIDENCE.json',work_report/'REPORT.md')}
        if any((repo/name).exists() for name in evfiles):raise RuntimeError('GIT_EVIDENCE_PATH_COLLISION')
        for target,src in evfiles.items():safe_copy(src,repo/target)
        git(repo,'add','--',*sorted(evfiles))
        if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(evfiles):raise RuntimeError('GIT_EVIDENCE_ALLOWLIST_FAILURE')
        git(repo,'commit','-m','Obsidianti: diagnose exported glTF keyframe values and verify Mwni baked action parity')
        evidencecommit=publish(repo,'EVIDENCE');rec['evidenceCommit']=evidencecommit
        for path,f in evfiles.items():
            if git(repo,'show','HEAD:'+path).stdout!=f.read_text():raise RuntimeError('GIT_REMOTE_EVIDENCE_BYTES_DIFFER '+path)
        if {p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}!=original:raise RuntimeError('CANONICAL_GIT_BLOBS_CHANGED')
        for f in evfiles.values():
            dest=downloads/(V+'_'+runid+'_'+f.name);safe_copy(f,dest)
            print('DOWNLOAD_EVIDENCE='+str(dest),flush=True)
        print('REPORT_URL=https://github.com/Valar05/parametric-parambulator/blob/'+evidencecommit+'/'+DIR+'/'+runid+'/REPORT.md',flush=True)
        optional_status=optional_original(repo,models,paths)
        if not models:raise RuntimeError('VIEWER_NO_MODEL_TO_PRESENT')
        token=hashlib.sha256((launcher_sha+runid+evidencecommit).encode()).hexdigest()[:24]
        manifest={'schema':'obsidianti-mwni-export-parity-v1.4.8-viewer','runId':runid,'buildToken':token,
          'sourceCommit':commit,'launcherSHA256':launcher_sha,
          'models':models,'modelPaths':paths,'htmlPath':str(repo/('campaigns/'+V+'_viewer.html')),
          'originalStatus':optional_status,'ownerReviewRequired':True,
          'reviewClassification':review_gate,'canonicalModelSHA256':CANONICAL_SHA}
        ticket,log=start_viewer(repo,root,manifest)
        rec.update({'viewerURL':ticket['url'],'viewerPid':ticket['pid'],'status':'VIEWER_HTTP_IDENTITY_VERIFIED_OWNER_REVIEW_PENDING'});save()
        print('VIEWER_URL='+ticket['url'],flush=True)
        print('REVIEW_GATE='+str(review_gate),flush=True)
        browser=auto_open(ticket['url']);rec['browserOpenIntent']=browser;save()
        print('BROWSER_OPEN_INTENT_SENT='+str(browser.get('intentSent',False)).upper(),flush=True)
        live={'schema':'obsidianti-mwni-export-parity-viewer-v1.4.8','runId':runid,'url':ticket['url'],
          'sourceCommit':commit,'buildToken':token,'launcherSHA256':launcher_sha,
          'servedModels':{k:{'sha256':v['sha256'],'reviewGate':v.get('reviewGate')} for k,v in models.items()},
          'browserRender':'UNVERIFIED','ownerAcceptance':'PENDING','canonicalModified':False}
        viewer_file=work_report/'VIEWER_RECEIPT.json';viewer_file.write_text(json.dumps(live,indent=2)+'\n')
        viewer_path=DIR+'/'+runid+'/VIEWER_RECEIPT.json'
        if (repo/viewer_path).exists():raise RuntimeError('VIEWER_EVIDENCE_COLLISION')
        safe_copy(viewer_file,repo/viewer_path)
        git(repo,'add','--',viewer_path)
        if set(g(repo,'diff','--cached','--name-only').splitlines())!={viewer_path}:raise RuntimeError('VIEWER_EVIDENCE_PATH_SCOPE_FAILED')
        git(repo,'commit','-m','Obsidianti: record export parity viewer URL with verified session identity')
        viewercommit=publish(repo,'VIEWER')
        if git(repo,'show','HEAD:'+viewer_path).stdout!=viewer_file.read_text():raise RuntimeError('VIEWER_REMOTE_READBACK_FAILED')
        if {p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}!=original:raise RuntimeError('CANONICAL_GIT_BLOBS_CHANGED_AFTER_VIEWER')
        rec['viewerEvidenceCommit']=viewercommit;rec['status']='GLB_EXPORT_PARITY_VIEWER_READY__OWNER_ACCEPTANCE_PENDING';save()
        print('VIEWER_RECEIPT_URL=https://github.com/Valar05/parametric-parambulator/blob/'+viewercommit+'/'+viewer_path,flush=True)
        print('CANONICAL_MODEL_UNCHANGED=YES',flush=True)
        print('STATUS='+rec['status'],flush=True)
    except Exception as ex:
        rec.update({'status':'BLOCKED','error':str(ex),'traceback':traceback.format_exc()[-5000:]});save()
        print('STATUS=BLOCKED '+str(ex),flush=True)
        raise
    finally:
        save();print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('Usage driver.py PACKET_ROOT LAUNCHER_PATH LAUNCHER_SHA256')
    main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve(),sys.argv[3])
