#!/usr/bin/env python3
"""Strict published v24 -> isolated v25 procedural left-stride patch. No old writes."""
import pathlib,sys
root=pathlib.Path(sys.argv[1]);dest=pathlib.Path(sys.argv[2]);p=dest/'viewer.mjs';s=p.read_text()
def once(old,new):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError('V025_PINNED_VIEWER_ANCHOR_'+str(n)+'_'+old[:125])
 s=s.replace(old,new,1)
assert 'OrbitControls' in s and 'GLTFLoader' in s and 'SourceFootContact' in s
assert 'new THREE.AnimationMixer(actor)' not in s
once('/* v0.1.24. ONE moving Walking_Woman.','/* v0.1.25. ONE moving Walking_Woman.')
once("import {distalHeading} from './foot-heading.mjs';",
"import {distalHeading} from './foot-heading.mjs';\nimport {LATERAL_FACTOR,lateralCadence,leftRootDelta,lateralSource,lateralPreviewTarget,lateralPole,lateralKnee,leftTravelPass} from './lateral-gait.mjs';")
once("const directionMode=terrainArgs.get('move')==='forward'?'forward':'backward';\nconst backward=()=>directionMode==='backward';\nconst bodyPhase=p=>sourcePhase(directionMode,p);",
"""const requestedMove=terrainArgs.get('move');
const directionMode=['forward','backward','left'].includes(requestedMove)?requestedMove:'left';
const backward=()=>directionMode==='backward';
const lateral=()=>directionMode==='left';
const bodyPhase=p=>lateral()?mod1(p):sourcePhase(directionMode,p);
const travelUnits=()=>lateral()?-worldX:signForDirection(directionMode)*worldZ;
""")
once("(backward()?'flat':'profile-ridges')","((backward()||lateral())?'flat':'profile-ridges')")
once('rootCurve=null,worldZ=0,frameTimer=','rootCurve=null,worldZ=0,worldX=0,frameTimer=')
once('worldZ+=signForDirection(directionMode)*(nextCycle-previewCycle)*dynamicMotion.stride;',
"""if(lateral())worldX-=LATERAL_FACTOR*(nextCycle-previewCycle)*dynamicMotion.stride;
 else worldZ+=signForDirection(directionMode)*(nextCycle-previewCycle)*dynamicMotion.stride;""")
once('groundLift=terrainBodyLift(groundLift,terrainAt(0,worldZ),Math.min(.25,Math.max(0,dt)));',
     'groundLift=terrainBodyLift(groundLift,terrainAt(worldX,worldZ),Math.min(.25,Math.max(0,dt)));')
once('target.fromArray(adjustAnkleForSpeed(H.toArray(),target.toArray(),side,dynamicMotion));',
     'target.fromArray(lateral()?lateralPreviewTarget(H.toArray(),target.toArray(),side):adjustAnkleForSpeed(H.toArray(),target.toArray(),side,dynamicMotion));')
once('kneeFromTarget(H.toArray(),target.toArray(),c.upperLength,c.lowerLength,rotateY(v.poleLocal,yaw))',
     'kneeFromTarget(H.toArray(),target.toArray(),c.upperLength,c.lowerLength,lateral()?lateralPole(side,yaw):rotateY(v.poleLocal,yaw))')
once(' actor.position.z=worldZ;actor.position.y=-groundOffset+groundLift;actor.updateMatrixWorld(true);}',
     ' actor.position.x=worldX;actor.position.z=worldZ;actor.position.y=-groundOffset+groundLift;actor.updateMatrixWorld(true);}')
once('out[side]=worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion});',
     'out[side]=worldContacts[side].step({phase,worldX,worldZ,totalPhase,gait:dynamicMotion});')
once(" const chosen=chooseSourceKnee({hip:H.toArray(),sourceHip:t.source.hip,",
""" const chosen=lateral()?lateralKnee({hip:H.toArray(),sourceHip:t.source.hip,
   sourceKnee:t.source.knee,contactAnkle:requested.toArray(),
   upperLength:c.upperLength,lowerLength:c.lowerLength,side,pelvisYaw:yaw,
   centerX:hipCenterX}):chooseSourceKnee({hip:H.toArray(),sourceHip:t.source.hip,""")
