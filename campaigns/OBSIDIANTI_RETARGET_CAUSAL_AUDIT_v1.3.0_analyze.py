#!/usr/bin/env python3
"""Obsidianti v1.3.0: read-only, per-stage bilateral source->target causal audit.

Does not alter GLB, Blender source, or accepted animations. All conclusions are
limited to the exact SHA-identified source and historical pre-contact target.
"""
from __future__ import annotations
import argparse, collections, hashlib, importlib.util, json, math, pathlib, statistics

SIDES=('Left','Right')
MOVES=('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
BONENAMES=('UpLeg','Leg','Foot','ToeBase')
HIP='mixamorig:Hips'

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def load_module(path, name):
 spec=importlib.util.spec_from_file_location(name,str(path))
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return m

def vsub(a,b):return [float(x-y) for x,y in zip(a,b)]
def vadd(a,b):return [float(x+y) for x,y in zip(a,b)]
def vscale(a,r):return [float(r*x) for x in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def rms(v):return math.sqrt(sum(x*x for x in v)/len(v)) if v else None
def stats(v):
 return {'n':len(v),'max':round(max(v),7),'rms':round(rms(v),7),'mean':round(statistics.mean(v),7)} if v else None

def p(m):return [float(m[3]),float(m[7]),float(m[11])]
def local_rot(mod,tr,node,time):
 k=(node,'rotation')
 if k not in tr:return None
 tt,q=tr[k]
 return mod.sampled(tt,q,time,True)
def angular_error_deg(a,b):
 if a is None or b is None:return None
 n=lambda x:math.sqrt(sum(y*y for y in x))
 d=abs(dot(a,b))/(n(a)*n(b));return math.degrees(2*math.acos(max(-1,min(1,d))))

def freeze(tr):
 """Freeze every animated property at its t=0 value, preserving accessor type."""
 return {k:([0.,1.],[modval[1][0],modval[1][0]]) for k,modval in tr.items()}

def ablated(mod,g,real,frz,ids,t):
 tracks=dict(frz)
 for k in ids:
  if k in real:tracks[k]=real[k]
 return mod.global_matrices(g,tracks,t)

def fit_common_hip_scale(rows, low=0., high=2.):
 """Closed-form 1D vertical hip displacement fit, evaluated on source support frames.

 targetFootY(delta; a) = recordedTargetFootDeltaY + (a-1)*targetHipDeltaY
 The regression is *diagnostic*, never silently edits any GLB.
 """
 den=sum(q['targetHipDY']**2 for q in rows)
 if den<1e-12:return None
 num=sum(q['targetHipDY']*(q['targetFootDY']-q['sourceFootDY']*q['lengthRatio']-q['targetHipDY']) for q in rows)
 raw=-num/den
 alpha=min(high,max(low,raw))
 def calc(a):return rms([q['targetFootDY']+(a-1)*q['targetHipDY']-q['sourceFootDY']*q['lengthRatio'] for q in rows])
 return {'unconstrained':round(raw,6),'fitWithin0to2':round(alpha,6),
         'rmsRecorded_m':round(calc(1.),7),'rmsOptimal_m':round(calc(alpha),7),
         'rmsZeroHipMotion_m':round(calc(0.),7),'sampleCount':len(rows)}

def selftest():
 # One motion common to both feet can be removed by matching source displacement.
 rows=[{'targetHipDY':0.1,'targetFootDY':0.1,'sourceFootDY':0.,'lengthRatio':.87},
       {'targetHipDY':0.2,'targetFootDY':0.2,'sourceFootDY':0.,'lengthRatio':.87}]
 a=fit_common_hip_scale(rows)
 assert abs(a['fitWithin0to2'])<1e-7 and a['rmsOptimal_m']<1e-7
 # Equal common hip shift but unequal foot motions: no common root scalar can cancel both.
 rows=[{'targetHipDY':0.1,'targetFootDY':0.1,'sourceFootDY':0.,'lengthRatio':.87},
       {'targetHipDY':0.1,'targetFootDY':0.2,'sourceFootDY':0.,'lengthRatio':.87}]
 a=fit_common_hip_scale(rows)
 assert a['rmsOptimal_m']>.070 and a['rmsOptimal_m']<.071,a
 assert angular_error_deg([0,0,0,1],[0,0,0,-1])<1e-7
 assert norm(vsub([1,2,3],[0,2,1]))==math.sqrt(5)
 return True

def audit(args):
 selftest()
 target_sha=sha(args.model)
 if target_sha!=args.expected_model_sha:raise RuntimeError('WRONG_HISTORICAL_MODEL_HASH '+target_sha)
 donor_sha=sha(args.donor)
 if donor_sha!=args.expected_donor_samples_sha and args.expected_donor_samples_sha!='ANY_VERIFIED_FRESH_SOURCE':
  raise RuntimeError('SOURCE_EVALUATION_SAMPLE_SHA_MISMATCH '+donor_sha)
 donor=json.loads(pathlib.Path(args.donor).read_text())
 if donor.get('sourceKind')!='lionheart' or not set(MOVES).issubset(donor['actions']):raise RuntimeError('WRONG_DONOR_KIND_OR_CLIP_SET')
 evalmod=load_module(args.evaluator,'original_historical_glb_eval')
 importer=load_module(args.importer,'original_historical_retarg')
 g,b=evalmod.load_glb(args.model)
 names={n.get('name',''):i for i,n in enumerate(g['nodes']) if n.get('name')}
 needed=[HIP,*[f'mixamorig:{side}{part}' for side in SIDES for part in BONENAMES]]
 absent=[name for name in needed if name not in names]
 if absent:raise RuntimeError('MISSING_TARGET_BONES '+repr(absent))
 animations={a['name']:a for a in g['animations']}
 if not all('Lionheart_'+name in animations for name in MOVES):raise RuntimeError('MISSING_TARGET_CLIPS')
 approved,_=importer.approved_idle(g,b)
 rest=importer.ref_quats(g)
 base=donor['actions']['Idle']['frames'][0]
 floor=min(base['bones'][f'mixamorig:{side}ToeBase']['worldPosition'][1] for side in SIDES)
 witness,skin,ibm=evalmod.foot_witnesses(g,b)
 out={'schema':'obsidianti-retarget-causal-audit-v1.3.0',
      'state':'SOURCE_AND_TARGET_EVALUATED_DIAGNOSTIC_ONLY',
      'originalBlendSHA256':args.blend_sha,'sourceSamplesSHA256':donor_sha,
      'historicalGLBSHA256':target_sha,'targetRole':getattr(args,'target_role','historical'),'sourceImporter':'campaigns/OBSIDIANTI_GLTF_LIBRARY_v1.1.0.py',
      'sourceEvaluator':'campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py',
      'sourceFloorToeY_m':round(floor,7),'modelNodeCount':len(g['nodes']),
      'modelAnimationCount':len(g['animations']), 'clips':{},'interpretationWarnings':[],
      'canonicalModelMutated':False}
 for name in MOVES:
  source=donor['actions'][name]['frames'];an=animations['Lionheart_'+name]
  if len(source)<4:raise RuntimeError('TOO_FEW_SOURCE_FRAMES '+name)
  times=[float(row['time']) for row in source]
  if any(b<=a for a,b in zip(times,times[1:])):raise RuntimeError('NONMONOTONIC_SOURCE_TIME '+name)
  tr=evalmod.channels(g,b,an)
  frz=freeze(tr)
  initial=evalmod.global_matrices(g,tr,times[0])
  first={s:{'targetHip':p(initial[names[HIP]]),'targetFoot':p(initial[names[f'mixamorig:{s}Foot']]),
            'sourceHip':source[0]['bones'][HIP]['worldPosition'],
            'sourceFoot':source[0]['bones'][f'mixamorig:{s}Foot']['worldPosition']} for s in SIDES}
  origin_sep=vsub(first['Right']['targetFoot'],first['Left']['targetFoot'])
  source_sep=vsub(first['Right']['sourceFoot'],first['Left']['sourceFoot'])
  leg_len={}
  for side in SIDES:
   n=[f'mixamorig:{side}{part}' for part in ('UpLeg','Leg','Foot')]
   st=[source[0]['bones'][x]['worldPosition'] for x in n]
   tt=[p(initial[names[x]]) for x in n]
   sl=norm(vsub(st[1],st[0]))+norm(vsub(st[2],st[1]))
   tl=norm(vsub(tt[1],tt[0]))+norm(vsub(tt[2],tt[1]))
   if min(sl,tl)<.1:raise RuntimeError('UNEXPECTED_CHAIN_LENGTH '+name+side)
   leg_len[side]={'source_m':round(sl,7),'target_m':round(tl,7),'ratio':tl/sl}
  rec=[]
  qt_err={side:{bone:[] for bone in ('UpLeg','Leg','Foot')} for side in SIDES}
  qt_key={side:{bone:[] for bone in ('UpLeg','Leg','Foot')} for side in SIDES}
  qt_mid={side:{bone:[] for bone in ('UpLeg','Leg','Foot')} for side in SIDES}
  stages={side:{stage:[] for stage in ('HipTranslation','HipRotation','UpperLegRotation','ShinRotation','FootRotation')} for side in SIDES}
  sep_d=[]; src_sep_d=[]; contacts=[];sole_diff=[]
  for frame in source:
   t=float(frame['time']);srcbones=frame['bones'];full=evalmod.global_matrices(g,tr,t)
   mapped=importer.rebase_source_pose(frame,base,g,rest,approved,source)
   row={'t_s':round(t,6),'sides':{}}
   byside={}
   for side in SIDES:
    fq=f'mixamorig:{side}Foot';foot=p(full[names[fq]])
    hip=p(full[names[HIP]])
    srcfoot=srcbones[fq]['worldPosition'];srchip=srcbones[HIP]['worldPosition']
    f=first[side]
    tf=vsub(foot,f['targetFoot']); th=vsub(hip,f['targetHip'])
    sf=vsub(srcfoot,f['sourceFoot']);sh=vsub(srchip,f['sourceHip']);ratio=leg_len[side]['ratio']
    expectedSF=vscale(sf,ratio);expectedSH=vscale(sh,ratio)
    root_y=th[1]-expectedSH[1]
    limb_y=(tf[1]-th[1])-ratio*(sf[1]-sh[1])
    if abs((root_y+limb_y)-(tf[1]-expectedSF[1]))>1e-5:raise RuntimeError('VERTICAL_CAUSAL_DECOMPOSITION_IDENTITY_FAIL')
    contact=abs(srcbones[f'mixamorig:{side}ToeBase']['worldPosition'][1]-floor)<0.055
    steps=[]
    k=[(names[HIP],'translation'),(names[HIP],'rotation'),
       (names[f'mixamorig:{side}UpLeg'],'rotation'),
       (names[f'mixamorig:{side}Leg'],'rotation'),
       (names[f'mixamorig:{side}Foot'],'rotation')]
    active=[];prev=p(ablated(evalmod,g,tr,frz,active,t)[names[fq]])
    for channel,stage in zip(k,stages[side]):
     active.append(channel)
     now=p(ablated(evalmod,g,tr,frz,active,t)[names[fq]])
     stage_delta=now[1]-prev[1];stages[side][stage].append(stage_delta)
     steps.append(round(stage_delta,7));prev=now
    if norm(vsub(prev,foot))>.00015:raise RuntimeError('FK_STAGE_RECONSTRUCTION_MISMATCH '+name+' '+side+' '+str(t))
    q_errors={}
    for bone in ('UpLeg','Leg','Foot'):
     bn=f'mixamorig:{side}{bone}'
     qq=angular_error_deg(mapped.get(names[bn]),local_rot(evalmod,tr,names[bn],t))
     if qq is None:raise RuntimeError('ROTATION_CHANNEL_MISSING '+bn)
     qt_err[side][bone].append(qq)
     if abs(frame['sourceFrame']-round(frame['sourceFrame']))<1e-5:qt_key[side][bone].append(qq)
     else:qt_mid[side][bone].append(qq)
     q_errors[bone]=round(qq,5)
    byside[side]={'targetFootDelta_m':tf,'targetHipDelta_m':th,'sourceFootDelta_m':sf,
                   'sourceHipDelta_m':sh,'ratio':ratio,'sourceSupportCandidate':contact,
                   'verticalRootMismatch_m':root_y,'verticalLimbMismatch_m':limb_y,
                   'verticalFootResidual_m':tf[1]-expectedSF[1],
                   'stageVerticalContributions_m':steps,
                   'rotationImporterDeltaDegrees':q_errors,'isOriginalSourceKeyTime':abs(frame['sourceFrame']-round(frame['sourceFrame']))<1e-5,'sourceToeY_m':srcbones[f'mixamorig:{side}ToeBase']['worldPosition'][1]}
    row['sides'][side]={k:(round(v,6) if isinstance(v,float) else v) for k,v in byside[side].items() if k not in ('targetFootDelta_m','targetHipDelta_m','sourceFootDelta_m','sourceHipDelta_m')}
    row['sides'][side]['sourceEvaluatedChain']={bn:{'worldPosition':srcbones[bn]['worldPosition'],
      'restWorldQuat':srcbones[bn]['restWorldQuat'],'localDeltaQuat':srcbones[bn]['localDeltaQuat']}
      for bn in [HIP,*[f'mixamorig:{side}{part}' for part in BONENAMES]]}
    row['sides'][side]['targetWorldChainMatricesRowMajor']={bn:[round(float(v),7) for v in full[names[bn]]]
      for bn in [HIP,*[f'mixamorig:{side}{part}' for part in BONENAMES]]}
   targetsep=vsub(p(full[names['mixamorig:RightFoot']]),p(full[names['mixamorig:LeftFoot']]))
   srcsep=vsub(srcbones['mixamorig:RightFoot']['worldPosition'],srcbones['mixamorig:LeftFoot']['worldPosition'])
   sd=norm(vsub(srcsep,source_sep));td=norm(vsub(targetsep,origin_sep))
   sep_d.append(td);src_sep_d.append(sd)
   row['targetFootSeparationChange_m']=round(td,7)
   row['sourceFootSeparationChange_m']=round(sd,7)
   if byside['Left']['sourceSupportCandidate'] and byside['Right']['sourceSupportCandidate']:
    contacts.append(byside['Left']);contacts.append(byside['Right'])
    shoe_points=evalmod.skin_foot_points(witness,skin,ibm,full)
    fy={s:evalmod.floor_height(shoe_points[s]) for s in SIDES}
    sole_diff.append(abs(fy['Left']-fy['Right']))
    row['bilateralSkinnedSoleY_m']={s:round(fy[s],6) for s in SIDES}
   rec.append(row)
  # Fit vertical root scale on source-grounded bilateral samples only: no inferred airborne locking.
  fitrows=[{'targetHipDY':x['targetHipDelta_m'][1],
            'targetFootDY':x['targetFootDelta_m'][1],
            'sourceFootDY':x['sourceFootDelta_m'][1],'lengthRatio':x['ratio']} for x in contacts]
  fit=fit_common_hip_scale(fitrows) if len(fitrows)>=6 else None
  max_mapped=max(qt_err[s][b][i] for s in SIDES for b in qt_err[s] for i in range(len(qt_err[s][b])))
  motion={'sampleCount':len(source),'duration_s':times[-1],
          'legs':{s:{'ratio':round(leg_len[s]['ratio'],6),
                     'rootVerticalMismatch_m':stats([abs(row['sides'][s]['verticalRootMismatch_m']) for row in rec]),
                     'limbVerticalMismatch_m':stats([abs(row['sides'][s]['verticalLimbMismatch_m']) for row in rec]),
                     'footVerticalResidual_m':stats([abs(row['sides'][s]['verticalFootResidual_m']) for row in rec]),
                     'sourceFootYRange_m':round(max(q['bones'][f'mixamorig:{s}Foot']['worldPosition'][1] for q in source)-min(q['bones'][f'mixamorig:{s}Foot']['worldPosition'][1] for q in source),7),
                     'targetFootYRange_m':round(max(p(evalmod.global_matrices(g,tr,t)[names[f'mixamorig:{s}Foot']])[1] for t in times)-min(p(evalmod.global_matrices(g,tr,t)[names[f'mixamorig:{s}Foot']])[1] for t in times),7),
                     'stageYAmplitude_m':{stage:stats([abs(v) for v in vals]) for stage,vals in stages[s].items()},
                     'importerRotationErrorDeg':{bone:stats(vals) for bone,vals in qt_err[s].items()},
                     'importerRotationErrorOnSourceKeyDegrees':{bone:stats(vals) for bone,vals in qt_key[s].items()},
                     'importerRotationErrorAtTrueSourceMidframeDegrees':{bone:stats(vals) for bone,vals in qt_mid[s].items()}} for s in SIDES},
          'sourceFootSeparationVariation_m':stats(src_sep_d),
          'targetFootSeparationVariation_m':stats(sep_d),
          'bothSourceFeetNearFloorSampleCount':len(sole_diff),
          'soleBilateralYDifference_m':stats(sole_diff),
          'bestPossibleSharedHipYScaleOnBilateralContact':fit,
          'originalImporterQuatToHistoricalGLBMaxAngularErrorDeg':round(max_mapped,6),
          'originalImporterQuatToHistoricalGLBMaxAngularErrorAtKeysDeg':round(max(x for side in SIDES for bone in qt_key[side] for x in qt_key[side][bone]),6),
          'samples':rec}
  motion['provedRootOnlyInsufficientForStationaryPair']=bool(max(src_sep_d)<.001 and max(sep_d)>.02)
  out['clips'][name]=motion
 # A stationary source foot-pair that separates in the target is an invariant,
 # independent of common pelvis translation and without assuming facing axes.
 out['invariants']={'stationarySourcePairContradictions':[n for n,v in out['clips'].items() if v['provedRootOnlyInsufficientForStationaryPair']],
   'maxImporterQuatMismatchDeg':max(x['originalImporterQuatToHistoricalGLBMaxAngularErrorDeg'] for x in out['clips'].values()),
   'maxImporterQuatMismatchAtKeysDeg':max(x['originalImporterQuatToHistoricalGLBMaxAngularErrorAtKeysDeg'] for x in out['clips'].values()),
   'meaning':'If donor foot-pair world separation is static but target separation changes, no shared hip translation (of ANY magnitude/direction) can restore both positions. Quat parity isolates the defect to the mapping design or its source assumptions, not accidental changes to rotations after import.'}
 outpath=pathlib.Path(args.output);outpath.parent.mkdir(parents=True,exist_ok=True);outpath.write_text(json.dumps(out,indent=2)+'\n')
 print('CAUSAL_AUDIT_WRITTEN='+str(outpath),flush=True)
 print('STATIONARY_PAIR_INVARIANT_FAIL='+','.join(out['invariants']['stationarySourcePairContradictions']),flush=True)
 print('MAX_ROTATION_IMPORTER_MISMATCH_DEG='+str(out['invariants']['maxImporterQuatMismatchDeg']),flush=True)
 print('TARGET_MODEL_UNCHANGED=YES',flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--selftest',action='store_true');parser.add_argument('--target-role',choices=('historical','canonical'),default='historical');parser.add_argument('--model');parser.add_argument('--donor');parser.add_argument('--blend-sha');parser.add_argument('--expected-model-sha',default='955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32');parser.add_argument('--expected-donor-samples-sha',default='ANY_VERIFIED_FRESH_SOURCE');parser.add_argument('--evaluator');parser.add_argument('--importer');parser.add_argument('--output')
 a=parser.parse_args()
 if a.selftest:print('SELFTEST_PASS' if selftest() else 'SELFTEST_FAIL')
 else:
  for x in ('model','donor','blend_sha','evaluator','importer','output'):
   if not getattr(a,x):parser.error('missing '+x)
  audit(a)
