import assert from 'node:assert/strict';
import {speedGait,blendMotion,transformSourceFoot,rootStepDistance} from './speed-gait.mjs';
const D=1.224546;
const slow=speedGait(.30,D),normal=speedGait(.52,D),fast=speedGait(.8,D);
assert(slow.stride<normal.stride&&normal.stride<fast.stride,'world step distances must differ');
assert(slow.cadence<normal.cadence&&normal.cadence<fast.cadence);
assert.equal(normal.stride,D,'default preserves accepted full leg stride');
assert.equal(normal.scale,1);
assert(slow.scale>.95&&fast.scale<1.02,'stride must stay in real anatomical reach envelope');
assert(Math.abs(normal.stepDistance-D/2)<1e-12);
for(const speed of [.01,.15,.3,.52,.7,.8]){
 const m=speedGait(speed,D),test={hip:[.07,.89,.11],knee:[.02,.5,.21],ankle:[.10,.18,.40],heel:[.11,.1,.32],sole:[.10,.1,.41],toe:[.1,.11,.51]};
 for(const side of ['left','right']){
  const t=transformSourceFoot(test,side,m);
  assert.equal(t.ankle[2],test.ankle[2],'forbidden: hip-to-ankle Z compression');
  assert.equal(t.ankle[1],test.ankle[1],'forbidden: adjust ankle height');
  for(const part of ['heel','sole','toe']){
   assert.equal(t[part][2],test[part][2]);assert.equal(t[part][1],test[part][1]);
  }
 }
 assert(Math.abs(m.cadence*m.stride-speed)<1e-11,'speed is physical travel rate');
}
const curve={stride:D},linear=(_,q)=>D*q;
let state=speedGait(.52,D),q=0,world=0;
for(const requested of [.30,.8,.52,0,.8,.30])for(let j=0;j<240;j++){
 state=blendMotion(state,speedGait(requested,D),1/120);
 const nq=q+state.cadence/120,dist=rootStepDistance(linear,curve,q,nq,state);
 assert(Number.isFinite(dist)&&dist>=-1e-12&&dist<.015);
 world+=dist;q=nq;
}
assert(world>1);
assert.throws(()=>speedGait(NaN,D));
console.log('V017_ACTUAL_FOOTFALL_STRIDE_AND_CADENCE_PASS slow='+slow.stepDistance.toFixed(4)+' middle='+normal.stepDistance.toFixed(4)+' fast='+fast.stepDistance.toFixed(4));
console.log('V017_ORIGINAL_LEG_REACH_UNCOMPRESSED_AND_SPEED_TRANSITIONS_PASS');
