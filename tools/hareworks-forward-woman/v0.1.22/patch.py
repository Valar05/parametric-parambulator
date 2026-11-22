#!/usr/bin/env python3
"""Hareworks v0.1.22: severe longitudinal terrain and readable ground witnesses.
Build a new immutable version from exact published v0.1.21. Never edit older versions.
"""
from pathlib import Path
import sys
source,dest=map(Path,sys.argv[1:])
v=dest/'viewer.mjs';s=v.read_text()
def one(old,new):
 global s
 count=s.count(old)
 if count!=1:raise RuntimeError(f'V022_PINNED_VIEWER_ANCHOR_{count}_'+old[:125])
 s=s.replace(old,new,1)
one('/* v0.1.21. ONE moving Walking_Woman.', '/* v0.1.22. ONE moving Walking_Woman.')
one("import {TERRAIN_MODES,terrainHeight,terrainNormal,terrainBodyLift,terrainGrid} from './terrain-core.mjs';",
    "import {TERRAIN_MODES,isProfileTerrain,terrainHeight,terrainNormal,terrainBodyLift,terrainGrid,longitudinalProfile} from './terrain-core.mjs';")
one("let terrainMode=TERRAIN_MODES.includes(terrainArgs.get('terrain'))?terrainArgs.get('terrain'):'rough';",
    "let terrainMode=TERRAIN_MODES.includes(terrainArgs.get('terrain'))?terrainArgs.get('terrain'):'profile-ridges';")
one("const requestedStrength=Number(terrainArgs.get('relief')??'.65');",
    "const requestedStrength=Number(terrainArgs.get('relief')??'1.1');")
one('let terrainStrength=Number.isFinite(requestedStrength)?clamp(requestedStrength,0,1.25):.65;',
    'let terrainStrength=Number.isFinite(requestedStrength)?clamp(requestedStrength,0,3):1.1;')
one('let groundLift=0,terrainMesh=null,terrainWire=null,terrainCenterZ=0;',
    '''let groundLift=0,terrainMesh=null,terrainWire=null,terrainSlice=null,terrainCenterZ=0;
const profileMode=()=>isProfileTerrain(terrainMode);
// Ground projection markers show the exact height directly beneath each
// actual skinned heel, sole and toe. They never write IK targets or knee poles.
const projectedWitnesses={left:{},right:{}};
const witnessKinds=['heel','sole','toe'];''')
one("const drawPins={};for(const side of ['left','right']){const m=new THREE.Mesh(new THREE.SphereGeometry(.045,12,10),new THREE.MeshBasicMaterial({color:side==='left'?0x6bf5bf:0xb8fa83,depthTest:false}));m.renderOrder=15;scene.add(m);drawPins[side]=m;}",
'''const drawPins={};for(const side of ['left','right']){const m=new THREE.Mesh(new THREE.SphereGeometry(.045,12,10),new THREE.MeshBasicMaterial({color:side==='left'?0x6bf5bf:0xb8fa83,depthTest:false}));m.renderOrder=15;scene.add(m);drawPins[side]=m;}
for(const side of ['left','right'])for(const kind of witnessKinds){
 const r=kind==='sole'?.030:.019;
 const m=new THREE.Mesh(new THREE.SphereGeometry(r,10,8),new THREE.MeshBasicMaterial({color:side==='left'?0x00e8ff:0xffbd4a,depthTest:false}));
 m.renderOrder=18;scene.add(m);projectedWitnesses[side][kind]=m;
}''')
one('if(terrainMesh){scene.remove(terrainMesh);scene.remove(terrainWire);\n  terrainMesh.geometry.dispose();terrainMesh.material.dispose();terrainWire.material.dispose();\n  terrainMesh=null;terrainWire=null;}',
'''if(terrainMesh){scene.remove(terrainMesh);scene.remove(terrainWire);
  terrainMesh.geometry.dispose();terrainMesh.material.dispose();terrainWire.material.dispose();
  terrainMesh=null;terrainWire=null;}
 if(terrainSlice){scene.remove(terrainSlice);for(const l of terrainSlice.children){l.geometry.dispose();l.material.dispose();}terrainSlice=null;}''')
