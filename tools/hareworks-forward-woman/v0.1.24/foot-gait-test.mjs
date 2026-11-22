import assert from 'node:assert/strict';
import {phase01} from './root-motion.mjs';
import {sourceAt,supportMode,SourceFootContact} from './foot-gait.mjs';
const n=360;
const samples=Array.from({length:n},(_,i)=>{
 const q=i/n,theta=q*2*Math.PI,z=.28*Math.cos(theta);
 return {phase:q,hip:[.10,.91,0],knee:[.10,.55,.06],ankle:[.10,.21+.03*Math.max(0,Math.sin(theta)),z],
  heel:[.10,.015,z-.12],sole:[.10,.025,z],toe:[.10,.04,z+.12],q:[0,0,0,1]};
});
assert.equal(phase01(-.2),.8);
assert.equal(supportMode({heel:[0,-.03,0],toe:[0,.03,0]},0),'heel');
for(const q of [0,.1,.24,.50,.75,.999]){
 const sample=sourceAt(samples,q);
 for(const key of ['hip','knee','ankle','heel','sole','toe'])
  assert.equal(sample[key].length,3,key+' length');
 for(const key of ['hip','knee','ankle','heel','sole','toe'])
  assert(sample[key].every(Number.isFinite),key+' finite');
}
const gait={start:.10,duty:.58};
const fixed={heel:[.1,0,.15],sole:[.1,0,.25],toe:[.1,0,.35],ankle:[.1,.2,.25]};
const readWitness=kind=>fixed[kind].slice();
const c=new SourceFootContact({samples,gait,sourceGround:0,readWitness,rootAt:q=>q*1.2});
const a=c.step({phase:.12,totalPhase:.12,worldZ:.11});
assert(a.planted&&a.pivot==='heel');
const pin=a.anchor.slice();
for(const q of [.13,.18,.23,.3,.38,.45,.55,.62]){
 const b=c.step({phase:q,totalPhase:q,worldZ:q*1.2});
 assert(b.planted);
 assert.deepEqual(b.anchor,pin,'stance world anchor moved while rocker was constant');
 assert(b.ankleTarget.every(Number.isFinite));
}
const lift=c.step({phase:.70,totalPhase:.70,worldZ:.84});
assert(!lift.planted&&lift.pivot==='air');
assert(lift.ankleTarget.every(Number.isFinite));
assert(c.transitions>=2);
const terrain=(x,z)=>.10+.02*z;
const onHill=new SourceFootContact({samples,gait,sourceGround:0,readWitness,rootAt:q=>q*1.2,terrainAt:terrain});
const h=onHill.step({phase:.12,totalPhase:.12,worldZ:.11});
assert(Math.abs(h.anchor[1]-terrain(h.anchor[0],h.anchor[2]))<1e-12);
const reverse=new SourceFootContact({samples,gait,sourceGround:0,readWitness,rootAt:q=>q*1.2,reverseRocker:true});
const reverseStart=reverse.step({phase:.12,totalPhase:.12,worldZ:.11});
assert(reverseStart.planted&&reverseStart.anchor,'reverse rocker option is accepted');
assert.throws(()=>new SourceFootContact({samples,gait:{start:.1,duty:.30},sourceGround:0,readWitness}),/INVALID_SOURCE_STANCE_WINDOW/);
assert.throws(()=>sourceAt(samples.slice(0,5),.2),/SOURCE_SAMPLES_INSUFFICIENT/);
console.log('V024_CURRENT_FOOT_GAIT_API_CONTACT_TEST_PASS: sourceAt, phase01, heel stance lock, release, terrain anchor, reverse option, failures');
