import assert from 'node:assert/strict';
import fs from 'node:fs';
import {sourcePhase,reversedSamples,reversedWindows,backwardRootDelta,signedTravelPass,signForDirection} from './reverse-gait.mjs';
import {rootAt} from './root-motion.mjs';
const N=360;
const source={left:[],right:[]};
for(let i=0;i<N;i++){
 const q=i/N;
 for(const side of ['left','right']){
  const p=q+(side==='left'?0:.5),z=-.21*Math.sin(2*Math.PI*p);
  source[side].push({phase:q,hip:[side==='left'?.08:-.08,.9,.08],knee:[side==='left'?.09:-.09,.6,.11],ankle:[side==='left'?.1:-.1,.20,z],
   heel:[side==='left'?.1:-.1,.05,z+.08],sole:[side==='left'?.1:-.1,.04,z],toe:[side==='left'?.1:-.1,.06,z-.08],q:[0,0,0,1]});
 }
}
const backwards=reversedSamples(source);
for(const side of ['left','right']){
 assert.notEqual(backwards[side],source[side]);
 for(let i=0;i<N;i++){
  let orig=source[side][(N-i)%N],b=backwards[side][i];
  for(const key of ['ankle','hip','knee','heel','sole','toe','q'])assert.deepEqual(b[key],orig[key]);
  assert.equal(b.phase,i/N);
 }
 // Stance relative ankle velocity reverses sign even though shoe headings do not.
 const forward=source[side][60].ankle[2]-source[side][59].ankle[2];
 const reverse=backwards[side][60].ankle[2]-backwards[side][59].ankle[2];
 assert(forward*reverse<0,side+' velocity not reversed');
}
const g={left:{start:.1,duty:.60},right:{start:.6,duty:.60}};
const rg=reversedWindows(g);
const circularDistance=(a,b)=>{const d=Math.abs(a-b)%1;return Math.min(d,1-d);};
assert(Math.abs(rg.left.start-.30)<1e-12);
assert(Math.abs(rg.right.start-.80)<1e-12);
for(const side of ['left','right'])for(let i=0;i<N;i++){
 let q=i/N,original=(q-g[side].start+1)%1<g[side].duty;
 let newQ=(1-q)%1,backward=(q-rg[side].start+1)%1<rg[side].duty;
 // Avoid the exact boundaries, where discrete samples differ by one tick.
 if(Math.min(circularDistance(q,g[side].start),circularDistance(q,g[side].start+g[side].duty))>.008)
  assert.equal(original,((1-q-rg[side].start+2)%1)<rg[side].duty,'involutive phase reversal');
}
assert.equal(sourcePhase('backward',.25),.75);
assert.equal(sourcePhase('forward',.25),.25);
assert.equal(signForDirection('backward'),-1);
assert.throws(()=>sourcePhase('left',.25));
const positions=Array.from({length:121},(_,i)=>1.24*(i/120)+.045*Math.sin(2*Math.PI*i/120));
const curve={n:120,stride:1.24,positions};
const m={referenceStride:1.24,scale:1};
for(let i=0;i<720;i++){
 const old=i/120,now=(i+1)/120;
 const dz=backwardRootDelta(rootAt,curve,old,now,m);
 assert(dz<=0,'backward world root must travel negative');
 const opposite=rootAt(curve,-now)-rootAt(curve,-old);
 assert(Math.abs(dz-opposite)<1e-9);
}
assert(Math.abs(backwardRootDelta(rootAt,curve,0,3,m)+3*curve.stride)<1e-8);
assert(signedTravelPass('backward',-.52,.52,.01));
assert(!signedTravelPass('backward',.52,.52,.01));
assert(signedTravelPass('forward',.52,.52,.01));
const archivePath=process.argv[2];
if(archivePath){
 const archive=JSON.parse(fs.readFileSync(archivePath,'utf8'));
 assert.equal(archive.sourceClip,'Walking_Woman');
 assert.equal(archive.samples.length,60);
 for(const side of ['left','right']){
  let signBefore=0,signAfter=0;
  const src=archive.samples.map(s=>s.legs[side].ankle[2]);
  const rv=src.map((_,i)=>src[(60-i)%60]);
  for(let i=0;i<60;i++){
   const k=(i+1)%60;signBefore+=Math.abs(src[k]-src[i]);signAfter+=Math.abs(rv[k]-rv[i]);
  }
  assert(Math.abs(signBefore-signAfter)<1e-9);
 }
}
console.log('V024_BACKWARD_PHASE_ROOT_CONTACT_TEST_PASS samples='+N+' sourceArchive='+Boolean(archivePath));
