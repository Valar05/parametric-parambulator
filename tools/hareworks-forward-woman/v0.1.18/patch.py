#!/usr/bin/env python3
"""v0.1.18: pin original source knee geometry; change distal foot heading only.
Always patch a COPIED v0.1.17 viewer, never the source/model.
"""
import pathlib, sys
source=pathlib.Path(sys.argv[1]); dest=pathlib.Path(sys.argv[2]);
p=dest/'viewer.mjs';s=p.read_text()
def one(old,new):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError('V018_VIEWER_ANCHOR_EXPECTED_1_GOT_'+str(n)+' '+old[:100])
 s=s.replace(old,new,1)
def region(a,b,new):
 global s
 if s.count(a)!=1 or s.count(b)!=1:raise RuntimeError('V018_REGION_ANCHOR '+a[:80])
 i=s.index(a);j=s.index(b,i)
 s=s[:i]+new+s[j:]
assert 'OrbitControls' in s and 'function runwayFootQ(' in s
assert 'new THREE.AnimationMixer(actor)' not in s
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
one('/* v0.1.17. ONE moving Walking_Woman.', '/* v0.1.18. ONE moving Walking_Woman.')
one("import {speedGait,blendMotion,transformSourceFoot,adjustAnkleForSpeed,rootStepDistance} from './speed-gait.mjs';",
    "import {speedGait,blendMotion,transformSourceFoot,adjustAnkleForSpeed,rootStepDistance} from './speed-gait.mjs';\nimport {distalHeading} from './foot-heading.mjs';")
# Replace both foot style call sites with actual mirrored right yaw; preserve all
# source knee/hip/pole paths. Left yaw remains unmodified.
one('runwayFootQ(c,footFit.toeVector,footFit.ankleYaw)',
    "runwayFootQ(c,footFit.toeVector,distalHeading(side,footFit,pelvisProfile))")
# Replace ONLY the knee/foot solve region. The knee IK is the same original
# kneeFromTarget() and v0.1.9 pole. It NEVER reads a styled foot quaternion.
region('function solveLeg(side,t){','function physicsStep(dt){', '''function solveLeg(side,t){
 const c=legs[side],desiredQ=measuredFootQ(t.source),target=V(...t.ankleTarget);
 let desiredAnkle=target.clone(),best=Infinity;
 // Recover the v0.1.9/source knee IK. Correct sole witnesses only while the
 // shoe still carries its ORIGINAL measured source rotation. The approved
 // distal yaw styling is installed AFTER the final knee solve.
 for(let iter=0;iter<5;iter++){
  for(const b of c.chain)copyLocal(b,rest[b.name]);actor.updateMatrixWorld(true);
  // v0.1.9 did not artificially shorten extended legs. The old -.005
  // clamp bent 26 left and 23 right source poses. Keep only numerical safety.
  const H=wpos(c.up),K0=wpos(c.knee),max=c.upperLength+c.lowerLength-.00025,min=Math.abs(c.upperLength-c.lowerLength)+.00025;
  const direction=desiredAnkle.clone().sub(H);
  if(direction.length()>max||direction.length()<min){
   direction.setLength(clamp(direction.length(),min,max));desiredAnkle.copy(H).add(direction);unreachable++;
  }
  const pole=legAt(footProfile,side,phase*clipDuration).poleLocal;
  const yaw=independentPose(pelvisProfile,phase*clipDuration).pelvisYaw;
  const K=V(...kneeFromTarget(H.toArray(),desiredAnkle.toArray(),c.upperLength,c.lowerLength,rotateY(pole,yaw)));
  turnToward(c.up,K0,K);actor.updateMatrixWorld(true);
  turnToward(c.knee,wpos(c.foot),desiredAnkle);actor.updateMatrixWorld(true);
  setWorldQ(c.foot,desiredQ);actor.updateMatrixWorld(true);
  const actual=witnessWorld(c,t.planted?t.pivot:'ankle');
  const error=V(...t.witnessTarget).sub(actual);best=error.length();
  if(best<.0018)break;
  desiredAnkle.add(error.multiplyScalar(.92));
 }
 // KNEE FINAL: no toe/ankle yaw decision is allowed back into the IK loop.
 const kneeBefore=wpos(c.knee),hipBefore=wpos(c.up),ankleBefore=wpos(c.foot);
 const upperQ=c.up.quaternion.clone(),shinQ=c.knee.quaternion.clone();
 // Snapshot UNSTYLED source-orientation foot witnesses. Future touchdown
 // captures read these, never last frame's decorative foot heading.
 if(!unstyledWitnessCache)unstyledWitnessCache={};
 unstyledWitnessCache[side]=Object.fromEntries(['ankle','heel','sole','toe'].map(k=>[k,witnessWorld(c,k).toArray()]));
 const footFit=independentPose(pelvisProfile,phase*clipDuration).feet[side];
 const kneeToFoot=clamp(kneeBefore.x-ankleBefore.x,-.16,.16);
 const stylizedToe=[footFit.toeVector[0]+.20*kneeToFoot,footFit.toeVector[1],footFit.toeVector[2]];
 try{
  const original=wq(c.foot),fitted=runwayFootQ(c,stylizedToe,distalHeading(side,footFit,pelvisProfile));
  const styleBlend=t.planted?(best<.008?.35:.08):.52;
  setWorldQ(c.foot,original.slerp(fitted,styleBlend));actor.updateMatrixWorld(true);
 }catch(footError){
  setWorldQ(c.foot,desiredQ);previewFaults++;lastPreviewError=String(footError.message||footError);
 }
 // Runtime invariant: distal foot rotation CANNOT reposition the proximal
 // upper/shin joints or foot/ankle bone origin, even by 1e-6 model units.
 const kneeChanged=kneeBefore.distanceTo(wpos(c.knee));
 const hipChanged=hipBefore.distanceTo(wpos(c.up));
 const ankleChanged=ankleBefore.distanceTo(wpos(c.foot));
 const kneeQuatChanged=Math.max(upperQ.angleTo(c.up.quaternion),shinQ.angleTo(c.knee.quaternion));
 if(Math.max(kneeChanged,hipChanged,ankleChanged,kneeQuatChanged)>1e-6)
  throw Error('DISTAL_FOOT_STYLE_MUTATED_KNEE_IK_'+side+'_'+kneeChanged.toExponential(2));
 maxDistalKneeDelta=Math.max(maxDistalKneeDelta,kneeChanged);
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
  kneeFlexionDeg:flex,sourceKneeFlexionDeg:referenceFlex,distalKneePositionChange:kneeChanged};
}
''')
# Insert counters: separate distal style invariance from geometric constraints
one('let dynamicMotion=null; // speed changes measured world footfall spacing, never compresses the leg',
    'let dynamicMotion=null; // v0.1.18 anatomical pre-IK targets never depend on foot yaw\nlet maxDistalKneeDelta=0,maxKneeFlexDelta=0,unstyledWitnessCache=null;')
