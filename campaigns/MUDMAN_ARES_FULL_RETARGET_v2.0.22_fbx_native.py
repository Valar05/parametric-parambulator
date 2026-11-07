#!/usr/bin/env python3
"""Blender 5 native FBX import, replacing legacy import_scene.fbx (files RNA bug).
Called on an isolated Blender 5 scene. Import target geometry/rig only; Ares
source Action slots are retained as the sole retarget animation authority.
"""
from __future__ import annotations
import pathlib

def import_mudman_fbx(bpy,source):
 source=pathlib.Path(source)
 if not source.is_file() or source.suffix.lower()!='.fbx':
  raise RuntimeError('NATIVE_FBX_INPUT_MISSING_'+str(source))
 before=set(bpy.data.objects)
 try:
  op=bpy.ops.wm.fbx_import
  properties={p.identifier for p in op.get_rna_type().properties}
 except (RuntimeError,AttributeError,TypeError) as err:
  raise RuntimeError('BLENDER5_NATIVE_WM_FBX_IMPORT_UNAVAILABLE_'+str(err)[:350]) from err
 if 'filepath' not in properties or 'use_anim' not in properties:
  raise RuntimeError('BLENDER5_NATIVE_FBX_IMPORT_REQUIRED_PROPERTIES_MISSING_'+repr(sorted(properties)))
 kwargs={'filepath':str(source.resolve()),'use_anim':False}
 try:
  answer=op(**kwargs)
 except Exception as err:
  raise RuntimeError('BLENDER5_NATIVE_FBX_IMPORT_FAILED_'+str(err)[:550]) from err
 if answer!={'FINISHED'}:
  raise RuntimeError('BLENDER5_NATIVE_FBX_IMPORT_NOT_FINISHED_'+repr(answer))
 added=[obj for obj in bpy.data.objects if obj not in before]
 if not any(o.type=='ARMATURE' for o in added) or not any(o.type=='MESH' for o in added):
  raise RuntimeError('NATIVE_FBX_RETURNED_WITHOUT_ARMATURE_AND_MESH_'+repr([(o.name,o.type) for o in added]))
 return {'operator':'bpy.ops.wm.fbx_import','args':kwargs,'result':sorted(answer),
         'newArmatures':[o.name for o in added if o.type=='ARMATURE'],
         'newMeshes':[o.name for o in added if o.type=='MESH'],
         'animationImportedFromTarget':False}
