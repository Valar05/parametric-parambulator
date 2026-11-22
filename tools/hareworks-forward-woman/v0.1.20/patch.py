#!/usr/bin/env python3
"""v0.1.20 restore the pure v0.1.9 knee pole and source shape. NEVER edit older versions.
Start from a COPY of pinned, published v0.1.19. No binary/model writes.
"""
import pathlib,sys
source,dest=map(pathlib.Path,sys.argv[1:]);p=dest/'viewer.mjs';s=p.read_text()
def once(old,new):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError('V020_PATCH_ANCHOR_COUNT_'+str(n)+'_'+old[:100])
 s=s.replace(old,new,1)
def region(start,end,new):
 global s
 if s.count(start)!=1 or s.count(end)!=1:raise RuntimeError('V020_REGION_NOT_UNIQUE')
 i=s.index(start);j=s.index(end,i)
 s=s[:i]+new+s[j:]
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
assert 'function runwayFootQ(' in s and 'OrbitControls' in s
once('/* v0.1.19. ONE moving Walking_Woman.', '/* v0.1.20. ONE moving Walking_Woman.')
once("import {sourceKneePlane} from './source-knee-plane.mjs';",
    "import {chooseSourceKnee,stableForwardPole} from './source-knee-governor.mjs';")
once('let priorWorldKnee={left:null,right:null},minSignedKneeCenterline=Infinity,',
'''let priorWorldKnee={left:null,right:null},minSignedKneeCenterline=Infinity,''') if False else None
once('    maxKneeSourcePositionDelta=0,maxKneeWorldStep=0,kneeCenterlineCorrections=0;',
    '''    maxKneeSourcePositionDelta=0,maxKneeWorldStep=0,kneeCenterlineCorrections=0;
let maxAnkleContactConflict=0,sourceKneeBaselineMismatches=0;''')
# The 0.1.19 stateful bend-plane, its arbitrary angular speed limit and side
# clamp are rejected. This new solver is an ORIGINAL source-pole solve plus
# one bounded contact target choice. No skinned-witness iterative backreaction.
region('function solveLeg(side,t){','function physicsStep(dt){', '''function solveLeg(side,t){
 const c=legs[side],desiredQ=measuredFootQ(t.source),requested=V(...t.ankleTarget);
 // Start every step from the original v0.1.9 source phase, not the previous
 // frame's knee quaternion, contact error, or a history-dependent pole.
 for(const b of c.chain)copyLocal(b,rest[b.name]);actor.updateMatrixWorld(true);
 const H=wpos(c.up),K0=wpos(c.knee);
 const yaw=independentPose(pelvisProfile,phase*clipDuration).pelvisYaw;
 // Stable source-calibrated pole, fixed relative to model heading. No X sway.
 const pole=stableForwardPole(side,yaw);
 const hipCenterX=(wpos(legs.left.up).x+wpos(legs.right.up).x)*.5;
 const chosen=chooseSourceKnee({hip:H.toArray(),sourceHip:t.source.hip,
   sourceKnee:t.source.knee,sourceAnkle:t.source.ankle,
   contactAnkle:requested.toArray(),pole,upperLength:c.upperLength,
   lowerLength:c.lowerLength,side,centerX:hipCenterX,
   maxKneeDeviation:.025,minSideClearance:.012});
 // Keep the same ORIGINAL v0.1.9 two-link solve. Shoe style remains distal.
 const A=V(...chosen.ankle),K=V(...chosen.knee);
 turnToward(c.up,K0,K);actor.updateMatrixWorld(true);
 turnToward(c.knee,wpos(c.foot),A);actor.updateMatrixWorld(true);
 setWorldQ(c.foot,desiredQ);actor.updateMatrixWorld(true);
 const kneeBefore=wpos(c.knee),hipBefore=wpos(c.up),ankleBefore=wpos(c.foot);
 const upperQ=c.up.quaternion.clone(),shinQ=c.knee.quaternion.clone();
 // Keep witness caching unstyled; foot-yaw and knee pose are independent.
 if(!unstyledWitnessCache)unstyledWitnessCache={};
 unstyledWitnessCache[side]=Object.fromEntries(['ankle','heel','sole','toe'].map(k=>[k,witnessWorld(c,k).toArray()]));
 // Exact approved v0.1.18 foot heading logic, unchanged.
 const footFit=independentPose(pelvisProfile,phase*clipDuration).feet[side];
 const kneeToFoot=clamp(kneeBefore.x-ankleBefore.x,-.16,.16);
 const stylizedToe=[footFit.toeVector[0]+.20*kneeToFoot,footFit.toeVector[1],footFit.toeVector[2]];
 try{
  const original=wq(c.foot),fitted=runwayFootQ(c,stylizedToe,distalHeading(side,footFit,pelvisProfile));
  const styleBlend=t.planted?(chosen.unfulfilledContactDelta<.008?.35:.08):.52;
  setWorldQ(c.foot,original.slerp(fitted,styleBlend));actor.updateMatrixWorld(true);
 }catch(footError){
  setWorldQ(c.foot,desiredQ);previewFaults++;lastPreviewError=String(footError.message||footError);
 }
 const kneeChanged=kneeBefore.distanceTo(wpos(c.knee));
 const hipChanged=hipBefore.distanceTo(wpos(c.up));
 const ankleChanged=ankleBefore.distanceTo(wpos(c.foot));
 const kneeQuatChanged=Math.max(upperQ.angleTo(c.up.quaternion),shinQ.angleTo(c.knee.quaternion));
 if(Math.max(kneeChanged,hipChanged,ankleChanged,kneeQuatChanged)>1e-6)
  throw Error('DISTAL_FOOT_STYLE_MUTATED_KNEE_IK_'+side+'_'+kneeChanged.toExponential(2));
 maxDistalKneeDelta=Math.max(maxDistalKneeDelta,kneeChanged);
 const currentKnee=wpos(c.knee);
 const signedKnee=(side==='left'?1:-1)*(currentKnee.x-hipCenterX);
 minSignedKneeCenterline=Math.min(minSignedKneeCenterline,signedKnee);
 maxKneeSourcePositionDelta=Math.max(maxKneeSourcePositionDelta,chosen.kneeSourceError);
 maxAnkleContactConflict=Math.max(maxAnkleContactConflict,chosen.unfulfilledContactDelta);
 if(chosen.baselineMismatch)sourceKneeBaselineMismatches++;
 if(priorWorldKnee[side])maxKneeWorldStep=Math.max(maxKneeWorldStep,currentKnee.distanceTo(V(...priorWorldKnee[side])));
 priorWorldKnee[side]=currentKnee.toArray(); // evidence only, never used by solver
 const actual=witnessWorld(c,t.planted?t.pivot:'ankle'),drift=actual.distanceTo(V(...t.witnessTarget));
 const ankle=wpos(c.foot),reference=V(...t.source.ankle).add(actor.position);
 if(t.planted){const g=sourceGaits[side],u=mod1(phase-g.start)/g.duty;
  if(u>.70){const actualRelative=ankle.z-wpos(c.up).z,sourceRelative=t.source.ankle[2]-t.source.hip[2];
   maxTrailingExtensionDeficit=Math.max(maxTrailingExtensionDeficit,Math.max(0,actualRelative-sourceRelative));}
  maxAnchorHeight=Math.max(maxAnchorHeight,t.badAnchorHeight||0);
 }
 const flex=kneeFlexion(c.upperLength,c.lowerLength,wpos(c.up).toArray(),ankle.toArray());
 const referenceFlex=kneeFlexion(c.upperLength,c.lowerLength,t.source.hip,t.source.ankle);
 if(Number.isFinite(flex)&&Number.isFinite(referenceFlex))
  maxKneeFlexDelta=Math.max(maxKneeFlexDelta,Math.abs(flex-referenceFlex));
 const shapeError=ankle.distanceTo(reference);shapeSum+=shapeError*shapeError;shapeCount++;
 if(t.planted){maxDrift=Math.max(maxDrift,drift);contactCount++}else swingCount++;
 const h=['heel','sole','toe'].map(k=>witnessWorld(c,k).y);
 maxPenetration=Math.max(maxPenetration,Math.max(0,...h.map(y=>-y)));
 maxIK=Math.max(maxIK,drift);
 drawPins[side].position.copy(V(...t.witnessTarget));drawPins[side].visible=$('showContacts').checked;
 drawPins[side].material.color.setHex(t.planted?0x65f2b7:0xffb65f);
 return {planted:t.planted,pivot:t.pivot,drift,sole:witnessWorld(c,'sole').toArray(),
  ankle:ankle.toArray(),target:t.ankleTarget,anchor:t.anchor,shapeError,reach:c.upperLength+c.lowerLength,
  kneeFlexionDeg:flex,sourceKneeFlexionDeg:referenceFlex,distalKneePositionChange:kneeChanged,
  sourceKneeError:chosen.kneeSourceError,contactConflict:chosen.unfulfilledContactDelta,
  kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch};
}
''')
once('maxKneeSourcePositionDelta=0;maxKneeWorldStep=0;kneeCenterlineCorrections=0;',
     'maxKneeSourcePositionDelta=0;maxKneeWorldStep=0;kneeCenterlineCorrections=0;maxAnkleContactConflict=0;sourceKneeBaselineMismatches=0;')
