#!/usr/bin/env python3
"""Patch an immutable copy of published v0.1.18, never the source or model."""
import pathlib,sys
src=pathlib.Path(sys.argv[1]); dest=pathlib.Path(sys.argv[2]); file=dest/'viewer.mjs';s=file.read_text()
def once(old,new):
 global s
 count=s.count(old)
 if count!=1:raise RuntimeError(f'V019_PINNED_ANCHOR_COUNT_{count}_'+old[:110])
 s=s.replace(old,new,1)
assert 'OrbitControls' in s and 'kneeFromTarget' in s
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
assert 'distalHeading(side,footFit,pelvisProfile)' in s
assert 'new THREE.AnimationMixer(actor)' not in s
once('/* v0.1.18. ONE moving Walking_Woman.', '/* v0.1.19. ONE moving Walking_Woman.')
once("import {kneeFromTarget} from './ik-core.mjs';", "import {kneeFromTarget} from './ik-core.mjs';\nimport {sourceKneePlane} from './source-knee-plane.mjs';")
once('let maxDistalKneeDelta=0,maxKneeFlexDelta=0,unstyledWitnessCache=null;',
'''let maxDistalKneeDelta=0,maxKneeFlexDelta=0,unstyledWitnessCache=null;
// Source knee alignment is separate from foot styling and world ankle pinning.
let priorWorldKnee={left:null,right:null},minSignedKneeCenterline=Infinity,
    maxKneeSourcePositionDelta=0,maxKneeWorldStep=0,kneeCenterlineCorrections=0;''')
# Do not update foot yaw in either the primary IK or the preview.
once('const K=V(...kneeFromTarget(H.toArray(),desiredAnkle.toArray(),c.upperLength,c.lowerLength,rotateY(pole,yaw)));',
'''// IMPORTANT: the old knee pole produced centerline violations whenever the
  // planted foot constrained the ankle. Drive the pole from the original
  // source KNEE itself, then keep that knee on its anatomical side.
  const hipCenterX=(wpos(legs.left.up).x+wpos(legs.right.up).x)*.5;
  const solved=sourceKneePlane(H.toArray(),desiredAnkle.toArray(),t.source.hip,t.source.knee,
   c.upperLength,c.lowerLength,side,hipCenterX,priorWorldKnee[side],1/120,.018);
  const K=V(...solved.knee);
  minSignedKneeCenterline=Math.min(minSignedKneeCenterline,solved.sideClearance);
  maxKneeSourcePositionDelta=Math.max(maxKneeSourcePositionDelta,solved.sourceKneeDisplacement);
  if(solved.centerlineCorrected)kneeCenterlineCorrections++;''')
# Save last knee only once, after all IK iterations and distal foot heading.
once('maxDistalKneeDelta=Math.max(maxDistalKneeDelta,kneeChanged);',
'''maxDistalKneeDelta=Math.max(maxDistalKneeDelta,kneeChanged);
 const currentKnee=wpos(c.knee),hipCenterX=(wpos(legs.left.up).x+wpos(legs.right.up).x)*.5;
 const signedKnee=(side==='left'?1:-1)*(currentKnee.x-hipCenterX);
 if(signedKnee<.0179)throw Error('REAL_KNEE_CROSSED_PELVIS_CENTERLINE_'+side+'_'+signedKnee.toFixed(6));
 if(priorWorldKnee[side])maxKneeWorldStep=Math.max(maxKneeWorldStep,currentKnee.distanceTo(V(...priorWorldKnee[side])));
 priorWorldKnee[side]=currentKnee.toArray();''')
once('function clearStats(){maxDistalKneeDelta=0;maxKneeFlexDelta=0;',
'''function clearStats(){priorWorldKnee={left:null,right:null};minSignedKneeCenterline=Infinity;
 maxKneeSourcePositionDelta=0;maxKneeWorldStep=0;kneeCenterlineCorrections=0;
 maxDistalKneeDelta=0;maxKneeFlexDelta=0;''')
once('FOOT_YAW_TO_KNEE_IK_COUPLING ${maxDistalKneeDelta.toFixed(8)} u · max knee vs source flexion ${maxKneeFlexDelta.toFixed(2)}°',
'KNEE_CENTERLINE_CLEARANCE ${Number.isFinite(minSignedKneeCenterline)?minSignedKneeCenterline.toFixed(4):"pending"} u · centerline corrections ${kneeCenterlineCorrections} · max knee step ${maxKneeWorldStep.toFixed(4)} u · knee source delta ${maxKneeSourcePositionDelta.toFixed(4)} u\\nFOOT_YAW_TO_KNEE_IK_COUPLING ${maxDistalKneeDelta.toFixed(8)} u · max knee vs source flexion ${maxKneeFlexDelta.toFixed(2)}°')
# A crossing is a HARD physical failure; no PASS when the style guard is violated.
once('maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&maxKneeFlexDelta<6;',
'maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&maxKneeFlexDelta<6&&minSignedKneeCenterline>=.0179;')
once('kneeIKDecoupledFromFootYaw:true,maxDistalKneeDelta,maxKneeFlexDelta,observations:samples};',
'''kneeIKDecoupledFromFootYaw:true,maxDistalKneeDelta,maxKneeFlexDelta,
    minSignedKneeCenterline,maxKneeSourcePositionDelta,maxKneeWorldStep,
    kneeCenterlineCorrections,kneeSourceAuthority:'60-frame Walking_Woman real knee witnesses',observations:samples};''')
s=s.replace('v0.1.18','v0.1.19').replace('V0.1.18','V0.1.19')
assert 'sourceKneePlane(' in s and s.count('sourceKneePlane(')==1
assert 'distalHeading(side,footFit,pelvisProfile)' in s
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
file.write_text(s.rstrip()+'\n')
for name in ('index.html','review-server.py'):
 p=dest/name
 t=p.read_text().replace('v0.1.18','v0.1.19').replace('V0.1.18','V0.1.19').replace('v0.1.18-knee-independent-right-foot','v0.1.19-source-knee-plane')
 p.write_text(t.rstrip()+'\n')
# Original 0.1.18 heading, foot-gait, root and speed modules are byte-identical.
for f in dest.rglob('*'):
 if f.is_file() and f.suffix in ('.mjs','.py','.json','.md','.html','.sh'):
  f.write_bytes(f.read_bytes().rstrip(b'\r\n')+b'\n')
print('V019_SOURCE_KNEE_TARGET_CENTERLINE_GUARD_PATCH_PASS; FOOT_HEADING_UNCHANGED')
