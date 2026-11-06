#!/usr/bin/env python3
"""One Termux Git campaign to ACTUALLY serve and open the two real Mwni GLBs."""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,struct,subprocess,sys,time,traceback,urllib.request,uuid

V='OBSIDIANTI_MWNI_VIEWER_v1.4.4'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_COMMIT='45ee7b2fc7b06a66bfce17ebf7687e300666eabc'
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
     'campaigns/'+V+'_viewer.html':'viewer.html',
     'campaigns/'+V+'.contract.json':'contract.json',
     'tests/'+V+'_TEST.py':'test_driver.py'}
DIR='diagnostics/obsidianti/mwni-viewer-v1.4.4/runs'

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
    expected={'driver.py','server.py','viewer.html','contract.json','test_driver.py'}
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
    git(repo,'commit','-m','Obsidianti: publish SHA-locked Mwni GLB interactive review viewer')
    return publish(repo,'SOURCE')

def find_real_files(receipt,downloads):
    models={};paths={}
    for row in receipt['files']:
        if row['kind']!='candidateGLB':continue
        clip=row['clip'];key='candidate'+clip
        p=pathlib.Path(row['androidSharedPath']);original=downloads/p.name
        if str(p)!=str(original):raise RuntimeError('RECOVERY_RECEIPT_PATH_OUTSIDE_AUTHORIZED_DOWNLOADS '+str(p))
        if not p.name.startswith('OBSIDIANTI_MWNI_REVIEW_RECOVERY_v1.4.3_'):
            raise RuntimeError('RECOVERY_FILE_NAME_NOT_PINNED '+p.name)
        info=validate_glb(p,row['sha256Readback'],row['bytes'])
        if row['sha256Readback']!=row['priorSHA256']:raise RuntimeError('REVIEW_SHA_NOT_AUTHORITATIVE '+clip)
        info.update({'url':'/models/'+key+'.glb','clip':clip,'role':'Mwni IK candidate (unapproved)'})
        paths[key]=str(p);models[key]=info
        print('VIEWER_MODEL_VERIFIED='+clip+' SHA256='+info['sha256']+' ANIMATIONS='+repr(info['animations']),flush=True)
    if set(models)!={'candidateHeavy1','candidateLight2'}:raise RuntimeError('INCOMPLETE_CANDIDATE_SET')
    return models,paths

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

