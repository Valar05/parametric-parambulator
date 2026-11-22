#!/usr/bin/env python3
"""Hareworks v0.1.21 terrain stress harness. Copies v0.1.20; no historical edit."""
from pathlib import Path
import sys
root,dest=map(Path,sys.argv[1:])
v=dest/'viewer.mjs';s=v.read_text()
def one(a,b):
 global s
 n=s.count(a)
 if n!=1:raise RuntimeError('V021_PINNED_VIEWER_ANCHOR_'+str(n)+'_'+a[:100])
 s=s.replace(a,b,1)
one('/* v0.1.20. ONE moving Walking_Woman.', '/* v0.1.21. ONE moving Walking_Woman.')
one("import {inferVelocityContact,buildRootCurve,rootAt,kneeFlexion} from './root-motion.mjs';", "import {inferVelocityContact,buildRootCurve,rootAt,kneeFlexion} from './root-motion.mjs';\nimport {TERRAIN_MODES,terrainHeight,terrainNormal,terrainBodyLift,terrainGrid} from './terrain-core.mjs';")
one('const ground=new THREE.GridHelper(180,180,0x6b8696,0x354858);scene.add(ground);\nfor(let i=0;i<24;i++){const marker=new THREE.Mesh(new THREE.BoxGeometry(.075,.025,.075),new THREE.MeshBasicMaterial({color:i%2?0x42768b:0x6ea9a9}));marker.position.set(-1.3,.015,i*1.5);scene.add(marker)}',
'''const ground=new THREE.GridHelper(180,180,0x6b8696,0x354858);scene.add(ground);
const flatMarkers=new THREE.Group();scene.add(flatMarkers);
for(let i=0;i<24;i++){const marker=new THREE.Mesh(new THREE.BoxGeometry(.075,.025,.075),new THREE.MeshBasicMaterial({color:i%2?0x42768b:0x6ea9a9}));marker.position.set(-1.3,.015,i*1.5);flatMarkers.add(marker)}''')
one('let dynamicMotion=null; // v0.1.20 anatomical pre-IK targets never depend on foot yaw',
'''let dynamicMotion=null; // v0.1.20 original stateless knee solver remains unchanged
// Terrain is a true physical world surface, not a rendered displacement only.
const terrainArgs=new URLSearchParams(location.search);
let terrainMode=TERRAIN_MODES.includes(terrainArgs.get('terrain'))?terrainArgs.get('terrain'):'rough';
const requestedStrength=Number(terrainArgs.get('relief')??'.65');
let terrainStrength=Number.isFinite(requestedStrength)?clamp(requestedStrength,0,1.25):.65;
let groundLift=0,terrainMesh=null,terrainWire=null,terrainCenterZ=0;
const terrainAt=(x,z)=>terrainHeight(x,z,terrainMode,terrainStrength);''')
one('const wpos=b=>b.getWorldPosition(V());', '''// Both visible triangles and foot-contact targets use terrainAt() exactly.
function rebuildTerrain(centerZ=0){
 if(terrainMesh){scene.remove(terrainMesh);scene.remove(terrainWire);
  terrainMesh.geometry.dispose();terrainMesh.material.dispose();terrainWire.material.dispose();
  terrainMesh=null;terrainWire=null;}
 terrainCenterZ=centerZ;
 ground.visible=terrainMode==='flat';flatMarkers.visible=terrainMode==='flat';
 if(terrainMode==='flat')return;
 const grid=terrainGrid(terrainMode,terrainStrength,centerZ,24,176),geo=new THREE.BufferGeometry();
 geo.setAttribute('position',new THREE.Float32BufferAttribute(grid.positions,3));
 geo.setAttribute('color',new THREE.Float32BufferAttribute(grid.colors,3));
 geo.setIndex(grid.indices);geo.computeVertexNormals();
 terrainMesh=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.95,side:THREE.DoubleSide}));
 terrainWire=new THREE.Mesh(geo,new THREE.MeshBasicMaterial({color:0x9ad3d0,wireframe:true,transparent:true,opacity:.10,depthWrite:false}));
 scene.add(terrainMesh);scene.add(terrainWire);
}
rebuildTerrain(0);
function reloadTerrain(mode,strength){
 const url=new URL(location.href);url.searchParams.set('terrain',mode);url.searchParams.set('relief',String(strength));
 location.assign(url.toString()); // New terrain is a NEW run, never teleport a planted anchor.
}
$('terrain').value=terrainMode;$('terrainIntensity').value=String(terrainStrength);
$('terrainIntensityOut').textContent=Math.round(terrainStrength*100)+'%';
$('terrain').onchange=()=>reloadTerrain($('terrain').value,terrainStrength);
$('terrainIntensity').oninput=()=>{$('terrainIntensityOut').textContent=Math.round(Number($('terrainIntensity').value)*100)+'%'};
$('terrainIntensity').onchange=()=>reloadTerrain(terrainMode,Number($('terrainIntensity').value));
const wpos=b=>b.getWorldPosition(V());''')
one('worldZ+=(nextCycle-previewCycle)*dynamicMotion.stride;\n previewCycle=nextCycle;phase=mod1(previewCycle);',
'''worldZ+=(nextCycle-previewCycle)*dynamicMotion.stride;
 groundLift=terrainBodyLift(groundLift,terrainAt(0,worldZ),Math.min(.25,Math.max(0,dt)));
 previewCycle=nextCycle;phase=mod1(previewCycle);''')
