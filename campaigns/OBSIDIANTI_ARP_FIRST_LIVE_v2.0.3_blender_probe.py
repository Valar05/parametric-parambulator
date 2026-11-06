#!/usr/bin/env python3
"""Real purchased-ARP headless registration probe before LFS/model-heavy animation work."""
from __future__ import annotations
import argparse,json,pathlib,sys,traceback
import bpy
CAMPAIGN_DIR=str(pathlib.Path(__file__).resolve().parent)
if CAMPAIGN_DIR not in sys.path:sys.path.insert(0,CAMPAIGN_DIR)
from blender_trial import enable_arp

def main(a):
 out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 rec={'schema':'obsidianti-private-arp-operator-probe-v2.0.3','status':'START','blenderVersion':bpy.app.version_string,
      'vendorSourceExported':False}
 def save():out.write_text(json.dumps(rec,sort_keys=True,indent=2)+'\n')
 save()
 try:
  if bpy.app.version[:2] != (4,3):raise RuntimeError('REQUIRES_BLENDER_4_3_ACTUAL_'+bpy.app.version_string)
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
  rec.update({'status':'BLOCKED','errorType':type(exc).__name__,'error':str(exc)[:650]})
  save();print('ARP_HEADLESS_OPERATOR_REGISTRATION=BLOCKED '+str(exc)[:350],flush=True)
  raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--output',required=True)
 main(p.parse_args(sys.argv[sys.argv.index('--')+1:]))
