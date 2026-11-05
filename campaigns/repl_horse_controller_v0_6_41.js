// Repl procedural horse controller v0.6.41. No baked gait clips.
// Owner corrections: full stance extension, foreleg hinge, hind heel/toe orientation,
// longer reach, lowered body, real skinned hoof contacts, shared walk/trot solver.
import * as THREE from 'three';
const V=()=>new THREE.Vector3();
const LIMBS={LF:['Bone_016','Bone_015','Bone_014','Bone_013','Bone_012'],RF:['Bone_022','Bone_021','Bone_020','Bone_019','Bone_018'],LH:['Bone_027','Bone_026','Bone_025','Bone_024','Bone_023'],RH:['Bone_032','Bone_031','Bone_030','Bone_029','Bone_028']};
const PW={LH:0,LF:.25,RH:.5,RF:.75},PT={LF:0,RH:0,RF:.5,LH:.5};
const clamp=(a,x,y)=>Math.max(x,Math.min(y,a)),mix=(a,b,t)=>a+(b-a)*t;
const smooth=x=>{x=clamp(x,0,1);return x*x*(3-2*x)};
const TAU=Math.PI*2;
export class HorseController{
 constructor(scene){
  this.scene=scene;this.bones={};this.meshes=[];scene.traverse(o=>{if(o.isBone)this.bones[o.name]=o;if(o.isSkinnedMesh)this.meshes.push(o)});
  this.root=this.bones.Bone_000;if(!this.root||!this.meshes.length)throw Error('REPL_SKIN_OR_ROOT_MISSING');
  this.rest={};for(const [n,b] of Object.entries(this.bones))this.rest[n]={q:b.quaternion.clone(),p:b.position.clone()};
  this.legs={};scene.updateMatrixWorld(true);
  for(const [name,ns] of Object.entries(LIMBS)){
   const bones=ns.map(n=>this.bones[n]);if(bones.some(x=>!x))throw Error('LEG_CHAIN_MISSING:'+name);
   const kind=name[1]==='F'?'fore':'hind';
   const l={name,kind,bones,rest:bones.map(b=>b.getWorldPosition(V())),foot0:bones[4].getWorldPosition(V()),anchor:null,start:null,contact:false,
      a:[0,0,0,0],lim:kind==='fore'?[[-.85,.85],[-.85,.85],[-.85,.14],[-.45,.45]]:[[-.85,.85],[-.8,.8],[-.85,.85],[-.42,.48]],
      patch:null,restPitch:0,offset:0,reach:0};
   l.patch=this._findPatch(l);
   this.legs[name]=l;
  }
  this.speed=.55;this.strideGain=1.35;this.liftGain=1;this.terrain='flat';this.blend=0;this.requested='walk';this.mode='walk';
  this.distance=0;this.cycle=0;this.started=false;this.paused=false;this._axis=V().set(1,0,0);this._q=new THREE.Quaternion();
  this.stats={};
  this.scene.updateMatrixWorld(true);
  for(const l of Object.values(this.legs)){const p=this._patch(l);l.offset=.5*(p.toe.y+p.heel.y)-l.foot0.y;l.restPitch=p.pitch;l.foot0=p.toe.clone().add(p.heel).multiplyScalar(.5);l.reach=Math.abs(l.rest[0].y-l.foot0.y);l.chainLength=l.rest.slice(1).reduce((sum,p,i)=>sum+p.distanceTo(l.rest[i]),0);}
 }
 terrainHeight(x,z){switch(this.terrain){case 'slope':return .11*z;case 'rolling':return .043*Math.sin(z*3.1)+.025*Math.sin(2.1*x+z*5.3);case 'steps':return .065*Math.floor((z+.001)/.75);default:return 0}}
 setGait(g){if(!['walk','trot'].includes(g))throw Error('UNKNOWN_GAIT');this.requested=g}
 setTerrain(g){if(!['flat','rolling','slope','steps'].includes(g))throw Error('UNKNOWN_TERRAIN');this.terrain=g}
 _findPatch(l){
  // Select stable toe and heel VERTEX IDENTITIES, not changing lowest-point proxies.
  const distal=l.bones[3].name;let found=[];
  for(const mesh of this.meshes){const ia=mesh.geometry.getAttribute('skinIndex'),wa=mesh.geometry.getAttribute('skinWeight'),pos=mesh.geometry.getAttribute('position');
   if(!ia||!wa||!pos)continue;
   const sk=mesh.skeleton.bones.findIndex(b=>b.name===distal);if(sk<0)continue;
   const p=V();for(let i=0;i<pos.count;i++){
    let weight=0;for(let j=0;j<4;j++)if(ia.getComponent(i,j)===sk)weight+=wa.getComponent(i,j);
    if(weight<.35)continue;
    mesh.getVertexPosition(i,p);const world=p.clone().applyMatrix4(mesh.matrixWorld);
    if(world.y>.13)continue;found.push({mesh,i,x:world.x,y:world.y,z:world.z});
   }
  }
  if(found.length<20)throw Error('SKINNED_HOOF_PATCH_NOT_FOUND:'+l.name+':'+found.length);
  found.sort((a,b)=>a.z-b.z);
  const group=Math.max(4,Math.floor(found.length*.14));
  // The minimum longitudinal cluster is the heel. +Z is horse-forward.
  const heel=found.slice(0,group),toe=found.slice(-group);
  const stable=a=>a.slice().sort((x,y)=>x.y-y.y).slice(0,Math.max(3,Math.ceil(a.length*.5)));
  return {toe:stable(toe),heel:stable(heel)};
 }
 _patch(l){
  const center=list=>{const out=V();for(const p of list){const v=V();p.mesh.getVertexPosition(p.i,v);out.add(v.applyMatrix4(p.mesh.matrixWorld))}return out.multiplyScalar(1/list.length)};
  const toe=center(l.patch.toe),heel=center(l.patch.heel);let dz=toe.z-heel.z;if(Math.abs(dz)<.012)throw Error('HOOF_LONG_AXIS_DEGENERATE:'+l.name);
  return {toe,heel,pitch:Math.atan2(toe.y-heel.y,dz)};
 }
 _config(){const b=this.blend;return {duration:mix(1.28,.83,b),duty:mix(.62,.40,b),travel:mix(.36,.81,b)*this.strideGain,lift:mix(.105,.21,b)*this.liftGain,bob:mix(.025,.105,b)};}
 _phase(name){return mix(PW[name],PT[name],this.blend)}
 _foot(l){const p=this._patch(l);return p.toe.clone().add(p.heel).multiplyScalar(.5)}
 _angle(l,j,v){l.a[j]=clamp(v,...l.lim[j]);l.bones[j].quaternion.copy(this.rest[l.bones[j].name].q).multiply(this._q.setFromAxisAngle(this._axis,l.a[j]));}
 _apply(l){for(let j=0;j<4;j++)this._angle(l,j,l.a[j]);l.bones[4].quaternion.copy(this.rest[l.bones[4].name].q);}
 _pole(l){const pts=l.bones.map(b=>b.getWorldPosition(V()));let a=pts[1],b=pts[2],c=pts[3];const den=c.y-a.y;if(Math.abs(den)<1e-5)return 0;return b.z-(a.z+(b.y-a.y)/den*(c.z-a.z));}
 _solve(l,target,stance,swing){
  // Constrained damped numerical IK. End-point *and skinned toe/heel pitch*.
  // Penalize flexed stance knees; recover using proper fore/hind pole direction.
  const toeTarget=stance?0:Math.max(0,.025*Math.sin(Math.PI*clamp(swing,0,1)));
  const poleGoal=stance?(l.kind==='fore'?.005:-.075):(l.kind==='fore'?.082:-.155)*Math.sin(Math.PI*swing);
  const weights=[85,85,stance?160:23,stance?48:14,stance?21:13];
  const evaluate=()=>{
   this.scene.updateMatrixWorld(true);
   const patch=this._patch(l),foot=patch.toe.clone().add(patch.heel).multiplyScalar(.5),mid=foot.y,g=this.terrainHeight(foot.x,foot.z);
   return [(foot.y-target.y)*weights[0],(foot.z-target.z)*weights[1],(stance?Math.min(0,Math.min(patch.toe.y-g,patch.heel.y-g)):Math.min(0,mid-g-toeTarget))*weights[2],
     (patch.pitch-(stance?0:clamp(l.restPitch,-.12,.12)))*weights[3],(this._pole(l)-poleGoal)*weights[4]];
  };
  // Two different objective families are important: body/hoof placement and
  // anatomical bend. Weak regularization retains continuity; no rigid snaps.
  let lambda=.12,best=Infinity;
  for(let iter=0;iter<5;iter++){
   const r=evaluate();const cost=r.reduce((s,x)=>s+x*x,0);if(cost<1e-6)break;
   const jac=[];
   for(let j=0;j<4;j++){
    const old=l.a[j],h=.004;
    this._angle(l,j,old+h);const plus=evaluate();
    this._angle(l,j,old-h);const minus=evaluate();
    this._angle(l,j,old);
    jac.push(plus.map((v,k)=>(v-minus[k])/(2*h)));
   }
   const m=Array.from({length:4},(_,i)=>Array.from({length:5},(_,k)=> k===4?-jac[i].reduce((z,v,n)=>z+v*r[n],0):jac[i].reduce((z,v,n)=>z+v*jac[k][n],0)+(i===k?lambda:0)));
   let singular=false;
   for(let i=0;i<4;i++){let pivot=i;for(let k=i+1;k<4;k++)if(Math.abs(m[k][i])>Math.abs(m[pivot][i]))pivot=k;
    if(Math.abs(m[pivot][i])<1e-8){singular=true;break} [m[i],m[pivot]]=[m[pivot],m[i]];
    const scale=m[i][i];for(let k=i;k<5;k++)m[i][k]/=scale;
    for(let j=0;j<4;j++)if(j!==i){const factor=m[j][i];for(let k=i;k<5;k++)m[j][k]-=factor*m[i][k]}
   }
   if(singular)break;
   const original=l.a.slice();let improved=false;
   for(const scale of [.7,.35,.12]){
    for(let j=0;j<4;j++)this._angle(l,j,original[j]+clamp(m[j][4]*scale,-.16,.16));
    const after=evaluate().reduce((s,x)=>s+x*x,0);
    if(after<cost){improved=true;lambda=Math.max(.03,lambda*.75);break}
   }
   if(!improved){for(let j=0;j<4;j++)this._angle(l,j,original[j]);lambda*=2;if(lambda>8)break}
   best=Math.min(best,cost);
  }
  const patch=this._patch(l),foot=this._foot(l),terrain=this.terrainHeight(patch.toe.x,patch.toe.z);
  return {error:foot.distanceTo(target),solePenetration:Math.min(patch.toe.y-this.terrainHeight(patch.toe.x,patch.toe.z),patch.heel.y-this.terrainHeight(patch.heel.x,patch.heel.z)),pitch:patch.pitch,pole:this._pole(l)};
 }
 _rootY(c,q){const pulse=(1-Math.cos(4*Math.PI*q))*.5;return mix(-.135,-.22,this.blend)+c.bob*pulse;}
 update(dt){
  if(this.paused)return this.stats;
  dt=clamp(dt,0,.035);const b=this.requested==='trot'?1:0;this.blend=mix(this.blend,b,clamp(dt*1.1,0,1));if(Math.abs(this.blend-b)<.0002)this.blend=b;
  this.mode=this.blend>.5?'trot':'walk';const c=this._config(),speed=clamp(this.speed,0,2.3);
  this.distance+=speed*dt;this.cycle+=dt*speed/Math.max(.1,c.travel);
  const q=((this.cycle%1)+1)%1;this.root.position.copy(this.rest.Bone_000.p);this.root.position.z+=this.distance;
  this.root.position.y+=this._rootY(c,q)+this.terrainHeight(0,this.distance);
  this.scene.updateMatrixWorld(true);
  let error=0,solePenetration=1,contacts=0,stanceDrift=0,maxPitch=0;
  for(const [name,l] of Object.entries(this.legs)){
   const u=((q-this._phase(name))%1+1)%1,stance=u<c.duty;
   let goal;if(!this.started){l.anchor=this._foot(l);l.anchor.y=this.terrainHeight(l.anchor.x,l.anchor.z);l.start=l.anchor.clone();l.contact=stance;}
   if(stance){if(!l.contact){l.anchor=this._foot(l);l.anchor.y=this.terrainHeight(l.anchor.x,l.anchor.z);}l.contact=true;goal=l.anchor.clone();contacts++;}
   else {if(l.contact||!l.start)l.start=l.anchor?l.anchor.clone():this._foot(l);l.contact=false;
    const v=(u-c.duty)/(1-c.duty),e=smooth(v),p=l.foot0;
    const remaining=(1-v)*c.travel;
    const hipY=l.rest[0].y+this._rootY(c,q),groundAtHip=this.terrainHeight(p.x,l.rest[0].z+this.distance+remaining);
    const vertical=Math.abs(hipY-groundAtHip);
    const reachable=Math.sqrt(Math.max(.03,(.96*l.chainLength)**2-vertical**2));
    const forwardReach=Math.min(.5*c.travel,.94*reachable);
    const ahead=this.distance+remaining+forwardReach;
    const finish=V().set(p.x,0,ahead+p.z-this.rest.Bone_000.p.z);finish.y=this.terrainHeight(finish.x,finish.z);
    goal=l.start.clone().lerp(finish,e);goal.y=Math.max(goal.y,this.terrainHeight(goal.x,goal.z))+c.lift*Math.pow(Math.sin(Math.PI*v),1.15)*(l.kind==='fore'?1.32:1);
   }
   const res=this._solve(l,goal,stance,(u-c.duty)/(1-c.duty));error=Math.max(error,res.error);solePenetration=Math.min(solePenetration,res.solePenetration);maxPitch=Math.max(maxPitch,Math.abs(res.pitch));if(stance)stanceDrift=Math.max(stanceDrift,res.error);
  }
  this.started=true;this.stats={mode:this.mode,blend:this.blend,cycle:q,contacts,stanceDrift,error,rootY:this.root.position.y,travel:this.distance,solePenetration,maxPitch};return this.stats;
 }
}
export const GAIT_PROFILE={walk:PW,trot:PT};
