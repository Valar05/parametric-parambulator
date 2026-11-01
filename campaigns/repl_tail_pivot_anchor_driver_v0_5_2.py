#!/usr/bin/env python3
"""One model, one Termux Git commit: Repl v0.5.2 measured tail socket repair.

No GitHub direct connector writes and no production Git actions from ChatGPT.
Only the owner's existing Termux Git credentials perform the actual push.
Offline/local tests are preparation, not owner delivery or remote proof.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback

sys.dont_write_bytecode=True
VERSION='0.5.2'
CAMPAIGN='REPL_TAIL_PIVOT_ANCHOR'
REPO='Valar05/parametric-parambulator'
REPO_URL='https://github.com/Valar05/parametric-parambulator.git'
BRANCH='main'
LOCKED_PARENT='bc7fc1db9bd14d8408010def35a8ec6e67670986'
CANON='assets/repl/Repl.glb'
MANIFEST='assets/repl/CANONICAL_MODEL.json'
SOURCE_SHA='d44da2839ba05a4c520066e0d76cdb95339c2917456ee46fb27a02a7693c2d7a'
SOURCE_BLOB='35dfb120cb9518f3ccd8ca51514c8c8c2f0f0c3a'
EXPECTED_OUTPUT_SHA='55bca4c3406f46bd5c6475127158554a823f8aa36bfd7a6c969d9fb2806ccc7b'
EXPECTED_OUTPUT_BLOB='5fe7b6bdf6ffe4201e331d1db52ea0d24cad9002'
PREVIEW='REPL_TAIL_PIVOT_v0.5.2_textured.html'
REPORT='REPL_TAIL_PIVOT_v0.5.2_report.json'
RECEIPT='REPL_TAIL_PIVOT_v0.5.2_RECEIPT.txt'
FILES={
  'campaigns/REPL_TAIL_PIVOT_ANCHOR_v0.5.2.sh':'run-termux.sh',
  'campaigns/repl_tail_pivot_anchor_driver_v0_5_2.py':'driver.py',
  'campaigns/repl_tail_pivot_anchor_model_v0_5_2.py':'model.py',
  'campaigns/repl_tail_pivot_blender_review_v0_5_2.py':'blender_review.py',
  'campaigns/REPL_TAIL_PIVOT_ANCHOR_v0.5.2_CONTRACT.json':'contract.json',
}
class Blocked(RuntimeError):pass

def need(v,reason):
    if not v:raise Blocked(reason)

def emit(k,v):print(f'{k}={v}',flush=True)

def sha(b):return hashlib.sha256(b).hexdigest()

def file_sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def run(args,cwd=None,check=True,timeout=160):
    env=os.environ.copy();env['GIT_TERMINAL_PROMPT']='0';env['GIT_LFS_SKIP_SMUDGE']='1';env['PYTHONDONTWRITEBYTECODE']='1'
    r=subprocess.run(args,cwd=str(cwd) if cwd else None,env=env,
                     capture_output=True,text=True,check=False,timeout=timeout)
    if check and r.returncode:
        raise Blocked('COMMAND_FAILED:'+args[0]+':'+' '.join(args[1:3])+':rc='+str(r.returncode))
    return r

def git(repo,*args,check=True):return run(['git',*args],cwd=repo,check=check)

def gout(repo,*args):return git(repo,*args).stdout.strip()

def save_bytes(path,content):
    path=Path(path)
    need(path.parent.is_dir(),'OUTPUT_PARENT_DOES_NOT_EXIST')
    if path.exists():
        need(path.is_file() and file_sha(path)==sha(content),
             'IMMUTABLE_OUTPUT_COLLISION:'+path.name)
        return
    fd,temp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(content);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)
    need(file_sha(path)==sha(content),'PUBLISHED_SHA_MISMATCH:'+path.name)

def checkout(state):
    repo=state/'repo'
    if repo.exists():
        need((repo/'.git').is_dir(),'OWNER_CAMPAIGN_WORKSPACE_NOT_GIT')
        need(gout(repo,'remote','get-url','origin')==REPO_URL,
             'SAVED_CAMPAIGN_CHECKOUT_NOT_EXPECTED_REPOSITORY')
        need(not git(repo,'status','--porcelain','--untracked-files=all').stdout.strip(),
             'SAVED_CAMPAIGN_CHECKOUT_DIRTY__MANUAL_CONFLICT_PRESERVED')
        git(repo,'fetch','--quiet','origin',BRANCH)
        head=gout(repo,'rev-parse','HEAD')
        remote=gout(repo,'rev-parse','refs/remotes/origin/main')
        if head!=remote:
            need(git(repo,'merge-base','--is-ancestor',remote,head,check=False).returncode==0,
                 'SAVED_REPO_AND_REMOTE_DIVERGED__NOT_RESET')
        return repo
    temp=Path(tempfile.mkdtemp(prefix='.repl-clone-v052-',dir=state))
    try:
        temp.rmdir()
        run(['git','clone','--quiet','--branch',BRANCH,'--single-branch',REPO_URL,str(temp)],timeout=180)
        need(gout(temp,'remote','get-url','origin')==REPO_URL,
             'NEW_CLONE_REMOTE_MISMATCH')
        os.replace(temp,repo)
    finally:
        if temp.exists():shutil.rmtree(temp)
    return repo

def require_single(repo,ref):
    tracked=gout(repo,'ls-tree','-r','--name-only',ref).splitlines()
    actual=[p for p in tracked if p.lower().endswith('.glb')]
    need(actual==[CANON],f'CANONICAL_GLB_COUNT_WRONG:{actual}')
    return actual

def verify_remote(repo,digest,blob):
    remote='refs/remotes/origin/main'
    require_single(repo,remote)
    need(gout(repo,'rev-parse',f'{remote}:{CANON}')==blob,
         'REMOTE_CANONICAL_BLOB_MISMATCH')
    raw=subprocess.run(['git','show',f'{remote}:{CANON}'],cwd=repo,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90,check=False)
    need(raw.returncode==0 and sha(raw.stdout)==digest,
         'REMOTE_MODEL_BINARY_READBACK_SHA_MISMATCH')
    manifest=json.loads(git(repo,'show',f'{remote}:{MANIFEST}').stdout)
    active=manifest.get('active_model',{})
    need(active.get('version')==VERSION and active.get('sha256')==digest and
         active.get('git_blob_sha1')==blob,
         'REMOTE_MODEL_MANIFEST_WRONG_VERSION_OR_HASH')
    return gout(repo,'rev-parse',remote)

def push(repo,expected_head,state):
    new=gout(repo,'rev-parse','HEAD')
    preflight=git(repo,'ls-remote','origin','refs/heads/main').stdout.splitlines()
    need(preflight and preflight[0].split()[0]==expected_head,
         'REMOTE_ADVANCED_BEFORE_PUSH__DO_NOT_FORCE')
    commands=[(['git','push','--quiet','origin','HEAD:refs/heads/main'],'GIT')]
    if shutil.which('gh') and run(['gh','auth','status','-h','github.com'],check=False).returncode==0:
        commands.append((['git','-c','credential.helper=!gh auth git-credential',
                          'push','--quiet','origin','HEAD:refs/heads/main'],'GH_CREDENTIAL'))
    if shutil.which('ssh'):
        commands.append((['git','push','--quiet',
                          'git@github.com:Valar05/parametric-parambulator.git',
                          'HEAD:refs/heads/main'],'SSH'))
    lane=None
    for i,(command,name) in enumerate(commands):
        r=run(command,cwd=repo,check=False,timeout=140)
        (state/f'push-attempt-{i}.log').write_text('returncode='+str(r.returncode)+'\n')
        if r.returncode==0:
            lane=name;break
    need(lane is not None,'PUSH_FAILED__LOCAL_COMMIT_PRESERVED_FOR_RETRY')
    emit('PUSH_LANE',lane)
    live=git(repo,'ls-remote','origin','refs/heads/main').stdout.splitlines()
    need(live and live[0].split()[0]==new,'REMOTE_PUSH_HEAD_NOT_VISIBLE')
    git(repo,'fetch','--quiet','origin',BRANCH)
    return new

def update_manifest(text,report,output_sha,output_blob,preview_sha):
    value=json.loads(text)
    need(value.get('canonical_glb_path')==CANON,'MANIFEST_CANONICAL_PATH_CHANGED')
    prior=value.get('active_model',{})
    need(prior.get('version')=='0.5.1' and prior.get('sha256')==SOURCE_SHA,
         'CANONICAL_MANIFEST_NOT_EXPECTED_V051')
    value['status']='TAIL_ROOT_SOCKET_REANCHORED_v0.5.2__HUMAN_VISUAL_PENDING'
    value['single_canonical_glb_count']=1
    value['previous_model']={
       'commit':LOCKED_PARENT,'sha256':SOURCE_SHA,'git_blob_sha1':SOURCE_BLOB,
       'visual_issue':'tail base pivot misplaced, tail folds into rump on lift',
       'owner_acceptance':'REJECTED_ROOT_ATTACHMENT__RETAINED_IN_GIT_HISTORY'
    }
    active=dict(prior)
    active.update({
       'campaign':CAMPAIGN,'version':VERSION,'path':CANON,
       'sha256':output_sha,'git_blob_sha1':output_blob,
       'root_pivot_world':list(report['new_root_world']),
       'old_pivot_world':list(report['old_root_world']),
       'root_center_source':'measured tail/body intersection arc (estimated)',
       'tail_motion':'same 14-second straighten, corrected root and full-extension FK',
       'tail_bones':4,'bones':50,'animations':3,
       'mane_weights':'EXACT_UNCHANGED_V051',
       'tail_weights':'EXACT_UNCHANGED_V051',
       'first_two_animation_clips':'EXACT_UNCHANGED_V051',
       'preview_sha256':preview_sha,
       'human_visual_acceptance':'PENDING',
       'test_broad_root_prior_forward':report['peak']['old_broad_root_displacement'][2],
       'test_broad_root_fixed_forward':report['peak']['new_broad_root_displacement'][2]
    })
    value['active_model']=active
    return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode('utf8')

def update_readme(text):
    marker='## Tail attachment repair v0.5.2'
    need(marker not in text,'README_V052_NOTE_ALREADY_EXISTS')
    return text+('\n'+marker+'\n\nThe v0.5.1 root pivot was too low for the actual rump/tail attachment. '
       'The single canonical Repl.glb now uses a root at (0, 1.204, -0.889) '
       'derived from the measured body/tail intersection arc, while preserving '
       'the resting positions of the other three tail controls, unchanged '
       'original skin weights, original mane and materials. The 14-second '
       'straighten keys were recalculated against the corrected rest skeleton, '
       'reaching approximately -8 degrees across all three tail spans. '
       'No other GLB was created in the repository. The textured review includes '
       'the optional non-mutating root gizmo (off by default). '
       'The owner visual acceptance is pending. '
       'The earlier v0.5.1 commit remains available through Git history.\n')

def save_operator_receipt(downloads,commit,digest,blob,report):
    root=report['peak']
    lines=[
        f'CAMPAIGN={CAMPAIGN}',f'VERSION={VERSION}',
        'EXECUTION=TERMUX_GIT','REPOSITORY='+REPO,
        'CANONICAL_PATH='+CANON,'CANONICAL_GLB_COUNT=1',
        'REMOTE_HEAD='+commit,'REMOTE_GLB_SHA256='+digest,
        'REMOTE_GLB_GIT_BLOB='+blob,
        'WRONG_V051_ROOT=0,1.05,-0.93',
        'CORRECTED_ROOT=0,1.204,-0.889',
        f'OLD_ROOT_INTRUSION_FORWARD={root["old_broad_root_displacement"][2]}',
        f'NEW_ROOT_INTRUSION_FORWARD={root["new_broad_root_displacement"][2]}',
        'EXTENDED_SEGMENTS_DEGREES='+','.join(format(x,'.4f') for x in root['peak_segment_angles_degrees']),
        f'ROOT_SOCKET_RING_MAX_DRIFT={root["narrow_ring_max_motion"]}',
        f'MANE_DRIFT={report["max_mane_drift"]}',
        f'BODY_DRIFT={report["max_body_drift"]}',
        f'HOOF_DRIFT={report["max_hoof_drift"]}',
        'GIZMO=OPTIONAL_OFF_BY_DEFAULT',
        'NO_POSE_LAB=YES',
        'TEXTURED_VIEWER='+str(downloads/PREVIEW),
        'HUMAN_VISUAL_VERDICT=PENDING',
        'STATUS=REMOTE_CANONICAL_TAIL_PIVOT_CORRECTED_READBACK_VERIFIED'
    ]
    save_bytes(downloads/RECEIPT,('\n'.join(lines)+'\n').encode('utf8'))
    for line in lines:print(line,flush=True)

def load_model():
    file=Path(__file__).with_name('model.py')
    need(file.is_file(),'MODEL_PAYLOAD_MISSING')
    spec=importlib.util.spec_from_file_location('repl_pivot_model_052',file)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
    need(obj.SOURCE_SHA==SOURCE_SHA,'MODEL_AND_DRIVER_SOURCE_MISMATCH')
    return obj

def execute(args):
    packet=Path(args.packet).resolve()
    state=Path(args.state).expanduser().resolve()
    downloads=Path(args.downloads).expanduser().resolve()
    need(downloads.is_dir(),'TERMUX_DOWNLOADS_MISSING')
    need((packet/'campaign/run-termux.sh').is_file(),'PACKET_ENTRYPOINT_MISSING')
    state.mkdir(parents=True,exist_ok=True)
    repo=checkout(state)
    head=gout(repo,'rev-parse','HEAD')
    remote=gout(repo,'rev-parse','refs/remotes/origin/main')
    need(gout(repo,'remote','get-url','origin')==REPO_URL,'WRONG_GIT_REMOTE')
    require_single(repo,'HEAD')
    manifest=json.loads((repo/MANIFEST).read_text('utf8'))
    active=manifest.get('active_model',{})
    if active.get('version')==VERSION:
        outsha=active['sha256'];blob=active['git_blob_sha1']
        need(outsha==EXPECTED_OUTPUT_SHA and blob==EXPECTED_OUTPUT_BLOB,
             'V052_EXISTING_OUTPUT_NOT_EXPECTED_DETERMINISTIC_MODEL')
        need(file_sha(repo/CANON)==outsha and gout(repo,'rev-parse',f'HEAD:{CANON}')==blob,
             'V052_LOCAL_GLB_BYTES_OR_TREE_CHANGED')
        if head!=remote:
            need(remote==LOCKED_PARENT and
                 git(repo,'merge-base','--is-ancestor',remote,head,check=False).returncode==0,
                 'PENDING_V052_COMMIT_NOT_CHILD_OF_EXPECTED_PARENT')
            emit('RECOVERY','PUSH_EXISTING_LOCAL_V052_COMMIT__NO_REGENERATION')
            push(repo,remote,state)
        newhead=verify_remote(repo,outsha,blob)
        emit('STATUS','REMOTE_CANONICAL_TAIL_PIVOT_CORRECTED_READBACK_VERIFIED')
        emit('REMOTE_HEAD',newhead)
        emit('TEXTURED_REVIEW_PUBLISHED',str((downloads/PREVIEW).is_file()))
        emit('OWNER_VISUAL_VERDICT','PENDING')
        return
    need(head==remote==LOCKED_PARENT,'REMOTE_OR_LOCAL_HAS_ADVANCED__PRESERVE_EXISTING_WORK')
    need(active.get('version')=='0.5.1' and active.get('sha256')==SOURCE_SHA,
         'REMOTE_CANONICAL_NOT_EXPECTED_V051')
    need(gout(repo,'rev-parse',f'HEAD:{CANON}')==SOURCE_BLOB,
         'EXPECTED_PARENT_GIT_MODEL_BLOB_MISSING')
    need(file_sha(repo/CANON)==SOURCE_SHA,
         'OWNER_ACCEPTED_V051_GLB_SOURCE_HASH_MISMATCH')
    need(not git(repo,'status','--porcelain','--untracked-files=all').stdout.strip(),
         'SOURCE_REPO_ALREADY_DIRTY__NO_OVERWRITE')
    need((repo/CANON).is_file(),'CANONICAL_MODEL_FILE_MISSING')
    emit('CANONICAL_BEFORE_SHA256',SOURCE_SHA)
    model_module=load_model()
    base,v2,v4,gizmo=model_module.engines(repo)
    emit('DEPENDENCY_ENGINES','GIT_BLOB_LOCKED_VERIFIED')
    emit('TAIL_PIVOT_CORRECTION','BUILDING_AND_TESTING_REAL_CANONICAL_MODEL')
    model,report,html=model_module.repair((repo/CANON).read_bytes(),base,v2,v4,gizmo)
    digest=sha(model)
    need(digest==EXPECTED_OUTPUT_SHA,
         'REAL_MODEL_OUTPUT_DIFFERENT_FROM_TESTED_SHA256:'+digest)
    actual_blob=model_module.git_blob(model)
    need(actual_blob==EXPECTED_OUTPUT_BLOB,
         'REAL_MODEL_OUTPUT_DIFFERENT_FROM_TESTED_GIT_BLOB')
    emit('MODEL_VALIDATION','PASS_57_REAL_SKIN_FRAMES')
    emit('OLD_FORWARD_INTRUSION',report['peak']['old_broad_root_displacement'][2])
    emit('CORRECTED_FORWARD_INTRUSION',report['peak']['new_broad_root_displacement'][2])
    emit('EXTENDED_THREE_SEGMENT_ANGLES',report['peak']['peak_segment_angles_degrees'])
    emit('MANE_HOOF_BODY_DRIFT','ZERO_IN_TESTED_FRAMES')
    # Produce one real, full-texture HTML and a readable report, NOT an extra
    # GLB file in shared storage. The canonical is committed only in Git.
    review_bytes=html.encode('utf8')
    report_bytes=(json.dumps(report,indent=2,sort_keys=True)+'\n').encode('utf8')
    save_bytes(downloads/PREVIEW,review_bytes)
    save_bytes(downloads/REPORT,report_bytes)
    emit('TEXTURED_REVIEW',downloads/PREVIEW)
    if shutil.which('termux-media-scan'):
        try:
            p=run(['termux-media-scan',str(downloads/PREVIEW)],check=False,timeout=15)
            emit('MEDIA_REGISTRATION','REQUESTED_NOT_UI_VERIFIED' if p.returncode==0 else 'FAILED')
        except Exception:emit('MEDIA_REGISTRATION','FAILED')
    # The only GLB file changed in this isolated checkout is the canonical.
    tmp=state/'repl-canonical-v052.tmp'
    if tmp.exists():
        need(file_sha(tmp)==digest,'PREEXISTING_TEMP_FILE_WRONG_IDENTITY')
    else:save_bytes(tmp,model)
    need(file_sha(repo/CANON)==SOURCE_SHA,'SOURCE_CHANGED_DURING_BUILD')
    os.replace(tmp,repo/CANON)
    need(file_sha(repo/CANON)==digest,'UPDATED_CANONICAL_GLB_HASH_MISMATCH')
    manifest_data=update_manifest((repo/MANIFEST).read_text('utf8'),report,digest,actual_blob,sha(review_bytes))
    (repo/MANIFEST).write_bytes(manifest_data)
    readme=repo/'README.md'
    readme.write_text(update_readme(readme.read_text('utf8')),encoding='utf8')
    for target,source in FILES.items():
        dest=repo/target
        need(not dest.exists(),'VERSIONED_SOURCE_PATH_COLLISION:'+target)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(packet/'campaign'/source,dest)
    allow=[CANON,MANIFEST,'README.md',*FILES]
    for path in allow:
        need(git(repo,'check-ignore','-q','--',path,check=False).returncode!=0,
             'ALLOWLIST_PATH_IGNORED:'+path)
        git(repo,'add','--',path)
    staged=git(repo,'diff','--cached','--name-only').stdout.splitlines()
    need(set(staged).issubset(set(allow)) and CANON in staged,
         'STAGED_OTHER_FILES_OR_MODEL_MISSING')
    all_models=[p for p in gout(repo,'ls-files').splitlines() if p.lower().endswith('.glb')]
    need(all_models==[CANON],'INADVERTENT_EXTRA_GLB_STAGED')
    emit('STAGED_PATHS',','.join(staged))
    git(repo,'-c','user.name=Repl Termux Campaign',
        '-c','user.email=repl-termux-campaign@users.noreply.github.com',
        'commit','--quiet','-m',
        'Fix Repl tail root attachment at measured rump socket, preserve single model v0.5.2')
    localcommit=gout(repo,'rev-parse','HEAD')
    emit('LOCAL_COMMIT',localcommit)
    emit('LOCAL_COMMIT_IS_REMOTE_PROOF','NO')
    push(repo,LOCKED_PARENT,state)
    remotecommit=verify_remote(repo,digest,actual_blob)
    need(remotecommit==localcommit,'REMOTE_READBACK_DIFFERENT_FROM_LOCAL_COMMIT')
    save_operator_receipt(downloads,remotecommit,digest,actual_blob,report)
    if shutil.which('termux-open'):
        try:
            p=run(['termux-open',str(downloads/PREVIEW)],check=False,timeout=12)
            emit('VIEWER_OPEN','REQUESTED_NOT_CONFIRMED' if p.returncode==0 else 'FAILED')
        except Exception:emit('VIEWER_OPEN','FAILED')
    else:emit('VIEWER_OPEN','UNAVAILABLE')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--packet',required=True)
    ap.add_argument('--state',required=True)
    ap.add_argument('--downloads',required=True)
    args=ap.parse_args()
    emit('CAMPAIGN',CAMPAIGN)
    emit('VERSION',VERSION)
    emit('EXECUTION_LANE','TERMUX_GIT')
    emit('CANONICAL_PATH',CANON)
    execute(args)

if __name__=='__main__':
    try:main()
    except (Blocked,ValueError,KeyError,IndexError,TypeError,FileNotFoundError) as exc:
        emit('STATUS','BLOCKED')
        emit('CAUSE',type(exc).__name__+':'+str(exc))
        emit('SOURCE_MODEL_MUTATION_ON_REMOTE','NOT_CONFIRMED')
        sys.exit(2)
    except Exception as exc:
        traceback.print_exc()
        emit('STATUS','FAILED')
        emit('CAUSE',type(exc).__name__+':'+str(exc))
        sys.exit(3)
