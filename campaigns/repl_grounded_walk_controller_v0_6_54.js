// Repl v0.6.54: walking ONLY, source-derived Fourier motion + world hoof contacts.
// No baked playback and no canonical model mutation.
import * as THREE from 'three';
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const witnessBones={LF:'Bone_012',RF:'Bone_018',LH:'Bone_023',RH:'Bone_028'};
const solveBones={LF:['Bone_015','Bone_014','Bone_013'],RF:['Bone_021','Bone_020','Bone_019'],LH:['Bone_026','Bone_025','Bone_024'],RH:['Bone_031','Bone_030','Bone_029']};
const patterns={LF:['Bone_016','Bone_015','Bone_014','Bone_013','Bone_012'],RF:['Bone_022','Bone_021','Bone_020','Bone_019','Bone_018'],LH:['Bone_027','Bone_026','Bone_025','Bone_024','Bone_023'],RH:['Bone_032','Bone_031','Bone_030','Bone_029','Bone_028']};
const driven=new Set(Object.values(patterns).flat());
const V=()=>new THREE.Vector3();
const evalFourier=(cs,p)=>cs.map(c=>{let v=c[0];for(let k=1;k<=(c.length-1)/2;k++)v+=c[k*2-1]*Math.cos(2*Math.PI*k*p)+c[k*2]*Math.sin(2*Math.PI*k*p);return v});
export const MODE='GROUNDED_FOURIER_WALK_ONLY';
export class EquineGaitBasis {
 constructor(spec){if(spec.format!=='REPL_PARAMETRIC_FOURIER_V1')throw Error('FIT_FORMAT_INVALID');this.spec=spec;this.period=spec.duration/3;this.defaultStride=spec.root_advance[2]/3;this.defaultCadence=1/this.period}
 evaluate(track,phase){return evalFourier(track.coefficients,phase)}
}
export class ReplRigAdapter{
 constructor(scene,spec){this.scene=scene;this.nodes={};this.base={};scene.traverse(o=>{if(o.name){this.nodes[o.name]=o;this.base[o.name]={p:o.position.clone(),q:o.quaternion.clone(),s:o.scale.clone()}}});for(const [leg,arr] of Object.entries(patterns))if(arr.some(n=>!this.nodes[n]))throw Error('MISSING_CHAIN_'+leg);if(!this.nodes[spec.root_node])throw Error('MISSING_ROOT');this.root=this.nodes[spec.root_node];for(const tr of spec.tracks)if(!this.nodes[tr.node])throw Error('MISSING_TRACK_'+tr.node)}
 reset(){for(const [n,b] of Object.entries(this.base)){const o=this.nodes[n];o.position.copy(b.p);o.quaternion.copy(b.q);o.scale.copy(b.s)}}
}
export class GroundedWalk{
 constructor(gltf,spec){this.model=gltf.scene;this.basis=new EquineGaitBasis(spec);this.rig=new ReplRigAdapter(this.model,spec);this.elapsed=0;this.phase=0;this.travel=0;this.paused=false;this.speed=.5;this.status={};this.contact={};this.meshes=[];
  this.model.traverse(o=>{if(o.isSkinnedMesh){o.frustumCulled=false;this.meshes.push(o)}});
  this._fitted(0);this._initializeWitnesses();this._deriveContactSchedule();this.evaluate(0);
 }
 setParams({speed}){if(!Number.isFinite(+speed))throw Error('SPEED_INVALID');this.speed=clamp(+speed,0,1)}
 get cadence(){return this.basis.defaultCadence*(.44+.43*this.speed)}
 get stride(){return this.maxStride*(.58+.42*this.speed)}
 get velocity(){return this.stride*this.cadence}
 seek(t){this.elapsed=Math.max(0,t);this.phase=((this.elapsed*this.cadence/3)%1+1)%1;this.travel=this.elapsed*this.velocity;for(const c of Object.values(this.contact)){c.active=false;c.release=0}this.evaluate(this.elapsed)}
 update(dt){if(!this.paused){const d=clamp(dt,0,.07);this.elapsed+=d;this.phase=(this.phase+this.cadence*d/3)%1;this.travel+=this.velocity*d}return this.evaluate(this.elapsed)}
 _fitted(time){const s=this.basis.spec,b=this.basis,p=this.phase;this.rig.reset();const root=this.rig.root;
  for(const tr of s.tracks){const n=this.rig.nodes[tr.node],r=b.evaluate(tr,p);if(tr.path==='rotation'){let scale=1;if(driven.has(tr.node))scale=.93;const rv=V().fromArray(r).multiplyScalar(scale),a=rv.length(),q=new THREE.Quaternion();if(a>1e-9)q.setFromAxisAngle(rv.multiplyScalar(1/a),a);n.quaternion.copy(this.rig.base[tr.node].q).multiply(q).normalize()}else if(tr.path==='translation'){n.position.set(...r);if(tr.node===s.root_node){n.position.x+=s.root_start[0];n.position.y+=s.root_start[1];n.position.z+=s.root_start[2]+this.travel}}}
  this.model.updateMatrixWorld(true);
 }
 _allVertices(){const a=[];for(const mesh of this.meshes){const pos=mesh.geometry.getAttribute('position');if(!pos)continue;const sampled=Math.min(pos.count,22000),step=Math.max(1,Math.floor(pos.count/sampled));for(let i=0;i<pos.count;i+=step){const v=mesh.getVertexPosition(i,V());mesh.localToWorld(v);a.push({mesh,i,point:v})}}return a}
 _initializeWitnesses(){const verts=this._allVertices();if(verts.length<100)throw Error('NO_SKINNED_VERTICES');for(const [leg,name] of Object.entries(witnessBones)){
   const bone=this.rig.nodes[name],p=bone.getWorldPosition(V());
   let nearby=verts.map(v=>({v,d:v.point.distanceToSquared(p)})).filter(x=>x.d<.18*.18);
   if(nearby.length<6){nearby=verts.map(v=>({v,d:v.point.distanceToSquared(p)})).sort((a,b)=>a.d-b.d).slice(0,180)}
   if(nearby.length<6)throw Error('NO_HOOF_GEOMETRY_'+leg);
   const floor=Math.min(...nearby.map(x=>x.v.point.y));const patch=nearby.filter(x=>x.v.point.y<=floor+.018).sort((a,b)=>a.d-b.d).slice(0,16).map(x=>({mesh:x.v.mesh,i:x.v.i}));
   if(patch.length<3)throw Error('INSUFFICIENT_SOLE_PATCH_'+leg);
   const world=V();for(const x of patch){const q=x.mesh.getVertexPosition(x.i,V());x.mesh.localToWorld(q);world.add(q)}world.multiplyScalar(1/patch.length);
   const local=bone.worldToLocal(world.clone());this.contact[leg]={name,bone,joints:solveBones[leg].map(n=>this.rig.nodes[n]),patch,local,active:false,anchor:null,release:0,groundY:floor,failures:0,maxDrift:0};
  }
 }
 _realWitness(c){const a=V();for(const x of c.patch){const v=x.mesh.getVertexPosition(x.i,V());x.mesh.localToWorld(v);a.add(v)}return a.multiplyScalar(1/c.patch.length)}
 _marker(c){return c.bone.localToWorld(c.local.clone())}
 _deriveContactSchedule(){const N=288,s=this.basis.spec,prevTravel=this.travel,prevSpeed=this.speed;this.speed=.5;this.maxStride=Math.min(Math.max(.045,Math.abs(this.basis.defaultStride)),.24);
  const coords={};for(const k of Object.keys(this.contact))coords[k]=[];
  for(let i=0;i<N;i++){this.phase=i/N;this.travel=0;this._fitted(0);const root=this.rig.root.getWorldPosition(V());for(const [k,c] of Object.entries(this.contact)){const w=this._realWitness(c);coords[k].push({y:w.y,z:w.z-root.z})}}
  for(const [k,c] of Object.entries(this.contact)){
   const v=coords[k],floor=Math.min(...v.map(x=>x.y)),span=Math.max(...v.map(x=>x.y))-floor;
   // The skinned sole determines stance, not an animation-track or bone-pivot proxy.
   const threshold=floor+Math.max(.014,Math.min(.038,span*.26));
   const raw=v.map((x,i)=>{const a=v[(i-2+N)%N],b=v[(i+2)%N];return x.y<=threshold && (b.z-a.z)<.007});
   // Suppress isolated contact flickers; no arbitrary four-beat phase assignments.
   c.mask=raw.map((_,i)=>{let q=0;for(let d=-2;d<=2;d++)if(raw[(i+d+N)%N])q++;return q>=3});
   const count=c.mask.filter(Boolean).length;
   if(count<N*.06||count>N*.76)throw Error('CONTACT_SCHEDULE_UNRELIABLE_'+k+':'+count+'/'+N);
   c.contactFraction=count/N;c.groundY=floor;
   const backward=v.filter((_,i)=>c.mask[i]).map(x=>x.z);c.physicalReach=Math.max(...backward)-Math.min(...backward);
  }
  const reach=Math.min(...Object.values(this.contact).map(c=>c.physicalReach));if(!Number.isFinite(reach)||reach<.04)throw Error('WALK_CONTACT_REACH_UNRELIABLE:'+reach);this.maxStride=Math.min(this.maxStride,reach*.82);
  this.speed=prevSpeed;this.travel=prevTravel;this.phase=0;this._fitted(0);
 }
 _solve(c,target){const worldX=new THREE.Vector3(1,0,0),jointPos=V(),point=V(),derivative=V();let err=Infinity;
  for(let iter=0;iter<16;iter++){
   for(const joint of c.joints){joint.getWorldPosition(jointPos);
    point.copy(this._marker(c));derivative.copy(worldX).cross(point.sub(jointPos));
    const e=target.clone().sub(this._marker(c));const den=derivative.lengthSq();if(den<1e-7)continue;
    const delta=clamp(e.dot(derivative)/den,-.10,.10)*.72;
    const parent=joint.parent;const pq=parent.getWorldQuaternion(new THREE.Quaternion());const qworld=new THREE.Quaternion().setFromAxisAngle(worldX,delta);joint.quaternion.premultiply(pq.clone().invert().multiply(qworld).multiply(pq)).normalize();this.model.updateMatrixWorld(true);
   }
   err=this._marker(c).distanceTo(target);if(err<.0015)break;
  }
  return err;
 }
 evaluate(time){this._fitted(time);const N=288,p=this.phase,index=Math.floor(p*N)%N;let maxDrift=0,stance=0,failures=0;const feet={};
  for(const [name,c] of Object.entries(this.contact)){
   const planted=!!c.mask[index],reference=this._marker(c);
   if(planted){if(!c.active){c.anchor=reference.clone();c.active=true;c.release=0;}const err=this._solve(c,c.anchor);const patchDrift=this._realWitness(c).distanceTo(c.anchor);c.maxDrift=Math.max(c.maxDrift,patchDrift);maxDrift=Math.max(maxDrift,patchDrift);stance++;if(err>.013||patchDrift>.025)c.failures++;feet[name]={contact:true,drift:patchDrift,solveError:err};}
   else{if(c.active){c.active=false;c.release=1;c.lastAnchor=c.anchor.clone()}
    if(c.release>0){const original=this._marker(c),weight=c.release;const target=original.clone().lerp(c.lastAnchor,weight);target.y=Math.max(target.y,original.y)+.014*Math.sin(Math.PI*(1-weight));this._solve(c,target);c.release=Math.max(0,c.release-.09)}
    feet[name]={contact:false,drift:0};}
   failures+=c.failures;
  }
  this.status={mode:MODE,speed:this.speed,velocity:this.velocity,stride:this.stride,cadence:this.cadence,phase:p,stance,maxDrift,failures,feet,contactFractions:Object.fromEntries(Object.entries(this.contact).map(([k,c])=>[k,c.contactFraction]))};return this.status;
 }
}