once('KNEE_CENTERLINE_CLEARANCE ${Number.isFinite(minSignedKneeCenterline)?minSignedKneeCenterline.toFixed(4):"pending"} u · centerline corrections ${kneeCenterlineCorrections} · max knee step ${maxKneeWorldStep.toFixed(4)} u · knee source delta ${maxKneeSourcePositionDelta.toFixed(4)} u',
    'SOURCE_KNEE_RESTORED clearance ${Number.isFinite(minSignedKneeCenterline)?minSignedKneeCenterline.toFixed(4):"pending"} u · source knee Δ ${maxKneeSourcePositionDelta.toFixed(4)} u · maximum contact conflict ${maxAnkleContactConflict.toFixed(4)} u · max step ${maxKneeWorldStep.toFixed(4)} u')
once('maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&maxKneeFlexDelta<6&&minSignedKneeCenterline>=.0179;',
    'maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&maxKneeFlexDelta<6&&minSignedKneeCenterline>=.012&&maxKneeSourcePositionDelta<=.025&&maxAnkleContactConflict<=.025&&sourceKneeBaselineMismatches===0;')
once("kneeCenterlineCorrections,kneeSourceAuthority:'60-frame Walking_Woman real knee witnesses',observations:samples};",
    "kneeCenterlineCorrections:0,kneeSourceAuthority:'stationary character-local anterior knee poles; stateless 60-frame source shape envelope',maxAnkleContactConflict,sourceKneeBaselineMismatches,observations:samples};")
