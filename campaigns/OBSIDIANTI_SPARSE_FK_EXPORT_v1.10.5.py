"""Export ONLY the sparse FK authoring rig, never the reference rig."""
import bpy,sys,pathlib,json,traceback,collections
source,output,report=sys.argv[sys.argv.index('--')+1:]
MOVES=['Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp']
r={'status':'STARTED','sourceBlend':source,'output':output,'requested':MOVES}
def save():pathlib.Path(report).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
try:
 bpy.ops.wm.open_mainfile(filepath=source,load_ui=False)
 arm=bpy.data.objects.get('OBSIDIANTI_SPARSE_FK_EDITABLE_UNAPPROVED')
 if arm is None or arm.type!='ARMATURE':raise RuntimeError('SPARSE_FK_AUTHOR_RIG_MISSING')
 reference=bpy.data.objects.get('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT')
 if reference is None:raise RuntimeError('PROTECTED_FK_REFERENCE_MISSING')
 acts=[]
 for move in MOVES:
  a=bpy.data.actions.get('SPARSE_FK_'+move)
  if a is None:raise RuntimeError('SPARSE_FK_ACTION_MISSING_'+move)
  acts.append(a)
 # Create fresh export-only NLA tracks. Each track is a separately named glTF clip.
 arm.animation_data_create()
 ad=arm.animation_data
 ad.action=None
 for track in list(ad.nla_tracks):ad.nla_tracks.remove(track)
 for move,action in zip(MOVES,acts):
  t=ad.nla_tracks.new();t.name='SPARSE_FK_'+move
  strip=t.strips.new(t.name,int(action.frame_range[0]),action)
  strip.name=t.name;strip.blend_type='REPLACE';strip.extrapolation='HOLD';strip.influence=1.0
  t.mute=False
 meshes=[]
 for ob in bpy.data.objects:
  if ob.type!='MESH' or not ob.name.startswith('SPARSE_EDIT_'):continue
  belongs=ob.parent==arm or any(m.type=='ARMATURE' and m.object==arm for m in ob.modifiers)
  if belongs:meshes.append(ob)
 if not meshes:raise RuntimeError('NO_SKINNED_SPARSE_EDIT_MESHES')
 for ob in bpy.context.selected_objects:ob.select_set(False)
 for ob in bpy.data.objects:
  if ob.type in {'MESH','ARMATURE'}:
   ob.hide_set(False);ob.hide_render=False
   ob.select_set(ob==arm or ob in meshes)
 bpy.context.view_layer.objects.active=arm
 bpy.context.scene.frame_set(1)
 # Explicit selection guard prevents accidentally exporting the protected reference.
 selected=[x.name for x in bpy.context.selected_objects]
 if len(selected)!=len(meshes)+1 or reference.name in selected:raise RuntimeError('EXPORT_SELECTION_INVALID_'+repr(selected))
 r.update({'selectedObjects':selected,'sourceActions':[a.name for a in acts], 'sourceActionFrames':{a.name:[float(v) for v in a.frame_range] for a in acts}})
 save()
 opts=dict(filepath=output,export_format='GLB',use_selection=True,export_animations=True,
           export_nla_strips=True,export_apply=False,export_yup=True,export_lights=False,export_cameras=False)
 prop=bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
 # Current Blender (4.x) names this use_selection/export_selected, older uses use_selection.
 if 'export_selected' in prop:
  opts['export_selected']=opts.pop('use_selection')
 if 'export_animation_mode' in prop:opts['export_animation_mode']='NLA_TRACKS'
 if 'export_force_sampling' in prop:opts['export_force_sampling']=True
 if 'export_frame_step' in prop:opts['export_frame_step']=1
 if 'export_nla_strips' not in prop:opts.pop('export_nla_strips',None)
 if 'export_apply' not in prop:opts.pop('export_apply',None)
 for k in list(opts):
  if k not in prop:opts.pop(k)
 result=bpy.ops.export_scene.gltf(**opts)
 if 'FINISHED' not in result:raise RuntimeError('BLENDER_GLTF_EXPORT_NOT_FINISHED_'+str(result))
 if not pathlib.Path(output).is_file() or pathlib.Path(output).stat().st_size<20000:raise RuntimeError('EXPORTED_GLB_MISSING_OR_TOO_SMALL')
 r['status']='EXPORTED_PENDING_INDEPENDENT_GLB_VALIDATION';r['exportOptions']=opts;save()
 print('SPARSE_FK_GLB_EXPORTED='+output,flush=True)
except Exception as e:
 r.update(status='EXPORT_BLOCKED',error=type(e).__name__+': '+str(e));save();traceback.print_exc();raise
