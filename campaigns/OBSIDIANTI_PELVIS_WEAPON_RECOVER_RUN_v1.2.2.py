#!/usr/bin/env python3
"""Recover the ALREADY COMMITTED v1.2.1 Obsidianti pelvis+weapon result.

Termux Git only. Never rerun sampling, solve, or alter canonical model bytes.
Only generated v1.2.1 solver Python bytecode may be quarantined, never cleaned broadly.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

CAMPAIGN = 'OBSIDIANTI_PELVIS_WEAPON_RECOVER_v1.2.2'
PRIOR = 'OBSIDIANTI_PELVIS_WEAPON_v1.2.1'
REMOTE = 'https://github.com/Valar05/parametric-parambulator.git'
CANONICAL = 'assets/obsidianti/Obsidianti.glb'
REPL = 'assets/repl/Repl.glb'
EXPECTED_BASE = '806cf70cdd957312d290d3cdd3d5e0c239f1f5a6'
EXPECTED_SOURCE_OID = '5fa8773736cf4fd28eae13e13368246642642a1802d76e47ed7e14faf70d04c0'
EXPECTED_AGENTS_BLOB = '547c2af52303f4efb718bbf8f82a698110c7bfca'
PRIOR_FILES = {
    'campaigns/OBSIDIANTI_PELVIS_WEAPON_v1.2.1.sh',
    'campaigns/OBSIDIANTI_PELVIS_WEAPON_RUN_v1.2.1.py',
    'campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py',
    'docs/obsidianti/PELVIS_WEAPON_v1.2.1.md',
    'tests/OBSIDIANTI_PELVIS_WEAPON_TEST_v1.2.1.py',
    'tests/OBSIDIANTI_RULES_GATE_TEST_v1.2.1.py',
}
NEW_FILES = {
    'campaigns/OBSIDIANTI_PELVIS_WEAPON_RECOVER_v1.2.2.sh',
    'campaigns/OBSIDIANTI_PELVIS_WEAPON_RECOVER_RUN_v1.2.2.py',
    'tests/OBSIDIANTI_PELVIS_WEAPON_RECOVER_TEST_v1.2.2.py',
    'docs/obsidianti/PELVIS_WEAPON_RECOVER_v1.2.2.md',
}
CACHE_PATTERN = re.compile(r'^campaigns/__pycache__/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1\.2\.1\.cpython-\d+\.pyc$')


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def run(args, *, ok=True, timeout=150, env=None):
    p = subprocess.run(args, text=True, capture_output=True, timeout=timeout, env=env)
    if ok and p.returncode:
        raise RuntimeError('COMMAND_FAILED ' + repr(args[:8]) + ' ' + p.stderr[-1600:])
    return p.stdout.strip()


def git(repo, *args, ok=True, timeout=150):
    return run(['git', '-C', str(repo), *args], ok=ok, timeout=timeout)


def lfs_oid(repo, revision, path):
    p = run(['git', '-C', str(repo), 'show', revision + ':' + path])
    if not p.startswith('version https://git-lfs.github.com/spec/v1'):
        raise RuntimeError('INVALID_CANONICAL_LFS_POINTER:' + revision + ':' + path)
    for line in p.splitlines():
        if line.startswith('oid sha256:'):
            return line[len('oid sha256:'):].strip()
    raise RuntimeError('INVALID_LFS_OID:' + path)


def safe_receipt(packet, specified=None):
    downloads = pathlib.Path.home() / 'storage/downloads'
    if specified is not None:
        choices = [pathlib.Path(specified).expanduser()]
    else:
        exact = downloads / (PRIOR + '_20261104T204813Z-76d247_RECEIPT.json')
        choices = [exact] if exact.is_file() else sorted(downloads.glob(PRIOR + '_*_RECEIPT.json'))
    matches = []
    for choice in choices:
        if not choice.is_file():
            continue
        try:
            data = json.loads(choice.read_text())
            if data.get('campaign') != PRIOR or data.get('error') != 'DIRTY_AFTER_MODEL_COMMIT':
                continue
            if data.get('headBefore') != EXPECTED_BASE:
                continue
            if not isinstance(data.get('fitReport'), dict):
                continue
            matches.append((choice.resolve(), data))
        except (OSError, ValueError, TypeError):
            continue
    if len(matches) != 1:
        raise RuntimeError('RECOVERY_RECEIPT_NOT_UNAMBIGUOUS:' + str(len(matches)))
    return matches[0]


def verify_packet(packet):
    m = json.loads((packet / 'manifest.json').read_text())
    if m.get('campaign') != CAMPAIGN or set(m.get('files', {})) != NEW_FILES:
        raise RuntimeError('WRONG_RECOVERY_PACKET')
    for rel, expected in m['files'].items():
        p = packet / rel
        if not p.is_file() or p.is_symlink() or digest(p) != expected:
            raise RuntimeError('PACKET_MEMBER_HASH_INVALID:' + rel)
    return m


def preflight(repo, old):
    if not repo.is_dir() or repo.is_symlink():
        raise RuntimeError('RECOVERY_CHECKOUT_MISSING_OR_SYMLINK')
    if pathlib.Path(git(repo, 'rev-parse', '--show-toplevel')).resolve() != repo.resolve():
        raise RuntimeError('RECOVERY_REPOSITORY_ROOT_MISMATCH')
    if git(repo, 'remote', 'get-url', 'origin') != REMOTE:
        raise RuntimeError('RECOVERY_REMOTE_IDENTITY_MISMATCH')
    if git(repo, 'rev-parse', 'HEAD:AGENTS.md') != EXPECTED_AGENTS_BLOB:
        raise RuntimeError('REPO_AGENTS_BLOB_CHANGED')
    if git(repo, 'hash-object', str(repo / 'AGENTS.md')) != EXPECTED_AGENTS_BLOB:
        raise RuntimeError('REPO_AGENTS_CONTENT_MODIFIED')
    actual = git(repo, 'rev-parse', 'HEAD')
    fit = old['fitReport']
    expected_model = fit.get('afterSha256')
    if not re.fullmatch(r'[a-f0-9]{64}', expected_model or ''):
        raise RuntimeError('RECEIPT_NEW_MODEL_SHA_INVALID')
    if old.get('remoteOldModelOid') != EXPECTED_SOURCE_OID:
        raise RuntimeError('RECEIPT_SOURCE_MODEL_OID_MISMATCH')
    if old.get('sourceBlendBytesVerified') is not True or old.get('sourceModelBytesVerified') is not True:
        raise RuntimeError('PRIOR_RUN_DID_NOT_VERIFY_SOURCES')
    if old.get('verifiedPreflight', {}).get('expectedFinalSha256') != expected_model:
        raise RuntimeError('RECEIPT_PREFLIGHT_MISMATCH')
    if not old.get('sourceSampleSha256') or fit.get('beforeSha256') != EXPECTED_SOURCE_OID:
        raise RuntimeError('SOURCE_MOTION_PROVENANCE_MISSING')
    if int(fit.get('clipCount', -1)) != 23 or int(fit.get('weaponTranslationChannelsRemoved', 0)) < 3:
        raise RuntimeError('PRIOR_SOLVER_OUTPUT_INCOMPLETE')
    # `merge-base --is-ancestor` returns no stdout on success. Check exit status.
    check = subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', EXPECTED_BASE, actual], capture_output=True)
    if check.returncode:
        raise RuntimeError('EXPECTED_BASE_NOT_ANCESTOR')
    commits = git(repo, 'log', '--format=%s', EXPECTED_BASE + '..HEAD').splitlines()
    if 'Obsidianti: source v1.2 pelvis contact and weapon-drift repair' not in commits:
        raise RuntimeError('MISSING_V121_SOURCE_COMMIT')
    if 'Obsidianti: correct Lionheart pelvis pitch and remove weapon translation on SAME GLB' not in commits:
        raise RuntimeError('MISSING_V121_MODEL_COMMIT')
    if old.get('scriptCommit') not in git(repo, 'rev-list', EXPECTED_BASE + '..HEAD').splitlines():
        raise RuntimeError('SCRIPT_COMMIT_FROM_RECEIPT_NOT_IN_HISTORY')
    if lfs_oid(repo, 'HEAD', CANONICAL) != expected_model:
        raise RuntimeError('LOCAL_COMMITTED_LFS_POINTER_NOT_EXPECTED_SOLUTION')
    if digest(repo / CANONICAL) != expected_model:
        raise RuntimeError('LOCAL_WORKING_MODEL_BYTES_DIFFER_FROM_COMMIT')
    if lfs_oid(repo, EXPECTED_BASE, CANONICAL) != EXPECTED_SOURCE_OID:
        raise RuntimeError('SOURCE_MODEL_POINTER_CHANGED')
    if git(repo, 'rev-parse', 'HEAD:' + REPL) != git(repo, 'rev-parse', EXPECTED_BASE + ':' + REPL):
        raise RuntimeError('REPL_CHANGED_IN_RECOVERY_CHECKOUT')
    allowed = PRIOR_FILES | NEW_FILES | {CANONICAL}
    modified = git(repo, 'diff', '--name-only', EXPECTED_BASE + '..HEAD').splitlines()
    if not set(modified).issubset(allowed) or CANONICAL not in modified:
        raise RuntimeError('RECOVERY_HISTORY_TOUCHES_UNAUTHORIZED_FILES:' + repr(modified))
    for rel in PRIOR_FILES:
        if subprocess.run(['git', '-C', str(repo), 'cat-file', '-e', 'HEAD:' + rel], capture_output=True).returncode:
            raise RuntimeError('EXPECTED_V121_SOURCE_FILE_MISSING:' + rel)
    return {'headBeforeRecovery': actual, 'expectedFinalSha256': expected_model, 'pelvisPitchClipsApplied': fit.get('pelvisPitchClipsApplied'), 'weaponTranslationChannelsRemoved': fit.get('weaponTranslationChannelsRemoved'), 'priorSourceCommit': old['scriptCommit']}


def inspect_dirty(repo):
    raw = subprocess.run(['git','-C',str(repo),'status','--porcelain=v1','-z','--untracked-files=all'],check=True,capture_output=True).stdout
    entries = []
    for part in raw.split(b'\0'):
        if not part:
            continue
        decoded = part.decode('utf-8', errors='strict')
        if len(decoded) < 4:
            raise RuntimeError('UNRECOGNIZED_GIT_STATUS_ENTRY')
        status, name = decoded[:2], decoded[3:]
        entries.append((status, name))
    return entries


def quarantine_expected_cache(repo, workspace, report):
    entries = inspect_dirty(repo)
    unsafe = [(state, path) for state, path in entries if state != '??' or not CACHE_PATTERN.fullmatch(path)]
    if unsafe:
        raise RuntimeError('UNRELATED_DIRTY_PATHS_PRESENT:' + repr(unsafe))
    moved = []
    if entries:
        destroot = workspace / 'v1.2.2-quarantined-bytecode'
        if destroot.is_symlink() or destroot.exists():
            raise RuntimeError('RECOVERY_CACHE_QUARANTINE_DESTINATION_COLLISION')
        destroot.mkdir()
        for state, path in entries:
            target = repo / path
            if not target.is_file() or target.is_symlink():
                raise RuntimeError('UNEXPECTED_CACHE_FILE_TYPE:' + path)
            content = target.read_bytes()
            if len(content) < 16 or len(content) > 4_000_000 or content[:4] != __import__('importlib.util').util.MAGIC_NUMBER:
                raise RuntimeError('UNVERIFIED_PYTHON_CACHE_BYTES:' + path)
            quarantined = destroot / target.name
            if quarantined.exists():
                raise RuntimeError('CACHE_QUARANTINE_COLLISION:' + path)
            os.replace(target, quarantined)
            moved.append({'path': path, 'quarantinedPath': str(quarantined), 'sha256': digest(quarantined)})
        if inspect_dirty(repo):
            raise RuntimeError('WORKTREE_NOT_CLEAN_AFTER_EXACT_CACHE_QUARANTINE:' + repr(inspect_dirty(repo)))
    report['quarantinedCaches'] = moved


def stage_sources(repo, packet, receipt):
    for rel in sorted(NEW_FILES):
        src = packet / rel
        target = repo / rel
        if target.exists() and digest(target) != digest(src):
            raise RuntimeError('VERSIONED_RECOVERY_DESTINATION_COLLISION:' + rel)
    created = []
    for rel in sorted(NEW_FILES):
        dst = repo / rel
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(packet / rel, dst)
            created.append(rel)
    git(repo, 'add', '--', *sorted(NEW_FILES))
    staged = git(repo, 'diff', '--cached', '--name-only').splitlines()
    if any(path not in NEW_FILES for path in staged):
        raise RuntimeError('RECOVERY_STAGING_OUTSIDE_ALLOWLIST:' + repr(staged))
    if staged:
        if not git(repo, 'config', 'user.name', ok=False):
            git(repo, 'config', 'user.name', 'Obsidianti Termux Campaign')
        if not git(repo, 'config', 'user.email', ok=False):
            git(repo, 'config', 'user.email', 'obsidianti-campaign@users.noreply.github.com')
        git(repo, 'commit', '-m', 'Obsidianti: recover verified v1.2.1 result and prevent Python cache false-dirty gate')
    for rel in sorted(NEW_FILES):
        blob = subprocess.run(['git','-C',str(repo),'show','HEAD:'+rel],capture_output=True,check=True).stdout
        if hashlib.sha256(blob).hexdigest() != digest(packet / rel):
            raise RuntimeError('RECOVERY_SOURCE_GIT_READBACK_MISMATCH:' + rel)
    if inspect_dirty(repo):
        raise RuntimeError('WORKTREE_DIRTY_AFTER_RECOVERY_SOURCE_COMMIT:' + repr(inspect_dirty(repo)))
    receipt['recoveryScriptCommit'] = git(repo, 'rev-parse', 'HEAD')
    receipt['newScriptsCommitted'] = bool(staged)


def remote_head(repo):
    for delay in (0, 2, 4):
        if delay:
            time.sleep(delay)
        p = subprocess.run(['git','-C',str(repo),'ls-remote','origin','refs/heads/main'],capture_output=True,text=True,timeout=45)
        if p.returncode == 0 and p.stdout.split():
            return p.stdout.split()[0]
    raise RuntimeError('REMOTE_MAIN_READ_FAILED')


def publish(repo, receipt):
    before = remote_head(repo)
    local = git(repo, 'rev-parse', 'HEAD')
    if before not in (EXPECTED_BASE, local):
        raise RuntimeError('REMOTE_MAIN_ADVANCED_UNRELATED_NO_FORCE:' + before)
    if before != local:
        # Push LFS object explicitly before pushing the Git pointer.
        lfs = subprocess.run(['git','-C',str(repo),'lfs','push','origin','HEAD'],capture_output=True,text=True,timeout=300)
        if lfs.returncode:
            raise RuntimeError('MODEL_GIT_LFS_PUSH_FAILED:' + lfs.stderr[-1500:])
        push = subprocess.run(['git','-C',str(repo),'push','origin','HEAD:refs/heads/main'],capture_output=True,text=True,timeout=240)
        if push.returncode and shutil.which('gh'):
            push = subprocess.run(['git','-C',str(repo),'-c','credential.helper=!gh auth git-credential','push','origin','HEAD:refs/heads/main'],capture_output=True,text=True,timeout=240)
        if push.returncode:
            raise RuntimeError('GIT_PUSH_FAILED_NO_FORCE:' + push.stderr[-1600:])
    confirmed = remote_head(repo)
    if confirmed != local:
        raise RuntimeError('REMOTE_COMMIT_NOT_VERIFIED: local=' + local + ' remote=' + confirmed)
    git(repo, 'fetch', 'origin', 'main', timeout=150)
    ref = git(repo, 'rev-parse', 'FETCH_HEAD')
    if ref != local:
        raise RuntimeError('POSTFETCH_REMOTE_REVISION_MISMATCH')
    if lfs_oid(repo, 'FETCH_HEAD', CANONICAL) != receipt['expectedFinalSha256']:
        raise RuntimeError('REMOTE_MODEL_LFS_POINTER_INCORRECT')
    if git(repo, 'rev-parse', 'FETCH_HEAD:' + REPL) != git(repo, 'rev-parse', EXPECTED_BASE + ':' + REPL):
        raise RuntimeError('REMOTE_REPL_CHANGED')
    receipt.update({'remoteHeadVerified': confirmed, 'remoteModelPointerSha256': receipt['expectedFinalSha256'], 'remoteLfsObjectBytesIndependentlyDownloaded': False})


def viewer(repo, workspace, receipt):
    viewer_rel = 'review/obsidianti-library-v1.1.0.html'
    if not (repo / viewer_rel).is_file():
        receipt['viewerState'] = 'VIEWER_FILE_NOT_AVAILABLE'
        return
    for port in range(8179, 8188):
        sock = socket.socket()
        try:
            sock.bind(('127.0.0.1', port))
        except OSError:
            continue
        finally:
            sock.close()
        log = open(workspace / ('viewer-recovery-' + str(port) + '.log'), 'ab', buffering=0)
        try:
            p = subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(repo)], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            time.sleep(.5)
            url = 'http://127.0.0.1:' + str(port) + '/' + viewer_rel
            try:
                with urllib.request.urlopen(url, timeout=3) as res:
                    if res.status == 200:
                        receipt.update({'viewerUrl': url, 'viewerPid': p.pid, 'viewerState': 'HTTP_200_NOT_HUMAN_VISUAL_APPROVAL'})
                        return
            except Exception:
                pass
            if p.poll() is None:
                p.terminate()
        finally:
            log.close()
    receipt['viewerState'] = 'NO_FREE_PHONE_HTTP_PORT'


def write_receipt(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp = path.with_suffix('.writing')
    temp.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    os.replace(temp, path)


def main():
    a = argparse.ArgumentParser()
    a.add_argument('packet')
    a.add_argument('--receipt')
    args = a.parse_args()
    packet = pathlib.Path(args.packet).resolve()
    verify_packet(packet)
    original_path, old = safe_receipt(packet, args.receipt)
    workspace = pathlib.Path(old['workdir']).expanduser().resolve()
    expected_parent = (pathlib.Path.home() / '.local/state' / PRIOR).resolve()
    if workspace.parent != expected_parent or workspace.name != original_path.name.removeprefix(PRIOR + '_').removesuffix('_RECEIPT.json'):
        raise RuntimeError('RECOVERY_WORKDIR_NOT_PRIOR_CAMPAIGN_ISOLATED_PATH')
    repo = workspace / 'repo'
    out = pathlib.Path.home() / 'storage/downloads' / (CAMPAIGN + '_' + workspace.name + '_RECEIPT.json')
    record = {'campaign':CAMPAIGN,'sourceReceipt':str(original_path),'sourceError':old['error'], 'sourceHead':EXPECTED_BASE, 'rulesAuthority':'AGENTS.md read and checked against HEAD; live Campaign Etiquette read by author 2026-11-04', 'stage':'PRECHECK', 'modelMutatedByRecovery':False, 'humanVisualAcceptance':'PENDING'}
    write_receipt(out, record)
    try:
        confirmed = preflight(repo, old)
        record.update(confirmed)
        record['stage'] = 'VERIFIED_OLD_MODEL_COMMIT_AND_ACTUAL_MODEL_BYTES'
        write_receipt(out, record)
        print('RECOVERED_LOCAL_MODEL_SHA256=' + confirmed['expectedFinalSha256'], flush=True)
        quarantine_expected_cache(repo, workspace, record)
        record['stage'] = 'EXACT_PYTHON_CACHE_QUARANTINED'
        write_receipt(out, record)
        print('QUARANTINED_GENERATED_CACHE=' + str(len(record['quarantinedCaches'])), flush=True)
        stage_sources(repo, packet, record)
        record['stage'] = 'RECOVERY_SOURCE_GIT_COMMITTED'
        write_receipt(out, record)
        publish(repo, record)
        record['stage'] = 'REMOTE_MODEL_GIT_LFS_POINTER_VERIFIED'
        write_receipt(out, record)
        viewer(repo, workspace, record)
        record['stage'] = 'PUBLISHED_CANDIDATE_VISUAL_REVIEW_PENDING'
        write_receipt(out, record)
        print('STATUS=' + record['stage'] + '\nREMOTE_HEAD=' + record['remoteHeadVerified'] + '\nCANONICAL_MODEL_SHA256=' + record['expectedFinalSha256'] + '\nWEAPON_TRANSLATION_REMOVED=' + str(record['weaponTranslationChannelsRemoved']) + '\nRECEIPT=' + str(out), flush=True)
        if record.get('viewerUrl'):
            print('REVIEW_URL=' + record['viewerUrl'], flush=True)
        return 0
    except Exception as exc:
        record['stage'] = 'BLOCKED_RECOVERY_UNPUBLISHED'
        record['error'] = str(exc)
        write_receipt(out, record)
        print('STATUS=BLOCKED\nREASON=' + str(exc) + '\nRECEIPT=' + str(out), flush=True)
        return 2

if __name__ == '__main__':
    sys.exit(main())