s=s.replace('v0.1.19','v0.1.20').replace('V0.1.19','V0.1.20')
assert 'sourceKneePlane(' not in s
assert 'chooseSourceKnee(' in s and 'stableForwardPole(' in s and 'kneeFromTarget(' in s
assert 'distalHeading(side,footFit,pelvisProfile)' in s
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
p.write_text(s.rstrip()+'\n')
for name in ('index.html','review-server.py'):
 p=dest/name;t=p.read_text().replace('v0.1.19','v0.1.20').replace('V0.1.19','V0.1.20').replace('v0.1.19-source-knee-plane','v0.1.20-source-knee-recovery')
 p.write_text(t.rstrip()+'\n')
# Retire obsolete stateful solver from this NEW version only (old sources immutable).
for old in ('source-knee-plane.mjs','source-knee-plane-test.mjs'):
 f=dest/old
 if f.exists():f.unlink()
for f in dest.rglob('*'):
 if f.is_file() and f.suffix in ('.mjs','.py','.json','.md','.html','.sh'):
  f.write_bytes(f.read_bytes().rstrip(b'\r\n')+b'\n')
print('V020_FIXED_FORWARD_KNEE_POLES_PATCH_PASS approvedFootHeading=UNCHANGED kneePoleLateralSway=REMOVED')
