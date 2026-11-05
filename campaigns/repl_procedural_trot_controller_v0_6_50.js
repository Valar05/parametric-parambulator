// Repl v0.6.50: approved procedural walk with separately constructed diagonal trot.
// All animation tracks become time-indexed pose calibration data. No mixer drives
// the presented horse. Geometry-preserving terrain adaptation is bounded and gated.
import * as THREE from 'three';
const WALK='REPL_WALK_03_FORWARD_SECONDARY_INTEGRATED';
const CHAINS={LF:['Bone_016','Bone_015','Bone_014','Bone_013','Bone_012'],RF:['Bone_022','Bone_021','Bone_020','Bone_019','Bone_018'],LH:['Bone_027','Bone_026','Bone_025','Bone_024','Bone_023'],RH:['Bone_032','Bone_031','Bone_030','Bone_029','Bone_028']};
const PHASE={LH:0,LF:.25,RH:.5,RF:.75};
const CLAMP=(v,a,b)=>Math.max(a,Math.min(b,v));
const SMOOTH=t=>{t=CLAMP(t,0,1);return t*t*(3-2*t)};
const v=()=>new THREE.Vector3();

export class ReplProceduralWalk {
  constructor(gltf){
    this.model=gltf.scene;this.bones={};this.meshes=[];this.objects={};
    this.model.traverse(o=>{if(o.name)this.objects[o.name]=o;if(o.isBone)this.bones[o.name]=o;if(o.isSkinnedMesh)this.meshes.push(o)});
    if(!this.bones.Bone_000||!this.meshes.length)throw Error('REAL_REPL_SKIN_OR_ROOT_MISSING');
    this.clip=gltf.animations.find(c=>c.name===WALK);
    if(!this.clip)throw Error('APPROVED_WALK_CLIP_MISSING');
    this.channels=[];this.initial=new Map();
    for(const [name,o] of Object.entries(this.objects)){
      if(o.position&&o.quaternion)this.initial.set(name,{p:o.position.clone(),q:o.quaternion.clone(),s:o.scale.clone()});
    }
    for(const tr of this.clip.tracks){
      const mt=/^(.+)\.(position|quaternion|scale)$/.exec(tr.name);
      if(!mt)throw Error('UNSUPPORTED_APPROVED_TRACK:'+tr.name);
      const object=this.objects[mt[1]];
      if(!object)throw Error('APPROVED_TRACK_TARGET_MISSING:'+tr.name);
      this.channels.push({object,property:mt[2],interp:tr.createInterpolant(),track:tr});
    }
    this.elapsed=0;this.paused=false;this.rate=1;this.terrain='flat';this.adaptation=0;
    this.gait='walk';this.period=this.clip.duration/3;
    if(!(this.period>.4&&this.period<2))throw Error('APPROVED_PERIOD_INVALID:'+this.period);
    this.legs={};this.model.updateMatrixWorld(true);
    for(const [name,names] of Object.entries(CHAINS)){
      const bones=names.map(n=>this.bones[n]);if(bones.some(b=>!b))throw Error('REPL_CHAIN_MISSING:'+name);
      this.legs[name]={name,bones,drivers:bones.slice(0,3),patch:null,last:[0,0,0],contact:false,anchor:null,delta:0,patchError:0};
    }
    this.seek(0);
    for(const l of Object.values(this.legs))l.patch=this.findPatch(l);
    // At flat baseline, no correction. Stance status is a procedural footfall state.
    this.status={};
  }
  terrainHeight(x,z){
    if(this.terrain==='rolling')return .020*Math.sin(2.0*z)+.012*Math.sin(1.3*x+3.2*z);
    if(this.terrain==='slope')return .032*z;
    return 0;
  }
  setRate(n){this.rate=CLAMP(Number(n)||1,.4,1.6)}
  setTerrain(s){if(!['flat','rolling','slope'].includes(s))throw Error('INVALID_TERRAIN');this.terrain=s;
    for(const l of Object.values(this.legs)){l.anchor=null;l.contact=false;l.delta=0;l.last=[0,0,0]}}
  setAdaptation(n){this.adaptation=CLAMP(Number(n)||0,0,1)}
  sample(t){
    for(const [name,state] of this.initial){const o=this.objects[name];o.position.copy(state.p);o.quaternion.copy(state.q);o.scale.copy(state.s)}
    for(const c of this.channels){const a=c.interp.evaluate(t);if(c.property==='quaternion')c.object.quaternion.fromArray(a).normalize();else if(c.property==='position')c.object.position.fromArray(a);else c.object.scale.fromArray(a)}
    this.model.updateMatrixWorld(true);
  }
  seek(t){this.elapsed=((t%this.clip.duration)+this.clip.duration)%this.clip.duration;this.sample(this.elapsed)}
  findPatch(l){
    const distal=l.bones[3].name;let verts=[];
    for(const mesh of this.meshes){
      const id=mesh.geometry.getAttribute('skinIndex'),weight=mesh.geometry.getAttribute('skinWeight'),pos=mesh.geometry.getAttribute('position');
      if(!id||!weight||!pos)continue;
      const joint=mesh.skeleton.bones.findIndex(b=>b.name===distal);if(joint<0)continue;
      for(let i=0;i<pos.count;i++){
        let w=0;for(let j=0;j<4;j++)if(id.getComponent(i,j)===joint)w+=weight.getComponent(i,j);
        if(w<.4)continue;
        const p=mesh.getVertexPosition(i,v()).applyMatrix4(mesh.matrixWorld);
        if(p.y<.16)verts.push({mesh,index:i,initial:p.clone()});
      }
    }
    if(verts.length<8)throw Error('HOOF_SKIN_WITNESSES_MISSING:'+l.name+':'+verts.length);
    verts.sort((a,b)=>a.initial.y-b.initial.y);
    const lowest=verts.slice(0,Math.max(8,Math.min(26,Math.ceil(verts.length*.20))));
    lowest.sort((a,b)=>a.initial.z-b.initial.z);
    return {witnesses:lowest,heel:lowest.slice(0,Math.max(3,Math.floor(lowest.length/3))),toe:lowest.slice(-Math.max(3,Math.floor(lowest.length/3)))};
  }
  centroid(group){const p=v();for(const a of group)p.add(a.mesh.getVertexPosition(a.index,v()).applyMatrix4(a.mesh.matrixWorld));return p.multiplyScalar(1/group.length)}
  patch(l){const heel=this.centroid(l.patch.heel),toe=this.centroid(l.patch.toe),mid=heel.clone().add(toe).multiplyScalar(.5);return {heel,toe,mid,pitch:Math.atan2(toe.y-heel.y,toe.z-heel.z)}}
  stance(l){const u=((this.elapsed/this.period-PHASE[l.name])%1+1)%1;return {u,planted:u<.62,swing:CLAMP((u-.62)/.38,0,1)}}
  // Residual small-angle Jacobian IK from the APPROVED limb pose. It never
  // replaces the known-good joint angles, never touches the terminal hoof.
  // If it cannot meet hard error, pitch and angular continuity gates, it
  // RESTORES the reference pose and signals an unsupported terrain step.
  offsetPatch(l,needY,needZ,dt){
    if(Math.abs(needY)<1e-6&&Math.abs(needZ)<1e-6){l.last=[0,0,0];return {accepted:true,error:0,reason:'BASELINE'}};
    const reference=l.drivers.map(b=>b.quaternion.clone()),axes=new THREE.Vector3(1,0,0);
    const original=this.patch(l);let offsets=[0,0,0];
    const apply=(q)=>{for(let i=0;i<3;i++)l.drivers[i].quaternion.copy(reference[i]).multiply(new THREE.Quaternion().setFromAxisAngle(axes,q[i]));this.model.updateMatrixWorld(true)};
    const residual=(q)=>{apply(q);const x=this.patch(l);return [x.mid.y-original.mid.y-needY,x.mid.z-original.mid.z-needZ,(x.pitch-original.pitch)*.08]};
    let best=Infinity;
    for(let iter=0;iter<5;iter++){
      const f=residual(offsets),cost=Math.hypot(...f);best=Math.min(best,cost);if(cost<.001)break;
      const J=[];for(let i=0;i<3;i++){
        let p=offsets.slice();p[i]+=.002;const up=residual(p);
        p[i]-=.004;const down=residual(p);
        J.push(up.map((z,k)=>(z-down[k])/.004));
      }
      const delta=[0,0,0];for(let j=0;j<3;j++){
        const mag=Math.max(.005,J[j].reduce((s,x)=>s+x*x,0));delta[j]=-CLAMP(J[j].reduce((s,x,k)=>s+x*f[k],0)/mag,-.03,.03);
      }
      const candidate=offsets.map((x,i)=>CLAMP(x+delta[i],-.08,.08));
      if(Math.hypot(...residual(candidate))<cost)offsets=candidate;else break;
    }
    apply(offsets);const result=this.patch(l);
    const e=Math.hypot(result.mid.y-original.mid.y-needY,result.mid.z-original.mid.z-needZ);
    const pitch=Math.abs(result.pitch-original.pitch);
    const speedLimit=.10*Math.max(dt,.02)/.04;
    const continuity=Math.max(...offsets.map((a,i)=>Math.abs(a-l.last[i])));
    const penetration=Math.min(result.toe.y-this.terrainHeight(result.toe.x,result.toe.z),result.heel.y-this.terrainHeight(result.heel.x,result.heel.z));
    const good=e<.012&&pitch<.12&&continuity<Math.max(.10,speedLimit)&&penetration>-.012;
    if(!good){apply([0,0,0]);l.last=[0,0,0];return {accepted:false,error:e,pitch,penetration,reason:'ADAPTATION_REJECTED'}};
    l.last=offsets;return {accepted:true,error:e,pitch,penetration,reason:'ANATOMICAL_REFERENCE_DELTA'};
  }
  update(dt){
    if(!this.paused)this.elapsed=(this.elapsed+CLAMP(dt,0,.055)*this.rate)%this.clip.duration;
    this.sample(this.elapsed);
    let blocked=0,contacts=0,maxError=0;const corrections=[];
    const root=this.bones.Bone_000;
    // Current support center governs body height. Flat reference is identical.
    const support=[];
    for(const l of Object.values(this.legs)){
      const s=this.stance(l);if(s.planted){contacts++;const p=this.patch(l).mid;support.push(this.terrainHeight(p.x,p.z));}
    }
    const bodyTerrain=support.length?support.reduce((a,b)=>a+b,0)/support.length:0;
    const amt=this.adaptation;
    const dy=amt*bodyTerrain;
    if(this.terrain!=='flat'&&amt>0){root.position.y+=dy;this.model.updateMatrixWorld(true)}
    for(const l of Object.values(this.legs)){
      const s=this.stance(l),p=this.patch(l),terrain=this.terrainHeight(p.mid.x,p.mid.z);
      // Reconcile terrain relative to the new procedural body height. For the
      // flat baseline, both are exactly zero and IK is exactly bypassed.
      const desired=amt*(terrain-bodyTerrain);
      const r=this.offsetPatch(l,desired,0,dt);
      if(!r.accepted)blocked++;maxError=Math.max(maxError,r.error||0);
      corrections.push({leg:l.name,contact:s.planted,error:r.error||0,accepted:r.accepted,reason:r.reason});
    }
    if(blocked>0){this.sample(this.elapsed);for(const l of Object.values(this.legs))l.last=[0,0,0];}
    this.model.updateMatrixWorld(true);
    this.status={mode:'PROCEDURAL_PHASE_WALK',reference:WALK,phase:(this.elapsed/this.period)%1,rate:this.rate,terrain:this.terrain,adaptation:amt,contacts,blocked,maxError,corrections,sourceDuration:this.clip.duration};
    return this.status;
  }
  signature(){const s={};for(const [n,o]of Object.entries(this.bones))s[n]=[...o.position.toArray(),...o.quaternion.toArray()];return s}
}
export const APPROVED_WALK_REFERENCE=WALK;