one('const grid=terrainGrid(terrainMode,terrainStrength,centerZ,24,176),geo=new THREE.BufferGeometry();',
    'const grid=terrainGrid(terrainMode,terrainStrength,centerZ,profileMode()?12:24,profileMode()?400:176),geo=new THREE.BufferGeometry();')
one('scene.add(terrainMesh);scene.add(terrainWire);',
'''scene.add(terrainMesh);scene.add(terrainWire);
 terrainWire.visible=!profileMode(); // Do not obscure the profile with crisscross wireframe.
 if(profileMode()){
  terrainSlice=new THREE.Group();
  const profile=longitudinalProfile(terrainMode,terrainStrength,centerZ,400);
  for(const x of [-.81,.81]){
   const curve=new THREE.BufferGeometry().setFromPoints(profile.map(({z,y})=>V(x,y+.013,z)));
   const line=new THREE.Line(curve,new THREE.LineBasicMaterial({color:x<0?0xf6d383:0x729ca2,depthTest:false,transparent:true,opacity:x<0?.97:.62}));
   line.renderOrder=12;terrainSlice.add(line);
  }
  scene.add(terrainSlice);
 }''')
one('rebuildTerrain(0);', "rebuildTerrain(0);\nif(profileMode()){view='side';camera.position.fromArray(cameraOffsets.side);orbit.update();}")
one("$('terrainIntensityOut').textContent=Math.round(terrainStrength*100)+'%';",
    "$('terrainIntensityOut').textContent=Math.round(terrainStrength*100)+'%';$('terrainReadability').textContent=profileMode()?'PROFILE: identical height under both feet at equal forward Z':'LEGACY: height varies across width; select a Profile course for clear foot evaluation';")
one('const footPatches=[\'heel\',\'sole\',\'toe\'].map(k=>witnessWorld(c,k));',
'''const footPatches=witnessKinds.map(k=>witnessWorld(c,k));
 // Bright dots trace the same analytic contact surface sampled by the IK.
 // Terrain projections are diagnostic only, never anatomy or contact targets.
 for(let i=0;i<witnessKinds.length;i++){
  const p=footPatches[i],marker=projectedWitnesses[side][witnessKinds[i]];
  marker.position.set(p.x,terrainAt(p.x,p.z)+.013,p.z);
  marker.visible=$('showContacts').checked&&ready&&motionMode==='PHYSICAL_GROUND_PINNING';
 }''')
one("for(const p of Object.values(drawPins))p.visible=false;\n $('play').textContent='Pause';",
    "for(const p of Object.values(drawPins))p.visible=false;for(const side of ['left','right'])for(const p of Object.values(projectedWitnesses[side]))p.visible=false;\n $('play').textContent='Pause';")
one("$('showContacts').onchange=()=>{\n for(const side of ['left','right'])drawPins[side].visible=ready&&motionMode==='PHYSICAL_GROUND_PINNING'&&$('showContacts').checked;\n};",
    "$('showContacts').onchange=()=>{\n for(const side of ['left','right']){drawPins[side].visible=ready&&motionMode==='PHYSICAL_GROUND_PINNING'&&$('showContacts').checked;for(const p of Object.values(projectedWitnesses[side]))p.visible=drawPins[side].visible;}\n};")
one('const terrainIntrusion=Math.max(0,...footPatches.map(p=>terrainAt(p.x,p.z)-p.y));',
'''const terrainClearances=Object.fromEntries(witnessKinds.map((k,i)=>[k,footPatches[i].y-terrainAt(footPatches[i].x,footPatches[i].z)]));
 const terrainIntrusion=Math.max(0,...footPatches.map(p=>terrainAt(p.x,p.z)-p.y));''')
one('kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch,',
    'kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch,terrainClearances,')
