#!/usr/bin/env python3
"""Add exactly the latest v2.0.16 Lionheart ARP set to the verified v2.0.31 30-clip GLB.
No retarget, no silent clip replacement, no mesh/skin/material/shield mutation.
"""
from __future__ import annotations
import copy,hashlib,importlib.util,json,pathlib,sys
sys.dont_write_bytecode=True
VERSION='OBSIDIANTI_ANIMATION_REUNION_v2.0.32'
BASE_SHA='53339b746023c096c1df7196f3adeb29702f63345d45f8fcec75dde49d500b66'
DONOR_SHA='e7f60fea731fd9537380868adbb52fee63df34fdf1b6d7694bc39925b440fa1d'
CANON_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
LIONHEART=('Lionheart_Idle','Lionheart_Cast','Lionheart_Heavy1','Lionheart_Heavy2','Lionheart_Heavy3','Lionheart_Kick','Lionheart_Light1','Lionheart_Light2','Lionheart_Light3','Lionheart_SpringAttack','Lionheart_Stomp')
PRESERVED=('Running','ObsidiantiIdle','Ares_StepForward_Lower','Ares_StepForwardLeft_Lower','Ares_StepLeft_Lower','Ares_StepBackLeft_Lower','Ares_StepBack_Lower','Ares_StepBackRight_Lower','Ares_StepRight_Lower','Ares_StepForwardRight_Lower','Vanguard_0T-Pose','Vanguard_ClubIdle','Vanguard_Idle','Vanguard_Jump','Vanguard_JumpCrouch','Vanguard_JumpForward','Vanguard_Land','Vanguard_LedgeClimb','Vanguard_LedgeGrab','Vanguard_LedgeGrabHang','Vanguard_Midair','Vanguard_MidairSwordAttack1','Vanguard_MidairSwordAttack2','Vanguard_RunForwardOld','Vanguard_SpinAttack','Vanguard_SwordAttack1','Vanguard_SwordAttack2','Vanguard_SwordAttack4','Vanguard_SwordAttack5','AxeKick')

def require(cond,message):
 if not cond:raise RuntimeError(message)

def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def load_prior(path):
 p=pathlib.Path(path)
 require(p.is_file(),'PINNED_V231_COMPOSER_MISSING')
 spec=importlib.util.spec_from_file_location('obs_reunion_v231_schema',p)
 require(spec and spec.loader,'V231_COMPOSER_IMPORT_UNAVAILABLE')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module