one('actor.position.z=worldZ;actor.position.y=-groundOffset;actor.updateMatrixWorld(true);}',
'''actor.position.z=worldZ;actor.position.y=-groundOffset+groundLift;actor.updateMatrixWorld(true);}''')
one('worldZ+=rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);\n totalPhase=newPhase;phase=mod1(totalPhase);frameBody(phase);',
'''worldZ+=rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);
 groundLift=terrainBodyLift(groundLift,terrainAt(0,worldZ),dt);
 totalPhase=newPhase;phase=mod1(totalPhase);frameBody(phase);''')
one('phase=0;totalPhase=0;worldZ=0;dynamicMotion=speedGait(speed,rootCurve.stride);',
'''phase=0;totalPhase=0;worldZ=0;groundLift=terrainAt(0,0);dynamicMotion=speedGait(speed,rootCurve.stride);''')
one('sourceGround,readWitness:k=>witnessCache[side][k],rootAt:q=>rootAt(rootCurve,q),\n  transformSource:(s,gait)=>transformSourceFoot(s,side,gait||dynamicMotion)});',
'''sourceGround,readWitness:k=>witnessCache[side][k],rootAt:q=>rootAt(rootCurve,q),
  terrainAt:terrainMode==='flat'?null:terrainAt,
  transformSource:(s,gait)=>transformSourceFoot(s,side,gait||dynamicMotion)});''')
one('const kneeChanged=kneeBefore.distanceTo(wpos(c.knee));',
'''// Pitch/roll the already-styled shoe to the measured surface normal.
 // This is distal only: the accepted knee poles, joint positions and foot yaw
 // remain unmodified. Real skinned heel/toe clearance is audited below.
 if(terrainMode!=='flat'){
  const footP=wpos(c.foot),normal=V(...terrainNormal(footP.x,footP.z,terrainMode,terrainStrength));
  const slopeTilt=Q().setFromUnitVectors(V(0,1,0),normal);
  setWorldQ(c.foot,Q().slerp(slopeTilt,.72).multiply(wq(c.foot)).normalize());actor.updateMatrixWorld(true);
 }
 const kneeChanged=kneeBefore.distanceTo(wpos(c.knee));''')
one("const h=['heel','sole','toe'].map(k=>witnessWorld(c,k).y);\n maxPenetration=Math.max(maxPenetration,Math.max(0,...h.map(y=>-y)));",
'''const footPatches=['heel','sole','toe'].map(k=>witnessWorld(c,k));
 const terrainIntrusion=Math.max(0,...footPatches.map(p=>terrainAt(p.x,p.z)-p.y));
 maxPenetration=Math.max(maxPenetration,terrainIntrusion);''')
one('kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch};',
'''kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch,
  terrainHeightAtPivot:terrainAt(actual.x,actual.z),terrainClearance:actual.y-terrainAt(actual.x,actual.z),
  terrainMode};''')
one('contactFrames:contactCount,swingFrames:swingCount,solvedIKPerFrame:true,generatedAnimationMixerCount:0};',
'''contactFrames:contactCount,swingFrames:swingCount,solvedIKPerFrame:true,generatedAnimationMixerCount:0,
 terrainMode,terrainStrength,bodyTerrainLift:groundLift};''')
one('Skinned support error ${maxDrift.toFixed(5)} u, floor penetration ${maxPenetration.toFixed(5)} u',
'''Skinned support error ${maxDrift.toFixed(5)} u, TERRAIN penetration ${maxPenetration.toFixed(5)} u
Surface ${terrainMode} at ${Math.round(terrainStrength*100)}% · root ground Y ${terrainAt(0,worldZ).toFixed(4)} · body lift ${groundLift.toFixed(4)}''')
one('sourceClip:CLIP,rigBones:74,sourceContactMethod:sourceGaits,sourceSeamRepair,',
'''sourceClip:CLIP,rigBones:74,sourceContactMethod:sourceGaits,sourceSeamRepair,
    terrainMode,terrainStrength,terrainSourceOfTruth:'terrain-core.mjs height(x,z) shared by mesh, touchdown, swing, body and audit',
    surfaceAtRoot:terrainAt(0,worldZ),bodyTerrainLift:groundLift,terrainContactsUseWorldSpace:true,''')
one('function frame(now){requestAnimationFrame(frame);',
'''function frame(now){requestAnimationFrame(frame);
 if(terrainMode!=='flat'&&worldZ-terrainCenterZ>14)rebuildTerrain(Math.floor(worldZ/14)*14);''')
