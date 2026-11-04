#!/usr/bin/env python3
"""Disposable real Git transaction and cache/quarantine regression tests.

These tests DO NOT simulate a successful LFS upload or actual phone playback.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile

SRC=pathlib.Path(__file__).resolve().parents[1]/'campaigns/OBSIDIANTI_PELVIS_WEAPON_RECOVER_RUN_v1.2.2.py'
spec=importlib.util.spec_from_file_location('recovery_driver_v122', SRC)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def execute(*args,env=None):
    p=subprocess.run(args,text=True,capture_output=True,check=False,env=env)
    if p.returncode:
        raise RuntimeError(repr(args)+': '+p.stderr)
    return p.stdout.strip()

def fixture(parent):
    base=parent/'bare.git';repo=parent/'checkout';execute('git','init','--bare',str(base));execute('git','clone',str(base),str(repo))
    execute('git','-C',str(repo),'config','user.name','Fixture');execute('git','-C',str(repo),'config','user.email','fixture@example.test')
    execute('git','-C',str(repo),'checkout','-b','main')
    (repo/'AGENTS.md').write_text('# AGENTS.md\nRepository parametric-parambulator, Termux Git only. Read Campaign Etiquette.\n')
    (repo/'assets/repl').mkdir(parents=True);(repo/'assets/repl/Repl.glb').write_text('unchanged Repl')
    (repo/'assets/obsidianti').mkdir(exist_ok=True)
    old_bytes=b'original actual skinned GLB'
    newer_bytes=b'corrected actual skinned GLB'
    source_oid=hashlib.sha256(old_bytes).hexdigest();target_oid=hashlib.sha256(newer_bytes).hexdigest()
    oldpointer=f'version https://git-lfs.github.com/spec/v1\noid sha256:{source_oid}\nsize {len(old_bytes)}\n'
    newpointer=f'version https://git-lfs.github.com/spec/v1\noid sha256:{target_oid}\nsize {len(newer_bytes)}\n'
    (repo/mod.CANONICAL).write_text(oldpointer)
    execute('git','-C',str(repo),'add','.')
    execute('git','-C',str(repo),'commit','-m','baseline')
    basehead=execute('git','-C',str(repo),'rev-parse','HEAD')
    for filename in mod.PRIOR_FILES:
        dest=repo/filename;dest.parent.mkdir(exist_ok=True,parents=True);dest.write_text('prior script '+filename)
    execute('git','-C',str(repo),'add','.')
    execute('git','-C',str(repo),'commit','-m','Obsidianti: source v1.2 pelvis contact and weapon-drift repair')
    sourcehead=execute('git','-C',str(repo),'rev-parse','HEAD')
    (repo/mod.CANONICAL).write_text(newpointer)
    execute('git','-C',str(repo),'add','.')
    execute('git','-C',str(repo),'commit','-m','Obsidianti: correct Lionheart pelvis pitch and remove weapon translation on SAME GLB')
    # Emulate Python's REAL dynamic module import in the repository and check that .pyc appears.
    solver=repo/'campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py'
    solver.write_text('NUMBER=12\n')  # fixture must not edit any tracked content after commit; re-commit solver next
    execute('git','-C',str(repo),'add',str(solver));execute('git','-C',str(repo),'commit','-m','fixture source-only edit')
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='0'
    execute(sys.executable,'-c',f'import importlib.util; p={str(solver)!r}; s=importlib.util.spec_from_file_location("testsolv",p); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)',env=env)
    pycache=list((repo/'campaigns/__pycache__').glob('OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.cpython-*.pyc'))
    assert len(pycache)==1, pycache
    return base,repo,basehead,sourcehead,source_oid,target_oid

def run_tests():
    with tempfile.TemporaryDirectory(prefix='obsidianti-recovery-v122-test-') as td:
        parent=pathlib.Path(td);bare,repo,basehead,sourcehead,source_oid,oid=fixture(parent)
        # Exercise the REAL recovery preflight on actual Git history with a
        # synthetic LFS content digest adapter. The fixture does not run LFS.
        saved=(mod.REMOTE,mod.EXPECTED_BASE,mod.EXPECTED_SOURCE_OID,mod.EXPECTED_AGENTS_BLOB,mod.digest)
        mod.REMOTE=str(bare);mod.EXPECTED_BASE=basehead;mod.EXPECTED_SOURCE_OID=source_oid
        mod.EXPECTED_AGENTS_BLOB=execute('git','-C',str(repo),'rev-parse','HEAD:AGENTS.md')
        def fake_digest(path):
            if pathlib.Path(path).resolve()==(repo/mod.CANONICAL).resolve():return oid
            return saved[4](path)
        mod.digest=fake_digest
        prior={'fitReport':{'beforeSha256':source_oid,'afterSha256':oid,'clipCount':23,'weaponTranslationChannelsRemoved':20},
               'headBefore':basehead,'remoteOldModelOid':source_oid,'sourceBlendBytesVerified':True,
               'sourceModelBytesVerified':True,'verifiedPreflight':{'expectedFinalSha256':oid},
               'sourceSampleSha256':'a'*64,'scriptCommit':sourcehead}
        assessment=mod.preflight(repo,prior)
        assert assessment['expectedFinalSha256']==oid
        mod.digest=saved[4]  # Return to non-mocked byte hashing.
        cache=mod.inspect_dirty(repo)
        assert len(cache)==1 and mod.CACHE_PATTERN.fullmatch(cache[0][1]),cache
        unsafe=repo/'unrelated-note.txt';unsafe.write_text('not our file')
        try:
            mod.quarantine_expected_cache(repo,parent,{})
        except RuntimeError as exc:
            assert 'UNRELATED_DIRTY_PATHS' in str(exc)
        else:raise AssertionError('unexpected unrelated-file acceptance')
        assert unsafe.exists() and len(mod.inspect_dirty(repo))==2
        unsafe.unlink() # only test fixture, NEVER user's repo
        rep={};mod.quarantine_expected_cache(repo,parent,rep)
        assert len(rep['quarantinedCaches'])==1
        assert mod.inspect_dirty(repo)==[]
        expected_sha=mod.digest(rep['quarantinedCaches'][0]['quarantinedPath'])
        assert expected_sha==rep['quarantinedCaches'][0]['sha256']
        # Commit brand-new versioned recovery scripts, real Git transactions in disposable checkout.
        packet=parent/'packet';packet.mkdir()
        for rel in mod.NEW_FILES:
            dest=packet/rel;dest.parent.mkdir(exist_ok=True,parents=True);dest.write_text('v1.2.2 recovery source '+rel)
        result={}
        mod.stage_sources(repo,packet,result)
        assert result.get('recoveryScriptCommit')
        assert mod.inspect_dirty(repo)==[]
        assert len(list((repo/'assets/obsidianti').glob('*.glb')))==1
        # Unknown worktree content always fails; no automatic cleanup.
        (repo/'misc.txt').write_text('protect me')
        try:mod.quarantine_expected_cache(repo,parent,{})
        except RuntimeError as exc:assert 'UNRELATED_DIRTY_PATHS' in str(exc)
        else:raise AssertionError('unexpected cleaning of unrelated file')
        assert (repo/'misc.txt').read_text()=='protect me'
        (repo/'misc.txt').unlink()
        # Test recovery's remote readback over a real disposable bare repository.
        # Full publish path using a disposable bare Git remote and an explicit
        # lfs-push stub. This is a Git transaction fixture, NOT a real LFS upload.
        execute('git','-C',str(repo),'push','origin',basehead+':refs/heads/main')
        fakebin=parent/'fakebin';fakebin.mkdir()
        gitshim=fakebin/'git'
        gitshim.write_text('#!/bin/sh\nif [ "$3" = "lfs" ] && [ "$4" = "push" ]; then exit 0; fi\nexec /usr/bin/git "$@"\n')
        gitshim.chmod(0o755)
        oldpath=os.environ.get('PATH','')
        os.environ['PATH']=str(fakebin)+os.pathsep+oldpath
        try:
            receipt={'expectedFinalSha256':oid}
            mod.publish(repo,receipt)
            assert receipt['remoteHeadVerified']==execute('git','-C',str(repo),'rev-parse','HEAD')
            assert receipt['remoteModelPointerSha256']==oid
            assert receipt['remoteLfsObjectBytesIndependentlyDownloaded'] is False
        finally:
            os.environ['PATH']=oldpath
            mod.REMOTE,mod.EXPECTED_BASE,mod.EXPECTED_SOURCE_OID,mod.EXPECTED_AGENTS_BLOB,mod.digest=saved
    print('PASS:REAL_PYTHON_IMPORT_CREATED_CACHE')
    print('PASS:UNRELATED_DIRTY_FILES_PROTECTED')
    print('PASS:EXACT_CACHE_SHA_QUARANTINED')
    print('PASS:VERSIONED_SOURCE_COMMITTED_REAL_GIT')
    print('PASS:CANONICAL_SINGLE_GLB_PATH_AND_READBACK')
    print('PASS:FULL_RECOVERY_PREFLIGHT_REAL_GIT_HISTORY_SYNTHETIC_LFS_DIGEST')
    print('PASS:NONFORCED_GIT_PUSH_AND_REMOTE_HEAD_AND_MODEL_POINTER_FIXTURE')
    print('STATUS=OFF_DEVICE_GIT_TRANSACTION_FIXTURE_NOT_PRODUCTION_ACCEPTANCE')

if __name__=='__main__':run_tests()
