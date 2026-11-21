#!/usr/bin/env python3
"""Patch immutable published v0.1.12 into a NEW v0.1.13 directory only.
All anchors are single-occurrence and version/hashes are externally pinned by Termux.
The original asset and approved v0.1.9 remain untouched.
"""
from pathlib import Path
import json
import sys

root=Path(sys.argv[1]).resolve()
target=root/'tools/hareworks-forward-woman/v0.1.13'
v=target/'viewer.mjs'
s=v.read_text()

def once(old,new):
    global s
    n=s.count(old)
    if n!=1:raise RuntimeError(f'PATCH_ANCHOR_MISMATCH count={n}, anchor={old[:110]!r}')
    s=s.replace(old,new,1)

def region(first,end,replacement):
    global s
    if s.count(first)!=1 or s.count(end)!=1:raise RuntimeError('PATCH_REGION_ANCHOR_MISMATCH '+first[:60])
    a=s.index(first);b=s.index(end,a)
    s=s[:a]+replacement+s[b:]

once('/* v0.1.11. ONE moving Walking_Woman.', '/* v0.1.13. ONE moving Walking_Woman.')
once("import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';", "import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';\nimport {OrbitControls} from 'three/addons/controls/OrbitControls.js';")
once("import {inferContacts,sourceAt,SourceFootContact} from './foot-gait.mjs';", "import {sourceAt,SourceFootContact} from './foot-gait.mjs';\nimport {inferVelocityContact,buildRootCurve,rootAt,kneeFlexion} from './root-motion.mjs';")
once("const camera=new THREE.OrthographicCamera(-3,3,2,-2,.01,300);const cameraOffsets={oblique:[-4.8,3.15,5.7],side:[-6.4,2.75,0],front:[0,2.9,7.0],top:[-.01,8,.01]};let view='oblique';", "const camera=new THREE.OrthographicCamera(-3,3,2,-2,.01,300);const cameraOffsets={oblique:[-4.8,3.15,5.7],side:[-6.4,2.75,0],front:[0,2.9,7.0],top:[-.01,8,.01]};let view='oblique';\nconst orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.dampingFactor=.10;orbit.enablePan=false;orbit.enableRotate=true;orbit.minZoom=.55;orbit.maxZoom=3.5;orbit.target.set(0,.90,0);camera.position.fromArray(cameraOffsets[view]);orbit.update();")
once("let ready=false,playing=true,speed=.52,stride=.66,phase=0,worldZ=0,frameTimer=performance.now(),accumulator=0,groundOffset=0,runFrames=0,report=null,lastStats=null;", "let ready=false,playing=true,speed=.52,stride=.66,phase=0,totalPhase=0,rootCurve=null,worldZ=0,frameTimer=performance.now(),accumulator=0,groundOffset=0,runFrames=0,report=null,lastStats=null;")
once("let maxDrift=0,maxIK=0,maxPenetration=0,unreachable=0,contactCount=0,swingCount=0,transitions=0,failedFrames=0;", "let maxDrift=0,maxIK=0,maxPenetration=0,unreachable=0,contactCount=0,swingCount=0,transitions=0,failedFrames=0,maxTrailingExtensionDeficit=0,maxAnchorHeight=0;")
once("return soleWorld(c.meshes,patch);\n}", "return soleWorld(c.meshes,patch);\n}\nfunction splitFootPatches(meshes,foot,toe,all){\n const axis=wpos(toe).sub(wpos(foot));if(axis.length()<.035)throw Error('FOOT_TOE_AXIS_DEGENERATE_'+foot.name);axis.normalize();\n const points=all.indexes.map(idx=>{const m=meshes[idx.mi],p=m.getVertexPosition(idx.j,V());m.localToWorld(p);return {idx,forward:p.dot(axis)};}).sort((a,b)=>a.forward-b.forward);\n if(points.length<12||points.at(-1).forward-points[0].forward<.025)throw Error('SKINNED_HEEL_TOE_SEPARATION_INSUFFICIENT_'+foot.name);\n const k=Math.max(4,Math.floor(points.length/4));const mid=points.slice(k,points.length-k);\n const patch=part=>({indexes:part.map(p=>p.idx),count:part.length});\n const groups={heel:patch(points.slice(0,k)),sole:patch(mid),toe:patch(points.slice(-k))};\n const identity=g=>g.indexes.map(x=>x.mi+':'+x.j).join('|');\n if(new Set(Object.values(groups).map(identity)).size!==3)throw Error('HEEL_SOLE_TOE_WITNESSES_IDENTICAL');\n return groups;\n}")
region('function adjustReach(targets){','function solveLeg(side,t){', '''function adjustReach(targets){
 // The source-v0.1.9 hip curve is a protected style constraint. Do NOT push pelvis
 // down by an arbitrary 0.14 units. The real IK gate records any genuine overreach.
 for(const side of ['left','right']){
  const c=legs[side],reach=wpos(c.up).distanceTo(V(...targets[side].ankleTarget))-(c.upperLength+c.lowerLength);
  if(reach>.003)unreachable++;
 }
}
''')
once("const ankle=wpos(c.foot),reference=V(...t.source.ankle).add(actor.position);", "const ankle=wpos(c.foot),reference=V(...t.source.ankle).add(actor.position);\n  if(t.planted){const g=sourceGaits[side],u=mod1(phase-g.start)/g.duty;\n   if(u>.70){const actualRelative=ankle.z-wpos(c.up).z,sourceRelative=t.source.ankle[2]-t.source.hip[2];\n    maxTrailingExtensionDeficit=Math.max(maxTrailingExtensionDeficit,Math.max(0,actualRelative-sourceRelative));}\n   maxAnchorHeight=Math.max(maxAnchorHeight,t.badAnchorHeight||0);}")
once("out[side]=worldContacts[side].step({phase,worldZ,stride});", "out[side]=worldContacts[side].step({phase,worldZ,totalPhase});")
once("phase=mod1(phase+cadence*dt);worldZ+=speed*dt;frameBody(phase);", "totalPhase+=cadence*dt;phase=mod1(totalPhase);worldZ=rootAt(rootCurve,totalPhase);frameBody(phase);")
region('const cameraTarget=V();','function renderMetrics(', '''const trackedFollow=V(0,.90,0);
function pinCamera(){
 if(!actor)return;
 const desired=actor.position.clone().add(V(0,.90,0)),delta=desired.sub(trackedFollow);
 orbit.target.add(delta);camera.position.add(delta);trackedFollow.add(delta);orbit.update();
}
function setCameraPreset(k){
 view=k;const world=actor?actor.position:V();trackedFollow.copy(world).add(V(0,.90,0));
 orbit.target.copy(trackedFollow);camera.position.fromArray(cameraOffsets[k]).add(world);
 camera.up.set(0,1,0);orbit.update();camera.updateProjectionMatrix();
}
''')
once("function clearStats(){maxDrift=0;maxIK=0;maxPenetration=0;unreachable=0;contactCount=0;swingCount=0;transitions=0;runFrames=0;lastStats=null;shapeSum=0;shapeCount=0;}", "function clearStats(){maxDrift=0;maxIK=0;maxPenetration=0;unreachable=0;contactCount=0;swingCount=0;transitions=0;runFrames=0;lastStats=null;shapeSum=0;shapeCount=0;maxTrailingExtensionDeficit=0;maxAnchorHeight=0;}")
once("phase=0;worldZ=0;clearStats();frameBody(0);", "phase=0;totalPhase=0;worldZ=0;clearStats();frameBody(0);")
once("sourceGround,readWitness:k=>witnessCache[side][k]});", "sourceGround,readWitness:k=>witnessCache[side][k],rootAt:q=>rootAt(rootCurve,q)});")
once("for(const k of Object.keys(cameraOffsets))$(k).onclick=()=>{view=k;pinCamera()};", "for(const k of Object.keys(cameraOffsets))$(k).onclick=()=>setCameraPreset(k);\n$('resetCamera').onclick=()=>setCameraPreset('oblique');")
once("a.download='hareworks-woman-source-world-ik-v0.1.12.json'", "a.download='hareworks-woman-accepted-v019-world-pin-v0.1.13.json'")
once("try{initRun();const n=Math.ceil((3/cadenceFor(speed,stride))*120);", "try{initRun();const cameraOffsetBefore=camera.position.clone().sub(actor.position);const n=Math.ceil((3/cadenceFor(speed,stride))*120);")
once("pinCamera();const cameraError=Math.abs((camera.position.z-actor.position.z)-cameraOffsets[view][2]);", "pinCamera();const cameraError=camera.position.clone().sub(actor.position).distanceTo(cameraOffsetBefore);")
once("&&worldZ>.9&&cameraError<1e-8&&unreachable===0;", "&&worldZ>2.5&&cameraError<1e-6&&unreachable===0&&maxTrailingExtensionDeficit<.055&&maxAnchorHeight<.026;")
once("schema:'hareworks-woman-source-measured-world-ik-v0.1.12'", "schema:'hareworks-woman-accepted-v019-world-pin-v0.1.13'")
once("solver:'measured phase + hybrid heel/sole/toe contact + true world-space two-bone IK'", "solver:'accepted v0.1.9 ankle/pelvis curves + inverse phase-dependent support-root + world-space contact IK'")
once("sourceAnkleRms:Math.sqrt(shapeSum/Math.max(shapeCount,1)),sourcePoseSamples:360,", "sourceAnkleRms:Math.sqrt(shapeSum/Math.max(shapeCount,1)),sourcePoseSamples:360,\n    rootMethod:rootCurve.method,rootStridePerFullCycle:rootCurve.stride,\n    cameraOrbitEnabled:orbit.enableRotate&&orbit.enableZoom,\n    maxTrailingExtensionDeficit,maxAnchorHeight,")
once("if(ready&&playing){accumulator", "if(ready&&playing){accumulator")
once("renderer.render(scene,camera);}", "orbit.update();renderer.render(scene,camera);}")
once("const heelPatch=pickSolePatch(actorMeshes,foot),toePatch=pickSolePatch(actorMeshes,toe);\n  legs[side]={side,chain:b,up,knee,bridge,foot,toe,patch,heelPatch,toePatch,meshes:actorMeshes,soleLocal,upperLength,lowerLength};patches[side]=patch;", "const split=splitFootPatches(actorMeshes,foot,toe,patch),heelPatch=split.heel,toePatch=split.toe,solePatch=split.sole;\n  legs[side]={side,chain:b,up,knee,bridge,foot,toe,patch:solePatch,heelPatch,toePatch,meshes:actorMeshes,soleLocal,upperLength,lowerLength};patches[side]=solePatch;")
region(' // The authored clip has a documented final <7% phase reset:', ' groundOffset=absoluteGround;', ''' // Preserve original sub-duration source samples unchanged; do not invent a seam morph.
 sourceSeamRepair={left:{repaired:false},right:{repaired:false}};
 sourceGround=absoluteGround;
 sourceGaits={left:inferVelocityContact(sourceSamples.left),right:inferVelocityContact(sourceSamples.right)};
 const phaseSeparation=mod1(sourceGaits.left.start-sourceGaits.right.start);
 if(phaseSeparation<.30||phaseSeparation>.70)throw Error('LEFT_RIGHT_CONTACT_TIMING_AMBIGUOUS '+phaseSeparation);
 rootCurve=buildRootCurve(sourceSamples,sourceGaits);stride=rootCurve.stride;
 updateMotionStatus();
''')
once("const c=legs[side],foot=srcRig[c.foot.name],q=wq(foot).toArray();\n   const obs={phase:i/N,ankle:wpos(foot).toArray(),heel:soleWorld(refMeshes,c.heelPatch).toArray(),", "const c=legs[side],foot=srcRig[c.foot.name],q=wq(foot).toArray();\n   const sourceHip=wpos(srcRig[c.up.name]),accepted=legAt(footProfile,side,clipDuration*i/N),\n     acceptedYaw=independentPose(pelvisProfile,clipDuration*i/N).pelvisYaw;\n   const acceptedAnkle=sourceHip.clone().add(V(...rotateY(accepted.ankleLocal,acceptedYaw)));\n   const obs={phase:i/N,ankle:acceptedAnkle.toArray(),hip:sourceHip.toArray(),knee:wpos(srcRig[c.knee.name]).toArray(),\n    heel:soleWorld(refMeshes,c.heelPatch).toArray(),")
once("v0.1.12 SOURCE TASK-SPACE", "v0.1.13 ACCEPTED V019 INVERSE SUPPORT ROOT")
once("status('MEASURED SOURCE GAIT ACTIVE · world support · two-bone IK · owner gait review pending');", "status('ACCEPTED V0.1.9 WALK + INVERTED WORLD SUPPORT · orbit restored · owner review pending');")
# No auto pass: a quantitative gate is independent of human inspection.
if 'new THREE.AnimationMixer(actor)' in s or 'Math.sin(Math.PI*' in s:
    raise RuntimeError('SOURCE_LEG_PLAYBACK_OR_SYNTHETIC_SINE_DETECTED')
