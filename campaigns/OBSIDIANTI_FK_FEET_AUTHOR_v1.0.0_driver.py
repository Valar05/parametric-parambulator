#!/usr/bin/env python3
"""One-invocation Termux Git source+Blender delivery for FK-foot authoring."""
import os,sys,subprocess,hashlib,json,pathlib,tempfile,shutil,datetime,traceback,time
V='OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
SOURCE='diagnostics/obsidianti/animation-reunion-v2.0.32/runs/20261107T203838Z-d49615bb/OBSIDIANTI_41_CLIP_SHIELD_LANCE_LIONHEART_ARP_REVIEW_UNAPPROVED.glb'
SOURCE_SHA='9ff2b5423b4bf5fea1bf67295b52d848803381699fede56164aca9ce65bea9b7'
OUT='assets/obsidianti/source/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_UNAPPROVED.blend'
DOC='docs/obsidianti/PRODUCTION_ARCHAEOLOGY_AND_FK_FEET_2026-11-08.md'
FILES={
'campaigns/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_driver.py':'driver.py',
'campaigns/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_blender_author.py':'author.py',
'campaigns/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_blender_verify.py':'verify.py',
DOC:'ARCHAEOLOGY.md'
}
PK=pathlib.Path(__file__).resolve().parent
D=pathlib.Path.home()/'storage'/'downloads'
RUN=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid())
STATE=pathlib.Path.home()/'.local'/'state'/V/RUN
STATE.mkdir(parents=True,exist_ok=False)
receipt=STATE/'RECEIPT.json'
r={'campaign':V,'run':RUN,'stage':'BOOT','status':'STARTED','source':SOURCE,'sourceSHA256':SOURCE_SHA,
   'rulesAGENTSblob':AGENTS_BLOB,'rulesCampaignEtiquette':'Home Center document 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI read in commissioning turn',
   'lane':'ISOLATED_TERMUX_GIT_ONLY','ownerVisualAcceptance':'PENDING'}
def save():
    receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
def stage(n):
    r['stage']=n;save();print('STAGE='+n,flush=True)
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def require(cond,msg):
    if not cond:raise RuntimeError(msg)
def call(argv,timeout=420,env=None,check=True):
    p=subprocess.run([str(x) for x in argv],text=True,errors='replace',capture_output=True,
                     timeout=timeout,stdin=subprocess.DEVNULL,env=env)
    if check and p.returncode:raise RuntimeError('COMMAND_FAILED_'+repr(argv)+'\n'+p.stderr[-1100:]+'\n'+p.stdout[-700:])
    return p
def git(root,*args,timeout=420,check=True):return call(['git','-C',root,*args],timeout=timeout,check=check)
def assert_clean(root):require(not git(root,'status','--porcelain').stdout.strip(),'DIRTY_ISOLATED_REPO')
def push_verify(root):
    head=git(root,'rev-parse','HEAD').stdout.strip()
    for attempt in range(3):
        p=git(root,'push','origin','HEAD:refs/heads/main',timeout=600,check=False)
        if p.returncode==0:break
        if attempt==2:raise RuntimeError('GIT_PUSH_FAILED_'+p.stderr[-1100:])
        time.sleep(2*(attempt+1))
    remote=call(['git','ls-remote',REMOTE,'refs/heads/main']).stdout.split()[0]
    require(remote==head,'REMOTE_READBACK_HEAD_MISMATCH_'+head+'_'+remote)
    r['verifiedRemoteHEAD']=head;save()
    return head

