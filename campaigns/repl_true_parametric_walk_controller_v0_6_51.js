// Repl 0.6.51: parameter-generated equine walk. No AnimationMixer, no animation
// track interpolants, no time-indexed joint curves, and no walk/trot blending.
// One rig adapter maps semantic joints. The generic trajectory generator never
// uses Repl-specific node names, dimensions or material information.
import * as THREE from 'three';
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const smooth=(u)=>{u=clamp(u,0,1);return u*u*(3-2*u);};
const vec=()=>new THREE.Vector3();
const axis=new THREE.Vector3(1,0,0);
const qdelta=(n)=>new THREE.Quaternion().setFromAxisAngle(axis,n);
const LEG_MAP={
  leftFore:['Bone_016','Bone_015','Bone_014','Bone_013','Bone_012'],
  rightFore:['Bone_022','Bone_021','Bone_020','Bone_019','Bone_018'],
  leftHind:['Bone_027','Bone_026','Bone_025','Bone_024','Bone_023'],
  rightHind:['Bone_032','Bone_031','Bone_030','Bone_029','Bone_028']
};
const OFFSETS={leftHind:0,leftFore:.25,rightHind:.5,rightFore:.75};
export const MODE='TRUE_PARAMETRIC_WALK_NO_ANIMATION_PLAYBACK';
export const SPEC={stride:0.24,frequency:1.15,duty:.68,clearance:.07,bodyBob:.009};

export class ReplRigAdapter {
 constructor(model){
  this.model=model;this.objects={};this.meshes=[];this.bones={};this.baseline=new Map();
  model.traverse(o=>{if(o.name)this.objects[o.name]=o;if(o.isBone)this.bones[o.name]=o;if(o.isSkinnedMesh)this.meshes.push(o);
    if(o.position&&o.quaternion)this.baseline.set(o,{position:o.position.clone(),quaternion:o.quaternion.clone(),scale:o.scale.clone()});});
  this.root=this.bones.Bone_000;
  if(!this.root||!this.meshes.length)throw Error('REPL_RIG_OR_SKIN_MISSING');
  this.model.updateMatrixWorld(true);this.legs={};
  for(const [semantic,names] of Object.entries(LEG_MAP)){
   const bones=names.map(n=>this.bones[n]);if(bones.some(b=>!b))throw Error('MISSING_SEMANTIC_LIMB:'+semantic);
   // Every rig maps semantic roles into its own bones. Generic gait code below
   // has no concept of Bone_015 or any other author-specific node name.
   const leg={semantic,bones,drivers:bones.slice(0,3),base:[],patch:null,neutral:null,reach:0};
   leg.base=leg.drivers.map(b=>b.quaternion.clone());
   const [upper,mid,lower]=bones.map(b=>b.getWorldPosition(vec()));
   leg.reach=upper.distanceTo(mid)+mid.distanceTo(lower);
   this.legs[semantic]=leg;
  }
  for(const leg of Object.values(this.legs)){leg.patch=this.findPatch(leg);leg.neutral=this.patch(leg).mid.clone();}
  this.rootInitial={position:this.root.position.clone(),quaternion:this.root.quaternion.clone()};
 }
 reset(){for(const [o,s] of this.baseline){o.position.copy(s.position);o.quaternion.copy(s.quaternion);o.scale.copy(s.scale);}this.model.updateMatrixWorld(true);}
 findPatch(leg){
  const distal=leg.bones[3];const candidate=[];
  for(const mesh of this.meshes){
   const sk=mesh.geometry.getAttribute('skinIndex'),sw=mesh.geometry.getAttribute('skinWeight'),pos=mesh.geometry.getAttribute('position');
   if(!sk||!sw||!pos)continue;const joint=mesh.skeleton.bones.indexOf(distal);if(joint<0)continue;
   for(let i=0;i<pos.count;i++){
    let weight=0;for(let j=0;j<4;j++)if(sk.getComponent(i,j)===joint)weight+=sw.getComponent(i,j);
    if(weight<.4)continue;const p=mesh.getVertexPosition(i,vec()).applyMatrix4(mesh.matrixWorld);
    if(p.y<.18)candidate.push({mesh,index:i,position:p});
   }
  }
  if(candidate.length<8)throw Error('HOOF_PATCH_NOT_FOUND:'+leg.semantic);
  candidate.sort((a,b)=>a.position.y-b.position.y);
  const low=candidate.slice(0,Math.max(8,Math.min(26,Math.ceil(candidate.length*.2))));
  low.sort((a,b)=>a.position.z-b.position.z);
  const n=Math.max(3,Math.floor(low.length/3));
  return {heel:low.slice(0,n),toe:low.slice(-n)};
 }
 center(group){const c=vec();for(const a of group)c.add(a.mesh.getVertexPosition(a.index,vec()).applyMatrix4(a.mesh.matrixWorld));return c.multiplyScalar(1/group.length);}
 patch(l){const heel=this.center(l.patch.heel),toe=this.center(l.patch.toe);return {heel,toe,mid:heel.clone().add(toe).multiplyScalar(.5),pitch:Math.atan2(toe.y-heel.y,toe.z-heel.z)};}
 solve(l,goal,maxIter=14){
  const base=l.base,angles=[0,0,0],clampAngle=.95;
  const apply=()=>{for(let j=0;j<3;j++)l.drivers[j].quaternion.copy(base[j]).multiply(qdelta(angles[j]));this.model.updateMatrixWorld(true);};
  let previous=Infinity;
  for(let iter=0;iter<maxIter;iter++){
   apply();const here=this.patch(l).mid,dy=goal.y-here.y,dz=goal.z-here.z,err=Math.hypot(dy,dz);
   if(err<.006)break;if(err>previous+.003)break;previous=err;
   const J=[];
   for(let j=0;j<3;j++){
    angles[j]+=.002;apply();const a=this.patch(l).mid;
    angles[j]-=.004;apply();const b=this.patch(l).mid;angles[j]+=.002;
    J.push([(a.y-b.y)/.004,(a.z-b.z)/.004]);
   }
   let aa=.012,ab=0,bb=.012;
   for(const row of J){aa+=row[0]*row[0];ab+=row[0]*row[1];bb+=row[1]*row[1];}
   const determinant=aa*bb-ab*ab;if(determinant<1e-9)break;
   const wy=(bb*dy-ab*dz)/determinant,wz=(aa*dz-ab*dy)/determinant;
   const step=J.map(r=>clamp(r[0]*wy+r[1]*wz,-.075,.075));
   if(step.every(s=>Math.abs(s)<1e-7))break;
   for(let j=0;j<3;j++)angles[j]=clamp(angles[j]+step[j],-clampAngle,clampAngle);
  }
  apply();const actual=this.patch(l),error=actual.mid.distanceTo(goal);
  return {actual,error,angles:angles.slice(),valid:Number.isFinite(error)&&error<.045};
 }
}

