#!/usr/bin/env python3
"""Termux-only immutable Heavy1 saved-Blender side GIF capture and Git evidence."""
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time,uuid,traceback
from gif_writer import assemble
V='OBSIDIANTI_MWNI_HEAVY1_SIDE_GIF_v1.4.9'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE_COMMIT='20f57127429c59740b9f408cd0af196d8152aa15'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANONICAL='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
DONOR='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
HEAVY_BLEND='cb4ce023b885072ecbc5e58cb0a255bdbf20bcef56cf0bb787314778cb87514d'
HEAVY_RUN='20261106T172615Z-6d53cfaf'
SOURCE=pathlib.Path.home()/'.local/state'/'OBSIDIANTI_MWNI_RETARGET_PLUGIN_v1.4.0'/HEAVY_RUN/'work/Heavy1/MWNI_Heavy1_UNAPPROVED.blend'
RECOVERY='diagnostics/obsidianti/mwni-recovery-v1.4.3/RECOVERY_RECEIPT.json'
LOCKED=('assets/obsidianti/Obsidianti.glb','assets/repl/Repl.glb')
SRC={'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER', 'campaigns/'+V+'_driver.py':'driver.py',
     'campaigns/'+V+'_render.py':'render_heavy1.py', 'campaigns/'+V+'_gif.py':'gif_writer.py',
     'campaigns/'+V+'.contract.json':'contract.json', 'tests/'+V+'_TEST.py':'test_gif.py'}
OUTDIR='diagnostics/obsidianti/mwni-heavy1-sidegif-v1.4.9/runs'

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def command(args,timeout=240,env=None,check=True):
    p=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=timeout,env=env)
    if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+repr([str(x) for x in args][:8])+'\n'+p.stdout[-1300:]+'\n'+p.stderr[-1600:])
    return p

def git(repo,*args,timeout=240,check=True):return command(['git','-C',repo,*args],timeout=timeout,check=check)
def g(repo,*args):return git(repo,*args).stdout.strip()

def publish(repo,label):
    head=g(repo,'rev-parse','HEAD')
    for attempt in range(3):
        p=git(repo,'push','origin','HEAD:refs/heads/main',timeout=320,check=False)
        if p.returncode==0:break
        if attempt==2:raise RuntimeError('REMOTE_PUSH_FAILED_'+label+' '+p.stderr[-1700:])
        time.sleep(attempt+2)
    readback=git(repo,'ls-remote','origin','refs/heads/main',timeout=120).stdout.split()
    if not readback or readback[0]!=head:raise RuntimeError('REMOTE_HEAD_IDENTITY_MISMATCH_'+label)
    git(repo,'fetch','--quiet','origin','main',timeout=180)
    if g(repo,'rev-parse','refs/remotes/origin/main')!=head:raise RuntimeError('REMOTE_FETCH_IDENTITY_MISMATCH_'+label)
    return head

def checked_copy(src,dst):
    src=pathlib.Path(src);dst=pathlib.Path(dst)
    if dst.exists():
        if dst.is_file() and sha(dst)==sha(src):return
        raise RuntimeError('NO_OVERWRITE_DESTINATION_COLLISION '+str(dst))
    dst.parent.mkdir(parents=True,exist_ok=True)
    tmp=dst.with_name('.'+dst.name+'.'+uuid.uuid4().hex[:8]+'.tmp')
    try:
        shutil.copyfile(src,tmp)
        if sha(tmp)!=sha(src):raise RuntimeError('COPY_SHA_INVALID '+str(src))
        os.replace(tmp,dst)
    finally:
        if tmp.exists():tmp.unlink()

