#!/usr/bin/env python3
"""Exact 90-degree left-hit hips correction, from immutable unmodified v2.0.23 GLB.
Not the measured 62.38 degree pose-fit from rejected v2.0.26.
"""
from __future__ import annotations
import copy,hashlib,json,math,pathlib
V='MUDMAN_HITHEADLEFT_QUARTERTURN_v2.0.27'
BASE_SHA='19304bf8007670e36a38b354b5f8d2ea0c39982c97e2a247acdac1190fe2b7ef'
NORMAL_AXIS=(-1.0,0.0,0.0)
MEASURED_AXIS=(-0.96422,-0.02065,0.2643)
EXPECTED={'Cross-Enemy','Run','BackImpact','Death','HitHeadLeft','HitHeadRightBig','Idle-Cross','Jab-Enemy',
'KnockedBack','ProneBack','ProneBackDamage','ProneBackStandUp','ProneFrontDamage','ProneFront','StandUp',
'StepBack','StepBackLeft','StepBackRight','StepForward','StepForwardLeft','StepForwardRight','StepLeft','StepRight'}
def require(ok,message):
 if not ok:raise RuntimeError(message)
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def apply_one(original,output,base_tools,prior_fix,axis,identity,expected_source=BASE_SHA):
 original,output=pathlib.Path(original),pathlib.Path(output)
 require(original.is_file() and sha(original)==expected_source,'EXACT_ORIGINAL_CURATED_23_CLIP_GLB_REQUIRED')
 require(not output.exists(),'OUTPUT_COLLISION_NO_CLOBBER')
 # These are SHA-locked published helpers. Never import v26 corrected derivative.
 g=prior_fix.load_tools(base_tools)
 js,bin_data=g.glb_load(original)
 names=[a.get('name') for a in js['animations']]
 require(len(names)==23 and set(names)==EXPECTED and len(set(names))==23,'CURATED_23_CLIP_SET_DRIFT')
 hip,head,chain=prior_fix.rig_chain(js)
 require(js['nodes'][hip].get('name')=='mixamorig:Hips','MEASURED_HIPS_NODE_CHANGED')
 target=js['animations'][names.index('HitHeadLeft')]
 rot=prior_fix.rot_channel(g,js,bin_data,target,hip)
 require(rot is not None,'HITHEADLEFT_HIPS_ROTATION_NOT_PRESENT')
 sm=target['samplers'][rot['sampler']]
 vals=g.accessor(js,bin_data,sm['output']);times=g.accessor(js,bin_data,sm['input'])
 require(len(vals)==31 and len(times)==31,'HITHEADLEFT_EXACT_31_ROTATION_KEYS_CHANGED')
 q=prior_fix.axis_angle(axis,math.pi/2) # exactly 90 degrees, NOT 62.38
 require(abs(prior_fix.degrees(q,(0,0,0,1))-90)<1e-8,'MUST_BE_EXACT_90_DEGREES')
 before={a['name']:g.clip_bytes(js,bin_data,a) for a in js['animations']}
 newjs=copy.deepcopy(js);newclip=newjs['animations'][names.index('HitHeadLeft')]
 newbin,mod=prior_fix.write_track(g,newjs,bin_data,newclip,hip,q)
 require(newbin.startswith(bin_data),'ORIGINAL_BUFFER_BYTES_CHANGED')
 for old,new in zip(js['animations'],newjs['animations']):
  if old['name']!='HitHeadLeft':require(old==new,'NON_TARGET_ANIMATION_METADATA_CHANGED_'+old['name'])
 for key in ('nodes','meshes','materials','skins','textures','images','scenes'):
  require(newjs.get(key)==js.get(key),'SCENE_OR_MATERIAL_CHANGED_'+key)
 # Forward model tilt angles from actual head/hip transforms. These are diagnostic,
 # not a fake promise that the new pose is visually acceptable.
 idle=js['animations'][names.index('Idle-Cross')]
 ref_t=prior_fix.clip_range(g,(js,bin_data),idle)[0]
 reference=prior_fix.body_vector(g,js,bin_data,idle,ref_t,hip,head)
 t0,t1=prior_fix.clip_range(g,(js,bin_data),target)
 rows=[]
 for fraction in (0.0,0.07,0.18,0.32,0.5,0.75,1.0):
  t=t0+(t1-t0)*fraction
  oldvec=prior_fix.body_vector(g,js,bin_data,target,t,hip,head)
  newvec=prior_fix.body_vector(g,newjs,newbin,newclip,t,hip,head)
  rows.append({'fraction':fraction,'seconds':round(t,6),'originalBodyUpDotIdle':round(prior_fix.dot(oldvec,reference),6),'quarterTurnBodyUpDotIdle':round(prior_fix.dot(newvec,reference),6)})
 # Real skinned geometry full-vertex witnesses at start, midpoint, end.
 bounds=[]
 for t in (t0,(t0+t1)*.5,t1):
  geo=g.sampled_skinned_bounds(newjs,newbin,newclip,t)
  require(geo.get('witnessVertices',0)>=200,'INSUFFICIENT_REAL_SKINNED_GEOMETRY')
  bounds.append({'time':round(t,6),'minY':geo['minY'],'maxY':geo['maxY'],'witnessVertices':geo['witnessVertices']})
 g.glb_save(newjs,newbin,output)
 reread,rebin=g.glb_load(output)
 require(sha(output)!=sha(original),'NO_QUARTERTURN_CHANGE_WRITTEN')
 require(rebin.startswith(bin_data),'EXPORTED_GLB_REPLACED_OLD_BUFFER')
 for a in reread['animations']:
  if a['name']!='HitHeadLeft':require(g.clip_bytes(reread,rebin,a)==before[a['name']],'OTHER_22_CLIPS_NOT_IDENTICAL_'+a['name'])
 dest_ch=prior_fix.rot_channel(g,reread,rebin,reread['animations'][names.index('HitHeadLeft')],hip)
 actual=g.accessor(reread,rebin,reread['animations'][names.index('HitHeadLeft')]['samplers'][dest_ch['sampler']]['output'])
 for old,new in zip(vals,actual):
  want=prior_fix.mul(q,old)
  require(prior_fix.degrees(new,want)<.005,'EXACT_QUARTERTURN_KEYFRAME_MISMATCH')
 proof={'schema':V,'candidate':identity,'status':'EXACT_90_DEGREE_REVIEW_CANDIDATE_UNAPPROVED',
   'sourceSHA256':sha(original),'candidateSHA256':sha(output),'candidateBytes':output.stat().st_size,
   'axis':list(axis),'quaternion':list(q),'rotationDegrees':90.0,'bone':'mixamorig:Hips','boneNode':hip,
   'rotationKeys':len(vals),'mutation':mod,'originalRotationFirst':list(vals[0]),
   'other22AnimationsByteIdentical':True,'meshesMaterialsSkinsPreserved':True,'originalBinaryPrefixIdentical':True,
   'samples':rows,'realSkinnedBounds':bounds,'visualAcceptance':'PENDING'}
 return proof

if __name__=='__main__':
 raise SystemExit('Run via versioned Termux Git driver, not as a standalone file.')
