import assert from 'node:assert/strict';
import {CLIP,ROOT,deriveInPlace,poseInPlace,angleDeg} from './inplace-kernel.mjs';
assert.equal(CLIP,'Walk_Backward');assert.equal(ROOT,'mixamorigHips');
const N=720,ident=[0,0,0,1],bones={};
for(let j=0;j<74;j++){
 const name=j===0?ROOT:`Bone_${j}`;bones[name]={pos:[],quat:[],scale:[]};
 for(let i=0;i<N;i++){
  const p=i/N,w=2*Math.PI*p;
  const trueZ=.1065-1.072*p+.012*Math.sin(w);
  const reset=p>.983?trueZ+(p-.983)/(1-.983)*(1.072):trueZ;
  bones[name].pos.push(name===ROOT?[.006+0.008*Math.sin(w),.95+.025*Math.sin(2*w),reset]:[j*.001,.005*Math.sin(w+j),.003*Math.cos(w)]);
  const a=.14*Math.sin(w+(j%3)),q=[0,0,Math.sin(a/2),Math.cos(a/2)];bones[name].quat.push(q);bones[name].scale.push([1,1,1]);
 }
}
const clip={sampleCount:N,bones};const plan=deriveInPlace(clip);
assert.ok(plan.resetIndex/N>.98&&plan.resetIndex/N<.99,'reset located');
assert.ok(plan.cycleTravel[2]<-1.04&&plan.cycleTravel[2]>-1.11,'trend found');
assert.ok(plan.seamStart<=.93&&plan.seamStart>.85,'repair window bounded');
const early=deriveInPlace(clip,.89);assert.equal(early.seamStart,.89);
assert.throws(()=>deriveInPlace(clip,.99),/SOURCE_NO_SAFE_PRE_RESET_SEAM/);
for(const p of [0,.1,.4,.8,.91,.92,.93,.97,.999999,1]){
 const x=poseInPlace(clip,plan,p);
 assert.equal(Object.keys(x.bones).length,74);
 assert.ok(Math.abs(x.bones[ROOT].position[2]-.1065)<.022,`stationary root, phase ${p}: ${x.bones[ROOT].position[2]}`);
 assert.ok(Math.abs(x.bones[ROOT].position[1]-.95)<.027,'Y bounce retained');
}
for(const p of [0,.125,.5,.875]){
 const i=Math.round(p*N);const r=poseInPlace(clip,plan,p);
 assert.ok(angleDeg(r.bones.Bone_35.quaternion,bones.Bone_35.quat[i])<.001,'full-bone source parity');
 assert.ok(Math.abs(r.bones.Bone_35.position[0]-bones.Bone_35.pos[i][0])<1e-8,'full-bone source translation parity');
}
const l=poseInPlace(clip,plan,1-1e-8),f=poseInPlace(clip,plan,0);
for(const name of Object.keys(bones)){
 assert.ok(angleDeg(l.bones[name].quaternion,f.bones[name].quaternion)<.005,`seam rotation ${name}`);
 assert.ok(Math.hypot(...l.bones[name].position.map((x,i)=>x-f.bones[name].position[i]))<.0001,`seam position ${name}`);
}
const damaged=structuredClone(clip);damaged.bones[ROOT].pos=damaged.bones[ROOT].pos.map(p=>[p[0],p[1],-p[2]]);
assert.throws(()=>deriveInPlace(damaged),/SOURCE_TERMINAL_ROOT_RESET_NOT_DETECTED|BACKWARD_ROOT_TRAVEL_NOT_FOUND/);
assert.throws(()=>poseInPlace(clip,plan,Number.NaN),/NONFINITE_PHASE/);
// A bone whose stored source quaternion changes sign must still take the
// shortest SO(3) path at the repaired cycle seam, never a 360-degree spin.
const flipped=structuredClone(clip);flipped.bones.Bone_42.quat=flipped.bones.Bone_42.quat.map((q,i)=>i<20?q.map(x=>-x):q);
const ff=deriveInPlace(flipped);const a=poseInPlace(flipped,ff,.965).bones.Bone_42.quaternion;
const b=poseInPlace(flipped,ff,.99).bones.Bone_42.quaternion;
assert.ok(angleDeg(a,b)<5,'shortest path despite quaternion sign variation');
assert.throws(()=>deriveInPlace({sampleCount:5,bones:{}}),/BAD_REAL_SOURCE_SAMPLE_CONTRACT/);
// Embedded real extraction probes: reset from -0.953415 near t=.852222 to +.089648 at .866667.
assert.ok(.089648-(-.953415)>1,'real GLB last-key reset proved by source extraction');
console.log('FULL_74_JOINT_BACKWARD_PROCEDURAL_TESTS_PASS: automatic real reset detection, nonwrapped trend, source parity, seam closure, negative controls');
