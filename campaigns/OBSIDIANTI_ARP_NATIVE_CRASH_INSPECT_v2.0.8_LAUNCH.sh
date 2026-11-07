#!/data/data/com.termux/files/usr/bin/bash
# OBSIDIANTI_ARP_NATIVE_CRASH_INSPECT_v2.0.8
# Read only the real Debian/Blender crash reports from the prior ARP trials.
# Authority: Termux Git only. No add-on modification, no Blender execution, no model modification.
set -Eeuo pipefail
if [ -z "${PREFIX:-}" ] || [ ! -x "${PREFIX}/bin/bash" ]; then
  printf '%s\n' 'BLOCKED: Termux is required'; exit 2
fi
SELF="$(readlink -f -- "$0")"
[ -f "$SELF" ] || { echo 'BLOCKED: launcher missing'; exit 2; }
command -v python3 >/dev/null || { echo 'BLOCKED: Termux python3 missing'; exit 2; }
command -v git >/dev/null || { echo 'BLOCKED: Termux git missing'; exit 2; }
command -v proot-distro >/dev/null || { echo 'BLOCKED: Termux proot-distro missing'; exit 2; }
printf 'CAMPAIGN=OBSIDIANTI_ARP_NATIVE_CRASH_INSPECT_v2.0.8\nAUTHORITY=TERMUX_GIT_ONLY\nLAUNCHER_SHA256=%s\n' "$(sha256sum "$SELF" | cut -d' ' -f1)"
PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 python3 - "$SELF" <<'PY'
from __future__ import annotations
import datetime,hashlib,json,os,pathlib,re,shutil,subprocess,sys,time,traceback,uuid

V='OBSIDIANTI_ARP_NATIVE_CRASH_INSPECT_v2.0.8'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE='649b5aa611d0e2f18bf04c9466accad3b0d4279e'
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
LION='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
ARPSHA='2b377bbc5d81dfcef4209971e332a8bcb402ed44605e5ed0cddc2e90fafebf28'
PUBLISH_SOURCE='campaigns/'+V+'_LAUNCH.sh'
EVIDENCE_DIR='diagnostics/obsidianti/arp-native-crash-v2.0.8/runs/'
PRIOR='diagnostics/obsidianti/arp-retarget-failure-forensics-v2.0.7/runs/20261107T004441Z-1acbf29b/EVIDENCE.json'
LOCKED=('assets/obsidianti/Obsidianti.glb','assets/repl/Repl.glb')
SCRIPT=pathlib.Path(sys.argv[1]).resolve()

def sha_bytes(x):return hashlib.sha256(x).hexdigest()
def sha_file(p):return sha_bytes(pathlib.Path(p).read_bytes())
def run(a,timeout=180,check=True,env=None):
    a=[str(x) for x in a]
    p=subprocess.run(a,timeout=timeout,env=env,capture_output=True,text=True)
    if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+repr(a[:6])+' exit='+str(p.returncode)+' STDOUT='+p.stdout[-450:]+' STDERR='+p.stderr[-1100:])
    return p

def git(repo,*args,check=True,timeout=180):return run(['git','-C',repo,*args],check=check,timeout=timeout)
def g(repo,*args):return git(repo,*args).stdout.strip()

def copy_new(src,dst):
    src=pathlib.Path(src);dst=pathlib.Path(dst)
    if not src.is_file() or src.is_symlink():raise RuntimeError('SOURCE_NOT_ORDINARY_FILE '+str(src))
    if dst.exists():raise RuntimeError('NO_OVERWRITE_COLLISION '+str(dst))
    dst.parent.mkdir(parents=True,exist_ok=True)
    tmp=dst.with_name('.'+dst.name+'.'+uuid.uuid4().hex[:10]+'.tmp')
    try:
        shutil.copyfile(src,tmp)
        if sha_file(tmp)!=sha_file(src):raise RuntimeError('COPY_SHA_MISMATCH '+str(dst))
        os.replace(tmp,dst)
    finally:
        if tmp.exists():tmp.unlink()

def sanit(s):
    # No home directories, private add-on package paths, line-of-code dumps or vendor source.
    s=str(s).replace('\\x00','')[:200]
    s=re.sub(r'/[^\s\]\[()"<>]+/', '<dir>/',s)
    return s

