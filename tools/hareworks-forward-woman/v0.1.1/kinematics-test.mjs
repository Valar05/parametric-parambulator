import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {trajectory,worldOffset,inverseWorldOffset} from './gait-kernel.mjs';
const json=f=>JSON.parse(readFileSync(new URL(f,import.meta.url),'utf8'));
const profile=json('./profile.json'),ref=json('./reference-legs.json');
assert.equal(ref.frames.length,60);
assert.equal(ref.sourceSha256,profile.modelSha256);
assert.ok(Math.abs(ref.duration-profile.clipDuration)<1e-4);
function dot(a,b){return a.reduce((r,v,i)=>r+v*b[i],0)}
function minus(a,b){return a.map((v,i)=>v-b[i])}
function plus(a,b){return a.map((v,i)=>v+b[i])}
function mult(a,k){return a.map(v=>v*k)}
function norm(a){return Math.hypot(...a)}
function getKnee(h,a,l1,l2,pole,yaw){
 const diff=minus(a,h),d=norm(diff),u=mult(diff,1/d),alpha=(l1*l1-l2*l2+d*d)/(2*d);
 const c=plus(h,mult(u,alpha)),rad=Math.sqrt(Math.max(0,l1*l1-alpha*alpha));
 const cs=Math.cos(yaw),sn=Math.sin(yaw),pw=[pole[0]*cs+pole[2]*sn,pole[1],-pole[0]*sn+pole[2]*cs];
 const pp=minus(pw,mult(u,dot(pw,u)));
 return plus(c,mult(pp,rad/norm(pp)));
}
const evidence={schema:'hareworks-forward-woman-v0.1.1-node-geometry-proof',referenceSha256:ref.sourceSha256,samples:ref.frames.length,validation:'source 30 Hz complementary holdout',results:{}};
for(const side of ['left','right']){
 const p=profile[side];let errA=0,errK=0,N=0,front=-Infinity,rear=Infinity,maxTargetReach=0;
 for(let i=0;i<ref.frames.length;i++){
  const frame=ref.frames[i],r=frame.feet[side],f=trajectory(frame.t,profile,side),ofs=worldOffset(f,frame.pelvisYaw,r.hip[1]),a=plus(r.hip,ofs);
  const inv=inverseWorldOffset(ofs,frame.pelvisYaw);
  assert.ok(Math.abs(inv.z-f.z)<1e-9&&Math.abs(inv.x-f.x)<1e-9,'angle/sign convention regression');
  const d=norm(minus(a,r.hip)),k=getKnee(r.hip,a,p.upperLength,p.lowerLength,p.pole,frame.pelvisYaw);
  assert.ok(Number.isFinite(k[0]+k[1]+k[2]));
  assert.ok(d<=p.upperLength+p.lowerLength-0.004,'unsupported heel target beyond anatomical reach '+side+' '+i);
  assert.ok(Math.abs(norm(minus(k,r.hip))-p.upperLength)<1e-8,'upper bone not rigid');
  assert.ok(Math.abs(norm(minus(k,a))-p.lowerLength)<1e-8,'lower bone not rigid');
  maxTargetReach=Math.max(maxTargetReach,d);front=Math.max(front,f.z);rear=Math.min(rear,f.z);
  // 60Hz odd frames train, 60Hz even frames represent the held-out 30fps grid.
  if(i%2===0){errA+=norm(minus(a,r.ankle))**2;errK+=norm(minus(k,r.knee))**2;N++;}
 }
 const ankleRMS=Math.sqrt(errA/N),kneeRMS=Math.sqrt(errK/N);
 assert.ok(front>.35,'never plants a leading foot in front of hip');
 assert.ok(rear<-.20,'never swings the foot behind hip');
 assert.ok(ankleRMS<.035,'generated ankle path failed woman reference fit');
 assert.ok(kneeRMS<.055,'IK knee path failed woman reference fit');
 evidence.results[side]={samples:N,front,rear,maxTargetReach,ankleRMS,kneeRMS};
 // The generator must make continuous swing and stance movement at their connection.
 const edge=(p.phaseOffset+profile.beta)*profile.clipDuration;const dt=1e-5;
 const z0=trajectory(edge-dt,profile,side).z,z1=trajectory(edge,profile,side).z,z2=trajectory(edge+dt,profile,side).z;
 assert.ok(Math.abs((z1-z0)-(z2-z1))<.001,'swing/stance velocity discontinuity');
}
// Failure injection: invalid +X/+Z handedness must be detected by the projection round trip.
const sample=worldOffset({x:.3,z:.6,y:.2},.5,.7);assert.ok(Math.abs(inverseWorldOffset(sample,.5).z-.6)<1e-9);
assert.ok(Math.abs(inverseWorldOffset(sample,-.5).z-.6)>.1,'handedness negative-control not detected');
console.log('FORWARD_WOMAN_30FPS_REFERENCE_HOLDOUT=PASS');console.log(JSON.stringify(evidence,null,2));
