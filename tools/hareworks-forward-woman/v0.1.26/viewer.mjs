/* Hareworks v0.1.26: source-authored Cautious_Crouch_Walk_Left, procedural generated rig.
 * NO Walking_Woman lateral guess. NO backward-only direction-dispatcher.
 * A/B shows only ONE rig at a time. Original source rig has an AnimationMixer
 * for comparison; generated rig has ZERO source animation actions. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {ROOT,CLIPS,calibrate,pose,angleDeg} from './sidestep-core.mjs';
import {sourceContactWindow,isSourcePlanted,projectedSourceKnee,travelPhaseRate,distance} from './left-contact.mjs';
const $=x=>document.getElementById(x),V=()=>new THREE.Vector3(),Q=()=>new THREE.Quaternion();
const MODEL='../../../assets/hareworks/Hareworks-nine-clips.glb';
const SOURCE_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const SIZE=6784896,N=720,CONTACT_MAX_CORRECTION=.085,KNEE_MAX_CORRECTION=.035;
const limbs={left:['mixamorigLeftUpLeg','mixamorigLeftLeg','mixamorigLeftFoot'],right:['mixamorigRightUpLeg','mixamorigRightLeg','mixamorigRightFoot']};
const scene=new THREE.Scene();scene.background=new THREE.Color('#142231');scene.add(new THREE.HemisphereLight(0xeaf6ff,0x42576b,2.5));
const sunlight=new THREE.DirectionalLight(0xffffff,3.3);sunlight.position.set(-4,8,6);scene.add(sunlight);
const grid=new THREE.GridHelper(240,240,0x608ba7,0x2d4357);scene.add(grid);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-3,3,2,-2,.01,300),orbit=new OrbitControls(camera,renderer.domElement);orbit.enablePan=false;orbit.enableDamping=true;orbit.dampingFactor=.1;orbit.minZoom=.55;orbit.maxZoom=4;
const views={oblique:[-3.8,2.8,5.0],front:[0,2.6,6.5],side:[-6.5,2.5,0],top:[-.01,8,.01]};
let currentView='front',cameraTracked=V(0,.9,0);
function cameraAt(name){currentView=name;let at=actor?actor.position.clone().add(V(0,.9,0)):V(0,.9,0);cameraTracked.copy(at);orbit.target.copy(at);camera.position.copy(at).add(V(...views[name]));camera.up.set(0,1,0);orbit.update();}
function follow(){if(!actor)return;const to=actor.position.clone().add(V(0,.9,0)),step=to.sub(cameraTracked);orbit.target.add(step);camera.position.add(step);cameraTracked.add(step);}
function resize(){let w=Math.max(300,$('stage').clientWidth),h=Math.max(320,Math.min(720,Math.round(w*.78)));renderer.setSize(w,h,false);camera.top=2.4;camera.bottom=-2.4;camera.left=-2.4*w/h;camera.right=-camera.left;camera.updateProjectionMatrix();}
window.addEventListener('resize',resize);resize();
let source=null,actor=null,sourceRig=null,actorRig=null,sourceMixer=null,sourceClips={},snapshots={},plans={},sourceContacts={},ground=0;
let phase=0,cycles=0,worldX=0,playing=true,speed=1.23,lastTime=performance.now(),ready=false,frameCount=0;
let mode='procedural',contactLock={left:null,right:null},contactFlags={left:false,right:false},maxAnchorDrift=0,maxKneeShift=0,maxContactError=0,skippedCorrections=0,lastFailure='',lastStats=null,lastAudit=null;
let worldStride=0,duration=0,referenceClip=CLIPS[1];
const status=x=>$('status').textContent=x;
cameraAt(currentView);
const wpos=b=>b.getWorldPosition(V()),wq=b=>b.getWorldQuaternion(Q());
function rig(root){let out={};root.traverse(o=>{if(o.isBone){if(out[o.name])throw Error('DUPLICATE_BONE_'+o.name);out[o.name]=o;}});if(Object.keys(out).length!==74||!out[ROOT])throw Error('LEFT_SOURCE_NOT_74_BONES');return out;}
function setWorldQ(b,q){b.quaternion.copy(wq(b.parent).invert().multiply(q)).normalize();}
function aimJoint(b,from,to){let org=wpos(b),u=from.clone().sub(org),v=to.clone().sub(org);if(u.lengthSq()<1e-12||v.lengthSq()<1e-12)throw Error('LEFT_IK_ZERO_VECTOR');let q=Q().setFromUnitVectors(u.normalize(),v.normalize());setWorldQ(b,q.multiply(wq(b)));}
function snapshot(name){const clip=sourceClips[name],clone=cloneSkeleton(source),bones=rig(clone),mixer=new THREE.AnimationMixer(clone);mixer.clipAction(clip).reset().play();const result={name,sampleCount:N,duration:clip.duration,bones:{}};
 for(const key of Object.keys(bones))result.bones[key]={pos:[],quat:[],scale:[]};
 for(let i=0;i<N;i++){mixer.setTime(clip.duration*i/N);clone.updateMatrixWorld(true);for(const [key,b] of Object.entries(bones)){let o=result.bones[key];o.pos.push(b.position.toArray());o.quat.push(b.quaternion.toArray());o.scale.push(b.scale.toArray());}}
 const tr=clip.tracks.find(t=>t.name===ROOT+'.position');if(tr){let n=tr.times.length,size=tr.getValueSize();result.terminalRootTrack={lastTime:tr.times[n-1],lastPosition:Array.from(tr.values.slice((n-1)*size,n*size))};}
 return result;}
function sampleFootTravel(gltf){const clip=sourceClips[CLIPS[0]],model=cloneSkeleton(gltf.scene),bones=rig(model),m=new THREE.AnimationMixer(model);m.clipAction(clip).reset().play();let out={left:[],right:[]};
 for(let i=0;i<N;i++){m.setTime(clip.duration*i/N);model.updateMatrixWorld(true);for(let side of ['left','right'])out[side].push({ankle:wpos(bones[limbs[side][2]]).toArray()});}
 return out;}
function setPose(targetBones,snapshot,plan,p){const result=pose(snapshot,plan,p);for(const [name,part] of Object.entries(result.bones)){let b=targetBones[name];b.position.fromArray(part.position);b.quaternion.fromArray(part.quaternion).normalize();b.scale.fromArray(part.scale);}return result;}
function sourceAt(q){sourceMixer.stopAllAction();sourceMixer.clipAction(sourceClips[referenceClip]).reset().play();sourceMixer.setTime(((q%1)+1)%1*sourceClips[referenceClip].duration);source.updateMatrixWorld(true);}
function resetContact(){contactLock={left:null,right:null};contactFlags={left:false,right:false};maxAnchorDrift=0;maxKneeShift=0;maxContactError=0;skippedCorrections=0;lastFailure='';}
function applyIK(side,target){const [un,kn,fn]=limbs[side],up=actorRig[un],knee=actorRig[kn],foot=actorRig[fn];const H=wpos(up),K=wpos(knee),A=wpos(foot),d=A.distanceTo(target);maxContactError=Math.max(maxContactError,d);
 if(d>CONTACT_MAX_CORRECTION){skippedCorrections++;lastFailure='SOURCE_CONTACT_X_ERROR_'+side+'_'+d.toFixed(4);return false;}
 // Correct the source-authored leg without importing last frame's pole or a
 // changing left/right knee steering signal. The reference curve is rebuilt
 // from SOURCE every step, and any excessive correction is rejected visibly.
 const ik=projectedSourceKnee(H.toArray(),K.toArray(),A.toArray(),target.toArray());
 if(!ik.valid||ik.sourceKneeDisplacement>KNEE_MAX_CORRECTION){skippedCorrections++;lastFailure='SOURCE_KNEE_ENVELOPE_'+side+'_'+(ik.sourceKneeDisplacement??ik.reason);return false;}
 const footQ=wq(foot).clone();aimJoint(up,K,V(...ik.knee));actor.updateMatrixWorld(true);aimJoint(knee,wpos(foot),target);actor.updateMatrixWorld(true);setWorldQ(foot,footQ);actor.updateMatrixWorld(true);
 maxKneeShift=Math.max(maxKneeShift,ik.sourceKneeDisplacement);return true;
}
function poseProcedural(p,rootX,{correct=true}={}){setPose(actorRig,snapshots[CLIPS[1]],plans[CLIPS[1]],p);actor.position.set(rootX,0,0);actor.updateMatrixWorld(true);
 const ret={};for(const side of ['left','right']){
  let confidence=sourceContacts[side].method==='ANALYTIC_SOURCE_GROUND_VELOCITY';
  let pin=isSourcePlanted(p,sourceContacts[side]),foot=actorRig[limbs[side][2]],actual=wpos(foot),entry=contactLock[side];
  if(correct){if(pin&&!contactFlags[side]){entry={world:actual.clone(),phase:cycles};contactLock[side]=entry;}if(!pin)contactLock[side]=null;
   contactFlags[side]=pin;if(pin&&entry){let settled=confidence?applyIK(side,entry.world):false;if(!confidence)lastFailure='SOURCE_LEFT_CONTACT_UNVERIFIED_'+side;actual=wpos(foot);maxAnchorDrift=Math.max(maxAnchorDrift,actual.distanceTo(entry.world));ret[side]={planted:true,drift:actual.distanceTo(entry.world),solverApplied:settled,foot:actual.toArray(),anchor:entry.world.toArray()};}
   else ret[side]={planted:false,drift:null,solverApplied:false,foot:actual.toArray()};}
  else ret[side]={planted:pin,drift:null,solverApplied:false,foot:actual.toArray()};
 }
 return ret;}
function redraw({physics=true}={}){if(!ready)return;
 const p=((cycles%1)+1)%1;phase=p;worldX=cycles*worldStride;lastStats=poseProcedural(p,worldX,{correct:physics&&mode==='procedural'});
 if(mode==='source'){sourceAt(p);source.position.set(referenceClip===CLIPS[0]?Math.floor(cycles)*worldStride:worldX,0,0);source.visible=true;actor.visible=false;}else{source.visible=false;actor.visible=true;}
 source.updateMatrixWorld(true);actor.updateMatrixWorld(true);follow();$('phaseOut').textContent=(p*100).toFixed(1)+'%';$('phase').value=Math.round(p*1000);
 if(frameCount++%30===0)metrics();}
function metrics(){if(!ready)return;const state=mode==='source'?'SOURCE_ANIMATION_REFERENCE__NOT_GENERATED':skippedCorrections?'PROCEDURAL_LEFT_SOURCE_CORRECTION_WARN':'PROCEDURAL_LEFT_SOURCE_DERIVED';
 $('metrics').textContent=`${state}\nOriginal source: Cautious_Crouch_Walk_Left_inplace · generated rig source mixer=0\nMeasured authored lateral travel ${worldStride.toFixed(4)} u/cycle; actual X ${worldX.toFixed(4)} u; speed ${speed.toFixed(2)} u/s\nGenerated cadence ${(speed/worldStride).toFixed(3)} cycles/s · source period ${duration.toFixed(4)} s\nLeft contact ${JSON.stringify(sourceContacts.left)}\nRight contact ${JSON.stringify(sourceContacts.right)}\nWorld-ankle anchor max residual ${maxAnchorDrift.toFixed(4)} u; max permitted correction ${CONTACT_MAX_CORRECTION.toFixed(3)} u\nRejected IK corrections ${skippedCorrections}; source knee max adjustment ${maxKneeShift.toFixed(4)} u\n${lastFailure||'No source-contact conflict yet'}\nOriginal v0.1.24 forward/backward and v0.2.7 source comparison untouched.\nWhole-body source parity is independent of foot-contact success. Owner acceptance PENDING.`;}
function reset(){cycles=0;worldX=0;resetContact();if(ready){redraw();cameraAt('front');}}
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';};
$('reset').onclick=()=>reset();
$('speed').oninput=()=>{speed=Number($('speed').value);$('speedOut').textContent=speed.toFixed(2)+' u/s';};
$('direction').onchange=()=>{
 const selected=$('direction').value;if(selected==='left')return;
 if(!['forward','backward'].includes(selected))throw Error('UNKNOWN_DIRECTION_'+selected);
 const u=new URL('../v0.1.24/index.html',location.href);u.searchParams.set('move',selected);u.searchParams.set('terrain','flat');
 location.assign(u.toString()); // Navigation to immutable old slot, not a live blend or a new pose.
};
$('mode').onchange=()=>{mode=$('mode').value;resetContact();redraw();status(mode==='source'?'ORIGINAL IN-PLACE LEFT CLIP: SOURCE ANIMATION REFERENCE':'PROCEDURAL LEFT: MATHEMATICAL 74-BONE GAIT + WORLD-X CONTACT IK');};
$('reference').onchange=()=>{referenceClip=$('reference').value;redraw();};
$('phase').oninput=()=>{playing=false;$('play').textContent='Play';cycles=Math.floor(cycles)+Number($('phase').value)/1000;resetContact();redraw({physics:false});};
for(const key of Object.keys(views))$(key).onclick=()=>cameraAt(key);
$('audit').onclick=async()=>{if(!ready)return;let old={cycles,playing,mode,speed,referenceClip};playing=false;mode='procedural';referenceClip=CLIPS[1];cycles=0;resetContact();let frames=0,maxJointAngle=0,maxJointPosition=0,firstFrameFootGap=0,contactPhases={left:0,right:0};
 status('Auditing 3 traveling source-derived left cycles at 120 Hz; independent source parity and actual world contact...');
 try{const steps=Math.ceil(3*duration*120),startDate=performance.now();for(let i=0;i<steps;i++){
    cycles=(i/steps)*3;redraw();const p=phase;
    // Math reconstruction is audited BEFORE IK at reference snapshot phase.
    let computed=pose(snapshots[CLIPS[1]],plans[CLIPS[1]],p).bones;
    sourceAt(p);
    if(p<plans[CLIPS[1]].seamStart){for(const name of Object.keys(actorRig)){
     const b=sourceRig[name],a=computed[name];maxJointAngle=Math.max(maxJointAngle,angleDeg(b.quaternion.toArray(),a.quaternion));
     maxJointPosition=Math.max(maxJointPosition,b.position.distanceTo(V(...a.position)));
    }}
    for(const side of ['left','right'])if(lastStats?.[side]?.planted)contactPhases[side]++;
    frames++;if(i%40===0)await new Promise(requestAnimationFrame);
   }
   let maxDrift=maxAnchorDrift,skips=skippedCorrections,verifiedContactWindows=['left','right'].every(s=>sourceContacts[s].method==='ANALYTIC_SOURCE_GROUND_VELOCITY');
   lastAudit={schema:'hareworks-v0.1.26-real-left-source-procedural-audit',sourceSha256:SOURCE_SHA,
    sourceClips:CLIPS,controller:'source-calibrated 74-bone mathematical procedural pose plus world-X ankle IK, no generated animation mixer',
    renderedReferenceForAudit:'source AnimationMixer on hidden reference rig only',actualSourceBytes:SIZE,rigBones:74,sourceFramesPerClip:N,
    travelPerCycle:worldStride,worldTravelX:cycles*worldStride,sourcePeriod:duration,sourceGroundContacts:sourceContacts,
    actualFrames:frames,physicsHz:120,contactSampleFrames:contactPhases,worldAnkleAnchorMaxDrift:maxDrift,skippedContactIK:skips,
    sourceJointMaxQuaternionDeg:maxJointAngle,sourceJointMaxPosition:maxJointPosition,strictSourceParityExcludedSeam:1-plans[CLIPS[1]].seamStart,
    contactGate:(verifiedContactWindows&&maxDrift<=.025&&skips===0)?'ANKLE_PIN_PASS__NOT_SKINNED_SOLE_CERTIFICATION':'ANKLE_PIN_WARN',
    sourceParityGate:maxJointAngle<1&&maxJointPosition<.006?'SOURCE_MATH_PARITY_PASS':'SOURCE_MATH_PARITY_WARN',
    ownerAccepted:false};
   $('auditOut').textContent=JSON.stringify(lastAudit,null,2);
   try{await fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(lastAudit)});}catch(e){}
   status('LEFT SOURCE/PROCEDURAL AUDIT COMPLETE · contact '+lastAudit.contactGate+' · source '+lastAudit.sourceParityGate+' · owner review pending');
  }catch(e){status('AUDIT_ERROR '+e.message);console.error(e)}finally{cycles=old.cycles;playing=old.playing;mode=old.mode;speed=old.speed;referenceClip=old.referenceClip;redraw();}
};
$('export').onclick=()=>{if(!lastAudit){status('Run audit first');return;}let u=URL.createObjectURL(new Blob([JSON.stringify(lastAudit,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=u;a.download='hareworks-v0.1.26-left-procedural-audit.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),5000);};
function animate(t){requestAnimationFrame(animate);let dt=Math.max(0,Math.min((t-lastTime)/1000,.05));lastTime=t;
 if(ready&&playing){cycles+=dt*travelPhaseRate(speed,worldStride);redraw();}orbit.update();renderer.render(scene,camera);}
requestAnimationFrame(animate);
try{
 const res=await fetch(MODEL,{cache:'no-store'});if(!res.ok)throw Error('LEFT_MODEL_HTTP_'+res.status);
 const bytes=await res.arrayBuffer();if(bytes.byteLength!==SIZE)throw Error('LEFT_SOURCE_GLB_SIZE_'+bytes.byteLength);
 const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');if(hash!==SOURCE_SHA)throw Error('LEFT_SOURCE_GLB_HASH_'+hash);
 const gltf=await new GLTFLoader().parseAsync(bytes,new URL('../../../assets/hareworks/',import.meta.url).href);
 if(gltf.animations.length!==9)throw Error('LEFT_SOURCE_REQUIRES_NINE_CLIPS_'+gltf.animations.length);
 for(let clip of CLIPS){let found=gltf.animations.find(o=>o.name===clip);if(!found)throw Error('LEFT_SOURCE_CLIP_MISSING_'+clip);sourceClips[clip]=found;}
 source=cloneSkeleton(gltf.scene);actor=cloneSkeleton(gltf.scene);sourceRig=rig(source);actorRig=rig(actor);scene.add(source,actor);source.visible=false;
 sourceMixer=new THREE.AnimationMixer(source);for(let clip of CLIPS)sourceMixer.clipAction(sourceClips[clip]).reset().play();
 for(let clip of CLIPS){snapshots[clip]=snapshot(clip);plans[clip]=calibrate(snapshots[clip],.93);}
 duration=snapshots[CLIPS[1]].duration;worldStride=plans[CLIPS[0]].trend[0]-plans[CLIPS[1]].trend[0];
 if(!(worldStride>1&&worldStride<2))throw Error('LEFT_TRUE_WALK_SOURCE_TRAVEL_NOT_SEPARATED_'+worldStride);
 let original=sampleFootTravel(gltf);for(let side of ['left','right']){
  try{sourceContacts[side]=sourceContactWindow(original[side],sourceClips[CLIPS[0]].duration)}
  catch(e){throw Error('LEFT_ACTUAL_CLIP_CONTACT_DISCOVERY_FAILED_'+side+'_'+e.message)}
 }
 // This is left in the real clip's GLB +X convention; the old guessed -X
 // control was based on forward Walking_Woman and was NEVER an accepted slot.
 speed=Number((worldStride/duration).toFixed(2));$('speed').value=String(speed);$('speedOut').textContent=speed.toFixed(2)+' u/s';
 grid.position.y=new THREE.Box3().setFromObject(actor).min.y;
 ready=true;reset();sourceAt(0);source.visible=false;actor.visible=true;
 $('identity').textContent=`v0.1.26 · REAL Cautious_Crouch_Walk_Left_inplace · source ${SOURCE_SHA} · 74 joints · 720 source-calibrated phases per clip · 0 generated mixer · source left world +X=${worldStride.toFixed(3)}u/cycle · commit ${new URLSearchParams(location.search).get('commit')||'unknown'} · entry ${new URLSearchParams(location.search).get('scriptSha')||'unknown'}`;
 status('TRUE LEFT CLIP DERIVED · GENERATED 74-BONE PROCEDURAL GAIT ACTIVE · IK ankle pin audit PENDING');
}catch(e){status('LEFT_SOURCE_OR_STARTUP_BLOCKED '+String(e.message||e));$('auditOut').textContent='BLOCKED_REAL_GLTF_SOURCE '+String(e.message||e);console.error(e);}
