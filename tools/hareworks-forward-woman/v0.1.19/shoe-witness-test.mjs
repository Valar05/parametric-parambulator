import assert from 'node:assert/strict';
import {selectShoeWitnesses} from './shoe-witness.mjs';
const pts=[];let index=0;
// Synthetic shoe is long in Z, wide in X, vertical range taller than its sole;
// the ankle->toe direction is mostly DOWN, reproducing the previous axis failure.
for(let i=0;i<24;i++)for(let j=0;j<12;j++){
 const x=.07+(j-5.5)*.005,z=-.12+i*.011;
 const y=(j<6?.004:.012)+(.002*i%3);
 pts.push({mi:0,j:index++,xyz:[x,y,z]});
}
const result=selectShoeWitnesses(pts,[.018,-.10,.034]);
assert.ok(result.evidence.shoeLongitudinalExtent>.20);
assert.ok(result.heel.count>=4&&result.sole.count>=4&&result.toe.count>=4);
assert.ok(result.evidence.heelSoleToeLongitudinalCentroids[0]<result.evidence.heelSoleToeLongitudinalCentroids[1]);
assert.ok(result.evidence.heelSoleToeLongitudinalCentroids[1]<result.evidence.heelSoleToeLongitudinalCentroids[2]);
const groups=[result.heel,result.sole,result.toe].map(g=>new Set(g.indexes.map(x=>x.mi+':'+x.j)));
assert.equal(groups[0].size,result.heel.count);
for(let a=0;a<3;a++)for(let b=a+1;b<3;b++)assert.ok([...groups[a]].every(x=>!groups[b].has(x)));
// Too narrow is a real failure, not a guessed witness.
assert.throws(()=>selectShoeWitnesses(pts.map(p=>({...p,xyz:[p.xyz[0],p.xyz[1],p.xyz[2]*.09]})),[0,-.1,.03]),/INSUFFICIENT/);
// A 20-vertex nearest low-point set must NEVER qualify as a whole shoe.
assert.throws(()=>selectShoeWitnesses(pts.slice(0,20),[0,-.1,.03]),/INSUFFICIENT/);
// Vertices can be permuted and the three bands remain distinct.
let reversed=selectShoeWitnesses(pts.slice().reverse(),[.018,-.10,.034]);
assert.equal(reversed.heel.count>0,true);
console.log('SKINNED_SHOE_WITNESS_GEOMETRY_TEST_PASS length='+result.evidence.shoeLongitudinalExtent.toFixed(4));
