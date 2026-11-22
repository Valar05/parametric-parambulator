import assert from 'node:assert/strict';
import {sourceAt,supportMode,SourceFootContact} from './foot-gait.mjs';
import {phase01} from './root-motion.mjs';
const n=360;
const samples=Array.from({length:n},(_,i)=>{
 const q=i/n,angle=q*2*Math.PI,ankle=[.1,.23+.05*Math.max(0,Math.sin(angle)),.35*Math.cos(angle)];
 return {phase:q,hip:[.1,1,0],knee:[.1,.55,.05],ankle,
  heel:[.1,.04,ankle[2]-.12],sole:[.1,.02,ankle[2]],toe:[.1,.04,ankle[2]+.12],q:[0,0,0,1]};
});
assert(sourceAt(samples,.2).ankle.every(Number.isFinite));
assert.equal(phase01(-.1),.9);
assert.equal(supportMode({heel:[0,-.03,0],toe:[0,.03,0]},0),'heel');
let current={heel:[.1,0,.0],sole:[.1,0,.10],toe:[.1,0,.21],ankle:[.1,.23,.11]};
const c=new SourceFootContact({samples,gait:{start:0,duty:.60},sourceGround:.02,readWitness:k=>current[k],rootAt:q=>q*1.2});
let p=c.step({phase:.01,worldZ:.01,totalPhase:.01});assert(p.planted&&p.anchor);
const prev=p.anchor.slice();
p=c.step({phase:.03,worldZ:.04,totalPhase:.03});if(p.pivot==='heel')assert.deepEqual(p.anchor,prev);
const before=current.ankle.slice();
p=c.step({phase:.601,worldZ:.68,totalPhase:.601});assert(!p.planted&&p.ankleTarget.every(Number.isFinite));
// At liftoff, source swing inherits the previously solved foot without a reset.
assert(Math.hypot(...p.ankleTarget.map((v,i)=>v-before[i]))<.1);
assert.throws(()=>new SourceFootContact({samples,gait:{start:0,duty:.31},sourceGround:0,readWitness:k=>current[k]}),/INVALID_SOURCE_STANCE/);
console.log('CONTACT_TRANSITION_UNIT_PASS');