def preflight(repo_parent):
    repo=repo_parent/'repo'
    env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
    command(['git','clone','--quiet','--depth=1','--single-branch','--branch=main',REMOTE,repo],timeout=480,env=env)
    if g(repo,'remote','get-url','origin').removesuffix('.git')!=REMOTE.removesuffix('.git'):
        raise RuntimeError('WRONG_REPO_ORIGIN')
    head=g(repo,'rev-parse','HEAD')
    if head!=BASE_COMMIT and git(repo,'merge-base','--is-ancestor',BASE_COMMIT,'HEAD',check=False).returncode:
        git(repo,'fetch','--no-tags','--depth=100','origin',BASE_COMMIT,timeout=200)
        if git(repo,'merge-base','--is-ancestor',BASE_COMMIT,'HEAD',check=False).returncode:
            raise RuntimeError('REMOTE_MAIN_NOT_DESCENDANT_OF_PINNED_SOURCE_'+head)
    if g(repo,'rev-parse','HEAD:AGENTS.md')!=AGENTS_BLOB:
        raise RuntimeError('REPOSITORY_RULES_CHANGED')
    pointer=git(repo,'show','HEAD:assets/obsidianti/Obsidianti.glb').stdout
    if ('oid sha256:'+CANONICAL) not in pointer:raise RuntimeError('CANONICAL_ORIGINAL_IDENTITY_MISMATCH')
    recovery=json.loads((repo/RECOVERY).read_text())
    matches=[x for x in recovery['files'] if x['clip']=='Heavy1' and x['kind']=='editableBlend']
    if len(matches)!=1 or matches[0]['sha256Readback']!=HEAVY_BLEND:raise RuntimeError('RECOVERY_HEAVY_BLEND_SHA_NOT_CONFIRMED')
    if g(repo,'status','--porcelain'):raise RuntimeError('ISOLATED_CHECKOUT_DIRTY')
    return repo,head

def source_commit(repo,launcher,packet):
    files={p:launcher if source=='LAUNCHER' else packet/source for p,source in SRC.items()}
    if any((repo/p).exists() for p in files):raise RuntimeError('VERSIONED_GIT_SOURCE_PATH_COLLISION')
    for p,v in files.items():checked_copy(v,repo/p)
    git(repo,'add','--',*sorted(files))
    if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(files):raise RuntimeError('SOURCE_STAGE_ALLOWLIST_FAILED')
    if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Campaign')
    if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','obsidianti-campaign@users.noreply.github.com')
    git(repo,'commit','-m','Obsidianti: capture genuine Mwni Heavy1 saved Blender side-profile GIF')
    return publish(repo,'SOURCE')

def render_blender(packet,runroot):
    scene_file=SOURCE.resolve();out=runroot/'frames'
    script=runroot/'render_heavy1.py';checked_copy(packet/'render_heavy1.py',script)
    if shutil.which('proot-distro'):
        argv=['proot-distro','login','debian','--bind',str(scene_file.parent)+':/mnt/obs-heavy1-input',
              '--bind',str(runroot)+':/mnt/obs-heavy1-output','--','blender','--background',
              '--factory-startup','--python','/mnt/obs-heavy1-output/render_heavy1.py','--',
              '--blend','/mnt/obs-heavy1-input/'+scene_file.name,'--output','/mnt/obs-heavy1-output/frames']
    elif shutil.which('blender'):
        argv=['blender','--background','--factory-startup','--python',str(script),'--',
              '--blend',str(scene_file),'--output',str(out)]
    else:raise RuntimeError('BOTH_TERMUX_PROOT_AND_BLENDER_MISSING')
    result=command(argv,timeout=1800,check=False)
    (runroot/'BLENDER.log').write_text(result.stdout+'\n'+result.stderr)
    metadata=out/'RENDER.json'
    if not metadata.is_file():raise RuntimeError('BLENDER_NO_FRAME_RECEIPT '+result.stderr[-1000:])
    data=json.loads(metadata.read_text())
    if result.returncode or data.get('status')!='SIDE_PROFILE_FRAMES_RENDERED_FROM_SAVED_BLEND':
        raise RuntimeError('REAL_SAVED_BLEND_SIDE_RENDER_FAILED '+repr(data.get('error'))+' '+result.stderr[-600:])
    files=[out/name for name in data['frameFiles']]
    if len(files)!=24 or not all(f.is_file() and f.stat().st_size>50000 for f in files):
        raise RuntimeError('BLENDER_NOT_ALL_24_REAL_RENDER_FRAMES')
    return data,files

