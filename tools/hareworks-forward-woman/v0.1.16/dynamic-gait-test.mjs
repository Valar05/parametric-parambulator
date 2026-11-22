import assert from 'node:assert/strict';
import {speedGait,blendMotion,transformSourceFoot,adjustAnkleForSpeed,rootStepDistance} from './speed-gait.mjs';
const D=1.224546, slow=speedGait(.30,D),middle=speedGait(.52,D),fast=speedGait(1.27,D);
assert(slow.stride<middle.stride&&middle.stride<fast.stride,'Speed must change stride geometry');
assert(slow.cadence<middle.cadence&&middle.cadence<fast.cadence,'Speed must change cadence');
assert(slow.crossover<fast.crossover,'Runway placement must respond to speed');
assert(slow.stanceDuty>fast.stanceDuty,'Support timing must respond to speed');
assert(Math.abs(fast.scale-1)<.002,'Reference source gait must remain accurate at its native speed');
assert(Math.abs(middle.cadence*middle.stride-.52)<1e-12,'True distance/time consistency');
const l={hip:[.071,.90,.10],ankle:[.12,.19,.37],heel:[.14,.08,.31],sole:[.15,.08,.39],toe:[.15,.10,.48]},
 r={hip:[-.062,.90,.10],ankle:[-.02,.19,.37],heel:[-.03,.08,.31],sole:[-.03,.08,.39],toe:[-.03,.10,.48]};
const le=transformSourceFoot(l,'left',fast),re=transformSourceFoot(r,'right',fast);
assert(le.ankle[0]<l.ankle[0]&&re.ankle[0]>r.ankle[0],'Foot placement must move toward centerline');
assert(Math.abs((le.toe[2]-le.heel[2])-(l.toe[2]-l.heel[2])*fast.scale)<1e-10,
 'Heel and toe geometry scale consistently');
assert(Math.abs(adjustAnkleForSpeed(l.hip,l.ankle,'left',fast)[2]-(l.hip[2]+(l.ankle[2]-l.hip[2])*fast.scale))<1e-10);
const fake={stride:D},rootAt=(_,q)=>D*q;
for(const target of [0,.3,.52,.8,1.27,1.6]){
 const g=speedGait(target,D),dt=.00833333,q=target/g.stride*dt;
 assert(Math.abs(rootStepDistance(rootAt,fake,1,1+q,g)-target*dt)<1e-10,'Root velocity must match slider');
}
let state=speedGait(.52,D),phase=0,position=0,locked=[12.3,-.4,7.3];
for(const target of [0,.52,1.27,.3,1.5,0]){
 for(let i=0;i<240;i++){
  state=blendMotion(state,speedGait(target,D),1/120);
  const next=phase+state.cadence/120;
  const delta=rootStepDistance(rootAt,fake,phase,next,state);
  assert(delta>=-1e-10 && delta<.05,'Root continuity on speed change');
  phase=next;position+=delta;
  const stanceTarget=locked.slice();
  assert.deepEqual(stanceTarget,locked,'World contact anchor must never move with gait speed');
 }
}
assert(position>0);
assert.throws(()=>speedGait(NaN,D));
assert.throws(()=>speedGait(.52,.66));
assert.throws(()=>rootStepDistance(rootAt,fake,1,0,fast));
console.log('DYNAMIC_SPEED_STRIDE_CADENCE_AND_RUNWAY_PASS');
console.log('SPEED_CHANGE_NO_ROOT_TELEPORT_AND_STATIC_WORLD_ANCHOR_PASS');
