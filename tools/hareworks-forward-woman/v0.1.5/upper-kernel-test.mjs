import assert from 'node:assert/strict';
import {TAU,quatMultiply,quatConjugate,quatLog,quatExp,quatAngle,fitHarmonics,evalHarmonics,fitVectorSeries,evalVectorSeries,angularStepSeries} from './upper-kernel.mjs';
const near=(a,b,e=1e-7)=>assert.ok(Math.abs(a-b)<e,`${a} != ${b}`);
const s=[0.22,-.13,.33],q=quatExp(s);const id=quatMultiply(q,quatConjugate(q));near(id[3],1);for(let i=0;i<3;i++)near(id[i],0);
const r=quatLog(q);for(let i=0;i<3;i++)near(r[i],s[i]);near(quatAngle(q,q.map(x=>-x)),0);
const N=240,values=Array.from({length:N},(_,i)=>.2*Math.sin(TAU*i/N)+.09*Math.cos(2*TAU*i/N)-.07*Math.sin(3*TAU*i/N));
const c=fitHarmonics(values,4);near(evalHarmonics(c,0),0);near(evalHarmonics(c,1),0);near(evalHarmonics(c,-1),0);
for(let i=0;i<N;i++){const t=i/N;near(evalHarmonics(c,t),values[i]-values[0],1e-7)}
for(let limit=1;limit<=4;limit++){near(evalHarmonics(c,0,limit),0);near(evalHarmonics(c,1,limit),0)}
const probes=Array.from({length:N},(_,i)=>[values[i],values[(i+N/2)%N]*.4,values[i]*.2]);
const fitted=fitVectorSeries(probes);const at=t=>evalVectorSeries(fitted,t,3,.75);
near(at(0)[0],0);near(at(1)[0],0);assert.ok(angularStepSeries(at,[0,0,0,1],120)<.10);
assert.throws(()=>fitHarmonics([NaN,1,2,3],1),/UPPER_BAD/);
assert.throws(()=>evalVectorSeries(fitted,.3,4,-1),/UPPER_STRENGTH/);
assert.throws(()=>quatLog([0,0,0,0]),/UPPER_QUAT_ZERO/);
console.log('UPPER_PHASE_FIT=PASS quaternion log/exp, sign parity, anchored periodic loops, constrained harmonic modes, synthetic 120Hz continuity, malformed-data rejection');