one('const startZ=worldZ;for(let i=0;i<32;i++)physicsStep(1/120);',
'''const startZ=worldZ;for(let i=0;i<32;i++)physicsStep(1/120);''') if False else None
one("status('PHYSICAL IK CONTROLLER STARTED · 32 REAL SKINNED STEPS EXECUTED · owner gait approval pending');",
    "status('PHYSICAL IK ON '+terrainMode.toUpperCase()+' TERRAIN · 32 real skinned startup steps · run contact audit to verify ground clearance');")
one("ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,",
'''ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,''') if False else None
# Reuse v0.1.20 original source knees, foot yaw, and protected gait math; version UI only.
s=s.replace('v0.1.20','v0.1.21').replace('V0.1.20','V0.1.21')
assert "terrainAt:terrainMode==='flat'?null:terrainAt" in s
assert "const pole=stableForwardPole(side,yaw);" in s
assert "const chosen=chooseSourceKnee" in s
assert "distalHeading(side,footFit,pelvisProfile)" in s
assert "worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})" in s
v.write_text(s.rstrip()+'\n')
# Physical ground anchor is the selected surface height, not a screen ornament.
f=dest/'foot-gait.mjs';src=f.read_text()
def replace_foot(old,new,expected=1):
 global src
 n=src.count(old)
 if n!=expected:raise RuntimeError('V021_FOOT_ANCHOR_COUNT_'+str(n)+'_'+old[:70])
 src=src.replace(old,new)
replace_foot('constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0,transformSource=null}){',
             'constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0,transformSource=null,terrainAt=null}){')
replace_foot('this.readWitness=readWitness;this.rootAt=rootAt;this.transformSource=transformSource;this.activeDuty=gait.duty;',
             'this.readWitness=readWitness;this.rootAt=rootAt;this.transformSource=transformSource;this.terrainAt=terrainAt;this.activeDuty=gait.duty;')
replace_foot(' step({phase,worldZ,totalPhase,gait}){', ''' captureAnchor(kind){
  const anchor=this.readWitness(kind).slice();
  if(this.terrainAt)anchor[1]=this.terrainAt(anchor[0],anchor[2]);
  if(!finite(anchor))throw Error('TERRAIN_CONTACT_ANCHOR_INVALID');
  return anchor;
 }
 step({phase,worldZ,totalPhase,gait}){''')
replace_foot('const baseline=add(s.ankle,[0,-this.sourceGround,worldZ]);',
             '''const baseline=add(s.ankle,[0,-this.sourceGround,worldZ]);
  if(this.terrainAt)baseline[1]+=this.terrainAt(baseline[0],baseline[2]);''')
replace_foot('this.anchor=this.readWitness(pivot).slice();','this.anchor=this.captureAnchor(pivot);',2)
replace_foot('Math.abs(this.anchor[1]-this.groundY)',
             'Math.abs(this.anchor[1]-(this.terrainAt?this.terrainAt(this.anchor[0],this.anchor[2]):this.groundY))',2)
assert src.count('this.anchor=this.captureAnchor(pivot)')==2
f.write_text(src.rstrip()+'\n')
# UI selects separate physical tests, never invisibly changes terrain mid-contact.
p=dest/'index.html';html=p.read_text()
needle='<div class="bar" role="group" aria-label="Orbit camera presets (drag to rotate, pinch to zoom)">'
assert html.count(needle)==1
block='''<div class="bar" role="group" aria-label="Physical terrain test selection">
<label for="terrain">Ground surface</label><select id="terrain"><option value="flat">Flat control</option><option value="uphill">Uphill</option><option value="downhill">Downhill</option><option value="cross-slope">Side slope</option><option value="rough">Rough ground</option></select>
<label for="terrainIntensity">Slope / relief</label><input id="terrainIntensity" type="range" min="0" max="1.25" step="0.05" value="0.65"><output id="terrainIntensityOut">65%</output>
<span class="small">Surface change restarts the run to avoid teleporting planted feet. Green and orange markers show true world contact targets. Default: rough.</span></div>
'''
html=html.replace(needle,block+needle)
html=html.replace('button,input{font:inherit}', 'button,input,select{font:inherit}')
html=html.replace('v0.1.20','v0.1.21').replace('V0.1.20','V0.1.21')
html=html.replace('v0.1.20-source-knees','v0.1.21-terrain-world-contact')
html=html.replace('One source-measured, independently IK-solved skinned Hareworks character',
'''One source-measured, independently IK-solved skinned Hareworks character on physically sampled rough or sloped ground''')
html=html.replace('Audit source gait + skinned contacts','Audit terrain + real skinned contacts')
p.write_text(html.rstrip()+'\n')
p=dest/'review-server.py';txt=p.read_text().replace('v0.1.20','v0.1.21').replace('V0.1.20','V0.1.21');p.write_text(txt.rstrip()+'\n')
print('V021_PINNED_TERRAIN_PATCH_PASS: source knees, foot heading and flat-gait retained')
