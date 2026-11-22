import assert from 'node:assert/strict';
import {kneeFromTarget} from './ik-core.mjs';
const L1=.3567690913,L2=.3803240094;
const H0=[-.15,.85,0],H1=[-.15,.81,.12],A=[-.15,.18,.05],pole=[-.2,.1,.8];
const K0=kneeFromTarget(H0,A,L1,L2,pole),K1=kneeFromTarget(H1,A,L1,L2,pole);
const distance=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
for(const [h,k] of [[H0,K0],[H1,K1]]){assert(Math.abs(distance(h,k)-L1)<1e-8);assert(Math.abs(distance(k,A)-L2)<1e-8)}
assert(distance(K0,K1)>.01,'IK knee must respond to translated hip while ankle remains WORLD anchored');
assert.throws(()=>kneeFromTarget(H0,[3,0,0],L1,L2,pole),/UNREACHABLE/);
console.log('TRUE_TWO_BONE_WORLD_TARGET_GEOMETRY_PASS');
