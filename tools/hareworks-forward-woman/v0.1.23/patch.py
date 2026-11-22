import pathlib,sys
source=pathlib.Path(sys.argv[1]); dest=pathlib.Path(sys.argv[2]);f=dest/'viewer.mjs';s=f.read_text()
def one(a,b):
 global s
 n=s.count(a)
 if n!=1:raise RuntimeError('V023_SOURCE_ANCHOR_COUNT_'+str(n)+'_'+a[:120])
 s=s.replace(a,b,1)
one('/* v0.1.22. ONE moving Walking_Woman.','/* v0.1.23. ONE moving Walking_Woman.')
one("import {TERRAIN_MODES,isProfileTerrain,terrainHeight,terrainNormal,terrainBodyLift,terrainGrid,longitudinalProfile} from './terrain-core.mjs';",
"import {TERRAIN_MODES,isProfileTerrain,terrainHeight,terrainNormal,terrainBodyLift,terrainGrid,longitudinalProfile} from './terrain-core.mjs';\nimport {pelvisReachCorrection,segmentTerrainPenetration} from './terrain-hip.mjs';")
one('let groundLift=0,terrainMesh=null,terrainWire=null,terrainSlice=null,terrainCenterZ=0;',
'let groundLift=0,terrainMesh=null,terrainWire=null,terrainSlice=null,terrainCenterZ=0;\nlet hipReachLimitCount=0,maxShinTerrainCollision=0,lastHipSolve=null;')
one(' const targets=contactTargets();adjustReach(targets);const feet={};',
''' const targets=contactTargets();
 // Contact anchors are sampled ONCE. Now move the pelvis within both actual
 // two-link reach envelopes. This is no longer just terrainAt(0,worldZ).
 const hips=Object.fromEntries(['left','right'].map(side=>[side,wpos(legs[side].up).toArray()]));
 const ankles=Object.fromEntries(['left','right'].map(side=>[side,targets[side].ankleTarget]));
 const lengths=Object.fromEntries(['left','right'].map(side=>[side,[legs[side].upperLength,legs[side].lowerLength]]));
 lastHipSolve=pelvisReachCorrection(hips,ankles,lengths,groundLift,terrainAt,dt);
 if(lastHipSolve.feasible){groundLift+=lastHipSolve.delta;frameBody(phase)}
 else hipReachLimitCount++;
 adjustReach(targets);const feet={};''')
one(' const terrainIntrusion=Math.max(0,...footPatches.map(p=>terrainAt(p.x,p.z)-p.y));',
''' const terrainIntrusion=Math.max(0,...footPatches.map(p=>terrainAt(p.x,p.z)-p.y));
 // Detect hillside intersections at the shin, not only the three shoe patches.
 const shinCollision=segmentTerrainPenetration(wpos(c.knee).toArray(),wpos(c.foot).toArray(),terrainAt);
 maxShinTerrainCollision=Math.max(maxShinTerrainCollision,shinCollision);''')
one('  kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch,terrainClearances,',
'  kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch,terrainClearances,shinCollision,')
one(' terrainMode,terrainStrength,bodyTerrainLift:groundLift};',
' terrainMode,terrainStrength,bodyTerrainLift:groundLift,hipReachLimitCount,maxShinTerrainCollision,hipSolve:lastHipSolve};')
one('function clearStats(){priorWorldKnee={left:null,right:null};',
'function clearStats(){hipReachLimitCount=0;maxShinTerrainCollision=0;lastHipSolve=null;priorWorldKnee={left:null,right:null};')
one('TERRAIN penetration ${maxPenetration.toFixed(5)} u',
'TERRAIN penetration ${maxPenetration.toFixed(5)} u · shin hillside intrusion ${maxShinTerrainCollision.toFixed(4)} u · hip reach limits ${hipReachLimitCount}')
one('terrainMode,terrainStrength,terrainWidthInvariant:profileMode(),',
 'terrainMode,terrainStrength,terrainHipReachSolver:true,maxShinTerrainCollision,hipReachLimitCount,terrainWidthInvariant:profileMode(),')
one('const physicalPass=worst.left<=.025&&worst.right<=.025&&',
 'const physicalPass=maxShinTerrainCollision<=.035&&hipReachLimitCount===0&&worst.left<=.025&&worst.right<=.025&&')
one("$('motionStatus').textContent='UNPINNED DYNAMIC GEOMETRY PREVIEW · target stride '+(dynamicMotion?.stride||0).toFixed(3)+' u/full cycle · no contact proof';",
"$('motionStatus').textContent='PHYSICAL TERRAIN IK UNAVAILABLE · UNPINNED PREVIEW ONLY · '+previewStage+' · '+previewFault+' · no contact proof';")
one("$('identity').textContent='v0.1.22 · ORIGINAL SKINNED 3D MODEL HASH '+SOURCE_SHA+' · STRESS PROFILE SOURCE AND CONTACT AUDIT PENDING';",
"$('identity').textContent='v0.1.23 · REAL GLB '+SOURCE_SHA+' · TERRAIN HIP + SHIN PROBE · browser physics pending';")
s=s.replace('v0.1.22','v0.1.23').replace('V0.1.22','V0.1.23')
assert 'chooseSourceKnee' in s and 'distalHeading(side,footFit,pelvisProfile)' in s
f.write_text(s.rstrip()+'\n')
p=dest/'index.html';h=p.read_text().replace('v0.1.22','v0.1.23').replace('V0.1.22','V0.1.23');h=h.replace('Physically sampled', 'Physically sampled')
h=h.replace('The travel-speed slider changes physical world footfall spacing and cadence.', 'The travel-speed slider changes physical world footfall spacing and cadence. On steep terrain, the pelvis solves against both leg-reach limits and displays shin obstruction warnings; unpinned preview is NOT a ground test.')
p.write_text(h.rstrip()+'\n')
p=dest/'review-server.py';p.write_text(p.read_text().replace('v0.1.22','v0.1.23').replace('V0.1.22','V0.1.23').rstrip()+'\n')
print('V023_TWO_LEG_PELVIS_AND_HILLSIDE_COLLISION_PATCH_PASS')
