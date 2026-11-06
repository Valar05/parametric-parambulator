#!/usr/bin/env python3
"""Real purchased-ARP headless registration probe before LFS/model-heavy animation work."""
from __future__ import annotations
import argparse,json,pathlib,sys,traceback
import bpy
CAMPAIGN_DIR=str(pathlib.Path(__file__).resolve().parent)
if CAMPAIGN_DIR not in sys.path:sys.path.insert(0,CAMPAIGN_DIR)
from blender_trial import enable_arp,prep_armature_for_vendor_registration

def main(a):
 out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 rec={'schema':'obsidianti-private-arp-operator-probe-v2.0.5','status':'START','blenderVersion':bpy.app.version_string,
      'vendorSourceExported':False}
 def save():out.write_text(json.dumps(rec,sort_keys=True,indent=2)+'\n')
 save()
 try:
  if bpy.app.version[:2] != (4,3):raise RuntimeError('REQUIRES_BLENDER_4_3_ACTUAL_'+bpy.app.version_string)
  rec['registrationContext']=prep_armature_for_vendor_registration(create=True)
  # Record only structural facts about the user's private purchased version.
  # NEVER copy, embed, quote or publish its source code.
  private=pathlib.Path(a.private)
  candidates=list(private.rglob('reset_all_controllers.py'))
  rec['vendorImportBehavior']={'resetModuleCount':len(candidates)}
  if len(candidates)==1:
   code=candidates[0].read_text(errors='replace')
   rec['vendorImportBehavior'].update({'hasTopLevelControllerReset':any(
    line.strip()=='reset_all_controllers()' for line in code.splitlines()),
    'hasPoseSelectionOperator': 'bpy.ops.pose.select_all' in code})
  save()
  active=enable_arp(a.private)
  rec['activation']=active
  reg={'source_rig':hasattr(bpy.context.scene,'source_rig'),
       'target_rig':hasattr(bpy.context.scene,'target_rig'),
       'bones_map_v2':hasattr(bpy.context.scene,'bones_map_v2')}
  rec['sceneProperties']=reg
  if not all(reg.values()):raise RuntimeError('ARP_REMAP_SCENE_PROPERTIES_MISSING '+str(reg))
  rec['status']='REAL_PURCHASED_ARP_REMAP_HEADLESS_OPERATOR_REGISTRATION_PASS'
  save()
  print('ARP_HEADLESS_OPERATOR_REGISTRATION=PASS',flush=True)
 except Exception as exc:
  # Only error metadata and a traceback are persisted LOCALLY under Termux.
  # Do not copy the purchased addon package or traceback into public Git.
  frames=traceback.extract_tb(exc.__traceback__)
  rec.update({'status':'BLOCKED','errorType':type(exc).__name__,'error':str(exc)[:650],
   'stackSummary':[{'moduleFile':pathlib.Path(f.filename).name,
                    'function':f.name,'line':f.lineno}
                    for f in frames[-14:]],
   'tracebackLocal':traceback.format_exc()[-10000:]})
  save();print('ARP_HEADLESS_OPERATOR_REGISTRATION=BLOCKED '+str(exc)[:350],flush=True)
  raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--output',required=True)
 main(p.parse_args(sys.argv[sys.argv.index('--')+1:]))
