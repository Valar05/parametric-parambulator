"""Export an existing Obsidianti FK authoring rig, without altering the input .blend.
Blender runs with factory settings and opens a SHA-locked published native file.
"""
import bpy,sys,pathlib,json,hashlib,traceback
args=sys.argv[sys.argv.index('--')+1:]
source,out,report=map(pathlib.Path,args)
SOURCE_SHA='30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def require(v,msg):
 if not v:raise RuntimeError(msg)
def emit(v):report.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
proof={'status':'STARTED','sourceSHA256':sha(source),'source':str(source),'output':str(out)}
try:
 require(proof['sourceSHA256']==SOURCE_SHA,'SOURCE_BLEND_HASH_MISMATCH')
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
 rig=bpy.data.objects.get('OBSIDIANTI_FK_FEET_EDITABLE');ref=bpy.data.objects.get('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT')
 require(rig is not None and ref is not None and rig.type==ref.type=='ARMATURE' and rig.data!=ref.data,'FK_RIG_ISOLATION_FAILED')
 objs=[rig]+[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('FK_EDITABLE__')]
 require(len(objs)>1,'EDITABLE_MESHES_MISSING')
 require(all(o!=ref for o in objs),'REFERENCE_RIG_IN_EXPORT')
 nla=[]
 for tr in rig.animation_data.nla_tracks:
  for st in tr.strips:
   if st.action:nla.append({'track':tr.name,'strip':st.name,'action':st.action.name,'start':float(st.frame_start),'end':float(st.frame_end)})
 require(len(nla)>=41,'FEWER_THAN_41_EDITABLE_NLA_STRIPS_'+str(len(nla)))
 for o in bpy.context.selected_objects:o.select_set(False)
 for o in objs:
  o.hide_set(False);o.hide_render=False;o.select_set(True)
 bpy.context.view_layer.objects.active=rig
 # Export tracks, not all globally linked Blender actions. This avoids duplicating
 # the readonly reference library and prevents authoring an unexpected new clip.
 opts=dict(filepath=str(out),export_format='GLB',use_selection=True,
   export_animations=True,export_animation_mode='NLA_TRACKS',export_skins=True,
   export_morph=True,export_apply=False,export_yup=True,
   export_materials='EXPORT')
 props=bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
 require('export_animation_mode' in props,'BLENDER_GLTF_NLA_TRACK_EXPORT_UNAVAILABLE')
 bpy.ops.export_scene.gltf(**opts)
 require(out.is_file() and out.stat().st_size>100000,'GLB_EXPORT_MISSING_OR_TOO_SMALL')
 proof.update(status='EXPORTED_FK_EDITABLE_GLTF_REVIEW_PENDING',outputSHA256=sha(out),
  bytes=out.stat().st_size,selectedObjects=[o.name for o in objs],sourceNLAStrips=nla,
  sourceNLACount=len(nla),referenceRigNotExported=True,
  ownerVisualAcceptance='PENDING')
 emit(proof)
 print('EXPORTED_FK_GLB='+str(out)+' SHA256='+proof['outputSHA256'],flush=True)
except Exception as exc:
 proof.update(status='BLOCKED',error=str(exc),traceback=traceback.format_exc());emit(proof);raise
