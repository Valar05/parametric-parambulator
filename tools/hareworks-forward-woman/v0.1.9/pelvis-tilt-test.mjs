import assert from 'node:assert/strict';
import {quatMultiply,quatExp,quatAngle} from '../v0.1.5/upper-kernel.mjs';
import {yawQuat,decomposeWorldPelvis,fitSourcePelvisTilt,evaluatePelvisWorld,decodePelvisMode} from './pelvis-tilt.mjs';
const N=120,period=Math.PI*2,source=[];
for(let i=0;i<N;i++){
 const t=i/N, yaw=.23+.09*Math.sin(period*t),pitch=.12*Math.sin(period*t),roll=.075*Math.sin(2*period*t);
 const tilt=quatMultiply(quatExp([pitch,0,0]),quatExp([0,0,roll]));
 source.push(quatMultiply(yawQuat(yaw),tilt));
 const split=decomposeWorldPelvis(source.at(-1));
 assert(quatAngle(source.at(-1),quatMultiply(yawQuat(split.yaw),split.tilt))<1e-6);
}
const fit=fitSourcePelvisTilt(source,12);assert(fit.variationDeg>5);
for(let i=0;i<N;i++){
 const s=decomposeWorldPelvis(source[i]),q=evaluatePelvisWorld(fit,i/N,s.yaw,12);
 assert(quatAngle(q,source[i])<.006,'no yaw or pitch/roll sign inversion');
}
for(const n of [4,12]){
 const source0=decomposeWorldPelvis(source[0]);
 const a=evaluatePelvisWorld(fit,0,source0.yaw,n),b=evaluatePelvisWorld(fit,1,source0.yaw,n);
 assert(quatAngle(a,source[0])<1e-6,'exact time-zero source pose');
 assert(quatAngle(a,b)<1e-6,'continuous periodic seam');
}
assert.equal(decodePelvisMode('tilt12-half').gain,.5);
assert.equal(decodePelvisMode('off').harmonics,0);
assert.throws(()=>decodePelvisMode('clip'),/UNAUTHORIZED/);
assert.throws(()=>fitSourcePelvisTilt([[0,0,0,1]]),/SAMPLES/);
assert.throws(()=>decomposeWorldPelvis([0,0,0,0]),/ZERO/);
console.log('PELVIS_YAW_NEUTRAL_SOURCE_FIT_PASS 120 samples, sign, time-zero, seam, bad inputs, preserved yaw');
