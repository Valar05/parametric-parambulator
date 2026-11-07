#!/usr/bin/env python3
"""Derive vendor operator calls from the already-proven v2.0.12 repository baseline.
All modifications are explicit, one-occurrence, fail-closed substitutions.
"""
from __future__ import annotations
import pathlib,hashlib
BASE='campaigns/OBSIDIANTI_ARP_BLENDER5_ISOLATED_v2.0.12_blender_trial.py'
EXPORT='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_export.py'
VIEW='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_viewer.html'
SERVER='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_server.py'

def one(s,b,a):
 count=s.count(b)
 if count!=1:raise RuntimeError('DERIVE_SOURCE_PRECONDITION_'+str(count)+'_'+b[:75])
 return s.replace(b,a,1)

def make(repo,packet,version):
 repo=pathlib.Path(repo);packet=pathlib.Path(packet)
 s=(repo/BASE).read_text()
 selection='''def select_action(src,clip):
 acts=[a for a in bpy.data.actions if a.name==clip]
 if len(acts)!=1:raise RuntimeError('NATIVE_SOURCE_ACTION_MISSING '+clip)
 ad=src.animation_data_create();ad.use_nla=False
 for t in ad.nla_tracks:t.mute=True
 ad.action=acts[0]
 if hasattr(ad,'action_slot') and ad.action_slot is None and hasattr(acts[0],'slots'):
  for slot in acts[0].slots:ad.action_slot=slot;break
 return acts[0]
'''
 replacement='''def select_action(src,name,slot_id):
 action=bpy.data.actions.get(name)
 if action is None:raise RuntimeError('SOURCE_ACTION_MISSING_'+name)
 slots=[s for s in action.slots if s.identifier==slot_id and s.target_id_type=='OBJECT']
 if len(slots)!=1:raise RuntimeError('SOURCE_ANIMATION_SLOT_NOT_FOUND_'+name+'_'+slot_id)
 chosen=slots[0];num=0;useful=0
 for layer in action.layers:
  for strip in layer.strips:
   try:bag=strip.channelbag(chosen,ensure=False)
   except (AttributeError,RuntimeError,TypeError):bag=None
   if not bag:continue
   num+=len(bag.fcurves)
   useful+=sum(1 for fc in bag.fcurves if 'pose.bones["mixamorig:' in fc.data_path)
 if num<1 or useful<1:raise RuntimeError('SOURCE_ACTION_SLOT_HAS_NO_ARMATURE_MOTION_'+name+'_'+slot_id)
 ad=src.animation_data_create();ad.use_nla=False
 for tr in ad.nla_tracks:tr.mute=True
 ad.action=action;ad.action_slot=chosen
 if ad.action_slot!=chosen:raise RuntimeError('EXACT_ARES_ACTION_SLOT_BINDING_FAILED_'+name+'_'+slot_id)
 src['mudman_source_action']=name;src['mudman_source_slot']=slot_id
 src['mudman_source_curve_count']=num;src['mudman_source_useful_curves']=useful
 return action
'''
 s=one(s,selection,replacement)
 s=one(s,'src=source_candidates[0];action=select_action(src,args.clip)', 'src=source_candidates[0];action=select_action(src,args.action,args.slot)')
 target="  bpy.ops.import_scene.gltf(filepath=args.target,import_shading='NORMALS')"
 new='''  bpy.ops.import_scene.fbx(filepath=args.target)
  # The FBX remains the actual skinned target. This tag identifies it in the
  # export stage without relying on Blender's imported armature object name.
'''
 s=one(s,target,new.rstrip('\n'))
 s=one(s,"  tgt=targets[0];meshes=[o for o in arrivals if o.type=='MESH'", "  tgt=targets[0];tgt['mudman_target']=True;meshes=[o for o in arrivals if o.type=='MESH'")
 # Use the real uploaded Meshy texture if the FBX importer doesn't wire its
 # single texture automatically. No new procedural materials or model editing.
 needle="  if not meshes:raise RuntimeError('TARGET_WEIGHTED_SKIN_MISSING')\n  tgt.data.pose_position='POSE'"
 texture='''  if not meshes:raise RuntimeError('TARGET_WEIGHTED_SKIN_MISSING')
  image_path=pathlib.Path(args.target).with_suffix('.png')
  if not image_path.is_file():raise RuntimeError('EXACT_MUDMAN_PNG_MISSING_'+str(image_path))
  image=bpy.data.images.load(str(image_path),check_existing=True)
  # A texture may be embedded by FBX or linked through material nodes; ensure
  # the owner's uploaded original is what is present in the review output.
  wired=0
  for ob in meshes:
   if not ob.data.materials:
    mat=bpy.data.materials.new(name='MUDMAN_ORIGINAL_MESHY_TEXTURE');ob.data.materials.append(mat)
   for mat in ob.data.materials:
    if mat is None:continue
    mat.use_nodes=True
    bsdf=next((node for node in mat.node_tree.nodes if node.type=='BSDF_PRINCIPLED'),None)
    if bsdf is None:continue
    tex=next((node for node in mat.node_tree.nodes if node.type=='TEX_IMAGE' and node.image==image),None)
    if tex is None:
     tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);wired+=1
  if wired<1:raise RuntimeError('MUDMAN_ORIGINAL_TEXTURE_NOT_WIRED')
  result['mudmanTexture']={'name':image.name,'materialLinks':wired,'source':image_path.name}
  tgt.data.pose_position='POSE' '''
 s=one(s,needle,texture.rstrip())
 s=one(s,"  if end-start<5 or end-start>180:raise RuntimeError('NATIVE_ACTION_FRAME_RANGE_UNEXPECTED')", "  if end-start>1200:raise RuntimeError('ACTION_TOO_LONG_FOR_REVIEW_'+str(end-start))\n  if end-start<5:result['sourceStaticOrShort']=True;end=start+6")
 s=one(s,"  result['sourceMotion']=motion_stats(witnesses(src,start,end))", "  result['sourceWitness17']=witnesses(src,start,end)\n  result['sourceMotion']=motion_stats(result['sourceWitness17'])")
 s=one(s,"  result['targetMotion']=motion_stats(witnesses(tgt,start,end))", "  result['targetWitness17']=witnesses(tgt,start,end)\n  result['targetMotion']=motion_stats(result['targetWitness17'])")
 s=one(s,"  result['arpSourceAction']=scene.source_action", '''  result['arpSourceAction']=scene.source_action
  ss=next((slot for slot in action.slots if slot.identifier==args.slot),None)
  if ss is None:raise RuntimeError('SOURCE_SLOT_LOST_AFTER_ARP_SCENE_CALLBACK')
  src.animation_data.action=action;src.animation_data.action_slot=ss
  result['sourceSlot']={'identifier':ss.identifier,'sourceAction':action.name,
     'curveCount':int(src['mudman_source_curve_count']),
     'mappedCurveCount':int(src['mudman_source_useful_curves'])}''')
 s=one(s,"  result['mapping']={'boneCount':len(active),'mapped':active,'excludedCount':len(dropped)}", "  result['mapping']={'boneCount':len(active),'mapped':active,'excludedCount':len(dropped),\n    'profile':'ARES_ALL_SLOTS_TO_MUDMAN_MIXAMO','hipsLocation':True,'hipsRoot':True}")
 s=one(s,"  output_action=targetad.action\n  result['targetAction']=output_action.name", "  output_action=targetad.action\n  output_action.name=args.clip+'_remap'\n  result['targetAction']=output_action.name")
 s=one(s," for n in ('private','source','source-sha','target','target-sha','clip','output'):ap.add_argument('--'+n,required=True)"," for n in ('private','source','source-sha','target','target-sha','clip','action','slot','output'):ap.add_argument('--'+n,required=True)")
 (packet/'blender_trial.py').write_text(s)
 compile(s,str(packet/'blender_trial.py'),'exec')
 exp=(repo/EXPORT).read_text()
 exp=one(exp,"targets=[ob for ob in bpy.data.objects if ob.type=='ARMATURE' and ob.name.startswith('SmartRigArmature') and all('mixamorig:'+x in ob.pose.bones for x in ('Hips','LeftFoot','RightFoot'))]", "targets=[ob for ob in bpy.data.objects if ob.type=='ARMATURE' and bool(ob.get('mudman_target')) and all('mixamorig:'+x in ob.pose.bones for x in ('Hips','LeftFoot','RightFoot'))]")
 exp=one(exp,'if end-start<5 or end-start>300:raise RuntimeError(\'ACTION_FRAME_RANGE_INVALID\')',"if end-start<5 or end-start>1200:raise RuntimeError('ACTION_FRAME_RANGE_INVALID')")
 (packet/'export.py').write_text(exp);compile(exp,str(packet/'export.py'),'exec')
 html=(repo/VIEW).read_text()
 html=one(html,'<option value="Heavy1">Heavy1</option><option value="AxeKick">AxeKick</option>', '<option value="Mudman_Jab-Enemy">Mudman Jab-Enemy</option>')
 html=one(html,"mode==='candidate'?'candidate'+clip:'canonical'","mode==='candidate'?'candidate':'canonical'")
 html=one(html,'manifest=await mr.json();', '''manifest=await mr.json();
const animations=manifest.models.candidate.animations;
if(!Array.isArray(animations)||!animations.length)throw Error('NO_MUDMAN_ACTIONS_IN_MANIFEST');
el('move').replaceChildren();
const featured=['Mudman_Jab-Enemy','Mudman_Cross-Enemy','Mudman_Idle','Mudman_Run'];
const ordered=[...animations].sort((a,b)=>{
 const ai=featured.indexOf(a),bi=featured.indexOf(b);
 return (ai<0?999:ai)-(bi<0?999:bi)||a.localeCompare(b);
});
for(const name of ordered){const option=document.createElement('option');option.value=name;option.textContent=name;el('move').appendChild(option)}
''')
 html=html.replace('Obsidianti | ARP live 3D review','Mudman | All Ares animations')
 html=html.replace('Obsidianti | Auto-Rig Pro Interactive Review','Mudman | Ares ARP Review')
 html=html.replace('Heavy1 REVIEW | AxeKick OWNER ACCEPTED','MUDMAN ARES ACTION TRANSFER | UNAPPROVED')
 html=html.replace('AxeKick accepted; Heavy1 hip/foot IK under review. Floor guide is visual, not a contact solver.', 'Every populated Ares action slot transferred to the original Mudman Mixamo FBX. Includes enemy Jab/Cross. No manual cleanup. Floor guide is visual, not a physical ground solver.')
 html=html.replace('Review exported ARP Actions in the existing interactive viewer.', 'Review every exported Ares action slot on the Mudman.')
 (packet/'viewer.html').write_text(html)
 server=(repo/SERVER).read_text().replace('ObsidiantiARPViewer/2.0.13','MudmanAresARPViewer/2.0.20')
 (packet/'server.py').write_text(server)
 return {n:hashlib.sha256((packet/n).read_bytes()).hexdigest() for n in ('blender_trial.py','export.py','viewer.html','server.py')}
