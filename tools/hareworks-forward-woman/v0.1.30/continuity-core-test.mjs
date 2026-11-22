import assert from 'node:assert/strict';
import {stanceWeight,correctionWeight} from './continuity-core.mjs';
for(const start of [.03,.4,.93]){
 const window={start,duty:.46};
 const w=(t)=>stanceWeight((start+t+1)%1,window);
 assert(w(0)<1e-9);assert(w(.46)<1e-9);assert(w(.23)>.99);
 for(const edge of [0,.46])assert(Math.abs(w(edge+1e-6)-w(edge-1e-6))<.000001);
 let maxJump=0;for(let i=1;i<=10000;i++)maxJump=Math.max(maxJump,Math.abs(w(i/10000)-w((i-1)/10000)));
 assert(maxJump<.002,maxJump);
}
for(const limit of [.035,.085]){
 assert.equal(correctionWeight(0,limit),1);
 assert.equal(correctionWeight(limit,limit),0);
 for(let i=1;i<=10000;i++)assert(Math.abs(correctionWeight(i/10000*limit,limit)-correctionWeight((i-1)/10000*limit,limit))<.002);
}
console.log('CONTACT_TRANSITION_C0_CONTINUITY_PASS');