once(' const cadence=cadenceFor(speed,dynamicMotion.stride),newPhase=totalPhase+cadence*dt;',
     ' const cadence=lateral()?lateralCadence(speed,dynamicMotion):cadenceFor(speed,dynamicMotion.stride),newPhase=totalPhase+cadence*dt;')
once('worldZ+=backward()?backwardRootDelta(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion):rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);',
"""if(lateral())worldX+=leftRootDelta(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);
 else worldZ+=backward()?backwardRootDelta(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion):rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);""")
once('groundLift=terrainBodyLift(groundLift,terrainAt(0,worldZ),dt);',
     'groundLift=terrainBodyLift(groundLift,terrainAt(worldX,worldZ),dt);')
once('const touchdown={side,z:t.anchor[2],phase:totalPhase};',
     'const touchdown={side,z:lateral()?t.anchor[0]:t.anchor[2],phase:totalPhase};')
once('lastStats={phase,worldTravelZ:worldZ,speed,cadence,worldRootZ:actor.position.z,feet,transitions,',
     'lastStats={phase,worldTravelX:worldX,worldTravelZ:worldZ,directionAxisSignedTravel:travelUnits(),speed,cadence,worldRootX:actor.position.x,worldRootZ:actor.position.z,feet,transitions,')
once('Travel Z ${worldZ.toFixed(3)} u, phase ',
     'Travel X ${worldX.toFixed(3)} u, Z ${worldZ.toFixed(3)} u, signed axis ${travelUnits().toFixed(3)} u, phase ')
once('phase=0;totalPhase=0;worldZ=0;groundLift=terrainAt(0,0);',
     'phase=0;totalPhase=0;worldX=0;worldZ=0;groundLift=terrainAt(0,0);')
once('  transformSource:(s,gait)=>transformSourceFoot(s,side,gait||dynamicMotion)});',
     '  transformSource:(s,gait)=>lateral()?lateralSource(s,side):transformSourceFoot(s,side,gait||dynamicMotion)});')
once('  terrainAt:terrainMode===\'flat\'?null:terrainAt,reverseRocker:backward(),',
     '  terrainAt:terrainMode===\'flat\'?null:terrainAt,reverseRocker:backward(),') if False else None
once('  previewCycle=0;worldZ=0;dynamicMotion=speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE);frameBody(0);',
     '  previewCycle=0;worldX=0;worldZ=0;dynamicMotion=speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE);frameBody(0);')
once(' const startZ=worldZ;for(let i=0;i<32;i++)physicsStep(1/120);',
     '  const startTravel=travelUnits();for(let i=0;i<32;i++)physicsStep(1/120);')
once(' const travelled=worldZ-startZ;\n if(!Number.isFinite(travelled)||signForDirection(directionMode)*travelled<.04)',
     '  const travelled=travelUnits()-startTravel;\n if(!Number.isFinite(travelled)||travelled<.04)')
once(' directionMode,terrainMode,terrainStrength,bodyTerrainLift:groundLift,hipReachLimitCount,maxShinTerrainCollision,hipSolve:lastHipSolve};',
     '  lateralProceduralFootTargets:lateral(),directionRootX:worldX,terrainMode,terrainStrength,bodyTerrainLift:groundLift,hipReachLimitCount,maxShinTerrainCollision,hipSolve:lastHipSolve};')
once('if(terrainMode!==\'flat\'&&Math.abs(worldZ-terrainCenterZ)>14)',
     'if(terrainMode!==\'flat\'&&Math.abs(worldZ-terrainCenterZ)>14)') if False else None
# Live audit: X is the travel axis for left. Preserve all original negative-Z gates.
once('signForDirection(directionMode)*worldZ>speedGait(speed,stride).stride*2.70',
     'travelUnits()>(lateral()?LATERAL_FACTOR:1)*speedGait(speed,stride).stride*2.70')