one('witnessCache=measuredWitnesses();\n dynamicMotion=blendMotion',
    'witnessCache=unstyledWitnessCache?{...unstyledWitnessCache}:measuredWitnesses();\n dynamicMotion=blendMotion')
one('clearStats();frameBody(0);witnessCache=measuredWitnesses();const next={};',
    'clearStats();frameBody(0);unstyledWitnessCache=null;witnessCache=measuredWitnesses();const next={};')
one('function clearStats(){footfallHistory=[];',
    'function clearStats(){maxDistalKneeDelta=0;maxKneeFlexDelta=0;footfallHistory=[];')
one('ANIMATION MIXER ON VISIBLE ACTOR: ZERO · source joints NOT replayed',
    'FOOT_YAW_TO_KNEE_IK_COUPLING ${maxDistalKneeDelta.toFixed(8)} u · max knee vs source flexion ${maxKneeFlexDelta.toFixed(2)}°\\nANIMATION MIXER ON VISIBLE ACTOR: ZERO · source joints NOT replayed')
one('maxAnchorHeight<.026;',
    'maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&maxKneeFlexDelta<6;')
one('ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,observations:samples};',
    'ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,\n    kneeIKDecoupledFromFootYaw:true,maxDistalKneeDelta,maxKneeFlexDelta,observations:samples};')
# Keep v0.1.17 source leg trajectory. Change only distal heading / orientation,
# with no hidden ankle position changes from an artificially induced crossover.
assert 'const K=V(...kneeFromTarget(' in s
assert 'maxDistalKneeDelta' in s
assert s.count('runwayFootQ(')>=3
s=s.replace('v0.1.17','v0.1.18').replace('V0.1.17','V0.1.18')
p.write_text(s.rstrip()+'\n')
p=dest/'speed-gait.mjs'; t=p.read_text()
needle='return [ankle[0]+sign*motion.crossover*(.28+.72*leading),ankle[1],ankle[2]];'
if t.count(needle)!=1:raise RuntimeError('V018_ANKLE_CROSSOVER_COUPLING_NOT_FOUND')
t=t.replace(needle,"return [ankle[0],ankle[1],ankle[2]]; // NO knee IK change from foot-heading style")
needle='crossover:.014+.014*lead,stanceDuty:'
if t.count(needle)!=1:raise RuntimeError('V018_CROSSOVER_METRIC_NOT_FOUND')
t=t.replace(needle,'crossover:0,stanceDuty:')
t=t.replace('v0.1.17','v0.1.18').replace('V017','V018')
p.write_text(t.rstrip()+'\n')
p=dest/'index.html';t=p.read_text().replace('v0.1.17','v0.1.18').replace('V0.1.17','V0.1.18').replace('v0.1.17-anatomical-footfalls','v0.1.18-knee-independent-right-foot')
t=t.replace('with gentle lateral runway crossover', 'with the original source knee poles and no extra ankle crossover')
p.write_text(t.rstrip()+'\n')
p=dest/'review-server.py';t=p.read_text().replace('v0.1.17','v0.1.18');p.write_text(t.rstrip()+'\n')
for file in dest.rglob('*'):
 if file.is_file() and file.suffix in ('.mjs','.py','.json','.md','.html','.sh'):
  file.write_bytes(file.read_bytes().rstrip(b'\r\n')+b'\n')
print('V018_CORRECTION_PASS: source knee IK restored, approved left foot preserved, right mirrored source-heading bias, no feedback from styled foot to knee')
