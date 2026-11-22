import assert from 'node:assert/strict';
import fs from 'node:fs';
import {sourceKneePlane} from './source-knee-plane.mjs';
const archive=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const lengths=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
assert.equal(archive.samples.length,60);
let cases=0,maxError=0,maxJitter=0,minClearance=Infinity,corrections=0,physicallyInfeasible=0;
for(const side of ['left','right']){
 const {upperLength:l1,lowerLength:l2}=lengths[side],sign=side==='left'?1:-1;
 let prior=null;
 // Reconstruct source geometric knees with the original 60-frame phases.
 for(let i=0;i<60;i++){
  const s=archive.samples[i],data=s.legs[side];
  const center=(s.legs.left.hip[0]+s.legs.right.hip[0])/2;
  const a=sourceKneePlane(data.hip,data.ankle,data.hip,data.knee,l1,l2,side,center,null,0);
  const error=Math.hypot(...a.knee.map((v,j)=>v-data.knee[j]));
  maxError=Math.max(maxError,error);minClearance=Math.min(minClearance,a.sideClearance);
  assert(a.sideClearance>.018-1e-6,side+' knee crossed centerline at '+i);
  assert(a.hipToKnee<1e-6&&a.kneeToAnkle<1e-6);
  cases++;
 }
 // Force alternating left-right crossing and contact-driven ankle disturbances.
 // Keep every source ankle within the two anatomical links' feasible reach.
 for(let i=0;i<1200;i++){
  const s=archive.samples[i%60],data=s.legs[side],center=(s.legs.left.hip[0]+s.legs.right.hip[0])/2;
  const displacement=.055*Math.sin(i*.083)+(i%190>130?.07:0);
  const proposed=[data.ankle[0]-sign*displacement,data.ankle[1],data.ankle[2]];
  const d=Math.hypot(...proposed.map((v,j)=>v-data.hip[j]));
  const max=l1+l2-.00035,min=Math.abs(l1-l2)+.00035;
  const a=d>max||d<min?data.hip.map((v,j)=>v+(proposed[j]-v)*Math.max(min,Math.min(max,d))/d):proposed;
  const adversarialKnee=i%230>160?data.knee.map((v,j)=>j===0?v-sign*.32:v):data.knee;
  let k;try{k=sourceKneePlane(data.hip,a,data.hip,adversarialKnee,l1,l2,side,center,prior,1/120,.018)}
  catch(e){if(/KNEE_(CENTERLINE_GEOMETRY|STRAIGHT_LEG_CENTERLINE)_INFEASIBLE/.test(e.message)){physicallyInfeasible++;prior=null;continue}throw e;}
  assert(k.sideClearance>=.018-2e-6,side+' crossing despite guard');
  assert(k.hipToKnee<1e-6&&k.kneeToAnkle<1e-6);
  if(prior){const step=Math.hypot(...k.knee.map((v,j)=>v-prior[j]));maxJitter=Math.max(maxJitter,step)}
  if(k.centerlineCorrected)corrections++;
  prior=k.knee;cases++;
 }
}
assert(maxError<.01,'must reconstruct archived knees, not replace source style');
assert(minClearance>.018,'original source knees are already to the side');
assert(corrections>0,'injected crossing must reach correction rather than a vacuous PASS');
assert.throws(()=>sourceKneePlane([0,0,0],[0,0,3],[0,0,0],[0,.3,.2],.35,.39,'left',0));
assert.throws(()=>sourceKneePlane([0,0,0],[0,0,.2],[0,0,0],[0,.3,.2],.35,.39,'bad',0));
assert.throws(()=>sourceKneePlane([-.30,0,0],[-.31,-.65,0],[-.30,0,0],[-.28,-.3,.2],.35,.39,'left',0),/KNEE_CENTERLINE_GEOMETRY_INFEASIBLE/);
console.log('SOURCE_KNEE_PLANE_60_FRAME_PARITY_PASS maxError='+maxError.toFixed(6)+' minClearance='+minClearance.toFixed(5));
console.log('WORLD_IK_CROSSLINE_GUARD_PASS cases='+cases+' corrections='+corrections+' maxKneeStep='+maxJitter.toFixed(5)+' physicallyImpossibleInjectedCases='+physicallyInfeasible);
