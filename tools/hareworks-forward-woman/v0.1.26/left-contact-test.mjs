import assert from 'node:assert/strict';
import {sourceContactWindow,isSourcePlanted,projectedSourceKnee,targetTravelX,travelPhaseRate} from './left-contact.mjs';
const N=720,D=1.166667,travel=1.43;
for(const start of [.05,.30,.60]){
 const samples=Array.from({length:N},(_,i)=>{
  const q=i/N, p=((q-start+1)%1),stance=p<.58;
  // Physically planted source ankle has approximately zero horizontal speed.
  let x=stance?.4:.4+(.28*(p-.58)/.42),y=stance?.05:.05+.18*Math.sin(Math.PI*(p-.58)/.42)**2;
  return {ankle:[x,y,.1]};
 });
 const found=sourceContactWindow(samples,D);
 assert(found.duty>=.25&&found.duty<=.75,JSON.stringify(found));
 assert(isSourcePlanted(found.start+.02,found));
 assert(!isSourcePlanted(found.start+found.duty+.07,found));
}
assert.equal(targetTravelX({totalPhase:2,travelPerCycle:travel,speed:1.23}),2.86);
assert(Math.abs(travelPhaseRate(1.23,travel)*travel-1.23)<1e-12);
let a=projectedSourceKnee([0,.85,0],[.05,.49,.25],[0,.13,0],[.025,.15,.035]);
assert(a.valid&&Math.abs(Math.hypot(...a.knee.map((v,i)=>v-[0,.85,0][i]))-a.upperLength)<1e-8);
assert(!projectedSourceKnee([0,.85,0],[.05,.49,.25],[0,.13,0],[6,.15,.035]).valid);
assert.throws(()=>sourceContactWindow(Array.from({length:60},()=>({ankle:[0,0,0]})),D),/INVALID/);
assert.throws(()=>travelPhaseRate(.5,0),/INVALID/);
console.log('LEFT_AUTHORED_CLIP_PHASE_CONTACT_IK_TEST_PASS samples='+N+' source=Cautious_Crouch_Walk_Left');
