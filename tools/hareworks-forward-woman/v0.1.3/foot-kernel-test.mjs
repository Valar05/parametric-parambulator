import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {legAt,rotateY,kneeFromTarget,validateFootProfile,magnitude,add,sub} from './foot-kernel.mjs';
const here=new URL('.',import.meta.url);
const profile=JSON.parse(readFileSync(new URL('./foot-profile.json',here)));
const witness=JSON.parse(readFileSync(new URL('./reference-leg-witnesses.json',here)));
assert.ok(validateFootProfile(profile));
assert.equal(witness.schema,'hareworks-forward-woman-leg-witnesses-v0.1.3');
assert.equal(witness.sourceSha256,profile.sourceSha256);
assert.equal(witness.samples.length,60);
const result={schema:'hareworks-forward-woman-v0.1.3-offline-geometry',sourceSha256:profile.sourceSha256,holdout:'odd source 60Hz frames; even for fitting',fps:[30,60,120,240],sides:{}};
for(const side of ['left','right']) {
 let maxAnkle=0,maxKnee=0,ankleSq=0,kneeSq=0,n=0;
 for(let i=1;i<witness.samples.length;i+=2){
  const sample=witness.samples[i],rig=sample.legs[side];
  const g=legAt(profile,side,sample.t);
  const ankle=add(rig.hip,rotateY(g.ankleLocal,sample.pelvisYaw));
  const knee=kneeFromTarget(rig.hip,ankle,profile[side].upperLength,profile[side].lowerLength,rotateY(g.poleLocal,sample.pelvisYaw));
  const ea=magnitude(sub(ankle,rig.ankle)),ek=magnitude(sub(knee,rig.knee));
  maxAnkle=Math.max(maxAnkle,ea);maxKnee=Math.max(maxKnee,ek);ankleSq+=ea*ea;kneeSq+=ek*ek;n++;
 }
 assert.ok(Math.sqrt(ankleSq/n)<.004,`${side} ankle holdout mismatch`);
 assert.ok(Math.sqrt(kneeSq/n)<.007,`${side} knee holdout mismatch`);
 let minReach=Infinity,maxFront=-Infinity,maxStep={};
 for(const fps of result.fps){
  let prev=null,maxIncrement=0;
  for(let i=0;i<=Math.floor(profile.duration*fps);i++){
   const t=i/fps;if(t>=profile.duration-.0001)continue;
   const g=legAt(profile,side,t),d=magnitude(g.ankleLocal),reach=profile[side].upperLength+profile[side].lowerLength;
   minReach=Math.min(minReach,reach-d);maxFront=Math.max(maxFront,g.ankleLocal[2]);
   assert.ok(d<reach,`${side} unreachable at ${fps}Hz t=${t} d=${d} limit=${reach}`);
   // No implied pose from a constant: exercise each actual profile and knee solver.
   const ankle=add([0,0,0],g.ankleLocal),knee=kneeFromTarget([0,0,0],ankle,profile[side].upperLength,profile[side].lowerLength,g.poleLocal);
   assert.ok(knee.every(Number.isFinite));
   if(prev)maxIncrement=Math.max(maxIncrement,magnitude(sub(ankle,prev)));
   prev=ankle;
  }
  maxStep[fps]=maxIncrement;
 }
 assert.ok(maxFront>.30,`${side} never advances ahead of hip`);
 assert.ok(minReach>.0007,`${side} too near reach singularity ${minReach}`);
 const a=legAt(profile,side,0),b=legAt(profile,side,profile.duration);
 assert.ok(magnitude(sub(a.ankleLocal,b.ankleLocal))<1e-9,`${side} loop geometry discontinuous`);
 result.sides[side]={holdoutSamples:n,ankleRms:Math.sqrt(ankleSq/n),kneeRms:Math.sqrt(kneeSq/n),maxAnkle,maxKnee,minReach,maxFront,maxAnkleStep:maxStep};
}
console.log('FOOT_KERNEL_TESTS=PASS');console.log(JSON.stringify(result,null,2));
