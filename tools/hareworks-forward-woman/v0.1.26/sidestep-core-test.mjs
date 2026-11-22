import assert from 'node:assert/strict';
import {ROOT,CLIPS,angleDeg,calibrate,pose,qm,validate} from './sidestep-core.mjs';
assert.deepEqual(CLIPS,['Cautious_Crouch_Walk_Left','Cautious_Crouch_Walk_Left_inplace']);
assert.ok(angleDeg(qm([0,0,0,1],[0,0,0,1]),[0,0,0,1])<1e-7);
const N=720;
function make(name){const bones={};for(let j=0;j<74;j++){
 const k=j?`Bone_${j}`:ROOT;const p=[],quat=[],scale=[];
 for(let i=0;i<N;i++){const x=i/N,w=2*Math.PI*x,angle=.18*Math.sin(w+j*.03),travel=name===CLIPS[0]?1.43*x:.12*Math.sin(Math.PI*x)**2;
  p.push(k===ROOT?[.006+travel,.83-.024*Math.sin(Math.PI*x)**2,.1+.04*Math.sin(w)]:[j*.001,.03*Math.sin(w+j),-.03*Math.cos(w)]);
  quat.push([0,Math.sin(angle/2),0,Math.cos(angle/2)]);scale.push([1,1,1]);
 }
 bones[k]={pos:p,quat,scale};}
 return {name,sampleCount:N,duration:1.166667,bones,terminalRootTrack:{lastTime:1.166667,lastPosition:[.003,.966,.0896]}}}
for(const k of CLIPS){const c=make(k);assert.equal(validate(c),true);const m=calibrate(c,.93);assert.equal(m.clip,k);
 assert.ok(Math.abs(m.trend[0]-(k===CLIPS[0]?1.43:0))<.007,'measured source root trend');
 for(const p of [0,.1,.25,.5,.85,.929, .97, .999999]){
  const x=pose(c,m,p).bones;assert.equal(Object.keys(x).length,74);
  if(p<.93){const original=c.bones.Bone_20.quat[Math.floor(p*N)];assert.ok(angleDeg(x.Bone_20.quaternion,original)<1,'source joint reconstruction');}
 }
 const p0=pose(c,m,0).bones,pend=pose(c,m,1-1e-8).bones;
 for(const b of Object.keys(p0)){assert.ok(angleDeg(p0[b].quaternion,pend[b].quaternion)<.02,'seam rotations '+b);assert.ok(Math.hypot(...p0[b].position.map((v,i)=>v-pend[b].position[i]))<.0001,'seam positions '+b)}
 assert.ok(Math.abs(pose(c,m,.5).bones[ROOT].position[0]-(k===CLIPS[0]?.006:.126))<.005,'linear travel removed, cyclic sway preserved');
 assert.throws(()=>calibrate(c,.76),/SEAM_START_OUT_OF_RANGE/);assert.throws(()=>pose(c,m,NaN),/BAD_PHASE/);
 const damaged=structuredClone(c);delete damaged.bones.Bone_73;assert.throws(()=>validate(damaged),/SOURCE_NOT_74/);
 const broken=structuredClone(c);broken.bones.Bone_1.pos[3][2]=NaN;assert.throws(()=>validate(broken),/CORRUPT_SOURCE/);
}
console.log('SIDESTEP_V027_INPLACE_SOURCE_PARITY_TESTS_PASS');
