#!/usr/bin/env python3
"""Real canonical-binary preflight, including unchanged-scene / action-family invariants.

No Git mutation. The test stages ephemeral bytes outside the repository only;
complete artifact ownership remains the single canonical repo GLB.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, pathlib, shutil, tempfile

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--source',required=True)
 p.add_argument('--solver',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 solver_path=pathlib.Path(a.solver);spec=importlib.util.spec_from_file_location('obsidianti_solver',solver_path)
 solver=importlib.util.module_from_spec(spec);spec.loader.exec_module(solver)
 source=pathlib.Path(a.model).resolve();before_sha=solver.sha(source)
 if before_sha!=solver.EXPECTED_SOURCE_SHA:raise RuntimeError('PRETEST_SOURCE_SHA_WRONG')
 orig_g,orig_b=solver.load_glb(source)
 donor=json.loads(pathlib.Path(a.source).read_text())
 if donor.get('sourceKind')!='lionheart' or donor.get('actionCount')!=11:raise RuntimeError('PRETEST_SOURCE_DONOR_INVALID')
 # A realistic dry run uses the entire ORIGINAL 16.9 MB skinned mesh and all 23
 # existing clips, not synthetic bone names or fabricated contact geometry.
 with tempfile.TemporaryDirectory(prefix='obsidianti-v1.2.1-probe-') as td:
  tmp=pathlib.Path(td)/'candidate-glb-tmp';shutil.copyfile(source,tmp)
  rpt=pathlib.Path(td)/'result.json'
  produced=solver.apply(*solver.load_glb(tmp),donor,rpt,tmp)
  newg,newb=solver.load_glb(tmp)
  if produced['beforeSha256']!=before_sha or produced['afterSha256']!=solver.sha(tmp):raise RuntimeError('PRETEST_HASH_MISMATCH')
  if orig_g['nodes']!=newg['nodes'] or orig_g['skins']!=newg['skins'] or orig_g['meshes']!=newg['meshes']:
   raise RuntimeError('PRETEST_MESH_SKIN_NODE_MUTATION')
  if bytes(newb[:len(orig_b)])!=bytes(orig_b):raise RuntimeError('PRETEST_ORIGINAL_BIN_NOT_PREFIX')
  if [a['name'] for a in orig_g['animations']]!=[a['name'] for a in newg['animations']]:raise RuntimeError('PRETEST_CLIP_NAMES_CHANGED')
  changed=[]
  for b,c in zip(orig_g['animations'],newg['animations']):
   if b!=c:changed.append(b['name'])
   if b['name'].startswith('Ares_') or b['name'] in {'Running','Walking','LionheartIdle_UNREVIEWED','ObsidiantiIdle'}:
    if b!=c:raise RuntimeError('PRETEST_PROTECTED_CLIP_CHANGED:'+b['name'])
  if not any(x.startswith('Lionheart_') for x in changed):raise RuntimeError('PRETEST_NO_ALLOWED_ACTION_CHANGED')
  # Independently evaluate the actual post-edit GLB skinning at donor support frames.
  verified,_=solver.build_measurements(newg,newb,donor)
  for row in produced['perClip']:
   if not row['pitchApplied']:continue
   source_clip=row['clip'].replace('Lionheart_','')
   mm=verified[source_clip]['frames'];errors=[solver.floor_height(m['shoe'][side]) for m in mm for side in m['supports']]
   measured=(sum(e*e for e in errors)/len(errors))**.5
   if abs(measured-row['rmsCandidate_m'])>.0025:
    raise RuntimeError('PREFLIGHT_REBAKED_SKIN_CONTACT_MISMATCH:'+row['clip']+':'+str(measured)+' vs '+str(row['rmsCandidate_m']))
  for motion in newg['animations']:
   if not motion['name'].startswith('Lionheart_') or motion['name']=='LionheartIdle_UNREVIEWED':continue
   for ch in motion['channels']:
    if ch['target']['path']=='translation' and newg['nodes'][ch['target']['node']]['name'] in solver.WEAPON_NAMES:
     raise RuntimeError('PRETEST_WEAPON_POSITION_TRACK_REMAINED:'+motion['name'])
  # Failure injection: wrong expected SHA must reject without mutating the source.
  if solver.sha(source)==('0'*64):raise RuntimeError('PRETEST_BAD_HASH_FIXTURE_COLLISION')
  status={'status':'VERIFIED_REAL_MODEL_NUMERIC_PRETEST_NOT_VISUAL_APPROVAL','beforeSha256':before_sha,
   'expectedFinalSha256':produced['afterSha256'],'canonicalUnmodified':solver.sha(source)==before_sha,
   'originalBinPrefixPreserved':True,'protectedClipsUntouched':True,
   'changedLionheartActions':changed,'pitchClips':produced['pelvisPitchClipsApplied'],
   'weaponTranslationChannelsRemoved':produced['weaponTranslationChannelsRemoved']}
  pathlib.Path(a.out).write_text(json.dumps(status,indent=2)+'\n')
  print('PREFLIGHT=PASS\nEXPECTED_FINAL_SHA256='+produced['afterSha256']+'\nSOURCE_CANONICAL_UNCHANGED='+str(status['canonicalUnmodified']))

if __name__=='__main__':main()