def blender_args(root,work,script,params):
    native=shutil.which('blender')
    if native:return [native,'--background','--factory-startup','--disable-autoexec','--python',str(root/script),'--',*map(str,params)]
    pd=shutil.which('proot-distro')
    require(pd,'BLENDER_NOT_INSTALLED_NATIVE_OR_PROOT')
    for distro in ('obs-arp-blender50','debian'):
        probe=call([pd,'login',distro,'--','blender','--version'],timeout=50,check=False)
        if probe.returncode==0:
            def map_path(p):
                p=pathlib.Path(p).resolve()
                if p.is_relative_to(root.resolve()):return '/mnt/obs-repo/'+str(p.relative_to(root.resolve()))
                if p.is_relative_to(work.resolve()):return '/mnt/obs-work/'+str(p.relative_to(work.resolve()))
                raise RuntimeError('UNMAPPED_PROOT_PATH_'+str(p))
            return [pd,'login',distro,'--bind',str(root.resolve())+':/mnt/obs-repo',
                    '--bind',str(work.resolve())+':/mnt/obs-work','--',
                    'blender','--background','--factory-startup','--disable-autoexec','--python',map_path(root/script),'--',
                    *[map_path(p) for p in params]]
    raise RuntimeError('BLENDER_NOT_AVAILABLE_PROOT_DISTRIBUTIONS')

