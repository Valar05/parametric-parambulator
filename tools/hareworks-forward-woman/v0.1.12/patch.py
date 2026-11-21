#!/usr/bin/env python3
"""Hareworks v0.1.12 deterministic immutable-version patcher.
Requires pristine v0.1.11 copied to a brand-new v0.1.12 path by Termux.
"""
import json
import pathlib
import re
import sys

root=pathlib.Path(sys.argv[1]); target=root/'tools/hareworks-forward-woman/v0.1.12'
v=target/'viewer.mjs'; s=v.read_text()
def once(old,new):
    global s
    count=s.count(old)
    if count!=1:raise RuntimeError(f'PATCH_ANCHOR_COUNT expected=1 got={count} anchor={old[:80]!r}')
    s=s.replace(old,new)
def region(begin,end,replacement):
    global s
    if s.count(begin)!=1 or s.count(end)!=1:raise RuntimeError(f'PATCH_REGION_MISSING {begin!r}/{end!r}')
    a=s.index(begin);b=s.index(end,a+len(begin));s=s[:a]+replacement+s[b:]

once("import {WorldContact,mod1,clamp,swingProgress,nextStartDelta,followCamera,cadenceFor,travelToNextContact} from './contact-core.mjs';",
     "import {mod1,clamp,followCamera,cadenceFor} from './contact-core.mjs';\nimport {inferContacts,sourceAt,SourceFootContact} from './foot-gait.mjs';")
once('stride=.66,clearance=.055,phase=0','stride=.66,phase=0')
once('let maxDrift=0,maxIK=0,maxPenetration=0,unreachable=0,contactCount=0,swingCount=0,transitions=0,lastAnchorLocations={},failedFrames=0;',
     'let maxDrift=0,maxIK=0,maxPenetration=0,unreachable=0,contactCount=0,swingCount=0,transitions=0,failedFrames=0;\nlet sourceSamples=null,sourceGaits=null,sourceGround=0,witnessCache=null,sourceSeamRepair={},shapeSum=0,shapeCount=0;')
