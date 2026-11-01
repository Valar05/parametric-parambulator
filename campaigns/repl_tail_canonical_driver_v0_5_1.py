#!/usr/bin/env python3
"""Single-canonical-GLB Repl v0.5.1 release driver.

Runs ONLY behind the Termux entrypoint. Reuses pinned, Git-owned v0.1-v0.4
engines, builds the approved mane, four tapering tail controls and slow
straightening clip in memory, then commits the SAME canonical GLB path.
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

# Protect the owner checkout from import-generated untracked Python caches.
sys.dont_write_bytecode = True

CAMPAIGN='REPL_TAIL_CANONICAL_STRAIGHTEN'
VERSION='0.5.1'
REPOSITORY='Valar05/parametric-parambulator'
REPO_URL='https://github.com/Valar05/parametric-parambulator.git'
BRANCH='main'
ORIGINAL_IMPORT_COMMIT='0b388f2a7a16f199ae337d21bd1b7507bb4c2e11'
ORIGINAL_GLBSHA='d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f'
ORIGINAL_GIT_BLOB='02840305b7a71356839294e376c6c166ae98a9fc'
CANON='assets/repl/Repl.glb'
MANIFEST='assets/repl/CANONICAL_MODEL.json'
PREVIEW='REPL_TAIL_STRAIGHTEN_v0.5.1_textured.html'
REPORT='REPL_TAIL_STRAIGHTEN_v0.5.1_report.json'
RECEIPT='REPL_TAIL_STRAIGHTEN_v0.5.1_RECEIPT.txt'
SCRIPT_SOURCE='campaigns/REPL_TAIL_CANONICAL_v0.5.1.sh'
DRIVER_SOURCE='campaigns/repl_tail_canonical_driver_v0_5_1.py'
BLENDER_SOURCE='campaigns/repl_tail_blender_review_v0_5_1.py'
CONTRACT_SOURCE='campaigns/REPL_TAIL_CANONICAL_v0.5.1_CONTRACT.json'
EXPECTED_ENGINES={
  'repl_hair_bind_v0_1_0.py':'33ca93660f3d5858d4496027902b9b7a7e44d800',
  'repl_hair_five_controls_v0_2_0.py':'287567d6baf8e8fa415580dc57ee86600772f797',
  'repl_tail_four_controls_v0_3_0.py':'8c60a5a30d60ea3e016436afc5982404c2339e9d',
  'repl_tail_straighten_gizmo_v0_4_0.py':'a24601bf8b509732623a7b4219e6be1f6a556794',
  'repl_tail_gizmo_v0_4_0.js':'1b4396ed0027a0a75baed840d7ed741e57c58a92',
}

class Blocked(RuntimeError): pass

def need(cond, reason):
    if not cond: raise Blocked(reason)

def sha(b:bytes):return hashlib.sha256(b).hexdigest()

def file_sha(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def run(args:list[str],cwd:Path|None=None,check=True,timeout=160,quiet_err=False):
    e=os.environ.copy();e['GIT_TERMINAL_PROMPT']='0';e['GIT_LFS_SKIP_SMUDGE']='1'
    r=subprocess.run(args,cwd=str(cwd) if cwd else None,env=e,
                     capture_output=True,text=True,check=False,timeout=timeout)
    if check and r.returncode:
        # Git commands may contain authentication failures; do not print credentials.
        raise Blocked('COMMAND_FAILED:'+args[0]+' '+ ' '.join(args[1:3])+
                      ':returncode='+str(r.returncode))
    return r

def git(cwd:Path,*args,check=True,timeout=150):
    return run(['git',*args],cwd,check=check,timeout=timeout)

def goutput(cwd:Path,*args):return git(cwd,*args).stdout.strip()

def emit(k,v):print(f'{k}={v}',flush=True)

def save_atomic(path:Path,data:bytes):
    need(path.parent.is_dir(),'PUBLIC_OUTPUT_PARENT_MISSING')
    fd,temp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        if path.exists():
            need(file_sha(path)==sha(data),'PUBLIC_OUTPUT_NAME_COLLISION:'+path.name)
            os.unlink(temp)
            return
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)
    need(file_sha(path)==sha(data),'PUBLIC_OUTPUT_READBACK_MISMATCH:'+path.name)

def parse_glb(data):
    import struct
    need(data[:4]==b'glTF' and struct.unpack_from('<I',data,4)[0]==2,'BAD_GLB_MAGIC_OR_VERSION')
    need(struct.unpack_from('<I',data,8)[0]==len(data),'BAD_GLB_LENGTH')
    n,magic=struct.unpack_from('<I4s',data,12)
    need(magic==b'JSON','GLB_JSON_CHUNK_MISSING')
    return json.loads(data[20:20+n])

def inspect_original(repo):
    blob=goutput(repo,'rev-parse',f'HEAD:{CANON}')
    need(blob==ORIGINAL_GIT_BLOB,'EXISTING_CANONICAL_CHANGED__NO_OVERWRITE')
    source=(repo/CANON)
    need(source.is_file(),'CANONICAL_SOURCE_FILE_MISSING')
    need(file_sha(source)==ORIGINAL_GLBSHA,'CANONICAL_GLB_NOT_EXPECTED_IMPORT_SOURCE')
    glbs=[n for n in goutput(repo,'ls-tree','-r','--name-only','HEAD').splitlines()
          if n.lower().endswith('.glb')]
    need(glbs==[CANON],'CANONICAL_MODEL_COUNT_OR_PATH_CHANGED:'+str(glbs))
    model=parse_glb(source.read_bytes())
    need(len(model['skins'][0]['joints'])==43 and len(model.get('animations',[]))==0,
         'SOURCE_NOT_ORIGINAL_43_JOINT_BASELINE')
    return source

def checkout_repo(work_dir:Path):
    repo=work_dir/'repo'
    if repo.exists():
        need((repo/'.git').is_dir(),'REPO_WORKSPACE_COLLISION')
        need(goutput(repo,'remote','get-url','origin')==REPO_URL,
             'EXISTING_WORKSPACE_WRONG_REMOTE')
        need(not git(repo,'status','--porcelain','--untracked-files=all').stdout.strip(),
             'EXISTING_CAMPAIGN_CHECKOUT_DIRTY__PRESERVED')
        git(repo,'fetch','--quiet','origin',BRANCH)
        remote=goutput(repo,'rev-parse',f'refs/remotes/origin/{BRANCH}')
        if remote!=goutput(repo,'rev-parse','HEAD'):
            # If previous attempt committed locally but couldn't push, do not
            # throw away that commit. Preserve checkout for diagnosis/resume.
            local=goutput(repo,'rev-parse','HEAD')
            if git(repo,'merge-base','--is-ancestor',remote,local,check=False).returncode==0:
                return repo
            raise Blocked('REMOTE_BRANCH_ADVANCED__CHECKOUT_PRESERVED_NO_RESET')
        return repo
    need(not repo.exists(),'CAMPAIGN_REPOSITORY_PATH_OCCUPIED')
    tmp=Path(tempfile.mkdtemp(prefix='.clone-',dir=work_dir))
    try:
        shutil.rmtree(tmp)
        run(['git','clone','--quiet','--branch',BRANCH,'--single-branch',REPO_URL,str(tmp)],timeout=150)
        need(goutput(tmp,'remote','get-url','origin')==REPO_URL,
             'CLONE_REMOTE_IDENTITY_MISMATCH')
        os.replace(tmp,repo)
    finally:
        if tmp.exists():shutil.rmtree(tmp)
    return repo

def check_engines(repo):
    for file,expected in EXPECTED_ENGINES.items():
        p=repo/'campaigns'/file
        need(p.is_file(),'ENGINE_MISSING:'+file)
        actual=goutput(repo,'hash-object','--',str(p.relative_to(repo)))
        need(actual==expected,'ENGINE_GIT_BLOB_CHANGED:'+file)
    emit('LOCKED_EXISTING_V01_V02_V03_V04_ENGINES','VERIFIED')

def build_model(repo,source):
    script=repo/'campaigns/repl_tail_straighten_gizmo_v0_4_0.py'
    spec=importlib.util.spec_from_file_location('repl_v040',script)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    prev,old,base,gizmo_js=mod.load_engines()
    # 2026-10-31 regression: the v0.4 runner incorrectly calls
    # v0.3.read_glb_bytes(), but that helper is defined in v0.2.
    # Inject only the missing PURE GLB decoder into the in-memory module.
    # Do NOT edit v0.3 in Git, duplicate a GLB, or change skeleton/weights.
    need(callable(getattr(old,'read_glb_bytes',None)),
         'V020_EXPECTED_GLB_DECODER_MISSING')
    if not callable(getattr(prev,'read_glb_bytes',None)):
        prev.read_glb_bytes=old.read_glb_bytes
        emit('COMPAT_FIX','V040_USES_V020_GLB_DECODER_FOR_V030_READ')
    else:
        emit('COMPAT_FIX','V030_DECODER_ALREADY_PRESENT')
    # Catch other cross-version attribute regressions before generation.
    dependencies={
       'v040':(mod,('make_artifacts','load_engines','validate_straighten')),
       'v030':(prev,('make_artifacts','read_glb_bytes','TAIL_PIVOTS')),
       'v020':(old,('create_artifacts','read_glb_bytes','load_predecessor')),
       'v010':(base,('accessor','emit_accessor','glb_encode',
                     'skin_matrices','deform_vertex','world_matrices')),
    }
    for name,(module,attrs) in dependencies.items():
        missing=[attr for attr in attrs if not hasattr(module,attr)]
        need(not missing,'ENGINE_INTERFACE_MISMATCH:'+name+':'+','.join(missing))
    emit('ALL_ENGINE_INTERFACES','VERIFIED')
    emit('REAL_MODEL_GENERATION','STARTED')
    model,report_text,html=mod.make_artifacts(source,prev,old,base,gizmo_js)
    new=parse_glb(model)
    need(len(new['skins'][0]['joints'])==50 and len(new['nodes'])==53,
         'DERIVED_EXPECTED_FIFTY_JOINTS_MISSING')
    need(len(new.get('animations',[]))==3,
         'SLOW_STRAIGHTEN_ANIMATION_MISSING')
    named=[a.get('name','') for a in new['animations']]
    need(any('SLOW_STRAIGHTEN' in a for a in named),
         'STRAIGHTEN_ANIMATION_NOT_PRESENT')
    need(len(new['animations'][-1]['channels'])==4,
         'STRAIGHTEN_REVIEW_NOT_FOUR_BONE')
    original=parse_glb(source.read_bytes())
    need(len(new['meshes'])==len(original['meshes']),
         'MESH_COUNT_CHANGED')
    need(len(new['materials'])==len(original['materials']),
         'MATERIAL_COUNT_CHANGED')
    need([json.dumps(x,sort_keys=True) for x in new['materials']] ==
         [json.dumps(x,sort_keys=True) for x in original['materials']],
         'ORIGINAL_MATERIAL_VALUES_CHANGED')
    need(new['images']==original['images'], 'ORIGINAL_TEXTURE_REFS_CHANGED')
    need(len(new['meshes'])==2 and len(new['skins'][0]['joints'])==50,
         'DERIVED_HAIR_AND_BODY_RIG_IDENTITY_MISMATCH')
    need(all(c['target']['path']=='rotation' for c in
         new['animations'][-1]['channels']),
         'TAIL_REVIEW_HAS_NONROTATION_CHANNEL')
    for channel in new['animations'][-1]['channels']:
        joint_name=new['nodes'][channel['target']['node']].get('name','')
        need(joint_name.startswith('REPL_TAIL_'),
             'TAIL_STRAIGHTEN_KEYS_UNAUTHORIZED_NODE:'+joint_name)
    report=json.loads(report_text)
    validity=report.get('validation',{})
    need(validity.get('maximum_hoof_displacement',float('inf'))<1e-6,
         'HORSE_HOOF_MOVEMENT_REJECTED')
    need(validity.get('maximum_body_displacement',float('inf'))<1e-6,
         'HORSE_BODY_MOVEMENT_REJECTED')
    need(validity.get('maximum_accepted_mane_displacement',float('inf'))<1e-6,
         'ACCEPTED_MANE_UNEXPECTEDLY_MOVED')
    need(0.08<validity.get('maximum_tail_vertex_displacement',0)<0.8,
         'TAIL_STRAIGHTEN_OUTSIDE_ACCEPTANCE_BOUNDS')
    need('TransformControls' in html and 'gizmo-enable' in html,
         'OPTIONAL_GIZMO_NOT_IN_VIEWER')
    need(len(model)<30_000_000,'DERIVED_MODEL_ABNORMALLY_LARGE')
    emit('REAL_MODEL_GENERATION','NUMERIC_PASS')
    emit('TAIL_CLIP_NAME',named[-1])
    emit('TAIL_MAX_DEFORMATION',round(validity['maximum_tail_vertex_displacement'],6))
    return model,report,html

def amend_manifest(source_json,model_sha,blob_sha,source_head,preview_sha):
    d=json.loads(source_json)
    need(d['canonical_glb_path']==CANON,'MANIFEST_WRONG_CANONICAL_PATH')
    need(d.get('initial_import',{}).get('source_sha256')==ORIGINAL_GLBSHA,
         'MANIFEST_DID_NOT_RECORD_VERIFIED_INITIAL_IMPORT')
    d['status']='FOUR_BONE_TAIL_STRAIGHTEN_V0_5_0__HUMAN_VISUAL_PENDING'
    d['single_canonical_glb_count']=1
    d['source_baseline']={
       'commit':source_head,'sha256':ORIGINAL_GLBSHA,
       'git_blob_sha1':ORIGINAL_GIT_BLOB,
       'source_regression':'NONE'
    }
    d['active_model']={
       'campaign':CAMPAIGN,'version':VERSION,
       'path':CANON,'sha256':model_sha,'git_blob_sha1':blob_sha,
       'bones':50,'animations':3,
       'mane_weights':'from_original_v0.2_hair_candidate',
       'tail_bones':4,'tail_motion':'14s_slow_straighten',
       'gizmo':'optional_in_textured_viewer_off_by_default',
       'human_visual_acceptance':'PENDING',
       'preview_sha256':preview_sha,
    }
    return json.dumps(d,indent=2,sort_keys=True)+'\n'

def change_readme(path):
    s=path.read_text('utf8')
    if '## Current canonical motion candidate' in s:
        # Never edit another author's newer campaign note under this title.
        need('v0.5.1' in s,'README_CAMPAIGN_SECTION_COLLISION')
        return
    s+='\n## Current canonical motion candidate\n\n'
    s+='The single `assets/repl/Repl.glb` model is updated in place with '
    s+='the 3-control mane, 4-control tapering tail, preserved body/hooves, '
    s+='and 14-second tail straightening clip. Full-textured review includes '
    s+='an optional, non-mutating tail pivot gizmo, off by default. '
    s+='Version v0.5.1 is a candidate awaiting owner visual verdict, '
    s+='not automatic aesthetic acceptance. Git history preserves prior model.\n'
    path.write_text(s,encoding='utf8')

def publish_view(path,data):
    save_atomic(path,data)
    if shutil.which('termux-media-scan'):
        try:
            r=run(['termux-media-scan',str(path)],timeout=20,check=False)
            emit('MEDIA_SCAN_REQUESTED' if r.returncode==0 else 'MEDIA_SCAN_FAILED',path.name)
        except Exception:emit('MEDIA_SCAN','UNAVAILABLE')

def publish_report_and_preview(downloads,html,report):
    html_bytes=html.encode('utf8')
    report_bytes=(json.dumps(report,indent=2,sort_keys=True)+'\n').encode()
    publish_view(downloads/PREVIEW,html_bytes)
    save_atomic(downloads/REPORT,report_bytes)
    emit('TEXTURED_REVIEW',downloads/PREVIEW)
    emit('OPTIONAL_PIVOT_GIZMO','INCLUDED_OFF_BY_DEFAULT')
    return sha(html_bytes)

def stage_allowlist(repo, allowed):
    for f in allowed:git(repo,'add','--',f)
    staged=git(repo,'diff','--cached','--name-only').stdout.splitlines()
    need(set(staged).issubset(set(allowed)),'UNRELATED_FILES_STAGED')
    need(CANON in staged,'CANONICAL_MODEL_NOT_STAGED')
    return staged

def do_push(repo,expected_head,work_dir):
    new=goutput(repo,'rev-parse','HEAD')
    remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.splitlines()
    need(remote and remote[0].split()[0]==expected_head,
         'REMOTE_MOVED_BEFORE_PUSH')
    # Keep errors in private state; never reveal credentials.
    trials=[['git','push','--quiet','origin','HEAD:refs/heads/main']]
    if shutil.which('gh'):
        if run(['gh','auth','status','-h','github.com'],check=False).returncode==0:
            trials.append(['git','-c','credential.helper=!gh auth git-credential',
                           'push','--quiet','origin','HEAD:refs/heads/main'])
    if shutil.which('ssh'):
        trials.append(['git','push','--quiet',
                       'git@github.com:Valar05/parametric-parambulator.git',
                       'HEAD:refs/heads/main'])
    succeeded=False
    for i,cmd in enumerate(trials):
        result=run(cmd,cwd=repo,check=False,timeout=130)
        (work_dir/f'push-attempt-{i}.log').write_text(
          'returncode='+str(result.returncode)+'\n',encoding='utf8')
        if result.returncode==0:
            succeeded=True;emit('PUSH_LANE',['git','gh','ssh'][i]);break
    need(succeeded,'REMOTE_GITHUB_PUSH_FAILED__LOCAL_COMMIT_PRESERVED')
    remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.splitlines()
    need(remote and remote[0].split()[0]==new,
         'REMOTE_BRANCH_HEAD_NOT_EXPECTED_COMMIT')
    git(repo,'fetch','--quiet','origin','main')
    return new

def verify_remote(repo, expected_sha,expected_blob):
    ref='refs/remotes/origin/main'
    glbs=[p for p in goutput(repo,'ls-tree','-r','--name-only',ref).splitlines()
          if p.lower().endswith('.glb')]
    need(glbs==[CANON],'REMOTE_NOT_EXACTLY_ONE_CANONICAL_GLB')
    remote_blob=goutput(repo,'rev-parse',f'{ref}:{CANON}')
    need(remote_blob==expected_blob,'REMOTE_GLB_BLOB_SHA_MISMATCH')
    # Avoid decoding binary Git stdout through text; use a binary subprocess.
    result=subprocess.run(['git','show',f'{ref}:{CANON}'],cwd=repo,
                          capture_output=True,check=False,timeout=90)
    need(result.returncode==0 and sha(result.stdout)==expected_sha,
         'REMOTE_CANONICAL_ASSET_CONTENT_MISMATCH')
    manifest=json.loads(git(repo,'show',f'{ref}:{MANIFEST}').stdout)
    need(manifest['active_model']['sha256']==expected_sha and
         manifest['active_model']['version']==VERSION,
         'REMOTE_CANONICAL_MANIFEST_MISMATCH')
    return len(glbs)

def save_receipt(downloads,commit,digest,blob,count,report):
    val=report['validation']
    lines=[
      f'CAMPAIGN={CAMPAIGN}',f'VERSION={VERSION}',
      'EXECUTION_LANE=TERMUX_GIT',f'REPOSITORY={REPOSITORY}',
      'SINGLE_MODEL=YES',f'REMOTE_HEAD={commit}',
      f'REMOTE_CANONICAL_PATH={CANON}',f'REMOTE_CANONICAL_SHA256={digest}',
      f'REMOTE_CANONICAL_BLOB={blob}',f'REMOTE_GLB_COUNT={count}',
      'MANE_FROM_ACCEPTED_ALGORITHM=RECONSTRUCTED_NOT_VISUALLY_REAPPROVED',
      'TAIL_BONES=4','TAIL_STRAIGHTEN_DURATION_SECONDS=14',
      f'TAIL_DEFORMATION_MAX={val["maximum_tail_vertex_displacement"]}',
      f'HOOF_DRIFT_MAX={val["maximum_hoof_displacement"]}',
      'GIZMO=OPTIONAL_OFF_BY_DEFAULT',
      f'TEXTURED_REVIEW={downloads/PREVIEW}',
      'OWNER_VISUAL_ACCEPTANCE=PENDING',
      'STATUS=REMOTE_CANONICAL_GLB_UPDATED_AND_READBACK_VERIFIED',
    ]
    save_atomic(downloads/RECEIPT,('\n'.join(lines)+'\n').encode())
    emit('RECEIPT',downloads/RECEIPT)
    return lines

def execute(args):
    path=Path(args.packet).resolve()
    repo_state=Path(args.state).expanduser().resolve()
    downloads=Path(args.downloads).expanduser().resolve()
    need(downloads.is_dir(),'DOWNLOADS_NOT_AVAILABLE')
    need((path/'campaign/run-termux.sh').is_file(),'PACKET_TERMUX_ENTRYPOINT_MISSING')
    need((path/'campaign/blender_review.py').is_file(),'PACKET_BLENDER_RENDER_SCRIPT_MISSING')
    repo_state.mkdir(parents=True,exist_ok=True)
    repo=checkout_repo(repo_state)
    remote_base=goutput(repo,'rev-parse','refs/remotes/origin/main')
    head=goutput(repo,'rev-parse','HEAD')
    need(goutput(repo,'remote','get-url','origin')==REPO_URL,'REMOTE_MISMATCH')
    check_engines(repo)
    current=json.loads((repo/MANIFEST).read_text('utf8'))
    if current.get('active_model',{}).get('version')==VERSION:
        # True remote-first idempotence; do not create another GLB.
        expected=current['active_model']['sha256']
        blob=goutput(repo,'rev-parse',f'HEAD:{CANON}')
        need(file_sha(repo/CANON)==expected,'EXISTING_COMPLETED_MODEL_WRONG_SHA')
        if head==remote_base:
            count=verify_remote(repo,expected,blob)
            emit('CAMPAIGN_STATUS','IDEMPOTENT_REMOTE_MODEL_VERIFIED')
            emit('REMOTE_HEAD',head)
            emit('MODEL_SHA256',expected)
            emit('REMOTE_GLB_COUNT',count)
            emit('TEXTURED_REVIEW_AVAILABLE',(downloads/PREVIEW).exists())
            return
        # An earlier invocation may have completed its local commit but
        # lost authentication/network during push. Resume THAT commit,
        # never reset, rebuild, overwrite, or discard it.
        need(remote_base==ORIGINAL_IMPORT_COMMIT,
             'REMOTE_ADVANCED_DURING_PREVIOUS_PARTIAL_ATTEMPT')
        need(git(repo,'merge-base','--is-ancestor',remote_base,head,check=False).returncode==0,
             'UNPUSHED_COMMIT_IS_NOT_DESCENDANT_OF_IMPORT')
        emit('RESUME','PUSH_EXISTING_VERIFIED_LOCAL_CANDIDATE')
        new_head=do_push(repo,remote_base,repo_state)
        need(new_head==head,'RESUMED_GIT_HEAD_MISMATCH')
        count=verify_remote(repo,expected,blob)
        report_path=downloads/REPORT
        if report_path.is_file():
            report=json.loads(report_path.read_text('utf8'))
            save_receipt(downloads,head,expected,blob,count,report)
        emit('CAMPAIGN_STATUS','RESUMED_REMOTE_CANONICAL_GLB_UPDATED')
        emit('REMOTE_HEAD',head)
        return
    need(remote_base==ORIGINAL_IMPORT_COMMIT,
         'MAIN_HAS_ADVANCED_SINCE_LOCKED_IMPORT__NO_REWRITE')
    need(head==remote_base,
         'UNPUSHED_OR_MIXED_CHECKOUT_STATE__PRESERVED')
    need(not git(repo,'status','--porcelain','--untracked-files=all').stdout.strip(),
         'REPO_WORKSPACE_DIRTY__PRESERVED')
    source=inspect_original(repo)
    emit('SOURCE_BASELINE_SHA256',file_sha(source))
    model,report,html=build_model(repo,source)
    digest=sha(model)
    # Test all before mutating canonical file.
    need(digest!=ORIGINAL_GLBSHA,'ANIMATION_NOT_WRITTEN')
    source_blob=goutput(repo,'hash-object','--',CANON)
    need(source_blob==ORIGINAL_GIT_BLOB,'SOURCE_CHANGED_DURING_MODEL_BUILD')
    # Pre-commit evidence, no temporary *.glb visible in public Downloads.
    preview_sha=publish_report_and_preview(downloads,html,report)
    source.parent.mkdir(parents=True,exist_ok=True)
    # This replaces the canonical working copy in an isolated clean checkout;
    # original source remains retrievable from Git's parent commit.
    save_atomic(source.with_suffix('.glb.tmp'),model)
    need(file_sha(source.with_suffix('.glb.tmp'))==digest,'MODEL_WRITE_READBACK_FAILED')
    os.replace(source.with_suffix('.glb.tmp'),source)
    need(file_sha(source)==digest,'CANONICAL_WORKTREE_HASH_MISMATCH')
    new_blob=goutput(repo,'hash-object','--',CANON)
    (repo/MANIFEST).write_text(amend_manifest(
        (repo/MANIFEST).read_text('utf8'),digest,new_blob,head,preview_sha),'utf8')
    change_readme(repo/'README.md')
    # Commit the operator and code used, in addition to the same GLB.
    files={SCRIPT_SOURCE:'run-termux.sh',DRIVER_SOURCE:'driver.py',
           BLENDER_SOURCE:'blender_review.py',CONTRACT_SOURCE:'contract.json'}
    for target,src in files.items():
        dst=repo/target
        need(not dst.exists(),'VERSIONED_CAMPAIGN_SOURCE_PATH_COLLISION:'+target)
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path/'campaign'/src,dst)
    allowed=[CANON,MANIFEST,'README.md',*files]
    staged=stage_allowlist(repo,allowed)
    emit('STAGED_PATHS',','.join(staged))
    # Auditable commit, not an accidental mutation of any user workspace.
    git(repo,'-c','user.name=Repl Termux Campaign',
        '-c','user.email=repl-termux-campaign@users.noreply.github.com',
        'commit','--quiet','-m',
        'Advance one canonical Repl GLB: mane, 4-tail rig and slow straighten v0.5.1')
    commit=goutput(repo,'rev-parse','HEAD')
    emit('LOCAL_COMMIT',commit)
    emit('LOCAL_COMMIT_IS_REMOTE_PROOF','NO')
    remote_head=do_push(repo,remote_base,repo_state)
    need(commit==remote_head,'GIT_COMMIT_READBACK_CHANGED')
    count=verify_remote(repo,digest,new_blob)
    lines=save_receipt(downloads,commit,digest,new_blob,count,report)
    for line in lines:print(line,flush=True)
    if shutil.which('termux-open'):
        try:
            r=run(['termux-open',str(downloads/PREVIEW)],check=False,timeout=12)
            emit('VIEWER_OPEN','REQUESTED_UNCONFIRMED' if r.returncode==0 else 'FAILED')
        except Exception:emit('VIEWER_OPEN','FAILED')
    else:emit('VIEWER_OPEN','NOT_AVAILABLE')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--packet',required=True)
    p.add_argument('--state',required=True)
    p.add_argument('--downloads',required=True)
    a=p.parse_args()
    emit('CAMPAIGN',CAMPAIGN);emit('VERSION',VERSION)
    emit('AUTHORIZED_LANE','TERMUX_GIT__NO_DIRECT_CHATGPT_GITHUB_MUTATIONS')
    emit('SINGLE_CANONICAL_PATH',CANON)
    execute(a)

if __name__=='__main__':
    try:main()
    except (Blocked,ValueError,KeyError,IndexError,TypeError,FileNotFoundError) as err:
        emit('CAMPAIGN_STATUS','BLOCKED')
        emit('CAUSE',type(err).__name__+':'+str(err))
        emit('REPO_SOURCE_PRESERVATION','GIT_HISTORY_AND_ORIGINAL_IMPORT')
        sys.exit(2)
    except Exception as err:
        traceback.print_exc()
        emit('CAMPAIGN_STATUS','FAILED')
        emit('CAUSE',type(err).__name__+':'+str(err))
        sys.exit(3)
