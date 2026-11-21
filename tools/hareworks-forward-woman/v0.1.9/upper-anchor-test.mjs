import assert from 'node:assert/strict';
import {fitSourceAnchoredTrack,evalSourceAnchoredTrack} from './upper-anchor.mjs';
import {quatAngle,quatExp,quatMultiply} from '../v0.1.5/upper-kernel.mjs';
// Source begins 81 degrees from bind pose, explicitly reproducing the v0.1.7 failure class.
const base=quatExp([0,1.413716694,0]),N=120;
const samples=Array.from({length:N},(_,i)=>{
 const q=i/N,drive=.17*Math.sin(Math.PI*2*q)+.09*Math.sin(Math.PI*4*q);
 return {quaternion:quatMultiply(base,quatExp([drive,0,0])),position:[.21,-.04+.015*Math.sin(Math.PI*2*q),.05]};
});
const fit=fitSourceAnchoredTrack(samples,12);
assert.equal(fit.sampleCount,120);
for(const strength of [0,.7,1])for(const harmonics of [3,4,8,12]){
 const zero=evalSourceAnchoredTrack(fit,0,harmonics,strength);
 assert(quatAngle(zero.quaternion,base)<1e-6,'source t0 quaternion must exactly match original');
 assert(zero.position.every((v,k)=>Math.abs(v-samples[0].position[k])<1e-12));
 const seam=evalSourceAnchoredTrack(fit,1,harmonics,strength);
 assert(quatAngle(seam.quaternion,zero.quaternion)<1e-6);
}
for(let i=0;i<N;i++){
 const p=evalSourceAnchoredTrack(fit,i/N,4,1);
 assert(quatAngle(p.quaternion,samples[i].quaternion)<.005,'known 2-harmonic source must be reproduced');
 assert(Math.hypot(...p.position.map((v,k)=>v-samples[i].position[k]))<1e-5);
}
// Negative test: earlier generator falsely used bind identity as its source-zero pose.
assert(quatAngle([0,0,0,1],base)>.8,'old baseline would fail loudly');
for(const wrong of [[],[{quaternion:[0,0,0,1],position:[0,0,0]}]])assert.throws(()=>fitSourceAnchoredTrack(wrong,12),/SAMPLES/);
assert.throws(()=>evalSourceAnchoredTrack(fit,.2,13,1),/HARMONICS/);
console.log('SOURCE_ZERO_ANCHOR_PASS 81deg bind/source discrepancy, exact t0 + seam, nonzero pose, 120 synthetic samples, negative fixtures');
