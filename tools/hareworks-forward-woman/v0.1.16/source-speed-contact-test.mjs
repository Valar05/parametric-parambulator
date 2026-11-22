import assert from 'node:assert/strict';
import {SourceFootContact} from './foot-gait.mjs';
import {speedGait,transformSourceFoot} from './speed-gait.mjs';
const n=60,source=Array.from({length:n},(_,i)=>{
 const q=i/n,theta=q*2*Math.PI,hip=[.06,.91,0],ankle=[.11,.18,.37*Math.sin(theta)];
 return {phase:q,hip,knee:[.11,.54,.1],ankle,
   heel:[ankle[0],.01,ankle[2]-.12],sole:[ankle[0],0,ankle[2]],toe:[ankle[0],.01,ankle[2]+.12],
   q:[0,0,0,1]};
});
let last=[.1,.19,0],contact=new SourceFootContact({samples:source,
 gait:{start:.1,duty:.58},sourceGround:0,readWitness:kind=>kind==='ankle'?last.slice():[.04,0,1.2],
 transformSource:(s,gait)=>transformSourceFoot(s,'left',gait)});
let pin=null,planted=0,changes=0,lastDuty=null;
for(let i=0;i<900;i++){
 const target=i<300?.3:i<600?1.18:.52, gait=speedGait(target,1.224546),q=(i/300)%1;
 const f=contact.step({phase:q,totalPhase:i/300,worldZ:i*.001,gait});
 if(f.planted){
  if(pin!==null)assert.deepEqual(f.anchor,pin,'speed changed a world pin during stance');
  pin=f.anchor;planted++;
  assert(f.pivot!=='air');
 }else pin=null;
 if(lastDuty!==null&&lastDuty!==contact.activeDuty){changes++;assert(pin!==null,'stance duration changed outside touchdown');}
 lastDuty=contact.activeDuty;
 last=f.ankleTarget.slice();
}
assert(planted>150&&changes>=2,'gait speed must change touchdown timing');
assert(contact.transitions>3);
console.log('WORLD_PIN_STAYS_FIXED_ACROSS_SPEED_CHANGE_PASS transitions='+contact.transitions+' dutyUpdates='+changes);
