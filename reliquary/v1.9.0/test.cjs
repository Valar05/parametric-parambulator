const assert=require('node:assert/strict'),{blade,mapPad,envelope}=require('./motion-v1.9.0.js');let n=0;for(let a=-180;a<180;a+=10){let p=blade([0,-270]);for(let r of [.1,.5,1]){let q=mapPad(600+130*r*Math.sin(a*Math.PI/180),200-130*r*Math.cos(a*Math.PI/180),800,400,0,{});let z=blade(q,a,p);assert(Number.isFinite(z.error)&&Math.abs(z.wrist)<=65.0001&&Math.abs(z.twist)<=30&&z.branch===1);p=z;n++;}}for(let a of [0,90,-90,180]){let k=(a+360)%360;if(!envelope[k])continue;let q=mapPad(600+130*Math.sin(a*Math.PI/180),200-130*Math.cos(a*Math.PI/180),800,400,0,{});assert(Math.abs(Math.hypot(...q)-envelope[k][1])<1e-6);}console.log('CONSTRAINT_PASS',n,'covered bins',envelope.filter(Boolean).length);
const {orientationMemory}=require('./motion-v1.9.0.js');
for(const h of [0,90,180,-90]){const r=h*Math.PI/180, axis=[Math.sin(r),-Math.cos(r)], side=[Math.cos(r),Math.sin(r)], m={};assert.equal(orientationMemory(axis.map(v=>-20*v),h,h,m),h);assert.equal(orientationMemory(axis.map(v=>20*v),h,h,m),h);orientationMemory(side.map(v=>20*v),h,h,m);assert.equal(m.lock,undefined);}
console.log('orientation memory PASS');

const {coherentBlade}=require('./motion-v1.9.0.js');
for(const a of [0,45,90,135,180,-90]){let q=mapPad(600+80*Math.sin(a*Math.PI/180),200-80*Math.cos(a*Math.PI/180),800,400,0,{}), c={}, p=coherentBlade(q,a,blade([0,-270]),false,c);for(let i=0;i<120;i++){let n=coherentBlade([q[0]+.2*Math.sin(i),q[1]],a,p,false,c);assert.strictEqual(n,p);}let q2=[q[0]+10,q[1]-10];assert.notStrictEqual(coherentBlade(q2,a,p,false,c),p);}
console.log('720 stationary jitter checks PASS');