// Separate trot generator. The approved walk remains available, byte-for-byte in its
// sampling/update path. No AnimationMixer and no changes to the GLB. The trot has
// its own two-beat contact schedule and world-space hoof target solver.
const TROT_OFFSETS={LF:0,RH:0,RF:.5,LH:.5};
// Independent trot calibration. Increased forward travel creates a readable
// stance sweep; diagonally paired footfalls remain exactly half a cycle apart.
const TROT_PERIOD=.82;
const TROT_FORWARD_MPS=.82; // review only: target forward speed, not gait transition
const TROT_STEP_REACH=.78; // fraction of the full-cycle forward advance
const TROT_SWING_FOOT_CLEARANCE=.085;
export class ReplProceduralTrot extends ReplProceduralWalk {
 constructor(gltf){
  super(gltf);
  this.mode='trot';this.trotClock=0;this.paused=false;
  this.trotRootZ=this.bones.Bone_000.position.z;
  this.trotStrideZ=TROT_FORWARD_MPS*TROT_PERIOD*TROT_STEP_REACH;
  this.trotLegs={};this.legChannels={};
  for(const [name,leg] of Object.entries(this.legs)){
   const names=new Set(leg.bones.map(b=>b.name));
   this.legChannels[name]=this.channels.filter(c=>names.has(c.object.name));
   if(this.legChannels[name].length<2)throw Error('TROT_ANATOMICAL_TRACKS_MISSING:'+name);
   this.trotLegs[name]={phasePrevious:null,anchor:null,toeOff:null,landing:null,stage:'UNKNOWN',contactDrift:0,
      solveError:0,solveAccepted:false,correctionRadians:0,lastActual:null,frameDelta:0};
  }
  this.trotReport={};this.seekTrot(0);
 }
 seekTrot(seconds){
  this.trotClock=Math.max(0,Number(seconds)||0);
  for(const s of Object.values(this.trotLegs)){
   s.phasePrevious=null;s.anchor=null;s.toeOff=null;s.landing=null;s.lastActual=null;s.frameDelta=0;s.stage='UNKNOWN';
  }
  this.updateTrot(0);
 }
 // Time reparametrization of anatomical *seed* only, not the locomotion law.
 // The actual trot trajectory comes from diagonal contact timing, stance
 // anchors, swing height and the spatial inverse-kinematics target.
 seedLeg(name,u){
  const walkLocal=(u<.52 ? .10 + (u/.52)*.50 : .60 + ((u-.52)/.48)*.40);
  const walkPhase=(walkLocal+PHASE[name])%1;
  const t=walkPhase*this.period;
  for(const c of this.legChannels[name]){
   const arr=c.interp.evaluate(t);
   if(c.property==='quaternion')c.object.quaternion.fromArray(arr).normalize();
   else if(c.property==='position')c.object.position.fromArray(arr);
   else c.object.scale.fromArray(arr);
  }
 }
 // Damped least-squares world-space sagittal solver. No arbitrary knee pole
 // reversals, no terminal hoof edits. The approved anatomy supplies the seed.
 solveTarget(l,target){
  const original=l.drivers.map(b=>b.quaternion.clone());
  const quat=new THREE.Quaternion(),axis=new THREE.Vector3(1,0,0);
  let angles=[0,0,0],best=Infinity,accepted=false;
  const apply=()=>{
   for(let i=0;i<3;i++)l.drivers[i].quaternion.copy(original[i]).multiply(quat.setFromAxisAngle(axis,angles[i]));
   this.model.updateMatrixWorld(true);
  };
  let p=this.patch(l);
  let previousError=Infinity;
  for(let iteration=0;iteration<14;iteration++){
   apply();p=this.patch(l);
   const dy=target.y-p.mid.y,dz=target.z-p.mid.z;
   const err=Math.hypot(dy,dz);
   if(err<.012){accepted=true;break}
   if(err>previousError+.002)break;
   previousError=err;best=Math.min(best,err);
   const J=[];
   for(let i=0;i<3;i++){
    angles[i]+=.004;apply();const a=this.patch(l).mid;
    angles[i]-=.008;apply();const b=this.patch(l).mid;
    angles[i]+=.004;
    J.push([(a.y-b.y)/.008,(a.z-b.z)/.008]);
   }
   // Damped 2x2 inverse; protects the almost-straight and nearly singular knees.
   let aa=.006,ab=0,bb=.006;
   for(const c of J){aa+=c[0]*c[0];ab+=c[0]*c[1];bb+=c[1]*c[1]}
   const det=aa*bb-ab*ab;
   if(det<1e-9)break;
   const y=(bb*dy-ab*dz)/det,z=(aa*dz-ab*dy)/det;
   const delta=J.map(c=>CLAMP(c[0]*y+c[1]*z,-.09,.09));
   const trial=angles.map((a,i)=>CLAMP(a+delta[i],-.68,.68));
   if(trial.every((a,i)=>Math.abs(a-angles[i])<1e-5))break;
   angles=trial;
  }
  apply();p=this.patch(l);
  const error=p.mid.distanceTo(target);
  if(error<.018)accepted=true;
  // Preserve reference on catastrophic/NaN solves; observation remains possible.
  if(!Number.isFinite(error)||error>.22){
    for(let i=0;i<3;i++)l.drivers[i].quaternion.copy(original[i]);
    this.model.updateMatrixWorld(true);
    return {accepted:false,error,angles:[0,0,0],reason:'FALLBACK_APPROVED_ANATOMY'};
  }
  return {accepted,error,angles,reason:accepted?'WORLD_FOOT_TARGET_SOLVED':'REVIEW_IMPERFECT_TARGET'};
 }
 updateTrot(dt){
  if(!this.paused)this.trotClock+=CLAMP(dt,0,.055);
  const phase=(this.trotClock/TROT_PERIOD)%1;
  // Reference root/body/mane movement remains calibrated; independent trot
  // generates restrained vertical loading for the two diagonal supports.
  const walkTime=(phase*this.period)%this.clip.duration;
  this.sample(walkTime);
  const root=this.bones.Bone_000;
  root.position.y-=.020*Math.cos(phase*4*Math.PI);
  root.position.z=this.trotRootZ+TROT_FORWARD_MPS*this.trotClock;
  this.model.updateMatrixWorld(true);
  let contacts=0,maxError=0,review=0,maxDrift=0,maxFrameDelta=0;
  const report=[];
  for(const [name,l] of Object.entries(this.legs)){
    const local=(phase+TROT_OFFSETS[name])%1;
    const contact=local<.52;
    const state=this.trotLegs[name];
    const newState=contact?'STANCE':'SWING';
    this.seedLeg(name,local);
    this.model.updateMatrixWorld(true);
    const ref=this.patch(l).mid.clone();
    if(state.phasePrevious===null){
      state.anchor=ref.clone();state.landing=ref.clone();state.toeOff=ref.clone();
    }else if(state.stage!==newState){
      if(contact){state.anchor=state.landing.clone()}
      else {state.toeOff=(state.lastActual||state.anchor).clone();state.landing=state.toeOff.clone().add(new THREE.Vector3(0,0,this.trotStrideZ))}
    }
    let goal;
    if(contact){
      contacts++;
      // Stance stays fixed in world Z as the body travels over it.
      goal=state.anchor.clone();
      goal.y=state.anchor.y;
    }else{
      const s=SMOOTH((local-.52)/.48);
      goal=state.toeOff.clone().lerp(state.landing,s);
      goal.y+=TROT_SWING_FOOT_CLEARANCE*Math.sin(Math.PI*s);
    }
    const result=this.solveTarget(l,goal);
    const actual=this.patch(l).mid;
    state.solveAccepted=result.accepted;state.solveError=result.error;
    state.correctionRadians=Math.max(...result.angles.map(Math.abs));
    state.contactDrift=contact?actual.distanceTo(goal):0;
    state.frameDelta=state.lastActual?actual.distanceTo(state.lastActual):0;
    state.lastActual=actual.clone();maxFrameDelta=Math.max(maxFrameDelta,state.frameDelta);
    maxError=Math.max(maxError,Number.isFinite(result.error)?result.error:999);
    maxDrift=Math.max(maxDrift,state.contactDrift);
    if(!result.accepted)review++;
    report.push({leg:name,stage:newState,phase:local,contact,goal:goal.toArray(),actual:actual.toArray(),
       residual:result.error,accepted:result.accepted,reason:result.reason,frameDelta:state.frameDelta});
    state.phasePrevious=local;state.stage=newState;
  }
  this.model.updateMatrixWorld(true);
  this.status={mode:'PROCEDURAL_DIAGONAL_TROT_EXPERIMENTAL',phase,period:TROT_PERIOD,contacts,
    targetSpeed:TROT_FORWARD_MPS,strideTravel:this.trotStrideZ,maxError,maxDrift,maxFrameDelta,review,feet:report,terrain:'flat',adaptation:0};
  return this.status;
 }
 update(dt){return this.updateTrot(dt)}
}
export const TROT_MODE='EXPERIMENTAL_FIXED_SPEED_DIAGONAL_TROT_LONG_STRIDE_V050';