one('Skinned support error ${maxDrift.toFixed(5)} u, TERRAIN penetration ${maxPenetration.toFixed(5)} u',
'''Skinned support error ${maxDrift.toFixed(5)} u, TERRAIN penetration ${maxPenetration.toFixed(5)} u
WIDTH-PARITY ${profileMode()?'SAME HEIGHT LEFT/RIGHT':'VARIABLE (legacy mode)'} · cyan/orange = terrain level at actual heel,sole,toe
HEEL/SOLE/TOE above ground L ${Object.values(feet.left.terrainClearances).map(x=>x.toFixed(3)).join('/')} · R ${Object.values(feet.right.terrainClearances).map(x=>x.toFixed(3)).join('/')}''')
one("terrainMode,terrainStrength,terrainSourceOfTruth:'terrain-core.mjs height(x,z) shared by mesh, touchdown, swing, body and audit',",
    "terrainMode,terrainStrength,terrainWidthInvariant:profileMode(),terrainProfileHeightSameAcrossWidth:profileMode(),terrainSourceOfTruth:'terrain-core.mjs height(x,z) shared by mesh, touchdown, swing, body and audit',")
one("status('PHYSICAL IK ON '+terrainMode.toUpperCase()+' TERRAIN · 32 real skinned startup steps · run contact audit to verify ground clearance');",
    "status('PHYSICAL IK ON '+terrainMode.toUpperCase()+' AT '+Math.round(terrainStrength*100)+'% · width-invariant profile='+profileMode()+' · run real contact audit');")
# The boot-screen build identity must never display a stale v0.1.14 version.
one("$('identity').textContent='v0.1.14 · ORIGINAL SKINNED 3D MODEL HASH '+SOURCE_SHA+' · SOURCE MATH AND CONTACT AUDIT PENDING';",
    "$('identity').textContent='v0.1.22 · ORIGINAL SKINNED 3D MODEL HASH '+SOURCE_SHA+' · STRESS PROFILE SOURCE AND CONTACT AUDIT PENDING';")
# This source code must NOT mutate anatomical step or foot heading definitions.
for protected in ["const pole=stableForwardPole(side,yaw);",'const chosen=chooseSourceKnee(', 'distalHeading(side,footFit,pelvisProfile)',"worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion})"]:
 if protected not in s:raise RuntimeError('V022_ACCEPTED_GAIT_MISSING '+protected)
assert 'sourceKneePlane(' not in s
s=s.replace('v0.1.21','v0.1.22').replace('V0.1.21','V0.1.22')
v.write_text(s.rstrip()+'\n')
p=dest/'index.html';h=p.read_text()
h=h.replace('<option value="rough">Rough ground</option>',
'''<option value="rough">Legacy side-varying rough</option><option value="profile-ridges">Profile ridges (clear cross-width)</option><option value="profile-steps">Profile high steps (hard)</option><option value="profile-ramp">Profile steep ramp (hard)</option>''')
h=h.replace('max="1.25" step="0.05" value="0.65"','max="3" step="0.1" value="1.1"')
h=h.replace('<output id="terrainIntensityOut">65%</output>', '<output id="terrainIntensityOut">110%</output>')
h=h.replace('Surface change restarts the run to avoid teleporting planted feet. Green and orange markers show true world contact targets. Default: rough.',
'''Profile courses have identical ground height across the entire walking width. The copper side rails mark the true surface height. Cyan and amber dots mark height directly under each heel/sole/toe. Maximum stress = 300%. Terrain changes reset planted contacts; the original gait is unchanged.<span id="terrainReadability" role="status" aria-live="polite"></span>''')
h=h.replace('Show world contact anchors','Show anchors and heel/sole/toe ground markers')
h=h.replace('one character</span>','one character · stress profiles</span>')
h=h.replace('v0.1.21','v0.1.22').replace('V0.1.21','V0.1.22')
assert h.count('id="terrainReadability"')==1
assert h.count('<option value="profile-ridges">')==1
p.write_text(h.rstrip()+'\n')
p=dest/'review-server.py';t=p.read_text().replace('v0.1.21','v0.1.22').replace('V0.1.21','V0.1.22');p.write_text(t.rstrip()+'\n')
print('V022_PINNED_PROFILE_STRESS_PATCH_PASS: source knee/foot/flat gait untouched; stronger width-invariant contact surface')
