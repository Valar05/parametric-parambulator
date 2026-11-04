#!/usr/bin/env python3
"""Packet and canonical GLB guard for Obsidianti, using Python stdlib only.

This verifier does NOT prove visual acceptance, foot contact, or live playback.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

CAMPAIGN = 'OBSIDIANTI_IDLE_CANONICAL_v1.0.0'
CANONICAL = 'assets/obsidianti/Obsidianti.glb'
CANDIDATE = 'payload/Obsidianti.idle-candidate.glb'
ORIGINAL = 'payload/Obsidianti.original.glb'
EXP_SOURCE = {
    'payload/Obsidianti.original.glb': '171d6d9d92fde6c65c0ed2eefc6a5a1fa86d2b0e48a9c3395582658610a9093a',
    'payload/Obsidianti.idle-candidate.glb': '27f943ddf1ba1f72169026a2cb4750662f00b053f78e4346f43b3888c744e95b',
    'payload/Obsidianti.blend': '68f7b29cfa76e0cc300d72fc37062ba786c1d6c75841f0b3a9c1ae78dbd33ce1',
    'payload/LionheartLancer.blend': '81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4',
}

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(2**20), b''):
            h.update(b)
    return h.hexdigest()

def fail(message: str):
    raise SystemExit('VERIFY_FAIL: ' + message)

def glb(path: Path):
    b = path.read_bytes()
    if len(b) < 28 or b[:4] != b'glTF':
        fail(f'not a GLB: {path}')
    _, ver, length = struct.unpack_from('<4sII', b)
    if ver != 2 or length != len(b):
        fail(f'invalid GLB header: {path}')
    n, chunk = struct.unpack_from('<I4s', b, 12)
    if chunk != b'JSON' or n % 4 or n > len(b)-28:
        fail(f'invalid GLB JSON chunk: {path}')
    g = json.loads(b[20:20+n])
    offset = 20 + n
    m, chunk2 = struct.unpack_from('<I4s', b, offset)
    if chunk2 != b'BIN\0' or offset+8+m != len(b) or m % 4:
        fail(f'invalid GLB BIN chunk: {path}')
    if g.get('buffers', [{}])[0].get('byteLength', 0) > m:
        fail(f'GLB buffer length out of bounds: {path}')
    return g, b[offset+8:]

def check_pose(original: Path, candidate: Path):
    g0, b0 = glb(original)
    g1, b1 = glb(candidate)
    if not b1.startswith(b0):
        fail('the candidate overwrote preexisting source BIN bytes')
    for name in ('nodes','skins','meshes','materials','images','textures','samplers','extensionsUsed'):
        if g0.get(name) != g1.get(name):
            fail('candidate changes protected glTF section '+name)
    if len(g0['animations']) != 2 or len(g1['animations']) != 3:
        fail('expected 2 original clips and exactly 1 added Idle candidate')
    if g0['animations'] != g1['animations'][:2]:
        fail('original Walking/Running clips changed')
    if [a['name'] for a in g1['animations']] != ['Running','Walking','LionheartIdle_UNREVIEWED']:
        fail('animation naming/order changed')
    roots0 = g0['scenes'][0]['nodes']
    roots1 = g1['scenes'][0]['nodes']
    if roots0 != [77,78,79] or roots1 != [77]:
        fail(f'incorrect cloth root exclusion: {roots0} -> {roots1}')
    for name, n in (('geometry_0.001',78),('TabardHang',79)):
        x = g1['nodes'][n]
        if x.get('name') != name or 'skin' in x or 'mesh' not in x:
            fail(f'unused cloth root identity mismatch for {name}')
    skinj = g1['skins'][0]['joints']
    if len(skinj) != 73:
        fail(f'not expected 73 exported skin joints: {len(skinj)}')
    if len(g1['animations'][2]['channels']) != 28:
        fail('Idle candidate does not contain 27 bone rotations + 1 Hips translation')
    by_name = {n.get('name'):i for i,n in enumerate(g1['nodes'])}
    for x in ('mixamorig:LeftWeapon.L','mixamorig:RightWeapon.R','mixamorig:HeadCrest.001','mixamorig:HeadCrest.005'):
        if x not in by_name:
            fail('missing skinned weapon/hair bone: '+x)
    for x in ('mixamorig:LeftWeapon.L','mixamorig:RightWeapon.R'):
        bone = by_name[x]
        if not any(c['target']['node'] == bone and c['target']['path']=='rotation' for c in g1['animations'][-1]['channels']):
            fail('Idle does not animate independently rigged weapon: '+x)
    # Every animation sampler's accessor must exist and remain in the single embedded binary.
    count = len(g1['accessors'])
    for anim in g1['animations']:
        for channel in anim['channels']:
            sid = channel['sampler']
            if not 0 <= sid < len(anim['samplers']): fail('animation sampler out of range')
        for smp in anim['samplers']:
            for fld in ('input','output'):
                ai = smp[fld]
                if not 0 <= ai < count: fail('animation accessor out of range')
                acc = g1['accessors'][ai]
                if not 0 <= acc.get('bufferView',-1) < len(g1['bufferViews']):fail('animation view out of range')
    return {
        'status':'STRUCTURAL_PASS_VISUAL_PENDING',
        'animationNames':[x['name'] for x in g1['animations']],
        'skinnedJointReferences':len(skinj),
        'idleChannels':len(g1['animations'][-1]['channels']),
        'clothExcluded':['geometry_0.001','TabardHang'],
        'originalBinBytesPreserved':len(b0),
        'targetSourceSha256':sha(original),
        'candidateSha256':sha(candidate),
        'note':'No Blender or phone viewer playback, visible acceptance or foot-contact evaluation is implied.'
    }

def verify_packet(root: Path):
    manifest = json.loads((root/'manifest.json').read_text())
    if manifest.get('campaign') != CAMPAIGN:
        fail('wrong packet campaign')
    files=manifest.get('files')
    if not isinstance(files,dict) or len(files)<7:
        fail('incomplete packet manifest')
    actual=set(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='manifest.json')
    if set(files)!=actual:
        fail(f'packet member mismatch missing={sorted(set(files)-actual)} extra={sorted(actual-set(files))}')
    for n, expected in files.items():
        p=(root/n).resolve()
        if not p.is_relative_to(root.resolve()) or not p.is_file() or p.is_symlink():
            fail('unsafe packet path '+n)
        actualsha=sha(p)
        if actualsha != expected:
            fail(f'packet file hash mismatch {n}: expected {expected}, got {actualsha}')
    for n, expected in EXP_SOURCE.items():
        if files.get(n)!=expected:
            fail(f'original source lock mismatch: {n}')
    info=check_pose(root/ORIGINAL,root/CANDIDATE)
    info['packetEntries']=len(files)
    info['campaign']=CAMPAIGN
    return info

def canonical_check(root:Path, canon:Path):
    if sha(canon)!=EXP_SOURCE[CANDIDATE]:
        fail('canonical model differs from approved-by-image candidate, refusing overwrite')
    info=check_pose(root/ORIGINAL,canon)
    parent=canon.parent
    other=[p.name for p in parent.glob('*.glb') if p.name!='Obsidianti.glb']
    if other:fail('multiple canonical GLBs detected: '+str(other))
    return info

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--packet-root',required=True)
    ap.add_argument('--canonical')
    args=ap.parse_args()
    root=Path(args.packet_root).resolve()
    info=verify_packet(root)
    if args.canonical:
        info['canonical']=canonical_check(root,Path(args.canonical))
    print(json.dumps(info,indent=2,sort_keys=True))
if __name__=='__main__':
    main()