PROOT_CODE=r'''import os,sys,glob,hashlib,json,re,subprocess
items=[]
for basename in ('Ares (1).crash.txt','LionheartLancer.crash.txt'):
 p='/tmp/'+basename
 ent={'clip':'AxeKick' if basename.startswith('Ares') else 'Heavy1','expectedCrashName':basename,'found':False}
 try:
  if os.path.isfile(p) and not os.path.islink(p):
   b=open(p,'rb').read(512000)
   s=b.decode('utf-8','replace')
   ent.update({'found':True,'sha256':hashlib.sha256(b).hexdigest(), 'bytesRead':len(b),'mtimeEpoch':int(os.stat(p).st_mtime),
    'head':s.splitlines()[:12],'backtrace':[],'pythonBacktrace':[],'signalLines':[]})
   # Native stack printed below # backtrace; Python stack often below # Python backtrace.
   mode=None
   for line in s.splitlines():
    if line.strip().startswith('# backtrace'): mode='native';continue
    if line.strip().startswith('# Python backtrace'):mode='python';continue
    if line.strip().startswith('# ' ) and ('information' in line or 'end' in line):mode=None
    if any(w in line.lower() for w in ('signal 11','sigsegv','segmentation fault')):
     if len(ent['signalLines'])<10:ent['signalLines'].append(line)
    if mode=='native' and len(ent['backtrace'])<85:ent['backtrace'].append(line)
    if mode=='python' and len(ent['pythonBacktrace'])<45:ent['pythonBacktrace'].append(line)
   if not ent['backtrace']:
    ent['backtrace']=s.splitlines()[12:75]
 except Exception as exc:ent['readError']=type(exc).__name__+': '+str(exc)[:180]
 items.append(ent)
meta={'blenderRuntime':'UNAVAILABLE','versionedExecutables':{},'debianRelease':'UNAVAILABLE'}
try:
 p=subprocess.run(['blender','--version'],capture_output=True,text=True,timeout=20)
 meta['blenderRuntime']=(p.stdout+p.stderr).splitlines()[:4]
except Exception as exc:meta['blenderRuntimeError']=type(exc).__name__
for name in ('blender','blender4.4','blender4.5','blender4.6','blender5.0'):
 try:
  p=subprocess.run(['sh','-c','command -v '+name],capture_output=True,text=True,timeout=2)
  if p.returncode==0:meta['versionedExecutables'][name]=p.stdout.strip()
 except Exception:pass
try:
 s=open('/etc/os-release').read();meta['debianRelease']=next((l for l in s.splitlines() if l.startswith('PRETTY_NAME=')),'UNAVAILABLE')
except Exception:pass
print('ARP_CRASH_DIAGNOSTICS_JSON='+json.dumps({'schema':'arp-native-crash-proot-v1','crashes':items,'runtime':meta},sort_keys=True))
'''

def proot_crash():
    p=run(['proot-distro','login','debian','--','python3','-c',PROOT_CODE],timeout=90,check=False)
    lines=[l[len('ARP_CRASH_DIAGNOSTICS_JSON='):] for l in p.stdout.splitlines() if l.startswith('ARP_CRASH_DIAGNOSTICS_JSON=')]
    if not lines:
        return {'error':'DEBIAN_CRASH_INSPECTION_NO_JSON','returncode':p.returncode,'stderr':sanit(p.stderr[-350:]),'crashes':[]}
    j=json.loads(lines[-1]);j['prootReturncode']=p.returncode
    return j

def summarize(native):
    result=[]
    for x in native.get('crashes',[]):
        item={'clip':x['clip'],'found':x['found'],'expectedCrashName':x['expectedCrashName']}
        if x['found']:
            for k in ('sha256','bytesRead','mtimeEpoch'):item[k]=x.get(k)
            item['header']=[sanit(s) for s in x.get('head',[])][:8]
            item['nativeBacktrace']=[sanit(s) for s in x.get('backtrace',[]) if s.strip()][:62]
            item['pythonBacktrace']=[sanit(s) for s in x.get('pythonBacktrace',[]) if s.strip()][:30]
            item['signalLines']=[sanit(s) for s in x.get('signalLines',[])]
            joined=' '.join(x.get('backtrace',[])).lower()
            if 'libpython' in joined or 'bpy' in joined or 'python' in joined:item['stackHint']='PYTHON_OR_BPY_FRAME_PRESENT_NOT_CAUSAL_PROOF'
            elif item['nativeBacktrace']:item['stackHint']='NATIVE_STACK_PRESENT_REQUIRES_EXPERT_INTERPRETATION'
            else:item['stackHint']='EMPTY_BACKTRACE'
        else:item['status']='CRASH_TEXT_NOT_PERSISTED_IN_PROOT_TMP'
        result.append(item)
    return result

