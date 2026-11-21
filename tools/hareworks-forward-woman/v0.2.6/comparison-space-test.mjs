import assert from 'node:assert/strict';
import {comparisonPoint,collectComparisonPositions} from './comparison-space.mjs';
class V3{
 constructor(x=0,y=0,z=0){this.x=x;this.y=y;this.z=z}
 clone(){return new V3(this.x,this.y,this.z)}
 distanceTo(b){return Math.hypot(this.x-b.x,this.y-b.y,this.z-b.z)}
}
// Synthetic roots implement the Three.js spatial contract, including yaw.
// View placement is intentionally ±1.4, exactly the v0.2.5 regression.
class Root{
 constructor(tx,ty,tz,yaw=0){this.t=new V3(tx,ty,tz);this.yaw=yaw}
 worldToLocal(q){const x=q.x-this.t.x,y=q.y-this.t.y,z=q.z-this.t.z;
  q.x=Math.cos(this.yaw)*x-Math.sin(this.yaw)*z;
  q.y=y;q.z=Math.sin(this.yaw)*x+Math.cos(this.yaw)*z;
  return q}
 localToWorld(p){const c=Math.cos(this.yaw),s=Math.sin(this.yaw);
  return new V3(this.t.x+c*p.x+s*p.z,this.t.y+p.y,this.t.z-s*p.x+c*p.z)}
}
class Bone{constructor(root,x,y,z){this.root=root;this.p=new V3(x,y,z)}getWorldPosition(out){const p=this.root.localToWorld(this.p);out.x=p.x;out.y=p.y;out.z=p.z;return out}}
const mk=()=>new V3();
const a=new Root(0,0,-1.4),b=new Root(0,0,1.4);
const names=['mixamorigLeftFoot','mixamorigLeftToeBase','mixamorigRightFoot','mixamorigRightToeBase','mixamorigHead'];
const points={mixamorigLeftFoot:[-.2,.15,.5],mixamorigLeftToeBase:[-.2,.1,.65],mixamorigRightFoot:[.2,.15,-.5],mixamorigRightToeBase:[.2,.1,-.65],mixamorigHead:[0,1.8,0]};
const aa={},bb={};for(const n of names){aa[n]=new Bone(a,...points[n]);bb[n]=new Bone(b,...points[n])}
const A=collectComparisonPositions(aa,a,names,mk),B=collectComparisonPositions(bb,b,names,mk);
for(const name of names){assert.ok(Math.abs(aa[name].getWorldPosition(mk()).distanceTo(bb[name].getWorldPosition(mk()))-2.8)<1e-9,'v0.2.5 bug reproduced');assert.ok(A[name].distanceTo(B[name])<1e-9,'zero style must pass despite view separation')}
// Deliberate real movement remains measurable; no threshold weakening.
bb.mixamorigLeftFoot.p.z+=.058;
assert.ok(comparisonPoint(a,aa.mixamorigLeftFoot,mk).distanceTo(comparisonPoint(b,bb.mixamorigLeftFoot,mk))>.05,'unsafe 0.058 contact drift must remain rejected');
bb.mixamorigLeftFoot.p.z-=.058;
bb.mixamorigHead.p.x+=.21;
assert.ok(comparisonPoint(a,aa.mixamorigHead,mk).distanceTo(comparisonPoint(b,bb.mixamorigHead,mk))>.20,'unsafe 0.21 head shift must remain rejected');
// A different display rotation is also excluded, proving general model-local
// coordinate handling rather than a fragile hardcoded 2.8 subtraction.
const turned=new Root(4,0,-7,Math.PI/3),one=new Bone(turned,1,.3,.7),original=new Bone(a,1,.3,.7);
assert.ok(comparisonPoint(turned,one,mk).distanceTo(comparisonPoint(a,original,mk))<1e-9);
assert.throws(()=>comparisonPoint(null,one,mk),/COMPARISON_RIG_CONTRACT/);
assert.throws(()=>collectComparisonPositions(aa,a,['nonexistent'],mk),/COMPARISON_MISSING_BONE/);
console.log('V026_MODEL_SPACE_GATE_PASS: zero baseline <1e-9 at 2.8 visible separation, 0.058 foot and 0.21 head reject, rotated display stable');