export class EquineWalkGenerator {
 constructor(adapter){this.adapter=adapter;this.elapsed=0;this.paused=false;this.params={...SPEC};this.previous={};this.status={};}
 setParams(p){
  this.params={stride:clamp(Number(p.stride),.07,.48),frequency:clamp(Number(p.frequency),.35,2.4),duty:clamp(Number(p.duty),.53,.83),clearance:clamp(Number(p.clearance),.015,.14),bodyBob:clamp(Number(p.bodyBob),0,.032)};
 }
 restart(){this.elapsed=0;this.previous={};this.update(0);}
 // All targets are closed-form from elapsed time, speed and rig calibration.
 // No feedback from yesterday's IK error is permitted in the next footfall.
 target(leg,cycles){
  const {stride,duty,clearance}=this.params;
  const offset=OFFSETS[leg.semantic];const x=cycles-offset;const k=Math.floor(x),u=x-k;
  const stanceCenter=k+offset+duty*.5;
  const z0=leg.neutral.z+stanceCenter*stride;
  const z1=z0+stride;
  const y=leg.neutral.y;
  if(u<duty)return {u,contact:true,goal:new THREE.Vector3(leg.neutral.x,y,z0)};
  const swing=(u-duty)/(1-duty),s=smooth(swing);
  return {u,contact:false,goal:new THREE.Vector3(leg.neutral.x,y+clearance*Math.sin(Math.PI*swing),z0+(z1-z0)*s)};
 }
 update(dt){
  if(!this.paused)this.elapsed+=clamp(dt,0,.055);
  const a=this.adapter,p=this.params,cycles=this.elapsed*p.frequency;
  a.reset();
  a.root.position.copy(a.rootInitial.position);
  a.root.position.z+=cycles*p.stride;
  a.root.position.y+=p.bodyBob*(.5-.5*Math.cos(4*Math.PI*cycles));
  a.model.updateMatrixWorld(true);
  let maxError=0,maxStanceDrift=0,contacts=0,imperfect=0;const feet=[];
  for(const leg of Object.values(a.legs)){
   const t=this.target(leg,cycles),result=a.solve(leg,t.goal);
   maxError=Math.max(maxError,Number.isFinite(result.error)?result.error:999);
   if(!result.valid)imperfect++;
   if(t.contact){contacts++;maxStanceDrift=Math.max(maxStanceDrift,result.error);}
   feet.push({leg:leg.semantic,contact:t.contact,u:t.u,target:t.goal.toArray(),actual:result.actual.mid.toArray(),heel:result.actual.heel.toArray(),toe:result.actual.toe.toArray(),error:result.error,valid:result.valid});
  }
  this.status={mode:MODE,phase:cycles%1,cycles,contacts,stride:p.stride,frequency:p.frequency,duty:p.duty,clearance:p.clearance,speed:p.stride*p.frequency,maxError,maxStanceDrift,imperfect,feet};
  return this.status;
 }
}

export class ReplParametricWalk {
 constructor(gltf){this.model=gltf.scene;this.adapter=new ReplRigAdapter(gltf.scene);this.bones=this.adapter.bones;this.core=new EquineWalkGenerator(this.adapter);this.paused=false;this.status=this.core.update(0);}
 setParams(p){this.core.setParams(p)}
 seek(t){this.core.elapsed=Math.max(0,t);this.status=this.core.update(0)}
 update(dt){this.core.paused=this.paused;this.status=this.core.update(dt);return this.status}
}
