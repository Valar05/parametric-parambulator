"""Export 41 baked motions from the verified native IK authoring Blender file.
Source blend never saved or modified. Nondeforming IK controls remain in .blend.
"""
import bpy,sys,pathlib,json,hashlib,traceback
src,out,report=map(pathlib.Path,sys.argv[sys.argv.index('--')+1:])
EXPECTED='30ad2518a820e6b1770dcced6a46f1f2f91db28af799c60dfa21ab3488cda75e'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
a={'status':'STARTED','inputSHA256':EXPECTED,'visualAcceptance':'PENDING'}
def save():report.write_text(json.dumps(a,indent=2,sort_keys=True)+'\n')
try:
 need(sha(src)==EXPECTED,'PINNED_IK_BLEND_SHA_CHANGED')
 bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
 rig=bpy.data.objects.get('OBSIDIANTI_FK_FEET_EDITABLE')
 ref=bpy.data.objects.get('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT')
 need(rig and ref and rig.type=='ARMATURE' and ref.type=='ARMATURE' and rig.data!=ref.data,'AUTHORING_RIG_OR_REFERENCE_MISSING')
 need(rig.animation_data and len(rig.animation_data.nla_tracks)==41,'IK41_NLA_TRACKS_MISSING')
 tracks=[]
 for tr in rig.animation_data.nla_tracks:
  need(len(tr.strips)==1 and tr.strips[0].action and tr.strips[0].action.name.startswith('IK41_EDIT__'),'IK41_NLA_ACTION_INVALID_'+tr.name)
  tracks.append(tr.name)
 need(len(set(tracks))==41,'DUPLICATE_IK41_TRACK_NAMES')
 for side in ('Left','Right'):
  shin=rig.pose.bones['mixamorig:'+side+'Leg'];foot=rig.pose.bones['mixamorig:'+side+'Foot']
  ik=shin.constraints.get('IK41_TWO_BONE_'+side);rot=foot.constraints.get('IK41_FOOT_ROT_'+side)
  need(ik and ik.type=='IK' and ik.influence==1.0 and rot and rot.influence==1.0,'IK_NOT_ENABLED_'+side)
 meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('FK_EDITABLE__')]
 need(meshes,'EDITABLE_MESHES_MISSING')
 # All NLA tracks are deliberately unmuted for exporter discovery; GLTF NLA_TRACKS
 # traverses each separately. No scene or action changes are saved to native source.
 for tr in rig.animation_data.nla_tracks:tr.mute=False
 rig.animation_data.action=None
 rig.animation_data.use_nla=True
 for ob in bpy.context.selected_objects:ob.select_set(False)
 for ob in [rig,*meshes]:ob.hide_set(False);ob.hide_render=False;ob.select_set(True)
 ref.hide_set(True);ref.hide_render=True
 bpy.context.view_layer.objects.active=rig
 kw=dict(filepath=str(out),export_format='GLB',use_selection=True,export_animations=True,
         export_animation_mode='NLA_TRACKS',export_skins=True,export_materials='EXPORT',
         export_apply=False,export_yup=True,export_force_sampling=True,export_frame_step=1)
 opts=set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
 need('export_animation_mode' in opts and 'export_force_sampling' in opts,'BLENDER_GLTF_BAKE_OPTIONS_UNAVAILABLE')
 bpy.ops.export_scene.gltf(**kw)
 need(out.is_file() and out.stat().st_size>100000,'EXPORTED_GLTF_MISSING')
 a.update(status='IK41_BAKED_41_CLIP_PREVIEW_EXPORTED_UNAPPROVED',outputSHA256=sha(out),bytes=out.stat().st_size,
          sourceNLA=tracks,sourceNLACount=len(tracks),editableIKRigStillOnlyInNativeBlend=True,sourceUnmodified=sha(src)==EXPECTED)
 need(a['sourceUnmodified'],'SOURCE_BLEND_CHANGED')
 save();print('IK41_GLTF_EXPORTED='+str(out)+' SHA256='+a['outputSHA256'],flush=True)
except BaseException as e:
 a.update(status='BLOCKED',error=repr(e),traceback=traceback.format_exc()[-4000:]);save();raise