def compose(base30,donor16,canonical,output,report,prior_source,
            expected_base=BASE_SHA,expected_donor=DONOR_SHA,expected_canon=CANON_SHA):
 base30,donor16,canonical,output,report=map(pathlib.Path,(base30,donor16,canonical,output,report))
 for file,dig,label in [(base30,expected_base,'V231_30_CLIP'),(donor16,expected_donor,'V216_LIONHEART'),(canonical,expected_canon,'ORIGINAL_CANONICAL')]:
  require(file.is_file() and digest(file)==dig,label+'_SHA256_MISMATCH')
 require(not output.exists() and not report.exists(),'OUTPUT_DESTINATION_ALREADY_EXISTS')
 c=load_prior(prior_source)
 base,oldbin=c.read_glb(base30);donor,srcbin=c.read_glb(donor16);canon,canonbin=c.read_glb(canonical)
 priornames=[x['name'] for x in base['animations']]
 require(priornames==list(PRESERVED),'V231_PRESERVED_30_CLIPS_INVENTORY_OR_ORDER_CHANGED')
 donor_names=[x['name'] for x in donor['animations']]
 require(len(donor_names)==23 and set(LIONHEART).issubset(set(donor_names)),'V216_DONOR_MISSING_LIONHEART_ACTION')
 require(len(donor_names)==len(set(donor_names)),'V216_DUPLICATE_SOURCE_ACTION')
 for attr in ('nodes','meshes','skins','materials','textures','images','scenes'):
  require(base.get(attr)==canon.get(attr),'V231_BASE_MODEL_NOT_CANONICAL_'+attr)
 require(oldbin.startswith(canonbin),'CANONICAL_GEOMETRY_BIN_NOT_PRESERVED')
 original=copy.deepcopy(base)
 app=c.Appender(copy.deepcopy(base),oldbin)
 names=c.name_ids(app.js)
 transferred=[]
 for name in LIONHEART:
  source=next(x for x in donor['animations'] if x['name']==name)
  check=c.check_animation_transfer(donor,app.js,source)
  out=app.copy_clip(donor,srcbin,source,name,names)
  require(len(out['channels'])==len(source['channels']) and len(out['samplers'])==len(source['samplers']), 'TRANSFER_CHANNEL_OR_SAMPLER_LOSS_'+name)
  for source_ch,target_ch in zip(source['channels'],out['channels']):
   bs=donor['nodes'][source_ch['target']['node']].get('name')
   bt=app.js['nodes'][target_ch['target']['node']].get('name')
   require(bs==bt and source_ch['target']['path']==target_ch['target']['path'],'TRANSFER_BONE_PATH_MISMATCH_'+name)
  for left,right in zip(source['samplers'],out['samplers']):
   for k in ('input','output'):
    require(c.raw_accessor(donor,srcbin,left[k])==c.raw_accessor(app.js,app.bin,right[k]),'SOURCE_ANIMATION_SAMPLE_CHANGED_'+name+'_'+k)
  start,end=c.range_times(donor,srcbin,source)
  require(end>=start and (end-start)>.01,'RETARGET_DURATION_MISSING_'+name)
  transferred.append({'name':name,'sourceSHA256':digest(donor16),'source':'ARP v2.0.16 Hips Location ON','channels':check['channels'],'uniqueTargets':check['uniqueTargets'],'durationSeconds':round(end-start,6),'sourceSamplersPreserved':True})
 require(app.js['animations'][:30]==original['animations'],'PREVIOUS_30_CLIPS_MODIFIED')
 require([a['name'] for a in app.js['animations']]==list(PRESERVED)+list(LIONHEART),'OUTPUT_41_CLIP_INVENTORY_INVALID')
 for key in ('nodes','meshes','skins','materials','textures','images','scenes'):
  require(app.js.get(key)==original.get(key),'ORIGINAL_MODEL_STRUCTURE_MODIFIED_'+key)
 require(bytes(app.bin[:len(oldbin)])==oldbin,'PREVIOUS_30_CLIP_SOURCE_BINARY_CHANGED')
 output.parent.mkdir(parents=True,exist_ok=True)
 c.glb_save(app.js,bytes(app.bin),output)
 out,reb=c.read_glb(output)
 require(len(out['animations'])==41 and out['animations'][:30]==original['animations'],'REOPENED_GLTF_LOST_OLD_CLIPS')
 require(reb.startswith(oldbin),'REOPENED_GLTF_CHANGED_ORIGINAL_BUFFER')
 for key in ('nodes','meshes','skins','materials','textures','images','scenes'):
  require(out.get(key)==canon.get(key),'REOPENED_MODEL_NOT_ORIGINAL_'+key)
 result={'schema':VERSION,'status':'41_CLIP_SHIELD_AND_LANCE_REVIEW_UNAPPROVED','count':41,
         'outSHA256':digest(output),'outBytes':output.stat().st_size,
         'inputThirtySHA256':digest(base30),'v216LionheartSHA256':digest(donor16),
         'originalCanonicalSHA256':digest(canonical),'preservedFirstThirtyNames':list(PRESERVED),
         'appended':transferred,'sourceV216DonorCount':len(donor_names),
         'original30AnimationsJSONUnchanged':True,'original30BinaryPrefixUnchanged':True,
         'shieldAndLanceAndRigAndMaterialsUnchanged':True,'importedLionheartClips':11,
         'vanguardAnimationsPreserved':19,'historicalAresGuardStepsPreserved':8,
         'authorIdleAnimationPreserved':True,'axekickPreserved':True,'lionheartV219ToeRollExperimentNotImported':True,
         'noARPRerun':True,'noCanonicalMutation':True,'ownerVisualAcceptance':'PENDING'}
 report.parent.mkdir(parents=True,exist_ok=True)
 report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 return result

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser()
 for key in ('base','donor','canonical','output','report','prior-source'):p.add_argument('--'+key,required=True)
 a=p.parse_args();print(json.dumps(compose(a.base,a.donor,a.canonical,a.output,a.report,a.prior_source),indent=2))
