import assert from 'node:assert/strict';
import {SourceFootContact} from './foot-gait.mjs';
const n=120;
const make=()=>Array.from({length:n},(_,i)=>{
 const q=i/n,p=(q-.10+1)%1;
 let h=.01,t=.01;
 if(p<.17){h=.06;t=0;}
 else if(p>.43&&p<.60){h=0;t=.06;}
 return {phase:q,hip:[0,.9,0],knee:[0,.55,.06],ankle:[0,.2,Math.cos(2*Math.PI*q)*.15],
  heel:[0,h,0],sole:[0,0,0],toe:[0,t,0],q:[0,0,0,1]};
});
const samples=make(),gait={start:.1,duty:.60},readWitness=kind=>[0,0,0];
const back=new SourceFootContact({samples,gait,sourceGround:0,readWitness,rootAt:()=>0,reverseRocker:true});
const first=back.step({phase:.12,totalPhase:.12,worldZ:0});
const middle=back.step({phase:.35,totalPhase:.35,worldZ:0});
const last=back.step({phase:.60,totalPhase:.60,worldZ:0});
assert.equal(first.pivot,'toe','backward initial ground contact must be toe');
assert.equal(middle.pivot,'sole','backward middle contact must roll onto sole');
assert.equal(last.pivot,'heel','backward last contact must roll onto heel');
assert.equal(first.planted,true);assert.equal(last.planted,true);
const forward=new SourceFootContact({samples,gait,sourceGround:0,readWitness,rootAt:()=>0});
forward.step({phase:.12,totalPhase:.12,worldZ:0});
const fp=forward.step({phase:.60,totalPhase:.60,worldZ:0});
assert.equal(fp.pivot,'toe','protected forward default must retain monotonic heel-to-toe restriction');
console.log('V024_REVERSE_ROCKER_TOE_SOLE_HEEL_PASS');
