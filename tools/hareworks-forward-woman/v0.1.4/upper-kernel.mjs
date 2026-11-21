/* Forward Woman v0.1.4: upper-body motion is Fourier-reconstructed from the
 * reference's local-space joint rotations once at startup. Generated upper
 * pose NEVER plays upper animation tracks after fitting. All calculations
 * operate on signed quaternion differences in the original joint local frame.
 * This module is pure and has no Three.js or browser dependency. */
export const TAU = Math.PI * 2;
export function finite3(v) { return Array.isArray(v)&&v.length===3&&v.every(Number.isFinite) }
export function quatConjugate(q) { return [-q[0],-q[1],-q[2],q[3]] }
export function quatMultiply(a,b){
 const [x,y,z,w]=a,[X,Y,Z,W]=b;
 return [w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X, w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z];
}
export function quatLog(raw) {
 if(!Array.isArray(raw)||raw.length!==4||!raw.every(Number.isFinite))throw Error('UPPER_QUAT_INVALID');
 const d=Math.hypot(...raw);if(d<1e-10)throw Error('UPPER_QUAT_ZERO');
 let [x,y,z,w]=raw.map(v=>v/d);
 // q and -q denote the same rotation: choose shortest local rotation.
 if(w<0){x=-x;y=-y;z=-z;w=-w}
 const n=Math.hypot(x,y,z);
 if(n<1e-11)return [2*x,2*y,2*z];
 const a=2*Math.atan2(n,w);
 return [x*a/n,y*a/n,z*a/n];
}
export function quatExp(v) {
 if(!finite3(v))throw Error('UPPER_ROT_VECTOR_INVALID');
 const a=Math.hypot(...v);const h=a*.5;
 const s=a<1e-9?.5:Math.sin(h)/a;
 return [v[0]*s,v[1]*s,v[2]*s,Math.cos(h)];
}
export function quatAngle(a,b){let d=Math.abs(a.reduce((s,x,i)=>s+x*b[i],0));d=Math.min(1,d);return 2*Math.acos(d)}
export function fitHarmonics(values,maxHarmonics=4){
 if(!Array.isArray(values)||values.length<2*maxHarmonics+4||!values.every(Number.isFinite))throw Error('UPPER_BAD_SAMPLE_SET');
 const n=values.length,mean=values.reduce((s,v)=>s+v,0)/n;
 const sin=[],cos=[];
 for(let h=1;h<=maxHarmonics;h++){
  let a=0,b=0;for(let i=0;i<n;i++){const p=TAU*h*i/n;a+=values[i]*Math.sin(p);b+=values[i]*Math.cos(p)}
  sin.push(2*a/n);cos.push(2*b/n);
 }
 // Force exact t=0 seed; periodic with equal derivatives at the seam.
 return {sin,cos,zero:mean+cos.reduce((s,x)=>s+x,0)};
}
export function evalHarmonics(c,q,limit=4) {
 if(!Number.isFinite(q))throw Error('UPPER_PHASE_NONFINITE');
 const p=((q%1)+1)%1, count=Math.min(limit,c.sin.length);
 let value=0;
 for(let i=0;i<count;i++){
  const a=TAU*(i+1)*p;
  value+=c.sin[i]*Math.sin(a)+c.cos[i]*(Math.cos(a)-1);
 }
 return value;
}
export function fitVectorSeries(samples,maxHarmonics=4){
 if(!samples.length||!samples.every(finite3))throw Error('UPPER_VECTOR_SAMPLE_INVALID');
 return [0,1,2].map(k=>fitHarmonics(samples.map(x=>x[k]),maxHarmonics));
}
export function evalVectorSeries(coeff,q,limit=4,strength=1){
 if(!Number.isFinite(strength)||strength<0||strength>1.5)throw Error('UPPER_STRENGTH_INVALID');
 return coeff.map(c=>evalHarmonics(c,q,limit)*strength);
}
export function angularStepSeries(rotVectors, seedQuat, stepHz=120){
 let max=0;let before=null;
 for(let i=0;i<=stepHz;i++){
  const v=rotVectors(i/stepHz),next=quatMultiply(seedQuat,quatExp(v));
  if(before)max=Math.max(max,quatAngle(before,next));
  before=next;
 }
 return max;
}