region('function setWorldQ(', 'function turnToward(', '''function witnessWorld(c,kind){
 if(kind==='ankle')return wpos(c.foot);
 const patch=kind==='heel'?c.heelPatch:kind==='toe'?c.toePatch:c.patch;
 return soleWorld(c.meshes,patch);
}
function measuredFootQ(s){return Q().fromArray(s.q0).slerp(Q().fromArray(s.q1),s.qt).normalize()}
function setWorldQ(b,desired){b.quaternion.copy(wq(b.parent).invert().multiply(desired)).normalize()}
''')
region('function nominalLanding(', 'const cameraTarget=', '''function measuredWitnesses(){const out={};for(const side of ['left','right']){
 const c=legs[side];out[side]=Object.fromEntries(['ankle','heel','sole','toe'].map(k=>[k,witnessWorld(c,k).toArray()]));
 }return out;}
function contactTargets(){const out={};for(const side of ['left','right']){
 out[side]=worldContacts[side].step({phase,worldZ,stride});
 }return out;}
function adjustReach(targets){let correction=0;
 for(const side of ['left','right']){
  const leg=legs[side],ankle=V(...targets[side].ankleTarget),hip=wpos(leg.up),r=leg.upperLength+leg.lowerLength-.014;
  correction=Math.max(correction,Math.max(0,hip.distanceTo(ankle)-r));}
 if(correction>0){const moved=Math.min(.14,correction+.002);rig.mixamorigHips.position.y-=moved;actor.updateMatrixWorld(true);if(correction>.14)unreachable++;}
}
function solveLeg(side,t){const c=legs[side],desiredQ=measuredFootQ(t.source),target=V(...t.ankleTarget);
 let desiredAnkle=target.clone(),best=Infinity;
 for(let iter=0;iter<5;iter++){
  for(const b of c.chain)copyLocal(b,rest[b.name]);actor.updateMatrixWorld(true);
  const H=wpos(c.up),K0=wpos(c.knee),max=c.upperLength+c.lowerLength-.005,min=Math.abs(c.upperLength-c.lowerLength)+.005;
  let direction=desiredAnkle.clone().sub(H);
  if(direction.length()>max||direction.length()<min){direction.setLength(clamp(direction.length(),min,max));desiredAnkle.copy(H).add(direction);unreachable++;}
  const pole=legAt(footProfile,side,phase*clipDuration).poleLocal;
  const yaw=independentPose(pelvisProfile,phase*clipDuration).pelvisYaw;
  const K=V(...kneeFromTarget(H.toArray(),desiredAnkle.toArray(),c.upperLength,c.lowerLength,rotateY(pole,yaw)));
  turnToward(c.up,K0,K);actor.updateMatrixWorld(true);
  turnToward(c.knee,wpos(c.foot),desiredAnkle);actor.updateMatrixWorld(true);
  setWorldQ(c.foot,desiredQ);actor.updateMatrixWorld(true);
  const actual=witnessWorld(c,t.planted?t.pivot:'ankle');
  const wanted=V(...t.witnessTarget),error=wanted.sub(actual);best=error.length();
  if(best<.0018)break;desiredAnkle.add(error.multiplyScalar(.92));
 }
 const actual=witnessWorld(c,t.planted?t.pivot:'ankle'),drift=actual.distanceTo(V(...t.witnessTarget));
 const ankle=wpos(c.foot),reference=V(...t.source.ankle).add(actor.position);
 const shapeError=ankle.distanceTo(reference);shapeSum+=shapeError*shapeError;shapeCount++;
 if(t.planted){maxDrift=Math.max(maxDrift,drift);contactCount++}else swingCount++;
 const h=['heel','sole','toe'].map(k=>witnessWorld(c,k).y);maxPenetration=Math.max(maxPenetration,Math.max(0,...h.map(y=>-y)));
 maxIK=Math.max(maxIK,drift);
 drawPins[side].position.copy(V(...t.witnessTarget));drawPins[side].visible=$('showContacts').checked;
 drawPins[side].material.color.setHex(t.planted?0x65f2b7:0xffb65f);
 return {planted:t.planted,pivot:t.pivot,drift,sole:witnessWorld(c,'sole').toArray(),
  ankle:ankle.toArray(),target:t.ankleTarget,anchor:t.anchor,shapeError,reach:c.upperLength+c.lowerLength};
}
function physicsStep(dt){
 // Capture last physically solved geometry BEFORE frameBody restores the source-calibration skeleton.
 witnessCache=measuredWitnesses();
 const cadence=cadenceFor(speed,stride);phase=mod1(phase+cadence*dt);worldZ+=speed*dt;frameBody(phase);
 const targets=contactTargets();adjustReach(targets);const feet={};
 for(const side of ['left','right'])feet[side]=solveLeg(side,targets[side]);
 transitions=worldContacts.left.transitions+worldContacts.right.transitions;runFrames++;
 lastStats={phase,worldTravelZ:worldZ,speed,cadence,worldRootZ:actor.position.z,feet,transitions,
 maxSkinnedStanceDrift:maxDrift,maxSkinnedTargetError:maxIK,maxNewFloorPenetration:maxPenetration,
 sourceAnkleRms:Math.sqrt(shapeSum/Math.max(1,shapeCount)),reachAdjustments:unreachable,
 contactFrames:contactCount,swingFrames:swingCount,solvedIKPerFrame:true,generatedAnimationMixerCount:0};
 return lastStats;
}
''')
region('function renderMetrics(', "$('play').onclick=", '''function renderMetrics(prefix='LIVE'){if(!lastStats)return;const feet=lastStats.feet;
 $('metrics').textContent=`${prefix} · SOURCE-MEASURED WALKING_WOMAN · WORLD IK\\nTravel Z ${worldZ.toFixed(3)} u, phase ${(phase*100).toFixed(1)}%, cadence ${cadenceFor(speed,stride).toFixed(3)} cycles/s\\nLEFT ${feet.left.pivot} ${feet.left.planted?'PLANTED':'SWING'}, drift ${feet.left.drift.toFixed(4)} u\\nRIGHT ${feet.right.pivot} ${feet.right.planted?'PLANTED':'SWING'}, drift ${feet.right.drift.toFixed(4)} u\\nSkinned support error ${maxDrift.toFixed(5)} u, floor penetration ${maxPenetration.toFixed(5)} u\\nSource ankle RMS ${lastStats.sourceAnkleRms.toFixed(5)} u; knee reach warnings ${unreachable}\\nContact transitions ${transitions}; source stance L ${(sourceGaits.left.duty*100).toFixed(1)}%, R ${(sourceGaits.right.duty*100).toFixed(1)}%\\nANIMATION MIXER ON VISIBLE ACTOR: ZERO · source joints NOT replayed`;
}
function clearStats(){maxDrift=0;maxIK=0;maxPenetration=0;unreachable=0;contactCount=0;swingCount=0;transitions=0;runFrames=0;lastStats=null;shapeSum=0;shapeCount=0;}
function initRun(){if(!ready)return;
 phase=0;worldZ=0;clearStats();frameBody(0);witnessCache=measuredWitnesses();const next={};
 for(const side of ['left','right'])next[side]=new SourceFootContact({samples:sourceSamples[side],gait:sourceGaits[side],
  sourceGround,readWitness:k=>witnessCache[side][k]});
 worldContacts=next;physicsStep(0);pinCamera();renderMetrics('RESET');
}
''')
region("$('speed').oninput=", "$('showContacts').onchange=", '''$('speed').oninput=()=>{speed=Number($('speed').value);$('speedOut').textContent=speed.toFixed(2)+' u/s';updateMotionStatus()};
function updateMotionStatus(){
 $('motionStatus').textContent=`SOURCE-DERIVED FOOT PATH · ${stride.toFixed(3)} u travel/cycle · ${cadenceFor(speed,stride).toFixed(3)} cycles/s · no synthetic foot lift`;
}
updateMotionStatus();
''')
region("$('audit').onclick=",'function frame(now)', '''$('audit').onclick=async()=>{if(!ready)return;const was=playing;playing=false;
 status('Auditing measured contacts across 3 cycles, 120 Hz; source resemblance is a separate gate…');const oldSpeed=speed;speed=.52;
 try{initRun();const n=Math.ceil((3/cadenceFor(speed,stride))*120);
  const worst={left:0,right:0},previous={left:null,right:null},pivotCounts={},samples=[];
  let anchorMaxStep=0;
  for(let i=0;i<n;i++){
   const m=physicsStep(1/120);
   for(const side of ['left','right']){
    const f=m.feet[side];pivotCounts[side+':'+f.pivot]=(pivotCounts[side+':'+f.pivot]||0)+1;
    if(f.planted){worst[side]=Math.max(worst[side],f.drift);
      if(previous[side]&&previous[side].pivot===f.pivot)
       anchorMaxStep=Math.max(anchorMaxStep,Math.hypot(...f.anchor.map((x,j)=>x-previous[side].anchor[j])));
      previous[side]={pivot:f.pivot,anchor:f.anchor?.slice()};}
    else previous[side]=null;
   }
   if(i%15===0)samples.push({time:i/120,phase:m.phase,worldZ:m.worldTravelZ,
    left:m.feet.left,right:m.feet.right,cameraTrackingOffset:cameraOffsets[view]});
   if(i%35===0)await new Promise(requestAnimationFrame);
  }
  pinCamera();const cameraError=Math.abs((camera.position.z-actor.position.z)-cameraOffsets[view][2]);
  const physicalPass=worst.left<=.025&&worst.right<=.025&&maxPenetration<=.020&&anchorMaxStep<=1e-8&&worldZ>.9&&cameraError<1e-8&&unreachable===0;
  report={schema:'hareworks-woman-source-measured-world-ik-v0.1.12',sourceSha256:SOURCE_SHA,
    sourceClip:CLIP,rigBones:74,sourceContactMethod:sourceGaits,sourceSeamRepair,
    strideCycle:stride,actualCyclesTested:n/120*cadenceFor(speed,stride),
    nominalForwardAdvance:worldZ,generatedAnimationMixerCount:0,calibrationOnlySourceMixer:true,
    oneVisibleCharacter:true,rootMovementIsWorldTravel:true,cameraFixedFollow:true,
    stanceAnchorCoordinateSystem:'WORLD',contactPatch:'skinned heel/sole/toe witnesses',physicsRateHz:120,
    sampledFrames:n,worldTravelZ:worldZ,referenceRigWasNotDisplayed:true,
    solver:'measured phase + hybrid heel/sole/toe contact + true world-space two-bone IK',
    maxSkinnedSoleDriftPerSide:worst,maximumContactAnchorTranslation:anchorMaxStep,
    maxFootPenetration:maxPenetration,maxIKResidual:maxIK,reachAdjustments:unreachable,
    cameraWorldFollowError:cameraError,touchdownTransitions:transitions,contactPivotCounts:pivotCounts,
    sourceAnkleRms:Math.sqrt(shapeSum/Math.max(shapeCount,1)),sourcePoseSamples:360,
    contactGate:physicalPass?'PASS':'WARN',resemblanceGate:'OWNER_VISUAL_REVIEW_PENDING',
    status:physicalPass?'PHYSICAL_CONTACT_PASS_STYLE_OWNER_PENDING':'PHYSICAL_CONTACT_WARN_OWNER_REVIEW_REQUIRED',
    ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,observations:samples};
  $('metrics').textContent=`${report.status}\\nCONTACT: heel/sole/toe anchors L ${worst.left.toFixed(5)}, R ${worst.right.toFixed(5)} u (limit .025)\\nSource ankle RMS ${report.sourceAnkleRms.toFixed(5)} u (advisory, NOT gait approval)\\nFloor intrusion ${maxPenetration.toFixed(5)} u; IK warnings ${unreachable}\\n3 measured cycles, 120 Hz, traveling root ${worldZ.toFixed(3)} u\\nSTYLE GATE: must resemble v0.1.9 Walking_Woman in owner's inspection`;
  try{const response=await fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(report)});
   if(!response.ok)throw Error('HTTP_'+response.status);const receipt=await response.json();status(report.status+' · evidence saved '+receipt.sha256.slice(0,12));}
  catch(e){status(report.status+' · autosave unavailable '+e.message+' · Export still works')}
 }catch(e){status('SOURCE_GAIT_AUDIT_ERROR '+e.message);console.error(e)}
 finally{const summary=$('metrics').textContent;speed=oldSpeed;initRun();$('metrics').textContent=summary;playing=was;$('play').textContent=playing?'Pause':'Play';}
};
''')
region(' // Calibrate source contact LOW phases', ' groundOffset=absoluteGround;', ''' // Measure actual heel/toe/sole/ankle positions and orientation from the immutable source clip.
 const N=360;sourceSamples={left:[],right:[]};let absoluteGround=Infinity;
 for(let i=0;i<N;i++){
  mixer.setTime(clipDuration*i/N);source.updateMatrixWorld(true);
  for(const side of ['left','right']){
   const c=legs[side],foot=srcRig[c.foot.name],q=wq(foot).toArray();
   const obs={phase:i/N,ankle:wpos(foot).toArray(),heel:soleWorld(refMeshes,c.heelPatch).toArray(),
    sole:soleWorld(refMeshes,c.patch).toArray(),toe:soleWorld(refMeshes,c.toePatch).toArray(),q};
   sourceSamples[side].push(obs);absoluteGround=Math.min(absoluteGround,obs.heel[1],obs.toe[1]);
  }
 }
 // The authored clip has a documented final <7% phase reset: smooth ONLY a verified seam.
 sourceSeamRepair={};
 for(const side of ['left','right']){
  const arr=sourceSamples[side],start=Math.floor(.93*N),a=arr[start],b=arr[0],last=arr[N-1];
  const jump=V(...last.ankle).distanceTo(V(...b.ankle));
  sourceSeamRepair[side]={terminalResetAnkleJump:jump,repaired:false};
  if(jump>.045){for(let i=start+1;i<N;i++){
   const t=(i-start)/(N-start),w=t*t*(3-2*t);
   for(const k of ['ankle','heel','sole','toe'])arr[i][k]=a[k].map((v,j)=>v*(1-w)+b[k][j]*w);
   arr[i].q=Q().fromArray(a.q).slerp(Q().fromArray(b.q),w).toArray();
  }sourceSeamRepair[side].repaired=true;}
 }
 sourceGround=absoluteGround;sourceGaits={left:inferContacts(sourceSamples.left),right:inferContacts(sourceSamples.right)};
 // Source-derived spatial travel per cycle; no artist-tuned stride/clearance parameters.
 const measuredTravel=['left','right'].map(side=>{
  const z=sourceSamples[side].map(s=>s.ankle[2]);return Math.max(...z)-Math.min(...z);
 });
 stride=(measuredTravel[0]+measuredTravel[1])*.5;
 if(!(stride>=.3&&stride<=1))throw Error('SOURCE_DERIVED_TRAVEL_OUT_OF_RANGE '+stride);
 updateMotionStatus();
 const phaseSeparation=mod1(sourceGaits.left.start-sourceGaits.right.start);
 if(phaseSeparation<.30||phaseSeparation>.70)throw Error('LEFT_RIGHT_CONTACT_TIMING_AMBIGUOUS '+phaseSeparation);
''')
# Original low-phase identifiers removed; preserve reference source and dispose source Mixer.
region(' const footPhases=Object.fromEntries(', ' ready=true;', ''' const footPhases=Object.fromEntries(Object.entries(sourceGaits).map(([side,g])=>
  [side,{contactStart:g.start,sourceStanceDuty:g.duty,threshold:g.threshold,seam:sourceSeamRepair[side]}]));
''')
once('legs[side]={side,chain:b,up,knee,bridge,foot,toe,patch,meshes:actorMeshes,soleLocal,upperLength,lowerLength,stanceQ:wq(foot),contactStart:0};',
     "const heelPatch=pickSolePatch(actorMeshes,foot),toePatch=pickSolePatch(actorMeshes,toe);\n  legs[side]={side,chain:b,up,knee,bridge,foot,toe,patch,heelPatch,toePatch,meshes:actorMeshes,soleLocal,upperLength,lowerLength};")