if 'new OrbitControls(camera,renderer.domElement)' not in s or 'rootAt(rootCurve,totalPhase)' not in s:
    raise RuntimeError('CAMERA_OR_ROOT_FEATURE_MISSING')
v.write_text(s)

html=target/'index.html';h=html.read_text()
if h.count('v0.1.12')<1:raise RuntimeError('UNEXPECTED_HTML_VERSION')
h=h.replace('v0.1.12','v0.1.13').replace('Measured Source Foot IK','Accepted Walk + World Pin')
h=h.replace('Fixed-follow camera presets','Orbit camera presets (drag to rotate, pinch to zoom)')
h=h.replace('<strong>Camera pinned:</strong>','<strong>Camera follows and orbits:</strong>')
h=h.replace('<button id="top">Top</button>','<button id="top">Top</button><button id="resetCamera">Reset orbit</button><span>Drag to rotate · pinch to zoom</span>')
h=h.replace('The camera follows a fixed offset while the ground moves past.', 'The camera follows the traveling actor while preserving your orbit and zoom.')
h=h.replace('src="./viewer.mjs?build=v0.1.13"','src="./viewer.mjs?build=v0.1.13-inverse-root"')
if 'resetCamera' not in h:raise RuntimeError('HTML_CAMERA_RESET_MISSING')
html.write_text(h)
print(json.dumps({'status':'PATCHED_NEW_DIRECTORY_ONLY','viewerBytes':len(s),'orbitRestored':True,'inverseRoot':True,'noLegacyEdits':True}))
