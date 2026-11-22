import assert from 'node:assert/strict';
import fs from 'node:fs';
import {wrapAngle,mirrorRightHeadingBias,distalHeading} from './foot-heading.mjs';
const model=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const baseL=model.feet.left.ankleYaw.start,baseR=model.feet.right.ankleYaw.start;
const bias=mirrorRightHeadingBias(baseL,baseR);
assert(Math.abs(bias+.152167562)<.00001,'right heading must use source profile, not invented rotation');
assert(Math.abs(wrapAngle(baseR+bias+baseL))<1e-10,'right heading should mirror approved left direction');
for(let i=0;i<120;i++){
 const q=i/120;
 const sample=(p)=>p.start+p.sin.reduce((v,c,j)=>v+c*Math.sin(2*Math.PI*(j+1)*q)+p.cosMinusOne[j]*(Math.cos(2*Math.PI*(j+1)*q)-1),0);
 const l=sample(model.feet.left.ankleYaw),r=sample(model.feet.right.ankleYaw);
 assert.equal(distalHeading('left',{ankleYaw:l},model),l,'approved left must remain byte-identical');
 assert(Math.abs(distalHeading('right',{ankleYaw:r},model)-(r+bias))<1e-12);
}
assert.throws(()=>mirrorRightHeadingBias(3,-1));
assert.throws(()=>distalHeading('bad',{ankleYaw:0},model));
console.log('V018_RIGHT_FOOT_FORWARD_MIRROR_PASS biasDeg='+(bias*180/Math.PI).toFixed(3)+' leftUnchanged=1');
