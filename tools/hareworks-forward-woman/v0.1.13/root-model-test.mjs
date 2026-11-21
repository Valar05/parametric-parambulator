import assert from 'node:assert/strict';
import fs from 'node:fs';
import {legAt,rotateY} from '../v0.1.3/foot-kernel.mjs';
import {independentPose} from '../v0.1.2/pose-kernel.mjs';
import {inferVelocityContact,buildRootCurve,rootAt,kneeFlexion} from './root-motion.mjs';

const witnesses=JSON.parse(fs.readFileSync(new URL('../v0.1.3/reference-leg-witnesses.json',import.meta.url),'utf8'));
const legs=JSON.parse(fs.readFileSync(new URL('../v0.1.3/foot-profile.json',import.meta.url),'utf8'));
const pelvis=JSON.parse(fs.readFileSync(new URL('../v0.1.2/motion-profile.json',import.meta.url),'utf8'));
const N=witnesses.samples.length;assert.equal(N,60);
const data={left:[],right:[]};const errors={left:[],right:[]};
for(let i=0;i<N;i++){
 const source=witnesses.samples[i],q=i/N,t=q*legs.duration;
 const yaw=independentPose(pelvis,t).pelvisYaw;
 for(const side of ['left','right']){
  const s=source.legs[side],local=legAt(legs,side,t).ankleLocal;
  const r=rotateY(local,yaw),ankle=s.hip.map((v,j)=>v+r[j]);
  const err=Math.hypot(...ankle.map((x,j)=>x-s.ankle[j]));errors[side].push(err);
  // A heel proxy is used ONLY in this source-witness math test. The actual
  // physical heel/sole/toe patches MUST be validated on the real skinned GLB.
  const heel=[ankle[0],s.toe[1]+.014,ankle[2]-.10];
  const toe=s.toe,sole=[(heel[0]+toe[0])/2,Math.min(heel[1],toe[1]),(heel[2]+toe[2])/2];
  data[side].push({phase:q,ankle,hip:s.hip,knee:s.knee,heel,sole,toe,q:[0,0,0,1]});
 }
}
const rms=x=>Math.sqrt(x.reduce((a,b)=>a+b*b,0)/x.length);
const errL=rms(errors.left),errR=rms(errors.right);
assert(errL<.003&&errR<.003,`v0.1.9 source-fit regression ${errL} ${errR}`);
const gaits=Object.fromEntries(['left','right'].map(side=>[side,inferVelocityContact(data[side])]));
for(const side of ['left','right'])assert(gaits[side].duty>.48&&gaits[side].duty<.70,JSON.stringify(gaits[side]));
const root=buildRootCurve(data,gaits);
assert(root.stride>1.06&&root.stride<1.46,'FULL_GAIT_CYCLE_DISTANCE_COUNTED_AS_HALF_CYCLE '+root.stride);
const values={};
for(const side of ['left','right']){
 const s=gaits[side],i0=s.start*N,steps=240;
 const at=q=>{const x=((q%1)+1)%1*N,i=Math.floor(x),t=x-i;const a=data[side][i].ankle,b=data[side][(i+1)%N].ankle;return a.map((v,j)=>v+(b[j]-v)*t)};
 const base=at(s.start)[2]+rootAt(root,s.start);
 let maxDrift=0,maxWrongDrift=0;
 for(let i=0;i<=steps;i++){
  const q=s.start+s.duty*i/steps;
  const exact=at(q)[2]+rootAt(root,q)-base;
  const wrong=at(q)[2]+.68*(q-s.start)-at(s.start)[2];
  maxDrift=Math.max(maxDrift,Math.abs(exact));maxWrongDrift=Math.max(maxWrongDrift,Math.abs(wrong));
 }
 assert(maxDrift<.11,`${side} FULL_CYCLE_WORLD_SUPPORT_DRIFT_TOO_LARGE ${maxDrift}`);
 assert(maxWrongDrift>maxDrift+.09,`${side} WRONG_HALF_STRIDE_NO_LONGER_REJECTED`);
 values[side]={originalFitRMSError:rms(errors[side]),stanceStart:s.start,duty:s.duty,
  maxWorldAnkleDriftBeforePin:maxDrift,rejectedHalfCycleMaxDrift:maxWrongDrift};
}
assert(Math.abs(rootAt(root,2)-2*root.stride)<1e-9,'ROOT_MULTI_CYCLE_SEAM');
assert(Math.abs(rootAt(root,1)-root.stride)<1e-9,'ROOT_FIRST_CYCLE_SEAM');
assert(kneeFlexion(.35,.39,[0,0,0],[0,-.7,0])<50);
const failing={left:data.left.map(x=>({...x,ankle:[1,2,3]})),right:data.right};
assert.throws(()=>inferVelocityContact(failing.left),/AMBIGUOUS/,'FAIL_INJECTED_CONTACT_FLAT');
assert.throws(()=>buildRootCurve({left:data.left,right:data.right.slice(1)},gaits),/ROOT_SAMPLE_COUNT_MISMATCH/,'FAIL_INJECTED_ROOT_SAMPLE_MISMATCH');
console.log('ACCEPTED_V019_MATH_GATE_PASS',JSON.stringify({modelSource:witnesses.sourceSha256,referenceFrames:N,rootFullCycle:root.stride,...values}));
console.log('REAL_SKINNED_GL_B_AND_BROWSER_AUDIT_NOT_YET_RUN');