once('v0.1.11 · SHA ${SOURCE_SHA}', 'v0.1.12 SOURCE TASK-SPACE · SHA ${SOURCE_SHA}')
once('· low-foot phases ${JSON.stringify(footPhases)}', '· inferred heel/toe contact ${JSON.stringify(footPhases)}')
once("a.download='hareworks-woman-world-foot-ik-v0.1.11.json'", "a.download='hareworks-woman-source-world-ik-v0.1.12.json'")
once("status('REAL RIG ACTIVE · one moving actor · fixed-follow camera · world-locked skinned soles');", "status('MEASURED SOURCE GAIT ACTIVE · world support · two-bone IK · owner gait review pending');")
# There must not be a generated AnimationMixer driving the actor.
if 'new THREE.AnimationMixer(actor)' in s:raise RuntimeError('GENERATED_ACTOR_HAS_ANIMATION_MIXER')
if 'Math.sin(Math.PI*' in s:raise RuntimeError('GENERIC_SWING_SINE_RETAINED')
v.write_text(s)

html=target/'index.html';h=html.read_text()
h=h.replace('v0.1.11','v0.1.12').replace('Real World Foot IK','Measured Source Foot IK')
h=h.replace('One independently posed skinned Hareworks character walking','One source-measured, independently IK-solved skinned Hareworks character walking')
h=h.replace('Longer, lower swing by default; tune stride and clearance independently. Foot anchors and IK stay active.','Swing and heel-to-toe motion are reconstructed from the original Walking_Woman source, not parameter sliders. Physical contact and style resemblance are distinct gates.')
# Delete old synthetic-shape controls but retain world speed input.
a=h.index('<div class="bar" role="group" aria-label="Stride and foot clearance tuning">')
b=h.index('<div id="motionStatus"',a)
h=h[:a]+h[b:]
h=h.replace('Checking stride, clearance and cadence agreement...', 'Deriving measured gait and ground support...')
h=h.replace('Run 3-cycle skinned foot-pin audit','Audit source gait + skinned contacts')
h=h.replace('src="./viewer.mjs"','src="./viewer.mjs?build=v0.1.12"')
h=h.replace('The model moves in world Z;', 'The model moves in world Z;')
html.write_text(h)

# Only new-version paths may be written. Treat successful patch publication as pending human approval.
for p in ['viewer.mjs','index.html','foot-gait.mjs','foot-gait-test.mjs']:
    assert (target/p).is_file(),p
print(json.dumps({'patch':'SOURCE_MEASURED_GAIT_PATCHED','modelUnchanged':True,'viewerBytes':v.stat().st_size,'htmlBytes':html.stat().st_size}))