def clone(root):
    repo=root/'repo'
    env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
    run(['git','clone','--quiet','--depth=1','--single-branch','--branch','main',REMOTE,repo],timeout=480,env=env)
    if g(repo,'remote','get-url','origin').removesuffix('.git')!=REMOTE.removesuffix('.git'):raise RuntimeError('REMOTE_IDENTITY_MISMATCH')
    head=g(repo,'rev-parse','HEAD')
    if head!=BASE and git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False).returncode:
        git(repo,'fetch','--no-tags','--depth=120','origin',BASE,timeout=240)
        if git(repo,'merge-base','--is-ancestor',BASE,'HEAD',check=False).returncode:raise RuntimeError('REMOTE_MAIN_NOT_DESCENDANT_OF_PINNED_CRASH_EVIDENCE')
    if g(repo,'rev-parse','HEAD:AGENTS.md')!=AGENTS:raise RuntimeError('REPOSITORY_RULES_CHANGED')
    raw=g(repo,'show','HEAD:assets/obsidianti/Obsidianti.glb')
    if 'oid sha256:'+CANON not in raw:raise RuntimeError('CANONICAL_MODEL_IDENTITY_CHANGED')
    previous=json.loads(git(repo,'show','HEAD:'+PRIOR).stdout)
    if previous['canonicalModelSHA256']!=CANON or previous['privateVendorZIPSHA256']!=ARPSHA:raise RuntimeError('PRIOR_VENDOR_MODEL_IDENTITY_CHANGED')
    if not all(x['trialStatus']=='BOOT' for x in previous['clips']):raise RuntimeError('PRIOR_CRASH_STATUS_CHANGED')
    if g(repo,'status','--porcelain'):raise RuntimeError('DISPOSABLE_GIT_WORKTREE_DIRTY')
    return repo,head

def push(repo,phase):
    head=g(repo,'rev-parse','HEAD')
    for i in range(3):
        p=git(repo,'push','origin','HEAD:refs/heads/main',check=False,timeout=300)
        if not p.returncode:break
        if i==2:raise RuntimeError('GIT_PUSH_FAILED_'+phase+' '+p.stderr[-400:])
        time.sleep(i+1)
    remote=git(repo,'ls-remote','origin','refs/heads/main',timeout=90).stdout.split()
    if not remote or remote[0]!=head:raise RuntimeError('REMOTE_HEAD_NOT_EQUAL_PUBLISHED_COMMIT_'+phase)
    git(repo,'fetch','--quiet','origin','main',timeout=240)
    if g(repo,'rev-parse','refs/remotes/origin/main')!=head:raise RuntimeError('REMOTE_FETCH_DIFFERENT_'+phase)
    return head

