/* v0.1.11. ONE moving Walking_Woman. REAL world-fixed skinned-sole contacts.
   Generated actor has NO AnimationMixer, NO per-frame original clip sampling,
   NO source leg joint tracks. Pelvis+upper motions are fitted once at startup.
   Leg joint rotations are freshly computed from anchored world foot targets. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {fitSourceAnchoredTrack,evalSourceAnchoredTrack} from '../v0.1.9/upper-anchor.mjs';
import {independentPose,validateProfile} from '../v0.1.2/pose-kernel.mjs';
import {legAt,rotateY,validateFootProfile} from '../v0.1.3/foot-kernel.mjs';
import {kneeFromTarget} from './ik-core.mjs';
import {mod1,clamp,followCamera,cadenceFor} from './contact-core.mjs';
import {inferContacts,sourceAt,SourceFootContact} from './foot-gait.mjs';
const $=id=>document.getElementById(id),V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z),Q=()=>new THREE.Quaternion();
const SOURCE_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const MODEL='../../../assets/hareworks/Hareworks-nine-clips.glb',BONES=74,CLIP='Walking_Woman';
const names={left:['mixamorigLeftUpLeg','mixamorigLeftLeg','Bone_017','mixamorigLeftFoot','mixamorigLeftToeBase'],right:['mixamorigRightUpLeg','mixamorigRightLeg','Bone_013','mixamorigRightFoot','mixamorigRightToeBase']};
const scene=new THREE.Scene();scene.background=new THREE.Color('#102030');scene.add(new THREE.HemisphereLight(0xf3f9ff,0x34485d,2.5));
const sun=new THREE.DirectionalLight(0xffffff,3.1);sun.position.set(-4,8,4);scene.add(sun);
const ground=new THREE.GridHelper(180,180,0x6b8696,0x354858);scene.add(ground);
for(let i=0;i<24;i++){const marker=new THREE.Mesh(new THREE.BoxGeometry(.075,.025,.075),new THREE.MeshBasicMaterial({color:i%2?0x42768b:0x6ea9a9}));marker.position.set(-1.3,.015,i*1.5);scene.add(marker)}
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-3,3,2,-2,.01,300);const cameraOffsets={oblique:[-4.8,3.15,5.7],side:[-6.4,2.75,0],front:[0,2.9,7.0],top:[-.01,8,.01]};let view='oblique';
function resize(){const w=Math.max(300,$('stage').clientWidth),h=Math.max(310,Math.min(690,Math.round(w*.76)));renderer.setSize(w,h,false);camera.top=2.2;camera.bottom=-2.2;camera.left=-2.2*w/h;camera.right=-camera.left;camera.updateProjectionMatrix()}
addEventListener('resize',resize);resize();const status=x=>$('status').textContent=x;
let actor=null,rig=null,legs=null,fit=null,pelvisProfile=null,footProfile=null,clipDuration=0,rest=null,patches=null,worldContacts=null,footOrient=null;
let ready=false,playing=true,speed=.52,stride=.66,phase=0,worldZ=0,frameTimer=performance.now(),accumulator=0,groundOffset=0,runFrames=0,report=null,lastStats=null;
let maxDrift=0,maxIK=0,maxPenetration=0,unreachable=0,contactCount=0,swingCount=0,transitions=0,failedFrames=0;
let sourceSamples=null,sourceGaits=null,sourceGround=0,witnessCache=null,sourceSeamRepair={},shapeSum=0,shapeCount=0;
const drawPins={};for(const side of ['left','right']){const m=new THREE.Mesh(new THREE.SphereGeometry(.045,12,10),new THREE.MeshBasicMaterial({color:side==='left'?0x6bf5bf:0xb8fa83,depthTest:false}));m.renderOrder=15;scene.add(m);drawPins[side]=m;}
const wpos=b=>b.getWorldPosition(V());const wq=b=>b.getWorldQuaternion(Q());
function bonesOf(o){let found={};o.traverse(b=>{if(b.isBone){if(found[b.name])throw Error('DUPLICATE_BONE_'+b.name);found[b.name]=b}});if(Object.keys(found).length!==BONES)throw Error('EXPECTED_74_JOINTS_GOT_'+Object.keys(found).length);return found}
const skinned=o=>{let a=[];o.traverse(x=>{if(x.isSkinnedMesh){x.frustumCulled=false;a.push(x)}});return a};
function pickSolePatch(meshes,foot){const anchor=wpos(foot),near=[];
 for(let mi=0;mi<meshes.length;mi++){const m=meshes[mi],attribute=m.geometry.getAttribute('position');if(!attribute)continue;
  const step=Math.max(1,Math.floor(attribute.count/16000));for(let j=0;j<attribute.count;j+=step){const p=m.getVertexPosition(j,V());m.localToWorld(p);const d=p.distanceToSquared(anchor);if(d<.32*.32)near.push({mi,j,point:p.toArray(),d})}}
 if(near.length<15)throw Error('SKINNED_SOLE_VERTICES_NOT_FOUND_'+foot.name+'_'+near.length);
 near.sort((a,b)=>a.d-b.d);const candidates=near.slice(0,180),low=Math.min(...candidates.map(a=>a.point[1]));
 const chosen=candidates.filter(p=>p.point[1]<=low+.02).slice(0,20);if(chosen.length<4)throw Error('SOLE_PATCH_TOO_SMALL_'+foot.name);
 return {indexes:chosen.map(p=>({mi:p.mi,j:p.j})),low,count:chosen.length};
}
function soleWorld(meshes,patch){const out=V();for(const {mi,j} of patch.indexes){const m=meshes[mi];if(!m)throw Error('SOLE_SKINNED_MESH_MISMATCH');const p=m.getVertexPosition(j,V());m.localToWorld(p);out.add(p)}return out.multiplyScalar(1/patch.indexes.length)}
function witnessWorld(c,kind){
 if(kind==='ankle')return wpos(c.foot);
 const patch=kind==='heel'?c.heelPatch:kind==='toe'?c.toePatch:c.patch;
 return soleWorld(c.meshes,patch);
}
function measuredFootQ(s){return Q().fromArray(s.q0).slerp(Q().fromArray(s.q1),s.qt).normalize()}
function setWorldQ(b,desired){b.quaternion.copy(wq(b.parent).invert().multiply(desired)).normalize()}
function turnToward(b,from,to){const origin=wpos(b),a=from.clone().sub(origin),c=to.clone().sub(origin);
 if(a.lengthSq()<1e-10||c.lengthSq()<1e-10)throw Error('IK_ZERO_BONE_VECTOR_'+b.name);
 const delta=Q().setFromUnitVectors(a.normalize(),c.normalize());setWorldQ(b,delta.multiply(wq(b)))}
const copyLocal=(b,p)=>{b.position.fromArray(p.p);b.quaternion.fromArray(p.q);b.scale.fromArray(p.s)};
function captureSeed(){const out={};for(const [name,b] of Object.entries(rig))out[name]={p:b.position.toArray(),q:b.quaternion.toArray(),s:b.scale.toArray()};return out}
function sampleFitted(source,mixer,sourceRig,count=120){const tracked=[sourceRig.mixamorigHips];sourceRig.mixamorigSpine.traverse(b=>{if(b.isBone)tracked.push(b)});
 const data=new Map(tracked.map(b=>[b.name,[]]));for(let i=0;i<count;i++){mixer.setTime(i*clipDuration/count);source.updateMatrixWorld(true);for(const b of tracked)data.get(b.name).push({quaternion:b.quaternion.toArray(),position:b.position.toArray()})}
 mixer.setTime(0);source.updateMatrixWorld(true);return Object.fromEntries([...data.entries()].map(([name,samples])=>[name,fitSourceAnchoredTrack(samples,12)]))}
function frameBody(p){const fitPhase=mod1(p),pelvis=independentPose(pelvisProfile,fitPhase*clipDuration),zero=independentPose(pelvisProfile,0);
 for(const [name,r] of Object.entries(rest))if(name in rig&&!(name in fit)&&name!=='mixamorigHips')copyLocal(rig[name],r);
 for(const [name,track] of Object.entries(fit)){const b=rig[name],s=evalSourceAnchoredTrack(track,fitPhase,12,1);b.quaternion.fromArray(s.quaternion).normalize();b.position.fromArray(s.position)}
 const hip=rig.mixamorigHips,p0=rest.mixamorigHips.p;hip.position.set(p0[0]+pelvis.pelvis[0]-zero.pelvis[0],p0[1]+pelvis.pelvis[1]-zero.pelvis[1],p0[2]+pelvis.pelvis[2]-zero.pelvis[2]);
 actor.position.z=worldZ;actor.position.y=-groundOffset;actor.updateMatrixWorld(true);}
function measuredWitnesses(){const out={};for(const side of ['left','right']){
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
const cameraTarget=V();let stableOffset=V();function pinCamera(){if(!actor)return;const pinned=followCamera(actor.position.toArray(),cameraOffsets[view],.90);cameraTarget.fromArray(pinned.target);stableOffset.fromArray(cameraOffsets[view]);camera.position.fromArray(pinned.position);camera.up.set(0,1,0);camera.lookAt(cameraTarget);camera.updateProjectionMatrix();}
function renderMetrics(prefix='LIVE'){if(!lastStats)return;const feet=lastStats.feet;
 $('metrics').textContent=`${prefix} · SOURCE-MEASURED WALKING_WOMAN · WORLD IK\nTravel Z ${worldZ.toFixed(3)} u, phase ${(phase*100).toFixed(1)}%, cadence ${cadenceFor(speed,stride).toFixed(3)} cycles/s\nLEFT ${feet.left.pivot} ${feet.left.planted?'PLANTED':'SWING'}, drift ${feet.left.drift.toFixed(4)} u\nRIGHT ${feet.right.pivot} ${feet.right.planted?'PLANTED':'SWING'}, drift ${feet.right.drift.toFixed(4)} u\nSkinned support error ${maxDrift.toFixed(5)} u, floor penetration ${maxPenetration.toFixed(5)} u\nSource ankle RMS ${lastStats.sourceAnkleRms.toFixed(5)} u; knee reach warnings ${unreachable}\nContact transitions ${transitions}; source stance L ${(sourceGaits.left.duty*100).toFixed(1)}%, R ${(sourceGaits.right.duty*100).toFixed(1)}%\nANIMATION MIXER ON VISIBLE ACTOR: ZERO · source joints NOT replayed`;
}
function clearStats(){maxDrift=0;maxIK=0;maxPenetration=0;unreachable=0;contactCount=0;swingCount=0;transitions=0;runFrames=0;lastStats=null;shapeSum=0;shapeCount=0;}
function initRun(){if(!ready)return;
 phase=0;worldZ=0;clearStats();frameBody(0);witnessCache=measuredWitnesses();const next={};
 for(const side of ['left','right'])next[side]=new SourceFootContact({samples:sourceSamples[side],gait:sourceGaits[side],
  sourceGround,readWitness:k=>witnessCache[side][k]});
 worldContacts=next;physicsStep(0);pinCamera();renderMetrics('RESET');
}
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';status(playing?'RUNNING · world travel and anchored soles':'PAUSED · world contact anchors retained')};
$('reset').onclick=()=>{initRun();status('WORLD RUN RESET · actor, anchors and camera synchronized')};
$('speed').oninput=()=>{speed=Number($('speed').value);$('speedOut').textContent=speed.toFixed(2)+' u/s';updateMotionStatus()};
function updateMotionStatus(){
 $('motionStatus').textContent=`SOURCE-DERIVED FOOT PATH · ${stride.toFixed(3)} u travel/cycle · ${cadenceFor(speed,stride).toFixed(3)} cycles/s · no synthetic foot lift`;
}
updateMotionStatus();
$('showContacts').onchange=()=>{for(const side of ['left','right'])drawPins[side].visible=$('showContacts').checked};
for(const k of Object.keys(cameraOffsets))$(k).onclick=()=>{view=k;pinCamera()};
$('export').onclick=()=>{if(!report){status('Run real skinned foot-pin audit first.');return}const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='hareworks-woman-source-world-ik-v0.1.12.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),6000)};
$('audit').onclick=async()=>{if(!ready)return;const was=playing;playing=false;
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
  $('metrics').textContent=`${report.status}\nCONTACT: heel/sole/toe anchors L ${worst.left.toFixed(5)}, R ${worst.right.toFixed(5)} u (limit .025)\nSource ankle RMS ${report.sourceAnkleRms.toFixed(5)} u (advisory, NOT gait approval)\nFloor intrusion ${maxPenetration.toFixed(5)} u; IK warnings ${unreachable}\n3 measured cycles, 120 Hz, traveling root ${worldZ.toFixed(3)} u\nSTYLE GATE: must resemble v0.1.9 Walking_Woman in owner's inspection`;
  try{const response=await fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(report)});
   if(!response.ok)throw Error('HTTP_'+response.status);const receipt=await response.json();status(report.status+' · evidence saved '+receipt.sha256.slice(0,12));}
  catch(e){status(report.status+' · autosave unavailable '+e.message+' · Export still works')}
 }catch(e){status('SOURCE_GAIT_AUDIT_ERROR '+e.message);console.error(e)}
 finally{const summary=$('metrics').textContent;speed=oldSpeed;initRun();$('metrics').textContent=summary;playing=was;$('play').textContent=playing?'Pause':'Play';}
};
function frame(now){requestAnimationFrame(frame);const delta=Math.min(.055,Math.max(0,(now-frameTimer)/1000));frameTimer=now;
 if(ready&&playing){accumulator=Math.min(.06,accumulator+delta);try{let count=0;while(accumulator>=1/120&&count<9){physicsStep(1/120);accumulator-=1/120;count++}pinCamera();if(runFrames%30===0)renderMetrics();}catch(e){playing=false;failedFrames++;status('IK_RUNTIME_WARN '+e.message+' · last valid model remains visible');console.error(e)}}renderer.render(scene,camera);}
requestAnimationFrame(frame);
try{
 const response=await fetch(MODEL,{cache:'no-store'});if(!response.ok)throw Error('SOURCE_HTTP_'+response.status);const bytes=await response.arrayBuffer();if(bytes.byteLength!==6784896)throw Error('SOURCE_SIZE_'+bytes.byteLength);
 const sha=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');if(sha!==SOURCE_SHA)throw Error('SOURCE_SHA_MISMATCH '+sha);
 const [p,f]=await Promise.all([fetch('../v0.1.2/motion-profile.json',{cache:'no-store'}).then(x=>x.json()),fetch('../v0.1.3/foot-profile.json',{cache:'no-store'}).then(x=>x.json())]);validateProfile(p);validateFootProfile(f);pelvisProfile=p;footProfile=f;
 const gltf=await new GLTFLoader().parseAsync(bytes,new URL('../../../assets/hareworks/',import.meta.url).href);const sourceClip=gltf.animations.find(a=>a.name===CLIP);if(!sourceClip||gltf.animations.length!==9)throw Error('SOURCE_WALKING_WOMAN_REQUIRED');clipDuration=sourceClip.duration;
 const source=cloneSkeleton(gltf.scene);actor=cloneSkeleton(gltf.scene);const srcRig=bonesOf(source);rig=bonesOf(actor);const mixer=new THREE.AnimationMixer(source);mixer.clipAction(sourceClip).reset().play();mixer.setTime(0);source.updateMatrixWorld(true);
 for(const [name,b] of Object.entries(rig)){const a=srcRig[name];b.position.copy(a.position);b.quaternion.copy(a.quaternion);b.scale.copy(a.scale)}actor.updateMatrixWorld(true);rest=captureSeed();
 fit=sampleFitted(source,mixer,srcRig);mixer.setTime(0);source.updateMatrixWorld(true);
 const actorMeshes=skinned(actor),refMeshes=skinned(source);if(actorMeshes.length!==refMeshes.length||actorMeshes.length<1)throw Error('SKINNED_MESH_1_TO_1_REQUIRED');
 legs={};patches={};for(const [side,arr] of Object.entries(names)){const b=arr.map(n=>rig[n]);if(b.some(x=>!x))throw Error('LEG_JOINTS_MISSING_'+side);const [up,knee,bridge,foot,toe]=b;
  if(up.parent!==rig.mixamorigHips||knee.parent!==up||bridge.parent!==knee||foot.parent!==bridge||toe.parent!==foot)throw Error('LEG_CHAIN_TOPOLOGY_'+side);
  const patch=pickSolePatch(actorMeshes,foot),sole=soleWorld(actorMeshes,patch),soleLocal=foot.worldToLocal(sole.clone());
  const upperLength=wpos(up).distanceTo(wpos(knee)),lowerLength=wpos(knee).distanceTo(wpos(foot));if(upperLength<.20||lowerLength<.20)throw Error('ANATOMICAL_LINKS_INVALID_'+side);
  if(Math.abs(upperLength-footProfile[side].upperLength)>.009||Math.abs(lowerLength-footProfile[side].lowerLength)>.009)throw Error('SOURCE_FOOT_PROFILE_LENGTH_MISMATCH_'+side);
  const heelPatch=pickSolePatch(actorMeshes,foot),toePatch=pickSolePatch(actorMeshes,toe);
  legs[side]={side,chain:b,up,knee,bridge,foot,toe,patch,heelPatch,toePatch,meshes:actorMeshes,soleLocal,upperLength,lowerLength};patches[side]=patch;}
 // Measure actual heel/toe/sole/ankle positions and orientation from the immutable source clip.
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
 groundOffset=absoluteGround;mixer.stopAllAction();mixer.uncacheRoot(source); // calibration only, NEVER drives actor
 actor.position.y=-groundOffset;scene.add(actor);actor.updateMatrixWorld(true);
 const footPhases=Object.fromEntries(Object.entries(sourceGaits).map(([side,g])=>
  [side,{contactStart:g.start,sourceStanceDuty:g.duty,threshold:g.threshold,seam:sourceSeamRepair[side]}]));
 ready=true;initRun();pinCamera();status('MEASURED SOURCE GAIT ACTIVE · world support · two-bone IK · owner gait review pending');
 $('identity').textContent=`v0.1.12 SOURCE TASK-SPACE · SHA ${SOURCE_SHA} · exact Walking_Woman · 74 bones · two-bone world IK · one actor · root WORLD travel · source mixer CALIBRATION ONLY · inferred heel/toe contact ${JSON.stringify(footPhases)} · commit ${new URLSearchParams(location.search).get('commit')||'unknown'} · entry ${new URLSearchParams(location.search).get('scriptSha')||'unknown'}`;
}catch(e){status('REAL_MODEL_CALIBRATION_BLOCKED '+e.message);console.error(e)}
