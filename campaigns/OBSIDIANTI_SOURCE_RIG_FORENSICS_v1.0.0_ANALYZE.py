"""Read-only Blender source rig IK/bake forensic measurement. Run once for each source .blend."""
import bpy, sys, math, json, pathlib, hashlib, collections, statistics, traceback
from mathutils import Vector
source, target = sys.argv[sys.argv.index('--') + 1:]
report={'schema':'obsidianti-source-rig-forensics-v1.0.0','sourceFile':pathlib.Path(source).name,'blenderVersion':bpy.app.version_string,'status':'STARTED','rigs':[],'actions':[],'warnings':[]}
def write():pathlib.Path(target).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
def vec(v):return [round(float(z),7) for z in v]
def eval_frame(t):
 k=math.floor(t);bpy.context.scene.frame_set(k,subframe=t-k);bpy.context.view_layer.update()
def orient_diff(q1,q2):return math.degrees(q1.rotation_difference(q2).angle)
def rig_action(arm,act):
 arm.animation_data_create();arm.animation_data.action=act
 for tr in arm.animation_data.nla_tracks:tr.mute=True
 def item(side):
  bones=list(arm.pose.bones)
  pats=['left','right'] if side=='L' else ['right','left']
  patterns=['leftfoot','l_foot','foot.l','left_foot','left ankle','leftankle'] if side=='L' else ['rightfoot','r_foot','foot.r','right_foot','right ankle','rightankle']
  matches=[b for b in bones if any(x in b.name.lower().replace(' ','') for x in patterns) and not any(z in b.name.lower() for z in ('ctrl','ik','target','pole'))]
  if not matches:matches=[b for b in bones if ('foot' in b.name.lower() or 'ankle' in b.name.lower()) and (('left' in b.name.lower() or b.name.lower().endswith('.l')) if side=='L' else ('right' in b.name.lower() or b.name.lower().endswith('.r')))]
  if not matches:return None
  return min(matches,key=lambda b:len(b.name))
 feet={s:item(s) for s in ('L','R')}
 if not any(feet.values()):return None
 lo,hi=map(float,act.frame_range)
 if hi-lo>1000:return {'action':act.name,'skipped':'ACTION_TOO_LONG','range':[lo,hi]}
 # Preserve exact keys and multiple midpoints without truncating original animation.
 times=sorted(set([lo,hi]+[lo+(hi-lo)*i/80 for i in range(81)]))
 all_constraints=[c for b in arm.pose.bones for c in b.constraints if not c.mute and c.influence>0]
 active_ik=[c for c in all_constraints if c.type in ('IK','SPLINE_IK')]
 sample=[]
 def footrec():
  out={}
  for side,b in feet.items():
   if b is None:continue
   m=arm.matrix_world@b.matrix
   out[side]={'position':(m.translation.copy()),'rotation':m.to_quaternion().copy(),'bone':b.name}
  return out
 try:
  for t in times:
   eval_frame(t); enabled=footrec()
   for c in active_ik:c.mute=True
   eval_frame(t); disabled=footrec()
   for c in active_ik:c.mute=False
   row={'frame':round(t,5),'feet':{}}
   for side in enabled:
    a=enabled[side];b=disabled[side]
    row['feet'][side]={'activePos':vec(a['position']),'inactivePos':vec(b['position']),'constraintDelta_m':round((a['position']-b['position']).length,7),'constraintDelta_deg':round(orient_diff(a['rotation'],b['rotation']),6),'bone':a['bone']}
   sample.append(row)
 finally:
  for c in active_ik:c.mute=False
  bpy.context.view_layer.update()
 stats={}
 for side in ('L','R'):
  seq=[x['feet'][side] for x in sample if side in x['feet']]
  if not seq:continue
  offsets=[x['constraintDelta_m'] for x in seq];rots=[x['constraintDelta_deg'] for x in seq]
  starts=[Vector(x['activePos']) for x in seq]
  delta=[(starts[i]-starts[i-1]).length for i in range(1,len(starts))]
  stats[side]={'footBone':seq[0]['bone'],'maxConstraintPositionDelta_m':max(offsets),'meanConstraintPositionDelta_m':round(statistics.mean(offsets),7),'maxConstraintRotationDelta_deg':max(rots),'samplesAffectedOver1mm':sum(z>.001 for z in offsets),'maxFootStep_m':max(delta,default=0)}
 return {'action':act.name,'range':[lo,hi],'sampleCount':len(sample),'activeConstraintsCount':len(all_constraints),'activeIKConstraintsCount':len(active_ik),'stats':stats,'samples':sample}
try:
 bpy.ops.wm.open_mainfile(filepath=source,load_ui=False)
 rig_objects=[o for o in bpy.data.objects if o.type=='ARMATURE']
 report['objects']={'armatures':len(rig_objects),'meshes':sum(o.type=='MESH' for o in bpy.data.objects)}
 report['actionsTotal']=len(bpy.data.actions)
 for ob in rig_objects:
  constraints=[{'bone':pb.name,'name':c.name,'type':c.type,'mute':bool(c.mute),'influence':round(float(c.influence),5),'target':getattr(getattr(c,'target',None),'name',None),'subtarget':getattr(c,'subtarget',None)} for pb in ob.pose.bones for c in pb.constraints]
  arm={'name':ob.name,'boneCount':len(ob.data.bones),'constraints':constraints,'constraintCounts':dict(collections.Counter(c['type'] for c in constraints)),'IKControlCandidates':[b.name for b in ob.data.bones if any(x in b.name.lower() for x in ['ik','pole','target'])][:120],'legBones':[{'name':b.name,'length':round(b.length,6),'parent':b.parent.name if b.parent else None,'use_connect':b.use_connect} for b in ob.data.bones if any(x in b.name.lower() for x in ('foot','ankle','leg','thigh','shin'))][:120],'activeAction':ob.animation_data.action.name if ob.animation_data and ob.animation_data.action else None}
  report['rigs'].append(arm)
  # Prefer anims apparently controlled by this rig, sampling up to 12 relevant actions.
  actions=[a for a in bpy.data.actions if any(x in a.name.lower() for x in ('heavy','light','cast','spring','kick','stomp'))]
  if not actions:
   actions=[a for a in bpy.data.actions if 'walk' in a.name.lower() or 'idle' in a.name.lower()][:4]
  if not actions and ob.animation_data and ob.animation_data.action:actions=[ob.animation_data.action]
  for act in actions[:12]:
   try:
    result=rig_action(ob,act)
    if result:report['actions'].append({'rig':ob.name,**result})
   except Exception as e:report['warnings'].append({'action':act.name,'rig':ob.name,'error':str(e),'traceback':traceback.format_exc()[-1600:]})
 report['status']='ANALYSIS_COMPLETE'
except Exception as e:
 report['status']='ANALYSIS_ERROR';report['error']=str(e);report['traceback']=traceback.format_exc()[-2500:]
write()
print('SOURCE_ANALYSIS_STATUS='+report['status'])
print('SOURCE_RIGS='+str(len(report['rigs']))+' ACTIONS_MEASURED='+str(len(report['actions'])))
if report['status']=='ANALYSIS_ERROR':sys.exit(2)
