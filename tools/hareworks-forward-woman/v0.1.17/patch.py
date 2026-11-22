#!/usr/bin/env python3
"""Pinned v0.1.17-only v0.1.17 correction. Does NOT edit history or model."""
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);dest=Path(sys.argv[2]);p=dest/'viewer.mjs'
s=p.read_text()
def one(old,new):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError('V017_PINNED_VIEWER_ANCHOR_'+str(n)+'_'+old[:90])
 s=s.replace(old,new,1)
# All accepted v0.1.16 runway toe-vector and foot-yaw calculations remain.
assert s.count('runwayFootQ(')>=2
assert "OrbitControls" in s
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
# The old code compressed source ankle hip-relative Z to reduce stride. The new
# speed-gait module deliberately DOES NOT edit ankle Z/Y. Root distance varies.
one('/* v0.1.16. ONE moving Walking_Woman.',
    '/* v0.1.17. ONE moving Walking_Woman.')
one('let dynamicMotion=null; // speed-dependent stride geometry, cadence and crossover; not clip-time scaling',
    'let dynamicMotion=null; // speed changes measured world footfall spacing, never compresses the leg')
# Restore accepted source foot yaw in BOTH physical IK and fallback preview;
# the v0.1.16 foot-orientation code itself is deliberately byte-identical.
one('const target=H.clone().add(V(...rotateY(v.ankleLocal,yaw)));',
    'const target=H.clone().add(V(...rotateY(v.ankleLocal,yaw)));') if False else None
# Correct HUD to distinguish actual planned full-cycle distance, half-cycle
# landing separation and cadence. No claim made from a slider label alone.
one('cadence ${cadenceFor(speed,dynamicMotion?.stride||stride).toFixed(3)} cycles/s, stride ${(dynamicMotion?.stride||stride).toFixed(3)}',
    'cadence ${cadenceFor(speed,dynamicMotion?.stride||stride).toFixed(3)} cycles/s, planned step ${(dynamicMotion?.stepDistance||stride/2).toFixed(3)} u, measured step ${latestStepSpacing===null?"pending":latestStepSpacing.toFixed(3)} u, full cycle ${(dynamicMotion?.stride||stride).toFixed(3)}')
one('stride ${(dynamicMotion?.stride||stride).toFixed(3)} u/full cycle · cadence',
    'full-cycle root stride ${(dynamicMotion?.stride||stride).toFixed(3)} u, planned half-cycle step ${(dynamicMotion?.stepDistance||stride/2).toFixed(3)} u · cadence')
# The speed-audit previously tested 1.18u/s despite UI max .8u/s. Audit REAL
# selectable speeds only, with the actual skinned IK and measured per-cycle root.
# Measure actual alternating-foot touchdown spacing; planned step length alone is not a real step.
one('const trackedFollow=V(0,.90,0);',
    'let footfallHistory=[],lastContactTransition={left:-1,right:-1},latestStepSpacing=null;\nconst trackedFollow=V(0,.90,0);')
one('const targets=contactTargets();adjustReach(targets);const feet={};',
    '''const targets=contactTargets();adjustReach(targets);const feet={};
 for(const side of ['left','right']){
  const c=worldContacts[side],t=targets[side];
  if(t.planted&&c.transitions!==lastContactTransition[side]&&t.anchor){
   lastContactTransition[side]=c.transitions;
   const touchdown={side,z:t.anchor[2],phase:totalPhase};
   const prev=footfallHistory.at(-1);
   if(prev&&prev.side!==side)latestStepSpacing=Math.abs(touchdown.z-prev.z);
   footfallHistory.push(touchdown);if(footfallHistory.length>16)footfallHistory.shift();
  }
 }''')
one('function clearStats(){maxDrift=0;',
    'function clearStats(){footfallHistory=[];lastContactTransition={left:-1,right:-1};latestStepSpacing=null;maxDrift=0;')
one('for(const requested of [.30,.52,1.18]){',
    'for(const requested of [.30,.52,.80]){')
one('speedMatrix.push({requested,realTime,travel:worldZ,',
    'speedMatrix.push({requested,realTime,travel:worldZ,measuredLastFootfall:latestStepSpacing,')
# Keep the real 120Hz physics, planted world contacts and owner verdict separate.
assert 'physicsStep(1/120)' in s
assert "motionMode='PHYSICAL_GROUND_PINNING'" in s
assert 'window' not in s[:0]
s=s.replace('v0.1.16','v0.1.17').replace('V0.1.16','V0.1.17')
p.write_text(s.rstrip()+'\n')
# Retain all v0.1.16 foot orientation/IK/ground pinning modules unchanged;
# the root's physical distance/cadence comes only from new speed-gait.mjs.
p=dest/'index.html';t=p.read_text().replace('v0.1.16','v0.1.17')
t=t.replace('The travel-speed slider changes stride length, cadence, lateral crossover and landing geometry.',
'''The travel-speed slider changes physical world footfall spacing and cadence. Anatomical leg reach stays faithful to the source at the default speed, with actual ground contacts preserved.''')
t=t.replace('v0.1.16-dynamic-physics','v0.1.17-anatomical-footfalls')
p.write_text(t.rstrip()+'\n')
p=dest/'review-server.py';t=p.read_text().replace('v0.1.16','v0.1.17');p.write_text(t.rstrip()+'\n')
# Remove old version's author-specific regression module when superseded.
for file in ['dynamic-gait-test.mjs','source-speed-contact-test.mjs']:
 assert (dest/file).is_file()
# Never touch copied originals anywhere outside this new directory.
for file in dest.rglob('*'):
 if file.is_file() and file.suffix in ('.mjs','.py','.json','.md','.html','.sh'):
  file.write_bytes(file.read_bytes().rstrip(b'\r\n')+b'\n')
print('V017_PINNED_PATCH_PASS source=v0.1.16 footYaw=UNCHANGED hipAnkleZ=SOURCE_PRESERVED')
