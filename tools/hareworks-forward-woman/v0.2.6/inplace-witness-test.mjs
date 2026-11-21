import fs from 'node:fs';import assert from 'node:assert/strict';
import {deriveInPlace,poseInPlace,ROOT} from './inplace-kernel.mjs';
const w=JSON.parse(fs.readFileSync(new URL('./source-witness.json',import.meta.url)));
assert.equal(w.sourceSha256,'a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6');
assert.equal(w.clip,'Walk_Backward');assert.equal(w.samples.length,61);
const N=720,bones={};for(let b=0;b<74;b++){const name=b===0?ROOT:'Bone_'+b;bones[name]={pos:[],quat:[],scale:[]};
 for(let i=0;i<N;i++){
  const t=(i/N)*w.duration;const ind=Math.max(0,Math.min(59,w.samples.findIndex((s,j)=>j<60&&s.t<=t&&w.samples[j+1].t>=t)));const k=ind<0?59:ind;
  const a=w.samples[k],z=w.samples[k+1],f=Math.max(0,Math.min(1,(t-a.t)/(z.t-a.t)));
  const xyz=a.p.map((x,k)=>x+(z.p[k]-x)*f);bones[name].pos.push(name===ROOT?xyz:[0,b*.001,0]);
  bones[name].quat.push([0,0,0,1]);bones[name].scale.push([1,1,1]);
 }
}
const cal={sampleCount:N,bones};const plan=deriveInPlace(cal);
assert.ok(plan.cleanPhase>.97&&plan.cleanPhase<.99,'safely detected terminal reset in actual source curve');
assert.ok(plan.cycleTravel[2]<-1.04&&plan.cycleTravel[2]>-1.12,'travel recovered from actual source curve');
assert.ok(plan.resetRootStep===null||plan.resetRootStep>.05,'sampled reset only when observed');
const checkpoints=[0,.2,.55,.9,.999999];for(const p of checkpoints){let r=poseInPlace(cal,plan,p).bones[ROOT].position;assert.ok(Math.abs(r[2]-.1065)<.06,`in-place root from actual source at phase=${p}: ${r[2]}`)}
console.log('REAL_61_SOURCE_WITNESS_TEST_PASS 74 synthetic joint scaffolds; observed root reset verified, actual GLB browser parity still pending');