once('maxTrailingExtensionDeficit<.055&&maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&maxKneeFlexDelta<6',
     '(lateral()||maxTrailingExtensionDeficit<.055)&&maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&(lateral()||maxKneeFlexDelta<6)')
once('minSignedKneeCenterline>=.012&&maxKneeSourcePositionDelta<=.025',
     'minSignedKneeCenterline>=.012&&(lateral()||maxKneeSourcePositionDelta<=.025)')
once('directionStatus:"FORWARD_AND_BACKWARD_IMPLEMENTED; SIX_OTHER_DIRECTIONS_UNIMPLEMENTED"',
     'directionStatus:"FORWARD_BACKWARD_LEFT_IMPLEMENTED; FIVE_OTHER_DIRECTIONS_UNIMPLEMENTED"')
once('surfaceAtRoot:terrainAt(0,worldZ)', 'surfaceAtRoot:terrainAt(worldX,worldZ)')
once('directionSlot:directionMode,expectedTravelSign:signForDirection(directionMode),signedWorldAdvance:worldZ',
     'directionSlot:directionMode,expectedTravelSign:backward()||lateral()?-1:1,signedWorldAdvance:lateral()?worldX:worldZ,rootWorldX:worldX,rootWorldZ:worldZ')
once('sampledFrames:n,worldTravelZ:worldZ,referenceRigWasNotDisplayed:true,',
     'sampledFrames:n,worldTravelX:worldX,worldTravelZ:worldZ,referenceRigWasNotDisplayed:true,')
once('if(i%15===0)samples.push({time:i/120,phase:m.phase,worldZ:m.worldTravelZ,',
     'if(i%15===0)samples.push({time:i/120,phase:m.phase,worldX:m.worldTravelX,worldZ:m.worldTravelZ,')
once('const expected=speedGait(requested,stride),steps=Math.ceil((1.20/expected.cadence)*120);',
     'const expected=speedGait(requested,stride),steps=Math.ceil((1.20/(lateral()?lateralCadence(requested,expected):expected.cadence))*120);')
once('speedMatrix.push({requested,realTime,travel:worldZ,measuredLastFootfall:latestStepSpacing,',
     'speedMatrix.push({requested,realTime,travelX:worldX,travelZ:worldZ,measuredLastFootfall:latestStepSpacing,')
once('rootMeanSpeed:worldZ/realTime,',
     'rootMeanSpeed:travelUnits()/realTime,')
once('signedTravelPass(directionMode,worldZ/realTime,requested,.17)',
     '(lateral()?leftTravelPass(worldX/realTime,worldZ/realTime,requested,.17):signedTravelPass(directionMode,worldZ/realTime,requested,.17))')
once('Math.abs(worldZ/realTime-requested)<.17',
     'Math.abs(travelUnits()/realTime-requested)<.17') if False else None
once('const n=Math.ceil((3/cadenceFor(speed,speedGait(speed,stride).stride))*120);',
     'const n=Math.ceil((3/(lateral()?lateralCadence(speed,speedGait(speed,stride)):cadenceFor(speed,speedGait(speed,stride).stride)))*120);')
once('nominalForwardAdvance:worldZ,generatedAnimationMixerCount:0',
     'nominalAxisTravel:travelUnits(),generatedAnimationMixerCount:0') if False else None
once("schema:'hareworks-v0.1.24-directional-two-of-eight'","schema:'hareworks-v0.1.25-directional-three-of-eight'")
once("a.download='hareworks-v0.1.24-'+directionMode+'-world-pin.json'","a.download='hareworks-v0.1.25-'+directionMode+'-world-pin.json'")
once('3 measured cycles, 120 Hz, ${directionMode} traveling root ${worldZ.toFixed(3)} u',
     '3 measured cycles, 120 Hz, ${directionMode} signed travel ${travelUnits().toFixed(3)} u')
