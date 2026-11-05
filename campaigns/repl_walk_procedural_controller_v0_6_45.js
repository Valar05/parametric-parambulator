// Repl v0.6.45: reference-calibrated, phase-driven procedural WALK only.
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