try:
    save()
    require(shutil.which('git') and shutil.which('python3'),'TERMUX_GIT_PYTHON3_REQUIRED')
    require(shutil.which('git-lfs') or call(['git','lfs','version'],check=False).returncode==0,'GIT_LFS_REQUIRED')
    stage('VALIDATE_BUNDLED_SOURCES')
    for dest,src in FILES.items():
        f=PK/src
        require(f.is_file() and f.stat().st_size>100,'MISSING_PACKET_MEMBER_'+src)
    for src in ('author.py','verify.py','driver.py'):
        compile((PK/src).read_text(),src,'exec')
    D.mkdir(parents=True,exist_ok=True)
    root=STATE/'repo'
    stage('ISOLATED_GIT_CHECKOUT')
    env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1'
    p=call(['git','clone','--depth','1','--single-branch','--branch','main','--filter=blob:none',REMOTE,str(root)],timeout=600,env=env,check=False)
    if p.returncode:
        # Only this freshly created disposable run directory may be cleared.
        if root.exists():shutil.rmtree(root)
        p=call(['git','clone','--depth','1','--single-branch','--branch','main',REMOTE,str(root)],timeout=600,env=env)
    assert_clean(root)
    source_head=git(root,'rev-parse','HEAD').stdout.strip();r['sourceHEAD']=source_head
    require(git(root,'rev-parse','HEAD:AGENTS.md').stdout.strip()==AGENTS_BLOB,'AGENTS_CHANGED_READ_RULES_AGAIN')
    r['rulesReadAGENTSsha']=AGENTS_BLOB
    stage('DESTINATION_COLLISION_GATE')
    for target in [*FILES,OUT]:
        require(not (root/target).exists(),'DESTINATION_EXISTS_'+target)
        require(git(root,'cat-file','-e','HEAD:'+target,check=False).returncode!=0,'DESTINATION_ALREADY_TRACKED_'+target)
    stage('PUBLISH_POLICY_AND_RIG_SOURCE_BY_TERMUX_GIT')
    for dest,src in FILES.items():
        f=root/dest;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PK/src,f)
    git(root,'add','--',*FILES)
    git(root,'commit','-m',V+': document Sword1 shelf and FK feet Blender source')
    first=push_verify(root);r['sourcePublicationHEAD']=first
    # Source publication is not a native Blender deliverable.
    stage('HYDRATE_EXACT_41_CLIP_LFS')
    r['glbInput']='UNVERIFIED';save()
    p=git(root,'lfs','pull','--include='+SOURCE,'--exclude=',timeout=1200,check=False)
    require(p.returncode==0,'LFS_INPUT_FETCH_FAILED_'+p.stderr[-900:])
    model=root/SOURCE
    require(model.is_file() and sha(model)==SOURCE_SHA,'SOURCE_GLB_SHA_OR_HYDRATION_MISMATCH')
    r['glbInput']='VERIFIED';save()
    stage('BLENDER_NATIVE_FK_FEET_BUILD')
    outfile=STATE/pathlib.Path(OUT).name; audit=STATE/'BLENDER_BUILD.json'; verify=STATE/'BLENDER_VERIFY.json'
    command=blender_args(root,STATE,root/'campaigns/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_blender_author.py',[model,outfile,audit])
    p=call(command,timeout=2400,check=False)
    (STATE/'BLENDER_BUILD.log').write_text(p.stdout+'\n'+p.stderr)
    require(p.returncode==0 and outfile.is_file(),'BLENDER_AUTHOR_FAILED_'+p.stdout[-650:]+p.stderr[-1150:])
    a=json.loads(audit.read_text());require(a['status']=='BLENDER_SAVED_UNAPPROVED' and a['outputSHA256']==sha(outfile),'BLENDER_BUILD_RECEIPT_INVALID')
    stage('INDEPENDENT_BLENDER_REOPEN_VERIFY')
    command=blender_args(root,STATE,root/'campaigns/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_blender_verify.py',[outfile,audit,verify])
    p=call(command,timeout=900,check=False)
    (STATE/'BLENDER_VERIFY.log').write_text(p.stdout+'\n'+p.stderr)
    require(p.returncode==0 and verify.is_file(),'INDEPENDENT_REOPEN_FAILED_'+p.stdout[-650:]+p.stderr[-1150:])
    require(json.loads(verify.read_text())['status']=='REOPENED_FK_FEET_VERIFIED','REOPEN_NOT_VERIFIED')
    stage('PUBLISH_VERSIONED_BLEND_TERMUX_GIT_LFS')
    target=root/OUT;target.parent.mkdir(parents=True,exist_ok=True)
    require(not target.exists(),'OUTPUT_DEST_COLLISION')
    require(git(root,'check-attr','filter','--',OUT).stdout.strip().endswith(': lfs'),'BLEND_LFS_ATTRIBUTE_MISSING')
    shutil.copyfile(outfile,target)
    git(root,'add','--',OUT)
    staged=git(root,'show',':'+OUT).stdout if False else git(root,'show',':'+OUT,check=False)
    # git show of staged LFS pointer must be pointer text, not huge binary
    require(staged.returncode==0 and ('oid sha256:'+sha(outfile)) in staged.stdout,'LFS_POINTER_STAGE_FAILED')
    git(root,'commit','-m',V+': independent FK-foot Blender authoring copy, unapproved')
    second=push_verify(root);r['blendPublicationHEAD']=second
    remote_pointer=git(root,'show','origin/main:'+OUT).stdout
    require('oid sha256:'+sha(outfile) in remote_pointer,'REMOTE_LFS_POINTER_MISMATCH')
    stage('PUBLISH_DOWNLOADS_AND_RECEIPTS')
    dest=D/outfile.name
    require(not dest.exists(),'ANDROID_DOWNLOAD_COLLISION_'+dest.name)
    shutil.copyfile(outfile,dest)
    require(sha(dest)==sha(outfile),'ANDROID_DOWNLOAD_READBACK_SHA_MISMATCH')
    r.update(status='BLENDER_FK_FEET_SAVED_AND_GIT_VERIFIED_VISUAL_PENDING',blendSHA256=sha(outfile),downloadPath=str(dest),
             sourceModelSHA256=SOURCE_SHA,originalClipCount=41,ownerVisualAcceptance='PENDING',stage='COMPLETE')
    save()
    copyreceipt=D/(V+'_'+RUN+'_RECEIPT.json')
    shutil.copyfile(receipt,copyreceipt)
    print('STATUS='+r['status']+'\nDOWNLOAD='+str(dest)+'\nSHA256='+r['blendSHA256']+'\nRECEIPT='+str(copyreceipt),flush=True)
except BaseException as exc:
    r.update(status='BLOCKED',error=str(exc),traceback=traceback.format_exc())
    save()
    try:
        D.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(receipt,D/(V+'_'+RUN+'_BLOCKED_RECEIPT.json'))
    except Exception:pass
    print('STATUS=BLOCKED '+str(exc)+'\nRECEIPT='+str(receipt),flush=True)
    sys.exit(1)
