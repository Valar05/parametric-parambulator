/* v0.1.10. ONE moving Walking_Woman. REAL world-fixed skinned-sole contacts.
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
import {WorldContact,mod1,clamp,swingProgress,nextStartDelta,followCamera} from './contact-core.mjs';
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
let ready=false,playing=true,speed=.52,phase=0,worldZ=0,frameTimer=performance.now(),accumulator=0,groundOffset=0,runFrames=0,report=null,lastStats=null;
let maxDrift=0,maxIK=0,maxPenetration=0,unreachable=0,contactCount=0,swingCount=0,transitions=0,lastAnchorLocations={},failedFrames=0;
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
function nominalLanding(side,phaseNow){const f=worldContacts[side],dtPhase=nextStartDelta(phaseNow,f.start),landingPhase=mod1(phaseNow+dtPhase);
 const current=independentPose(pelvisProfile,phaseNow*clipDuration),future=independentPose(pelvisProfile,landingPhase*clipDuration);
 const c=legs[side],H=wpos(c.up),offset=legAt(footProfile,side,landingPhase*clipDuration).ankleLocal;
 const yawFuture=future.pelvisYaw;const ankle=H.add(V(future.pelvis[0]-current.pelvis[0],future.pelvis[1]-current.pelvis[1],future.pelvis[2]-current.pelvis[2] +speed*clipDuration*dtPhase));ankle.add(V(...rotateY(offset,yawFuture)));
 const soleLocal=c.soleLocal.clone().multiply(c.foot.getWorldScale(V())).applyQuaternion(c.stanceQ);
 const target=ankle.add(soleLocal);target.y=0;return target.toArray();}
function contactTargets(){const out={};for(const side of ['left','right']){const c=worldContacts[side];const target=c.step({phase,nominalLanding:nominalLanding(side,phase),footLift:.12});out[side]=target;}return out}
function ankleForSole(c,worldSole,worldFootQ){const offset=c.soleLocal.clone().multiply(c.foot.getWorldScale(V())).applyQuaternion(worldFootQ);return worldSole.clone().sub(offset)}
function adjustReach(targets){let correction=0;for(const side of ['left','right']){const leg=legs[side],target=V(...targets[side].target),q=leg.stanceQ;
 const a=ankleForSole(leg,target,q),h=wpos(leg.up),r=leg.upperLength+leg.lowerLength-.014,d=h.distanceTo(a);correction=Math.max(correction,Math.max(0,d-r))}
 if(correction>0){const moved=Math.min(.14,correction+.002);rig.mixamorigHips.position.y-=moved;actor.updateMatrixWorld(true);if(correction>.14)unreachable++;}}
function solveLeg(side,worldSole,planted,footPhase){const c=legs[side],target=V(...worldSole),desiredQ=c.stanceQ.clone();
 if(!planted){const u=swingProgress(footPhase,worldContacts[side].start,worldContacts[side].duty);desiredQ.premultiply(Q().setFromAxisAngle(V(1,0,0),-.10*Math.sin(Math.PI*u)));}
 let desiredAnkle=ankleForSole(c,target,desiredQ),best=Infinity;
 for(let iter=0;iter<4;iter++){
  for(const b of c.chain)copyLocal(b,rest[b.name]);actor.updateMatrixWorld(true);
  const H=wpos(c.up),K0=wpos(c.knee),A0=wpos(c.foot),pole=legAt(footProfile,side,phase*clipDuration).poleLocal;
  const yaw=independentPose(pelvisProfile,phase*clipDuration).pelvisYaw;
  let knee;try{knee=V(...kneeFromTarget(H.toArray(),desiredAnkle.toArray(),c.upperLength,c.lowerLength,rotateY(pole,yaw)));}
  catch(e){const dir=desiredAnkle.clone().sub(H),max=c.upperLength+c.lowerLength-.005,min=Math.abs(c.upperLength-c.lowerLength)+.005;dir.setLength(clamp(dir.length(),min,max));desiredAnkle.copy(H).add(dir);unreachable++;knee=V(...kneeFromTarget(H.toArray(),desiredAnkle.toArray(),c.upperLength,c.lowerLength,rotateY(pole,yaw)));}
  turnToward(c.up,K0,knee);actor.updateMatrixWorld(true);
  turnToward(c.knee,wpos(c.foot),desiredAnkle);actor.updateMatrixWorld(true);
  setWorldQ(c.foot,desiredQ);actor.updateMatrixWorld(true);
  const actual=soleWorld(c.meshes,c.patch),e=target.clone().sub(actual);best=e.length();
  if(best<.0018)break;desiredAnkle.add(e.multiplyScalar(.95));
 }
 const actual=soleWorld(c.meshes,c.patch),drift=actual.distanceTo(target);
 if(planted){maxDrift=Math.max(maxDrift,drift);contactCount++;if(actual.y<-.012)maxPenetration=Math.max(maxPenetration,-actual.y)}else swingCount++;
 maxIK=Math.max(maxIK,drift);drawPins[side].position.copy(V(...worldSole));drawPins[side].visible=$('showContacts').checked;drawPins[side].material.color.setHex(planted?0x65f2b7:0xffb65f);
 return {planted,drift,sole:actual.toArray(),target:target.toArray(),anchor:worldContacts[side].anchor.slice(),reach:c.upperLength+c.lowerLength};
}
function physicsStep(dt){const cadence=speed<=0?0:speed/.52/clipDuration;
 phase=mod1(phase+cadence*dt);worldZ+=speed*dt;frameBody(phase);
 const targets=contactTargets();adjustReach(targets);const feet={};for(const side of ['left','right'])feet[side]=solveLeg(side,targets[side].target,targets[side].planted,phase);
 transitions=worldContacts.left.transitions+worldContacts.right.transitions;runFrames++;lastStats={phase,worldTravelZ:worldZ,speed,cadence,worldRootZ:actor.position.z,feet,transitions,maxSkinnedStanceDrift:maxDrift,maxSkinnedTargetError:maxIK,maxNewFloorPenetration:maxPenetration,reachAdjustments:unreachable,contactFrames:contactCount,swingFrames:swingCount,solvedIKPerFrame:true,generatedAnimationMixerCount:0};
 return lastStats;}
const cameraTarget=V();let stableOffset=V();function pinCamera(){if(!actor)return;const pinned=followCamera(actor.position.toArray(),cameraOffsets[view],.90);cameraTarget.fromArray(pinned.target);stableOffset.fromArray(cameraOffsets[view]);camera.position.fromArray(pinned.position);camera.up.set(0,1,0);camera.lookAt(cameraTarget);camera.updateProjectionMatrix();}
function renderMetrics(prefix='LIVE'){if(!lastStats)return;const feet=lastStats.feet;
 $('metrics').textContent=`${prefix} · WORLD-SPACE FOOT CONTACT / TRUE IK\nTravel Z ${worldZ.toFixed(3)} u · cycle ${(phase*100).toFixed(1)}% · speed ${speed.toFixed(2)} u/s\nLEFT ${feet.left.planted?'PINNED':'SWING'} sole drift ${feet.left.drift.toFixed(4)} u; RIGHT ${feet.right.planted?'PINNED':'SWING'} sole drift ${feet.right.drift.toFixed(4)} u\nMax stance skinned sole drift ${maxDrift.toFixed(5)} u · max target IK residual ${maxIK.toFixed(5)} u\nFloor penetration ${maxPenetration.toFixed(5)} u · reach adjustments ${unreachable}\nTouchdown transitions ${transitions}, contact samples ${contactCount}; generated clip mixer = 0\nCAMERA: pinned to actor world Z, stable height and angle. Ground markers stay world-fixed.`}
function clearStats(){maxDrift=0;maxIK=0;maxPenetration=0;unreachable=0;contactCount=0;swingCount=0;transitions=0;runFrames=0;lastStats=null;}
function initRun(){if(!ready)return;phase=0;worldZ=0;clearStats();frameBody(0);const m=skinned(actor),next={};for(const side of ['left','right']){const c=legs[side],sole=soleWorld(m,c.patch);next[side]=new WorldContact({side,start:c.contactStart,duty:.55,sole:sole.toArray(),groundY:0});}
 worldContacts=next;physicsStep(0);pinCamera();renderMetrics('RESET');}
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';status(playing?'RUNNING · world travel and anchored soles':'PAUSED · world contact anchors retained')};
$('reset').onclick=()=>{initRun();status('WORLD RUN RESET · actor, anchors and camera synchronized')};
$('speed').oninput=()=>{speed=Number($('speed').value);$('speedOut').textContent=speed.toFixed(2)+' u/s'};
$('showContacts').onchange=()=>{for(const side of ['left','right'])drawPins[side].visible=$('showContacts').checked};
for(const k of Object.keys(cameraOffsets))$(k).onclick=()=>{view=k;pinCamera()};
$('export').onclick=()=>{if(!report){status('Run real skinned foot-pin audit first.');return}const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='hareworks-woman-world-foot-ik-v0.1.10.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),6000)};
$('audit').onclick=async()=>{if(!ready)return;const was=playing;playing=false;status('Auditing 3 real world-travel cycles, 120 Hz and skinned sole patches…');const oldSpeed=speed;speed=.52;
 try{initRun();const n=Math.ceil(clipDuration*3*120);let worstPerFoot={left:0,right:0},anchorMaxStep=0,previous={left:null,right:null},sampled=[];
  for(let i=0;i<n;i++){const m=physicsStep(1/120);for(const side of ['left','right']){const f=m.feet[side];if(f.planted){worstPerFoot[side]=Math.max(worstPerFoot[side],f.drift);if(previous[side])anchorMaxStep=Math.max(anchorMaxStep,Math.hypot(...f.anchor.map((x,j)=>x-previous[side][j])));previous[side]=f.anchor.slice()}else previous[side]=null;}
   if(i%15===0)sampled.push({time:i/120,worldZ:m.worldTravelZ,phase:m.phase,left:m.feet.left,right:m.feet.right,cameraTrackingOffset:cameraOffsets[view]});if(i%35===0)await new Promise(requestAnimationFrame);}
  pinCamera();const cameraError=Math.abs((camera.position.z-actor.position.z)-cameraOffsets[view][2]);
  const pass=worstPerFoot.left<=.025&&worstPerFoot.right<=.025&&maxPenetration<=.020&&anchorMaxStep<=1e-8&&worldZ>.9&&cameraError<1e-8&&unreachable===0;
  report={schema:'hareworks-woman-world-pinned-ik-v0.1.10',sourceSha256:SOURCE_SHA,sourceClip:CLIP,rigBones:74,generatedAnimationMixerCount:0,calibrationOnlySourceMixer:true,oneVisibleCharacter:true,rootMovementIsWorldTravel:true,cameraFixedFollow:true,stanceAnchorCoordinateSystem:'WORLD',contactPatch:'actual skinned mesh.getVertexPosition() samples',physicsRateHz:120,sampledFrames:n,worldTravelZ:worldZ,referenceRigWasNotDisplayed:true,solver:'two-bone knee IK + world foot orientation + iterative skinned sole witness residual correction',maxSkinnedSoleDriftPerSide:worstPerFoot,maximumContactAnchorTranslation:anchorMaxStep,maxFootPenetration:maxPenetration,maxIKResidual:maxIK,reachAdjustments:unreachable,cameraWorldFollowError:cameraError,touchdownTransitions:transitions,status:pass?'WORLD_IK_GATE_PASS_OWNER_REVIEW_PENDING':'WORLD_IK_GATE_WARN_OWNER_REVIEW_REQUIRED',ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,observations:sampled};
  $('metrics').textContent=`${report.status}\nREAL skinned soles: L ${worstPerFoot.left.toFixed(5)} u; R ${worstPerFoot.right.toFixed(5)} u (limit 0.025)\nFoot anchors max motion DURING stance ${anchorMaxStep.toFixed(9)} u (required 0)\nRoot traveled ${worldZ.toFixed(3)} units; camera follow error ${cameraError.toExponential(2)}\nFoot penetration ${maxPenetration.toFixed(5)}; reach adjustments ${unreachable}; ${n} frames at 120 Hz.\nThe approved v0.1.9 is not modified. Export JSON for per-frame world evidence.`;
  try{const response=await fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(report)});if(!response.ok)throw Error('HTTP_'+response.status);const receipt=await response.json();status(report.status+' · phone evidence saved '+receipt.sha256.slice(0,12))}catch(e){status(report.status+' · autosave unavailable '+e.message+' · Export evidence available')}
 }catch(e){status('IK_AUDIT_ERROR '+e.message);console.error(e)}finally{const summary=$('metrics').textContent;speed=oldSpeed;initRun();$('metrics').textContent=summary;playing=was;$('play').textContent=playing?'Pause':'Play';}}
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
  legs[side]={side,chain:b,up,knee,bridge,foot,toe,patch,meshes:actorMeshes,soleLocal,upperLength,lowerLength,stanceQ:wq(foot),contactStart:0};patches[side]=patch;}
 // Calibrate source contact LOW phases from REAL skinned patch vertices,
 // not the animated foot pivot. Runtime NEVER consults these source clips.
 const lows={left:{y:Infinity,phase:0},right:{y:Infinity,phase:0}};let absoluteGround=Infinity;
 for(let i=0;i<240;i++){mixer.setTime(clipDuration*i/240);source.updateMatrixWorld(true);for(const side of ['left','right']){const c=legs[side],y=soleWorld(refMeshes,c.patch).y;absoluteGround=Math.min(absoluteGround,y);if(y<lows[side].y){lows[side]={y,phase:i/240}}}}
 for(const side of ['left','right']){const c=legs[side];c.contactStart=mod1(lows[side].phase-.23);mixer.setTime(clipDuration*lows[side].phase);source.updateMatrixWorld(true);c.stanceQ=wq(srcRig[c.foot.name]);}
 groundOffset=absoluteGround;mixer.stopAllAction();mixer.uncacheRoot(source); // calibration only, NEVER drives actor
 actor.position.y=-groundOffset;scene.add(actor);actor.updateMatrixWorld(true);
 const footPhases=Object.fromEntries(Object.entries(lows).map(([side,v])=>[side,{lowPhase:v.phase,stanceStart:legs[side].contactStart}]));
 ready=true;initRun();pinCamera();status('REAL RIG ACTIVE · one moving actor · fixed-follow camera · world-locked skinned soles');
 $('identity').textContent=`v0.1.10 · SHA ${SOURCE_SHA} · exact Walking_Woman · 74 bones · two-bone world IK · one actor · root WORLD travel · source mixer CALIBRATION ONLY · low-foot phases ${JSON.stringify(footPhases)} · commit ${new URLSearchParams(location.search).get('commit')||'unknown'} · entry ${new URLSearchParams(location.search).get('scriptSha')||'unknown'}`;
}catch(e){status('REAL_MODEL_CALIBRATION_BLOCKED '+e.message);console.error(e)}