def main():
    if not SCRIPT.is_file() or SCRIPT.is_symlink():raise RuntimeError('LAUNCHER_NOT_ORDINARY_FILE')
    runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    root=pathlib.Path.home()/'.local/state'/V/runid
    root.mkdir(parents=True,exist_ok=False)
    receipt=root/'RECEIPT.json'
    r={'campaign':V,'runId':runid,'authority':'TERMUX_GIT_ONLY','launcherSHA256':sha_file(SCRIPT),
        'status':'BOOT','modelSHA256':CANON,'donorSHA256':LION,'vendorZipSHA256':ARPSHA,'agentsBlobSHA':AGENTS,
        'etiquetteReadByAgent':'2026-11-06','mutation':'NONE_TO_CANONICAL_OR_VENDOR','ownerVisualAcceptance':'PENDING'}
    def save():
        tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');os.replace(tmp,receipt)
    save()
    try:
        native=proot_crash()
        report=summarize(native)
        r['crashFilesFound']=sum(x.get('found',False) for x in report)
        r['runtime']=native.get('runtime',{})
        r['status']='REAL_PRIOR_DEBIAN_CRASH_FILES_INSPECTED';save()
        for x in report:
            print('CRASH_'+x['clip'].upper()+'='+('FOUND_SHA256_'+x['sha256'] if x['found'] else x.get('status')),flush=True)
            print('NATIVE_BACKTRACE_'+x['clip'].upper()+'=BEGIN',flush=True)
            for line in x.get('nativeBacktrace',[])[:45]:print(line,flush=True)
            print('NATIVE_BACKTRACE_'+x['clip'].upper()+'=END',flush=True)
        if not report:print('CRASH_INSPECTION='+native.get('error','NO_REPORTS'),flush=True)
        repo,priorhead=clone(root)
        original={p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}
        r['inputGitHEAD']=priorhead
        priorfile=repo/PUBLISH_SOURCE
        if priorfile.exists():
            if sha_file(priorfile)!=sha_file(SCRIPT):raise RuntimeError('VERSION_COLLISION_EXISTING_SCRIPT_DIFFERS')
            sourcecommit=g(repo,'log','-1','--format=%H','--',PUBLISH_SOURCE)
        else:
            copy_new(SCRIPT,priorfile)
            git(repo,'add','--',PUBLISH_SOURCE)
            if g(repo,'diff','--cached','--name-only')!=PUBLISH_SOURCE:raise RuntimeError('SOURCE_STAGE_SCOPE_FAIL')
            if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Diagnostic')
            if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','termux-diagnostics@users.noreply.github.com')
            git(repo,'commit','-m','Obsidianti: inspect actual Blender native crash stack without retarget rerun')
            sourcecommit=push(repo,'SOURCE')
        r['sourceCommit']=sourcecommit;save()
        artifact=root/'evidence';artifact.mkdir()
        j=artifact/'EVIDENCE.json'
        safe={'schema':V,'runId':runid,'sourceCommit':sourcecommit,'inputGitHEAD':priorhead,
              'priorCrashReceiptGitCommit':BASE,'agentsSHA':AGENTS,'campaignEtiquetteRead':'2026-11-06',
              'canonicalGLBSHA256':CANON,'vendorZIPSHA256':ARPSHA,
              'sourceFilesBlender44032Warning':True,'executedNewBlenderTrial':False,
              'vendorSourceIncluded':False,'canonicalModified':False,'ownerVisualAcceptance':'PENDING',
              'runtime':native.get('runtime',{}),'crashes':report,'error':native.get('error')}
        j.write_text(json.dumps(safe,indent=2,sort_keys=True)+'\n')
        md=artifact/'REPORT.md'
        md.write_text('# Auto-Rig Pro native crash backtrace inspection\n\n'
           'The existing Blender 4.3.2 Ares and Lionheart retarget processes terminated with SIGSEGV. '
           'This campaign did not rerun Blender, retarget, render, modify vendor files, or edit canonical GLBs.\n\n'
           'Original source .blend files were saved with newer Blender binary (404.32). '
           'The precise crash stack, if retained in Debian /tmp, appears in EVIDENCE.json.\n\n'
           +'\n'.join('- '+x['clip']+': '+('native crash report found' if x['found'] else 'crash report missing') for x in report)
           +'\n\nNo claimed animation success or owner visual approval.\n')
        destinations={EVIDENCE_DIR+runid+'/EVIDENCE.json':j,EVIDENCE_DIR+runid+'/REPORT.md':md}
        if any((repo/p).exists() for p in destinations):raise RuntimeError('OUTPUT_DESTINATION_ALREADY_EXISTS')
        for p,src in destinations.items():copy_new(src,repo/p)
        git(repo,'add','--',*sorted(destinations))
        if set(g(repo,'diff','--cached','--name-only').splitlines())!=set(destinations):raise RuntimeError('EVIDENCE_GIT_STAGE_SCOPE_FAIL')
        if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Obsidianti Termux Diagnostic')
        if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','termux-diagnostics@users.noreply.github.com')
        git(repo,'commit','-m','Obsidianti: publish sanitized real Blender native crash backtraces')
        commit=push(repo,'EVIDENCE')
        for p,f in destinations.items():
            raw=subprocess.run(['git','-C',str(repo),'cat-file','blob','refs/remotes/origin/main:'+p],capture_output=True,check=True).stdout
            if sha_bytes(raw)!=sha_file(f):raise RuntimeError('REMOTE_EVIDENCE_BLOB_DIFFERS '+p)
        if {p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED}!=original:raise RuntimeError('PROTECTED_MODEL_GIT_POINTER_CHANGED')
        r.update({'gitEvidenceCommit':commit,'status':'NATIVE_CRASH_INSPECTION_GIT_REMOTE_VERIFIED','modelUnchanged':True});save()
        out='https://github.com/Valar05/parametric-parambulator/blob/'+commit+'/'+EVIDENCE_DIR+runid+'/EVIDENCE.json'
        print('EVIDENCE_URL='+out,flush=True)
        print('CANONICAL_MODEL_UNCHANGED=YES',flush=True)
        print('STATUS='+r['status'],flush=True)
    except Exception as exc:
        r.update({'status':'BLOCKED','errorType':type(exc).__name__,'error':str(exc)[:900],'tracebackLocal':traceback.format_exc()[-2500:]});save()
        print('STATUS=BLOCKED '+type(exc).__name__+' '+str(exc)[:500],flush=True)
        raise
    finally:
        print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':main()
PY
