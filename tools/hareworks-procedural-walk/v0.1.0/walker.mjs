/* Hareworks procedural WALK v0.1.0: independent movement + aim, authored footsteps, full skinned GLB. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clamp,wrap,shortest,smooth,landing,swing,chooseFoot,targetHeading,headingStep,DEFAULTS} from './gait-core.mjs';

const $=id=>document.getElementById(id);
const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const AXIS_Y=V(0,1,0);
const SOURCE_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const NAMES={
  left:['mixamorigLeftUpLeg','mixamorigLeftLeg','Bone_017','mixamorigLeftFoot','mixamorigLeftToeBase'],
  right:['mixamorigRightUpLeg','mixamorigRightLeg','Bone_013','mixamorigRightFoot','mixamorigRightToeBase']
};
// Extracted at Idle_Turn_Left t=0 from the exact nine-clip binary. Per-foot initial seed only.
// These are *not* accepted running floor/contact truths.
const HEURISTIC_SOLE={left:{ankleY:.159439,soleY:.010807},right:{ankleY:.155861,soleY:-.012837}};
function round(v){return Math.round(v*1000)/1000}
function finite(v){return Number.isFinite(v)}
function yaw(v){return Math.atan2(v.x,v.z)}
function boneWorld(b){return b.getWorldPosition(V())}
function worldQuat(b){return b.getWorldQuaternion(new THREE.Quaternion())}

class HareworksController {
  constructor(scene,gltf){
    this.scene=scene;
    this.actor=new THREE.Group();this.actor.name='PROCEDURAL_ACTOR';scene.add(this.actor);
    this.model=gltf.scene;this.actor.add(this.model);
    this.actualClips=gltf.animations.map(c=>c.name);
    if(gltf.animations.length!==9||!['Idle_Turn_Left','Idle_Turn_Right','Walk_Backward','slide_right'].every(n=>this.actualClips.includes(n)))throw Error('SOURCE_CLIP_COUNT_OR_NAMES_INVALID');
    this.seedOneFrame(gltf.animations);
    this.rig=this.discoverRig();
    this.rootRest={position:this.actor.position.clone(),yaw:0};
    this.baseHipsPosition=this.rig.hips.position.clone();
    this.originalQuat=new Map();this.model.traverse(o=>{if(o.isBone)this.originalQuat.set(o,o.quaternion.clone())});
    this.baseWorldFoot={};this.legs={};
    this.actor.updateMatrixWorld(true);
    for(const side of ['left','right']){
      const chain=this.rig.chains[side],ankle=chain[3],wp=boneWorld(ankle);
      const hip=boneWorld(chain[0]),knee=boneWorld(chain[1]),pole=knee.clone().sub(hip).cross(wp.clone().sub(hip)).normalize();
      this.legs[side]={side,chain,ankle,anchor:wp.clone(),rest:wp.clone(),bindPole:pole,worldFootQ:worldQuat(ankle),swing:null,stance:true,cooldown:0,lastResidual:0,lastYawDrift:0};
      this.baseWorldFoot[side]={pos:wp.clone(),quat:worldQuat(ankle)};
    }
    this.floorY=(HEURISTIC_SOLE.left.soleY+HEURISTIC_SOLE.right.soleY)/2;
    this.markers={};
    const colors={left:0x46c5fa,right:0xffc67b};
    for(const side of ['left','right']){
      const marker=new THREE.Mesh(new THREE.SphereGeometry(.045,12,8),new THREE.MeshBasicMaterial({color:colors[side],depthTest:false}));marker.renderOrder=10;
      this.scene.add(marker);this.markers[side]=marker;
    }
    this.lastStepped='right';this.stats={frames:0,steps:0,maxStanceError:0,maxIKResidual:0,maxWorldFootOrientationErrorDeg:0,kneePoleFlipFrames:0,feetInSwing:0};
    this.vel=V();this.bodyYaw=0;this.aimYaw=0;this.elapsed=0;this.lastFootstepAt=-3;this.maxReach=DEFAULTS.reach;
    const l=this.legs.left.rest,r=this.legs.right.rest;
    this.stanceWidth=Math.abs(l.x-r.x);
    this.legLength=Math.min(...['left','right'].map(s=>this.rig.chains[s].slice(0,-2).reduce((acc,b,i)=>acc+boneWorld(b).distanceTo(boneWorld(this.rig.chains[s][i+1])),0)));
    this.maxReach=Math.max(.23,Math.min(.44,this.legLength*.35));
    this.reset();
  }
  seedOneFrame(clips){
    const seed=clips.find(c=>c.name==='Idle_Turn_Left');
    // One-time pose seed for grounded visual setup. Runtime never plays or blends a source animation.
    const mixer=new THREE.AnimationMixer(this.model);mixer.clipAction(seed).reset().play();mixer.setTime(0);this.model.updateMatrixWorld(true);
    const poses=[];this.model.traverse(o=>{if(o.isBone)poses.push([o,o.position.clone(),o.quaternion.clone(),o.scale.clone()])});
    mixer.stopAllAction();mixer.uncacheRoot(this.model);
    for(const [o,p,q,s] of poses){o.position.copy(p);o.quaternion.copy(q);o.scale.copy(s)}
    this.model.updateMatrixWorld(true);
  }
  discoverRig(){
    const map=new Map();this.model.traverse(o=>{if(o.isBone){if(map.has(o.name))throw Error('DUPLICATE_RIG_NAME '+o.name);map.set(o.name,o)}});
    if(map.size!==74)throw Error('RIG_JOINT_COUNT_'+map.size+'_EXPECTED_74');
    const hips=map.get('mixamorigHips');if(!hips)throw Error('MISSING_HIPS');
    const chains={};
    for(const [side,names] of Object.entries(NAMES)){
      const chain=names.map(n=>{const b=map.get(n);if(!b)throw Error('MISSING_RIG_BONE '+n);return b});
      if(chain[0].parent!==hips||chain.some((b,i)=>i&&b.parent!==chain[i-1]))throw Error('RIG_PARENT_CHAIN_'+side);
      const lengths=chain.slice(0,-1).map((b,i)=>boneWorld(b).distanceTo(boneWorld(chain[i+1])));
      if(lengths.some(n=>!Number.isFinite(n)||n<.008))throw Error('RIG_SEGMENT_LENGTH_INVALID_'+side);
      chains[side]=chain;
    }
    const upper=['mixamorigSpine','mixamorigSpine1','mixamorigSpine2','mixamorigNeck','mixamorigHead'].map(n=>map.get(n));
    if(upper.some(x=>!x))throw Error('UPPER_BODY_RIG_MISSING');
    return {hips,chains,upper,all:map};
  }
  reset(){
    for(const [b,q] of this.originalQuat)b.quaternion.copy(q);
    this.rig.hips.position.copy(this.baseHipsPosition);
    this.actor.position.set(0,0,0);this.actor.rotation.y=0;this.actor.updateMatrixWorld(true);
    this.vel.set(0,0,0);this.bodyYaw=0;this.aimYaw=0;this.elapsed=0;this.lastFootstepAt=-3;this.lastStepped='right';
    for(const side of ['left','right']){
      const leg=this.legs[side];leg.anchor.copy(this.baseWorldFoot[side].pos);leg.worldFootQ.copy(this.baseWorldFoot[side].quat);leg.swing=null;leg.stance=true;leg.cooldown=0;leg.lastResidual=0;
    }
    this.stats={frames:0,steps:0,maxStanceError:0,maxIKResidual:0,maxWorldFootOrientationErrorDeg:0,kneePoleFlipFrames:0,feetInSwing:0};
    this.actor.updateMatrixWorld(true);
  }
  setUpperTwist(twist){
    const proportions=[.10,.3,.36,.14,.10];
    for(let i=0;i<this.rig.upper.length;i++){
      const b=this.rig.upper[i];b.quaternion.copy(this.originalQuat.get(b));
      this.model.updateMatrixWorld(true);
      const parentQ=worldQuat(b.parent),yawWorld=new THREE.Quaternion().setFromAxisAngle(AXIS_Y,twist*proportions[i]);
      const localYaw=parentQ.clone().invert().multiply(yawWorld).multiply(parentQ);
      b.quaternion.premultiply(localYaw);
    }
  }
  // Bounded real-bone CCD for the nonuniform five-node chain. The ankle is the
  // positional effector; its world orientation is then restored in stance.
  solveLeg(leg,target,footWorldQ){
    const chain=leg.chain,ankle=leg.ankle;
    for(const b of chain.slice(0,4))b.quaternion.copy(this.originalQuat.get(b));
    let residual=Infinity;
    const maxAngles=[1.0,1.25,.78];
    for(let pass=0;pass<14;pass++){
      for(let i=2;i>=0;i--){
        const bone=chain[i];this.actor.updateMatrixWorld(true);
        const pivot=boneWorld(bone),end=boneWorld(ankle),a=end.sub(pivot),b=target.clone().sub(pivot);
        if(a.lengthSq()<1e-9||b.lengthSq()<1e-9)continue;
        a.normalize();b.normalize();
        // New world orientation, with per-iteration rotation cap.
        const raw=new THREE.Quaternion().setFromUnitVectors(a,b),limited=new THREE.Quaternion();
        limited.slerpQuaternions(new THREE.Quaternion(),raw,Math.min(1,.22/Math.max(1e-9,2*Math.acos(clamp(raw.w,-1,1)))));
        const parentQ=worldQuat(bone.parent),newQ=parentQ.clone().invert().multiply(limited).multiply(worldQuat(bone));
        const base=this.originalQuat.get(bone),theta=base.angleTo(newQ);
        if(theta>maxAngles[i])newQ.slerpQuaternions(base,newQ,maxAngles[i]/theta);
        bone.quaternion.copy(newQ);
      }
      this.actor.updateMatrixWorld(true);residual=boneWorld(ankle).distanceTo(target);
      if(residual<.008)break;
    }
    this.actor.updateMatrixWorld(true);
    const parentQ=worldQuat(ankle.parent);
    ankle.quaternion.copy(parentQ.invert().multiply(footWorldQ));
    this.actor.updateMatrixWorld(true);
    residual=boneWorld(ankle).distanceTo(target);
    leg.lastResidual=residual;
    const actualQ=worldQuat(ankle);
    leg.lastYawDrift=THREE.MathUtils.radToDeg(actualQ.angleTo(footWorldQ));
    this.stats.maxIKResidual=Math.max(this.stats.maxIKResidual,residual);
    this.stats.maxWorldFootOrientationErrorDeg=Math.max(this.stats.maxWorldFootOrientationErrorDeg,leg.lastYawDrift);
    const hip=boneWorld(chain[0]),knee=boneWorld(chain[1]),normal=knee.sub(hip).cross(boneWorld(ankle).sub(hip)).normalize();
    const expected=leg.bindPole.clone().applyAxisAngle(AXIS_Y,this.bodyYaw);
    if(expected.dot(normal)<-.05)this.stats.kneePoleFlipFrames++;
    return residual;
  }
  stepLeg(side,destination){
    const leg=this.legs[side];if(leg.swing)return false;
    leg.swing={from:leg.anchor.clone(),to:destination.clone(),fromQ:leg.worldFootQ.clone(),toQ:new THREE.Quaternion().setFromAxisAngle(AXIS_Y,this.bodyYaw).multiply(this.baseWorldFoot[side].quat),time:0,duration:DEFAULTS.stepDuration};
    leg.stance=false;this.lastStepped=side;this.lastFootstepAt=this.elapsed;this.stats.steps++;
    return true;
  }
  update(dt,input){
    dt=clamp(dt,0,1/30);
    this.elapsed+=dt;this.stats.frames++;
    const desired=V(input.moveX||0,0,input.moveZ||0),inputMag=Math.min(1,desired.length());
    if(inputMag>.001)desired.normalize().multiplyScalar(DEFAULTS.speed*inputMag);
    const blend=1-Math.exp(-8*dt);this.vel.lerp(desired,blend);
    if(this.vel.lengthSq()<.00001&&inputMag===0)this.vel.set(0,0,0);
    this.actor.position.addScaledVector(this.vel,dt);
    const moving=this.vel.length()>.09;
    this.aimYaw=wrap(input.aimYaw??this.aimYaw);
    if(moving){this.bodyYaw=headingStep(this.bodyYaw,yaw(this.vel),DEFAULTS.turnRate,dt)}
    else{
      const t=targetHeading(this.bodyYaw,this.aimYaw,DEFAULTS.aimTwistBudget);
      if(Math.abs(t.excess)>.05)this.bodyYaw=headingStep(this.bodyYaw,this.aimYaw-Math.sign(t.excess)*DEFAULTS.aimTwistBudget,DEFAULTS.actorTurnRate,dt);
    }
    this.actor.rotation.y=this.bodyYaw;
    const aim=targetHeading(this.bodyYaw,this.aimYaw,DEFAULTS.aimTwistBudget);
    // Runtime torso yaw is independent of planar root locomotion.
    this.rig.hips.position.copy(this.baseHipsPosition);
    this.rig.hips.position.y+=moving?.008*Math.sin(this.elapsed*12):0;
    this.setUpperTwist(aim.twist);
    this.actor.updateMatrixWorld(true);
    const planned={};const errors={};
    for(const side of ['left','right']){
      const leg=this.legs[side],rest=leg.rest;
      planned[side]=new THREE.Vector3(...landing(this.actor.position.toArray(),rest.toArray(),this.bodyYaw,this.vel.toArray(),DEFAULTS.stepLead,leg.anchor.y));
      errors[side]=Math.hypot(planned[side].x-leg.anchor.x,planned[side].z-leg.anchor.z);
    }
    if(!Object.values(this.legs).some(l=>l.swing)&&this.elapsed-this.lastFootstepAt>.11){
      const direction=(!moving&&Math.abs(aim.excess)>.01)?Math.sign(aim.excess):0;
      const threshold=moving?this.maxReach:Math.max(.19,this.maxReach*.65);
      if(Math.max(errors.left,errors.right)>threshold){
        const side=chooseFoot(errors.left,errors.right,this.lastStepped,direction);
        const target=planned[side];const d=target.distanceTo(this.legs[side].anchor);
        const maxTravel=this.legLength*.7;
        if(d>maxTravel)target.lerp(this.legs[side].anchor,1-maxTravel/d);
        this.stepLeg(side,target);
      }
    }
    let swinging=0;
    for(const side of ['left','right']){
      const leg=this.legs[side];let target=leg.anchor.clone();
      if(leg.swing){
        swinging++;
        leg.swing.time+=dt;
        const u=clamp(leg.swing.time/leg.swing.duration,0,1);
        target.fromArray(swing(leg.swing.from.toArray(),leg.swing.to.toArray(),u,DEFAULTS.footLift));
        leg.worldFootQ.slerpQuaternions(leg.swing.fromQ,leg.swing.toQ,smooth(u));
        if(u>=1){leg.anchor.copy(leg.swing.to);leg.worldFootQ.copy(leg.swing.toQ);leg.swing=null;leg.stance=true;target.copy(leg.anchor)}
      }
      this.solveLeg(leg,target,leg.worldFootQ);
      if(leg.stance){this.stats.maxStanceError=Math.max(this.stats.maxStanceError,boneWorld(leg.ankle).distanceTo(leg.anchor))}
      this.markers[side].position.copy(leg.anchor);this.markers[side].position.y-=.025;
      this.markers[side].material.opacity=leg.stance?1:.45;this.markers[side].material.transparent=!leg.stance;
    }
    this.stats.feetInSwing=swinging;
    if(![this.actor.position.x,this.actor.position.z,this.bodyYaw,this.aimYaw,...Object.values(this.legs).map(l=>l.lastResidual)].every(finite))throw Error('NONFINITE_RIG_STATE');
  }
  diagnostics(){return {schema:'hareworks-procedural-walk-v0.1.0',modelSha256:SOURCE_SHA,origin:'independent root movement and IK; seeded Idle_Turn_Left at t=0 only',calibration:'PROVISIONAL_NOT_VISUALLY_ACCEPTED',rootPosition:this.actor.position.toArray().map(round),bodyYawDeg:round(THREE.MathUtils.radToDeg(this.bodyYaw)),aimYawDeg:round(THREE.MathUtils.radToDeg(this.aimYaw)),...this.stats,stanceWidth:round(this.stanceWidth),reach:round(this.maxReach),legs:Object.fromEntries(Object.entries(this.legs).map(([side,l])=>[side,{state:l.stance?'stance':'swing',target:l.anchor.toArray().map(round),ankleResidual:round(l.lastResidual),worldFootOrientationErrorDeg:round(l.lastYawDrift)}]))}}
}

const scene=new THREE.Scene();scene.background=new THREE.Color(0x101721);
scene.add(new THREE.HemisphereLight(0xe7e9ff,0x25303d,2.0));
const sunlight=new THREE.DirectionalLight(0xffffff,2.5);sunlight.position.set(-2,6,2);scene.add(sunlight);
const ground=new THREE.GridHelper(30,30,0x667788,0x384654);scene.add(ground);
const camera=new THREE.PerspectiveCamera(43,1,.02,150);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
let controller=null,last=performance.now(),paused=false,debug=true,framesSinceHud=0;
let moveStick={x:0,z:0},keyMove=new Set(),aimYaw=0;
function resize(){const w=$('stage').clientWidth,h=Math.max(300,Math.min(innerHeight*.64,w*.86));renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}
window.addEventListener('resize',resize);
function setupPad(id,onVector){const el=$(id);let pid=null;function update(e){const r=el.getBoundingClientRect(),dx=(e.clientX-(r.left+r.width/2))/(r.width*.39),dy=(e.clientY-(r.top+r.height/2))/(r.height*.39);const mag=Math.max(1,Math.hypot(dx,dy));onVector(dx/mag,-dy/mag)}
  el.addEventListener('pointerdown',e=>{pid=e.pointerId;el.setPointerCapture(pid);update(e)});
  el.addEventListener('pointermove',e=>{if(e.pointerId===pid)update(e)});
  const end=e=>{if(e.pointerId===pid){pid=null;if(id==='move-pad')onVector(0,0)}};
  el.addEventListener('pointerup',end);el.addEventListener('pointercancel',end);
}
setupPad('move-pad',(x,z)=>{moveStick={x,z};$('move-dot').style.transform=`translate(${x*34}px,${-z*34}px)`});
setupPad('aim-pad',(x,z)=>{if(Math.hypot(x,z)>.12)aimYaw=Math.atan2(x,z);$('aim-dot').style.transform=`translate(${x*34}px,${-z*34}px)`});
window.addEventListener('keydown',e=>{if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','KeyQ','KeyE','Space'].includes(e.code)){e.preventDefault();keyMove.add(e.code)}});
window.addEventListener('keyup',e=>keyMove.delete(e.code));
for(const [id,key,fmt] of [['step-lead','stepLead',v=>Number(v).toFixed(2)],['twist-budget','aimTwistBudget',v=>Math.round(v)+'°'],['foot-lift','footLift',v=>Number(v).toFixed(2)]]){const el=$(id);el.addEventListener('input',()=>{DEFAULTS[key]=key==='aimTwistBudget'?THREE.MathUtils.degToRad(Number(el.value)):Number(el.value);$(id+'-value').textContent=fmt(el.value)});}
$('pause').onclick=()=>{paused=!paused;$('pause').textContent=paused?'Resume':'Pause'};
$('reset').onclick=()=>{controller?.reset();aimYaw=0;moveStick={x:0,z:0};$('move-dot').style.transform='';$('aim-dot').style.transform=''};
$('debug').onclick=()=>{debug=!debug;$('metrics').hidden=!debug;for(const m of Object.values(controller?.markers||{}))m.visible=debug};
$('download').onclick=()=>{if(!controller)return;const s=JSON.stringify(controller.diagnostics(),null,2),url=URL.createObjectURL(new Blob([s],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='hareworks-procedural-walk-v0.1.0-diagnostics.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000)};
$('test').onclick=()=>{
  if(!controller)return;paused=true;controller.reset();
  const matrix=[{label:'forward',x:0,z:1,n:210},{label:'release',x:0,z:0,n:70},{label:'backward',x:0,z:-1,n:210},{label:'right-strafe',x:1,z:0,n:210},{label:'diagonal',x:-.7,z: .7,n:210},{label:'idle-aim-left',x:0,z:0,n:210,aim:-Math.PI*.75},{label:'idle-aim-right',x:0,z:0,n:210,aim:Math.PI*.75}];
  const evidence=[];let invalid=null;
  try{for(const phase of matrix){for(let i=0;i<phase.n;i++)controller.update(1/60,{moveX:phase.x,moveZ:phase.z,aimYaw:phase.aim??Math.atan2(phase.x,phase.z||1)});evidence.push({phase:phase.label,...controller.diagnostics()});if(controller.stats.maxIKResidual>0.35){invalid='large IK target error; inspect source geometry and knee constraints';break}if(controller.stats.kneePoleFlipFrames>0){invalid='knee bend pole inversion observed; inspect actual skeleton and adjust anatomical constraints';break}if(invalid)break}}
  catch(e){invalid=e.message}
  const report={schema:'hareworks-procedural-walk-v0.1.0-physical-check',publishedAsset:SOURCE_SHA,tests:evidence,result:invalid?'WARN_REVIEW_REQUIRED':'MEASUREMENT_COMPLETED_REVIEW_REQUIRED',warning:invalid,ownerAccepted:false};
  const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='hareworks-walk-real-rig-check-v0.1.0.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);
  $('status').textContent=`Real-rig movement check: ${report.result}; ${evidence.length}/${matrix.length} phases. Exported evidence. No visual acceptance implied.`;
  controller.reset();paused=false;
};
function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-last)/1000,1/30);last=now;
  if(controller&&!paused){const k=(a,b)=>keyMove.has(a)||keyMove.has(b),x=(k('KeyD','ArrowRight')?1:0)-(k('KeyA','ArrowLeft')?1:0),z=(k('KeyW','ArrowUp')?1:0)-(k('KeyS','ArrowDown')?1:0);
    const v=V(x+moveStick.x,0,z+moveStick.z);if(v.length()>1)v.normalize();
    if(keyMove.has('KeyQ'))aimYaw-=dt*1.8;if(keyMove.has('KeyE'))aimYaw+=dt*1.8;
    try{controller.update(dt,{moveX:v.x,moveZ:v.z,aimYaw})}catch(e){paused=true;$('status').textContent='BLOCKED_RUNTIME '+e.message;console.error(e)}
  }
  if(controller){camera.position.set(controller.actor.position.x,controller.floorY+5.7,controller.actor.position.z-3.4);camera.lookAt(controller.actor.position.x,.8+controller.floorY,controller.actor.position.z)}
  if(controller&&++framesSinceHud%15===0){const d=controller.diagnostics();$('metrics').textContent=`Steps ${d.steps} · Stance ankle residual ${d.maxStanceError.toFixed(3)} · IK target error ${d.maxIKResidual.toFixed(3)} · Twist ${d.bodyYawDeg}° body / ${d.aimYawDeg}° aim · ${d.legs.left.state}/${d.legs.right.state}`;}
  renderer.render(scene,camera)}
requestAnimationFrame(animate);
try{
  $('status').textContent='Loading exact published Hareworks 9-clip GLB (no animation playback)…';
  const gltf=await new GLTFLoader().loadAsync('../../../assets/hareworks/Hareworks-nine-clips.glb');
  controller=new HareworksController(scene,gltf);
  ground.position.y=controller.floorY;
  // Automatic actual-skeleton smoke: bind seed, forward stepping, reversal, idle turn.
  for(let i=0;i<180;i++){const q=i<60?{moveX:0,moveZ:1,aimYaw:0}:i<120?{moveX:0,moveZ:-1,aimYaw:0}:{moveX:0,moveZ:0,aimYaw:Math.PI/2};controller.update(1/60,q)}
  const smoke=controller.diagnostics();
  const smokeWarning=smoke.maxIKResidual>.35?' IK residual needs visual inspection: '+smoke.maxIKResidual.toFixed(3):' Real-rig smoke sampled.';
  console.info('HAREWORKS_REAL_RIG_SMOKE',smoke);controller.reset();
  resize();
  $('status').textContent='PROCEDURAL WALK LIVE · real rig · seed pose only.'+smokeWarning+' Use touch pads/WASD; run real-rig checks.';
  console.info('HAREWORKS_RIG_READY',controller.diagnostics());
}catch(e){$('status').textContent='BLOCKED_MODEL_OR_RIG: '+e.message;console.error(e)}