def main(packet,launcher,launcher_sha):
    packet=pathlib.Path(packet);launcher=pathlib.Path(launcher)
    files=json.loads((packet/'manifest.json').read_text())
    expected={'driver.py','render_heavy1.py','gif_writer.py','test_gif.py','contract.json'}
    if set(files)!=expected:raise RuntimeError('PAYLOAD_MANIFEST_MEMBER_SET_INVALID')
    for path,digest in files.items():
        if sha(packet/path)!=digest:raise RuntimeError('PAYLOAD_MEMBER_HASH_MISMATCH '+path)
    contract=json.loads((packet/'contract.json').read_text())
    if contract['sourceMutablePaths']!=sorted(SRC) or contract['sourceBlendSHA256']!=HEAVY_BLEND or contract['authority']!='TERMUX_GIT_ONLY':
        raise RuntimeError('CONTRACT_LOCK_MISMATCH')
    command(['python3','-m','py_compile',*[packet/p for p in ('driver.py','render_heavy1.py','gif_writer.py','test_gif.py')]])
    command(['python3',packet/'test_gif.py'],timeout=90)
    if not SOURCE.is_file() or SOURCE.is_symlink() or SOURCE.stat().st_size!=26758008 or sha(SOURCE)!=HEAVY_BLEND:
        raise RuntimeError('EXACT_REAL_HEAVY1_EDITABLE_BLENDER_FILE_MISSING_OR_SHA_MISMATCH '+str(SOURCE))
    downloads=pathlib.Path.home()/'storage/downloads'
    if not downloads.is_dir():raise RuntimeError('ANDROID_DOWNLOADS_UNAVAILABLE')
    runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
    receipt=root/'RECEIPT.json';rec={'campaign':V,'runId':runid,'launcherSHA256':launcher_sha,'authority':'TERMUX_GIT_ONLY',
        'sourceBlendSHA256':HEAVY_BLEND,'canonicalModelSHA256':CANONICAL,'agentsBlob':AGENTS_BLOB,
        'campaignEtiquetteRead':'2026-11-06 live','status':'BOOT','canonicalModified':False}
    def save():
        tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(rec,indent=2)+'\n');os.replace(tmp,receipt)
    save()
    try:
        repo,head=preflight(root);rec['inputGitHEAD']=head
        original={p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}
        rec['protectedBlobBefore']=original
        sourcecommit=source_commit(repo,launcher,packet);rec['sourceCommit']=sourcecommit;rec['status']='SOURCE_REMOTE_VERIFIED';save()
        render,frames=render_blender(packet,root)
        gif=root/'HEAVY1_MWNI_BAKED_SIDE.gif';gif_info=assemble(frames,gif)
        if gif_info['frames']!=24 or gif_info['width']!=512 or gif_info['height']!=512:raise RuntimeError('GIF_FRAME_SIZE_OR_COUNT_WRONG')
        rec['gif']=gif_info;rec['status']='ACTUAL_BLENDER_FRAMES_GIF_CREATED_PENDING_GIT';save()
        output=root/'evidence';output.mkdir()
        md=output/'REPORT.md';js=output/'RENDER_EVIDENCE.json';raw=output/gif.name
        checked_copy(gif,raw)
        differences=len({sha(f) for f in frames})
        leg_movement=max((render['maxJointExcursionsDeg'].get(p,0) for p in ('LeftUpLeg','LeftLeg','RightUpLeg','RightLeg')),default=0)
        rec['renderDistinctFrameHashes']=differences
        rec['legJointExcursionMaxDeg']=leg_movement
        ev={'schema':'obsidianti-mwni-heavy1-saved-blend-gif-v1.4.9','runId':runid,
            'sourceCommit':sourcecommit,'sourceBlendSHA256':HEAVY_BLEND,'originalDonorBlendSHA256':DONOR,
            'canonicalGLBSHA256':CANONICAL,'originalGLBNotUsed':True,'retargetRerun':False,
            'gif':gif_info,'distinctFrameHashes':differences,'render':render,
            'ownerVisualAcceptance':'PENDING','canonicalModelModified':False}
        js.write_text(json.dumps(ev,indent=2)+'\n')
        md.write_text('# Obsidianti Heavy1 actual saved Blender side-profile GIF\n\n'+
            'Source: exactly SHA-verified v1.4.0 saved Mwni Heavy1 .blend, **not the static exported GLB**.\n\n'+
            'Render: Blender 4.3.2 actual skinned mesh, fixed side-on camera along +X, constant Z=0 floor, 24 frames.\n'+
            'No retarget solver or exporter run. Camera and output do not alter any model asset.\n\n'+
            'Distinct rendered frame hashes: '+str(differences)+' of 24.\n'+
            'Maximum recorded local leg-bone rotation: '+str(leg_movement)+' degrees.\n'+
            'GIF SHA256: '+gif_info['sha256']+'.\n\nOwner visual acceptance: PENDING.\n')
        destinations={OUTDIR+'/'+runid+'/'+p.name:p for p in (md,js,raw)}
        if any((repo/p).exists() for p in destinations):raise RuntimeError('GIF_GIT_EVIDENCE_PATH_COLLISION')
        for p,f in destinations.items():checked_copy(f,repo/p)
        git(repo,'add','--',*sorted(destinations))
        if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(destinations):
            raise RuntimeError('GIF_EVIDENCE_STAGE_ALLOWLIST_FAILED')
        git(repo,'commit','-m','Obsidianti: publish real Blender-rendered Heavy1 side GIF and frame evidence')
        published=publish(repo,'GIF_EVIDENCE')
        if {p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}!=original:raise RuntimeError('PROTECTED_CANONICAL_GIT_BLOBS_CHANGED')
        for path,f in destinations.items():
            if path.endswith('.gif'):
                # Verify the committed bytes directly, not the file name or LFS-pointer size.
                blob=subprocess.run(['git','-C',str(repo),'cat-file','blob','HEAD:'+path],
                                    capture_output=True,timeout=180,check=True).stdout
                if hashlib.sha256(blob).hexdigest()!=sha(f):
                    raise RuntimeError('GIT_GIF_BLOB_SHA_MISMATCH')
            elif git(repo,'show','HEAD:'+path).stdout!=f.read_text():
                raise RuntimeError('REMOTE_REPORT_OR_EVIDENCE_MISMATCH '+path)
        for f in (gif,md,js):
            dest=downloads/(V+'_'+runid+'_'+f.name);checked_copy(f,dest)
            print('DOWNLOAD_OUTPUT='+str(dest)+' SHA256='+sha(dest),flush=True)
        url='https://raw.githubusercontent.com/Valar05/parametric-parambulator/'+published+'/'+OUTDIR+'/'+runid+'/'+gif.name
        rec.update({'status':'ACTUAL_HEAVY1_BLENDER_SIDE_GIF_GIT_REMOTE_VERIFIED_OWNER_REVIEW_PENDING',
            'gifGitCommit':published,'gifURL':url,'protectedBlobAfter':{p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}});save()
        print('GIF_URL='+url,flush=True)
        print('REPORT_URL=https://github.com/Valar05/parametric-parambulator/blob/'+published+'/'+OUTDIR+'/'+runid+'/REPORT.md',flush=True)
        print('HEAVY1_ACTUAL_BLENDER_SAVED_ACTION='+render['action'],flush=True)
        print('GIF_REAL_FRAMES=24 DISTINCT='+str(differences)+' LEG_MAX_DEG='+str(leg_movement),flush=True)
        print('CANONICAL_MODEL_UNCHANGED=YES',flush=True)
        print('STATUS='+rec['status'],flush=True)
        print('RECEIPT='+str(receipt),flush=True)
    except Exception as exc:
        rec.update({'status':'BLOCKED_'+type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc()[-5000:]});save();raise

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('USAGE driver.py packet launcher launcherSHA')
    main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve(),sys.argv[3])