def main(packet,launcher,launcher_sha):
    downloads=pathlib.Path.home()/'storage/downloads'
    if not downloads.is_dir():raise RuntimeError('ANDROID_SHARED_DOWNLOADS_NOT_PRESENT')
    runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    runroot=pathlib.Path.home()/'.local/state'/V/runid;runroot.mkdir(parents=True,exist_ok=False)
    receiptfile=runroot/'RECEIPT.json'
    receipt={'campaign':V,'runId':runid,'status':'STARTED','authority':'TERMUX_GIT_ONLY',
        'launcherSHA256':launcher_sha,'canonicalModelModified':False,'reviewFilesModified':False,
        'agentsBlobVerified':AGENTS_BLOB,'etiquetteReadByAuthor':'2026-11-06 live'}
    def save():
        tmp=receiptfile.with_suffix('.tmp');tmp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n');os.replace(tmp,receiptfile)
    save()
    try:
        receipt['manifestSHA256']=packet_guard(packet)
        cmd(['python3','-m','py_compile',str(packet/'driver.py'),str(packet/'server.py'),str(packet/'test_driver.py')])
        cmd(['python3',str(packet/'test_driver.py')],timeout=50)
        contract=json.loads((packet/'contract.json').read_text())
        if set(contract['sourceMutablePaths'])!=set(SRC):raise RuntimeError('SOURCE_WRITE_CONTRACT_INVALID')
        repo,head,old=repo_preflight(runroot);receipt['remoteInputHead']=head
        originals={path:g(repo,'rev-parse','HEAD:'+path) for path in LOCKED}
        receipt['protectedModelGitBlobsBefore']=originals
        srccommit=source_commit(repo,launcher,packet)
        receipt['sourceCommit']=srccommit;receipt['status']='SOURCE_COMMITTED_REMOTE_VERIFIED';save()
        models,paths=find_real_files(old,downloads)
        receipt['optionalOriginalStatus']=optional_original(repo,models,paths)
        # Only the repo committed viewer source and the exact output files are served.
        token=hashlib.sha256((runid+srccommit+launcher_sha+''.join(sorted(x['sha256'] for x in models.values()))).encode()).hexdigest()[:24]
        manifest={'schema':'obsidianti-mwni-viewer-v1.4.4','runId':runid,'buildToken':token,
            'launcherSHA256':launcher_sha,'sourceCommit':srccommit,'originalInputHead':head,
            'modelPaths':paths,'models':models,'htmlPath':str(repo/('campaigns/'+V+'_viewer.html')),
            'mode':'EXACT_UNAPPROVED_GLBS_READ_ONLY', 'canonicalModelSHA256':CANONICAL_SHA}
        receipt['viewerBuildToken']=token
        ticket,serverlog=start_viewer(repo,runroot,manifest)
        receipt['viewerURL']=ticket['url'];receipt['serverPid']=ticket['pid'];receipt['serverPort']=ticket['port']
        receipt['status']='VIEWER_HTTP_AND_REAL_MODEL_HEADERS_VERIFIED_BROWSER_REVIEW_PENDING';save()
        # Show URL as soon as HTTP is actually verified, even if later Git publication is unavailable.
        print('VIEWER_URL='+ticket['url'],flush=True)
        print('VIEWER_PID='+str(ticket['pid'])+' PORT='+str(ticket['port']),flush=True)
        print('VIEWER_MODE=ACTUAL_GLBS_WITH_SHA256_IN_BROWSER',flush=True)
        browser=auto_open(ticket['url']);receipt['browserLaunch']=browser;save()
        print('BROWSER_OPEN_INTENT_SENT='+str(browser['intentSent']).upper(),flush=True)
        # Evidence is published by the authorized Termux Git lane only.
        reportdir=runroot/'evidence';reportdir.mkdir()
        evidence={
            'schema':'obsidianti-mwni-live-viewer-v1.4.4','status':'VIEWER_HTTP_VERIFIED__BROWSER_RENDER_UNVERIFIED',
            'runId':runid,'url':ticket['url'],'serverPid':ticket['pid'],'serverPort':ticket['port'],
            'sourceCommit':srccommit,'inputHead':head,'launcherSHA256':launcher_sha,'buildToken':token,
            'models':{k:{z:v[z] for z in ('sha256','bytes','animations','meshes','skins')} for k,v in models.items()},
            'originalStatus':receipt['optionalOriginalStatus'],'browserLaunch':browser,
            'rulesRead':{'agentsBlob':AGENTS_BLOB,'campaignEtiquette':'2026-11-06 live'},
            'protectedBlobsBefore':originals,'protectedBlobsAfter':{x:g(repo,'rev-parse','HEAD:'+x) for x in LOCKED},
            'canonicalModelModified':False,'candidateModelModified':False,
            'HTTPValidation':['run identity','build token','live server pid','exact viewer HTML hash','cache-control headers','model content-length and claimed SHA headers'],
            'actualBrowserModelShaVerification':'REQUIRED_BY_VIEWER_CODE_NOT_YET_CONFIRMED','ownerVisualVerdict':'PENDING'}
        if evidence['protectedBlobsBefore']!=evidence['protectedBlobsAfter']:raise RuntimeError('PROTECTED_MODELS_CHANGED')
        lines=['# Obsidianti Mwni interactive 3D viewer v1.4.4','',
            '**HTTP server tested and real GLB bytes SHA-checked on-device. Browser visual approval is pending.**','',
            '- Browser URL on the SAME PHONE: `'+ticket['url']+'`',
            '- Source commit: `'+srccommit+'`',
            '- Browser: orbit/pinch, play/pause, replay, seek, speed, camera presets, Heavy1/Light2 switching.',
            '- On browser load, a fresh SHA-256 digest verifies the entire selected GLB before displaying animation.',
            '- Optional canonical comparison: '+receipt['optionalOriginalStatus'],
            '- This is the exact Mwni result from v1.4.0/recovered v1.4.3, not a new retarget run.',
            '- No model files have been changed or promoted; do not equate HTTP check with browser rendering.',
            '', '| Model | SHA-256 | Animations |','|---|---|---|']
        for key,item in models.items():lines.append('| '+key+' | `'+item['sha256']+'` | '+', '.join(item['animations'])+' |')
        reportdir.joinpath('VIEWER_REPORT.md').write_text('\n'.join(lines)+'\n')
        evidence['reportSHA256']=sha(reportdir/'VIEWER_REPORT.md')
        reportdir.joinpath('VIEWER_RECEIPT.json').write_text(json.dumps(evidence,indent=2)+'\n')
        files={DIR+'/'+runid+'/VIEWER_REPORT.md':reportdir/'VIEWER_REPORT.md',
            DIR+'/'+runid+'/VIEWER_RECEIPT.json':reportdir/'VIEWER_RECEIPT.json'}
        if any((repo/path).exists() for path in files):raise RuntimeError('UNIQUE_RUN_EVIDENCE_PATH_COLLISION')
        for dst,source in files.items():safe_copy(source,repo/dst)
        git(repo,'add','--',*sorted(files));staged=set(g(repo,'diff','--cached','--name-only').splitlines())
        if staged!=set(files):raise RuntimeError('EVIDENCE_STAGING_ALLOWLIST_MISMATCH')
        git(repo,'commit','-m','Obsidianti: publish actual SHA-verified Mwni viewer session and browser URL')
        evidencecommit=publish(repo,'EVIDENCE')
        receipt['evidenceCommit']=evidencecommit
        for path,source in files.items():
            if git(repo,'show','HEAD:'+path).stdout!=source.read_text():raise RuntimeError('EVIDENCE_GIT_READBACK_BYTES_CHANGED '+path)
        if {x:g(repo,'rev-parse','HEAD:'+x) for x in LOCKED}!=originals:raise RuntimeError('CANONICAL_ASSET_GIT_TREE_CHANGED')
        receipt.update({'status':'VIEWER_HTTP_VERIFIED_GIT_REMOTE_READBACK_OWNER_VISUAL_PENDING','protectedModelGitBlobsAfter':originals});save()
        for item in files.values():
            dest=downloads/(V+'_'+runid+'_'+item.name);safe_copy(item,dest)
            print('DOWNLOAD_EVIDENCE='+str(dest),flush=True)
        print('SOURCE_COMMIT='+srccommit,flush=True)
        print('RESEARCH_COMMIT='+evidencecommit,flush=True)
        print('REPORT_URL=https://github.com/Valar05/parametric-parambulator/blob/'+evidencecommit+'/'+DIR+'/'+runid+'/VIEWER_REPORT.md',flush=True)
        print('CANONICAL_MODEL_UNCHANGED=YES',flush=True)
        print('STATUS='+receipt['status'],flush=True)
    except Exception as error:
        receipt.update({'status':'BLOCKED','error':str(error),'traceback':traceback.format_exc()[-4000:]});save()
        if receipt.get('viewerURL'):
            print('VIEWER_URL='+receipt['viewerURL']+' (HTTP verified, later stage blocked)',flush=True)
        print('STATUS=BLOCKED '+str(error),flush=True)
        raise
    finally:
        save();print('RECEIPT='+str(receiptfile),flush=True)

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('usage: driver.py PACKET_ROOT LAUNCHER_PATH LAUNCHER_SHA256')
    main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve(),sys.argv[3])
