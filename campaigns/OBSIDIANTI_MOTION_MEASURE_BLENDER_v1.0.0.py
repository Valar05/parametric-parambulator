#!/usr/bin/env python3
"""Read-only Blender measurement of native donor and exact target GLB.
Does not save scenes, edit source files, add constraints, or retarget motions.
"""
import bpy,sys,json,math,csv,re,collections,traceback,pathlib
from mathutils import Vector
src,kind,outdir=sys.argv[sys.argv.index('--')+1:]
out=pathlib.Path(outdir);out.mkdir(parents=True,exist_ok=True)
MOVES=['Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp']
ALIASES={'hips':['Hips','Pelvis'], 'spine':['Spine','Spine1','Spine01'], 'chest':['Spine2','Chest','UpperChest'], 'root':['Root','Armature','root'],'left_hip':['LeftUpLeg','LeftThigh'],'right_hip':['RightUpLeg','RightThigh'],
 'left_knee':['LeftLeg','LeftShin'],'right_knee':['RightLeg','RightShin'],
 'left_foot':['LeftFoot','LeftAnkle'],'right_foot':['RightFoot','RightAnkle'],
 'left_ik':['LeftFoot.IK','Foot.IK.L','LeftFootIK','FootIK_L'],
 'right_ik':['RightFoot.IK','Foot.IK.R','RightFootIK','FootIK_R'],
 'left_pole':['LeftKnee.IK','Knee.IK.L','LeftKneeIK'],
 'right_pole':['RightKnee.IK','Knee.IK.R','RightKneeIK']}
def norm(s):return re.sub(r'[^a-z0-9]','',s.lower().split(':')[-1])
def locate(arm,key,required=True):
 b=list(arm.pose.bones)
 for a in ALIASES[key]:
  exact=[x for x in b if norm(x.name)==norm(a)]
  if len(exact)==1:return exact[0]
 if required:raise RuntimeError('BONE_UNRESOLVED '+kind+' '+key+' '+repr([x.name for x in b]))
 return None
def resolve_action(name):
 acts=list(bpy.data.actions)
 exact=[a for a in acts if a.name==name]
 if len(exact)==1:return exact[0]
 matches=[a for a in acts if a.name.endswith('_'+name) or a.name.endswith('|'+name) or a.name.endswith('.'+name)]
 if len(matches)==1:return matches[0]
 raise RuntimeError('ACTION_UNRESOLVED '+name+' '+repr([a.name for a in acts]))
def fcurves(a):
 try:return list(a.fcurves)
 except (AttributeError,RuntimeError):
  z=[]
  for layer in getattr(a,'layers',[]):
   for strip in getattr(layer,'strips',[]):
    for bag in getattr(strip,'channelbags',[]):z.extend(bag.fcurves)
  return z
def world(arm,p):return arm.matrix_world@p.matrix
# Keep all trajectories in native Blender axes, then rotate target/source into comparably anatomical axes only in analysis.
def vec(v):return [round(float(x),8) for x in v]
def quat(q):return [round(float(x),8) for x in (q.w,q.x,q.y,q.z)]
def position(arm,p):return (arm.matrix_world@p.matrix).translation
def side_data(arm,roles,side,rest):
 up=roles[side+'_hip'];kn=roles[side+'_knee'];ft=roles[side+'_foot'];h=position(arm,up);k=position(arm,kn);f=position(arm,ft)
 l1=(arm.matrix_world@up.bone.matrix_local).translation
 l2=(arm.matrix_world@kn.bone.matrix_local).translation
 l3=(arm.matrix_world@ft.bone.matrix_local).translation
 thigh=(l2-l1).length;shin=(l3-l2).length;d=(f-h).length
 ret={'hip':vec(h),'knee':vec(k),'ankle':vec(f),'hipToAnkle_m':round(d,7),
 'thighRest_m':round(thigh,7),'shinRest_m':round(shin,7),'extensionRatio':round(d/max(1e-6,thigh+shin),7),
 'kneeAngle_deg':round(math.degrees((h-k).angle(f-k)),6),
 'footQuatWXYZ':quat(world(arm,ft).to_quaternion()),
 'footLocalDelta':vec(ft.location),
 'footLocalRotWXYZ':quat(ft.rotation_quaternion if ft.rotation_mode=='QUATERNION' else ft.matrix_basis.to_quaternion())}
 for key,tag in [('ik','footController'),('pole','kneePole')]:
  p=roles.get(side+'_'+key)
  if p:
   ret[tag]={'world':vec(position(arm,p)),'localDelta':vec(p.location), 'quatWXYZ':quat(world(arm,p).to_quaternion()),
             'parent':p.parent.name if p.parent else None}
 return ret