once("$('identity').textContent=`v0.1.24 ${directionMode.toUpperCase()} DIRECTIONAL IK · TWO OF EIGHT CARDINAL SLOTS",
     "$('identity').textContent=`v0.1.25 ${directionMode.toUpperCase()} DIRECTIONAL IK · THREE OF EIGHT SLOTS")
once(" initRun();motionMode='PHYSICAL_GROUND_PINNING';playing=true;pinCamera();",
     " initRun();if(lateral())setCameraPreset('front');motionMode='PHYSICAL_GROUND_PINNING';playing=true;pinCamera();")
once("$('identity').textContent='v0.1.24 · REAL GLB '",
     "$('identity').textContent='v0.1.25 · REAL GLB '")
# Keep old physical controller fallback honest and visibly identify new direction.
once('V0.1.9 PROCEDURAL WALK PREVIEW MOVING · NOT GROUND PINNED',
     '${directionMode.toUpperCase()} PROCEDURAL WALK PREVIEW MOVING · NOT GROUND PINNED') if False else None
s=s.replace('v0.1.24','v0.1.25').replace('V0.1.24','V0.1.25')
assert "lateralSource(s,side)" in s and "lateralKnee(" in s and "leftRootDelta(" in s
assert s.count('new THREE.AnimationMixer(actor)')==0
p.write_text(s.rstrip()+'\n')
# World-X interpolation is an opt-in argument; forward/backward remain zero.
p=dest/'foot-gait.mjs';t=p.read_text()
needle='step({phase,worldZ,totalPhase,gait}){'
if t.count(needle)!=1:raise RuntimeError('V025_SOURCE_FOOT_STEP_ANCHOR')
t=t.replace(needle,'step({phase,worldX=0,worldZ,totalPhase,gait}){',1)
needle='const baseline=add(s.ankle,[0,-this.sourceGround,worldZ]);'
if t.count(needle)!=1:raise RuntimeError('V025_BASELINE_ANKLE_X_ANCHOR')
t=t.replace(needle,'const baseline=add(s.ankle,[worldX,-this.sourceGround,worldZ]);',1)
p.write_text(t.rstrip()+'\n')
# Readable three-slot direction selector with default left and no actor rotation.
p=dest/'index.html';t=p.read_text()
needle='<option value="backward">Backward (−Z)</option><option value="forward">Forward (+Z, baseline)</option>'
if t.count(needle)!=1:raise RuntimeError('V025_DIRECTION_CONTROL_ANCHOR')
t=t.replace(needle,'<option value="left">Left strafe (−X, procedural)</option><option value="backward">Backward (−Z, existing)</option><option value="forward">Forward (+Z, baseline)</option>',1)
t=t.replace('two of eight slots','three of eight slots').replace('<strong>2/8 directional slots</strong>','<strong>3/8 directional slots</strong>')
t=t.replace('Lateral and diagonal slots are not implemented.','Left is independently procedural; right and diagonals are not implemented.')
t=t.replace('Hareworks v0.1.24 | Forward + Backward Procedural IK','Hareworks v0.1.25 | Forward + Backward + Left Procedural IK')
t=t.replace('Walking_Woman · Forward / Backward Procedural IK','Walking_Woman · Three-direction Procedural IK')
t=t.replace('Backward uses reversed procedural phase, reversed world root travel and toe-first heel-last rocker.',
 'Backward uses reversed phase and root travel. Left uses distinct −X planted anchors, sideways foot trajectories, and stationary anterior knee poles while facing forward.')
t=t.replace('The model moves in world Z;','The model moves in world X for left and Z for forward/backward;')
t=t.replace('v0.1.24','v0.1.25').replace('V0.1.24','V0.1.25')
t=t.replace('v0.1.25-backward-direction-physical-ik','v0.1.25-left-procedural-world-x-ik')
p.write_text(t.rstrip()+'\n')
p=dest/'review-server.py';t=p.read_text().replace('v0.1.24','v0.1.25');p.write_text(t.rstrip()+'\n')
print('V025_LEFT_PROCEDURAL_PATCH_PASS immutable v24 sources copied; world-X targets and stateless knee IK only in v25')
