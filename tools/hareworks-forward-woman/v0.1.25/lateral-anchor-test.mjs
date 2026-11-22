import assert from 'node:assert/strict';
import {SourceFootContact} from './foot-gait.mjs';
import {lateralSource} from './lateral-gait.mjs';
const n=120,samples=Array.from({length:n},(_,i)=>{
 const q=i/n,z=.35*Math.cos(2*Math.PI*q),h=q>.62? .13*Math.sin(Math.PI*(q-.62)/.38):0;
 return {phase:q,hip:[.10,.9,.10],knee:[.14,.58,.22],ankle:[.12,.18+h,z],heel:[.12,.03+h,z-.1],sole:[.12,.02+h,z],toe:[.12,.03+h,z+.13],q:[0,0,0,1]};
});
const witness={ankle:[.1,.18,0],heel:[.1,0,0],sole:[.1,0,0],toe:[.1,0,0]};
const gait={start:.03,duty:.58};
const calc=new SourceFootContact({samples,gait,sourceGround:0,readWitness:k=>witness[k],transformSource:s=>lateralSource(s,'left')});
let anchor=null,planted=0,swing=0;
for(let i=0;i<480;i++){
 const p=(i/120)%1,x=-.004*i;
 const t=calc.step({phase:p,worldX:x,worldZ:0,totalPhase:i/120});
 if(t.planted){planted++;if(anchor&&t.pivot==='sole')assert.deepEqual(t.anchor,anchor,'world-X anchor must not drift under root travel');anchor=t.anchor;}
 else{anchor=null;swing++;assert(t.ankleTarget.every(Number.isFinite));}
}
assert(planted>200&&swing>80);
console.log('V025_LEFT_WORLD_X_CONTACT_ANCHOR_PASS planted='+planted+' swing='+swing);
