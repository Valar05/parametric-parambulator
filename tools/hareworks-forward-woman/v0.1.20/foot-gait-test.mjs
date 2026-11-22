import assert from 'node:assert/strict';
import {phase01,sourceAt,inferContacts,swingResidual,SourceFootContact,supportMode} from './foot-gait.mjs';
const n=360,samples=Array.from({length:n},(_,i)=>{
 const p=i/n,stance=p>=.08&&p<.62,h=stance?0:.16*Math.sin(Math.PI*((p-.62+1)%1)/.46)**2;
 const z=.35*Math.cos(2*Math.PI*p),ankle=[.1,.2+h,z];
 return {phase:p,ankle,heel:[.1,h,z-.10],toe:[.1,h,z+.12],sole:[.1,h,z],q:[0,0,0,1]};
});
assert.equal(phase01(-.2),.8);
const g=inferContacts(samples);
assert(g.duty>.3&&g.duty<.8,JSON.stringify(g));
assert(sourceAt(samples,.333).ankle.every(Number.isFinite));
assert(swingResidual(samples,g,g.start+g.duty+.1).every(Number.isFinite));
assert.equal(supportMode({heel:[0,-.03,0],toe:[0,.03,0]},0),'heel');
let witness={heel:[0,0,0],toe:[0,0,.2],sole:[0,0,.1],ankle:[0,.2,0]};
const c=new SourceFootContact({samples,gait:g,sourceGround:0,readWitness:x=>witness[x]});
let first=c.step({phase:g.start+.01,worldZ:0,stride:.65});
assert(first.planted&&first.anchor&&first.pivot);
const anchor=first.anchor.slice();
for(let k=0;k<Math.floor(g.duty*n)-3;k++){let f=c.step({phase:g.start+.01+(k/n),worldZ:k*.002,stride:.65});assert(f.planted);if(f.pivot===first.pivot)assert.deepEqual(f.anchor,anchor)}
let air=c.step({phase:g.start+g.duty+.005,worldZ:.4,stride:.65});assert(!air.planted&&air.ankleTarget.every(Number.isFinite));
assert.throws(()=>inferContacts([{heel:[0,0,0]}]),/INVALID/);
assert.throws(()=>inferContacts(Array.from({length:n},()=>({ankle:[0,0,0],heel:[0,0,0],toe:[0,0,0],sole:[0,0,0],q:[0,0,0,1]}))),/CLEARANCE/);
console.log('SOURCE_GAIT_UNIT_PASS',JSON.stringify(g));
