#!/usr/bin/env python3
"""One-clip fix 3D A/B viewer from SHA-locked previous working viewer.
Keeps exact clip selection, texture check, ground origin and all previous controls.
"""
from __future__ import annotations
import hashlib,pathlib
VERSION='MUDMAN_HITHEADLEFT_AXIS_v2.0.25'
PREV='Mudman | Godot curation 2.0.24'
CURR='Mudman | HitHeadLeft axis repair 2.0.25'

def replace_once(s,old,new):
 if s.count(old)!=1:raise RuntimeError('VIEWER_TEMPLATE_FRAGMENT_MISMATCH_'+str(s.count(old))+'_'+old[:70])
 return s.replace(old,new,1)

def build(text):
 s=replace_once(text,PREV,CURR)
 s=replace_once(s,'<option value="candidate">Purchased ARP retarget</option><option value="original" disabled>Original not available for these actions</option>',
  '<option value="candidate">Corrected HitHeadLeft · review</option><option value="original">Before repair · same animations</option>')
 s=replace_once(s,"const featured=['Jab-Enemy','Cross-Enemy','Idle-Cross','Run'];",
  "const featured=['HitHeadLeft','HitHeadRightBig','Jab-Enemy','Cross-Enemy','Idle-Cross','Run'];")
 s=replace_once(s,"el('identity').textContent+=' | TEXTURED '+texturedMeshes+'/'+physicalMeshes;",
  "const identity=el('identity');identity.textContent=identity.textContent.replace(/(?:\\s*\\|\\s*TEXTURED \\d+\\/\\d+)+$/,'')+' | TEXTURED '+texturedMeshes+'/'+physicalMeshes;")
 s=replace_once(s,'Review 23 Godot-mapped enemy clips on the textured, floor-grounded Mudman.',
  'Review the real HitHeadLeft root-axis correction against the original GLB. Only HitHeadLeft rotation data may differ; all other 22 clips, UVs, textures, mesh, and ground origin are preserved.')
 if 'EXACT_ANIMATION_SELECTION_FAILED_' not in s:raise RuntimeError('EXACT_STANDUP_SELECTOR_REGRESSED')
 if 'MUDMAN_TEXTURE_NOT_MAPPED' not in s:raise RuntimeError('MESHY_MATERIAL_REGRESSED')
 if "floor.position.y=Number(el('ground').value)" not in s:raise RuntimeError('Y_ZERO_GROUND_REGRESSED')
 if 'value="original" disabled' in s:raise RuntimeError('A_B_VIEWER_NOT_ENABLED')
 return s

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');a=p.parse_args()
 pathlib.Path(a.output).write_text(build(pathlib.Path(a.source).read_text()))
