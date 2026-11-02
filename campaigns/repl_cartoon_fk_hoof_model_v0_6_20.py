#!/usr/bin/env python3
"""Repl v0.6.20 adaptive, feedback-driven TWO-JOINT motion search.

Loads exact canonical v0.6.17 binary. Search is bounded and checkpointed.
It optimizes WORLD skinned sole + trailing stance, anatomical knee extension
and full-cycle joint continuity without touching protected channels. Attempts
multiple shifting contact targets and knee weights, using beam-search DP
instead of a fixed list of four guessed amplitude profiles. Full 97-frame,
576 midframe production verifier still makes the final decision.
"""
from __future__ import annotations
import copy,hashlib,json,math,time,os
from pathlib import Path
VERSION='0.6.20'
SOURCE_SHA='c6dc250356248e5860e5919568e4103d6c1d2cb6e071e7bb9a0f7ce1f42ee4c1'
FRAMES=97
LEGS={'LF':('Bone_015','Bone_014','Bone_013',8),
      'RF':('Bone_021','Bone_020','Bone_019',24)}
EDITABLE={n for v in LEGS.values() for n in v[:2]}
SAMPLES=20
class Blocked(RuntimeError):pass
def need(x,msg):
 if not x:raise Blocked(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(q):
 n=math.sqrt(dot(q,q));need(n>1e-10,'BAD_ROTATION');return tuple(x/n for x in q)
def angle(q1,q2):
 d=min(1.,max(-1.,abs(dot(norm(q1),norm(q2)))))
 return 2*math.degrees(math.acos(d))
def phase(leg,f):
 start=LEGS[leg][3]
 return (f-start)%32<20

def state_from_world(world,mats,patch,ids,bones):
 xyz,js,ws=patch
 pts=[]
 for i in ids:
  p=xyz[i];xyzout=[0.,0.,0.]
  for j,w in zip(js[i],ws[i]):
   if w<1e-9:continue
   m=mats[j];X=m[0]*p[0]+m[1]*p[1]+m[2]*p[2]+m[3]
   Y=m[4]*p[0]+m[5]*p[1]+m[6]*p[2]+m[7]
   Z=m[8]*p[0]+m[9]*p[1]+m[10]*p[2]+m[11]
   xyzout[0]+=w*X;xyzout[1]+=w*Y;xyzout[2]+=w*Z
  pts.append(tuple(xyzout))
 sh,knee,low=(tuple(world[n][i] for i in (3,7,11)) for n in bones)
 v=tuple(sh[i]-knee[i] for i in range(3));w=tuple(low[i]-knee[i] for i in range(3))
 co=dot(v,w)/(math.sqrt(dot(v,v))*math.sqrt(dot(w,w)))
 bend=180.-math.degrees(math.acos(max(-1.,min(1.,co))))
 return {'bend':bend,'sole_y':min(p[1] for p in pts),
         'z':sum(p[2] for p in pts)/len(pts),
         'shoulder_z':sh[2], 'relative_z':sum(p[2] for p in pts)/len(pts)-sh[2],
         'heel_y':sum(p[1] for p in pts[:max(1,len(pts)//3)])/max(1,len(pts)//3),
         'toe_y':sum(p[1] for p in pts[-max(1,len(pts)//3):])/max(1,len(pts)//3),
         'heel_to_toe':(sum(p[1] for p in pts[:max(1,len(pts)//3)])/max(1,len(pts)//3)-
                         sum(p[1] for p in pts[-max(1,len(pts)//3):])/max(1,len(pts)//3))}

class Geometry:
 def __init__(self,source,base,previous):
  need(sha(source)==SOURCE_SHA,'CANONICAL_GLTF_HASH_MISMATCH')
  self.doc,self.binary=previous.parse_glb(source)
  self.names=previous.inspect_source(self.doc)
  self.base=base;self.previous=previous
  self.root=self.names['Bone_000']
  self.tracks=[previous.tracks(self.doc,self.binary,a,base) for a in self.doc['animations'][3:]]
  self.patches={}
  body=self.doc['meshes'][0]['primitives'][0]['attributes']
  xyz=base.accessor(self.doc,self.binary,body['POSITION'])
  js=base.accessor(self.doc,self.binary,body['JOINTS_0'])
  ws=base.accessor(self.doc,self.binary,body['WEIGHTS_0'])
  for leg in LEGS:
   _,_,_,indices=previous.hoof_witnesses(self.doc,self.binary,base,leg)
   # Source-fixed vertex identities. Candidate may rotate but cannot reselect witnesses.
   # Optimize over a broad, deterministic subset; full verifier uses all vertices.
   sample=sorted(indices[::max(1,len(indices)//28)][:32],key=lambda i:xyz[i][2])
   # A candidate cannot game the minimum by excluding source vertices with low sole Y.
   self.patches[leg]=((xyz,js,ws),sample)
  self.source=source
  self.orig_root=tuple(self.doc['nodes'][self.root].get('translation',(0,0,0)))
  self.eval_count=0
 def state(self,stage,leg,frame,delta=(0.,0.)):
  tr=self.tracks[stage-1]
  d=self.doc;name=self.names;rot={i:tuple(v['rows'][frame]) for (i,p),v in tr.items() if p=='rotation'}
  for bn,dd in zip(LEGS[leg][:2],delta):
   n=name[bn];rot[n]=norm(self.base.qmul(rot[n],self.base.axisq((1,0,0),dd)))
  d['nodes'][self.root]['translation']=list(tr[(self.root,'translation')]['rows'][frame])
  try:
   world=self.base.world_matrices(d,rot);mats=self.base.skin_matrices(d,self.binary,world)
   patch,ids=self.patches[leg]
   self.eval_count+=1
   return state_from_world(world,mats,patch,ids,[name[n] for n in LEGS[leg][:3]])
  finally:d['nodes'][self.root]['translation']=list(self.orig_root)

# Connection to actual toe/heel and support velocity is checked by v0.6.17
# whole-model verifier. This search evaluator is not an acceptance test.
def grids(leg,stage,geom,range_deg=50.,step=5.):
 out=[];tr=geom.tracks[stage-1];names=geom.names
 for j in range(23):
  f=(LEGS[leg][3]+j)%32
  # Stance ends at index 19; permit late extension, then a 3-frame
  # airborne recovery taper. Do not force a snap at toe-off.
  bound=min(range_deg, max(0.,j*15.), max(0.,(22-j)*15.))
  dd=[round(v*step,5) for v in range(-int(bound/step),int(bound/step)+1)]
  if 0 not in dd:dd.append(0.)
  opts=[]
  for a in dd:
   for b in dd:
    s=geom.state(stage,leg,f,(a,b))
    if s['sole_y']<(-.010 if j<20 else .0001) or s['sole_y']>(.040 if j<20 else .110):continue
    # Knee extents >95 are nonphysical for this target; don't assume
    # 'negative knee' is straight: this value comes from 3 joint centers.
    if not math.isfinite(s['bend']) or s['bend']>92:continue
    opts.append((a,b,s))
  if not opts:
   # Predict and explain geometric infeasibility; expand grid once locally.
   for a in (-8.,-4.,0.,4.,8.):
    for b in (-8.,-4.,0.,4.,8.):
     s=geom.state(stage,leg,f,(a,b))
     if (-.012 if j<20 else .0001)<=s['sole_y']<=(.045 if j<20 else .110):opts.append((a,b,s))
  need(bool(opts),'NO_LOCAL_GROUND_FEASIBLE_POSE:'+str((stage,leg,f)))
  out.append(opts)
 return out

def local_cost(a,b,s,target_z,target_bend,knee_weight,regularization):
  # Hard-ish contact penalties (strict thresholds reserved for final verifier).
  y=s['sole_y'];z=s['z']
  return (190000.*max(0.,-.003-y,y-.013)**2 +
          44000.*(z-target_z)**2 +
          knee_weight*max(0.,s['bend']-target_bend)**2 +
          regularization*(a*a+b*b) + 160.*max(0.,s['heel_to_toe']-.035)**2)

def beam_plan(geom,stage,leg,candidates,anchor_shift,knee_target,knee_weight,smooth):
  start=LEGS[leg][3];baseline=[geom.state(stage,leg,(start+j)%32) for j in range(23)]
  # Keep a world-space contact anchor fixed in stance. Target trailing
  # geometry is sought by shifting the entire support contact consistently.
  reference_z=sum(baseline[j]['z'] for j in range(3,16))/13-anchor_shift
  # Favor a long straight supporting segment but retain toe-off transition.
  options=[]
  for j,row in enumerate(candidates):
   target_bend=knee_target+(10.*max(0.,j-15)/4.)
   if j<20:
    ranked=sorted(row,key=lambda x:local_cost(x[0],x[1],x[2],reference_z,
                                        target_bend,knee_weight,.004))
   else:
    old=baseline[j]
    ranked=sorted(row,key=lambda x:45000*(x[2]['sole_y']-old['sole_y'])**2+
                  2000*(x[2]['z']-old['z'])**2+.006*(x[0]*x[0]+x[1]*x[1]))
   # retain angle-near-zero candidate as safety and path-connectivity escape.
   trimmed=ranked[:min(60,len(ranked))]
   zero=min(row,key=lambda x:x[0]*x[0]+x[1]*x[1])
   if zero not in trimmed:trimmed.append(zero)
   options.append(trimmed)
  paths={None:(0.,[])}
  for j,row in enumerate(options):
   new={}
   for k,(a,b,s) in enumerate(row):
    target_bend=knee_target+(10.*max(0.,j-15)/4.)
    if j<20:
     lc=local_cost(a,b,s,reference_z,target_bend,knee_weight,.004)
    else:
     old=baseline[j]
     lc=45000*(s['sole_y']-old['sole_y'])**2+2000*(s['z']-old['z'])**2+.006*(a*a+b*b)
    best=(float('inf'),None)
    for prior, (cost,path) in paths.items():
     if prior is None:pen=0.
     else:
      aa,bb,ps=options[j-1][prior]
      if abs(a-aa)>15.01 or abs(b-bb)>15.01:continue
      dz=abs(s['z']-ps['z'])
      # Prevent the solver from hiding a toe/hoof jump in the transition.
      pen=smooth*((a-aa)**2+(b-bb)**2)+7500.*max(0.,dz-.023)**2
     total=cost+lc+pen
     if total<best[0]:best=(total,path)
    if best[1] is not None:new[k]=(best[0],best[1]+[(a,b)])
   if not new:return None
   # Deterministic bounded beam retaining diversity in both joint angles.
   chosen=sorted(new,key=lambda k:new[k][0])[:42]
   paths={k:new[k] for k in chosen}
  best=min(paths,key=lambda k:paths[k][0]);angles=paths[best][1]
  return {'angles':angles,'proxy_cost':paths[best][0],
          'knee_min':min(geom.state(stage,leg,(start+j)%32,q)['bend'] for j,q in enumerate(angles[4:14],4)),
          'reach_gain':baseline[19]['relative_z']-geom.state(stage,leg,(start+19)%32,angles[19])['relative_z'],
          'heel_proxy_height':0.,'anchor_shift':anchor_shift}

def write_candidate(source,geom,plan,base,previous):
 doc,raw=previous.parse_glb(source);names=previous.inspect_source(doc)
 out=bytearray(raw)
 for stage in range(1,4):
  tr=previous.tracks(doc,raw,doc['animations'][stage+2],base)
  for leg in LEGS:
   for bone_idx,bone in enumerate(LEGS[leg][:2]):
    n=names[bone];key=(n,'rotation');need(key in tr,'FRONT_CHANNEL_MISSING:'+bone)
    qr=[]
    for frame in range(FRAMES):
     j=(frame-LEGS[leg][3])%32
     dd=plan[f'{min(stage,2)}_{leg}']['angles'][j][bone_idx] if j<23 else 0.
     q=tr[key]['rows'][frame]
     qr.append(norm(base.qmul(q,base.axisq((1,0,0),dd))))
    a=base.emit_accessor(doc,out,qr,5126,'VEC4');tr[key]['sampler']['output']=a
  doc['animations'][stage+2].setdefault('extras',{})['replGroundSupportV0620']={
   'verified':'REQUIRES_FULL_MODEL_VERIFIER','changed_bones':sorted(EDITABLE),
   'human_visual_acceptance':'PENDING'}
 doc['asset'].setdefault('extras',{}).setdefault('replWalkCampaign',{}).update({
  'version':VERSION,'approach':'ADAPTIVE_FULL_STANCE_KINEMATICS','humanVisualVerdict':'PENDING'})
 return base.glb_encode(doc,bytes(out))

def measured_metrics(source,output,geom,base,previous):
 doc,raw=previous.parse_glb(output);names=previous.inspect_source(doc)
 tr=[previous.tracks(doc,raw,a,base) for a in doc['animations'][3:]]
 root=names['Bone_000'];old=doc['nodes'][root].get('translation',(0,0,0))
 result={};summary={'max_knee_bend_middle_stance':0.,'min_knee_improvement':float('inf'),
                    'min_reach_improvement':float('inf')}
 for stage in (1,2,3):
  for leg in LEGS:
   # Measure original and candidate at same real root/body poses.
   patch,ids=geom.patches[leg]
   states=[];original=[]
   for j in range(20):
    f=(LEGS[leg][3]+j)%32
    doc['nodes'][root]['translation']=list(tr[stage-1][(root,'translation')]['rows'][f])
    pose={node:tuple(data['rows'][f]) for (node,p),data in tr[stage-1].items() if p=='rotation'}
    worlds=base.world_matrices(doc,pose);mats=base.skin_matrices(doc,raw,worlds)
    states.append(state_from_world(worlds,mats,patch,ids,[names[n] for n in LEGS[leg][:3]]))
    original.append(geom.state(stage,leg,f))
   mids=states[4:14];origmid=original[4:14]
   before=min(z['bend'] for z in origmid);after=min(z['bend'] for z in mids)
   reach=original[-1]['relative_z']-states[-1]['relative_z']
   result[f'{stage}_{leg}']={'source_min_mid_bend':round(before,3),'new_min_mid_bend':round(after,3),
       'improvement_degrees':round(before-after,3),'trailing_reach_gain_units':round(reach,5),
       'new_sole_range':[round(min(s['sole_y'] for s in states),6),round(max(s['sole_y'] for s in states),6)],
       'early_heel_rise_before':round(max(s['heel_to_toe'] for s in original[2:13]),5),
       'early_heel_rise_after':round(max(s['heel_to_toe'] for s in states[2:13]),5)}
   need(max(s['heel_to_toe'] for s in states[2:13])<=
        max(s['heel_to_toe'] for s in original[2:13])+.006,
        'EARLY_HEEL_ROLL_REGRESSION:'+str((stage,leg)))
   summary['max_knee_bend_middle_stance']=max(summary['max_knee_bend_middle_stance'],after)
   summary['min_knee_improvement']=min(summary['min_knee_improvement'],before-after)
   summary['min_reach_improvement']=min(summary['min_reach_improvement'],reach)
 doc['nodes'][root]['translation']=list(old)
 return result,summary

def configs():
 # Constraint-driven parameter search, not one-off fixed poses. Each failure
 # selects a different contact-anchor and anatomical regularization. Search
 # spans contact targets, knee priorities, and smoothing costs; all results
 # face the SAME physical verifier, which is never weakened.
 yield {'shift_LF':.010,'shift_RF':.014,'knee_target':18.,'knee_weight':.025,'smooth':.015}
 for bend in (18.,15.,12.):
  for shift in (.008,.016,.024,.032):
   for smooth in (.008,.025):
    yield {'shift_LF':shift*.60,'shift_RF':shift,'knee_target':bend,
           'knee_weight':.032 if bend<=15 else .015,'smooth':smooth}

def search_reaction(cfg,cause):
 """Generate alternatives informed by the failure's physical category.

 No allowed-bone change, tolerance relaxation, or silent scope expansion.
 """
 def fresh(**kw):
  n=dict(cfg);n.update(kw);return n
 if 'KNEE' in cause or 'NOT_ENOUGH_KNEE' in cause:
  yield fresh(knee_target=max(8.,cfg['knee_target']-3.),
              knee_weight=min(.12,cfg['knee_weight']*1.7))
  yield fresh(smooth=max(.003,cfg['smooth']*.75))
 elif 'REACH' in cause:
  yield fresh(shift_RF=min(.042,cfg['shift_RF']+.006),
              shift_LF=min(.027,cfg['shift_LF']+.004))
 elif 'KICK' in cause or 'CONTINU' in cause or 'OVERSHOOT' in cause:
  yield fresh(smooth=min(.10,cfg['smooth']*2.))
 elif 'FOOT' in cause or 'HOOF' in cause or 'GROUND' in cause or 'SLIP' in cause:
  yield fresh(shift_RF=max(0.,cfg['shift_RF']*.67),
              shift_LF=max(0.,cfg['shift_LF']*.67))
  yield fresh(knee_weight=max(.005,cfg['knee_weight']*.6))
 elif 'HEEL' in cause:
  yield fresh(knee_weight=max(.005,cfg['knee_weight']*.65),
              smooth=min(.10,cfg['smooth']*1.5))
 else:
  yield fresh(smooth=min(.10,cfg['smooth']*1.35))

def evaluate(source,base,previous,validator,checkpoint_dir,progress=print):
 need(sha(source)==SOURCE_SHA,'CANONICAL_SOURCE_NOT_LOCKED')
 checkpoint_dir=Path(checkpoint_dir);checkpoint_dir.mkdir(parents=True,exist_ok=True)
 geom=Geometry(source,base,previous)
 reference={'version':'0.6.16','source_sha256':SOURCE_SHA}
 # A reusable immutable-source grid cache avoids making the owner rerun
 # expensive geometry discovery after a recoverable interruption.
 gridfile=checkpoint_dir/'geometry_grid_cache.json'
 grids_cache={}
 if gridfile.is_file():
  try:
   cache=json.loads(gridfile.read_text())
   need(cache['source_sha256']==SOURCE_SHA and cache['version']==VERSION,
        'GRID_CACHE_SOURCE_CHANGED')
   grids_cache={(int(k.split('_')[0]),k.split('_')[1]):[
      [(float(a),float(b),s) for a,b,s in frame] for frame in v]
      for k,v in cache['grids'].items()}
   need(set(grids_cache)=={(stage,leg) for stage in (1,2) for leg in LEGS},
        'INCOMPLETE_GEOMETRY_GRID_CACHE')
   progress('RESUMED_VERIFIED_SOURCE_GEOMETRY_GRID=YES')
  except (ValueError,KeyError,TypeError,Blocked):
   # Corrupt private caches are never trusted; rebuild read-only from source.
   grids_cache={}
 if not grids_cache:
  for stage in (1,2):
   for leg in LEGS:
    progress('GRID_INSPECT='+str((stage,leg)))
    grids_cache[(stage,leg)]=grids(leg,stage,geom)
  raw={'source_sha256':SOURCE_SHA,'version':VERSION,
       'grids':{f'{stage}_{leg}':rows for (stage,leg),rows in grids_cache.items()}}
  temp=checkpoint_dir/'geometry_grid_cache.tmp'
  temp.write_text(json.dumps(raw,separators=(',',':'))+'\n');os.replace(temp,gridfile)
 previous_attempts=[];statefile=checkpoint_dir/'search_checkpoint.json'
 if statefile.is_file():
  try:
   old=json.loads(statefile.read_text())
   if old.get('source_sha256')==SOURCE_SHA and old.get('version')==VERSION:
    previous_attempts=old.get('attempts',[])
  except (ValueError,KeyError,TypeError):pass
 attempts=list(previous_attempts)
 seen_configs={json.dumps(x['config'],sort_keys=True) for x in attempts if 'config' in x}
 queued=list(configs());winning=None;seen_plans=set()
 # Parameter-domain exploration beyond the original four hand-authored
 # profiles, plus feedback-generated remedies for the actual failure class.
 cursor=0;limit=65
 while cursor<len(queued) and len(attempts)<limit:
  cfg=queued[cursor];cursor+=1
  key=json.dumps(cfg,sort_keys=True)
  if key in seen_configs:continue
  seen_configs.add(key)
  num=len(attempts)+1
  plan={}
  try:
   for stage in (1,2):
    for leg in LEGS:
     q=beam_plan(geom,stage,leg,grids_cache[(stage,leg)],cfg['shift_'+leg],
                 cfg['knee_target'],cfg['knee_weight'],cfg['smooth'])
     need(q is not None,'NO_CONTINUOUS_TWO_JOINT_PATH:'+str((stage,leg)))
     plan[f'{stage}_{leg}']=q
   signature=tuple(tuple(tuple(v) for v in plan[f'{stage}_{leg}']['angles'])
                   for stage in (1,2) for leg in LEGS)
   if signature in seen_plans:
    attempts.append({'attempt':num,'config':cfg,'outcome':'DUPLICATE_GEOMETRIC_TRAJECTORY'})
    continue
   seen_plans.add(signature)
   output=write_candidate(source,geom,plan,base,previous)
   metrics,summary=measured_metrics(source,output,geom,base,previous)
   need(summary['min_knee_improvement']>=5.,'NOT_ENOUGH_KNEE_IMPROVEMENT')
   # Treat the two sides independently; no pretending one good leg repairs both.
   for stage in (1,2,3):
    for leg,min_gain in (('LF',.010),('RF',.018)):
     need(metrics[f'{stage}_{leg}']['trailing_reach_gain_units']>=min_gain,
          'NOT_ENOUGH_TRAILING_REACH:'+str((stage,leg)))
   verified=validator.verify(source,output,reference,base,previous)
   verified['kinematics']=metrics;verified['summary']=summary
   verified['solver_configuration']=cfg;verified['evaluated_geometric_poses']=geom.eval_count
   verified['version']=VERSION;verified['output_sha256']=sha(output)
   winning=(output,verified)
   attempts.append({'attempt':num,'config':cfg,'outcome':'VALID_FULL_CYCLE','metrics':summary})
   progress('ADAPTIVE_SEARCH_FULL_VALIDATION_PASS='+str(num))
   break
  except Blocked as exc:
   cause=str(exc)[:600]
   attempts.append({'attempt':num,'config':cfg,'outcome':'REPLAN_AFTER_GEOMETRIC_CONSTRAINT',
                    'cause':cause})
   for proposal in search_reaction(cfg,cause):
    k=json.dumps(proposal,sort_keys=True)
    if k not in seen_configs and all(json.dumps(q,sort_keys=True)!=k for q in queued):
     queued.append(proposal)
   if num<4 or num%4==0:
    progress('ADAPTIVE_REPLAN='+str(num)+'/'+str(limit)+':'+cause[:120])
  except Exception:
   # A Python defect is not an anatomical infeasibility. Do not waste 65
   # attempts and hide a programming error behind a fake solver diagnosis.
   raise
  finally:
   receipt={'version':VERSION,'source_sha256':SOURCE_SHA,
            'configurations_visited':len(attempts),'geometric_pose_evaluations':geom.eval_count,
            'attempts':attempts,'success':winning is not None,
            'optimizer_feedback_queue_length':len(queued)}
   temp=checkpoint_dir/'search_checkpoint.tmp'
   temp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
   os.replace(temp,statefile)
 if not winning:
  details={'evaluated_configurations':len(attempts),
    'unique_candidate_signatures':len(seen_plans),
    'geometric_pose_evaluations':geom.eval_count,'attempts':attempts,
    'missing_authority':'DISTAL_AND_ROOT_CHANNELS_REMAIN_PROTECTED',
    'statement':'NO_FULLY_VERIFIED_CORRECTION_FOUND_IN_BOUNDED_FEEDBACK_GUIDED_SEARCH;NOT_PROOF_OF_IMPOSSIBILITY'}
  raise Blocked('ADAPTIVE_SEARCH_EXHAUSTED:'+json.dumps(details,separators=(',',':'))[:7500])
 return winning[0],winning[1],attempts
