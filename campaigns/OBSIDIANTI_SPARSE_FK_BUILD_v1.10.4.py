"""Sparse FK-only authoring of Obsidianti's verified Ares-scaled FK Blender baseline.
No IK, no root/weapon modifications; all original actions survive unchanged.
"""
import bpy,sys,math,json,pathlib,traceback,collections
from mathutils import Quaternion
base,out,reportfile=sys.argv[sys.argv.index('--')+1:]
MOVES=('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
SIDES=('Left','Right')
LEG=('UpLeg','Leg','Foot')
# These are tolerances against the ORIGINAL FK pose, not ground-contact repairs.
LIMIT={'hip_m':.0005,'knee_m':.003,'ankle_m':.003,'foot_deg':.5,'joint_deg':.5}
report={'schema':'obsidianti-sparse-fk-v1.10.4','status':'STARTED','authority':'EXACT_VERIFIED_V1.10.1_FK_BLENDER_BASELINE','limits':LIMIT,'ikConstraintsIntroduced':False,'originalActionsProtected':True,'actions':{},'errors':[]}
def save():pathlib.Path(reportfile).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
def curves(a):
 try:r=list(a.fcurves)
 except (RuntimeError,AttributeError):r=[]
 if not r:
  for layer in getattr(a,'layers',[]):
   for strip in getattr(layer,'strips',[]):
    for bag in getattr(strip,'channelbags',[]):r.extend(getattr(bag,'fcurves',[]))
 return r
def actions(ref):
 rows=[]
 if not ref.animation_data:raise RuntimeError('FK_REFERENCE_NO_ANIMATION_DATA')
 for track in ref.animation_data.nla_tracks:
  for strip in track.strips:
   if strip.action:rows.append((track.name,strip.name,strip.action))
 if ref.animation_data.action:rows.append(('ACTIVE','ACTIVE',ref.animation_data.action))
 ans={}
 for move in MOVES:
  token='Lionheart_'+move
  cand={id(a):a for t,s,a in rows if token in (t,s,a.name) or a.name.startswith(token+'_SmartRigArmature')}
  if len(cand)!=1:raise RuntimeError('SOURCE_ACTION_AMBIGUITY_'+token+' '+str([(t,s,a.name) for t,s,a in rows]))
  ans[move]=next(iter(cand.values()))
 return ans
def frame(t):
 k=math.floor(t);bpy.context.scene.frame_set(k,subframe=t-k);bpy.context.view_layer.update()
def quat_error(a,b):
 a=a.normalized();b=b.normalized()
 return math.degrees(a.rotation_difference(b).angle)
def bonechannels(action):
 result={}
 for side in SIDES:
  for limb in LEG:
   name='mixamorig:'+side+limb
   path='pose.bones["'+name+'"].rotation_quaternion'
   fc={f.array_index:f for f in curves(action) if f.data_path==path}
   if len(fc)==4:
    ks=[sorted(float(k.co.x) for k in f.keyframe_points) for f in fc.values()]
    if not all(ks[0]==k for k in ks[1:]):raise RuntimeError('QUAT_CHANNEL_TIME_MISMATCH '+name)
    result[name]=fc
   elif fc:raise RuntimeError('PARTIAL_ROTATION_QUATERNION_CHANNELS '+name)
 return result
def reduce_group(original,candidate,threshold):
 originalGroups=bonechannels(original);newGroups=bonechannels(candidate)
 details={};total_before=total_after=0
 for name,fc in originalGroups.items():
  fnew=newGroups[name];ts=sorted(float(k.co.x) for k in fc[0].keyframe_points)
  if len(ts)<3:continue
  # Query actual ORIGINAL FCurves at the source keys and time midpoints.
  sample=sorted(set(ts+[(a+b)/2 for a,b in zip(ts,ts[1:])]))
  def q(t):return Quaternion(tuple(fc[c].evaluate(t) for c in range(4))).normalized()
  qs={t:q(t) for t in sample}
  keep={0,len(ts)-1};stack=[(0,len(ts)-1)]
  while stack:
   a,b=stack.pop()
   if b-a<2:continue
   t0,t1=ts[a],ts[b];qa=qs[t0];qb=qs[t1]
   # Compare the true source trajectory with the candidate interpolation across
   # this whole interval. Quaternion hemisphere is chosen only for measuring.
   if qa.dot(qb)<0:qb=Quaternion(tuple(-v for v in qb))
   worst=(-1.,None)
   for i in range(a+1,b):
    t=ts[i];u=(t-t0)/(t1-t0)
    qq=qa.slerp(qb,u)
    err=quat_error(qq,qs[t])
    if err>worst[0]:worst=(err,i)
   # Also test intermediate original timing; never trust only reduced keys.
   for t in sample:
    if not t0<t<t1:continue
    qq=qa.slerp(qb,(t-t0)/(t1-t0));err=quat_error(qq,qs[t])
    if err>worst[0]:
     nearest=min(range(a+1,b),key=lambda i:abs(ts[i]-t)) if b-a>1 else None
     worst=(err,nearest)
   if worst[0]>threshold and worst[1] is not None:
    m=worst[1];keep.add(m);stack.extend([(a,m),(m,b)])
  chosen={round(ts[i],6) for i in keep};before=len(ts)
  for f in fnew.values():
   for k in list(f.keyframe_points):
    if round(float(k.co.x),6) not in chosen:f.keyframe_points.remove(k,fast=True)
   f.update()
  after=len(chosen);total_before+=before;total_after+=after
  details[name]={'sourceTimes':before,'sparseTimes':after}
 return {'sourceKeyGroups':total_before,'sparseKeyGroups':total_after,'groups':details}
def snapshot(arm):
 p=arm.pose.bones;result={}
 for side in SIDES:
  result[side]={}
  for limb in LEG:
   b=p['mixamorig:'+side+limb]
   result[side][limb]={'head':b.head.copy(),'tail':b.tail.copy(),'rot':b.matrix.to_quaternion().copy()}
 return result
def compare(orig,edited):
 maxs={'hip_m':0.,'knee_m':0.,'ankle_m':0.,'foot_deg':0.,'joint_deg':0.};worst={}
 for side in SIDES:
  o=orig[side];e=edited[side]
  for limb,measure in [('UpLeg','hip_m'),('Leg','knee_m'),('Foot','ankle_m')]:
   x=(o[limb]['head']-e[limb]['head']).length
   if x>maxs[measure]:maxs[measure]=x;worst[measure]=side+'_'+limb
  for limb in LEG:
   x=quat_error(o[limb]['rot'],e[limb]['rot'])
   key='foot_deg' if limb=='Foot' else 'joint_deg'
   if x>maxs[key]:maxs[key]=x;worst[key]=side+'_'+limb
 return maxs,worst
try:
 bpy.ops.wm.open_mainfile(filepath=base,load_ui=False)
 rigs=[o for o in bpy.data.objects if o.type=='ARMATURE']
 ref=next((r for r in rigs if r.name=='OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT'),None)
 if ref is None:
  if len(rigs)!=1:raise RuntimeError('SOURCE_REFERENCE_RIG_AMBIGUOUS '+str([x.name for x in rigs]))
  ref=rigs[0]
 src=actions(ref)
 for a in list(bpy.data.actions):a.use_fake_user=True
 ref.animation_data.use_nla=False
 for track in ref.animation_data.nla_tracks:track.mute=True
 # FK-only authoring twin. Its animation datablocks are separate from all 23 source actions.
 author=ref.copy();author.data=ref.data.copy();bpy.context.scene.collection.objects.link(author)
 author.name='OBSIDIANTI_SPARSE_FK_EDITABLE_UNAPPROVED'
 author.animation_data_clear();author.animation_data_create()
 author.animation_data.use_nla=False
 for obj in list(bpy.context.scene.objects):
  if obj.type!='MESH':continue
  if obj.parent!=ref and not any(m.type=='ARMATURE' and m.object==ref for m in obj.modifiers):continue
  dup=obj.copy();dup.data=obj.data.copy();bpy.context.scene.collection.objects.link(dup)
  dup.name='SPARSE_EDIT_'+obj.name
  if dup.parent==ref:dup.parent=author;dup.matrix_parent_inverse=obj.matrix_parent_inverse.copy()
  for mod in dup.modifiers:
   if mod.type=='ARMATURE' and mod.object==ref:mod.object=author
  obj.hide_render=True;obj.hide_set(True)
 ref.hide_render=True;ref.hide_set(True)
 # Preserve all source action data: work only on independently copied actions.
 for move,source in src.items():
  raw=curves(source)
  source_paths=[(f.data_path,f.array_index,len(f.keyframe_points)) for f in raw]
  # With each stricter threshold we rebuild from the intact source, never a
  # previously simplified action, so retries cannot accumulate degradation.
  candidate=None;last=None
  for tol in (.35,.15,.06,.02,.0):
   if candidate is not None:
    author.animation_data.action=None
    candidate.use_fake_user=False
    bpy.data.actions.remove(candidate)
   candidate=source.copy();candidate.name='SPARSE_FK_'+move;candidate.use_fake_user=True
   reduction=reduce_group(source,candidate,tol)
   if reduction['sourceKeyGroups']==0:raise RuntimeError('NO_FK_LEG_QUATERNION_CHANNELS '+move)
   # Validate all ORIGINAL sample intervals plus independent quarter-times.
   origkey=sorted({round(float(k.co.x),6) for f in raw for k in f.keyframe_points})
   testtimes=set(origkey)
   for a,b in zip(origkey,origkey[1:]):testtimes.update((a+(b-a)*.25,a+(b-a)*.5,a+(b-a)*.75))
   ref.animation_data.action=source;author.animation_data.action=candidate
   extrema={k:0. for k in LIMIT};worst={};allpass=True
   for t in sorted(testtimes):
    frame(t);errors,location=compare(snapshot(ref),snapshot(author))
    for key,val in errors.items():
     if val>extrema[key]:extrema[key]=val;worst[key]={'time':t,'bone':location.get(key),'error':val}
     if val>LIMIT[key]:allpass=False
   last={'attemptTolerance_deg':tol,'limitsPassed':allpass,'maxError':extrema,'worst':worst,'samples':len(testtimes),**reduction}
   if allpass:break
  if not last['limitsPassed']:raise RuntimeError('ACTION_POSE_PARITY_FAILED_'+move)
  before=len(source_paths);after=len(curves(candidate))
  if before!=after or {(f.data_path,f.array_index) for f in raw}!={(f.data_path,f.array_index) for f in curves(candidate)}:
   raise RuntimeError('ACTION_CHANNEL_INVENTORY_CHANGED_'+move)
  last['originalAction']=source.name;last['editableAction']=candidate.name
  last['originalFCurves']=before;last['editableFCurves']=after
  report['actions'][move]=last;save()
 # All nonleg actions are original, and original FK actions still retain their keys.
 for move,source in src.items():
  if not source.use_fake_user:raise RuntimeError('ORIGINAL_SOURCE_NOT_PINNED_'+move)
 total=sum(v['sourceKeyGroups'] for v in report['actions'].values())
 sparse=sum(v['sparseKeyGroups'] for v in report['actions'].values())
 report['totalOriginalLegKeyGroups']=total;report['totalSparseLegKeyGroups']=sparse
 report['reductionFraction']=round(1-sparse/total,6) if total else 0
 if report['reductionFraction']<.05:raise RuntimeError('INSUFFICIENT_KEY_REDUCTION_'+str(report['reductionFraction']))
 author.animation_data.action=bpy.data.actions['SPARSE_FK_Heavy1']
 # Explicitly no IK: this is a cleanup of baked FK only.
 if any(c.type=='IK' for p in author.pose.bones for c in p.constraints):raise RuntimeError('IK_CONSTRAINT_PRESENT_IN_SPARSE_FK_RIG')
 note=bpy.data.texts.get('OBSIDIANTI_SPARSE_FK_README') or bpy.data.texts.new('OBSIDIANTI_SPARSE_FK_README')
 note.write('Original FK actions are preserved. Select SPARSE_FK_* actions on the editable rig.\n')
 note.write('Only copy action leg quaternion keys are reduced; no original actions or canonical GLB were changed.\n')
 note.write('This does not fix pre-existing shoe floor penetration or right foot placement.\n')
 bpy.ops.wm.save_as_mainfile(filepath=out,check_existing=False,compress=False)
 report['status']='SPARSE_FK_PARITY_PASS_UNAPPROVED_FOR_VISUAL_REVIEW';report['outputBlend']=out
 save();print('SPARSE_FK_POSE_PARITY=PASS REDUCTION='+str(report['reductionFraction']),flush=True)
except Exception as e:
 report['status']='SPARSE_FK_PARITY_FAILED';report['error']=type(e).__name__+': '+str(e)
 save();traceback.print_exc();raise
