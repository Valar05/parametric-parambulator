import assert from 'node:assert/strict';
import {CLIPS,CONTACT,contactWarp,phaseTriplet,quatMul,quatConj,quatNormalize,quatSlerp,quatAngle,transferBone,transferPose,mod1} from './transfer-kernel.mjs';
const near=(a,b,eps=1e-7)=>Math.abs(a-b)<eps;
const axis=(a,deg)=>{const r=deg*Math.PI/360;return [a[0]*Math.sin(r),a[1]*Math.sin(r),a[2]*Math.sin(r),Math.cos(r)]};
assert.deepEqual(CLIPS,['Walking','Walking_Woman','Walk_Backward']);
for(const x of ['left','right']){
 const p=CONTACT.backward[x];const mapped=phaseTriplet(p);
 assert(near(mapped.normal,CONTACT.normal[x]),'normal contact event '+x);
 assert(near(mapped.woman,CONTACT.woman[x]),'woman contact event '+x);
}
for(let i=0,last=-Infinity;i<500;i++){
 const q=CONTACT.backward.left+i/500*(CONTACT.backward.left+1-CONTACT.backward.left);
 const out=contactWarp(q,CONTACT.backward,CONTACT.normal);
 let unwrapped=out;if(unwrapped<CONTACT.normal.left-1e-4)unwrapped+=1;
 assert(unwrapped>=last-1e-8,'monotone gait phase');last=unwrapped;
}
const I=[0,0,0,1],B=axis([0,0,1],24),N=axis([0,1,0],25),W=quatMul(N,axis([1,0,0],20));
const A={quat:B,pos:[2,3,-0.8]},D={quat:N,pos:[1,2,0.3]},F={quat:W,pos:[1.2,2.15,1.8]};
const p=transferBone(A,D,F,1,'mixamorigSpine');
assert(quatAngle(p.quat,quatMul(B,quatMul(quatConj(N),W)))<1e-6,'noncommuting B*inv(N)*W');
assert.deepEqual(p.pos.map(v=>Math.round(v*100)/100),[2.2,3.15,0.7]);
const h=transferBone(A,D,F,1,'mixamorigHips');assert.equal(h.pos[2],A.pos[2],'backward root travel preserved');
const z=transferBone(A,D,F,0,'mixamorigSpine');assert(quatAngle(z.quat,B)<1e-6&&z.pos.every((v,i)=>near(v,A.pos[i])));
const half=transferBone(A,D,F,.5,'mixamorigSpine');assert(near(quatAngle(B,half.quat),quatAngle(B,p.quat)/2,1e-5));
assert.throws(()=>transferBone(A,D,F,1.01,'mixamorigSpine'),/OUT_OF_RANGE/);
assert.throws(()=>quatNormalize([0,0,0,0]),/ZERO/);
assert(quatAngle(quatSlerp(I,axis([0,1,0],95),.5),axis([0,1,0],47.5))<1e-7);
for(let i=0;i<=100;i++)assert(near(mod1(i/100),mod1((i+100)/100)));
// Construct three 74-bone synthetic clip samples, including an animated source style.
const names=['mixamorigHips',...Array.from({length:73},(_,i)=>'Bone_'+i)];
function synthetic(style=0,base=0){const bones={};for(const name of names){
  const quat=[],pos=[];for(let i=0;i<80;i++){
   const q=i/80;quat.push(quatMul(axis([0,0,1],base+8*Math.sin(2*Math.PI*q)),axis([1,0,0],style+5*Math.sin(2*Math.PI*q+style/90))));
   pos.push([.1*Math.sin(2*Math.PI*q),1+.02*Math.cos(2*Math.PI*q),-q*.4]);
  }bones[name]={quat,pos};}
  return {sampleCount:80,bones};}
const clips={Walk_Backward:synthetic(0,-20),Walking:synthetic(0,5),Walking_Woman:synthetic(9,5)};
const a=transferPose(clips,.32,0),b=transferPose(clips,.32,1);
assert.equal(Object.keys(a.bones).length,74);assert(a.nonzeroBoneCount>10);
assert(quatAngle(a.bones.Bone_0.quat,b.bones.Bone_0.quat)>.02,'style actually transfers');
assert.equal(a.bones.mixamorigHips.pos[2],b.bones.mixamorigHips.pos[2]);
const seam0=transferPose(clips,0,1),seam1=transferPose(clips,1-1e-10,1);
assert(quatAngle(seam0.bones.Bone_0.quat,seam1.bones.Bone_0.quat)<1e-6);
console.log('BACKWARD_STYLE_TRANSFER_TEST_PASS: 3-way local delta, contact anchors, noncommuting quaternion, pelvis Z lock, true derived pose, seam');
