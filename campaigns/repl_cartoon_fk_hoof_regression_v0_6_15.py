#!/usr/bin/env python3
"""Fail-closed independent result-vs-measured-model guard for Repl v0.6.15.

The reference numbers were obtained by full skinning of the EXACT original
v0.6.10 bytes before publication, not by a synthetic fixture. Verify physical
numbers on the device before any Git staging, commit or push.
"""
from __future__ import annotations
import math
class Blocked(RuntimeError):pass
def need(ok,msg):
 if not ok:raise Blocked(msg)
def verify_measurements(report,plan):
 expected={
  '1_LF':(.285692,.005567),'1_RF':(.293651,.007839),
  '2_LF':(.282521,.007630),'2_RF':(.292100,.005521),
  '3_LF':(.282521,.007630),'3_RF':(.292100,.005521)}
 need(set(report['front_hoof_clearance'])==set(expected),'MEASUREMENT_STAGE_LEG_COVERAGE')
 for k,(ratio,low) in expected.items():
  actual=report['front_hoof_clearance'][k]
  need(abs(actual['verified_ratio']-ratio)<.003,'ACTUAL_PEAK_DIFFERS_FROM_REAL_SOURCE_PREDICTION:'+k)
  need(abs(actual['min_swing']-low)<.003,'ACTUAL_SWING_LOW_DIFFERS_FROM_REAL_SOURCE_PREDICTION:'+k)
  need(actual['min_swing']>.0035,'ACTUAL_SWING_SOLE_TOUCHES_GROUND:'+k)
  need(.245<=actual['verified_ratio']<=.335,'ACTUAL_PEAK_RATIO_OUTSIDE_OWNER_GOAL:'+k)
 need(report['tested_physical_frames']==1164,'REAL_MESH_FRAME_CHECK_INCOMPLETE')
 need(abs(report['max_stance_vertex_delta']-.0072682)<.003,'UNEXPECTED_STANCE_MESH_DELTA')
 need(report['max_joint_step_deg']<30,'FORELEG_ROTATION_JUMP_EXCEEDS_PRETEST')
 for k in ('2','3'):
  sag=report['loaded_shoulder_drop'][k]
  need(abs(sag['supported_side_drop_y']-.002304)<.0012,'LOADED_SHOULDER_SAG_DIFFERS_FROM_PRETEST:'+k)
  need(abs(sag['differential_y']-.001406)<.0012,'LOADED_CORNER_ROLL_DIFFERS_FROM_PRETEST:'+k)
 need(plan['version']=='0.6.15','WRONG_TRAJECTORY_VERSION')
 return {'production_model_replay':'PASS','all_three_clips':'PASS',
         'protected_stance_and_body':'PASS','front_swing_clearance':'PASS'}