try:
 if kind=='lionheart':bpy.ops.wm.open_mainfile(filepath=src)
 elif kind=='obsidianti':bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
 else:raise RuntimeError('INVALID_KIND')
 arms=[o for o in bpy.data.objects if o.type=='ARMATURE' and len(o.pose.bones)>=24]
 if len(arms)!=1:raise RuntimeError('ARMATURE_AMBIGUOUS '+repr([(x.name,len(x.pose.bones)) for x in arms]))
 arm=arms[0];roles={k:locate(arm,k,required=k not in ('left_ik','right_ik','left_pole','right_pole','spine','chest','root')) for k in ALIASES}
 ad=arm.animation_data_create()
 clips={}
 if kind=='lionheart':clips={n:resolve_action(n) for n in MOVES}
 else:
  inventory=[]
  for t in ad.nla_tracks:
   for strip in t.strips:
    if strip.action:inventory.append((t.name,strip.name,strip.action))
  if ad.action:inventory.append(('__ACTIVE__','__ACTIVE__',ad.action))
  for n in MOVES:
   label='Lionheart_'+n;c={id(a):a for track,strip,a in inventory if label in (track,strip,a.name)}
   if len(c)!=1:raise RuntimeError('GLB_ACTION_NOT_UNIQUE '+label)
   clips[n]=next(iter(c.values()))
 for tr in ad.nla_tracks:tr.mute=True
 ad.use_nla=False
 fps=bpy.context.scene.render.fps/bpy.context.scene.render.fps_base
 metadata={'kind':kind,'source':src,'blenderVersion':bpy.app.version_string,'fps':fps,'rig':arm.name,
  'objectMatrixWorld':[vec(r) for r in arm.matrix_world],
  'roles':{k:v.name if v else None for k,v in roles.items()},
  'boneParents':{p.name:(p.parent.name if p.parent else None) for p in arm.pose.bones},
  'constraints':{p.name:[{'name':c.name,'type':c.type,'target':getattr(getattr(c,'target',None),'name',None),'subtarget':getattr(c,'subtarget',None),'influence':c.influence} for c in p.constraints] for p in arm.pose.bones if p.constraints},
  'sourceActions':{},'meshCount':len([x for x in bpy.data.objects if x.type=='MESH'])}
 for n,a in clips.items():
  cs=fcurves(a)
  raw=[]
  for c in cs:
   if 'location' not in c.data_path:continue
   ks=list(c.keyframe_points)
   raw.append({'channel':c.data_path,'index':c.array_index,'keyTimes':[round(k.co.x,6) for k in ks],
               'firstLastValues':[round(ks[0].co.y,7),round(ks[-1].co.y,7)] if ks else [],'keyCount':len(ks)})
  metadata['sourceActions'][n]={'name':a.name,'frameRange':list(map(float,a.frame_range)),
    'translationChannels':raw,'fcurveCount':len(cs)}
 (out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
 # Target foot skin witness: vertices heavily weighted to foot/toe joint; all evaluated mesh vertices
 # only at original key and midpoint samples, bounded by ~80 sample frames per attack.
 candidates={side:[] for side in ('left','right')}
 if kind=='obsidianti':
  for obj in bpy.data.objects:
   if obj.type!='MESH':continue
   groups={g.index:norm(g.name) for g in obj.vertex_groups}
   if not groups:continue
   for vert in obj.data.vertices:
    for side in ('left','right'):
     if any(groups.get(g.group,'').startswith(side+'foot') or groups.get(g.group,'').startswith(side+'toe') for g in vert.groups if g.weight>=.25):
      candidates[side].append((obj.name,vert.index));break
 metadata['skinWitnessCounts']={side:len(v) for side,v in candidates.items()}
 (out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
 fieldnames=['kind','clip','frame','seconds','side','hip_x','hip_y','hip_z','knee_x','knee_y','knee_z',
 'ankle_x','ankle_y','ankle_z','hipToAnkle_m','thighRest_m','shinRest_m','extensionRatio','kneeAngle_deg',
 'hipLocal_x','hipLocal_y','hipLocal_z','chest_x','chest_y','chest_z','root_x','root_y','root_z','hipRotation_w','hipRotation_x','hipRotation_y','hipRotation_z','footLocal_x','footLocal_y','footLocal_z',
 'ik_x','ik_y','ik_z','pole_x','pole_y','pole_z','soleMinZ','soleMinY','footRotation_w','footRotation_x','footRotation_y','footRotation_z']
 with (out/'trajectories.csv').open('w',newline='') as fp:
  writer=csv.DictWriter(fp,fieldnames=fieldnames);writer.writeheader()
  for n,a in clips.items():
   ad.action=a
   start,end=map(float,a.frame_range)
   if end-start>400 or end<=start:raise RuntimeError('ACTION_DURATION_INVALID '+n+' '+str((start,end)))
   # Sample native time at 1/2 frame resolution, preserving source/key timing for post-analysis.
   frames=[start+i*.5 for i in range(int(math.floor((end-start)*2))+1)]
   if end-frames[-1]>1e-5:frames.append(end)
   previous={}
   for f in frames:
    bpy.context.scene.frame_set(math.floor(f),subframe=f-math.floor(f));bpy.context.view_layer.update()
    evaluated=bpy.context.evaluated_depsgraph_get()
    mesh_cache={}
    # Source and target measured in their actual import coordinate systems; metadata contains axes.
    for side in ('left','right'):
     row=side_data(arm,roles,side,None)
     h=row['hip'];k=row['knee'];foot=row['ankle'];r={'kind':kind,'clip':n,'frame':round(f,5),'seconds':round((f-start)/fps,7),'side':side,
      **{'hip_'+axis:h[i] for i,axis in enumerate('xyz')},
      **{'knee_'+axis:k[i] for i,axis in enumerate('xyz')},
      **{'ankle_'+axis:foot[i] for i,axis in enumerate('xyz')},
      'hipToAnkle_m':row['hipToAnkle_m'],'thighRest_m':row['thighRest_m'],'shinRest_m':row['shinRest_m'],
      'extensionRatio':row['extensionRatio'],'kneeAngle_deg':row['kneeAngle_deg'],
      **{'hipLocal_'+axis:roles['hips'].location[i] for i,axis in enumerate('xyz')},
      **{'chest_'+axis:(vec(position(arm,roles['chest']))[i] if roles['chest'] else None) for i,axis in enumerate('xyz')},
      **{'root_'+axis:(vec(position(arm,roles['root']))[i] if roles['root'] else None) for i,axis in enumerate('xyz')},
      **{'hipRotation_'+axis:quat(world(arm,roles['hips']).to_quaternion())[i] for i,axis in enumerate('wxyz')},
      **{'footLocal_'+axis:roles[side+'_foot'].location[i] for i,axis in enumerate('xyz')},
      **{'ik_'+axis:row.get('footController',{}).get('world',[None]*3)[i] for i,axis in enumerate('xyz')},
      **{'pole_'+axis:row.get('kneePole',{}).get('world',[None]*3)[i] for i,axis in enumerate('xyz')},
      **{'footRotation_'+axis:row['footQuatWXYZ'][i] for i,axis in enumerate('wxyz')}}
     if kind=='obsidianti' and candidates[side]:
      # Evaluate true deformed mesh at all sampled frames and include actual skinning evidence.
      zs=[];ys=[]
      byobj=collections.defaultdict(list)
      for name,idx in candidates[side]:byobj[name].append(idx)
      for objname,indices in byobj.items():
       ob=bpy.data.objects[objname]
       if ob.type!='MESH':continue
       if objname not in mesh_cache:
        eob=ob.evaluated_get(evaluated);mesh=eob.to_mesh()
        mesh_cache[objname]=(eob,mesh)
       eob,mesh=mesh_cache[objname]
       mat=eob.matrix_world
       for idx in indices:
        if idx>=len(mesh.vertices):continue
        p=mat@mesh.vertices[idx].co;zs.append(p.z);ys.append(p.y)
      if zs:r['soleMinZ']=min(zs);r['soleMinY']=min(ys)
     writer.writerow(r)
    for eob,mesh in mesh_cache.values():eob.to_mesh_clear()
   print('MEASURED='+kind+'/'+n+' half_frames='+str(len(frames)),flush=True)
 print('MEASUREMENT_COMPLETE='+kind,flush=True)
except Exception as e:
 (out/'blender_error.txt').write_text(traceback.format_exc())
 traceback.print_exc();raise
