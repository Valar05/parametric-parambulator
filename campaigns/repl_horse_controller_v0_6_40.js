// Repl unified runtime locomotion prototype v0.6.40.
// Input: actual GLB joints. Output: procedurally updated bone transforms.
// No animation curves and no copied walk rotations.
import * as THREE from 'three';
const V=()=>new THREE.Vector3();
const LIMBS={
 LF:['Bone_016','Bone_015','Bone_014','Bone_013','Bone_012'],
 RF:['Bone_022','Bone_021','Bone_020','Bone_019','Bone_018'],
 LH:['Bone_027','Bone_026','Bone_025','Bone_024','Bone_023'],
 RH:['Bone_032','Bone_031','Bone_030','Bone_029','Bone_028']
};
const phaseWalk={LH:0,LF:.25,RH:.5,RF:.75},phaseTrot={LF:0,RH:0,RF:.5,LH:.5};
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const mix=(a,b,t)=>a+(b-a)*t;
const smoother=t=>{t=clamp(t,0,1);return t*t*(3-2*t)};
const sin=Math.sin,cos=Math.cos,PI=Math.PI;
export class HorseController {
 constructor(scene,options={}) {
  this.scene=scene;this.bones={};scene.traverse(o=>{if(o.isBone)this.bones[o.name]=o});
  this.root=this.bones.Bone_000;
  if(!this.root)throw Error('BONE_000_MISSING');
  this.rest={};for(const [n,b] of Object.entries(this.bones))this.rest[n]={q:b.quaternion.clone(),p:b.position.clone()};
  this.legs={};scene.updateMatrixWorld(true);
  for(const [name,chain] of Object.entries(LIMBS)){
   const bones=chain.map(n=>this.bones[n]);if(bones.some(b=>!b))throw Error('LEG_BONES_MISSING_'+name);
   const pts=bones.map(b=>b.getWorldPosition(V()));
   const side=name[0]==='L'?-1:1,kind=name[1]==='F'?'fore':'hind';
   this.legs[name]={name,kind,side,bones,rest:pts,foot0:pts.at(-1).clone(),anchor:null,contact:false,
    start:null,end:null,lo:[-.64,-.76,-.85,-.50],hi:[.64,.76,.85,.50],a:[0,0,0,0],lastPhase:0};
   if(kind==='fore'){
    // The v0.6.3 joint polarity on Bone_014/020 was rejected by owner.
    // Pole direction is constrained by calibrated witness, not a transferred animal profile.
    this.legs[name].lo[2]=-.20;this.legs[name].hi[2]=.92;
   }
  }
  this.mode='walk';this.requested='walk';this.blend=0;this.speed=.26;this.time=0;this.distance=0;
  this.strideGain=1;this.liftGain=1;this.terrain='flat';this.yaw=0;this.paused=false;
  this.started=false;this.stats={stanceDrift:0,contacts:0,mode:'walk',error:0};
  this._axis=new THREE.Vector3(1,0,0);this._tmpq=new THREE.Quaternion();
 }
 terrainHeight(x,z){switch(this.terrain){case 'slope':return .11*z;case 'rolling':return .043*sin(z*3.1)+.025*sin(2.1*x+z*5.3);case 'steps':return .065*Math.floor((z+.001)/.75);default:return 0}}
 setGait(g){if(!['walk','trot'].includes(g))throw Error('UNKNOWN_GAIT');this.requested=g;}
 setTerrain(t){if(!['flat','slope','rolling','steps'].includes(t))throw Error('UNKNOWN_TERRAIN');this.terrain=t;}
 _configuration(){const b=this.blend;return {duration:mix(1.28,.78,b),duty:mix(.64,.43,b),travel:mix(.34,.68,b)*this.strideGain,lift:mix(.085,.19,b)*this.liftGain,bob:mix(.009,.061,b)};}
 _phase(name){return mix(phaseWalk[name],phaseTrot[name],this.blend);}
 _footWorld(l){return l.bones.at(-1).getWorldPosition(V());}
 _resetPose(){for(const [n,o] of Object.entries(this.rest)){const b=this.bones[n];b.quaternion.copy(o.q);if(n==='Bone_000')b.position.copy(o.p)};this.scene.updateMatrixWorld(true)}
 _applyAngles(l){for(let i=0;i<4;i++)l.bones[i].quaternion.copy(this.rest[l.bones[i].name].q).multiply(this._tmpq.setFromAxisAngle(this._axis,l.a[i]));
  // Terminal hoof bone stays precisely at its original FK quaternion.
  l.bones[4].quaternion.copy(this.rest[l.bones[4].name].q);}
 _footError(l,target){return this._footWorld(l).sub(target)}
 _ik(l,target){
  // Bounded, warm-started sagittal CCD on the ACTUAL five-joint chain.
  // No generic seven-axis Euler search. The toe terminal is never driven.
  const bone=l.bones,side=l.side;
  for(let iter=0;iter<7;iter++){
   for(let j=3;j>=0;j--){
    this.scene.updateMatrixWorld(true);
    const joint=bone[j].getWorldPosition(V()),foot=this._footWorld(l);
    const a=foot.sub(joint),b=target.clone().sub(joint);
    const cross=a.y*b.z-a.z*b.y;
    const dot=a.y*b.y+a.z*b.z;
    let ang=Math.atan2(cross,dot);
    if(!Number.isFinite(ang))continue;
    // Calibrate world-axis sign to each local bone X orientation.
    const xdir=new THREE.Vector3(1,0,0).transformDirection(bone[j].matrixWorld);
    ang*=xdir.x>=0?1:-1;
    // A world +X rotation changes a YZ vector with opposite sign to cross convention.
    const proposed=clamp(l.a[j]+clamp(ang,-.18,.18),l.lo[j],l.hi[j]);
    l.a[j]=mix(l.a[j],proposed,.8);
    bone[j].quaternion.copy(this.rest[bone[j].name].q).multiply(this._tmpq.setFromAxisAngle(this._axis,l.a[j]));
   }
  }
  this.scene.updateMatrixWorld(true);
  return this._footError(l,target).length();
 }
 _rootHeight(cfg,q){
  const support=cos(4*PI*q); // two compression pulses per trot cycle
  return -this.blend*.055 + cfg.bob*(1-support)*.5 + (1-this.blend)*.006*sin(2*PI*q);
 }
 update(dt){
  if(this.paused)return this.stats;
  dt=clamp(dt,0,.035);this.time+=dt;
  // Blend contact scheduling and IK inputs, not complete animation poses.
  const target=this.requested==='trot'?1:0;
  this.blend=mix(this.blend,target,clamp(dt*.95,0,1));
  if(Math.abs(this.blend-target)<.0002)this.blend=target;
  this.mode=this.blend>.5?'trot':'walk';const c=this._configuration();
  const speed=clamp(this.speed,0,1.6);
  this.distance+=speed*dt;
  const phaseRate=speed/Math.max(.08,c.travel);
  this.cycle=(this.cycle||0)+dt*phaseRate;
  const q=((this.cycle%1)+1)%1;
  const root=this.root;root.position.copy(this.rest.Bone_000.p);
  root.position.z+=this.distance;
  root.position.y+=this._rootHeight(c,q)+this.terrainHeight(0,this.distance);
  this.scene.updateMatrixWorld(true);
  let error=0,stanceDrift=0,contacts=0;
  for(const [name,l] of Object.entries(this.legs)){
   const u=((q-this._phase(name))%1+1)%1;
   const inStance=u<c.duty;
   let targetFoot;
   if(!this.started){l.anchor=this._footWorld(l);l.anchor.y=this.terrainHeight(l.anchor.x,l.anchor.z);l.contact=inStance;l.start=l.anchor.clone();}
   if(inStance){
    if(!l.contact){
     // Carry the actual last touchdown position into the newly planted contact.
     l.anchor=this._footWorld(l);l.anchor.y=this.terrainHeight(l.anchor.x,l.anchor.z);
    }
    l.contact=true;contacts++;
    targetFoot=l.anchor.clone();
   }else{
    if(l.contact || !l.start){l.start=l.anchor?l.anchor.clone():this._footWorld(l);}
    l.contact=false;
    const v=(u-c.duty)/(1-c.duty),e=smoother(v);
    const upcomingRootZ=this.distance+speed*c.duration*(1-v)+c.travel*.12;
    const p=l.foot0;
    const finish=new THREE.Vector3(p.x,0,upcomingRootZ+p.z-this.rest.Bone_000.p.z);
    finish.y=this.terrainHeight(finish.x,finish.z);
    // Swing: faster mid-recovery with high foreleg clearance.
    targetFoot=l.start.clone().lerp(finish,e);
    const surfaceMax=Math.max(this.terrainHeight(targetFoot.x,targetFoot.z),l.start.y,finish.y);
    targetFoot.y=Math.max(targetFoot.y,surfaceMax)+c.lift*sin(PI*v)**1.35*(l.kind==='fore'?1.22:1);
   }
   // Restore source bind quaternions at the start of each independent limb solve.
   for(let j=0;j<4;j++)l.a[j]=clamp(l.a[j],l.lo[j],l.hi[j]);
   this._applyAngles(l);
   this.scene.updateMatrixWorld(true);
   const e=this._ik(l,targetFoot);error=Math.max(error,e);
   if(inStance)stanceDrift=Math.max(stanceDrift,e);
  }
  this.started=true;
  this.stats={mode:this.mode,blend:this.blend,cycle:q,contacts,stanceDrift,error,rootY:root.position.y,speed,travel:this.distance};
  return this.stats;
 }
}
export const GAIT_PROFILE={walk:phaseWalk,trot:phaseTrot};
