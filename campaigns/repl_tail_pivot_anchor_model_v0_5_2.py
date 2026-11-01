#!/usr/bin/env python3
"""Real Repl GLB v0.5.1 -> v0.5.2, deterministic in-memory fix.

One canonical model: update its tail base and its descendant rest offsets and
inverse bind matrices, then recompute only the third (slow-straighten) clip.
No other model, animation, material, mesh, vertex weight, or bone is changed.

The selected socket is the measured dominant body/tail intersection arc:
world (0.000, 1.204, -0.889). This is a geometric estimate, not an exact
closed ring or a separately approved manual gizmo reading.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct

ROOT=(0.0,1.204,-0.889)
OLD_ROOT=(0.0,1.050,-0.930)
SOURCE_SHA='d44da2839ba05a4c520066e0d76cdb95339c2917456ee46fb27a02a7693c2d7a'
ENGINE_FILES={
 'repl_hair_bind_v0_1_0.py':'33ca93660f3d5858d4496027902b9b7a7e44d800',
 'repl_hair_five_controls_v0_2_0.py':'287567d6baf8e8fa415580dc57ee86600772f797',
 'repl_tail_straighten_gizmo_v0_4_0.py':'a24601bf8b509732623a7b4219e6be1f6a556794',
 'repl_tail_gizmo_v0_4_0.js':'1b4396ed0027a0a75baed840d7ed741e57c58a92',
}
TAIL=('REPL_TAIL_BASE','REPL_TAIL_TIP','REPL_TAIL_NEAR_TIP','REPL_TAIL_TERMINAL')
MANE=('REPL_MANE_REAR','REPL_MANE_MIDDLE','REPL_MANE_FRONT')
CLIP_NAME='REPL_TAIL_SLOW_STRAIGHTEN_14S_FOUR_JOINTS'

class Blocked(RuntimeError):pass

def need(v,why):
    if not v:raise Blocked(why)

def sha(b):return hashlib.sha256(b).hexdigest()

def git_blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def install_engine(path,label):
    import sys
    spec=importlib.util.spec_from_file_location(label,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def engines(repo):
    names=[]
    for name,blob in ENGINE_FILES.items():
        f=repo/'campaigns'/name
        need(f.is_file(),'PINNED_ENGINE_MISSING:'+name)
        need(git_blob(f.read_bytes())==blob,'PINNED_ENGINE_CHANGED:'+name)
        names.append(name)
    return (
      install_engine(repo/'campaigns'/names[0],'repl_fix_v010'),
      install_engine(repo/'campaigns'/names[1],'repl_fix_v020'),
      install_engine(repo/'campaigns'/names[2],'repl_fix_v040'),
      (repo/'campaigns'/names[3]).read_text('utf8')
    )

def glb_chunks(data):
    need(len(data)>28 and data[:4]==b'glTF','NOT_A_GLB')
    need(struct.unpack_from('<I',data,4)[0]==2 and struct.unpack_from('<I',data,8)[0]==len(data),'BAD_GLB_HEADER')
    n,kind=struct.unpack_from('<I4s',data,12)
    need(kind==b'JSON','GLB_JSON_CHUNK_MISSING')
    start=20+n
    n2,kind2=struct.unpack_from('<I4s',data,start)
    need(kind2==b'BIN\0' and start+8+n2==len(data),'GLB_BIN_CHUNK_INCONSISTENT')
    return json.loads(data[20:start]),data[start+8:]

def world_pos(world,node):return tuple(world[node][k] for k in (3,7,11))

def distance(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))

def euler_segment_angle(a,b):return math.degrees(math.atan2(b[1]-a[1],-(b[2]-a[2])))

def subset_deform(base,positions,joints,weights,mats,indices):
    return [base.deform_vertex(positions[k],joints[k],weights[k],mats) for k in indices]

def step_frames(doc,binary,base,anim_index):
    animation=doc['animations'][anim_index]
    node_to_key={}
    for channel in animation['channels']:
        sampler=animation['samplers'][channel['sampler']]
        need(channel['target']['path']=='rotation' and sampler.get('interpolation')=='LINEAR',
             'UNEXPECTED_ANIMATION_CHANNEL_OR_INTERPOLATION')
        node_to_key[channel['target']['node']]=base.accessor(doc,binary,sampler['output'])
    return node_to_key

def measured_root_indices(positions):
    # The dominant real mesh intersection arc was analyzed using the original
    # body and tail triangles. This is a stationary witness slice, not guessed
    # from the bounding box of the entire tail.
    narrow=[i for i,p in enumerate(positions)
         if -.93<p[2]<-.86 and 1.18<p[1]<1.23]
    broad=[i for i,p in enumerate(positions)
         if -.94<p[2]<-.84 and 1.15<p[1]<1.30]
    need(20<=len(narrow)<=45 and 65<=len(broad)<=95,
         'ATTACHMENT_CROSS_SECTION_CHANGED')
    center=tuple(sum(positions[i][a] for i in narrow)/len(narrow) for a in range(3))
    need(distance(center,ROOT)<0.013,
         'SELECTED_ROOT_IS_NOT_NEAR_MEASURED_ROOT_ARC')
    return narrow,broad,center

def repair(source_bytes,base,v2,v4,gizmo_js):
    need(sha(source_bytes)==SOURCE_SHA,'PARENT_V051_CANONICAL_GLB_SHA_MISMATCH')
    doc,binary=glb_chunks(source_bytes)
    need(len(doc['nodes'])==53 and len(doc['skins'])==1 and
         len(doc['skins'][0]['joints'])==50 and len(doc['animations'])==3 and
         len(doc['meshes'])==2,'V051_RIG_OR_MESH_COUNT_CHANGED')
    need(doc['animations'][2]['name']==CLIP_NAME and
         len(doc['animations'][2]['channels'])==4,'EXPECTED_SLOW_STRAIGHTEN_CLIP_NOT_FOUND')
    old_doc,old_binary=glb_chunks(source_bytes)
    # Preserve JSON sections that are not explicitly authorized to change.
    locked={name:json.dumps(doc[name],sort_keys=True)
            for name in ('meshes','materials','images','textures','samplers','scenes')
            if name in doc}
    locked_other_nodes={i:json.dumps(n,sort_keys=True) for i,n in enumerate(doc['nodes'])
                        if n.get('name') not in TAIL}
    old_clips=json.dumps(doc['animations'][:2],sort_keys=True)
    old_skin_joints=list(doc['skins'][0]['joints'])
    names={n.get('name'):i for i,n in enumerate(doc['nodes'])}
    need(all(n in names for n in TAIL+MANE+('Bone_004',)),
         'REQUIRED_ANATOMY_NODES_MISSING')
    joints=old_skin_joints
    mapping={doc['nodes'][nodeid]['name']:idx for idx,nodeid in enumerate(joints)}
    need(all(n in mapping for n in TAIL+MANE+('Bone_004',)),
         'REQUIRED_SKIN_JOINTS_MISSING')
    before=base.world_matrices(doc,{})
    old_roots={name:world_pos(before,names[name]) for name in TAIL}
    need(distance(old_roots[TAIL[0]],OLD_ROOT)<1e-4,'SOURCE_PIVOT_ALREADY_CHANGED')
    old_inverse=base.accessor(doc,binary,doc['skins'][0]['inverseBindMatrices'])
    need(len(old_inverse)==50,'EXPECTED_FIFTY_IBMS_MISSING')
    orig_ibms=[v2.matrix_from_glb_mat4(row) for row in old_inverse]
    new_ibms=[list(row) for row in orig_ibms]
    # The new root is in the body/tail intersection, ABOVE and slightly ahead
    # of the old displaced pivot. All children retain their exact original
    # rest-world positions; changing the base must NOT shift the others.
    desired=[ROOT,*[old_roots[n] for n in TAIL[1:]]]
    for i,(name,target) in enumerate(zip(TAIL,desired)):
        parent='Bone_004' if i==0 else TAIL[i-1]
        parent_ibm=new_ibms[mapping[parent]]
        translation=base.apply_matrix(parent_ibm,target)
        node=doc['nodes'][names[name]]
        need('matrix' not in node,'PIVOT_BONE_TRANSFORM_UNSUPPORTED')
        node['translation']=[float(v) for v in translation]
        new_ibms[mapping[name]]=base.matrix_mult(
            v2.translation_matrix(tuple(-v for v in translation)),parent_ibm)
    updated=base.world_matrices(doc,{})
    center_error=distance(world_pos(updated,names[TAIL[0]]),ROOT)
    child_errors={name:distance(world_pos(updated,names[name]),old_roots[name])
                  for name in TAIL[1:]}
    need(center_error<3e-6 and max(child_errors.values())<3e-6,
         'BONE_REBASE_CHANGED_REST_WORLD_POSITIONS')
    appended=bytearray(binary)
    ibm_id=base.emit_accessor(doc,appended,
             [v2.matrix_to_glb_mat4(mat) for mat in new_ibms],5126,'MAT4')
    doc['skins'][0]['inverseBindMatrices']=ibm_id
    need(sha(bytes(appended[:len(binary)]))==sha(binary),'ORIGINAL_BUFFER_PREFIX_REWRITTEN')
    # The old clip straightened a different first segment. Recompute four
    # joint keys against the corrected world rest positions. No change to
    # existing sway or neck clips. Stop/hold/return timing remains 14 s.
    target=-8.0
    rest_angles=[euler_segment_angle(a,b) for a,b in zip(desired,desired[1:])]
    absolutes=[target-x for x in rest_angles]
    corrections=[absolutes[0],absolutes[1]-absolutes[0],
                 absolutes[2]-absolutes[1],8.0]
    need(max(abs(x) for x in corrections)<45,'ROOT_CORRECTION_TOO_LARGE')
    name_to_node={name:names[name] for name in TAIL}
    axes={name:v4.local_axis_for_world_x(updated[names[name]]) for name in TAIL}
    old_pose=step_frames(old_doc,old_binary,base,2)
    slow=doc['animations'][2]
    times=base.accessor(doc,appended,slow['samplers'][0]['input'])
    need(len(times)==len(v4.SAMPLE_TIMES)==57 and
         max(abs(t[0]-expected) for t,expected in zip(times,v4.SAMPLE_TIMES))<1e-6,
         'SOURCE_SLOW_CLIP_TIMELINE_CHANGED')
    keys={}
    for i,name in enumerate(TAIL):
        nodeid=names[name]
        q0=base.node_rotation(doc['nodes'][nodeid])
        rotation=[]
        for t in v4.SAMPLE_TIMES:
            amount=corrections[i]*v4.slow_progress(t,i)
            q=base.qmul(q0,base.axisq(axes[name],amount))
            qmag=math.sqrt(sum(x*x for x in q))
            rotation.append(tuple(x/qmag for x in q))
        need(max(abs(a-b) for a,b in zip(rotation[0],rotation[-1]))<1e-6,
             'CORRECTED_CLIP_NOT_LOOPED')
        keys[nodeid]=rotation
    target_nodes=set()
    for channel in slow['channels']:
        nodeid=channel['target']['node']
        need(nodeid in keys and channel['target']['path']=='rotation',
             'UNAUTHORIZED_SLOW_CLIP_TARGET')
        target_nodes.add(nodeid)
        slot=slow['samplers'][channel['sampler']]
        need(slot.get('interpolation')=='LINEAR','UNEXPECTED_KEY_INTERPOLATION')
        slot['output']=base.emit_accessor(doc,appended,keys[nodeid],5126,'VEC4')
    need(len(target_nodes)==4,'FOUR_ROOT_TO_TIP_ROTATION_CHANNELS_REQUIRED')
    slow.setdefault('extras',{})['attachmentRootPivot']={
        'world':list(ROOT),'priorMisplacedWorld':list(OLD_ROOT),
        'method':'source-mesh body/tail intersection arc geometric estimate',
        'humanVerdict':'PENDING',
        'rootLockedWorldPosition':True,
        'allOtherRestPivotsPreserved':True
    }
    doc['asset'].setdefault('extras',{})['replTailRootCorrectionV052']={
        'oldRoot':list(OLD_ROOT),'newRoot':list(ROOT),
        'originalManeWeights':'PRESERVED','originalTailWeights':'PRESERVED',
        'hairGeometry':'UNMODIFIED','clips':'neck+sway locked, straighten FK corrected',
        'version':'0.5.2','ownerAcceptance':'PENDING'
    }
    # Structure-level regression checks: unchanged legacy data and old binary.
    need(json.dumps(doc['animations'][:2],sort_keys=True)==old_clips,
         'PREVIOUS_TWO_CLIPS_CHANGED')
    need(list(doc['skins'][0]['joints'])==old_skin_joints,
         'JOINT_INDEX_MAPPING_CHANGED')
    need(all(json.dumps(doc[name],sort_keys=True)==value
             for name,value in locked.items()),'GEOMETRY_MATERIAL_OR_TEXTURE_CHANGED')
    need(all(json.dumps(doc['nodes'][i],sort_keys=True)==value
             for i,value in locked_other_nodes.items()),
         'MANE_OR_BODY_OR_OTHER_SKELETON_NODE_CHANGED')
    need(all(new_ibms[i]==orig_ibms[i]
             for i in range(len(new_ibms)) if i not in
             {mapping[n] for n in TAIL}),
         'BODY_OR_MANE_INVERSE_BIND_MATRIX_CHANGED')
    base_original_expected=base.EXPECTED_JOINTS
    try:
        base.EXPECTED_JOINTS=50
        oldrest=base.skin_matrices(old_doc,old_binary,before)
        newrest=base.skin_matrices(doc,appended,updated)
        restdiff=max(abs(a-b) for a,b in zip(oldrest,newrest) for a,b in zip(a,b))
        need(restdiff<2e-6,'SKINNING_REST_POSE_PARITY_FAILED')
        hair=doc['meshes'][1]['primitives'][0]
        hairpos=base.accessor(doc,appended,hair['attributes']['POSITION'])
        hairj=base.accessor(doc,appended,hair['attributes']['JOINTS_0'])
        hairw=base.accessor(doc,appended,hair['attributes']['WEIGHTS_0'])
        narrow,broad,rootband_center=measured_root_indices(hairpos)
        body=doc['meshes'][0]['primitives'][0]
        bodypos=base.accessor(doc,appended,body['attributes']['POSITION'])
        bodyj=base.accessor(doc,appended,body['attributes']['JOINTS_0'])
        bodyw=base.accessor(doc,appended,body['attributes']['WEIGHTS_0'])
        need(len(bodypos)==6082 and len(hairpos)==1819,'SOURCE_VERTEX_COUNTS_CHANGED')
        hooves=[i for i,p in enumerate(bodypos) if p[1]<.12]
        mane=[i for i,p in enumerate(hairpos) if p[2]>=-.65]
        tail=[i for i,p in enumerate(hairpos) if p[2]<-.65]
        bodytest=list(range(0,len(bodypos),11))
        need(len(hooves)>50 and len(mane)>600 and len(tail)>900,
             'SKIN_REGION_LAYOUT_CHANGED')
        body_rest=subset_deform(base,bodypos,bodyj,bodyw,newrest,hooves)
        body_samples=subset_deform(base,bodypos,bodyj,bodyw,newrest,bodytest)
        mane_rest=subset_deform(base,hairpos,hairj,hairw,newrest,mane)
        tail_rest=subset_deform(base,hairpos,hairj,hairw,newrest,tail)
        broad_rest=subset_deform(base,hairpos,hairj,hairw,newrest,broad)
        narrow_rest=subset_deform(base,hairpos,hairj,hairw,newrest,narrow)
        old_broad_rest=subset_deform(base,hairpos,hairj,hairw,oldrest,broad)
        old_narrow_rest=subset_deform(base,hairpos,hairj,hairw,oldrest,narrow)
        max_hoof=max_body=max_mane=max_tail=0.0
        max_broad_drift=max_narrow_drift=0.0
        peak=None
        for frame,t in enumerate(v4.SAMPLE_TIMES):
            new_pose={k:rot[frame] for k,rot in keys.items()}
            old_phase={k:rot[frame] for k,rot in old_pose.items()}
            mw=base.world_matrices(doc,new_pose)
            mat=base.skin_matrices(doc,appended,mw)
            for points,weights,jids,ids,baseline,tag in [
                (bodypos,bodyw,bodyj,hooves,body_rest,'hoof'),
                (bodypos,bodyw,bodyj,bodytest,body_samples,'body'),
                (hairpos,hairw,hairj,mane,mane_rest,'mane'),
                (hairpos,hairw,hairj,tail,tail_rest,'tail')]:
                latest=subset_deform(base,points,jids,weights,mat,ids)
                d=max(distance(x,y) for x,y in zip(latest,baseline))
                if tag=='hoof':max_hoof=max(max_hoof,d)
                elif tag=='body':max_body=max(max_body,d)
                elif tag=='mane':max_mane=max(max_mane,d)
                else:max_tail=max(max_tail,d)
            broad_points=subset_deform(base,hairpos,hairj,hairw,mat,broad)
            narrow_points=subset_deform(base,hairpos,hairj,hairw,mat,narrow)
            max_broad_drift=max(max_broad_drift,max(distance(x,y) for x,y in zip(broad_points,broad_rest)))
            max_narrow_drift=max(max_narrow_drift,max(distance(x,y) for x,y in zip(narrow_points,narrow_rest)))
            if abs(t-8.0)<1e-7:
                old_m=base.skin_matrices(old_doc,old_binary,
                    base.world_matrices(old_doc,old_phase))
                prev_broad=subset_deform(base,hairpos,hairj,hairw,old_m,broad)
                def average_displacement(points,reference):
                    return tuple(sum(p[axis]-q[axis] for p,q in zip(points,reference))/len(points)
                                 for axis in range(3))
                prev_broad_delta=average_displacement(prev_broad,old_broad_rest)
                new_broad_delta=average_displacement(broad_points,broad_rest)
                prev_narrow=subset_deform(base,hairpos,hairj,hairw,old_m,narrow)
                new_narrow_delta=average_displacement(narrow_points,narrow_rest)
                prev_narrow_delta=average_displacement(prev_narrow,old_narrow_rest)
                pivots=[world_pos(mw,names[n]) for n in TAIL]
                segments=[euler_segment_angle(a,b) for a,b in zip(pivots,pivots[1:])]
                peak={
                    'time':t,
                    'old_broad_root_displacement':prev_broad_delta,
                    'new_broad_root_displacement':new_broad_delta,
                    'old_narrow_ring_displacement':prev_narrow_delta,
                    'new_narrow_ring_displacement':new_narrow_delta,
                    'peak_segment_angles_degrees':segments,
                    'narrow_ring_max_motion':max(distance(x,y) for x,y in zip(narrow_points,narrow_rest)),
                    'root_world_at_peak':pivots[0],
                }
        need(max_body<1e-6 and max_hoof<1e-6 and max_mane<1e-6,
             'BODY_HOOF_OR_ACCEPTED_MANE_MOVED')
        need(.20<max_tail<.85,'STRAIGHTEN_INVISIBLE_OR_EXPLOSIVE')
        need(peak is not None and max(abs(x-target) for x in peak['peak_segment_angles_degrees'])<.15,
             'FULL_EXTENSION_NOT_STRAIGHT')
        need(distance(peak['root_world_at_peak'],ROOT)<3e-6,
             'ROOT_WORLD_PIVOT_MIGRATES_DURING_ANIMATION')
        need(peak['old_broad_root_displacement'][2]>.055,
             'PREVIOUS_ROOT_INTRUSION_NOT_REPRODUCED')
        need(abs(peak['new_broad_root_displacement'][2])<.016,
             'ROOT_STILL_PULLED_BACK_INTO_BODY')
        need(abs(peak['new_broad_root_displacement'][2])<.25*abs(peak['old_broad_root_displacement'][2]),
             'ROOT_INTRUSION_NOT_SUBSTANTIALLY_REDUCED')
        need(peak['narrow_ring_max_motion']<.03,
             'MEASURED_NEAR_SOCKET_SURFACE_TEAR_OR_DRIFT')
        need(max_narrow_drift<.04,'MEASURED_SOCKET_MOVED_EXCESSIVELY')
        need(max_broad_drift<.09,'BROAD_TAIL_ROOT_MOVED_EXCESSIVELY')
        report={
          'campaign':'REPL_TAIL_ROOT_PIVOT_ANCHOR','version':'0.5.2',
          'input_sha256':SOURCE_SHA,
          'old_root_world':list(OLD_ROOT),'new_root_world':list(ROOT),
          'pivot_source':'measured true body/tail surface intersection arc, not mesh bounds',
          'approximate_geometric_pivot_not_a_user_extracted_gizmo_json':True,
          'root_cross_section_narrow_vertices':len(narrow),
          'root_cross_section_broad_vertices':len(broad),
          'root_cross_section_center':list(rootband_center),
          'root_center_error':center_error,
          'child_rest_position_errors':child_errors,
          'rest_skin_matrix_max_diff':restdiff,
          'max_hoof_drift':max_hoof,
          'max_body_drift':max_body,
          'max_mane_drift':max_mane,
          'max_tail_motion':max_tail,
          'max_broad_root_drift':max_broad_drift,
          'max_narrow_ring_drift':max_narrow_drift,
          'peak':peak,
          'bone_count':50,
          'tail_bones':list(TAIL),
          'animations':[x['name'] for x in doc['animations']],
          'slow_motion_seconds':14,
          'owner_visual_verdict':'PENDING',
          'old_mane_and_sway_clips':'PRESERVED',
          'body_geometry_and_materials':'UNMODIFIED',
          'model_delivery':'SAME_CANONICAL_GLB_ONLY'
        }
    finally:
        base.EXPECTED_JOINTS=base_original_expected
    # Retain original glTF metadata, append extra only and never touch images.
    result=base.glb_encode(doc,bytes(appended))
    doc_after,_=glb_chunks(result)
    need(len(doc_after['nodes'])==53 and len(doc_after['skins'][0]['joints'])==50,
         'FINAL_GLB_SKIN_STRUCTURE_INVALID')
    need(len(result)<25_000_000,'DERIVED_GLB_UNEXPECTEDLY_LARGE')
    return result,report,make_viewer(result,v4,gizmo_js,report)

def make_viewer(result,v4,gizmo_js,report):
    import base64
    # The published HTML embeds the new CANONICAL bytes for full textured
    # triangles; the old gizmo script is adapted in-memory, never mutated in Git.
    script=gizmo_js
    replacements={
      'const chosen = new THREE.Vector3(0,1.05,-0.93); // preserved v0.3 root pivot':
      'const chosen = new THREE.Vector3(0,1.204,-0.889); // v0.5.2 measured root',
      'const arcEstimate = new THREE.Vector3(0.002,1.204,-0.889); // not owner-approved':
      'const arcEstimate = new THREE.Vector3(0,1.05,-0.93); // displaced v0.5.1 root',
      'existing.position.copy(chosen);':'existing.position.copy(arcEstimate);',
      "status.textContent='Intersection ARC estimate loaded for comparison; it is not a certified joint center.';":
      "status.textContent='Old v0.5.1 misplaced root loaded for comparison; do not use for the attachment.';",
      'priorV030Root:[chosen.x,chosen.y,chosen.z],':
      'priorV030Root:[arcEstimate.x,arcEstimate.y,arcEstimate.z],',
      'openArcEstimate:[arcEstimate.x,arcEstimate.y,arcEstimate.z],':
      'openArcEstimate:[chosen.x,chosen.y,chosen.z],',
      "inputGLBSha256:originalSourceSha,":
      'inputGLBSha256:originalSourceSha,',
    }
    for old,new in replacements.items():
        need(old in script,'GIZMO_PATCH_ANCHOR_MISSING:'+old[:40])
        script=script.replace(old,new)
    old='const originalSourceSha = \'d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f\';'
    need(old in script,'GIZMO_OLD_SOURCE_HASH_NOT_FOUND')
    script=script.replace(old,"const originalSourceSha = '"+sha(result)+"';")
    html=v4.HTML_TEMPLATE
    # Preserve textual provenance: v0.5.1 pivot is superseded, not accepted.
    html=html.replace('Repl v0.4 · Tail straighten + optional pivot gizmo',
                      'Repl v0.5.2 · Corrected tail-root socket + optional gizmo')
    html=html.replace('Repl · Four-bone slow tail straightening',
                      'Repl · Fixed tail-root attachment with 14-second slow straighten')
    html=html.replace('The original mane, tail pivots, skin weights, textures and body are preserved.',
                      'The mane, tail SKIN WEIGHTS, original materials and body are preserved. The tail ROOT PIVOT was corrected to the measured rump attachment; the other three tail rest pivots remain fixed.')
    html=html.replace('Orange = v0.3 root.',
                      'Orange = misplaced v0.5.1 root; cyan = corrected v0.5.2 root.')
    html=html.replace('Current v0.3 root','Corrected v0.5.2 root')
    html=html.replace('Open-arc estimate (uncertain)','Previous misplaced v0.5.1 root')
    html=html.replace('The new 14-second motion unfurls the tail gradually, holds, then returns.',
                      'The repaired 14-second motion unfurls the four-bone tail from its actual rump socket, holds at roughly -8 degrees, then returns.')
    need('__GIZMO_MODULE__' in html and '__EMBEDDED_GLB_BASE64__' in html,
         'MISSING_VIEWER_HTML_PLACEHOLDER')
    return html.replace('__GIZMO_MODULE__',script).replace(
             '__EMBEDDED_GLB_BASE64__',base64.b64encode(result).decode('ascii'))
