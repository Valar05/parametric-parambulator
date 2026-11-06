"""Create protected, native Blender FK baseline from the verified Ares-scaled GLB.
This is not an IK reconstruction. It saves the existing FK Actions without changing them.
"""
import bpy,sys,json,pathlib,hashlib,traceback
source,out,reportfile=sys.argv[sys.argv.index('--')+1:]
EXPECTED='955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32'
MOVES=('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
report={'schema':'obsidianti-native-fk-baseline-v1.10.1','status':'STARTED','sourceSHA256':None}
def save():pathlib.Path(reportfile).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
try:
 data=pathlib.Path(source).read_bytes();digest=hashlib.sha256(data).hexdigest()
 report['sourceSHA256']=digest
 if digest!=EXPECTED:raise RuntimeError('INPUT_GLB_SHA_MISMATCH')
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=source)
 arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
 if len(arms)!=1:raise RuntimeError('ARMATURE_COUNT_WRONG '+str(len(arms)))
 arm=arms[0];arm.name='OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT'
 actions={a.name:a for a in bpy.data.actions}
 if len(actions)<23:raise RuntimeError('EXPECTED_23_CLIPS_NOT_FOUND '+str(len(actions)))
 nla=[(tr.name,st.name,st.action.name) for tr in arm.animation_data.nla_tracks for st in tr.strips if st.action]
 missing=[move for move in MOVES if not any('Lionheart_'+move in entry for row in nla for entry in row)]
 if missing:raise RuntimeError('MISSING_FK_ATTACK_ACTIONS '+repr(missing))
 for a in actions.values():a.use_fake_user=True
 if arm.animation_data:
  arm.animation_data.use_nla=False
  for t in arm.animation_data.nla_tracks:t.mute=True
 # Imported animation is the authority. Do not modify any pose or constraint.
 for o in arms:
  if any(c.type=='IK' for pb in o.pose.bones for c in pb.constraints):
   raise RuntimeError('FK_BASELINE_UNEXPECTED_ACTIVE_IK')
 scene=bpy.context.scene;scene.frame_start=0;scene.frame_end=35
 note=bpy.data.texts.new('FK_BASELINE_READ_ME')
 note.write('Verified source: Ares-scaled pre-contact-FK candidate '+EXPECTED+'\n')
 note.write('All 23 original imported animations preserved. No native IK reconstruction applied.\n')
 note.write('Select the original named Action or its imported NLA strip to inspect a clip.\n')
 note.write('This baseline is editable, but NOT a visual or physical fix.\n')
 bpy.ops.wm.save_as_mainfile(filepath=out,check_existing=False,compress=False)
 if not pathlib.Path(out).is_file() or pathlib.Path(out).stat().st_size<100000:
  raise RuntimeError('BLEND_NOT_SAVED_OR_TOO_SMALL')
 report.update(status='FK_BASELINE_SAVED',blenderVersion=bpy.app.version_string,
               actionCount=len(actions),sourceActions=sorted(actions),
               nlaAssociations=nla,outputSHA256=hashlib.sha256(pathlib.Path(out).read_bytes()).hexdigest())
 save();print('FK_BASELINE_SAVED='+out,flush=True)
except Exception as e:
 report.update(status='BLOCKED',error=type(e).__name__+': '+str(e));save();traceback.print_exc();raise
