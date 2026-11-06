#!/usr/bin/env python3
"""Read-only archaeology of prior Obsidianti work in exact Termux checkout."""
from __future__ import annotations
import datetime,hashlib,json,pathlib,re,subprocess,sys
repo=pathlib.Path(sys.argv[1]);dest=pathlib.Path(sys.argv[2]);dest.mkdir(parents=True,exist_ok=True)
def git(*args):
 x=subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True,timeout=90)
 if x.returncode:raise RuntimeError('ARCHAEOLOGY_GIT_FAIL '+repr(args)+' '+x.stderr[-600:])
 return x.stdout
paths=git('ls-files').splitlines()
relevant=[p for p in paths if ('obsidianti' in p.lower() or 'lionheart' in p.lower() or 'ARES_FK' in p or 'LIONHEART' in p) and (p.endswith(('.md','.json','.py','.sh')))]
key=['campaigns/OBSIDIANTI_SOURCE_SAMPLER_v1.1.0.py','campaigns/OBSIDIANTI_GLTF_LIBRARY_v1.1.0.py','docs/obsidianti/FULL_LIBRARY_v1.1.0.md','docs/obsidianti/ARES_FK_REBASE_v1.0.1.md','campaigns/OBSIDIANTI_ARES_FK_REBASE_APPLY_v1.0.1.py','campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py','campaigns/OBSIDIANTI_CONTACT_IK_SOLVE_v1.3.0.py']
missing=[p for p in key if not (repo/p).is_file()]
if missing:raise RuntimeError('MANDATORY_HISTORICAL_CODE_MISSING '+repr(missing))
original=(repo/key[0]).read_text();transfer=(repo/key[1]).read_text()
assert "if a.kind=='lionheart':" in original and 'bpy.ops.wm.open_mainfile' in original and 'bpy.ops.import_scene.gltf' in original,'HISTORICAL_IMPORT_BRANCHES_MISSING'
assert 'def rebase_source_pose(' in transfer and 'qbase=mapped(' in transfer and 'qnow=mapped(' in transfer,'HISTORICAL_RETARGET_ALGORITHM_MISSING'
tracked=[]
for p in relevant:
 raw=(repo/p).read_bytes();digest=hashlib.sha256(raw).hexdigest();record={'path':p,'sizeBytes':len(raw),'SHA256':digest}
 if p.endswith(('.md','.json')) and len(raw)<100000:
  try:
   content=raw.decode('utf-8')
   record['lines']=len(content.splitlines())
   if p.endswith('.json'):
    obj=json.loads(content)
    record['topLevelKeys']=sorted(obj) if isinstance(obj,dict) else []
    for k in ('status','sourceSha256','candidateSha256','algorithm','modelCommit','sourceCommit','sourceBlendSHA256','originalSource','maxFootError_m'):
     if isinstance(obj,dict) and k in obj:record[k]=obj[k] if not isinstance(obj[k],(dict,list)) else '[STRUCTURED]'
   else:
    record['headings']=[l.strip() for l in content.splitlines() if l.startswith('#')][:12]
  except (UnicodeError,ValueError) as e:record['parseWarning']=str(e)
 tracked.append(record)
history=git('log','--all','--format=%h|%ad|%s','--date=short','-n','120','--','campaigns/','docs/obsidianti/').splitlines()
report={'schema':'obsidianti-existing-research-index-v1.2.0','gitHead':git('rev-parse','HEAD').strip(),'repository':'Valar05/parametric-parambulator','numberOfRelevantTrackedFiles':len(tracked),'priorArtifacts':tracked,'recentCampaignHistory':history,'originalImportProvenance':{'script':key[0],'lionheart':'BLEND_OPEN_MAINFILE','ares':'GLTF_IMPORT','evaluatedPoseSampling':'pb.matrix in Blender depsgraph','restPoseMapping':key[1],'sourceToApprovedIdleQuatRebase':'offset = approved_target_idle * inverse(mapped_source_idle); output = offset * mapped_source_pose','pelvisTransfer':'source hip world-space delta added to approved target hip, with a single global translation, without per-foot world-space lock','glbRotations':'LINEAR interpolation at sampled source action frames'},'cautions':['Historic script explicitly evaluated source IK; merely changing the Lionheart file format does not repair geometry-dependent retarget error.','The source and target may have different rest poses; local rotations matching do not establish equal world-space foot placement.','This index is repository archaeology, not evidence that any past visual report was accepted.']}
(dest/'ARCHAEOLOGY_INDEX.json').write_text(json.dumps(report,indent=2)+'\n')
print('ARCHAEOLOGY_INDEXED_FILES='+str(len(tracked)))
print('ORIGINAL_IMPORT_BRANCH=Lionheart_Blend_Ares_Glb')
