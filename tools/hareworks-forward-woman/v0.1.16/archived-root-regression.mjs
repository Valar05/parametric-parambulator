import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {inferVelocityContact,buildRootCurve,rootAt} from './root-motion.mjs';
const p=JSON.parse(readFileSync(process.argv[2],'utf8'));
assert.equal(p.sourceSha256,'a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6');
assert.equal(p.samples.length,60);
const x={left:[],right:[]};for(const s of p.samples)for(const side of ['left','right']){
 const a=s.legs[side].ankle;
 x[side].push({ankle:a,heel:s.legs[side].ankle,sole:s.legs[side].ankle,toe:s.legs[side].toe});
}
const g={left:inferVelocityContact(x.left),right:inferVelocityContact(x.right)},curve=buildRootCurve(x,g);
assert.ok(g.left.duty>.47&&g.right.duty>.47);
assert.ok(curve.stride>1.15&&curve.stride<1.35,'complete cycle root must NOT be half stride');
assert.ok(rootAt(curve,3)>3.45);
function sample(side,q){const n=x[side].length,z=((q%1)+1)%1*n,j=Math.floor(z),t=z-j;return x[side][j].ankle[2]*(1-t)+x[side][(j+1)%n].ankle[2]*t}
for(const side of ['left','right']){
 const gg=g[side],q0=gg.start,anchor=sample(side,q0)+rootAt(curve,q0);
 let worst=0;for(let i=0;i<=300;i++){
  const q=q0+gg.duty*i/300,w=sample(side,q)+rootAt(curve,q);
  worst=Math.max(worst,Math.abs(w-anchor));
 }
 assert.ok(worst<.06,side+' measured source root contact proxy drift '+worst);
 console.log('ARCHIVED_GAIT_RECONSTRUCTION',side,'duty',gg.duty.toFixed(3),'ankleZdrift',worst.toFixed(5));
}
console.log('ARCHIVED_V019_ROOT_MATH_PASS fullCycle='+curve.stride.toFixed(6));
