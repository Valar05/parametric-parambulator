import bpy,sys,json,hashlib,pathlib
src,out=sys.argv[sys.argv.index('--')+1:]
expected="81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4"
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert sha(src)==expected,'SOURCE_BLEND_SHA_MISMATCH'
bpy.ops.wm.open_mainfile(filepath=src)
arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
assert len(arms)==1,('SOURCE_ARMATURE_COUNT',len(arms))
arm=arms[0]
assets=[o for o in bpy.data.objects if o.type=='MESH' and (o.parent==arm or any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers))]
assert assets,'SKIN_MESH_NOT_FOUND'
assert all(any(a.name==n for a in bpy.data.actions) for n in ('Idle','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp','Cast')),'REQUIRED_SOURCE_ACTION_MISSING'
for o in bpy.context.selected_objects:o.select_set(False)
for o in [arm,*assets]:
 o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=arm
# The key under test: Blender evaluates IK/Copy Rotation before glTF animation baking.
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_apply=False,export_current_frame=False,export_reset_pose_bones=False)
assert pathlib.Path(out).stat().st_size>10000,'EMPTY_EXPORT'
pathlib.Path(out+'.json').write_text(json.dumps({'sourceSha256':expected,'exportSha256':sha(out),'mode':'BLENDER_GLTF_EXPORT_EVALUATED_CONSTRAINTS_ACTIONS','blenderVersion':bpy.app.version_string,'sourceActions':sorted(a.name for a in bpy.data.actions),'sourceConstraints':{b.name:[c.type for c in b.constraints] for b in arm.pose.bones if b.constraints}},indent=2))
print('LIONHEART_EXPORTED_GLB_SHA256='+sha(out),flush=True)
