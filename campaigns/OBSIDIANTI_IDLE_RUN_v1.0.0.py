#!/usr/bin/env python3
"""Termux Git-only, single-canonical-GLB import of Obsidianti's Idle candidate.

Invoked by the versioned .sh entrypoint. The attached ZIP is data ingress,
not proof of repository delivery or visual acceptance.
"""
from __future__ import annotations
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
import uuid

VERSION='OBSIDIANTI_IDLE_CANONICAL_v1.0.0'
REPO='Valar05/parametric-parambulator'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
MODEL='assets/obsidianti/Obsidianti.glb'
SOURCE='assets/obsidianti/source/'
SCRIPT='campaigns/OBSIDIANTI_IDLE_CANONICAL_v1.0.0.sh'
RUNNER='campaigns/OBSIDIANTI_IDLE_RUN_v1.0.0.py'
GUARD='campaigns/OBSIDIANTI_IDLE_VERIFY_v1_0_0.py'
MANIFEST='campaigns/OBSIDIANTI_IDLE_PACKET_MANIFEST_v1.0.0.json'
DOC='docs/obsidianti/IDLE_TRANSFER_v1.0.0.md'
VIEW='review/obsidianti.html'
EXPECTED_GLB_SHA='27f943ddf1ba1f72169026a2cb4750662f00b053f78e4346f43b3888c744e95b'
SRC_MAPPINGS={
 SCRIPT:'campaigns/OBSIDIANTI_IDLE_CANONICAL_v1.0.0.sh',
 RUNNER:'campaigns/OBSIDIANTI_IDLE_RUN_v1.0.0.py',
 GUARD:'campaigns/OBSIDIANTI_IDLE_VERIFY_v1_0_0.py',
 DOC:'docs/obsidianti/IDLE_TRANSFER_v1.0.0.md',
 VIEW:'review/obsidianti.html',
 SOURCE+'Obsidianti.blend':'payload/Obsidianti.blend',
 SOURCE+'LionheartLancer.blend':'payload/LionheartLancer.blend',
}
ALL_MUTABLE=set(SRC_MAPPINGS)|{MANIFEST,MODEL}

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as fp:
        for chunk in iter(lambda:fp.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def run(args,cwd=None,timeout=120,env=None,check=True):
    cp=subprocess.run(args,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if check and cp.returncode:
        raise RuntimeError(f'COMMAND_FAILED exit={cp.returncode} argv={args!r} stderr={cp.stderr[-1700:]} stdout={cp.stdout[-700:]}')
    return cp

def git(args,repo,timeout=120,check=True):
    return run(['git','-C',str(repo),*args],timeout=timeout,check=check)

def git_blob(repo,path):
    cp=subprocess.run(['git','-C',str(repo),'show',f'HEAD:{path}'],
                      stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
    if cp.returncode:return None
    return cp.stdout

def tracked_sha(repo,path):
    # LFS objects stored by pointer; source payload is validated by SHA separately.
    data=git_blob(repo,path)
    if data is None:return None
    txt=data.decode('utf-8','replace')
    if txt.startswith('version https://git-lfs.github.com/spec/v1'):
        for line in txt.splitlines():
            if line.startswith('oid sha256:'):
                return line[len('oid sha256:'):].strip()
        raise RuntimeError(f'LFS_POINTER_MALFORMED {path}')
    return hashlib.sha256(data).hexdigest()

def preflight_packet(packet):
    sys.path.insert(0,str(packet/'campaigns'))
    from OBSIDIANTI_IDLE_VERIFY_v1_0_0 import verify_packet
    return verify_packet(packet)

def check_scoped_status(repo):
    cp=git(['status','--porcelain=v1','--untracked-files=all'],repo)
    names=[]
    for row in cp.stdout.splitlines():
        if row:
            names.append(row[3:])
    bad=[n for n in names if n not in ALL_MUTABLE]
    if bad:
        raise RuntimeError('UNAUTHORIZED_WORKTREE_DIFF '+str(bad[:20]))
    return names

def read_rules(repo):
    text=(repo/'AGENTS.md').read_text()
    if not text.startswith('# AGENTS.md') or 'Termux Git only' not in text:
        raise RuntimeError('RULES_READ_BLOCKED: repo AGENTS.md identity missing or policy changed')
    return digest(repo/'AGENTS.md')

def ensure_lfs(test_mode):
    if test_mode:return 'TEST_FIXTURE_NO_LFS'
    if run(['git','lfs','version'],check=False).returncode:
        pkg=shutil.which('pkg')
        if not pkg:
            raise RuntimeError('GIT_LFS_UNAVAILABLE: git-lfs missing and Termux pkg is unavailable')
        run([pkg,'install','-y','git-lfs'],timeout=180)
    if run(['git','lfs','version'],check=False).returncode:
        raise RuntimeError('GIT_LFS_UNAVAILABLE after package installation')
    return run(['git','lfs','version']).stdout.strip()

def repo_identity(repo):
    name=git(['config','--get','user.name'],repo,check=False).stdout.strip()
    email=git(['config','--get','user.email'],repo,check=False).stdout.strip()
    if name and email:
        return 'USER_GIT_IDENTITY'
    # Keep the owner uninvolved in busywork. Explicit campaign-bot author,
    # never impersonation, and use existing user's configured identity if present.
    git(['config','user.name','Obsidianti Termux Campaign'],repo)
    git(['config','user.email','obsidianti-campaign@users.noreply.github.com'],repo)
    return 'CAMPAIGN_BOT_FALLBACK'

def current_sha(repo):
    return git(['rev-parse','HEAD'],repo).stdout.strip()

def verify_stage(repo,allowed):
    changed=git(['diff','--cached','--name-only'],repo).stdout.splitlines()
    bad=[p for p in changed if p not in allowed]
    if bad:raise RuntimeError('GIT_SCOPE_VIOLATION '+str(bad))
    return changed

def commit_files(repo,paths,message,test_mode):
    if not paths:return None
    git(['add','--',*paths],repo)
    changed=verify_stage(repo,set(paths))
    if not changed:return None
    if not test_mode:
        for p in changed:
            if pathlib.Path(p).suffix not in ('.blend','.glb'): continue
            attr=git(['check-attr','filter','--',p],repo).stdout
            if not attr.rstrip().endswith(': lfs'):
                raise RuntimeError('LFS_NOT_ENFORCED_FOR_BINARY '+p+' '+attr)
            index=git(['show',':'+p],repo).stdout
            if not index.startswith('version https://git-lfs.github.com/spec/v1'):
                raise RuntimeError('LFS_POINTER_MISSING '+p)
    git(['commit','-m',message],repo,timeout=160)
    return current_sha(repo)

def record_receipt(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    temp.replace(path)

def main():
    if len(sys.argv)!=2:
        raise RuntimeError('EXPECTED_USAGE: run.sh /absolute/verified/unpacked/packet')
    packet=pathlib.Path(sys.argv[1]).resolve()
    if not packet.is_dir() or not (packet/'manifest.json').is_file():
        raise RuntimeError('PACKET_ROOT_NOT_FOUND')
    print('CAMPAIGN='+VERSION,flush=True)
    print('AUTHORITY=TERMUX_GIT_ONLY',flush=True)
    print('CANONICAL_MODEL='+MODEL,flush=True)
    test_mode=os.environ.get('OBSIDIANTI_INTERNAL_TEST_MODE')=='1'
    remote=os.environ.get('OBSIDIANTI_INTERNAL_TEST_REMOTE') if test_mode else REMOTE
    if test_mode and (not remote or not remote.startswith('file:///')):
        raise RuntimeError('test mode requires file:/// fixture remote')
    if not test_mode and os.environ.get('OBSIDIANTI_INTERNAL_TEST_REMOTE'):
        raise RuntimeError('fixture remote override forbidden outside explicit test mode')
    source=preflight_packet(packet)
    print('PACKET_VERIFIED='+str(source['candidateSha256']),flush=True)
    lfs=ensure_lfs(test_mode)
    print('GIT_LFS='+lfs,flush=True)
    runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    base=pathlib.Path.home()/'.local'/'state'/'obsidianti-idle-v1.0.0'/runid
    base.mkdir(parents=True,exist_ok=False)
    checkout=base/'checkout'
    downloads=pathlib.Path.home()/'storage'/'downloads'
    downloads=downloads if downloads.is_dir() else base
    receipt=downloads/(VERSION+'_'+runid+'_RECEIPT.json')
    state={
        'campaign':VERSION,'runId':runid,'authorizedLane':'Termux Git',
        'replModel':'untouched','canonicalModel':MODEL,'expectedCanonicalSha256':EXPECTED_GLB_SHA,
        'packetManifestSha256':digest(packet/'manifest.json'),'sourcePoseAppearanceVerdict':'positive from user-provided screenshot',
        'sourceBlendSha256s':{
            'Obsidianti.blend':'68f7b29cfa76e0cc300d72fc37062ba786c1d6c75841f0b3a9c1ae78dbd33ce1',
            'LionheartLancer.blend':'81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
        },
        'campaignEtiquetteReadAtAuthoring':{'documentId':'1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI','source':'Home Center drive_read','remoteLiveReadByRunner':False},
        'riggedIdlePlaybackVerdict':'pending','status':'STARTED',
        'isTestFixture':test_mode,'gitRemote':remote if test_mode else REPO,
        'receiptPath':str(receipt),'workspace':str(base),
    }
    record_receipt(receipt,state)
    try:
        env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1';env['GIT_TERMINAL_PROMPT']='0'
        cmd=['git','clone','--depth=1','--branch','main','--single-branch',remote,str(checkout)]
        # Timeout covers source clone only, not background/interactive prompt.
        clone=run(cmd,timeout=170,env=env)
        state['sourceHead']=current_sha(checkout)
        print('SOURCE_HEAD='+state['sourceHead'],flush=True)
        state['liveAgentsSha256']=read_rules(checkout)
        state['sourceReadState']='VERIFIED'
        if git(['status','--porcelain=v1'],checkout).stdout.strip():
            raise RuntimeError('CLONE_DIRTY: do not mutate a dirty working tree')
        if not test_mode:
            git(['lfs','install','--local'],checkout)
        state['gitAuthorMode']=repo_identity(checkout)
        # Existing published paths are allowed only if they match exact content.
        mapping=dict(SRC_MAPPINGS)
        mapping[MANIFEST]='manifest.json'
        pending=[]
        for target,origin in mapping.items():
            sp=packet/origin;dp=checkout/target
            if not sp.is_file():raise RuntimeError('MISSING_PACKET_MEMBER '+origin)
            if dp.exists():
                if digest(dp)!=digest(sp):
                    # LFS skip-smudge can produce a pointer for existing files; check its OID.
                    if tracked_sha(checkout,target)!=digest(sp):
                        raise RuntimeError('COLLISION_DIFFERENT_EXISTING_FILE '+target)
            else:
                dp.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(sp,dp)
                if digest(dp)!=digest(sp):raise RuntimeError('SOURCE_COPY_SHA_MISMATCH '+target)
                pending.append(target)
        for p in (checkout/'assets'/'obsidianti').glob('*.glb'):
            if p.name != 'Obsidianti.glb':raise RuntimeError('MULTIPLE_CANONICAL_GLB '+str(p))
        model=checkout/MODEL
        if model.exists():
            if digest(model)!=EXPECTED_GLB_SHA and tracked_sha(checkout,MODEL)!=EXPECTED_GLB_SHA:
                raise RuntimeError('UNKNOWN_CANONICAL_GLB: refusing to overwrite a later asset')
            state['modelChange']='ALREADY_PRESENT_SAME_SHA'
        else:
            state['modelChange']='INITIAL_IMPORT_SINGLE_PATH'
        # Source commit first, then target model commit. Keep Repl entirely untouched.
        initial=commit_files(checkout,pending,'Obsidianti: add versioned Idle campaign and original Blender sources',test_mode)
        if initial:state['sourceCommit']=initial
        if not model.exists():
            model.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(packet/'payload/Obsidianti.idle-candidate.glb',model)
            if digest(model)!=EXPECTED_GLB_SHA:raise RuntimeError('MODEL_COPY_SHA_MISMATCH')
            sys.path.insert(0,str(packet/'campaigns'))
            from OBSIDIANTI_IDLE_VERIFY_v1_0_0 import canonical_check
            canonical_check(packet,model)
            output=commit_files(checkout,[MODEL],'Obsidianti: initialize ONE canonical GLB with Lionheart Idle candidate',test_mode)
            state['modelCommit']=output
        if check_scoped_status(checkout):
            raise RuntimeError('UNEXPECTED_DIRTY_FINAL_WORKTREE')
        head=current_sha(checkout)
        state['finalLocalHead']=head
        # Protected Repl SHA must be the same Git tree object in source and final history.
        original_repl=git(['rev-parse',f"{state['sourceHead']}:assets/repl/Repl.glb"],checkout,check=False)
        final_repl=git(['rev-parse',f"{head}:assets/repl/Repl.glb"],checkout,check=False)
        if original_repl.returncode==0 and final_repl.returncode==0 and original_repl.stdout!=final_repl.stdout:
            raise RuntimeError('REPL_MODEL_MUTATION_DETECTED')
        state['replSourceGitBlob']=original_repl.stdout.strip() if original_repl.returncode==0 else 'UNREADABLE'
        state['replFinalGitBlob']=final_repl.stdout.strip() if final_repl.returncode==0 else 'UNREADABLE'
        if tracked_sha(checkout,MODEL)!=EXPECTED_GLB_SHA:
            raise RuntimeError('COMMITTED_MODEL_POINTER_SHA_MISMATCH')
        if tracked_sha(checkout,SCRIPT)!=digest(packet/SRC_MAPPINGS[SCRIPT]):
            raise RuntimeError('COMMITTED_CAMPAIGN_SOURCE_MISMATCH')
        if head!=state['sourceHead']:
            # Only standard non-forced push; retries may change authentication,
            # never the destination, content or force policy.
            push=git(['push','origin','HEAD:refs/heads/main'],checkout,timeout=180,check=False)
            if push.returncode:
                rejected=('non-fast-forward' in push.stderr.lower() or '[rejected]' in push.stderr.lower())
                if rejected:
                    raise RuntimeError('PUSH_REJECTED_REMOTE_MOVED: '+push.stderr[-700:])
                if shutil.which('gh'):
                    with_gh=['git','-C',str(checkout),'-c',
                             'credential.helper=!gh auth git-credential','push',
                             'origin','HEAD:refs/heads/main']
                    push=run(with_gh,timeout=180,check=False)
                    state['pushAuthFallback']='gh auth git-credential'
                if push.returncode:
                    raise RuntimeError('PUSH_AUTH_OR_TRANSPORT_FAILED: '+push.stderr[-1100:])
        state['gitPushReturned']='SUCCESS'
        remote_line=git(['ls-remote','origin','refs/heads/main'],checkout,timeout=45).stdout.strip()
        remote_sha=remote_line.split()[0] if remote_line else ''
        if remote_sha!=head:
            raise RuntimeError('REMOTE_HEAD_READBACK_MISMATCH: pushed='+head+' remote='+remote_sha)
        state['remoteHeadVerified']=remote_sha
        state['remoteModelPointerOidVerified']=tracked_sha(checkout,MODEL)
        state['remoteScriptByteShaVerified']=tracked_sha(checkout,SCRIPT)
        # The new workspace contains the committed candidate, usable for local phone review.
        # Remote LFS byte readback requires a separate download and is not implied by pointer parity.
        state['remoteLfsBinaryReadback']='NOT_INDEPENDENTLY_CHECKED'
        state['status']='REMOTE_GIT_POINTER_VERIFIED__VISUAL_PENDING'
        # Start a local, read-only HTTP viewer only on an available port.
        from socket import socket,AF_INET,SOCK_STREAM
        port=8179
        sock=socket(AF_INET,SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1',port))
            available=True
        except OSError:
            available=False
        finally:
            sock.close()
        if available:
            log=open(base/'viewer.log','ab',buffering=0)
            try:
                proc=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(checkout)],
                    stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                (base/'viewer.pid').write_text(str(proc.pid))
                time.sleep(.65)
                if proc.poll() is None:
                    state['viewerPid']=proc.pid
                    state['viewerUrl']='http://127.0.0.1:8179/review/obsidianti.html'
                    print('PHONE_VIEWER='+state['viewerUrl'],flush=True)
                else:state['viewerStatus']='START_FAILED_CHECK_VIEWER_LOG'
            finally:log.close()
        else:state['viewerStatus']='PORT_BUSY_NOT_CLAIMED'
        record_receipt(receipt,state)
        print('STATUS='+state['status'],flush=True)
        print('CANONICAL='+MODEL,flush=True)
        print('REMOTE_HEAD='+remote_sha,flush=True)
        print('RECEIPT='+str(receipt),flush=True)
        print('HUMAN_VISUAL_VERDICT=REQUIRED_FOR_ACTUAL_RIGGED_IDLE_PLAYBACK',flush=True)
        return 0
    except Exception as ex:
        state['status']='BLOCKED'
        state['error']=str(ex)
        record_receipt(receipt,state)
        print('STATUS=BLOCKED',flush=True)
        print('REASON='+str(ex),flush=True)
        print('RECEIPT='+str(receipt),flush=True)
        return 2

if __name__=='__main__':
    sys.exit(main())
