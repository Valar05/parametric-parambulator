import assert from 'node:assert/strict';
import {SourceFootContact} from './foot-gait.mjs';
import {speedGait,transformSourceFoot} from './speed-gait.mjs';
const n=60,original=Array.from({length:n},(_,i)=>{
 const q=i/n,theta=q*2*Math.PI,ankle=[.11,.18,.37*Math.sin(theta)];
 return {phase:q,hip:[.06,.91,0],knee:[.11,.54,.1],ankle,
   heel:[ankle[0],.01,ankle[2]-.12],sole:[ankle[0],0,ankle[2]],toe:[ankle[0],.01,ankle[2]+.12],q:[0,0,0,1]};
});
let foot=[.1,.19,0],contact=new SourceFootContact({samples:original,
 gait:{start:.1,duty:.58},sourceGround:0,
 readWitness:key=>key==='ankle'?foot.slice():[.04,0,1.2],
 transformSource:(s,gait)=>transformSourceFoot(s,'left',gait)});
let pin=null,planted=0,updates=0,lastDuty=null;
for(let i=0;i<900;i++){
 const requested=i<300?.30:i<600?.8:.52, gait=speedGait(requested,1.224546);
 const x=contact.step({phase:(i/300)%1,totalPhase:i/300,worldZ:i*.001,gait});
 if(x.planted){if(pin!==null)assert.deepEqual(x.anchor,pin,'planted anchor moved');pin=x.anchor;planted++;}
 else pin=null;
 if(lastDuty!==null&&lastDuty!==contact.activeDuty){updates++;assert(pin!==null);}
 lastDuty=contact.activeDuty;
}
assert(planted>180&&updates>=2&&contact.transitions>3);
console.log('V017_PLANTED_WORLD_CONTACT_STAYS_FIXED_SPEED_CHANGES_PASS transitions='+contact.transitions);
